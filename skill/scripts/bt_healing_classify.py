"""Why a run stopped, placed in a closed taxonomy from the evidence (REQ-030 step 5, the diagnosis half of self-healing).

`classify(request, ...)` reads what the run knows about one open stop (the reason code, the LAST real error, the verifier's
notes, the attempt history, the plan and who owns which files) and returns a `Case`: one class of `bt_interventions.CLASSES`
plus the evidence lines that justify it. Rules, in this order, and the first that matches wins:

1. the last real error beats any heuristic about older text or the reason code (REQ-029: a stop was called "quota" because
   `429` and `quota` appeared somewhere in the bundle, when the last error was an unclassified route);
2. integration -> transient -> criterion -> plan -> environment -> quota -> test failures (regression / plan defect);
3. nothing recognised: no case. An unplaced stop is never repaired by guesswork; it stays a card for a person.

Nothing here changes the run. The repairs live in `bt_scheduler_healing`.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

CLASSES = ("plan_defect", "integration_defect", "regression", "environment", "criterion_unmapped", "quota", "transient")

INTEGRATION = re.compile(r"INTEGRATION_CONFLICT|INTEGRATION_FILES_LOST|PREDECESSOR_NEEDS_RESOLUTION|PREDECESSOR_HANDOFF_MISSING"
                         r"|integration gate:|REVERTED|UNRESOLVED", re.I)
TRANSIENT = re.compile(r"ROUTE_INVALID|SANDBOX_UNAVAILABLE|RUNNER_BUSY|CHECK_TIMEOUT|ENGINE_INTERRUPTED|execution_unsettled"
                       r"|ECONNRESET|ETIMEDOUT|EAI_AGAIN|temporarily unavailable|decision was replaced|stale_or_cancelled|manual_cancel")
CRITERION = re.compile(r"CRITERION_UNVERIFIABLE|CRITERION_AMBIGUOUS|CRITERION_MANUAL|CHECK_UNMAPPED")
PLAN = re.compile(r"CHECK_UNSUPPORTED|not a git repository|relative executable|CHECK_PRODUCTION_ACTION")
ENVIRONMENT = re.compile(r"ENOTCACHED|only-if-cached|EROFS|read-only file system|ENOSPC|No space left|ECONNREFUSED|connection refused|could not connect to server"
                         r"|Cannot find module '[^'.\/][^']*'|No module named|\b[A-Z][A-Z0-9]*_[A-Z0-9_]{2,}\b[^\n]{0,40}\b(?:is not set|is missing|undefined)", re.I)
# a real quota/rate-limit message, never a bare number or a word that happens to be in the text
QUOTA = re.compile(r"usage limit|rate[- ]?limit(?:ed)?|quota (?:exceeded|exhausted|reached)|insufficient[_ ]quota|too many requests"
                   r"|you(?:'ve| have) hit your limit|\b429\b[^\n]{0,60}(?:too many|rate|limit)", re.I)
FAIL_LINE = re.compile(r"^(?:FAIL|ERROR):\s*(?P<test>\S+)\s*\((?P<where>[\w.]+)\)", re.M)
FAIL_FILE = re.compile(r"(?:FAIL|✖|✗|not ok)\s+(?P<file>[\w./-]+\.(?:test|spec)\.\w+|[\w./-]*test_[\w]+\.py)")
TRACE_FILE = re.compile(r'File "(?P<file>[^"]+?(?:test_[\w]+|[\w]+_test)\.py)"')


# what `bt_block_diagnosis` calls a cause -> the class of the taxonomy (for the interventions an owner makes by hand)
FROM_DIAGNOSIS = {"conflict": "integration_defect", "plan": "plan_defect", "environment": "environment",
                  "dependency": "environment", "quota": "quota", "transient": "transient", "cancelled": "transient",
                  "verifier": "criterion_unmapped", "manual": "criterion_unmapped", "code": "regression"}


def class_of_diagnosis(diagnosis: dict | None) -> str:
    return FROM_DIAGNOSIS.get((diagnosis or {}).get("kind", ""), "unknown")


@dataclass(frozen=True)
class Case:
    request_id: str
    task: str
    kind: str                                   # one of CLASSES
    evidence: tuple[str, ...]
    owners: tuple[str, ...] = ()                # accepted tasks that own the failing surface (regression)
    failing: tuple[str, ...] = ()               # failing test modules/files found in the verifier's output
    signature: str = field(default="")

    def describe(self) -> str:
        return f"{self.kind}: {'; '.join(self.evidence[:3])}"[:600]


def _normal(text: str) -> str:
    """The decisive part of an error with the volatile bits removed, so the same failure has the same signature."""
    text = re.sub(r"0x[0-9a-f]+|\b[0-9a-f]{7,64}\b|\b\d+(?:\.\d+)?\b|att-\d+|/[\w./-]+", "#", text.lower())
    return re.sub(r"\s+", " ", text).strip()[:240]


def signature(task: str, kind: str, decisive: str) -> str:
    return hashlib.sha256(f"{task}\0{kind}\0{_normal(decisive)}".encode()).hexdigest()[:16]


def last_error(request: dict, verify: str, failures) -> str:
    """The most recent real error: the failure of the last attempt, else the verifier's note, else what the card shows."""
    for item in reversed([f for f in (failures or ()) if f]):
        return str(item)
    return verify or str(request.get("error") or "")


