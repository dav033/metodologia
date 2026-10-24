"""Restart reconciliation for M1 version counters and composition publications."""
from __future__ import annotations

import bt_composition_adapter
import bt_scheduler_adapter as m1_adapter
import bt_scheduler_owner_version_adapter as version_adapter


def reconcile_store_version_counters(runtime) -> None:
    """Recover M1's strict version counter before publishing a version after an owner crash."""
    facts = version_adapter.version_facts(runtime.scheduler, include_stale=True)
    for subplan in runtime.plan.subplans:
        number = int(facts.get(subplan.id, {}).get("version", 0))
        for version in runtime.store.list_versions(runtime.plan.plan_id, subplan.id):
            if version.version <= number:
                continue
            try:
                m1_adapter.record_subplan_version(runtime.scheduler, subplan.id, version.version,
                                                  version.commit, version.manifest_sha256)
            except Exception:
                version_adapter.record_stale_version(runtime.scheduler, subplan.id, version.version,
                                                     version.commit, version.manifest_sha256)
            number = version.version


def reconcile_compositions(runtime) -> tuple[str, ...]:
    if runtime.scheduler is None:
        return ()
    accepted = m1_adapter.accepted_attempt_facts(runtime.scheduler)
    published = []
    composition_facts = m1_adapter.composition_facts(runtime.scheduler)
    for gate in runtime.plan.composition_gates:
        current_members, _ = runtime._members_for_gate(gate)
        reusable_fact = next(((candidate_id, item) for candidate_id, item in composition_facts.items()
                              if item.get("state") in {"candidate", "published"} and
                              item.get("members") == current_members), None)
        if current_members and reusable_fact:
            candidate_id, item = reusable_fact
            try:
                candidate = bt_composition_adapter.get_candidate(runtime.store, candidate_id)
                if candidate is not None and candidate.state == item.get("state"):
                    if item.get("revision") != runtime.plan.revision:
                        tree = runtime.git.tree_oid(candidate.integrated_commit)
                        if tree is None:
                            raise RuntimeError("OWNER_COMPOSITION_TREE_UNAVAILABLE")
                        m1_adapter.record_composition(runtime.scheduler, item["state"], candidate_id,
                                                      candidate.members, candidate.manifest_sha256, tree_digest=tree)
                    if (item.get("state") == "published" and
                            runtime.scheduler.snapshot().tasks[gate.task]["state"] == "completed"):
                        continue
            except Exception as error:  # noqa: BLE001 - keep one damaged publication local to its gate
                runtime._attend(gate.task, getattr(error, "code", str(error) or type(error).__name__))
                continue
        fact = accepted.get(gate.task)
        candidate_id = None
        if fact is None:
            continue
        try:
            candidate_id = runtime._manifest_candidate_id(fact.get("verdict_id"))
            candidate = (bt_composition_adapter.get_candidate(runtime.store, candidate_id)
                         if candidate_id else None)
            if candidate is None:
                runtime._hold_composition_gate(gate.task, candidate_id, "OWNER_COMPOSITION_CANDIDATE_UNAVAILABLE")
                runtime._attend(gate.task, "OWNER_COMPOSITION_CANDIDATE_UNAVAILABLE")
                continue
            composition_fact = m1_adapter.composition_facts(runtime.scheduler).get(candidate.id)
            if composition_fact and composition_fact.get("state") == "published" \
                    and composition_fact.get("members") == current_members:
                continue
            if gate.audit_task:
                audit_fact = accepted.get(gate.audit_task)
                if audit_fact is None:
                    continue
                audit_proof = runtime._composition_proof(candidate, gate.audit_task, audit_fact,
                                                         audit_fact.get("verdict_id"))
                if audit_proof is None or audit_proof.verdict != "PASS":
                    runtime._hold_composition_gate(gate.task, candidate.id,
                                                   "OWNER_COMPOSITION_AUDIT_PROOF_MISMATCH")
                    runtime._attend(gate.task, "OWNER_COMPOSITION_AUDIT_PROOF_MISMATCH")
                    continue
            proof = runtime._composition_proof(candidate, gate.task, fact, fact.get("verdict_id"))
            if proof is None:
                runtime._hold_composition_gate(gate.task, candidate.id, "OWNER_COMPOSITION_PROOF_MISMATCH")
                runtime._attend(gate.task, "OWNER_COMPOSITION_PROOF_MISMATCH")
                continue
            if proof.verdict == "FAIL":
                runtime.engine.reject(candidate.id, {"verdicts": {"M6": "FAIL"},
                                    "proofs": {"M6": {"verifier_id": runtime.verifier_id,
                                                      "evidence_id": proof.evidence_id}}})
                m1_adapter.record_composition(runtime.scheduler, "rejected", candidate.id, candidate.members,
                                              candidate.manifest_sha256, "M6_FAIL",
                                              tree_digest=proof.evaluated_tree)
                runtime._attend(gate.task, "OWNER_COMPOSITION_M6_FAIL")
                continue
            if runtime.engine.publish(candidate.id, {"M6": proof}):
                m1_adapter.record_composition(runtime.scheduler, "published", candidate.id, candidate.members,
                                              candidate.manifest_sha256, tree_digest=proof.evaluated_tree)
                published.append(candidate.id)
        except RuntimeError as error:
            if "COMPOSITION_CURRENT_MOVED" in str(error):
                runtime._hold_composition_gate(gate.task, candidate_id, "COMPOSITION_CURRENT_MOVED")
                runtime._attend(gate.task, "COMPOSITION_CURRENT_MOVED")
                continue
            runtime._attend(gate.task, getattr(error, "code", str(error)))
        except Exception as error:  # noqa: BLE001 - isolate one damaged gate from the owner loop
            runtime._attend(gate.task, getattr(error, "code", str(error) or type(error).__name__))
    return tuple(published)
