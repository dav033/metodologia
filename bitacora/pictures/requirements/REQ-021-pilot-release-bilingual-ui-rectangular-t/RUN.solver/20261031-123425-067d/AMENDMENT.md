# Proposed SP-2 amendment — owner confirmation required

Status: proposal only; no approval, freeze, join or product implementation. Source: P-209 rejection of SP-2 v2, reproduced in evidence/owner-rejected/SP-2-v2.md.

## Exact requested delta

| Frozen contract | Proposed owner-requested revision |
|---|---|
| T2.4: account menu shows name and role | Show the actual person's name (explicit name label in Mi cuenta; email fallback only when no name exists). For accounts assigned a catalogue plan, show Plan and its catalogue name; keep truthful Administrator/Internal employee/custom-role identity for non-plan roles. No permission changes. |
| Native disclosure has no specified outside/Escape closure regression | Close by trigger toggle, outside pointer and Escape, with accessible keyboard behavior and predictable focus; browser regression at 390px and 1280px. |
| cuentas-admin@v1 F7/V6 requires ordinary profile notice version/date | Remove accepted-notice metadata from the ordinary account presentation; keep versioned consent capture, reacceptance gate and storage untouched. |
| Existing account/password arrangement | Complete visual redesign of /cuenta and password section in a new immutable cuentas-admin contract version, prepared by the normal Planner/Designer path and approved by the owner before UI implementation. |

## Required work sequence

1. Planner prepares the SP-2-only contract/plan delta and revised UI deliverable for owner confirmation. This document is a reviewable amendment brief, not a substitute for an approved mockup.
2. Owner confirms the new SP-2 contract/subplan. Other subplans need no blanket reconfirmation unless the impact review proves their own contracts change.
3. The run implements the amended UI and real dismissal/name regressions before existing T2.7 visual review and T2.8 audit. Existing checks/gates remain; no fake ui:false repair or self-approval.
4. Compose and reverify affected consumers under the existing gate mechanism; publish a new SP-2 version as to_test. P-209 closes only after owner approval of that later version.

## Invariants

No self-editing of plan/role/profile added. No permission or session-policy changes. Preserve current-password verification, password validation and mismatch/errors, renewal of the requesting browser and invalidation of other sessions, sign-out, ES/EN, permission-scoped administration links, versioned notice consent/enforcement/storage, all existing acceptance checks and composition gates. Do not replace role labels with invented paid plans for staff/custom roles. Validate a named account as well as the test recipe's nameless account; email fallback does not prove a missing-name production defect.

## Owner question

¿Confirmas el cambio de contrato propuesto aquí para SP-2: nombre visible, «Plan» cuando corresponda, identidad correcta de administradores/empleados/roles personalizados, sin el aviso aceptado en el perfil, cierre del menú al pulsar fuera o Escape y rediseño de Mi cuenta y contraseña? Con tu confirmación se tramita la nueva versión visual y su aprobación antes de implementarla; si rechazas el cambio, el Planner conserva el contrato actual y separa la reparación del cierre del menú.

## Why confirmation is required

The solver contract, section “the plan”, permits only dependency-only implement/test additions with no existing criterion, check, path, gate or subplan-definition changes under D-241. It explicitly requires the owner for every other plan change. The full requested redesign changes cuentas-admin@v1 F7/V6 and T2.4, so only SP-2 requires reconfirmation; this cannot be classified as bounded repair.
