"""Owner-scoped native T1 experiment; actual M1/M2, custom process/review ports, no M3 handoff commits."""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import bt_scheduler_adapter as adapter
import bt_scheduler_core as core
import bt_scheduler_executor_adapter as launch_api

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'pictures'
REQ = next(ROOT.glob('REQ-018-*'))
MANIFEST = json.loads((REQ/'plan-revisions/MANIFEST.json').read_text())['revisions'][-1]
RAW = (REQ/'plan-revisions'/f"PLAN.r{MANIFEST['revision']}.json").read_text()
PLAN = core.load_plan(RAW, approved_sha256=MANIFEST['sha256'], plan_id='REQ-018', revision=MANIFEST['revision'])


def save(name, value):
    (ROOT/name).write_text(json.dumps(value,indent=2,default=str)+'\n')


class ScopeAssignment:
    """Keep full-DAG M2 planning intact; operator permits native launch of T1 only."""
    def __init__(self):
        self.port = adapter.DecisionAssignmentPort('pictures', ROOT/'m2.sqlite3', laya_root=ROOT)

    def plan(self, request):
        result = self.port.plan(request)
        save('full-dag-routes.json',[dataclasses.asdict(row) for row in result])
        return result

    def propose(self, request):
        scoped = dataclasses.replace(request,ready=tuple(t for t in request.ready if t.id=='T1'))
        return self.port.propose(scoped) if scoped.ready else []


