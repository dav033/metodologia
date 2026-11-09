---
req: REQ-027
status: in-progress
created: 2026-11-09
---
# Plan — REQ-027 — Telegram bot MVP: photo to balloon count (same backend as /contador)

## Approach
New isolated package `services/telegram-globos/` (TypeScript, Node 24), same pattern as `services/whatsapp-globos`
(ports + one adapter). It long-polls Telegram, downloads the photo and counts it with the same capability the web
`/contador` uses: `llamarPythonContadorFoto` → ai-api `contador-foto.v1` (`src/lib/contador/foto.ts`). One adapter file
(`src/adapters/contador.ts`) is the only importer of `src/lib/**`. Channel code (Telegram client/polling) is kept apart
from the policy/reply core so WhatsApp can reuse the core later.
Alternatives (rejected): calling the Vercel `/api/contador` route (needs a user session cookie; fragile for a bot);
the REQ-024 recogniser reading (a different path from `/contador`, owner asked for the same as `/contador`);
a webhook on the VPS (needs public URL/deploy; deferred, laptop first).

## Global constraints
- Reuse, never modify: `contador-foto.v1`, ai-api, recogniser. Touch only `services/telegram-globos/**`; work in a
  dedicated worktree/branch from `origin/main`. No images stored or logged; secrets from env only.
- Live Gemini calls only in the last task, ≤ 3 photos (cost). All other tests use fakes.

## Tasks
### M1 — MVP (single milestone)
- [ ] T1 — Scaffold package: package.json, tsconfig, env schema (`TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_IDS`, `DAILY_QUOTA_PER_USER`, `DAILY_CAP_GLOBAL`), README, test runner · kind: implement · files: services/telegram-globos/package.json, services/telegram-globos/src/config.ts · verify: `npm --prefix services/telegram-globos test` · covers: R8, R9
- [ ] T2 — Telegram client + long-polling loop: getUpdates with offset, dedup, per-chat queue, photo/document pick, getFile download, magic-byte + 10 MB validation, sendMessage/typing, 409 handling · kind: implement · after: T1 · files: services/telegram-globos/src/telegram/*.ts · verify: `npm --prefix services/telegram-globos test` · covers: R1, R2, R6
- [ ] T3 — Adapter over `llamarPythonContadorFoto` (telemetry/DB off, HMAC, timeout) and `ResultadoFotoContador` → plain result type; contract test with a fake backend · kind: implement · after: T1 · files: services/telegram-globos/src/adapters/contador.ts · verify: `npm --prefix services/telegram-globos test` · covers: R3, R4, R7
- [ ] T4 — Policy + store (own SQLite): allow-list, per-user quota, global cap, hashed ids, counters survive restart · kind: implement · after: T1 · files: services/telegram-globos/src/policy/*.ts, services/telegram-globos/src/store/*.ts · verify: `npm --prefix services/telegram-globos test` · covers: R5
- [ ] T5 — Replies (ES, ≤900 chars: total, exact/estimate ±, sizes, Sempertex colours, no-balloons, errors, /start /ayuda /id) and wiring of the whole flow; `--dry-run` with a local image and a canned result · kind: implement · after: T2, T3, T4 · files: services/telegram-globos/src/replies/*.ts, services/telegram-globos/bin/*.ts · verify: `npm --prefix services/telegram-globos test` · covers: R3, R4, R5, R9
- [ ] T6 — Parity test: same fixture result through the web mapping (`resultadoDeFoto`) and the bot gives identical total/size/colour figures; the dry-run CLI runs a fixture image end to end · kind: test · after: T5 · files: services/telegram-globos/test/paridad.test.ts, services/telegram-globos/test/fixtures/* · verify: `npm --prefix services/telegram-globos test` · covers: R3, R4
- [ ] T7 — Independent review (spec + standards) of the diff · kind: audit · review_axis: spec · after: T6 · files: services/telegram-globos/audit/t7-review.md, services/telegram-globos/audit/t7.findings.json · verify: `bitacora.py audit-ledger check services/telegram-globos/audit/t7.findings.json` · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9
- [ ] T8 — Live check on the laptop with the owner's bot token: start poller, send 1–3 real photos, compare with `/contador`; record evidence · kind: test · after: T7 · verify: `npm --prefix services/telegram-globos run dry-run -- --help` · covers: R1, R3, R4, R5

## Verification
`npm --prefix services/telegram-globos test` green (no network); `npm run dry-run -- --foto x.jpg` prints the reply;
T8 live comparison with `/contador` on up to 3 photos. Needs from David before T8 only: bot token (@BotFather), his
Telegram id (`/id` command), running ai-api + `INTERNAL_HMAC_SECRET` + `GEMINI_API_KEY`.

## Rulings

## Progress log
- 2026-11-09 T8 live: owner gave the sddm PIN; Hyprland session + agent Firefox (Xephyr :20, BiDi 9223) started; bot `@dav033_globos_bot` created through BotFather in Telegram Web (token read from the DOM into `services/telegram-globos/.env`, mode 600; owner's id read from the web session). Bot running (long polling, laptop) with ai-api on 41731. /start answered; one real photo (arch, pink/gold/white) -> 135 balloons ±21 in 3.4 s, 61+40+34 colours = total, Sempertex names/codes, honest estimate wording. Not done: side-by-side comparison with production /contador (Gemini is not deterministic; same function by construction + parity test).
- 2026-11-09 T1–T6 built manually by the main session (owner: no scheduler). 34 tests, tsc and eslint clean; dry-run OK; live adapter count OK (1 photo, ~50 s). T7 review (antagonist, CONCERNS): 3 major + 3 minor real defects, all fixed (YOLO branch forced off, 20 s Telegram timeouts, same sharp image check as the web, dedup only for allowed users, refund on the reservation day, reply wording); 42 tests, tsc, eslint clean. T8 waits for the BotFather token and the owner's Telegram id.
