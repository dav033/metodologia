"""Full regression of one metodologia worktree: every tests/test_*.py in isolation (its own BITACORA_ROOT).

Legacy suites run under the system interpreter, suites that need the new packages (DBOS, pydantic, the supervisor)
under the worktree's uv venv; the heavy durable/supervisor end-to-end suites run one at a time after the rest. It was
an operator's scratchpad script until REQ-031: the integration (`bt_integrate`) and the Solucionador run it now.

A failure is judged in three steps: a suite in the known baseline (`integrate.allowed_failures`) is allowed; any other
failing suite runs once more ALONE (load flakes seen on 2026-10-29: test_platform, test_supervisor_limits pass alone);
what still fails is real and stops an integration.

usage: python3 bt_regress.py <worktree> <scratch> <results.txt> [only.txt]
"""
from __future__ import annotations

import concurrent.futures as cf
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

NEW = re.compile(r"\b(bt_durable|bt_contracts|bt_supervisor|pydantic|dbos|hypothesis|psutil|durable_support|"
                 r"supervisor_support|test_durable_\w+|bench_runtimes)\b")
HEAVY = re.compile(r"^test_(durable_|supervisor_)")
BASELINE = ("test_plan_boundary", "test_real_designer_kit", "test_recovery_views", "test_remote_panel")
SYSTEM_PYTHON = "/usr/bin/python3"
TIMEOUT = 1800


@dataclass
class Result:
    lines: list[str]                       # "<suite> <exit code> <seconds> <interpreter>", sorted
    failed: list[str] = field(default_factory=list)      # suites that failed in the full run
    allowed: list[str] = field(default_factory=list)     # failed, but in the known baseline
    flaky: list[str] = field(default_factory=list)       # failed in the full run, passed alone
    real: list[str] = field(default_factory=list)        # failed again alone: the regression is red

    @property
    def ok(self) -> bool:
        return not self.real

    def summary(self) -> str:
        """The line that goes to the release log: `291 files, only the 4 baseline failures` or what failed."""
        text = f"{len(self.lines)} files"
        if self.real:
            return f"{text}, {len(self.real)} real failure(s): {', '.join(self.real)}"
        extra = f" + {', '.join(self.flaky)} (load flake, passes alone)" if self.flaky else ""
        if self.allowed:
            return f"{text}, only baseline failures ({', '.join(self.allowed)}){extra}"
        return f"{text}, no failures{extra}"


def allowed_failures() -> tuple[str, ...]:
    try:
        import bt_config
        value = bt_config.get("integrate.allowed_failures", list(BASELINE))
    except Exception:  # noqa: BLE001 - outside a bitácora the baseline is the known list
        value = list(BASELINE)
    return tuple(value) if isinstance(value, list) else BASELINE


def run_suite(worktree: Path, scratch: Path, path: Path, tag: str = "") -> str:
    """One suite in its own process and root; returns its result line. `tag` keeps a rerun's logs apart."""
    tests = worktree / "skill" / "scripts" / "tests"
    name = path.stem
    new = bool(NEW.search(path.read_text(encoding="utf-8", errors="replace")))
    root = scratch / "roots" / f"{name}{tag}"
    root.mkdir(parents=True, exist_ok=True)
    lab = scratch / "lab"
    lab.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "BITACORA_ROOT": str(root), "BT_LAB_DIR": str(lab),
           "PYTHONPATH": f"{worktree / 'skill' / 'scripts'}:{tests}"}
    for leak in ("BITACORA_ATTEMPT", "BITACORA_TASK", "BITACORA_DELEGATION", "BT_DURABLE_DATABASE_URL"):
        env.pop(leak, None)                # a suite must never reach the live engine's database or act as a run
    venv = worktree / ".venv" / "bin" / "python"
    interpreter = str(venv) if new else SYSTEM_PYTHON
    log = scratch / "logs" / f"{name}{tag}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        done = subprocess.run([interpreter, "-m", "unittest", name], cwd=tests, env=env, capture_output=True,
                              text=True, timeout=TIMEOUT)
        code = done.returncode
        log.write_text(done.stdout + done.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired:
        code = 124
        log.write_text("TIMEOUT", encoding="utf-8")
    return f"{name} {code} {round(time.monotonic() - started)} {'venv' if new else 'python3'}"


def suites(worktree: Path, only: Iterable[str] | None = None) -> list[Path]:
    files = sorted((worktree / "skill" / "scripts" / "tests").glob("test_*.py"))
    if only is not None:
        wanted = set(only)
        files = [f for f in files if f.stem in wanted]
    return files


def judge(lines: list[str], allowed: Iterable[str], rerun: Callable[[str], bool]) -> Result:
    """Classify the full run's failures; `rerun(name)` runs one suite alone and says whether it passed."""
    result = Result(lines=sorted(lines))
    allowed = set(allowed)
    for line in result.lines:
        name, code = line.split()[:2]
        if code == "0":
            continue
        result.failed.append(name)
        if name in allowed:
            result.allowed.append(name)
        elif rerun(name):
            result.flaky.append(name)
        else:
            result.real.append(name)
    return result


def run(worktree: Path, scratch: Path, out: Path | None = None, *, only: Iterable[str] | None = None,
        workers: int = 6, allowed: Iterable[str] | None = None, suite: Callable[..., str] = run_suite) -> Result:
    worktree, scratch = Path(worktree), Path(scratch)
    files = suites(worktree, only)
    heavy = [f for f in files if HEAVY.match(f.stem)]
    light = [f for f in files if not HEAVY.match(f.stem)]
    lines: list[str] = []
    with cf.ThreadPoolExecutor(workers) as pool:
        lines += list(pool.map(lambda f: suite(worktree, scratch, f), light))
    for f in heavy:
        lines.append(suite(worktree, scratch, f))
    by_name = {f.stem: f for f in files}
    rerun_lines: list[str] = []

    def rerun(name: str) -> bool:
        line = suite(worktree, scratch, by_name[name], ".rerun")
        rerun_lines.append(line)
        return line.split()[1] == "0"

    result = judge(lines, allowed_failures() if allowed is None else allowed, rerun)
    if out is not None:
        Path(out).write_text("\n".join(result.lines) + "\n"
                             + "".join(f"# rerun alone: {line}\n" for line in rerun_lines)
                             + f"# {result.summary()}\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in (3, 4):
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    only = Path(args[3]).read_text(encoding="utf-8").split() if len(args) == 4 else None
    result = run(Path(args[0]), Path(args[1]), Path(args[2]), only=only)
    print(result.summary())
    for name in result.real:
        print(f"FAILED {name} (log: {Path(args[1]) / 'logs' / (name + '.rerun.log')})")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