class NativeExecutor:
    def __init__(self):
        self.process = None
        self.order = None
        self.exit_code = None
        self.driver = launch_api.MethodologyDriver('pictures')

    def start(self, order):
        if order.task_id!='T1': return core.Ack('rejected','Owner scope permits T1 only')
        if self.order is not None:
            return core.Ack('duplicate' if order.attempt_id==self.order.attempt_id else 'rejected')
        found=launch_api.m2_ledger_lookup(ROOT/'m2.sqlite3')(order.executor)
        assert found, 'M2 selected reference did not resolve'
        save('selected-route.json',found)
        request=launch_api.m3.StartRequest(order.idempotency_key, PLAN.plan_id, PLAN.revision, order.task_id, order.attempt_id, order.token, order.executor, 'pictures', project='pictures', plan_sha256=PLAN.sha256)
        launch_api.RouteResolver.check_context(found,request)
        route=launch_api.m3.Route.from_dict({**found,'single_use':True,'reference':order.executor})
        role=Path('/home/david/dev/metodologia/skill/agents/implementer.md').read_text().split('---',2)[2]
        prompt=f'''{role}

GOAL: Repair the root causes in the previously rejected Pictures REQ-018 v2 T1, then verify the actual T1 retry in this isolated copy.
OWNER APPROVAL: David explicitly requested "arreglalo desde el origen y vuelve a intentarlo" after the prior real rejection. This is a newly authorized isolated T1 retry; the prior rejected run is immutable. This supersedes planning-only metadata in copied SPEC/PLAN, ONLY for T1. Do not implement or launch T2-T8. Do not edit requirement documents.
POINTERS: spec={REQ/'SPEC.md'}; plan={REQ/'PLAN.md'}; task data={REQ/'PLAN.json'} T1; project instructions={WORK/'AGENTS.md'}.
OWNERSHIP: T1 expected paths only, plus a narrowly necessary pure helper/test if justified. You are not alone in the codebase; do not revert other work. This snapshot includes unrelated dirty source changes: preserve them.
RULES: No commits, commit-tree, pushes, merges, deploys, deletion of user files, providers/images/production calls, methodology CLI/hook invocations, global settings changes, memory or bitacora edits, or subagent spawning. No .env reading. Network is only for this native model process, not product tests. Main coordinator owns logs and acceptance. Hooks disabled for this process. Stay in {WORK}; external requirement/instruction files are read-only. Do not modify node_modules or dependency symlink targets.
IMPLEMENT: Follow normative SPEC Matching and decision contract, especially rules1-5, and detailed T1. Pure matcher plus catalogue adapter, strict category/refinements/negatives, preserve legacy consumers, no padding. Do not expand to API, turn state, UI, or package script registration (T6).

ROOT-CAUSE REPAIR (required): Read {ROOT/'prior-findings.json'} and {ROOT/'prior-reproductions.json'}; do not just special-case those strings. First add behavior regression tests asserting CORRECT outcomes and show them fail against this rejected-code baseline (cover all four causes). Then repair the domain owners:
- Semantic affinity is not lexical equivalence. Keep legacy affinities unchanged for legacy consumers, but strict matching must use only genuine lexical variants, including existing dino/dinosaurio variants. Colours must never prove style or a different motif. Verify both positive genuine aliases and negative cross-affinity examples (elegante vs negro/dorado, romantico vs oro rosa, unicornio vs arcoiris, specific flower vs broader unrelated flower if expanded).
- Parse clause polarity as structured data shared by all strict matching consumers: repeated negative markers and transitions back to positive requirements must retain their meaning, not become literal tokens or leak across clauses. Include sin flores y sin gotico, sin negro y con dorado, no quiero negro pero si dorado, sin negro ni rosa and positive/negative mixed controls. Do not duplicate a second negative parser in the adapter.
- Preserve explicit style/theme refinements in customer messages even when unknown to catalogue/motif vocabulary. For quiero un estilo gotico / quiero estilo gotico / quiero tematica X, no matching evidence yields empty; matching literal evidence still succeeds. Do not drop unknown constraints or treat all conversational filler as requested styles.
- Baby gender interpretation must consume the same polarity-aware preference facts: no quiero nina may never select genero nina or admit derived/explicit girl candidates. Keep existing baby-only gender interpretation, positive nino/nina/neutro controls, and allow opposite/neutral candidates when permitted. Preserve lexical exclusions and other independent preferences. Add matcher and adapter regressions, including optional stored thematic text.
A narrowly named pure preference/lexical helper under src/lib/biblioteca-sempertex is allowed when it gives these rules a single authoritative owner; no broad rewrite/framework/table of special whole-request strings. Preserve legacy public helpers/behavior. New fields/functions are internal strict-boundary contracts; identify consumers and don't change wire DTOs. Keep domain helpers pure and acyclic.
BASELINE: npm lint/build-workspaces already pass with50 warnings; typecheck has one pre-existing isolated LayoutProps error at src/app/layout.tsx:26. Preserve that diagnosis; no unrelated fix. Tests must fail semantically, not merely missing-module/export. Never weaken old assertions. Save original red logs and final green logs separately under {ROOT}/checks.

VERIFY: first demonstrate new behavior tests fail against baseline, then implement. Execute all three T1 verification commands. Also run npm run lint, npm run build --workspaces --if-present, npx tsc --noEmit as required by AGENTS; save full noisy output only under {ROOT}/checks/ (this is the sole permitted outside-workspace write). Do not change unrelated defects or suppress failures. Typecheck may expose pre-existing/isolated setup issues; report precisely. No full app build required for this pure matcher task.
RETURN: STATUS, CHANGES, actual checks/results, RULINGS, CONCERNS; no manufactured success. Mention any limits. Each user-facing message starts Aye, in Spanish. Code follows repository naming conventions.
'''
        (ROOT/'brief.txt').write_text(prompt)
        ws=launch_api.m3.Workspace(str(WORK),'experiment/req018-t1','', '/home/david/dev/pictures')
        launch=self.driver.prepare(route,prompt,ws,1200)
        argv=list(launch.argv)
        if route.provider=='claude':
            argv[1:1]=['--settings',json.dumps({'disableAllHooks':True}),'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence']
        elif route.provider=='codex':
            argv[2:2]=['--disable','hooks']
        else:raise RuntimeError('Unsupported provider for hook-safe native experiment')
        env=dict(os.environ)
        for key in launch.env_remove:env.pop(key,None)
        env.update(dict(launch.env_set))
        env['PATH']=str(ROOT/'guard-bin')+os.pathsep+env.get('PATH','')
        env['BITACORA_AUTOCOMMIT']='0'
        # Do not persist environment values or credentials.
        save('native-launch.json',{'provider':route.provider,'profile':route.profile,'model':route.model,'effort':route.effort,'hooks_disabled':True,'custom_execution_port':True,'timeout_seconds':1200,'m3_used':False})
        self.out=(ROOT/'native.stdout.jsonl').open('w');self.err=(ROOT/'native.stderr.log').open('w')
        self.process=subprocess.Popen(argv,cwd=WORK,env=env,stdin=subprocess.PIPE if launch.stdin is not None else subprocess.DEVNULL,stdout=self.out,stderr=self.err,text=True,start_new_session=True)
        if launch.stdin is not None:self.process.stdin.write(launch.stdin);self.process.stdin.close()
        self.order=order;self.started=time.time()
        save('start-order.json',dataclasses.asdict(order))
        print(json.dumps({'started':order.task_id,**json.loads((ROOT/'native-launch.json').read_text())}),flush=True)
        return core.Ack('accepted')

    def query(self, aid):
        if self.order is None or aid!=self.order.attempt_id:return core.ExecutionStatus('not_found')
        rc=self.process.poll()
        return core.ExecutionStatus('running' if rc is None else 'finished' if rc==0 else 'failed')

    def cancel(self, order):
        if self.process and self.process.poll() is None:self.process.terminate()
        return core.Ack('accepted')


