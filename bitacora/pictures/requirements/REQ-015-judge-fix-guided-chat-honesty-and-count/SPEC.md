---
id: REQ-015
status: in-progress
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
- US-1 (P1) count parity D2: card «Tu elección» shows the engine's count (or labels it approximate).
- US-2 (P1) price on idea and plan card D3 via the single pricer (cotizarBom, D-038).
- US-3 (P1) honest colour-swap banner D4: print the real per-colour diff, or keep other colours fixed.
- US-4 (P2) deterministic chips/quote request D5: no model turn for «Cuánto cuesta», use choice.
- US-5 (P2) answer count/size/colour questions by rule D1.
- US-6 (P3) one collapsed rating row, ≥40 px targets D8.
<!--
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
- D6 theme coverage (NC-2), D7 compare two ideas (CUS-21), paid runs, push/deploy/migrations.

## Requirements
- R1. When an idea is chosen, the card shall show the same balloon total as the plan the engine builds for it.
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
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
