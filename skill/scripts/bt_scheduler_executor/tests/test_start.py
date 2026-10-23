"""T3: validation before side effects; idempotent start, duplicate/conflict/queue_full answers; no second writer."""
from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import model as m
from support import World, order


class Start(unittest.TestCase):
    def quiet(self, **kw):
        """An executor that accepts but never runs anything (no supervisor loop)."""
        return World(self, autostart=False, **kw)

    def no_side_effects(self, w, attempt_id="att-0001"):
        self.assertFalse(list((w.root / "ws").glob("worktrees/*")) if (w.root / "ws").exists() else [])
        self.assertFalse(list(w.root.glob("attempts/*")))
        self.assertEqual(support.git(w.repo, "worktree", "list").count("\n"), 0)
        self.assertEqual(support.git(w.repo, "branch", "--list", "m3/*"), "")

    def test_an_accepted_order_is_queued_and_nothing_starts_without_the_loop(self):
        w = self.quiet()
        r = w.x.start(order(1))
        self.assertEqual((r.status, r.attempt_id), ("accepted", "att-0001"))
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.QUEUED)
        self.assertEqual(w.x.query("att-0001").state, "queued")

    def test_the_same_order_twice_is_one_attempt(self):
        w = self.quiet()
        self.assertEqual(w.x.start(order(1)).status, "accepted")
        self.assertEqual(w.x.start(order(1)).status, "duplicate")
        self.assertEqual(w.x.start(order(1)).status, "duplicate")
        self.assertEqual(len(w.x.ledger.all_ids()), 1)
        self.assertEqual(w.resolver.calls, 1)           # a replay is answered from the record, not re-evaluated

    def test_a_replay_is_answered_even_if_the_route_would_no_longer_resolve(self):
        w = self.quiet()
        w.x.start(order(1))
        w.resolver.fail = ex.ExecutorError("ROUTE_UNRESOLVABLE", "stale now")
        self.assertEqual(w.x.start(order(1)).status, "duplicate")

    def test_a_legacy_order_without_plan_hash_replays_without_a_second_writer(self):
        w = self.quiet()
        original = order(1)
        self.assertEqual(w.x.start(original).status, "accepted")
        stored = w.x.ledger.get(original.attempt_id)["request"]
        stored.pop("plan_sha256")
        with sqlite3.connect(w.x.ledger.path) as connection:
            connection.execute("UPDATE attempts SET request=? WHERE attempt_id=?",
                               (json.dumps(stored, sort_keys=True, separators=(",", ":")), original.attempt_id))
        replay = w.x.start(replace(original, plan_sha256="a" * 64))
        self.assertEqual((replay.status, replay.attempt_id), ("duplicate", original.attempt_id))
        self.assertEqual(w.resolver.calls, 1)
        self.assertEqual(w.x.ledger.all_ids(), [original.attempt_id])

    def test_the_same_key_with_a_different_order_is_rejected(self):
        w = self.quiet()
        w.x.start(order(1))
        r = w.x.start(order(1, scenario="crash"))
        self.assertEqual((r.status, r.code), ("rejected", "KEY_CONFLICT"))

    def test_the_same_attempt_id_with_another_key_is_rejected_and_does_not_start_anything(self):
        w = self.quiet()
        w.x.start(order(1))
        r = w.x.start(order(1, key="another"))
        self.assertEqual((r.status, r.code), ("rejected", "KEY_CONFLICT"))
        self.assertEqual(len(w.x.ledger.all_ids()), 1)

    def test_another_token_for_the_same_attempt_is_a_conflict_not_a_new_run(self):
        w = self.quiet()
        w.x.start(order(1, token=1))
        r = w.x.start(order(1, token=2))
        self.assertEqual((r.status, r.code), ("rejected", "KEY_CONFLICT"))

    def test_an_unresolvable_route_is_rejected_before_any_side_effect_and_never_defaulted(self):
        w = self.quiet()
        r = w.x.start(order(1, executor="local"))
        self.assertEqual((r.status, r.code), ("rejected", "ROUTE_UNRESOLVABLE"))
        self.no_side_effects(w)
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.REJECTED)
        self.assertEqual(w.driver.prepared, [])

    def test_the_rejection_is_stable_on_replay(self):
        w = self.quiet()
        first = w.x.start(order(1, executor="nope"))
        second = w.x.start(order(1, executor="nope"))
        self.assertEqual((first.status, first.code), (second.status, second.code))
        self.assertEqual(w.resolver.calls, 1)

    def test_invalid_route_policy_denial_unknown_repository_and_bad_base_are_all_refused_up_front(self):
        for err in ("ROUTE_INVALID", "POLICY_DENIED"):
            w = self.quiet()
            w.resolver.fail = ex.ExecutorError(err, "no")
            r = w.x.start(order(1))
            self.assertEqual((r.status, r.code), ("rejected", err))
            self.no_side_effects(w)
        w = self.quiet()
        r = w.x.start(order(1, repo="nope"))
        self.assertEqual((r.status, r.code), ("rejected", "REPOSITORY_UNKNOWN"))
        self.no_side_effects(w)
        r = w.x.start(order(2, base="no-such-ref"))
        self.assertEqual((r.status, r.code), ("rejected", "BASE_UNRESOLVED"))
        self.no_side_effects(w)

    def test_a_repository_without_commits_gets_an_empty_root_commit_instead_of_blocking_the_first_task(self):
        import subprocess
        import tempfile

        fresh = Path(tempfile.mkdtemp(prefix="bt-fresh-")) / "new"
        fresh.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=fresh, check=True)
        workspaces = ex.GitWorkspaces(Path(tempfile.mkdtemp(prefix="bt-ws-")), {"fresh": fresh})
        self.assertRegex(workspaces.check(order(1, repo="fresh")), r"^[0-9a-f]{40,64}$")
        self.assertEqual(support.git(fresh, "status", "--porcelain"), "")

    def test_a_base_that_looks_like_an_option_is_refused(self):
        w = self.quiet()
        r = w.x.start(order(1, base="--upload-pack=evil"))
        self.assertEqual((r.status, r.code), ("rejected", "BASE_UNRESOLVED"))

    def test_a_port_that_raises_something_else_is_a_port_error_not_a_crash(self):
        w = self.quiet()
        w.resolver.fail = KeyError("boom")
        r = w.x.start(order(1))
        self.assertEqual((r.status, r.code), ("rejected", "PORT_ERROR"))

    def test_a_malformed_order_is_rejected_without_a_record(self):
        w = self.quiet()
        r = w.x.start(order(1, token=None))   # type: ignore[arg-type]
        self.assertEqual((r.status, r.code), ("rejected", "ORDER_INVALID"))
        self.assertEqual(w.x.start("not an order").code, "ORDER_INVALID")   # type: ignore[arg-type]
        self.assertEqual(w.x.ledger.all_ids(), [])

    def test_an_order_of_another_run_is_foreign(self):
        w = self.quiet()
        w.x.start(order(1))
        self.assertEqual(w.x.start(order(2, plan="REQ-OTHER")).code, "FOREIGN_RUN")
        self.assertEqual(w.x.start(order(3, revision=2)).code, "FOREIGN_RUN")
        self.assertEqual(w.x.ledger.all_ids(), ["att-0001"])

    def test_the_queue_is_bounded_and_the_refusal_is_a_stable_record(self):
        w = self.quiet(config=ex.Config(max_queued=2))
        self.assertEqual([w.x.start(order(n)).status for n in (1, 2)], ["accepted", "accepted"])
        r = w.x.start(order(3))
        self.assertEqual((r.status, r.code), ("rejected", "QUEUE_FULL"))
        self.assertEqual(w.x.start(order(3)).code, "QUEUE_FULL")
        self.assertEqual(w.x.ledger.count((m.QUEUED,)), 2)

    def test_start_is_fast_it_only_records(self):
        import time
        w = self.quiet()
        t0 = time.monotonic()
        for n in range(1, 30):
            w.x.start(order(n))
        self.assertLess(time.monotonic() - t0, 10)
        self.assertEqual(w.x.ledger.count((m.QUEUED,)), 29)

    def test_artifacts_of_an_accepted_order_hold_the_order_and_the_route_but_no_secret(self):
        w = self.quiet()
        w.x.start(order(1))
        adir = next(w.root.glob("attempts/*"))
        text = (adir / "order.json").read_text() + (adir / "route.json").read_text()
        self.assertIn("att-0001", text)
        self.assertNotIn("secret-for", text)

    def test_unknown_ids_answer_not_found(self):
        w = self.quiet()
        self.assertEqual(w.x.query("att-9999").state, "not_found")
        self.assertEqual(w.x.cancel("att-9999", 1, "k").code, "UNKNOWN_ATTEMPT")

    def test_the_same_order_delivered_concurrently_starts_one_process_in_the_end(self):
        import threading
        w = World(self)
        out = []
        threads = [threading.Thread(target=lambda: out.append(w.x.start(order(1, "ok")).status)) for _ in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(out.count("accepted"), 1, out)
        d = w.finish("att-0001")
        self.assertEqual(d["state"], m.FINISHED)
        self.assertEqual(len(w.driver.prepared), 1)
        self.assertEqual(len(list((w.root / "ws" / "worktrees").glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
