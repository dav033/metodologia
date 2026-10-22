"""Owner lifecycle and durable journal for bounded diagnostic recovery.

This module coordinates plain versioned mappings; the M5 package boundary stays in
``bt_scheduler_recovery_adapter``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
import time
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path

import bt_scheduler_adapter as sched


def _verified_cycle_success(result: Mapping[str, object]) -> bool:
    """Require corrections and independent proofs over one resulting tree; phase flags are not evidence."""
    corrections = result.get("corrective_tasks")
    tree = result.get("resulting_tree_digest")
    proof = result.get("independent_evidence")
    progress = result.get("progress")
    if (not isinstance(corrections, list) or not 1 <= len(corrections) <= 8
            or len({item.get("task_id") for item in corrections if isinstance(item, Mapping)}) != len(corrections)
            or any(not isinstance(item, Mapping) or item.get("state") != "accepted"
                   for item in corrections)):
        return False
    if (not isinstance(tree, str) or len(tree) != 64 or any(c not in "0123456789abcdef" for c in tree)
            or not isinstance(proof, Mapping) or not isinstance(progress, Mapping)
            or progress.get("verified") is not True or progress.get("unresolved") is not False):
        return False
    required = ("m1_revision", "m3_snapshot", "m6_verdict", "independent_audit", "independent_cross_check")
    for key in required:
        item = proof.get(key)
        if (not isinstance(item, Mapping) or item.get("status") != "verified"
                or item.get("resulting_tree_digest") != tree
                or not isinstance(item.get("evidence_ref"), str) or not item["evidence_ref"].strip()):
            return False
    return True


def _two_verified_unchanged(observations: object) -> bool:
    if not isinstance(observations, list) or len(observations) < 2:
        return False
    previous, current = observations[-2:]
    keys = ("semantic_digest", "source_digest", "check_digest")
    return (isinstance(previous, Mapping) and isinstance(current, Mapping)
            and previous.get("verified") is True and current.get("verified") is True
            and all(isinstance(previous.get(key), str) and previous.get(key)
                    and previous.get(key) == current.get(key) for key in keys))


def _owner_hold_active(rdir: Path) -> bool:
    import bt_scheduler_ops

    return bt_scheduler_ops.on_hold(rdir)


def strategy_identity(strategy: Mapping[str, object], evidence: Mapping[str, object]) -> str:
    """Hash the executable DAG and semantic evidence, excluding prose labels and summaries."""
    actions = strategy.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError("recovery strategy has no action DAG")
    normalized = []
    for action in actions:
        if not isinstance(action, Mapping):
            raise TypeError("recovery strategy action is malformed")
        paths = action.get("owner_paths")
        outcomes = action.get("expected_outcomes")
        checks = action.get("checks")
        if not all(isinstance(value, list) for value in (paths, outcomes, checks)):
            raise ValueError("recovery strategy is missing paths, outcomes or checks")
        dependencies = action.get("depends_on", [])
        if (not isinstance(action.get("task_id"), str) or not action["task_id"]
                or not isinstance(action.get("kind"), str) or not action["kind"]
                or not isinstance(dependencies, list) or not all(isinstance(value, str) for value in dependencies)
                or not all(isinstance(value, str) and value for value in paths)
                or not all(isinstance(value, str) and value for value in outcomes)
                or not all(isinstance(value, (str, Mapping)) for value in checks)):
            raise ValueError("recovery strategy contains invalid executable identity fields")
        normalized.append({"task_id": action.get("task_id"), "kind": action.get("kind"),
                           "depends_on": sorted(dependencies),
                           "owner_paths": sorted(paths), "expected_outcomes": sorted(outcomes),
                           "checks": sorted(checks, key=lambda value: json.dumps(value, sort_keys=True))})
    semantic = {key: evidence.get(key) for key in
                ("semantic_digest", "source_digest", "check_digest", "source_digests", "snapshot_digests")}
    if not all(semantic.values()):
        raise ValueError("strategy identity requires semantic, source and check evidence")
    payload = {"actions": sorted(normalized, key=lambda value: str(value["task_id"])), "evidence": semantic}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()




class DiagnosticRecoveryLifecycle:
    def _live_identity(self) -> dict[str, object]:
        """Read the current M1 revision, stop fence and accepted map from its authority."""
        if self.rdir is None:
            raise RuntimeError("recovery run directory is unavailable")
        identity = sched.revision_identity(self.rdir)
        required = ("plan_id", "revision", "source_sha256", "stop_generation", "accepted_map_digest")
        if any(key not in identity for key in required):
            raise RuntimeError("M1 recovery identity is incomplete")
        return {"plan_id": identity["plan_id"], "revision": identity["revision"],
                "plan_sha256": identity["source_sha256"], "stop_generation": identity["stop_generation"],
                "accepted_map_digest": identity["accepted_map_digest"], "paused": identity.get("paused", False),
                "cancelled": identity.get("cancelled", False),
                "live_attempts": identity.get("live_attempts", [])}

    def _activation_path(self) -> Path:
        if self.rdir is None:
            raise RuntimeError("recovery run directory is unavailable")
        return self.rdir / "RUN.recovery-policy.json"

    def _cycle_db(self) -> sqlite3.Connection:
        """The sole M5 adapter owns this compact lineage ledger beside its normal decision store."""
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=2, isolation_level=None)
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("CREATE TABLE IF NOT EXISTS diagnostic_cycles ("
                            "lineage_id TEXT PRIMARY KEY, cycle_token TEXT NOT NULL UNIQUE, state TEXT NOT NULL, "
                            "identity_json TEXT NOT NULL, payload_json TEXT NOT NULL, updated_at REAL NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS conflict_observations ("
                            "reference TEXT PRIMARY KEY, observation_json TEXT NOT NULL, sha256 TEXT NOT NULL, "
                            "created_at REAL NOT NULL)")
        return connection

    @staticmethod
    def _lineage_id(observation: Mapping[str, object]) -> str:
        """Correlate revisions by source/tree/check evidence, never by plan wording or revision labels."""
        semantic = {key: observation.get(key) for key in (
            "run_id", "audit_lineage", "conflict_lineage", "source_digests", "snapshot_digests",
            "changed_paths_digest", "check_digests", "accepted_attempts", "merge_base_digest", "carry_digest")}
        if not semantic["run_id"] or not any(semantic[key] for key in (
                "audit_lineage", "conflict_lineage", "source_digests", "snapshot_digests")):
            raise ValueError("recovery lineage lacks stable source identity")
        return hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=True, allow_nan=False).encode()).hexdigest()

    def preview_recovery(self) -> dict[str, object]:
        """Read live evidence and M1 identity without persisting a case, invoking diagnosis or answering decisions."""
        try:
            identity = self._live_identity()
            sources = dict(self.recovery_sources() if self.recovery_sources else {})
            source_digest = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(",", ":"),
                                                      allow_nan=False).encode()).hexdigest()
            activation = self._activation_path()
            authorized = activation.is_file()
            body = {"schema_version": "recovery-preview/1", "run_id": self.run_id, "identity": identity,
                    "source_digest": source_digest, "sources": sources, "activation_present": authorized}
            body["preview_digest"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                                       allow_nan=False).encode()).hexdigest()
            return body
        except Exception as error:  # noqa: BLE001 - preview reports unavailable evidence, it does not infer a trigger
            return {"schema_version": "recovery-preview/1", "run_id": self.run_id, "status": "unavailable",
                    "blocker": f"recovery_preview_unavailable:{type(error).__name__}"}

    def enable_diagnostic_recovery(self, run_identity: str, preview_digest: str, stop_generation: int,
                                   authorization_ref: str) -> dict[str, object]:
        """Persist one explicit policy activation; a preview itself can never enable the policy."""
        preview = self.preview_recovery()
        if preview.get("schema_version") != "recovery-preview/1" or "identity" not in preview:
            return {"schema_version": "recovery-activation/1", "enabled": False,
                    "blocker": preview.get("blocker", "preview_unavailable")}
        identity = preview["identity"]
        valid_authorization = (authorization_ref == "approved-policy:REQ-029:r2"
                               or isinstance(authorization_ref, str)
                               and re.fullmatch(r"owner-control:[0-9a-f]{32}", authorization_ref) is not None)
        if (run_identity != self.run_id or preview.get("preview_digest") != preview_digest
                or identity.get("stop_generation") != stop_generation
                or not valid_authorization):
            return {"schema_version": "recovery-activation/1", "enabled": False,
                    "blocker": "stale_preview_or_missing_authorization"}
        if identity.get("cancelled") or identity.get("paused") or _owner_hold_active(self.rdir):
            return {"schema_version": "recovery-activation/1", "enabled": False, "blocker": "owner_stop_or_hold"}
        record = {"schema_version": "recovery-policy/1", "run_id": self.run_id, "identity": identity,
                  "preview_digest": preview_digest, "authorization_ref": authorization_ref,
                  "limits": {"diagnoses": 1, "corrective_tasks": 8, "supplemental_audits_per_lineage": 1}}
        target = self._activation_path()
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".recovery-policy-", dir=target.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(record, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        finally:
            Path(temp_name).unlink(missing_ok=True)
        return {"schema_version": "recovery-activation/1", "enabled": True,
                "policy_digest": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()}

    def recovery_status(self) -> dict[str, object]:
        """Return durable cycle state without starting work."""
        return read_cycle_status(self.path, run_id=self.run_id)

    def publish_conflict_observation(self, observation: Mapping[str, object]) -> str:
        """Persist a complete, M5-validated conflict payload before any M6/operator clipping."""
        parsed = self._parse_conflict_observation(observation)
        payload = parsed.to_dict()
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        reference = f"conflict:{digest}"
        connection = self._cycle_db()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT observation_json,sha256 FROM conflict_observations WHERE reference=?",
                                     (reference,)).fetchone()
            if row is not None and row != (encoded, digest):
                raise ValueError("conflict evidence reference collision")
            connection.execute("INSERT OR IGNORE INTO conflict_observations VALUES(?,?,?,?)",
                               (reference, encoded, digest, time.time()))
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        return reference

    def read_conflict_observation(self, reference: str) -> dict[str, object] | None:
        """Read and revalidate one immutable conflict record from trusted M5 storage."""
        if not isinstance(reference, str) or not reference.startswith("conflict:"):
            return None
        connection = self._cycle_db()
        try:
            row = connection.execute("SELECT observation_json,sha256 FROM conflict_observations WHERE reference=?",
                                     (reference,)).fetchone()
        finally:
            connection.close()
        if row is None or hashlib.sha256(row[0].encode()).hexdigest() != row[1] or reference != f"conflict:{row[1]}":
            return None
        return self._parse_conflict_observation(json.loads(row[0])).to_dict()

    def tick_diagnostic_recovery(self) -> dict[str, object]:
        """Advance one authorized, durable cycle through the configured recovery transport."""
        lineage_id: str | None = None
        preview = self.preview_recovery()
        if preview.get("schema_version") != "recovery-preview/1" or "identity" not in preview:
            return {"schema_version": "recovery-tick/1", "state": "blocked",
                    "blocker": preview.get("blocker", "recovery_preview_unavailable")}
        if not preview.get("activation_present"):
            return {"schema_version": "recovery-tick/1", "state": "preview_only", "preview_digest": preview["preview_digest"]}
        try:
            policy = json.loads(self._activation_path().read_text(encoding="utf-8"))
            identity = self._live_identity()
            if (policy.get("schema_version") != "recovery-policy/1" or policy.get("run_id") != self.run_id
                    or policy.get("identity", {}).get("stop_generation") != identity["stop_generation"]
                    or identity.get("cancelled") or identity.get("paused")
                    or _owner_hold_active(self.rdir)):
                return {"schema_version": "recovery-tick/1", "state": "blocked", "blocker": "stale_activation"}
            import bt_remediation
            if bt_remediation.requested(self.rdir):
                return {"schema_version": "recovery-tick/1", "state": "waiting_ordinary_remediation"}
            import bt_scheduler_decisions
            pending = bt_scheduler_decisions.open_requests(self.rdir)
            if any(request.get("unskippable") is True for request in pending):
                return {"schema_version": "recovery-tick/1", "state": "waiting_owner_decision"}
            if self.recovery_sources is None:
                return {"schema_version": "recovery-tick/1", "state": "blocked",
                        "blocker": "recovery_evidence_source_unavailable"}
            sources = dict(self.recovery_sources())
            conflicts = sources.get("conflict_observations", [])
            if not isinstance(conflicts, list):
                return {"schema_version": "recovery-tick/1", "state": "blocked",
                        "blocker": "conflict_observations_malformed"}
            try:
                for observation in conflicts:
                    if not isinstance(observation, Mapping):
                        raise TypeError("invalid conflict observation")
                    self._validate_conflict_observation(observation)
            except (ValueError, TypeError):
                return {"schema_version": "recovery-tick/1", "state": "blocked",
                        "blocker": "conflict_observation_invalid"}
            if sources.get("ordinary_remediation_pending") is True:
                return {"schema_version": "recovery-tick/1", "state": "waiting_ordinary_remediation"}
            if sources.get("owner_only_decision_pending") is True:
                return {"schema_version": "recovery-tick/1", "state": "waiting_owner_decision"}
            if sources.get("ordinary_exhausted") is not True and not _two_verified_unchanged(sources.get("observations")):
                return {"schema_version": "recovery-tick/1", "state": "ordinary_path_first"}
            route = sources.get("planner_route")
            lineage_id = self._lineage_id(sources)
            with closing(self._cycle_db()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute("SELECT cycle_token,state,payload_json FROM diagnostic_cycles "
                                         "WHERE lineage_id=?", (lineage_id,)).fetchone()
                if row:
                    if row[1] == "diagnosing":
                        interrupted = {"state": "blocked", "blocker": "diagnostic_cycle_interrupted_after_restart"}
                        connection.execute("UPDATE diagnostic_cycles SET state='blocked',payload_json=?,updated_at=? "
                                           "WHERE lineage_id=?", (json.dumps(interrupted), time.time(), lineage_id))
                        connection.execute("COMMIT")
                        return {"schema_version": "recovery-tick/1", "state": "blocked", "cycle_token": row[0],
                                "result": interrupted, "duplicate": True}
                    connection.execute("COMMIT")
                    return {"schema_version": "recovery-tick/1", "state": row[1], "cycle_token": row[0],
                            "result": json.loads(row[2]), "duplicate": True}
                token = hashlib.sha256(f"{self.run_id}:{lineage_id}".encode()).hexdigest()
                started = {"state": "diagnosing", "lineage_id": lineage_id}
                connection.execute("INSERT INTO diagnostic_cycles VALUES(?,?,?,?,?,?)",
                                   (lineage_id, token, "diagnosing", json.dumps(identity, sort_keys=True),
                                    json.dumps(started), time.time()))
                connection.execute("COMMIT")
            latest_identity = self._live_identity()
            if (latest_identity.get("stop_generation") != identity.get("stop_generation")
                    or latest_identity.get("accepted_map_digest") != identity.get("accepted_map_digest")
                    or latest_identity.get("cancelled") or latest_identity.get("paused")
                    or _owner_hold_active(self.rdir)):
                result = {"state": "blocked", "blocker": "recovery_identity_changed_before_diagnosis"}
            elif self.diagnostic_pipeline is None:
                result = {"state": "blocked", "blocker": "diagnostic_pipeline_unavailable"}
            elif (not isinstance(route, Mapping) or route.get("role") != "planner"
                  or route.get("verified") is not True
                  or any(not isinstance(route.get(key), str) or not route[key].strip()
                         for key in ("provider", "profile", "model", "authorization_ref"))):
                result = {"state": "blocked", "blocker": "authorized_planner_route_unavailable"}
            elif sources.get("evidence_available") is not True:
                result = {"state": "blocked", "blocker": "recovery_evidence_unavailable"}
            else:
                result = dict(self.diagnostic_pipeline({"identity": identity, "sources": sources,
                                                       "cycle_token": token, "preview": preview}))
            if result.get("state") == "succeeded" and not _verified_cycle_success(result):
                result = {"state": "blocked", "blocker": "independent_resulting_tree_proof_missing"}
            state_name = result.get("state", "blocked")
            if state_name not in {"succeeded", "blocked", "escalated", "applying", "executing", "auditing"}:
                result, state_name = {"state": "blocked", "blocker": "invalid_recovery_pipeline_state"}, "blocked"
            with closing(self._cycle_db()) as connection:
                connection.execute("UPDATE diagnostic_cycles SET state=?,payload_json=?,updated_at=? WHERE lineage_id=?",
                                   (state_name, json.dumps(result, sort_keys=True), time.time(), lineage_id))
            return {"schema_version": "recovery-tick/1", "state": state_name, "cycle_token": token,
                    "result": result, "duplicate": False}
        except Exception as error:  # noqa: BLE001 - failure is durable and never falls through to ordinary retry
            if lineage_id is not None:
                try:
                    with closing(self._cycle_db()) as connection:
                        connection.execute("UPDATE diagnostic_cycles SET state='blocked',payload_json=?,updated_at=? "
                                           "WHERE lineage_id=? AND state='diagnosing'",
                                           (json.dumps({"state": "blocked", "blocker":
                                                        f"diagnostic_cycle_failed:{type(error).__name__}"}),
                                            time.time(), lineage_id))
                except sqlite3.Error:
                    pass
            return {"schema_version": "recovery-tick/1", "state": "blocked",
                    "blocker": f"diagnostic_cycle_failed:{type(error).__name__}"}

    def _validate_conflict_observation(self, observation: Mapping[str, object]) -> None:
        raise NotImplementedError

    def _parse_conflict_observation(self, observation: Mapping[str, object]):
        raise NotImplementedError


def read_cycle_status(path: Path | str, *, run_id: str) -> dict[str, object]:
    """Read only the durable diagnostic-cycle ledger; do not create or migrate a store."""
    target = Path(path)
    try:
        if not target.is_file():
            return {"schema_version": "recovery-status/1", "run_id": run_id, "cycles": []}
        connection = sqlite3.connect(f"{target.resolve().as_uri()}?mode=ro", uri=True, timeout=2)
        try:
            exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                        "AND name='diagnostic_cycles'").fetchone()
            rows = connection.execute("SELECT lineage_id,cycle_token,state,payload_json FROM diagnostic_cycles "
                                      "ORDER BY updated_at DESC").fetchall() if exists else []
        finally:
            connection.close()
        return {"schema_version": "recovery-status/1", "run_id": run_id,
                "cycles": [{"lineage_id": row[0], "cycle_token": row[1], "state": row[2],
                            "result": json.loads(row[3])} for row in rows]}
    except (OSError, sqlite3.Error, ValueError) as error:
        return {"schema_version": "recovery-status/1", "run_id": run_id,
                "blocker": f"recovery_status_unavailable:{type(error).__name__}", "cycles": []}

