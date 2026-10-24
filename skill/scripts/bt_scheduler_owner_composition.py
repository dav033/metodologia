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
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import bt_composition_adapter
import bt_scheduler_adapter as m1_adapter
import bt_scheduler_executor_adapter as m3_adapter
import bt_scheduler_quality_owner_adapter as m6_adapter


class CompositionRuntimeError(RuntimeError):
    pass


def _propagation_change_id(composition_id: str, manifest_sha256: str, evidence_ids: tuple[str, ...],
                           consumer: str, action: str, reason: str) -> str:
    value = {"composition_id": composition_id, "manifest_sha256": manifest_sha256,
             "evidence_ids": sorted(evidence_ids), "consumer": consumer, "action": action, "reason": reason}
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return "cp-" + digest


def _opaque_evidence_ref(value: str) -> str:
    match = re.fullmatch(r"(?:m6://result/|sha256:)([0-9a-f]{64})", value)
    digest = match.group(1) if match else hashlib.sha256(value.encode("utf-8")).hexdigest()
    return "m6:" + digest


def composition_store_path(rdir: Path, project: str, req: str) -> Path:
    db = m1_adapter.run_db_path(Path(rdir))
    state_root = db.parent.parent if db.parent.name == "scheduler" else Path(rdir) / ".state"
    return state_root / "composition" / f"{project}-{req}.db"


