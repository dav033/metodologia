"""Deterministic subplan versioning and candidate composition over injected ports."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from collections.abc import Mapping, Sequence

from .contracts import Action, Candidate, EvidenceKey, GitPort, PropagationChange, StorePort, SubplanVersion

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_CONTRACT_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}@[1-9][0-9]{0,3}$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _candidate_manifest(candidate: Candidate) -> Candidate:
    body = {key: value for key, value in candidate.__dict__.items() if key != "manifest_sha256"}
    return replace(candidate, manifest_sha256=_sha(body))


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value) or value in {".", ".."}:
        raise ValueError(code)


class CompositionEngine:
    def __init__(self, git: GitPort, store: StorePort, workspace_root: str | Path):
        self.git = git
        self.store = store
        self.workspace_root = Path(workspace_root)

    @staticmethod
    def version_ref(plan_id: str, subplan_id: str, version: int) -> str:
        return f"refs/subplans/{plan_id}/{subplan_id}/v{version}"

    @staticmethod
    def candidate_ref(plan_id: str, candidate_id: str) -> str:
        return f"refs/compositions/{plan_id}/candidates/{candidate_id}"

    def publish_subplan_version(self, plan_id: str, plan_revision: str, subplan_id: str, commit: str,
                                line_base: str, contracts: Mapping[str, str], evidence: Sequence[Mapping[str, object]]) -> SubplanVersion:
        for value in (plan_id, subplan_id):
            _validate_identifier(value, "INVALID_IDENTIFIER")
        if not plan_revision or not commit or not line_base:
            raise ValueError("INVALID_VERSION_INPUT")
        if any(not isinstance(k, str) or not _CONTRACT_KEY.fullmatch(k) or not isinstance(v, str)
               or (v != "declared" and not _SHA256.fullmatch(v)) for k, v in contracts.items()):
            raise ValueError("INVALID_CONTRACT_HASHES")
        evidence_fields = ("task_id", "kind", "verdict_id", "tree_digest", "environment")
        for item in evidence:
            if not isinstance(item, Mapping) or any(not isinstance(item.get(field), str) or not item[field]
                                                     for field in evidence_fields):
                raise ValueError("INVALID_VERSION_EVIDENCE")
        request = {"plan_id": plan_id, "plan_revision": plan_revision, "subplan_id": subplan_id,
                   "commit": commit, "line_base": line_base, "contracts": dict(contracts),
                   "evidence": [dict(item) for item in evidence]}
        request_sha = _sha(request)
        existing = self.store.find_version(request_sha)
        if existing is not None:
            return existing
        version_number = self.store.next_version(plan_id, subplan_id)
        ref = self.version_ref(plan_id, subplan_id, version_number)
        manifest = {**request, "version": version_number}
        version = SubplanVersion(plan_id, plan_revision, subplan_id, version_number, commit, line_base,
                                 dict(contracts), tuple(dict(item) for item in evidence), _sha(manifest))
        ref_commit = self.git.rev_parse(ref)
        if ref_commit is None:
            self.git.update_refs(((ref, commit, None),))
        else:
            concurrent = self.store.find_version(request_sha)
            if concurrent is not None:
                return concurrent
            raise ValueError("SUBPLAN_VERSION_CONFLICT")
        self.store.put_version(version, request_sha)
        return version

    def build_candidate(self, plan_id: str, members: Mapping[str, int], *, run_base: str | None = None,
                        required_verdicts: Sequence[str] = ("M6",)) -> Candidate:
        _validate_identifier(plan_id, "INVALID_IDENTIFIER")
        if not members or any(type(version) is not int or version < 1 for version in members.values()):
            raise ValueError("INVALID_MEMBERS")
        for subplan in members:
            _validate_identifier(subplan, "INVALID_IDENTIFIER")
        required = tuple(sorted(set(required_verdicts)))
        if not required or any(not value for value in required):
            raise ValueError("REQUIRED_VERDICTS_MISSING")
        versions: dict[str, SubplanVersion] = {}
        for subplan, number in sorted(members.items()):
            version = self.store.get_version(plan_id, subplan, number)
            if version is None:
                raise ValueError("SUBPLAN_VERSION_MISSING")
            versions[subplan] = version
        current_ref = f"refs/compositions/{plan_id}/current"
        current_commit = self.git.rev_parse(current_ref)
        parent_candidate = self.store.candidate_for_commit(plan_id, current_commit) if current_commit else None
        parent = parent_candidate.id if parent_candidate else None
        if parent_candidate is not None:
            if not set(parent_candidate.members).issubset(members):
                raise ValueError("INVALID_MEMBERS")
            if run_base is None and dict(parent_candidate.members) == dict(members):
                return parent_candidate
        base = current_commit or run_base or versions[sorted(versions)[0]].line_base
        if not self.git.rev_parse(base):
            raise ValueError("COMPOSITION_BASE_MISSING")
        request_sha = _sha({"plan_id": plan_id, "members": dict(sorted(members.items())), "base": base,
                            "required_verdicts": required})
        existing = self.store.find_candidate(request_sha)
        if existing is not None:
            return existing
        previous_members = parent_candidate.members if parent_candidate else {}
        integrated = base
        conflicts: set[str] = set()
        for subplan, version_number in sorted(members.items()):
            if previous_members.get(subplan) == version_number:
                continue
            version = versions[subplan]
            result = self.git.merge_tree(version.line_base, integrated, version.commit)
            if result.conflicts:
                conflicts.update(result.conflicts)
                break
            if result.tree is None:
                raise RuntimeError("GIT_MERGE_TREE_FAILED")
            integrated = self.git.commit_tree(result.tree, (integrated, version.commit),
                                              f"compose {plan_id} {subplan}@v{version_number}")
        sequence = self.store.next_candidate(plan_id)
        candidate_id = f"C{sequence}"
        state = "rejected" if conflicts else "candidate"
        candidate = Candidate(candidate_id, plan_id, parent, dict(sorted(members.items())), base, integrated,
                              "", state, {}, required,
                              "git_text_conflict" if conflicts else None, tuple(sorted(conflicts)))
        candidate = _candidate_manifest(candidate)
        self.git.update_refs(((self.candidate_ref(plan_id, candidate_id), integrated, None),))
        self.store.put_candidate(candidate, request_sha)
        return candidate

    def open_workspace(self, candidate_id: str) -> str:
        candidate = self._candidate(candidate_id)
        if candidate.state not in ("candidate", "verifying"):
            raise ValueError("CANDIDATE_NOT_OPENABLE")
        return self.git.add_worktree(candidate.integrated_commit, self.workspace_root)

    def close_workspace(self, path: str | Path) -> None:
        self.git.remove_worktree(path)

    def publish(self, candidate_id: str, verdicts: Mapping[str, str]) -> bool:
        candidate = self._candidate(candidate_id)
        if candidate.state == "published":
            return True
        if candidate.state != "candidate":
            return False
        clean_verdicts = dict(verdicts)
        complete = all(clean_verdicts.get(name) == "PASS" for name in candidate.required_verdicts)
        if not complete:
            self.reject(candidate_id, {"verdicts": clean_verdicts})
            return False
        current_ref = f"refs/compositions/{candidate.plan_id}/current"
        published_ref = f"refs/compositions/{candidate.plan_id}/{candidate.id}"
        expected_current = None
        if candidate.parent is not None:
            parent = self.store.get_candidate(candidate.parent)
            if parent is None or parent.state != "published":
                raise RuntimeError("COMPOSITION_PARENT_MISSING")
            expected_current = parent.integrated_commit
        if self.git.rev_parse(current_ref) != expected_current:
            raise RuntimeError("COMPOSITION_CURRENT_MOVED")
        self.git.update_refs(((published_ref, candidate.integrated_commit, None),
                              (current_ref, candidate.integrated_commit, expected_current)))
        updated = _candidate_manifest(replace(candidate, state="published", verdicts=clean_verdicts))
        self.store.update_candidate(updated)
        return True

    def reject(self, candidate_id: str, evidence: Mapping[str, object]) -> Candidate:
        candidate = self._candidate(candidate_id)
        if candidate.state == "published":
            raise ValueError("PUBLISHED_COMPOSITION_IMMUTABLE")
        updated = _candidate_manifest(replace(
            candidate, state="rejected", verdicts={"evidence": _canonical(dict(evidence)).decode("utf-8")}))
        self.store.update_candidate(updated)
        return updated

    def _candidate(self, candidate_id: str) -> Candidate:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError("CANDIDATE_MISSING")
        return candidate


def reusable(old: EvidenceKey, new: EvidenceKey) -> bool:
    return (old.tree_digest == new.tree_digest and old.contracts == new.contracts
            and old.environment == new.environment)


def propagate(change: PropagationChange, consumers: Sequence[Mapping[str, object]],
              evidence: Sequence[Mapping[str, object]]) -> tuple[Action, ...]:
    actions: list[Action] = []
    for consumer in consumers:
        consumer_id = str(consumer.get("id", ""))
        if not consumer_id:
            raise ValueError("CONSUMER_ID_MISSING")
        if change.ancestry_only:
            actions.append(Action(consumer_id, "reverify", "ancestry_change_only"))
            continue
        finding = next((item for item in evidence if item.get("demonstrated") is True
                        and item.get("consumer") == consumer_id
                        and item.get("design_cannot_meet_contract") is True), None)
        if finding is not None:
            actions.append(Action(consumer_id, "reimplement", "demonstrated_design_failure"))
            continue
        if change.git_conflict:
            actions.append(Action(consumer_id, "reintegrate", "git_text_conflict"))
            continue
        failed = consumer.get("contract_test_executed") is True and consumer.get("contract_test_failed") is True
        if failed:
            operation = "adapt_contract" if change.producer_broke_declared_major else "modify"
            actions.append(Action(consumer_id, operation, "executed_contract_test_failed"))
        elif change.contract_major_changed:
            actions.append(Action(consumer_id, "reverify", "new_producer_contract_not_yet_verified"))
            if change.public_surface_changed:
                actions.append(Action(consumer_id, "audit", "public_surface_changed"))
        elif consumer.get("evidence_reusable") is not True:
            actions.append(Action(consumer_id, "reverify", "evidence_key_changed_or_unproven"))
    return tuple(actions)


__all__ = ["CompositionEngine", "propagate", "reusable"]
