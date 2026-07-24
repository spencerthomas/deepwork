"""Bounded stdlib SQLite persistence for the credential-free local task mode."""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import weakref
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeVar, cast

from deepwork_api.domain import (
    CANCELLATION_SAFE_REASON,
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    MAX_TASK_OBJECTIVE_LENGTH,
    MAX_TASK_RESULT_LENGTH,
    CancellationRecord,
    DecisionConflictError,
    DecisionRecord,
    DecisionValue,
    EventData,
    EventDataValue,
    EvidenceClass,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    InterruptMismatchError,
    InvalidEventCursorError,
    PlanRevisionConflictError,
    PlanUnavailableError,
    PlanUpdateRecord,
    ProposedPlan,
    StaleInterruptError,
    TaskAlreadyResolvedError,
    TaskEvent,
    TaskEventName,
    TaskNotFoundError,
    TaskSnapshot,
    TaskStatus,
)
from deepwork_api.ports import Clock, system_clock

_APPLICATION_ID = 0x44575031
_SCHEMA_VERSION = 3
_BUSY_TIMEOUT_MILLISECONDS = 5_000
_MAX_SERIALIZED_BYTES = 64 * 1024
_MAX_TASK_NUMBER = 99_999_999
_MAX_TASK_TITLE_LENGTH = 80
_MAX_PLAN_TITLE_LENGTH = 100
_MAX_EVIDENCE_SUMMARY_LENGTH = 300
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_T = TypeVar("_T")


class SQLiteTaskRepositoryError(Exception):
    """Base exception for safe local persistence failures."""


class SQLiteTaskRepositoryPathError(SQLiteTaskRepositoryError):
    """The configured local database path is unsafe or unusable."""


class SQLiteTaskRepositorySchemaError(SQLiteTaskRepositoryError):
    """The local database schema is absent, unknown, or unsupported."""


class SQLiteTaskRepositoryDataError(SQLiteTaskRepositoryError):
    """Stored task state is corrupt or cannot be projected safely."""


class SQLiteTaskRepositoryClosedError(SQLiteTaskRepositoryError):
    """The repository has been closed and cannot accept more work."""


@dataclass(slots=True)
class _ProcessState:
    """Same-event-loop serialization and waiter notification for one database."""

    condition: asyncio.Condition
    references: int = 0


_PROCESS_STATES: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop,
    dict[str, _ProcessState],
] = weakref.WeakKeyDictionary()


_SCHEMA_STATEMENTS = (
    """
CREATE TABLE tasks (
    task_number INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL,
    pending_interrupt_id TEXT,
    plan_revision INTEGER,
    plan_title TEXT,
    plan_steps TEXT,
    plan_evidence_refs TEXT,
    result TEXT,
    created_at TEXT
)
""",
    """
CREATE TABLE events (
    task_id TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (task_id, event_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
)
""",
    """
CREATE TABLE evidence (
    task_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    evidence_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL,
    verified INTEGER NOT NULL,
    PRIMARY KEY (task_id, position),
    UNIQUE (task_id, evidence_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
)
""",
    """
CREATE TABLE decisions (
    task_id TEXT NOT NULL,
    interrupt_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    response_digest TEXT,
    PRIMARY KEY (task_id, interrupt_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
)
""",
    "CREATE INDEX events_task_order ON events(task_id, event_id)",
    "CREATE INDEX evidence_task_order ON evidence(task_id, position)",
)

# In-place upgrades from an older on-disk schema version to _SCHEMA_VERSION,
# keyed by the stored user_version. Each converges the `tasks` table onto the
# single canonical shape (created_at nullable and last) so a fresh database and
# any upgraded database validate identically. Real timestamps are preserved; a
# never-recorded creation instant becomes NULL rather than a fabricated value.
_SUPPORTED_UPGRADES: dict[int, tuple[str, ...]] = {
    # v1 predates created_at: appending the column leaves existing rows NULL.
    1: ("ALTER TABLE tasks ADD COLUMN created_at TEXT",),
    # v2 (the first timestamp release) stored created_at as a NOT NULL fourth
    # column. Move it last and drop NOT NULL without losing the recorded values,
    # using only column operations so child foreign keys are never disturbed.
    2: (
        "ALTER TABLE tasks RENAME COLUMN created_at TO created_at_legacy",
        "ALTER TABLE tasks ADD COLUMN created_at TEXT",
        "UPDATE tasks SET created_at = created_at_legacy",
        "ALTER TABLE tasks DROP COLUMN created_at_legacy",
    ),
}

_EXPECTED_COLUMNS = {
    "tasks": (
        "task_number",
        "task_id",
        "run_id",
        "title",
        "objective",
        "status",
        "pending_interrupt_id",
        "plan_revision",
        "plan_title",
        "plan_steps",
        "plan_evidence_refs",
        "result",
        "created_at",
    ),
    "events": ("task_id", "event_id", "name", "data"),
    "evidence": (
        "task_id",
        "position",
        "evidence_id",
        "kind",
        "summary",
        "source",
        "verified",
    ),
    "decisions": ("task_id", "interrupt_id", "decision", "response_digest"),
}

