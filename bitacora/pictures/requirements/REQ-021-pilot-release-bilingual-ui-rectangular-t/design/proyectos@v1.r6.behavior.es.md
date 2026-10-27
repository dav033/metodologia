# Requisitos de comportamiento compartidos

{
  "id": "SP-4",
  "title": "Proyectos guardados",
  "outcome": "Un usuario guarda, enumera, vuelve a abrir y continúa proyectos de Taller almacenados en su cuenta; los empleados y administradores abren los de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida.",
  "covers": [
    "R6",
    "R7"
  ],
  "criteria": [
    "El contrato del repositorio es idéntico byte por byte al artefacto proyectos@v1 aprobado por el propietario.",
    "Un proyecto se almacena en Postgres bajo la cuenta de la sesión, con un documento de escena completo y versionado; las actualizaciones condicionales incrementan la revisión de forma atómica y rechazan escrituras obsoletas sin modificar los datos almacenados.",
    "Se rechaza la eliminación de una cuenta si existen proyectos, incluso ante una condición de carrera entre guardar un proyecto y eliminar la cuenta; los documentos malformados o demasiado grandes, los ID de nodo duplicados, las dimensiones no finitas y los vínculos de padre rotos o cíclicos se rechazan sin escrituras.",
    "Las API de proyectos enumeran y leen solo los proyectos propios, salvo que se conceda proyectos.ver_todos; rechazan escrituras no autorizadas y mutaciones de origen cruzado, y devuelven conflictos de versión estables sin revelar el documento de otro propietario.",
    "La búsqueda por nombre de proyecto y los filtros autorizados por propietario se aplican a toda la colección del servidor antes de paginar; los cursores vinculados a filtros, la coincidencia literal de nombres y la autorización por cuenta impiden omitir coincidencias en páginas posteriores y divulgar metadatos.",
    "El usuario asigna nombres, guarda, enumera y vuelve a abrir proyectos con la escena completa intacta entre navegadores; las ediciones pendientes nunca se marcan como guardadas debido a una respuesta obsoleta.",
    "Dos copias abiertas no pueden sobrescribirse silenciosamente: un 409 detiene el guardado automático, conserva la escena local no enviada y ofrece cargar la versión del servidor o guardar una nueva copia propia; el personal y los administradores leen originales ajenos sin acceso de escritura y pueden guardar una copia propia solo con taller.usar.",
    "El primer guardado con nombre es explícito y las ediciones posteriores se guardan automáticamente; la búsqueda de la lista de proyectos encuentra coincidencias autorizadas más allá de la primera página cargada, los cambios de filtro reinician la paginación y las respuestas obsoletas de consultas no pueden reemplazar los resultados actuales.",
    "A una cuenta con sesión iniciada y una escena heredada en el navegador se le ofrece una importación explícita; aceptarla crea exactamente un proyecto propio, incluso tras un reintento; rechazarla o que falle la validación conserva los datos locales sin procesar, y ninguna cuenta recibe automáticamente una escena heredada.",
    "El entorno de pruebas de proyectos inicia puntos de entrada reales de Next contra un esquema de prueba aislado y ejecuta contextos de navegador autenticados e independientes para comprobar persistencia, denegación de acceso, conflictos e importación heredada.",
    "El entorno de pruebas del navegador carga más de cincuenta proyectos y verifica una coincidencia más allá de la primera página, el filtrado autorizado por propietario, el reintento de la página siguiente y el rechazo de respuestas obsoletas de búsqueda, sin divulgar metadatos ajenos.",
    "Un usuario guarda, enumera, vuelve a abrir y continúa proyectos de Taller almacenados en su cuenta; los empleados y administradores abren los de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida.",
    "Una compilación de producción real supera las comprobaciones de persistencia entre contextos de navegador nuevos, denegación por cuenta, lectura y copia por parte del personal, conflicto entre guardados simultáneos, reintento de importación y aislamiento al cambiar de cuenta en la base de datos REQ-021.",
    "La lista de proyectos, los estados de guardado/sin conexión/conflicto, la vista ajena de solo lectura y el aviso de importación coinciden con proyectos@v1 aprobado en anchos de teléfono, tableta y escritorio, con el comportamiento del teclado y del foco verificado.",
    "Una auditoría independiente de especificación y estándares de SP-4 no tiene hallazgos críticos o altos abiertos y verifica la propiedad, el control atómico de versiones, la idempotencia y conservación de importaciones, el registro de eliminación y el aislamiento al cambiar de cuenta.",
    "Antes del trabajo de UI, el servicio real de proyectos y las comprobaciones de la API superan las pruebas de rechazo atómico de escrituras obsoletas, aislamiento de cuentas, validación, claves de reintento de importación y la condición de carrera entre guardar un proyecto y eliminar la cuenta."
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
      "title": "Copiar el contrato de diseño aprobado para proyectos guardados",
      "objective": "El contrato del repositorio es idéntico byte por byte al artefacto proyectos@v1 aprobado por el propietario.",
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
      "estimate_rationale": "Estimación no calibrada de 20 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: el límite inspeccionado requiere cambios acotados que usen operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "scope": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: los cambios se limitan a design/contracts/proyectos@v1.md y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "duration": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: estimación no calibrada del agente: 6 minutos de inspección, 6 de implementación o ejecución y 8 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "risk": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "coupling": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T92"
          ]
        },
        "confidence": {
          "justification": "Copiar el contrato de diseño aprobado para proyectos guardados: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "El contrato del repositorio es idéntico byte por byte al artefacto proyectos@v1 aprobado por el propietario."
      ],
      "verification": [
        {
          "type": "command",
          "value": "cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md",
          "purpose": "El contrato del repositorio es idéntico byte por byte al artefacto proyectos@v1 aprobado por el propietario.",
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
      "title": "Implementar el almacenamiento versionado de proyectos y la validación de escenas",
      "objective": "Un proyecto se almacena en Postgres bajo la cuenta de la sesión, con un documento de escena completo y versionado; las actualizaciones condicionales incrementan la revisión de forma atómica y rechazan escrituras obsoletas sin modificar los datos almacenados.",
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
      "estimate_rationale": "Estimación no calibrada de 170 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "scope": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: los cambios se limitan a scripts/migrations/038_proyectos.sql, src/lib/proyectos/contrato.ts y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "duration": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: estimación no calibrada del agente: 56 minutos de inspección, 56 de implementación o ejecución y 58 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "risk": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.1"
          ]
        },
        "coupling": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T1.8",
            "task:T2.2",
            "task:T4.1"
          ]
        },
        "confidence": {
          "justification": "Implementar el almacenamiento versionado de proyectos y la validación de escenas: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "Un proyecto se almacena en Postgres bajo la cuenta de la sesión, con un documento de escena completo y versionado; las actualizaciones condicionales incrementan la revisión de forma atómica y rechazan escrituras obsoletas sin modificar los datos almacenados.",
        "Se rechaza la eliminación de una cuenta si existen proyectos, incluso ante una condición de carrera entre guardar un proyecto y eliminar la cuenta; los documentos malformados o demasiado grandes, los ID de nodo duplicados, las dimensiones no finitas y los vínculos de padre rotos o cíclicos se rechazan sin escrituras."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts",
          "purpose": "Un proyecto se almacena en Postgres bajo la cuenta de la sesión, con un documento de escena completo y versionado; las actualizaciones condicionales incrementan la revisión de forma atómica y rechazan escrituras obsoletas sin modificar los datos almacenados.",
          "category": "functional",
          "created_by": "T4.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts",
          "purpose": "Se rechaza la eliminación de una cuenta si existen proyectos, incluso ante una condición de carrera entre guardar un proyecto y eliminar la cuenta; los documentos malformados o demasiado grandes, los ID de nodo duplicados, las dimensiones no finitas y los vínculos de padre rotos o cíclicos se rechazan sin escrituras.",
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
      "title": "Implementar las API de proyectos con autorización por recurso",
      "objective": "Las API de proyectos enumeran y leen solo los proyectos propios, salvo que se conceda proyectos.ver_todos; rechazan escrituras no autorizadas y mutaciones de origen cruzado, y devuelven conflictos de versión estables sin revelar el documento de otro propietario.",
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
      "estimate_rationale": "Estimación no calibrada de 100 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar las API de proyectos con autorización por recurso: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "scope": {
          "justification": "Implementar las API de proyectos con autorización por recurso: los cambios se limitan a src/app/api/proyectos/route.ts, src/app/api/proyectos/[id]/route.ts y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "duration": {
          "justification": "Implementar las API de proyectos con autorización por recurso: estimación no calibrada del agente: 33 minutos de inspección, 33 de implementación o ejecución y 34 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "risk": {
          "justification": "Implementar las API de proyectos con autorización por recurso: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2"
          ]
        },
        "coupling": {
          "justification": "Implementar las API de proyectos con autorización por recurso: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "spec:SPEC.md#requirements",
            "task:T4.2",
            "task:T1.6",
            "task:T4.2"
          ]
        },
        "confidence": {
          "justification": "Implementar las API de proyectos con autorización por recurso: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "scripts de package.json",
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "Las API de proyectos enumeran y leen solo los proyectos propios, salvo que se conceda proyectos.ver_todos; rechazan escrituras no autorizadas y mutaciones de origen cruzado, y devuelven conflictos de versión estables sin revelar el documento de otro propietario.",
        "La búsqueda por nombre de proyecto y los filtros autorizados por propietario se aplican a toda la colección del servidor antes de paginar; los cursores vinculados a filtros, la coincidencia literal de nombres y la autorización por cuenta impiden omitir coincidencias en páginas posteriores y divulgar metadatos."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-api",
          "purpose": "Las API de proyectos enumeran y leen solo los proyectos propios, salvo que se conceda proyectos.ver_todos; rechazan escrituras no autorizadas y mutaciones de origen cruzado, y devuelven conflictos de versión estables sin revelar el documento de otro propietario.",
          "category": "functional",
          "created_by": "T4.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-api",
          "purpose": "La búsqueda por nombre de proyecto y los filtros autorizados por propietario se aplican a toda la colección del servidor antes de paginar; los cursores vinculados a filtros, la coincidencia literal de nombres y la autorización por cuenta impiden omitir coincidencias en páginas posteriores y divulgar metadatos.",
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
      "title": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos",
      "objective": "El usuario asigna nombres, guarda, enumera y vuelve a abrir proyectos con la escena completa intacta entre navegadores; las ediciones pendientes nunca se marcan como guardadas debido a una respuesta obsoleta.",
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
      "estimate_rationale": "Estimación no calibrada de 180 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "scope": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: los cambios se limitan a src/app/proyectos/page.tsx, src/components/proyectos/ListaProyectos.tsx y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "duration": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: estimación no calibrada del agente: 60 minutos de inspección, 60 de implementación o ejecución y 60 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "risk": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.31"
          ]
        },
        "coupling": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/Taller3D.tsx",
            "spec:SPEC.md#requirements",
            "task:T4.1",
            "task:T4.3",
            "task:T4.31"
          ]
        },
        "confidence": {
          "justification": "Implementar la lista de proyectos y el guardado de Taller con protección ante conflictos: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "El usuario asigna nombres, guarda, enumera y vuelve a abrir proyectos con la escena completa intacta entre navegadores; las ediciones pendientes nunca se marcan como guardadas debido a una respuesta obsoleta.",
        "Dos copias abiertas no pueden sobrescribirse silenciosamente: un 409 detiene el guardado automático, conserva la escena local no enviada y ofrece cargar la versión del servidor o guardar una nueva copia propia; el personal y los administradores leen originales ajenos sin acceso de escritura y pueden guardar una copia propia solo con taller.usar.",
        "El primer guardado con nombre es explícito y las ediciones posteriores se guardan automáticamente; la búsqueda de la lista de proyectos encuentra coincidencias autorizadas más allá de la primera página cargada, los cambios de filtro reinician la paginación y las respuestas obsoletas de consultas no pueden reemplazar los resultados actuales."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "El usuario asigna nombres, guarda, enumera y vuelve a abrir proyectos con la escena completa intacta entre navegadores; las ediciones pendientes nunca se marcan como guardadas debido a una respuesta obsoleta.",
          "category": "functional",
          "created_by": "T4.4"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "Dos copias abiertas no pueden sobrescribirse silenciosamente: un 409 detiene el guardado automático, conserva la escena local no enviada y ofrece cargar la versión del servidor o guardar una nueva copia propia; el personal y los administradores leen originales ajenos sin acceso de escritura y pueden guardar una copia propia solo con taller.usar.",
          "category": "functional",
          "created_by": "T4.4"
        },
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-cliente.ts",
          "purpose": "El primer guardado con nombre es explícito y las ediciones posteriores se guardan automáticamente; la búsqueda de la lista de proyectos encuentra coincidencias autorizadas más allá de la primera página cargada, los cambios de filtro reinician la paginación y las respuestas obsoletas de consultas no pueden reemplazar los resultados actuales.",
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
      "title": "Implementar la importación sin pérdida e idempotente de escenas heredadas",
      "objective": "A una cuenta con sesión iniciada y una escena heredada en el navegador se le ofrece una importación explícita; aceptarla crea exactamente un proyecto propio, incluso tras un reintento; rechazarla o que falle la validación conserva los datos locales sin procesar, y ninguna cuenta recibe automáticamente una escena heredada.",
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
      "estimate_rationale": "Estimación no calibrada de 110 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "scope": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: los cambios se limitan a src/lib/proyectos/importar-local.ts, src/components/proyectos/ImportarEscenaLocal.tsx y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "duration": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: estimación no calibrada del agente: 36 minutos de inspección, 36 de implementación o ejecución y 38 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "risk": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4"
          ]
        },
        "coupling": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.4",
            "task:T4.4"
          ]
        },
        "confidence": {
          "justification": "Implementar la importación sin pérdida e idempotente de escenas heredadas: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "A una cuenta con sesión iniciada y una escena heredada en el navegador se le ofrece una importación explícita; aceptarla crea exactamente un proyecto propio, incluso tras un reintento; rechazarla o que falle la validación conserva los datos locales sin procesar, y ninguna cuenta recibe automáticamente una escena heredada."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npx tsx scripts/test/test-proyectos-importacion.ts",
          "purpose": "A una cuenta con sesión iniciada y una escena heredada en el navegador se le ofrece una importación explícita; aceptarla crea exactamente un proyecto propio, incluso tras un reintento; rechazarla o que falle la validación conserva los datos locales sin procesar, y ninguna cuenta recibe automáticamente una escena heredada.",
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
      "title": "Implementar el entorno de integración de proyectos guardados en varios navegadores",
      "objective": "El entorno de pruebas de proyectos inicia puntos de entrada reales de Next contra un esquema de prueba aislado y ejecuta contextos de navegador autenticados e independientes para comprobar persistencia, denegación de acceso, conflictos e importación heredada.",
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
      "estimate_rationale": "Estimación no calibrada de 120 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: el límite inspeccionado requiere razonar sobre identidad entre solicitudes, concurrencia y restauración.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "scope": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: los cambios se limitan a scripts/test/test-integracion-proyectos.ts, scripts/test/test-harness-proyectos.ts y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "duration": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: estimación no calibrada del agente: 40 minutos de inspección, 40 de implementación o ejecución y 40 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "risk": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5"
          ]
        },
        "coupling": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "spec:SPEC.md#requirements",
            "task:T4.5",
            "task:T2.6",
            "task:T4.5"
          ]
        },
        "confidence": {
          "justification": "Implementar el entorno de integración de proyectos guardados en varios navegadores: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "scripts de package.json",
        "proyectos:document"
      ],
      "acceptance_criteria": [
        "El entorno de pruebas de proyectos inicia puntos de entrada reales de Next contra un esquema de prueba aislado y ejecuta contextos de navegador autenticados e independientes para comprobar persistencia, denegación de acceso, conflictos e importación heredada.",
        "El entorno de pruebas del navegador carga más de cincuenta proyectos y verifica una coincidencia más allá de la primera página, el filtrado autorizado por propietario, el reintento de la página siguiente y el rechazo de respuestas obsoletas de búsqueda, sin divulgar metadatos ajenos."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-harness",
          "purpose": "El entorno de pruebas de proyectos inicia puntos de entrada reales de Next contra un esquema de prueba aislado y ejecuta contextos de navegador autenticados e independientes para comprobar persistencia, denegación de acceso, conflictos e importación heredada.",
          "category": "functional",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-harness",
          "purpose": "El entorno de pruebas del navegador carga más de cincuenta proyectos y verifica una coincidencia más allá de la primera página, el filtrado autorizado por propietario, el reintento de la página siguiente y el rechazo de respuestas obsoletas de búsqueda, sin divulgar metadatos ajenos.",
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
      "title": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones",
      "objective": "Un usuario guarda, enumera, vuelve a abrir y continúa proyectos de Taller almacenados en su cuenta; los empleados y administradores abren los de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida.",
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
      "estimate_rationale": "Estimación no calibrada de 60 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: el límite inspeccionado requiere cambios acotados que usen operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "scope": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: los cambios se limitan a .evidence/REQ-021/SP-4.integration.json y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "duration": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: estimación no calibrada del agente: 20 minutos de inspección, 20 de implementación o ejecución y 20 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "risk": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6"
          ]
        },
        "coupling": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.6",
            "task:T4.6"
          ]
        },
        "confidence": {
          "justification": "Ejecutar el escenario de integración entre navegadores para proyectos e importaciones: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "Un usuario guarda, enumera, vuelve a abrir y continúa proyectos de Taller almacenados en su cuenta; los empleados y administradores abren los de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida.",
        "Una compilación de producción real supera las comprobaciones de persistencia entre contextos de navegador nuevos, denegación por cuenta, lectura y copia por parte del personal, conflicto entre guardados simultáneos, reintento de importación y aislamiento al cambiar de cuenta en la base de datos REQ-021."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-integracion",
          "purpose": "Un usuario guarda, enumera, vuelve a abrir y continúa proyectos de Taller almacenados en su cuenta; los empleados y administradores abren los de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida.",
          "category": "integration",
          "created_by": "T4.6",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run proyectos:test-integracion",
          "purpose": "Una compilación de producción real supera las comprobaciones de persistencia entre contextos de navegador nuevos, denegación por cuenta, lectura y copia por parte del personal, conflicto entre guardados simultáneos, reintento de importación y aislamiento al cambiar de cuenta en la base de datos REQ-021.",
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
      "title": "Revisar las interfaces renderizadas de proyectos e importación",
      "objective": "La lista de proyectos, los estados de guardado/sin conexión/conflicto, la vista ajena de solo lectura y el aviso de importación coinciden con proyectos@v1 aprobado en anchos de teléfono, tableta y escritorio, con el comportamiento del teclado y del foco verificado.",
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
      "estimate_rationale": "Estimación no calibrada de 75 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: el límite inspeccionado requiere cambios acotados que usen operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "scope": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: los cambios se limitan a .evidence/REQ-021/SP-4.visual.md, .evidence/REQ-021/SP-4.visual.findings.json y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "duration": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: estimación no calibrada del agente: 25 minutos de inspección, 25 de implementación o ejecución y 25 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "risk": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7"
          ]
        },
        "coupling": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.7",
            "task:T4.7"
          ]
        },
        "confidence": {
          "justification": "Revisar las interfaces renderizadas de proyectos e importación: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "La lista de proyectos, los estados de guardado/sin conexión/conflicto, la vista ajena de solo lectura y el aviso de importación coinciden con proyectos@v1 aprobado en anchos de teléfono, tableta y escritorio, con el comportamiento del teclado y del foco verificado."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json",
          "purpose": "La lista de proyectos, los estados de guardado/sin conexión/conflicto, la vista ajena de solo lectura y el aviso de importación coinciden con proyectos@v1 aprobado en anchos de teléfono, tableta y escritorio, con el comportamiento del teclado y del foco verificado.",
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
      "title": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones",
      "objective": "Una auditoría independiente de especificación y estándares de SP-4 no tiene hallazgos críticos o altos abiertos y verifica la propiedad, el control atómico de versiones, la idempotencia y conservación de importaciones, el registro de eliminación y el aislamiento al cambiar de cuenta.",
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
      "estimate_rationale": "Estimación no calibrada de 90 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: el límite inspeccionado requiere cambios acotados que usen operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "scope": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: los cambios se limitan a .evidence/REQ-021/SP-4.audit.md, .evidence/REQ-021/SP-4.findings.json y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "duration": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: estimación no calibrada del agente: 30 minutos de inspección, 30 de implementación o ejecución y 30 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "risk": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8"
          ]
        },
        "coupling": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.8",
            "task:T4.8"
          ]
        },
        "confidence": {
          "justification": "Auditar el aislamiento de proyectos, la concurrencia y la conservación de importaciones: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "Una auditoría independiente de especificación y estándares de SP-4 no tiene hallazgos críticos o altos abiertos y verifica la propiedad, el control atómico de versiones, la idempotencia y conservación de importaciones, el registro de eliminación y el aislamiento al cambiar de cuenta."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json",
          "purpose": "Una auditoría independiente de especificación y estándares de SP-4 no tiene hallazgos críticos o altos abiertos y verifica la propiedad, el control atómico de versiones, la idempotencia y conservación de importaciones, el registro de eliminación y el aislamiento al cambiar de cuenta.",
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
      "title": "Ejecutar el punto de control de almacenamiento y autorización de proyectos",
      "objective": "Antes del trabajo de UI, el servicio real de proyectos y las comprobaciones de la API superan las pruebas de rechazo atómico de escrituras obsoletas, aislamiento de cuentas, validación, claves de reintento de importación y la condición de carrera entre guardar un proyecto y eliminar la cuenta.",
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
      "estimate_rationale": "Estimación no calibrada de 35 minutos, incluida la verificación específica; no es una fecha límite.",
      "classification_evidence": {
        "complexity": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: el límite inspeccionado requiere cambios acotados que usen operaciones de dominio existentes.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "scope": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: los cambios se limitan a .evidence/REQ-021/SP-4.storage.json y los artefactos de verificación específica indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "duration": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: estimación no calibrada del agente: 11 minutos de inspección, 11 de implementación o ejecución y 13 de verificación específica y recopilación de evidencia.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "risk": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: un fallo podría hacer perder el trabajo guardado o exponer el documento de otra cuenta.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3"
          ]
        },
        "coupling": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: los prerrequisitos explícitos ordenan los archivos de escena compartidos y el registro de scripts del paquete; los consumidores usan los contratos versionados indicados.",
          "evidence": [
            "file:src/components/tres-d/guardado-escena.ts",
            "spec:SPEC.md#requirements",
            "task:T4.3",
            "task:T4.3"
          ]
        },
        "confidence": {
          "justification": "Ejecutar el punto de control de almacenamiento y autorización de proyectos: se inspeccionó el código existente; las respuestas de la ronda 9 ya definen el comportamiento del producto, mientras que la conciliación con Designer y la evidencia de integración futura siguen pendientes.",
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
        "Antes del trabajo de UI, el servicio real de proyectos y las comprobaciones de la API superan las pruebas de rechazo atómico de escrituras obsoletas, aislamiento de cuentas, validación, claves de reintento de importación y la condición de carrera entre guardar un proyecto y eliminar la cuenta."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run proyectos:test-checkpoint",
          "purpose": "Antes del trabajo de UI, el servicio real de proyectos y las comprobaciones de la API superan las pruebas de rechazo atómico de escrituras obsoletas, aislamiento de cuentas, validación, claves de reintento de importación y la condición de carrera entre guardar un proyecto y eliminar la cuenta.",
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

Lee SPEC.md y PLAN.md para conocer el comportamiento completo. No inventes flujos.
