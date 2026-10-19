"""Real product M1/M2/M3, serialized acceptance gates and verified cumulative patches."""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import bt_scheduler_adapter as adapter
import bt_scheduler_executor_adapter as api
from bt_scheduler_executor import gitutil
from bt_scheduler_executor.workspace import dirname_of
from bt_scheduler_patch_chain import PatchChainReceipt, PatchChainWorkspaces
from child_guards import install

ART = Path(__file__).resolve().parent
ROOT = Path(json.loads((ART/'runtime.json').read_text())['root'])
REQ = next(ROOT.glob('REQ-018-*'))
REPO = ROOT/'repository'
BASE = gitutil.run(REPO, ['rev-parse', 'HEAD'])


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n')


def tree(path):
    index = ROOT/f'index-{time.time_ns()}'
    env = {'GIT_INDEX_FILE': str(index)}
    gitutil.run(path, ['read-tree', 'HEAD'], env=env)
    gitutil.run(path, ['add', '-A'], env=env)
    return gitutil.run(path, ['write-tree'], env=env)


class Assignment:
    def __init__(self, task):
        self.task = task
        self.port = adapter.DecisionAssignmentPort('pictures', ROOT/'m2.sqlite3', laya_root=ROOT)

    def plan(self, request):
        rows = self.port.plan(request)
        save(ROOT/'routes'/f'{time.time_ns()}.json', [dataclasses.asdict(r) for r in rows])
        return rows

    def propose(self, request):
        scoped = dataclasses.replace(request, ready=tuple(t for t in request.ready if t.id == self.task))
        return self.port.propose(scoped) if scoped.ready else []


class ReviewInbox:
    def request(self, order):
        path = ROOT/'reviews'/order.task_id/f'order-{order.attempt_id}.json'
        value = dataclasses.asdict(order)
        if path.exists():
            assert json.loads(path.read_text()) == value
            return api.core.Ack('duplicate')
        save(path, value)
        save(ROOT/'reviews'/order.task_id/'order.json', value)
        return api.core.Ack('accepted')


