"""Collects the legacy suite in place so `python -m unittest discover -s tests` runs one complete suite (T6).

The files stay under skill/scripts/tests until their relocation is proven by a collected-test identity
comparison; moving them is a separate, reviewable step. Isolation is preserved: legacy discovery runs with its own
top-level directory so test_00_isolation still sets BITACORA_ROOT before any bt_* module is imported.
"""
from pathlib import Path

MINIMUM_LEGACY_TESTS = 591  # observed baseline (578) plus the D-013 regression; raise it, never lower it
LEGACY = Path(__file__).resolve().parents[1] / "skill" / "scripts" / "tests"


def load_tests(loader, standard_tests, pattern):
    suite = type(standard_tests)()
    legacy = loader.discover(str(LEGACY), pattern="test*.py", top_level_dir=str(LEGACY))
    if legacy.countTestCases() < MINIMUM_LEGACY_TESTS:  # a silent empty discovery must fail, not pass
        raise AssertionError(f"legacy discovery found {legacy.countTestCases()} tests, expected >= "
                             f"{MINIMUM_LEGACY_TESTS}")
    suite.addTests(legacy)
    return suite
