---
req: REQ-021
status: draft
created: 2026-10-26
---
# Plan — Pilot release: accounts and access plans, saved work, AI spend, Taller essentials, English, modules and chat

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: draft · ejecución: paused · hitos 0/5 · tareas 29/92 · generado: 2026-10-28T17:13:37-05:00

**M1 — Accounts, access plans and the plans section** · dificultad alta · 18/29

**SP-1 — Accounts, sessions and server-side permissions**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1.1 | Accounts schema: migration 037 and the isolated test-schema helper | media | completada | gpt-6-luna | codex-1 | 2 |
| T1.2 | Permission catalogue, the plan catalogue, the six system roles and the route permission map | media | completada | gpt-6-luna | codex-2 | 1 |
| T1.3 | Account service: invitations, activation, sign-in with lockout, reset links, roles and the one-time commands | alta | completada | gpt-6-luna | codex-luis | 2 |
| T1.4 | Server sessions and the permission guard in the proxy and the sign-in API, replacing APP_PASSWORD | alta | completada | gpt-6-luna | codex-2 | 1 |
| T1.5 | Local no-restrictions mode that refuses to start outside next dev on loopback | media | completada | gpt-6-luna | codex-1 | 3 |
| T1.6 | Apply the permission guard to every API handler and move the existing suites to a shared test session | baja | completada | gpt-6-luna | codex-luis | 1 |
| T1.7 | End-to-end check of accounts and permissions on a production build, and the SP-1 suites in CI | media | completada | gpt-6-luna | codex-2 | 6 |
| T1.8 | SP-1 security audit: accounts, sessions, permissions, local mode and the one-time commands | alta | completada | gpt-6.1-sol | codex-luis | 12 |
| T1.8b | Cross-check audit of T1.8: SP-1 security audit: accounts, sessions, permissions, local mode and the one-time commands | alta | completada | gpt-6.1-sol | codex-luis | 1 |
| T1.9 | Remediate T1.8 findings F1, F2, F3, F4 | media | completada | gpt-6-luna | codex-2 | 1 |
| T1.10 | Remediate T1.8 findings F6 | alta | completada | gpt-6-luna | codex-2 | 3 |
| T1.11 | Remediate T1.8 findings F16, F17 | media | completada | gpt-6-luna | codex-2 | 2 |
| T1.12 | Remediate T1.8 findings F19, F20 | media | completada | gpt-6-luna | codex-luis | 1 |

**SP-2 — Sign-in, invitation and administration screens**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T2.1 | Copy the owner-approved cuentas-admin@v1 contract into the repository | baja | completada | gpt-6.1-sol | codex-2 | 2 |
| T2.2 | Account APIs: activation, reset, notice acceptance, own password and the administration of accounts and roles | media | completada | gpt-6-luna | codex-1 | 4 |
| T2.3 | Sign-in, invitation activation, password reset and notice re-acceptance screens | media | completada | gpt-6-luna | codex-1 | 3 |
| T2.4 | Account menu on every signed-in page and the Mi cuenta page | media | completada | gpt-6-luna | codex-2 | 2 |
| T2.5 | Administration screens: accounts list, invitations, account actions and the role editor | media | completada | gpt-6-luna | codex-luis | 2 |
| T2.6 | Browser end-to-end: invite, activate, sign in and change plan on a production build | media | bloqueada | gpt-6-luna | codex-luis | 24 |
| T2.7 | SP-2 visual review against the cuentas-admin@v1 contract | media | pendiente | — | — | 0 |
| T2.8 | SP-2 audit: account screens, administration APIs and the data notice | media | pendiente | — | — | 0 |

**SP-14 — Plans section: the four access plans, public and informative**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T14.1 | Copy the owner-approved planes@v1 contract into the repository | baja | pendiente | — | — | 0 |
| T14.2 | Public plans page: the four plans from the plan catalogue, prices by language | media | pendiente | — | — | 0 |
| T14.3 | Plans links on the sign-in screen and in the account menu | baja | pendiente | — | — | 0 |
| T14.4 | Browser end-to-end of the plans section on a production build | media | pendiente | — | — | 0 |
| T14.5 | SP-14 visual review against the planes@v1 contract | media | pendiente | — | — | 0 |
| T14.6 | SP-14 audit: catalogue use, public route and copy | media | pendiente | — | — | 0 |

**Sin subplan**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T91 | M1 composition check: first administrator to an Entusiasta user on the integrated tree | media | pendiente | — | — | 0 |
| T94 | Composition check CG-4: access plans from the plans section to the accounts screen | media | pendiente | — | — | 0 |

**M2 — Saved work, Taller essentials, spend per user and the chat tools** · dificultad alta · 11/54

**SP-3 — Taller essentials: researched and modelled Backing and table types, type cards and every-type Blender export**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T3.1 | Repair what blocks T3.8 | alta | completada | gpt-6-luna | codex-2 | 1 |
| T3.14 | Repair what blocks T3.8 | baja | completada | gpt-6-luna | codex-2 | 1 |
| T3.2 | Research new Backing structures and table types, write the validated proposal and get the owner's approval | media | completada | gpt-6-luna | codex-luis | 2 |
| T3.3 | Make the table, piece and Backing registries exhaustive and add the Backing extension points | alta | completada | gpt-6-luna | codex-2 | 1 |
| T3.4 | Record the owner-approved list of new Backings and table types in the repository | baja | completada | gemini-3.8-flash-low | antigravity | 6 |
| T3.5 | Model the approved new table types in the parametric table generator | alta | completada | gpt-6-luna | codex-luis | 1 |
| T3.6 | Model the approved new Backing structures as parametric Taller furniture | alta | completada | gpt-6-luna | codex-luis | 1 |
| T3.7 | Teach photo reading the approved new Backing structures | media | completada | gpt-6-luna | codex-luis | 1 |
| T3.8 | Checkpoint: run the registry and modelling suites before Taller UI and export work | baja | completada | gpt-6-luna | codex-2 | 5 |
| T3.9 | One creation card per table type in Fondos y muebles | media | completada | gpt-6-luna | codex-2 | 1 |
| T3.10 | Backing group in Fondos y muebles with the seven existing and the new Backing props | baja | completada | sonnet | claude-luis | 1 |
| T3.11 | Verify and repair the GLB export of every scene element type | alta | lista | gpt-6-luna | codex-2 | 2 |
| T3.12 | Implement the Taller browser and Blender verification harness for every element type | alta | pendiente | — | — | 0 |
| T3.13 | Run the real Taller essentials integration scenario | media | pendiente | — | — | 0 |
| T3.15 | Audit Taller essentials and export compatibility | media | pendiente | — | — | 0 |

**SP-4 — Saved projects**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T4.1 | Copy the approved saved-projects design contract | baja | pendiente | — | — | 0 |
| T4.2 | Implement versioned project storage and scene validation | alta | pendiente | — | — | 0 |
| T4.3 | Implement project APIs with per-resource authorization | alta | pendiente | — | — | 0 |
| T4.4 | Implement the project list and conflict-safe Taller saving | alta | pendiente | — | — | 0 |
| T4.5 | Implement a lossless and idempotent legacy-scene import | alta | pendiente | — | — | 0 |
| T4.6 | Implement the multi-browser saved-project integration harness | alta | pendiente | — | — | 0 |
| T4.7 | Run the cross-browser project and import integration scenario | media | pendiente | — | — | 0 |
| T4.8 | Review the rendered project and import interfaces | media | pendiente | — | — | 0 |
| T4.9 | Audit project isolation, concurrency and import preservation | media | pendiente | — | — | 0 |
| T4.31 | Run the project storage and authorization checkpoint | media | pendiente | — | — | 0 |

**SP-5 — Saved decorations**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T5.1 | Copy the approved personal-decoration library UI contract | baja | pendiente | — | — | 0 |
| T5.2 | Add account-owned validated storage and protected personal-decoration API | alta | pendiente | — | — | 0 |
| T5.3 | Connect Taller save, place and idempotent browser-library import flows | alta | pendiente | — | — | 0 |
| T5.4 | Verify cross-browser persistence, placement and ownership isolation | alta | pendiente | — | — | 0 |
| T5.5 | Review the rendered personal-library UI against its contract | media | pendiente | — | — | 0 |
| T5.6 | Audit personal-decoration ownership and import recovery | media | pendiente | — | — | 0 |

**SP-6 — AI spend per user and session**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T6.1 | Pin the approved AI-spend UI contract | baja | pendiente | — | — | 0 |
| T6.2 | Define durable AI usage storage and ai-usage@1 | alta | pendiente | — | — | 0 |
| T6.3 | Attribute usage at every paid Next and ai-api model call | alta | pendiente | — | — | 0 |
| T6.4 | Build the staff spend dashboard and server-filtered API | alta | pendiente | — | — | 0 |
| T6.5 | Run real-entrypoint usage attribution and authorization checks | alta | pendiente | — | — | 0 |
| T6.6 | Review the rendered spend dashboard against gasto-ia@v1 | media | pendiente | — | — | 0 |
| T6.7 | Audit AI spend completeness, identity and data minimization | media | pendiente | — | — | 0 |

**SP-7 — Assisted chat as three tools and the decorations explorer**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T7.1 | Copy the owner-approved herramientas-chat@v1 contract into the repository | baja | pendiente | — | — | 0 |
| T7.2 | Tool catalogue, server-side price gating of the guided chat and per-tool spend tags | alta | pendiente | — | — | 0 |
| T7.3 | Balloon counter API by form, phrase or photo on the existing counting engines | media | pendiente | — | — | 0 |
| T7.4 | Checkpoint: tool gating, counter API and spend tags on a running server | media | pendiente | — | — | 0 |
| T7.5 | Tool home page at / and retirement of the classic chat page | media | pendiente | — | — | 0 |
| T7.6 | Balloon counter page: form, phrase and photo with a price-free result | media | pendiente | — | — | 0 |
| T7.7 | Cost calculator page from the existing professional quote, fed by the counter or by hand | media | pendiente | — | — | 0 |
| T7.8 | Ready-made decorations gallery in the Taller with an open-as-new-project link | media | pendiente | — | — | 0 |
| T7.9 | Browser end-to-end of the three tools and the gallery on a production build | media | pendiente | — | — | 0 |
| T7.10 | SP-7 visual review against the herramientas-chat@v1 contract | media | pendiente | — | — | 0 |
| T7.11 | SP-7 audit: tool gating, price leaks, counting sources and spend tags | media | pendiente | — | — | 0 |

**Sin subplan**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T92 | Composition check CG-2: accounts, plans section and Taller essentials | media | pendiente | — | — | 0 |
| T93 | Composition check CG-3: accounts and saved projects | media | pendiente | — | — | 0 |
| T95 | Composition check CG-5: saved decorations on the integrated candidate | media | pendiente | — | — | 0 |
| T96 | Composition check CG-6: AI spend per account on the integrated candidate | media | pendiente | — | — | 0 |
| T97 | Composition check CG-7: chat tools and gallery on the integrated candidate | media | pendiente | — | — | 0 |

**M3 — English / Spanish** · dificultad media · 0/9

**SP-8 — Language switch, Taller 3D and navigation in English**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T8.1 | Language mechanism: detection order, typed bilingual dictionaries and the saved choice | media | pendiente | — | — | 0 |
| T8.2 | Language switch and English for navigation, account screens, the plans page and the data notice | media | pendiente | — | — | 0 |
| T8.3 | Coverage guard that finds Spanish literals outside the text dictionaries | media | pendiente | — | — | 0 |
| T8.4 | Taller in English, part 1: shell, library, add panels, menus, help and export | baja | pendiente | — | — | 0 |
| T8.5 | Taller in English, part 2: inspector, editors, panels, shopping list and assembly sheet | baja | pendiente | — | — | 0 |
| T8.6 | Taller in English, part 3: AI panel and the user-facing sentences built in lib | media | pendiente | — | — | 0 |
| T8.7 | Browser end-to-end: English first visit, saved choice, no Spanish left and text that fits | media | pendiente | — | — | 0 |
| T8.8 | SP-8 audit: language detection, saved choice, coverage and unchanged Spanish | media | pendiente | — | — | 0 |

**Sin subplan**

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T98 | Composition check CG-8: English across accounts, saved projects, tools and the Taller | media | pendiente | — | — | 0 |

**M4 — Editable modules and chat → 3D** · dificultad — · 0/0

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|

**M5 — Pilot release** · dificultad — · 0/0

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
- Contrato de diseño SP-2: `cuentas-admin@v1` · aprobación aprobado
- Contrato de diseño SP-14: `planes@v1` · aprobación aprobado
- Contrato de diseño SP-4: `proyectos@v1` · aprobación pendiente
- Contrato de diseño SP-5: `decoraciones@v1` · aprobación pendiente
- Contrato de diseño SP-6: `gasto-ia@v1` · aprobación pendiente
- Contrato de diseño SP-7: `herramientas-chat@v1` · aprobación pendiente
- Contrato de diseño SP-9: `textos-producto@v1` · aprobación pendiente
- Contrato de diseño SP-10: `idioma-resto@v1` · aprobación pendiente
- Contrato de diseño SP-11: `modulos-editables@v1` · aprobación pendiente
- Contrato de diseño SP-12: `chat-a-3d@v1` · aprobación pendiente
<!-- bitacora:status:end -->

Skeleton (collaborative planning, phase Esqueleto). Milestones and subplans only; tasks are defined subplan by subplan
with the owner.

## Approach
Code base: origin/main `a9f3d6e5` of `dav033/pictures` (Next 16 on Vercel, Python ai-api on the VPS, Neon Postgres with
`scripts/migrations/NNN_*.sql` applied by `npm run rag:migrate`). Work branches from origin/main in new worktrees;
`~/dev/pictures` is never used.

**Order backwards from the pilot (2026-11-16).** Accounts come first because saved projects, saved decorations, spend
per user, the access plans and the per-account language all need a signed-in user. The Taller items that do not need
accounts (rectangular tables, Backing, Blender export, editable modules) run in parallel from day one. Language runs
from its own foundation in parallel and is the first to be cut.

| Milestone | Target | Never cut? | Cut date (owner, round 4) |
|---|---|---|---|
| M1 — Accounts, access plans and the plans section | 2026-11-01 | yes (SP-14 too: owner 2026-10-27) | — |
| M2 — Saved work, Taller essentials, spend per user and the chat tools | 2026-11-07 (SP-3 at risk, must land before 2026-11-16) | yes | — |
| M3 — English / Spanish | 2026-11-09 | no (cut 1) | 2026-11-09: only SP-8 (Taller 3D and navigation) ships |
| M4 — Editable modules and chat → 3D | 2026-11-12 | no (cuts 2 and 3) | 2026-11-11 modules out; 2026-11-12 chat beyond split and reliability out |
| M5 — Pilot release | 2026-11-16 | yes | — |

**Dependencies.** SP-1 (accounts, plan catalogue) → SP-2, SP-4, SP-5, SP-6, SP-7, SP-8, SP-14; SP-14 (plans section) also
waits for the M1 composition check CG-1 because it adds links to SP-2's sign-in screen and account menu. SP-4 (project identity) → SP-6 and SP-12.
SP-6 (spend tagging) → SP-7. SP-8 (language mechanism) → SP-9, SP-10. SP-7 (chat tools, decorations explorer) →
SP-10, SP-12. SP-3 follows SP-1's audit (its harness signs in) and SP-4 follows T3.3, which defines taller-scene@1. SP-11 depends on nothing. SP-13 consumes every shipped subplan.

**Fit, said plainly.** Rough size: about 70 tasks for the whole SPEC, about 45 for the never-cut part (SP-1 to SP-7 and
SP-13). Agent time is not the limit; waits are: retries, usage limits and the owner's per-subplan test (under 24 h,
D-131). It fits only if the scheduler runs two or more subplans at once and retries stay low. If M1 slips past
2026-11-03, the cut dates above apply as agreed; never-cut work is never traded for language, modules or chat→3D.

**Security.** SP-1 (identity, sessions, permissions, server-side enforcement, local flag, first administrator) is its
own subplan with its own audit; SP-4 audits that a usuario can only reach their own projects.

Out of this plan: 3D space, Illustrator/vector export, AI spend caps (D-072), plan purchase or request, chat-limit
values and their enforcement.

**Re-scope of SP-3 (2026-10-27, owner correction).** The owner: «el plan no es para agregar la funcionalidad, la
funcionalidad ya está», and SP-3 must «investigar Backings, modelarlos e ingresarlos al sistema, y lo mismo con las mesas:
añadir más tipos de mesas»; the GLB export must cover the whole scene. SP-3 now researches and gets the owner's approval of
new Backing structures and table types, models and integrates them, adds the type cards and the Backing group, and verifies
the export of every element type (details and schedule risk under SP-3). SP-4 keeps its scope; its brief now separates the
existing local autosave, status text and scene name from what is new.

**Milestone move (2026-10-27, owner answer B).** SP-3 moves from M1 to M2 so M1 (SP-1, SP-2, SP-14) integrates and ships
without the Backing and table modelling; SP-3 still lands before the pilot (2026-11-16). This supersedes the gate rows of
the A-1 table below.

