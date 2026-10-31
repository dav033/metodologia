"""Only the live bitácora may fall back to the live engine's database (~/.config/bitacora/durable.env, D-256).

Until 2026-10-31 any root without its own URL resolved it: a scratch root created by hand, and every bt_regress suite
(which drops BT_DURABLE_DATABASE_URL, so the per-user file was the next thing it read), reached the live PostgreSQL.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_core
from bt_durable import cli

FAKE = "postgresql://live:not-a-real-password@127.0.0.1:1/live_engine"


class LiveDatabaseFallback(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-live-db-"))
        self.env_file = self.tmp / "durable.env"
        self.env_file.write_text(f"BT_DURABLE_DATABASE_URL={FAKE}\n")
        self.state = self.tmp / "root" / ".state"
        for patcher in (patch.object(cli, "ENV_FILE", self.env_file), patch("bt_config.STATE", self.state),
                        patch.object(bt_core, "STATE", self.state),
                        patch.dict(os.environ, {"BT_DURABLE_DATABASE_URL": ""})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_a_scratch_root_gets_its_own_sqlite(self):
        with patch.object(bt_core, "ROOT", self.state.parent):
            url = cli.database_url()
        self.assertTrue(url.startswith("sqlite:///"), "a scratch root resolved the live engine's database")
        self.assertIn(str(self.state.resolve()), url)

    def test_the_live_root_keeps_the_per_user_file(self):
        with patch.object(bt_core, "ROOT", bt_core.LIVE_ROOT):
            self.assertEqual(cli.database_url(), FAKE)

    def test_the_variable_and_the_roots_config_still_win(self):
        with patch.object(bt_core, "ROOT", self.state.parent), \
                patch.dict(os.environ, {"BT_DURABLE_DATABASE_URL": "sqlite:///lab.sqlite3"}):
            self.assertEqual(cli.database_url(), "sqlite:///lab.sqlite3")


if __name__ == "__main__":
    unittest.main()
