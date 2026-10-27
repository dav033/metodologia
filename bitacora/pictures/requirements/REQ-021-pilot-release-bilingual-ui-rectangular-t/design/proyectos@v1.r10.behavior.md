# Shared behavioural requirements

{
  "id": "SP-4",
  "title": "Saved projects",
  "outcome": "A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.",
  "covers": [
    "R6",
    "R7"
  ],
  "criteria": [
    "The repository contract is byte-identical to the owner-approved proyectos@v1 artifact.",
    "A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data.",
    "Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes.",
    "Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document.",
    "Project-name search and authorized owner filters apply to the whole server collection before pagination; filter-bound cursors, literal name matching and per-account authorization prevent skipped later-page matches and metadata disclosure.",
    "The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response.",
    "Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar.",
    "The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results.",
    "A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically.",
    "The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import.",
    "The browser harness seeds more than fifty projects and verifies a matching project beyond the first page, authorized owner filtering, next-page retry and stale search-response rejection without leaking foreign metadata.",
    "A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.",
    "A real production build passes persistence across fresh browser contexts, per-account denial, staff read/copy, competing-save conflict, import retry and account-switch isolation checks on the REQ-021 database.",
    "Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified.",
    "An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation.",
    "Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race."
  ],
  "ui": {
    "contract": "proyectos",
    "version": 1,
    "design_task": "T4.1",
    "visual_review_task": "T4.8"
  },
  "ref": "proyectos@v1",
  "tasks": [
    {
      "id": "T4.1",
      "milestone_id": "M2",
      "title": "Copy the approved saved-projects design contract",
      "objective": "The repository contract is byte-identical to the owner-approved proyectos@v1 artifact.",
      "repository": "pictures",
      "after": [
        "T92"
      ],
      "complexity": "low",
      "scope": "small_change",
      "estimated_minutes": 20,
      "risk": "low",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 20 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Copy the approved saved-projects design contract: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "scope": {
          "justification": "Copy the approved saved-projects design contract: Changes are limited to design/contracts/proyectos@v1.md and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "duration": {
          "justification": "Copy the approved saved-projects design contract: Uncalibrated agent estimate: 6 minutes inspection, 6 implementation or execution, 8 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "risk": {
          "justification": "Copy the approved saved-projects design contract: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "coupling": {
          "justification": "Copy the approved saved-projects design contract: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "confidence": {
          "justification": "Copy the approved saved-projects design contract: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T92"
          ]
        }
      },
      "expected_paths": [
        "design/contracts/proyectos@v1.md"
      ],
      "shared_resources": [
        "design:T4.1"
      ],
      "acceptance_criteria": [
        "The repository contract is byte-identical to the owner-approved proyectos@v1 artifact."
      ],
      "verification": [
        {
          "type": "command",
          "value": "cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md",
          "purpose": "The repository contract is byte-identical to the owner-approved proyectos@v1 artifact.",
          "category": "static",
          "created_by": "T4.1"
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "design",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.2",
      "milestone_id": "M2",
      "title": "Implement versioned project storage and scene validation",
      "objective": "A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data.",
      "repository": "pictures",
      "after": [
        "T4.1"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 170,
      "risk": "high",
      "coupling": "high",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 170 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement versioned project storage and scene validation: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "scope": {
          "justification": "Implement versioned project storage and scene validation: Changes are limited to scripts/migrations/038_proyectos.sql, src/lib/proyectos/contrato.ts and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "duration": {
          "justification": "Implement versioned project storage and scene validation: Uncalibrated agent estimate: 56 minutes inspection, 56 implementation or execution, 58 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "risk": {
          "justification": "Implement versioned project storage and scene validation: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "coupling": {
          "justification": "Implement versioned project storage and scene validation: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T1.8",
            "task:T2.2",
            "task:T4.1"
          ]
        },
        "confidence": {
          "justification": "Implement versioned project storage and scene validation: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.1"
          ]
        }
      },
      "expected_paths": [
        "scripts/migrations/038_proyectos.sql",
        "src/lib/proyectos/contrato.ts",
        "src/lib/proyectos/servicio.ts",
        "src/lib/proyectos/repositorio.ts",
        "src/lib/proyectos/validar-escena.ts",
        "src/lib/cuentas/dependientes.ts",
        "scripts/test/test-proyectos-servicio.ts"
      ],
      "shared_resources": [
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data.",
        "Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts",
          "purpose": "A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data.",
          "category": "functional",
          "created_by": "T4.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts",
          "purpose": "Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes.",
          "category": "functional",
          "created_by": "T4.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "implement",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.3",
      "milestone_id": "M2",
      "title": "Implement project APIs with per-resource authorization",
      "objective": "Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document.",
      "repository": "pictures",
      "after": [
        "T4.2"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 100,
      "risk": "high",
      "coupling": "high",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 100 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement project APIs with per-resource authorization: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "scope": {
          "justification": "Implement project APIs with per-resource authorization: Changes are limited to src/app/api/proyectos/route.ts, src/app/api/proyectos/[id]/route.ts and the listed focused verification artifacts.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "duration": {
          "justification": "Implement project APIs with per-resource authorization: Uncalibrated agent estimate: 33 minutes inspection, 33 implementation or execution, 34 focused verification and evidence.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "risk": {
          "justification": "Implement project APIs with per-resource authorization: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "coupling": {
          "justification": "Implement project APIs with per-resource authorization: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2",
            "task:T1.6",
            "task:T4.2"
          ]
        },
        "confidence": {
          "justification": "Implement project APIs with per-resource authorization: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.2"
          ]
        }
      },
      "expected_paths": [
        "src/app/api/proyectos/route.ts",
        "src/app/api/proyectos/[id]/route.ts",
        "src/lib/proyectos/http.ts",
        "src/lib/cuentas/mapa-rutas.ts",
        "scripts/test/test-proyectos-api.ts",
        "package.json",
        "scripts/test/test-checkpoint-proyectos.ts"
      ],
      "shared_resources": [
        "package.json scripts",
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document.",
        "Project-name search and authorized owner filters apply to the whole server collection before pagination; filter-bound cursors, literal name matching and per-account authorization prevent skipped later-page matches and metadata disclosure."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-api",
          "purpose": "Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document.",
          "category": "functional",
          "created_by": "T4.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-api",
          "purpose": "Project-name search and authorized owner filters apply to the whole server collection before pagination; filter-bound cursors, literal name matching and per-account authorization prevent skipped later-page matches and metadata disclosure.",
          "category": "functional",
          "created_by": "T4.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "implement",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.4",
      "milestone_id": "M2",
      "title": "Implement the project list and conflict-safe Taller saving",
      "objective": "The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response.",
      "repository": "pictures",
      "after": [
        "T4.31"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 180,
      "risk": "high",
      "coupling": "high",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 180 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement the project list and conflict-safe Taller saving: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "scope": {
          "justification": "Implement the project list and conflict-safe Taller saving: Changes are limited to src/app/proyectos/page.tsx, src/components/proyectos/ListaProyectos.tsx and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "duration": {
          "justification": "Implement the project list and conflict-safe Taller saving: Uncalibrated agent estimate: 60 minutes inspection, 60 implementation or execution, 60 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "risk": {
          "justification": "Implement the project list and conflict-safe Taller saving: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "coupling": {
          "justification": "Implement the project list and conflict-safe Taller saving: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.1",
            "task:T4.3",
            "task:T4.31"
          ]
        },
        "confidence": {
          "justification": "Implement the project list and conflict-safe Taller saving: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.31"
          ]
        }
      },
      "expected_paths": [
        "src/app/proyectos/page.tsx",
        "src/components/proyectos/ListaProyectos.tsx",
        "src/components/proyectos/EstadoGuardado.tsx",
        "src/components/proyectos/ConflictoProyecto.tsx",
        "src/components/proyectos/useProyecto.ts",
        "src/components/proyectos/textos-proyectos.ts",
        "src/components/tres-d/Taller3D.tsx",
        "src/app/3d/page.tsx",
        "src/lib/proyectos/borrador-local.ts",
        "scripts/test/test-proyectos-cliente.ts",
        "src/app/proyectos/[id]/page.tsx"
      ],
      "shared_resources": [
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response.",
        "Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar.",
        "The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response.",
          "category": "functional",
          "created_by": "T4.4"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar.",
          "category": "functional",
          "created_by": "T4.4"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results.",
          "category": "functional",
          "created_by": "T4.4"
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "implement",
      "subplan_id": "SP-4",
      "ui": true
    },
    {
      "id": "T4.5",
      "milestone_id": "M2",
      "title": "Implement a lossless and idempotent legacy-scene import",
      "objective": "A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically.",
      "repository": "pictures",
      "after": [
        "T4.4"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 110,
      "risk": "high",
      "coupling": "high",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 110 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement a lossless and idempotent legacy-scene import: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "scope": {
          "justification": "Implement a lossless and idempotent legacy-scene import: Changes are limited to src/lib/proyectos/importar-local.ts, src/components/proyectos/ImportarEscenaLocal.tsx and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "duration": {
          "justification": "Implement a lossless and idempotent legacy-scene import: Uncalibrated agent estimate: 36 minutes inspection, 36 implementation or execution, 38 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "risk": {
          "justification": "Implement a lossless and idempotent legacy-scene import: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "coupling": {
          "justification": "Implement a lossless and idempotent legacy-scene import: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4",
            "task:T4.4"
          ]
        },
        "confidence": {
          "justification": "Implement a lossless and idempotent legacy-scene import: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.4"
          ]
        }
      },
      "expected_paths": [
        "src/lib/proyectos/importar-local.ts",
        "src/components/proyectos/ImportarEscenaLocal.tsx",
        "src/components/tres-d/guardado-escena.ts",
        "src/components/proyectos/useProyecto.ts",
        "scripts/test/test-proyectos-importacion.ts"
      ],
      "shared_resources": [
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-importacion.ts",
          "purpose": "A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically.",
          "category": "functional",
          "created_by": "T4.5"
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "implement",
      "subplan_id": "SP-4",
      "ui": true
    },
    {
      "id": "T4.6",
      "milestone_id": "M2",
      "title": "Implement the multi-browser saved-project integration harness",
      "objective": "The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import.",
      "repository": "pictures",
      "after": [
        "T4.5"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 120,
      "risk": "high",
      "coupling": "high",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 120 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement the multi-browser saved-project integration harness: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "scope": {
          "justification": "Implement the multi-browser saved-project integration harness: Changes are limited to scripts/test/test-integracion-proyectos.ts, scripts/test/test-harness-proyectos.ts and the listed focused verification artifacts.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "duration": {
          "justification": "Implement the multi-browser saved-project integration harness: Uncalibrated agent estimate: 40 minutes inspection, 40 implementation or execution, 40 focused verification and evidence.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "risk": {
          "justification": "Implement the multi-browser saved-project integration harness: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "coupling": {
          "justification": "Implement the multi-browser saved-project integration harness: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5",
            "task:T2.6",
            "task:T4.5"
          ]
        },
        "confidence": {
          "justification": "Implement the multi-browser saved-project integration harness: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.5"
          ]
        }
      },
      "expected_paths": [
        "scripts/test/test-integracion-proyectos.ts",
        "scripts/test/test-harness-proyectos.ts",
        "package.json"
      ],
      "shared_resources": [
        "package.json scripts",
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import.",
        "The browser harness seeds more than fifty projects and verifies a matching project beyond the first page, authorized owner filtering, next-page retry and stale search-response rejection without leaking foreign metadata."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-harness",
          "purpose": "The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import.",
          "category": "functional",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-harness",
          "purpose": "The browser harness seeds more than fifty projects and verifies a matching project beyond the first page, authorized owner filtering, next-page retry and stale search-response rejection without leaking foreign metadata.",
          "category": "functional",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "implement",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.7",
      "milestone_id": "M2",
      "title": "Run the cross-browser project and import integration scenario",
      "objective": "A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.",
      "repository": "pictures",
      "after": [
        "T4.6"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 60,
      "risk": "medium",
      "coupling": "high",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 60 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Run the cross-browser project and import integration scenario: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "scope": {
          "justification": "Run the cross-browser project and import integration scenario: Changes are limited to .evidence/REQ-021/SP-4.integration.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "duration": {
          "justification": "Run the cross-browser project and import integration scenario: Uncalibrated agent estimate: 20 minutes inspection, 20 implementation or execution, 20 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "risk": {
          "justification": "Run the cross-browser project and import integration scenario: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "coupling": {
          "justification": "Run the cross-browser project and import integration scenario: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6",
            "task:T4.6"
          ]
        },
        "confidence": {
          "justification": "Run the cross-browser project and import integration scenario: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.6"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-4.integration.json"
      ],
      "shared_resources": [
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.",
        "A real production build passes persistence across fresh browser contexts, per-account denial, staff read/copy, competing-save conflict, import retry and account-switch isolation checks on the REQ-021 database."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-integracion",
          "purpose": "A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.",
          "category": "integration",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-integracion",
          "purpose": "A real production build passes persistence across fresh browser contexts, per-account denial, staff read/copy, competing-save conflict, import retry and account-switch isolation checks on the REQ-021 database.",
          "category": "integration",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "test",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.8",
      "milestone_id": "M2",
      "title": "Review the rendered project and import interfaces",
      "objective": "Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified.",
      "repository": "pictures",
      "after": [
        "T4.7"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 75,
      "risk": "medium",
      "coupling": "high",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 75 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Review the rendered project and import interfaces: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "scope": {
          "justification": "Review the rendered project and import interfaces: Changes are limited to .evidence/REQ-021/SP-4.visual.md, .evidence/REQ-021/SP-4.visual.findings.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "duration": {
          "justification": "Review the rendered project and import interfaces: Uncalibrated agent estimate: 25 minutes inspection, 25 implementation or execution, 25 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "risk": {
          "justification": "Review the rendered project and import interfaces: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "coupling": {
          "justification": "Review the rendered project and import interfaces: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7",
            "task:T4.7"
          ]
        },
        "confidence": {
          "justification": "Review the rendered project and import interfaces: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.7"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-4.visual.md",
        ".evidence/REQ-021/SP-4.visual.findings.json"
      ],
      "shared_resources": [
        "ledger:T4.8"
      ],
      "acceptance_criteria": [
        "Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json",
          "purpose": "Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified.",
          "category": "static",
          "created_by": "T4.8"
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "audit",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.9",
      "milestone_id": "M2",
      "title": "Audit project isolation, concurrency and import preservation",
      "objective": "An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation.",
      "repository": "pictures",
      "after": [
        "T4.8"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 90,
      "risk": "high",
      "coupling": "high",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 90 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Audit project isolation, concurrency and import preservation: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "scope": {
          "justification": "Audit project isolation, concurrency and import preservation: Changes are limited to .evidence/REQ-021/SP-4.audit.md, .evidence/REQ-021/SP-4.findings.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "duration": {
          "justification": "Audit project isolation, concurrency and import preservation: Uncalibrated agent estimate: 30 minutes inspection, 30 implementation or execution, 30 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "risk": {
          "justification": "Audit project isolation, concurrency and import preservation: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "coupling": {
          "justification": "Audit project isolation, concurrency and import preservation: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8",
            "task:T4.8"
          ]
        },
        "confidence": {
          "justification": "Audit project isolation, concurrency and import preservation: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.8"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-4.audit.md",
        ".evidence/REQ-021/SP-4.findings.json"
      ],
      "shared_resources": [
        "ledger:T4.9"
      ],
      "acceptance_criteria": [
        "An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json",
          "purpose": "An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation.",
          "category": "static",
          "created_by": "T4.9"
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "audit",
      "subplan_id": "SP-4",
      "ui": false
    },
    {
      "id": "T4.31",
      "milestone_id": "M2",
      "title": "Run the project storage and authorization checkpoint",
      "objective": "Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race.",
      "repository": "pictures",
      "after": [
        "T4.3"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 35,
      "risk": "medium",
      "coupling": "high",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 35 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Run the project storage and authorization checkpoint: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "scope": {
          "justification": "Run the project storage and authorization checkpoint: Changes are limited to .evidence/REQ-021/SP-4.storage.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "duration": {
          "justification": "Run the project storage and authorization checkpoint: Uncalibrated agent estimate: 11 minutes inspection, 11 implementation or execution, 13 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "risk": {
          "justification": "Run the project storage and authorization checkpoint: Failure would lose saved work or expose another account document.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "coupling": {
          "justification": "Run the project storage and authorization checkpoint: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3",
            "task:T4.3"
          ]
        },
        "confidence": {
          "justification": "Run the project storage and authorization checkpoint: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T4.3"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-4.storage.json"
      ],
      "shared_resources": [
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-checkpoint",
          "purpose": "Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race.",
          "category": "integration",
          "created_by": "T4.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R6",
        "R7"
      ],
      "kind": "test",
      "subplan_id": "SP-4",
      "ui": false
    }
  ],
  "digest": "749be52ec4afc053"
}

Read SPEC.md and PLAN.md for the complete behaviour. Do not invent flows.