class OwnerCompositionRuntime:
    def __init__(self, *, repository: Path, role: str, plan, project: str, req: str,
                 run_id: str, store_path: Path, workspace_root: Path, verifier_id: str):
        self.repository = Path(repository).resolve()
        self.role, self.plan, self.project, self.req, self.run_id = role, plan, project, req, run_id
        self.store_path, self.workspace_root = Path(store_path), Path(workspace_root)
        self.verifier_id = verifier_id
        self._m6_store = None
        self._quality_policy = None
        self._secure_store_location()
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
        path = composition_store_path(rdir, project, req)
        return cls(repository=Path(repository), role=role, plan=plan, project=project, req=req,
                   run_id="", store_path=path,
                   workspace_root=Path(tempfile.gettempdir()) / "bt-composition-owner" / project / req,
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
            if any(row[:2] != (self.project, self.req) or row[2] != self.plan.plan_id
                   or row[3] != self.run_id or row[4] != repository_id for row in rows):
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

    def bind_scheduler(self, scheduler) -> None:
        self.scheduler = scheduler
        self.run_id = m3_adapter.run_identity(scheduler)
        self._bind_identity()
        self.engine.prune_workspaces()

    def close(self) -> None:
        self.store.close()

    def _line_commits(self, subplan_id: str) -> tuple[str | None, str | None]:
        run_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", self.run_id).strip("-") or "run"
        role_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", self.role).strip("-")
        prefix = f"refs/m3/line/{run_ref}/{role_ref}/{subplan_id}"
        base, tip = self.git.rev_parse(prefix + "-base"), self.git.rev_parse(prefix)
        return base, tip

    def _m6_evidence(self, task_id: str, fact: dict[str, Any]) -> dict[str, str]:
        reference = fact.get("verdict_id")
        if not isinstance(reference, str) or not reference.startswith("m6://result/"):
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_EVIDENCE_MISSING")
        raw = self._read_m6_manifest(reference)
        if raw is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_EVIDENCE_UNAVAILABLE")
        try:
            manifest = json.loads(raw)
            request, evidence_input = manifest["request"], manifest["input"]
            identity_ok = (request["plan_id"], request["task_id"], request["attempt_id"], request["revision"],
                           request["token"]) == (self.plan.plan_id, task_id, fact["attempt_id"],
                                                  self.plan.revision, fact["token"])
            tree, environment = evidence_input.get("tree_digest"), evidence_input.get("environment_fingerprint")
            if (not identity_ok or manifest.get("reason_code") != "PASS"
                    or not isinstance(tree, str) or re.fullmatch(r"[0-9a-f]{40,64}", tree) is None
                    or not isinstance(environment, str) or re.fullmatch(r"[0-9a-f]{64}", environment) is None):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise CompositionRuntimeError("OWNER_COMPOSITION_M6_EVIDENCE_IDENTITY_MISMATCH") from None
        return {"task_id": task_id, "kind": str(self.plan.task(task_id).meta.get("kind", "task")),
                "verdict_id": reference, "tree_digest": tree, "environment": environment}

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
                    continue  # M3 may still be folding the last accepted handoff after restart/reconciliation.
                evidence = tuple(self._m6_evidence(task.id, facts[task.id]) for task in member_tasks)
                contracts = self._contract_hashes(subplan.id, line_commit)
                version = self.engine.publish_subplan_version(
                    self.plan.plan_id, f"r{self.plan.revision}:{self.plan.sha256}", subplan.id,
                    line_commit, line_base, contracts, evidence)
                m1_adapter.record_subplan_version(self.scheduler, subplan.id, version.version, version.commit,
                                                  version.manifest_sha256)
                published.append(subplan.id)
            except CompositionRuntimeError:
                raise
            except Exception as error:  # noqa: BLE001 - restart reconciliation retries durable boundaries
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_SUBPLAN_RECONCILE_FAILED: {type(error).__name__}") from None
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

    def _candidate_for_gate(self, task_id: str):
        if self.scheduler is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M1_UNAVAILABLE")
        gate = next((item for item in self.plan.composition_gates if item.task == task_id), None)
        if gate is None:
            return None
        versions = m1_adapter.subplan_publication_facts(self.scheduler)
        members = {subplan_id: versions[subplan_id]["version"] for subplan_id in gate.subplans
                   if subplan_id in versions and versions[subplan_id].get("revision") == self.plan.revision}
        if set(members) != set(gate.subplans):
            raise CompositionRuntimeError("OWNER_COMPOSITION_MEMBER_VERSION_STALE")
        order = tuple(subplan.id for subplan in self.plan.subplans if subplan.id in members)
        candidate = self.engine.build_candidate(self.plan.plan_id, members, member_order=order,
                                                required_verdicts={"M6": self.verifier_id})
        self.candidates[task_id] = candidate
        tree = (self.git.tree_oid(candidate.integrated_commit)
                if candidate.integrated_commit else "")
        facts = m1_adapter.composition_facts(self.scheduler)
        if candidate.id not in facts:
            m1_adapter.record_composition(self.scheduler, "candidate", candidate.id, candidate.members,
                                          candidate.manifest_sha256, tree_digest=tree or "")
        if candidate.state == "rejected":
            m1_adapter.record_composition(self.scheduler, "rejected", candidate.id, candidate.members,
                                          candidate.manifest_sha256,
                                          candidate.reason_code or "git_text_conflict", tree_digest=tree or "")
            raise CompositionRuntimeError("OWNER_COMPOSITION_CANDIDATE_REJECTED")
        return candidate

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
                "contract_identities": contracts,
                "environment_fingerprint": hashlib.sha256(b"composition-owner-env/1").hexdigest()}

    def reconcile_compositions(self) -> tuple[str, ...]:
        if self.scheduler is None:
            return ()
        accepted = m1_adapter.accepted_attempt_facts(self.scheduler)
        published = []
        for gate in self.plan.composition_gates:
            fact = accepted.get(gate.task)
            candidate = self._candidate_for_gate(gate.task) if fact else self.candidates.get(gate.task)
            if fact is None or candidate is None:
                continue
            if gate.audit_task:
                audit_fact = accepted.get(gate.audit_task)
                if audit_fact is None:
                    continue
                try:
                    self._m6_evidence(gate.audit_task, audit_fact)
                except CompositionRuntimeError:
                    continue
            reference = fact.get("verdict_id")
            proof = self._composition_proof(candidate, gate.task, fact, reference)
            if proof is None:
                continue
            if self.engine.publish(candidate.id, {"M6": proof}):
                m1_adapter.record_composition(self.scheduler, "published", candidate.id, candidate.members,
                                              candidate.manifest_sha256,
                                              tree_digest=self.git.tree_oid(candidate.integrated_commit) or "")
                published.append(candidate.id)
        return tuple(published)

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
            environment = hashlib.sha256(b"composition-owner-env/1").hexdigest()
            expected_environment = (m6_adapter.expected_environment_fingerprint(
                self._quality_policy, contracts, request.get("environment_fingerprint"))
                if self._quality_policy is not None and isinstance(request.get("environment_fingerprint"), str)
                else None)
            if (manifest.get("reason_code") != "PASS" or
                    (request.get("plan_id"), request.get("revision"), request.get("task_id"),
                     request.get("attempt_id"), request.get("token")) !=
                    (self.plan.plan_id, self.plan.revision, task_id, fact["attempt_id"], fact["token"])
                    or request.get("attempt_id") != fact["attempt_id"]
                    or request.get("composition_id") != candidate.id
                    or request.get("manifest_sha256") != candidate.manifest_sha256
                    or request.get("contract_identities") != contracts
                    or request.get("environment_fingerprint") != environment
                    or evidence_input.get("composition_id") != candidate.id
                    or evidence_input.get("manifest_sha256") != candidate.manifest_sha256
                    or evidence_input.get("tree_digest") != tree
                    or evidence_input.get("contract_identities") != contracts
                    or evidence_input.get("environment_fingerprint") != expected_environment):
                return None
            return bt_composition_adapter.VerdictProof(
                candidate.id, candidate.manifest_sha256, candidate.integrated_commit, tree, "PASS",
                self.verifier_id, "sha256:" + reference.removeprefix("m6://result/"))
        except (KeyError, TypeError, ValueError):
            return None

    def verification_identity_for(self, candidate) -> dict[str, str]:
        versions = {subplan: self.store.get_version(self.plan.plan_id, subplan, number)
                    for subplan, number in candidate.members.items()}
        return {key: value for version in versions.values() for key, value in version.contracts.items()}

    def propagate(self, change, consumers, evidence, *, composition_id: str, manifest_sha256: str,
                  tree_digest: str, source_task_id: str) -> tuple[str, ...]:
        """Produce real composition actions, validate each through M5, and apply its exact task frontier through M1."""
        if self.scheduler is None:
            raise CompositionRuntimeError("OWNER_COMPOSITION_M1_UNAVAILABLE")
        actions = bt_composition_adapter.propagate(change, consumers, evidence)
        if not actions:
            return ()
        evidence_ids = self._evidence_ids(evidence)
        if not evidence_ids:
            raise CompositionRuntimeError("OWNER_COMPOSITION_PROPAGATION_EVIDENCE_IDS_MISSING")
        if len(evidence_ids) > 32:
            raise CompositionRuntimeError("OWNER_COMPOSITION_PROPAGATION_EVIDENCE_LIMIT")
        consumer_map = {}
        for item in consumers:
            consumer_id = item.get("id") if isinstance(item, Mapping) else None
            if not isinstance(consumer_id, str) or not consumer_id or consumer_id in consumer_map:
                raise CompositionRuntimeError("OWNER_COMPOSITION_ACTION_CONSUMERS_AMBIGUOUS")
            consumer_map[consumer_id] = item
        advice_items = []
        for action in actions:
            if action.operation not in {"reverify", "reintegrate", "audit", "adapt_contract", "modify", "reimplement"}:
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_ACTION_UNMAPPABLE:{action.operation}")
            consumer = consumer_map.get(action.consumer)
            task_ids = consumer.get("task_ids") if isinstance(consumer, Mapping) else None
            if (not isinstance(task_ids, list) or not task_ids or
                    any(not isinstance(task_id, str) for task_id in task_ids) or
                    len(task_ids) != len(set(task_ids)) or
                    any(task_id not in self.scheduler.plan.ids() or task_id == source_task_id for task_id in task_ids)):
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_ACTION_FRONTIER_UNMAPPABLE:{action.consumer}")
            change_id = _propagation_change_id(composition_id, manifest_sha256, evidence_ids,
                                               action.consumer, action.operation, action.reason)
            evidence_refs = tuple(_opaque_evidence_ref(value) for value in evidence_ids)
            payload = {"schema_version": "m5.demonstrated-frontier/1", "change_id": change_id,
                       "source_task_id": source_task_id, "composition_id": composition_id,
                       "manifest_sha256": manifest_sha256, "tree_digest": tree_digest,
                       "action": action.operation, "frontier": list(task_ids),
                       "evidence_refs": list(evidence_refs)}
            self._frontier_proposals[change_id] = payload
            recovery_port = getattr(getattr(self.scheduler, "ports", None), "recovery", None)
            if recovery_port is None or not callable(getattr(recovery_port, "demonstrated_frontier", None)):
                raise CompositionRuntimeError("OWNER_COMPOSITION_M5_PROPAGATION_UNAVAILABLE")
            try:
                advice = recovery_port.demonstrated_frontier(change_id)
                advice_items.append(advice)
            except Exception as error:  # noqa: BLE001 - fail closed at the public module boundary
                code = getattr(error, "code", type(error).__name__)
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_M5_PROPAGATION_REFUSED:{code}") from None
        if not advice_items:
            return ()
        try:
            return m1_adapter.apply_demonstrated_frontiers(self.scheduler, tuple(advice_items))
        except Exception as error:  # noqa: BLE001 - the batch is atomic in M1
            code = getattr(error, "code", type(error).__name__)
            raise CompositionRuntimeError(f"OWNER_COMPOSITION_M1_FRONTIER_REFUSED:{code}") from None

    def demonstrated_frontier(self, change_id: str):
        """M5 composition_propagation port; returns only the staged, exact payload for this change id."""
        proposal = self._frontier_proposals.get(change_id)
        return dict(proposal) if proposal is not None else None

    @staticmethod
    def _evidence_ids(evidence) -> tuple[str, ...]:
        values = []
        for item in evidence:
            if not isinstance(item, Mapping):
                raise CompositionRuntimeError("OWNER_COMPOSITION_PROPAGATION_EVIDENCE_INVALID")
            identity = item.get("evidence_id", item.get("verdict_id"))
            if not isinstance(identity, str) or not identity:
                raise CompositionRuntimeError("OWNER_COMPOSITION_PROPAGATION_EVIDENCE_IDS_MISSING")
            values.append(identity)
        return tuple(dict.fromkeys(values))

