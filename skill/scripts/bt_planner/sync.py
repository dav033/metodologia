"""PLAN.md <-> PLAN.json for one plan directory: skeleton derivation, consistency by ids/milestones/dependencies,
approval freeze, and a read-only compatibility report for plans written before the contract existed.

PLAN.json owns the classification; PLAN.md stays the human narrative. What is compared is everything the task line
states structurally, never free prose: ids (each defined once on both sides), milestone membership and titles, task
titles, `repo` against `repository`, `after` links, a stated `verify` against the plan's command verifications and a
legacy `risk:` on the same low/medium/high scale. A value PLAN.md does not state is not a contradiction; a value it
states differently is an error. Nothing here invents classification values; the only files written are PLAN.json
(init) and `plan-revisions/` (freeze).
"""
from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from pathlib import Path

from . import contract as pc
from . import evidence as ev
from . import markdown as md
from . import quality
from . import revisions as rev
from . import traceability

PLAN_MD = "PLAN.md"
PLAN_JSON = "PLAN.json"
DEFAULT_SPEC_REF = "SPEC.md"
# A generated progress block, `<!-- <owner>:status:begin -->` ... `<!-- <owner>:status:end -->`, is not narrative and not
# drift: whoever generates it names itself in the marker, the planner only knows the shape.
_STATUS_REGION = re.compile(r"<!-- ([A-Za-z0-9_.-]+):status:begin -->.*?<!-- \1:status:end -->\n?", re.S)
APPROVED_STATES = ("approved", "launched", "done", "merged")  # PLAN.md `status:` words that allow a freeze


def default_plan_id(directory: Path) -> str:
    """`REQ-042-some-slug` -> `REQ-042`; any other directory name is used as it is."""
    name = Path(directory).resolve().name
    found = re.match(r"[A-Za-z][A-Za-z0-9]*-[0-9]+", name)
    return found.group(0) if found else name


def narrative_digest(directory: Path) -> str | None:
    """Digest of what a reader of PLAN.md is told, ignoring what legitimately changes after approval: the front
    matter (status), dated log lines and the checkbox marks. Whoever consumes the live PLAN.md later reads it as if
    it had been approved, so prose changed after approval must not pass unnoticed."""
    try:
        text = (Path(directory) / PLAN_MD).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    text = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)
    text = _STATUS_REGION.sub("", text)
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*-\s+\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}\b", line):
            continue
        lines.append(re.sub(r"\[[xX]\]", "[ ]", line).strip())
    return rev.sha256("\n".join(l for l in lines if l))


