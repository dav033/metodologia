"""Owner orchestration for accepted 1.3.0 subplans and composition gates.

All module state changes go through the M1 adapter. Git and composition persistence go through the
composition adapter. This runtime deliberately supports one repository role until cross-repository
candidate semantics have an explicit contract.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from pathlib import Path
from typing import Any

import bt_composition_adapter
import bt_scheduler_adapter as m1_adapter
import bt_scheduler_executor_adapter as m3_adapter
import bt_scheduler_quality_owner_adapter as m6_adapter
import bt_integration_line
from bt_scheduler_owner_errors import CompositionRuntimeError
from bt_scheduler_owner_propagation import OwnerPropagationMixin
from bt_scheduler_owner_validation import validate_contract_paths, validate_gate_chain
import bt_scheduler_owner_workspace


def composition_store_path(rdir: Path, project: str, req: str) -> Path:
    db = m1_adapter.run_db_path(Path(rdir))
    state_root = db.parent.parent if db.parent.name == "scheduler" else Path(rdir) / ".state"
    return state_root / "composition" / f"{project}-{req}.db"


class OwnerCompositionRuntime(OwnerPropagationMixin):
    def __init__(self, *, repository: Path, role: str, plan, project: str, req: str,
                 run_id: str, store_path: Path, workspace_root: Path, verifier_id: str):
        self.repository = Path(repository).resolve()
        self.role, self.plan, self.project, self.req, self.run_id = role, plan, project, req, run_id
        self.store_path, self.workspace_root = Path(store_path), Path(workspace_root)
        self.verifier_id = verifier_id
        self._m6_store = None
        self._quality_policy = None
        self._secure_store_location()
        self._secure_workspace_location()
        self.git = bt_composition_adapter.GitSubprocessPort(self.repository, self.workspace_root)
        self.engine, self.store = bt_composition_adapter.create_engine(
            self.repository, self.store_path, self.workspace_root, allow_owner_state=True)
        try:
            self._secure_store_file()
        except BaseException:
            self.store.close()
            raise
        self.scheduler = None
        self.candidates: dict[str, Any] = {}
        self._frontier_proposals: dict[str, dict[str, Any]] = {}
        self.attentions: list[tuple[str, str]] = []

    def _attend(self, identity: str, reason: object) -> None:
        item = (identity, str(reason))
        if item not in self.attentions:
            self.attentions.append(item)

    def drain_attentions(self) -> tuple[tuple[str, str], ...]:
        values = tuple(self.attentions)
        self.attentions.clear()
        return values

    @staticmethod
    def supports(plan) -> bool:
        return getattr(plan, "schema_version", "") == "1.3.0" and bool(getattr(plan, "subplans", ()))

    @classmethod
    def create(cls, *, rdir: Path, project: str, req: str, plan,
               repositories: dict[str, Path], verifier_id: str):
        if not cls.supports(plan):
            return None
        roles = set()
        for task in plan.tasks:
            role = task.repository
            if not role:
                raise CompositionRuntimeError("OWNER_COMPOSITION_REPOSITORY_UNKNOWN: task has no declared repository")
            roles.add(role)
        if len(roles) != 1:
            names = ", ".join(sorted(roles))
            raise CompositionRuntimeError(
                f"OWNER_COMPOSITION_MULTI_REPOSITORY_UNSUPPORTED: roles {names}; F4-9 has no cross-repository commit contract")
        role = next(iter(roles))
        repository = repositories.get(role)
        if repository is None or not Path(repository).is_dir():
            raise CompositionRuntimeError(f"OWNER_COMPOSITION_REPOSITORY_MISSING: registered role {role}")
        validate_contract_paths(plan)
        validate_gate_chain(plan)
        path = composition_store_path(rdir, project, req)
        state_root = composition_store_path(rdir, project, req).parent
        workspace_root = state_root / "workspaces" / f"{project}-{req}"
        return cls(repository=Path(repository), role=role, plan=plan, project=project, req=req,
                   run_id="", store_path=path,
                   workspace_root=workspace_root,
                   verifier_id=verifier_id)

    def _bind_identity(self) -> None:
        repository_id = str(self.repository)
        head = self.git.rev_parse("HEAD")
        if head is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_REPOSITORY_NOT_GIT")
        connection = sqlite3.connect(self.store_path)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE IF NOT EXISTS owner_identity ("
                                "project TEXT NOT NULL, req TEXT NOT NULL, plan_id TEXT NOT NULL, run_id TEXT NOT NULL, "
                                "revision INTEGER NOT NULL, plan_sha256 TEXT NOT NULL, repository TEXT NOT NULL, "
                                "repo_head TEXT NOT NULL, PRIMARY KEY(project, req, run_id, revision))")
            rows = connection.execute("SELECT DISTINCT project,req,plan_id,run_id,repository "
                                      "FROM owner_identity").fetchall()
            same_revision_runs = connection.execute(
                "SELECT run_id FROM owner_identity WHERE project=? AND req=? AND revision=?",
                (self.project, self.req, self.plan.revision)).fetchall()
            if (any(row[:2] != (self.project, self.req) or row[2] != self.plan.plan_id or row[4] != repository_id
                    for row in rows) or any(row[0] != self.run_id for row in same_revision_runs)):
                raise CompositionRuntimeError("OWNER_COMPOSITION_STORE_IDENTITY_MISMATCH")
            connection.execute("INSERT OR IGNORE INTO owner_identity VALUES (?,?,?,?,?,?,?,?)",
                               (self.project, self.req, self.plan.plan_id, self.run_id, self.plan.revision,
                                self.plan.sha256, repository_id, head))
            row = connection.execute("SELECT plan_sha256,repository FROM owner_identity "
                                     "WHERE project=? AND req=? AND run_id=? AND revision=?",
                                     (self.project, self.req, self.run_id, self.plan.revision)).fetchone()
            if row != (self.plan.sha256, repository_id):
                raise CompositionRuntimeError("OWNER_COMPOSITION_REVISION_IDENTITY_MISMATCH")
            connection.commit()
        finally:
            connection.close()

    def _secure_store_location(self) -> None:
        self.store_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        state_info = self.store_path.parent.parent.lstat()
        info = self.store_path.parent.lstat()
        if (not stat.S_ISDIR(state_info.st_mode) or stat.S_ISLNK(state_info.st_mode)
                or not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or info.st_uid != os.getuid()):
            raise CompositionRuntimeError("OWNER_COMPOSITION_STORE_DIRECTORY_UNSAFE")
        os.chmod(self.store_path.parent, 0o700, follow_symlinks=False)
        try:
            existing = self.store_path.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISREG(existing.st_mode) or existing.st_uid != os.getuid():
            raise CompositionRuntimeError("OWNER_COMPOSITION_STORE_FILE_UNSAFE")
        os.chmod(self.store_path, 0o600, follow_symlinks=False)

    def _secure_store_file(self) -> None:
        info = self.store_path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise CompositionRuntimeError("OWNER_COMPOSITION_STORE_FILE_UNSAFE")
        os.chmod(self.store_path, 0o600, follow_symlinks=False)

    def _secure_workspace_location(self) -> None:
        state_root = self.store_path.parent.parent.resolve()
        workspace = self.workspace_root
        if workspace != state_root and state_root not in workspace.parents:
            raise CompositionRuntimeError("OWNER_COMPOSITION_WORKSPACE_OUTSIDE_STATE")
        workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = workspace.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
            raise CompositionRuntimeError("OWNER_COMPOSITION_WORKSPACE_DIRECTORY_UNSAFE")
        os.chmod(workspace, 0o700, follow_symlinks=False)
        marker_path = workspace / ".owner.json"
        try:
            bt_scheduler_owner_workspace.ensure_owner_marker(
                marker_path, project=self.project, req=self.req, plan_id=self.plan.plan_id,
                revision=self.plan.revision, plan_sha256=self.plan.sha256)
        except ValueError as error:
            raise CompositionRuntimeError(str(error)) from None

    def bind_scheduler(self, scheduler) -> None:
        self.scheduler = scheduler
        self.run_id = m3_adapter.run_identity(scheduler)
        marker_path = self.workspace_root / ".owner.json"
        try:
            bt_scheduler_owner_workspace.bind_owner_marker(
                marker_path, project=self.project, req=self.req, plan_id=self.plan.plan_id,
                revision=self.plan.revision, plan_sha256=self.plan.sha256, run_id=self.run_id)
        except ValueError as error:
            raise CompositionRuntimeError(str(error)) from None
        self._bind_identity()
        self.engine.prune_workspaces()

    def close(self) -> None:
        self.store.close()

    def _line_commits(self, subplan_id: str) -> tuple[str | None, str | None]:
        line = bt_integration_line.Line.__new__(bt_integration_line.Line)
        line.identity = self.run_id
        line.scope_id = subplan_id
        line.ref_prefix = bt_integration_line.REF_PREFIX
        line_ref = line.ref(self.role)
        base, tip = self.git.rev_parse(line_ref + "-base"), self.git.rev_parse(line_ref)
        return base, tip

    def _m6_evidence(self, task_id: str, fact: dict[str, Any]) -> dict[str, str]:
        reference = fact.get("verdict_id")
        if not isinstance(reference, str) or not reference.startswith("m6://result/"):
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_EVIDENCE_MISSING")
        identity = m6_adapter.verified_result_identity(
            self._m6_store, reference, plan_id=self.plan.plan_id, revision=self.plan.revision,
            task_id=task_id, attempt_id=fact["attempt_id"], token=fact["token"], policy=self._quality_policy)
        if identity is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_EVIDENCE_UNAVAILABLE")
        return {"task_id": task_id, "kind": str(self.plan.task(task_id).meta.get("kind", "task")),
                "verdict_id": reference, **identity}

    def bind_m6_store(self, store) -> None:
        """Use the already-open M6 store through its public content-addressed evidence reader."""
        if not callable(getattr(store, "get_result_manifest", None)):
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_STORE_API_UNAVAILABLE")
        self._m6_store = store

    def bind_quality_policy(self, policy) -> None:
        self._quality_policy = policy

    def _read_m6_manifest(self, reference: str) -> bytes | None:
        if self._m6_store is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_STORE_UNBOUND")
        value = self._m6_store.get_result_manifest(reference)
        return value if isinstance(value, bytes) and len(value) <= 1024 * 1024 else None

    def reconcile_subplans(self) -> tuple[str, ...]:
        if self.scheduler is None:
            return ()
        statuses = m1_adapter.subplan_status(self.scheduler)
        facts = m1_adapter.accepted_attempt_facts(self.scheduler)
        published = []
        for subplan in self.plan.subplans:
            if statuses.get(subplan.id) == "published":
                continue
            if statuses.get(subplan.id) != "accepted":
                continue
            member_ids = {task.id for task in self.plan.tasks if task.meta.get("subplan_id") == subplan.id}
            if subplan.ui is not None:
                member_ids.update((subplan.ui.design_task, subplan.ui.visual_review_task))
            member_tasks = [task for task in self.plan.tasks if task.id in member_ids]
            if any(task.id not in facts for task in member_tasks):
                continue
            try:
                line_base, line_commit = self._line_commits(subplan.id)
                if line_base is None or line_commit is None:
                    self._attend(subplan.id, "OWNER_COMPOSITION_LINE_REF_MISSING")
                    continue
                evidence = tuple(self._m6_evidence(task.id, facts[task.id]) for task in member_tasks)
                line_tree = self.git.tree_oid(line_commit)
                if line_tree is None or any(item["tree_digest"] != line_tree for item in evidence):
                    self._attend(subplan.id, "OWNER_COMPOSITION_LINE_TREE_MISMATCH")
                    continue
                contracts = self._contract_hashes(subplan.id, line_commit)
                versions = self.store.list_versions(self.plan.plan_id, subplan.id)
                version = versions[-1] if versions and (
                    versions[-1].commit, versions[-1].line_base, versions[-1].contracts,
                    tuple(dict(item) for item in versions[-1].evidence)) == (
                    line_commit, line_base, contracts, tuple(dict(item) for item in evidence)) else None
                if version is None:
                    version = self.engine.publish_subplan_version(
                        self.plan.plan_id, f"r{self.plan.revision}:{self.plan.sha256}", subplan.id,
                        line_commit, line_base, contracts, evidence)
                m1_adapter.record_subplan_version(self.scheduler, subplan.id, version.version, version.commit,
                                                  version.manifest_sha256)
                published.append(subplan.id)
            except Exception as error:  # noqa: BLE001 - isolate one damaged subplan from the owner loop
                self._attend(subplan.id, getattr(error, "code", str(error) or type(error).__name__))
        return tuple(published)

    def _contract_hashes(self, subplan_id: str, commit: str) -> dict[str, str]:
        subplan = next(item for item in self.plan.subplans if item.id == subplan_id)
        contracts = {}
        for item in subplan.produces:
            key = f"{item['contract']}@{item['version']}"
            producer = self.plan.task(item["defined_by"])
            paths = tuple(producer.expected_paths)
            if subplan.ui is not None and item["contract"] == subplan.ui.contract:
                paths = (f"design/contracts/{subplan.ui.contract}@v{subplan.ui.version}.md",)
            hashes = {path: self.git.blob_sha256(commit, path) for path in paths}
            if not hashes or any(value is None for value in hashes.values()):
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_CONTRACT_HASH_UNAVAILABLE: {key}")
            contracts[key] = next(iter(hashes.values())) if len(hashes) == 1 else hashlib.sha256(
                json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if not contracts:
            raise CompositionRuntimeError(f"OWNER_COMPOSITION_CONTRACTS_UNDECLARED: {subplan_id}")
        return contracts

    def _members_for_gate(self, gate) -> tuple[dict[str, int], tuple[str, ...]]:
        versions = m1_adapter.subplan_publication_facts(self.scheduler)
        members = {subplan_id: versions[subplan_id]["version"] for subplan_id in gate.subplans
                   if subplan_id in versions and versions[subplan_id].get("revision") == self.plan.revision}
        if set(members) != set(gate.subplans):
            return {}, ()
        return members, tuple(subplan.id for subplan in self.plan.subplans if subplan.id in members)

    def _candidate_for_gate(self, task_id: str):
        if self.scheduler is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M1_UNAVAILABLE")
        gate = next((item for item in self.plan.composition_gates
                     if task_id in {item.task, getattr(item, "audit_task", None)}), None)
        if gate is None:
            return None
        members, _order = self._members_for_gate(gate)
        if not members:
            return None
        facts = m1_adapter.composition_facts(self.scheduler)
        reservation = next(((candidate_id, fact) for candidate_id, fact in facts.items()
                            if fact.get("members") == members), None)
        if reservation is None:
            return None
        candidate_id, _fact = reservation
        candidate = bt_composition_adapter.get_candidate(self.store, candidate_id)
        if candidate is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_RESERVED_CANDIDATE_MISSING")
        self.candidates[task_id] = candidate
        return candidate

    def _hold_composition_gate(self, task_id: str, composition_id: str | None, reason: str) -> None:
        if self.scheduler is None:
            return
        if not composition_id:
            members, _ = self._members_for_gate(next((gate for gate in self.plan.composition_gates
                                                       if gate.task == task_id), None))
            composition_id = next((candidate_id for candidate_id, fact in
                                   m1_adapter.composition_facts(self.scheduler).items()
                                   if fact.get("state") == "candidate" and fact.get("members") == members), None)
        m1_adapter.hold_composition_gate(self.scheduler, task_id, composition_id or "", str(reason)[:500])

    def reserve_candidates(self) -> tuple[str, ...]:
        """Build and durably reserve candidates before M1 can dispatch a gate task."""
        if self.scheduler is None:
            return ()
        reserved = []
        for gate in self.plan.composition_gates:
            try:
                if self._candidate_for_gate(gate.task) is not None:
                    continue
                members, order = self._members_for_gate(gate)
                if not members:
                    continue
                candidate = self.engine.build_candidate(self.plan.plan_id, members, member_order=order,
                                                        required_verdicts={"M6": self.verifier_id})
                tree = self.git.tree_oid(candidate.integrated_commit) if candidate.integrated_commit else ""
                m1_adapter.record_composition(self.scheduler, "candidate", candidate.id, candidate.members,
                                              candidate.manifest_sha256, tree_digest=tree or "")
                self.candidates[gate.task] = candidate
                reserved.append(candidate.id)
                if candidate.state == "rejected":
                    self.engine.reject(candidate.id, {"reason": candidate.reason_code or "git_text_conflict"})
                    m1_adapter.record_composition(self.scheduler, "rejected", candidate.id, candidate.members,
                                                  candidate.manifest_sha256,
                                                  candidate.reason_code or "git_text_conflict", tree_digest=tree or "")
                    self._attend(gate.task, "OWNER_COMPOSITION_CANDIDATE_REJECTED")
            except Exception as error:  # noqa: BLE001
                self._attend(gate.task, getattr(error, "code", str(error) or type(error).__name__))
        return tuple(reserved)

    def composition_base(self, task_id: str, _order=None) -> str | None:
        candidate = self._candidate_for_gate(task_id)
        return candidate.integrated_commit if candidate is not None else None

    def verification_identity(self, order) -> dict[str, Any] | None:
        candidate = self._candidate_for_gate(order.task_id)
        if candidate is None:
            return None
        versions = {subplan: self.store.get_version(self.plan.plan_id, subplan, number)
                    for subplan, number in candidate.members.items()}
        contracts = {key: value for version in versions.values() for key, value in version.contracts.items()}
        return {"composition_id": candidate.id, "manifest_sha256": candidate.manifest_sha256,
                "contract_identities": contracts}

    def reconcile_compositions(self) -> tuple[str, ...]:
        if self.scheduler is None:
            return ()
        accepted = m1_adapter.accepted_attempt_facts(self.scheduler)
        published = []
        for gate in self.plan.composition_gates:
            fact = accepted.get(gate.task)
            candidate_id = None
            # M1's manifest evidence names the immutable candidate; restart never rebuilds it.
            if fact is None:
                continue
            try:
                candidate_id = self._manifest_candidate_id(fact.get("verdict_id"))
                candidate = (bt_composition_adapter.get_candidate(self.store, candidate_id)
                             if candidate_id else None)
                if candidate is None:
                    self._hold_composition_gate(gate.task, candidate_id, "OWNER_COMPOSITION_CANDIDATE_UNAVAILABLE")
                    self._attend(gate.task, "OWNER_COMPOSITION_CANDIDATE_UNAVAILABLE")
                    continue
                composition_fact = m1_adapter.composition_facts(self.scheduler).get(candidate.id)
                current_members, _ = self._members_for_gate(gate)
                if composition_fact and composition_fact.get("state") == "published" \
                        and composition_fact.get("members") == current_members:
                    continue
                if gate.audit_task:
                    audit_fact = accepted.get(gate.audit_task)
                    if audit_fact is None:
                        continue
                    audit_proof = self._composition_proof(candidate, gate.audit_task, audit_fact,
                                                          audit_fact.get("verdict_id"))
                    if audit_proof is None or audit_proof.verdict != "PASS":
                        self._hold_composition_gate(gate.task, candidate.id,
                                                    "OWNER_COMPOSITION_AUDIT_PROOF_MISMATCH")
                        self._attend(gate.task, "OWNER_COMPOSITION_AUDIT_PROOF_MISMATCH")
                        continue
                proof = self._composition_proof(candidate, gate.task, fact, fact.get("verdict_id"))
                if proof is None:
                    self._hold_composition_gate(gate.task, candidate.id, "OWNER_COMPOSITION_PROOF_MISMATCH")
                    self._attend(gate.task, "OWNER_COMPOSITION_PROOF_MISMATCH")
                    continue
                if proof.verdict == "FAIL":
                    self.engine.reject(candidate.id, {"verdicts": {"M6": "FAIL"},
                                        "proofs": {"M6": {"verifier_id": self.verifier_id,
                                                          "evidence_id": proof.evidence_id}}})
                    m1_adapter.record_composition(self.scheduler, "rejected", candidate.id, candidate.members,
                                                  candidate.manifest_sha256, "M6_FAIL",
                                                  tree_digest=proof.evaluated_tree)
                    self._attend(gate.task, "OWNER_COMPOSITION_M6_FAIL")
                    continue
                if self.engine.publish(candidate.id, {"M6": proof}):
                    m1_adapter.record_composition(self.scheduler, "published", candidate.id, candidate.members,
                                                  candidate.manifest_sha256, tree_digest=proof.evaluated_tree)
                    published.append(candidate.id)
            except RuntimeError as error:
                if "COMPOSITION_CURRENT_MOVED" in str(error):
                    self._hold_composition_gate(gate.task, candidate_id, "COMPOSITION_CURRENT_MOVED")
                    self._attend(gate.task, "COMPOSITION_CURRENT_MOVED")
                    continue
                self._attend(gate.task, getattr(error, "code", str(error)))
            except Exception as error:  # noqa: BLE001
                self._attend(gate.task, getattr(error, "code", str(error) or type(error).__name__))
        return tuple(published)

    def _manifest_candidate_id(self, reference: object) -> str | None:
        if not isinstance(reference, str) or not reference.startswith("m6://result/"):
            return None
        raw = self._read_m6_manifest(reference)
        try:
            manifest = json.loads(raw) if raw else {}
            candidate_id = manifest.get("request", {}).get("composition_id")
            return candidate_id if isinstance(candidate_id, str) else None
        except (TypeError, ValueError):
            return None

    def _composition_proof(self, candidate, task_id: str, fact: dict[str, Any], reference: object):
        if not isinstance(reference, str) or not reference.startswith("m6://result/"):
            return None
        raw = self._read_m6_manifest(reference)
        if raw is None:
            return None
        try:
            manifest = json.loads(raw)
            request, evidence_input = manifest["request"], manifest["input"]
            tree = self.git.tree_oid(candidate.integrated_commit)
            contracts = self.verification_identity_for(candidate)
            environment_matches = (self._quality_policy is not None and m6_adapter.environment_fingerprint_matches(
                    self._quality_policy, contracts, request.get("environment_fingerprint"),
                    evidence_input.get("environment_fingerprint")))
            request_revision = request.get("revision")
            if (manifest.get("reason_code") not in {"PASS", "FAIL"} or
                    (request.get("plan_id"), request.get("task_id"), request.get("attempt_id"),
                     request.get("token")) != (self.plan.plan_id, task_id, fact["attempt_id"], fact["token"])
                    or type(request_revision) is not int or not 1 <= request_revision <= self.plan.revision
                    or request.get("attempt_id") != fact["attempt_id"]
                    or request.get("composition_id") != candidate.id
                    or request.get("manifest_sha256") != candidate.manifest_sha256
                    or request.get("contract_identities") != contracts
                    or evidence_input.get("composition_id") != candidate.id
                    or evidence_input.get("manifest_sha256") != candidate.manifest_sha256
                    or evidence_input.get("tree_digest") != tree
                    or evidence_input.get("contract_identities") != contracts or not environment_matches):
                return None
            verdict = manifest.get("reason_code")
            if verdict not in {"PASS", "FAIL"}:
                return None
            return bt_composition_adapter.VerdictProof(
                candidate.id, candidate.manifest_sha256, candidate.integrated_commit, tree, verdict,
                self.verifier_id, "sha256:" + reference.removeprefix("m6://result/"))
        except (KeyError, TypeError, ValueError):
            return None

    def verification_identity_for(self, candidate) -> dict[str, str]:
        versions = {subplan: self.store.get_version(self.plan.plan_id, subplan, number)
                    for subplan, number in candidate.members.items()}
        return {key: value for version in versions.values() for key, value in version.contracts.items()}

