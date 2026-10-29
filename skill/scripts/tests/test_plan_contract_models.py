"""Plan/subplan Pydantic contracts (bt_contracts.plan) against the stdlib readers they are proven equivalent to.

REQ-030 item 7. Runs in the uv environment (pydantic):
    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_plan_contract_models

Readers compared, each through its door:
- runtime loader: the core's `load_plan` (bt_durable.legacy), which both runtimes use to consume a frozen plan;
- planner: `bt_plan_adapter.validate_candidate`, the authoring and freeze gate.

The contract = the structural rules of both readers + closed objects (an unknown key is refused). The planner's
authoring rules (text and evidence quality, coverage totality, roles, ordering, policies that tightened after plans
were frozen) are not part of it; `AUTHORING_POLICY` names them, so a planner rejection the contract does not share
must be made only of those, and anything else is reported as a disagreement with its file and reason.

The corpus is the real bitácora (`$BT_REAL_BITACORA`, default ~/bitacora). When it is absent the test says so loudly
on stderr and compares the bitácora snapshot checked into this repository instead; it fails when neither has plans.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_core
import bt_plan_adapter
import bt_scheduler_decision_adapter
import bt_scheduler_executor_adapter
import bt_scheduler_quality
from bt_contracts import plan as contract
from bt_contracts import schemas
from bt_contracts.execution import RunRef
from bt_durable import cli, legacy
from plan_contract_cases import CASES, base

FROZEN_GLOB = "*/requirements/*/plan-revisions/PLAN.r*.json"

# Planner rules the contract leaves to authoring (bt_contracts/plan.py docstring). "Mixed" codes also fire on a
# missing reference; that half is enforced by the contract and the runtime loader as well.
AUTHORING_POLICY = tuple((name, re.compile(pattern)) for name, pattern in (
    ("audit findings ledger (added after REQ-027 r1-r3 were frozen)",
     r"\.expected_paths: an audit task must list exactly one findings ledger"),
    ("audit after an integration test (added after REQ-027 r1-r2 were frozen)",
     r": an audit needs a `kind: test` task with an `integration` command verification"),
    ("single audit", r": the plan has a single audit"),
    ("orphan milestone", r": orphan milestone \(no task belongs to it\)$"),
    ("uncovered requirement", r"^requirements\.\S+: no task covers this requirement$"),
    ("SPEC agreement", r"^requirements: .*SPEC"),
    ("milestone order", r"\.after: \S+ belongs to a later milestone"),
    ("interface ordering", (r"^interfaces\[\d+\]\.(?:consumer_tasks\[\d+\]: producer \S+ is not an ancestor|"
                            r"integration_task: \S+ must depend on)")),
    ("unordered shared work", r": nothing orders them yet both touch"),
    ("text quality", (r"promises parallel safety|is a placeholder|is too short|repeats the same words|"
                      r"repeats the title|duplicate criterion|cannot fail, so it verifies nothing|"
                      r"admits that the number|share the same justification|shares no term")),
    ("evidence strength", (r"\.classification_evidence\.\w+\.evidence\[\d+\]: (?:command evidence|precedent|file|"
                           r"task |spec path|command )|\.confidence: high|\.coupling: (?:medium|high) names neither")),
    ("git-ignored check input", r"is git-ignored and is not produced"),
    ("schema 1.3 coverage, roles and ordering",
     (r"^(?:SUBPLAN_NO_OUTCOME|SUBPLAN_EMPTY|SUBPLAN_CRITERION_UNCARRIED|SUBPLAN_LATE_CHECKPOINT|LATE_CHECKPOINT|"
      r"SUBPLAN_AUDIT|SUBPLAN_ORDER|SUBPLAN_EDGE|SUBPLAN_CYCLE|COMPOSITION_MISSING|REQUIREMENT_ORPHAN|"
      r"TASK_OUTSIDE_SUBPLAN|EXTERNAL_ONLY_IMPLEMENT|FILE_EXISTENCE_CHECK|UI_WORK_UNDECLARED|UI_GATE_ORDER|"
      r"UI_REVIEW_ORDER): ")),
    ("schema 1.3 roles (mixed)",
     (r"^(?:SUBPLAN_MILESTONE: T|SUBPLAN_COVERAGE: (?:T|SP-\d+: each)|SUBPLAN_INVALID: SP-\d+\.checkpoints|"
      r"UI_GATE_MISSING: SP-|COMPOSITION_INVALID: |SUBPLAN_CONTRACT: SP-\d+\.(?:produces\[\d+\]: invalid|"
      r"consumes\[\d+\]\.verified_by))")),
    ("owner composition", r"^\w+: owner: "),
))
UNKNOWN_FIELD = "unknown field for this schema version"


def real_root() -> tuple[Path, bool]:
    configured = os.environ.get("BT_REAL_BITACORA")
    root = Path(configured) if configured else Path.home() / "bitacora"
    if root.is_dir() and any(root.glob(FROZEN_GLOB)):
        return root, True
    return REPO / "bitacora", False


def plan_files(root: Path) -> list[Path]:
    """Every PLAN.json draft and frozen PLAN.r*.json under root, hidden folders (.trash, .state) included."""
    found = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for name in files:
            if name == "PLAN.json" or (Path(dirpath).name == "plan-revisions" and name.startswith("PLAN.r")
                                       and name.endswith(".json")):
                found.append(Path(dirpath) / name)
    return sorted(found)


def runtime_error(raw: bytes) -> str | None:
    """None when the runtime loader accepts the exact bytes; else its error (a crash counts as a refusal)."""
    try:
        legacy.load_plan(raw, approved_sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:  # noqa: BLE001 - TypeError on unhashable values is a refusal too
        return f"{type(exc).__name__}: {exc}"
    return None


def policy_rule(error: str) -> str | None:
    return next((name for name, pattern in AUTHORING_POLICY if pattern.search(error)), None)


class Verdicts:
    """One plan file seen by the contract, the runtime loader and the planner."""

    def __init__(self, path: Path, root: Path):
        self.path, self.name = path, str(path.relative_to(root))
        raw = path.read_bytes()
        try:
            data = contract.parse_text(raw)
        except contract.PlanContractError as exc:
            data, self.contract = None, exc.issues
        else:
            self.contract = contract.issues(data)
        self.runtime = runtime_error(raw)
        self.planner = list(bt_plan_adapter.validate_candidate(data)) if data is not None else ["not JSON"]
        self.structural = [e for e in self.planner if policy_rule(e) is None]

    def disagreement(self) -> str | None:
        """Why the contract's verdict is not explained by the legacy readers, or None."""
        if self.runtime and not self.contract:
            return f"the runtime loader refuses ({self.runtime[:200]}) but the contract accepts"
        if self.structural and not self.contract:
            return f"the planner refuses on structure ({'; '.join(self.structural[:3])}) but the contract accepts"
        if self.contract and not self.planner and not self.runtime and \
                not all(UNKNOWN_FIELD in issue for issue in self.contract):
            return f"the contract refuses ({'; '.join(self.contract[:3])}) but both legacy readers accept"
        return None


class PlanCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.real = real_root()
        if not cls.real:
            print(f"\n!!! REAL BITÁCORA ABSENT ({os.environ.get('BT_REAL_BITACORA') or Path.home() / 'bitacora'} has "
                  f"no frozen plan): comparing the repository snapshot {cls.root} instead !!!", file=sys.stderr)
        cls.frozen = [Verdicts(path, cls.root) for path in sorted(cls.root.glob(FROZEN_GLOB))]

    def test_the_corpus_is_there(self):
        self.assertTrue(self.frozen, f"no frozen plan under {self.root}/{FROZEN_GLOB}: nothing was compared")
        versions = {json.loads(v.path.read_text(encoding="utf-8")).get("schema_version") for v in self.frozen}
        print(f"\nfrozen plans compared: {len(self.frozen)} from {self.root} (schema {', '.join(sorted(versions))})",
              file=sys.stderr)

    def test_every_frozen_plan_gets_the_runtime_loaders_verdict(self):
        differ = [f"{v.name}: contract {'refuses: ' + '; '.join(v.contract[:3]) if v.contract else 'accepts'}, "
                  f"runtime loader {'refuses: ' + v.runtime[:200] if v.runtime else 'accepts'}"
                  for v in self.frozen if bool(v.contract) != bool(v.runtime)]
        self.assertEqual(differ, [], "\n".join(differ))

    def test_every_frozen_plan_gets_the_planners_structural_verdict(self):
        differ, policy_only = [], []
        for v in self.frozen:
            if bool(v.contract) != bool(v.structural):
                differ.append(f"{v.name}: contract {'; '.join(v.contract[:3]) or 'accepts'} | planner structural "
                              f"{'; '.join(v.structural[:3]) or 'accepts'}")
            elif v.planner and not v.contract:
                rules = sorted({policy_rule(e) for e in v.planner})
                policy_only.append(f"{v.name}: {', '.join(rules)}")
        if policy_only:
            print("\nrefused by the planner's authoring policy only (accepted by the contract and the runtime "
                  "loader):\n  " + "\n  ".join(policy_only), file=sys.stderr)
        self.assertEqual(differ, [], "\n".join(differ))
        accepted = sum(not v.contract for v in self.frozen)
        print(f"\ncontract accepts {accepted}/{len(self.frozen)} frozen plans; disagreements: 0", file=sys.stderr)

    def test_every_plan_file_of_the_bitacora_is_explained(self):
        """Drafts, trash, artifacts and lab copies too: refusals by the contract are refusals of a legacy reader
        (or an unknown key), and every legacy structural refusal is a contract refusal."""
        found = [Verdicts(path, self.root) for path in plan_files(self.root)]
        differ = [f"{v.name}: {why}" for v in found if (why := v.disagreement())]
        stricter = [v.name for v in found if v.contract and not v.planner and not v.runtime]
        print(f"\nplan files explained: {len(found)}; refused only by the contract for unknown keys: "
              f"{len(stricter)} {stricter[:4]}", file=sys.stderr)
        self.assertEqual(differ, [], "\n".join(differ))


