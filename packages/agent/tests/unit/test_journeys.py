"""Deterministic fake-model tests for the research and writing journeys."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, cast

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import Field

from deepwork_agent import (
    PROTECTED_ACTION,
    JourneyProfile,
    JourneySubagent,
    create_journey_graph,
    initial_state,
    journey_capabilities,
    research_profile,
    validate_approval_response,
    writing_profile,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable, RunnableConfig

ToolDefinition = dict[str, Any] | type | Any
REVISED_PLAN_REVISION = 2


class ToolBindingFakeChatModel(GenericFakeChatModel):
    """Official fake model with the tool-binding method agents require."""

    bound_tool_names: set[str] = Field(default_factory=set)

    def bind_tools(
        self,
        tools: Sequence[ToolDefinition],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,  # noqa: ANN401 - mirrors the public BaseChatModel contract
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Record tool binding and remain a deterministic runnable."""
        _ = tool_choice, kwargs
        for candidate in tools:
            if isinstance(candidate, BaseTool):
                self.bound_tool_names.add(candidate.name)
            elif isinstance(candidate, dict):
                name = candidate.get("name")
                if isinstance(name, str):
                    self.bound_tool_names.add(name)
            else:
                name = getattr(candidate, "__name__", None)
                if isinstance(name, str):
                    self.bound_tool_names.add(name)
        return self


def _model(*messages: AIMessage | str) -> ToolBindingFakeChatModel:
    normalized = [
        AIMessage(content=message) if isinstance(message, str) else message for message in messages
    ]
    return ToolBindingFakeChatModel(messages=iter(normalized))


def _tool_call(name: str, args: dict[str, Any], call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def _artifact_call(call_id: str, **overrides: Any) -> AIMessage:  # noqa: ANN401 - test fixture
    args: dict[str, Any] = {
        "title": "Plan-first agents",
        "summary": "Short summary.",
        "body": "Full report body.",
        "claims": [
            {"text": "Cited claim.", "basis": "evidence", "evidence_ids": ["e1"]},
            {"text": "Reasoned claim.", "basis": "inference", "evidence_ids": []},
            {"text": "Open claim.", "basis": "unverified", "evidence_ids": []},
        ],
        "evidence": [
            {
                "evidence_id": "e1",
                "source_title": "Example source",
                "locator": "https://example.test/a",
                "observed_at": "2026-07-23T00:00:00Z",
            }
        ],
        "unresolved": ["Open claim needs a second source."],
    }
    args.update(overrides)
    return _tool_call("JourneyArtifactDraft", args, call_id)


def _grader_call(
    call_id: str,
    result: str,
    criteria: list[dict[str, Any]],
    explanation: str = "Verdict summary.",
) -> AIMessage:
    return _tool_call(
        "GraderResponse",
        {"result": result, "explanation": explanation, "criteria": criteria},
        call_id,
    )


def _satisfied_for(profile: JourneyProfile, call_id: str) -> AIMessage:
    criteria = [
        {"name": criterion.criterion_id, "passed": True} for criterion in profile.rubric.criteria
    ]
    return _grader_call(call_id, "satisfied", criteria)


def _run_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def _exhausted(model: ToolBindingFakeChatModel) -> bool:
    return next(model.messages, None) is None


def test_journey_capabilities_stay_truthful_about_unsupported_behavior() -> None:
    """Hosted artifacts, async subagents, and coding remain unavailable."""
    capabilities = journey_capabilities()

    assert capabilities.journeys == ("research", "writing")
    assert capabilities.coding_journey == "unavailable"
    assert capabilities.artifact_declaration == "structured-run-output"
    assert capabilities.artifact_bytes_owner == "caller"
    assert capabilities.hosted_artifact_storage is False
    assert capabilities.artifact_transfer == "unavailable"
    assert capabilities.subagents == "synchronous-in-process"
    assert capabilities.async_subagents == "unavailable"
    assert capabilities.verification == "rubric-middleware-bounded"
    assert capabilities.verification_ground_truth is False
    assert capabilities.verifier_ref == "deepagents:RubricMiddleware:0.6.12"
    assert capabilities.plan_approval == "langgraph-interrupt"
    assert capabilities.hosted_deployment is False
    assert capabilities.provider_credentials_managed is False


def test_research_journey_produces_artifact_provenance_and_passed_verification() -> None:
    """The full research path keeps the official approval boundary and labels claims."""
    profile = research_profile()
    model = _model(
        "- Gather evidence.\n- Draft the report.",
        _artifact_call("c1"),
    )
    verifier = _model(_satisfied_for(profile, "g1"))
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-passed")

    paused = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Research plan-first agents."), run_config),
    )

    assert paused["journey"] == "research"
    interrupts = paused["__interrupt__"]
    assert len(interrupts) == 1
    request = interrupts[0].value
    assert request["kind"] == "deepwork-plan-approval"
    assert request["action"] == PROTECTED_ACTION
    assert request["plan_trust"] == "untrusted"
    assert request["allowed_decisions"] == ["approve", "reject", "respond"]

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["status"] == "completed"
    artifact = result["artifact"]
    assert artifact["kind"] == "report"
    assert artifact["trust"] == "untrusted"
    assert [claim["basis"] for claim in artifact["claims"]] == [
        "evidence",
        "inference",
        "unverified",
    ]
    assert artifact["evidence"][0]["locator"] == "https://example.test/a"
    assert artifact["unresolved"] == ["Open claim needs a second source."]
    verification = result["verification"]
    assert verification["status"] == "passed"
    assert verification["rubric_id"] == "deepwork-research-default"
    assert verification["verifier_ref"] == "deepagents:RubricMiddleware:0.6.12"
    assert [entry["criterion_id"] for entry in verification["verdicts"][0]["results"]] == [
        "claims-labeled",
        "evidence-cited",
        "unresolved-disclosed",
        "report-complete",
    ]
    assert result["final_answer"] == "Short summary."
    assert result["final_answer_trust"] == "untrusted"
    assert _exhausted(model)
    assert _exhausted(verifier)


