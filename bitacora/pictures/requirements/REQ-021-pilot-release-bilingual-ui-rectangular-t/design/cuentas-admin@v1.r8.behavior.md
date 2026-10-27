# Shared behavioural requirements

{
  "id": "SP-2",
  "title": "Sign-in, invitation and administration screens",
  "outcome": "A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns role or access plan, creates roles by choosing permissions, and deactivates or deletes accounts.",
  "covers": [
    "R1",
    "R3",
    "R16"
  ],
  "criteria": [
    "Generating a new invitation or reset link for an account invalidates every older unused link of the same kind for that account, and a custom role with no permission is refused with ROL_SIN_PERMISOS.",
    "Deleting an account that owns any row of a table registered as account work is refused with CUENTA_CON_TRABAJO and changes nothing, while deleting an account without saved work removes it and keeps its AI spend rows without personal data.",
    "On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them.",
    "Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one.",
    "When the notice version changes, a signed-in person must accept the new version before any other page opens.",
    "Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one.",
    "An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message.",
    "An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted.",
    "An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the five system roles read-only with their permissions, and cannot delete a role that still has accounts.",
    "The account and role administration APIs refuse anyone without the users or roles permission with 403 and accept only same-origin requests with validated bodies.",
    "The data notice exists in Spanish and English with a version number, its bracketed placeholders are still marked for legal review, and accepting stores the version and date on the account.",
    "On a production build against the REQ-021 test database, an administrator invites a Plan 2 person through the screens, the person activates the link in a separate browser, accepts the notice, signs in and reaches the chat and the costs tool but not the Taller 3D, and after the administrator moves them to Plan 3 their next request opens the Taller.",
    "The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger.",
    "An independent audit of SP-2 records every confirmed defect with the task that must redo it in the SP-2 findings ledger, and the ledger has no open critical or high finding."
  ],
  "ui": {
    "contract": "cuentas-admin",
    "version": 1,
    "design_task": "T2.1",
    "visual_review_task": "T2.7"
  },
  "ref": "cuentas-admin@v1",
  "tasks": [
    {
      "id": "T2.1",
      "milestone_id": "M1",
      "title": "Copy the owner-approved cuentas-admin@v1 contract into the repository",
      "objective": "The repository holds the exact owner-approved visual contract for the sign-in, activation, account and administration screens before any of them is built.",
      "repository": "pictures",
      "after": [
        "T1.4"
      ],
      "complexity": "low",
      "scope": "isolated_fix",
      "estimated_minutes": 10,
      "risk": "low",
      "coupling": "medium",
      "confidence": "high",
      "estimate_rationale": "Agent estimate in minutes: 10 to copy the pinned file and check its hash; the design itself is done during planning.",
      "classification_evidence": {
        "complexity": {
          "justification": "Copying an already approved file byte for byte needs no design decisions.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "scope": {
          "justification": "One markdown file added under design/contracts.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.4"
          ]
        },
        "duration": {
          "justification": "Ten minutes to copy and compare the hash.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind design -> status unknown, no comparable samples",
            "task:T2.5"
          ]
        },
        "risk": {
          "justification": "A wrong copy only blocks UI tasks through the hash gate, which is easy to redo.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "coupling": {
          "justification": "Every UI task of SP-2 reads this contract, so they wait for it.",
          "evidence": [
            "task:T2.3",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "The flow copies the plan-pinned draft, a fully known step with no open questions.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.6"
          ]
        }
      },
      "expected_paths": [
        "design/contracts/cuentas-admin@v1.md"
      ],
      "shared_resources": [
        "design:cuentas-admin@v1"
      ],
      "acceptance_criteria": [
        "The owner-approved cuentas-admin@v1 contract is copied byte for byte into design/contracts/cuentas-admin@v1.md."
      ],
      "verification": [
        {
          "type": "command",
          "value": "test -s design/contracts/cuentas-admin@v1.md",
          "purpose": "The owner-approved cuentas-admin@v1 contract is copied byte for byte into design/contracts/cuentas-admin@v1.md.",
          "category": "static"
        }
      ],
      "covers": [
        "R1",
        "R3",
        "R16"
      ],
      "kind": "design",
      "subplan_id": "SP-2",
      "ui": false
    },
    {
      "id": "T2.2",
      "milestone_id": "M1",
      "title": "Account APIs: activation, reset, notice acceptance, own password and the administration of accounts and roles",
      "objective": "Server routes expose activation, reset, notice acceptance and own-password change to their holders, and account and role administration only to administrators, all on top of the SP-1 service.",
      "repository": "pictures",
      "after": [
        "T1.4"
      ],
      "complexity": "medium",
      "scope": "large_change",
      "estimated_minutes": 120,
      "risk": "high",
      "coupling": "high",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 15 notice module + 35 holder APIs + 40 admin APIs + 30 tests = 120.",
      "classification_evidence": {
        "complexity": {
          "justification": "Thin routes over the SP-1 service, but tokens, same-origin checks and permission splits must be exact.",
          "evidence": [
            "file:src/lib/auth/request.ts",
            "task:T1.3"
          ]
        },
        "scope": {
          "justification": "Eight route files, the notice module, map entries and one test file.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "task:T1.2"
          ]
        },
        "duration": {
          "justification": "Fifteen notice, thirty-five holder APIs, forty admin APIs and thirty tests make one hundred twenty minutes.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "task:T1.3"
          ]
        },
        "risk": {
          "justification": "These routes create administrators and set passwords; a gap gives control of the pilot to anyone.",
          "evidence": [
            "spec:SPEC.md#constraints",
            "task:T1.4"
          ]
        },
        "coupling": {
          "justification": "Consumes contract:account-service and contract:session-guard from SP-1 and feeds every screen of SP-2.",
          "evidence": [
            "task:T1.4",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "Existing route patterns were read and the service API is fixed by T1.3, though zod schemas are new.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "task:T1.3"
          ]
        }
      },
      "expected_paths": [
        "src/lib/cuentas/aviso-datos.ts",
        "src/app/api/cuentas/activar/route.ts",
        "src/app/api/cuentas/restablecer/route.ts",
        "src/app/api/cuentas/aviso/route.ts",
        "src/app/api/cuentas/mi-cuenta/route.ts",
        "src/app/api/admin/cuentas/route.ts",
        "src/app/api/admin/cuentas/[id]/route.ts",
        "src/app/api/admin/roles/route.ts",
        "src/app/api/admin/roles/[id]/route.ts",
        "src/lib/cuentas/dependientes.ts",
        "src/lib/cuentas/regenerar-enlace.ts",
        "src/lib/cuentas/mapa-rutas.ts",
        "scripts/test/test-cuentas-api.ts"
      ],
      "shared_resources": [
        "package.json scripts",
        "contract:account-service",
        "contract:session-guard"
      ],
      "acceptance_criteria": [
        "The activation, reset and notice-acceptance APIs accept only a valid unused token or a signed-in session, validate every body, answer a used or expired link with LINK_INVALIDO without saying which, and a successful activation opens a session at once.",
        "The account and role administration APIs refuse anyone without the users or roles permission with 403 and accept only same-origin requests with validated bodies.",
        "Generating a new invitation or reset link for an account invalidates every older unused link of the same kind for that account, and a custom role with no permission is refused with ROL_SIN_PERMISOS.",
        "Changing one's own password requires the current password, ends every session of that account and signs the requesting browser in again with a new session.",
        "The data notice exists in Spanish and English with a version number, its bracketed placeholders are still marked for legal review, and accepting stores the version and date on the account.",
        "Deleting an account that owns any row of a table registered as account work is refused with CUENTA_CON_TRABAJO and changes nothing, while deleting an account without saved work removes it and keeps its AI spend rows without personal data."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=enlaces",
          "purpose": "The activation, reset and notice-acceptance APIs accept only a valid unused token or a signed-in session, validate every body, answer a used or expired link with LINK_INVALIDO without saying which, and a successful activation opens a session at once.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=admin",
          "purpose": "The account and role administration APIs refuse anyone without the users or roles permission with 403 and accept only same-origin requests with validated bodies.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=regenerar",
          "purpose": "Generating a new invitation or reset link for an account invalidates every older unused link of the same kind for that account, and a custom role with no permission is refused with ROL_SIN_PERMISOS.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=mi-cuenta",
          "purpose": "Changing one's own password requires the current password, ends every session of that account and signs the requesting browser in again with a new session.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=aviso",
          "purpose": "The data notice exists in Spanish and English with a version number, its bracketed placeholders are still marked for legal review, and accepting stores the version and date on the account.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=borrar",
          "purpose": "Deleting an account that owns any row of a table registered as account work is refused with CUENTA_CON_TRABAJO and changes nothing, while deleting an account without saved work removes it and keeps its AI spend rows without personal data.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R1",
        "R3",
        "R16"
      ],
      "kind": "implement",
      "subplan_id": "SP-2",
      "ui": false
    },
    {
      "id": "T2.3",
      "milestone_id": "M1",
      "title": "Sign-in, invitation activation, password reset and notice re-acceptance screens",
      "objective": "A person signs in, activates an invitation accepting the data notice, resets a password from an administrator's link and re-accepts a new notice version, with the states the contract defines.",
      "repository": "pictures",
      "after": [
        "T2.1",
        "T2.2"
      ],
      "complexity": "medium",
      "scope": "full_feature",
      "estimated_minutes": 150,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 30 sign-in + 45 activation with notice + 20 reset + 20 re-acceptance redirect + 35 render tests = 150.",
      "classification_evidence": {
        "complexity": {
          "justification": "Four screens with error, locked, expired and loading states and a proxy redirect for re-acceptance.",
          "evidence": [
            "file:src/app/login/page.tsx",
            "file:src/proxy.ts"
          ]
        },
        "scope": {
          "justification": "Four pages, three shared components and one proxy rule, verifiable end to end.",
          "evidence": [
            "file:src/app/login/page.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Thirty, forty-five, twenty, twenty and thirty-five minutes add to one hundred fifty.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/app/login/page.tsx"
          ]
        },
        "risk": {
          "justification": "A broken sign-in or activation locks every pilot user out on day one.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.6"
          ]
        },
        "coupling": {
          "justification": "Edits src/proxy.ts after T1.4 and shares contract:session-guard with the other UI tasks.",
          "evidence": [
            "task:T1.4",
            "task:T2.4"
          ]
        },
        "confidence": {
          "justification": "The current login page was read; the contract states are not drafted yet.",
          "evidence": [
            "file:src/app/login/page.tsx",
            "assumption:the contract keeps the current centred card layout"
          ]
        }
      },
      "expected_paths": [
        "src/app/login/page.tsx",
        "src/app/login/LoginForm.tsx",
        "src/app/activar/[token]/page.tsx",
        "src/app/restablecer/[token]/page.tsx",
        "src/app/aviso-datos/page.tsx",
        "src/components/cuentas/FormularioContrasena.tsx",
        "src/components/cuentas/AvisoDatos.tsx",
        "src/components/cuentas/textos-acceso.ts",
        "src/proxy.ts",
        "scripts/test/test-ui-acceso.ts"
      ],
      "shared_resources": [
        "package.json scripts",
        "contract:session-guard"
      ],
      "acceptance_criteria": [
        "On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them.",
        "Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one.",
        "Opening a reset link lets the person set a new password and then sign in; a used or expired link shows the same message as an invalid invitation.",
        "When the notice version changes, a signed-in person must accept the new version before any other page opens."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo ingreso",
          "purpose": "On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo activacion",
          "purpose": "Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo restablecer",
          "purpose": "Opening a reset link lets the person set a new password and then sign in; a used or expired link shows the same message as an invalid invitation.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo aviso",
          "purpose": "When the notice version changes, a signed-in person must accept the new version before any other page opens.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R1"
      ],
      "kind": "implement",
      "subplan_id": "SP-2",
      "ui": true
    },
    {
      "id": "T2.4",
      "milestone_id": "M1",
      "title": "Account menu on every signed-in page and the Mi cuenta page",
      "objective": "Every signed-in person sees who they are and their role, signs out, and changes their own password from Mi cuenta.",
      "repository": "pictures",
      "after": [
        "T2.1",
        "T2.2"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 75,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 30 menu in the root layout + 25 Mi cuenta + 20 tests = 75.",
      "classification_evidence": {
        "complexity": {
          "justification": "The app has no shared navigation, so the menu must fit pages as different as the chat and the Taller.",
          "evidence": [
            "file:src/app/layout.tsx",
            "file:src/app/page.tsx"
          ]
        },
        "scope": {
          "justification": "One menu component in the root layout, one page and a test.",
          "evidence": [
            "file:src/app/layout.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Thirty for the menu, twenty-five for the page and twenty for tests, seventy-five minutes.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/app/layout.tsx"
          ]
        },
        "risk": {
          "justification": "A layout change can overlap the Taller toolbar or the chat composer on phones.",
          "evidence": [
            "file:src/app/layout.tsx",
            "spec:SPEC.md#ui--design-contract-optional"
          ]
        },
        "coupling": {
          "justification": "Shares the root layout with later language work and reads contract:session-guard.",
          "evidence": [
            "task:T1.4",
            "task:T2.3"
          ]
        },
        "confidence": {
          "justification": "The root layout was read; where the contract places the menu is not drafted yet.",
          "evidence": [
            "file:src/app/layout.tsx",
            "assumption:the contract places the menu as a corner control like the theme switch"
          ]
        }
      },
      "expected_paths": [
        "src/components/cuentas/MenuCuenta.tsx",
        "src/app/layout.tsx",
        "src/app/cuenta/page.tsx",
        "src/components/cuentas/textos-cuenta.ts",
        "scripts/test/test-ui-mi-cuenta.ts"
      ],
      "shared_resources": [
        "package.json scripts",
        "contract:session-guard"
      ],
      "acceptance_criteria": [
        "Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-mi-cuenta",
          "purpose": "Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one.",
          "category": "functional",
          "created_by": "T2.4",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R1"
      ],
      "kind": "implement",
      "subplan_id": "SP-2",
      "ui": true
    },
    {
      "id": "T2.5",
      "milestone_id": "M1",
      "title": "Administration screens: accounts list, invitations, account actions and the role editor",
      "objective": "An administrator manages every account and custom role from two screens that show exactly what each action will do and why one is refused.",
      "repository": "pictures",
      "after": [
        "T2.1",
        "T2.2"
      ],
      "complexity": "medium",
      "scope": "full_feature",
      "estimated_minutes": 180,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 60 accounts list with search and filters + 35 invite dialog + 35 account actions + 30 role editor + 20 tests = 180.",
      "classification_evidence": {
        "complexity": {
          "justification": "Several dialogs with confirmation, refusal reasons and a link shown once need careful state handling.",
          "evidence": [
            "file:src/components/admin/AdminTabs.tsx",
            "task:T2.2"
          ]
        },
        "scope": {
          "justification": "Two pages and five components with their test, a full end-to-end feature.",
          "evidence": [
            "file:src/components/admin/AdminTabs.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Sixty, thirty-five, thirty-five, thirty and twenty minutes make one hundred eighty.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/components/admin/AdminTabs.tsx"
          ]
        },
        "risk": {
          "justification": "A wrong action button deletes a real user's account or changes their access.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.2"
          ]
        },
        "coupling": {
          "justification": "Reads contract:permission-map for the permission checkboxes and calls the T2.2 APIs.",
          "evidence": [
            "task:T1.2",
            "task:T2.2"
          ]
        },
        "confidence": {
          "justification": "The existing admin tabs were read; list density and dialogs depend on the contract.",
          "evidence": [
            "file:src/components/admin/AdminTabs.tsx",
            "assumption:the contract reuses the existing tabs and dialog components"
          ]
        }
      },
      "expected_paths": [
        "src/app/admin/cuentas/page.tsx",
        "src/app/admin/roles/page.tsx",
        "src/components/admin/cuentas/ListaCuentas.tsx",
        "src/components/admin/cuentas/DialogoInvitar.tsx",
        "src/components/admin/cuentas/AccionesCuenta.tsx",
        "src/components/admin/cuentas/EditorRol.tsx",
        "src/components/admin/cuentas/textos-admin-cuentas.ts",
        "src/components/admin/AdminTabs.tsx",
        "scripts/test/test-ui-admin-cuentas.ts"
      ],
      "shared_resources": [
        "package.json scripts",
        "contract:permission-map"
      ],
      "acceptance_criteria": [
        "An administrator sees all accounts with name, email, company, role, state and last access, searches by name or email and filters by role and state.",
        "An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message.",
        "An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted.",
        "An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the five system roles read-only with their permissions, and cannot delete a role that still has accounts."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo lista",
          "purpose": "An administrator sees all accounts with name, email, company, role, state and last access, searches by name or email and filters by role and state.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo invitar",
          "purpose": "An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo acciones",
          "purpose": "An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo roles",
          "purpose": "An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the five system roles read-only with their permissions, and cannot delete a role that still has accounts.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R1",
        "R3",
        "R16"
      ],
      "kind": "implement",
      "subplan_id": "SP-2",
      "ui": true
    },
    {
      "id": "T2.6",
      "milestone_id": "M1",
      "title": "Browser end-to-end: invite, activate, sign in and change plan on a production build",
      "objective": "Two real browsers against next start prove the full invitation-to-access flow and that a plan change takes effect on the next request.",
      "repository": "pictures",
      "after": [
        "T2.3",
        "T2.4",
        "T2.5"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 90,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 15 build + 50 two-context Playwright flow + 25 evidence and teardown = 90.",
      "classification_evidence": {
        "complexity": {
          "justification": "Two browser contexts, a copied link and a role change between requests need careful sequencing.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "task:T2.5"
          ]
        },
        "scope": {
          "justification": "One Playwright script and its evidence file.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "task:T2.3"
          ]
        },
        "duration": {
          "justification": "Fifteen build, fifty flow and twenty-five evidence add to ninety minutes.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind test -> status unknown, no comparable samples",
            "file:package.json"
          ]
        },
        "risk": {
          "justification": "Last barrier before the audit for the screens real users meet first.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.8"
          ]
        },
        "coupling": {
          "justification": "Exercises every SP-2 task and the SP-1 contracts together.",
          "evidence": [
            "task:T2.3",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "Playwright is already a dependency and the smoke shows its use; build time is not measured.",
          "evidence": [
            "file:package.json",
            "assumption:next build finishes within the sandbox time limit"
          ]
        }
      },
      "expected_paths": [
        "scripts/test/test-integracion-cuentas-ui.ts",
        ".evidence/REQ-021/SP-2.integration.json"
      ],
      "shared_resources": [
        "package.json scripts"
      ],
      "acceptance_criteria": [
        "On a production build against the REQ-021 test database, an administrator invites a Plan 2 person through the screens, the person activates the link in a separate browser, accepts the notice, signs in and reaches the chat and the costs tool but not the Taller 3D, and after the administrator moves them to Plan 3 their next request opens the Taller."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-integracion-ui",
          "purpose": "On a production build against the REQ-021 test database, an administrator invites a Plan 2 person through the screens, the person activates the link in a separate browser, accepts the notice, signs in and reaches the chat and the costs tool but not the Taller 3D, and after the administrator moves them to Plan 3 their next request opens the Taller.",
          "category": "integration",
          "created_by": "T2.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R1",
        "R3",
        "R16"
      ],
      "kind": "test",
      "subplan_id": "SP-2"
    },
    {
      "id": "T2.7",
      "milestone_id": "M1",
      "title": "SP-2 visual review against the cuentas-admin@v1 contract",
      "objective": "A fresh reviewer compares the rendered screens with the approved contract at three widths and records every mismatch with the task to redo.",
      "repository": "pictures",
      "after": [
        "T2.6"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 60,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 40 screenshots and comparison of five screens at three widths + 20 ledger = 60.",
      "classification_evidence": {
        "complexity": {
          "justification": "Comparing rendered states with a written contract needs judgement but no new design.",
          "evidence": [
            "task:T2.1",
            "task:T2.6"
          ]
        },
        "scope": {
          "justification": "Writes only a report and its ledger.",
          "evidence": [
            "task:T2.6",
            "spec:SPEC.md#ui--design-contract-optional"
          ]
        },
        "duration": {
          "justification": "Forty for screenshots and comparison and twenty for the ledger, sixty minutes.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind audit -> status unknown, no comparable samples",
            "task:T2.3"
          ]
        },
        "risk": {
          "justification": "A missed mismatch reaches pilot users as a confusing first screen.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "coupling": {
          "justification": "Its ledger:SP-2-visual can send T2.3 to T2.5 back.",
          "evidence": [
            "task:T2.4",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "The screens and contract are bounded, so the estimate rests on known tasks.",
          "evidence": [
            "task:T2.6",
            "task:T2.1"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-2.visual.md",
        ".evidence/REQ-021/SP-2.visual.findings.json"
      ],
      "shared_resources": [
        "ledger:SP-2-visual"
      ],
      "acceptance_criteria": [
        "The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json",
          "purpose": "The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger.",
          "category": "static",
          "created_by": "T2.7"
        }
      ],
      "covers": [
        "R1",
        "R3"
      ],
      "kind": "audit",
      "subplan_id": "SP-2"
    },
    {
      "id": "T2.8",
      "milestone_id": "M1",
      "title": "SP-2 audit: account screens, administration APIs and the data notice",
      "objective": "An independent read-only review confirms SP-2 against R1, R3 and R16 and records each confirmed defect with the task to redo in a blocking findings ledger.",
      "repository": "pictures",
      "after": [
        "T2.7"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 75,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Agent estimate in minutes: 30 admin API permissions and tokens + 25 screens against acceptance + 20 ledger = 75.",
      "classification_evidence": {
        "complexity": {
          "justification": "Checking that every admin action is permission-checked and that links never leak needs security reading.",
          "evidence": [
            "task:T2.2",
            "spec:SPEC.md#constraints"
          ]
        },
        "scope": {
          "justification": "The audit writes only its report and ledger.",
          "evidence": [
            "task:T2.7",
            "spec:SPEC.md#requirements"
          ]
        },
        "duration": {
          "justification": "Thirty, twenty-five and twenty minutes make seventy-five.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind audit -> status unknown, no comparable samples",
            "task:T2.2"
          ]
        },
        "risk": {
          "justification": "A missed defect lets a non-administrator manage accounts of real users.",
          "evidence": [
            "spec:SPEC.md#constraints",
            "task:T2.2"
          ]
        },
        "coupling": {
          "justification": "Its ledger:SP-2 can send T2.2 to T2.5 back.",
          "evidence": [
            "task:T2.2",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "Bounded by one API task and three screens with tests.",
          "evidence": [
            "task:T2.6",
            "task:T2.7"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-2.audit.md",
        ".evidence/REQ-021/SP-2.findings.json"
      ],
      "shared_resources": [
        "ledger:SP-2"
      ],
      "acceptance_criteria": [
        "An independent audit of SP-2 records every confirmed defect with the task that must redo it in the SP-2 findings ledger, and the ledger has no open critical or high finding."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json",
          "purpose": "An independent audit of SP-2 records every confirmed defect with the task that must redo it in the SP-2 findings ledger, and the ledger has no open critical or high finding.",
          "category": "static",
          "created_by": "T2.8"
        }
      ],
      "covers": [
        "R1",
        "R3",
        "R16"
      ],
      "kind": "audit",
      "subplan_id": "SP-2"
    }
  ],
  "digest": "abde9480c2f8d545"
}

Read SPEC.md and PLAN.md for the complete behaviour. Do not invent flows.