class StructuralDefects(unittest.TestCase):
    def test_the_bases_satisfy_every_reader(self):
        for version in contract.SCHEMA_VERSIONS:
            plan = base(version)
            raw = json.dumps(plan).encode()
            with self.subTest(version=version):
                self.assertEqual(contract.issues(plan), [])
                self.assertEqual(bt_plan_adapter.validate_candidate(plan), ())
                self.assertIsNone(runtime_error(raw))

    def test_each_defect_is_refused_by_the_contract_and_pinned_for_the_legacy_readers(self):
        families = set()
        for case in CASES:
            plan = case.plan()
            with self.subTest(case=case.name):
                issues = contract.issues(plan)
                self.assertTrue(any(case.expect in issue for issue in issues), (case.expect, issues))
                self.assertEqual(bool(bt_plan_adapter.validate_candidate(plan)), case.planner, "planner verdict moved")
                self.assertEqual(bool(runtime_error(json.dumps(plan).encode())), case.runtime,
                                 "runtime loader verdict moved")
                families.add(case.family)
        self.assertEqual(families, {"req/req_id", "array/object", "missing field", "unknown value", "identifiers"})

    def test_every_issue_names_where_it_is(self):
        plan = base("1.3.0")
        plan["tasks"][2]["kind"] = "deploy"
        plan["subplans"][1]["consumes"][0]["dependency"] = "soon"
        issues = contract.issues(plan)
        self.assertTrue(any(i.startswith("tasks[2].kind: ") for i in issues), issues)
        self.assertTrue(any(i.startswith("subplans[1].consumes[0].dependency: ") for i in issues), issues)

    def test_strict_json_text(self):
        for text in ('{"schema_version": "1.0.0", "schema_version": "1.0.0"}', '{"revision": NaN}', "[1,"):
            with self.subTest(text=text), self.assertRaises(contract.PlanContractError):
                contract.validate_text(text)
        self.assertEqual(contract.validate_text(json.dumps(base("1.1.0"))).schema_version, "1.1.0")


class DurableStartRefusesBeforeEnqueue(unittest.TestCase):
    """`bt-durable start` / migration pre-flight: a defective frozen plan stops before an owner record, a workflow
    or an agent exists (no quota is spent)."""

    def setUp(self):
        lab = os.environ.get("BT_LAB_DIR") or None
        self.tmp = tempfile.TemporaryDirectory(prefix="plan-contract-", dir=lab)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "bitacora"
        (self.root / "proj").mkdir(parents=True)
        (self.root / "proj" / "project.json").write_text(json.dumps({"work": False}))
        self.rdir = self.root / "proj" / "requirements" / "REQ-901-contract"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        self.clients: list[str] = []
        for target, value in ((bt_core, "ROOT"), (bt_core, "STATE")):
            patcher = patch.object(target, value, self.root if value == "ROOT" else self.root / ".state")
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(cli, "_client", self._client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _client(self):
        self.clients.append("created")

        class Recorder:
            def start(inner, run, settings, progress=None):
                self.clients.append(f"start {run.run_id}")
                return f"bt:{run.run_id}"

            def close(inner):
                pass
        return Recorder()

    def freeze(self, plan: dict) -> Path:
        raw = json.dumps(plan, indent=1).encode()
        path = self.rdir / "plan-revisions" / "PLAN.r1.json"
        path.write_bytes(raw)
        (self.rdir / "plan-revisions" / "MANIFEST.json").write_text(json.dumps(
            {"schema": 1, "revisions": [{"revision": 1, "sha256": hashlib.sha256(raw).hexdigest()}]}))
        return path

    def written(self) -> list[str]:
        return sorted(p.name for p in self.rdir.iterdir() if p.name != "plan-revisions")

    def test_every_defect_stops_start_before_anything_is_enqueued(self):
        for case in CASES:
            self.freeze(case.plan())
            with self.subTest(case=case.name), self.assertRaises(SystemExit) as stop:
                cli.main(["start", "proj", "REQ-901"])
            self.assertIn("PLAN_CONTRACT", str(stop.exception.code))
            self.assertEqual(self.clients, [], "a durable client was created for a defective plan")
            self.assertEqual(self.written(), [], "an owner record or run file was written for a defective plan")

    def test_migration_pre_flight_refuses_the_same_plan(self):
        case = next(c for c in CASES if c.family == "req/req_id")
        path = self.freeze(case.plan())
        run = RunRef(project="proj", req="REQ-901", plan_id="REQ-901", revision=1,
                     plan_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), plan_path=path)
        with self.assertRaises(SystemExit) as stop:
            cli.preflight(run, self.rdir)
        self.assertIn("req_id: unknown field", str(stop.exception.code))

    def test_a_valid_plan_reaches_the_enqueue(self):
        self.freeze(base("1.3.0"))
        self.assertEqual(cli.main(["start", "proj", "REQ-901"]), 0)
        self.assertEqual(self.clients, ["created", "start proj:REQ-901:r1"])
        self.assertIn("RUN.durable-run.json", self.written())


