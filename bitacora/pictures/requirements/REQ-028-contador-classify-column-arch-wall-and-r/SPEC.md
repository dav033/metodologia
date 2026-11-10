---
id: REQ-028
status: ready
created: 2026-11-10
track: standard
---
# REQ-028 — Contador: classify column/arch/wall and return the formula count

## Problem & goal
Users say the balloon count (REQ-026) is inaccurate. For structures that can be computed (columns, arches, balloon walls) the
total follows from the construction, but today the automatic count is a statistical model over detector boxes
(`conteo_automatico.py`, commit `baaf77f2b`) that does not know the type. The AI type recognition and the geometric formulas
(`formulas-estructura.ts`, `identificar-estructura.ts`) were removed in `baaf77f2b` and exist only in history (`914e2b96a`).
Production errors on the 4 genuine corrections: -9 %, 0 %, -5 %, +24 % (classic arch 144 vs 116).

**Goal (first deliverable):** from one photo the system tells column / arch / wall (and the wall kind), applies the right
formula and returns the total, with no user interaction.

**Success looks like (owner-approved):** type correct in >= 95 % of the evaluation photos, and exact total on every photo the
gate accepts, measured on 3D renders with exact truth and on the labelled real photos. Photos the gate does not accept keep the
current statistical count unchanged.

## Users / actors / stakeholders
- Sempertex/Pictures users uploading a photo to the Contador (web, chat, Telegram, WhatsApp consumers of the same service).
- Owner (David): approves the plan and the acceptance numbers.

## Scope (in)
### US-1 (P1, Must) — Type recognition
As a user, I upload a photo and the system decides column, arch (incl. semi-arch), garland, or wall kind (single layer, duplet,
link/mesh, braided) or "not computable".
**Acceptance:** >= 95 % correct type on the labelled set; "not computable" is preferred over a wrong type.
### US-2 (P1, Must) — Formula applied and returned
As a user, I get the total from the construction formula for the recognised type, with how it was obtained
(`metodo: formula|regla`, units counted, k per cluster, toppers).
**Acceptance:** exact total on every accepted classic column/arch in 3D truth; walls use construction factor x visible and are
reported as `regla`; accepted photos are never worse than the current count on the production corrections.
### US-3 (P1, Must) — Safe fallback
When the gate is unsure, the existing count is returned unchanged, and the response says which path produced it.

## Out of scope
- Any correction UI (owner chose automatic only); per-balloon colours and sizes (separate lane, prototypes in
  `~/dev/pictures-infra/conteo/lab/at-color-tamano/REPORTE.md`); organic/free-form structures and figures.
- Training or replacing the detector.

## Requirements
- R1. The system shall classify each photo into one of: columna, arco, guirnalda, pared_una_capa, pared_duplas, pared_malla, pared_trenzas, no_computable.
- R2. If classification confidence is below the gate threshold, then the system shall return the current statistical count and flag `metodo: "estadistico"`.
- R3. When the type is column, arch or garland, the system shall count rings along the centreline and return rings x k + toppers.
- R4. When the type is a wall, the system shall return visible x the construction factor of that wall kind.
- R5. The response shall include type, method, units, k and a reason when it abstains, without changing the existing response fields consumers use.
- R6. Cluster size k defaults to 4 and is labelled as an assumption in the response (frontal photos cannot tell 4 from 5).
- R7. The AGENTS.md rules apply: runtime validation of the service payload, bounded time per photo, tests that do not need paid providers.

## UI / design contract
Not applicable (no UI change in this deliverable).

## Edge cases & errors
- Several pieces in one photo (columns + arch): sum per piece, only if every piece passes the gate; otherwise abstain.
- Photo < 480 px short side: abstain from the formula path (measured error range is too high).
- Partially hidden rings, toppers (balloon much larger on top), arches with one leg out of frame.
- Detector returns < 6 boxes in a piece: no formula.

## Constraints
- CPU only for the formula path; the detector stays as is (t2 + final boxes, `cajas_finales`).
- Python service owns the geometry (`scripts/conteo-vision`); TS owns the contract. One owner per rule; the removed TS formulas are not resurrected as a second copy.
- Evaluation sets: 3D renders (417, 51 classic), real labelled photos (web_train/web_dev/real_dev), 4 production classics. Never the reserved/test split for tuning.

## Priorities & phases
- M1 Measurement set: freeze labelled classic/wall set with types and truth, scoring script (no behaviour change).
- M2 Type classifier + gate, tuned on train, reported once on validation.
- M3 Formula path in the Python service + TS contract + fallback + tests.
- M4 Independent audit and evidence report; rollout behind a flag.

## Timeline & dependencies
- Depends on prototype in `~/dev/pictures-infra/conteo/lab/at-color-tamano/clasicos/` (45/51 exact on 3D, gate false accepts 43/366 3D and 30/255 real: the gate is the main risk).

## Assumptions
- "Pared simple" = all four wall kinds (owner answer); their totals are rule-based (visible x factor), so "exact" is judged on 3D truth where hidden balloons are known.
- Garland is included with column/arch because it uses the same ring method (assumed from the prototype).
- Rollout is behind a flag with the old count as fallback (production change only after owner OK on the report).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| UI / design direction | N/A |
| Priorities & phases | Covered |
| Timeline | Covered |

## Clarifications
### Round 1 — 2026-11-10
- Q: User flow of deliverable 1? → A: Automatic only (no correction UI).
- Q: What is a simple wall? → A: All walls (single layer, duplet, link, braided).
- Q: Acceptance? → A: type >= 95 % and exact total on what passes the gate.
