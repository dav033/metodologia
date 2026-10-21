#!/usr/bin/env bash
# Usage: rollback.sh [--dry-run]
# Points `current` back to the release recorded in `previous` and restarts the gateway.
set -euo pipefail
dry=${1:-}
root=${GATEWAY_ROOT:-/opt/bitacora-gateway}
run() { if [ "$dry" = "--dry-run" ]; then echo "+ $*"; else "$@"; fi; }

target=$(readlink "$root/previous" 2>/dev/null || true)
[ -n "$target" ] && [ -d "$target" ] || { echo "no previous release recorded under $root" >&2; exit 2; }
run ln -sfn "$target" "$root/current"
run systemctl restart bitacora-gateway
echo "rolled back to $target"
