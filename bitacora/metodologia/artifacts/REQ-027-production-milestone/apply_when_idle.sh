#!/usr/bin/env bash
# Wait until REQ-027 has finished cleanly (every task completed, nothing live), then add milestone M6 and let the Scheduler
# run it. Stops without changing anything if the run needs the owner (blocked task, open decision) or never settles.
set -u
cd /home/david/dev/metodologia/skill || exit 1
B="python3 scripts/bitacora.py --project metodologia"
R=$(ls -d ~/bitacora/metodologia/requirements/REQ-027-*)
A=~/bitacora/metodologia/artifacts/REQ-027-production-milestone/add_production_milestone.py
say() { echo "$(date +%H:%M:%S) $*"; }
for i in $(seq 1 720); do
  S=$($B scheduler-op REQ-027 status 2>/dev/null)
  LIVE=$(echo "$S" | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['live_attempts']),len(d['open_decisions']),len(d['blocked_tasks']))" 2>/dev/null)
  DONE=$(python3 -c "import json,sys;d=json.load(open('$R/RUN.projection.json'));print(d.get('status'))" 2>/dev/null)
  set -- $LIVE
  if [ "${2:-0}" != "0" ] || [ "${3:-0}" != "0" ]; then say "STOP: the run needs the owner (decisions=$2 blocked=$3); nothing changed"; exit 3; fi
  if [ "${1:-1}" = "0" ] && [ "$DONE" = "done" ]; then break; fi
  sleep 120
done
[ "${1:-1}" = "0" ] && [ "$DONE" = "done" ] || { say "STOP: the run did not finish within 24 h; nothing changed"; exit 2; }
say "run is done and idle: preparing revision"
TMP=$(mktemp -d); cp -r "$R" "$TMP/req"; python3 "$A" "$TMP/req" --apply >/dev/null || { say "STOP: generator failed on the copy"; exit 4; }
cp "$R/SPEC.md" "$TMP/SPEC.md.bak"; cp "$R/PLAN.md" "$TMP/PLAN.md.bak"; cp "$R/PLAN.json" "$TMP/PLAN.json.bak"
python3 "$A" "$R" --apply || { say "STOP: apply failed"; exit 4; }
if ! $B plan-json check REQ-027 2>&1 | grep -q "^OK: PLAN.json is publishable"; then
  cp "$TMP/SPEC.md.bak" "$R/SPEC.md"; cp "$TMP/PLAN.md.bak" "$R/PLAN.md"; cp "$TMP/PLAN.json.bak" "$R/PLAN.json"
  say "STOP: plan-json check refused the new revision; files restored"; exit 5
fi
$B plan-json freeze REQ-027 2>&1 | tail -1 || exit 6
$B scheduler-op REQ-027 revise --reason "plan r6: milestone M6 builds and verifies the production environment (owner 2026-10-19)" 2>&1 | tail -4
say "done: M6 is queued; T20 starts when the Scheduler claims it"
