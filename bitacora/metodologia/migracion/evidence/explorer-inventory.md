# Read-only inventory review
Provider: built-in explorer, dispatched before David requested Claude Haiku max. No code changes.

Confirmed preservation areas: CLI commands (bitacora.py:34); document IDs/templates (bt_core.py:38,240); workspace machine paths (bt_workspace.py:131,157); install surfaces (install.py:93,109,174); learn/context (bt_learn.py:104,176, bt_hooks.py:71); rounds/approval (bt_rounds.py:53,108, bt_handoff.py:116); durable runs (bt_runstate.py:167,201); relay/quota (bt_subscriptions.py:95, bt_relay.py:34, bt_relay_handoff.py:97); quality metrics (bt_quality.py:109); host support/VCS/security (bt_platform.py:87, bt_notify.py:81, bt_autostart.py:33, bt_vcs.py:52, bt_secrets.py:51); behavioral evals and tests (tests/test_00_isolation.py:22, tests/test_parallel.py:29, evals/graders.py:75,143).

Reviewer did not run tests/providers. Coordinator inspected the decisive resource paths, router, lock, installer, hook and provider contracts separately. The proposed six-directory topology does not explicitly account for all of these areas; INVENTORY records their ownership.
