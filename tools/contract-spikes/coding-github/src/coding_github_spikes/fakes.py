"""Deterministic fake Git/API/webhook evidence producers."""

from __future__ import annotations

from dataclasses import dataclass, field

from coding_github_spikes.contracts import ContractDenied, MutationLedger


@dataclass
class FakeGitHub:
    """A tiny stateful fake that refuses overwrite, force push, and duplicate PRs."""

    base_sha: str
    refs: dict[str, str] = field(default_factory=dict)
    prs: dict[tuple[str, str], dict[str, object]] = field(default_factory=dict)
    calls: list[dict[str, object]] = field(default_factory=list)

    def create_ref(self, ref: str, sha: str) -> str:
        self.calls.append({"operation": "create_ref", "ref": ref, "sha": sha})
        if ref in self.refs and self.refs[ref] != sha:
            raise ContractDenied("unknown ref collision; overwrite denied")
        self.refs.setdefault(ref, sha)
        return self.refs[ref]

    def push(self, ref: str, old_sha: str, new_sha: str, *, force: bool = False) -> str:
        self.calls.append({"operation": "push", "ref": ref, "force": force})
        if force:
            raise ContractDenied("force push denied")
        if self.refs.get(ref) != old_sha:
            raise ContractDenied("non-fast-forward or stale head")
        self.refs[ref] = new_sha
        return new_sha

    def create_draft_pr(
        self, *, base: str, head: str, head_sha: str, ledger: MutationLedger
    ) -> dict[str, object]:
        key = (base, head)
        if key in self.prs:
            return self.prs[key]
        ledger.before_create()
        identity = f"PR_{len(self.prs) + 1}"
        pr = {
            "node_id": identity,
            "number": len(self.prs) + 1,
            "draft": True,
            "base": base,
            "head": head,
            "head_sha": head_sha,
        }
        self.prs[key] = pr
        ledger.record_remote_result(identity)
        self.calls.append({"operation": "create_draft_pr", "identity": identity})
        return pr

