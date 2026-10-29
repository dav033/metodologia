"""Plan and subplan contracts: PLAN.json schema 1.0.0 to 1.3.0 as Pydantic v2 models (REQ-030 M1, item 7).

This is the canonical, versioned description of a frozen plan the runtimes consume: one model per schema version,
selected by `schema_version`, and the JSON Schema is generated from them (`python -m bt_contracts.schemas` writes
`bt_contracts/schemas/plan.schema.json`; a test fails when that file is stale).

What the contract decides, so that a plan that passes it can be loaded and scheduled without a lookup failing:
- shape: closed objects (an unknown or renamed key such as `req_id` is an error, never ignored), exact JSON types (an
  array where an object is expected is an error; nothing is coerced), required fields, enumerations, id grammars;
- versioning: a field exists only from the schema version that introduced it. A 1.2.0 plan carrying `subplans` would
  be run without them by a 1.2 reader, so it is refused instead of silently changing meaning;
- identity: ids are unique (milestones, tasks, requirements, interfaces, subplans, gates, produced contracts);
- references: every id resolves to a declared object of the right sort, `after` is acyclic, a consumed contract is
  produced by the subplan it names, a stage lists exactly the revision's subplans.

What it leaves to the planner's authoring rules (stdlib, reached through `bt_plan_adapter`): text and evidence
quality, coverage totality (orphan milestones, uncovered requirements, empty subplans), task roles (the kind or the
membership of an audit, integration or design task), ordering beyond acyclicity (milestone order, interface, subplan
and UI ordering, checkpoints) and policies that tightened after plans were frozen (audit findings ledgers). Those
rules decide whether a plan may be published; this contract decides whether a published plan is structurally
runnable, before any agent quota is spent.

The hand-written readers stay as the stdlib adapters (the hooks and the bitácora CLI cannot import pydantic);
`tests/test_plan_contract_models.py` proves both give the same verdict on every frozen plan of the bitácora.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)
from pydantic_core import PydanticCustomError

from bt_contracts.plan_rules import (
    EVIDENCE_KINDS,
    SECRET_PAIR,
    SECRET_URL,
    command,
    evidence_ref,
    generated_path,
    nonblank,
    reference_issues,
    relative_path,
    strict_json,
)

SCHEMA_VERSIONS = ("1.0.0", "1.1.0", "1.2.0", "1.3.0")
MAX_BYTES = 2_000_000
MAX_TASKS = 10_000
MAX_REVISION = 1_000_000
MAX_MINUTES = 100_000

COMPLEXITY = ("low", "medium", "high", "extreme")
SCOPE = ("isolated_fix", "small_change", "large_change", "full_feature", "full_system")
LEVELS = ("low", "medium", "high")
VERIFICATION_TYPES = ("command", "manual")
VERIFICATION_CATEGORIES = ("static", "functional", "integration", "regression", "product")
VERIFICATION_ENVIRONMENTS = ("sandbox", "external_authorized", "production", "human_attestation")
TASK_KINDS = ("implement", "test", "docs", "audit", "research")
TASK_KINDS_13 = TASK_KINDS + ("design",)
DIMENSIONS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")
DEPENDENCIES = ("contract", "implementation", "publication")


# ---------------------------------------------------------------------------------------------------- value types

Text = Annotated[str, AfterValidator(nonblank), Field(json_schema_extra={"pattern": r"\S"})]
RelativePath = Annotated[str, AfterValidator(nonblank), AfterValidator(relative_path),
                         Field(json_schema_extra={"pattern": r"\S"})]
TaskId = Annotated[str, Field(pattern=r"^T[0-9]+(?:\.[0-9]+)?[a-z]?$")]
MilestoneId = Annotated[str, Field(pattern=r"^M[0-9]+$")]
RequirementId = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9]{0,7}-?[0-9]{1,4}$")]
SubplanId = Annotated[str, Field(pattern=r"^SP-[1-9][0-9]*$")]
GateId = Annotated[str, Field(pattern=r"^CG-[1-9][0-9]*$")]
InterfaceId = Annotated[str, Field(pattern=r"^IF-[1-9][0-9]*$")]
ContractSlug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")]
ContractVersion = Annotated[int, Field(ge=1, le=1000)]
ResourceName = Annotated[str, Field(pattern=r"^(?:[A-Z][A-Z0-9_]{1,63}|service:[a-z0-9][a-z0-9-]{0,63})$")]
GeneratedPath = Annotated[str, AfterValidator(generated_path), Field(min_length=1, max_length=1024)]
Command = Annotated[str, AfterValidator(command), Field(max_length=4096)]
EvidenceRef = Annotated[str, AfterValidator(evidence_ref),
                        Field(description="kind:value, kind in " + ", ".join(EVIDENCE_KINDS))]
# A reference to another object of the plan: its existence is checked by the plan, not by the grammar.
Ref = Text


class PlanModel(BaseModel):
    """Closed, strict and frozen: unknown keys are errors and no value is coerced into another JSON type.

    Optional fields declared `X = None` may be absent but never null (the legacy readers refuse null there)."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, serialize_by_alias=True,
                              validate_by_alias=True, validate_by_name=False)


