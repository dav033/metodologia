#!/bin/sh
set -eu

if [ "${1:-}" = "--check" ]; then
	echo 'rollback target: bitacora-gateway.service'
	exit 0
fi
[ "$(id -u)" -eq 0 ] || { echo 'run rollback.sh as root' >&2; exit 1; }
if systemctl cat bitacora-gateway.service >/dev/null 2>&1; then
	systemctl disable --now bitacora-gateway.service
	rm -f /etc/systemd/system/bitacora-gateway.service
fi
systemctl daemon-reload
echo 'Remove the staged reverse_proxy block from Caddy, validate, and reload Caddy.'
