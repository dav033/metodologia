# Requisitos de comportamiento compartidos

{
  "id": "SP-2",
  "title": "Pantallas de inicio de sesión, invitaciones y administración",
  "outcome": "Una persona inicia sesión con correo electrónico y contraseña, activa un enlace de invitación y acepta el aviso de datos; un administrador invita a personas, asigna un rol o plan de acceso, crea roles al elegir permisos y desactiva o elimina cuentas.",
  "covers": [
    "R1",
    "R3",
    "R16"
  ],
  "criteria": [
    "Generar un nuevo enlace de invitación o restablecimiento para una cuenta invalida todos los enlaces anteriores sin usar del mismo tipo para esa cuenta, y se rechaza un rol personalizado sin permisos con ROL_SIN_PERMISOS.",
    "Se rechaza la eliminación de una cuenta que sea propietaria de alguna fila de una tabla registrada como trabajo de cuenta con CUENTA_CON_TRABAJO y no se modifica nada; al eliminar una cuenta sin trabajo guardado, esta se elimina y se conservan sus filas de gasto de IA sin datos personales.",
    "En /login, una persona inicia sesión con correo electrónico y contraseña; una contraseña incorrecta, un correo desconocido, una cuenta desactivada y un correo bloqueado muestran el mismo mensaje, que siempre indica que después de varios intentos fallidos se debe esperar quince minutos, y, si el inicio de sesión es exitoso, se redirige a la página solicitada o a la primera área permitida para el rol, o a Mi cuenta si no tiene acceso a ninguna de ellas.",
    "Al abrir un enlace de invitación, se muestran el nombre y el correo electrónico de la persona invitada, se solicita dos veces una contraseña de al menos ocho caracteres y se muestra el aviso de datos en el idioma del navegador con una casilla para aceptarlo; la activación no es posible sin aceptarlo y, después de activar la cuenta, la persona inicia sesión y llega a la primera herramienta permitida para su rol; un enlace usado o vencido muestra un mensaje para solicitar uno nuevo al administrador.",
    "Cuando cambia la versión del aviso, una persona con sesión iniciada debe aceptar la nueva versión antes de que se abra cualquier otra página.",
    "Todas las páginas con sesión iniciada muestran un menú de cuenta con el nombre y el rol de la persona, Mi cuenta y la opción para cerrar sesión; en Mi cuenta, para cambiar la contraseña se solicita la actual.",
    "Un administrador invita a una persona indicando su nombre, correo electrónico, empresa opcional y rol, y obtiene el enlace de un solo uso una única vez con un botón para copiarlo; se rechaza una dirección de correo electrónico ya registrada con un mensaje claro.",
    "Un administrador cambia el rol de una cuenta, la desactiva y reactiva, genera un enlace de restablecimiento y elimina una cuenta sin trabajo guardado después de escribir su correo electrónico; la pantalla explica por qué no se puede eliminar al último administrador o una cuenta con trabajo guardado.",
    "Un administrador crea y edita un rol personalizado por nombre y casillas de permisos agrupadas por herramienta, ve los cinco roles del sistema en modo de solo lectura con sus permisos y no puede eliminar un rol que aún tenga cuentas asignadas.",
    "Las API de administración de cuentas y roles rechazan con 403 a quienes no tengan el permiso users o roles y solo aceptan solicitudes del mismo origen con cuerpos validados.",
    "El aviso de datos existe en español e inglés e incluye un número de versión; sus marcadores de posición entre corchetes siguen identificados para revisión legal, y al aceptarlo se guardan la versión y la fecha en la cuenta.",
    "En una compilación de producción conectada a la base de datos de prueba de REQ-021, un administrador invita desde las pantallas a una persona con Plan 2; la persona activa el enlace en otro navegador, acepta el aviso, inicia sesión y accede al chat y a la herramienta de costos, pero no al Taller 3D; después de que el administrador la cambie a Plan 3, su siguiente solicitud abre el Taller.",
    "Las pantallas renderizadas de inicio de sesión, activación, cuenta y administración coinciden con el contrato aprobado cuentas-admin@v1 en los anchos de teléfono, tableta y escritorio, y cada hallazgo queda registrado con la tarea que debe rehacerse en el registro visual de SP-2.",
    "Una auditoría independiente de SP-2 registra cada defecto confirmado con la tarea que debe rehacerse en el registro de hallazgos de SP-2, y el registro no tiene hallazgos críticos ni altos abiertos."
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
      "title": "Copiar al repositorio el contrato cuentas-admin@v1 aprobado por el propietario",
      "objective": "El repositorio contiene el contrato visual exacto, aprobado por el propietario, para las pantallas de inicio de sesión, activación, cuenta y administración antes de construir cualquiera de ellas.",
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
      "estimate_rationale": "Estimación del agente en minutos: 10 para copiar el archivo fijado y comprobar su hash; el diseño se completa durante la planificación.",
      "classification_evidence": {
        "complexity": {
          "justification": "Copiar byte por byte un archivo ya aprobado no requiere tomar decisiones de diseño.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "scope": {
          "justification": "Se agrega un archivo Markdown en design/contracts.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.4"
          ]
        },
        "duration": {
          "justification": "Diez minutos para copiar el archivo y comparar el hash.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind design -> status unknown, no comparable samples",
            "task:T2.5"
          ]
        },
        "risk": {
          "justification": "Una copia incorrecta solo bloquea las tareas de interfaz mediante la comprobación del hash, y es fácil rehacerla.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "coupling": {
          "justification": "Todas las tareas de interfaz de SP-2 leen este contrato, por lo que deben esperar a que esté disponible.",
          "evidence": [
            "task:T2.3",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "El flujo copia el borrador fijado en el plan, un paso completamente conocido y sin preguntas pendientes.",
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
        "El contrato cuentas-admin@v1 aprobado por el propietario se copia byte por byte en design/contracts/cuentas-admin@v1.md."
      ],
      "verification": [
        {
          "type": "command",
          "value": "test -s design/contracts/cuentas-admin@v1.md",
          "purpose": "El contrato cuentas-admin@v1 aprobado por el propietario se copia byte por byte en design/contracts/cuentas-admin@v1.md.",
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
      "title": "API de cuentas: activación, restablecimiento, aceptación del aviso, cambio de contraseña propia y administración de cuentas y roles",
      "objective": "Las rutas del servidor ofrecen activación, restablecimiento, aceptación del aviso y cambio de contraseña propia a las personas titulares, y limitan la administración de cuentas y roles a los administradores; todo se basa en el servicio de SP-1.",
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
      "estimate_rationale": "Estimación del agente en minutos: 15 para el módulo del aviso + 35 para las API de titulares + 40 para las API de administración + 30 para las pruebas = 120.",
      "classification_evidence": {
        "complexity": {
          "justification": "Son rutas delgadas sobre el servicio de SP-1, pero los tokens, las comprobaciones de mismo origen y la separación de permisos deben ser exactos.",
          "evidence": [
            "file:src/lib/auth/request.ts",
            "task:T1.3"
          ]
        },
        "scope": {
          "justification": "Ocho archivos de rutas, el módulo del aviso, entradas del mapa y un archivo de pruebas.",
          "evidence": [
            "file:src/app/api/login/route.ts",
            "task:T1.2"
          ]
        },
        "duration": {
          "justification": "Quince minutos para el aviso, treinta y cinco para las API de titulares, cuarenta para las API de administración y treinta para las pruebas suman ciento veinte minutos.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "task:T1.3"
          ]
        },
        "risk": {
          "justification": "Estas rutas crean administradores y establecen contraseñas; una brecha permitiría que cualquiera tomara el control del piloto.",
          "evidence": [
            "spec:SPEC.md#constraints",
            "task:T1.4"
          ]
        },
        "coupling": {
          "justification": "Consume los contratos contract:account-service y contract:session-guard de SP-1 y alimenta todas las pantallas de SP-2.",
          "evidence": [
            "task:T1.4",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "Se leyeron los patrones de rutas existentes y la API del servicio quedó fijada en T1.3, aunque los esquemas de zod son nuevos.",
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
        "Las API de activación, restablecimiento y aceptación del aviso solo aceptan un token válido sin usar o una sesión iniciada, validan todos los cuerpos, responden a un enlace usado o vencido con LINK_INVALIDO sin indicar cuál es el caso, y una activación exitosa inicia una sesión de inmediato.",
        "Las API de administración de cuentas y roles rechazan con 403 a quienes no tengan el permiso users o roles y solo aceptan solicitudes del mismo origen con cuerpos validados.",
        "Generar un nuevo enlace de invitación o restablecimiento para una cuenta invalida todos los enlaces anteriores sin usar del mismo tipo para esa cuenta, y se rechaza un rol personalizado sin permisos con ROL_SIN_PERMISOS.",
        "Para cambiar la propia contraseña se requiere la contraseña actual; se terminan todas las sesiones de esa cuenta y se vuelve a iniciar sesión en el navegador solicitante con una sesión nueva.",
        "El aviso de datos existe en español e inglés e incluye un número de versión; sus marcadores de posición entre corchetes siguen identificados para revisión legal, y al aceptarlo se guardan la versión y la fecha en la cuenta.",
        "Se rechaza la eliminación de una cuenta que sea propietaria de alguna fila de una tabla registrada como trabajo de cuenta con CUENTA_CON_TRABAJO y no se modifica nada; al eliminar una cuenta sin trabajo guardado, esta se elimina y se conservan sus filas de gasto de IA sin datos personales."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=enlaces",
          "purpose": "Las API de activación, restablecimiento y aceptación del aviso solo aceptan un token válido sin usar o una sesión iniciada, validan todos los cuerpos, responden a un enlace usado o vencido con LINK_INVALIDO sin indicar cuál es el caso, y una activación exitosa inicia una sesión de inmediato.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=admin",
          "purpose": "Las API de administración de cuentas y roles rechazan con 403 a quienes no tengan el permiso users o roles y solo aceptan solicitudes del mismo origen con cuerpos validados.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=regenerar",
          "purpose": "Generar un nuevo enlace de invitación o restablecimiento para una cuenta invalida todos los enlaces anteriores sin usar del mismo tipo para esa cuenta, y se rechaza un rol personalizado sin permisos con ROL_SIN_PERMISOS.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=mi-cuenta",
          "purpose": "Para cambiar la propia contraseña se requiere la contraseña actual; se terminan todas las sesiones de esa cuenta y se vuelve a iniciar sesión en el navegador solicitante con una sesión nueva.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=aviso",
          "purpose": "El aviso de datos existe en español e inglés e incluye un número de versión; sus marcadores de posición entre corchetes siguen identificados para revisión legal, y al aceptarlo se guardan la versión y la fecha en la cuenta.",
          "category": "functional",
          "created_by": "T2.2",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-api -- --test-name-pattern=borrar",
          "purpose": "Se rechaza la eliminación de una cuenta que sea propietaria de alguna fila de una tabla registrada como trabajo de cuenta con CUENTA_CON_TRABAJO y no se modifica nada; al eliminar una cuenta sin trabajo guardado, esta se elimina y se conservan sus filas de gasto de IA sin datos personales.",
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
      "title": "Pantallas de inicio de sesión, activación de invitación, restablecimiento de contraseña y nueva aceptación del aviso",
      "objective": "Una persona inicia sesión, activa una invitación aceptando el aviso de datos, restablece una contraseña mediante un enlace del administrador y vuelve a aceptar una versión nueva del aviso, con los estados definidos en el contrato.",
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
      "estimate_rationale": "Estimación del agente en minutos: 30 para el inicio de sesión + 45 para la activación con el aviso + 20 para el restablecimiento + 20 para la redirección de nueva aceptación + 35 para las pruebas de renderizado = 150.",
      "classification_evidence": {
        "complexity": {
          "justification": "Cuatro pantallas con estados de error, bloqueo, vencimiento y carga, además de una redirección del proxy para volver a aceptar el aviso.",
          "evidence": [
            "file:src/app/login/page.tsx",
            "file:src/proxy.ts"
          ]
        },
        "scope": {
          "justification": "Cuatro páginas, tres componentes compartidos y una regla del proxy, verificables de extremo a extremo.",
          "evidence": [
            "file:src/app/login/page.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Treinta, cuarenta y cinco, veinte, veinte y treinta y cinco minutos suman ciento cincuenta.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/app/login/page.tsx"
          ]
        },
        "risk": {
          "justification": "Si el inicio de sesión o la activación fallan, todos los usuarios del piloto quedan fuera desde el primer día.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.6"
          ]
        },
        "coupling": {
          "justification": "Modifica src/proxy.ts después de T1.4 y comparte contract:session-guard con las demás tareas de interfaz.",
          "evidence": [
            "task:T1.4",
            "task:T2.4"
          ]
        },
        "confidence": {
          "justification": "Se leyó la página de inicio de sesión actual; aún no se han redactado los estados del contrato.",
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
        "En /login, una persona inicia sesión con correo electrónico y contraseña; una contraseña incorrecta, un correo desconocido, una cuenta desactivada y un correo bloqueado muestran el mismo mensaje, que siempre indica que después de varios intentos fallidos se debe esperar quince minutos, y, si el inicio de sesión es exitoso, se redirige a la página solicitada o a la primera área permitida para el rol, o a Mi cuenta si no tiene acceso a ninguna de ellas.",
        "Al abrir un enlace de invitación, se muestran el nombre y el correo electrónico de la persona invitada, se solicita dos veces una contraseña de al menos ocho caracteres y se muestra el aviso de datos en el idioma del navegador con una casilla para aceptarlo; la activación no es posible sin aceptarlo y, después de activar la cuenta, la persona inicia sesión y llega a la primera herramienta permitida para su rol; un enlace usado o vencido muestra un mensaje para solicitar uno nuevo al administrador.",
        "Al abrir un enlace de restablecimiento, la persona puede establecer una contraseña nueva y luego iniciar sesión; un enlace usado o vencido muestra el mismo mensaje que una invitación no válida.",
        "Cuando cambia la versión del aviso, una persona con sesión iniciada debe aceptar la nueva versión antes de que se abra cualquier otra página."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo ingreso",
          "purpose": "En /login, una persona inicia sesión con correo electrónico y contraseña; una contraseña incorrecta, un correo desconocido, una cuenta desactivada y un correo bloqueado muestran el mismo mensaje, que siempre indica que después de varios intentos fallidos se debe esperar quince minutos, y, si el inicio de sesión es exitoso, se redirige a la página solicitada o a la primera área permitida para el rol, o a Mi cuenta si no tiene acceso a ninguna de ellas.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo activacion",
          "purpose": "Al abrir un enlace de invitación, se muestran el nombre y el correo electrónico de la persona invitada, se solicita dos veces una contraseña de al menos ocho caracteres y se muestra el aviso de datos en el idioma del navegador con una casilla para aceptarlo; la activación no es posible sin aceptarlo y, después de activar la cuenta, la persona inicia sesión y llega a la primera herramienta permitida para su rol; un enlace usado o vencido muestra un mensaje para solicitar uno nuevo al administrador.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo restablecer",
          "purpose": "Al abrir un enlace de restablecimiento, la persona puede establecer una contraseña nueva y luego iniciar sesión; un enlace usado o vencido muestra el mismo mensaje que una invitación no válida.",
          "category": "functional",
          "created_by": "T2.3",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-acceso -- --solo aviso",
          "purpose": "Cuando cambia la versión del aviso, una persona con sesión iniciada debe aceptar la nueva versión antes de que se abra cualquier otra página.",
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
      "title": "Menú de cuenta en todas las páginas con sesión iniciada y página Mi cuenta",
      "objective": "Todas las personas con sesión iniciada ven quiénes son y cuál es su rol, cierran sesión y cambian su propia contraseña desde Mi cuenta.",
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
      "estimate_rationale": "Estimación del agente en minutos: 30 para el menú en el diseño raíz + 25 para Mi cuenta + 20 para las pruebas = 75.",
      "classification_evidence": {
        "complexity": {
          "justification": "La aplicación no tiene navegación compartida, así que el menú debe adaptarse a páginas tan distintas como el chat y el Taller.",
          "evidence": [
            "file:src/app/layout.tsx",
            "file:src/app/page.tsx"
          ]
        },
        "scope": {
          "justification": "Un componente de menú en el diseño raíz, una página y una prueba.",
          "evidence": [
            "file:src/app/layout.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Treinta minutos para el menú, veinticinco para la página y veinte para las pruebas: setenta y cinco minutos.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/app/layout.tsx"
          ]
        },
        "risk": {
          "justification": "Un cambio en el diseño puede superponerse a la barra de herramientas del Taller o al área de redacción del chat en teléfonos.",
          "evidence": [
            "file:src/app/layout.tsx",
            "spec:SPEC.md#ui--design-contract-optional"
          ]
        },
        "coupling": {
          "justification": "Comparte el diseño raíz con el trabajo posterior de idiomas y lee contract:session-guard.",
          "evidence": [
            "task:T1.4",
            "task:T2.3"
          ]
        },
        "confidence": {
          "justification": "Se leyó el diseño raíz; aún no se ha definido en el contrato dónde se ubicará el menú.",
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
        "Todas las páginas con sesión iniciada muestran un menú de cuenta con el nombre y el rol de la persona, Mi cuenta y la opción para cerrar sesión; en Mi cuenta, para cambiar la contraseña se solicita la actual."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-mi-cuenta",
          "purpose": "Todas las páginas con sesión iniciada muestran un menú de cuenta con el nombre y el rol de la persona, Mi cuenta y la opción para cerrar sesión; en Mi cuenta, para cambiar la contraseña se solicita la actual.",
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
      "title": "Pantallas de administración: lista de cuentas, invitaciones, acciones de cuenta y editor de roles",
      "objective": "Un administrador gestiona todas las cuentas y los roles personalizados desde dos pantallas que explican exactamente qué hará cada acción y por qué se rechaza.",
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
      "estimate_rationale": "Estimación del agente en minutos: 60 para la lista de cuentas con búsqueda y filtros + 35 para el diálogo de invitación + 35 para las acciones de cuenta + 30 para el editor de roles + 20 para las pruebas = 180.",
      "classification_evidence": {
        "complexity": {
          "justification": "Varios diálogos con confirmaciones, motivos de rechazo y un enlace que se muestra una sola vez requieren gestionar cuidadosamente los estados.",
          "evidence": [
            "file:src/components/admin/AdminTabs.tsx",
            "task:T2.2"
          ]
        },
        "scope": {
          "justification": "Dos páginas y cinco componentes, además de sus pruebas: una funcionalidad completa de extremo a extremo.",
          "evidence": [
            "file:src/components/admin/AdminTabs.tsx",
            "task:T2.2"
          ]
        },
        "duration": {
          "justification": "Sesenta, treinta y cinco, treinta y cinco, treinta y veinte minutos suman ciento ochenta.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind implement -> status unknown, no comparable samples",
            "file:src/components/admin/AdminTabs.tsx"
          ]
        },
        "risk": {
          "justification": "Un botón de acción incorrecto elimina la cuenta de una persona real o cambia su acceso.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.2"
          ]
        },
        "coupling": {
          "justification": "Lee contract:permission-map para las casillas de permisos y llama a las API de T2.2.",
          "evidence": [
            "task:T1.2",
            "task:T2.2"
          ]
        },
        "confidence": {
          "justification": "Se leyeron las pestañas de administración existentes; la densidad de la lista y los diálogos dependen del contrato.",
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
        "Un administrador ve todas las cuentas con nombre, correo electrónico, empresa, rol, estado y último acceso; busca por nombre o correo electrónico y filtra por rol y estado.",
        "Un administrador invita a una persona indicando su nombre, correo electrónico, empresa opcional y rol, y obtiene el enlace de un solo uso una única vez con un botón para copiarlo; se rechaza una dirección de correo electrónico ya registrada con un mensaje claro.",
        "Un administrador cambia el rol de una cuenta, la desactiva y reactiva, genera un enlace de restablecimiento y elimina una cuenta sin trabajo guardado después de escribir su correo electrónico; la pantalla explica por qué no se puede eliminar al último administrador o una cuenta con trabajo guardado.",
        "Un administrador crea y edita un rol personalizado por nombre y casillas de permisos agrupadas por herramienta, ve los cinco roles del sistema en modo de solo lectura con sus permisos y no puede eliminar un rol que aún tenga cuentas asignadas."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo lista",
          "purpose": "Un administrador ve todas las cuentas con nombre, correo electrónico, empresa, rol, estado y último acceso; busca por nombre o correo electrónico y filtra por rol y estado.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo invitar",
          "purpose": "Un administrador invita a una persona indicando su nombre, correo electrónico, empresa opcional y rol, y obtiene el enlace de un solo uso una única vez con un botón para copiarlo; se rechaza una dirección de correo electrónico ya registrada con un mensaje claro.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo acciones",
          "purpose": "Un administrador cambia el rol de una cuenta, la desactiva y reactiva, genera un enlace de restablecimiento y elimina una cuenta sin trabajo guardado después de escribir su correo electrónico; la pantalla explica por qué no se puede eliminar al último administrador o una cuenta con trabajo guardado.",
          "category": "functional",
          "created_by": "T2.5",
          "requires": [
            "PICTURES_REQ021_DATABASE_URL"
          ]
        },
        {
          "type": "command",
          "value": "npm run cuentas:test-ui-admin -- --solo roles",
          "purpose": "Un administrador crea y edita un rol personalizado por nombre y casillas de permisos agrupadas por herramienta, ve los cinco roles del sistema en modo de solo lectura con sus permisos y no puede eliminar un rol que aún tenga cuentas asignadas.",
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
      "title": "Prueba de extremo a extremo en navegador: invitar, activar, iniciar sesión y cambiar el plan en una compilación de producción",
      "objective": "Dos navegadores reales conectados mediante next start demuestran el flujo completo desde la invitación hasta el acceso y que un cambio de plan surte efecto en la siguiente solicitud.",
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
      "estimate_rationale": "Estimación del agente en minutos: 15 para la compilación + 50 para el flujo de Playwright con dos contextos + 25 para las evidencias y la limpieza = 90.",
      "classification_evidence": {
        "complexity": {
          "justification": "Dos contextos de navegador, un enlace copiado y un cambio de rol entre solicitudes requieren una secuencia cuidadosa.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "task:T2.5"
          ]
        },
        "scope": {
          "justification": "Un script de Playwright y su archivo de evidencias.",
          "evidence": [
            "file:scripts/e2e/humo/configuracion.ts",
            "task:T2.3"
          ]
        },
        "duration": {
          "justification": "Quince minutos para la compilación, cincuenta para el flujo y veinticinco para las evidencias suman noventa minutos.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind test -> status unknown, no comparable samples",
            "file:package.json"
          ]
        },
        "risk": {
          "justification": "Es la última barrera antes de la auditoría para las pantallas que ven primero los usuarios reales.",
          "evidence": [
            "spec:SPEC.md#requirements",
            "task:T2.8"
          ]
        },
        "coupling": {
          "justification": "Prueba en conjunto todas las tareas de SP-2 y los contratos de SP-1.",
          "evidence": [
            "task:T2.3",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "Playwright ya es una dependencia y la prueba de humo muestra cómo se utiliza; no se ha medido el tiempo de compilación.",
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
        "En una compilación de producción conectada a la base de datos de prueba de REQ-021, un administrador invita desde las pantallas a una persona con Plan 2; la persona activa el enlace en otro navegador, acepta el aviso, inicia sesión y accede al chat y a la herramienta de costos, pero no al Taller 3D; después de que el administrador la cambie a Plan 3, su siguiente solicitud abre el Taller."
      ],
      "verification": [
        {
          "type": "command",
          "value": "npm run cuentas:test-integracion-ui",
          "purpose": "En una compilación de producción conectada a la base de datos de prueba de REQ-021, un administrador invita desde las pantallas a una persona con Plan 2; la persona activa el enlace en otro navegador, acepta el aviso, inicia sesión y accede al chat y a la herramienta de costos, pero no al Taller 3D; después de que el administrador la cambie a Plan 3, su siguiente solicitud abre el Taller.",
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
      "title": "Revisión visual de SP-2 con respecto al contrato cuentas-admin@v1",
      "objective": "Una persona revisora nueva compara las pantallas renderizadas con el contrato aprobado en tres anchos y registra cada diferencia junto con la tarea que debe rehacerse.",
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
      "estimate_rationale": "Estimación del agente en minutos: 40 para capturas de pantalla y comparación de cinco pantallas en tres anchos + 20 para el registro = 60.",
      "classification_evidence": {
        "complexity": {
          "justification": "Comparar estados renderizados con un contrato escrito requiere criterio, pero no un diseño nuevo.",
          "evidence": [
            "task:T2.1",
            "task:T2.6"
          ]
        },
        "scope": {
          "justification": "Solo se escribe un informe y su registro.",
          "evidence": [
            "task:T2.6",
            "spec:SPEC.md#ui--design-contract-optional"
          ]
        },
        "duration": {
          "justification": "Cuarenta minutos para las capturas de pantalla y la comparación, y veinte para el registro: sesenta minutos.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind audit -> status unknown, no comparable samples",
            "task:T2.3"
          ]
        },
        "risk": {
          "justification": "Una diferencia que no se detecte llega a los usuarios del piloto como una primera pantalla confusa.",
          "evidence": [
            "spec:SPEC.md#ui--design-contract-optional",
            "task:T2.3"
          ]
        },
        "coupling": {
          "justification": "Su ledger:SP-2-visual puede devolver las tareas T2.3 a T2.5 para que se rehagan.",
          "evidence": [
            "task:T2.4",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "El alcance de las pantallas y el contrato está definido, por lo que la estimación se basa en tareas conocidas.",
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
        "Las pantallas renderizadas de inicio de sesión, activación, cuenta y administración coinciden con el contrato aprobado cuentas-admin@v1 en los anchos de teléfono, tableta y escritorio, y cada hallazgo queda registrado con la tarea que debe rehacerse en el registro visual de SP-2."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json",
          "purpose": "Las pantallas renderizadas de inicio de sesión, activación, cuenta y administración coinciden con el contrato aprobado cuentas-admin@v1 en los anchos de teléfono, tableta y escritorio, y cada hallazgo queda registrado con la tarea que debe rehacerse en el registro visual de SP-2.",
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
      "title": "Auditoría de SP-2: pantallas de cuenta, API de administración y aviso de datos",
      "objective": "Una revisión independiente de solo lectura confirma que SP-2 cumple con R1, R3 y R16, y registra cada defecto confirmado junto con la tarea que debe rehacerse en un registro de hallazgos bloqueante.",
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
      "estimate_rationale": "Estimación del agente en minutos: 30 para los permisos y tokens de las API de administración + 25 para revisar las pantallas con respecto a los criterios de aceptación + 20 para el registro = 75.",
      "classification_evidence": {
        "complexity": {
          "justification": "Verificar que cada acción de administración compruebe los permisos y que los enlaces nunca se filtren requiere una revisión de seguridad.",
          "evidence": [
            "task:T2.2",
            "spec:SPEC.md#constraints"
          ]
        },
        "scope": {
          "justification": "La auditoría solo escribe su informe y el registro.",
          "evidence": [
            "task:T2.7",
            "spec:SPEC.md#requirements"
          ]
        },
        "duration": {
          "justification": "Treinta, veinticinco y veinte minutos suman setenta y cinco.",
          "evidence": [
            "command:python3 /home/david/.claude/skills/metodologia/scripts/bitacora.py --project pictures plan-json history --kind audit -> status unknown, no comparable samples",
            "task:T2.2"
          ]
        },
        "risk": {
          "justification": "Un defecto que no se detecte permite que una persona no administradora gestione las cuentas de usuarios reales.",
          "evidence": [
            "spec:SPEC.md#constraints",
            "task:T2.2"
          ]
        },
        "coupling": {
          "justification": "Su ledger:SP-2 puede devolver las tareas T2.2 a T2.5 para que se rehagan.",
          "evidence": [
            "task:T2.2",
            "task:T2.5"
          ]
        },
        "confidence": {
          "justification": "El alcance se limita a una tarea de API y tres pantallas con pruebas.",
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
        "Una auditoría independiente de SP-2 registra cada defecto confirmado con la tarea que debe rehacerse en el registro de hallazgos de SP-2, y el registro no tiene hallazgos críticos ni altos abiertos."
      ],
      "verification": [
        {
          "type": "command",
          "value": "bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json",
          "purpose": "Una auditoría independiente de SP-2 registra cada defecto confirmado con la tarea que debe rehacerse en el registro de hallazgos de SP-2, y el registro no tiene hallazgos críticos ni altos abiertos.",
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

Lee SPEC.md y PLAN.md para conocer el comportamiento completo. No inventes flujos.
