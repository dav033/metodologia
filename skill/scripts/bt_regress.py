"""Full regression of one metodologia worktree: every tests/test_*.py in isolation (its own BITACORA_ROOT).

Legacy suites run under the system interpreter, suites that need the new packages (DBOS, pydantic, the supervisor)
under the worktree's uv venv; the heavy durable/supervisor end-to-end suites run one at a time after the rest. It was
an operator's scratchpad script until REQ-031: the integration (`bt_integrate`) and the Solucionador run it now.

A failure is judged in three steps: a suite in the known baseline (`integrate.allowed_failures`) is allowed; any other
failing suite runs once more ALONE (a load flake passes alone); what still fails is real and stops an integration. The
baseline is empty since 2026-10-29: its four suites (test_plan_boundary, test_real_designer_kit, test_recovery_views,
test_remote_panel) and the two load flakes (test_platform, test_supervisor_limits) were fixed at their origin. The
mechanism stays for a failure the owner accepts for a while; the live config can list it.

Selection (D-NNN, `bt_regress_select`): with `--mode staged` the suites the branch's changes can reach run first and a
red there stops at once (the fast red); then the rest run. `--mode selective` runs the selected suites alone. A
selection that is not trusted runs everything. The results file lists why each suite was selected and how long each
phase took; `--dry-run` prints the selection, and with `--timings <an earlier results.txt>` its time vs the full one.

usage: python3 bt_regress.py <worktree> <scratch> <results.txt> [only.txt] [--mode full|staged|selective] [--base main]
       python3 bt_regress.py <worktree> --dry-run [--base main] [--timings results.txt]
"""
from __future__ import annotations

import argparse
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
BASELINE: tuple[str, ...] = ()
SYSTEM_PYTHON = "/usr/bin/python3"
TIMEOUT = 1800


@dataclass
class Result:
    lines: list[str]                       # "<suite> <exit code> <seconds> <interpreter>", sorted
    failed: list[str] = field(default_factory=list)      # suites that failed in the full run
    allowed: list[str] = field(default_factory=list)     # failed, but in the known baseline
    flaky: list[str] = field(default_factory=list)       # failed in the full run, passed alone
    real: list[str] = field(default_factory=list)        # failed again alone: the regression is red
    mode: str = "full"                                   # full | staged | selective, as it actually ran
    stopped: str = ""                                    # "selected": a staged run stopped red after its first phase
    phases: list[tuple[str, int, float]] = field(default_factory=list)   # (label, suites, seconds)
    selection: list[str] = field(default_factory=list)  # bt_regress_select's description, when one was made

    @property
    def ok(self) -> bool:
        return not self.real

    def summary(self) -> str:
        """The line that goes to the release log: `291 files, only the 4 baseline failures` or what failed."""
        text = f"{len(self.lines)} files"
        if self.real:
            text = f"{text}, {len(self.real)} real failure(s): {', '.join(self.real)}"
        else:
            extra = f" + {', '.join(self.flaky)} (load flake, passes alone)" if self.flaky else ""
            if self.allowed:
                text = f"{text}, only baseline failures ({', '.join(self.allowed)}){extra}"
            else:
                text = f"{text}, no failures{extra}"
        return text + self.timing()

    def timing(self) -> str:
        """` [selected 25 in 2m10s, then 275 in 24m02s]`; empty for a plain full run."""
        if self.mode == "full" or not self.phases:
            return ""
        parts = [f"{label} {count} in {clock(seconds)}" for label, count, seconds in self.phases]
        tail = "; stopped at the selected suites" if self.stopped else ""
        return f" [{self.mode}: {', then '.join(parts)}{tail}]"


def clock(seconds: float) -> str:
    return f"{int(seconds) // 60}m{int(seconds) % 60:02d}s"


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
    started = time.monotonic()
    result, rerun_lines = _execute(Path(worktree), Path(scratch), only, workers, allowed, suite)
    result.phases = [("all", len(result.lines), time.monotonic() - started)]
    if out is not None:
        write(out, result, rerun_lines)
    return result


def write(out: Path, result: Result, rerun_lines: list[str]) -> None:
    Path(out).write_text("\n".join(result.lines) + "\n"
                         + "".join(f"# rerun alone: {line}\n" for line in rerun_lines)
                         + "".join(f"# {line}\n" for line in result.selection)
                         + f"# {result.summary()}\n", encoding="utf-8")


def _execute(worktree: Path, scratch: Path, only: Iterable[str] | None, workers: int, allowed: Iterable[str] | None,
             suite: Callable[..., str]) -> tuple[Result, list[str]]:
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

    return judge(lines, allowed_failures() if allowed is None else allowed, rerun), rerun_lines


