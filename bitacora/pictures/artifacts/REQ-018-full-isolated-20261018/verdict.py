"""Apply an externally evidenced verdict; never infer acceptance from agent exit."""
import argparse
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path

p = Path(__file__).with_name('flow.py')
spec = importlib.util.spec_from_file_location('product_flow', p)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)
parser = argparse.ArgumentParser()
parser.add_argument('task')
parser.add_argument('evidence', type=Path)
parser.add_argument('--reject', action='store_true')
args = parser.parse_args()
evidence = json.loads(args.evidence.read_text())
assert evidence['task'] == args.task
assert evidence['accepted'] is (not args.reject)
assert evidence['independent_reviews'] and evidence['checks'], 'external reviews/checks required'
order = json.loads((flow.ROOT/'reviews'/args.task/'order.json').read_text())
plan = flow.api.sched.approved_plan(flow.REQ)
description = json.loads((flow.ROOT/'descriptions'/f'{args.task}.json').read_text())
manifest_path = Path(description['artifacts']['handoff'])/'manifest.json'
manifest = json.loads(manifest_path.read_text())
assert manifest['attempt_id'] == order['attempt_id']
ws = Path(manifest['worktree'])
current_tree = flow.tree(ws)
assert evidence['tree'] == current_tree, 'reviewed source changed'
input_receipt = json.loads((flow.ROOT/'transfer-receipts'/f"{flow.dirname_of(order['attempt_id'])}.json").read_text())
input_tree = input_receipt['receipt']['target_tree']
removed = flow.gitutil.run(ws, ['diff', '--name-only', '--diff-filter=D', input_tree, current_tree])
assert not removed, f'New deletions forbidden: {removed}'
assert flow.gitutil.run(ws, ['rev-parse', 'HEAD']) == flow.BASE
assert manifest['status'] == 'captured' and manifest['head_sha'] == flow.BASE
# Replaying the exact M3 artifact must yield the reviewed tree before accepting it.
lineage = tuple(input_receipt['receipt']['lineage'])+(order['attempt_id'],)
receipt = flow.PatchChainReceipt(flow.BASE, current_tree, lineage, str(manifest_path), hashlib.sha256(manifest_path.read_bytes()).hexdigest())
request = flow.api.m3.StartRequest('review-replay-'+order['attempt_id'], plan.plan_id, plan.revision,
    args.task, 'review-replay-'+order['attempt_id'], 1, 'independent-replay', 'pictures', base_ref=flow.BASE,
    plan_sha256=plan.sha256)
manager = flow.PatchChainWorkspaces(flow.NoCheckout(flow.ROOT/'review-replays', {'pictures': flow.REPO}),
    lambda _: receipt, flow.ROOT/'review-replay-receipts', lambda _: lineage, materialize_empty=True)
replayed = manager.allocate(request)
assert flow.tree(Path(replayed.path)) == current_tree
scheduler = flow.api.sched.open_scheduler(flow.REQ)
try:
    snapshot = scheduler.snapshot()
    assert snapshot.tasks[args.task]['attempt'] == order['attempt_id']
    if not args.reject:
        flow.save(flow.ROOT/'accepted'/f'{args.task}.json', {'plan_sha256': plan.sha256,
            'receipt': dataclasses.asdict(receipt), 'evidence_path': str(args.evidence.resolve()),
            'evidence_sha256': hashlib.sha256(args.evidence.read_bytes()).hexdigest(),
            'replayed_tree': current_tree})
    verdict = flow.api.core.Verdict('external-'+order['attempt_id'], plan.plan_id, plan.revision,
        args.task, order['attempt_id'], not args.reject, 'independent-tests-and-reviews',
        str(args.evidence.resolve()), order['token'])
    result = scheduler.submit_verdict(verdict)
    flow.save(flow.ROOT/'reviews'/args.task/'applied-verdict.json', dataclasses.asdict(verdict))
    flow.save(flow.ROOT/'snapshot.json', scheduler.snapshot().to_dict())
    flow.save(flow.ROOT/'audit.json', [r.to_dict() for r in scheduler.audit_log()])
    print(result)
finally:
    closer = getattr(scheduler.repository, 'close', None)
    if closer is not None:
        closer()
