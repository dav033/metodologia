"""Real Pictures plan after Implementer availability-policy correction."""
import hashlib
import json
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import bt_agents
import bt_events
import bt_profiles
import bt_role_routing
import bt_scheduler_adapter as adapter
import bt_scheduler_core as core
import bt_scheduler_plan_routing as routing
import bt_subscriptions
from bt_scheduler_core.simulators import ManualClock

ROOT = Path(__file__).resolve().parent
RUN_OUTPUT = Path(tempfile.mkdtemp(prefix='run-', dir=ROOT))
CASES = [('REQ018', 'real-approved-plan', 'mixed', 'mixed', 20, 60, 'per-task-policy')]
EXPECTED = {
    ('claude', 'implement'): ('sonnet', 'medium'),
    ('codex', 'implement'): ('gpt-6-luna', 'high'),
    ('claude', 'research'): ('sonnet', 'low'),
    ('codex', 'research'): ('gpt-6-luna', 'high'),
    ('claude', 'test'): ('sonnet', 'low'),
    ('codex', 'test'): ('gpt-6-luna', 'high'),
    ('claude', 'audit'): ('sonnet', 'medium'),
    ('codex', 'audit'): ('gpt-6.1-sol', 'medium'),
}


def run_case(case, reverse):
    number, shape, difficulty, kind, claude_used, codex_used, expected_provider = case
    directory = RUN_OUTPUT / f'case-{number}' / ('reverse' if reverse else 'forward')
    directory.mkdir(parents=True, exist_ok=False)
    requirement = next(ROOT.glob('REQ-018-*'))
    manifest = json.loads((requirement/'plan-revisions/MANIFEST.json').read_text())['revisions'][-1]
    frozen = requirement/'plan-revisions'/f"PLAN.r{manifest['revision']}.json"
    raw = frozen.read_text()
    digest = hashlib.sha256(frozen.read_bytes()).hexdigest()
    assert digest == manifest['sha256']
    (directory/'PLAN.json').write_bytes(frozen.read_bytes())
    plan = core.load_plan(raw, approved_sha256=manifest['sha256'], plan_id='REQ-018', revision=manifest['revision'])
    profiles = {p: {'provider': provider, 'bin': provider, 'env': {}, 'work_only': False}
                for p, provider in [('sim-claude', 'claude'), ('sim-codex', 'codex')]}
    pool = list(profiles)
    if reverse:
        pool.reverse()
    clock = ManualClock()
    now = clock()
    usage = {p: {'status': 'ok', 'observed_at': now-1, 'pressure': used}
             for p, used in [('sim-claude', claude_used), ('sim-codex', codex_used)]}

    def capacity(row, model, instant=None):
        pressure = row['pressure']
        return pressure, (clock()+10000 if pressure >= 100 else None)

    def preflight(project):
        return {p: {'status': 'available', 'state': 'exhausted' if v['pressure'] >= 100 else 'fresh',
                    'reason': 'quota_exhausted' if v['pressure'] >= 100 else 'quota_fresh'}
                for p, v in usage.items()}

    executor, verifier = core.FakeExecutor(), core.FakeVerifier()
    port = adapter.DecisionAssignmentPort('isolated-matrix', directory/'m2.sqlite3', laya_root=directory)
    trace, selected = [], []
    original_plan, original_propose = port.plan, port.propose

    def traced_plan(request):
        rows = original_plan(request)
        assert len(request.tasks) == len(plan.tasks) == len(rows)
        assert all(row.route_metadata.get('route_id') and not row.reason for row in rows), rows
        trace.append({'interaction': 'full DAG', 'recommendations': [row.__dict__ for row in rows]})
        return rows

    def traced_propose(request):
        snap = scheduler.snapshot()
        for task in request.ready:
            assert all(snap.tasks[parent]['state'] == 'completed' for parent in task.dependencies)
        rows = original_propose(request)
        trace.append({'interaction': 'READY assignment', 'ready': [t.id for t in request.ready],
                      'selected': [row.task_id for row in rows]})
        return rows

    try:
        with ExitStack() as stack:
            boundary_patches = [
                patch.object(bt_agents, 'pool_for', return_value=pool),
                patch.object(bt_profiles, 'load', return_value=profiles),
                patch.object(bt_agents, 'account_key', side_effect=lambda p, provider=None: p),
                patch.object(bt_agents, '_pool_account_identity', side_effect=lambda p, spec: (spec['provider'], p)),
                patch.object(bt_agents, 'cooling_until', return_value=None),
                patch.object(bt_subscriptions, 'load', return_value=usage),
                patch.object(bt_subscriptions, 'capacity', side_effect=capacity),
                patch.object(bt_events, 'read_all', return_value=[]),
                patch.object(adapter.decision_sources.shutil, 'which', return_value='/synthetic/provider'),
                patch.object(bt_role_routing.time, 'time', side_effect=clock),
                patch.object(adapter, 'refresh_quota_preflight', side_effect=preflight),
                patch.object(routing, 'quota_aware_requested_at', side_effect=lambda instant, status: instant),
                patch.object(port, 'plan', side_effect=traced_plan),
                patch.object(port, 'propose', side_effect=traced_propose),
                patch('socket.socket', side_effect=AssertionError('Network forbidden')),
                patch('subprocess.Popen', side_effect=AssertionError('Process launch forbidden')),
            ]
            for boundary in boundary_patches:
                stack.enter_context(boundary)
            scheduler = core.SchedulerCore(plan, core.SqliteRepository(directory/'m1.sqlite3'),
                ports=core.Ports(routing=port, assignment=port, execution=executor, verification=verifier),
                config=core.Config(max_parallel_tasks=2), clock=clock)
            scheduler.start()
            executed, verified = set(), set()
            for _ in range(100):
                scheduler.step()
                assert scheduler.snapshot().counts.get('live_attempts', 0) <= 2
                for aid, order in list(executor.started.items()):
                    if aid in executed:
                        continue
                    executed.add(aid)
                    route = adapter.resolve_m2_route(directory/'m2.sqlite3', order.executor)
                    assert route is not None
                    task_kind = bt_agents.infer_kind(plan.task(order.task_id).meta['title'],
                                                     plan.task(order.task_id).meta.get('kind'))
                    task_difficulty = plan.task(order.task_id).meta['complexity']
                    expected_provider = 'codex' if task_kind == 'audit' and task_difficulty == 'high' else 'claude'
                    model, effort = EXPECTED[(expected_provider, task_kind)]
                    if task_kind == 'audit' and task_difficulty == 'high':
                        effort = 'high'
                    assert (route['provider'], route['model'], route['effort']) == (expected_provider, model, effort), route
                    selected.append({'task': order.task_id, 'kind': task_kind, **route})
                    scheduler.ingest(core.Event(f'ev-{aid}', plan.plan_id, plan.revision, order.task_id, aid,
                        'simulated-executor', 'execution_finished', '', {}, order.token))
                for aid, order in list(verifier.requests.items()):
                    if aid in verified:
                        continue
                    verified.add(aid)
                    scheduler.submit_verdict(core.Verdict(f'v-{aid}', plan.plan_id, plan.revision, order.task_id,
                        aid, True, 'simulated-validator', 'scripted offline acceptance', order.token))
                if scheduler.snapshot().status == 'completed':
                    break
                clock.advance(1)
            snapshot = scheduler.snapshot()
            assert snapshot.status == 'completed', snapshot.to_dict()
            assert len(executed) == len(verified) == len(plan.tasks)
            report = {'case': case, 'reversed_accounts': reverse, 'simulation_plan_sha256': digest,
                      'approval_scope': 'isolated-simulation-only; real frozen Pictures plan', 'result': snapshot.to_dict(),
                      'routes': selected, 'trace': trace}
            (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
            (directory/'audit.json').write_text(json.dumps([e.to_dict() for e in scheduler.audit_log()], indent=2)+'\n')
            return {'case': number, 'shape': shape, 'difficulty': difficulty, 'kind': kind,
                    'claude_used': claude_used, 'codex_used': codex_used, 'tasks': len(plan.tasks),
                    'routes': [(r['task'], r['provider'], r['model'], r['effort']) for r in selected],
                    'status': snapshot.status}
    finally:
        port.close()


if __name__ == '__main__':
    summary = []
    for case in CASES:
        forward, reverse = run_case(case, False), run_case(case, True)
        assert forward == reverse, ('account order changed routing', case, forward, reverse)
        summary.append({**forward, 'account_order_invariant': True})
        print(json.dumps(summary[-1]), flush=True)
        (RUN_OUTPUT/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print('Evidence:', RUN_OUTPUT)
    print(f'PASS: {len(summary)} scenarios, 2 isolated runs, {sum(r["tasks"] for r in summary)*2} simulated tasks')
