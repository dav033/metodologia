"""State machine (SC-AC09): the tables are closed, illegal transitions are refused and roll back, and randomised
interleavings of every operation never break the invariants."""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep, task

import bt_scheduler_core as sc
from bt_scheduler_core import states as S
from bt_scheduler_core.resources import conflict
from bt_scheduler_core.transitions import set_attempt, set_task

T, A = S.TaskState, S.AttemptState


class Tables(unittest.TestCase):
    def test_every_state_has_a_row_and_targets_are_states(self):
        self.assertEqual(set(S.TASK_TRANSITIONS), set(T))
        self.assertEqual(set(S.ATTEMPT_TRANSITIONS), set(A))
        for table in (S.TASK_TRANSITIONS, S.ATTEMPT_TRANSITIONS):
            for targets in table.values():
                self.assertTrue(targets <= set(table))

    def test_terminal_states_have_no_exit(self):
        self.assertEqual(S.TASK_TRANSITIONS[T.COMPLETED], frozenset())
        self.assertEqual(S.TASK_TRANSITIONS[T.CANCELLED], frozenset())
        for state in S.ATTEMPT_TERMINAL:
            self.assertEqual(S.ATTEMPT_TRANSITIONS[state], frozenset())

    def test_completed_is_only_reachable_from_active(self):
        sources = {s for s, targets in S.TASK_TRANSITIONS.items() if T.COMPLETED in targets}
        self.assertEqual(sources, {T.ACTIVE})  # in particular never pending -> completed
        self.assertEqual({s for s, t in S.ATTEMPT_TRANSITIONS.items() if A.ACCEPTED in t}, {A.VERIFYING})

    def test_every_state_is_reachable_from_the_start(self):
        for table, start in ((S.TASK_TRANSITIONS, T.PENDING), (S.ATTEMPT_TRANSITIONS, A.RESERVED)):
            seen, todo = {start}, [start]
            while todo:
                for nxt in table[todo.pop()]:
                    if nxt not in seen:
                        seen.add(nxt)
                        todo.append(nxt)
            self.assertEqual(seen, set(table))

    def test_executor_events_never_lead_to_acceptance(self):
        self.assertNotIn(A.ACCEPTED, S.EVENT_TARGETS.values())
        self.assertNotIn(A.REJECTED, S.EVENT_TARGETS.values())


class Guards(unittest.TestCase):
    def test_illegal_transitions_are_refused_and_the_transaction_rolls_back(self):
        h = Harness([task("T1")])
        before = h.core.repository.audit_log()
        with self.assertRaises(sc.SchedulerError) as cm:
            h.core.write(lambda c: set_task(c, "T1", T.COMPLETED))  # ready -> completed: never
        self.assertEqual(cm.exception.code, "ILLEGAL_TRANSITION")
        self.assertEqual(h.state("T1"), "ready")
        self.assertEqual(h.core.repository.audit_log(), before)

    def test_an_attempt_cannot_skip_verification(self):
        h = Harness([task("T1")])
        h.core.step()
        with self.assertRaises(sc.SchedulerError):
            h.core.write(lambda c: set_attempt(c, h.attempt("T1"), A.ACCEPTED))
        self.assertEqual(h.state("T1"), "active")

    def test_pending_cannot_jump_to_completed(self):
        h = Harness([task("T1"), task("T2", ["T1"])])
        with self.assertRaises(sc.SchedulerError):
            h.core.write(lambda c: set_task(c, "T2", T.COMPLETED))
        self.assertEqual(h.state("T2"), "pending")

    def test_a_task_cannot_be_reopened_once_completed_or_cancelled(self):
        h = Harness([task("T1")])
        h.core.step()
        h.finish_and_accept("T1")
        with self.assertRaises(sc.SchedulerError):
            h.core.write(lambda c: set_task(c, "T1", T.READY))


