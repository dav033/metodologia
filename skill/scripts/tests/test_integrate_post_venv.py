"""The post-merge regression never borrows the live checkout's venv (D-240).

2026-10-30 18:56: a suite's `uv run` inside the post-merge worktree re-synced the project into the worktree's `.venv`,
a symlink to the live venv, so the live editable install pointed at the post-merge worktree; when that worktree was
removed (19:07) the live venv could not import `bt_durable` and the engine's next start would have failed.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_integrate_post as post
import test_integrate as base


class SeenVenv(base.Fake):
    def regress(self, worktree, scratch, out, selection=None, mode="full"):
        venv = Path(worktree) / ".venv"
        self.seen = (venv.exists() or venv.is_symlink(), venv.is_symlink())
        return super().regress(worktree, scratch, out, selection, mode)


class PostMergeVenv(unittest.TestCase):
    setUp, request, run_it = base.Integrate.setUp, base.Integrate.request, base.Integrate.run_it    # its fixtures, not its tests

    def test_the_post_merge_worktree_does_not_link_the_live_venv(self):
        live_venv = self.live / ".venv" / "lib"
        live_venv.mkdir(parents=True)
        (live_venv / "marker").write_text("live", encoding="utf-8")
        merged = self.run_it(base.Fake(self), regression="selective", keep_worktree=True)
        fake = SeenVenv(self)
        self.assertEqual(post.post_merge(self.request(), merged.merge, fake, say=lambda text: None), 0)
        self.assertEqual(fake.seen, (False, False))         # bt_regress.venv creates the worktree's own on demand
        self.assertEqual((live_venv / "marker").read_text(encoding="utf-8"), "live")


if __name__ == "__main__":
    unittest.main()
