"""Freeze a real-source Explorer ladder; oracle stays outside model workspaces."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/home/david/dev/metodologia/skill/scripts')

CASES = [
    ('E1', 'Targeted CLI lookup', [
        ('Q1', 'Where is `plan-json report REQ-NNN` registered, and which handler receives it?', 'bt_cli_plan.py', 'add_parser', 'report action registered; dispatch handles plan-json'),
        ('Q2', 'Trace the handler to the Planner module. Is report already implemented or only advertised?', 'bt_plan_adapter.py', 'def run_cli', 'dispatch calls adapter.run_cli then planner_cli.run; report implementation exists'),
        ('Q3', 'Find an existing test for report output or its CLI integration; explain the exact behavior it asserts.', 'bt_planner/tests/test_report.py', None, 'real report test and actual assertion, not an invented test'),
    ]),
    ('E2', 'UI ownership and similarly named reports', [
        ('Q1', 'Which page and function render the plan before approval? Trace its caller.', 'bt_page_req.py', 'def plan_panel', 'requirement plan tab calls plan_panel; renders PLAN.md'),
        ('Q2', 'Does that approval panel currently include the structured Planner report? Cite the actual render path.', 'bt_page_req.py', 'return md("doc", read(plan)) + form', 'no structured report in plan_panel; markdown plus form only'),
        ('Q3', 'The application also has a Review tab and REPORT.md. Are these the same report or a different lifecycle stage?', 'bt_page_review.py', None, 'executor report and merge/review stage distinct from plan approval/Planner report'),
        ('Q4', 'Find the reusable report producer and its presentation-independent shape. Identify the adapter boundary a future UI would use, without implementing it.', 'bt_planner/cli.py', 'if action == "report"', 'quality.analyze plus schema-gated coverage/interfaces/verification projections; adapter boundary for UI'),
    ]),
    ('E3', 'History projection and misleading nearby telemetry', [
        ('Q1', 'Trace `plan-json history --kind ...` from argument validation to its result producer. When is REQ-NNN rejected?', 'bt_cli_plan.py', 'if action == "history"', 'history separate branch rejects req/force and requires kind; project_history'),
        ('Q2', 'What exact context dimensions and task kinds are accepted? What happens to unknown fields or invalid values?', 'bt_plan_history.py', 'CONTEXT_FIELDS', 'complexity/scope/risk/coupling and bt_agents.KINDS; stable invalid errors'),
        ('Q3', 'Find the returned quality, duration, retry and consumption measurements. Are any of them currently observed numbers?', 'bt_plan_history.py', 'metrics = {', 'all four unknown/null, not 0 or estimates'),
        ('Q4', 'Why does existing per-route M2 quality or attempt telemetry not automatically populate these Planner measurements?', 'bt_plan_history.py', 'Current M2 quality evidence', 'route scoped quality, absent applied M6 correlation and incompatible token units prevent cross-route claims'),
        ('Q5', 'Locate tests that demonstrate unknown output and prevent leaking route identities. State what these tests do not establish about live performance.', 'tests/test_plan_history.py', None, 'actual tests of unknown/redaction; no live performance inference'),
    ]),
    ('E4', 'Whole DAG recommendation versus READY reservation', [
        ('Q1', 'Trace Scheduler start into whole-plan route mapping. Does it include blocked/dependent tasks or only READY tasks?', 'bt_scheduler_core/scheduler.py', 'def _plan_all_routes', 'start asks port.plan for every plan task before reconciliation; dependency and criteria passed'),
        ('Q2', 'Find the concrete bridge to M2 and the bounded joint allocation. Is it one decision per task or one batch operation for the map?', 'bt_scheduler_plan_routing.py', 'def plan_full_dag', 'DecisionAssignmentPort.plan -> plan_full_dag -> one batch persist, task/matrix bounds'),
        ('Q3', 'Where are planned routes/unavailable reasons persisted, and what prevents repeating the map on restart?', 'bt_scheduler_core/scheduler.py', 'routing_complete', 'state planned metadata/reasons, routing_complete guards restart'),
        ('Q4', 'Does whole-plan mapping reserve executor capacity or launch work? Locate the component that really reserves.', 'bt_scheduler_core/reservation.py', 'def claim', 'map nonreserving; M1 claim transaction owns holds, attempt, start outbox'),
        ('Q5', 'Trace READY assignment after account quota changes. Is the old planned model/profile blindly reused?', 'bt_scheduler_adapter.py', 'def propose', 'propose refreshes and rebuilds candidates then persists batch and typed decision; no blind planned route reuse'),
        ('Q6', 'Where are quota refresh failures converted into unknown/unavailable facts, and how is the request timestamp tied to fresh observations?', 'bt_scheduler_plan_routing.py', 'def quota_aware_requested_at', 'preflight failure disqualifies affected candidates; requested_at >= observation and current wall time'),
        ('Q7', 'Find an existing integration/regression test for plan-time routes versus execution-time revalidation or nonreservation. Explain its actual scenario.', 'tests/test_scheduler_decision_integration.py', 'def test_ready_revalidation_uses_changed_quota_and_m1_owns_the_only_reservation', 'actual full-plan/revalidation/nonreservation test, not a claimed live provider run'),
    ]),
    ('E5', 'Tier floors, comparable quality and effective account allocation', [
        ('Q1', 'Locate the real task-tier floor calculation. Explain the effects of high/extreme complexity, scope, coupling, duration and risk. Does medium risk alone force a higher tier?', 'bt_scheduler_decision_adapter.py', 'def _tier_floor', 'floor rules incl 120/240 duration, coupling medium/high tier1; medium risk alone no bump'),
        ('Q2', 'Trace creation of candidate model/effort/profile/account identities. Is account identity simply a provider name?', 'bt_scheduler_decision_adapter.py', 'def _candidate_rows', 'route options and profile-specific candidate IDs, account_reference(account_key), not provider-only'),
        ('Q3', 'Trace quota sampling preflight. How are aliases of one effective account grouped, is refresh always forced, and what bounds the work?', 'bt_scheduler_quota_preflight.py', 'def refresh', 'effective identity grouping, one leader, max32 accounts, poll due-only not forced'),
        ('Q4', 'Locate hard eligibility filters for unsupported sources, auth/runtime and stale/unknown/exhausted quota. Can a good quality score bypass them?', 'bt_scheduler_decision/policy.py', 'def _candidate_reasons', 'hard filters precede optional quality ranking; no bypass'),
        ('Q5', 'When can quality rank routes? Trace minimum verified samples, uncertainty intervals and cross-route selected-level comparability.', 'bt_scheduler_decision/policy.py', 'def _quality_objective_is_comparable', 'validated observed interval/sample evidence for every eligible candidate at same selected level; otherwise skip quality objective'),
        ('Q6', 'Without comparable quality, what is the actual lexicographic order? How are missing or incomparable duration/cost facts handled?', 'bt_scheduler_decision/policy.py', 'def _route_objective_key', 'quota then measured duration then comparable relative cost, reserve/reset/baseline/stable id; missing uses infinity'),
        ('Q7', 'Does the actual whole-plan adapter supply contextual quality assessments and API prices to that ranking? Separate policy capability from currently wired evidence.', 'bt_scheduler_plan_routing.py', 'def _route_evidence', 'whole-plan evidence currently quota windows/duration, no quality_assessment or relative_cost supplied'),
        ('Q8', 'Trace batch matching by effective account. Can two profile aliases manufacture capacity, and is a persisted batch a durable execution reservation?', 'bt_scheduler_decision/batch.py', 'def _rank_batch_routes', 'dedup options by account_ref, account capacities and matching, recommendations not reservations'),
        ('Q9', 'Find tests that cover floor variation and account alias/capacity behavior. Identify any runtime facts about actual account quotas that this source snapshot cannot prove.', 'tests/test_scheduler_decision_sources.py', None, 'real floor/account tests; no credentials or live quota conclusions from source'),
    ]),
    ('E6', 'Extreme: crash, lost acknowledgement, stale events and independent verification', [
        ('Q1', 'Reconstruct the path from READY selection to a durable start order and M3 acceptance. Identify ownership and transaction boundaries, including when external calls happen.', 'bt_scheduler_core/reservation.py', 'def claim', 'M1 atomic attempt/hold/outbox commit then Dispatcher external start, CoreExecutionPort translates, M3 ledger acceptance'),
        ('Q2', 'Suppose M3 accepted a start but its acknowledgement was lost and M1 restarts. Trace how M1 decides whether to resend; identify the same-key protection in M3.', 'bt_scheduler_core/dispatch.py', 'if kind == "start" and before > 0', 'write-ahead delivery count, query before resend, M3 by_key replay and KEY_CONFLICT'),
        ('Q3', 'If the attempt lease expires and the executor query returns unknown, what happens to task, attempt, resource holds and retry eligibility? Cite the real branches.', 'bt_scheduler_core/recovery.py', 'def apply_observation', 'lease schedules reconcile; unknown -> UNCERTAIN keeps task ACTIVE/holds and no automatic duplicate retry'),
        ('Q4', 'Contrast query not_found for a pending unsent start versus not_found after delivery. Which branch allows safe redelivery and which records loss?', 'bt_scheduler_core/recovery.py', 'elif verdict == "not_found"', 'pending start RESERVED/UNCERTAIN resets RESERVED/redeliver; otherwise FAILED lost'),
        ('Q5', 'Trace an execution_finished event all the way to task completion. Is clean process exit or claimed success sufficient, and who may accept the work?', 'bt_scheduler_core/events.py', 'def apply_verdict', 'finished -> VERIFYING + verify outbox, independent accepted verdict with evidence completes/promotes; exit not acceptance'),
        ('Q6', 'During VERIFYING, a later executor query says unknown or failed. Does reconciliation override the verifier? Locate the exception for operator action.', 'bt_scheduler_core/recovery.py', 'verifying_is_settled_by_verdict', 'ignore failed/not_found/cancelled/unknown while VERIFYING unless manual'),
        ('Q7', 'Trace duplicate event IDs, wrong plan/revision, old attempt IDs and wrong fencing tokens. Explain the incident-event exception rather than applying one blanket rule.', 'bt_scheduler_core/events.py', 'def _preflight', 'wrong plan invalid, duplicate seen, mismatch stale, superseded stale; INCIDENT_OBSERVED allow_superseded and incident dedup'),
        ('Q8', 'What happens if cancellation arrives before pending start delivery versus while work may already be running? Are holds immediately discarded in both cases?', 'bt_scheduler_core/operations.py', 'def cancel', 'unsent RESERVED start can close/cancel; running/uncertain sends cancel retains holds until authoritative terminal, no new starts'),
        ('Q9', 'Locate M3 restart recovery for PREPARING/RUNNING/SETTLING. What persisted process/shim/result facts are checked, and what remains uncertain instead of launching a duplicate?', 'bt_scheduler_executor/recovery.py', None, 'actual persisted launch/result/process identity recovery; uncertain physical outcome not blind respawn'),
        ('Q10', 'Trace how an opaque M2 reference is bound back to the approved plan/task and account before M3 launch. Can a stale or mismatched reference silently fall back?', 'bt_scheduler_executor_adapter.py', 'def check_context', 'M2 ledger lookup plan/revision/hash/task and resolver/account gates, no silent legacy fallback for failed M2 ref'),
        ('Q11', 'Find executable tests covering lost-ack restart, unknown-hold retention and stale/duplicate/verifier handling. Give distinct examples and explain their assertions; do not run them.', 'bt_scheduler_core/tests/test_dispatch.py', None, 'actual tests from dispatch/restart/recovery/events asserting the named behaviors'),
        ('Q12', 'State the limit of the end-to-end guarantee. Does this source prove exactly-once effects at an arbitrary external provider, automatic quality acceptance, or live-account availability?', 'bt_scheduler_executor/executor.py', None, 'idempotent local acceptance is not arbitrary remote exactly-once; verifier independent; source cannot prove quota/live auth'),
    ]),
]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__ == '__main__':
    assert not (ROOT/'workspace.json').exists(), 'Already frozen'
    work = Path(tempfile.mkdtemp(prefix='metodologia-explorer-ladder-20261017-'))
    source = work/'source'/'repo'/'skill'/'scripts'
    files = [p for p in SOURCE.rglob('*') if p.is_file() and not p.is_symlink()
             and p.suffix in {'.py', '.md', '.json'}
             and not any(part in {'__pycache__', '.state', 'node_modules'} for part in p.relative_to(SOURCE).parts)]
    for p in files:
        dest = source/p.relative_to(SOURCE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    cases=[]; oracle=[]
    for cid,title,questions in CASES:
        cases.append({'id':cid,'title':title,'difficulty':int(cid[1:]),
                      'questions':[{'id':qid,'question':q} for qid,q,*_ in questions]})
        for qid,q,path,anchor,expected in questions:
            target=source/path
            # Test-file names are discovered from the frozen source before calls.
            oracle.append({'case':cid,'question':qid,'path_hint':f'skill/scripts/{path}',
                           'anchor':anchor,'expected':expected,'hint_exists':target.exists(),
                           'anchor_line':next((i for i,line in enumerate(target.read_text().splitlines(),1)
                                               if anchor and anchor in line),None) if target.exists() else None})
        for route in (['luna','haiku','gemini'] if cid in ('E1','E2','E3') else ['luna','haiku','gemini','sol','sonnet']):
            shutil.copytree(work/'source'/'repo',work/'cells'/cid/route/'repo')
    for name,data in [('cases.json',cases),('oracle.json',oracle),('workspace.json',{'root':str(work),'snapshot_root':str(work/'source'/'repo')}),
                      ('source-hashes.json',{str(p.relative_to(work/'source'/'repo')):digest(p) for p in (work/'source'/'repo').rglob('*') if p.is_file()})]:
        (ROOT/name).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'workspace':str(work),'source_files':len(files),'source_bytes':sum(p.stat().st_size for p in files),
                      'cases':len(cases),'criteria':len(oracle),'missing_hint_paths':[x['path_hint'] for x in oracle if not x['hint_exists']]}))