# ---------------------------------------------------------------------------------------------------- invariants
def invariants(h: Harness, parallel: int, history: dict) -> None:
    state = h.core.read(lambda c: c.state.to_dict())
    plan = h.plan
    tasks, attempts, holds = state["tasks"], state["attempts"], state["holds"]
    live = {a for a, rec in attempts.items() if rec["state"] not in ("accepted", "failed", "rejected", "cancelled")}
    # one writer: at most one live attempt per task; ACTIVE <=> exactly one live attempt
    for tid, rec in tasks.items():
        mine = [a for a in rec["attempts"] if a in live]
        assert len(mine) <= 1, (tid, mine)
        assert (rec["state"] == "active") == (len(mine) == 1), (tid, rec["state"], mine)
    # reservations belong to live attempts exactly, never to closed ones
    assert set(holds) == live, (set(holds), live)
    assert sum(1 for r in tasks.values() if r["state"] == "active") <= parallel
    # no two live attempts hold conflicting claims
    spec = {t.id: t for t in plan.tasks}
    held = sorted(live)
    for i, a in enumerate(held):
        for b in held[i + 1:]:
            assert not conflict(holds[a], holds[b]), (a, b)
    # completed only through an accepted, independently verified attempt, after completed prerequisites
    for tid, rec in tasks.items():
        if rec["state"] == "completed":
            last = attempts[rec["attempts"][-1]]
            assert last["state"] == "accepted" and last["evidence"] and last["verifier"] and last["verifier"] != last["executor"]
            assert all(tasks[d]["state"] == "completed" for d in spec[tid].after)
        if rec["state"] in ("active", "ready", "completed") or rec["state"] == "recovering":
            assert all(tasks[d]["state"] == "completed" for d in spec[tid].after), (tid, rec["state"])
    # terminal tasks never move again
    for tid, rec in tasks.items():
        if history.get(tid) in ("completed", "cancelled"):
            assert rec["state"] == history[tid], (tid, history[tid], rec["state"])
        history[tid] = rec["state"]
    # fencing tokens strictly increase with attempt creation
    ordered = sorted(attempts, key=lambda a: int(a.split("-")[1]))
    tokens = [attempts[a]["token"] for a in ordered]
    assert tokens == sorted(set(tokens)), tokens
    # the audit trail is contiguous
    seqs = [e.seq for e in h.core.audit_log()]
    assert seqs == list(range(1, len(seqs) + 1)), "audit gap"


TASKS = [indep("T1"), indep("T2", ["T1"]), indep("T3"), indep("T4", ["T2", "T3"]), indep("T5"),
         task("T6", ["T1"], repo="shared", paths=["lib/**"], resources=["db"]),
         task("T7", repo="shared", paths=["lib/x"], resources=["db"]), task("T8")]
KINDS = ["execution_started", "execution_finished", "execution_failed", "execution_cancelled", "heartbeat"]


class Fuzz(unittest.TestCase):
    def run_seed(self, seed: int, steps: int = 100):
        rng = random.Random(seed)
        parallel = rng.choice([1, 2, 3])
        h = Harness(TASKS, parallel=parallel, max_attempts=rng.choice([1, 2, 3]))
        history: dict = {}
        for _ in range(steps):
            op = rng.random()
            tid = rng.choice([t["id"] for t in TASKS])
            attempts = h.core.read(lambda c: list(c.state.attempts))
            att = rng.choice(attempts) if attempts else "att-9999"
            if op < 0.25:
                h.core.step()
            elif op < 0.5 and attempts:
                owner = h.core.read(lambda c, a=att: c.state.attempts[a].task_id)
                h.send(owner, rng.choice(KINDS), att, token=rng.choice(["auto", "auto", None, 999]))
            elif op < 0.65 and attempts:
                owner = h.core.read(lambda c, a=att: c.state.attempts[a].task_id)
                h.verdict(owner, rng.random() < 0.7, att, verifier=rng.choice(["validator", "validator", "local", ""]),
                          evidence=rng.choice(["ok", "ok", ""]))
            elif op < 0.7:
                h.core.ingest({"event_id": "x", "kind": "bogus"})
            elif op < 0.78:
                h.clock.advance(rng.choice([1, 400, 4000]))
            elif op < 0.84:
                h.crash()
            elif op < 0.88:
                h.core.claim(sc.Assignment(tid, "manual"))
            elif op < 0.91:
                try:
                    h.core.reopen(tid, "tester")
                except sc.SchedulerError:
                    pass
            elif op < 0.93:
                (h.core.pause if rng.random() < 0.5 else h.core.resume)("tester")
            elif op < 0.94 and rng.random() < 0.3:
                h.core.cancel("tester")
            invariants(h, parallel, history)
        return h

    def test_invariants_hold_under_random_interleavings(self):
        for seed in range(50):
            with self.subTest(seed=seed):
                try:
                    self.run_seed(seed)
                except AssertionError as exc:
                    self.fail(f"seed {seed}: {exc!r}")

    def test_the_fuzzer_can_actually_complete_work(self):
        """Guard against a vacuous fuzzer: some seeds must reach completed tasks."""
        done = 0
        for seed in range(25):
            h = self.run_seed(seed)
            done += sum(1 for s in h.states().values() if s == "completed")
        self.assertGreater(done, 0)


if __name__ == "__main__":
    unittest.main()