def plan_status(directory: Path) -> str:
    try:
        return md.status((Path(directory) / PLAN_MD).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return ""


def _same_text(a: object, b: object) -> bool:
    """Titles compare without markup noise (emphasis/backticks), spacing or case: a rewording is a contradiction, a
    different capitalisation is not."""
    def norm(value: object) -> str:
        text = re.sub(r"[*`]", "", str(value or ""))
        text = text.strip("_")  # emphasis around an entire title
        text = re.sub(r"(?<!\w)_([^ \t\r\n]+)_(?!\w)", r"\1", text)  # paired emphasis, never identifier underscores
        return re.sub(r"\s+", " ", text).strip().casefold()
    return norm(a) == norm(b)


def skeleton(directory: Path, plan_id: str | None = None) -> dict:
    """Derive declared requirements and task metadata; classification and verification categories are never guessed."""
    parsed, stones = md.read(Path(directory) / PLAN_MD)
    titles = {m["id"]: m["title"] for m in stones}
    tasks = []
    for item in parsed:
        entry: dict = {"id": item["id"], "title": item["title"], "after": list(item["after"])}
        if item.get("milestone"):
            entry["milestone_id"] = item["milestone"]
        if item.get("repo"):
            entry["repository"] = item["repo"]
        if item.get("files"):
            entry["expected_paths"] = list(item["files"])
        if item.get("resources"):
            entry["shared_resources"] = list(item["resources"])
        entry["covers"] = list(item.get("covers") or [])
        if item.get("kind"):
            entry["kind"] = item["kind"]
        if item.get("verify"):
            entry["verification"] = [{"type": "command", "value": item["verify"],
                                      "purpose": "verify command declared in PLAN.md"}]
        tasks.append(entry)
    seen = list(dict.fromkeys(t["milestone_id"] for t in tasks if "milestone_id" in t))
    last = rev.latest(directory)
    spec_ids = traceability.read_spec_ids(directory, DEFAULT_SPEC_REF) or set()
    return {"schema_version": pc.SCHEMA_VERSION, "plan_id": plan_id or default_plan_id(directory), "revision": (last["revision"] + 1) if last else 1,
            "spec_ref": DEFAULT_SPEC_REF,
            "milestones": [{"id": mid, "title": titles.get(mid, "")} for mid in seen], "tasks": tasks,
            "requirements": sorted(spec_ids)}


def write_skeleton(directory: Path, force: bool = False, plan_id: str | None = None) -> Path:
    target = Path(directory) / PLAN_JSON
    if target.exists() and not force:
        raise pc.PlanContractError("PLAN_EXISTS", [f"{target.name} already exists; edit it, or pass --force to rebuild"])
    ambiguous = md_problems(directory)
    if ambiguous:
        raise pc.PlanContractError("PLAN_MD_AMBIGUOUS", ambiguous)
    data = skeleton(directory, plan_id)
    if not data["tasks"]:
        raise pc.PlanContractError("PLAN_MD_EMPTY", ["PLAN.md has no task lines (`- [ ] T1 — title · …`) to derive from"])
    # Skeleton is incomplete by design: write it as-is (not canonicalised through validation).
    target.write_text(pc.dumps(data), encoding="utf-8")
    return target


def _dicts(value: object) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def md_problems(directory: Path) -> list[str]:
    """PLAN.md ambiguities that exist before any comparison: ids or milestone headings defined twice, repeated or
    unusable fields (`markdown.parse_document`). Independent of PLAN.json."""
    return md.read_document(Path(directory) / PLAN_MD)["problems"]


def consistency(directory: Path, plan: dict, plan_id: str | None = None) -> list[str]:
    """Differences between PLAN.md and PLAN.json (empty list = consistent): ids defined once on each side, milestone
    membership and titles, task titles, repo, `after`, stated verify command, and a legacy risk on the same scale.
    Schema 1.2.0 also compares explicitly stated `covers` and `kind`; legacy plans keep their prior interpretation."""
    doc = md.read_document(Path(directory) / PLAN_MD)
    parsed, stones = doc["tasks"], doc["milestones"]
    problems: list[str] = list(doc["problems"])
    md_tasks = {t["id"]: t for t in parsed}
    if not md_tasks:
        return problems + ["PLAN.md: no task lines found to compare with PLAN.json"]
    expected_id = plan_id or default_plan_id(directory)
    if plan.get("plan_id") != expected_id:
        problems.append(f"plan.plan_id: {plan.get('plan_id')!r} does not match the plan directory ({expected_id})")
    try:
        spec = (Path(directory) / str(plan.get("spec_ref") or DEFAULT_SPEC_REF)).resolve()
        spec_ok = spec.is_relative_to(Path(directory).resolve()) and spec.is_file()
    except (ValueError, OSError):
        spec_ok = False
    if not spec_ok:
        problems.append(f"plan.spec_ref: {plan.get('spec_ref')!r} does not exist in the plan directory")
    json_list = [t for t in _dicts(plan.get("tasks")) if isinstance(t.get("id"), str)]
    json_tasks = {t["id"]: t for t in json_list}
    schema_12 = pc.schema_tuple(plan) >= pc.EXTENSIONS_SINCE
    for tid in sorted({t["id"] for t in json_list if sum(1 for o in json_list if o["id"] == t["id"]) > 1}):
        problems.append(f"{tid}: defined more than once in PLAN.json")
    for tid in sorted(md_tasks.keys() - json_tasks.keys()):
        problems.append(f"{tid}: in PLAN.md but missing from PLAN.json")
    for tid in sorted(json_tasks.keys() - md_tasks.keys()):
        problems.append(f"{tid}: in PLAN.json but missing from PLAN.md")
    for tid in sorted(md_tasks.keys() & json_tasks.keys()):
        doc_t, js = md_tasks[tid], json_tasks[tid]
        if doc_t.get("milestone") != js.get("milestone_id"):
            problems.append(f"{tid}.milestone_id: PLAN.md puts it under {doc_t.get('milestone') or 'no milestone'}, "
                            f"PLAN.json says {js.get('milestone_id')}")
        if doc_t.get("title") and not _same_text(doc_t["title"], js.get("title")):
            problems.append(f"{tid}.title: PLAN.md says {doc_t['title']!r}, PLAN.json says {js.get('title')!r}")
        if doc_t.get("repo") and doc_t["repo"].strip() != str(js.get("repository") or "").strip():
            problems.append(f"{tid}.repository: PLAN.md says repo {doc_t['repo']!r}, PLAN.json says "
                            f"{js.get('repository')!r}")
        their_after = [a for a in js.get("after") if isinstance(a, str)] if isinstance(js.get("after"), list) else []
        if set(doc_t["after"]) != set(their_after):
            problems.append(f"{tid}.after: PLAN.md has {sorted(doc_t['after'])}, PLAN.json has {sorted(their_after)}")
        if doc_t.get("verify"):
            verifs = js.get("verification") if isinstance(js.get("verification"), list) else []
            commands = [v["value"].strip() for v in verifs
                        if isinstance(v, dict) and v.get("type") == "command" and isinstance(v.get("value"), str)]
            if doc_t["verify"].strip() not in commands:
                problems.append(f"{tid}.verification: PLAN.md verifies with `{doc_t['verify']}` but PLAN.json has "
                                + (f"only {', '.join(f'`{c}`' for c in commands)}" if commands
                                   else "no command verification"))
        for md_key, js_key, label in (("files", "expected_paths", "files"), ("resources", "shared_resources", "resources")):
            stated = doc_t.get(md_key) or []
            theirs = js.get(js_key)
            have = {x for x in theirs if isinstance(x, str)} if isinstance(theirs, list) else set()
            absent = [x for x in stated if x not in have]
            if absent:
                problems.append(f"{tid}.{js_key}: PLAN.md `{label}:` lists {', '.join(absent)} but PLAN.json does not "
                                "(PLAN.json may add more, never drop what PLAN.md states)")
        if doc_t.get("risk") in pc.LEVELS and doc_t["risk"] != js.get("risk"):
            problems.append(f"{tid}.risk: PLAN.md says risk: {doc_t['risk']}, PLAN.json says {js.get('risk')}")
        if schema_12:
            stated_covers = doc_t.get("covers")
            if stated_covers is not None:
                raw_covers = js.get("covers")
                json_covers = [value for value in raw_covers if isinstance(value, str)] \
                    if isinstance(raw_covers, list) else []
                if set(stated_covers) != set(json_covers):
                    problems.append(f"{tid}.covers: PLAN.md has {sorted(stated_covers)}, PLAN.json has "
                                    f"{sorted(json_covers)}")
            if doc_t.get("kind") is not None and doc_t["kind"] != js.get("kind"):
                problems.append(f"{tid}.kind: PLAN.md says {doc_t['kind']!r}, PLAN.json says {js.get('kind')!r}")
    md_milestones = {m["id"]: m for m in stones}
    json_milestones = {m["id"]: m for m in _dicts(plan.get("milestones")) if isinstance(m.get("id"), str)}
    for mid in sorted(md_milestones.keys() - json_milestones.keys()):
        problems.append(f"{mid}: milestone heading in PLAN.md missing from PLAN.json")
    for mid in sorted(json_milestones.keys() - md_milestones.keys()):
        problems.append(f"{mid}: milestone in PLAN.json has no `### {mid}` heading with tasks in PLAN.md")
    for mid in sorted(md_milestones.keys() & json_milestones.keys()):
        said = md_milestones[mid]["title"]
        if said and not _same_text(said, json_milestones[mid].get("title")):
            problems.append(f"{mid}.title: PLAN.md heading says {said!r}, PLAN.json says "
                            f"{json_milestones[mid].get('title')!r}")
    return problems


def read_plan(directory: Path) -> tuple[object | None, pc.Report]:
    """The parsed PLAN.json (None when unusable) and a report holding why."""
    report = pc.Report()
    path = Path(directory) / PLAN_JSON
    try:
        loaded = pc.loads(path.read_text(encoding="utf-8"))
        if loaded is None:  # a JSON `null` is not "no plan": it is a plan that is not an object
            report.errors.append(f"{PLAN_JSON}: top level must be an object (found null)")
            return None, report
        return loaded, report
    except FileNotFoundError:
        report.errors.append(f"{PLAN_JSON}: not found (legacy plan; run `init` to derive a skeleton)")
    except (OSError, ValueError, UnicodeError) as exc:
        report.errors.append(f"{PLAN_JSON}: unreadable ({type(exc).__name__})")
    return None, report


def _file_resolver(repo_roots: Mapping[str, Path]) -> ev.FileExists:
    """`file:` evidence must resolve to a concrete path that stays inside its registered repository."""
    def exists(repository: str, path: str) -> bool | None:
        root = repo_roots.get(repository)
        if root is None:
            return None
        normalized = path.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part and part != "."]
        if (not parts or any(part == ".." for part in parts) or normalized.startswith("/")
                or re.match(r"^[A-Za-z]:", normalized) or "\0" in normalized or re.search(r"[*?\[]", path)):
            return False  # a pattern or `.` is not something that was inspected
        try:
            repository_root = Path(root).resolve(strict=True)
            target = repository_root.joinpath(*parts).resolve(strict=True)
            return target.is_relative_to(repository_root) and target.exists()
        except (OSError, RuntimeError, ValueError):
            return False
    return exists


