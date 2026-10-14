"""Native diagram capability: the pinned Archify renderer behind a safe, atomic, bitácora-aware adapter.

Archify (MIT, vendored byte-for-byte under skill/vendor/archify, see PIN.json) renders JSON-IR into standalone HTML.
This adapter owns what the renderer must not: bounded input, a scrubbed environment with the update check
disabled, a deadline and output cap, validation before publishing, and an atomic swap so a failed render never
replaces a previously valid artifact. Source IR and a provenance record are kept beside every HTML so it can be
regenerated. Missing Node disables diagrams with an actionable error, never anything else.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from bt_resources import resource_root

TYPES = ("architecture", "workflow", "sequence", "dataflow", "lifecycle")  # the five the owner asked for
MAX_IR_BYTES = 512 * 1024
MAX_HTML_BYTES = 8 * 1024 * 1024
DEADLINE_SEC = 60
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")


class DiagramError(Exception):
    """`code` is stable for callers; `message` is for people."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


def renderer_dir() -> Path:
    return resource_root() / "vendor" / "archify"


def pin() -> dict:
    return json.loads((renderer_dir() / "PIN.json").read_text(encoding="utf-8"))


def node() -> str:
    found = shutil.which("node")
    if not found:
        raise DiagramError("NODE_MISSING", "Node.js 18+ is required to render diagrams; install it and retry "
                           "(nothing else in the platform depends on it)")
    return found


