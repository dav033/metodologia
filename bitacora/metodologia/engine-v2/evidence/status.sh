#!/bin/bash
# One line per worker: log size, commits ahead of origin/main, result file presence, quota hints.
cd ~/dev/.engine-v2-wt
for b in *.brief.md; do t=${b%.brief.md}; [ -f $t.log ] || { echo "$t queued"; continue; }
  c=$(git -C $t log --oneline origin/main..HEAD 2>/dev/null | wc -l)
  r=$([ -s $t.result.md ] && head -1 $t.result.md || echo running)
  q=$(grep -c -E '^ERROR.*(usage limit|rate limit|429)|You.ve hit your usage limit' $t.log)
  echo "$t log=$(stat -c %s $t.log) commits=$c quota_hits=$q $r $(grep -o 'codex exit=.*' $t.log | tail -1)"
done
