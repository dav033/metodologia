"""Shared, memoized wheel build + venv for the migration tests (built once per test process)."""
from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Installed:
    work: Path
    wheel: Path
    site: Path
    python: Path
    sdist: Path
    sources: Path


_cache: Installed | None = None


def get() -> Installed:
    """Build the wheel from a temporary copy of the sources and install it by extraction into a fresh venv.
    Raises unittest.SkipTest when setuptools/venv are unavailable (a skip, never a pass)."""
    global _cache
    if _cache is not None:
        return _cache
    try:
        import setuptools  # noqa: F401
        import venv  # noqa: F401
    except ImportError as error:
        raise unittest.SkipTest(f"packaging tools unavailable: {error}") from None
    work = Path(tempfile.mkdtemp(prefix="package-install-"))
    atexit.register(shutil.rmtree, work, ignore_errors=True)
    shutil.copy2(REPO / "pyproject.toml", work / "pyproject.toml")
    shutil.copytree(REPO / "skill", work / "skill",
                    ignore=shutil.ignore_patterns("__pycache__", "tests", "*.egg-info", "*.pyc"))
    (work / "dist").mkdir()
    build = subprocess.run([sys.executable, "-I", "-c",
                            "from setuptools import build_meta; print(build_meta.build_wheel('dist'))"],
                           cwd=work, capture_output=True, text=True, timeout=300)
    if build.returncode != 0:
        raise AssertionError(f"wheel build failed:\n{build.stdout[-2000:]}\n{build.stderr[-2000:]}")
    wheel = work / "dist" / build.stdout.strip().splitlines()[-1]
    made = subprocess.run([sys.executable, "-I", "-c",
                           "from setuptools import build_meta; print(build_meta.build_sdist('dist'))"],
                          cwd=work, capture_output=True, text=True, timeout=300)
    if made.returncode != 0:
        raise AssertionError(f"sdist build failed:\n{made.stdout[-2000:]}\n{made.stderr[-2000:]}")
    sdist = work / "dist" / made.stdout.strip().splitlines()[-1]
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(work / "venv")], check=True)
    python = work / "venv" / "bin" / "python"
    site = Path(subprocess.run([str(python), "-c", "import sysconfig;print(sysconfig.get_paths()['purelib'])"],
                               check=True, capture_output=True, text=True).stdout.strip())
    with zipfile.ZipFile(wheel) as archive:  # a pure-Python wheel installs by extraction
        archive.extractall(site)
    _cache = Installed(work, wheel, site, python, sdist, work)
    return _cache
