import json
import shutil
import subprocess
import unittest
from pathlib import Path

import bt_page_flow as pf

ASSETS = Path(__file__).resolve().parents[2] / "assets"
CORE = ASSETS / "flow-core.js"

NODE_TEST = r"""
const C = require(process.argv[1]);
const assert = require('assert');
const ev = (seq, from, to, kind, extra) => Object.assign({v: 1, seq, ord: String(100 + seq), run: 'p/REQ-1', from, to, kind,
  task: 'T4', attempt: 'A-1', at_epoch: 100 + seq, summary: kind, data: {}}, extra || {});

// categories: what a reader sees, including failures hidden inside ordinary kinds
assert.strictEqual(C.kindClass(ev(3, 'M6', 'M1', 'verdict', {data: {status: 'FAIL'}})), 'k-bad');
assert.strictEqual(C.kindClass(ev(3, 'M6', 'M1', 'verdict', {data: {status: 'PASS'}})), 'k-verify');
assert.strictEqual(C.kindClass(ev(3, 'M5', 'M1', 'recommendation', {data: {action: 'block'}})), 'k-bad');
assert.strictEqual(C.kindClass(ev(3, 'M1', 'M1', 'unknown')), 'k-bad');
assert.strictEqual(C.label('dispatch_ack'), 'acepta la orden');
assert.strictEqual(C.label('brand_new'), 'brand_new');
assert.strictEqual(C.taskState('verifying'), 'running');
assert.strictEqual(C.taskState('rejected'), 'retry');

// filters: task, category, node, edge
const events = [ev(1, 'M2', 'M1', 'assignment'), ev(2, 'M1', 'M3', 'start_order', {task: 'T5'}),
  ev(3, 'M6', 'M1', 'verdict', {data: {status: 'FAIL'}}), ev(4, 'M1', 'M1', 'task_state')];
const pick = f => events.filter(e => C.matches(e, f)).map(e => e.seq);
assert.deepStrictEqual(pick({task: 'T4'}), [1, 3, 4]);
assert.deepStrictEqual(pick({cats: {bad: true}}), [3]);
assert.deepStrictEqual(pick({cats: {bad: false}}), [1, 2, 3, 4]);       // an unticked chip filters nothing
assert.deepStrictEqual(pick({node: 'M3'}), [2]);
assert.deepStrictEqual(pick({edge: 'M6>M1'}), [3]);

// the map: loops apart from edges; digests only add when given
const t = C.tally(events, [{stream: 50, incidents: 7, at_epoch: 200}]);
assert.strictEqual(t.edges['M2>M1'].count, 1);
assert.strictEqual(t.loops.M1, 1);
assert.strictEqual(t.edges['M3>M4'].count, 50);
assert.strictEqual(t.edges['M4>M1'].count, 7);
assert.strictEqual(C.tally(events).edges['M3>M4'], undefined);
assert.strictEqual(C.dominant({plan: 2, bad: 5}), 'bad');

// the message list: newest first, repeats folded with their time range
const rows = C.groupRows([ev(1, 'M4', 'M1', 'incident'), ev(2, 'M4', 'M1', 'incident'), ev(3, 'M2', 'M1', 'assignment')]);
assert.deepStrictEqual(rows.map(r => [r.ev.seq, r.n]), [[3, 1], [2, 2]]);    // a row shows its newest message
assert.deepStrictEqual([rows[1].first, rows[1].last], [101, 102]);

// a task's path: attempts from plan-status, the assignment before an attempt joins it
const hist = [{id: 'A-1', number: 1, state: 'rejected', started_at: new Date(103 * 1000).toISOString()},
  {id: 'A-2', number: 2, state: 'accepted', started_at: new Date(110 * 1000).toISOString()}];
const path = [ev(2, 'M2', 'M1', 'assignment', {attempt: null}), ev(4, 'M6', 'M1', 'verdict'),
  ev(9, 'M2', 'M1', 'assignment', {attempt: null}), ev(12, 'M6', 'M1', 'verdict', {attempt: 'A-2'})];
const blocks = C.attempts(path, 'T4', hist);
assert.deepStrictEqual(blocks.map(b => [b.id, b.steps.map(e => e.seq)]), [['A-1', [2, 4]], ['A-2', [9, 12]]]);
assert.deepStrictEqual(C.attempts(path, 'T4', []).map(b => [b.id, b.steps.length]), [['A-1', 2], ['A-2', 2]]);   // no plan: from messages

// live insertion keeps `ord` order and ignores a replayed message
const list = [ev(1, 'M2', 'M1', 'a'), ev(5, 'M2', 'M1', 'b')], seen = {};
list.forEach(e => C.insert([], seen, e));
assert.strictEqual(C.insert(list, seen, ev(3, 'M2', 'M1', 'c')), true);
assert.strictEqual(C.insert(list, seen, ev(3, 'M2', 'M1', 'c')), false);
assert.deepStrictEqual(list.map(e => e.seq), [1, 3, 5]);

// replay: virtual time caps idle gaps
assert.strictEqual(C.span(events).length, 3);
assert.deepStrictEqual(C.upTo(events, 1.5).map(e => e.seq), [1, 2]);
const gap = [ev(1, 'M1', 'M3', 'start_order'), ev(2, 'M3', 'M1', 'dispatch_ack', {at_epoch: 100 + 3600})];
assert.strictEqual(C.span(gap).length, C.GAP_CAP);          // an idle hour replays as GAP_CAP seconds
assert.strictEqual(C.span(gap).real, 3600 - 1);
assert.deepStrictEqual(C.upTo([], 5), []);

// who is working now: from plan-status and the latest sign of life; a quiet one is marked, a waiting run shows M1
const iso = t => new Date(t * 1000).toISOString();
const run = {active: true, status: 'running', tasks: [
  {id: 'T1', state: 'completed', attempt: {id: 'A-1', live: false}},
  {id: 'T2', state: 'running', attempt: {id: 'A-2', live: true, state: 'running', started_at: iso(1000), last_activity_at: iso(1100)}},
  {id: 'T3', state: 'running', attempt: {id: 'A-3', live: true, state: 'verifying', started_at: iso(1000), last_activity_at: iso(1000)}},
  {id: 'T4', state: 'rejected', attempt: {id: 'A-4', live: false}}]};
const acts = C.activity(run, [{attempt: 'A-2', at_epoch: 1490}], 1500);
assert.deepStrictEqual(acts.map(a => [a.node, a.task, a.quiet]), [['M3', 'T2', false], ['M6', 'T3', true], ['M5', 'T4', false]]);
assert.strictEqual(acts[0].last, 1490);                     // the provider's digest is a newer sign than M1's record
assert.deepStrictEqual(acts[0].edges, [['M1', 'M3'], ['M3', 'M4']]);
assert.deepStrictEqual(C.activity({active: true, status: 'paused', tasks: []}, [], 0).map(a => a.node), ['M1']);
assert.deepStrictEqual(C.activity({active: false, status: 'completed', tasks: []}, [], 0), []);

let parts = [];
for (let i = 0; i < 50; i++) C.spawn(parts, ev(i, 'M1', 'M3', 'start_order'), 1000, 900);
assert.strictEqual(parts.length, C.MAX_PARTICLES);         // never more than 30 on screen
assert.strictEqual(C.alive(parts, 1000 + 899).length, 30);
assert.strictEqual(C.alive(parts, 1000 + 900).length, 0);
console.log('ok');
"""