class NoCheckout(api.m3.GitWorkspaces):
    def allocate(self, request):
        path = self.root/'worktrees'/dirname_of(request.attempt_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        repo = self.repository(request.repository)
        if not path.exists():
            gitutil.run(repo, ['worktree', 'add', '--detach', '--no-checkout', str(path), request.base_ref])
        return api.m3.Workspace(str(path), '(detached)', self.check(request), str(repo))


class ProtectedDriver(api.MethodologyDriver):
    def prepare(self, route, prompt, workspace, timeout_seconds):
        # Private dependency copy: workspace package symlinks must resolve locally.
        deps = Path(workspace.path)/'node_modules'
        if not deps.exists():
            subprocess.run(['cp', '-a', '--reflink=auto', '/home/david/dev/pictures/node_modules', str(deps)], check=True)
        launch = super().prepare(route, prompt, workspace, timeout_seconds)
        args = list(launch.argv)
        if route.provider == 'claude':
            args[1:1] = ['--settings', '{"disableAllHooks":true}', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence']
        elif route.provider == 'codex':
            args[2:2] = ['--disable', 'hooks']
        else:
            raise api.m3.ExecutorError('POLICY_DENIED', 'No child hook protection for provider')
        env = dict(launch.env_set)
        env['PATH'] = str(ROOT/'guard-bin')+os.pathsep+env.get('PATH', os.environ.get('PATH', ''))
        save(ROOT/'launches'/f'{time.time_ns()}.json', {'provider': route.provider, 'model': route.model,
             'profile': route.profile, 'effort_requested': route.effort, 'workspace': workspace.path,
             'hooks_disabled_child_only': True, 'patch_handoff': True})
        return dataclasses.replace(launch, argv=tuple(args), env_set=tuple(env.items()))


def notes(request):
    repair = ROOT/'task-notes'/f'{request.task_id}.txt'
    extra = repair.read_text() if repair.exists() else ''
    return f'''Owner approved the COMPLETE isolated REQ-018 product plan and revoked its cancellation ONLY in isolation.
Execute ONLY {request.task_id}; successor acceptance and dispatch belong to coordinator. Historical planning-only/cancelled notes in copied docs are superseded for this isolated run.
Read SPEC={REQ/'SPEC.md'}, PLAN={REQ/'PLAN.md'}, full task/interface data={REQ/'PLAN.json'}, local AGENTS.md, and relevant local Next.js guides under node_modules/next/dist/docs before Next changes.
You are not alone; preserve unrelated edits already in this cumulative worktree. Own this task's expected paths plus narrowly necessary same-responsibility helpers/tests. No broad refactoring.
STRICT RESTRICTIONS: no commits, commit-tree, push, merges, rebase, deploy, deleting files, product/provider/image/network calls, .env reads, methodology CLI/hooks, global config, subagents, memory, bitacora or requirement edits. Git is guarded; do not bypass guard or run absolute Git binary. No installs or dependency mutations. Existing node_modules is a PRIVATE copy. Main coordinator alone owns log/acceptance.
Retain ALL diagnostic/generated test copies and logs; no cleanup commands. rm/rmdir/unlink/shred are process-locally blocked. Never bypass command guards with absolute binaries or Python/Node filesystem deletion. Existing independent originals are read-only; run adapted diagnostics under .logs-tN instead of tracked source paths.
Tests must be deterministic and provider-free; browser local HTTP is allowed with all external calls stubbed. Run affected declared verification and required lint/workspace build/types, preserving full output in a new local ignored logs directory if needed. Tests before domain/bug changes: retain red/green evidence. No weakened assertions or fabricated passing checks.
Run verification commands in the foreground with bounded tool deadlines and capture real exit codes. A successful tsc may have an empty log; never wait for nonempty logs as completion proof. Do not use pgrep loops that match their own command text or other workspaces. Do not launch diagnostic monitor processes that outlive verification.
Environment evidence: local Next docs require generated route helpers. After package builds and before final npx tsc --noEmit, run npx next typegen. An independent att-0001 check proved typegen exit0 followed by tsc exit0 with unchanged source hashes/status. Do not misclassify absent generated LayoutProps as a source defect or skip final types. Keep logs under .logs-t1 through .logs-t8 (ignored only in this private clone).
T1 ONLY: seven files from prior accepted isolated T1 were independently hash-verified and seeded as CANDIDATE source; current plan semantically equals prior plan but prior acceptance DOES NOT transfer. Inspect compatibility, verify strict matcher and adapter behavior including all SPEC refinements, run declared tests, repair concrete in-scope defects. Do not require a gratuitous change if reuse is correct; report actual reuse and checks. Historical sole LayoutProps type failure needs fresh confirmation.
All other tasks: accepted predecessor cumulative patch and full accepted lineage have been verified before your process starts. Build on these files. No REQ-017 imports, whitelists or stale result padding. Do not claim full acceptance from exit0.
T7 is run/report only; do not fix. T8 is independent audit only; trace IF1–IF4, R1–R6 and AC1–AC9 to actual evidence, including blockers, do not fix. Main coordinator owns official verdict.
Output STATUS, CHANGES, actual tests and failures, remaining concerns. User-facing text Spanish starts Aye. Code follows repository language.
ADDITIONAL CURRENT TASK FINDINGS / REPAIR INSTRUCTIONS:
{extra}
'''


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('task')
    args = parser.parse_args()
    task = args.task
    install(ROOT)
    assignment = Assignment(task)
    wiring = api.wire(REQ, project='pictures', assignment=assignment, verification=ReviewInbox(),
        m2_ledger=ROOT/'m2.sqlite3', allow_direct=False, repos={'pictures': REPO}, default_repository='pictures',
        base_ref=BASE, config=api.core.Config(max_parallel_tasks=1, lease_seconds=3600),
        executor_config=api.m3.Config(max_running=1, timeout_seconds=2400, poll_seconds=0.5,
                                     handoff_mode='patch', patch_max_bytes=32*1024*1024),
        driver=ProtectedDriver('pictures'), autostart=False, integrate_predecessors=False)
    plan = wiring.scheduler.plan
    ids = list(plan.ids())
    assert all(tuple(plan.task(t).after) == (() if i == 0 else (ids[i-1],)) for i, t in enumerate(ids)), 'linear DAG required'

    def root_candidate():
        selected = ROOT/'root-candidate.json'
        if selected.exists():
            data = json.loads(selected.read_text())
            assert data['plan_sha256'] == plan.sha256 and data['status'] == 'candidate-not-accepted'
            assert data['task_id'] == ids[0] == 'T1'
            receipt = data['receipt']
            return PatchChainReceipt(**{**receipt, 'lineage': tuple(receipt['lineage'])})
        manifest = ROOT/'candidate-t1/handoff/manifest.json'
        return PatchChainReceipt(BASE, tree(REPO), ('candidate-t1',), str(manifest), hashlib.sha256(manifest.read_bytes()).hexdigest())

    def expected(request):
        snap = wiring.scheduler.snapshot().tasks
        lineage = list(root_candidate().lineage)
        for tid in ids[:ids.index(request.task_id)]:
            assert snap[tid]['state'] == 'completed' and snap[tid]['attempt_state'] == 'accepted', tid
            lineage.append(snap[tid]['attempt'])
        return tuple(lineage)

    def source(request):
        i = ids.index(request.task_id)
        if i:
            data = json.loads((ROOT/'accepted'/f'{ids[i-1]}.json').read_text())
            assert data['plan_sha256'] == plan.sha256
            receipt = data['receipt']
            return PatchChainReceipt(**{**receipt, 'lineage': tuple(receipt['lineage'])})
        return root_candidate()

    wiring.executor.workspaces = PatchChainWorkspaces(NoCheckout(wiring.executor.root/'chain-ws', {'pictures': REPO}),
         source, ROOT/'transfer-receipts', expected, materialize_empty=True)
    wiring.executor.briefs.notes = notes
    try:
        if wiring.scheduler.snapshot().paused:
            wiring.scheduler.resume('owner-isolated-full-run')
        wiring.executor.start_loop()
        deadline = time.time()+2700
        while time.time() < deadline:
            wiring.scheduler.step()
            snap = wiring.scheduler.snapshot()
            save(ROOT/'snapshot.json', snap.to_dict())
            view = snap.tasks[task]
            if view.get('attempt'):
                desc = wiring.executor.describe(view['attempt'])
                save(ROOT/'descriptions'/f'{task}.json', desc)
                if (ROOT/'reviews'/task/f"order-{view['attempt']}.json").exists() or view['state'] == 'blocked':
                    wiring.scheduler.pause('independent-verification', f'{task}: awaiting external tests/review before successor')
                    save(ROOT/'snapshot.json', wiring.scheduler.snapshot().to_dict())
                    save(ROOT/'audit.json', [r.to_dict() for r in wiring.scheduler.audit_log()])
                    print(json.dumps({'task': task, 'state': view['state'], 'attempt_state': view['attempt_state'], 'description': str(ROOT/'descriptions'/f'{task}.json')}), flush=True)
                    return
            elif time.time() > deadline-2650:
                wiring.scheduler.pause('route-or-state-blocker', 'No attempt started; inspect real M2 evidence')
                save(ROOT/'snapshot.json', wiring.scheduler.snapshot().to_dict())
                print('No task attempt started; inspect routes/snapshot', flush=True)
                return
            time.sleep(1)
        wiring.scheduler.pause('timeout-inspection', 'Caller bounded wait expired; inspect native process before retry')
        raise RuntimeError('Caller bounded wait expired')
    finally:
        wiring.close()
        assignment.port.close()


if __name__ == '__main__':
    main()
