#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST=${BITACORA_DEPLOY_ROOT:-/opt/bitacora}
CONFIG=${BITACORA_CADDY_CONFIG:-/etc/caddy/Caddyfile}

if [ "${1:-}" = "--check" ]; then
	grep -Fq 'Environment=GATEWAY_BIND=172.20.0.1' "$ROOT/bitacora-gateway.service"
	grep -Fq 'reverse_proxy 172.20.0.1:8790' "$ROOT/Caddyfile"
	echo 'deployment topology: 172.20.0.1:8790'
	exit 0
fi

[ "$(id -u)" -eq 0 ] || { echo 'run deploy.sh as root' >&2; exit 1; }
install -d -m 0755 "$DEST/remote/deploy" "$DEST/remote/gateway"
install -m 0644 "$ROOT"/../gateway/*.py "$DEST/remote/gateway/"
install -m 0644 "$ROOT/bitacora-gateway.service" /etc/systemd/system/bitacora-gateway.service
install -m 0644 "$ROOT/Caddyfile" "$DEST/remote/deploy/Caddyfile"
systemctl daemon-reload
systemctl enable --now bitacora-gateway.service
echo "Caddy block staged at $DEST/remote/deploy/Caddyfile; merge it into $CONFIG, then run: caddy validate --config $CONFIG && systemctl reload caddy"