_EXPECTED_TABLE_INFO = {
    "tasks": (
        ("task_number", "INTEGER", 0, 1),
        ("task_id", "TEXT", 1, 0),
        ("run_id", "TEXT", 1, 0),
        ("title", "TEXT", 1, 0),
        ("objective", "TEXT", 1, 0),
        ("status", "TEXT", 1, 0),
        ("pending_interrupt_id", "TEXT", 0, 0),
        ("plan_revision", "INTEGER", 0, 0),
        ("plan_title", "TEXT", 0, 0),
        ("plan_steps", "TEXT", 0, 0),
        ("plan_evidence_refs", "TEXT", 0, 0),
        ("result", "TEXT", 0, 0),
        # Nullable and last so a fresh database and every in-place upgrade in
        # _SUPPORTED_UPGRADES converge on one canonical column layout.
        ("created_at", "TEXT", 0, 0),
    ),
    "events": (
        ("task_id", "TEXT", 1, 1),
        ("event_id", "INTEGER", 1, 2),
        ("name", "TEXT", 1, 0),
        ("data", "TEXT", 1, 0),
    ),
    "evidence": (
        ("task_id", "TEXT", 1, 1),
        ("position", "INTEGER", 1, 2),
        ("evidence_id", "TEXT", 1, 0),
        ("kind", "TEXT", 1, 0),
        ("summary", "TEXT", 1, 0),
        ("source", "TEXT", 1, 0),
        ("verified", "INTEGER", 1, 0),
    ),
    "decisions": (
        ("task_id", "TEXT", 1, 1),
        ("interrupt_id", "TEXT", 1, 2),
        ("decision", "TEXT", 1, 0),
        ("response_digest", "TEXT", 0, 0),
    ),
}

_EXPECTED_INDEXES = {
    "tasks": Counter(
        {
            (True, "u", ("task_id",)): 1,
            (True, "u", ("run_id",)): 1,
        }
    ),
    "events": Counter(
        {
            (True, "pk", ("task_id", "event_id")): 1,
            (False, "c", ("task_id", "event_id")): 1,
        }
    ),
    "evidence": Counter(
        {
            (True, "pk", ("task_id", "position")): 1,
            (True, "u", ("task_id", "evidence_id")): 1,
            (False, "c", ("task_id", "position")): 1,
        }
    ),
    "decisions": Counter(
        {
            (True, "pk", ("task_id", "interrupt_id")): 1,
        }
    ),
}

_EXPECTED_FOREIGN_KEYS = {
    "tasks": (),
    "events": (("tasks", "task_id", "task_id", "NO ACTION", "RESTRICT", "NONE"),),
    "evidence": (("tasks", "task_id", "task_id", "NO ACTION", "RESTRICT", "NONE"),),
    "decisions": (("tasks", "task_id", "task_id", "NO ACTION", "RESTRICT", "NONE"),),
}

_EXPECTED_OBJECTS = {
    "tasks",
    "events",
    "evidence",
    "decisions",
    "events_task_order",
    "evidence_task_order",
}


