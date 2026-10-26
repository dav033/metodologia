"""Spanish translation of a requirement's planning documents, kept current while the conversation edits them.

The English files stay the source of truth. Each document is cut into sections; every section's translation is cached
by the SHA-256 of its English text (`.translations/cache.json`), so an edit retranslates only the sections it touched.
`PLAN.es.md`, `SPEC.es.md` and `design/<contract>@vN.es.md` are written next to their originals; the plan's subplan
and task titles are translated through the same cache. A cheap model runs with no tools, in an empty directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CACHE_DIR = ".translations"
SECTION_MAX = 6000      # characters per section sent at once
BATCH_MAX = 14000       # characters per model call
DEBOUNCE_SEC = 10       # wait for the conversation to stop typing into a file before translating it
RUN_TTL_SEC = 30 * 60
RETRY_SEC = 5 * 60
MAX_STREAK = 3
PROMPT = """Translate every string of the JSON array below from English to Spanish (neutral Latin American,
technical register). Keep the Markdown structure exactly: headings, lists, tables, emphasis and line breaks. Do not
translate code spans, code blocks, file paths, commands, URLs, identifiers (REQ-001, SP-2, T14, R3, D-127, UI-AC-01,
contract@v1) or product names. Answer with ONLY a JSON array of strings: same length, same order, no commentary.