def staged(worktree: Path, scratch: Path, out: Path | None = None, *, selection=None, mode: str = "staged",
           workers: int = 6, allowed: Iterable[str] | None = None, suite: Callable[..., str] = run_suite) -> Result:
    """The regression by `mode` over a `bt_regress_select.Selection`: `staged` runs the selected suites, stops when
    they are red, then runs the rest; `selective` runs the selected ones alone; `full` (or no selection) runs
    everything at once. A selection that is not trusted runs staged whatever the mode: its first phase (the always-run,
    changed and directly reached suites) first, then everything else."""
    worktree, scratch = Path(worktree), Path(scratch)
    described = selection.describe() if selection is not None else []
    if selection is not None and not selection.trusted:
        mode = "staged"                                    # everything runs before the merge; the selection goes first
    if mode == "full" or selection is None or not selection.first:
        started = time.monotonic()
        result, reruns = _execute(worktree, scratch, None, workers, allowed, suite)
        result.selection, result.phases = described, [("all", len(result.lines), time.monotonic() - started)]
        if out is not None:
            write(out, result, reruns)
        return result
    everything = [f.stem for f in suites(worktree)]
    head = set(selection.first)
    chosen = [name for name in everything if name in head]
    started = time.monotonic()
    first, reruns = _execute(worktree, scratch, chosen, workers, allowed, suite)
    first.mode, first.selection = mode, described
    first.phases = [("selected" if selection.trusted else "first", len(first.lines), time.monotonic() - started)]
    if not first.ok or mode == "selective":
        first.stopped = "selected" if not first.ok and mode == "staged" else ""
        if out is not None:
            write(out, first, reruns)
        return first
    started = time.monotonic()
    rest, more = _execute(worktree, scratch, [n for n in everything if n not in head], workers, allowed, suite)
    merged = Result(lines=sorted(first.lines + rest.lines), failed=first.failed + rest.failed,
                    allowed=first.allowed + rest.allowed, flaky=first.flaky + rest.flaky, real=first.real + rest.real,
                    mode=mode, selection=described,
                    phases=first.phases + [("the rest", len(rest.lines), time.monotonic() - started)])
    if out is not None:
        write(out, merged, reruns + more)
    return merged


def durations(results: Path) -> dict[str, int]:
    """Seconds per suite from an earlier results file (its first-run lines)."""
    found = {}
    try:
        for line in Path(results).read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) >= 3 and not line.startswith("#") and fields[2].isdigit():
                found[fields[0]] = int(fields[2])
    except OSError:
        pass
    return found


def estimate(seconds: dict[str, int], names: Iterable[str], workers: int = 6) -> int:
    """Wall-clock seconds of a run of `names` the way `run` schedules it: light suites on `workers` threads in name
    order, then the heavy ones one at a time. Suites without a timing count as 0."""
    names = sorted(names)
    free = [0] * workers
    for name in (n for n in names if not HEAVY.match(n)):
        free[free.index(min(free))] += seconds.get(name, 0)
    return max(free) + sum(seconds.get(n, 0) for n in names if HEAVY.match(n))


def dry_run(worktree: Path, base: str = "main", timings: Path | None = None) -> list[str]:
    """What a selected run would do: the selection, why, and (with an earlier results file) its time vs the full one."""
    import bt_regress_select
    selection = bt_regress_select.select(Path(worktree), base=base)
    lines = selection.describe()
    seconds = durations(timings) if timings else {}
    if seconds:
        everything = [f.stem for f in suites(Path(worktree))]
        label = "selected" if selection.trusted else "first phase (not trusted: everything runs)"
        lines.append(f"estimated from {timings}: {label} {clock(estimate(seconds, selection.first))} vs full "
                     f"{clock(estimate(seconds, everything))}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bt_regress", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("worktree", type=Path)
    parser.add_argument("scratch", type=Path, nargs="?")
    parser.add_argument("results", type=Path, nargs="?")
    parser.add_argument("only", type=Path, nargs="?", help="a file of suite names: run only those")
    parser.add_argument("--mode", choices=("full", "staged", "selective"), default="full")
    parser.add_argument("--base", default="main", help="what the selection diffs the worktree against")
    parser.add_argument("--dry-run", action="store_true", help="print the selection and run nothing")
    parser.add_argument("--timings", type=Path, help="an earlier results file, to estimate the times (--dry-run)")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.dry_run:
        print("\n".join(dry_run(args.worktree, args.base, args.timings)))
        return 0
    if args.scratch is None or args.results is None:
        parser.error("scratch and results are required unless --dry-run")
    if args.only is not None:
        result = run(args.worktree, args.scratch, args.results,
                     only=args.only.read_text(encoding="utf-8").split())
    elif args.mode == "full":
        result = run(args.worktree, args.scratch, args.results)
    else:
        import bt_regress_select
        selection = bt_regress_select.select(args.worktree, base=args.base)
        print("\n".join(selection.describe()))
        result = staged(args.worktree, args.scratch, args.results, selection=selection, mode=args.mode)
    print(result.summary())
    for name in result.real:
        print(f"FAILED {name} (log: {args.scratch / 'logs' / (name + '.rerun.log')})")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
