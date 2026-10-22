"""Versioned, data-only contracts for structural conflict recovery."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from .validation import decode, digest, enum, identifier, integer, require


def _path(value: object) -> None:
    require(type(value) is str and bool(value) and len(value) <= 512 and
            not value.startswith("/") and "\\" not in value and "\x00" not in value and
            all(part not in ("", ".", "..") for part in value.split("/")))


def _paths(value: object, *, allow_empty: bool = False) -> None:
    require(type(value) is tuple and len(value) <= 4096 and (allow_empty or bool(value)))
    for item in value:
        _path(item)
    require(len(value) == len(set(value)))


@dataclass(frozen=True)
class ConflictSide:
    ordinal: int
    role: str
    task_id: str
    attempt_id: str
    base_digest: str
    snapshot_digest: str
    tree_digest: str

    def __post_init__(self) -> None:
        integer(self.ordinal, 0, 4095)
        enum(self.role, ("accepted", "candidate"))
        identifier(self.task_id)
        identifier(self.attempt_id)
        digest(self.base_digest)
        digest(self.snapshot_digest)
        digest(self.tree_digest)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: object) -> ConflictSide:
        data = decode(cls, raw)
        try:
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class ConflictObservation:
    source_type: str
    run_id: str
    plan_id: str
    revision: int
    plan_sha256: str
    task_id: str
    attempt_id: str
    token: str
    consumer_id: str
    repository_id: str
    paths: tuple[str, ...]
    sides: tuple[ConflictSide, ...]
    original_merge_base: str
    carry_ancestry: tuple[str, ...]
    evidence_digests: tuple[str, ...]
    ordinary_rework_refusal: str
    ordinary_rework_refusal_detail: str

    def __post_init__(self) -> None:
        enum(self.source_type, ("start", "integration_gate"))
        for value in (self.run_id, self.plan_id, self.task_id, self.attempt_id, self.token,
                      self.consumer_id, self.repository_id):
            identifier(value)
        integer(self.revision, 1)
        digest(self.plan_sha256)
        _paths(self.paths)
        require(type(self.sides) is tuple and len(self.sides) >= 2 and
                all(type(item) is ConflictSide for item in self.sides))
        require(tuple(item.ordinal for item in self.sides) == tuple(range(len(self.sides))))
        require(len({(item.role, item.task_id, item.attempt_id) for item in self.sides}) == len(self.sides))
        accepted = sum(item.role == "accepted" for item in self.sides)
        candidates = [item for item in self.sides if item.role == "candidate"]
        require(accepted >= 1)
        if self.source_type == "start":
            # At start, a conflict can prevent the consumer attempt from existing.
            require(not candidates and accepted >= 2)
        else:
            require(len(candidates) == 1 and candidates[0].task_id == self.task_id and
                    candidates[0].attempt_id == self.attempt_id)
        digest(self.original_merge_base)
        require(type(self.carry_ancestry) is tuple and len(self.carry_ancestry) <= 128)
        for item in self.carry_ancestry:
            digest(item)
        require(len(self.carry_ancestry) == len(set(self.carry_ancestry)))
        require(type(self.evidence_digests) is tuple and 1 <= len(self.evidence_digests) <= 256)
        for item in self.evidence_digests:
            digest(item)
        require(len(self.evidence_digests) == len(set(self.evidence_digests)))
        enum(self.ordinary_rework_refusal,
             ("overlap_requires_structural_recovery", "ordinary_rework_refused"))
        require(type(self.ordinary_rework_refusal_detail) is str and
                bool(self.ordinary_rework_refusal_detail.strip()) and
                len(self.ordinary_rework_refusal_detail) <= 4096)

    def to_dict(self) -> dict:
        return {"schema_version": "conflict-observation/1", **asdict(self),
                "paths": list(self.paths), "sides": [item.to_dict() for item in self.sides],
                "carry_ancestry": list(self.carry_ancestry),
                "evidence_digests": list(self.evidence_digests)}

    @classmethod
    def from_dict(cls, raw: object) -> ConflictObservation:
        data = decode(cls, raw, "conflict-observation/1")
        try:
            for key in ("paths", "sides", "carry_ancestry", "evidence_digests"):
                require(type(data.get(key)) is list)
            data["paths"] = tuple(data["paths"])
            data["sides"] = tuple(ConflictSide.from_dict(item) for item in data["sides"])
            data["carry_ancestry"] = tuple(data["carry_ancestry"])
            data["evidence_digests"] = tuple(data["evidence_digests"])
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class ConflictPlanFacts:
    source_type: str
    run_id: str
    plan_id: str
    revision: int
    plan_sha256: str
    task_id: str
    attempt_id: str
    token: str
    consumer_id: str
    repository_id: str
    approved_start_paths: tuple[str, ...]
    approved_integration_paths: tuple[str, ...]
    authority_status: str

    def __post_init__(self) -> None:
        enum(self.source_type, ("start", "integration_gate"))
        for value in (self.run_id, self.plan_id, self.task_id, self.attempt_id, self.token,
                      self.consumer_id, self.repository_id):
            identifier(value)
        integer(self.revision, 1)
        digest(self.plan_sha256)
        _paths(self.approved_start_paths, allow_empty=True)
        _paths(self.approved_integration_paths, allow_empty=True)
        enum(self.authority_status, ("authorized", "missing", "owner_stop"))

    def to_dict(self) -> dict:
        return {"schema_version": "conflict-plan-facts/1", **asdict(self),
                "approved_start_paths": list(self.approved_start_paths),
                "approved_integration_paths": list(self.approved_integration_paths)}

    @classmethod
    def from_dict(cls, raw: object) -> ConflictPlanFacts:
        data = decode(cls, raw, "conflict-plan-facts/1")
        try:
            for key in ("approved_start_paths", "approved_integration_paths"):
                require(type(data.get(key)) is list)
                data[key] = tuple(data[key])
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class ConflictLineageFacts:
    status: str
    evidence_complete: bool
    semantic_conflict: bool
    incompatible_requirements: tuple[str, ...] = ()
    ownership_or_order_defect: bool = False
    demonstrated_future_defect: bool = False
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        enum(self.status, ("current", "stale", "unknown"))
        require(type(self.evidence_complete) is bool and type(self.semantic_conflict) is bool and
                type(self.ownership_or_order_defect) is bool and type(self.demonstrated_future_defect) is bool)
        require(type(self.incompatible_requirements) is tuple and
                all(type(item) is str and bool(item.strip()) and len(item) <= 512
                    for item in self.incompatible_requirements))
        require(len(self.incompatible_requirements) == len(set(self.incompatible_requirements)))
        require(not self.semantic_conflict or bool(self.incompatible_requirements))
        require(type(self.aliases) is tuple and len(self.aliases) <= 256 and
                all(type(item) is str for item in self.aliases))
        for item in self.aliases:
            identifier(item)
        require(len(self.aliases) == len(set(self.aliases)))

    def to_dict(self) -> dict:
        return {"schema_version": "conflict-lineage-facts/1", **asdict(self),
                "incompatible_requirements": list(self.incompatible_requirements),
                "aliases": list(self.aliases)}

    @classmethod
    def from_dict(cls, raw: object) -> ConflictLineageFacts:
        data = decode(cls, raw, "conflict-lineage-facts/1")
        try:
            for key in ("incompatible_requirements", "aliases"):
                require(type(data.get(key)) is list)
                data[key] = tuple(data[key])
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class ConflictStrategy:
    source_digests: tuple[str, ...]
    accepted_map_digest: str
    path_digests: tuple[str, ...]
    check_digests: tuple[str, ...]
    actions: tuple[str, ...]
    action_edges: tuple[tuple[str, str], ...] = ()
    strategy_id: str = ""

    def __post_init__(self) -> None:
        for group in (self.source_digests, self.path_digests, self.check_digests):
            require(type(group) is tuple and 1 <= len(group) <= 256)
            for item in group:
                digest(item)
            require(len(group) == len(set(group)))
        digest(self.accepted_map_digest)
        allowed = ("rebuild_stale_descendant", "converge_owned_paths",
                   "repair_demonstrated_future_ownership_order", "inherit_additive_checks")
        require(type(self.actions) is tuple and 1 <= len(self.actions) <= 4)
        for action in self.actions:
            enum(action, allowed)
        require(len(self.actions) == len(set(self.actions)) and
                self.actions[0] in ("rebuild_stale_descendant", "converge_owned_paths"))
        allowed_sequences = (
            ("rebuild_stale_descendant", "inherit_additive_checks"),
            ("rebuild_stale_descendant", "converge_owned_paths", "inherit_additive_checks"),
            ("rebuild_stale_descendant", "converge_owned_paths",
             "repair_demonstrated_future_ownership_order", "inherit_additive_checks"),
            ("converge_owned_paths", "inherit_additive_checks"),
            ("converge_owned_paths", "repair_demonstrated_future_ownership_order", "inherit_additive_checks"),
        )
        require(self.actions in allowed_sequences)
        require(type(self.action_edges) is tuple and len(self.action_edges) <= 8)
        require(all(type(edge) is tuple and len(edge) == 2 and edge[0] in self.actions and edge[1] in self.actions
                    and edge[0] != edge[1] for edge in self.action_edges))
        require(len(set(self.action_edges)) == len(self.action_edges))
        expected_edges = tuple((self.actions[index], self.actions[index + 1])
                               for index in range(len(self.actions) - 1))
        require(self.action_edges == expected_edges)
        identity = hashlib.sha256(json.dumps({
            "source_digests": self.source_digests, "accepted_map_digest": self.accepted_map_digest,
            "path_digests": self.path_digests, "check_digests": self.check_digests,
            "actions": self.actions, "action_edges": self.action_edges,
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if self.strategy_id:
            require(self.strategy_id == identity)
        object.__setattr__(self, "strategy_id", identity)

    def to_dict(self) -> dict:
        return {"schema_version": "conflict-strategy/1", **asdict(self),
                "source_digests": list(self.source_digests), "path_digests": list(self.path_digests),
                "check_digests": list(self.check_digests), "actions": list(self.actions),
                "action_edges": [list(edge) for edge in self.action_edges]}

    @classmethod
    def from_dict(cls, raw: object) -> ConflictStrategy:
        data = decode(cls, raw, "conflict-strategy/1")
        try:
            for key in ("source_digests", "path_digests", "check_digests", "actions", "action_edges"):
                require(type(data.get(key)) is list)
            for key in ("source_digests", "path_digests", "check_digests", "actions"):
                data[key] = tuple(data[key])
            data["action_edges"] = tuple(tuple(edge) for edge in data["action_edges"])
            return cls(**data)
        except TypeError:
            require(False)