# ---------------------------------------------------------------------------------------------------- parts

class Milestone(PlanModel):
    id: MilestoneId
    title: Text
    acceptance_criteria: list[Text] = Field(min_length=1)


class ScopeException(PlanModel):
    """Only with `scope: full_system`, which must otherwise be decomposed."""
    reason: Text


class DimensionEvidence(PlanModel):
    justification: Text
    evidence: list[EvidenceRef] = Field(min_length=1)


class ClassificationEvidence(PlanModel):
    """Every classification argued per dimension (schema 1.1.0 and later)."""
    complexity: DimensionEvidence
    scope: DimensionEvidence
    duration: DimensionEvidence
    risk: DimensionEvidence
    coupling: DimensionEvidence
    confidence: DimensionEvidence


class Verification100(PlanModel):
    type: Literal[VERIFICATION_TYPES]
    value: Text
    purpose: Text
    expected: str | None = Field(default=None, description="required (non-blank) for a manual check")
    created_by: str | None = Field(default=None, description="the task that creates a check that does not exist yet")

    @model_validator(mode="after")
    def _manual(self):
        if self.type == "manual" and not (isinstance(self.expected, str) and self.expected.strip()):
            raise ValueError("a manual check must state the expected result (expected)")
        return self


class Verification120(Verification100):
    category: Literal[VERIFICATION_CATEGORIES]


class Verification130(Verification120):
    environment: Literal[VERIFICATION_ENVIRONMENTS] = None
    requires: list[ResourceName] = Field(default_factory=list, description="resource names, never secret values")
    authorization_needed: str | None = None

    @model_validator(mode="after")
    def _environment(self):
        authorization = self.authorization_needed
        if self.environment == "production" and not (isinstance(authorization, str) and authorization.strip()):
            raise ValueError("a production check needs authorization_needed")
        if isinstance(authorization, str) and ("=" in authorization or SECRET_URL.search(authorization)
                                               or SECRET_PAIR.search(authorization)):
            raise ValueError("authorization_needed must describe the authorization without secret values")
        if self.environment == "human_attestation" and (self.type != "manual" or not self.expected):
            raise ValueError("human_attestation requires a manual check with expected")
        return self


class Task100(PlanModel):
    id: TaskId
    milestone_id: Ref
    title: Text
    objective: Text
    repository: Text
    after: list[Ref]
    complexity: Literal[COMPLEXITY]
    scope: Literal[SCOPE]
    estimated_minutes: int = Field(ge=1, le=MAX_MINUTES)
    risk: Literal[LEVELS]
    coupling: Literal[LEVELS]
    confidence: Literal[LEVELS]
    estimate_rationale: Text
    expected_paths: list[RelativePath]
    shared_resources: list[Text]
    acceptance_criteria: list[Text] = Field(min_length=1)
    verification: list[Verification100] = Field(min_length=1)
    scope_exception: ScopeException = None
    # Compiler-owned metadata of generated recovery tasks (bt_recovery_convergence); opaque to the planner.
    recovery_task: bool = None
    recovery_case_id: Text = None
    recovery_owner_tasks: list[Text] = None
    bootstrap: dict[str, Any] = None

    @model_validator(mode="after")
    def _scope(self):
        if self.scope == "full_system" and self.scope_exception is None:
            raise ValueError("scope full_system must be decomposed, or carry scope_exception {reason} for review")
        if self.scope != "full_system" and self.scope_exception is not None:
            raise ValueError("scope_exception is only valid with scope full_system")
        return self


class Task110(Task100):
    classification_evidence: ClassificationEvidence


class Task120(Task110):
    covers: list[RequirementId] = Field(min_length=1)
    kind: Literal[TASK_KINDS]
    verification: list[Verification120] = Field(min_length=1)


class Task130(Task120):
    kind: Literal[TASK_KINDS_13]
    verification: list[Verification130] = Field(min_length=1)
    subplan_id: SubplanId = None
    ui: bool = None

    @model_validator(mode="after")
    def _ui(self):
        if self.ui is True and self.subplan_id is None:
            raise ValueError("a ui task requires subplan_id")
        return self