class OperatorReview:
    def request(self, order):
        save('verify-order.json',dataclasses.asdict(order))
        return core.Ack('accepted')


def main():
    assignment=ScopeAssignment();execution=NativeExecutor();review=OperatorReview()
    scheduler=core.SchedulerCore(PLAN,core.SqliteRepository(ROOT/'m1.sqlite3'),ports=core.Ports(routing=assignment,assignment=assignment,execution=execution,verification=review),config=core.Config(max_parallel_tasks=1,lease_seconds=1500))
    scheduler.start()
    if scheduler.snapshot().paused and not (ROOT/'verify-order.json').exists():
        scheduler.resume('David-scoped-T1-experiment','Actual Claude-work quota refreshed through ensure_fresh; no synthetic override')
    deadline=time.time()+1300;finished=False
    try:
        while time.time()<deadline:
            scheduler.step()
            if execution.process is None and (ROOT/'full-dag-routes.json').exists():
                t1=next(row for row in json.loads((ROOT/'full-dag-routes.json').read_text()) if row['task_id']=='T1')
                if t1.get('reason'):
                    save('no-route.json',t1)
                    scheduler.pause('David-scoped-T1-experiment','Actual quota or auth unavailable; no synthetic fallback')
                    save('snapshot.json',scheduler.snapshot().to_dict())
                    save('audit.json',[e.to_dict() for e in scheduler.audit_log()])
                    print(json.dumps({'no_route':t1}),flush=True)
                    return
            save('snapshot.json',scheduler.snapshot().to_dict())
            if execution.process is not None and execution.process.poll() is not None and not finished:
                execution.out.close();execution.err.close()
                raw=(ROOT/'native.stdout.jsonl').read_text()
                outcome=execution.driver.classify(launch_api.m3.Route.from_dict(json.loads((ROOT/'selected-route.json').read_text())),raw,execution.process.returncode)
                save('native-outcome.json',dataclasses.asdict(outcome))
                order=execution.order
                scheduler.ingest(core.Event('native-exit-'+order.attempt_id,PLAN.plan_id,PLAN.revision,order.task_id,order.attempt_id,'native-process-adapter','execution_finished' if outcome.status=='completed' else 'execution_failed','',{'returncode':execution.process.returncode,'outcome':outcome.status},order.token))
                finished=True
            if (ROOT/'verify-order.json').exists() or (finished and not (ROOT/'verify-order.json').exists() and scheduler.snapshot().tasks['T1']['state'] in {'blocked','failed'}):
                scheduler.pause('David-scoped-T1-experiment','Await actual independent review; T2 launch forbidden')
                scheduler.step()
                save('snapshot.json',scheduler.snapshot().to_dict())
                save('audit.json',[e.to_dict() for e in scheduler.audit_log()])
                print(json.dumps({'state':scheduler.snapshot().to_dict(),'awaiting_review':(ROOT/'verify-order.json').exists()}),flush=True)
                return
            time.sleep(1)
        if execution.process and execution.process.poll() is None:
            import signal
            os.killpg(execution.process.pid,signal.SIGTERM)
        raise RuntimeError('Bounded native experiment exceeded 1300 seconds')
    finally:assignment.port.close()


if __name__=='__main__':main()
