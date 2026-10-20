# AdvIn gateway go-live and rollback

The gateway runs on the AdvIn host at `172.20.0.1:8790`. Caddy runs in Docker and proxies to that host address;
do not bind the gateway to loopback or point Caddy at a container loopback address. Keep `/etc/bitacora/gateway.env`
owned by root with mode `0600`; populate it from `remote/deploy/gateway.env.example` using the deployment secret
store. Never put credential values in the repository.

## Go-live

1. Create the service account, application directory, and writable data directory; install the gateway source under
   `/opt/bitacora/remote/gateway` and create `/var/lib/bitacora` owned by `bitacora`.
   Rollback: remove these newly created directories and account only after confirming they contain no retained data.
2. Create `/etc/bitacora/gateway.env` from the example, fill all required values, set `GATEWAY_DATABASE` to a file
   under `/var/lib/bitacora`, and set mode `0600` and owner `root:root`.
   Rollback: remove the env file through the secret store; keep a protected backup if a redeploy may be needed.
3. Run `remote/deploy/deploy.sh --check`, then run `remote/deploy/deploy.sh` as root to install and start the unit.
   Confirm `systemctl status bitacora-gateway` is active and `ss -ltn` shows `172.20.0.1:8790`.
   Rollback: run `remote/deploy/rollback.sh` as root; inspect the service journal and preserve `/var/lib/bitacora`.
4. Add the block in `remote/deploy/Caddyfile` to the Docker-hosted Caddy configuration. Validate the complete
   configuration with `docker exec caddy caddy validate --config /etc/caddy/Caddyfile`.
   Rollback: remove only the added site block, validate the prior configuration, and leave Caddy serving other sites.
5. Reload Caddy with `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`, then verify HTTPS login and an
   authenticated API request through the public hostname. Confirm gateway requests arrive at the host listener.
   Rollback: remove the site block, validate and reload Caddy, then stop the gateway using step 3's rollback.

## Full rollback

1. Remove the Bitacora site block from Caddy, validate the remaining config, and reload Caddy.
   Rollback: restore the saved block, validate, and reload Caddy.
2. Run `remote/deploy/rollback.sh` as root to stop and disable the gateway service.
   Rollback: reinstall the unit with `deploy.sh`, check the env file, then verify service health.
3. Retain `/var/lib/bitacora` and the protected env file until the rollback is accepted; delete them only under the
   site's data-retention procedure.
   Rollback: restore the retained data and env file from their protected backup before reinstalling the service.
