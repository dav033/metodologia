---
req: REQ-028
status: awaiting-approval
created: 2026-11-10
---
# Plan — REQ-028 — Contador: classify column/arch/wall and return the formula count

## Approach
Build the formula path in the Python service (`scripts/conteo-vision`), where the geometry prototype already lives, behind a
precision-first gate: classify the photo from detector boxes only (ring/grid structure features), count rings or apply the wall
factor when the gate accepts, otherwise return the current statistical count. The TS side only carries the contract and the
flag. Alternative rejected: resurrecting `formulas-estructura.ts` in TS (second owner of the rule, height/diameter estimate
that the investigation showed to be wrong) and an AI type recogniser (removed in `baaf77f2b` because it lost).

## Global constraints
- Precision first: abstain rather than return a wrong formula total (R2). Fallback = today's count, unchanged.
- No tuning on reserved/test splits; report once on validation. One owner per rule (Python). No new `any`/unchecked casts.
- No production change without owner OK on the M4 report; rollout behind a flag. Do not touch other sessions' uncommitted work (`src/lib/rag/*`).

## Tasks
- [ ] T1 — Freeze the labelled evaluation set (types + exact truth for 3D, labelled real/production photos, walls) and the scoring script · kind: implement · repo: pictures-infra · files: ~/dev/pictures-infra/conteo/lab/at-color-tamano/clasicos/ · verify: `python medir.py` · covers: R1, US-1
- [ ] T2 — Type classifier (column/arch/garland/wall kinds/no_computable) from boxes, tuned on train, reported once on val · kind: implement · level: architecture · after: T1 · verify: type accuracy >= 95 % on val · covers: R1, R2, US-1
- [ ] T3 — Precision gate: drive false accepts to ~0 on non-classic 3D and real photos; small-photo abstention · kind: implement · level: architecture · after: T2 · verify: false accepts reported per set · covers: R2, US-3
- [ ] T4 — Ring count for column/arch/garland and wall factor for walls, as importable Python module with tests · kind: implement · after: T2 · files: scripts/conteo-vision/ · verify: `uv run pytest` in scripts/conteo-vision · covers: R3, R4, R6, US-2
- [ ] T5 — Wire into the service response (type, method, units, k, abstain reason) and the TS contract schema with runtime validation, flag-gated, fallback unchanged · kind: implement · after: T3, T4 · files: scripts/conteo-vision/servicio_yolo.py, src/lib/contador/ · verify: `npm run lint && npx tsc --noEmit` and affected contador tests · covers: R2, R5, R7, US-3
- [ ] T6 — Independent audit (spec + standards) and evidence report with the numbers vs today's count on the production corrections · kind: audit · after: T5 · verify: report in REQ-028 REPORT.md · covers: US-1, US-2, US-3
<!-- Small, verifiable steps (one session each), in dependency order. Mark parallelizable ones with ∥.
- [ ] T1 — Author UI contract <contract>@v1 · kind: design · subplan: <id> · files: design/contracts/<contract>@v1.md · verify: <contract review> · covers: R1
- [ ] T2 — Implement UI behavior · kind: implement · subplan: <id> · ui: true · after: T1 · files: <paths> · verify: `<command>` · covers: R2, US-1
- [ ] T3 — Review rendered UI against <contract>@v1 · kind: audit · subplan: <id> · review_axis: visual · after: T2 · verify: <visual evidence review> · covers: R3
- [ ] T4 — <what> · kind: implement · repo: backend · verify: `npm test -- orders` · covers: R4
- [ ] T5 — <hard design problem> · level: architecture · after: T1 · verify: `<command>` · covers: R5
Plans for the scheduler also carry a classified `PLAN.json` (references/plan-contract.md): `bitacora.py plan-json init|check REQ-NNN`.
The scheduler (via `PLAN.json`) reads these lines: repo:, after: (task ids), verify: and level: are optional; verify is run by the
verifier only when it is a command inside backticks; level: architecture marks a hard task for the router (it picks the
model and effort). `kind: design` routes to Designer; every UI subplan declares its contract, version, design task and visual-review task.
Every `ui: true` task depends on the design task and reads the owner-approved contract. Owner approval is a run-time gate
between design and UI implementation, performed with `bitacora.py design approve|changes REQ-NNN <contract>@vN` or the web
requirement page; it is separate from plan approval. Keep each task to one session of work. -->

## Verification
Score the final pipeline on the frozen set: type accuracy >= 95 %, exact total on every gate-accepted classic piece, false-accept
count per set, and photo-by-photo comparison with today's count on the 4 production classics; run the Python and TS checks above.
Milestones: M1 = T1, M2 = T2+T3, M3 = T4+T5, M4 = T6, each closed by an independent audit.

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
