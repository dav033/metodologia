"""Every top-level module of skill/scripts travels in the distribution, and the installed one finds them all (D-277).

`pyproject.toml` lists the modules by hand in `[tool.setuptools] py-modules`; the editable install maps only what is
listed, so a module left out is invisible to anything that does not run with skill/scripts on sys.path: on 2026-10-31
the engine and the CLI failed with `No module named 'bt_stage_confirmations'`, five modules having drifted out while
the regression (and with it `test_package_modules`) was off (D-261). Two checks share this code: `drift` (the source
tree against the list: the test and `bt_integrate.preflight`) and `install_problems` (an interpreter's installed
distribution against the list: `bt_integrate` after it refreshes the live venv). Stdlib only."""
from __future__ import annotations

import json
import subprocess
import tomllib
from collections.abc import Callable, Iterable
from pathlib import Path

SCRIPTS = "skill/scripts"
NOT_MODULES = {"ops_check": "operator script run by path", "ops_matrix_check": "operator script run by path",
               "setup_bt_scheduler_laya": "one-off setup script run by path"}

# run by the checked interpreter in isolated mode (-I: no cwd, no PYTHONPATH), so only its installed finders answer;
# find_spec of a top-level name runs no module code
_PROBE = ("import importlib.util, json, sys\n"
          "out = {}\n"
          "for name in json.loads(sys.argv[1]):\n"
          "    spec = importlib.util.find_spec(name)\n"
          "    out[name] = None if spec is None else (spec.origin if spec.origin not in (None, 'namespace') else\n"
          "        next(iter(spec.submodule_search_locations or []), ''))\n"
          "print(json.dumps(out))\n")


def setuptools_table(pyproject_text: str) -> dict:
    return tomllib.loads(pyproject_text).get("tool", {}).get("setuptools", {})


def drift(script_files: Iterable[str], pyproject_text: str) -> tuple[list[str], list[str]]:
    """(unlisted, gone): top-level modules of skill/scripts missing from `py-modules`, and listed ones that no longer
    exist. `script_files` are the file names directly in skill/scripts (any suffix; only `.py` count)."""
    listed = set(setuptools_table(pyproject_text).get("py-modules", []))
    real = {Path(name).stem for name in script_files if name.endswith(".py") and "/" not in name}
    return sorted(real - listed - set(NOT_MODULES)), sorted(listed - real)


def drift_message(unlisted: list[str], gone: list[str]) -> str:
    parts = ([f"not listed in pyproject.toml py-modules (the installed engine cannot import them): {', '.join(unlisted)}"]
             if unlisted else []) + ([f"listed in py-modules but gone: {', '.join(gone)}"] if gone else [])
    return "; ".join(parts)


def distribution_names(pyproject_text: str) -> list[str]:
    """The top-level import names the distribution installs: every py-module and every top-level package."""
    table = setuptools_table(pyproject_text)
    packages = [p for p in table.get("packages", []) if "." not in p]
    return list(table.get("py-modules", [])) + packages


def install_problems(python: Path, root: Path, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                     timeout: float = 60.0) -> list[str]:
    """What `python` (a venv's interpreter) cannot import from the distribution `root/pyproject.toml` lists: a name it
    does not find, or finds outside `root` (an editable install pointing at another checkout, D-240). [] when all
    resolve under `root`."""
    root = Path(root).resolve()
    names = distribution_names((root / "pyproject.toml").read_text(encoding="utf-8"))
    try:
        done = runner([str(python), "-I", "-B", "-c", _PROBE, json.dumps(names)], cwd=str(root), capture_output=True,
                      text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return [f"{python} could not run: {error}"]
    if done.returncode:
        return [f"{python} failed ({done.returncode}): {(done.stderr or done.stdout).strip()[-300:]}"]
    try:
        found = json.loads(done.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return [f"{python} answered no module list: {done.stdout.strip()[-200:]}"]
    missing = [name for name in names if not found.get(name)]
    elsewhere = [f"{name} ({found[name]})" for name in names
                 if found.get(name) and not _under(Path(found[name]), root)]
    return ([f"not importable: {', '.join(missing)}"] if missing else []) + \
           ([f"imported from outside {root}: {', '.join(elsewhere[:5])}"] if elsewhere else [])


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False
