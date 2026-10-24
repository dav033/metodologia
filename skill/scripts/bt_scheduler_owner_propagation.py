"""M5/M1 propagation operations composed by the owner runtime."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

import bt_composition_adapter
import bt_scheduler_adapter as m1_adapter
from bt_composition_adapter import EvidenceKey, PropagationChange
from bt_scheduler_owner_errors import CompositionRuntimeError


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


class OwnerPropagationMixin:
    def propagate(self, change, consumers, evidence, *, composition_id: str, manifest_sha256: str,
                  tree_digest: str, source_task_id: str) -> tuple[str, ...]:
        """Validate M5 advice and apply its exact task frontier through M1."""
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
                advice_items.append(recovery_port.demonstrated_frontier(change_id))
            except Exception as error:  # noqa: BLE001
                code = getattr(error, "code", type(error).__name__)
                raise CompositionRuntimeError(f"OWNER_COMPOSITION_M5_PROPAGATION_REFUSED:{code}") from None
        try:
            return m1_adapter.apply_demonstrated_frontiers(self.scheduler, tuple(advice_items)) if advice_items else ()
        except Exception as error:  # noqa: BLE001 - M1 applies the batch atomically
            code = getattr(error, "code", type(error).__name__)
            raise CompositionRuntimeError(f"OWNER_COMPOSITION_M1_FRONTIER_REFUSED:{code}") from None

    def demonstrated_frontier(self, change_id: str):
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

    @staticmethod
    def _environment_identity(version) -> str | None:
        values = {item.get("environment_fingerprint") for item in version.evidence
                  if isinstance(item.get("environment_fingerprint"), str)}
        return next(iter(values)) if len(values) == 1 else None

    def reconcile_propagation(self) -> tuple[str, ...]:
        """Derive M5 actions from published composition members and their declared consumers."""
        if self.scheduler is None:
            return ()
        applied = []
        facts = m1_adapter.composition_facts(self.scheduler)
        subplans = {item.id: item for item in self.plan.subplans}
        plan_order = {item.id: index for index, item in enumerate(self.plan.subplans)}
        for composition_id, fact in facts.items():
            if fact.get("state") != "published":
                continue
            candidate = bt_composition_adapter.get_candidate(self.store, composition_id)
            if candidate is None:
                continue
            for source_id, version_number in candidate.members.items():
                if version_number < 2 or source_id not in subplans:
                    continue
                current = self.store.get_version(self.plan.plan_id, source_id, version_number)
                previous = self.store.get_version(self.plan.plan_id, source_id, version_number - 1)
                if (current is None or previous is None
                        or (current.contracts == previous.contracts and current.commit == previous.commit)):
                    continue
                source_gate = next((gate for gate in self.plan.composition_gates
                                    if source_id in gate.subplans and gate.task in
                                    m1_adapter.accepted_attempt_facts(self.scheduler)), None)
                if source_gate is None:
                    continue
                evidence = [dict(item) for item in current.evidence]
                evidence_ids = self._evidence_ids(evidence)
                if not evidence_ids:
                    self._attend(source_id, "OWNER_COMPOSITION_PROPAGATION_EVIDENCE_MISSING")
                    continue
                old_environment = self._environment_identity(previous)
                new_environment = self._environment_identity(current)
                if not old_environment or not new_environment:
                    self._attend(source_id, "OWNER_COMPOSITION_PROPAGATION_ENVIRONMENT_IDENTITY_MISSING")
                    continue
                consumers = []
                for consumer in self.plan.subplans:
                    if plan_order[consumer.id] <= plan_order[source_id]:
                        continue
                    if not any(item.get("from") == source_id for item in consumer.consumes):
                        continue
                    task_ids = [task.id for task in self.plan.tasks
                                if task.meta.get("subplan_id") == consumer.id]
                    if consumer.ui is not None:
                        task_ids.extend((consumer.ui.design_task, consumer.ui.visual_review_task))
                    task_ids = list(dict.fromkeys(task_ids))
                    consumers.append({"id": consumer.id, "task_ids": task_ids,
                                      "old_evidence_key": EvidenceKey(previous.commit, previous.contracts,
                                                                      old_environment),
                                      "new_evidence_key": EvidenceKey(current.commit, current.contracts,
                                                                      new_environment)})
                if not consumers:
                    continue
                ancestry_only = current.contracts == previous.contracts
                change = PropagationChange(source_id, ancestry_only=ancestry_only,
                                           public_surface_changed=not ancestry_only)
                try:
                    moved = self.propagate(change, consumers, evidence, composition_id=composition_id,
                                           manifest_sha256=candidate.manifest_sha256,
                                           tree_digest=fact.get("tree_digest", ""),
                                           source_task_id=source_gate.task)
                    applied.extend(moved)
                except Exception as error:  # noqa: BLE001 - one producer cannot break unrelated owner work
                    self._attend(source_id, getattr(error, "code", str(error) or type(error).__name__))
        return tuple(dict.fromkeys(applied))

