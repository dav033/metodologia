---
status: draft
---
# pictures — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Development resumed on the laptop and REQ-015 judge fixes reached a locally verified feature branch; all 10 gate suites pass.
- 2026-10-15: P-092's ring cap, P-100's 1.42 m placement dip and P-099's semiarco fill calibration merged to main through PR #11 (`f8227ca5`); bands and failure policy remain unchanged.

## Done
- Owner-requested local Python setup is working: /readyz ready, authenticated quotation 39,111 COP. npm commands load `.env.local` explicitly; backend keeps operational state in memory and reads the existing catalogue. P-075 now exposes a material-name assertion failure instead of missing configuration.
- 2026-10-14: repaired P-075 colour regression's ignored Shopify snapshot dependency with controlled catalogue titles and registered it in guiada:test. Standalone regression and guided suite pass; final lint/types checks recorded in the day log. Reconciled stale P-041 after salon regression suite passed 27/27. Quotation UI integration reproduced exit 1 with missing Python configuration (503).
- REQ-016 M2 independently audited and rejected for P-082 (same-selection replay changes another pink). Local audit corrections `df0be2a0` enforce reader-first issuance, preserve unknown legacy history and bound the last order; main suite 20/20, existing gate 10/10. A committed standalone regression remains red; app build issues are separate P-083.
- Reconciled local clone and marathon records. Existing branch has 21 commits over tracked origin/main; T12 and audit #3 corrections are integrated as uncommitted changes.
- P-092 (`125548cf`), P-091 (`4916115f`) and P-099/P-100 (`5c7649fb`) are merged to main in PR #11 (`f8227ca5`). The PR contained 38 branch commits and 268 changed paths, beyond the four-file P-092 slice; this includes earlier work already on the branch. The two later local P-087 modifications remain unstaged.
- P-099 calibrates semiarco fill with the empirical cap 1.04 (D-050), using the constructor's rounded/clamped measures; contour and structural density are unchanged. E-01637, E-03398 and E-03979 regressions pass. P-100 retains the 1.42 m minimum and measured cap after closed-ring fill candidates moved to 1 cm.
- Seed 2 n=4000 after P-099: 3,999/4,000 pass, with 422/422 semiarcos passing. Sole failure E-03532 (lujosa guirnalda, 944, 5.97 m) is the same exact repro recorded in the baseline (3,996/4,000); no allowed-failure entry was added. Antagonist review SOUND; invariants, matrix, CI sweep, tsc, lint and workspace builds pass.
- Fixed selected-idea chips with an unrelated open plan, restored quote parity, and mixed round/Link-O-Loon color counts. Both independent review axes approve the corrections; P-076 closed.
- Confirmed stale generated development route types caused the historical typecheck errors. Recoverable backup retained; source types and app build pass without weakening checks.

## Decisions
- D-046: last successful colour replacement belongs to signed editing context; a present destination alone never prompts for known history, while proven replay is an honest no-op and true ambiguity still asks.
- D-049: semiarco fill is calibrated to the contractual quarter-ellipse axis while preserving the current contour and count-band contract.
- D-040 temporary bitácora location in metodologia; D-041 laptop development; D-043 canned-chip fallback by rules; D-044 durable hourly quote cap with bounded memory fallback.

## Not done / dropped
- No new commit, push, merge, deploy, paid journey or production migration in the REQ-015 close-out. Full selected-idea browser journey remains a proposed test; historical test debt is separate.
- `next build` and the full local repository gate were not run; the affected suites and PR checks passed before merge. Post-merge Quality workflow `38816458147` succeeded and Vercel reports deployment completed; no manual VPS deploy was initiated. The two P-087 worktree modifications remain separate. E-03532 is a baseline guirnalda failure outside P-099 and remains follow-up work.

## Carried over to next week
- Keep the two local P-087 follow-up modifications separate from merged code; track the exact baseline E-03532 guirnalda failure independently and do not add an allowlist entry. P-077 calibrates the default quote cap, P-075 retains historical tests to reproduce separately. Current evidence: [REQ-015 report](../../requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/REPORT.md).
