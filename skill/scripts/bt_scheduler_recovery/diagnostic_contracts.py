"""Versioned diagnostic records; occurrence identity is ledger-bound, not prose-derived."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .validation import decode, digest, enum, identifier, integer, reference, refs, require


def _occurrence_ref(value: object) -> None:
    require(type(value) is str and ":" in value)
    ledger_digest, finding_id = value.split(":", 1)
    digest(ledger_digest)
    identifier(finding_id)


@dataclass(frozen=True)
class FindingOccurrence:
    ledger_digest: str
    finding_id: str
    state: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        digest(self.ledger_digest)
        identifier(self.finding_id)
        enum(self.state, ("open", "fixed", "accepted"))
        refs(self.evidence_refs)

    @property
    def occurrence_id(self) -> str:
        return f"{self.ledger_digest}:{self.finding_id}"

    def to_dict(self) -> dict:
        return asdict(self) | {"evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, raw: object) -> FindingOccurrence:
        data = decode(cls, raw)
        try:
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class FindingRelation:
    previous_occurrence: str
    current_occurrence: str
    relation: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _occurrence_ref(self.previous_occurrence)
        _occurrence_ref(self.current_occurrence)
        enum(self.relation, ("same_finding",))
        refs(self.evidence_refs)
        require(bool(self.evidence_refs))

    def to_dict(self) -> dict:
        return asdict(self) | {"evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, raw: object) -> FindingRelation:
        data = decode(cls, raw)
        try:
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class DiagnosticCase:
    trigger_id: str
    run_id: str
    plan_id: str
    revision: int
    plan_sha256: str
    symptom: str
    occurrences: tuple[FindingOccurrence, ...]
    relations: tuple[FindingRelation, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.trigger_id)
        identifier(self.run_id)
        identifier(self.plan_id)
        integer(self.revision, 1)
        digest(self.plan_sha256)
        identifier(self.symptom)
        require(type(self.occurrences) is tuple and all(type(item) is FindingOccurrence for item in self.occurrences))
        require(type(self.relations) is tuple and all(type(item) is FindingRelation for item in self.relations))
        ids = [item.occurrence_id for item in self.occurrences]
        require(len(ids) == len(set(ids)))
        sources = [item.previous_occurrence for item in self.relations]
        targets = [item.current_occurrence for item in self.relations]
        require(len(sources) == len(set(sources)) and len(targets) == len(set(targets)))
        require(set(targets) <= set(ids))

    def to_dict(self) -> dict:
        return {"schema_version": "recovery-case/1", **asdict(self),
                "occurrences": [item.to_dict() for item in self.occurrences],
                "relations": [item.to_dict() for item in self.relations]}

    @classmethod
    def from_dict(cls, raw: object) -> DiagnosticCase:
        data = decode(cls, raw, "recovery-case/1")
        try:
            require(type(data.get("occurrences")) is list and type(data.get("relations")) is list)
            data["occurrences"] = tuple(FindingOccurrence.from_dict(item) for item in data["occurrences"])
            data["relations"] = tuple(FindingRelation.from_dict(item) for item in data["relations"])
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class RecoveryProposal:
    trigger_id: str
    generation: int
    action: str
    reason_code: str
    evidence_refs: tuple[str, ...]
    confidence: str

    def __post_init__(self) -> None:
        identifier(self.trigger_id)
        integer(self.generation)
        enum(self.action, ("retry", "wait", "block", "rework_findings"))
        identifier(self.reason_code)
        refs(self.evidence_refs)
        enum(self.confidence, ("confirmed", "reported", "inferred", "unknown"))

    def to_dict(self) -> dict:
        return {"schema_version": "recovery-proposal/1", **asdict(self), "evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, raw: object) -> RecoveryProposal:
        data = decode(cls, raw, "recovery-proposal/1")
        try:
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class PrerequisiteCheck:
    check_id: str
    status: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.check_id)
        enum(self.status, ("pass", "fail", "blocked", "unknown"))
        refs(self.evidence_refs)


@dataclass(frozen=True)
class ProgressSnapshot:
    occurrences: tuple[FindingOccurrence, ...]
    relations: tuple[FindingRelation, ...] = ()
    prerequisite_checks: tuple[PrerequisiteCheck, ...] = ()

    def __post_init__(self) -> None:
        require(type(self.occurrences) is tuple and all(type(item) is FindingOccurrence for item in self.occurrences))
        require(type(self.relations) is tuple and all(type(item) is FindingRelation for item in self.relations))
        require(type(self.prerequisite_checks) is tuple and all(type(item) is PrerequisiteCheck for item in self.prerequisite_checks))


@dataclass(frozen=True)
class RecoveryProgress:
    persisted: tuple[str, ...]
    fixed: tuple[str, ...]
    new: tuple[str, ...]
    regressed: tuple[str, ...]
    uncertain: tuple[str, ...]
    blocked_prerequisites: tuple[str, ...]

    def __post_init__(self) -> None:
        groups = (self.persisted, self.fixed, self.new, self.regressed, self.uncertain,
                  self.blocked_prerequisites)
        require(all(type(group) is tuple and all(type(item) is str and bool(item) for item in group) for group in groups))
        require(all(len(group) == len(set(group)) for group in groups))
        finding_groups = [set(group) for group in groups[:5]]
        require(all(not finding_groups[left] & finding_groups[right]
                    for left in range(len(finding_groups)) for right in range(left + 1, len(finding_groups))))

    def to_dict(self) -> dict:
        return {"schema_version": "recovery-progress/1", **{key: list(value) for key, value in asdict(self).items()}}

    @classmethod
    def from_dict(cls, raw: object) -> RecoveryProgress:
        data = decode(cls, raw, "recovery-progress/1")
        try:
            require(all(type(value) is list for value in data.values()))
            return cls(**{key: tuple(value) for key, value in data.items()})
        except (TypeError, ValueError):
            require(False)


@dataclass(frozen=True)
class VerificationPath:
    path: str
    source_digest: str
    owner_task_id: str

    def __post_init__(self) -> None:
        require(type(self.path) is str and bool(self.path) and not self.path.startswith("/") and
                "\\" not in self.path and all(part not in ("", ".", "..") for part in self.path.split("/")))
        digest(self.source_digest)
        identifier(self.owner_task_id)


@dataclass(frozen=True)
class VerificationCheck:
    check_id: str
    owner_task_id: str
    command: str
    symptom: str
    verdict_identity: str

    def __post_init__(self) -> None:
        identifier(self.check_id)
        identifier(self.owner_task_id)
        require(type(self.command) is str and bool(self.command.strip()))
        identifier(self.symptom)
        reference(self.verdict_identity)


@dataclass(frozen=True)
class VerificationMap:
    changed_paths: tuple[VerificationPath, ...]
    checks: tuple[VerificationCheck, ...]
    existing_owner_commands: tuple[str, ...]
    uncovered_paths: tuple[str, ...] = ()
    uncovered_checks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require(type(self.changed_paths) is tuple and all(type(item) is VerificationPath for item in self.changed_paths))
        require(type(self.checks) is tuple and all(type(item) is VerificationCheck for item in self.checks))
        require(type(self.existing_owner_commands) is tuple and all(type(item) is str and bool(item.strip()) for item in self.existing_owner_commands))
        require(type(self.uncovered_paths) is tuple and all(type(item) is str and bool(item) for item in self.uncovered_paths))
        require(type(self.uncovered_checks) is tuple and all(type(item) is str and bool(item) for item in self.uncovered_checks))
        covered_tasks = {check.owner_task_id for check in self.checks}
        require(all(item.path in self.uncovered_paths or item.owner_task_id in covered_tasks
                    for item in self.changed_paths))
        commands = set(self.existing_owner_commands)
        require(all(check.command in commands or check.check_id in self.uncovered_checks for check in self.checks))

    def to_dict(self) -> dict:
        return {"schema_version": "recovery-verification-map/1",
                "changed_paths": [asdict(item) for item in self.changed_paths],
                "checks": [asdict(item) for item in self.checks],
                "existing_owner_commands": list(self.existing_owner_commands),
                "uncovered_paths": list(self.uncovered_paths),
                "uncovered_checks": list(self.uncovered_checks)}

    @classmethod
    def from_dict(cls, raw: object) -> VerificationMap:
        data = decode(cls, raw, "recovery-verification-map/1")
        try:
            for key, item_type in (("changed_paths", VerificationPath), ("checks", VerificationCheck)):
                require(type(data.get(key)) is list)
                data[key] = tuple(item_type(**decode(item_type, item)) for item in data[key])
            for key in ("existing_owner_commands", "uncovered_paths", "uncovered_checks"):
                if key in data:
                    require(type(data[key]) is list)
                    data[key] = tuple(data[key])
            return cls(**data)
        except TypeError:
            require(False)
