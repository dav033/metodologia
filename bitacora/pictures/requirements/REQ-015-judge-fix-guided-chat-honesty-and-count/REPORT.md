# REQ-015 — local close-out

## Built

The guided assistant now preserves the selected idea's quote and answers its price/learning chips by rules, including when another plan remains open. Explicit rule requests exclude unrelated plan/proposal context without relaxing the v1 server contract. Retrying preserves the original messages; reload reuses an identifiable saved quote instead of repricing with a changed engine flag.

T12 uses the existing durable global counter (`costeo_idea_hora`, default 300/hour, configurable through `COSTEO_IDEA_TOPE_HORA`). Exhaustion prevents costing and quote audit rows and returns an SSE 200 rule answer. D-044 permits the same bounded per-instance fallback during database outages. Interrupted requests refund only their original counter/window.

The audit also found a global 3D color-swap count defect across round and Link-O-Loon products. The new real-engine regression reproduced a message reporting 128 blue balloons and incorrectly treating another 81 as a separate color; family-level matching now reports all 209.

## Verification evidence

| Check | Result |
| --- | --- |
| Workspace package build | PASS, exit 0 |
| Full ESLint | PASS, exit 0; 49 warnings, no errors |
| T12 cap + action tests | PASS, no external provider/database |
| T13 selected-idea + restored-price tests | PASS; targeted ESLint clean |
| Mixed-format 3D regression | Expected assertion failure before source fix; PASS after |
| `npx tsc --noEmit` | PASS after stale generated development types were moved to a recoverable backup |
| Application `npm run build` | PASS; 83/83 routes prerendered |
| Final `npm run gate` | PASS, exit 0, GATE OK; all 10 suites including the 405-scene golden |
| Additional contract/rating tests and final snapshot checks | In progress; not yet claimed passing |
| Independent audit #3, specification and standards axes | Initial findings fixed; targeted re-reviews approve |
| Trace lint for REQ-015 and its decisions | No uncovered/unknown/dangling findings; unrelated historical trace warnings remain |

Full check logs: `/tmp/pictures-checks-8fTm18/`. The obsolete `.next/dev/types` files referenced removed LoRA/catalogue snapshot routes; no source typing or check was weakened. Backup: `/tmp/pictures-stale-dev-types-Ac1paX/types`.

## Rulings

- The accepted US-1/T1 exception remains: source idea counts are marked approximate with a final-plan recalculation notice. This is not a claim that every preview count is already exact.
- A restored combined/ambiguous plan does not supply an individual idea price. Its card shows “Precio al elegir”; its plan quote remains available. No new persisted fields were added under D-035.
- D-044's actual wording permits bounded memory fallback; the preceding session's “fail closed” summary was inaccurate.
- The owner's “procede” authorizes completing local implementation and verification. No new commit, push, merge, deployment, paid call or production migration was performed.

## Needs your eyes

Review `src/lib/guiada-motor/tope-costeo-idea.ts` and `costear-idea-elegida.ts` for the hourly quote policy, and `src/components/guiado/opcion-idea.ts` / `precio-idea-elegida.ts` for how idea requests and restored prices are bound to their context.

## Proposals

1. Add a mounted React journey test for selected idea B with plan A, interruption/retry and reload. Current evidence combines pure behavior tests, real server/engine tests, wiring assertions and independent static review.

## Pending

- Final snapshot verification and additional contract/rating checks are still running; the full gate passed.
- P-077: calibrate the default 300/hour quote cap from production counts; no production queries were run.
- Historical P-075 test debt is separate; the old 180-type-error claim no longer describes this local tree.
- No live paid dinosaur/XV journey or browser walkthrough was executed; representative quote parity is checked by fixtures, not a newly measured production price.
- The feature branch retains its existing 21 commits. This session's integration/corrections remain uncommitted; the original t12 draft worktree is preserved.

## Walkthrough

`elegirOpcion` routes price/learning chips to the chosen idea's exact plan or the current matching plan. When no saved exact plan is available, `estadoDelTurnoDeIdea` preserves the selected ID and explicit rule intent while removing unrelated plan/scope fields. The server validates the unchanged contract and calls `responderAccionIdea`; costing uses the shared application function and hourly cap before calling the pricer or writing its audit row. Quote responses update the idea card and invalidate a superseded cached result. Reload uses the persisted identifiable quote and avoids a fresh engine choice. For 3D family swaps, the confirmation counts all store products belonging to the new color in the affected pieces.
