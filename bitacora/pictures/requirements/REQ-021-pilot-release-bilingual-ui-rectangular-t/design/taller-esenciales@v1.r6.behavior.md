# Shared behavioural requirements

{
  "id": "SP-3",
  "title": "Taller essentials: rectangular tables, Backing and Blender export",
  "outcome": "A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.",
  "covers": [
    "R9",
    "R10",
    "R11"
  ],
  "criteria": [
    "The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact.",
    "Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo.",
    "The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call.",
    "Each existing parametric table type has a creation card that adds its default-sized table and opens the inspector; rectangular tables use 240 × 90 × 75 cm by default and the shopping list contains quantities and dimensions without rental prices.",
    "Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible.",
    "The seven Backing cards appear once in the new Taller group and no longer in their previous visual groups; Shopify /catalogo is unchanged and the original names and AI/photo discovery still resolve the same IDs.",
    "The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable.",
    "The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked.",
    "An explicit setup step provisions a checksum-verified official portable Blender LTS under ~/.local/opt/blender without system-package changes, records its version and executable, and the real import harness never treats a missing executable as a pass.",
    "A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.",
    "A production build on loopback completes the real table-to-Backing-to-GLB flow, recording Blender import evidence or an explicit external block; no unexecuted check is reported as passed.",
    "Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks.",
    "An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task and distinguishes GLB structural evidence from real Blender and owner evidence."
  ],
  "ui": {
    "contract": "taller-esenciales",
    "version": 1,
    "design_task": "T3.1",
    "visual_review_task": "T3.7"
  },
  "ref": "taller-esenciales@v1",
  "tasks": [
    {
      "id": "T3.1",
      "milestone_id": "M1",
      "title": "Copy the approved Taller essentials design contract",
      "objective": "The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact.",
      "repository": "pictures",
      "after": [
        "T1.8"
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
          "justification": "Copy the approved Taller essentials design contract: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "scope": {
          "justification": "Copy the approved Taller essentials design contract: Changes are limited to design/contracts/taller-esenciales@v1.md and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "duration": {
          "justification": "Copy the approved Taller essentials design contract: Uncalibrated agent estimate: 6 minutes inspection, 6 implementation or execution, 8 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "risk": {
          "justification": "Copy the approved Taller essentials design contract: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "coupling": {
          "justification": "Copy the approved Taller essentials design contract: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "confidence": {
          "justification": "Copy the approved Taller essentials design contract: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T1.8"
          ]
        }
      },
      "expected_paths": [
        "design/contracts/taller-esenciales@v1.md"
      ],
      "shared_resources": [
        "design:T3.1"
      ],
      "acceptance_criteria": [
        "The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact."
      ],
      "verification": [
        {
          "type": "command",
          "value": "cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md",
          "purpose": "The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact.",
          "category": "static",
          "created_by": "T3.1"
        }
      ],
      "covers": [
        "R9",
        "R10",
        "R11"
      ],
      "kind": "design",
      "subplan_id": "SP-3",
      "ui": false
    },
    {
      "id": "T3.2",
      "milestone_id": "M1",
      "title": "Add rectangular tables through the existing table editor",
      "objective": "Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo.",
      "repository": "pictures",
      "after": [
        "T3.1"
      ],
      "complexity": "medium",
      "scope": "full_feature",
      "estimated_minutes": 110,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 110 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Add rectangular tables through the existing table editor: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "scope": {
          "justification": "Add rectangular tables through the existing table editor: Changes are limited to src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/EditorConjuntoMesa.tsx and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "duration": {
          "justification": "Add rectangular tables through the existing table editor: Uncalibrated agent estimate: 36 minutes inspection, 36 implementation or execution, 38 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "risk": {
          "justification": "Add rectangular tables through the existing table editor: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "coupling": {
          "justification": "Add rectangular tables through the existing table editor: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1",
            "task:T1.6",
            "task:T3.1"
          ]
        },
        "confidence": {
          "justification": "Add rectangular tables through the existing table editor: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.1"
          ]
        }
      },
      "expected_paths": [
        "src/components/tres-d/FondosYMuebles.tsx",
        "src/components/tres-d/EditorConjuntoMesa.tsx",
        "src/lib/globos3d/mobiliario-conjunto-escena.ts",
        "src/components/tres-d/textos-taller-esenciales.ts",
        "scripts/test/test-taller-mesas-piloto.ts"
      ],
      "shared_resources": [
        "taller:scene",
        "taller:scene"
      ],
      "acceptance_criteria": [
        "Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo.",
        "The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call.",
        "Each existing parametric table type has a creation card that adds its default-sized table and opens the inspector; rectangular tables use 240 × 90 × 75 cm by default and the shopping list contains quantities and dimensions without rental prices."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo.",
          "category": "functional",
          "created_by": "T3.2"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call.",
          "category": "functional",
          "created_by": "T3.2"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "Each existing parametric table type has a creation card that adds its default-sized table and opens the inspector; rectangular tables use 240 × 90 × 75 cm by default and the shopping list contains quantities and dimensions without rental prices.",
          "category": "functional",
          "created_by": "T3.2"
        }
      ],
      "covers": [
        "R9"
      ],
      "kind": "implement",
      "subplan_id": "SP-3",
      "ui": true
    },
    {
      "id": "T3.3",
      "milestone_id": "M1",
      "title": "Group existing party props under Backing without changing their identities",
      "objective": "Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible.",
      "repository": "pictures",
      "after": [
        "T3.2"
      ],
      "complexity": "medium",
      "scope": "full_feature",
      "estimated_minutes": 80,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 80 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Group existing party props under Backing without changing their identities: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "scope": {
          "justification": "Group existing party props under Backing without changing their identities: Changes are limited to src/components/tres-d/FondosYMuebles.tsx, src/lib/catalogo/backing.ts and the listed focused verification artifacts.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "duration": {
          "justification": "Group existing party props under Backing without changing their identities: Uncalibrated agent estimate: 26 minutes inspection, 26 implementation or execution, 28 focused verification and evidence.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "risk": {
          "justification": "Group existing party props under Backing without changing their identities: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "coupling": {
          "justification": "Group existing party props under Backing without changing their identities: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2",
            "task:T3.2"
          ]
        },
        "confidence": {
          "justification": "Group existing party props under Backing without changing their identities: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.2"
          ]
        }
      },
      "expected_paths": [
        "src/components/tres-d/FondosYMuebles.tsx",
        "src/lib/catalogo/backing.ts",
        "src/components/tres-d/textos-taller-esenciales.ts",
        "scripts/test/test-backing-piloto.ts"
      ],
      "shared_resources": [
        "taller:scene",
        "taller:scene"
      ],
      "acceptance_criteria": [
        "Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible.",
        "The seven Backing cards appear once in the new Taller group and no longer in their previous visual groups; Shopify /catalogo is unchanged and the original names and AI/photo discovery still resolve the same IDs."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-backing-piloto.ts",
          "purpose": "Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible.",
          "category": "functional",
          "created_by": "T3.3"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-backing-piloto.ts",
          "purpose": "The seven Backing cards appear once in the new Taller group and no longer in their previous visual groups; Shopify /catalogo is unchanged and the original names and AI/photo discovery still resolve the same IDs.",
          "category": "functional",
          "created_by": "T3.3"
        }
      ],
      "covers": [
        "R11"
      ],
      "kind": "implement",
      "subplan_id": "SP-3",
      "ui": true
    },
    {
      "id": "T3.4",
      "milestone_id": "M1",
      "title": "Verify and repair the GLB geometry and material export",
      "objective": "The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable.",
      "repository": "pictures",
      "after": [
        "T3.3"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 140,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 140 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Verify and repair the GLB geometry and material export: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "scope": {
          "justification": "Verify and repair the GLB geometry and material export: Changes are limited to src/components/tres-d/exportar-escena-glb.ts, src/components/tres-d/exportadores-escena-globos.ts and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "duration": {
          "justification": "Verify and repair the GLB geometry and material export: Uncalibrated agent estimate: 46 minutes inspection, 46 implementation or execution, 48 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "risk": {
          "justification": "Verify and repair the GLB geometry and material export: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "coupling": {
          "justification": "Verify and repair the GLB geometry and material export: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3",
            "task:T3.3"
          ]
        },
        "confidence": {
          "justification": "Verify and repair the GLB geometry and material export: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.3"
          ]
        }
      },
      "expected_paths": [
        "src/components/tres-d/exportar-escena-glb.ts",
        "src/components/tres-d/exportadores-escena-globos.ts",
        "src/components/tres-d/ExportarEscenaTaller.tsx",
        "scripts/test/test-exportadores-escena-taller.ts",
        "scripts/test/fixtures/req021-export-scene.json"
      ],
      "shared_resources": [
        "taller:scene"
      ],
      "acceptance_criteria": [
        "The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-exportadores-escena-taller.ts",
          "purpose": "The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable.",
          "category": "functional",
          "created_by": "T3.4"
        }
      ],
      "covers": [
        "R10"
      ],
      "kind": "implement",
      "subplan_id": "SP-3",
      "ui": true
    },
    {
      "id": "T3.5",
      "milestone_id": "M1",
      "title": "Implement the Taller browser and Blender verification harness",
      "objective": "The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked.",
      "repository": "pictures",
      "after": [
        "T3.4"
      ],
      "complexity": "high",
      "scope": "full_feature",
      "estimated_minutes": 120,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "low",
      "estimate_rationale": "Uncalibrated estimate of 120 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implement the Taller browser and Blender verification harness: The inspected boundary requires cross-request identity, concurrency and restoration reasoning.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "scope": {
          "justification": "Implement the Taller browser and Blender verification harness: Changes are limited to scripts/test/test-integracion-taller-esenciales.ts, scripts/test/blender/verificar_glb.py and the listed focused verification artifacts.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "duration": {
          "justification": "Implement the Taller browser and Blender verification harness: Uncalibrated agent estimate: 40 minutes inspection, 40 implementation or execution, 40 focused verification and evidence.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "risk": {
          "justification": "Implement the Taller browser and Blender verification harness: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "coupling": {
          "justification": "Implement the Taller browser and Blender verification harness: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4",
            "task:T1.7",
            "task:T3.4"
          ]
        },
        "confidence": {
          "justification": "Implement the Taller browser and Blender verification harness: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.4"
          ]
        }
      },
      "expected_paths": [
        "scripts/test/test-integracion-taller-esenciales.ts",
        "scripts/test/blender/verificar_glb.py",
        "scripts/test/test-harness-taller-esenciales.ts",
        "docs/req021-blender.md",
        "package.json"
      ],
      "shared_resources": [
        "package.json scripts",
        "taller:scene"
      ],
      "acceptance_criteria": [
        "The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked.",
        "An explicit setup step provisions a checksum-verified official portable Blender LTS under ~/.local/opt/blender without system-package changes, records its version and executable, and the real import harness never treats a missing executable as a pass."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run taller:test-harness-esenciales",
          "purpose": "The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked.",
          "category": "functional",
          "created_by": "T3.5"
        },
        {
          "type": "command",
          "value": "npm run taller:test-harness-esenciales",
          "purpose": "An explicit setup step provisions a checksum-verified official portable Blender LTS under ~/.local/opt/blender without system-package changes, records its version and executable, and the real import harness never treats a missing executable as a pass.",
          "category": "functional",
          "created_by": "T3.5"
        }
      ],
      "covers": [
        "R9",
        "R10",
        "R11"
      ],
      "kind": "implement",
      "subplan_id": "SP-3",
      "ui": false
    },
    {
      "id": "T3.6",
      "milestone_id": "M1",
      "title": "Run the real Taller essentials integration scenario",
      "objective": "A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.",
      "repository": "pictures",
      "after": [
        "T3.5"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 50,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 50 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Run the real Taller essentials integration scenario: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "scope": {
          "justification": "Run the real Taller essentials integration scenario: Changes are limited to .evidence/REQ-021/SP-3.integration.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "duration": {
          "justification": "Run the real Taller essentials integration scenario: Uncalibrated agent estimate: 16 minutes inspection, 16 implementation or execution, 18 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "risk": {
          "justification": "Run the real Taller essentials integration scenario: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "coupling": {
          "justification": "Run the real Taller essentials integration scenario: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5",
            "task:T3.5"
          ]
        },
        "confidence": {
          "justification": "Run the real Taller essentials integration scenario: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.5"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-3.integration.json"
      ],
      "shared_resources": [
        "taller:scene"
      ],
      "acceptance_criteria": [
        "A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.",
        "A production build on loopback completes the real table-to-Backing-to-GLB flow, recording Blender import evidence or an explicit external block; no unexecuted check is reported as passed."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run taller:test-integracion-esenciales",
          "purpose": "A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.",
          "category": "integration",
          "created_by": "T3.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run taller:test-integracion-esenciales",
          "purpose": "A production build on loopback completes the real table-to-Backing-to-GLB flow, recording Blender import evidence or an explicit external block; no unexecuted check is reported as passed.",
          "category": "integration",
          "created_by": "T3.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        }
      ],
      "covers": [
        "R9",
        "R10",
        "R11"
      ],
      "kind": "test",
      "subplan_id": "SP-3",
      "ui": false
    },
    {
      "id": "T3.7",
      "milestone_id": "M1",
      "title": "Review rendered Taller essentials against the design",
      "objective": "Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks.",
      "repository": "pictures",
      "after": [
        "T3.6"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 60,
      "risk": "medium",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 60 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Review rendered Taller essentials against the design: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "scope": {
          "justification": "Review rendered Taller essentials against the design: Changes are limited to .evidence/REQ-021/SP-3.visual.md, .evidence/REQ-021/SP-3.visual.findings.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "duration": {
          "justification": "Review rendered Taller essentials against the design: Uncalibrated agent estimate: 20 minutes inspection, 20 implementation or execution, 20 focused verification and evidence.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "risk": {
          "justification": "Review rendered Taller essentials against the design: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "coupling": {
          "justification": "Review rendered Taller essentials against the design: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6",
            "task:T3.6"
          ]
        },
        "confidence": {
          "justification": "Review rendered Taller essentials against the design: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.6"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-3.visual.md",
        ".evidence/REQ-021/SP-3.visual.findings.json"
      ],
      "shared_resources": [
        "ledger:T3.7"
      ],
      "acceptance_criteria": [
        "Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-3.visual.findings.json",
          "purpose": "Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks.",
          "category": "static",
          "created_by": "T3.7"
        }
      ],
      "covers": [
        "R9",
        "R10",
        "R11"
      ],
      "kind": "audit",
      "subplan_id": "SP-3",
      "ui": false
    },
    {
      "id": "T3.8",
      "milestone_id": "M1",
      "title": "Audit Taller essentials and export compatibility",
      "objective": "An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task and distinguishes GLB structural evidence from real Blender and owner evidence.",
      "repository": "pictures",
      "after": [
        "T3.7"
      ],
      "complexity": "medium",
      "scope": "small_change",
      "estimated_minutes": 90,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Uncalibrated estimate of 90 minutes including focused verification, not a deadline.",
      "classification_evidence": {
        "complexity": {
          "justification": "Audit Taller essentials and export compatibility: The inspected boundary requires bounded changes using existing domain operations.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "scope": {
          "justification": "Audit Taller essentials and export compatibility: Changes are limited to .evidence/REQ-021/SP-3.audit.md, .evidence/REQ-021/SP-3.findings.json and the listed focused verification artifacts.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "duration": {
          "justification": "Audit Taller essentials and export compatibility: Uncalibrated agent estimate: 30 minutes inspection, 30 implementation or execution, 30 focused verification and evidence.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "risk": {
          "justification": "Audit Taller essentials and export compatibility: Failure would produce incorrect scene geometry, shopping quantities or exported materials.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "coupling": {
          "justification": "Audit Taller essentials and export compatibility: Explicit prerequisites order shared scene files and package script registration; consumers use the stated versioned contracts.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7",
            "task:T3.7"
          ]
        },
        "confidence": {
          "justification": "Audit Taller essentials and export compatibility: Existing source was inspected; round 9 answers now settle product behavior, while Designer reconciliation and future integration evidence remain pending.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "spec:SPEC.md#clarifications",
            "task:T3.7"
          ]
        }
      },
      "expected_paths": [
        ".evidence/REQ-021/SP-3.audit.md",
        ".evidence/REQ-021/SP-3.findings.json"
      ],
      "shared_resources": [
        "ledger:T3.8"
      ],
      "acceptance_criteria": [
        "An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task and distinguishes GLB structural evidence from real Blender and owner evidence."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json",
          "purpose": "An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task and distinguishes GLB structural evidence from real Blender and owner evidence.",
          "category": "static",
          "created_by": "T3.8"
        }
      ],
      "covers": [
        "R9",
        "R10",
        "R11"
      ],
      "kind": "audit",
      "subplan_id": "SP-3",
      "ui": false
    }
  ],
  "digest": "f3f2ed19d4dc6d0a"
}

Read SPEC.md and PLAN.md for the complete behaviour. Do not invent flows.
