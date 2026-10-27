# Requisitos de comportamiento compartidos

{
  "id": "SP-3",
  "title": "Elementos esenciales del Taller: mesas rectangulares, fondos y exportación a Blender",
  "outcome": "Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita el tamaño y las sillas, y ve las cantidades reales y las dimensiones en la lista de compras, sin precios de alquiler; Taller Fondos y muebles tiene un grupo Fondos que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y la detección mediante IA/fotos; el GLB exportado se abre en Blender LTS portable con la misma distribución, tamaños en metros y colores base.",
  "covers": [
    "R9",
    "R10",
    "R11"
  ],
  "criteria": [
    "El contrato del repositorio es idéntico byte por byte al artefacto taller-esenciales@v1 aprobado por el propietario.",
    "Al agregar una mesa rectangular, se muestran el largo, la profundidad y la cantidad de sillas, se selecciona en el inspector y se actualiza la lista de compras real con las sillas colocadas, incluidas las advertencias de capacidad y la opción de deshacer.",
    "Las herramientas existentes agregar_mesas, cambiar_mesas y cambiar_sillas producen las mismas dimensiones de mesa y las mismas cantidades reales de sillas que la edición manual, sin una llamada de IA de pago.",
    "Cada tipo de mesa paramétrica existente tiene una tarjeta de creación que agrega una mesa con el tamaño predeterminado y abre el inspector; las mesas rectangulares usan 240 × 90 × 75 cm de forma predeterminada y la lista de compras contiene cantidades y dimensiones, sin precios de alquiler.",
    "Fondos incluye panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, y permite agregar cada uno; los IDs existentes, las escenas guardadas, la propiedad del repositorio, la búsqueda y la detección mediante IA/fotos siguen siendo compatibles.",
    "Las siete tarjetas de Fondos aparecen una sola vez en el nuevo grupo Taller y ya no aparecen en sus grupos visuales anteriores; Shopify /catalogo no cambia y los nombres originales y la detección mediante IA/fotos siguen resolviendo los mismos IDs.",
    "El GLB exportado conserva las transformaciones de mundo reales de la escena, las dimensiones en metros, las instancias visibles y los colores base, sin modificar el editor ni llamar a la red; los errores de exportación son visibles y se pueden reintentar.",
    "El arnés inicia una compilación real de next start, ejecuta en Chromium las operaciones de mesas y Fondos, descarga el GLB real y compara con el fixture las posiciones, las dimensiones en metros y los colores base importados por Blender; si falta Blender, lo informa como bloqueado.",
    "Un paso de configuración explícito instala una versión oficial portable de Blender LTS con checksum verificado en ~/.local/opt/blender, sin cambios en los paquetes del sistema, registra su versión y ejecutable, y el arnés de importación real nunca considera que la falta del ejecutable sea un resultado aprobado.",
    "Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita el tamaño y las sillas, y ve las cantidades reales y las dimensiones en la lista de compras, sin precios de alquiler; Taller Fondos y muebles tiene un grupo Fondos que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y la detección mediante IA/fotos; el GLB exportado se abre en Blender LTS portable con la misma distribución, tamaños en metros y colores base.",
    "Una compilación de producción en loopback completa el flujo real de mesa a Fondos y a GLB, y registra evidencia de importación en Blender o un bloqueo externo explícito; ningún control no ejecutado se informa como aprobado.",
    "Las representaciones en teléfono, tableta y escritorio de los estados de creación y edición de mesas, Fondos y exportación coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos accionables se asignan a sus tareas responsables.",
    "Una auditoría independiente de especificación y estándares de SP-3 no tiene hallazgos críticos o altos abiertos, asigna cada defecto a la tarea que lo introdujo y distingue la evidencia estructural del GLB de la evidencia real de Blender y del propietario."
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
      "title": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller",
      "objective": "El contrato del repositorio es idéntico byte por byte al artefacto taller-esenciales@v1 aprobado por el propietario.",
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
      "estimate_rationale": "Estimación no calibrada de 20 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "scope": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: los cambios se limitan a design/contracts/taller-esenciales@v1.md y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "duration": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: estimación no calibrada del agente: 6 minutos de inspección, 6 de implementación o ejecución y 8 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "risk": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "coupling": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T1.8"
          ]
        },
        "confidence": {
          "justification": "Copiar el contrato de diseño aprobado de Elementos esenciales del Taller: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "El contrato del repositorio es idéntico byte por byte al artefacto taller-esenciales@v1 aprobado por el propietario."
      ],
      "verification": [
        {
          "type": "command",
          "value": "cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md",
          "purpose": "El contrato del repositorio es idéntico byte por byte al artefacto taller-esenciales@v1 aprobado por el propietario.",
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
      "title": "Agregar mesas rectangulares mediante el editor de mesas existente",
      "objective": "Al agregar una mesa rectangular, se muestran el largo, la profundidad y la cantidad de sillas, se selecciona en el inspector y se actualiza la lista de compras real con las sillas colocadas, incluidas las advertencias de capacidad y la opción de deshacer.",
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
      "estimate_rationale": "Estimación no calibrada de 110 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "scope": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: los cambios se limitan a src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/EditorConjuntoMesa.tsx y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "duration": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: estimación no calibrada del agente: 36 minutos de inspección, 36 de implementación o ejecución y 38 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "risk": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1"
          ]
        },
        "coupling": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.1",
            "task:T1.6",
            "task:T3.1"
          ]
        },
        "confidence": {
          "justification": "Agregar mesas rectangulares mediante el editor de mesas existente: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "Al agregar una mesa rectangular, se muestran el largo, la profundidad y la cantidad de sillas, se selecciona en el inspector y se actualiza la lista de compras real con las sillas colocadas, incluidas las advertencias de capacidad y la opción de deshacer.",
        "Las herramientas existentes agregar_mesas, cambiar_mesas y cambiar_sillas producen las mismas dimensiones de mesa y las mismas cantidades reales de sillas que la edición manual, sin una llamada de IA de pago.",
        "Cada tipo de mesa paramétrica existente tiene una tarjeta de creación que agrega una mesa con el tamaño predeterminado y abre el inspector; las mesas rectangulares usan 240 × 90 × 75 cm de forma predeterminada y la lista de compras contiene cantidades y dimensiones, sin precios de alquiler."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "Al agregar una mesa rectangular, se muestran el largo, la profundidad y la cantidad de sillas, se selecciona en el inspector y se actualiza la lista de compras real con las sillas colocadas, incluidas las advertencias de capacidad y la opción de deshacer.",
          "category": "functional",
          "created_by": "T3.2"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "Las herramientas existentes agregar_mesas, cambiar_mesas y cambiar_sillas producen las mismas dimensiones de mesa y las mismas cantidades reales de sillas que la edición manual, sin una llamada de IA de pago.",
          "category": "functional",
          "created_by": "T3.2"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-taller-mesas-piloto.ts",
          "purpose": "Cada tipo de mesa paramétrica existente tiene una tarjeta de creación que agrega una mesa con el tamaño predeterminado y abre el inspector; las mesas rectangulares usan 240 × 90 × 75 cm de forma predeterminada y la lista de compras contiene cantidades y dimensiones, sin precios de alquiler.",
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
      "title": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades",
      "objective": "Fondos incluye panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, y permite agregar cada uno; los IDs existentes, las escenas guardadas, la propiedad del repositorio, la búsqueda y la detección mediante IA/fotos siguen siendo compatibles.",
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
      "estimate_rationale": "Estimación no calibrada de 80 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "scope": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: los cambios se limitan a src/components/tres-d/FondosYMuebles.tsx, src/lib/catalogo/backing.ts y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "duration": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: estimación no calibrada del agente: 26 minutos de inspección, 26 de implementación o ejecución y 28 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "risk": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2"
          ]
        },
        "coupling": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/lib/catalogo/asignacion-fondos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.2",
            "task:T3.2"
          ]
        },
        "confidence": {
          "justification": "Agrupar los elementos existentes para fiestas bajo Fondos sin cambiar sus identidades: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "Fondos incluye panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, y permite agregar cada uno; los IDs existentes, las escenas guardadas, la propiedad del repositorio, la búsqueda y la detección mediante IA/fotos siguen siendo compatibles.",
        "Las siete tarjetas de Fondos aparecen una sola vez en el nuevo grupo Taller y ya no aparecen en sus grupos visuales anteriores; Shopify /catalogo no cambia y los nombres originales y la detección mediante IA/fotos siguen resolviendo los mismos IDs."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-backing-piloto.ts",
          "purpose": "Fondos incluye panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, y permite agregar cada uno; los IDs existentes, las escenas guardadas, la propiedad del repositorio, la búsqueda y la detección mediante IA/fotos siguen siendo compatibles.",
          "category": "functional",
          "created_by": "T3.3"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-backing-piloto.ts",
          "purpose": "Las siete tarjetas de Fondos aparecen una sola vez en el nuevo grupo Taller y ya no aparecen en sus grupos visuales anteriores; Shopify /catalogo no cambia y los nombres originales y la detección mediante IA/fotos siguen resolviendo los mismos IDs.",
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
      "title": "Verificar y corregir la exportación de geometría y materiales GLB",
      "objective": "El GLB exportado conserva las transformaciones de mundo reales de la escena, las dimensiones en metros, las instancias visibles y los colores base, sin modificar el editor ni llamar a la red; los errores de exportación son visibles y se pueden reintentar.",
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
      "estimate_rationale": "Estimación no calibrada de 140 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "scope": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: los cambios se limitan a src/components/tres-d/exportar-escena-glb.ts, src/components/tres-d/exportadores-escena-globos.ts y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "duration": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: estimación no calibrada del agente: 46 minutos de inspección, 46 de implementación o ejecución y 48 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "risk": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3"
          ]
        },
        "coupling": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/exportar-escena-glb.ts",
            "spec:SPEC.md#requirements",
            "task:T3.3",
            "task:T3.3"
          ]
        },
        "confidence": {
          "justification": "Verificar y corregir la exportación de geometría y materiales GLB: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "El GLB exportado conserva las transformaciones de mundo reales de la escena, las dimensiones en metros, las instancias visibles y los colores base, sin modificar el editor ni llamar a la red; los errores de exportación son visibles y se pueden reintentar."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-exportadores-escena-taller.ts",
          "purpose": "El GLB exportado conserva las transformaciones de mundo reales de la escena, las dimensiones en metros, las instancias visibles y los colores base, sin modificar el editor ni llamar a la red; los errores de exportación son visibles y se pueden reintentar.",
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
      "title": "Implementar el arnés de verificación del Taller en navegador y Blender",
      "objective": "El arnés inicia una compilación real de next start, ejecuta en Chromium las operaciones de mesas y Fondos, descarga el GLB real y compara con el fixture las posiciones, las dimensiones en metros y los colores base importados por Blender; si falta Blender, lo informa como bloqueado.",
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
      "estimate_rationale": "Estimación no calibrada de 120 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "scope": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: los cambios se limitan a scripts/test/test-integracion-taller-esenciales.ts, scripts/test/blender/verificar_glb.py y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "duration": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: estimación no calibrada del agente: 40 minutos de inspección, 40 de implementación o ejecución y 40 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "risk": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4"
          ]
        },
        "coupling": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:scripts/test/test-exportadores-escena-taller.ts",
            "spec:SPEC.md#requirements",
            "task:T3.4",
            "task:T1.7",
            "task:T3.4"
          ]
        },
        "confidence": {
          "justification": "Implementar el arnés de verificación del Taller en navegador y Blender: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "El arnés inicia una compilación real de next start, ejecuta en Chromium las operaciones de mesas y Fondos, descarga el GLB real y compara con el fixture las posiciones, las dimensiones en metros y los colores base importados por Blender; si falta Blender, lo informa como bloqueado.",
        "Un paso de configuración explícito instala una versión oficial portable de Blender LTS con checksum verificado en ~/.local/opt/blender, sin cambios en los paquetes del sistema, registra su versión y ejecutable, y el arnés de importación real nunca considera que la falta del ejecutable sea un resultado aprobado."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run taller:test-harness-esenciales",
          "purpose": "El arnés inicia una compilación real de next start, ejecuta en Chromium las operaciones de mesas y Fondos, descarga el GLB real y compara con el fixture las posiciones, las dimensiones en metros y los colores base importados por Blender; si falta Blender, lo informa como bloqueado.",
          "category": "functional",
          "created_by": "T3.5"
        },
        {
          "type": "command",
          "value": "npm run taller:test-harness-esenciales",
          "purpose": "Un paso de configuración explícito instala una versión oficial portable de Blender LTS con checksum verificado en ~/.local/opt/blender, sin cambios en los paquetes del sistema, registra su versión y ejecutable, y el arnés de importación real nunca considera que la falta del ejecutable sea un resultado aprobado.",
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
      "title": "Ejecutar el escenario de integración real de Elementos esenciales del Taller",
      "objective": "Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita el tamaño y las sillas, y ve las cantidades reales y las dimensiones en la lista de compras, sin precios de alquiler; Taller Fondos y muebles tiene un grupo Fondos que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y la detección mediante IA/fotos; el GLB exportado se abre en Blender LTS portable con la misma distribución, tamaños en metros y colores base.",
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
      "estimate_rationale": "Estimación no calibrada de 50 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "scope": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: los cambios se limitan a .evidence/REQ-021/SP-3.integration.json y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "duration": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: estimación no calibrada del agente: 16 minutos de inspección, 16 de implementación o ejecución y 18 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "risk": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5"
          ]
        },
        "coupling": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.5",
            "task:T3.5"
          ]
        },
        "confidence": {
          "justification": "Ejecutar el escenario de integración real de Elementos esenciales del Taller: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita el tamaño y las sillas, y ve las cantidades reales y las dimensiones en la lista de compras, sin precios de alquiler; Taller Fondos y muebles tiene un grupo Fondos que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y la detección mediante IA/fotos; el GLB exportado se abre en Blender LTS portable con la misma distribución, tamaños en metros y colores base.",
        "Una compilación de producción en loopback completa el flujo real de mesa a Fondos y a GLB, y registra evidencia de importación en Blender o un bloqueo externo explícito; ningún control no ejecutado se informa como aprobado."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run taller:test-integracion-esenciales",
          "purpose": "Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita el tamaño y las sillas, y ve las cantidades reales y las dimensiones en la lista de compras, sin precios de alquiler; Taller Fondos y muebles tiene un grupo Fondos que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y la detección mediante IA/fotos; el GLB exportado se abre en Blender LTS portable con la misma distribución, tamaños en metros y colores base.",
          "category": "integration",
          "created_by": "T3.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run taller:test-integracion-esenciales",
          "purpose": "Una compilación de producción en loopback completa el flujo real de mesa a Fondos y a GLB, y registra evidencia de importación en Blender o un bloqueo externo explícito; ningún control no ejecutado se informa como aprobado.",
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
      "title": "Revisar la representación visual de Elementos esenciales del Taller según el diseño",
      "objective": "Las representaciones en teléfono, tableta y escritorio de los estados de creación y edición de mesas, Fondos y exportación coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos accionables se asignan a sus tareas responsables.",
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
      "estimate_rationale": "Estimación no calibrada de 60 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "scope": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: los cambios se limitan a .evidence/REQ-021/SP-3.visual.md, .evidence/REQ-021/SP-3.visual.findings.json y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "duration": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: estimación no calibrada del agente: 20 minutos de inspección, 20 de implementación o ejecución y 20 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "risk": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6"
          ]
        },
        "coupling": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/FondosYMuebles.tsx",
            "spec:SPEC.md#requirements",
            "task:T3.6",
            "task:T3.6"
          ]
        },
        "confidence": {
          "justification": "Revisar la representación visual de Elementos esenciales del Taller según el diseño: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "Las representaciones en teléfono, tableta y escritorio de los estados de creación y edición de mesas, Fondos y exportación coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos accionables se asignan a sus tareas responsables."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-3.visual.findings.json",
          "purpose": "Las representaciones en teléfono, tableta y escritorio de los estados de creación y edición de mesas, Fondos y exportación coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos accionables se asignan a sus tareas responsables.",
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
      "title": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación",
      "objective": "Una auditoría independiente de especificación y estándares de SP-3 no tiene hallazgos críticos o altos abiertos, asigna cada defecto a la tarea que lo introdujo y distingue la evidencia estructural del GLB de la evidencia real de Blender y del propietario.",
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
      "estimate_rationale": "Estimación no calibrada de 90 minutos, incluida la verificación focalizada; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: el límite inspeccionado requiere cambios acotados que usan operaciones de dominio existentes.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "scope": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: los cambios se limitan a .evidence/REQ-021/SP-3.audit.md, .evidence/REQ-021/SP-3.findings.json y a los artefactos de verificación focalizada indicados.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "duration": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: estimación no calibrada del agente: 30 minutos de inspección, 30 de implementación o ejecución y 30 de verificación focalizada y recopilación de evidencia.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "risk": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: un fallo produciría geometría incorrecta de la escena, cantidades incorrectas en la lista de compras o materiales exportados incorrectos.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7"
          ]
        },
        "coupling": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: los requisitos previos explícitos ordenan los archivos compartidos de escena y el registro del script del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/lib/globos3d/mobiliario-conjunto-tipos.ts",
            "spec:SPEC.md#requirements",
            "task:T3.7",
            "task:T3.7"
          ]
        },
        "confidence": {
          "justification": "Auditar Elementos esenciales del Taller y la compatibilidad de exportación: se inspeccionó el código fuente existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación del diseñador y la evidencia de integración futura siguen pendientes.",
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
        "Una auditoría independiente de especificación y estándares de SP-3 no tiene hallazgos críticos o altos abiertos, asigna cada defecto a la tarea que lo introdujo y distingue la evidencia estructural del GLB de la evidencia real de Blender y del propietario."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json",
          "purpose": "Una auditoría independiente de especificación y estándares de SP-3 no tiene hallazgos críticos o altos abiertos, asigna cada defecto a la tarea que lo introdujo y distingue la evidencia estructural del GLB de la evidencia real de Blender y del propietario.",
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

Lee SPEC.md y PLAN.md para conocer el comportamiento completo. No inventes flujos.
