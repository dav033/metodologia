"""Deterministic subplan versioning and candidate composition over injected ports."""
from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
from collections.abc import Mapping, Sequence

from .contracts import Action, Candidate, EvidenceKey, GitPort, PropagationChange, StorePort, SubplanVersion, VerdictProof

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_CONTRACT_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}@[1-9][0-9]{0,3}$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _candidate_manifest(candidate: Candidate) -> Candidate:
    immutable_fields = ("id", "plan_id", "parent", "members", "member_order", "base_commit", "integrated_commit",
                        "required_verdicts", "reason_code", "conflict_paths", "conflicts")
    body = {key: getattr(candidate, key) for key in immutable_fields}
    if candidate.required_verifiers is not None:
        body["required_verifiers"] = candidate.required_verifiers
    return replace(candidate, manifest_sha256=_sha(body))


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value) or value in {".", ".."}:
        raise ValueError(code)


class CompositionEngine:
    def __init__(self, git: GitPort, store: StorePort, workspace_root: str | Path):
        self.git = git
        self.store = store
        self.workspace_root = Path(workspace_root)
        self._transition_lock = threading.RLock()

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
        resolved_commit = self.git.rev_parse(commit)
        resolved_base = self.git.rev_parse(line_base)
        if resolved_commit is None or resolved_base is None:
            raise ValueError("INVALID_VERSION_COMMIT")
        if any(not isinstance(k, str) or not _CONTRACT_KEY.fullmatch(k) or not isinstance(v, str)
               or (v != "declared" and not _SHA256.fullmatch(v)) for k, v in contracts.items()):
            raise ValueError("INVALID_CONTRACT_HASHES")
        evidence_fields = ("task_id", "kind", "verdict_id", "tree_digest", "environment")
        for item in evidence:
            if not isinstance(item, Mapping) or any(not isinstance(item.get(field), str) or not item[field]
                                                     for field in evidence_fields):
                raise ValueError("INVALID_VERSION_EVIDENCE")
        request = {"plan_id": plan_id, "plan_revision": plan_revision, "subplan_id": subplan_id,
                   "commit": resolved_commit, "line_base": resolved_base, "contracts": dict(contracts),
                   "evidence": [dict(item) for item in evidence]}
        request_sha = _sha(request)
        existing = self.store.find_version(request_sha)
        if existing is not None:
            return existing
        with self.store.write_transaction():
            existing = self.store.find_version(request_sha)
            if existing is not None:
                return existing
            version = self.store.find_version_reservation(request_sha)
            created_reservation = version is None
            if version is None:
                version_number = self.store.next_version(plan_id, subplan_id)
                manifest = {**request, "version": version_number}
                version = SubplanVersion(plan_id, plan_revision, subplan_id, version_number, resolved_commit, resolved_base,
                                         dict(contracts), tuple(dict(item) for item in evidence), _sha(manifest),
                                         datetime.now(timezone.utc).isoformat())
                self.store.reserve_version(version, request_sha)
        ref = self.version_ref(plan_id, subplan_id, version.version)
        ref_commit = self.git.rev_parse(ref)
        if ref_commit is not None and created_reservation:
            if ref_commit != version.commit:
                raise ValueError("SUBPLAN_VERSION_CONFLICT")
            raise ValueError("SUBPLAN_VERSION_REF_UNOWNED")
        if ref_commit is None:
            try:
                self.git.update_refs(((ref, version.commit, None),))
            except Exception:
                if self.git.rev_parse(ref) != version.commit:
                    raise
        elif ref_commit != version.commit:
            raise ValueError("SUBPLAN_VERSION_CONFLICT")
        with self.store.write_transaction():
            existing = self.store.find_version(request_sha)
            if existing is not None:
                return existing
            self.store.complete_version(version, request_sha)
        return version

    def build_candidate(self, plan_id: str, members: Mapping[str, int], *, run_base: str | None = None,
                        required_verdicts: Sequence[str] | Mapping[str, str] = ("M6",),
                        member_order: Sequence[str] | None = None) -> Candidate:
        _validate_identifier(plan_id, "INVALID_IDENTIFIER")
        if not members or any(type(version) is not int or version < 1 for version in members.values()):
            raise ValueError("INVALID_MEMBERS")
        for subplan in members:
            _validate_identifier(subplan, "INVALID_IDENTIFIER")
        if isinstance(required_verdicts, Mapping):
            required_verifiers = dict(required_verdicts)
            required = tuple(sorted(required_verifiers))
        else:
            required = tuple(sorted(set(required_verdicts)))
            required_verifiers = {name: name for name in required}
        if not required or any(not value for value in required):
            raise ValueError("REQUIRED_VERDICTS_MISSING")
        if any(not isinstance(key, str) or not key or not isinstance(value, str) or not value
               for key, value in required_verifiers.items()):
            raise ValueError("REQUIRED_VERDICTS_MISSING")
        versions: dict[str, SubplanVersion] = {}
        if member_order is None and len(members) > 1:
            raise ValueError("MEMBER_ORDER_REQUIRED")
        order = tuple(member_order) if member_order is not None else tuple(members)
        if len(order) != len(members) or set(order) != set(members):
            raise ValueError("INVALID_MEMBERS")
        for subplan in order:
            number = members[subplan]
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
            if any(members.get(subplan, 0) < version for subplan, version in parent_candidate.members.items()):
                raise ValueError("INVALID_MEMBERS")
            if run_base is None and dict(parent_candidate.members) == dict(members):
                return parent_candidate
        base = current_commit or run_base or versions[order[0]].line_base
        resolved_base = self.git.rev_parse(base)
        if not resolved_base:
            raise ValueError("COMPOSITION_BASE_MISSING")
        base = resolved_base
        request_sha = _sha({"plan_id": plan_id, "members": {key: members[key] for key in order}, "base": base,
                            "required_verdicts": required, "required_verifiers": required_verifiers, "order": order})
        existing = self.store.find_candidate(request_sha)
        if existing is not None:
            return existing
        reservation = self.store.find_candidate_reservation(request_sha)
        if reservation is not None:
            return self._complete_candidate_reservation(reservation, request_sha)
        previous_members = parent_candidate.members if parent_candidate else {}
        integrated = base
        conflicts: set[str] = set()
        member_conflicts: dict[str, tuple[str, ...]] = {}
        rejected_deltas: list[tuple[str, set[str]]] = []
        applied_deltas: list[tuple[str, set[str]]] = []
        for subplan in order:
            version_number = members[subplan]
            if previous_members.get(subplan) == version_number:
                continue
            version = versions[subplan]
            result = self.git.merge_tree(version.line_base, integrated, version.commit)
            delta_paths = set(self.git.diff_paths(version.line_base, version.commit))
            for rejected_member, rejected_paths in rejected_deltas:
                overlap = delta_paths & rejected_paths
                if overlap:
                    conflicts.update(overlap)
                    member_conflicts[rejected_member] = tuple(sorted(
                        set(member_conflicts.get(rejected_member, ())) | overlap))
                    member_conflicts[subplan] = tuple(sorted(
                        set(member_conflicts.get(subplan, ())) | overlap))
            if result.conflicts:
                conflicts.update(result.conflicts)
                member_conflicts[subplan] = tuple(sorted(set(result.conflicts)))
                for applied_member, applied_paths in applied_deltas:
                    overlap = applied_paths & set(result.conflicts)
                    if overlap:
                        member_conflicts[applied_member] = tuple(sorted(
                            set(member_conflicts.get(applied_member, ())) | overlap))
                rejected_deltas.append((subplan, delta_paths))
                continue
            if result.tree is None:
                raise RuntimeError("GIT_MERGE_TREE_FAILED")
            integrated = self.git.commit_tree(result.tree, (integrated, version.commit),
                                              f"compose {plan_id} {subplan}@v{version_number}")
            applied_deltas.append((subplan, delta_paths))
        with self.store.write_transaction():
            existing = self.store.find_candidate(request_sha)
            if existing is not None:
                return existing
            reservation = self.store.find_candidate_reservation(request_sha)
            if reservation is None:
                sequence = self.store.next_candidate(plan_id)
                while self.git.rev_parse(self.candidate_ref(plan_id, f"C{sequence}")) is not None:
                    sequence += 1
                candidate_id = f"C{sequence}"
                state = "rejected" if conflicts else "candidate"
                candidate = Candidate(candidate_id, plan_id, parent, dict(members), base, integrated,
                                      "", state, {}, required,
                                      "git_text_conflict" if conflicts else None, tuple(sorted(conflicts)), member_conflicts,
                                      order, required_verifiers)
                reservation = _candidate_manifest(candidate)
                self.store.reserve_candidate(reservation, request_sha)
        return self._complete_candidate_reservation(reservation, request_sha)

    def _complete_candidate_reservation(self, candidate: Candidate, request_sha: str) -> Candidate:
        ref = self.candidate_ref(candidate.plan_id, candidate.id)
        ref_commit = self.git.rev_parse(ref)
        if ref_commit is not None and ref_commit != candidate.integrated_commit:
            raise ValueError("COMPOSITION_CANDIDATE_CONFLICT")
        if ref_commit is None:
            self.git.update_refs(((ref, candidate.integrated_commit, None),))
        with self.store.write_transaction():
            existing = self.store.find_candidate(request_sha)
            if existing is not None:
                return existing
            self.store.complete_candidate(candidate, request_sha)
        return candidate

    def open_workspace(self, candidate_id: str) -> str:
        candidate = self._candidate(candidate_id)
        if candidate.state not in ("candidate", "verifying"):
            raise ValueError("CANDIDATE_NOT_OPENABLE")
        if candidate.state == "candidate":
            candidate = _candidate_manifest(replace(candidate, state="verifying"))
            self.store.update_candidate(candidate)
        return self.git.add_worktree(candidate.integrated_commit, self.workspace_root)

    def close_workspace(self, path: str | Path) -> None:
        self.git.remove_worktree(path)

    def prune_workspaces(self) -> tuple[str, ...]:
        return self.git.prune_workspaces()

    def publish(self, candidate_id: str, verdicts: Mapping[str, VerdictProof]) -> bool:
        with self._transition_lock:
            with self.store.write_transaction():
                return self._publish(candidate_id, verdicts)

    def _publish(self, candidate_id: str, verdicts: Mapping[str, VerdictProof]) -> bool:
        candidate = self._candidate(candidate_id)
        if candidate.state == "published":
            published_ref = f"refs/compositions/{candidate.plan_id}/{candidate.id}"
            if self.git.rev_parse(published_ref) == candidate.integrated_commit:
                return True
            raise RuntimeError("COMPOSITION_PUBLISHED_REF_MISSING")
        if candidate.state not in ("candidate", "verifying"):
            return False
        clean_verdicts: dict[str, str] = {}
        proofs: dict[str, dict[str, str]] = {}
        for name in candidate.required_verdicts:
            proof = verdicts.get(name)
            if (not isinstance(proof, VerdictProof) or proof.candidate_id != candidate.id
                    or proof.manifest_sha256 != candidate.manifest_sha256
                    or proof.evaluated_commit != candidate.integrated_commit
                    or proof.evaluated_tree != self.git.tree_oid(candidate.integrated_commit)
                    or proof.verdict not in {"PASS", "FAIL"}
                    or proof.verifier_id != (candidate.required_verifiers or {}).get(name, name)
                    or not isinstance(proof.evidence_id, str)
                    or not re.fullmatch(r"sha256:[0-9a-f]{64}", proof.evidence_id)):
                raise ValueError("VERDICT_PROOF_INVALID")
            clean_verdicts[name] = proof.verdict
            proofs[name] = {"verdict": proof.verdict, "verifier_id": proof.verifier_id, "evidence_id": proof.evidence_id}
        complete = all(clean_verdicts.get(name) == "PASS" for name in candidate.required_verdicts)
        if not complete:
            self._reject(candidate_id, {"verdicts": clean_verdicts, "proofs": proofs})
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
            if (self.git.rev_parse(current_ref) == candidate.integrated_commit
                    and self.git.rev_parse(published_ref) == candidate.integrated_commit):
                updated = _candidate_manifest(replace(candidate, state="published", verdicts=clean_verdicts, verdict_proofs=proofs))
                self.store.update_candidate(updated)
                return True
            raise RuntimeError("COMPOSITION_CURRENT_MOVED")
        published_commit = self.git.rev_parse(published_ref)
        current_commit = self.git.rev_parse(current_ref)
        if published_commit is None or current_commit != candidate.integrated_commit:
            self.git.update_refs(((published_ref, candidate.integrated_commit, None),
                                  (current_ref, candidate.integrated_commit, expected_current)))
        updated = _candidate_manifest(replace(candidate, state="published", verdicts=clean_verdicts, verdict_proofs=proofs))
        self.store.update_candidate(updated)
        return True

    def reject(self, candidate_id: str, evidence: Mapping[str, object]) -> Candidate:
        with self._transition_lock:
            with self.store.write_transaction():
                candidate = self._reject(candidate_id, evidence)
            if candidate.state == "published":
                raise ValueError("PUBLISHED_COMPOSITION_IMMUTABLE")
            return candidate

    def _reject(self, candidate_id: str, evidence: Mapping[str, object]) -> Candidate:
        candidate = self._candidate(candidate_id)
        if candidate.state != "published":
            published_ref = f"refs/compositions/{candidate.plan_id}/{candidate.id}"
            current_ref = f"refs/compositions/{candidate.plan_id}/current"
            if (self.git.rev_parse(published_ref) == candidate.integrated_commit
                    and self.git.rev_parse(current_ref) == candidate.integrated_commit):
                candidate = _candidate_manifest(replace(candidate, state="published"))
                self.store.update_candidate(candidate)
        if candidate.state == "published":
            return candidate
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
    return (_valid_paths(old.paths) and _valid_paths(new.paths)
            and old.tree_digest == new.tree_digest and old.contracts == new.contracts
            and old.environment == new.environment and tuple(sorted(old.paths)) == tuple(sorted(new.paths)))