def failing_tests(text: str) -> tuple[str, ...]:
    """Test modules/files named by the verifier's output: unittest `FAIL: name (mod.Class.name)`, node `FAIL file.test.ts`,
    pytest-style `test_x.py` files in a traceback."""
    found: list[str] = []
    for match in FAIL_LINE.finditer(text):
        parts = match["where"].split(".")
        found.append(next((part for part in parts if part.startswith("test_")), parts[0]))
    found += [m["file"] for m in FAIL_FILE.finditer(text)]
    found += [m["file"] for m in TRACE_FILE.finditer(text)]
    return tuple(dict.fromkeys(f for f in found if f))


def owners_of(failing, plan, doc: dict, task: str) -> tuple[str, ...]:
    """Accepted tasks (not `task`) whose declared files contain a failing test module/file."""
    if plan is None or not failing:
        return ()
    done = {t for t, rec in (doc.get("tasks") or {}).items() if rec.get("state") == "completed"}
    found = []
    for spec in getattr(plan, "tasks", ()):
        if spec.id == task or spec.id not in done:
            continue
        for path in spec.expected_paths:
            stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if any(f == stem or f.endswith(path) or path.endswith(f) or f.rsplit("/", 1)[-1].rsplit(".", 1)[0] == stem
                   for f in failing):
                found.append(spec.id)
                break
    return tuple(found)


def classify(request: dict, *, verify: str = "", failures=(), plan=None, doc: dict | None = None) -> Case | None:
    doc = doc or {}
    task, error = request.get("task", ""), last_error(request, verify, failures)
    diagnosis = request.get("diagnosis") or {}
    review_text = "\n".join(request.get("evidence") or ()) if request.get("source") == "review" else ""
    text = "\n".join(p for p in (error, review_text, verify) if p)
    reason = str(request.get("reason") or "")

    def case(kind: str, *evidence: str, decisive: str = "", **extra) -> Case:
        lines = tuple(e for e in (*evidence, f"reason code: {reason}" if reason else "") if e)
        return Case(request.get("id", ""), task, kind, lines, signature=signature(task, kind, decisive or text), **extra)

    if INTEGRATION.search(text) or diagnosis.get("kind") == "conflict":
        return case("integration_defect", f"integration evidence in the last error: {_first(INTEGRATION, text)}")
    if TRANSIENT.search(text) or diagnosis.get("kind") in ("cancelled", "transient"):
        return case("transient", f"transient signature: {_first(TRANSIENT, text) or diagnosis.get('kind')}")
    if CRITERION.search(text):
        return case("criterion_unmapped", f"verifier doubt about the mapping of evidence: {_first(CRITERION, text)}")
    if PLAN.search(text) or diagnosis.get("kind") == "plan":
        return case("plan_defect", f"a check of the plan cannot work as written: {_first(PLAN, text) or diagnosis.get('headline', '')}")
    hit = ENVIRONMENT.search(text)
    if hit or diagnosis.get("kind") in ("environment", "dependency"):
        return case("environment", f"environment signature: {(hit.group(0) if hit else diagnosis.get('headline', ''))[:120]}")
    if QUOTA.search(error) or reason.endswith(("quota_reset_unknown", "wait_limit", "wait_window_exceeded")):
        return case("quota", f"quota signature in the last error: {_first(QUOTA, error) or reason}", decisive=error)
    if "audit gate:" in text and reason.endswith(("rework_impact", "rework_limit")):
        return case("regression", "the independent audit still finds blocking problems after its remediation rounds and would "
                    "send back accepted tasks", decisive="audit gate " + task)
    failing = failing_tests(text)
    if failing:
        owners = owners_of(failing, plan, doc, task)
        if owners:
            return case("regression", f"failing tests {', '.join(failing[:4])} belong to accepted {', '.join(owners)}",
                        owners=owners, failing=failing)
        if _executor_only(plan, task):
            return case("plan_defect", f"{task} only runs and records, and its checks fail on {', '.join(failing[:4])}: it "
                        "cannot repair the code itself", failing=failing)
    return None


def unplaced(request: dict, *, verify: str = "", failures=()) -> Case:
    """A stop the rules do not place, as a case of class `unknown`: the signature is the task plus the decisive error, so the same
    failure coming back is recognised. Only the model step of the healing may act on it (REQ-029 R3/R4)."""
    error = last_error(request, verify, failures)
    reason = str(request.get("reason") or "")
    lines = tuple(e for e in (f"unplaced error: {error[:200]}" if error else "", f"reason code: {reason}" if reason else "") if e)
    return Case(request.get("id", ""), request.get("task", ""), "unknown", lines or ("no evidence text",),
                signature=signature(request.get("task", ""), "unknown", error or reason))


def _first(pattern: re.Pattern, text: str) -> str:
    match = pattern.search(text or "")
    return match.group(0)[:100] if match else ""


def _executor_only(plan, task: str) -> bool:
    try:
        return plan.task(task).meta.get("kind") in ("test", "audit")
    except Exception:  # noqa: BLE001 - an unknown task is not "executor only"
        return False