class Interface(PlanModel):
    """A cross-task interface (schema 1.2.0): who produces it, who consumes it, what must hold."""
    id: InterfaceId
    title: Text
    owner: Text
    producer_task: Ref
    consumer_tasks: list[Ref] = Field(min_length=1)
    integration_task: Ref = None
    inputs: list[Text] = Field(min_length=1)
    outputs: list[Text] = Field(min_length=1)
    invariants: list[Text] = Field(min_length=1)
    integration_criteria: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def _roles(self):
        if len(set(self.consumer_tasks)) != len(self.consumer_tasks):
            raise ValueError("consumer_tasks has a duplicate task")
        if self.producer_task in self.consumer_tasks:
            raise ValueError("producer and consumer must differ")
        if self.integration_task is not None and self.integration_task in self.consumer_tasks:
            raise ValueError("integration_task cannot be one of the consumer tasks")
        return self


class ProducedContract(PlanModel):
    contract: ContractSlug
    version: ContractVersion
    defined_by: Ref
    interfaces: list[InterfaceId] = Field(default_factory=list)


class ConsumedContract(PlanModel):
    contract: ContractSlug
    version: ContractVersion
    from_: Annotated[str, Field(alias="from", pattern=r"^(?:SP-[1-9][0-9]*|external)$")]
    dependency: Literal[DEPENDENCIES]
    verified_by: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def _external(self):
        if self.from_ == "external" and self.dependency != "contract":
            raise ValueError("an external dependency can only be on a contract")
        return self


class Checkpoint(PlanModel):
    task: Ref
    purpose: Text


class SubplanUI(PlanModel):
    contract: ContractSlug
    version: ContractVersion
    design_task: Ref
    visual_review_task: Ref


class UIFlow(PlanModel):
    name: Text
    steps: list[Text] = Field(min_length=1)


class ExistingSurface(PlanModel):
    routes: list[Text] = None
    paths: list[Text] = None
    components: list[Text] = None
    screenshots: list[Text] = None
    notes: str = None


class UIBrief(PlanModel):
    """Optional Planner hand-off to the Designer for a UI subplan."""
    flows: list[Text | UIFlow] = None
    screens_states: list[Text] = None
    existing_surface: ExistingSurface = None
    must_not_change: list[Text] = None
    copy_rules: list[Text] = None
    criteria: list[Text] = None


class Subplan(PlanModel):
    """A functional slice of a 1.3.0 plan with its own integration test and audit."""
    id: SubplanId
    milestone_id: Ref
    title: Text
    outcome: Text
    covers: list[RequirementId] = Field(min_length=1)
    acceptance_criteria: list[Text] = Field(min_length=1)
    integration_test_task: Ref
    audit_task: Ref
    produces: list[ProducedContract] = Field(default_factory=list)
    consumes: list[ConsumedContract] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    ui: SubplanUI = None
    ui_brief: UIBrief = None

    @model_validator(mode="after")
    def _brief(self):
        if self.ui_brief is not None and self.ui is None:
            raise ValueError("ui_brief needs a ui contract on the same subplan")
        return self


class CompositionGate(PlanModel):
    """Subplans whose published versions are composed and tested together before dependent work continues."""
    id: GateId
    subplans: list[SubplanId] = Field(min_length=1)
    task: Ref
    audit_task: Ref | None = None
    criteria: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def _distinct(self):
        if len(set(self.subplans)) != len(self.subplans):
            raise ValueError("subplans has a duplicate subplan")
        return self


class Stage(PlanModel):
    """D-134: this revision is a stage, the projection of the draft onto these subplans."""
    version: int = Field(ge=1, le=1, description="stage contract version; this reader knows 1 (a strict int: "
                                                     "Literal[1] would also accept true)")
    subplans: list[SubplanId] = Field(min_length=1)

    @model_validator(mode="after")
    def _distinct(self):
        if len(set(self.subplans)) != len(self.subplans):
            raise ValueError("subplans has a duplicate subplan")
        return self


# ---------------------------------------------------------------------------------------------------- plans

class Plan100(PlanModel):
    """A frozen PLAN.json revision, schema 1.0.0: milestones and classified tasks."""
    schema_version: Literal["1.0.0"]
    plan_id: Text
    revision: int = Field(ge=1, le=MAX_REVISION)
    spec_ref: RelativePath
    milestones: list[Milestone] = Field(min_length=1)
    tasks: list[Task100] = Field(min_length=1, max_length=MAX_TASKS)
    generated_paths: list[GeneratedPath] = Field(default=None, max_length=256)
    generated_command: Command | Annotated[dict[Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]{1,128}$")], Command],
                                           Field(min_length=1, max_length=256)] = None

    @model_validator(mode="after")
    def _references(self):
        found = reference_issues(self)
        if found:
            raise PydanticCustomError("plan_references", "{count} inconsistent identifier(s): {issues}",
                                      {"count": len(found), "issues": found})
        return self


