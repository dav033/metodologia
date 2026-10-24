#!/bin/bash
# Usage: launch.sh <task-id> <codex-home-suffix: codex|codex-2|codex-luis> [base-ref]
# Creates the worktree (if missing) and runs codex exec in the foreground (caller backgrounds it).
set -u
T=$1; H=$HOME/.$2; BASE=${3:-origin/main}
W=$HOME/dev/.engine-v2-wt/${WT:-$T}
cd $HOME/dev/metodologia
git fetch -q origin
[ -d "$W" ] || git worktree add -q -b ev2/$T "$W" "$BASE"
start=$(date +%s)
BITACORA_EXECUTION_POLICY=restricted-v1 CODEX_HOME=$H codex exec -m gpt-6-luna -c model_reasoning_effort=high \
  --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  -C "$W" -o "$HOME/dev/.engine-v2-wt/$T.result.md" - < "$HOME/dev/.engine-v2-wt/$T.brief.md" > "$HOME/dev/.engine-v2-wt/$T.log" 2>&1
code=$?
echo "codex exit=$code elapsed=$(( $(date +%s)-start ))s account=$2" >> "$HOME/dev/.engine-v2-wt/$T.log"
echo "$T codex exit=$code account=$2 elapsed=$(( $(date +%s)-start ))s"
