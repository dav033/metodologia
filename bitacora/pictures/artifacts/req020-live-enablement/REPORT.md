# REQ-020 live enablement

Owner authorization: enable live/deployed checks and generate random credentials, 2026-10-22.

## Configuration and safety

- Generated independent random user/admin passwords and matching scrypt hashes, plus a random signing secret. Both roles authenticate. Private files are mode 600 in `/home/david/.config/pictures/`; no values are in this evidence.
- Existing voice service secret reused. Public Whisper test speech fixture used, never personal recordings.
- VPS environment backed up before modification. Only web recreated, with the exact already-running image; ai-api untouched. Running web is healthy, voice enabled and valid scrypt hashes/signing secret confirmed. No plaintext E2E passwords installed in the service.
- Vercel Production environment backed up privately; seven advisor/voice variables configured via stdin. Redeployment reuses the prior published source rather than unaccepted scheduler work. Deployment: dpl_GfE62U7W4nAUjeioZvpkuL78Zh3A; state must be checked against the day log.
- Final deployment state: READY. This activates the configuration on the existing published source; it does not publish the scheduler's advisor implementation.
- Supabase photo metadata migration 002 was absent, causing `42703: column a.photo_kind does not exist` and HTTP 503. PostgreSQL 17 schema dump retained privately (11952 bytes); existing runner applied 002 and skipped unchanged 001. No data deleted.

## Actual verification

| Check | Result |
| --- | --- |
| Generated user/admin authentication | PASS |
| Real signed Whisper request | PASS, HTTP 200, nonempty 114-character transcript |
| App `/api/voz/transcribir` during real M2 | PASS, HTTP 200 |
| Workspace and production builds during LIVE runs | PASS |
| Direct `tsc --noEmit` | PASS |
| ESLint on changed runner/scenario/test files | PASS |
| Deployed-runner argument/target tests | PASS, 3 tests |
| LIVE M1 complete scenario | FAIL, `initial summary was not proposed` |
| LIVE M2 complete scenario | FAIL, `correction did not invalidate the previous summary` |
| Deployed VPS M1/M2 | FAIL, login HTTP 307 to generic login; no credentials sent |
| Full gate / phone acceptance | Not run |

The functional failures are Pictures P-124. The released application still does not contain the advisor entry point; configuration alone cannot publish it. No manual PASS receipt issued.

## Coordinator runner

- Worktree: `/home/david/.local/tmp/req020-live-coordinator`, based on captured att-0087 snapshot 71a8f78400d437f09423cac1b51ca38120b8f6c7.
- Uncommitted runner patch retained in `coordinator-runner.patch`. Active att-0088 worktree is untouched.
- Local LIVE: `node --env-file=/home/david/.config/pictures/asesor-live.env --conditions=react-server --import tsx scripts/e2e/asesor/run.ts --start --live --milestone M1` (then M2).
- Deployed: replace `--start` with `--deployed`; private environment pins VPS origin and exact currently published SHA. Update that pin deliberately after the advisor release changes.
- Deployed mode never starts/builds locally, rejects mixed fake/local flags and unsafe origins, and checks login readiness before sending passwords. It enumerates only checks actually performed; local provider-failure injection remains local.