{payload}"""
_FRONT = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sections(text: str) -> tuple[str, list[str]]:
    """(front matter kept verbatim, translatable sections) — cut at headings, then at blank lines outside fences."""
    match = _FRONT.match(text)
    front, body = (match.group(0), text[match.end():]) if match else ("", text)
    out: list[str] = []
    for part in re.split(r"(?m)^(?=#{1,3} )", body):
        while len(part) > SECTION_MAX:
            cut, fence, pos = -1, False, 0
            for line in part.splitlines(keepends=True):
                if line.lstrip().startswith("```"):
                    fence = not fence
                pos += len(line)
                if not fence and not line.strip() and pos <= SECTION_MAX:
                    cut = pos
            if cut <= 0:
                break
            out.append(part[:cut])
            part = part[cut:]
        if part:
            out.append(part)
    return front, out


def _cache_file(rdir: Path) -> Path:
    return Path(rdir) / CACHE_DIR / "cache.json"


def load_cache(rdir: Path) -> dict[str, str]:
    try:
        data = json.loads(_cache_file(rdir).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_cache(rdir: Path, cache: dict[str, str]) -> None:
    target = _cache_file(rdir)
    target.parent.mkdir(parents=True, exist_ok=True)
    current = load_cache(rdir)  # a concurrent run may have added entries: never drop them
    current.update(cache)
    fd, tmp = tempfile.mkstemp(prefix=".cache.", dir=target.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(current, stream, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, target)


def documents(rdir: Path) -> list[tuple[Path, Path]]:
    """(English source, Spanish output) for every translated document of the requirement."""
    rdir = Path(rdir)
    pairs = [(rdir / name, rdir / name.replace(".md", ".es.md")) for name in ("SPEC.md", "PLAN.md")]
    pairs += [(f, f.with_name(f.name[:-3] + ".es.md")) for f in sorted((rdir / "design").glob("*@v*.md"))
              if not f.name.endswith(".es.md")]
    return [(src, dst) for src, dst in pairs if src.is_file()]


def plan_strings(rdir: Path) -> list[str]:
    """Short texts of PLAN.json the web shows per subplan: titles, outcomes, criteria and task titles."""
    import bt_design_drafts
    out: list[str] = [m.get("title") or "" for m in bt_design_drafts._plan(rdir).get("milestones") or []
                      if isinstance(m, dict)]
    for item in bt_design_drafts.subplans(rdir):
        out += [item["title"], item["outcome"], *[c for c in item["criteria"] if isinstance(c, str)]]
        out += [t.get("title") or "" for t in item["tasks"]]
    return [s for s in dict.fromkeys(out) if s and s.strip()]


def pending(rdir: Path) -> list[str]:
    """English texts that still have no translation in the cache."""
    cache = load_cache(rdir)
    texts = [s for src, _ in documents(rdir) for s in sections(src.read_text(encoding="utf-8"))[1]] + plan_strings(rdir)
    return [t for t in dict.fromkeys(texts) if t.strip() and _sha(t) not in cache]


def render(rdir: Path, text: str) -> tuple[str, int]:
    """Spanish text of an English document from the cache, English where a section is missing; returns the count."""
    cache = load_cache(rdir)
    front, parts = sections(text)
    missing = sum(1 for p in parts if p.strip() and _sha(p) not in cache)
    return front + "".join(cache.get(_sha(p), p) if p.strip() else p for p in parts), missing


def phrase(cache: dict[str, str], text: str) -> str:
    return cache.get(_sha(text), text) if text else text


def _write_outputs(rdir: Path) -> None:
    for src, dst in documents(rdir):
        es, _ = render(rdir, src.read_text(encoding="utf-8"))
        if not dst.is_file() or dst.read_text(encoding="utf-8") != es:
            dst.write_text(es, encoding="utf-8")


def _route(project: str) -> dict:
    import bt_config
    import bt_delegate
    pinned = bt_config.get("translate.route", None)  # {"profile", "model", "effort"} to pin one account
    if isinstance(pinned, dict) and pinned.get("profile"):
        import bt_profiles
        return {"agent": bt_profiles.provider_of(pinned["profile"]), **pinned}
    return bt_delegate.auto_route(project, "test", None, role="runner")


def complete(project: str, prompt: str, *, timeout: int = 600) -> str:
    """One tool-less model answer (text) from the router's runner-role choice."""
    import bt_profiles
    route = _route(project)
    agent, profile, model, effort = route["agent"], route.get("profile"), route.get("model"), route.get("effort")
    spec = bt_profiles.get(profile) if profile else {"bin": agent}
    binary = shutil.which(spec.get("bin") or agent)
    if not binary:
        raise RuntimeError(f"{agent} is not on PATH")
    env = bt_profiles.session_env(profile, agent, None, project)
    with tempfile.TemporaryDirectory(prefix="bt-translate-") as work:
        if agent == "claude":
            empty = Path(work) / "mcp.json"
            empty.write_text('{"mcpServers": {}}', encoding="utf-8")
            argv = [binary, "--print", "--model", model, "--tools", "", "--strict-mcp-config", "--mcp-config", str(empty),
                    "--setting-sources", "project", "--disable-slash-commands", "--output-format", "text"]
            argv += ["--effort", effort] if effort else []
            done = subprocess.run(argv, input=prompt, cwd=work, env=env, capture_output=True, text=True,
                                  timeout=timeout, check=False)
            answer = done.stdout
        elif agent == "codex":
            last = Path(work) / "answer.txt"
            argv = [binary, "exec", "--model", model, "--sandbox", "read-only", "--skip-git-repo-check", "-C", work,
                    "--output-last-message", str(last)]
            argv += ["--config", f"model_reasoning_effort={json.dumps(effort)}"] if effort else []
            done = subprocess.run([*argv, "-"], input=prompt, cwd=work, env=env, capture_output=True, text=True,
                                  timeout=timeout, check=False)
            answer = last.read_text(encoding="utf-8") if last.is_file() else ""
        else:
            raise RuntimeError(f"translation does not support provider {agent}")
    if done.returncode != 0 or not answer.strip():
        raise RuntimeError(f"{agent} {model} failed ({done.returncode}): {(done.stderr or '')[-300:]}")
    return answer


def _parse(answer: str, size: int) -> list[str] | None:
    start, end = answer.find("["), answer.rfind("]")
    try:
        items = json.loads(answer[start:end + 1]) if start >= 0 < end else None
    except ValueError:
        return None
    if not isinstance(items, list) or len(items) != size or not all(isinstance(i, str) for i in items):
        return None
    return items


def _batches(texts: list[str]) -> list[list[str]]:
    out, cur, size = [], [], 0
    for text in texts:
        if cur and size + len(text) > BATCH_MAX:
            out.append(cur)
            cur, size = [], 0
        cur.append(text)
        size += len(text)
    return out + ([cur] if cur else [])


