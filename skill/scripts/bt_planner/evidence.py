"""Classification evidence (schema 1.1.0): every classification is argued, not asserted.

A task carries `classification_evidence`, one entry per dimension (complexity, scope, duration, risk, coupling,
confidence), each `{"justification": text, "evidence": ["kind:value", ...]}`. Evidence kinds:

    file:<relative path>     something in the repository the planner actually inspected: a concrete path, never a
                             pattern or `.` (existence is checked when the caller can resolve the task's repository)
    command:<cmd> -> <seen>  a command the planner ran and what it showed (the arrow and a result are required)
    precedent:<ref>          an earlier requirement/task (REQ-009/T4), decision or pending id, a commit hash or a URL
    spec:<path>[#anchor]     a place in the requirement folder: the file must exist and an anchor must match one of
                             its headings; without an anchor it is context, not support
    task:<id>                another task of this plan (must exist, never the task itself)
    assumption:<text>        an explicit, unverified premise: allowed, but it never counts as support

Rules are deterministic and textual-only (no language model): the point is that a plan cannot be published with a
bare label, a placeholder, one sentence pasted under six dimensions, or a `high` confidence resting on assumptions.
Schema 1.0.0 documents (frozen before this existed) keep loading; the same findings are warnings for them.
"""
from __future__ import annotations

import re
from collections.abc import Callable

DIMENSIONS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")
KINDS = ("file", "command", "precedent", "spec", "task", "assumption")
MIN_JUSTIFICATION_WORDS = 4
MIN_CRITERION_WORDS = 3
MIN_OBJECTIVE_WORDS = 4
PLACEHOLDERS = frozenset({"tbd", "todo", "to do", "na", "n a", "none", "tba", "wip", "fixme", "pending", "unknown",
                          "same", "same as above", "as above", "lorem ipsum", "ok", "done", "works", "etc", "xxx",
                          "por definir", "pendiente", "igual", "ninguno"})
# only a command that is *nothing but* a no-op: any pipe, list, redirection or substitution makes it real
TRIVIAL_COMMAND_RE = re.compile(r"^\s*(true|:|exit\s+0|ls|pwd|(?:echo|printf|sleep)\b[^&;|<>$`()]*)\s*$")
PRECEDENT_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9_.-]*-[0-9]+(?:[/#][A-Za-z0-9._-]+)*|(?:commit )?[0-9a-f]{7,40}|"
                          r"https?://\S+)$")
COMMAND_RE = re.compile(r"^\S.*\s(?:->|=>)\s+\S")
_LINE_SUFFIX_RE = re.compile(r"(?::[0-9]+(?:-[0-9]+)?|#L[0-9]+(?:-L?[0-9]+)?)$")

FileExists = Callable[[str, str], "bool | None"]  # (repository, relative path) -> exists; None = cannot tell
RefExists = Callable[[str, str, str], "bool | None"]  # (kind, value, repository) -> exists; None = cannot tell


def normalise(text: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(text or "").casefold())).strip()