def _valid_paths(paths: Sequence[str]) -> bool:
    if not paths:
        return False
    for path in paths:
        if not isinstance(path, str) or not path or "\\" in path:
            return False
        pure = PurePosixPath(path)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in path.split("/")):
            return False
        if pure.as_posix() != path:
            return False
    return True


def propagate(change: PropagationChange, consumers: Sequence[Mapping[str, object]],
              evidence: Sequence[Mapping[str, object]]) -> tuple[Action, ...]:
    actions: list[Action] = []
    for consumer in consumers:
        consumer_id = str(consumer.get("id", ""))
        if not consumer_id:
            raise ValueError("CONSUMER_ID_MISSING")
        old_key = consumer.get("old_evidence_key")
        new_key = consumer.get("new_evidence_key")
        has_keys = isinstance(old_key, EvidenceKey) and isinstance(new_key, EvidenceKey)
        evidence_is_reusable = reusable(old_key, new_key) if has_keys else False
        if change.ancestry_only:
            if evidence_is_reusable:
                continue
            actions.append(Action(consumer_id, "reverify", "ancestry_change_only"))
            continue
        finding = next((item for item in evidence if item.get("demonstrated") is True
                        and item.get("consumer") == consumer_id
                        and item.get("design_cannot_meet_contract") is True), None)
        if finding is not None:
            actions.append(Action(consumer_id, "reimplement", "demonstrated_design_failure"))
            continue
        conflict_paths = consumer.get("conflict_paths", ())
        has_conflict = consumer_id in change.conflicting_members or bool(conflict_paths)
        if change.git_conflict and has_conflict:
            paths = ",".join(str(path) for path in conflict_paths)
            actions.append(Action(consumer_id, "reintegrate", f"git_text_conflict:{paths}" if paths else "git_text_conflict"))
            continue
        old_contracts = old_key.contracts if isinstance(old_key, EvidenceKey) else {}
        new_contracts = new_key.contracts if isinstance(new_key, EvidenceKey) else {}
        changed_contracts = {key for key in set(old_contracts) | set(new_contracts)
                             if old_contracts.get(key) != new_contracts.get(key)}
        contract_changed = bool(changed_contracts)
        current_version = consumer.get("current_producer_version")
        evidence_version = consumer.get("evidence_producer_version")
        current_manifest = consumer.get("current_producer_manifest")
        evidence_manifest = consumer.get("evidence_producer_manifest")
        evidence_is_current = (current_version is not None and evidence_version == current_version
                               and current_manifest is not None and evidence_manifest == current_manifest)
        failed = (consumer.get("contract_test_executed") is True
                  and consumer.get("contract_test_failed") is True)
        failed = failed and evidence_is_current
        if failed:
            operation = "adapt_contract" if change.producer_broke_declared_major else "modify"
            actions.append(Action(consumer_id, operation, "executed_contract_test_failed"))
        elif contract_changed:
            actions.append(Action(consumer_id, "reverify", "new_producer_contract_not_yet_verified"))
            if change.public_surface_changed:
                actions.append(Action(consumer_id, "audit", "public_surface_changed"))
        elif has_keys and evidence_is_reusable:
            continue
        elif not has_keys or not evidence_is_reusable:
            actions.append(Action(consumer_id, "reverify", "evidence_key_changed_or_unproven"))
    return tuple(actions)


__all__ = ["CompositionEngine", "propagate", "reusable"]
