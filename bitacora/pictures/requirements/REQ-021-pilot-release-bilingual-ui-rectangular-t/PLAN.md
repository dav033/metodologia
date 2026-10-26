---
req: REQ-021
status: draft
created: 2026-10-26
---
# Plan — Pilot release: accounts and access plans, saved work, AI spend, Taller essentials, English, modules and chat

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
| M1 — Accounts, access plans and Taller essentials | 2026-11-01 | yes | — |
| M2 — Saved work, spend per user and the chat tools | 2026-11-07 | yes | — |
| M3 — English / Spanish | 2026-11-09 | no (cut 1) | 2026-11-09: only SP-8 (Taller 3D and navigation) ships |
| M4 — Editable modules and chat → 3D | 2026-11-12 | no (cuts 2 and 3) | 2026-11-11 modules out; 2026-11-12 chat beyond split and reliability out |
| M5 — Pilot release | 2026-11-16 | yes | — |

**Dependencies.** SP-1 (accounts) → SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. SP-4 (project identity) → SP-6 and SP-12.
SP-6 (spend tagging) → SP-7. SP-8 (language mechanism) → SP-9, SP-10. SP-7 (chat tools, decorations explorer) →
SP-10, SP-12. SP-3 and SP-11 depend on nothing. SP-13 consumes every shipped subplan.

**Fit, said plainly.** Rough size: about 70 tasks for the whole SPEC, about 45 for the never-cut part (SP-1 to SP-7 and
SP-13). Agent time is not the limit; waits are: retries, usage limits and the owner's per-subplan test (under 24 h,
D-131). It fits only if the scheduler runs two or more subplans at once and retries stay low. If M1 slips past
2026-11-03, the cut dates above apply as agreed; never-cut work is never traded for language, modules or chat→3D.

**Security.** SP-1 (identity, sessions, permissions, server-side enforcement, local flag, first administrator) is its
own subplan with its own audit; SP-4 audits that a usuario can only reach their own projects.

Out of this plan: 3D space, Illustrator/vector export, AI spend caps (D-072).

### M1 — Accounts, access plans and Taller essentials
Real people sign in with their own invited account and each one reaches exactly what their role or access plan allows; the shared APP_PASSWORD no longer opens the app; tables, Backing and the Blender file work in the Taller.

- **SP-1 — Accounts, sessions and server-side permissions**: Invited accounts with hashed passwords and revocable server sessions replace the shared APP_PASSWORD; every page and API of the pilot checks the permission it needs on the server; roles and the three access plans are sets of permissions; the local no-restrictions flag cannot be enabled in production; the first administrator is created by a one-off command. Covers R1, R2, R3, R16.
- **SP-2 — Sign-in, invitation and administration screens** (UI: `cuentas-admin@v1`): A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns role or access plan, creates roles by choosing permissions, and deactivates or deletes accounts. Covers R1, R3, R16.
- **SP-3 — Taller essentials: rectangular tables, Backing and Blender export** (UI: `taller-esenciales@v1`): A user adds and edits a rectangular table with its size and chairs and the shopping list reflects it; the catalogue and the Taller show one Backing category with every existing party prop; the exported GLB opens in Blender with the same layout, sizes in metres and colours. Covers R9, R10, R11.

### M2 — Saved work, spend per user and the chat tools
Each signed-in user saves and reopens projects and decorations from any browser, every paid AI call is attributed to a user and a session, and the assisted chat is three separate tools gated by access plan.

- **SP-4 — Saved projects** (UI: `proyectos@v1`): A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Covers R6, R7.
- **SP-5 — Saved decorations** (UI: `decoraciones@v1`): A user saves a selection or composition from the scene with a name to their personal library on the server and places it in any of their projects; items already in the browser's own library are imported. Covers R8.
- **SP-6 — AI spend per user and session** (UI: `gasto-ia@v1`): Every paid AI call (Next and ai-api) is stored with user, sign-in session, work item (project or conversation), tool and kind (text or image); employees and administrators see totals grouped by project or conversation, filtered by user and kind; a usuario cannot open the view. Covers R4, R5.
- **SP-7 — Assisted chat as three tools and the decorations explorer** (UI: `herramientas-chat@v1`): The assisted chat becomes a balloon counter, a cost calculator and the normal chat, each with its own prompts and spend measured separately and never inventing counts or prices; a ready-made decorations explorer lists existing 3D decorations; each tool is reachable only with its access plan. Covers R13, R16.

### M3 — English / Spanish
The interface follows the browser language on the first visit and the account's choice afterwards; the Taller 3D and navigation are fully in English first, then product texts, the remaining screens and the AI replies.

- **SP-8 — Language switch, Taller 3D and navigation in English** (UI: `idioma-taller@v1`): A language mechanism with first-visit detection, a switch remembered per account, and every string of the Taller 3D and the navigation in both languages. Covers R12.
- **SP-9 — Product and decoration texts in English** (UI: `textos-producto@v1`): English names and descriptions for every product and decoration are generated once from the Spanish source, stored, shown when the language is English with the Spanish text as fallback, and correctable by an administrator. Covers R12.
- **SP-10 — Remaining screens and AI replies in English** (UI: `idioma-resto@v1`): The chat tools, catalogue, administration, spend and statistics screens are fully in English, and the scene AI and the chat tools reply in the user's language. Covers R12.

### M4 — Editable modules and chat → 3D
Users edit modules and quartets beyond colours, and the normal chat recommends ready-made 3D decorations that open in the workshop.

- **SP-11 — Editable modules and quartets** (UI: `modulos-editables@v1`): A user edits a module or quartet in the scene beyond its colours (the exact edits are settled with the owner in this subplan) and the counts and shopping list update. Covers R15.
- **SP-12 — Normal chat recommends ready-made 3D decorations** (UI: `chat-a-3d@v1`): In two or three messages the normal chat defines the need and recommends existing 3D decorations that open in the Taller 3D as a new project, using the real catalogue and engine. Covers R13.

### M5 — Pilot release
The pilot runs in production with real accounts: the first administrator exists, every shipped subplan is published, a production smoke passes and anything cut is listed.

- **SP-13 — Pilot release in production**: Every approved subplan is published to production with its migrations, the first administrator is created, an end-to-end flow (invite → activate → save project and decoration → spend appears → export GLB) passes against production, and the cut list is recorded. Covers R14.
