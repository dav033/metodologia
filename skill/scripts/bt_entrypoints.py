"""Console-script targets for the legacy scripts that run at import time (no `main()` of their own).

The installed commands and the checkout scripts execute the same file: `runpy` runs the module as `__main__`,
so `globalusage.py` and `install_rtk.py` keep one implementation and need no wrapper copy of their logic.
"""
from __future__ import annotations

import runpy


def globalusage() -> None:
    runpy.run_module("globalusage", run_name="__main__")


def install_rtk() -> None:
    runpy.run_module("install_rtk", run_name="__main__")