def _headings(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return set()
    found = set()
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if match:
            title = match.group(1)
            found.add(re.sub(r"[^\w]+", "-", title.casefold()).strip("-"))
            found.add(title.casefold().strip())
    return found


def _evidence_scope_problems(directory: Path, plan: dict, repo_roots: Mapping[str, Path] | None,
                             verify_files: bool = False) -> tuple[list[str], list[str]]:
    """What `contract.validate` cannot see: `spec:` evidence must exist in the plan folder and its anchor must match
    a heading; `file:` evidence is only as good as the repositories the caller could resolve. Unverified file evidence
    is a warning for a standalone check and an error where it matters (`verify_files`: approval and launch)."""
    errors: list[str] = []
    warnings: list[str] = []
    root = Path(directory).resolve()
    unresolved: set[str] = set()
    has_files = False
    for task in _dicts(plan.get("tasks")):
        where = str(task.get("id"))
        for dim, rel, anchor in ev.spec_refs(task):
            try:
                target = (root / rel).resolve()
                found = target.is_relative_to(root) and target.is_file()
            except (ValueError, OSError):
                found = False
            if not found:
                errors.append(f"{where}.classification_evidence.{dim}: spec {rel!r} does not exist in the plan folder")
            elif anchor and re.sub(r"[^\w]+", "-", anchor.casefold()).strip("-") not in _headings(target) \
                    and anchor.casefold() not in _headings(target):
                errors.append(f"{where}.classification_evidence.{dim}: spec anchor #{anchor} matches no heading of "
                              f"{rel}")
        entries = task.get("classification_evidence")
        refs = [r for e in (entries.values() if isinstance(entries, dict) else ()) if isinstance(e, dict)
                for r in (e.get("evidence") if isinstance(e.get("evidence"), list) else ())]
        if any((ev.parse_ref(r) or ("", ""))[0] == "file" for r in refs):
            has_files = True
            if repo_roots is None or str(task.get("repository")) not in repo_roots:
                unresolved.add(str(task.get("repository")))
    sink = errors if verify_files else warnings
    if has_files and repo_roots is None:
        sink.append("classification_evidence: file references could not be verified against a repository (no "
                    "repository roots available; register and clone the project's repositories)")
    elif unresolved:
        for name in sorted(unresolved):
            sink.append(f"classification_evidence: repository {name!r} has no checkout here, so its file evidence "
                        "could not be verified")
    return errors, warnings


def check(directory: Path, plan: object | None = None, plan_id: str | None = None,
          repo_roots: Mapping[str, Path] | None = None, verify_files: bool = False,
          ref_exists: ev.RefExists | None = None) -> pc.Report:
    """Full publication gate: schema + graph rules + classification evidence, PLAN.md consistency, revision store and
    frozen-revision immutability. Pass `plan` to check an already parsed object (so a caller can freeze exactly what was
    checked) and `repo_roots` ({repository role: path}) to verify that `file:` evidence really exists; with
    `verify_files` evidence that cannot be verified is an error, not a warning. `ref_exists` verifies `command:` and
    `precedent:` references (a reference that is verifiably absent is always an error)."""
    if plan is None:
        plan, report = read_plan(directory)
        if plan is None:
            return report
    report = pc.Report()
    spec_ids = None
    if isinstance(plan, dict):
        version = pc.schema_tuple(plan)
        if version[0] == pc.SUPPORTED_MAJOR and version >= pc.EXTENSIONS_SINCE:
            spec_ids = traceability.read_spec_ids(directory, plan.get("spec_ref") or DEFAULT_SPEC_REF)
    inner = pc.validate(plan, _file_resolver(repo_roots) if repo_roots is not None else None, ref_exists,
                        spec_ids=spec_ids)
    report.errors += inner.errors
    report.warnings += inner.warnings
    if isinstance(plan, dict):
        # Both layers always run, so one `check` shows every problem; the comparison only reads what is well formed.
        report.errors += consistency(directory, plan, plan_id)
        scoped = _evidence_scope_problems(directory, plan, repo_roots, verify_files)
        report.errors += scoped[0]
        report.warnings += scoped[1]
        try:
            last = rev.latest(directory)
            expected = last["revision"] + 1 if last else 1
            report.errors += rev.verify_store(directory, tolerate=expected)  # freeze() adopts or rejects that one itself
            if expected in rev.orphans(directory):
                report.warnings.append(f"PLAN.r{expected}.json exists but is not in the manifest (freeze in progress or "
                                       "interrupted); `freeze` adopts it if identical, rejects it otherwise")
            frozen = next((r for r in rev.list_revisions(directory) if r["revision"] == plan.get("revision")), None)
            same = bool(frozen) and rev.sha256(pc.dumps(plan)) == frozen["sha256"]
            if frozen and not same:
                report.errors.append(f"plan.revision: r{frozen['revision']} is frozen and PLAN.json differs from it; "
                                     f"set revision to {frozen['revision'] + 1} for the change")
            if isinstance(plan.get("revision"), int) and plan["revision"] > expected:
                report.errors.append(f"plan.revision: next revision is {expected}, got {plan['revision']}")
            if pc.schema_tuple(plan) < pc.EVIDENCE_SINCE and not same:
                report.errors.append(f"plan.schema_version: {plan.get('schema_version')!r} predates classification "
                                     f"evidence; publish new revisions with {pc.SCHEMA_VERSION} and justify each "
                                     "classification (a revision frozen earlier stays valid as it is)")
        except pc.PlanContractError as exc:
            report.errors += exc.issues
    return report


def approve_freeze(directory: Path, plan_id: str | None = None,
                   approved_states: tuple[str, ...] = APPROVED_STATES,
                   repo_roots: Mapping[str, Path] | None = None, verify_files: bool = False,
                   ref_exists: ev.RefExists | None = None) -> dict:
    """Freeze the current PLAN.json as an immutable revision. Requires an approved PLAN.md status and a clean check."""
    status = plan_status(directory)
    if status not in approved_states:
        raise pc.PlanContractError("PLAN_NOT_APPROVED", [f"PLAN.md status is {status or 'missing'!r}; freeze after approval"])
    rev.list_revisions(directory)  # preserve the revision store's stable error code at the approval boundary
    plan, report = read_plan(directory)
    if plan is not None:
        report = check(directory, plan, plan_id, repo_roots, verify_files, ref_exists)  # the very object frozen below
    if not report.ok:
        raise pc.PlanContractError("PLAN_INVALID", report.errors)
    return rev.freeze(directory, plan, narrative=narrative_digest(directory))


def _next_id(taken: set[str], base: str) -> str:
    """`T18` -> `T18b` (the next free letter); a task that already ends in a letter gets the next free number."""
    if re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?", base):
        for letter in "bcdefghijklmnopqrstuvwxyz":
            if base + letter not in taken:
                return base + letter
    top = max((int(m.group(1)) for t in taken if (m := re.match(r"T([0-9]+)", t))), default=0)
    return f"T{top + 1}"


def _cross_check_of(task: dict, new_id: str) -> dict:
    """A copy of an audit task that reviews the same scope independently, with its own report and ledger."""
    clone = copy.deepcopy(task)
    paths = [p for p in task.get("expected_paths", []) if isinstance(p, str)]
    old_report = next((p for p in paths if p.endswith(".md")), None)
    stem = (old_report[:-3] if old_report else next((p[: -len(quality.LEDGER_SUFFIX)] for p in paths
                                                      if p.endswith(quality.LEDGER_SUFFIX)), f"{task['id'].lower()}"))
    new_stem = f"{stem}-crosscheck"
    clone["id"] = new_id
    clone["title"] = f"Cross-check audit of {task['id']}: {task.get('title', '')}"[:200]
    clone["objective"] = (f"An independent second audit of the scope of {task['id']}. Do not read its report or ledger "
                          "first: confirm findings yourself and record every one in your own ledger.")
    clone["expected_paths"] = ([f"{new_stem}.md"] if old_report else []) + [f"{new_stem}{quality.LEDGER_SUFFIX}"]
    if old_report:
        for item in clone.get("verification", []):
            if isinstance(item, dict) and isinstance(item.get("value"), str):
                item["value"] = item["value"].replace(old_report, f"{new_stem}.md")
    clone["estimate_rationale"] = (f"Cross-check of {task['id']}: a bounded independent pass over the same scope; "
                                   + str(task.get("estimate_rationale", "")))[:400]
    return clone


def retrofit_audit(directory: Path, cross_check: bool = False) -> list[str]:
    """Bring a plan written before the audit gate in line, as a new working revision: each `kind: audit` task that does
    not list exactly one findings ledger gets `<its first .md report>` with the ledger suffix (else `<task>.findings.json`
    in its first directory), in PLAN.json and on its PLAN.md line. Nothing else changes and nothing is frozen: review the
    diff, then `freeze`. It never invents an end-to-end test; if the plan lacks one `check` still says so. Returns what
    it changed (empty when the plan already complies)."""
    directory = Path(directory)
    plan, report = read_plan(directory)
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        raise pc.PlanContractError("PLAN_INVALID", report.errors or ["PLAN.json is missing or unreadable"])
    last = rev.latest(directory)
    changed: list[str] = []
    md_path = directory / PLAN_MD
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    for task in plan["tasks"]:
        if not isinstance(task, dict) or task.get("kind") != "audit":
            continue
        paths = task.get("expected_paths") if isinstance(task.get("expected_paths"), list) else []
        if sum(1 for p in paths if isinstance(p, str) and p.endswith(quality.LEDGER_SUFFIX)) == 1:
            continue
        report_md = next((p for p in paths if isinstance(p, str) and p.endswith(".md")), None)
        if report_md:
            ledger = report_md[:-3] + quality.LEDGER_SUFFIX
        else:
            first_dir = next((p.rsplit("/", 1)[0] + "/" for p in paths if isinstance(p, str) and "/" in p), "")
            ledger = f"{first_dir}{str(task.get('id')).lower()}{quality.LEDGER_SUFFIX}"
        task["expected_paths"] = [p for p in paths if not (isinstance(p, str) and p.endswith(quality.LEDGER_SUFFIX))] + [ledger]
        line = re.compile(rf"^(- \[.\] {re.escape(str(task.get('id')))} .*?· files: )([^·\n]*?)(\s*(?:·|$))", re.M)
        md_text, count = line.subn(lambda m: f"{m.group(1)}{m.group(2).rstrip()}, {ledger}{m.group(3)}", md_text, count=1)
        changed.append(f"{task['id']}: declares {ledger}" + ("" if count else " (PLAN.md line has no `files:`; add it by hand)"))
    audits = [t for t in plan["tasks"] if isinstance(t, dict) and t.get("kind") == "audit"]
    if cross_check and len(audits) == 1:
        original = audits[0]
        taken = {t.get("id") for t in plan["tasks"] if isinstance(t, dict)}
        new_id = _next_id({i for i in taken if isinstance(i, str)}, original["id"])
        clone = _cross_check_of(original, new_id)
        plan["tasks"].insert(plan["tasks"].index(original) + 1, clone)
        for task in plan["tasks"]:                       # whatever waited for the audit waits for its cross-check too
            if isinstance(task, dict) and original["id"] in task.get("after", []) and task is not clone:
                task["after"] = [*task["after"], new_id]
                md_text = re.sub(rf"^(- \[.\] {re.escape(str(task['id']))} .*?after: [^·\n]*?\b{re.escape(original['id'])})(?=[,\s·]|$)",
                                 lambda m: f"{m.group(1)}, {new_id}", md_text, count=1, flags=re.M)
        line = re.search(rf"^(- \[.\] {re.escape(original['id'])} .*)$", md_text, re.M)
        if line:
            row = line.group(1).replace(f"{original['id']} —", f"{new_id} —", 1)
            row = re.sub(r"(?<=— )(.*?)(?= ·)", lambda m: f"Cross-check audit of {original['id']}: {m.group(1)}", row, count=1)
            row = re.sub(r"files: [^·\n]*", "files: " + ", ".join(clone["expected_paths"]) + " ", row, count=1)
            row = re.sub(r"verify: `[^`]*`", f"verify: `{clone['verification'][0]['value']}`", row, count=1) \
                if clone.get("verification") else row
            md_text = md_text[:line.end()] + "\n" + row + md_text[line.end():]
        else:
            changed.append(f"{new_id}: PLAN.md has no line for {original['id']}; add the cross-check line by hand")
        changed.append(f"{new_id}: cross-check audit of {original['id']} ({', '.join(clone['expected_paths'])})")
    if changed:
        plan["revision"] = (last["revision"] + 1) if last else plan.get("revision", 1)
        (directory / PLAN_JSON).write_text(pc.dumps(plan), encoding="utf-8")
        if md_text:
            md_path.write_text(md_text, encoding="utf-8")
    return changed


def freeze_if_present(directory: Path, plan_id: str | None = None,
                      approved_states: tuple[str, ...] = APPROVED_STATES,
                      repo_roots: Mapping[str, Path] | None = None, verify_files: bool = False,
                      ref_exists: ev.RefExists | None = None) -> dict | None:
    """Opt-in contract, approval side. No PLAN.json -> None (legacy plan). With one and an approved PLAN.md, freeze it
    (idempotent; a new revision number is a new approval) or raise PlanContractError; a not-yet-approved plan is left
    alone. Launch paths use `bind_approved`, which never turns an unreviewed edit into a revision."""
    if not (Path(directory) / PLAN_JSON).exists() or plan_status(directory) not in approved_states:
        return None
    return approve_freeze(directory, plan_id, approved_states, repo_roots, verify_files, ref_exists)


def bind_approved(directory: Path, plan_id: str | None = None, approved_states: tuple[str, ...] = APPROVED_STATES, *,
                  repo_roots: Mapping[str, Path] | None = None, freeze: bool = True, forced: bool = False,
                  verify_files: bool = False, ref_exists: ev.RefExists | None = None) -> dict | None:
    """The gate every launch passes: returns the entry (revision, sha256, frozen_at) of the revision a new run will
    execute, or None for a legacy plan (no PLAN.json and nothing ever frozen).

    The approved revision is the latest frozen one. PLAN.json must be exactly that (same canonical bytes); an edit made
    after approval is refused with PLAN_DRIFT instead of being frozen on the way in, so a launch cannot run content
    nobody approved. A plan that was never frozen has no approval record and is refused (`PLAN_NOT_FROZEN`): only
    the approval act (`plan approve`, `freeze`) creates the record, a launch never does. `freeze=False` verifies
    without writing (dry runs, re-checks); `forced=True` is the owner's explicit launch, taken as the approval, and
    is the only way a launch freezes (`source: launch-forced`).

    Codes: PLAN_MISSING, PLAN_NOT_APPROVED, PLAN_INVALID, PLAN_DRIFT, PLAN_NOT_FROZEN, plus the revision-store codes."""
    directory = Path(directory)
    last = rev.latest(directory)
    if not (directory / PLAN_JSON).exists():
        if last:
            raise pc.PlanContractError("PLAN_MISSING", [
                f"{PLAN_JSON} is gone but revision r{last['revision']} was frozen from it; restore it from plan-revisions/"])
        return None
    status = plan_status(directory)
    if status not in approved_states and not forced:
        raise pc.PlanContractError("PLAN_NOT_APPROVED", [
            f"PLAN.md status is {status or 'missing'!r}; approve the plan before launching it"])
    plan, report = read_plan(directory)
    if plan is not None:
        report = check(directory, plan, plan_id, repo_roots, verify_files, ref_exists)
    if not report.ok:
        raise pc.PlanContractError("PLAN_INVALID", report.errors)
    digest = rev.sha256(pc.dumps(plan))
    if last:
        if plan.get("revision") == last["revision"] and digest == last["sha256"]:
            approved_prose = last.get("plan_md_sha256")
            if approved_prose and narrative_digest(directory) != approved_prose:
                raise pc.PlanContractError("PLAN_PROSE_DRIFT", [
                    "PLAN.md prose changed after the plan was approved (readers take the live file as approved); "
                    "re-approve it with `plan approve`/`plan-json freeze` so what is run is what was approved"])
            return last
        approved = f"r{last['revision']}"
        message = (f"PLAN.json (revision {plan.get('revision')}) is not the approved revision {approved}; approve it "
                   f"(`plan approve`, or `plan-json freeze` once the owner accepts it) before launching, or restore "
                   f"{approved} from plan-revisions/")
        raise pc.PlanContractError("PLAN_DRIFT", [message])
    if not forced:
        raise pc.PlanContractError("PLAN_NOT_FROZEN", [
            "nothing was frozen at approval, so there is no record of what was approved; approve it with "
            "`plan approve` (or run `plan-json freeze` once the owner accepted exactly this PLAN.json) and launch again"])
    if not freeze:  # an explicit --force is the owner's own approval of this content
        return {"revision": plan["revision"], "sha256": digest, "frozen_at": None, "source": "launch-forced"}
    return rev.freeze(directory, plan, "launch-forced", narrative=narrative_digest(directory))


def compat(directory: Path, plan_id: str | None = None) -> dict:
    """Read-only: what an existing plan already provides for the contract and what needs explicit enrichment.
    Never writes anything, never reads values as if they were estimates; legacy labels are reported as such."""
    tasks, stones = md.read(Path(directory) / PLAN_MD)
    skel = skeleton(directory, plan_id)
    required = [k for k in pc.TASK_KEYS]
    per_task = []
    derived_by_id = {t["id"]: t for t in skel["tasks"]}
    for item in tasks:
        derived = derived_by_id[item["id"]]
        missing = [k for k in required if k not in derived]
        per_task.append({"id": item["id"], "derived": sorted(k for k in derived if k in required),
                         "needs_enrichment": missing, "done_in_md": item["done"],
                         "legacy_complexity": item.get("complexity"), "legacy_risk": item.get("risk")})
    return {"plan_id": plan_id or default_plan_id(directory), "plan_status": plan_status(directory),
            "plan_md_problems": md_problems(directory),
            "has_plan_json": (Path(directory) / PLAN_JSON).exists(), "task_count": len(tasks),
            "milestones_in_md": [m["id"] for m in stones],
            "tasks_without_milestone": [t["id"] for t in tasks if not t.get("milestone")], "tasks": per_task,
            "skeleton_errors": len(pc.validate(skel).errors)}
