"""Actual M1/M2/M3 smoke. Only native CLI flags and independent verification are caller-owned."""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import bt_scheduler_adapter as adapter
import bt_scheduler_executor_adapter as api

ROOT = Path(__file__).resolve().parent
REQ = ROOT/'REQ-M3'
REPO = ROOT/'repository'


def save(name,value):
    (ROOT/name).write_text(json.dumps(value,indent=2,default=str)+'\n')


class ScopeAssignment:
    def __init__(self):
        self.port=adapter.DecisionAssignmentPort('pictures',ROOT/'m2.sqlite3',laya_root=ROOT)

    def plan(self,request):
        rows=self.port.plan(request)
        save('initial-routes.json',[dataclasses.asdict(row) for row in rows])
        return rows

    def propose(self,request):
        request=dataclasses.replace(request,ready=tuple(t for t in request.ready if t.id=='T1'))
        return self.port.propose(request) if request.ready else []


class ReviewInbox:
    def request(self,order):
        path=ROOT/'verify-order.json'
        if path.exists():
            assert json.loads(path.read_text())==dataclasses.asdict(order)
            return api.core.Ack('duplicate')
        save('verify-order.json',dataclasses.asdict(order))
        return api.core.Ack('accepted')


class NoHookDriver(api.MethodologyDriver):
    def prepare(self,route,prompt,workspace,timeout_seconds):
        launch=super().prepare(route,prompt,workspace,timeout_seconds)
        args=list(launch.argv)
        if route.provider=='claude':
            args[1:1]=['--settings','{"disableAllHooks":true}','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence']
        elif route.provider=='codex':
            args[2:2]=['--disable','hooks']
        else:
            raise api.m3.ExecutorError('POLICY_DENIED','Native hook protection not configured for this provider')
        env=dict(os.environ)
        for key in launch.env_remove:env.pop(key,None)
        env.update(dict(launch.env_set))
        env['PATH']=str(ROOT/'guard-bin')+os.pathsep+env.get('PATH','')
        added=tuple((k,v) for k,v in env.items() if os.environ.get(k)!=v)
        save('native-launch.json',{'provider':route.provider,'model':route.model,'profile':route.profile,'effort':route.effort,'hooks_disabled':True,'m3_agent_executor':True,'worktree':workspace.path,'handoff_mode':'patch'})
        return dataclasses.replace(launch,argv=tuple(args),env_set=added)


def main():
    assignment=ScopeAssignment()
    before=subprocess.check_output(['git','rev-list','--all','--count'],cwd=REPO,text=True).strip()
    save('baseline-git.json',{'commit_count':int(before),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()})
    wiring=api.wire(REQ,project='pictures',assignment=assignment,verification=ReviewInbox(),
        m2_ledger=ROOT/'m2.sqlite3',allow_direct=False,repos={'probe':REPO},
        default_repository='probe',config=api.core.Config(max_parallel_tasks=1,lease_seconds=900),
        executor_config=api.m3.Config(max_running=1,timeout_seconds=420,grace_seconds=5,poll_seconds=0.2,handoff_mode='patch'),
        driver=NoHookDriver('pictures'),autostart=False,integrate_predecessors=False)
    wiring.executor.briefs.notes=lambda request: (
        'Owner approved an isolated M1/M2/M3 technical smoke only. Do not implement Pictures features or execute successor. '
        'Use built-in Node and write only m3-smoke/normalize-tags.mjs and m3-smoke/normalize-tags.test.mjs. '
        'You are not alone; preserve all other files. No commits,commit-tree,push,merge,rebase,deploy,deleting files,env reading,network/product/provider calls,workflow CLI,hooks,global config or subagents. '
        'No package/dependency changes. This is a standalone JS probe, not application integration: run node --test m3-smoke/normalize-tags.test.mjs only. '
        'Do not run Pictures lint/build/types/server or touch existing product source. Parent owns independent tests/logs/acceptance. '
        'Create meaningful behavior tests first, demonstrate red then implement. Code/comments English. Spanish response starts Aye. '
        'An optional attempt report at the M3-provided path is permitted; never claim external acceptance.'
    )
    wiring.executor.start_loop()
    wiring.scheduler.step()
    deadline=time.time()+520
    terminal_observed=False
    try:
        while time.time()<deadline:
            wiring.executor.tick()
            wiring.scheduler.step()
            snap=wiring.scheduler.snapshot()
            save('snapshot.json',snap.to_dict())
            attempt=snap.tasks['T1']['attempt']
            if attempt:
                described=wiring.executor.describe(attempt)
                save('m3-description.json',described)
                if described and described.get('state') in {'finished','failed','cancelled','rejected'}:
                    if (ROOT/'verify-order.json').exists() or snap.tasks['T1']['state']=='blocked':
                        terminal_observed=True
                        wiring.scheduler.pause('David-M3-smoke','Actual executor terminal; await external verification, successor forbidden')
                        save('snapshot.json',wiring.scheduler.snapshot().to_dict())
                        save('audit.json',[entry.to_dict() for entry in wiring.scheduler.audit_log()])
                        print(json.dumps({'root':str(ROOT),'m3_state':described['state'],'m1_attempt_state':snap.tasks['T1']['attempt_state'],'verification_requested':(ROOT/'verify-order.json').exists()}),flush=True)
                        return
            if not attempt and (ROOT/'initial-routes.json').exists():
                rows=json.loads((ROOT/'initial-routes.json').read_text())
                if any(row['task_id']=='T1' and row.get('reason') for row in rows):
                    terminal_observed=True
                    wiring.scheduler.pause('David-M3-smoke','No eligible actual account; no fake quota override')
                    save('snapshot.json',wiring.scheduler.snapshot().to_dict());print('NO ELIGIBLE ROUTE',flush=True);return
            time.sleep(0.5)
        raise RuntimeError('Bounded actual M3 smoke exceeded deadline')
    finally:
        if not terminal_observed:
            snap=wiring.scheduler.snapshot()
            task=snap.tasks['T1']
            if task['attempt'] and task['attempt_state'] not in {'accepted','rejected','failed','cancelled'}:
                wiring.scheduler.cancel('David-M3-smoke','Bounded experiment deadline')
                wiring.scheduler.step()
                cleanup_deadline=time.time()+15
                while time.time()<cleanup_deadline:
                    wiring.executor.tick()
                    if wiring.executor.query(task['attempt']).state in {'finished','failed','cancelled','rejected'}:break
                    time.sleep(0.2)
        wiring.close()
        assignment.port.close()


if __name__=='__main__':main()
