"""The combined `discover -s tests` run collects exactly the legacy suite plus the migration tests (T6)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEGACY = REPO / "skill" / "scripts" / "tests"


def ids(suite) -> list[str]:
    """Every collected test id, duplicates kept (inherited test bodies appear once per concrete class)."""
    found = []
    for item in suite:
        found.extend(ids(item) if isinstance(item, unittest.TestSuite) else [item.id()])
    return sorted(found)


class CollectionIdentityTests(unittest.TestCase):
    def test_every_legacy_test_id_is_collected_through_the_tests_root(self) -> None:
        loader = unittest.TestLoader()
        direct = ids(loader.discover(str(LEGACY), pattern="test*.py", top_level_dir=str(LEGACY)))
        import importlib.util
        spec = importlib.util.spec_from_file_location("legacy_collection", REPO / "tests" / "test_legacy_collection.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        through_root = ids(module.load_tests(loader, unittest.TestSuite(), "test*.py"))
        self.assertEqual(direct, through_root)
        self.assertGreaterEqual(len(direct), 579)

    def test_no_legacy_test_module_lost_tests_against_the_recorded_baseline(self) -> None:
        """tests/migration/legacy-test-counts.json holds tests per module at the 2026-10-13 baseline. A module may
        grow; a module that vanished or shrank means a test was dropped or renamed and needs an explicit decision
        (update the file in the same change, with the reason)."""
        recorded = json.loads((Path(__file__).parent / "legacy-test-counts.json").read_text())
        counts: dict[str, int] = {}
        for test_id in ids(unittest.TestLoader().discover(str(LEGACY), pattern="test*.py", top_level_dir=str(LEGACY))):
            module = test_id.split(".")[0]
            counts[module] = counts.get(module, 0) + 1
        lost = {m: (n, counts.get(m, 0)) for m, n in recorded.items() if counts.get(m, 0) < n}
        self.assertEqual(lost, {}, "tests disappeared from these modules (recorded, now)")


if __name__ == "__main__":
    unittest.main()