class Plan110(Plan100):
    """Schema 1.1.0: every classification is argued in classification_evidence."""
    schema_version: Literal["1.1.0"]
    tasks: list[Task110] = Field(min_length=1, max_length=MAX_TASKS)


class Plan120(Plan110):
    """Schema 1.2.0: requirement coverage, task kind, verification categories and interfaces."""
    schema_version: Literal["1.2.0"]
    requirements: list[RequirementId] = Field(min_length=1)
    tasks: list[Task120] = Field(min_length=1, max_length=MAX_TASKS)
    interfaces: list[Interface] = Field(default_factory=list)


class Plan130(Plan120):
    """Schema 1.3.0: functional subplans, composition gates, UI contracts, verification environments, stages."""
    schema_version: Literal["1.3.0"]
    tasks: list[Task130] = Field(min_length=1, max_length=MAX_TASKS)
    subplans: list[Subplan] = Field(default_factory=list, max_length=64)
    composition_gates: list[CompositionGate] = Field(default_factory=list, max_length=32)
    stage: Stage = None


PLAN_MODELS = {"1.0.0": Plan100, "1.1.0": Plan110, "1.2.0": Plan120, "1.3.0": Plan130}
Plan = Plan100 | Plan110 | Plan120 | Plan130
PlanDocument = Annotated[Plan, Field(discriminator="schema_version")]
PLAN_ADAPTER: TypeAdapter[Plan] = TypeAdapter(PlanDocument)


# ---------------------------------------------------------------------------------------------------- entry points

class PlanContractError(ValueError):
    """The plan does not satisfy its schema version's contract; `issues` are actionable `path: message` lines."""

    def __init__(self, issues: list[str]):
        self.issues = list(issues)
        more = f" (+{len(self.issues) - 6} more)" if len(self.issues) > 6 else ""
        super().__init__("PLAN_CONTRACT: " + "; ".join(self.issues[:6]) + more)


def _path(loc: tuple) -> str:
    out = ""
    for part in loc:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out


def _issues(error: ValidationError) -> list[str]:
    lines: list[str] = []
    for item in error.errors(include_url=False):
        loc = tuple(item["loc"])
        if loc and loc[0] in SCHEMA_VERSIONS:
            loc = loc[1:]
        where = _path(loc)
        kind = item["type"]
        if kind == "plan_references":
            lines += list(item["ctx"]["issues"])
            continue
        if kind == "extra_forbidden":
            message = "unknown field for this schema version (a renamed or misspelled key is refused, not ignored)"
        elif kind == "missing":
            message = "required field missing"
        elif kind in ("union_tag_invalid", "union_tag_not_found"):
            where, message = "schema_version", (f"must be one of {', '.join(SCHEMA_VERSIONS)} "
                                                f"(got {item['ctx'].get('tag', 'nothing')})")
        else:
            message = item["msg"].removeprefix("Value error, ")
        lines.append(f"{where}: {message}" if where else message)
    return lines


def validate(data: object) -> Plan:
    """The typed plan, or PlanContractError listing every shape issue (or, once the shape holds, every reference)."""
    try:
        return PLAN_ADAPTER.validate_python(data)
    except ValidationError as exc:
        raise PlanContractError(_issues(exc)) from None


def issues(data: object) -> list[str]:
    """[] when `data` (a parsed PLAN.json) satisfies the contract, else the issues."""
    try:
        validate(data)
    except PlanContractError as exc:
        return exc.issues
    return []


def parse_text(text: str | bytes) -> object:
    """Strict JSON: NaN/Infinity and duplicate keys are refused, as the planner's reader does."""
    raw = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    if len(raw) > MAX_BYTES:
        raise PlanContractError([f"plan: larger than {MAX_BYTES} bytes"])
    try:
        return strict_json(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise PlanContractError([f"plan: not valid JSON ({exc})"]) from None


def validate_text(text: str | bytes) -> Plan:
    return validate(parse_text(text))


def validate_file(path: str | Path) -> Plan:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise PlanContractError([f"{path}: unreadable ({type(exc).__name__})"]) from None
    return validate_text(raw)


__all__ = ["DIMENSIONS", "MAX_BYTES", "PLAN_ADAPTER", "PLAN_MODELS", "SCHEMA_VERSIONS", "Plan", "PlanContractError",
           "PlanDocument", "issues", "parse_text", "reference_issues", "validate", "validate_file", "validate_text"]
