---
id: REQ-015
status: done (local branch awaiting owner review)
created: 2026-10-13
track: standard
---
# REQ-015 — judge-fix: guided chat honesty and count/price parity (D1-D5, D8)

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The product judge (research/juez/JUEZ-ASISTENTE-2026-10-11.md, 7/10) found that the guided chat /asistente contradicts itself:
the idea card says 101/102 balloons while plan and quote say 115, the colour-swap banner claims «lo demás quedó igual» while three other colours
lost balloons, canned chips cost a paid model turn, and a direct question is ignored. The fix task (e7x) lived only on the lost clone, so it is redone here from the report.

**Success looks like:** for the judge's 2 journeys the idea card, plan card and quote show the same balloon count and price; the edit banner prints the real diff; canned chips and count questions cost 0 model calls.

## Users / actors / stakeholders
-

## Scope (in)
### US-1 (P1) — Count parity D2
Card «Tu elección» shows the engine's count (or labels it approximate).
### US-2 (P1) — Price on idea and plan cards D3
Use the single pricer (cotizarBom, D-038).
### US-3 (P1) — Honest colour-swap banner D4
Print the real per-colour diff, or keep other colours fixed.
### US-4 (P2) — Deterministic chips and quote requests D5
No model turn for «Cuánto cuesta» or use choice.
### US-5 (P2) — Direct count, size and colour questions D1
Answer questions by rule.
### US-6 (P3) — Rating row D8
One collapsed rating row with targets ≥40 px.
<!--
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
- D6 theme coverage (NC-2), D7 compare two ideas (CUS-21), paid runs, push/deploy/migrations.

## Requirements
- R1. When an idea is chosen, the card shall show the engine's balloon total or clearly label its source count approximate and state that the final plan recalculates it (the already accepted US-1/T1 exception).
- R2. When the plan or idea card renders, it shall show «Materiales desde $X» from cotizarBom, equal to the quote after «Cuánto cuesta».
- R3. When a colour swap changes other colours' counts, the banner shall list the real before/after counts and price change; it shall never say «igual» if any count moved.
- R4. When the customer taps a canned chip, the system shall answer by rules without a model call.
- R5. When the customer asks balloons/size/colour of the chosen idea or plan, the server or view shall answer by rule.
- R6. The rating row shall not sit above actionable chips; tap targets ≥ 40 px.
<!-- EARS style, numbered so tests/plan can cite them:
- R1. When <trigger>, the system shall <response>.
- R2. If <unwanted condition>, then the system shall <response>.
- R3. While <state>, the system shall <response>.
For business processes, "the system" can be a role or the process ("the approver shall…"). -->

## Edge cases & errors
-

## Constraints
Repo AGENTS.md rules; no paid AI calls; every behaviour change has a test that fails without it; no push/merge/migration; antagonist review before each commit; customer text in Spanish without engine terms.

## Priorities & phases
MVP = US-1..US-3; then US-4, US-5; US-6 last.

## Timeline & dependencies
-

## Assumptions
- Owner away; plan self-approved under the autonomy given in the /loop request (D-041: all development from this laptop). Origin of 101 vs 115 not yet verified; M1 starts by measuring it.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Missing |
| Users / actors | Missing |
| Scope | Missing |
| Out of scope | Missing |
| Flows & behavior | Missing |
| Edge cases | Missing |
| Acceptance criteria | Missing |
| Constraints | Missing |
| Priorities & phases | Missing |
| Timeline | Missing |

## Clarifications
- 2026-10-13: local implementation and verification complete, PLAN.md done and REPORT.md ready. Spec remains in-progress until owner review/integration/publication; no push or merge authorized.
- 2026-10-13 close-out: normalized US headings for trace tooling and made R1's wording reflect the approximation exception already approved in US-1/T1; no new scope or acceptance change.
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
