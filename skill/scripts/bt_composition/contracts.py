"""Public data contracts and ports for candidate composition."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class GitResult:
    tree: str | None
    conflicts: tuple[str, ...] = ()


class GitPort(Protocol):
    def rev_parse(self, revision: str) -> str | None: ...
    def tree_oid(self, commit: str) -> str | None: ...
    def merge_tree(self, base: str, ours: str, theirs: str) -> GitResult: ...
    def commit_tree(self, tree: str, parents: Sequence[str], message: str) -> str: ...
    def update_refs(self, updates: Sequence[tuple[str, str | None, str | None]]) -> None: ...
    def tree_digest(self, commit: str, paths: Sequence[str]) -> str: ...
    def diff_paths(self, a: str, b: str) -> tuple[str, ...]: ...
    def add_worktree(self, commit: str, parent: str | Path) -> str: ...
    def remove_worktree(self, path: str | Path) -> None: ...
    def prune_workspaces(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class SubplanVersion:
    plan_id: str
    plan_revision: str
    subplan_id: str
    version: int
    commit: str
    line_base: str
    contracts: dict[str, str]
    evidence: tuple[dict[str, object], ...]
    manifest_sha256: str
    published_at: str | None = None


@dataclass(frozen=True)
class Candidate:
    id: str
    plan_id: str
    parent: str | None
    members: dict[str, int]
    base_commit: str
    integrated_commit: str
    manifest_sha256: str
    state: str
    verdicts: dict[str, str]
    required_verdicts: tuple[str, ...]
    reason_code: str | None = None
    conflict_paths: tuple[str, ...] = ()
    conflicts: dict[str, tuple[str, ...]] | None = None
    member_order: tuple[str, ...] = ()
    required_verifiers: dict[str, str] | None = None
    verdict_proofs: dict[str, dict[str, str]] | None = None  # who proved each verdict; not part of the manifest


@dataclass(frozen=True)
class VerdictProof:
    candidate_id: str
    manifest_sha256: str
    evaluated_commit: str
    evaluated_tree: str
    verdict: str
    verifier_id: str
    evidence_id: str


@dataclass(frozen=True)
class EvidenceKey:
    tree_digest: str
    contracts: dict[str, str]
    environment: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class PropagationChange:
    producer: str
    ancestry_only: bool = False
    contract_major_changed: bool = False
    public_surface_changed: bool = False
    git_conflict: bool = False
    producer_broke_declared_major: bool = False
    conflicting_members: tuple[str, ...] = ()


@dataclass(frozen=True)
class Action:
    consumer: str
    operation: str
    reason: str


class StorePort(Protocol):
    def write_transaction(self) -> AbstractContextManager[None]: ...
    def next_version(self, plan_id: str, subplan_id: str) -> int: ...
    def get_version(self, plan_id: str, subplan_id: str, version: int) -> SubplanVersion | None: ...
    def find_version(self, request_sha256: str) -> SubplanVersion | None: ...
    def find_version_reservation(self, request_sha256: str) -> SubplanVersion | None: ...
    def reserve_version(self, version: SubplanVersion, request_sha256: str) -> None: ...
    def complete_version(self, version: SubplanVersion, request_sha256: str) -> None: ...
    def list_versions(self, plan_id: str, subplan_id: str) -> tuple[SubplanVersion, ...]: ...
    def get_candidate(self, candidate_id: str) -> Candidate | None: ...
    def candidate_for_commit(self, plan_id: str, commit: str) -> Candidate | None: ...
    def find_candidate(self, request_sha256: str) -> Candidate | None: ...
    def next_candidate(self, plan_id: str) -> int: ...
    def put_candidate(self, candidate: Candidate, request_sha256: str) -> None: ...
    def update_candidate(self, candidate: Candidate) -> None: ...


__all__ = ["Action", "Candidate", "EvidenceKey", "GitPort", "GitResult", "PropagationChange", "StorePort",
           "SubplanVersion", "VerdictProof"]