| Where | Before | After |
|---|---|---|
| Milestones | M1 «Accounts, access plans and Taller essentials» with SP-3 | M1 «Accounts, access plans and the plans section» (SP-1, SP-2, SP-14); M2 «Saved work, Taller essentials, spend per user and the chat tools» adds SP-3 |
| Gate chain | CG-1 → CG-2 [SP-1, SP-2, SP-3] → CG-4 [+SP-14] → CG-3 [+SP-4] | CG-1 [SP-1, SP-2] → CG-4 [SP-1, SP-2, SP-14] (closes M1, T94 after T14.6, which follows T91) → CG-2 [+SP-3] (M2, T92 after T94, T3.15) → CG-3 [+SP-4] (T93 after T92, T4.9) → CG-5 [+SP-5] (T95 after T93, T5.6) → CG-6 [+SP-6] (T96 after T95, T6.7) |
| SP-4 start | T4.1 after T92 (SP-3's audit) | T4.1 after T94 and T3.3 (taller-scene@1 consumed as a contract) |
| SP-3 tasks | T3.1–T3.13 | T3.2–T3.13 and T3.15: research and approval record split (T3.2, T3.4), registries first (T3.3), existing card/group patterns in Taller UI tasks, every-type GLB (T3.11) separate from the Blender harness (T3.12); no design contract or visual review |

**Amendment A-1 (2026-10-27, owner round 10): four access plans and the plans section.** The owner replaced the three
access plans of rounds 4 and 6 (Usuario · Plan 1/2/3) with four cumulative, priced plans for Usuario accounts:
Entusiasta (free), Designer (COP 20,000 / USD 7), Designer Plus (COP 45,000 / USD 14) and Master Designer (COP 70,000 /
USD 25), plus a public, informative plans section (SPEC R16 amended, R17–R20, Clarifications round 10). What changed,
so nothing is rewritten silently:

| Where | Before | After | Owner action |
|---|---|---|---|
| SP-1 outcome, T1.1, T1.2, T1.3, T1.7, SPEC Pruebas SP-1 | three plan roles, «five system roles», seed plan1@/plan2@/plan3@, checks with Plan 1/Plan 3 | four plan roles from the plan catalogue, «six system roles», seed entusiasta@/designer@/designer-plus@/master-designer@, checks with Entusiasta/Designer Plus/Master Designer | SP-1 was confirmed 2026-10-26; the change reopens it (`planning status` shows `changed`): **re-confirm SP-1** (its inputs were answered 2026-10-27) |
| T1.2 | permission catalogue, roles, route map (90 min) | + plan catalogue `src/lib/planes/catalogo.ts`, contract `plan-catalogue@1`, check `planes:test-catalogo` (120 min) | part of SP-1 re-confirmation |
| SP-2 (cuentas-admin@v1) | T2.5 «five system roles», T2.6 «Plan 2 person … moves them to Plan 3», mockup shows Plan 1/2/3 | **amendment A-2, applied 2026-10-27**: «six system roles» named; T2.5 role picker reads the four plans from plan-catalogue@1 (SP-2 consumes it, covers R17); T2.6 invites a Designer Plus person and moves them to Master Designer; the contract and mockup must show the four plan names | the chosen design (direction A, r13) is amended, not redone: run `design amend` for cuentas-admin@v1, then confirm SP-2 |
| SP-7, SP-8 outcomes | explorer gated by «its access plan»; language mechanism | tools gated by the catalogue's plans; the explorer, like all of the Taller 3D, only in Master Designer and the staff roles (owner 2026-10-27); SP-8 moves the plans section and data notice to the language mechanism | none now (no tasks yet) |
| New SP-14, CG-4 (T94) | — | public plans section `planes@v1`, cumulative gate CG-4 [SP-1, SP-2, SP-3, SP-14] | define and confirm SP-14 when in focus |
| CG-1 (T91), CG-2 (T92), CG-3 (T93) | Plan 1 / Plan 3 personas; CG-3 [SP-1..SP-4] after T92 | Entusiasta / Master Designer personas; CG-3 [SP-1, SP-2, SP-3, SP-14, SP-4] after T94 | none (gate tasks) |
| SP-3, SP-4 | no `ui_brief` | `ui_brief` written (owner request 2026-10-27); their drafts become stale and are redrafted from it | none beyond the normal design choice |

Why the plan catalogue lives in SP-1 and not in SP-14: SP-1's roles need it first, and SP-14 needs SP-2's screens, so a
catalogue owned by SP-14 would create the cycle SP-14 → SP-1 → SP-2 → SP-14. SP-14 consumes it.

### M1 — Accounts, access plans and the plans section
Real people sign in with their own invited account and each one reaches exactly what their role or access plan allows; the shared APP_PASSWORD no longer opens the app; anyone can compare the four access plans in the public plans section.

- **SP-1 — Accounts, sessions and server-side permissions**: Invited accounts with hashed passwords and revocable server sessions replace the shared APP_PASSWORD; every page and API of the pilot checks the permission it needs on the server; roles and the four access plans of Usuario accounts (Entusiasta, Designer, Designer Plus, Master Designer) are sets of permissions read from one plan catalogue; the local no-restrictions flag cannot be enabled in production; the first administrator is created by a one-off command. Covers R1, R2, R3, R16, R17.

<!-- SP-1 tasks -->

  SP-1 tasks (confirmed 2026-10-26, **reopened by amendment A-1 on 2026-10-27**: re-confirm). Owner rulings, rounds 5–6 and 10: access plans are roles — round 10 replaces round 6's Usuario · Plan 1/2/3 with Usuario · Entusiasta, Usuario · Designer, Usuario · Designer Plus and Usuario · Master Designer, plus Empleado interno and Administrador; one role per account; permissions as in SPEC Clarifications round 6; session 30 days; password at least 8 characters; 5 failures per email in 15 min lock it 15 min; invitation link 7 days, reset link 24 h, both copied by the administrator (no email service); `AUTH_LOCAL_SIN_RESTRICCIONES=1` only under `next dev` on loopback; first production administrator by a one-time command the owner runs himself.
  Planner rulings (revisable at confirmation): an account «of type Usuario» is one whose role is one of the four plan roles; custom roles stay possible (round 6) but are not plans and never appear in the plans section; «Empleado interno and Administrador have access to everything for now» (round 10) is read as: both hold every plan permission, and their own staff permissions of round 6 are unchanged. The six system roles are fixed in code and read-only in the pilot (custom roles are editable), so no administrator can lock everyone out and plans always match R16; a path missing from the map is administrator-only; pages are enforced in `src/proxy.ts` (no server actions exist) and API handlers also call the guard themselves; SP-1 has no new screens: the sign-in, activation and admin screens are SP-2, so SP-1 is tried with the local mode in the browser and `npm run cuentas:probar-acceso` in the terminal. Until SP-2 lands the old /login page cannot sign in; nothing reaches `main` before M1's subplans are all approved.
  Contracts produced: permission-map@1 (T1.2: `src/lib/cuentas/permisos.ts` catalogue and system roles, `src/lib/cuentas/mapa-rutas.ts`), plan-catalogue@1 (T1.2: `src/lib/planes/catalogo.ts`; consumers SP-2, SP-7, SP-14), account-service@1 (T1.3: `src/lib/cuentas/servicio.ts`), session-guard@1 (T1.4: `obtenerSesion(request)`, `exigirPermiso(request, permiso)` in `src/lib/cuentas/guardia.ts`). Consumers: SP-2, SP-4, SP-5, SP-6, SP-7, SP-8, SP-14. DAG: T1.1 → T1.2 → T1.3 → T1.4 → {T1.5, T1.6} → T1.7 → T1.8.
  Test database: every database test reads `PICTURES_REQ021_DATABASE_URL` (or, only in CI, `DATABASE_URL` with `APP_ENV=test`) through `scripts/test/lib/base-prueba.ts`, which creates a throwaway schema (`search_path` = that schema, public) so runs never see each other's rows. Audit evidence lives under `.evidence/REQ-021/` because the engine needs the ledger in the repository.

- [ ] T1.1 — Accounts schema: migration 037 and the isolated test-schema helper · repo: pictures · verify: `npm run cuentas:test-esquema -- --test-name-pattern=migracion` · files: scripts/migrations/037_cuentas.sql, scripts/test/lib/base-prueba.ts, scripts/test/test-cuentas-esquema.ts · resources: package.json scripts · covers: R1, R2, R3 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence high; estimate 60 minutes.
  Tables (additive only, `IF NOT EXISTS`, rollback comment like 036): `roles` (id, `clave` unique for the six system roles `usuario_entusiasta`, `usuario_designer`, `usuario_designer_plus`, `usuario_master_designer`, `empleado_interno`, `administrador` (A-1; was `usuario_plan_1..3`), nombre, `sistema` boolean); `rol_permisos` (rol_id, permiso; custom roles only, system role permissions live in code); `cuentas` (id, correo with a unique index on `lower(correo)`, nombre, empresa nullable, rol_id, estado `invitada|activa|desactivada`, hash_contrasena nullable, invitada_en, activada_en, ultimo_acceso_en, aviso_datos_version, aviso_datos_aceptado_en, idioma nullable `es|en`, es_local boolean, creada_por nullable); `sesiones` (id, cuenta_id ON DELETE CASCADE, hash_token char(64) unique, creada_en, expira_en, revocada_en); `enlaces_cuenta` (id, cuenta_id ON DELETE CASCADE, tipo `invitacion|restablecer`, hash_token unique, expira_en, usado_en, creado_por); `intentos_ingreso` (correo normalizado, en, exitoso) indexed by (correo, en).
  Personal data kept is only what round 5 q6 lists. `base-prueba.ts` exports `crearBasePrueba()` → `{ url, pool, cerrar() }`: it refuses unless the URL comes from `PICTURES_REQ021_DATABASE_URL`, or from `DATABASE_URL` with `APP_ENV=test`; creates schema `prueba_<random>`, applies every migration of `scripts/migrations/` into it with the runner's logic, returns a URL whose `options` set `search_path=<schema>,public`, and drops the schema in `cerrar()`.
  npm script added: `cuentas:test-esquema` = `tsx --test scripts/test/test-cuentas-esquema.ts`.

  - Acceptance / integration: Migration 037 applies on an empty isolated schema and again on an already migrated one without error, creates the account, role, session, link and sign-in attempt tables, and seeds exactly the six system roles. Check: `npm run cuentas:test-esquema -- --test-name-pattern=migracion`
  - Acceptance / functional: The database rejects a second account whose email differs only in letter case and removes an account's sessions and links when the account is deleted. Check: `npm run cuentas:test-esquema -- --test-name-pattern=restricciones`
  - Acceptance / functional: Each test run works in its own throwaway schema of the REQ-021 test database, drops it at the end, and refuses to run against any database other than PICTURES_REQ021_DATABASE_URL or a CI database marked APP_ENV=test. Check: `npm run cuentas:test-esquema -- --test-name-pattern=aislamiento`

- [ ] T1.2 — Permission catalogue, the plan catalogue, the six system roles and the route permission map · repo: pictures · after: T1.1 · verify: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura` · files: src/lib/cuentas/permisos.ts, src/lib/planes/catalogo.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-mapa-rutas.ts, scripts/test/test-catalogo-planes.ts · resources: package.json scripts, contract:permission-map, contract:plan-catalogue · covers: R2, R3, R16, R17 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling high; confidence medium; estimate 120 minutes (A-1: was 90).
  Permissions (keys stable, labels ES/EN for SP-2): `chat.usar`, `contador.usar`, `catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, `proyectos.ver_todos`, `gasto.ver`, `internas.usar`, `cuentas.administrar`, `roles.administrar`, `textos.corregir`. System roles (A-1, round 10; supersedes round 6's Plan 1/2/3): Entusiasta = chat, contador, catálogo; Designer = the same permissions (its higher chat limits wait for the limit values, owner-deferred); Designer Plus = Designer + costos; Master Designer = Designer Plus + taller (scene AI, assembly plans and sheet, export, own projects and decorations, all under `taller.usar` as in round 6) + `decoraciones.explorar` (owner 2026-10-27: «todo lo del editor de globos 3D solo está en el último plan», so the ready-made decorations explorer lives only in Master Designer; Designer Plus keeps the cost calculator); Empleado interno = every plan permission + proyectos.ver_todos, gasto.ver, internas.usar; Administrador = everything. `catalogo.ver` stays in the base plan as round 6 gave it to Plan 1 (assumption to re-confirm). Extended chat, structure detection and advanced balloon detection get no permission key now: each is built, with its key, in its own requirement.
  Plan catalogue (`src/lib/planes/catalogo.ts`, contract plan-catalogue@1, the only place plan names, prices, tools and plan permissions are written): `PLANES` = ordered `[{ id: 'entusiasta' | 'designer' | 'designer-plus' | 'master-designer', rolClave, nombre: {es, en}, precioMensual: {cop, usd}, herramientas: [{clave, nombre: {es, en}, disponible}], permisos }]` with prices 0/0, 20000/7, 45000/14, 70000/25; tool keys `chat-basico`, `contador-globos`, `chat-limites-altos`, `chat-extendido` (not available), `calculadora-costos`, `deteccion-estructuras` (not available), `deteccion-globos-avanzada` (not available), `taller-3d`; each plan's `permisos` must contain the previous plan's. Names (owner 2026-10-27): `entusiasta` es «Entusiasta» / en «Enthusiast»; Designer, Designer Plus and Master Designer are the same in both languages. Chat tools without numbers: `chat-basico` es «Chat con límites» / en «Chat with limits» (Entusiasta); `chat-limites-altos` es «Chat con límites más altos» / en «Chat with higher limits» (Designer and above, replacing the Entusiasta line). The `taller-3d` tool line stands for the whole 3D balloon editor, the decorations explorer included (owner-confirmed 2026-10-27; no separate line). `permisos.ts` builds the four plan roles from `PLANES` (it never lists their permissions itself). npm script `planes:test-catalogo` = `tsx --test scripts/test/test-catalogo-planes.ts`.
  Map entries: `{ patron, acceso }` with `acceso` = `{ permiso }`, `'sesion'` (any signed-in account: home page, sign-out), `'publica'` (login, activation, `/cotizacion-compartida/*` and its public APIs, and `/planes`, the public plans section of SP-14, added by A-1) or `'auth-propia'` (today's proxy exceptions: asesor, Happie recommend/webhook, Shopify webhook, feedback cron, voice transcription). Classification: /asistente, chat and guided-engine APIs → chat.usar; /catalogo and catalogue/product read APIs → catalogo.ver; cotizacion-profesional → costos.usar; decorations read API → decoraciones.explorar; /3d, scene AI, plan-armado-*, plan-patron, plan-dibujo-estructura, plan-idea, plan-editar, taller/*, modulos-*, render and image generation, escena-desde-foto, hoja-armado → taller.usar; /admin, /api/admin/*, write APIs of products and decorations, /estadisticas, laboratorios, Happie test, IA provider, feedback admin, internal AI → internas.usar. The balloon counter has no route of its own until SP-7. A route whose tool is unclear goes to internas.usar and is listed in the task report.
  `resolverAcceso(path)` returns the single matching entry or `null` (= administrator-only, permission `cuentas.administrar`). npm script `cuentas:test-permisos` = `tsx --test scripts/test/test-mapa-rutas.ts`.

  - Acceptance / static: Every page.tsx and route.ts under src/app matches exactly one entry of the route permission map, and the test fails naming any file that matches none or several. Check: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura`
  - Acceptance / functional: The six system roles hold exactly these permissions: the four plan roles take theirs only from the plan catalogue, Entusiasta and Designer the assisted chat, the balloon counter and the catalogue, Designer Plus adds the cost calculator and Master Designer adds the Taller 3D with its scene AI, assembly plans and sheet, export, own projects and decorations and the ready-made decorations explorer; Empleado interno holds every plan permission, everyone's projects, AI spend and internal tools; Administrador holds every permission. Check: `npm run cuentas:test-permisos -- --test-name-pattern=roles-sistema`
  - Acceptance / functional: The plan catalogue holds exactly four plans in the order Entusiasta, Designer, Designer Plus and Master Designer, each with its name in Spanish and English (Entusiasta is Enthusiast in English; Designer, Designer Plus and Master Designer keep their names), its monthly price in COP and USD (free; 20,000 and 7; 45,000 and 14; 70,000 and 25), its tools in cumulative order with the Entusiasta chat described as with limits and the Designer chat as with higher limits and no limit number, extended chat, structure detection and advanced balloon detection marked not available yet, and its permission list; a catalogue with a missing name, price or tool, an unknown permission key or a plan that lacks a permission of the plan below it fails to load naming the plan and the field. Check: `npm run planes:test-catalogo`
  - Acceptance / functional: A path the map does not list is reachable only with the users-administration permission, and the public and own-auth exceptions of today's proxy matcher stay public or own-auth. Check: `npm run cuentas:test-permisos -- --test-name-pattern=excepciones`

- [ ] T1.3 — Account service: invitations, activation, sign-in with lockout, reset links, roles and the one-time commands · repo: pictures · after: T1.2 · verify: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion` · files: src/lib/seguridad/scrypt.ts, src/lib/asesor/auth.ts, src/lib/cuentas/servicio.ts, src/lib/cuentas/enlaces.ts, src/lib/cuentas/limite-intentos.ts, scripts/cuentas/primer-admin.ts, scripts/cuentas/sembrar-prueba.ts, scripts/test/test-cuentas-servicio.ts · resources: package.json scripts, contract:account-service, contract:permission-map · covers: R1, R3, R16 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 150 minutes.
  Move the scrypt hash/verify of `src/lib/asesor/auth.ts` into `src/lib/seguridad/scrypt.ts` unchanged; the advisor login imports it and keeps its behavior.
  Service API (`src/lib/cuentas/servicio.ts`, server-only): `invitar({correo, nombre, empresa?, rolId}, porCuentaId)` → link; `activar(token, {contrasena, versionAviso})`; `ingresar(correo, contrasena, ip)` → cuenta or the generic error `CREDENCIALES_INVALIDAS`; `crearEnlaceRestablecer(cuentaId, porCuentaId)`; `restablecer(token, contrasena)`; `cambiarRol`, `desactivar`, `reactivar`, `eliminar`; `crearRol({nombre, permisos})`, `editarRol`, `eliminarRol`. Tokens: 32 random bytes base64url, only SHA-256 stored; invitation 7 days, reset 24 h, single use under a row lock. Passwords: minimum 8 characters, maximum 200, scrypt. Lockout: 5 failures for one normalised email within 15 min → that email refused 15 min (checked before verifying the password, same generic error). The last active Administrador cannot be deactivated, deleted or moved to another role. Deleting an account removes its row, sessions, links and sign-in attempts; later subplans decide what happens to its projects.
  `npm run cuentas:primer-admin -- --correo <email>` (owner runs it at release against the database in `DATABASE_URL`): refuses without changes if an active Administrador exists; otherwise creates the invited Administrador and prints the activation link once to the terminal, never to a log file. `npm run cuentas:sembrar-prueba`: refuses unless the target is `PICTURES_REQ021_DATABASE_URL`; creates `entusiasta@prueba.local`, `designer@prueba.local`, `designer-plus@prueba.local`, `master-designer@prueba.local`, `empleado@prueba.local` and `admin@prueba.local` (A-1; was plan1@/plan2@/plan3@), active, with one password typed without echo. npm script `cuentas:test-servicio` = `tsx --conditions=react-server --test scripts/test/test-cuentas-servicio.ts`.

  - Acceptance / functional: An administrator's invitation creates an invited account with a single-use link valid seven days; activating it sets a password of at least eight characters, records the data-notice version and date, and a second use of the same link is refused. Check: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion`
  - Acceptance / functional: Signing in with the right email and password of an active account creates a session; a wrong password, an unknown email and a deactivated account all get the same generic refusal. Check: `npm run cuentas:test-servicio -- --test-name-pattern=ingreso`
  - Acceptance / functional: After five failed sign-ins for one email within fifteen minutes that email is refused for fifteen minutes even with the right password, and other emails are unaffected. Check: `npm run cuentas:test-servicio -- --test-name-pattern=bloqueo`
  - Acceptance / functional: An administrator-generated reset link is single-use, expires after 24 hours, sets a new password and revokes every open session of that account. Check: `npm run cuentas:test-servicio -- --test-name-pattern=restablecer`
  - Acceptance / functional: Deactivating, deleting or changing the role of the last active Administrador is refused; deleting an account removes its personal data rows. Check: `npm run cuentas:test-servicio -- --test-name-pattern=ultimo-admin`
  - Acceptance / functional: An administrator creates a role from permissions of the catalogue only; the six system roles cannot be edited or deleted; a role still assigned to accounts cannot be deleted. Check: `npm run cuentas:test-servicio -- --test-name-pattern=roles`
  - Acceptance / integration: npm run cuentas:primer-admin creates an invited Administrador for the given email and prints its activation link once, and refuses without changes when an active Administrador already exists. Check: `npm run cuentas:test-servicio -- --test-name-pattern=primer-admin`
  - Acceptance / functional: npm run cuentas:sembrar-prueba creates one active account per system role with a password read from the terminal without echo, and refuses when the target database is not the REQ-021 test database. Check: `npm run cuentas:test-servicio -- --test-name-pattern=sembrar`

- [ ] T1.4 — Server sessions and the permission guard in the proxy and the sign-in API, replacing APP_PASSWORD · repo: pictures · after: T1.3 · verify: `npm run cuentas:test-sesion -- --test-name-pattern=cookie` · files: src/lib/cuentas/sesion.ts, src/lib/cuentas/guardia.ts, src/proxy.ts, src/lib/auth/session.ts, src/lib/auth/request.ts, src/app/api/login/route.ts, src/app/api/cuentas/ingresar/route.ts, src/app/api/cuentas/salir/route.ts, src/app/sin-acceso/page.tsx, scripts/cuentas/probar-acceso.ts, scripts/test/test-sesion-guardia.ts, scripts/test/test-proxy-matcher.ts · resources: package.json scripts, contract:session-guard, contract:account-service, contract:permission-map · covers: R1, R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 150 minutes.
  `sesion.ts`: `crearSesion(cuentaId)` sets cookie `pictures_sesion` (httpOnly, SameSite=Lax, Secure unless the host is localhost/127.0.0.1, Max-Age 30 days, absolute expiry); `obtenerSesion(request)` → `{ cuenta, rol, permisos } | null` with one query (sessions × accounts × roles, custom role permissions from `rol_permisos`, system ones from `permisos.ts`), rejecting revoked, expired or non-active accounts and updating `ultimo_acceso_en` at most once per hour; `cerrarSesion`.
  `guardia.ts`: `exigirPermiso(request, permiso)` → `{ cuenta } | Response` (401 `SESION_REQUERIDA` / 403 `SIN_PERMISO`, JSON). `src/proxy.ts`: public and own-auth entries pass untouched (same matcher exceptions as today); otherwise resolve the session and the map: no session → page redirect to `/login?from=<path>` and API 401; missing permission → page rewrite to `/sin-acceso` (plain server page, text only) and API 403. Remove `APP_PASSWORD`, `sessionToken`, `loginOmitidoEnDesarrollo` and `DEV_REQUIRE_LOGIN`; `/api/login` is deleted in favor of `POST /api/cuentas/ingresar` (JSON email + password, same relative redirect rule as today for forms) and `POST /api/cuentas/salir`. Mutating APIs keep `isSameOriginRequest`.
  `npm run cuentas:probar-acceso -- --base http://localhost:3000 --correo <email>` reads the password without echo, signs in and prints allowed/denied for one representative page and API per map area. npm script `cuentas:test-sesion` = `tsx --conditions=react-server --test scripts/test/test-sesion-guardia.ts`; `test-proxy-matcher` is updated to the new matcher.

  - Acceptance / functional: A session cookie is httpOnly, SameSite=Lax, Secure outside localhost, lasts 30 days, and only the SHA-256 of its random token is stored. Check: `npm run cuentas:test-sesion -- --test-name-pattern=cookie`
  - Acceptance / functional: Deactivating an account, changing its password or signing out ends its sessions on the next request, and a role change applies on the next request without signing in again. Check: `npm run cuentas:test-sesion -- --test-name-pattern=revocacion`
  - Acceptance / functional: Without a valid session a page request redirects to /login keeping the path and an API request gets 401 JSON; with a session lacking the mapped permission a page shows the no-access page and an API gets 403 JSON. Check: `npm run cuentas:test-sesion -- --test-name-pattern=proxy`
  - Acceptance / regression: A cookie or form built from the old APP_PASSWORD no longer grants access, and no code path reads APP_PASSWORD. Check: `npm run cuentas:test-sesion -- --test-name-pattern=sin-clave-compartida`
  - Acceptance / integration: npm run cuentas:probar-acceso signs in against a running server with an email and a password read without echo and prints, for every mapped area, whether that account is allowed or denied. Check: `npm run cuentas:test-sesion -- --test-name-pattern=probar-acceso`

- [ ] T1.5 — Local no-restrictions mode that refuses to start outside next dev on loopback · repo: pictures · after: T1.4 · verify: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · files: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py · resources: package.json scripts · covers: R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence high; estimate 60 minutes.
  `modo-local.ts`: `validarModoLocal({ nodeEnv, vercel, fase })` throws `AUTH_LOCAL_SIN_RESTRICCIONES solo funciona con next dev en tu máquina` unless `NODE_ENV=development`, `VERCEL` unset and the phase is the dev server; called from `next.config.ts` (covers `next build`) and `register()` in `src/instrumentation.ts` (covers `next start` and the VPS container). The ai-api refuses to start if the variable is present at all. Per request, the session guard treats the request as the Administrador local account only when the mode is on and the connection address is loopback (127.0.0.1, ::1); the Host header is never trusted.
  The Administrador local account (`es_local = true`, correo `admin-local@localhost.invalid`, role Administrador, no password, so it can never sign in remotely) is created on first use in whatever database the local process points at; this also covers the owner's round-6 note of running locally against the production database to create administrators.
  npm script `cuentas:test-modo-local` = `tsx --conditions=react-server --test scripts/test/test-modo-local.ts`.

  - Acceptance / functional: With AUTH_LOCAL_SIN_RESTRICCIONES=1 under next dev, a request from 127.0.0.1, ::1 or localhost runs as the Administrador local account without signing in, and a request from any other address must sign in. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback`
  - Acceptance / functional: With AUTH_LOCAL_SIN_RESTRICCIONES set, next build, next start, a Vercel environment and the ai-api deployment refuse to start with an error naming the variable. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=rechazo-arranque`
  - Acceptance / regression: Without the variable next dev asks to sign in like production, and DEV_REQUIRE_LOGIN no longer changes anything. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=sin-variable`

- [ ] T1.6 — Apply the permission guard to every API handler and move the existing suites to a shared test session · repo: pictures · after: T1.4 · verify: `npm run cuentas:test-rutas` · files: src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/test/*.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts · resources: package.json scripts, contract:session-guard, contract:permission-map · covers: R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity low; scope large_change; risk high; coupling high; confidence high; estimate 180 minutes.
  Each handler outside `publica`/`auth-propia` starts with `const acceso = await exigirPermiso(request, '<permiso>'); if (acceso instanceof Response) return acceso;`, with the permission `resolverAcceso` gives its path; library helpers that called `isAuthenticatedRequest` receive the account from their handler instead. `test-guardias-rutas.ts` reads each `route.ts`, checks that every exported HTTP method calls `exigirPermiso` with exactly the mapped permission before any other await, and calls a sample of handlers in-process with no session, an Entusiasta session and an Administrador session.
  `scripts/test/lib/sesion-prueba.ts`: `conSesionDePrueba(rolClave)` creates an account and a session in the isolated test schema and returns the cookie header; no environment variable bypasses authentication. The e2e smoke (`npm run e2e:humo`) signs in with `E2E_CORREO`/`E2E_CONTRASENA` instead of APP_PASSWORD. npm script `cuentas:test-rutas` = `tsx --conditions=react-server --test scripts/test/test-guardias-rutas.ts`.

  - Acceptance / functional: Every API route handler outside the public and own-auth exceptions calls the permission guard with the permission the map assigns to its path before doing any work. Check: `npm run cuentas:test-rutas`
  - Acceptance / regression: The existing suites that signed in with APP_PASSWORD pass using the shared test-session helper and none of them sets APP_PASSWORD. Check: `npm run test-cotizacion-unica`
  - Acceptance / static: Lint and the TypeScript check pass on the whole repository after the guards are applied. Check: `npm run taller:test-estatico`

- [ ] T1.7 — End-to-end check of accounts and permissions on a production build, and the SP-1 suites in CI · repo: pictures · after: T1.5, T1.6 · verify: `npm run cuentas:test-integracion` · files: scripts/test/test-integracion-cuentas.ts, .github/workflows/checks.yml, .evidence/REQ-021/SP-1.integration.json · resources: package.json scripts, contract:session-guard · covers: R1, R2, R3, R16 · kind: test · subplan: SP-1

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 120 minutes.
  `test-integracion-cuentas.ts`: creates the isolated schema, seeds one account per role through the service, runs `next build` then `next start` on a free loopback port with `DATABASE_URL` = the schema URL, and with plain `fetch`: signs in through `/api/cuentas/ingresar`, asserts allowed and denied pages (redirect or `/sin-acceso`) and APIs (401/403) for Entusiasta, Designer Plus, Master Designer, Empleado interno and Administrador; deactivates the Master Designer account through the service and asserts its next request gets 401; posts the old shared password form and asserts refusal; then starts `next start` with `AUTH_LOCAL_SIN_RESTRICCIONES=1` and asserts it exits with the error. Writes `.evidence/REQ-021/SP-1.integration.json` and kills only its own processes.
  `checks.yml`: the Postgres job runs `cuentas:test-esquema`, `cuentas:test-permisos`, `cuentas:test-servicio`, `cuentas:test-sesion`, `cuentas:test-modo-local` and `cuentas:test-rutas`, plus a step that runs `next build` with the variable set and passes only if it fails. npm script `cuentas:test-integracion` = `tsx scripts/test/test-integracion-cuentas.ts`.

  - Acceptance / integration: Against a production build started with next start on the REQ-021 test database, one Entusiasta, one Designer Plus, one Master Designer, one Empleado interno and one Administrador account each reach exactly their mapped pages and APIs, a deactivated account loses access on its next request, and the old shared password is refused. Check: `npm run cuentas:test-integracion`
  - Acceptance / static: The CI checks workflow runs the SP-1 suites against its Postgres service and fails when a build is started with AUTH_LOCAL_SIN_RESTRICCIONES set. Check: `npm run cuentas:test-integracion -- --solo-ci`

- [ ] T1.9 — Remediate T1.8 findings F1, F2, F3, F4 · repo: pictures · after: T1.7 · verify: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · files: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py, src/lib/cuentas/permisos.ts, src/lib/planes/catalogo.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-mapa-rutas.ts, scripts/test/test-catalogo-planes.ts, src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/test/*.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts · resources: contract:permission-map, contract:plan-catalogue, contract:session-guard, package.json scripts · covers: R16, R17, R2, R3 · kind: implement · subplan: SP-1
- [ ] T1.10 — Remediate T1.8 findings F6 · repo: pictures · after: T1.7, T1.9 · verify: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion` · files: src/lib/seguridad/scrypt.ts, src/lib/asesor/auth.ts, src/lib/cuentas/servicio.ts, src/lib/cuentas/enlaces.ts, src/lib/cuentas/limite-intentos.ts, scripts/cuentas/primer-admin.ts, scripts/cuentas/sembrar-prueba.ts, scripts/test/test-cuentas-servicio.ts · resources: contract:account-service, contract:permission-map, package.json scripts · covers: R1, R16, R3 · kind: implement · subplan: SP-1
- [ ] T1.11 — Remediate T1.8 findings F16, F17 · repo: pictures · after: T1.7, T1.10 · verify: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · files: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py, src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts · resources: contract:permission-map, contract:session-guard · covers: R2 · kind: implement · subplan: SP-1
- [ ] T1.12 — Remediate T1.8 findings F19, F20 · repo: pictures · after: T1.7, T1.10, T1.11 · verify: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · files: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py, src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts, src/lib/cuentas/permisos.ts, src/lib/planes/catalogo.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-mapa-rutas.ts, scripts/test/test-catalogo-planes.ts, scripts/test/*.ts · resources: contract:permission-map, contract:plan-catalogue, contract:session-guard · covers: R16, R17, R2, R3 · kind: implement · subplan: SP-1
- [ ] T1.8 — SP-1 security audit: accounts, sessions, permissions, local mode and the one-time commands · repo: pictures · after: T1.7, T1.10, T1.11, T1.12 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json` · files: .evidence/REQ-021/SP-1.audit.md, .evidence/REQ-021/SP-1.findings.json · resources: ledger:SP-1 · covers: R1, R2, R3, R16 · kind: audit · subplan: SP-1
- [ ] T1.8b — Cross-check audit of T1.8: SP-1 security audit: accounts, sessions, permissions, local mode and the one-time commands · repo: pictures · after: T1.8 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.audit-crosscheck.findings.json` · files: .evidence/REQ-021/SP-1.audit-crosscheck.md, .evidence/REQ-021/SP-1.audit-crosscheck.findings.json · covers: R1, R2, R3, R16 · kind: audit · subplan: SP-1

  Classification: complexity high; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Checks at least: tokens and passwords never logged or stored in clear; timing-safe comparisons; lockout cannot be bypassed by case or spaces in the email; links are single-use under concurrency; every route.ts and page.tsx is mapped and guarded; own-auth exceptions unchanged; the local mode cannot activate in any build, start or deployment and ignores forged Host headers; `primer-admin` cannot create a second administrator; deleting an account removes its personal data. Each confirmed defect names the task to redo.

  - Acceptance / static: An independent security audit of SP-1 records every confirmed defect with the task that must redo it in the SP-1 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json`

<!-- /SP-1 tasks -->

- **SP-2 — Sign-in, invitation and administration screens** (UI: `cuentas-admin@v1`): A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns one of the four access plans or another role, creates roles by choosing permissions, and deactivates or deletes accounts. Covers R1, R3, R16, R17.

<!-- SP-2 tasks -->

  SP-2 tasks (draft for owner confirmation). Screens follow the Designer's `cuentas-admin@v1` contract once the owner approves it. Only the Administrador manages users and roles (round 6 q2). Screens are written in Spanish now with every string in one module per screen so SP-8/SP-10 translate them; the data notice ships in Spanish and English from the start (round 5 q6).
  **Amendment A-2 (applied 2026-10-27).** T2.5 names the six system roles and its role picker reads the four plans from plan-catalogue@1 (new criterion `--solo planes`; SP-2 now consumes plan-catalogue@1 from SP-1 and covers R17); T2.6 invites a Usuario · Designer Plus person (chat and cost calculator, no Taller 3D) and moves them to Usuario · Master Designer; the outcome says the administrator assigns one of the four access plans. The cuentas-admin@v1 contract and mockup must show Usuario · Entusiasta, Designer, Designer Plus and Master Designer instead of Plan 1/2/3. SP-2's design was finalised (direction A, r13), so this plan change marks it «contract to update»: it needs `design amend` (delta only), not a redraft; the owner confirms SP-2 after that. The plans section links on /login and in the account menu are SP-14's (T14.3), not SP-2's.
  DAG: T2.1 (design) ∥ T2.2 (APIs, after SP-1's session-guard T1.4) → {T2.3, T2.4, T2.5} (UI) → T2.6 (integration) → T2.7 (visual review) → T2.8 (audit). Consumes account-service@1, session-guard@1, permission-map@1 and plan-catalogue@1 from SP-1; composition gate CG-1 proves SP-1 and SP-2 together on the integrated M1 tree.

- [ ] T2.1 — Copy the owner-approved cuentas-admin@v1 contract into the repository · repo: pictures · after: T1.4 · verify: `test -s design/contracts/cuentas-admin@v1.md` · files: design/contracts/cuentas-admin@v1.md · resources: design:cuentas-admin@v1 · covers: R1, R3, R16 · kind: design · subplan: SP-2 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.
  The scheduler supplies the plan-approved draft; the task copies it unchanged.

  - Acceptance / static: The owner-approved cuentas-admin@v1 contract is copied byte for byte into design/contracts/cuentas-admin@v1.md. Check: `test -s design/contracts/cuentas-admin@v1.md`

- [ ] T2.2 — Account APIs: activation, reset, notice acceptance, own password and the administration of accounts and roles · repo: pictures · after: T1.4, T1.8b · verify: `npm run cuentas:test-api -- --test-name-pattern=enlaces` · files: src/lib/cuentas/aviso-datos.ts, src/app/api/cuentas/activar/route.ts, src/app/api/cuentas/restablecer/route.ts, src/app/api/cuentas/aviso/route.ts, src/app/api/cuentas/mi-cuenta/route.ts, src/app/api/admin/cuentas/route.ts, src/app/api/admin/cuentas/[id]/route.ts, src/app/api/admin/roles/route.ts, src/app/api/admin/roles/[id]/route.ts, src/lib/cuentas/dependientes.ts, src/lib/cuentas/regenerar-enlace.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-cuentas-api.ts · resources: package.json scripts, contract:account-service, contract:session-guard · covers: R1, R3, R16 · kind: implement · subplan: SP-2 · ui: no

  Classification: complexity medium; scope large_change; risk high; coupling high; confidence medium; estimate 120 minutes.
  `aviso-datos.ts` exports `AVISO_DATOS = { version: 1, es, en }` with the SPEC «Data-processing notice» text verbatim, placeholders included. Routes: `POST /api/cuentas/activar` {token, contrasena, versionAviso}; `POST /api/cuentas/restablecer` {token, contrasena}; `GET /api/cuentas/activar?token=` returns name and email for a valid invitation only; `POST /api/cuentas/aviso` accepts the current version for the session's account; `PATCH /api/cuentas/mi-cuenta` {actual, nueva} (the SP-1 service revokes every session of the account; the route then opens a new session for the requesting browser). Admin (`cuentas.administrar`): `GET/POST /api/admin/cuentas` (list with search and filters; invite), `PATCH/DELETE /api/admin/cuentas/[id]` (role, state, reset link; delete requires `confirmarCorreo` equal to the email). Roles (`roles.administrar`): `GET/POST /api/admin/roles`, `PATCH/DELETE /api/admin/roles/[id]`. All mutations keep `isSameOriginRequest`; errors are stable codes (`LINK_INVALIDO`, `CORREO_REGISTRADO`, `ULTIMO_ADMIN`, `ROL_EN_USO`, `ROL_SISTEMA`).
  Delete rule (owner, round 7 q1): `src/lib/cuentas/dependientes.ts` exports a registry of tables that hold an account's saved work (empty here; SP-4 adds projects and SP-5 saved decorations); `DELETE /api/admin/cuentas/[id]` refuses with `CUENTA_CON_TRABAJO` when any registered table has a row for the account, so such accounts are only deactivated. AI spend rows (SP-6) are never work: they keep their totals with the account reference set to null and show «Cuenta eliminada». Round 8: `regenerar-enlace.ts` revokes every unused link of the same kind for the account and issues a new one (`POST /api/admin/cuentas/[id]` action `enlace-nuevo`, for invited accounts and for resets); custom roles need at least one permission (`ROL_SIN_PERMISOS`, checked in the API schema); `POST /api/cuentas/activar` opens the session with SP-1 `crearSesion` and answers the first allowed destination. The notice-acceptance route also serves re-acceptance when `AVISO_DATOS.version` grows (round 7 q3). The map from T1.2 gets the new paths (public: activar, restablecer; sesion: aviso, mi-cuenta). npm script `cuentas:test-api` = `tsx --conditions=react-server --test scripts/test/test-cuentas-api.ts`.

  - Acceptance / functional: The activation, reset and notice-acceptance APIs accept only a valid unused token or a signed-in session, validate every body, answer a used or expired link with LINK_INVALIDO without saying which, and a successful activation opens a session at once. Check: `npm run cuentas:test-api -- --test-name-pattern=enlaces`
  - Acceptance / functional: The account and role administration APIs refuse anyone without the users or roles permission with 403 and accept only same-origin requests with validated bodies. Check: `npm run cuentas:test-api -- --test-name-pattern=admin`
  - Acceptance / functional: Generating a new invitation or reset link for an account invalidates every older unused link of the same kind for that account, and a custom role with no permission is refused with ROL_SIN_PERMISOS. Check: `npm run cuentas:test-api -- --test-name-pattern=regenerar`
  - Acceptance / functional: Changing one's own password requires the current password, ends every session of that account and signs the requesting browser in again with a new session. Check: `npm run cuentas:test-api -- --test-name-pattern=mi-cuenta`
  - Acceptance / functional: The data notice exists in Spanish and English with a version number, its bracketed placeholders are still marked for legal review, and accepting stores the version and date on the account. Check: `npm run cuentas:test-api -- --test-name-pattern=aviso`
  - Acceptance / functional: Deleting an account that owns any row of a table registered as account work is refused with CUENTA_CON_TRABAJO and changes nothing, while deleting an account without saved work removes it and keeps its AI spend rows without personal data. Check: `npm run cuentas:test-api -- --test-name-pattern=borrar`

- [ ] T2.3 — Sign-in, invitation activation, password reset and notice re-acceptance screens · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-acceso -- --solo ingreso` · files: src/app/login/page.tsx, src/app/login/LoginForm.tsx, src/app/activar/[token]/page.tsx, src/app/restablecer/[token]/page.tsx, src/app/aviso-datos/page.tsx, src/components/cuentas/FormularioContrasena.tsx, src/components/cuentas/AvisoDatos.tsx, src/components/cuentas/textos-acceso.ts, src/proxy.ts, scripts/test/test-ui-acceso.ts · resources: package.json scripts, contract:session-guard · covers: R1 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence medium; estimate 150 minutes.
  Strings live in `textos-acceso.ts` (Spanish now, keys ready for SP-8). The notice is shown in the browser language (`Accept-Language`: en → English, else Spanish). The proxy redirects a session whose account accepted an older notice version to `/aviso-datos?from=` before any page except sign-out. After sign-in the destination is `from` when allowed, else the first allowed of Taller 3D, chat, catalogue, else `/cuenta` (every active account can open it). The sign-in screen never distinguishes a locked email: SP-1 returns one generic refusal, and the message always adds the fifteen-minute wait hint. npm script `cuentas:test-ui-acceso` = `tsx scripts/test/test-ui-acceso.ts` (server render of every state plus a Playwright pass on a dev server against the isolated schema).

  - Acceptance / functional: On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them. Check: `npm run cuentas:test-ui-acceso -- --solo ingreso`
  - Acceptance / functional: Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one. Check: `npm run cuentas:test-ui-acceso -- --solo activacion`
  - Acceptance / functional: Opening a reset link lets the person set a new password and then sign in; a used or expired link shows the same message as an invalid invitation. Check: `npm run cuentas:test-ui-acceso -- --solo restablecer`
  - Acceptance / functional: When the notice version changes, a signed-in person must accept the new version before any other page opens. Check: `npm run cuentas:test-ui-acceso -- --solo aviso`

- [ ] T2.4 — Account menu on every signed-in page and the Mi cuenta page · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-mi-cuenta` · files: src/components/cuentas/MenuCuenta.tsx, src/app/layout.tsx, src/app/cuenta/page.tsx, src/components/cuentas/textos-cuenta.ts, scripts/test/test-ui-mi-cuenta.ts · resources: package.json scripts, contract:session-guard · covers: R1 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  The root layout reads the session on the server and renders `MenuCuenta` only for signed-in pages, at the place the contract defines. npm script `cuentas:test-ui-mi-cuenta` = `tsx scripts/test/test-ui-mi-cuenta.ts`.

  - Acceptance / functional: Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one. Check: `npm run cuentas:test-ui-mi-cuenta`

- [ ] T2.5 — Administration screens: accounts list, invitations, account actions and the role editor · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-admin -- --solo lista` · files: src/app/admin/cuentas/page.tsx, src/app/admin/roles/page.tsx, src/components/admin/cuentas/ListaCuentas.tsx, src/components/admin/cuentas/DialogoInvitar.tsx, src/components/admin/cuentas/AccionesCuenta.tsx, src/components/admin/cuentas/EditorRol.tsx, src/components/admin/cuentas/textos-admin-cuentas.ts, src/components/admin/AdminTabs.tsx, scripts/test/test-ui-admin-cuentas.ts · resources: package.json scripts, contract:permission-map, contract:plan-catalogue · covers: R1, R3, R16, R17 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence medium; estimate 180 minutes.
  The invitation and reset links are shown once with a copy button and a note that they are not shown again. Permission checkboxes come from `permisos.ts` with their labels, grouped by tool. A-2: the role picker (invite and change role) lists the four plan roles by their `PLANES` names in plan order (Usuario · Entusiasta, Usuario · Designer, Usuario · Designer Plus, Usuario · Master Designer), then Empleado interno, Administrador and the custom roles; no plan name is written in SP-2 code. Links to both screens appear only for accounts holding the permission. npm script `cuentas:test-ui-admin` = `tsx scripts/test/test-ui-admin-cuentas.ts`.

  - Acceptance / functional: An administrator sees all accounts with name, email, company, role, state and last access, searches by name or email and filters by role and state. Check: `npm run cuentas:test-ui-admin -- --solo lista`
  - Acceptance / functional: An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message. Check: `npm run cuentas:test-ui-admin -- --solo invitar`
  - Acceptance / functional: An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted. Check: `npm run cuentas:test-ui-admin -- --solo acciones`
  - Acceptance / functional: An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the six system roles (Usuario · Entusiasta, Usuario · Designer, Usuario · Designer Plus, Usuario · Master Designer, Empleado interno and Administrador) read-only with their permissions, and cannot delete a role that still has accounts. Check: `npm run cuentas:test-ui-admin -- --solo roles`
  - Acceptance / functional: The role picker of the invitation and account screens offers the four access plans with the names of the plan catalogue in plan order, then Empleado interno, Administrador and the custom roles. Check: `npm run cuentas:test-ui-admin -- --solo planes`

- [ ] T2.6 — Browser end-to-end: invite, activate, sign in and change plan on a production build · repo: pictures · after: T2.3, T2.4, T2.5, T1.8b · verify: `npm run cuentas:test-integracion-ui` · files: scripts/test/test-integracion-cuentas-ui.ts, .evidence/REQ-021/SP-2.integration.json · resources: package.json scripts · covers: R1, R3, R16 · kind: test · subplan: SP-2

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Seeds one Administrador in the isolated schema, builds and starts the app, drives the administrator browser to invite a Usuario · Designer Plus person and read the link, opens it in a second context, activates with the notice, signs in, checks chat and costs open and /3d does not, changes the role to Usuario · Master Designer in the first browser and reloads /3d in the second. npm script `cuentas:test-integracion-ui` = `tsx scripts/test/test-integracion-cuentas-ui.ts`.

  - Acceptance / integration: On a production build against the REQ-021 test database, an administrator invites a Designer Plus person through the screens, the person activates the link in a separate browser, accepts the notice, signs in and reaches the chat and the costs tool but not the Taller 3D, and after the administrator moves them to Master Designer their next request opens the Taller. Check: `npm run cuentas:test-integracion-ui`

- [ ] T2.7 — SP-2 visual review against the cuentas-admin@v1 contract · repo: pictures · after: T2.6 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json` · files: .evidence/REQ-021/SP-2.visual.md, .evidence/REQ-021/SP-2.visual.findings.json · resources: ledger:SP-2-visual · covers: R1, R3 · kind: audit · subplan: SP-2

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit).

  - Acceptance / static: The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json`

- [ ] T2.8 — SP-2 audit: account screens, administration APIs and the data notice · repo: pictures · after: T2.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json` · files: .evidence/REQ-021/SP-2.audit.md, .evidence/REQ-021/SP-2.findings.json · resources: ledger:SP-2 · covers: R1, R3, R16 · kind: audit · subplan: SP-2

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 75 minutes.
  Checks at least: admin APIs refuse without the permission and cross-origin; links shown once and never logged; generic sign-in errors; notice version stored; delete requires typing the email.

  - Acceptance / static: An independent audit of SP-2 records every confirmed defect with the task that must redo it in the SP-2 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json`

<!-- /SP-2 tasks -->



<!-- CG-1 tasks -->

  Composition gate CG-1: SP-1, SP-2.

- [ ] T91 — M1 composition check: first administrator to an Entusiasta user on the integrated tree · repo: pictures · after: T1.8, T1.8b, T2.8 · verify: `npm run m1:test-composicion` · files: scripts/test/test-composicion-m1.ts, .evidence/REQ-021/CG-1.integration.json · resources: package.json scripts · covers: R1, R2, R16 · kind: test

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 60 minutes.
  Reuses the helpers of T1.7 and T2.6; npm script `m1:test-composicion` = `tsx scripts/test/test-composicion-m1.ts`.

  - Acceptance / integration: On the integrated M1 tree started with next start against the REQ-021 test database, cuentas:primer-admin creates an administrator who activates through the activation screen, invites an Entusiasta person who activates and signs in, and that person reaches the chat and the catalogue but gets the no-access page on the Taller 3D and 403 on its APIs. Check: `npm run m1:test-composicion`

<!-- /CG-1 tasks -->

- **SP-14 — Plans section: the four access plans, public and informative** (UI: `planes@v1`): Anyone, signed in or not, opens the plans section from the sign-in screen or the account menu and compares Entusiasta, Designer, Designer Plus and Master Designer with their monthly price (COP in Spanish, USD in English) and included tools read from the plan catalogue, with the tools not built yet marked «aún no disponible»; a second view lets visitors highlight a plan for comparison only, with all tool lists visible and no account change. Covers R17, R18, R19, R20.

<!-- SP-14 tasks -->

  SP-14 tasks (draft, added by amendment A-1; not confirmed). Owner round 10: informative only (the administrator assigns the plan on the accounts screen), public without sign-in, linked from the sign-in screen and the account menu, Spanish shows COP and English USD, no limit values or limit UI, inside the pilot. Round 13: an extra view may highlight/select a plan for comparison only and must not change assignment. Owner also requests no hide-tools control and a corrected tablet layout. Consumes plan-catalogue@1, permission-map@1 and session-guard@1 from SP-1; starts after the M1 composition check T91 because T14.3 edits SP-2's sign-in page and account menu. Until SP-8 exists the page picks the language from `Accept-Language` (en → English, else Spanish), the same rule SP-2 uses for the data notice; SP-8 moves it to the language mechanism. `/planes` is a Planner technical default route. Owner answers 2026-10-27: Entusiasta is «Enthusiast» in English, the other names stay; chat lines say «con límites» / «con límites más altos» without numbers; the section is never cut; the explorer is part of Master Designer's Taller 3D line.
  DAG: T91 → T14.1 (design) → T14.2 (page) → T14.3 (links) → T14.4 (integration) → T14.5 (visual review) → T14.6 (audit); composition gate CG-4 (T94) after T91 and T14.6.

- [ ] T14.1 — Copy the owner-approved planes@v1 contract into the repository · repo: pictures · after: T91 · verify: `test -s design/contracts/planes@v1.md` · files: design/contracts/planes@v1.md · resources: design:planes@v1 · covers: R18, R19, R20 · kind: design · subplan: SP-14 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.

  - Acceptance / static: The owner-approved planes@v1 contract is copied byte for byte into design/contracts/planes@v1.md. Check: `test -s design/contracts/planes@v1.md`

- [ ] T14.2 — Public plans page: the four plans from the plan catalogue, prices by language · repo: pictures · after: T14.1 · verify: `npm run planes:test-ui -- --solo catalogo` · files: src/app/planes/page.tsx, src/components/planes/ComparadorPlanes.tsx, src/components/planes/textos-planes.ts, scripts/test/test-ui-planes.ts · resources: package.json scripts, contract:plan-catalogue, contract:permission-map, design:planes@v1 · covers: R17, R18, R20 · kind: implement · subplan: SP-14 · ui: yes

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  `ComparadorPlanes({ planes, idioma })` renders only from `PLANES`; strings outside the catalogue (headings the contract fixes, «aún no disponible», «Gratis», per-month suffix) live in `textos-planes.ts` in both languages. Price format follows the language: `es` → COP with thousands separator, `en` → USD; never both. No button or form. The `/planes` public entry of `mapa-rutas.ts` is written by T1.2 (A-1), so this task does not edit the map. npm script `planes:test-ui` = `tsx scripts/test/test-ui-planes.ts` (static render with `renderToStaticMarkup`, like `test-ui-armado-columna.ts`; `--solo` selects a case).

  - Acceptance / functional: The /planes page shows Entusiasta, Designer, Designer Plus and Master Designer in that order, each with its name, monthly price and included tools taken from the plan catalogue, and a value changed in the catalogue appears on the page without editing the page. Check: `npm run planes:test-ui -- --solo catalogo`
  - Acceptance / functional: With a Spanish browser language the page shows every price in COP per month and with an English one in USD per month, never both, Entusiasta shows as free in each language and is named Enthusiast in English. Check: `npm run planes:test-ui -- --solo idioma`
  - Acceptance / functional: Extended chat, structure detection and advanced balloon detection appear under Designer Plus and Master Designer marked «aún no disponible» in Spanish and «not available yet» in English, the Entusiasta chat reads «con límites» / «with limits» and the Designer chat «con límites más altos» / «with higher limits», and the page has no purchase, request or sign-up control and shows no limit value. Check: `npm run planes:test-ui -- --solo sin-acciones`
  - Acceptance / functional: Without a session the /planes page is served, because the route permission map lists /planes as public, and every other page and API keeps exactly one mapped entry. Check: `npm run planes:test-ui -- --solo ruta-publica`
  - Acceptance / functional: The extra plans view lets a visitor select/highlight any plan for comparison and return to the full comparison; it never changes account assignment. Check: `npm run planes:test-ui -- --solo vista-eleccion`
  - Acceptance / functional: At tablet width all four plans and full tool lists remain legible without horizontal scrolling, and no hide-tools control is rendered. Check: `npm run planes:test-ui -- --solo tablet`

- [ ] T14.3 — Plans links on the sign-in screen and in the account menu · repo: pictures · after: T14.2 · verify: `npm run planes:test-ui-entrada` · files: src/app/login/page.tsx, src/components/cuentas/MenuCuenta.tsx, scripts/test/test-ui-planes-entrada.ts · resources: package.json scripts, contract:session-guard, design:planes@v1 · covers: R19 · kind: implement · subplan: SP-14 · ui: yes

  Classification: complexity low; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  One link on the sign-in screen and one entry in the account menu, where planes@v1 places them; nothing else in those SP-2 files changes. npm script `planes:test-ui-entrada` = `tsx scripts/test/test-ui-planes-entrada.ts` (isolated schema and SP-1 test session).

  - Acceptance / functional: The sign-in screen and the account menu each show one link to the plans section that opens /planes, signed out from the sign-in screen and signed in from the menu. Check: `npm run planes:test-ui-entrada`
  - Acceptance / regression: Apart from the plans link, the sign-in screen keeps the sign-in behavior its SP-2 test checks. Check: `npm run cuentas:test-ui-acceso -- --solo ingreso`
  - Acceptance / regression: Apart from the plans entry, the account menu and Mi cuenta keep the behavior their SP-2 test checks. Check: `npm run cuentas:test-ui-mi-cuenta`

- [ ] T14.4 — Browser end-to-end of the plans section on a production build · repo: pictures · after: T14.3 · verify: `npm run planes:test-integracion` · files: scripts/test/test-integracion-planes.ts, .evidence/REQ-021/SP-14.integration.json · resources: package.json scripts · covers: R17, R18, R19, R20 · kind: test · subplan: SP-14

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  `next build` + `next start` on a loopback port against the isolated schema; Playwright contexts: signed out with `es-CO` (sign-in link → /planes, COP), signed out with `en-US` (USD), signed-in Entusiasta (account menu → /planes); widths 390 and 1280 (no horizontal scroll), keyboard Tab order; `--solo sin-sesion` requests a sample of mapped pages and APIs without a session after visiting /planes and expects redirect/401. Writes `.evidence/REQ-021/SP-14.integration.json`. npm script `planes:test-integracion` = `tsx scripts/test/test-integracion-planes.ts`.

  - Acceptance / integration: On a production build started with next start against the REQ-021 test database, a signed-out browser follows the sign-in screen's plans link to the four plans with COP prices, an English browser sees the same plans with USD prices, a signed-in Entusiasta reaches the section from the account menu, and the page fits 390 and 1280 pixel widths without horizontal scrolling with every link reachable by keyboard. Check: `npm run planes:test-integracion`
  - Acceptance / integration: Opening /planes without a session makes no other page or API reachable without a session. Check: `npm run planes:test-integracion -- --solo sin-sesion`

- [ ] T14.5 — SP-14 visual review against the planes@v1 contract · repo: pictures · after: T14.4 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-14.visual.findings.json` · files: .evidence/REQ-021/SP-14.visual.md, .evidence/REQ-021/SP-14.visual.findings.json · resources: ledger:SP-14-visual · covers: R18, R19, R20 · kind: audit · subplan: SP-14

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit), Spanish and English.

  - Acceptance / static: The rendered plans section, its link on the sign-in screen and its entry in the account menu match the approved planes@v1 contract at phone, tablet and desktop widths in Spanish and English, and every finding is recorded with the task to redo in the SP-14 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-14.visual.findings.json`

- [ ] T14.6 — SP-14 audit: catalogue use, public route and copy · repo: pictures · after: T14.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-14.findings.json` · files: .evidence/REQ-021/SP-14.audit.md, .evidence/REQ-021/SP-14.findings.json · resources: ledger:SP-14 · covers: R17, R18, R19, R20 · kind: audit · subplan: SP-14

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Checks at least: no price, plan name or tool written outside `catalogo.ts`; `/planes` is the only new public entry and the proxy still denies everything else without a session; no purchase/request control; no invented marketing copy or limit values; Accept-Language handling cannot inject markup.

  - Acceptance / static: An independent audit of SP-14 records every confirmed defect with the task that must redo it in the SP-14 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-14.findings.json`

<!-- /SP-14 tasks -->

<!-- CG-4 tasks -->

  Composition gate CG-4: SP-1, SP-2, SP-14 (cumulative, after CG-1); it closes M1.

- [ ] T94 — Composition check CG-4: access plans from the plans section to the accounts screen · repo: pictures · after: T14.6 · verify: `npm run planes:test-composicion` · files: scripts/test/test-composicion-planes.ts, .evidence/REQ-021/CG-4.integration.json · resources: package.json scripts, candidate:CG-4 · covers: R16, R17, R19 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 60 minutes.
  Reuses the helpers of T2.6 and T14.4; npm script `planes:test-composicion` = `tsx scripts/test/test-composicion-planes.ts`.

  - Acceptance / integration: On the integrated M1 candidate started with next start against the REQ-021 test database, a signed-out visitor follows the sign-in screen's plans link to the four plans, an administrator moves a Designer account to Designer Plus on the accounts screen and that person's next request opens the cost calculator but not the Taller 3D, and the plan names offered on the accounts screen are exactly the four the plans section shows. Check: `npm run planes:test-composicion`

<!-- /CG-4 tasks -->

### M2 — Saved work, Taller essentials, spend per user and the chat tools
Each signed-in user saves and reopens projects and decorations from any browser, every paid AI call is attributed to a user and a session, and the assisted chat is three separate tools gated by access plan; the new table types and Backing structures the owner approved are modelled and reachable in the Taller, and the Blender file covers every element type of the scene.

- **SP-3 — Taller essentials: researched and modelled Backing and table types, type cards and every-type Blender export** (no design contract; reuse existing Fondos y muebles patterns, no new screens): The owner approves, from a sourced proposal, which new Backing structures and table types the pilot gets; the Taller models them as parametric tables and parametric furniture through exhaustive type registries and integrates them with search, scene AI, photo reading, English phrases and the shopping list; Fondos y muebles offers one card per table type (the eight existing types, rectangular included, plus the new ones) that adds it at its default size and opens the existing table editor, and one Backing group with the seven existing props moved from their former groups plus the new ones; the GLB of every element type the code enumerates, alone and in one full scene, opens in portable Blender LTS with the same layout, sizes in metres and base colours, or the failing type is listed as a defect. Covers R9, R10, R11.

<!-- SP-3 tasks -->

  **Moved to M2 (owner 2026-10-27, answer B)** so M1 (SP-1, SP-2, SP-14) integrates and ships without the Backing and table modelling; SP-3 still lands before the pilot (2026-11-16). Per the owner (2026-10-27) the research is not done during planning: T3.2 runs it during execution and the owner approves the list then (T3.4 records it). What the plan fixes now is SP-3's behavior and the exact code changes: every task's full spec (files, registries, schemas, tests, commands) is its objective in PLAN.json, repeated below as «Spec».
  **Contracts.** T3.3 defines taller-scene@1 (IF-1: TIPOS_DE_PIEZA with all 17 piece types, modulo included; elementosEnumerables(); IDS_BACKING; the exhaustive table registries) and taller-catalogue@1 (IF-2: what the cards and the Backing group read). Completeness is enforced twice: `npx tsc --noEmit` (tsx does not type-check) and the runtime suite `test-taller-registros-completos.ts`. New Backings are parametric furniture (clase mueble) built from caja, cilindro and panel, plus a new scenography form when an approved candidate needs one (owner, round 14: more work and time in SP-3, accepted); FORMAS_ESCENOGRAFIA keeps forms exhaustive. SP-4 consumes taller-scene@1 as a contract (after T3.3), not SP-3's publication.
  **Schedule.** About 2045 agent minutes (~34 h, uncalibrated, sized for up to six new Backings and three new table types) plus the owner's approval wait after T3.2; T3.2 and T3.3 can start as soon as their prerequisites allow (T3.2 has none, T3.3 follows SP-1's audit T1.8). A larger approved list stops at T3.4 (ENVELOPE_EXCEEDED) for a plan amendment.
  DAG: T3.2 (research, owner approval) → T3.4 (record approval); T1.8b → T3.3 (registries, interface contracts) → {T3.5 tables, T3.6 Backings (both after T3.4) → T3.7 photo reading} → T3.8 checkpoint → {T3.9 type cards → T3.10 Backing group, T3.11 every-type GLB} → T3.12 harness and Blender → T3.13 integration → T3.15 audit; CG-2 (T92) after T94 and T3.15.

- [ ] T3.2 — Research new Backing structures and table types, write the validated proposal and get the owner's approval · repo: pictures · verify: `npx tsx scripts/taller/validar-propuesta-piloto.ts docs/req021/propuesta-backing-mesas.json` · files: scripts/taller/propuesta-piloto-esquema.ts, docs/req021/propuesta-backing-mesas.md, docs/req021/propuesta-backing-mesas.json, scripts/taller/validar-propuesta-piloto.ts, scripts/taller/test-validar-propuesta-piloto.ts · resources: taller:catalogue-proposal · covers: R9, R11 · kind: research · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 150 minutes.
  Spec: Write the owner-facing proposal of new Backing structures and table types and its machine-readable twin, both validated, and obtain the owner's named approval; no product source file changes. (1) New scripts/taller/propuesta-piloto-esquema.ts exports zod schemas. PropuestaPilotoSchema = { version: 1, fecha (ISO date), existentes: { backings: exactly panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico; mesas: exactly the eight TIPOS_MESA }, backings: Backing[], mesas: Mesa[] }. Backing = { id (/^[a-z][a-z0-9_]{2,39}$/), nombre { es, en }, descripcion { es, en }, medidasCm { ancho, fondo, alto } (positive, at most 600), coloresHex (1 to 3 #rrggbb), acabados (values of AcabadoEscenografia), grupo ('fondo' or 'decorado'), geometria: [{ forma: 'caja' | 'cilindro' | 'panel', proposito } | { forma: 'nueva', nombreForma, descripcion, parametros: [{ nombre, unidad }] (one or more), porQueNoBasta, estimacionMin, proposito }] (existing primitives of escenografia.ts, or one new shape T3.6 will add), sinonimos (at least one), relevanciaFoto ('alta' | 'media' | 'baja'), fuentes: [{ url or repository photo path, nota }] (at least one), estimacionMin (integer), rango (integer) }. Mesa = { tipo (same id pattern), nombre { es, en }, singular (es), contorno (text description of the top outline), limitesCm { ancho: [min, max], fondo: [min, max] or null, alto: [min, max] }, partidaCm { ancho, fondo, alto } inside the limits, medidaPrincipal ('diametro' | 'lado' | 'largo' | 'ancho_total'), etiquetas { ancho, fondo or null }, reglaSillas { lados: string[], capacidadPartida (integer >= 0) }, admiteCamino (boolean), simetrica (boolean), sinonimos, fuentes, estimacionMin, rango }. AprobacionPilotoSchema = { propuestaSha256 (64 hex), aprobadoPor: 'owner', fecha, backings: string[] (ids), mesas: string[] (tipos), notas (optional) }. (2) docs/req021/propuesta-backing-mesas.json conforms to PropuestaPilotoSchema; docs/req021/propuesta-backing-mesas.md is the Spanish owner-facing version: one ranked row per candidate with name, picture or link, dimensions, sources and estimate, marking which fit the planning envelope of up to six Backings and three table types, and, whenever a candidate needs a new shape, its name, drawing, justification and own estimate, so extra work is approved knowingly (owner, round 14). Sources: the owner reference photos and ideas in the repository (src/lib/globos3d/referencias-dueno.ts, src/lib/globos3d/ideas-sempertex/) and public balloon-decoration supplier and event-rental catalogues, each cited by URL. (3) New scripts/taller/validar-propuesta-piloto.ts <propuesta.json> [--aprobacion <aprobacion.json>] exits 0 when the proposal parses, every partidaCm lies inside its limits, every id or tipo is new against FONDOS_CATALOGO (src/lib/globos3d/fondos-escenografia.ts) and TIPOS_MESA (src/lib/globos3d/mobiliario-conjunto-tipos.ts) and unique in the file, and existentes is exact; with --aprobacion it also parses AprobacionPilotoSchema, checks that propuestaSha256 equals the SHA-256 of the proposal file bytes and that every approved id is in the proposal, and exits 3 printing ENVELOPE_EXCEEDED when more than six Backings or three table types are approved; every failure prints the field path and exits non-zero. (4) New scripts/taller/test-validar-propuesta-piloto.ts (node:test) covers a valid proposal, a colliding id, a default outside limits, a missing source, a wrong existing list, a new form without parameters, justification or estimate, a hash mismatch and an envelope overflow. Approval: the coordinator shows the owner the .md; the owner names the approved ids (or none); the coordinator writes /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/aprobacion-backing-mesas.json (outside the repository) in AprobacionPilotoSchema form with the SHA-256 of the proposal JSON.

  - Acceptance / static: The proposal JSON conforms to PropuestaPilotoSchema: every candidate Backing structure and table type has Spanish and English names, real reference dimensions with at least one cited source, limits and a default inside them, the chair rule for tables, geometry for Backings from caja, cilindro and panel or a new form described with its parameters, justification and estimate, photo-reading relevance, synonyms and an estimate; it lists the seven existing Backing ids and the eight table types as kept, and no candidate id collides with FONDOS_CATALOGO, TIPOS_MESA or another candidate. Check: `npx tsx scripts/taller/validar-propuesta-piloto.ts docs/req021/propuesta-backing-mesas.json`
  - Acceptance / functional: The proposal validator rejects a colliding id, a default outside its limits, a missing source, a wrong list of existing pieces, a new Backing form without parameters, justification or estimate, an approval whose SHA-256 does not match the proposal and an approval above the envelope, naming the failing field. Check: `npx tsx --test scripts/taller/test-validar-propuesta-piloto.ts`
  - Acceptance / product: The owner approved a named subset of the proposal, recorded in the requirement folder as aprobacion-backing-mesas.json with the proposal file's SHA-256, before any modelling task starts. Check: owner attestation (manual)

- [ ] T3.3 — Make the table, piece and Backing registries exhaustive and add the Backing extension points · repo: pictures · after: T1.8b · verify: `npx tsc --noEmit` · files: src/lib/globos3d/mobiliario-conjunto-tipos.ts, src/lib/globos3d/mobiliario-mesas-param.ts, src/lib/globos3d/mobiliario-conjunto.ts, src/lib/globos3d/herramientas-escena-mesas.ts, src/lib/globos3d/herramientas-escena.ts, src/lib/globos3d/tipos-escena.ts, src/lib/globos3d/fondos-backing.ts, src/lib/globos3d/fondos-escenografia.ts, src/lib/globos3d/backing.ts, scripts/test/test-taller-registros-completos.ts, scripts/test/test-catalogo-dorado.ts, scripts/test/dorado/catalogo-mesas-nuevas.json, scripts/test/dorado/catalogo-backing-nuevos.json, scripts/test/test-mobiliario-libre.ts, scripts/test/test-anadir-repositorios.tsx, src/lib/globos3d/escenografia.ts · resources: taller:scene, taller:furniture-model, taller:catalogue · covers: R9, R10, R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 240 minutes.
  Spec: Paths without a folder are under src/lib/globos3d/; test-* and dorado/ paths are under scripts/test/. Turn every per-type spot of the Taller into an exhaustive registry so new table, piece or Backing types become compiler-checked data changes that leave existing pieces unchanged; this defines contracts taller-scene@1 and taller-catalogue@1. (1) In mobiliario-conjunto-tipos.ts, next to NOMBRE_MESA, LIMITES_MESA, PARTIDA_MESA and FONDO_DEL_ANCHO, add Readonly<Record<TipoMesa, ...>> registries: MEDIDA_PRINCIPAL_MESA ('diametro' | 'lado' | 'largo' | 'ancho_total', the dimension medidaDeMesa prints), ETIQUETA_MEDIDAS_MESA ({ ancho: string; fondo: string | null }, today's editor labels Diámetro, Lado, Largo, Ancho total and Ancho de la mesa), SINONIMOS_MESA (readonly string[] search words: today's TEXTO_CONJUNTO words of FondosYMuebles.tsx split per type, plus «rectangular» for rectangular), MESA_ADMITE_CAMINO (boolean, true exactly for redonda, cuadrada, rectangular and ovalada), MESA_SIMETRICA (boolean, true exactly for redonda, cuadrada, rectangular, ovalada and coctel) and SINGULAR_MESA (the noun for sentences such as the status line). (2) In mobiliario-mesas-param.ts derive ADMITE_CAMINO and SIMETRICAS from those registries instead of literal Sets. (3) In mobiliario-conjunto.ts make medidaDeMesa read MEDIDA_PRINCIPAL_MESA instead of its if-chain and add sillasDePartida(tipo: TipoMesa): number = min(8, the capacity sillasParaMesa reports for PARTIDA_MESA[tipo] with the default chair). (4) In herramientas-escena-mesas.ts generate the tipo describe text of the scene-AI table tools from TIPOS_MESA, NOMBRE_MESA and SINONIMOS_MESA instead of hand-written strings. (5) New tipos-escena.ts exports TIPOS_DE_PIEZA = { columna: true, ..., modulo: true } as const satisfies Record<TipoPieza, true> (TipoPieza from piezas.ts, all 17 types), LISTA_TIPOS_DE_PIEZA (its keys) and elementosEnumerables(): readonly ElementoEnumerable[], with ElementoEnumerable = { clase: 'pieza'; tipo: TipoPieza } | { clase: 'mesa'; tipo: TipoMesa } | { clase: 'silla'; tipo: TipoSilla } | { clase: 'backing'; id: string } | { clase: 'forma'; forma: FormaEscenografia } | { clase: 'sala' }, listing every piece type, TIPOS_MESA type, TIPOS_SILLA type, IDS_BACKING id, scenography form and the room, in that order. Escenografia.ts gains FormaEscenografia (the union's discriminant), FORMAS_ESCENOGRAFIA satisfying Record<FormaEscenografia, true>, and an exhaustive never-checked switch inside armarEscenografia, so any shape T3.6 adds breaks compilation until built, rendered and listed. TIPOS_PIEZA in herramientas-escena.ts becomes LISTA_TIPOS_DE_PIEZA, so esquema-escena.ts accepts scenes holding modulo pieces (rejected today). (6) New fondos-backing.ts exports BACKING_NUEVOS: readonly MuebleCatalogo[] = [] (filled by T3.6), and FONDOS_CATALOGO in fondos-escenografia.ts becomes [...FONDOS_BASE, ...CATALOGO_MOBILIARIO, ...BACKING_NUEVOS]. (7) New backing.ts exports IDS_BACKING_EXISTENTES (panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico), IDS_BACKING = [...IDS_BACKING_EXISTENTES, ...BACKING_NUEVOS ids], esBacking(id): boolean and grupoVisibleDe(f: FondoCatalogo): 'backing' or the entry's current visual group, without changing any entry's semantic grupo, clase or repository. (8) Tests: new test-taller-registros-completos.ts asserts at runtime that every Record<TipoMesa> registry has exactly the TIPOS_MESA keys, TIPOS_DE_PIEZA has the 17 keys including modulo, every IDS_BACKING id is in FONDOS_CATALOGO and assigned to escenografia in ASIGNACION_FONDOS, elementosEnumerables() lists each element once, medidaDeMesa, the tool describe text, ADMITE_CAMINO, SIMETRICAS and sillasDePartida give today's results for the eight types, and a scene holding a modulo piece validates; test-catalogo-dorado.ts keeps dorado/catalogo-fondos.json byte-identical for the pre-existing catalogue entries and table types and compares entries and table types added later against new goldens dorado/catalogo-mesas-nuevas.json and dorado/catalogo-backing-nuevos.json (both start as empty lists; --escribir writes only those two); test-mobiliario-libre.ts asserts that the first eight TIPOS_MESA are the existing types in their order instead of TIPOS_MESA.length === 8; test-anadir-repositorios.tsx writes its card counts as expressions of BACKING_NUEVOS.length (Escenografía 25 + n, Todos 52 + n) while its DORADO_DE_SIEMPRE hashes stay unchanged. No UI change.

  - Acceptance / static: Every per-type registry of tables, piece types, Backings and scenography forms is exhaustive: TypeScript rejects a table type, piece type, Backing or form missing from any registry, and the type check of the whole application passes. Check: `npx tsc --noEmit`
  - Acceptance / functional: At runtime every table registry has exactly the TIPOS_MESA keys, TIPOS_DE_PIEZA lists the 17 piece types including modulo, every IDS_BACKING id is a catalogue prop assigned to the Escenografía repository, elementosEnumerables() lists each piece type, table type, chair type, Backing and scenography form once plus the room, and a saved scene holding a modulo piece validates. Check: `npx tsx --conditions=react-server scripts/test/test-taller-registros-completos.ts`
  - Acceptance / functional: The eight existing table types, their dimension text, AI tool descriptions, table-runner and symmetry rules and default chair counts give exactly the same results as before the registries. Check: `npx tsx --conditions=react-server scripts/test/test-taller-registros-completos.ts`
  - Acceptance / regression: The catalogue golden suite passes with the pre-existing catalogue entries and table types byte-identical to scripts/test/dorado/catalogo-fondos.json. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-dorado.ts`
  - Acceptance / regression: The free furniture suite passes with the first eight table types unchanged and in their order. Check: `npx tsx --conditions=react-server scripts/test/test-mobiliario-libre.ts`
  - Acceptance / regression: The existing chairs-per-table suite passes unchanged after the registries. Check: `npx tsx --conditions=react-server scripts/test/test-sillas-por-mesa.ts`
  - Acceptance / regression: The Añadir panel suite passes with its card counts written from BACKING_NUEVOS.length and its rendered-HTML hashes unchanged. Check: `npx tsx scripts/test/test-anadir-repositorios.tsx`

- [ ] T3.4 — Record the owner-approved list of new Backings and table types in the repository · repo: pictures · after: T3.2 · verify: `cmp -- docs/req021/aprobacion-backing-mesas.json /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/aprobacion-backing-mesas.json` · files: docs/req021/aprobacion-backing-mesas.json · resources: taller:catalogue-proposal · covers: R9, R11 · kind: docs · subplan: SP-3 · ui: no

  Classification: complexity low; scope isolated_fix; risk medium; coupling medium; confidence high; estimate 20 minutes.
  Spec: Copy the owner approval the coordinator wrote, /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/aprobacion-backing-mesas.json, byte for byte to docs/req021/aprobacion-backing-mesas.json and validate it against the committed proposal with npx tsx scripts/taller/validar-propuesta-piloto.ts docs/req021/propuesta-backing-mesas.json --aprobacion docs/req021/aprobacion-backing-mesas.json. T3.5 models exactly the approved mesas and T3.6 exactly the approved backings. If the validator prints ENVELOPE_EXCEEDED (more than six Backings or three table types approved), stop and report it: the coordinator amends the plan to re-estimate T3.5 and T3.6 before they start. An approval with no new table or no new Backing is valid; the matching modelling task then only proves that nothing changed.

  - Acceptance / static: docs/req021/aprobacion-backing-mesas.json is byte-identical to the owner approval recorded in the requirement folder. Check: `cmp -- docs/req021/aprobacion-backing-mesas.json /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/aprobacion-backing-mesas.json`
  - Acceptance / static: The recorded approval matches the SHA-256 of the committed proposal, names only candidates of the proposal and stays within the envelope of six Backings and three table types. Check: `npx tsx scripts/taller/validar-propuesta-piloto.ts docs/req021/propuesta-backing-mesas.json --aprobacion docs/req021/aprobacion-backing-mesas.json`

- [ ] T3.5 — Model the approved new table types in the parametric table generator · repo: pictures · after: T3.3, T3.4 · verify: `npx tsx --conditions=react-server scripts/test/test-taller-mesas-nuevas.ts` · files: src/lib/globos3d/mobiliario-conjunto-tipos.ts, src/lib/globos3d/mobiliario-mesas-param.ts, src/lib/globos3d/mobiliario-contornos.ts, src/lib/globos3d/mobiliario-perimetro.ts, src/lib/globos3d/mobiliario-conjunto-ingles.ts, scripts/test/test-taller-mesas-nuevas.ts, scripts/test/dorado/catalogo-mesas-nuevas.json · resources: taller:furniture-model · covers: R9 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence low; estimate 270 minutes.
  Spec: For each table type listed under mesas in docs/req021/aprobacion-backing-mesas.json, using its entry in docs/req021/propuesta-backing-mesas.json: append the tipo to TIPOS_MESA after the eight existing types and fill every registry of src/lib/globos3d/mobiliario-conjunto-tipos.ts (NOMBRE_MESA, LIMITES_MESA, PARTIDA_MESA, FONDO_DEL_ANCHO, MEDIDA_PRINCIPAL_MESA, ETIQUETA_MEDIDAS_MESA, SINONIMOS_MESA, MESA_ADMITE_CAMINO, MESA_SIMETRICA, SINGULAR_MESA) from the proposal, in cm; add its top outline in src/lib/globos3d/mobiliario-contornos.ts (it feeds the tablecloth, the skirt, the chair perimeter and the surface for centrepieces), its geometry case in armarMesa (src/lib/globos3d/mobiliario-mesas-param.ts), its chair distribution in src/lib/globos3d/mobiliario-perimetro.ts when the outline needs one, and its English phrase in src/lib/globos3d/mobiliario-conjunto-ingles.ts. MesaGuardadaSchema and the scene-AI tool enums read TIPOS_MESA and the tool descriptions are generated (T3.3), so saved scenes and the scene AI accept the new types without other changes; the shopping-list line comes from nombreDeMesa and medidaDeMesa (src/lib/globos3d/biblioteca.ts nombreEnLista). New scripts/test/test-taller-mesas-nuevas.ts covers, for every new type: bounds at its limits and default within 1 mm; chairs along the real outline without overlapping the top or each other; requested, placed and capacity counts; the shopping-list line with dimensions and actual chair count and no price; parity of the scene-AI table tools with manual editing through the deterministic tool executor, without a paid call; and, for the eight existing types, unchanged tables and chairs. Pin the new types in scripts/test/dorado/catalogo-mesas-nuevas.json with scripts/test/test-catalogo-dorado.ts --escribir (it writes only the new goldens). If the approval lists no table type, change no source; the test then asserts that TIPOS_MESA still holds exactly the eight types.

  - Acceptance / functional: Every approved new table type is a parametric table type with its Spanish name, limits, default size, top outline, tablecloth and legs, and the built table's bounds equal the requested length, depth and height within 1 mm at its limits and default. Check: `npx tsx --conditions=react-server scripts/test/test-taller-mesas-nuevas.ts`
  - Acceptance / functional: Chairs of every approved new table type are placed along its real outline without overlapping the top or each other, requested versus placed chairs and capacity are reported, and the shopping list shows the table with its dimensions and the actual chair count without a rental price. Check: `npx tsx --conditions=react-server scripts/test/test-taller-mesas-nuevas.ts`
  - Acceptance / functional: The eight existing table types, their saved scenes, the salon layout and the AI table tools produce exactly the same tables and chairs as before, and the AI table tools accept every new type with the same result as manual editing without a paid AI call. Check: `npx tsx --conditions=react-server scripts/test/test-taller-mesas-nuevas.ts`
  - Acceptance / static: The type check passes with every table registry filled for the new types. Check: `npx tsc --noEmit`
  - Acceptance / regression: The existing chairs-per-table suite passes unchanged with the new table types in the catalogue. Check: `npx tsx --conditions=react-server scripts/test/test-sillas-por-mesa.ts`
  - Acceptance / regression: The existing parametric salon suite passes unchanged with the new table types in the catalogue. Check: `npx tsx --conditions=react-server scripts/test/test-salon-mesas-parametricas.ts`
  - Acceptance / regression: The catalogue golden suite passes with the pre-existing entries unchanged and the new table types pinned in scripts/test/dorado/catalogo-mesas-nuevas.json. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-dorado.ts`

- [ ] T3.6 — Model the approved new Backing structures as parametric Taller furniture · repo: pictures · after: T3.3, T3.4 · verify: `npx tsx --conditions=react-server scripts/test/test-backing-nuevos.ts` · files: src/lib/globos3d/fondos-backing.ts, src/lib/catalogo/asignacion-fondos.ts, src/lib/globos3d/escenografia-ingles.ts, scripts/test/test-backing-nuevos.ts, scripts/test/dorado/catalogo-backing-nuevos.json, src/lib/globos3d/escenografia.ts, src/components/tres-d/escenografia-visor.ts, src/components/tres-d/DibujoFondo.tsx, src/lib/globos3d/piezas.ts, scripts/test/test-formas-escenografia-nuevas.ts · resources: taller:catalogue · covers: R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence low; estimate 480 minutes.
  Spec: For each Backing listed under backings in docs/req021/aprobacion-backing-mesas.json, using its entry in docs/req021/propuesta-backing-mesas.json, add a MuebleCatalogo to BACKING_NUEVOS in src/lib/globos3d/fondos-backing.ts with the same shape as the furniture of src/lib/globos3d/mobiliario-catalogo.ts built with mueble({...}): clase 'mueble', id, nombre, descripcion, medidas { anchoCm, fondoCm, altoCm }, colores, acabado, grupo ('fondo' or 'decorado') and armar(medidas, colores), where armar builds ElementoEscenografia with the forms of src/lib/globos3d/escenografia.ts scaled to the requested measures, so the prop is parametric in size and colour like the other furniture. Owner round 14 allows new forms: when an approved geometry names one, first add it as a union member of ElementoEscenografia and SolidoEscenografia carrying the proposal's parameters, plus its armarEscenografia branch, visor mesh (escenografia-visor.ts; flat outline in DibujoFondo.tsx), bounds helper (piezas.ts) and FORMAS_ESCENOGRAFIA entry; test-formas-escenografia-nuevas.ts checks each one: bounds at three sizes, mesh vertices, colour and finish. Add every new id to ESCENOGRAFIA in src/lib/catalogo/asignacion-fondos.ts and its English phrase to ESCENOGRAFIA_EN in src/lib/globos3d/escenografia-ingles.ts. Because FONDOS_CATALOGO appends BACKING_NUEVOS and IDS_BACKING reads it (T3.3), the Añadir panel, the scene-AI furniture tool (its id enum comes from FONDOS_CATALOGO), the photo-reading prompt and the shopping list («Escenografía · no es producto de la tienda», with quantity) see the new ids without other changes. New scripts/test/test-backing-nuevos.ts covers, per new Backing: bounds within 1 mm of the requested measures at the default and at two other sizes; only forms listed in FORMAS_ESCENOGRAFIA; colours applied; found by name in the Fondos y muebles search; present in the scene-AI furniture enum; English phrase present; shopping-list line with quantity and no price. Pin the new entries in scripts/test/dorado/catalogo-backing-nuevos.json with scripts/test/test-catalogo-dorado.ts --escribir. If the approval lists no Backing, change no source; the test then asserts BACKING_NUEVOS is empty.

  - Acceptance / functional: Every approved new Backing structure is a parametric catalogue furniture prop (clase mueble) with a new stable id, Spanish name, description, real dimensions, colours and finishes, built from caja, cilindro, panel and the new forms its approval names, whose bounds match the requested dimensions within 1 mm at its default and at other sizes, and is assigned to the Escenografía repository. Check: `npx tsx --conditions=react-server scripts/test/test-backing-nuevos.ts`
  - Acceptance / functional: Every approved new Backing is found by its name in the Fondos y muebles search, offered to the scene AI furniture tool, described by an English phrase for image prompts and listed in the shopping list as not a store product with its quantity. Check: `npx tsx --conditions=react-server scripts/test/test-backing-nuevos.ts`
  - Acceptance / regression: The catalogue repository suite passes with every new Backing assigned to the Escenografía repository and no unassigned entry. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-repositorios.ts`
  - Acceptance / regression: The Añadir panel suite passes with the Escenografía card count grown by exactly the number of approved Backings. Check: `npx tsx scripts/test/test-anadir-repositorios.tsx`
  - Acceptance / regression: The catalogue golden suite passes with the pre-existing entries unchanged and the new Backings pinned in scripts/test/dorado/catalogo-backing-nuevos.json. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-dorado.ts`

- [ ] T3.7 — Teach photo reading the approved new Backing structures · repo: pictures · after: T3.6 · verify: `npx tsx --conditions=react-server scripts/test/test-lectura-backing-nuevos.ts` · files: src/lib/globos3d/fondos-sinonimos.ts, src/lib/globos3d/fondos-familias.ts, src/lib/globos3d/compilar-lectura.ts, scripts/test/test-lectura-backing-nuevos.ts · resources: taller:photo-reading · covers: R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 90 minutes.
  Spec: Photo reading already lists every FONDOS_CATALOGO prop in its prompt and reading schema (src/lib/globos3d/prompt-lectura-foto.ts) and compiles a read furniture id generically through mobiliarioLeido (src/lib/globos3d/compilar-mobiliario.ts), so new Backings of clase mueble need: their reading synonyms (the proposal's sinonimos) in SINONIMOS_DE_FONDO (src/lib/globos3d/fondos-sinonimos.ts) and their family in FAMILIAS (src/lib/globos3d/fondos-familias.ts) when the proposal relates them to an existing family. src/lib/globos3d/compilar-lectura.ts changes only if a new Backing needs a dedicated compile rule, which the task report justifies. New scripts/test/test-lectura-backing-nuevos.ts uses deterministic readings, no paid model call: the prompt lists each new id; a reading that names it or one of its synonyms compiles into that prop with its measured size and colours; an unnamed box is not turned into that prop. scripts/test/test-compilar-lectura.ts (the owner reference photos read by hand) must stay identical. If the approval lists no Backing, the test asserts that IDS_BACKING holds only the seven existing ids and the regression passes.

  - Acceptance / functional: Photo reading knows every approved new Backing: the reading prompt lists it, a deterministic reading that names it or one of its synonyms compiles into that prop with its measured size and colours, and a box the reader did not name is not invented as that prop. Check: `npx tsx --conditions=react-server scripts/test/test-lectura-backing-nuevos.ts`
  - Acceptance / regression: The owner reference photos compile exactly as before, so the seven existing Backing props and the other catalogue props keep their photo discovery. Check: `npx tsx --conditions=react-server scripts/test/test-compilar-lectura.ts`

- [ ] T3.1 — Repair what blocks T3.8 · repo: pictures · after: T3.5, T3.7 · files: src/lib/globos3d/mobiliario-conjunto-tipos.ts, src/lib/globos3d/mobiliario-mesas-param.ts, src/lib/globos3d/mobiliario-conjunto.ts, src/lib/globos3d/herramientas-escena-mesas.ts, src/lib/globos3d/herramientas-escena.ts, src/lib/globos3d/tipos-escena.ts, src/lib/globos3d/fondos-backing.ts, src/lib/globos3d/fondos-escenografia.ts, src/lib/globos3d/backing.ts, scripts/test/test-taller-registros-completos.ts, scripts/test/test-catalogo-dorado.ts, scripts/test/dorado/catalogo-mesas-nuevas.json, scripts/test/dorado/catalogo-backing-nuevos.json, scripts/test/test-mobiliario-libre.ts, scripts/test/test-anadir-repositorios.tsx, src/lib/globos3d/escenografia.ts · resources: taller:catalogue, taller:furniture-model, taller:scene · covers: R10, R11, R9 · kind: implement · subplan: SP-3 · ui: no

  Repair task added by the run's self-repair (legacy runtime) when T3.8 could not pass; completed and inherited by the durable run. Objective, criteria and evidence are in PLAN.json.

- [ ] T3.14 — Repair what blocks T3.8 · repo: pictures · after: T3.5, T3.7, T3.1 · files: .evidence/REQ-021/SP-3.checkpoint.json · resources: taller:scene · covers: R11, R9 · kind: implement · subplan: SP-3

  Repair task added by the run's self-repair (legacy runtime) when T3.8 could not pass; completed and inherited by the durable run. Objective, criteria and evidence are in PLAN.json.

- [ ] T3.8 — Checkpoint: run the registry and modelling suites before Taller UI and export work · repo: pictures · after: T3.5, T3.7, T3.1, T3.14 · verify: `npx tsc --noEmit` · files: .evidence/REQ-021/SP-3.checkpoint.json · resources: taller:scene · covers: R9, R11 · kind: test · subplan: SP-3 · ui: no

  Classification: complexity low; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  Spec: Run, on one tree and without repairs, the suites authored by T3.3, T3.5, T3.6 and T3.7 plus the existing regressions, and write .evidence/REQ-021/SP-3.checkpoint.json with the tree identity and each command's exit status and summary. A failure sends back only the task whose suite failed.

  - Acceptance / static: Before any Taller UI or export work, the type check passes on the checkpoint tree. Check: `npx tsc --noEmit`
  - Acceptance / functional: Before any Taller UI or export work, the registry completeness suite passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-taller-registros-completos.ts`
  - Acceptance / functional: Before any Taller UI or export work, the new table types suite passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-taller-mesas-nuevas.ts`
  - Acceptance / functional: Before any Taller UI or export work, the new Backing props suite passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-backing-nuevos.ts`
  - Acceptance / functional: Before any Taller UI or export work, the photo-reading suite of the new Backings passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-lectura-backing-nuevos.ts`
  - Acceptance / regression: Before any Taller UI or export work, the existing chairs-per-table suite passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-sillas-por-mesa.ts`
  - Acceptance / regression: Before any Taller UI or export work, the catalogue golden suite passes on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-dorado.ts`
  - Acceptance / regression: Before any Taller UI or export work, the owner reference photos compile as before on the checkpoint tree. Check: `npx tsx --conditions=react-server scripts/test/test-compilar-lectura.ts`

- [ ] T3.9 — One creation card per table type in Fondos y muebles · repo: pictures · after: T3.8 · verify: `npx tsx scripts/test/test-taller-mesas-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/lib/globos3d/mobiliario-conjunto-escena.ts, src/components/tres-d/EditorConjuntoMesa.tsx, src/lib/catalogo/anadir-repositorios.ts, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-taller-mesas-piloto.ts, scripts/test/test-anadir-repositorios.tsx, scripts/test/test-anadir-repositorios-ui.ts · resources: taller:anadir-panel · covers: R9 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk low; coupling medium; confidence medium; estimate 120 minutes.
  Spec: In the existing «Mesas» group, reuse the current Fondos y muebles card markup and responsive grid; add no screen or navigation. Replace the single «Mesa con sillas a medida» card of the «Mesas» group in src/components/tres-d/FondosYMuebles.tsx with one card per TIPOS_MESA type (the eight existing types and the approved new ones, in TIPOS_MESA order, after the fixed catalogue tables, which stay), each named NOMBRE_MESA[tipo], with a thumbnail of that type at its PARTIDA_MESA size and search text NOMBRE_MESA plus SINONIMOS_MESA, so «rectangular» finds the Rectangular card; TEXTO_CONJUNTO goes away. Touching a card calls agregarConjuntoPorDefecto(escena, maxNodos, tipo) (src/lib/globos3d/mobiliario-conjunto-escena.ts; today it always builds a redonda with 8 chairs), which adds that type at its PARTIDA_MESA size with sillasDePartida(tipo) chairs, selects it, opens the existing table editor and shows the existing status line naming the type with SINGULAR_MESA. In src/components/tres-d/EditorConjuntoMesa.tsx the dimension labels come from ETIQUETA_MEDIDAS_MESA instead of the etiquetaAncho if-chain; controls, capacity warning and undo stay. contarFondosYMuebles and fijasDe (src/lib/catalogo/anadir-repositorios.ts) count the type cards instead of the single card. Every new string goes in src/components/tres-d/textos-taller-esenciales.ts. New scripts/test/test-taller-mesas-piloto.ts covers the cards, the search, the typed default add, the editor labels and limits for every type, capacity warning and undo; in scripts/test/test-anadir-repositorios.tsx and scripts/test/test-anadir-repositorios-ui.ts write the Mobiliario and Todos counts as expressions of TIPOS_MESA.length and re-pin the DORADO_DE_SIEMPRE hashes whose filter shows the «Mesas» group, stating in the task report that the HTML diff only replaces the table card.

  - Acceptance / functional: Fondos y muebles shows one creation card per parametric table type, the eight existing types and every approved new type, each found by searching its name or synonyms (rectangular included); touching a card adds that type at its default size (rectangular 240 × 90 × 75 cm) with as many default chairs as fit up to eight, selects it and opens the existing table editor. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`
  - Acceptance / functional: The existing table editor shows the right dimension labels and limits for every table type and keeps its capacity warning and undo, and the fixed Imperial and other fixed table pieces remain available. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`
  - Acceptance / regression: The repository card counts and the Mobiliario selector count include exactly the table type cards in place of the former single «Mesa con sillas a medida» card. Check: `npx tsx scripts/test/test-anadir-repositorios.tsx`
  - Acceptance / functional: At phone (390 px), tablet (768 px) and desktop (1280 px) widths, table-type cards reuse the existing Fondos y muebles card/grid pattern, stay legible and reachable, and add no screen or navigation. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`

- [ ] T3.10 — Backing group in Fondos y muebles with the seven existing and the new Backing props · repo: pictures · after: T3.9 · verify: `npx tsx scripts/test/test-backing-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-backing-piloto.ts, scripts/test/test-anadir-repositorios.tsx, scripts/test/test-anadir-repositorios-ui.ts · resources: taller:anadir-panel · covers: R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity low; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  Spec: In src/components/tres-d/FondosYMuebles.tsx, reuse the existing Fondos y muebles group and card patterns; add no screen or navigation. Show a «Backing» group, in Fondos y muebles under «Todos» and in the Escenografía repository view, listing every IDS_BACKING prop once (the seven existing ones and the approved new ones) through grupoVisibleDe (src/lib/globos3d/backing.ts), for presentation only: the seven no longer appear in «Fondos y tapetes» or «Decorado de pie», while the entries' semantic grupo, clase, ids, ASIGNACION_FONDOS repository, saved scenes, scene AI and photo reading stay unchanged and Shopify /catalogo is untouched. Searching «Backing» matches every Backing card (the word joins their search text in the panel only) and the original names still match. Cards add by click, drag and keyboard as today. New strings in src/components/tres-d/textos-taller-esenciales.ts. New scripts/test/test-backing-piloto.ts covers group membership, absence from the former groups, search and adding; update the group-dependent counts and re-pin the affected DORADO_DE_SIEMPRE hashes in scripts/test/test-anadir-repositorios.tsx and scripts/test/test-anadir-repositorios-ui.ts, stating in the task report that the HTML diff only moves the seven cards and adds the new ones.

  - Acceptance / functional: Fondos y muebles has one Backing group listing panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico and every approved new Backing once each, the seven no longer appear in «Fondos y tapetes» or «Decorado de pie», and each card adds its prop by click or drag. Check: `npx tsx scripts/test/test-backing-piloto.ts`
  - Acceptance / functional: Searching «Backing» finds every Backing card and the original names still find each prop; ids, repository ownership, saved scenes, scene AI and photo discovery resolve the same ids, and Shopify /catalogo is unchanged. Check: `npx tsx scripts/test/test-backing-piloto.ts`
  - Acceptance / regression: The catalogue repository suite passes with every Backing prop still assigned to its former repository. Check: `npx tsx --conditions=react-server scripts/test/test-catalogo-repositorios.ts`
  - Acceptance / functional: At phone (390 px), tablet (768 px) and desktop (1280 px) widths, the Backing group reuses the existing Fondos y muebles group/card pattern, stays legible and reachable, and adds no screen or navigation. Check: `npx tsx scripts/test/test-backing-piloto.ts`

- [ ] T3.11 — Verify and repair the GLB export of every scene element type · repo: pictures · after: T3.8 · verify: `npx tsx scripts/test/test-glb-todos-los-tipos.ts` · files: src/components/tres-d/exportar-escena-glb.ts, scripts/test/fixtures/escena-por-tipo.ts, scripts/test/lib/leer-glb.ts, scripts/test/lib/glb-por-tipo.ts, scripts/test/test-glb-todos-los-tipos.ts, scripts/test/glb-defectos-conocidos.json, docs/req021-blender.md · resources: taller:scene, taller:export · covers: R10 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 300 minutes.
  Spec: Prove per element type that the Taller's GLB keeps layout, size and base colour, enumerating the types from the code so a new type cannot be skipped. New scripts/test/fixtures/escena-por-tipo.ts exports builders typed as Record<TipoPieza, () => Pieza> plus builders keyed by TipoMesa, TipoSilla, Backing id and FormaEscenografia, giving a minimal scene node for every entry of elementosEnumerables() (src/lib/globos3d/tipos-escena.ts) and a room. New scripts/test/lib/leer-glb.ts decodes a GLB (JSON chunk, accessors, node world transforms, base-colour factors). New scripts/test/lib/glb-por-tipo.ts, run in Playwright Chromium and bundled with esbuild as scripts/test/test-ui-taller-reentrada.ts does, builds one scene per element with crearEscena(canvas) (src/components/tres-d/escena-globos.ts), mostrarArmada(visor, armarEscena(escena)) (src/components/tres-d/armada-visor.ts, src/lib/globos3d/escena.ts) and the visor's GLB exporter (crearExportadoresEscena in src/components/tres-d/exportadores-escena-globos.ts, the path of «Descargar modelo GLB»), and compares world bounds and positions within 1 mm (model cm converted once to metres) and base-colour channels within 1/255 in the same colour space. New scripts/test/test-glb-todos-los-tipos.ts runs it for every element and for one full scene holding all of them. In src/components/tres-d/exportar-escena-glb.ts name the root children decoracion and sala so per-type nodes can be found, and repair every type that fails. A type the GLB cannot carry faithfully is listed with the observed difference in scripts/test/glb-defectos-conocidos.json ({ tipo, propiedad, esperado, observado, motivo }) and in docs/req021-blender.md, and the test reports it as a known defect, never as passing. No network call; the export menu UI does not change.

  - Acceptance / functional: Every element type enumerated by elementosEnumerables(), that is the 17 piece types (columna, arco, pared_malla, pared_trenzas, organico, decoracion, arco_organico, guirnalda, escenografia, globo, forma, letras, metalizado, mural, techo, arbol_globos and modulo), every table type, every chair type, every Backing prop, every scenography form including any new one and the room, exports alone and inside one full scene to a GLB whose decoded nodes keep world positions and bounds within 1 mm in metres and base-colour channels within 1/255, without calling the network. Check: `npx tsx scripts/test/test-glb-todos-los-tipos.ts`
  - Acceptance / functional: Every element type that does not export faithfully is repaired or listed by type with the observed difference in scripts/test/glb-defectos-conocidos.json and the export evidence, and is never reported as passing. Check: `npx tsx scripts/test/test-glb-todos-los-tipos.ts`
  - Acceptance / regression: The Taller export menu keeps its PNG and GLB actions and its preparing, started and error states, and exporting leaves the editor scene unchanged. Check: `npx tsx --conditions=react-server scripts/test/test-exportadores-escena-taller.ts`

- [ ] T3.12 — Implement the Taller browser and Blender verification harness for every element type · repo: pictures · after: T3.10, T3.11 · verify: `npm run taller:test-harness-esenciales` · files: scripts/taller/preparar-blender.ts, scripts/test/blender/verificar_glb.py, scripts/test/blender/comparar_glb.py, scripts/test/blender/test_comparar_glb.py, scripts/test/test-harness-taller-esenciales.ts, scripts/test/test-integracion-taller-esenciales.ts, docs/req021-blender.md, package.json · resources: package.json scripts, taller:export · covers: R9, R10, R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 210 minutes.
  Spec: Paths starting with blender/ or test- are under scripts/test/. New scripts/taller/preparar-blender.ts is the explicit setup step: it downloads the newest official Blender LTS portable Linux archive from a URL and SHA-256 pinned in the script (checked against the published checksum when this task runs), verifies the hash, unpacks it under ~/.local/opt/blender/<version>, points ~/.local/opt/blender/current at it, prints version and executable, never touches pacman, and no test calls it implicitly. New blender/verificar_glb.py runs under blender --background --python: it imports a GLB with the bundled glTF importer and writes JSON with each object's name, world bounds in metres and base colour. New blender/comparar_glb.py compares that JSON with the fixture expectations per element type (1 mm, 1/255) and is unit-tested by blender/test_comparar_glb.py (python3 unittest, no Blender). New test-harness-taller-esenciales.ts tests the harness without Blender or a server: a missing BLENDER_EXECUTABLE or ~/.local/opt/blender/current gives status blocked, never pass; preparar-blender refuses an archive whose hash differs; comparison failures name the element type and property; the evidence writers produce the expected shape. New test-integracion-taller-esenciales.ts: with SP-1's isolated schema and seeded master-designer@ session, next build and next start on loopback; Chromium adds a table from each table type card and every Backing card, loads the every-element fixture of T3.11, downloads the real GLB from «Descargar modelo GLB», imports it with a bounded timeout and writes .evidence/REQ-021/SP-3.integration.json (tree, Blender version, per-type result, known defects, blocked reasons). With --composicion it runs the CG-2 flow on the integrated candidate (master-designer@ completes a table, a Backing and the GLB download; entusiasta@ gets the no-access page on /3d and 403 on its APIs) and writes .evidence/REQ-021/CG-2.integration.json. Document setup and limits in docs/req021-blender.md. Register in package.json: taller:preparar-blender, taller:test-harness-esenciales, taller:test-integracion-esenciales, taller:test-composicion-esenciales (--composicion mode), taller:test-registros-completos, taller:test-mesas-nuevas, taller:test-backing-nuevos, taller:test-lectura-backing-nuevos, taller:test-mesas-piloto, taller:test-backing-piloto and taller:test-glb-todos-los-tipos.

  - Acceptance / functional: Without Blender or a server, the harness self-test proves that a missing Blender executable is reported as blocked and never as passed, that a comparison failure names its element type and property, and that the integration and composition modes write their evidence with per-type results. Check: `npm run taller:test-harness-esenciales`
  - Acceptance / functional: An explicit setup step provisions a checksum-verified official portable Blender LTS under ~/.local/opt/blender without system-package changes and records its version and executable; no test downloads Blender implicitly. Check: `npm run taller:test-harness-esenciales`
  - Acceptance / functional: The Blender comparison script passes identical inputs and names the element type and property that differs beyond 1 mm or 1/255, tested without Blender. Check: `python3 scripts/test/blender/test_comparar_glb.py`

- [ ] T3.13 — Run the real Taller essentials integration scenario · repo: pictures · after: T3.12 · verify: `npm run taller:test-integracion-esenciales` · files: .evidence/REQ-021/SP-3.integration.json · resources: taller:scene · covers: R9, R10, R11 · kind: test · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  Spec: Execute npm run taller:test-integracion-esenciales (authored by T3.12) once on the SP-3 tree against the REQ-021 test database, with portable Blender under ~/.local/opt/blender/current provisioned beforehand by npm run taller:preparar-blender; record .evidence/REQ-021/SP-3.integration.json with the tree identity. A missing Blender is recorded as an external block, not a pass. No harness authoring or source repairs here.

  - Acceptance / integration: The owner approves, from a sourced proposal, which new Backing structures and table types the pilot gets; the Taller models them as parametric tables and parametric furniture through exhaustive type registries and integrates them with search, scene AI, photo reading, English phrases and the shopping list; Fondos y muebles offers one card per table type (the eight existing types, rectangular included, plus the new ones) that adds it at its default size and opens the existing table editor, and one Backing group with the seven existing props moved from their former groups plus the new ones; the GLB of every element type the code enumerates, alone and in one full scene, opens in portable Blender LTS with the same layout, sizes in metres and base colours, or the failing type is listed as a defect. Check: `npm run taller:test-integracion-esenciales`
  - Acceptance / integration: A production build on loopback completes the real table-card, Backing and every-element-type GLB flow, recording Blender import evidence per element type or an explicit external block; no unexecuted check is reported as passed. Check: `npm run taller:test-integracion-esenciales`

- [ ] T3.15 — Audit Taller essentials and export compatibility · repo: pictures · after: T3.13 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json` · files: .evidence/REQ-021/SP-3.audit.md, .evidence/REQ-021/SP-3.findings.json · resources: ledger:T3.15 · covers: R9, R10, R11 · kind: audit · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Review R9/R10/R11, the modelled pieces against the recorded approval and the proposal, old furniture ids and saved scenes, real chair counts, per-type export evidence and no paid calls. Run lint, workspace builds, application types and build plus the affected furniture, catalogue, photo-reading and export suites as AGENTS.md requires; keep baseline failures separate.

  - Acceptance / static: An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task, checks modelled pieces against docs/req021/aprobacion-backing-mesas.json and the proposal, and distinguishes GLB structural evidence from real Blender and owner evidence. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json`

<!-- /SP-3 tasks -->

<!-- CG-2 tasks -->

  Composition gate CG-2: SP-1, SP-2, SP-14, SP-3 (cumulative, after CG-4). Split on 2026-10-28 so SP-3 can be staged with M1 alone; saved decorations and AI spend moved to CG-5.

- [ ] T92 — Composition check CG-2: accounts, plans section and Taller essentials · repo: pictures · after: T94, T3.15 · verify: `npm run taller:test-composicion-esenciales` · files: .evidence/REQ-021/CG-2.integration.json · resources: candidate:CG-2 · covers: R2, R9, R10, R11 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Execute the composition mode authored by T3.12 (`taller:test-composicion-esenciales`) on the integrated candidate. Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate passes Master Designer table, Backing and GLB operations and Entusiasta direct access denial. Check: `npm run taller:test-composicion-esenciales`

<!-- /CG-2 tasks -->

- **SP-4 — Saved projects** (UI: `proyectos@v1`): A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Covers R6, R7.

<!-- SP-4 tasks -->

  Behavior and task breakdown reflect the owner answers to round 9. Subplan and design confirmation remain separate owner actions; focus stays SP-2.

- [ ] T4.1 — Copy the approved saved-projects design contract · repo: pictures · after: T94, T3.3 · verify: `node -e "process.exit(require('crypto').createHash('sha256').update(require('fs').readFileSync('design/contracts/proyectos@v1.md')).digest('hex')==='0bf08313894d4d1f810ee7e5a1567423b5776869b2aa5da1e824017948e46897'?0:1)"` · files: design/contracts/proyectos@v1.md · resources: design:T4.1 · covers: R6, R7 · kind: design · subplan: SP-4 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; estimate 20 minutes.
  Copy the pinned owner-approved contract without rewriting it. Starts after CG-4 (M1 closed) and after T3.3, which defines taller-scene@1; SP-4 no longer waits for SP-3's audit.

  - Acceptance / static: The repository contract is byte-identical to the owner-approved proyectos@v1 artifact. Check: `node -e "process.exit(require('crypto').createHash('sha256').update(require('fs').readFileSync('design/contracts/proyectos@v1.md')).digest('hex')==='0bf08313894d4d1f810ee7e5a1567423b5776869b2aa5da1e824017948e46897'?0:1)"`

- [ ] T4.2 — Implement versioned project storage and scene validation · repo: pictures · after: T4.1 · verify: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts` · files: scripts/migrations/038_proyectos.sql, src/lib/proyectos/contrato.ts, src/lib/proyectos/servicio.ts, src/lib/proyectos/repositorio.ts, src/lib/proyectos/validar-escena.ts, src/lib/cuentas/dependientes.ts, scripts/test/test-proyectos-servicio.ts · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 170 minutes.
  Use getRagPool and SP-1 isolated schema helper. Migration 038 creates proyectos with UUID id, owner FK RESTRICT, name, schema_version=1, JSONB scene, revision >=1 and created/updated timestamps plus owner/update index. Register it as work in dependientes.ts. Name trimmed 1–120 characters, document UTF-8 limit 2 MiB; enforce existing MAX_NODOS=150 and room limits, complete Pieza variants and references using runtime validation, never the shallow legacy type guard as server validation. Unsupported schema is a stable recoverable error; do not silently drop fields or normalize away user work.
  Update WHERE id AND owner_id AND revision; increment in same statement, zero rows on stale yields conflict. For create/retry use client mutation UUID unique per account, reject different content under reused key; imports additionally use a unique account+raw-source SHA-256. Lock the owner row in the write transaction with a lock mode conflicting with deletion; FK RESTRICT is the final barrier so delete cannot erase work even if registry precheck races. Service derives caller identity from trusted session context; no client owner id. Owner round 9 q6: document is name + complete Escena (including salon, room, materials and scene-node attachments). Separately stored AI conversations and generated images remain in the browser and are not promised across browsers. Preserve all valid scene fields and references; no local data is erased.
  Scene validation (`validar-escena.ts`) takes piece, table, chair and Backing types from taller-scene@1 (`TIPOS_DE_PIEZA`, `elementosEnumerables()` in `src/lib/globos3d/tipos-escena.ts`, `TIPOS_MESA`, `IDS_BACKING`), never from `TIPOS_PIEZA` or a re-typed list.
  Expose project-document@1: {schemaVersion:1, nombre, escena}; stored result adds id, ownerId, revision and timestamps. Register proyectos:test-servicio = tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts. Tests cover migrations twice, cross-account ownership, CAS race, idempotency, validation, rollback and delete race.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Migration 038 also creates account-scoped mutation receipts and legacy-import receipts: UNIQUE(account_id, mutation_id) binds payload SHA-256 and committed project/revision; UNIQUE(account_id, raw_source_sha256) binds one imported project. A repeated identical create/update returns the committed receipt without another write or revision increment; a reused key with different payload fails. Import receipt and project insert commit together; do not rely on browser-only markers. Receipts are included in account-work cleanup/constraints and are not exposed across accounts.

  - Acceptance / functional: A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`
  - Acceptance / functional: Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`
  - Acceptance / functional: Scene validation uses taller-scene@1: a document holding every element of elementosEnumerables(), modulo pieces, every table type and every Backing id included, is accepted unchanged, and a node whose piece type is outside TIPOS_DE_PIEZA or whose table type is outside TIPOS_MESA is refused without writes. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`

- [ ] T4.3 — Implement project APIs with per-resource authorization · repo: pictures · after: T4.2 · verify: `npm run proyectos:test-api` · files: src/app/api/proyectos/route.ts, src/app/api/proyectos/[id]/route.ts, src/lib/proyectos/http.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-proyectos-api.ts, package.json, scripts/test/test-checkpoint-proyectos.ts · resources: package.json scripts, proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 100 minutes.
  GET /api/proyectos accepts cursor, q (trimmed name substring, at most 120 characters), scope=mine|all (default mine) and ownerId (UUID, only with scope=all and proyectos.ver_todos). Filter the entire authorized server collection before pagination, never only the loaded page. Return metadata only, at most 50 rows, ordered by updatedAt DESC then id DESC; use a validated opaque cursor bound to scope/q/ownerId and reject cursor/filter mismatch with 400. Escape SQL wildcard characters so name search is literal and parameterized. scope=all requires proyectos.ver_todos and includes owner display identity. The owner selector contains only authorized project-owner metadata; never enumerate unrelated accounts. A forged foreign ownerId in own scope is refused without disclosure. Filter changes reset the cursor/results; stale responses from the previous query cannot replace current results. Show a loaded count, not an invented total, and preserve loaded rows on next-page failure. GET /api/proyectos/[id] returns authorized document. POST /api/proyectos creates for the session account (also used for Save copy/import). PATCH /api/proyectos/[id] requires baseRevision and mutationId. Owner round 9 q7: foreign originals are read-only; Save copy creates a caller-owned project and requires taller.usar. Opening never transfers ownership and staff/admin cannot update another owner original.
  Route permission map: own project routes require taller.usar; read-all may be allowed to proyectos.ver_todos even for custom roles without taller.usar, and the service checks resource ownership independently. Same-origin guard for mutations, schema validation on every request, no-store responses; invalid JSON 400, unauthenticated 401, unauthorized collection scope 403, inaccessible/missing item 404, stale revision 409, too large 413. No deletion UI/API is included in this pilot scope; it is not required by R6/R7. Register proyectos:test-api using real isolated database and Request-based route tests.
  Author proyectos:test-checkpoint = tsx --conditions=react-server scripts/test/test-checkpoint-proyectos.ts: start next start on loopback against the isolated schema and run real HTTP ownership/CAS/delete-race checks, emitting SP-4.storage.json. No import-only check is called integration.

  - Acceptance / functional: Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document. Check: `npm run proyectos:test-api`

  - Acceptance / functional: Project-name search and authorized owner filters apply to the whole server collection before pagination; filter-bound cursors, literal name matching and per-account authorization prevent skipped later-page matches and metadata disclosure. Check: `npm run proyectos:test-api`

- [ ] T4.31 — Run the project storage and authorization checkpoint · repo: pictures · after: T4.3 · verify: `npm run proyectos:test-checkpoint` · files: .evidence/REQ-021/SP-4.storage.json · resources: proyectos:document · covers: R6, R7 · kind: test · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 35 minutes.
  Execute the checkpoint runner authored by T4.3 against the isolated database; write exact observed API/database outcomes and tree identity. Stop downstream UI work on failure; no source repairs in this task.

  - Acceptance / integration: Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race. Check: `npm run proyectos:test-checkpoint`
  - Acceptance / integration: With expected statuses written from the SPEC, a Usuario gets 404 on GET, PUT and DELETE of another account's project, an account without taller.usar gets 403 on POST, staff get 403 on PUT and DELETE of a foreign original, and cross-origin POST, PUT and DELETE get 403, none of them changing the stored project. Check: `npm run proyectos:test-checkpoint -- --solo denegaciones`

- [ ] T4.4 — Implement the project list and conflict-safe Taller saving · repo: pictures · after: T4.31 · verify: `npx tsx scripts/test/test-proyectos-cliente.ts` · files: src/app/proyectos/page.tsx, src/components/proyectos/ListaProyectos.tsx, src/components/proyectos/EstadoGuardado.tsx, src/components/proyectos/ConflictoProyecto.tsx, src/components/proyectos/useProyecto.ts, src/components/proyectos/textos-proyectos.ts, src/components/tres-d/Taller3D.tsx, src/app/3d/page.tsx, src/lib/proyectos/borrador-local.ts, scripts/test/test-proyectos-cliente.ts, src/app/proyectos/[id]/page.tsx · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: yes

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 180 minutes.
  Owner round 9 q5/q7: first Save explicitly asks for a name; subsequent edits autosave with visible status and Save now. The 500 ms serialized debounce is a Planner technical default inherited from the local saver, not a user-specified timing. List route /proyectos and deep link /3d?proyecto=<uuid>. Staff all-project list can be read with proyectos.ver_todos; custom roles lacking taller.usar need a read-only project view, not a bypass that grants editing tools. Owner-only editable project route checks both permissions and ownership server-side.
  Keep one in-flight update per project, latest scene queued behind it, bind response to account+project+request identity and submitted edit generation. A response acknowledges only its submitted generation; older completions cannot clear newer dirty work. On 409 stop queue until explicit resolution; no automatic overwrite or retry with fetched revision. Network/401/permission failure retains a namespaced local draft and exposes retry. Switching/new project or navigation with dirty/pending edits asks to save, keep local draft or cancel; ignore completions for previous identity.
  Namespace new drafts by account and project; never auto-open the old global scene after account switch. On sign-out/auth loss clear scene state and query caches; a different account cannot enumerate/open drafts. Keep recovery drafts for the same account; do not delete original legacy data. Reset undo history and scene conversation identity on project switch; preserve the full document and do not silently attach another project conversation. Register proyectos:test-cliente with out-of-order replies, offline/reload, account switch and conflict reducer tests. UI states per proyectos@v1.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Provide /proyectos/[id] as a server-authorized read-only scene view for proyectos.ver_todos without taller.usar; link staff reads there, never bypass the /3d Taller permission. Save copy also requires taller.usar. Register both project pages in the T4.3 permission map and test custom staff read-only access.

  Owner 2026-10-27: «Escena nueva», a template or «Abrir en Escena» from the library start a new unsaved project named «Escena nueva»; pending edits of the open project are saved first and a never-saved scene asks before being discarded.
  Project-list name search and owner filtering use T4.3 server queries over the entire authorized collection. Debounce search, reset cursors on filter change, key requests by normalized query and ignore late responses; preserve loaded rows and expose retry for a failed next page. Do not perform page-only client filtering.

  - Acceptance / functional: The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`
  - Acceptance / functional: Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`

  - Acceptance / functional: The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`
  - Acceptance / functional: «Escena nueva», a template or «Abrir en Escena» start a new unsaved project: the open project keeps its last saved revision (its pending edits are saved first, or the user is asked before a never-saved scene is discarded), the new scene is linked to no project and nothing reaches the server until its first named save. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`
  - Acceptance / functional: When the server refuses a save because of a forged owner id, a malformed or oversized scene, a stale revision or a cross-origin request, the Taller shows the refusal, keeps the unsent local scene and never marks it saved. Check: `npx tsx scripts/test/test-proyectos-cliente.ts --solo abuso`

- [ ] T4.5 — Implement a lossless and idempotent legacy-scene import · repo: pictures · after: T4.4 · verify: `npx tsx scripts/test/test-proyectos-importacion.ts` · files: src/lib/proyectos/importar-local.ts, src/components/proyectos/ImportarEscenaLocal.tsx, src/components/tres-d/guardado-escena.ts, src/components/proyectos/useProyecto.ts, scripts/test/test-proyectos-importacion.ts · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: yes

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 110 minutes.
  Read raw taller3d:escena:v1 before legacy leerGuardada can normalize/discard it. Show import on first authenticated Taller visit with legacy data, not in login handlers; an account without Taller access keeps it until access is granted. Not now is reversible via project list. Consent belongs to the current account; explain the browser scene may be from another person on shared devices. Do not upload until explicit consent.
  Validate complete supported legacy schema on server. Use account+SHA-256 of original raw bytes for durable idempotency, mapping to imported project in the create transaction; response loss/reload/double-click returns that same project. A different account sees a fresh explicit consent, never a prior import association. Keep the original legacy key unchanged even after success; store separate account-scoped import receipt only after server acknowledgement. Invalid/unknown-version data gets a recoverable explanation and raw JSON download, never empty-scene replacement. Do not depend on existing leerGuardada silently returning null. Register proyectos:test-importacion with malformed/old versions, denial, two tabs and interrupted response tests.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically. Check: `npx tsx scripts/test/test-proyectos-importacion.ts`

- [ ] T4.6 — Implement the multi-browser saved-project integration harness · repo: pictures · after: T4.5 · verify: `npm run proyectos:test-harness` · files: scripts/test/test-integracion-proyectos.ts, scripts/test/test-harness-proyectos.ts, package.json · resources: package.json scripts, proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 120 minutes.
  Author proyectos:test-harness and proyectos:test-integracion, no paid AI. Seed owner A/B, staff and administrator with SP-1 helpers; next build and next start loopback. A creates scene fixture with table, Backing, attachments, colours and room; fresh A context reopens and compares canonical document and computed scene counts. B attempts list/read/write guessed IDs (also direct API); staff opens A read-only and saves copy. Two A contexts start same revision: second write gets 409 and draft survives. Simulate lost create/import response and retry, malformed legacy data, then account switch and verify no scene disclosure.
  Emit .evidence/REQ-021/SP-4.integration.json with exact tree, commands, browser contexts, expected/observed version and access results, preserve screenshots for visual audit; teardown processes and isolated schema in finally. Use deterministic seeded fixture/test doubles only at paid-provider boundary, not persistence/auth APIs.
  Own package.json registration for remaining SP-4 aliases (service, client and import); preserve the checkpoint/API aliases already registered in T4.3.
  Also author proyectos:test-composicion, combining sign-in, a scene with one table of every `TIPOS_MESA` type and one prop of every `IDS_BACKING` id (imported from the code, so SP-3's approved pieces are covered without editing the test), project persistence, staff read/copy and deletion refusal on the integrated candidate; record .evidence/REQ-021/CG-3.integration.json.

  Seed at least 51 authorized project metadata rows and place a uniquely named match beyond the first unfiltered page. Verify server search finds it, staff owner filtering is authorization-bound, regular accounts cannot query foreign owner metadata, filter changes discard stale cursors/responses, and next-page failure preserves visible results with retry.

  - Acceptance / functional: The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import. Check: `npm run proyectos:test-harness`

  - Acceptance / functional: The browser harness seeds more than fifty projects and verifies a matching project beyond the first page, authorized owner filtering, next-page retry and stale search-response rejection without leaking foreign metadata. Check: `npm run proyectos:test-harness`

- [ ] T4.7 — Run the cross-browser project and import integration scenario · repo: pictures · after: T4.6 · verify: `npm run proyectos:test-integracion` · files: .evidence/REQ-021/SP-4.integration.json · resources: proyectos:document · covers: R6, R7 · kind: test · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 60 minutes.
  Run the existing T4.6 harness, record command-level evidence and failures; no source repair or acceptance verdict in this execution task.

  - Acceptance / integration: A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Check: `npm run proyectos:test-integracion`
  - Acceptance / integration: A real production build passes persistence across fresh browser contexts, per-account denial, staff read/copy, competing-save conflict, import retry and account-switch isolation checks on the REQ-021 database. Check: `npm run proyectos:test-integracion`
  - Acceptance / integration: On the production build, with expected statuses taken from the SPEC, a Usuario's GET, PUT and DELETE of another account's project and a staff PUT on a foreign original are refused, and the stored project is byte-identical afterwards. Check: `npm run proyectos:test-integracion -- --solo denegaciones`

- [ ] T4.8 — Review the rendered project and import interfaces · repo: pictures · after: T4.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json` · files: .evidence/REQ-021/SP-4.visual.md, .evidence/REQ-021/SP-4.visual.findings.json · resources: ledger:T4.8 · covers: R6, R7 · kind: audit · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 75 minutes.
  Independent visual-axis review on rendered source; link screenshots, source identity and SP-4.integration.json. Map each mismatch to T4.4/T4.5 rather than blanket rework.

  - Acceptance / static: Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json`

- [ ] T4.9 — Audit project isolation, concurrency and import preservation · repo: pictures · after: T4.8 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json` · files: .evidence/REQ-021/SP-4.audit.md, .evidence/REQ-021/SP-4.findings.json · resources: ledger:T4.9 · covers: R6, R7 · kind: audit · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling high; confidence medium; estimate 90 minutes.
  Review R6/R7 against accepted round 9 answers and source; challenge direct API bypass, metadata leakage, stale-response ordering, project-switch races, delete/save race and invalid legacy recovery. Run required lint, workspace builds, app types/build and affected existing scene tests; distinguish baseline defects and unavailable external resources from passes.

  - Acceptance / static: An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json`

<!-- /SP-4 tasks -->

- **SP-5 — Saved decorations** (UI: `decoraciones@v1`): A signed-in Master Designer (and staff) saves a named scene composition or selected piece to a server-side personal decoration library and places it into projects from any browser; Empleado interno and Administrador open another account's items read-only and only the owner updates or deletes them; an account with saved decorations cannot be deleted, only deactivated; existing browser-local library entries stay local and are not imported in the pilot. Covers R8.

<!-- SP-5 tasks -->

  SP-5 tasks (rounds 7 and 11; reworked 2026-10-29). Round 11: no import of the browser-local library (`taller3d:biblioteca-propia:v1`), staff read-only access to other accounts' items, owner-only update and delete. Round 7: an account with saved decorations cannot be deleted (registered in `src/lib/cuentas/dependientes.ts`). The personal library uses permission `taller.usar` (Master Designer and staff) and stays separate from the global SQLite decorations catalogue of /admin.
  DAG: T5.1 (design) ∥ T5.2 (storage and API) → T5.3 (Taller library on the API) → T5.4 integration → T5.5 visual review → T5.6 audit. Consumes account-service@1, session-guard@1 (SP-1) and taller-scene@1 (SP-3); composition gate CG-5 adds SP-5 after CG-3.

- [ ] T5.1 — Copy the approved personal-decoration library UI contract · repo: pictures · after: T94, T3.3 · verify: `test -s design/contracts/decoraciones@v1.md` · files: design/contracts/decoraciones@v1.md · resources: design:decoraciones@v1 · covers: R8 · kind: design · subplan: SP-5 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.
  The scheduler supplies the plan-approved draft; the task copies it unchanged.

  - Acceptance / static: The owner-approved decoraciones@v1 contract is copied byte for byte into design/contracts/decoraciones@v1.md. Check: `test -s design/contracts/decoraciones@v1.md`

- [ ] T5.2 — Account-owned personal-decoration storage and its protected API · repo: pictures · after: T94, T3.3 · verify: `npm run decoraciones:test-api -- --test-name-pattern=almacen` · files: scripts/migrations/039_decoraciones_personales.sql, src/lib/decoraciones-personales/repositorio.ts, src/lib/decoraciones-personales/esquema.ts, src/app/api/decoraciones-personales/route.ts, src/app/api/decoraciones-personales/[id]/route.ts, src/lib/cuentas/dependientes.ts, scripts/test/test-decoraciones-personales-api.ts · resources: package.json scripts, contract:session-guard, contract:taller-scene · covers: R8 · kind: implement · subplan: SP-5 · ui: no

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence high; estimate 120 minutes.
  Table `decoraciones_personales` (id, cuenta_id REFERENCES cuentas ON DELETE RESTRICT, nombre ≤ 120, ocasion, miniatura ≤ 512 KB, composicion jsonb ≤ 2 MB validated with the taller-scene@1 schema, creada_en, actualizada_en). Routes require `taller.usar`; staff reads use `proyectos.ver_todos`; another Usuario's item answers 404. `dependientes.ts` registers the table as account work. npm script `decoraciones:test-api` = `tsx --conditions=react-server --test scripts/test/test-decoraciones-personales-api.ts`.

  - Acceptance / functional: Migration 039 creates an account-owned personal-decoration table in Postgres without changing the legacy SQLite global catalogue, and a saved item keeps its name, occasion, thumbnail and validated composition exactly as sent. Check: `npm run decoraciones:test-api -- --test-name-pattern=almacen`
  - Acceptance / functional: With expected statuses written from the SPEC, the owner lists and opens their items, Empleado interno and Administrador open another account's items read-only, a Usuario gets 404 on another account's item, and an account without taller.usar gets 403 on every personal-decoration API. Check: `npm run decoraciones:test-api -- --test-name-pattern=lectura`
  - Acceptance / functional: With expected statuses written from the SPEC, PUT and DELETE succeed only for the owner; staff and other accounts get 403 or 404 on PUT and DELETE, a cross-origin POST is refused, and a malformed or oversized composition is refused with 400 without a partial write. Check: `npm run decoraciones:test-api -- --test-name-pattern=escritura`
  - Acceptance / functional: Personal decorations are registered as account work in src/lib/cuentas/dependientes.ts, so deleting an account that owns one is refused with CUENTA_CON_TRABAJO. Check: `npm run decoraciones:test-api -- --test-name-pattern=borrar-cuenta`
  - Acceptance / regression: The personal library never writes to the global decorations catalogue or its /api/decoraciones routes, and no personal item appears to another Usuario. Check: `npm run decoraciones:test-api -- --test-name-pattern=separada`

- [ ] T5.3 — Taller personal library on the account API: save, place, staff read-only and account switch · repo: pictures · after: T5.1, T5.2 · verify: `npm run decoraciones:test-ui -- --solo guardar` · files: src/components/tres-d/Biblioteca.tsx, src/components/tres-d/biblioteca/BibliotecaPersonal.tsx, src/components/tres-d/biblioteca/textos-biblioteca.ts, scripts/test/test-biblioteca-personal-ui.ts · resources: package.json scripts · covers: R8 · kind: implement · subplan: SP-5 · ui: yes

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence medium; estimate 150 minutes.
  The server list comes first; legacy entries appear under a separate «En este navegador» group with no import action. Placing a staff-opened item adds a copy to the staff member's own scene. npm script `decoraciones:test-ui` = `tsx scripts/test/test-biblioteca-personal-ui.ts`.

  - Acceptance / functional: From the Taller a person saves the current scene or the selected piece with a name and occasion, sees saved only after the server confirms, and finds the item after a reload and in another browser of the same account. Check: `npm run decoraciones:test-ui -- --solo guardar`
  - Acceptance / functional: A saved item can be searched and placed into the open project, and the existing name, occasion, thumbnail and filter controls keep working. Check: `npm run decoraciones:test-ui -- --solo colocar`
  - Acceptance / functional: When staff open another account's item it is clearly read-only: rename, edit and delete controls are absent and placing it adds a copy to the staff member's own project. Check: `npm run decoraciones:test-ui -- --solo personal`
  - Acceptance / functional: Entries already in the browser key taller3d:biblioteca-propia:v1 stay in that browser's local list untouched, nothing imports them, and switching or signing out never shows the previous account's server items. Check: `npm run decoraciones:test-ui -- --solo local-y-cambio`

- [ ] T5.4 — Browser end-to-end: saved decorations across browsers, placement and ownership · repo: pictures · after: T5.3 · verify: `npm run decoraciones:test-integracion` · files: scripts/test/test-integracion-decoraciones-personales.ts, .evidence/REQ-021/SP-5.integration.json · resources: package.json scripts · covers: R8 · kind: test · subplan: SP-5

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  npm script `decoraciones:test-integracion` = `tsx scripts/test/test-integracion-decoraciones-personales.ts`; CG-5 reuses it.

  - Acceptance / integration: On a production build against the REQ-021 database, with expected results written from the SPEC, account A saves a composition, reloads, opens it in a second browser and places it into a project; staff open it read-only and their direct PUT and DELETE are refused; another Usuario cannot see it; and a legacy browser item stays local. Check: `npm run decoraciones:test-integracion`

- [ ] T5.5 — SP-5 visual review against the decoraciones@v1 contract · repo: pictures · after: T5.4 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-5.visual.findings.json` · files: .evidence/REQ-021/SP-5.visual.md, .evidence/REQ-021/SP-5.visual.findings.json · resources: ledger:SP-5-visual · covers: R8 · kind: audit · subplan: SP-5

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit).

  - Acceptance / static: The rendered personal-library save, list, read-only, empty, loading, retry and error states match the approved decoraciones@v1 contract at phone and desktop widths, and every finding is recorded with the task to redo in the SP-5 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-5.visual.findings.json`

- [ ] T5.6 — SP-5 audit: ownership of personal decorations, account switch and the deletion rule · repo: pictures · after: T5.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-5.findings.json` · files: .evidence/REQ-021/SP-5.audit.md, .evidence/REQ-021/SP-5.findings.json · resources: ledger:SP-5 · covers: R8 · kind: audit · subplan: SP-5

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 60 minutes.
  Checks at least: owner filter in every query, staff read-only on every method, 404 for other Usuarios, account-switch clearing, CUENTA_CON_TRABAJO.

  - Acceptance / static: An independent audit of SP-5 checks owner and staff boundaries for every method, account-switch isolation and the deletion rule, records every confirmed defect with the task that must redo it in the SP-5 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-5.findings.json`

<!-- /SP-5 tasks -->

- **SP-6 — AI spend per user and session** (UI: `gasto-ia@v1`): A separate `ai-usage@1` ledger attributes successful paid model calls from Next and ai-api to account, session, work item, tool, call kind, provider/model, available token usage and estimated USD cost; employees and administrators review totals, while Usuario accounts cannot open them. Covers R4, R5.

<!-- SP-6 tasks -->

- [ ] T6.1 — Pin the approved AI-spend UI contract · repo: pictures · after: T94 · verify: `test -s design/contracts/gasto-ia@v1.md` · files: design/contracts/gasto-ia@v1.md · resources: design:gasto-ia@v1 · covers: R4, R5 · kind: design · subplan: SP-6 · ui: no
- [ ] T6.2 — Define durable AI usage storage and ai-usage@1 · repo: pictures · after: T94 · verify: `npm run gasto:test-esquema` · files: scripts/migrations/040_gasto_ia.sql, src/lib/gasto-ia/repositorio.ts, src/lib/registro/contrato-uso.ts, src/lib/cuentas/dependientes.ts, services/ai-api/app/registro.py · resources: postgres:account-data, contract:account-service@1, contract:session-guard@1 · covers: R4, R5 · kind: implement · subplan: SP-6 · ui: no
- [ ] T6.3 — Attribute usage at every paid Next and ai-api model call · repo: pictures · after: T6.2 · verify: `npm run gasto:test-captura` · files: src/lib/registro/envoltorios.ts, src/lib/registro/ruta.ts, src/app/api/escena-ia/route.ts, src/lib/ia/nucleo/telemetria-llamadas.ts, services/ai-api/app/registro.py, services/ai-api/app/main.py · resources: contract:ai-usage@1, postgres:account-data, contract:session-guard@1 · covers: R4, R5 · kind: implement · subplan: SP-6 · ui: no
- [ ] T6.4 — Build the staff spend dashboard and server-filtered API · repo: pictures · after: T6.1, T6.2, T6.3 · verify: `npm run gasto:test-ui -- --solo filtros` · files: src/app/admin/page.tsx, src/app/api/admin/gasto/route.ts, src/lib/gasto-ia/repositorio.ts, src/components/admin/GastoIa.tsx · resources: design:gasto-ia@v1, contract:ai-usage@1, contract:permission-map@1 · covers: R4, R5 · kind: implement · subplan: SP-6 · ui: yes
- [ ] T6.5 — Run real-entrypoint usage attribution and authorization checks · repo: pictures · after: T6.4 · verify: `npm run gasto:test-integracion` · files: scripts/test/test-integracion-gasto-ia.ts, .evidence/REQ-021/SP-6.integration.json · resources: postgres:account-data, contract:ai-usage@1 · covers: R4, R5 · kind: test · subplan: SP-6 · ui: yes
- [ ] T6.6 — Review the rendered spend dashboard against gasto-ia@v1 · repo: pictures · after: T6.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-6.visual.findings.json` · files: .evidence/REQ-021/SP-6.visual.md, .evidence/REQ-021/SP-6.visual.findings.json · resources: ledger:SP-6-visual, design:gasto-ia@v1 · covers: R4, R5 · kind: audit · subplan: SP-6 · ui: no
- [ ] T6.7 — Audit AI spend completeness, identity and data minimization · repo: pictures · after: T6.6 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-6.findings.json` · files: .evidence/REQ-021/SP-6.audit.md, .evidence/REQ-021/SP-6.findings.json · resources: ledger:SP-6, contract:ai-usage@1 · covers: R4, R5 · kind: audit · subplan: SP-6 · ui: no

<!-- /SP-6 tasks -->
- **SP-7 — Assisted chat as three tools and the decorations explorer** (UI: `herramientas-chat@v1`): The assisted chat becomes a balloon counter, a cost calculator and the normal chat, each with its own prompts and spend measured separately and never inventing counts or prices; a ready-made decorations explorer lists existing 3D decorations and, like everything of the Taller 3D, is reachable only with Master Designer and the staff roles; each tool is reachable only with the access plans the plan catalogue gives it. Covers R13, R16.

<!-- SP-7 tasks -->

  SP-7 tasks (owner round 15, 2026-10-28). The guided chat (/asistente, VistaGuiada) becomes the normal chat; the classic chat page at / is retired and / becomes the tool home (q1). Counter: own page by form, phrase or photo, counts and shopping list without prices (q2 + owner note: also from a photo, using the existing services/ai-api conteo-referencia photo count; «detección avanzada de globos» stays «aún no disponible»). Calculator: the existing professional quote (src/components/cotizacion/CotizacionProfesional.tsx, src/lib/cotizacion/profesional.ts: materials, labour, equipment and transport, indirect costs, margin) as its own page, fed by the counter or by hand (q3 + owner note). Accounts without costos.usar get no prices in the chat, enforced on the server (q4). Gallery inside the Taller at /3d/decoraciones with its own link (q5).
  Permissions come from SP-1 (chat.usar, contador.usar, costos.usar, decoraciones.explorar). Spend tags feed SP-6's ai-usage@1 tool field. Contracts consumed: session-guard@1, permission-map@1, plan-catalogue@1 (SP-1), taller-scene@1 (SP-3), ai-usage@1 (SP-6). Composition gate CG-7 adds SP-7 to the M2 candidate. Cut order: the split, the no-price rule and reliability are never traded; the gallery's filters are the first thing to drop if late (owner cut 3: chat improvements beyond the split).
  DAG: T7.1 (design) ∥ T7.2 (tool catalogue, gating, tags) → T7.3 (counter API) → T7.4 checkpoint → {T7.5 home, T7.6 counter, T7.7 calculator, T7.8 gallery} (UI, after T7.1) → T7.9 integration → T7.10 visual review → T7.11 audit.

- [ ] T7.1 — Copy the owner-approved herramientas-chat@v1 contract into the repository · repo: pictures · after: T3.3, T6.2 · verify: `test -s design/contracts/herramientas-chat@v1.md` · files: design/contracts/herramientas-chat@v1.md · resources: design:herramientas-chat@v1 · covers: R13, R16 · kind: design · subplan: SP-7 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.
  The scheduler supplies the plan-approved draft; the task copies it unchanged.

  - Acceptance / static: The owner-approved herramientas-chat@v1 contract is copied byte for byte into design/contracts/herramientas-chat@v1.md. Check: `test -s design/contracts/herramientas-chat@v1.md`

- [ ] T7.2 — Tool catalogue, server-side price gating of the guided chat and per-tool spend tags · repo: pictures · after: T3.3, T6.2 · verify: `npm run herramientas:test-gating -- --test-name-pattern=catalogo` · files: src/lib/herramientas/catalogo-herramientas.ts, src/app/api/asistente-guiado/route.ts, src/lib/ia/guiado/prompt-guiado.ts, src/lib/guiada-motor/costear-idea-elegida.ts, src/lib/registro/cliente.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-herramientas-gating.ts · resources: package.json scripts, contract:permission-map, contract:ai-usage · covers: R13, R16 · kind: implement · subplan: SP-7 · ui: no

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 150 minutes.
  `catalogo-herramientas.ts`: `HERRAMIENTAS = { inicio, chat, contador, calculadora, galeria }` each with `ruta`, `permiso` (sesion, chat.usar, contador.usar, costos.usar, decoraciones.explorar), `etiquetaGasto` (chat, contador, calculadora; galeria has no paid call) and names ES/EN; `herramientasDe(permisos)` in catalogue order.
  Guided route: when the session lacks `costos.usar`, drop `costear_decoracion` and the `costear` plan action from the tool list sent to the model, make `respuestaSinModelo` and the final-text guard strip prices and totals, and answer the costing endpoints (`/api/guiada/motor/*` costing, `/api/cotizacion-profesional`, `/api/taller/cotizacion*`) 403 `SIN_PERMISO` through the map; the prompt gets a line telling it costs are not available here without naming a plan. Spend: `cliente.ts` sends `x-herramienta` from the page's tool and the server copies it into the ai-usage@1 `tool` field (never trusted for permissions). npm script `herramientas:test-gating` = `tsx --conditions=react-server --test scripts/test/test-herramientas-gating.ts`.

  - Acceptance / functional: One tool catalogue names the home, normal chat, balloon counter, cost calculator and decorations gallery with the permission and spend tag of each, and every page and API of the four tools is mapped to exactly that permission. Check: `npm run herramientas:test-gating -- --test-name-pattern=catalogo`
  - Acceptance / functional: For an account without costos.usar the guided chat never calls a costing tool, never answers with a price, total or quote, and its costing and professional-quote APIs answer 403 SIN_PERMISO, without naming which plan includes costs. Check: `npm run herramientas:test-gating -- --test-name-pattern=sin-precios`
  - Acceptance / functional: Every paid model call of the chat, counter and calculator is recorded in the AI usage ledger under its own tool tag (chat, contador, calculadora) with the signed-in account and session. Check: `npm run herramientas:test-gating -- --test-name-pattern=etiquetas`
  - Acceptance / functional: A forged x-herramienta header, a client-supplied account or session id and a cross-origin POST to the gated tool APIs never grant access and never change the account a spend row belongs to. Check: `npm run herramientas:test-gating -- --test-name-pattern=abuso`

- [ ] T7.3 — Balloon counter API by form, phrase or photo on the existing counting engines · repo: pictures · after: T7.2 · verify: `npm run contador:test-api -- --test-name-pattern=formulario` · files: src/app/api/contador/route.ts, src/lib/contador/contar.ts, src/lib/contador/esquema.ts, scripts/test/test-contador-api.ts · resources: package.json scripts, contract:ai-usage · covers: R13 · kind: implement · subplan: SP-7 · ui: no

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  `POST /api/contador` (permission contador.usar): `{ modo: 'formulario', estructura, medidas, tamanos, colores } | { modo: 'frase', texto } | { modo: 'foto', imagen }`. Form → `PYTHON_ESTIMAR_CONTEO_PATH`; phrase → one model call extracts the form fields (zod-validated), missing measures return `{ pregunta }`, then the engine; photo (JPEG/PNG/WebP, at most 8 MB) → `/internal/v1/ia/conteo-referencia` with its tolerance. Response `{ conteos: [{ tamano, color, cantidad }], listaCompra: [{ producto, cantidad }], origen, tolerancia? }`, never a price. npm script `contador:test-api` = `tsx --conditions=react-server --test scripts/test/test-contador-api.ts`.

  - Acceptance / functional: POST /api/contador with a structure, its measures, balloon sizes and colours returns the balloon count per size and colour and the shopping list without prices, equal to the engine's estimate for the same input. Check: `npm run contador:test-api -- --test-name-pattern=formulario`
  - Acceptance / functional: POST /api/contador with a phrase extracts the structure and measures with the model and then counts with the engine; when the phrase lacks a measure it asks for it instead of guessing a number. Check: `npm run contador:test-api -- --test-name-pattern=frase`
  - Acceptance / functional: POST /api/contador with a photo returns the existing photo count of services/ai-api conteo-referencia with its tolerance, labelled as an estimate from the photo, and refuses a non-image or oversized file. Check: `npm run contador:test-api -- --test-name-pattern=foto`

- [ ] T7.4 — Checkpoint: tool gating, counter API and spend tags on a running server · repo: pictures · after: T7.3 · verify: `npm run herramientas:test-checkpoint` · files: scripts/test/test-herramientas-checkpoint.ts, .evidence/REQ-021/SP-7.checkpoint.json · resources: package.json scripts · covers: R13, R16 · kind: test · subplan: SP-7

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  npm script `herramientas:test-checkpoint` = `tsx scripts/test/test-herramientas-checkpoint.ts`; expected statuses come from this SPEC (403 for costs without costos.usar).

  - Acceptance / integration: Before any screen is built, with expected statuses written from the SPEC, the real tool, counter and gating APIs pass on a running server against the REQ-021 database: Entusiasta counts by form, phrase and photo, its POST to the professional quote and costing APIs gets 403, and each call lands in the usage ledger under its tool tag. Check: `npm run herramientas:test-checkpoint`

- [ ] T7.5 — Tool home page at / and retirement of the classic chat page · repo: pictures · after: T7.1, T7.4 · verify: `npm run herramientas:test-ui-portada` · files: src/app/page.tsx, src/components/herramientas/PortadaHerramientas.tsx, src/components/herramientas/textos-herramientas.ts, src/components/ui/shell/CabeceraApp.tsx, src/components/ui/shell/MenuApp.tsx, scripts/test/test-ui-portada.ts · resources: package.json scripts, contract:plan-catalogue · covers: R13, R16 · kind: implement · subplan: SP-7 · ui: yes

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  / renders `herramientasDe(permisos)` as cards; /api/chat stays (the guided chat's plan agent). Components used only by the classic page are deleted; `npx tsc --noEmit` and the build prove nothing else imported them. npm script `herramientas:test-ui-portada` = `tsx scripts/test/test-ui-portada.ts`.

  - Acceptance / functional: The home page / shows only the tools the signed-in account's role grants, each opening its own page; the classic chat page is gone while /api/chat keeps serving the guided chat's plan agent. Check: `npm run herramientas:test-ui-portada`

- [ ] T7.6 — Balloon counter page: form, phrase and photo with a price-free result · repo: pictures · after: T7.1, T7.4 · verify: `npm run contador:test-ui` · files: src/app/contador/page.tsx, src/components/herramientas/contador/FormularioContador.tsx, src/components/herramientas/contador/ResultadoConteo.tsx, src/components/herramientas/contador/textos-contador.ts, scripts/test/test-ui-contador.ts · resources: package.json scripts · covers: R13 · kind: implement · subplan: SP-7 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  «Calcular costo» appears only with costos.usar and hands the result to /calculadora through sessionStorage key `calculadora:desde-contador` (no URL payload). npm script `contador:test-ui` = `tsx scripts/test/test-ui-contador.ts`.

  - Acceptance / functional: The balloon counter page counts by form, by phrase or by photo and shows counts per size and colour and the shopping list without any price, and offers «Calcular costo» only to accounts with costos.usar. Check: `npm run contador:test-ui`

- [ ] T7.7 — Cost calculator page from the existing professional quote, fed by the counter or by hand · repo: pictures · after: T7.1, T7.4 · verify: `npm run calculadora:test-ui` · files: src/app/calculadora/page.tsx, src/components/herramientas/calculadora/Calculadora.tsx, src/components/herramientas/calculadora/textos-calculadora.ts, scripts/test/test-ui-calculadora.ts · resources: package.json scripts · covers: R13 · kind: implement · subplan: SP-7 · ui: yes

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 90 minutes.
  Totals come from the existing Python professional quote; the page never computes a total itself. npm script `calculadora:test-ui` = `tsx scripts/test/test-ui-calculadora.ts`.

  - Acceptance / functional: The cost calculator page takes the counter's result or materials typed by hand, lets the person edit balloon prices and add labour, transport, indirect costs and margin, and shows per-product prices from the real catalogue and the professional quote totals. Check: `npm run calculadora:test-ui`

- [ ] T7.8 — Ready-made decorations gallery in the Taller with an open-as-new-project link · repo: pictures · after: T7.1, T7.4 · verify: `npm run galeria:test-ui -- --solo galeria` · files: src/app/3d/decoraciones/page.tsx, src/components/tres-d/galeria/GaleriaDecoraciones.tsx, src/components/tres-d/galeria/textos-galeria.ts, src/lib/globos3d/galeria-decoraciones.ts, src/components/tres-d/Taller3D.tsx, scripts/test/test-ui-galeria.ts · resources: package.json scripts, contract:taller-scene, contract:galeria-index · covers: R13, R16 · kind: implement · subplan: SP-7 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence medium; estimate 150 minutes.
  `galeria-decoraciones.ts` builds one index `{ id, nombre, ocasion, tamano, miniatura }` from `IDEAS_ASISTENTE` and `IDEAS_SEMPERTEX`. The Taller reads `?decoracion=<id>` once, opens it as a new unsaved scene with the same rule as «Abrir en Escena» (SP-4: pending edits of the open project are saved first or the user is asked) and removes the parameter. npm script `galeria:test-ui` = `tsx scripts/test/test-ui-galeria.ts`.

  - Acceptance / functional: The decorations gallery at /3d/decoraciones lists every Ideas del asistente and Ideas Sempertex item with search, occasion and size filters and a preview, and «Abrir como proyecto nuevo» opens /3d?decoracion=<id> as a new unsaved scene. Check: `npm run galeria:test-ui -- --solo galeria`
  - Acceptance / functional: The gallery and its deep link are reachable only with decoraciones.explorar; other accounts get the no-access page, and an unknown decoration id shows a not-found message without changing the open scene. Check: `npm run galeria:test-ui -- --solo permisos`

- [ ] T7.9 — Browser end-to-end of the three tools and the gallery on a production build · repo: pictures · after: T7.5, T7.6, T7.7, T7.8 · verify: `npm run herramientas:test-integracion` · files: scripts/test/test-integracion-herramientas.ts, .evidence/REQ-021/SP-7.integration.json · resources: package.json scripts · covers: R13, R16 · kind: test · subplan: SP-7

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  npm script `herramientas:test-integracion` = `tsx scripts/test/test-integracion-herramientas.ts`; paid model calls use the cheapest configured provider and one call per tool.

  - Acceptance / integration: On a production build against the REQ-021 database, with expected results written from the SPEC, an Entusiasta sees chat and counter on the home page, counts by form and photo without prices and is refused the calculator; a Designer Plus sends the counter result to the calculator and gets totals with margin; a Master Designer opens a gallery decoration as a new project; and the usage ledger holds one row per paid call with its tool tag. Check: `npm run herramientas:test-integracion`

- [ ] T7.10 — SP-7 visual review against the herramientas-chat@v1 contract · repo: pictures · after: T7.9 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-7.visual.findings.json` · files: .evidence/REQ-021/SP-7.visual.md, .evidence/REQ-021/SP-7.visual.findings.json · resources: ledger:SP-7-visual · covers: R13 · kind: audit · subplan: SP-7

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit).

  - Acceptance / static: The rendered home, counter, calculator and gallery screens match the approved herramientas-chat@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-7 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-7.visual.findings.json`

- [ ] T7.11 — SP-7 audit: tool gating, price leaks, counting sources and spend tags · repo: pictures · after: T7.10 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-7.findings.json` · files: .evidence/REQ-021/SP-7.audit.md, .evidence/REQ-021/SP-7.findings.json · resources: ledger:SP-7 · covers: R13, R16 · kind: audit · subplan: SP-7

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 75 minutes.
  Checks at least: no costing path without costos.usar (model tools, rule answers, final text, APIs); counts only from the engines; the spend tag never grants access; the deep link cannot overwrite unsaved work.

  - Acceptance / static: An independent audit of SP-7 records every confirmed defect with the task that must redo it in the SP-7 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-7.findings.json`

<!-- /SP-7 tasks -->


<!-- CG-3 tasks -->

  Composition of accepted subplans on the integrated candidate.

- [ ] T93 — Composition check CG-3: accounts and saved projects · repo: pictures · after: T92, T4.9 · verify: `npm run proyectos:test-composicion` · files: .evidence/REQ-021/CG-3.integration.json · resources: candidate:CG-3 · covers: R2, R6, R7, R9, R11 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Execute the composition mode authored by T4.6 on the integrated candidate (CG-3 holds SP-1, SP-2, SP-14, SP-3 and SP-4, so it follows CG-2, which follows CG-4). Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate passes account-scoped project save/reopen with every table type and every Backing prop, staff read/copy, conflict rejection and account deletion refusal. Check: `npm run proyectos:test-composicion`

<!-- /CG-3 tasks -->
<!-- CG-5 tasks -->

  Composition gate CG-5: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5 (cumulative, after CG-3).

- [ ] T95 — Composition check CG-5: saved decorations on the integrated candidate · repo: pictures · after: T93, T5.6 · verify: `npm run decoraciones:test-integracion` · files: .evidence/REQ-021/CG-5.integration.json · resources: candidate:CG-5, db:personal-decorations · covers: R8 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 35 minutes.
  Execute the SP-5 integration mode (authored by T5.4) on the integrated candidate. Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate passes account-owned saved-decoration persistence across browsers, placement into a project, staff read-only access and owner-only mutation and cross-account denial. Check: `npm run decoraciones:test-integracion`

<!-- /CG-5 tasks -->
<!-- CG-6 tasks -->

  Composition gate CG-6: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6 (cumulative, after CG-5).

- [ ] T96 — Composition check CG-6: AI spend per account on the integrated candidate · repo: pictures · after: T95, T6.7 · verify: `npm run gasto:test-integracion` · files: .evidence/REQ-021/CG-6.integration.json · resources: candidate:CG-6, db:ai-usage · covers: R4, R5 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 35 minutes.
  Execute the SP-6 integration mode (authored by T6.5) on the integrated candidate. Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate records account/session-attributed usage for representative text and image calls from Next and ai-api; project calls roll up under the project with conversation detail, known billable provider-error usage is partial/error, staff see totals, and Usuario is denied. Check: `npm run gasto:test-integracion`

<!-- /CG-6 tasks -->

<!-- CG-7 tasks -->

  Composition gate CG-7: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7 (cumulative, after CG-6).

- [ ] T97 — Composition check CG-7: chat tools and gallery on the integrated candidate · repo: pictures · after: T96, T7.11 · verify: `npm run herramientas:test-integracion -- --modo CG-7` · files: .evidence/REQ-021/CG-7.integration.json · resources: candidate:CG-7 · covers: R13, R16 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run herramientas:test-integracion -- --modo CG-7` adds the save-as-project and staff spend-view steps.

  - Acceptance / integration: On the integrated candidate with SP-7, an Entusiasta counts a decoration without prices and is refused the calculator, a Master Designer opens a gallery decoration as a new project and saves it as a project, and each tool's paid calls appear under its own tag in the staff spend view. Check: `npm run herramientas:test-integracion -- --modo CG-7`

<!-- /CG-7 tasks -->


### M3 — English / Spanish
The interface follows the browser language on the first visit and the account's choice afterwards; the Taller 3D and navigation are fully in English first, then product texts, the remaining screens and the AI replies.

- **SP-8 — Language switch, Taller 3D and navigation in English** (no Designer, owner round 15): A language mechanism with first-visit detection, a switch remembered per account, and every string of the Taller 3D and the navigation in both languages; the public plans section and the data notice move from the browser language to this mechanism. Covers R12.

<!-- SP-8 tasks -->

  SP-8 tasks (owner round 15, 2026-10-28): switch in the account menu, on sign-in and on the plans page; first visit from the browser, then saved on the account (q6); measures cm/m and catalogue prices COP in English too, USD only in the plans section (q7); no Designer: the switch follows the theme toggle and tests check that English text fits at three widths (q8); /asesor and /happie are not translated (q9). Cut order 1 (owner): SP-8 is the part of the language work that ships first; SP-9 and SP-10 are cut before it.
  Mechanism (idioma@1, T8.1): `src/lib/idioma/` with `type Idioma = 'es' | 'en'`, `resolverIdioma(request)`, server and client helpers and `definirTextos({ es, en })`, whose type forces both languages to hold the same keys. No URL prefix and no new dependency: dictionaries are typed modules next to the screens (`textos-*.ts`, `src/components/tres-d/textos/*.ts`). The account's language uses the `idioma` column created by SP-1 T1.1. Spanish stays the default and Spanish rendering does not change.
  Coverage guard (T8.3): a TypeScript-AST scan of the files a task names, used by each extraction task on its own files and by the integration test on all of them. DAG: T8.1 → {T8.2, T8.3} → {T8.4, T8.5, T8.6} → T8.7 integration → T8.8 audit; CG-8 adds SP-8 to the candidate.

- [ ] T8.1 — Language mechanism: detection order, typed bilingual dictionaries and the saved choice · repo: pictures · after: T1.8b · verify: `npm run idioma:test -- --test-name-pattern=deteccion` · files: src/lib/idioma/idioma.ts, src/lib/idioma/servidor.ts, src/lib/idioma/cliente.tsx, src/lib/idioma/textos.ts, src/app/layout.tsx, src/app/api/idioma/route.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-idioma.ts · resources: package.json scripts, contract:idioma, contract:session-guard · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 120 minutes.
  `POST /api/idioma` {idioma} is public (map entry `publica`): sets cookie `idioma` (1 year, SameSite=Lax) and, with a session, updates `cuentas.idioma` through the SP-1 service. npm script `idioma:test` = `tsx --conditions=react-server --test scripts/test/test-idioma.ts`.

  - Acceptance / functional: The language of a request is the signed-in account's saved language, else the idioma cookie, else English when Accept-Language prefers English, else Spanish, and the html lang attribute matches it. Check: `npm run idioma:test -- --test-name-pattern=deteccion`
  - Acceptance / static: Every text dictionary defines the same keys in Spanish and English: TypeScript rejects a key missing in either language and a runtime test lists every dictionary and finds no empty English value. Check: `npm run idioma:test -- --test-name-pattern=paridad`
  - Acceptance / functional: Choosing a language sets the idioma cookie for anyone and, when signed in, saves it on the account, so another browser of the same account opens in that language; a value other than es or en is refused with 400. Check: `npm run idioma:test -- --test-name-pattern=guardar`

- [ ] T8.2 — Language switch and English for navigation, account screens, the plans page and the data notice · repo: pictures · after: T8.1 · verify: `npm run idioma:test-ui-navegacion -- --solo selector` · files: src/components/idioma/SelectorIdioma.tsx, src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-acceso.ts, src/components/cuentas/textos-cuenta.ts, src/components/cuentas/AvisoDatos.tsx, src/app/planes/page.tsx, src/components/planes/textos-planes.ts, src/components/ui/shell/CabeceraApp.tsx, src/components/ui/shell/MenuApp.tsx, src/components/herramientas/textos-herramientas.ts, scripts/test/test-ui-idioma-navegacion.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  The plans page keeps COP for Spanish and USD for English, now from the mechanism (R20). npm script `idioma:test-ui-navegacion` = `tsx scripts/test/test-ui-idioma-navegacion.ts`.

  - Acceptance / functional: A language switch styled like the theme toggle appears in the account menu, on the sign-in screen and on the plans page, and switching re-renders the page in the other language without signing out or losing the open scene. Check: `npm run idioma:test-ui-navegacion -- --solo selector`
  - Acceptance / functional: The plans page, the data notice and the sign-in, activation, reset, notice and Mi cuenta screens and the shared navigation read their language from the mechanism instead of the browser, with every string in Spanish and English. Check: `npm run idioma:test-ui-navegacion -- --solo pantallas`

- [ ] T8.3 — Coverage guard that finds Spanish literals outside the text dictionaries · repo: pictures · after: T8.1 · verify: `npm run idioma:test-guardia` · files: scripts/idioma/cobertura.ts, scripts/idioma/test-cobertura-guardia.ts · resources: package.json scripts · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity medium; scope small_change; risk low; coupling medium; confidence high; estimate 60 minutes.
  `npm run idioma:test-cobertura -- <files…>` = `tsx scripts/idioma/cobertura.ts`; allow-list: numbers and units (cm, m, %), punctuation and icons, product codes (R12, 260Q), brand names (Sempertex). `idioma:test-guardia` = `tsx --test scripts/idioma/test-cobertura-guardia.ts`.

  - Acceptance / functional: npm run idioma:test-cobertura -- <paths> lists every JSX text node and label, title, placeholder or aria-label literal with letters in the given files that does not come from a text dictionary, and exits non-zero when it finds one. Check: `npm run idioma:test-guardia`

- [ ] T8.4 — Taller in English, part 1: shell, library, add panels, menus, help and export · repo: pictures · after: T8.3 · verify: `npm run idioma:test-cobertura -- src/components/tres-d/Taller3D.tsx src/components/tres-d/Biblioteca.tsx src/components/tres-d/PanelAnadir.tsx src/components/tres-d/FondosYMuebles.tsx src/components/tres-d/MenuMas.tsx src/components/tres-d/ExportarEscenaTaller.tsx src/components/tres-d/AyudaTaller.tsx` · files: src/components/tres-d/Taller3D.tsx, src/components/tres-d/Biblioteca.tsx, src/components/tres-d/PanelAnadir.tsx, src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/FormasYLetras.tsx, src/components/tres-d/DecoracionesPequenas.tsx, src/components/tres-d/UtileriaFiesta.tsx, src/components/tres-d/MuralesTechoArboles.tsx, src/components/tres-d/IdeasDelAsistente.tsx, src/components/tres-d/FiltrosTaxonomia.tsx, src/components/tres-d/SelectorRepositorio.tsx, src/components/tres-d/MenuMas.tsx, src/components/tres-d/MenuContextual.tsx, src/components/tres-d/AyudaTaller.tsx, src/components/tres-d/SobreVisor.tsx, src/components/tres-d/ExportarEscenaTaller.tsx, src/components/tres-d/CapturaRender.tsx, src/components/tres-d/ControlesTactiles.tsx, src/components/tres-d/HojaMovil.tsx, src/components/tres-d/DialogoTaller.tsx, src/components/tres-d/BuscarPorFoto.tsx, src/components/tres-d/SelectorAmbienteVisor.tsx, src/components/tres-d/nuevas-taller.tsx, src/components/tres-d/galeria/textos-galeria.ts, src/components/tres-d/textos/taller-marco.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity low; scope large_change; risk medium; coupling high; confidence high; estimate 180 minutes.
  Dictionary `src/components/tres-d/textos/taller-marco.ts`. English wording is plain decorator vocabulary; piece and product names keep their catalogue names until SP-9.

  - Acceptance / static: The Taller shell, library, add panels, menus, help, export and capture components pass the coverage guard, and render in English with no Spanish string left. Check: `npm run idioma:test-cobertura -- src/components/tres-d/Taller3D.tsx src/components/tres-d/Biblioteca.tsx src/components/tres-d/PanelAnadir.tsx src/components/tres-d/FondosYMuebles.tsx src/components/tres-d/MenuMas.tsx src/components/tres-d/ExportarEscenaTaller.tsx src/components/tres-d/AyudaTaller.tsx`

- [ ] T8.5 — Taller in English, part 2: inspector, editors, panels, shopping list and assembly sheet · repo: pictures · after: T8.3 · verify: `npm run idioma:test-taller -- edicion` · files: src/components/tres-d/Inspector.tsx, src/components/tres-d/ParametrosPieza.tsx, src/components/tres-d/EditorConjuntoMesa.tsx, src/components/tres-d/EditorMueble.tsx, src/components/tres-d/EditorRemate.tsx, src/components/tres-d/EditorRotulo.tsx, src/components/tres-d/EditorTrazo.tsx, src/components/tres-d/EditoresFiguras.tsx, src/components/tres-d/PanelEscena.tsx, src/components/tres-d/PanelDecoracion.tsx, src/components/tres-d/PanelPared.tsx, src/components/tres-d/PanelOrganico.tsx, src/components/tres-d/PanelFlor.tsx, src/components/tres-d/PanelPiezas.tsx, src/components/tres-d/PaletaEscena.tsx, src/components/tres-d/SeccionBomba.tsx, src/components/tres-d/SeccionHelio.tsx, src/components/tres-d/SeccionPrecio.tsx, src/components/tres-d/SelectorPerfilTamano.tsx, src/components/tres-d/PartesSolitario.tsx, src/components/tres-d/ListaCompra.tsx, src/components/tres-d/ListaEscenografia.tsx, src/components/tres-d/DialogoCompra.tsx, src/components/tres-d/HojaArmadoCapa.tsx, src/components/tres-d/HojaArmadoCompacta.tsx, src/components/tres-d/HojaArmadoCuartetos.tsx, src/components/tres-d/HojaArmadoEscena.tsx, src/components/tres-d/HojaArmadoEstructura.tsx, src/components/tres-d/HojaArmadoHelio.tsx, src/components/tres-d/HojaArmadoLista.tsx, src/components/tres-d/HojaArmadoMetalizados.tsx, src/components/tres-d/HojaArmadoPagina.tsx, src/components/tres-d/HojaArmadoTramos.tsx, src/components/tres-d/TarjetaReceta.tsx, src/components/tres-d/EtiquetasMedidas.tsx, src/components/tres-d/MarcaHelio.tsx, src/components/tres-d/ProcedenciaDeItem.tsx, src/components/tres-d/GrillaCompacta.tsx, src/components/tres-d/CampoTexto.tsx, src/components/tres-d/DiagramaCapa.tsx, src/components/tres-d/CotizacionProfesionalDesdeTaller.tsx, src/components/tres-d/ControlFotoIA.tsx, src/components/tres-d/EtapasFotoRealista.tsx, src/components/tres-d/VisorFoto.tsx, src/components/tres-d/GeneradorIA.tsx, src/components/tres-d/textos/taller-edicion.ts, scripts/test/test-idioma-taller.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity low; scope large_change; risk medium; coupling high; confidence high; estimate 210 minutes.
  Dictionary `src/components/tres-d/textos/taller-edicion.ts`. npm script `idioma:test-taller` = `tsx scripts/test/test-idioma-taller.ts <area>` renders the area in both languages and compares Spanish with the pre-change output; `HojaArmado.test.ts` keeps passing unchanged in Spanish. Measures stay cm/m and prices COP.

  - Acceptance / functional: The Taller inspector, piece editors, scene and decoration panels, shopping list, purchase dialog and assembly sheet pass the coverage guard and render in English with no Spanish string left, while Spanish rendering stays byte-identical. Check: `npm run idioma:test-taller -- edicion`

- [ ] T8.6 — Taller in English, part 3: AI panel and the user-facing sentences built in lib · repo: pictures · after: T8.3 · verify: `npm run idioma:test-mensajes` · files: src/components/tres-d/ia/BannerVerAntes.tsx, src/components/tres-d/ia/CalificacionTurno.tsx, src/components/tres-d/ia/ComposicionIA.tsx, src/components/tres-d/ia/MenuConversacion.tsx, src/components/tres-d/ia/PanelIA.tsx, src/components/tres-d/ia/PestanasLaterales.tsx, src/components/tres-d/ia/TarjetaEnCurso.tsx, src/components/tres-d/ia/TarjetaFotoRealista.tsx, src/components/tres-d/ia/TarjetaPregunta.tsx, src/components/tres-d/ia/TarjetaTurno.tsx, src/components/tres-d/ia/useNombresDePasos.ts, src/lib/globos3d/avisos-usuario.ts, src/lib/globos3d/glosario-taller.ts, src/lib/errores-ui/traducir-error-servidor.ts, src/components/tres-d/textos/taller-ia.ts, scripts/test/test-idioma-mensajes-taller.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-8 · ui: no

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 150 minutes.
  Sentence builders take `idioma: Idioma` (default 'es'). The model's own reply language is SP-10. npm script `idioma:test-mensajes` = `tsx --test scripts/test/test-idioma-mensajes-taller.ts`.

  - Acceptance / functional: The Taller AI panel and the user-facing sentences built in src/lib (tool notices, the Taller glossary and server error messages shown in the Taller) are produced in the request's language, and the AI panel files pass the coverage guard. Check: `npm run idioma:test-mensajes`

- [ ] T8.7 — Browser end-to-end: English first visit, saved choice, no Spanish left and text that fits · repo: pictures · after: T8.2, T8.4, T8.5, T8.6 · verify: `npm run idioma:test-integracion` · files: scripts/test/test-integracion-idioma.ts, .evidence/REQ-021/SP-8.integration.json · resources: package.json scripts · covers: R12 · kind: test · subplan: SP-8

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 100 minutes.
  npm script `idioma:test-integracion` = `tsx scripts/test/test-integracion-idioma.ts`; it also runs the coverage guard over every file of T8.2, T8.4, T8.5 and T8.6.

  - Acceptance / integration: On a production build, a first visit with an English browser shows the sign-in screen, the navigation and the Taller 3D in English, with expected texts taken from the dictionaries; switching to Spanish is kept on the account in a second browser; a scan of the rendered English Taller finds no Spanish string; and no label, button or menu item overflows its box at 390, 768 and 1280 px. Check: `npm run idioma:test-integracion`

- [ ] T8.8 — SP-8 audit: language detection, saved choice, coverage and unchanged Spanish · repo: pictures · after: T8.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-8.findings.json` · files: .evidence/REQ-021/SP-8.audit.md, .evidence/REQ-021/SP-8.findings.json · resources: ledger:SP-8 · covers: R12 · kind: audit · subplan: SP-8

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  Checks at least: detection order, cookie and account consistency, no Spanish in covered files, Spanish output unchanged, cm/m and COP kept.

  - Acceptance / static: An independent audit of SP-8 records every confirmed defect with the task that must redo it in the SP-8 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-8.findings.json`

<!-- /SP-8 tasks -->

<!-- CG-8 tasks -->

  Composition gate CG-8: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7, SP-8 (cumulative, after CG-7).

- [ ] T98 — Composition check CG-8: English across accounts, saved projects, tools and the Taller · repo: pictures · after: T97, T8.8 · verify: `npm run idioma:test-integracion -- --modo CG-8` · files: .evidence/REQ-021/CG-8.integration.json · resources: candidate:CG-8 · covers: R12 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run idioma:test-integracion -- --modo CG-8`.

  - Acceptance / integration: On the integrated candidate with SP-8, an English first visit signs in, opens a saved project and a gallery decoration in the English Taller, counts with the counter, and switching to Spanish is kept on the account in another browser. Check: `npm run idioma:test-integracion -- --modo CG-8`

<!-- /CG-8 tasks -->


- **SP-9 — Product and decoration texts in English** (no Designer, owner round 16): English names and descriptions for every product and decoration are generated once from the Spanish source, stored, shown when the language is English with the Spanish text as fallback, and correctable by an administrator. Covers R12.

<!-- SP-9 tasks -->

  SP-9 tasks (owner round 16, 2026-10-29): q1 names and descriptions of the 1,615 products, their variant colour and size names and the 448 ready-made decorations (25 Ideas del asistente, 423 Ideas Sempertex), never people's own texts; q2 never regenerated, only the administrator changes them; q3 no Designer: an «Textos en inglés» tab in Administración following the existing tabs. The catalogue lives in SQLite re-seeded on every Vercel start (src/lib/shopify/persistir-catalogo.ts, snapshot src/lib/shopify/datos/catalogo-publico.json), so English texts live in Postgres keyed by Shopify id. Translation runs once with Haiku 5.5 through the owner's Claude accounts (SPEC Inputs) and is committed as data files, so production receives it by the seed step of SP-13 without any AI call there.
  DAG: T9.1 (storage, lookup) → T9.2 (one-time generation, validation, seed) → {T9.3 show English at the boundaries, T9.4 admin tab} → T9.5 integration → T9.6 audit; CG-9 adds SP-9 after CG-8.

- [ ] T9.1 — English-text storage and the lookup with Spanish fallback · repo: pictures · after: T8.8 · verify: `npm run textos:test -- --test-name-pattern=almacen` · files: scripts/migrations/041_textos_ingles.sql, src/lib/textos-ingles/repositorio.ts, src/lib/textos-ingles/consulta.ts, scripts/test/test-textos-ingles.ts · resources: package.json scripts, contract:textos-ingles · covers: R12 · kind: implement · subplan: SP-9 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence high; estimate 75 minutes.
  Table `textos_ingles` (tipo `producto|variante_opcion|idea`, clave, campo `nombre|descripcion`, texto_es_fuente, texto_en, origen `ia|admin`, actualizado_en; unique (tipo, clave, campo)). `textosEn(peticiones, idioma)` returns a map in one query. npm script `textos:test` = `tsx --conditions=react-server --test scripts/test/test-textos-ingles.ts`.

  - Acceptance / functional: Migration 041 creates a Postgres table of English texts keyed by kind, source id and field with the Spanish source text, the English text and its origin (ia or admin), and a lookup returns the English text in English and the Spanish source when no English exists. Check: `npm run textos:test -- --test-name-pattern=almacen`

- [ ] T9.2 — One-time English generation with Haiku 5.5, its validator and the idempotent seed · repo: pictures · after: T9.1 · verify: `npm run textos:validar` · files: scripts/textos/traducir.ts, scripts/textos/glosario.ts, scripts/textos/validar.ts, scripts/textos/sembrar.ts, data/textos-ingles/productos.json, data/textos-ingles/variantes.json, data/textos-ingles/ideas.json, scripts/textos/test-textos-scripts.ts · resources: package.json scripts, contract:textos-ingles · covers: R12 · kind: implement · subplan: SP-9 · ui: no

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 180 minutes.
  `npm run textos:traducir` reads the snapshot (titulo/titulo_limpio, descripcion_txt), the distinct variant option values and both idea sets, sends batches of 40 to `claude -p --model claude-haiku-5-5 --output-format json` with the glossary (balloon sizes like R12 and 260Q, Sempertex, Fashion, Deco and Metallic lines kept as written) and writes the three data files. `npm run textos:validar` and `npm run textos:sembrar` work without any model; `textos:test-scripts` = `tsx --test scripts/textos/test-textos-scripts.ts`.

  - Acceptance / static: npm run textos:validar accepts the generated English files only when every catalogue product, variant colour or size name and ready-made decoration in the repository snapshot has a non-empty English name and description where a Spanish one exists, product codes and brand names are unchanged, and no English text equals its Spanish source unless the pair is listed as a brand or code. Check: `npm run textos:validar`
  - Acceptance / functional: npm run textos:sembrar loads the generated files into the database idempotently: a second run changes nothing, and a text whose origin is admin is never overwritten. Check: `npm run textos:test-scripts -- --test-name-pattern=sembrar`

- [ ] T9.3 — Show English product and decoration texts at every boundary that sends them to the browser · repo: pictures · after: T9.2 · verify: `npm run textos:test-fronteras` · files: src/lib/textos-ingles/aplicar.ts, src/app/catalogo/page.tsx, src/app/catalogo/[handle]/page.tsx, src/app/api/catalogo/repositorios/route.ts, src/app/api/taller/buscar/route.ts, src/lib/globos3d/biblioteca.ts, src/lib/globos3d/galeria-decoraciones.ts, src/lib/ia/herramientas/registro-herramientas.ts, scripts/test/test-textos-fronteras.ts · resources: package.json scripts, contract:textos-ingles, contract:idioma · covers: R12 · kind: implement · subplan: SP-9 · ui: no

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 150 minutes.
  `aplicarTextosIngles(items, idioma)` replaces name and description fields only when idioma is en; npm script `textos:test-fronteras` = `tsx --conditions=react-server --test scripts/test/test-textos-fronteras.ts` (each boundary in English and Spanish, Spanish compared with today's output).

  - Acceptance / functional: With the language set to English, every serialization boundary that sends product or decoration names to the browser (catalogue pages and APIs, Taller search, shopping list, chat product results, gallery index and the Taller idea library) sends the English text, falling back to Spanish, and with Spanish sends exactly what it sends today. Check: `npm run textos:test-fronteras`

- [ ] T9.4 — «Textos en inglés» administration tab and its protected API · repo: pictures · after: T9.2 · verify: `npm run textos:test-admin -- --solo correccion` · files: src/components/admin/TextosInglesTab.tsx, src/components/admin/AdminTabs.tsx, src/app/api/admin/textos-ingles/route.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-admin-textos-ingles.ts · resources: package.json scripts, contract:textos-ingles, contract:permission-map · covers: R12 · kind: implement · subplan: SP-9 · ui: no

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  Staff screens stay Spanish (round 16 q4). npm script `textos:test-admin` = `tsx scripts/test/test-admin-textos-ingles.ts`.

  - Acceptance / functional: An administrator with textos.corregir finds a text in the «Textos en inglés» administration tab by name or id, filters by pendiente, IA, corregido or la fuente cambió, saves a correction that becomes origin admin, and accounts without the permission get 403 from its API. Check: `npm run textos:test-admin -- --solo correccion`
  - Acceptance / functional: Nothing regenerates an English text after it is stored: a later change of the Spanish source only marks the text «la fuente cambió» in the administration list, and products added later show Spanish until an administrator writes English. Check: `npm run textos:test-admin -- --solo fuente-cambio`

- [ ] T9.5 — Browser end-to-end: English catalogue, Taller and gallery names with an administrator correction · repo: pictures · after: T9.3, T9.4 · verify: `npm run textos:test-integracion` · files: scripts/test/test-integracion-textos-ingles.ts, .evidence/REQ-021/SP-9.integration.json · resources: package.json scripts · covers: R12 · kind: test · subplan: SP-9

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  npm script `textos:test-integracion` = `tsx scripts/test/test-integracion-textos-ingles.ts`.

  - Acceptance / integration: On a production build against the REQ-021 database with the seeded English texts, an English session sees English product and decoration names in the catalogue, the Taller library, the shopping list and the gallery; an administrator's correction appears there on the next request; and a Spanish session sees today's Spanish names. Check: `npm run textos:test-integracion`

- [ ] T9.6 — SP-9 audit: English texts, fallback, no regeneration and correction permissions · repo: pictures · after: T9.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-9.findings.json` · files: .evidence/REQ-021/SP-9.audit.md, .evidence/REQ-021/SP-9.findings.json · resources: ledger:SP-9 · covers: R12 · kind: audit · subplan: SP-9

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 65 minutes.
  Read-only; checks the English texts' coverage, Spanish fallback, the no-regeneration rule and the correction permission.

  - Acceptance / static: An independent audit of SP-9 checks the English texts' coverage, Spanish fallback, the no-regeneration rule and the correction permission, records every confirmed defect with the task that must redo it in the SP-9 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-9.findings.json`

<!-- /SP-9 tasks -->

<!-- CG-9 tasks -->

  Composition gate CG-9: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7, SP-8, SP-9 (cumulative).

- [ ] T99 — Composition check CG-9: English product and decoration texts across tools and the Taller · repo: pictures · after: T98, T9.6 · verify: `npm run textos:test-integracion -- --modo CG-9` · files: .evidence/REQ-021/CG-9.integration.json · resources: candidate:CG-9 · covers: R12 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run textos:test-integracion -- --modo CG-9`.

  - Acceptance / integration: On the integrated candidate with SP-9, an English session sees English product names in the counter's shopping list, the calculator and the Taller library, and a saved project reopens with English names. Check: `npm run textos:test-integracion -- --modo CG-9`

<!-- /CG-9 tasks -->


- **SP-10 — Remaining screens and AI replies in English** (no Designer, Planner ruling after round 16): The chat tools, catalogue, administration, spend and statistics screens are fully in English, and the scene AI and the chat tools reply in the user's language. Covers R12.

<!-- SP-10 tasks -->

  SP-10 tasks (owner round 16, 2026-10-29): q4 every screen an external user sees plus the AI replies; staff screens stay Spanish; q5 the model understands English and searches the Spanish catalogue, answering in English with SP-9's names. No Designer (Planner ruling, same reason as SP-8 q8: only texts change; overflow is tested). Measured on origin/main: about 180 literals in src/components/guiado (47 files) and 325 in src/components/plan (62 files), plus the SP-4, SP-5 and SP-7 text modules.
  DAG: T10.1 (guided chat and plan views) ∥ T10.2 (tools, catalogue, gallery, projects, library) ∥ T10.3 (reply language and search) → T10.4 staff exclusion list → T10.5 integration → T10.6 audit; CG-10 adds SP-10 after CG-9. Cut order 1 (owner): SP-10 is the first language work to drop if late.

- [ ] T10.1 — Guided chat and structure-plan views in English · repo: pictures · after: T9.6 · verify: `npm run idioma:test-cobertura -- src/components/guiado src/components/propuesta src/components/plan` · files: src/components/guiado/**/*.tsx, src/components/propuesta/**/*.tsx, src/components/plan/**/*.tsx, src/components/guiado/textos/chat-guiado.ts, src/components/plan/textos/planes-estructura.ts, src/lib/estado/pasos-asistente.ts, src/lib/guiada-motor/mensajes-cliente.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-10 · ui: no

  Classification: complexity low; scope large_change; risk medium; coupling high; confidence high; estimate 240 minutes.
  npm script `idioma:test-cobertura` (SP-8) over the listed directories.

  - Acceptance / static: The guided chat and its components (src/components/guiado, src/components/propuesta) and the structure-plan views (src/components/plan) pass the coverage guard and render in English with no Spanish string left, while Spanish rendering is unchanged. Check: `npm run idioma:test-cobertura -- src/components/guiado src/components/propuesta src/components/plan`

- [ ] T10.2 — Tools, catalogue, gallery, saved projects and personal library in English · repo: pictures · after: T9.6 · verify: `npm run idioma:test-cobertura -- src/components/herramientas src/components/cotizacion src/components/catalogo src/app/catalogo src/components/tres-d/galeria src/components/proyectos src/components/tres-d/biblioteca` · files: src/components/herramientas/**/*.ts, src/components/herramientas/**/*.tsx, src/components/cotizacion/**/*.tsx, src/components/catalogo/**/*.tsx, src/app/catalogo/page.tsx, src/app/catalogo/[handle]/page.tsx, src/components/tres-d/galeria/textos-galeria.ts, src/components/proyectos/textos-proyectos.ts, src/components/tres-d/biblioteca/textos-biblioteca.ts · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-10 · ui: no

  Classification: complexity low; scope large_change; risk medium; coupling medium; confidence high; estimate 150 minutes.
  The professional quote keeps COP in English (round 15 q7).

  - Acceptance / static: The home, counter, calculator and professional quote (src/components/herramientas, src/components/cotizacion), the catalogue (src/components/catalogo, src/app/catalogo), the gallery and the saved-project and personal-library screens pass the coverage guard and render in English with no Spanish string left. Check: `npm run idioma:test-cobertura -- src/components/herramientas src/components/cotizacion src/components/catalogo src/app/catalogo src/components/tres-d/galeria src/components/proyectos src/components/tres-d/biblioteca`

- [ ] T10.3 — AI replies in the user's language with catalogue searches kept in Spanish · repo: pictures · after: T9.6 · verify: `npm run idioma:test-respuestas -- --test-name-pattern=prompt` · files: src/lib/ia/guiado/prompt-guiado.ts, src/lib/ia/omoikane/prompt-sistema.ts, src/lib/ia/escena/entorno-escena.ts, src/lib/ia/herramientas/herramientas.ts, src/lib/contador/contar.ts, src/lib/ia/nucleo/python-adapter.ts, services/ai-api/app/main.py, scripts/test/test-idioma-respuestas-ia.ts, services/ai-api/tests/test_idioma_respuesta.py · resources: package.json scripts, contract:idioma · covers: R12 · kind: implement · subplan: SP-10 · ui: no

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 150 minutes.
  npm script `idioma:test-respuestas` = `tsx --conditions=react-server --test scripts/test/test-idioma-respuestas-ia.ts`; ai-api test runs with `uv run --directory services/ai-api pytest tests/test_idioma_respuesta.py`.

  - Acceptance / functional: Every prompt builder that sets the model's reply language (guided chat, plan agent, counter phrase extraction and the Taller scene AI, in Next and in services/ai-api) receives the request's language, and with a stub provider an English request produces an English instruction while a Spanish request produces exactly today's prompt. Check: `npm run idioma:test-respuestas -- --test-name-pattern=prompt`
  - Acceptance / functional: With English input the chat's catalogue tools still search the Spanish catalogue: the tool instructions tell the model to search in Spanish, and a stubbed English conversation calls the search tool with Spanish terms and answers in English with the English product names of SP-9. Check: `npm run idioma:test-respuestas -- --test-name-pattern=busqueda`

- [ ] T10.4 — Explicit list of staff screens that stay in Spanish · repo: pictures · after: T10.1, T10.2, T10.3 · verify: `npm run idioma:test-personal` · files: scripts/idioma/pantallas-personal.ts, scripts/idioma/test-pantallas-personal.ts · resources: package.json scripts · covers: R12 · kind: implement · subplan: SP-10 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence high; estimate 40 minutes.
  `PANTALLAS_PERSONAL` = every page whose map permission is `internas.usar`, `gasto.ver`, `cuentas.administrar` or `roles.administrar`; the test fails if an external page is listed. npm script `idioma:test-personal` = `tsx --test scripts/idioma/test-pantallas-personal.ts`.

  - Acceptance / functional: Staff-only screens (administration, orders, statistics, AI spend, AI feedback, laboratories) stay in Spanish and are excluded from the coverage guard by an explicit list. Check: `npm run idioma:test-personal`

- [ ] T10.5 — Browser end-to-end: external screens and one live AI turn in English · repo: pictures · after: T10.4 · verify: `npm run idioma:test-integracion-resto` · files: scripts/test/test-integracion-idioma-resto.ts, .evidence/REQ-021/SP-10.integration.json · resources: package.json scripts · covers: R12 · kind: test · subplan: SP-10

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 90 minutes.
  npm script `idioma:test-integracion-resto` = `tsx scripts/test/test-integracion-idioma-resto.ts`; the live turn uses the cheapest configured model once.

  - Acceptance / integration: On a production build, with expected texts taken from the dictionaries, an English Designer Plus account uses the home, the guided chat, the counter and the calculator, and a Master Designer opens the gallery and a saved project, all in English; one live chat turn on the cheapest configured model answers in English; and a scan of each rendered page finds no Spanish string outside staff screens. Check: `npm run idioma:test-integracion-resto`

- [ ] T10.6 — SP-10 audit: external screens and AI replies in English · repo: pictures · after: T10.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-10.findings.json` · files: .evidence/REQ-021/SP-10.audit.md, .evidence/REQ-021/SP-10.findings.json · resources: ledger:SP-10 · covers: R12 · kind: audit · subplan: SP-10

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 65 minutes.
  Read-only; checks external-screen coverage, unchanged Spanish prompts and English replies.

  - Acceptance / static: An independent audit of SP-10 checks external-screen coverage, unchanged Spanish prompts and English replies, records every confirmed defect with the task that must redo it in the SP-10 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-10.findings.json`

<!-- /SP-10 tasks -->

<!-- CG-10 tasks -->

  Composition gate CG-10: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7, SP-8, SP-9, SP-10 (cumulative).

- [ ] T100 — Composition check CG-10: the whole external app in English · repo: pictures · after: T99, T10.6 · verify: `npm run idioma:test-integracion-resto -- --modo CG-10` · files: .evidence/REQ-021/CG-10.integration.json · resources: candidate:CG-10 · covers: R12 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run idioma:test-integracion-resto -- --modo CG-10`.

  - Acceptance / integration: On the integrated candidate with SP-10, an English Master Designer goes from sign-in through the home, chat, counter, calculator, gallery, a saved project and the Taller entirely in English, and a Spanish account sees today's Spanish. Check: `npm run idioma:test-integracion-resto -- --modo CG-10`

<!-- /CG-10 tasks -->



### M4 — Editable modules and chat → 3D
Users edit modules and quartets beyond colours, and the normal chat recommends ready-made 3D decorations that open in the workshop.

- **SP-11 — Editable modules and quartets** (no Designer, Planner ruling after round 16): A user edits a module or quartet in the scene beyond its colours (the exact edits are settled with the owner in this subplan) and the counts and shopping list update. Covers R15.

<!-- SP-11 tasks -->

  SP-11 tasks (owner round 16 q6 a, 2026-10-29): only spacing between quartets and thickness of columns, arches and garlands. Today `armarTrenza` (src/lib/globos3d/trenza.ts) fixes them with PASO_POR_DIAMETRO = 0.8 and RADIO_TRENZA_POR_DIAMETRO = 0.62 and the editor (EditorTrenzaCompleto in ParametrosPieza.tsx) has no control for them. Ranges 0.6–1.2 and 0.5–0.8 diameters are a Planner ruling (below 0.6 balloons overlap, above 1.2 gaps show); the defaults stay the constants. No Designer (Planner ruling): two sliders in the existing editor follow its slider pattern. Cut order 2 (owner): SP-11 drops before chat→3D if late.
  DAG: T11.1 (engine and schema) → T11.2 (editor controls) → T11.3 integration → T11.4 audit; CG-11 adds SP-11 after CG-10.

- [ ] T11.1 — Optional spacing and thickness in the quartet engine and the scene schema · repo: pictures · after: T100 · verify: `npm run trenza:test-separacion -- --test-name-pattern=rango-y-defecto` · files: src/lib/globos3d/trenza.ts, src/lib/globos3d/piezas.ts, src/lib/globos3d/esquema-escena.ts, src/lib/globos3d/hoja-armado-estructura.ts, scripts/test/test-trenza-separacion.ts · resources: package.json scripts, contract:taller-scene · covers: R15 · kind: implement · subplan: SP-11 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence high; estimate 120 minutes.
  Fields `separacion?: number` and `grosor?: number` (in diameters) on columna and arco and in OpcionesGuirnalda; `armarTrenza` reads them with the constants as defaults. npm script `trenza:test-separacion` = `tsx --conditions=react-server --test scripts/test/test-trenza-separacion.ts`; the existing goldens (`npm run globos3d:test`) stay unchanged.

  - Acceptance / functional: Columns, arches and garlands built from quartets accept an optional spacing between quartets of 0.6 to 1.2 balloon diameters and an optional thickness of 0.5 to 0.8 diameters; without them every existing piece, count and golden scene is byte-identical, and values outside the range are refused by the scene schema. Check: `npm run trenza:test-separacion -- --test-name-pattern=rango-y-defecto`
  - Acceptance / functional: Changing the spacing of a column, arch or garland changes its number of quartets as height or length divided by the spacing, and the balloon counts, the shopping list and the assembly sheet change accordingly, while changing only the thickness changes no count. Check: `npm run trenza:test-separacion -- --test-name-pattern=conteos`

- [ ] T11.2 — Spacing and thickness controls in the column, arch and garland editor · repo: pictures · after: T11.1 · verify: `npm run trenza:test-ui -- --solo controles` · files: src/components/tres-d/ParametrosPieza.tsx, src/components/tres-d/textos/taller-edicion.ts, scripts/test/test-ui-separacion-trenza.ts · resources: package.json scripts · covers: R15 · kind: implement · subplan: SP-11 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence high; estimate 75 minutes.
  npm script `trenza:test-ui` = `tsx scripts/test/test-ui-separacion-trenza.ts`.

  - Acceptance / functional: Selecting a column, arch or garland shows spacing and thickness controls in its editor with the current value in centimetres and a reset to the default; moving them updates the scene, the counts and the shopping list, and undo restores the previous values. Check: `npm run trenza:test-ui -- --solo controles`
  - Acceptance / functional: A scene holding pieces with spacing and thickness saves as a project, reopens with the same values and exports to GLB with the edited geometry. Check: `npm run trenza:test-ui -- --solo guardar-y-exportar`

- [ ] T11.3 — Browser end-to-end: edit spacing and thickness, save, reopen and export · repo: pictures · after: T11.2 · verify: `npm run trenza:test-integracion` · files: scripts/test/test-integracion-separacion-trenza.ts, .evidence/REQ-021/SP-11.integration.json · resources: package.json scripts · covers: R15 · kind: test · subplan: SP-11

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  npm script `trenza:test-integracion` = `tsx scripts/test/test-integracion-separacion-trenza.ts`.

  - Acceptance / integration: On a production build against the REQ-021 database, a Master Designer edits the spacing and thickness of a column and an arch, sees the counts and shopping list change, saves the project, reopens it in another browser with the same values, and exports a GLB whose column height is unchanged. Check: `npm run trenza:test-integracion`

- [ ] T11.4 — SP-11 audit: quartet spacing and thickness, counts and compatibility · repo: pictures · after: T11.3 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-11.findings.json` · files: .evidence/REQ-021/SP-11.audit.md, .evidence/REQ-021/SP-11.findings.json · resources: ledger:SP-11 · covers: R15 · kind: audit · subplan: SP-11

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 55 minutes.
  Read-only; checks the spacing and thickness ranges, count updates and unchanged existing scenes.

  - Acceptance / static: An independent audit of SP-11 checks the spacing and thickness ranges, count updates and unchanged existing scenes, records every confirmed defect with the task that must redo it in the SP-11 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-11.findings.json`

<!-- /SP-11 tasks -->

<!-- CG-11 tasks -->

  Composition gate CG-11: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7, SP-8, SP-9, SP-10, SP-11 (cumulative).

- [ ] T101 — Composition check CG-11: edited structures in saved projects, decorations and English · repo: pictures · after: T11.4 · verify: `npm run trenza:test-integracion -- --modo CG-11` · files: .evidence/REQ-021/CG-11.integration.json · resources: candidate:CG-11 · covers: R15 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run trenza:test-integracion -- --modo CG-11`.

  - Acceptance / integration: On the integrated candidate with SP-11, an edited column saves as a project and as a personal decoration, reopens with the same spacing, and its editor controls read in English for an English account. Check: `npm run trenza:test-integracion -- --modo CG-11`

<!-- /CG-11 tasks -->


- **SP-12 — Normal chat recommends ready-made 3D decorations** (UI: `chat-a-3d@v1`): In two or three messages the normal chat defines the need and recommends existing 3D decorations that open in the Taller 3D as a new project, using the real catalogue and engine. Covers R13.

<!-- SP-12 tasks -->

  SP-12 tasks (owner round 16 q7 a, 2026-10-29): every plan sees 2–3 recommended ready-made decorations with image, name and count; only Master Designer and staff see «Abrir en el Taller» (decoraciones.explorar), without naming the plan. Recommendations come from the SP-7 gallery index (galeria-index@1: IDEAS_ASISTENTE and IDEAS_SEMPERTEX) and counts from each idea's own shopping list, never from the model. Cut order 3 (owner): chat→3D drops before the never-cut items if late.
  DAG: T12.1 (design) ∥ T12.2 (recommender and chat tool) → T12.3 (cards) → T12.4 integration → T12.5 visual review → T12.6 audit; CG-12 adds SP-12 after CG-11.

- [ ] T12.1 — Copy the owner-approved chat-a-3d@v1 contract into the repository · repo: pictures · after: T101 · verify: `test -s design/contracts/chat-a-3d@v1.md` · files: design/contracts/chat-a-3d@v1.md · resources: design:chat-a-3d@v1 · covers: R13 · kind: design · subplan: SP-12 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.
  The scheduler supplies the plan-approved draft; the task copies it unchanged.

  - Acceptance / static: The owner-approved chat-a-3d@v1 contract is copied byte for byte into design/contracts/chat-a-3d@v1.md. Check: `test -s design/contracts/chat-a-3d@v1.md`

- [ ] T12.2 — Deterministic 3D decoration recommender and its guided-chat tool · repo: pictures · after: T101 · verify: `npm run recomendaciones:test -- --test-name-pattern=ranking` · files: src/lib/recomendaciones-3d/recomendar.ts, src/app/api/asistente-guiado/route.ts, src/lib/ia/guiado/prompt-guiado.ts, scripts/test/test-recomendaciones-3d.ts · resources: package.json scripts, contract:galeria-index · covers: R13 · kind: implement · subplan: SP-12 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 120 minutes.
  Tool `recomendar_decoraciones_3d` {ocasion, tamano, colores} → `[{ id, nombre, imagen, globos }]`. npm script `recomendaciones:test` = `tsx --conditions=react-server --test scripts/test/test-recomendaciones-3d.ts`.

  - Acceptance / functional: Given a brief with event type, approximate size and colours, the recommender returns two or three existing gallery decorations ranked by occasion, colour match and size, each with its id, name, preview image and total balloon count taken from the decoration's own shopping list, and returns none rather than a weak match when nothing fits. Check: `npm run recomendaciones:test -- --test-name-pattern=ranking`
  - Acceptance / functional: Within at most three customer messages the guided chat collects the brief and calls the recommendation tool; its reply names only the decorations the tool returned, and a stubbed model that tries to name another decoration or another count is corrected by the final-text guard. Check: `npm run recomendaciones:test -- --test-name-pattern=herramienta`

- [ ] T12.3 — Recommendation cards in the guided chat with a plan-gated open button · repo: pictures · after: T12.1, T12.2 · verify: `npm run recomendaciones:test-ui` · files: src/components/guiado/TarjetaRecomendacion3D.tsx, src/components/guiado/textos/recomendaciones-3d.ts, scripts/test/test-ui-recomendaciones-3d.ts · resources: package.json scripts, contract:permission-map · covers: R13 · kind: implement · subplan: SP-12 · ui: yes

  Classification: complexity low; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  npm script `recomendaciones:test-ui` = `tsx scripts/test/test-ui-recomendaciones-3d.ts`.

  - Acceptance / functional: The chat shows each recommendation as a card with preview, name in the session's language and balloon count; «Abrir en el Taller» appears only for accounts with decoraciones.explorar and opens /3d?decoracion=<id> as a new project, and other accounts see the card without the button and without any mention of a plan. Check: `npm run recomendaciones:test-ui`

- [ ] T12.4 — Browser end-to-end: recommendations for two plans and opening one in the Taller · repo: pictures · after: T12.3 · verify: `npm run recomendaciones:test-integracion` · files: scripts/test/test-integracion-recomendaciones-3d.ts, .evidence/REQ-021/SP-12.integration.json · resources: package.json scripts · covers: R13 · kind: test · subplan: SP-12

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  npm script `recomendaciones:test-integracion` = `tsx scripts/test/test-integracion-recomendaciones-3d.ts`.

  - Acceptance / integration: On a production build, with expected results written from the SPEC, an Entusiasta describes a birthday in two messages and gets two or three recommendation cards without an open button, and a Master Designer gets the same cards, opens one in the Taller as a new unsaved project and saves it. Check: `npm run recomendaciones:test-integracion`

- [ ] T12.5 — SP-12 visual review against the chat-a-3d@v1 contract · repo: pictures · after: T12.4 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-12.visual.findings.json` · files: .evidence/REQ-021/SP-12.visual.md, .evidence/REQ-021/SP-12.visual.findings.json · resources: ledger:SP-12-visual · covers: R13 · kind: audit · subplan: SP-12

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit).

  - Acceptance / static: The rendered recommendation cards with and without the open button match the approved chat-a-3d@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-12 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-12.visual.findings.json`

- [ ] T12.6 — SP-12 audit: recommendation sources, invented values and the open-button gate · repo: pictures · after: T12.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-12.findings.json` · files: .evidence/REQ-021/SP-12.audit.md, .evidence/REQ-021/SP-12.findings.json · resources: ledger:SP-12 · covers: R13 · kind: audit · subplan: SP-12

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 55 minutes.
  Read-only; checks recommendation sources, invented names or counts and the open-button permission.

  - Acceptance / static: An independent audit of SP-12 checks recommendation sources, invented names or counts and the open-button permission, records every confirmed defect with the task that must redo it in the SP-12 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-12.findings.json`

<!-- /SP-12 tasks -->

<!-- CG-12 tasks -->

  Composition gate CG-12: SP-1, SP-2, SP-14, SP-3, SP-4, SP-5, SP-6, SP-7, SP-8, SP-9, SP-10, SP-11, SP-12 (cumulative).

- [ ] T102 — Composition check CG-12: chat recommendations into saved projects, in both languages · repo: pictures · after: T12.6 · verify: `npm run recomendaciones:test-integracion -- --modo CG-12` · files: .evidence/REQ-021/CG-12.integration.json · resources: candidate:CG-12 · covers: R13 · kind: test

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 40 minutes.
  `npm run recomendaciones:test-integracion -- --modo CG-12`.

  - Acceptance / integration: On the integrated candidate with SP-12, an English Master Designer gets English recommendation cards, opens one as a new project, edits a column's spacing and saves it, and the AI spend view shows the chat call under its tag. Check: `npm run recomendaciones:test-integracion -- --modo CG-12`

<!-- /CG-12 tasks -->



### M5 — Pilot release
The pilot runs in production with real accounts: the first administrator exists, every shipped subplan is published, a production smoke passes and anything cut is listed.

- **SP-13 — Pilot release in production**: Every approved subplan is published to production with its migrations, the first administrator is created, an end-to-end flow (invite → activate → save project and decoration → spend appears → export GLB) passes against production, and the cut list is recorded. Covers R14.

## Review focus — amendment A-1 (plans)
Five likeliest uncovered input classes, each with its owning test:
1. A plan with a missing price or name, an unknown permission key or a plan that drops a permission of the plan below → T1.2 `planes:test-catalogo`.
2. A price or tool retyped in the page instead of read from the catalogue → T14.2 `planes:test-ui -- --solo catalogo` (changed catalogue value appears) and T14.6 audit.
3. Both currencies shown, or the wrong one for the browser language → T14.2 `--solo idioma`, T14.4 English context.
4. The new public route opening other pages or APIs without a session → T14.2 `--solo ruta-publica`, T14.4 `--solo sin-sesion`.
5. The accounts screen offering plan names that differ from the section, or a plan granting the wrong tools → T1.2 `roles-sistema`, T94 `planes:test-composicion`.

## Review focus — SP-3 (2026-10-27, contract and code changes)
1. A candidate whose id collides with an existing prop or table type, without a cited source, or a new form without parameters, justification or estimate → T3.2 `test-validar-propuesta-piloto.ts`, `validar-propuesta-piloto.ts`.
2. A registry missing a table type, a piece type (modulo) or a Backing → T3.3 `npx tsc --noEmit` and `test-taller-registros-completos.ts`.
3. A new table outline that seats chairs through the top or miscounts them in the shopping list → T3.5 `test-taller-mesas-nuevas.ts`.
4. An existing table type, catalogue golden, saved scene or reference photo that changes → T3.3/T3.5 `test-catalogo-dorado.ts`, `test-sillas-por-mesa.ts`, `test-salon-mesas-parametricas.ts`, T3.7 `test-compilar-lectura.ts`.
5. An element type that exports wrongly and is reported as passing → T3.11 `test-glb-todos-los-tipos.ts` (types enumerated by `elementosEnumerables()`), T3.12/T3.13 per-type Blender comparison.
