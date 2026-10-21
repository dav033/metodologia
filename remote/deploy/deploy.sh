#!/usr/bin/env bash
# Usage: deploy.sh <path-to-remote/gateway-dir> [--dry-run]
# Installs a timestamped release under /opt/bitacora-gateway/releases and switches `current` to it.
set -euo pipefail
if [ "${1:-}" = "--check" ]; then
  grep -Fq 'Environment=GATEWAY_BIND=172.20.0.1' "$(dirname "$0")/bitacora-gateway.service"
  grep -Fq 'reverse_proxy 172.20.0.1:8790' "$(dirname "$0")/Caddyfile"
  echo 'deployment topology: 172.20.0.1:8790'
  exit 0
fi
src=${1:?usage: deploy.sh <gateway-dir> [--dry-run]}
dry=${2:-}
root=${GATEWAY_ROOT:-/opt/bitacora-gateway}
env_file=${GATEWAY_ENV_FILE:-/etc/bitacora-gateway/gateway.env}
run() { if [ "$dry" = "--dry-run" ]; then echo "+ $*"; else "$@"; fi; }

[ -f "$src/main.py" ] || { echo "no main.py in $src" >&2; exit 2; }
if [ "$dry" != "--dry-run" ]; then
  [ -f "$env_file" ] || { echo "missing $env_file" >&2; exit 2; }
  for key in LAPTOP_ORIGIN FLOW_GATEWAY_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID GATEWAY_DATABASE \
             GITHUB_CLIENT_ID GITHUB_CLIENT_SECRET SESSION_SECRET FLOW_FRONTEND_ORIGIN; do
    grep -Eq "^${key}=.+" "$env_file" || { echo "$key is empty in $env_file" >&2; exit 2; }
  done
fi
release="$root/releases/$(date -u +%Y%m%dT%H%M%SZ)"
previous=$(readlink "$root/current" 2>/dev/null || true)
run mkdir -p "$release"
run cp -a "$src" "$release/gateway"
run python3 -m compileall -q "$release/gateway"
[ -n "$previous" ] && echo "previous release: $previous"
[ -n "$previous" ] && run ln -sfn "$previous" "$root/previous"
run ln -sfn "$release" "$root/current"
run systemctl restart bitacora-gateway
echo "deployed $release"