def test_repair_history_survives_a_pass_after_revision() -> None:
    """A failed first verdict stays visible after the repaired pass."""
    profile = research_profile()
    model = _model(
        "1. Gather evidence.\n2. Draft the report.",
        _artifact_call("c1", title="Draft one"),
        _artifact_call("c2", title="Draft two"),
    )
    verifier = _model(
        _grader_call(
            "g1",
            "needs_revision",
            [{"name": "evidence-cited", "passed": False, "gap": "Cite the claim."}],
        ),
        _satisfied_for(profile, "g2"),
    )
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-repaired")
    graph.invoke(initial_state("Research plan-first agents."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["artifact"]["title"] == "Draft two"
    verification = result["verification"]
    assert verification["status"] == "passed"
    assert verification["iterations_used"] == REVISED_PLAN_REVISION
    first, second = verification["verdicts"]
    assert first["verdict"] == "needs_revision"
    failed = {entry["criterion_id"]: entry for entry in first["results"]}["evidence-cited"]
    assert failed["outcome"] == "fail"
    assert failed["rationale_summary"] == "Cite the claim."
    assert second["verdict"] == "satisfied"


def test_iteration_cap_stops_the_repair_loop() -> None:
    """Two failing verdicts at max_iterations=2 end capped with no third run."""
    profile = research_profile(max_verification_iterations=2)
    model = _model(
        "1. Gather evidence.\n2. Draft the report.",
        _artifact_call("c1"),
        _artifact_call("c2"),
    )
    failing = [{"name": "evidence-cited", "passed": False, "gap": "Still uncited."}]
    verifier = _model(
        _grader_call("g1", "needs_revision", failing),
        _grader_call("g2", "needs_revision", failing),
    )
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-capped")
    graph.invoke(initial_state("Research plan-first agents."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["status"] == "completed"
    verification = result["verification"]
    assert verification["status"] == "capped"
    assert verification["status_reason"] == "iteration-cap-reached"
    assert verification["max_iterations"] == REVISED_PLAN_REVISION
    assert verification["iterations_used"] == REVISED_PLAN_REVISION
    last_results = {
        entry["criterion_id"]: entry["outcome"] for entry in verification["verdicts"][-1]["results"]
    }
    assert last_results["evidence-cited"] == "fail"
    assert _exhausted(model)
    assert _exhausted(verifier)


def test_grader_outage_reports_verification_error_not_a_pass() -> None:
    """Execution completes while a grader failure is reported as an error."""
    profile = research_profile()
    model = _model("1. Gather evidence.\n2. Draft the report.", _artifact_call("c1"))
    verifier = _model()
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-grader-error")
    graph.invoke(initial_state("Research plan-first agents."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["status"] == "completed"
    assert result["artifact"]["kind"] == "report"
    verification = result["verification"]
    assert verification["status"] == "error"
    assert verification["status_reason"] == "grader-error"
    assert verification["verdicts"][-1]["verdict"] == "grader_error"


def test_unsupported_citation_is_downgraded_in_the_final_artifact() -> None:
    """A fabricated citation is flagged and downgraded, never presented as cited."""
    profile = writing_profile()
    model = _model(
        "1. Outline.\n2. Draft.",
        _artifact_call(
            "c1",
            claims=[{"text": "Bold claim.", "basis": "evidence", "evidence_ids": ["ghost"]}],
        ),
    )
    verifier = _model(_satisfied_for(profile, "g1"))
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("writing-downgraded")
    graph.invoke(initial_state("Write the memo."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    artifact = result["artifact"]
    assert artifact["kind"] == "document"
    assert artifact["claims"][0]["basis"] == "unverified"
    assert artifact["claims"][0]["evidence_ids"] == []
    assert any("ghost" in flag for flag in artifact["citation_flags"])


def test_writing_journey_promotes_only_the_declared_artifact() -> None:
    """Working files written during the run never become the artifact."""
    profile = writing_profile()
    model = _model(
        "1. Outline.\n2. Draft.",
        _tool_call(
            "write_file",
            {"file_path": "/drafts/outline.md", "content": "- outline"},
            "c1",
        ),
        _artifact_call("c2", title="Final memo", body="Memo body."),
    )
    verifier = _model(_satisfied_for(profile, "g1"))
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("writing-working-files")
    graph.invoke(initial_state("Write the memo."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["artifact"]["title"] == "Final memo"
    assert "outline" not in result["artifact"]["body"]
    assert _exhausted(model)


def test_synchronous_subagent_runs_through_the_public_task_tool() -> None:
    """Profile subagents execute in-process through the pinned task tool."""
    profile = research_profile()
    model = _model(
        "1. Scout sources.\n2. Draft the report.",
        _tool_call(
            "task",
            {
                "description": "Collect sources about plan-first agents.",
                "subagent_type": "evidence-scout",
            },
            "c1",
        ),
        "Source S1: https://example.test/a, accessed 2026-07-23.",
        _artifact_call("c2"),
    )
    verifier = _model(_satisfied_for(profile, "g1"))
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-subagent")
    graph.invoke(initial_state("Research plan-first agents."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )

    assert result["status"] == "completed"
    assert result["artifact"]["evidence"][0]["evidence_id"] == "e1"
    assert "task" in model.bound_tool_names
    assert "JourneyArtifactDraft" in model.bound_tool_names
    assert _exhausted(model)


def test_rejection_ends_without_artifact_or_verification() -> None:
    """A rejected plan produces no artifact and no verdict placeholder."""
    model = _model("1. Gather evidence.\n2. Draft the report.")
    graph = create_journey_graph(model=model, profile=research_profile())
    run_config = _run_config("research-rejected")
    graph.invoke(initial_state("Research plan-first agents."), run_config)

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "reject"})),
        run_config,
    )

    assert result["status"] == "rejected"
    assert "artifact" not in result
    assert "verification" not in result
    assert result["final_answer"] == "Execution was not approved."
    assert result["final_answer_trust"] == "trusted"


def test_respond_replans_on_a_fresh_official_interrupt() -> None:
    """Reviewer guidance replans and pauses again before any execution."""
    profile = research_profile()
    model = _model(
        "1. Gather evidence.\n2. Draft the report.",
        "1. Use only supplied sources.\n2. Draft a two-paragraph report.",
        _artifact_call("c1"),
    )
    verifier = _model(_satisfied_for(profile, "g1"))
    graph = create_journey_graph(model=model, profile=profile, verifier_model=verifier)
    run_config = _run_config("research-respond")
    first_pause = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Research plan-first agents."), run_config),
    )

    second_pause = cast(
        "dict[str, Any]",
        graph.invoke(
            Command(
                resume=validate_approval_response(
                    {"decision": "respond", "comment": "Use only supplied sources."}
                )
            ),
            run_config,
        ),
    )

    assert second_pause["plan_revision"] == REVISED_PLAN_REVISION
    assert second_pause["__interrupt__"][0].id != first_pause["__interrupt__"][0].id
    completed = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )
    assert completed["status"] == "completed"
    assert completed["verification"]["status"] == "passed"


def test_journey_graph_requires_initialized_chat_models() -> None:
    """Provider strings can never select credentials implicitly."""
    with pytest.raises(TypeError, match="initialized BaseChatModel"):
        create_journey_graph(
            model="provider:model",  # type: ignore[arg-type]
            profile=research_profile(),
        )
    with pytest.raises(TypeError, match="verifier_model must be an initialized"):
        create_journey_graph(
            model=_model(),
            profile=research_profile(),
            verifier_model="provider:model",  # type: ignore[arg-type]
        )


def test_subagent_declarations_have_no_provider_or_credential_surface() -> None:
    """Subagent declarations cannot smuggle a provider or credential choice."""
    field_names = {field.name for field in dataclasses.fields(JourneySubagent)}

    assert field_names == {"name", "description", "instructions"}
    with pytest.raises(ValueError, match="lowercase text"):
        JourneySubagent(name="Bad Name", description="d", instructions="i")
    with pytest.raises(ValueError, match="1 to 2000 characters"):
        JourneySubagent(name="ok", description="", instructions="i")


def test_profiles_are_validated_and_immutable() -> None:
    """Profile coherence rules and the hard verification cap are enforced."""
    with pytest.raises(ValueError, match="between 1 and 5"):
        research_profile(max_verification_iterations=6)
    with pytest.raises(ValueError, match="research journeys declare a report artifact"):
        dataclasses.replace(research_profile(), artifact_kind="document")
    duplicate = writing_profile().subagents[0]
    with pytest.raises(ValueError, match="unique"):
        dataclasses.replace(writing_profile(), subagents=(duplicate, duplicate))