class FlowPage(unittest.TestCase):
    def test_page_has_the_controls_and_loads_the_two_scripts(self):
        html = pf.flow_page("run:demo/REQ-001")
        for needle in ('data-scope="run:demo/REQ-001"', 'id="flow-live"', 'id="flow-replay"', 'data-speed="20"',
                       "/static/flow-core.js", "/static/flow.js", "/static/flow.css", "Reproducir", 'id="fl-tasks"', 'id="fl-tab-trace"',
                       'id="fl-detail"', "Pausar animación", 'data-sim="metodologia/REQ-026"'):
            self.assertIn(needle, html)

    def test_scope_is_escaped(self):
        self.assertNotIn("<script>alert", pf.flow_page('"><script>alert(1)</script>'))

    def test_every_category_the_core_emits_has_a_colour_and_matches_the_page(self):
        css = (ASSETS / "flowmap.css").read_text(encoding="utf-8")
        core = CORE.read_text(encoding="utf-8")
        for cls, text in pf.CATEGORIES:
            self.assertIn(f".{cls} {{ --kc:", css)
            self.assertIn(f"['{cls[2:]}', '{text}']", core)
        self.assertIn(".k-stream { --kc:", css)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_core_reducer_in_node(self):
        out = subprocess.run(["node", "-e", NODE_TEST, str(CORE)], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "ok")


if __name__ == "__main__":
    unittest.main()


class SimulatedRun(unittest.TestCase):
    def test_demo_plan_simulates_with_a_retry_and_covers_the_message_chain(self):
        import json
        import tempfile

        import bt_flow_bus
        import bt_scheduler_adapter as adapter
        plan = {"schema_version": "1.2.0", "plan_id": "REQ-900", "revision": 1,
                "milestones": [{"id": "M1", "title": "m", "acceptance_criteria": ["ok"]}],
                "tasks": [{"id": f"T{n}", "milestone_id": "M1", "title": f"task {n}", "after": ([f"T{n - 1}"] if n > 1 else []),
                           "repository": "app", "shared_resources": [], "expected_paths": ["x"],
                           "acceptance_criteria": ["ok"], "kind": "implement",
                           "verification": [{"type": "command", "value": "true", "purpose": "ok", "category": "functional"}]}
                          for n in (1, 2, 3)]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "PLAN.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            audit = adapter.simulate_audit(path, fail={"T2": 1}, reject={"T3": 1}, start=1_000.0)
            self.assertEqual(list(Path(d).iterdir()), [path])                    # nothing was written
        events = bt_flow_bus.simulated("simulación/REQ-900", audit)
        kinds = [e["kind"] for e in events]
        for needed in ("run_created", "start_order", "verify_order", "state_change", "task_state"):
            self.assertIn(needed, kinds)
        self.assertGreaterEqual(sum(k == "start_order" for k in kinds), 5)      # 3 tasks + 1 failed + 1 rejected attempt
        self.assertNotIn("unknown", kinds)
        self.assertEqual([e["ord"] for e in events], sorted(e["ord"] for e in events))
