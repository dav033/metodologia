from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_composition.store import Store


class StoreMigrationTests(unittest.TestCase):
    def make_v1_database(self, path: Path) -> None:
        connection = sqlite3.connect(path)
        connection.executescript("""
            CREATE TABLE versions(
              plan_id TEXT NOT NULL, subplan_id TEXT NOT NULL, version INTEGER NOT NULL,
              body TEXT NOT NULL, request_sha256 TEXT NOT NULL,
              PRIMARY KEY(plan_id, subplan_id, version));
            CREATE TABLE candidates(
              id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, request_sha256 TEXT NOT NULL UNIQUE,
              body TEXT NOT NULL);
            INSERT INTO candidates VALUES('C1','P','request','{}');
            PRAGMA user_version=1;
        """)
        connection.close()

    def test_failed_migration_rolls_back_rename_and_recovers_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            self.make_v1_database(path)
            with patch.object(Store, "_copy_legacy_candidates", side_effect=RuntimeError("crash after rename")):
                with self.assertRaisesRegex(RuntimeError, "crash after rename"):
                    Store(path)
            connection = sqlite3.connect(path)
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("candidates", names)
            self.assertNotIn("candidates_v1", names)
            self.assertEqual(connection.execute("SELECT id FROM candidates").fetchone()[0], "C1")
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
            connection.close()

            store = Store(path)
            self.assertEqual(store.connection.execute("PRAGMA user_version").fetchone()[0], Store.SCHEMA_VERSION)
            self.assertEqual(store.connection.execute("SELECT id FROM candidates").fetchone()[0], "C1")
            store.close()

    def test_unsupported_schema_version_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE sentinel(value TEXT)")
            connection.execute("INSERT INTO sentinel VALUES('kept')")
            connection.execute("PRAGMA user_version=99")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SCHEMA_VERSION"):
                Store(path)
            connection = sqlite3.connect(path)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 99)
            self.assertEqual(connection.execute("SELECT value FROM sentinel").fetchone()[0], "kept")
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(names, {"sentinel"})
            connection.close()


if __name__ == "__main__":
    unittest.main()