class SQLiteTaskRepository:
    """Persist TaskRepository state in one explicit local SQLite database.

    This adapter is deliberately local-only. It does not provide the cross-process
    outbox, tenancy, migrations, backups, or production guarantees expected from
    the canonical PostgreSQL durability implementation.
    """

    def __init__(self, database_path: str | Path, *, clock: Clock = system_clock) -> None:
        self._path = _safe_database_path(database_path)
        self._clock = clock
        self._initialized = False
        self._closed = False
        self._initialization_lock = asyncio.Lock()
        self._process_state: _ProcessState | None = None
        self._process_loop: asyncio.AbstractEventLoop | None = None

    @property
    def database_path(self) -> Path:
        """Return the canonical explicit database path."""

        return self._path

    async def initialize(self) -> None:
        """Create or validate the versioned schema without blocking the event loop."""

        self._ensure_open()
        if self._is_initialized():
            return
        async with self._initialization_lock:
            self._ensure_open()
            if self._is_initialized():
                return
            await self._run_sync(self._initialize_sync)
            self._initialized = True

    async def close(self) -> None:
        """Close this logical adapter and wake its in-process waiters."""

        if self._is_closed():
            return
        state = self._process_state
        if state is not None:
            loop = asyncio.get_running_loop()
            if self._process_loop is not loop:
                raise SQLiteTaskRepositoryClosedError(
                    "local task repository must close on its owning event loop"
                )
            async with state.condition:
                if self._is_closed():
                    return
                self._closed = True
                state.condition.notify_all()
                state.references -= 1
                loop_states = _PROCESS_STATES.get(loop)
                if (
                    state.references == 0
                    and loop_states is not None
                    and loop_states.get(str(self._path)) is state
                ):
                    del loop_states[str(self._path)]
                    if not loop_states:
                        del _PROCESS_STATES[loop]
            self._process_state = None
            self._process_loop = None
        else:
            self._closed = True

    async def create_task(
        self, *, title: str, objective: str, run_id: str | None = None
    ) -> TaskSnapshot:
        """Create a queued task and its initial replayable event."""

        _validate_task_input(title=title, objective=objective)
        return await self._mutate(self._create_task_sync, title, objective, run_id)

    async def list_tasks(self) -> tuple[TaskSnapshot, ...]:
        """List tasks in deterministic creation order."""

        await self.initialize()
        return await self._run_sync(self._list_tasks_sync)

    async def get_task(self, task_id: str) -> TaskSnapshot:
        """Read one task or raise the port's safe not-found error."""

        await self.initialize()
        return await self._run_sync(self._get_task_sync, task_id)

    async def append_event(
        self,
        task_id: str,
        *,
        name: TaskEventName,
        data: EventData,
        status: TaskStatus | None = None,
        pending_interrupt_id: str | None = None,
        clear_pending_interrupt: bool = False,
        result: str | None = None,
    ) -> TaskEvent:
        """Append one event and atomically update related task state."""

        encoded_data = _encode_event_data(data)
        if result is not None and len(result) > MAX_TASK_RESULT_LENGTH:
            raise ValueError("task result exceeds the shared response bound")
        return await self._mutate(
            self._append_event_sync,
            task_id,
            name,
            encoded_data,
            status,
            pending_interrupt_id,
            clear_pending_interrupt,
            result,
        )

    async def record_evidence(
        self,
        task_id: str,
        evidence: EvidenceRecord,
    ) -> TaskEvent:
        """Store and replay one evidence record."""

        _validate_evidence(evidence)
        return await self._mutate(self._record_evidence_sync, task_id, evidence)

    async def set_plan(
        self,
        task_id: str,
        *,
        plan: ProposedPlan,
        event_name: TaskEventName,
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> TaskEvent:
        """Store and replay a runner-owned proposed or revised plan."""

        steps, references = _encode_plan(plan)
        return await self._mutate(
            self._set_plan_sync,
            task_id,
            plan,
            steps,
            references,
            event_name,
            evidence_class,
        )

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> PlanUpdateRecord:
        """Edit the current plan for an exact pending interrupt/revision."""

        _validate_plan_revision(expected_revision)
        _validate_steps(steps)
        encoded_steps = _encode_string_tuple(steps)
        return await self._mutate(
            self._update_plan_sync,
            task_id,
            interrupt_id,
            expected_revision,
            steps,
            encoded_steps,
            evidence_class,
        )

    async def events_after(self, task_id: str, event_id: int) -> tuple[TaskEvent, ...]:
        """Return replay events strictly after a validated cursor."""

        await self.initialize()
        return await self._run_sync(self._events_after_sync, task_id, event_id)

    async def wait_for_events(self, task_id: str, event_id: int) -> None:
        """Wait without polling for a later event or terminal state."""

        await self.initialize()
        state = self._state()
        async with state.condition:
            while True:
                self._ensure_open()
                ready = await self._run_sync(self._event_wait_ready_sync, task_id, event_id)
                if ready:
                    return
                await state.condition.wait()

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        """Atomically record or idempotently replay one interrupt decision."""

        if response_digest is not None and _SHA256_PATTERN.fullmatch(response_digest) is None:
            raise ValueError("response digest must be a lowercase SHA-256 value")
        return await self._mutate(
            self._record_decision_sync,
            task_id,
            interrupt_id,
            decision,
            comment_provided,
            response_digest,
        )

    async def wait_for_decision(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue:
        """Wait without polling for the exact interrupt decision."""

        await self.initialize()
        state = self._state()
        async with state.condition:
            while True:
                self._ensure_open()
                decision = await self._run_sync(
                    self._decision_wait_value_sync,
                    task_id,
                    interrupt_id,
                )
                if decision is not None:
                    return decision
                await state.condition.wait()

    async def cancel_task(self, task_id: str) -> CancellationRecord:
        """Atomically move a live task to a terminal cancelled state."""

        return await self._mutate(self._cancel_task_sync, task_id)

    async def _mutate(
        self,
        operation: Callable[..., _T],
        *arguments: object,
    ) -> _T:
        await self.initialize()
        state = self._state()
        async with state.condition:
            self._ensure_open()
            try:
                return await self._run_sync(operation, *arguments)
            finally:
                # _run_sync delays cancellation until its bounded worker has
                # finished, so every possibly committed mutation signals.
                state.condition.notify_all()

    async def _run_sync(
        self,
        operation: Callable[..., _T],
        *arguments: object,
    ) -> _T:
        worker = asyncio.create_task(asyncio.to_thread(operation, *arguments))
        try:
            return await asyncio.shield(worker)
        except asyncio.CancelledError as cancellation:
            while not worker.done():
                try:
                    await asyncio.shield(worker)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            if not worker.cancelled():
                worker.exception()
            raise cancellation
        except sqlite3.DatabaseError as error:
            raise SQLiteTaskRepositoryDataError(
                "local task database operation failed safely"
            ) from error

    def _state(self) -> _ProcessState:
        loop = asyncio.get_running_loop()
        if self._process_state is not None:
            if self._process_loop is not loop:
                raise SQLiteTaskRepositoryError(
                    "local task repository cannot move between event loops"
                )
            return self._process_state
        loop_states = _PROCESS_STATES.setdefault(loop, {})
        key = str(self._path)
        state = loop_states.get(key)
        if state is None:
            state = _ProcessState(condition=asyncio.Condition())
            loop_states[key] = state
        state.references += 1
        self._process_state = state
        self._process_loop = loop
        return state

    def _ensure_open(self) -> None:
        if self._closed:
            raise SQLiteTaskRepositoryClosedError("local task repository is closed")

    def _is_initialized(self) -> bool:
        return self._initialized

    def _is_closed(self) -> bool:
        return self._closed

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path,
            timeout=_BUSY_TIMEOUT_MILLISECONDS / 1_000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MILLISECONDS}")
        foreign_keys = cast(int, connection.execute("PRAGMA foreign_keys").fetchone()[0])
        if foreign_keys != 1:
            connection.close()
            raise SQLiteTaskRepositorySchemaError("local task database cannot enforce foreign keys")
        return connection

    def _initialize_sync(self) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            version = cast(int, connection.execute("PRAGMA user_version").fetchone()[0])
            application_id = cast(
                int,
                connection.execute("PRAGMA application_id").fetchone()[0],
            )
            objects = {
                cast(str, row["name"])
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type IN ('table', 'index')
                      AND name NOT LIKE 'sqlite_%'
                    """
                )
            }
            if version == 0 and application_id == 0 and not objects:
                for statement in _SCHEMA_STATEMENTS:
                    connection.execute(statement)
                connection.execute(f"PRAGMA application_id = {_APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif application_id == _APPLICATION_ID and version in _SUPPORTED_UPGRADES:
                # Upgrade an older local database in place. Every statement here
                # runs inside this initialization transaction, so if the migrated
                # database then fails strict validation below the whole upgrade
                # rolls back and the on-disk schema is left untouched.
                for statement in _SUPPORTED_UPGRADES[version]:
                    connection.execute(statement)
                connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif version != _SCHEMA_VERSION or application_id != _APPLICATION_ID:
                raise SQLiteTaskRepositorySchemaError(
                    "local task database schema version is unsupported"
                )
            objects = {
                cast(str, row["name"])
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type IN ('table', 'index')
                      AND name NOT LIKE 'sqlite_%'
                    """
                )
            }
            if objects != _EXPECTED_OBJECTS:
                raise SQLiteTaskRepositorySchemaError(
                    "local task database schema objects are unsupported"
                )
            self._validate_schema_sync(connection)
            check = cast(str, connection.execute("PRAGMA quick_check").fetchone()[0])
            if check != "ok":
                raise SQLiteTaskRepositoryDataError("local task database integrity check failed")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _validate_schema_sync(connection: sqlite3.Connection) -> None:
        for table, expected in _EXPECTED_COLUMNS.items():
            table_rows = tuple(connection.execute(f"PRAGMA table_info({table})"))
            actual = tuple(cast(str, row["name"]) for row in table_rows)
            table_info = tuple(
                (
                    cast(str, row["name"]),
                    cast(str, row["type"]).upper(),
                    cast(int, row["notnull"]),
                    cast(int, row["pk"]),
                )
                for row in table_rows
            )
            if (
                actual != expected
                or table_info != _EXPECTED_TABLE_INFO[table]
                or any(row["dflt_value"] is not None for row in table_rows)
            ):
                raise SQLiteTaskRepositorySchemaError(
                    "local task database schema shape is unsupported"
                )
            indexes: Counter[tuple[bool, str, tuple[str, ...]]] = Counter()
            for row in connection.execute(f"PRAGMA index_list({table})"):
                if cast(int, row["partial"]) != 0:
                    raise SQLiteTaskRepositorySchemaError(
                        "local task database partial indexes are unsupported"
                    )
                index_name = cast(str, row["name"])
                columns = tuple(
                    cast(str, column["name"])
                    for column in connection.execute(f"PRAGMA index_info({index_name})")
                )
                indexes[
                    (
                        bool(cast(int, row["unique"])),
                        cast(str, row["origin"]),
                        columns,
                    )
                ] += 1
            if indexes != _EXPECTED_INDEXES[table]:
                raise SQLiteTaskRepositorySchemaError(
                    "local task database index constraints are unsupported"
                )
            foreign_keys = tuple(
                (
                    cast(str, row["table"]),
                    cast(str, row["from"]),
                    cast(str, row["to"]),
                    cast(str, row["on_update"]),
                    cast(str, row["on_delete"]),
                    cast(str, row["match"]),
                )
                for row in connection.execute(f"PRAGMA foreign_key_list({table})")
            )
            if foreign_keys != _EXPECTED_FOREIGN_KEYS[table]:
                raise SQLiteTaskRepositorySchemaError(
                    "local task database foreign keys are unsupported"
                )

    def _create_task_sync(
        self, title: str, objective: str, external_run_id: str | None = None
    ) -> TaskSnapshot:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            created_at = self._clock().isoformat()
            cursor = connection.execute(
                """
                INSERT INTO tasks (
                    task_id, run_id, title, objective, status,
                    pending_interrupt_id, plan_revision, plan_title,
                    plan_steps, plan_evidence_refs, result, created_at
                ) VALUES ('pending', 'pending', ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, ?)
                """,
                (title, objective, TaskStatus.QUEUED.value, created_at),
            )
            number = cast(int, cursor.lastrowid)
            if number < 1 or number > _MAX_TASK_NUMBER:
                raise SQLiteTaskRepositoryDataError("local task identifier bound exhausted")
            suffix = f"{number:08d}"
            task_id = f"task_{suffix}"
            run_id = external_run_id or f"run_{suffix}"
            connection.execute(
                "UPDATE tasks SET task_id = ?, run_id = ? WHERE task_number = ?",
                (task_id, run_id, number),
            )
            event = TaskEvent(
                event_id=1,
                name=TaskEventName.TASK_CREATED,
                data=(
                    ("taskId", task_id),
                    ("runId", run_id),
                    ("status", TaskStatus.QUEUED.value),
                ),
            )
            self._insert_event_sync(connection, task_id, event)
            snapshot = self._snapshot_sync(connection, task_id)
            connection.commit()
            return snapshot
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _list_tasks_sync(self) -> tuple[TaskSnapshot, ...]:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            task_ids = tuple(
                cast(str, row["task_id"])
                for row in connection.execute("SELECT task_id FROM tasks ORDER BY task_number ASC")
            )
            snapshots = tuple(self._snapshot_sync(connection, task_id) for task_id in task_ids)
            connection.commit()
            return snapshots
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _get_task_sync(self, task_id: str) -> TaskSnapshot:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            snapshot = self._snapshot_sync(connection, task_id)
            connection.commit()
            return snapshot
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _append_event_sync(
        self,
        task_id: str,
        name: TaskEventName,
        encoded_data: str,
        status: TaskStatus | None,
        pending_interrupt_id: str | None,
        clear_pending_interrupt: bool,
        result: str | None,
    ) -> TaskEvent:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            if _decode_status(task["status"]).is_terminal:
                raise StaleInterruptError
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=name,
                data=_decode_event_data(encoded_data),
            )
            connection.execute(
                "INSERT INTO events (task_id, event_id, name, data) VALUES (?, ?, ?, ?)",
                (task_id, event.event_id, name.value, encoded_data),
            )
            updates: list[str] = []
            values: list[object] = []
            if status is not None:
                updates.append("status = ?")
                values.append(status.value)
            if pending_interrupt_id is not None:
                updates.append("pending_interrupt_id = ?")
                values.append(pending_interrupt_id)
            elif clear_pending_interrupt:
                updates.append("pending_interrupt_id = NULL")
            if result is not None:
                updates.append("result = ?")
                values.append(result)
            if updates:
                values.append(task_id)
                connection.execute(
                    f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?",
                    tuple(values),
                )
            connection.commit()
            return event
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _record_evidence_sync(
        self,
        task_id: str,
        evidence: EvidenceRecord,
    ) -> TaskEvent:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            if _decode_status(task["status"]).is_terminal:
                raise StaleInterruptError
            position = cast(
                int,
                connection.execute(
                    "SELECT COALESCE(MAX(position), 0) + 1 FROM evidence WHERE task_id = ?",
                    (task_id,),
                ).fetchone()[0],
            )
            connection.execute(
                """
                INSERT INTO evidence (
                    task_id, position, evidence_id, kind, summary, source, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    position,
                    evidence.evidence_id,
                    evidence.kind.value,
                    evidence.summary,
                    evidence.source.value,
                    int(evidence.verified),
                ),
            )
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=TaskEventName.EVIDENCE_RECORDED,
                data=(
                    ("evidenceId", evidence.evidence_id),
                    ("kind", evidence.kind),
                    ("summary", evidence.summary),
                    ("source", evidence.source),
                    ("verified", evidence.verified),
                ),
            )
            self._insert_event_sync(connection, task_id, event)
            connection.commit()
            return event
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _set_plan_sync(
        self,
        task_id: str,
        plan: ProposedPlan,
        encoded_steps: str,
        encoded_references: str,
        event_name: TaskEventName,
        evidence_class: EvidenceClass,
    ) -> TaskEvent:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            if _decode_status(task["status"]).is_terminal:
                raise StaleInterruptError
            current = self._plan_from_row(task)
            if current is not None and plan.revision <= current.revision:
                raise PlanRevisionConflictError
            connection.execute(
                """
                UPDATE tasks
                SET plan_revision = ?, plan_title = ?, plan_steps = ?,
                    plan_evidence_refs = ?
                WHERE task_id = ?
                """,
                (
                    plan.revision,
                    plan.title,
                    encoded_steps,
                    encoded_references,
                    task_id,
                ),
            )
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=event_name,
                data=_plan_event_data(plan, evidence_class),
            )
            self._insert_event_sync(connection, task_id, event)
            connection.commit()
            return event
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _update_plan_sync(
        self,
        task_id: str,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
        encoded_steps: str,
        evidence_class: EvidenceClass,
    ) -> PlanUpdateRecord:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            if _decode_status(task["status"]).is_terminal or task["pending_interrupt_id"] is None:
                raise StaleInterruptError
            if cast(str, task["pending_interrupt_id"]) != interrupt_id:
                raise InterruptMismatchError
            current = self._plan_from_row(task)
            if current is None:
                raise PlanUnavailableError
            if current.revision != expected_revision:
                raise PlanRevisionConflictError
            if current.revision >= MAX_PLAN_REVISION:
                raise PlanRevisionConflictError
            updated = ProposedPlan(
                revision=current.revision + 1,
                title=current.title,
                steps=steps,
                evidence_refs=current.evidence_refs,
            )
            connection.execute(
                "UPDATE tasks SET plan_revision = ?, plan_steps = ? WHERE task_id = ?",
                (updated.revision, encoded_steps, task_id),
            )
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=TaskEventName.PLAN_UPDATED,
                data=_plan_event_data(updated, evidence_class),
            )
            self._insert_event_sync(connection, task_id, event)
            connection.commit()
            return PlanUpdateRecord(
                task_id=cast(str, task["task_id"]),
                run_id=cast(str, task["run_id"]),
                interrupt_id=interrupt_id,
                plan=updated,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _events_after_sync(self, task_id: str, event_id: int) -> tuple[TaskEvent, ...]:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            count = self._event_count_sync(connection, task_id)
            self._validate_cursor(event_id, count)
            events = tuple(
                self._event_from_row(row)
                for row in connection.execute(
                    """
                    SELECT event_id, name, data
                    FROM events
                    WHERE task_id = ? AND event_id > ?
                    ORDER BY event_id ASC
                    """,
                    (task_id, event_id),
                )
            )
            connection.commit()
            return events
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _event_wait_ready_sync(self, task_id: str, event_id: int) -> bool:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            task = self._task_row_sync(connection, task_id)
            count = self._event_count_for_existing_task_sync(connection, task_id)
            self._validate_cursor(event_id, count)
            ready = count > event_id or _decode_status(task["status"]).is_terminal
            connection.commit()
            return ready
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _record_decision_sync(
        self,
        task_id: str,
        interrupt_id: str,
        decision: DecisionValue,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            existing = connection.execute(
                """
                SELECT decision, response_digest
                FROM decisions
                WHERE task_id = ? AND interrupt_id = ?
                """,
                (task_id, interrupt_id),
            ).fetchone()
            if existing is not None:
                existing_decision = _decode_decision(existing["decision"])
                existing_digest = cast(str | None, existing["response_digest"])
                if existing_decision is not decision or existing_digest != response_digest:
                    raise DecisionConflictError
                connection.commit()
                return DecisionRecord(
                    task_id=cast(str, task["task_id"]),
                    run_id=cast(str, task["run_id"]),
                    interrupt_id=interrupt_id,
                    decision=decision,
                    duplicate=True,
                )
            if _decode_status(task["status"]).is_terminal or task["pending_interrupt_id"] is None:
                raise StaleInterruptError
            if cast(str, task["pending_interrupt_id"]) != interrupt_id:
                raise InterruptMismatchError
            connection.execute(
                """
                INSERT INTO decisions (task_id, interrupt_id, decision, response_digest)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, interrupt_id, decision.value, response_digest),
            )
            connection.execute(
                """
                UPDATE tasks
                SET pending_interrupt_id = NULL, status = ?
                WHERE task_id = ?
                """,
                (TaskStatus.RUNNING.value, task_id),
            )
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=TaskEventName.DECISION_RECORDED,
                data=(
                    ("interruptId", interrupt_id),
                    ("decision", decision.value),
                    ("commentProvided", comment_provided),
                    ("responseProvided", response_digest is not None),
                ),
            )
            self._insert_event_sync(connection, task_id, event)
            connection.commit()
            return DecisionRecord(
                task_id=cast(str, task["task_id"]),
                run_id=cast(str, task["run_id"]),
                interrupt_id=interrupt_id,
                decision=decision,
                duplicate=False,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _cancel_task_sync(self, task_id: str) -> CancellationRecord:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            task = self._task_row_sync(connection, task_id)
            status = _decode_status(task["status"])
            if status is TaskStatus.CANCELLED:
                connection.commit()
                return CancellationRecord(
                    task_id=cast(str, task["task_id"]),
                    run_id=cast(str, task["run_id"]),
                    duplicate=True,
                )
            if status.is_terminal:
                raise TaskAlreadyResolvedError
            event = TaskEvent(
                event_id=self._next_event_id_sync(connection, task_id),
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", cast(str, task["run_id"])),
                    ("status", TaskStatus.CANCELLED.value),
                    ("safeReason", CANCELLATION_SAFE_REASON),
                    ("resultAvailable", False),
                ),
            )
            self._insert_event_sync(connection, task_id, event)
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, pending_interrupt_id = NULL
                WHERE task_id = ?
                """,
                (TaskStatus.CANCELLED.value, task_id),
            )
            connection.commit()
            return CancellationRecord(
                task_id=cast(str, task["task_id"]),
                run_id=cast(str, task["run_id"]),
                duplicate=False,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _decision_wait_value_sync(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue | None:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            task = self._task_row_sync(connection, task_id)
            row = connection.execute(
                "SELECT decision FROM decisions WHERE task_id = ? AND interrupt_id = ?",
                (task_id, interrupt_id),
            ).fetchone()
            if row is not None:
                decision = _decode_decision(row["decision"])
                connection.commit()
                return decision
            if _decode_status(task["status"]).is_terminal:
                raise StaleInterruptError
            connection.commit()
            return None
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _snapshot_sync(
        self,
        connection: sqlite3.Connection,
        task_id: str,
    ) -> TaskSnapshot:
        task = self._task_row_sync(connection, task_id)
        event_count = self._event_count_for_existing_task_sync(connection, task_id)
        evidence = tuple(
            self._evidence_from_row(row)
            for row in connection.execute(
                """
                SELECT evidence_id, kind, summary, source, verified
                FROM evidence
                WHERE task_id = ?
                ORDER BY position ASC
                """,
                (task_id,),
            )
        )
        title = _bounded_stored_string(
            task["title"],
            field="task title",
            maximum=_MAX_TASK_TITLE_LENGTH,
        )
        objective = _bounded_stored_string(
            task["objective"],
            field="task objective",
            maximum=MAX_TASK_OBJECTIVE_LENGTH,
        )
        result_value = task["result"]
        result = (
            None
            if result_value is None
            else _bounded_stored_string(
                result_value,
                field="task result",
                maximum=MAX_TASK_RESULT_LENGTH,
                allow_empty=True,
            )
        )
        pending = cast(str | None, task["pending_interrupt_id"])
        if pending is not None and not pending:
            raise SQLiteTaskRepositoryDataError("stored pending interrupt identifier is invalid")
        created_at_value = task["created_at"]
        created_at = (
            None
            if created_at_value is None
            else _bounded_stored_string(
                created_at_value,
                field="task creation timestamp",
                maximum=64,
            )
        )
        return TaskSnapshot(
            task_id=cast(str, task["task_id"]),
            run_id=cast(str, task["run_id"]),
            created_at=created_at,
            title=title,
            objective=objective,
            status=_decode_status(task["status"]),
            last_event_id=event_count,
            pending_interrupt_id=pending,
            proposed_plan=self._plan_from_row(task),
            evidence=evidence,
            result=result,
        )

    @staticmethod
    def _task_row_sync(
        connection: sqlite3.Connection,
        task_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise TaskNotFoundError
        return cast(sqlite3.Row, row)

    def _event_count_sync(self, connection: sqlite3.Connection, task_id: str) -> int:
        self._task_row_sync(connection, task_id)
        return self._event_count_for_existing_task_sync(connection, task_id)

    @staticmethod
    def _event_count_for_existing_task_sync(
        connection: sqlite3.Connection,
        task_id: str,
    ) -> int:
        rows = tuple(
            connection.execute(
                """
            SELECT event_id, name, data
            FROM events
            WHERE task_id = ?
            ORDER BY event_id ASC
            """,
                (task_id,),
            )
        )
        if not rows:
            raise SQLiteTaskRepositoryDataError("stored task event history is not contiguous")
        for expected_id, row in enumerate(rows, start=1):
            event = SQLiteTaskRepository._event_from_row(row)
            if event.event_id != expected_id:
                raise SQLiteTaskRepositoryDataError("stored task event history is not contiguous")
        return len(rows)

    def _next_event_id_sync(
        self,
        connection: sqlite3.Connection,
        task_id: str,
    ) -> int:
        return self._event_count_for_existing_task_sync(connection, task_id) + 1

    @staticmethod
    def _insert_event_sync(
        connection: sqlite3.Connection,
        task_id: str,
        event: TaskEvent,
    ) -> None:
        connection.execute(
            "INSERT INTO events (task_id, event_id, name, data) VALUES (?, ?, ?, ?)",
            (task_id, event.event_id, event.name.value, _encode_event_data(event.data)),
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> TaskEvent:
        event_id = row["event_id"]
        if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id < 1:
            raise SQLiteTaskRepositoryDataError("stored event identifier is invalid")
        return TaskEvent(
            event_id=event_id,
            name=_decode_event_name(row["name"]),
            data=_decode_event_data(row["data"]),
        )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> EvidenceRecord:
        verified = row["verified"]
        if verified not in (0, 1):
            raise SQLiteTaskRepositoryDataError("stored evidence verification is invalid")
        return EvidenceRecord(
            evidence_id=_bounded_stored_string(
                row["evidence_id"],
                field="evidence identifier",
                maximum=100,
            ),
            kind=_decode_evidence_kind(row["kind"]),
            summary=_bounded_stored_string(
                row["summary"],
                field="evidence summary",
                maximum=_MAX_EVIDENCE_SUMMARY_LENGTH,
            ),
            source=_decode_evidence_source(row["source"]),
            verified=bool(verified),
        )

    @staticmethod
    def _plan_from_row(row: sqlite3.Row) -> ProposedPlan | None:
        values = (
            row["plan_revision"],
            row["plan_title"],
            row["plan_steps"],
            row["plan_evidence_refs"],
        )
        if all(value is None for value in values):
            return None
        if any(value is None for value in values):
            raise SQLiteTaskRepositoryDataError("stored plan is incomplete")
        revision = values[0]
        if (
            not isinstance(revision, int)
            or isinstance(revision, bool)
            or revision < 1
            or revision > MAX_PLAN_REVISION
        ):
            raise SQLiteTaskRepositoryDataError("stored plan revision is invalid")
        title = _bounded_stored_string(
            values[1],
            field="plan title",
            maximum=_MAX_PLAN_TITLE_LENGTH,
        )
        steps = _decode_string_tuple(values[2], field="plan steps")
        references = _decode_string_tuple(values[3], field="plan evidence references")
        _validate_steps(steps, stored=True)
        _validate_evidence_references(references, stored=True)
        return ProposedPlan(
            revision=revision,
            title=title,
            steps=steps,
            evidence_refs=references,
        )

    @staticmethod
    def _validate_cursor(event_id: int, event_count: int) -> None:
        if event_id < 0 or event_id > event_count:
            raise InvalidEventCursorError


def _safe_database_path(database_path: str | Path) -> Path:
    path = Path(database_path)
    if not path.is_absolute():
        raise SQLiteTaskRepositoryPathError(
            "local task database path must be explicit and absolute"
        )
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as error:
        raise SQLiteTaskRepositoryPathError(
            "local task database parent directory is unavailable"
        ) from error
    candidate = parent / path.name
    if not path.name or (candidate.exists() and (candidate.is_symlink() or candidate.is_dir())):
        raise SQLiteTaskRepositoryPathError("local task database path is unsafe")
    return candidate


def _validate_task_input(*, title: str, objective: str) -> None:
    if not title or len(title) > _MAX_TASK_TITLE_LENGTH:
        raise ValueError("task title is outside the shared response bound")
    if not objective or len(objective) > MAX_TASK_OBJECTIVE_LENGTH:
        raise ValueError("task objective is outside the shared request bound")


def _validate_steps(steps: tuple[str, ...], *, stored: bool = False) -> None:
    if not steps or len(steps) > MAX_PLAN_STEPS:
        _invalid_value("plan step count is outside the shared bound", stored=stored)
    for step in steps:
        if not isinstance(step, str) or not step.strip() or len(step) > MAX_PLAN_STEP_LENGTH:
            _invalid_value("plan step is outside the shared request bound", stored=stored)


def _encode_plan(plan: ProposedPlan) -> tuple[str, str]:
    _validate_plan_revision(plan.revision)
    if not plan.title or len(plan.title) > _MAX_PLAN_TITLE_LENGTH:
        raise ValueError("plan title is outside the shared response bound")
    _validate_steps(plan.steps)
    _validate_evidence_references(plan.evidence_refs)
    return _encode_string_tuple(plan.steps), _encode_string_tuple(plan.evidence_refs)


def _validate_plan_revision(revision: int) -> None:
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision < 1
        or revision > MAX_PLAN_REVISION
    ):
        raise PlanRevisionConflictError


def _validate_evidence(evidence: EvidenceRecord) -> None:
    if not evidence.evidence_id or len(evidence.evidence_id) > 100:
        raise ValueError("evidence identifier is outside the shared response bound")
    if not evidence.summary or len(evidence.summary) > _MAX_EVIDENCE_SUMMARY_LENGTH:
        raise ValueError("evidence summary is outside the shared response bound")


def _validate_evidence_references(
    references: tuple[str, ...],
    *,
    stored: bool = False,
) -> None:
    if any(not reference or len(reference) > 100 for reference in references):
        _invalid_value(
            "plan evidence reference is outside the shared response bound",
            stored=stored,
        )


def _plan_event_data(plan: ProposedPlan, evidence_class: EvidenceClass) -> EventData:
    return (
        ("title", plan.title),
        ("steps", plan.steps),
        ("revision", plan.revision),
        ("evidenceRefs", plan.evidence_refs),
        ("evidenceClass", evidence_class.value),
    )


def _encode_event_data(data: EventData) -> str:
    items: list[dict[str, object]] = []
    for key, value in data:
        if not isinstance(key, str) or not key:
            raise ValueError("event data key must be a non-empty string")
        value_type: str
        encoded_value: object
        if value is None:
            value_type = "none"
            encoded_value = None
        elif isinstance(value, bool):
            value_type = "bool"
            encoded_value = value
        elif isinstance(value, int):
            value_type = "int"
            encoded_value = value
        elif isinstance(value, str):
            value_type = "str"
            encoded_value = value
        elif isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            value_type = "strings"
            encoded_value = list(value)
        else:
            raise ValueError("event data value has an unsupported type")
        items.append({"key": key, "type": value_type, "value": encoded_value})
    return _canonical_json({"items": items, "version": 1})


def _decode_event_data(value: object) -> EventData:
    payload = _decode_canonical_json(value, field="event data")
    if not isinstance(payload, dict) or set(payload) != {"items", "version"}:
        raise SQLiteTaskRepositoryDataError("stored event data shape is invalid")
    if payload["version"] != 1 or not isinstance(payload["items"], list):
        raise SQLiteTaskRepositoryDataError("stored event data version is unsupported")
    decoded: list[tuple[str, EventDataValue]] = []
    for item in payload["items"]:
        if not isinstance(item, dict) or set(item) != {"key", "type", "value"}:
            raise SQLiteTaskRepositoryDataError("stored event data item is invalid")
        key = item["key"]
        value_type = item["type"]
        item_value = item["value"]
        if not isinstance(key, str) or not key or not isinstance(value_type, str):
            raise SQLiteTaskRepositoryDataError("stored event data item is invalid")
        decoded_value: EventDataValue
        if value_type == "none" and item_value is None:
            decoded_value = None
        elif value_type == "bool" and isinstance(item_value, bool):
            decoded_value = item_value
        elif (
            value_type == "int" and isinstance(item_value, int) and not isinstance(item_value, bool)
        ):
            decoded_value = item_value
        elif value_type == "str" and isinstance(item_value, str):
            decoded_value = item_value
        elif (
            value_type == "strings"
            and isinstance(item_value, list)
            and all(isinstance(element, str) for element in item_value)
        ):
            decoded_value = tuple(item_value)
        else:
            raise SQLiteTaskRepositoryDataError("stored event data value is invalid")
        decoded.append((key, decoded_value))
    return tuple(decoded)


def _encode_string_tuple(value: tuple[str, ...]) -> str:
    if not all(isinstance(item, str) for item in value):
        raise ValueError("stored string collection has an unsupported value")
    return _canonical_json(list(value))


def _decode_string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    payload = _decode_canonical_json(value, field=field)
    if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
        raise SQLiteTaskRepositoryDataError(f"stored {field} is invalid")
    return tuple(payload)


def _canonical_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(encoded.encode("utf-8")) > _MAX_SERIALIZED_BYTES:
        raise ValueError("serialized local task value exceeds the adapter bound")
    return encoded


def _decode_canonical_json(value: object, *, field: str) -> object:
    if not isinstance(value, str) or len(value.encode("utf-8")) > _MAX_SERIALIZED_BYTES:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is outside the adapter bound")
    try:
        decoded: object = json.loads(value)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is invalid") from error
    try:
        canonical = _canonical_json(decoded)
    except (TypeError, ValueError) as error:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is invalid") from error
    if canonical != value:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is not canonical")
    return decoded


def _bounded_stored_string(
    value: object,
    *,
    field: str,
    maximum: int,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or len(value) > maximum:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is outside its bound")
    return value


def _decode_status(value: object) -> TaskStatus:
    return _decode_enum(value, TaskStatus, field="task status")


def _decode_decision(value: object) -> DecisionValue:
    return _decode_enum(value, DecisionValue, field="decision")


def _decode_event_name(value: object) -> TaskEventName:
    return _decode_enum(value, TaskEventName, field="event name")


def _decode_evidence_kind(value: object) -> EvidenceKind:
    return _decode_enum(value, EvidenceKind, field="evidence kind")


def _decode_evidence_source(value: object) -> EvidenceSource:
    return _decode_enum(value, EvidenceSource, field="evidence source")


def _decode_enum[EnumT: StrEnum](
    value: object,
    enum_type: type[EnumT],
    *,
    field: str,
) -> EnumT:
    if not isinstance(value, str):
        raise SQLiteTaskRepositoryDataError(f"stored {field} is invalid")
    try:
        return enum_type(value)
    except ValueError as error:
        raise SQLiteTaskRepositoryDataError(f"stored {field} is unknown") from error


def _invalid_value(message: str, *, stored: bool) -> None:
    if stored:
        raise SQLiteTaskRepositoryDataError(f"stored {message}")
    raise ValueError(message)
