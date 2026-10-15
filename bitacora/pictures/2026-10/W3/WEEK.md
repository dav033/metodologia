---
status: draft
---
# pictures — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Development resumed on the laptop and REQ-015 judge fixes reached a locally verified feature branch; all 10 gate suites pass.
- 2026-10-15: closed P-092 ring upper-cap correction on `feat/req-014-motor-bandas`; kept semiarco and ring lower-edge findings separate as P-099/P-100.

## Done
- Owner-requested local Python setup is working: /readyz ready, authenticated quotation 39,111 COP. npm commands load `.env.local` explicitly; backend keeps operational state in memory and reads the existing catalogue. P-075 now exposes a material-name assertion failure instead of missing configuration.
- 2026-10-14: repaired P-075 colour regression's ignored Shopify snapshot dependency with controlled catalogue titles and registered it in guiada:test. Standalone regression and guided suite pass; final lint/types checks recorded in the day log. Reconciled stale P-041 after salon regression suite passed 27/27. Quotation UI integration reproduced exit 1 with missing Python configuration (503).
- REQ-016 M2 independently audited and rejected for P-082 (same-selection replay changes another pink). Local audit corrections `df0be2a0` enforce reader-first issuance, preserve unknown legacy history and bound the last order; main suite 20/20, existing gate 10/10. A committed standalone regression remains red; app build issues are separate P-083.
- Reconciled local clone and marathon records. Existing branch has 21 commits over tracked origin/main; T12 and audit #3 corrections are integrated as uncommitted changes.
- P-092: measured ring maxima per centimetre for 570/056 and capped at +5 %; rings under 1 m now have no band. Regression checks centimetre points, all three densities and seven profiles per tenth. Scenario seed 2 n=2000 has no ring failure class; the single semiarco sencilla failure is retained as P-099. Matrix 200/200, CI sweep 300/300, targeted invariant test, types and lint pass.
- Fixed selected-idea chips with an unrelated open plan, restored quote parity, and mixed round/Link-O-Loon color counts. Both independent review axes approve the corrections; P-076 closed.
- Confirmed stale generated development route types caused the historical typecheck errors. Recoverable backup retained; source types and app build pass without weakening checks.

## Decisions
- D-046: last successful colour replacement belongs to signed editing context; a present destination alone never prompts for known history, while proven replay is an honest no-op and true ambiguity still asks.
- D-040 temporary bitácora location in metodologia; D-041 laptop development; D-043 canned-chip fallback by rules; D-044 durable hourly quote cap with bounded memory fallback.

## Not done / dropped
- No new commit, push, merge, deploy, paid journey or production migration in the REQ-015 close-out. Full selected-idea browser journey remains a proposed test; historical test debt is separate.
- REQ-014 branch remains uncommitted; `next build` and the full gate were not run for this script/band change. P-091 remains unreviewed for merge; P-099/P-100 remain open.

## Carried over to next week
- Keep the REQ-014 changes separate from other local edits before any commit; investigate P-099/P-100. P-077 calibrates the default quote cap, P-075 retains historical tests to reproduce separately. Current evidence: [REQ-015 report](../../requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/REPORT.md).