def translate(project: str, rdir: Path, *, ask=None) -> dict:
    """Translate every pending section; writes the cache and the .es.md files after each batch (progress shows)."""
    raw = ask or (lambda prompt: complete(project, prompt))

    def ask(prompt: str) -> str:  # no account or a usage limit (SystemExit) must still end in last.json
        try:
            return raw(prompt)
        except (SystemExit, Exception) as exc:  # noqa: BLE001 - recorded as a failed section, never raised
            raise RuntimeError(str(exc)) from None

    todo, done, failed = pending(rdir), 0, 0
    for batch in _batches(todo):
        result = None
        try:
            result = _parse(ask(PROMPT.format(payload=json.dumps(batch, ensure_ascii=False))), len(batch))
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            result = None
        if result is None and len(batch) > 1:  # one bad answer must not lose the whole batch
            result = []
            for text in batch:
                try:
                    one = _parse(ask(PROMPT.format(payload=json.dumps([text], ensure_ascii=False))), 1)
                except (RuntimeError, OSError, subprocess.TimeoutExpired):
                    one = None
                result.append(one[0] if one else None)
        pairs = {_sha(t): tr for t, tr in zip(batch, result or []) if tr}
        done, failed = done + len(pairs), failed + len(batch) - len(pairs)
        if pairs:
            _save_cache(rdir, pairs)
            _write_outputs(rdir)
    _write_outputs(rdir)
    try:
        streak = json.loads((Path(rdir) / CACHE_DIR / "last.json").read_text(encoding="utf-8")).get("streak", 0)
    except (OSError, ValueError, AttributeError):
        streak = 0
    result = {"translated": done, "failed": failed, "pending": len(pending(rdir)), "at": time.time(),
              "streak": 0 if done or not failed else int(streak) + 1}
    (Path(rdir) / CACHE_DIR).mkdir(parents=True, exist_ok=True)
    (Path(rdir) / CACHE_DIR / "last.json").write_text(json.dumps(result), encoding="utf-8")
    if done:
        import bt_planning_activity
        bt_planning_activity.record(rdir, "Traducción", f"Español al día · {done} secciones traducidas"
                                    + (f", {failed} pendientes" if failed else ""), kind="translate")
    return result


def _lock(rdir: Path) -> Path:
    return Path(rdir) / CACHE_DIR / "run.json"


def running(rdir: Path) -> bool:
    try:
        info = json.loads(_lock(rdir).read_text(encoding="utf-8"))
        os.kill(int(info["pid"]), 0)
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return time.time() - float(info.get("at", 0)) < RUN_TTL_SEC


def start_background(project: str, rdir: Path) -> int | None:
    """Translate in a detached process unless one is already at work; returns its pid."""
    import bt_platform as host
    from bt_core import ROOT, SCRIPT, req_id
    if running(rdir):
        return None
    _lock(rdir).parent.mkdir(parents=True, exist_ok=True)
    log = (_lock(rdir).parent / "run.log").open("ab")
    proc = subprocess.Popen([sys.executable, str(SCRIPT), "--project", project, "translate", req_id(Path(rdir))],
                            stdin=subprocess.DEVNULL, stdout=log, stderr=log, close_fds=True,
                            env={**os.environ, "BITACORA_ROOT": str(ROOT)}, **host.detached_options())
    _lock(rdir).write_text(json.dumps({"pid": proc.pid, "at": time.time()}), encoding="utf-8")
    return proc.pid


def ensure(project: str, rdir: Path, *, now: float | None = None) -> bool:
    """Start a background translation when something is pending and its sources stopped changing."""
    now = time.time() if now is None else now
    sources = [src for src, _ in documents(rdir)] + [Path(rdir) / "PLAN.json"]
    newest = max((f.stat().st_mtime for f in sources if f.is_file()), default=0)
    if now - newest < DEBOUNCE_SEC or running(rdir) or not pending(rdir):
        return False
    try:  # a run that just failed (no account, usage limit) is not retried on every page refresh
        last = json.loads((Path(rdir) / CACHE_DIR / "last.json").read_text(encoding="utf-8"))
        if last.get("failed") and (now - float(last["at"]) < RETRY_SEC or int(last.get("streak", 0)) >= MAX_STREAK):
            return False  # after MAX_STREAK runs that translated nothing, only `bitacora.py translate` retries
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return start_background(project, rdir) is not None


def status(rdir: Path) -> dict:
    return {"running": running(rdir), "pending": len(pending(rdir))}
