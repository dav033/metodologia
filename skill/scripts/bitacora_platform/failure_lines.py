"""The decisive lines of a failing command's output: what every note that clips that output must keep (REQ-030).

Each builder of a failure note (the M6 digest the agent reads, the owner's card, the diagnosis bundle, the repair excerpt, the
attempt history) kept a head or a tail plus its own regex of "error lines". pictures REQ-021 T2.6 att-0095: the Playwright line
`locator.waitFor: Timeout 30000ms exceeded.` sat above ~3 KB of JSON server logs, the 1500-char tail began after it and no regex
matched it, so 24 attempts read only logs and build banners. This module is the one place that knows what a decisive line looks
like, which lines are noise, how to clip a text without losing them, and whether a missing module is a package or a source file
of the repository (T3.11 att-0093: a file the agent never created was called a dependency problem). Stdlib only: it runs under
the system interpreter.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache

# Strong: a line that says what failed in the words of the tool that failed.
_STRONG_PATTERNS = (
    r"Timeout \d+ ?ms exceeded", r"Timed out \d+ ?ms waiting",                      # Playwright / Puppeteer / Jest
    r"\b(?:locator|page|frame|browser|browserContext|context|elementHandle|request|response|apiRequestContext)\.\w+:",
    r"^\s*(?:-\s+)?waiting for\b", r"^\s*✘", r"^\s*\d+\) \[[^\]\n]+\] ›",           # call log, list reporter, summary
    r"\b\w*(?:Error|Exception)\b\s*(?:\[[^\]\n]*\]\s*)?:",                           # TypeError: / Error [ERR_X]: / AssertionError
    r"\b(?:ERROR|FATAL|CRITICAL|PANIC)\b", r"\bAssertionError\b", r"^Traceback \(most recent call last\)",
    r"heap out of memory", r"Ineffective mark-compacts", r"\bSegmentation fault\b", r"\bcore dumped\b",
    r"^\s*Killed\s*$", r"^\s*Aborted(?: \(core dumped\))?\s*$",
    r"\b(?:ENOENT|EACCES|EPERM|ECONNREFUSED|ECONNRESET|EADDRINUSE|ENOMEM|ENOSPC|EROFS|ETIMEDOUT|ENOTCACHED|EAI_AGAIN|EMFILE)\b",
    r"\bTS\d{4}\b", r"^(?:FAIL|ERROR):\s", r"^FAILED\b", r"^E\s{2,}\S", r"^\s*(?:FAIL\b|not ok\b|[✗×])", r"✖",
    r"^\s*\[FAIL\]", r"\bCannot find (?:module|package|name)\b", r"\bNo module named\b", r"\bCan't resolve\b",
    r"\bFailed to resolve import\b", r"\bis not (?:defined|a function)\b", r"\bCannot read propert", r"\bpanicked at\b",
    r"^error(?:\[E\d+\])?:", r":\d+(?::\d+)?: error\b", r"^npm ERR!", r"^\s*(?:Expected|Received)\b[^\n]{0,20}:",
)
_STRONG = re.compile("|".join(_STRONG_PATTERNS), re.MULTILINE)
# Weak: worth a line when the budget allows, dropped first when it does not.
_WEAK = re.compile(r"(?i)\berrors?\b|\bfail(?:ed|ures?|ing|s)?\b|\bERR_[A-Z][A-Z_]{2,}\b|\bexit(?:ed)?\s+(?:with\s+)?(?:code|status)\b"
                   r"|!==|\bdenied\b|\brefused\b|\bcannot\b|\bunable to\b|\bnot found\b")
_PROPERTY = re.compile(r"^\s+[\w$]+: ")            # `  code: 'ERR_X',` of a dumped error object: context, never a start
# a JavaScript stack frame or a native one (`12: 0x19c77d1 [node]`): the first one says where, the rest are noise
_FRAME = re.compile(r"^\s+at\s|^\s*\d+: 0x[0-9a-f]+\b")
_LABEL = re.compile(r"^[A-Z][\w ]{0,24}:(?:\s|$)")     # `Call log:`, `Locator: ...`: the detail block of the error above
_NOISE_LINE = re.compile(r"^\s*npm (?:notice|warn(?:ing)?)\b", re.IGNORECASE)
_JSON_LEVEL = re.compile(r'"(?:nivel|level|lvl|severity|levelname)"\s*:\s*(?:"(?P<name>[A-Za-z]+)"|(?P<num>\d+))')
_JSON_FAULT = re.compile(r'"(?:error|err|exception|stack)"\s*:\s*(?!null\b|false\b|""|\{\})')
_LOUD = {"warn", "warning", "error", "err", "fatal", "critical", "crit", "panic", "alert", "emerg", "emergency"}
_MAX_LINE = 240


def structured(line: str) -> str:
    """'' for a line that is not a JSON log record; 'loud' (warn/error/fatal, a pino level >= 40, or an error field) or
    'quiet' (info/debug, or no level: flags, request bodies) for one that is. A server under test prints pages of quiet ones."""
    text = re.sub(r"^\[[\w:.-]{1,30}\]\s*", "", line.strip())
    if not (text.startswith('{"') and text.endswith("}")):         # JSON, not a Python dict repr an assertion printed
        return ""
    level = _JSON_LEVEL.search(text)
    if level is None:
        return "loud" if _JSON_FAULT.search(text) else "quiet"
    if level["num"]:
        return "loud" if int(level["num"]) >= 40 else "quiet"
    return "loud" if level["name"].lower() in _LOUD else "quiet"


def noise(line: str) -> bool:
    """`npm notice` / `npm warn` lines and quiet structured log records never explain a failure."""
    return bool(_NOISE_LINE.match(line)) or structured(line) == "quiet"


def without_noise(text: str, *, structured_logs: bool = True) -> str:
    """The output without lines that never explain a failure and without blank runs. Quiet JSON log records are counted, not
    dropped silently: the agent learns the server logged something without reading it."""
    kept: list[str] = []
    quiet = 0
    for line in text.splitlines():
        if _NOISE_LINE.match(line):
            continue
        if structured_logs and structured(line) == "quiet":
            quiet += 1
            continue
        if quiet:
            kept.append(f"[{quiet} structured log line(s) at info/debug level omitted]")
            quiet = 0
        kept.append(line)
    if quiet:
        kept.append(f"[{quiet} structured log line(s) at info/debug level omitted]")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


@lru_cache(maxsize=4096)                           # a long output repeats its lines, and each line is ranked a few times
def _rank(line: str) -> int:
    if not line.strip() or _NOISE_LINE.match(line):
        return 0
    kind = structured(line)
    if kind:
        return 2 if kind == "loud" else 0
    if _STRONG.search(line):
        return 2
    return 1 if _WEAK.search(line) and not _PROPERTY.match(line) and not _FRAME.match(line) else 0


def _shorten(line: str) -> str:
    """A long line cut to `_MAX_LINE` around its match: a one-line failure can carry its error after 400 chars of other text."""
    line = line.rstrip()
    if len(line) <= _MAX_LINE:
        return line
    match = _STRONG.search(line) or _WEAK.search(line)
    start = max(0, match.start() - 60) if match else 0
    return ("…" if start else "") + line[start:start + _MAX_LINE]


def _continues(line: str, after_blank: bool = False) -> bool:
    """A line that still belongs to the error above it: indented detail, a separator or a diff, the assertion's values,
    another match, and right under it (not after a blank) a label like `Call log:`. A plain unindented line is unrelated
    output and ends the context."""
    return bool(line[:1].isspace() or line.startswith(("+", "-", "=", "_", "~", ">")) or "!==" in line
                or (not after_blank and _LABEL.match(line)) or _rank(line))


def _segments(lines: list[str], context: int) -> list[tuple[int, list[str]]]:
    """(rank, lines) for each matched line with the few lines that explain it: a Playwright call log, the assertion's values,
    the first stack frame. A match inside the context extends it; the remaining stack frames are skipped."""
    out: list[tuple[int, list[str]]] = []
    i, total = 0, len(lines)
    while i < total:
        rank = _rank(lines[i])
        if not rank:
            i += 1
            continue
        segment, left, framed, j = [lines[i]], context, False, i + 1
        while j < total and left > 0 and len(segment) < 3 * context:
            line = lines[j]
            if not line.strip():
                if j + 1 < total and lines[j + 1].strip() and _continues(lines[j + 1], True) and not noise(lines[j + 1]):
                    j += 1
                    continue
                break
            if noise(line) or not _continues(line):
                break
            if _FRAME.match(line):
                if framed:
                    j += 1
                    continue
                framed = True
            elif framed and not _rank(line):
                break                                   # after the stack: a dumped error object or unrelated output
            line_rank = _rank(line)
            rank = max(rank, line_rank)
            left = context if line_rank else left - 1
            segment.append(line)
            j += 1
        out.append((rank, segment))
        i = j
    return out


def decisive_excerpt(text: str, limit: int = 1200, *, context: int = 4, exclude: str = "") -> str:
    """The matched error lines of `text`, anywhere in it, with their context: deduplicated, in order, at most `limit` chars.
    Weak matches are dropped first when everything does not fit; lines already in `exclude` are not repeated."""
    lines = str(text or "").splitlines()          # ranked whole (a JSON record cut short is no longer one), shortened after
    seen = {line.strip() for line in exclude.splitlines() if line.strip()}
    picked: list[tuple[int, list[str]]] = []
    for rank, segment in _segments(lines, context):
        fresh = []
        for line in map(_shorten, segment):
            if line.strip() and line.strip() not in seen:
                seen.add(line.strip())
                fresh.append(line)
        if fresh:
            picked.append((rank, fresh))
    size = sum(len(line) + 1 for _, segment in picked for line in segment)
    for index in range(len(picked) - 1, -1, -1):          # over budget: the weak segments go first, from the end
        if size <= limit:
            break
        if picked[index][0] < 2:
            size -= sum(len(line) + 1 for line in picked[index][1])
            picked[index] = (0, [])
    # one long segment (a whole stack, a dozen assertions) must not hide the ones after it: each gets half the room at most
    share = limit if sum(1 for _, segment in picked if segment) < 2 else max(limit // 2, _MAX_LINE)
    out: list[str] = []
    used = 0
    for _, segment in picked:
        taken = 0
        for line in segment:
            if used + len(line) + 1 > limit:
                return "\n".join(out)
            if taken + len(line) + 1 > share:
                break
            out.append(line)
            used += len(line) + 1
            taken += len(line) + 1
    return "\n".join(out)


def first_decisive(text: str) -> str:
    """The first strong line of `text` (else the first weak one), stripped; '' when nothing matches."""
    weak = ""
    for line in str(text or "").splitlines():
        rank = _rank(line)
        if rank == 2:
            return _shorten(line.strip())
        if rank and not weak:
            weak = _shorten(line.strip())
    return weak


def is_decisive(line: str) -> bool:
    return _rank(line) == 2


def clip(text: str, limit: int, *, keep: str = "head", marker: str = "\n…\n") -> str:
    """`text` cut to at most `limit` chars without losing the decisive lines of the part that is cut: the head (or the tail)
    that fits, then (before, for the tail) up to a third of the room with the decisive lines found in what was dropped."""
    text = str(text or "")
    if len(text) <= limit:
        return text
    room = max(0, limit // 3 - len(marker))
    kept_len = limit - limit // 3
    if keep == "tail":
        kept, dropped = text[-kept_len:], text[:-kept_len]
    else:
        kept, dropped = text[:kept_len], text[kept_len:]
    extra = decisive_excerpt(dropped, room, exclude=kept) if room > 0 else ""
    if not extra:
        return ("… " + text[-(limit - 2):].lstrip()) if keep == "tail" else (text[:limit - 2].rstrip() + " …")
    if keep == "tail":
        return extra + marker + text[-(limit - len(extra) - len(marker)):]
    return text[:limit - len(extra) - len(marker)].rstrip() + marker + extra


# --------------------------------------------------------------------------------------------------- missing modules
_MISSING = re.compile(r"Cannot find (?:module|package) ['\"`](?P<js>[^'\"`\n]+)['\"`]|Can't resolve ['\"`](?P<wp>[^'\"`\n]+)['\"`]"
                      r"|Failed to resolve import ['\"`](?P<vite>[^'\"`\n]+)['\"`]|No module named ['\"]?(?P<py>[\w.]+)")
_SOURCE_EXT = re.compile(r"\.(?:[cm]?tsx?|jsx|py|vue|svelte|astro)$")
_ANY_MISSING = re.compile(r"MODULE_NOT_FOUND|Cannot find (?:module|package)|No module named|ModuleNotFoundError|Can't resolve"
                          r"|Failed to resolve import")


def module_kind(name: str, known: Iterable[str] = ()) -> str:
    """'source' for a file of the repository the import names (a relative or absolute path, `/workspace/...`, a path alias
    like `@/lib/x`, a subpath import `#x`, a source extension, or a name that is a declared path of the plan), else 'package'
    (a bare specifier like `react`, `@scope/pkg`, a Python top-level distribution the repository does not hold)."""
    spec = name.strip()
    if "/node_modules/" in spec or spec.startswith("node_modules/"):
        return "package"                                # a broken install, not a missing file of the work
    if spec.startswith((".", "/", "file:", "~", "@/", "#")) or re.match(r"^[A-Za-z]:[\\/]", spec) or _SOURCE_EXT.search(spec):
        return "source"
    candidates = {spec.strip("/")}
    if re.fullmatch(r"[\w.]+", spec):
        candidates.add(spec.replace(".", "/"))          # a dotted Python module is a path in the repository
    for path in known:
        path = "/" + str(path).strip().lstrip("./").strip("/")
        stem = path.rsplit(".", 1)[0] if "." in path.rsplit("/", 1)[-1] else path
        if any(f"/{c}/" in path + "/" or stem.endswith("/" + c) for c in candidates if c):
            return "source"
    return "package"


def missing_modules(text: str, known: Iterable[str] = ()) -> list[tuple[str, str]]:
    """(name, 'package' | 'source') for every module the output says it cannot find, unique, in order of appearance."""
    known = tuple(known)
    found: dict[str, str] = {}
    for match in _MISSING.finditer(str(text or "")):
        name = next(value for value in match.groupdict().values() if value)
        name = name.removeprefix("file://") if name.startswith("file:///") else name
        found.setdefault(name, module_kind(name, known))
    return list(found.items())


def mentions_missing_module(text: str) -> bool:
    return bool(_ANY_MISSING.search(str(text or "")))


# --------------------------------------------------------------------------------------------------- resource limits
_MEMORY = re.compile(r"JavaScript heap out of memory|Ineffective mark-compacts near heap limit|Reached heap limit|heap limit Allocation"
                     r" failed|\bCannot allocate memory\b|std::bad_alloc|\bMemoryError\b|^\s*Killed\s*$|\bENOMEM\b", re.MULTILINE)
_PROCESSES = re.compile(r"pthread_create|uv_thread_create|\bspawn\b[^\n]*\bEAGAIN\b|fork: (?:retry|Resource temporarily unavailable)"
                        r"|Resource temporarily unavailable")


def resource_limit(text: str) -> tuple[str, str]:
    """('memory' | 'processes', the line that shows it) when the output shows the sandbox ran out of memory (the Node heap,
    an allocation, a process killed) or could not start a process or thread; ('', '') otherwise."""
    text = str(text or "")
    for kind, pattern in (("memory", _MEMORY), ("processes", _PROCESSES)):
        match = pattern.search(text)
        if match:
            start = text.rfind("\n", 0, match.start()) + 1
            end = text.find("\n", match.end())
            return kind, text[start:end if end >= 0 else len(text)].strip()[:200]
    return "", ""

