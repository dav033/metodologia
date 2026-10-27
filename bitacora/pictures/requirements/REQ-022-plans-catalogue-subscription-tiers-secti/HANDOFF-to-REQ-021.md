# Handoff: plans catalogue -> REQ-021 (owner decision 2026-10-27)

The owner decided the plans work belongs INSIDE REQ-021 as new subplan(s), not as a separate requirement.
REQ-022 is dropped; this folder is source material only (SPEC.md, PLAN.md, PLAN.json draft, rounds/round-01.json).
REQ-021's SPEC/PLAN are written by its dedicated Planner; nothing here was applied to REQ-021.

## What the owner asked (his words, Spanish)
- The side panel «Cada persona. Sus herramientas.» in the accounts screen (SP-2 `cuentas-admin@v1`) «no aporta nada» to
  users or administrators. It was removed from the SP-2 design (direction A, revision 12). SP-2 carries NO plan logic.
- Instead: a section to look at the plans. Four tiers:
  1. Free: «el asistente de decoración básico por chat, contador de globos y ya, con límites».
  2. Second tier: «20k pesos al mes / 7 dólares» (contents not stated).
  3. Designer: «chat extendido, calculadora de costos, detección de estructuras y detección de globos avanzado»; 45k pesos / 14 dólares.
  4. Designer Max: «todo lo anterior + el acceso al software de globos» (Taller 3D). Price not stated.
- «los requerimientos de los planes deben ser un nuevo subplan»: the plans section is a new subplan with its own UI design contract.

## Conflict to resolve in REQ-021
R16 and round 6 define THREE access plans as roles (Usuario · Plan 1/2/3). The owner's tiers are FOUR and priced.
How they map to roles/permissions is open (REQ-022 open question 3). Structure detection and advanced balloon detection are not
existing permissions.

## Draft already worked out (REQ-022 PLAN.md; reuse, do not trust blindly)
- SP-A «Plans section: view and compare the four plans (informative only)» with contract `planes@v1`, design task, visual review,
  integration test, audit; produces `plan-catalogue@1`. No buy/request action.
- Then: access by plan, Free limits, current plan marked and locked tools say which plan includes them.
- Conditional subplan (request or purchase) only if the owner answers so.
- Full text: PLAN.md next to this file; proposed requirements R1-R7 in its «Proposed requirements».

## Open questions for the owner (round-01.json has the 9 questions; not answered)
1 second tier contents + Free limits; 2 informative / request / purchase; 3 mapping to REQ-021 roles; 4 who sees it and where;
5 do the Designer tools exist; 6 pilot date (2026-11-16) or after; 7 Designer Max price; 8 are plans cumulative;
9 COP and USD together or by language.

## Owner answers (2026-10-27) — apply in REQ-021
1. Free plan is called «Entusiasta» (owner: «hagamos que el free sea entusiasta»). NO limits for now: no limit values, no limit UI, no «Free limits» subplan yet.
   Second tier (COP 20,000 / USD 7): name and contents STILL NOT GIVEN.
2. a — section is informative only; the administrator assigns the plan in the accounts screen. No request or purchase action.
3. Accounts of type Usuario can be on ANY of the four plans. Empleado interno and Administrador have access to everything for now.
   (So the four plans replace «Usuario · Plan 1/2/3»; staff roles are unchanged.)
4. a — public section (no sign-in), linked from the sign-in screen and from the account menu.
5. a — Designer lists «chat extendido», «detección de estructuras» and «detección de globos avanzado» as «aún no disponible»; each tool is built in its own requirement.
6. c — everything inside the pilot (2026-11-16), not only the informative section.
7. Designer Max: USD 25 / COP 70,000 per month.
8. Yes — plans are cumulative (second ⊃ Entusiasta, Designer ⊃ second, Designer Max ⊃ Designer).
9. Prices by language: Spanish shows COP, English shows USD.

Prices: second tier 20,000 COP / 7 USD; Designer 45,000 COP / 14 USD; Designer Max 70,000 COP / 25 USD.
Consequences to settle in REQ-021: SP-1 is CONFIRMED with roles Usuario · Plan 1/2/3 and tool permissions (R16, round 6, seed accounts plan1@/plan2@/plan3@);
SP-2's mockup also shows Plan 1/2/3. The Planner must decide how to reopen/amend them. The ready-made decorations explorer and the cost
calculator had been Plan 2 tools; where the new plans place the explorer is not stated.

## Owner correction (2026-10-27, later): plan names and second tier — SUPERSEDES the names above
Final four plans, cumulative, accounts of type Usuario are on exactly one of them:
1. **Entusiasta** (free): basic decoration assistant by chat (with limits, values not defined yet), basic balloon counter.
2. **Designer** (COP 20,000 / USD 7): the chat with HIGHER limits (less limited than Entusiasta; numbers unknown, decided later) + the basic balloon counter.
3. **Designer Plus** (COP 45,000 / USD 14): extended chat, cost calculator, structure detection, advanced balloon detection (the last three tools «aún no disponible» for now).
4. **Master Designer** (COP 70,000 / USD 25): everything above + access to the balloon software (Taller 3D).
Open: where the ready-made decorations explorer (old Plan 2 tool) lives; numeric chat limits (owner: later).
