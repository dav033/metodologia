"""Bounded cold-start scheduling (REQ-007 T8, R8): an under-sampled eligible provider is tried, within limits."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import datetime as dt  # noqa: E402
from unittest.mock import patch  # noqa: E402

import bt_agents  # noqa: E402
import bt_events  # noqa: E402
from test_agents import AgentTests  # noqa: E402


class ColdStartTests(AgentTests):
    def setUp(self):
        super().setUp()
        self.now = 1_800_000_000.0
        self.rows = []
        for patcher in (patch.object(bt_agents.time, "time", return_value=self.now),
                        patch.object(bt_events, "read_all", side_effect=lambda: self.rows),
                        patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def populate_rates(self, profile, agent, model, done, failed, kind="implement"):
        stamp = dt.datetime.fromtimestamp(self.now - 60, tz=dt.timezone.utc).isoformat()
        for i in range(done + failed):
            self.rows.append({"profile": profile, "agent": agent, "model": model, "kind": kind,
                              "result": "done" if i < done else "failed", "seconds": 10, "ts": stamp})

    def _all_clis(self):
        return patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")

    def order(self, kind="implement", tier=0, **kw):
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], tier, kind, **kw)
        return [r["agent"] for r in routes]

    def test_unseen_provider_beats_a_strong_incumbent_until_it_has_min_samples(self):
        self.populate_rates("claude", "claude", "haiku", 5, 0)       # incumbent: 100% over 5
        self.assertEqual(self.order(), ["codex", "claude"])           # codex has no history: it explores

    def test_exploration_is_bounded_by_the_sample_count(self):
        self.populate_rates("claude", "claude", "haiku", 5, 0)
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 4, 0)   # 4 judged attempts: still exploring
        self.assertEqual(self.order()[0], "codex")
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 0, 2)   # now 6 judged, 4/6 = 67%: judged, not explored
        self.assertEqual(self.order()[0], "claude")

    def test_a_proven_bad_provider_is_not_explored_again(self):
        self.populate_rates("claude", "claude", "haiku", 5, 0)
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 0, 5)   # 0% over 5
        self.assertEqual(self.order()[0], "claude")

    def test_exploration_never_overrides_avoidance_cooldown_or_audit_order(self):
        self.populate_rates("claude", "claude", "haiku", 5, 0)
        self.assertEqual(self.order(avoid_providers={"codex"})[0], "claude")          # builder-failure avoidance wins
        bt_agents.quota_mark("codex-named", "codex", self.now + 500)
        self.assertEqual(self.order(), ["claude"])                                       # cooling is excluded
        # audits keep the budget order: Claude before Codex regardless of cold start
        self.assertEqual(self.order("audit", 1)[0], "claude")

    def test_work_only_account_is_not_a_cold_start_candidate_for_personal_projects(self):
        import bt_profiles
        bt_profiles.add("claude-work2", "claude", {"CLAUDE_CONFIG_DIR": str(self.workdir)}, work_only=True)
        with self._all_clis():
            pool = bt_agents.pool_for("personal-project", ["claude-work2", "claude"])
        self.assertNotIn("claude-work2", pool)


if __name__ == "__main__":
    import unittest
    unittest.main()