class OneSource(unittest.TestCase):
    def test_generated_plan_schema_is_fresh(self):
        expected = schemas.plan_file()[schemas.PLAN_SCHEMA_PATH]
        self.assertTrue(schemas.PLAN_SCHEMA_PATH.is_file(), "run `uv run python -m bt_contracts.schemas`")
        self.assertEqual(schemas.PLAN_SCHEMA_PATH.read_text(encoding="utf-8"), expected,
                         "stale: run `uv run python -m bt_contracts.schemas` (from skill/scripts)")
        self.assertNotIn(schemas.PLAN_SCHEMA_PATH, schemas.stale())
        published = json.loads(expected)
        self.assertEqual(sorted(published["discriminator"]["mapping"]), list(contract.SCHEMA_VERSIONS))

    def test_every_reader_declares_the_contract_versions(self):
        declared = {"runtime loader": legacy.core.PLAN_SCHEMA_CAPABILITIES,
                    "executor": bt_scheduler_executor_adapter.PLAN_SCHEMA_CAPABILITIES,
                    "decision": bt_scheduler_decision_adapter.PLAN_SCHEMA_CAPABILITIES,
                    "verifier": bt_scheduler_quality.PLAN_SCHEMA_CAPABILITIES}
        for reader, versions in declared.items():
            with self.subTest(reader=reader):
                self.assertEqual(sorted(versions), list(contract.SCHEMA_VERSIONS))

    def test_vocabularies_match_the_planner_and_the_runtime_loader(self):
        planner = bt_plan_adapter.planner_contract
        self.assertEqual(contract.COMPLEXITY, planner.COMPLEXITY)
        self.assertEqual(contract.SCOPE, planner.SCOPE)
        self.assertEqual(contract.LEVELS, planner.LEVELS)
        self.assertEqual(contract.VERIFICATION_TYPES, planner.VERIFICATION_TYPES)
        self.assertEqual(contract.VERIFICATION_CATEGORIES, planner.VERIFICATION_CATEGORIES)
        self.assertEqual(contract.TASK_KINDS, planner.TASK_KINDS)
        self.assertEqual(contract.TASK_KINDS_13, planner.TASK_KINDS_13)
        self.assertEqual(contract.MAX_BYTES, planner.MAX_BYTES)
        self.assertEqual(set(contract.TASK_KINDS), set(legacy.core.plan.TASK_KINDS))
        self.assertEqual(set(contract.TASK_KINDS_13), set(legacy.core.plan.TASK_KINDS_13))
        self.assertEqual(set(contract.VERIFICATION_CATEGORIES), set(legacy.core.plan.VERIFICATION_CATEGORIES))
        models = contract.PLAN_MODELS
        literal = {name: models["1.3.0"].model_fields["tasks"].annotation.__args__[0].model_fields[name].annotation
                   for name in ("complexity", "scope", "risk", "kind")}
        self.assertEqual(literal["complexity"].__args__, contract.COMPLEXITY)
        self.assertEqual(literal["scope"].__args__, contract.SCOPE)
        self.assertEqual(literal["risk"].__args__, contract.LEVELS)
        self.assertEqual(literal["kind"].__args__, contract.TASK_KINDS_13)


if __name__ == "__main__":
    unittest.main()