def weak(text: object, min_words: int) -> str | None:
    """Why a text cannot be a justification/criterion (None when it can)."""
    norm = normalise(text)
    if not norm or norm in PLACEHOLDERS:
        return "is a placeholder"
    # scripts written without spaces (CJK) count roughly one word per three characters
    words = sum(max(1, len(tok) // 3) if any(ord(ch) > 0x2E7F for ch in tok) else 1 for tok in norm.split())
    if words < min_words:
        return f"is too short to justify anything (needs at least {min_words} words)"
    return None


def parse_ref(ref: object) -> tuple[str, str] | None:
    if not isinstance(ref, str):
        return None
    kind, sep, value = ref.partition(":")
    kind, value = kind.strip().lower(), value.strip()
    if not sep or kind not in KINDS or not value:
        return None
    return kind, value


def _file_path(value: str) -> str:
    return _LINE_SUFFIX_RE.sub("", value).strip()


def _unsafe(path: str) -> bool:
    flat = path.replace("\\", "/")
    return ("\0" in flat or flat.startswith("/") or re.match(r"^[A-Za-z]:", flat) is not None
            or ".." in flat.split("/"))


def spec_refs(task: dict) -> list[tuple[str, str, str]]:
    """(dimension, relative path, anchor) of every `spec:` reference, for the caller that can look at the directory."""
    found = []
    ev = task.get("classification_evidence")
    for dim, entry in (ev.items() if isinstance(ev, dict) else ()):
        for ref in (entry.get("evidence") if isinstance(entry, dict) and isinstance(entry.get("evidence"), list) else ()):
            parsed = parse_ref(ref)
            if parsed and parsed[0] == "spec":
                path, _, anchor = parsed[1].partition("#")
                found.append((dim, path.strip(), anchor.strip()))
    return found


def check_task(where: str, task: dict, *, strict: bool, task_ids: set[str], own_id: str | None,
               file_exists: FileExists | None = None,
               ref_exists: RefExists | None = None) -> tuple[list[str], list[str]]:
    """(errors, warnings) for one task's evidence and the quality of the text that carries the classification.
    `strict` (schema >= 1.1.0) makes absence and weakness errors; otherwise they are warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    soft = errors if strict else warnings
    ev = task.get("classification_evidence")
    if ev is None:
        soft.append(f"{where}.classification_evidence: missing; justify {', '.join(DIMENSIONS)} with evidence "
                    "(schema 1.1.0)" if strict else
                    f"{where}.classification_evidence: absent (schema 1.0.0 plan; new revisions need 1.1.0)")
        return errors, warnings
    if not isinstance(ev, dict):
        errors.append(f"{where}.classification_evidence: must be an object keyed by dimension")
        return errors, warnings
    for key in ev:
        if key not in DIMENSIONS:
            errors.append(f"{where}.classification_evidence.{key}: unknown dimension (use {', '.join(DIMENSIONS)})")
    solid: dict[str, bool] = {}
    kinds_seen: set[str] = set()
    texts: dict[str, list[str]] = {}
    for dim in DIMENSIONS:
        spot = f"{where}.classification_evidence.{dim}"
        entry = ev.get(dim)
        if entry is None:
            soft.append(f"{spot}: missing")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{spot}: must be an object {{justification, evidence}}")
            continue
        why = weak(entry.get("justification"), MIN_JUSTIFICATION_WORDS)
        if not isinstance(entry.get("justification"), str):
            errors.append(f"{spot}.justification: required text")
        elif why:
            soft.append(f"{spot}.justification: {why}")
        else:
            texts.setdefault(normalise(entry["justification"]), []).append(dim)
        refs = entry.get("evidence")
        if not isinstance(refs, list) or not refs:
            soft.append(f"{spot}.evidence: needs at least one reference (kind:value; kinds {', '.join(KINDS)})")
            continue
        solid[dim] = False
        for index, ref in enumerate(refs):
            parsed = parse_ref(ref)
            if parsed is None:
                errors.append(f"{spot}.evidence[{index}]: {ref!r} must look like kind:value with kind in "
                              f"{', '.join(KINDS)}")
                continue
            kind, value = parsed
            kinds_seen.add(kind)
            if kind not in ("assumption",) and not (kind == "spec" and "#" not in value):
                solid[dim] = True  # a spec file without an anchor is context, not support
            if kind == "command" and not COMMAND_RE.match(value):
                errors.append(f"{spot}.evidence[{index}]: command evidence must read '<command> -> <what it showed>'")
            elif kind == "precedent" and not PRECEDENT_RE.match(value):
                errors.append(f"{spot}.evidence[{index}]: precedent {value!r} must be a requirement/task id "
                              "(REQ-009/T4), decision/pending id, commit hash or URL")
            elif kind in ("command", "precedent") and ref_exists is not None:
                shown = re.split(r"\s(?:->|=>)\s", value, maxsplit=1)[0].strip() if kind == "command" else value
                if ref_exists(kind, shown, str(task.get("repository") or "")) is False:
                    what = "is not an executable or a path that exists" if kind == "command" else \
                        "does not exist (requirement, task, decision, pending item or commit not found)"
                    errors.append(f"{spot}.evidence[{index}]: {kind} {shown!r} {what}")
            if kind == "file":
                path = _file_path(value)
                static = [part for part in path.replace("\\", "/").split("/") if part and part != "."]
                static = [part for part in static if not re.search(r"[*?\[]", part)]
                if not static:
                    errors.append(f"{spot}.evidence[{index}]: file {value!r} must name a concrete path, not a pattern "
                                  "or the repository root")
                elif _unsafe(path):
                    errors.append(f"{spot}.evidence[{index}]: file path {value!r} must be relative, without '..'")
                elif file_exists is not None:
                    found = file_exists(str(task.get("repository") or ""), path)
                    if found is False:
                        errors.append(f"{spot}.evidence[{index}]: file {path!r} does not exist in repository "
                                      f"{task.get('repository')!r}; evidence must be something actually inspected")
            elif kind == "task":
                if value not in task_ids:
                    errors.append(f"{spot}.evidence[{index}]: task {value!r} is not in this plan")
                elif value == own_id:
                    errors.append(f"{spot}.evidence[{index}]: a task cannot be evidence for itself")
            elif kind == "spec":
                path = value.partition("#")[0].strip()
                if not path or _unsafe(path):
                    errors.append(f"{spot}.evidence[{index}]: spec path {value!r} must be relative to the plan folder")
    for same in (dims for dims in texts.values() if len(dims) > 1):
        soft.append(f"{where}.classification_evidence: {', '.join(same)} share the same justification text; "
                    "each dimension needs its own reasoning")
    def texts_of(value: object) -> list[str]:
        return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []

    vocabulary = {w for source in (task.get("title"), task.get("objective"), *texts_of(task.get("expected_paths")),
                                   *texts_of(task.get("shared_resources")), *texts_of(task.get("acceptance_criteria")))
                  if isinstance(source, str) for w in normalise(source).split() if len(w) >= 3}
    for dim, entry in ev.items():
        if isinstance(entry, dict) and isinstance(entry.get("justification"), str):
            refs = " ".join(texts_of(entry.get("evidence")))
            mine = {w for w in normalise(entry["justification"]).split() if len(w) >= 3}
            if vocabulary and not (mine & (vocabulary | set(normalise(refs).split()))) and len(mine) >= 1:
                warnings.append(f"{where}.classification_evidence.{dim}.justification: shares no term with the task "
                                "(title, objective, paths, criteria) or its evidence; is it about this task?")
    if task.get("confidence") == "high":
        thin = [d for d in ("complexity", "scope", "duration") if d in solid and not solid[d]]
        if thin:
            errors.append(f"{where}.confidence: high, but {', '.join(thin)} rest only on assumptions; investigate "
                          "(file/command/precedent evidence) or lower the confidence")
        if solid and not kinds_seen & {"file", "command", "precedent"}:
            errors.append(f"{where}.confidence: high requires evidence that something was inspected or run "
                          "(file/command/precedent)")
    coupling = ev.get("coupling")
    if task.get("coupling") in ("medium", "high") and isinstance(coupling, dict):
        cited = [parse_ref(r) for r in (coupling.get("evidence") if isinstance(coupling.get("evidence"), list) else [])]
        if not task.get("shared_resources") and not any(p and p[0] == "task" for p in cited):
            soft.append(f"{where}.coupling: {task['coupling']} names neither a shared resource nor the task it "
                        "interacts with (task:<id> in its evidence)")
    return errors, warnings


# `coupling` is a signal for the scheduler, never a promise: text that presents tasks as safe to run in parallel is a
# scheduling decision the planner does not make (AC-06, AC-15).
PARALLEL_CLAIM_RE = re.compile(
    r"(?:safe|ok|fine|free|able|ready)\s+(?:to|for)\s+(?:be\s+)?(?:run\s+|executed?\s+|done\s+|worked\s+on\s+)?"
    r"(?:in\s+parallel|concurrently|simultaneously|side\s+by\s+side)|"
    r"(?:can|may|could|should|must)\s+(?:be\s+)?(?:run|executed?|done|worked\s+on|started)\s+"
    r"(?:in\s+parallel|concurrently|simultaneously|alongside)|parallel(?:l?y)?[-\s]safe|safely\s+parallel|"
    r"no\s+(?:conflicts?|collisions?)\s+(?:with|between)\s+(?:other|any)\s+tasks?|"
    r"(?:se\s+puede|puede|pueden|se\s+pueden)\s+(?:ejecutar|correr|hacer|trabajar)\w*\s+en\s+paralelo|"
    r"seguro\s+(?:para|de)\s+(?:ejecutar|correr)\s+en\s+paralelo|paralelizable|en\s+paralelo\s+sin\s+(?:riesgo|conflicto)",
    re.I)


def parallel_claims(task: dict) -> list[tuple[str, str]]:
    """(field, text) of every free-text field of a task that promises parallel safety."""
    fields: list[tuple[str, object]] = [("objective", task.get("objective")),
                                        ("estimate_rationale", task.get("estimate_rationale"))]
    evidence = task.get("classification_evidence")
    for dim, entry in (evidence.items() if isinstance(evidence, dict) else ()):
        if isinstance(entry, dict):
            fields.append((f"classification_evidence.{dim}.justification", entry.get("justification")))
    for index, item in enumerate(task.get("acceptance_criteria") if isinstance(task.get("acceptance_criteria"), list) else ()):
        fields.append((f"acceptance_criteria[{index}]", item))
    return [(name, text) for name, text in fields if isinstance(text, str) and PARALLEL_CLAIM_RE.search(text)]


def check_text_quality(where: str, task: dict, *, strict: bool) -> tuple[list[str], list[str]]:
    """Objective, acceptance criteria and verification commands that carry no information."""
    errors: list[str] = []
    warnings: list[str] = []
    soft = errors if strict else warnings
    for name, text in parallel_claims(task):
        soft.append(f"{where}.{name}: {PARALLEL_CLAIM_RE.search(text).group(0)!r} promises parallel safety; coupling "
                    "is a signal for the scheduler, never a guarantee (the scheduler decides concurrency)")
    objective = task.get("objective")
    if isinstance(objective, str) and objective.strip():
        why = weak(objective, MIN_OBJECTIVE_WORDS)
        if why:
            soft.append(f"{where}.objective: {why}")
        elif normalise(objective) == normalise(task.get("title")):
            soft.append(f"{where}.objective: repeats the title; state the concrete result to achieve")
    criteria = task.get("acceptance_criteria")
    if isinstance(criteria, list):
        seen: set[str] = set()
        for index, item in enumerate(criteria):
            if not isinstance(item, str) or not item.strip():
                continue
            why = weak(item, MIN_CRITERION_WORDS)
            if why:
                soft.append(f"{where}.acceptance_criteria[{index}]: {why}; state an observable condition")
            if normalise(item) in seen:
                soft.append(f"{where}.acceptance_criteria[{index}]: duplicate criterion")
            seen.add(normalise(item))
    for index, item in enumerate(task.get("verification") if isinstance(task.get("verification"), list) else ()):
        if (isinstance(item, dict) and item.get("type") == "command" and isinstance(item.get("value"), str)
                and TRIVIAL_COMMAND_RE.match(item["value"])):
            soft.append(f"{where}.verification[{index}].value: {item['value']!r} cannot fail, so it verifies nothing")
    return errors, warnings