def _run(args: list[str], timeout: float = DEADLINE_SEC) -> subprocess.CompletedProcess:
    scratch = tempfile.mkdtemp(prefix="diagram-run-")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": scratch, "LANG": "C.UTF-8",
           "ARCHIFY_UPDATE_CHECK_DISABLED": "1", "NO_COLOR": "1", "TMPDIR": scratch}
    try:
        process = subprocess.Popen([node(), str(renderer_dir() / "bin" / "archify.mjs"), *args],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
                                   cwd=scratch, start_new_session=True)
        try:
            out, err = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise DiagramError("TIMEOUT", f"the renderer did not finish within {int(timeout)} s") from None
        return subprocess.CompletedProcess(process.args, process.returncode, out[-200_000:], err[-20_000:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _check_type(diagram_type: str) -> None:
    if diagram_type not in TYPES:
        raise DiagramError("BAD_TYPE", f"type must be one of {', '.join(TYPES)}")


def _read_ir(path: Path) -> bytes:
    data = Path(path).read_bytes()
    if len(data) > MAX_IR_BYTES:
        raise DiagramError("IR_TOO_LARGE", f"IR is {len(data)} bytes; the limit is {MAX_IR_BYTES}")
    try:
        json.loads(data)
    except ValueError as error:
        raise DiagramError("IR_NOT_JSON", str(error)[:200]) from None
    return data


def validate(diagram_type: str, ir_path: Path) -> dict:
    """The renderer's structured verdict: {'ok': bool, 'diagnostics': [...]}."""
    _check_type(diagram_type)
    _read_ir(ir_path)
    done = _run(["validate", diagram_type, str(ir_path), "--json"])
    try:
        report = json.loads(done.stdout)
    except ValueError:
        raise DiagramError("RENDERER_FAILED", (done.stderr or done.stdout)[-400:] or "no output") from None
    return {"ok": bool(report.get("ok")) and done.returncode == 0, "diagnostics": report.get("diagnostics", [])}


def external_references(html: str) -> list[str]:
    """http(s) resources a browser fetches on open: src=, <link href>, url(), @import, <form action>. Plain
    `<a href>` navigation (the renderer's attribution link) is not a fetch and is ignored."""
    found = re.findall(r"""\bsrc\s*=\s*["'](https?://[^"']+)""", html, re.IGNORECASE)
    found += re.findall(r"""<link\b[^>]*\bhref\s*=\s*["'](https?://[^"']+)""", html, re.IGNORECASE)
    found += re.findall(r"""<form\b[^>]*\baction\s*=\s*["'](https?://[^"']+)""", html, re.IGNORECASE)
    found += re.findall(r"url\(\s*['\"]?(https?://[^)'\"]+)", html, re.IGNORECASE)
    found += re.findall(r"@import\s+(?:url\()?['\"]?(https?://[^)'\";]+)", html, re.IGNORECASE)
    return sorted(set(found))


def _render_to(diagram_type: str, ir_path: Path, out: Path) -> None:
    done = _run(["render", diagram_type, str(ir_path), str(out)])
    if done.returncode != 0 or not out.exists():
        raise DiagramError("RENDER_FAILED", (done.stderr or done.stdout)[-600:] or "the renderer produced nothing")
    if out.stat().st_size > MAX_HTML_BYTES:
        out.unlink(missing_ok=True)
        raise DiagramError("OUTPUT_TOO_LARGE", f"HTML exceeds {MAX_HTML_BYTES} bytes")
    refs = external_references(out.read_text(encoding="utf-8", errors="replace"))
    if refs:
        out.unlink(missing_ok=True)
        raise DiagramError("NETWORK_REFERENCE", f"the HTML would fetch {refs[:3]}; diagrams must be standalone")


def publish(project_dir: Path, name: str, diagram_type: str, ir_path: Path, *, title: str | None = None) -> dict:
    """validate -> render -> verify -> swap into <project>/artifacts as diagram-<name>.{html,ir.json,provenance.json}.
    Any failure leaves the previous artifact untouched."""
    _check_type(diagram_type)
    if not NAME_RE.match(name or ""):
        raise DiagramError("BAD_NAME", "name must be lowercase letters, digits and dashes (max 61 characters)")
    ir = _read_ir(ir_path)
    verdict = validate(diagram_type, ir_path)
    if not verdict["ok"]:
        raise DiagramError("INVALID_IR", json.dumps(verdict["diagnostics"][:3])[:600])
    artifacts = Path(project_dir) / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="diagram-pub-", dir=artifacts) as stage_name:
        stage = Path(stage_name)
        html = stage / "diagram.html"
        staged_ir = stage / "ir.json"
        staged_ir.write_bytes(ir)
        _render_to(diagram_type, staged_ir, html)
        provenance = {"kind": "diagram", "type": diagram_type, "name": name, "title": title or name,
                      "ir_sha256": hashlib.sha256(ir).hexdigest(),
                      "html_sha256": hashlib.sha256(html.read_bytes()).hexdigest(),
                      "renderer": {k: pin()[k] for k in ("name", "version", "commit", "tree_sha256")},
                      "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        (stage / "provenance.json").write_text(json.dumps(provenance, indent=1) + "\n", encoding="utf-8")
        target = f"diagram-{name}"
        for source, suffix in ((staged_ir, ".ir.json"), (stage / "provenance.json", ".provenance.json"),
                               (html, ".html")):  # the page last: a listing never points at a missing IR
            os.replace(source, artifacts / f"{target}{suffix}")
    return {"html": str(artifacts / f"diagram-{name}.html"), **provenance}


def compare(project_dir: Path, name: str, base_ir: Path, head_ir: Path) -> dict:
    """Before/after architecture comparison (improve-architecture evidence) published like any diagram."""
    if not NAME_RE.match(name or ""):
        raise DiagramError("BAD_NAME", "name must be lowercase letters, digits and dashes (max 61 characters)")
    _read_ir(base_ir)
    _read_ir(head_ir)
    artifacts = Path(project_dir) / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="diagram-cmp-", dir=artifacts) as stage_name:
        out = Path(stage_name) / "compare.html"
        done = _run(["compare", "architecture", str(base_ir), str(head_ir), str(out)])
        if done.returncode != 0 or not out.exists():
            raise DiagramError("COMPARE_FAILED", (done.stderr or done.stdout)[-600:] or "no output")
        refs = external_references(out.read_text(encoding="utf-8", errors="replace"))
        if refs or out.stat().st_size > MAX_HTML_BYTES:
            raise DiagramError("COMPARE_REJECTED", "comparison is too large or fetches external resources")
        final = artifacts / f"diagram-{name}.compare.html"
        os.replace(out, final)
    return {"html": str(final), "base_sha256": hashlib.sha256(Path(base_ir).read_bytes()).hexdigest(),
            "head_sha256": hashlib.sha256(Path(head_ir).read_bytes()).hexdigest()}


def browser() -> str | None:
    for name in ("chromium", "google-chrome", "chromium-browser", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    return None


def visual_check(html_path: Path, timeout: float = 150) -> dict:
    """Automated light/dark, two-size browser capture of a published page (Archify visual-check). The screenshots and
    receipt land beside the page. A human still looks at them: the result says `visualReview: pending`."""
    chrome = browser()
    if not chrome:
        raise DiagramError("BROWSER_MISSING", "no Chromium/Chrome found; install one or review the page by hand")
    html_path = Path(html_path)
    # A republished HTML must not overwrite receipts owned by its previous content hash.
    digest = hashlib.sha256(html_path.read_bytes()).hexdigest()
    evidence_dir = html_path.parent / f"{html_path.stem}.visual-{digest[:16]}"
    scratch = tempfile.mkdtemp(prefix="diagram-visual-")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": scratch, "TMPDIR": scratch,
           "ARCHIFY_UPDATE_CHECK_DISABLED": "1", "ARCHIFY_CHROME": chrome,
           "ARCHIFY_CHROME_NO_SANDBOX": "1"}  # the page is generated by this adapter and loaded from a local file
    try:
        done = subprocess.run([node(), str(renderer_dir() / "bin" / "archify.mjs"), "visual-check", str(html_path),
                               "--summary", "--out-dir", str(evidence_dir)],
                              capture_output=True, text=True, env=env, cwd=scratch, timeout=timeout, check=False)
        try:
            return json.loads(done.stdout)
        except ValueError:
            raise DiagramError("VISUAL_CHECK_FAILED", (done.stderr or done.stdout)[-400:]) from None
    except subprocess.TimeoutExpired:
        raise DiagramError("TIMEOUT", f"visual check exceeded {int(timeout)} s") from None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def doctor() -> dict:
    """Capability report: never raises; says what is missing."""
    info = {"renderer": pin() if (renderer_dir() / "PIN.json").exists() else None, "node": shutil.which("node"),
            "types": list(TYPES), "browser": browser()}
    info["ready"] = bool(info["renderer"] and info["node"])
    return info
