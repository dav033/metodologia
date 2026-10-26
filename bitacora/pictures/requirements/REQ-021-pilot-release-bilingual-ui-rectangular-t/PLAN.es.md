---
req: REQ-021
status: draft
created: 2026-10-26
---
# Plan — Lanzamiento del piloto: cuentas y planes de acceso, trabajo guardado, gasto de IA, funciones esenciales del Taller, inglés, módulos y chat

Esquema (planificación colaborativa, fase Esqueleto). Solo hitos y subplanes; las tareas se definen subplan por subplan
con el propietario.

## Enfoque
Base de código: origin/main `a9f3d6e5` de `dav033/pictures` (Next 16 en Vercel, ai-api en Python en el VPS, Neon Postgres con
`scripts/migrations/NNN_*.sql` aplicados mediante `npm run rag:migrate`). El trabajo parte de origin/main en nuevos worktrees;
no se usa `~/dev/pictures`.

**Orden inverso desde el piloto (2026-11-16).** Las cuentas van primero porque los proyectos y las decoraciones guardados, el gasto
por usuario, los planes de acceso y el idioma por cuenta requieren una sesión iniciada. Los elementos del Taller que no requieren
cuentas (mesas rectangulares, Backing, exportación a Blender y módulos editables) se ejecutan en paralelo desde el primer día. El idioma
parte de su propia base en paralelo y es lo primero que se recorta.

| Hito | Fecha objetivo | ¿No se recorta? | Fecha límite de recorte (propietario, ronda 4) |
|---|---|---|---|
| M1 — Cuentas, planes de acceso y funciones esenciales del Taller | 2026-11-01 | sí | — |
| M2 — Trabajo guardado, gasto por usuario y herramientas del chat | 2026-11-07 | sí | — |
| M3 — Inglés / español | 2026-11-09 | no (primer recorte) | 2026-11-09: solo se publica SP-8 (Taller 3D y navegación) |
| M4 — Módulos editables y chat → 3D | 2026-11-12 | no (segundo y tercer recorte) | 2026-11-11: se recortan los módulos; 2026-11-12: se recortan las funciones del chat más allá de la división y la confiabilidad |
| M5 — Lanzamiento del piloto | 2026-11-16 | sí | — |

**Dependencias.** SP-1 (cuentas) → SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. SP-4 (identidad del proyecto) → SP-6 y SP-12.
SP-6 (etiquetado del gasto) → SP-7. SP-8 (mecanismo de idioma) → SP-9, SP-10. SP-7 (herramientas del chat, explorador de decoraciones) →
SP-10, SP-12. SP-3 y SP-11 no dependen de nada. SP-13 integra todos los subplanes publicados.

**Viabilidad, en términos claros.** Tamaño aproximado: unas 70 tareas para toda la SPEC y unas 45 para la parte que no se recorta (SP-1 a SP-7 y
SP-13). El tiempo de los agentes no es el límite; sí lo son las esperas: los reintentos, los límites de uso y las pruebas del propietario por subplan (menos de 24 h,
D-131). Solo es viable si el planificador ejecuta dos o más subplanes a la vez y los reintentos son pocos. Si M1 se retrasa más allá del
2026-11-03, se aplican las fechas de recorte acordadas; el trabajo que no se recorta nunca se sacrifica por el idioma, los módulos o el chat→3D.

**Seguridad.** SP-1 (identidad, sesiones, permisos, aplicación en el servidor, indicador local y primer administrador) es su
propio subplan y tiene su propia auditoría; SP-4 verifica que un usuario solo pueda acceder a sus propios proyectos.

Fuera de este plan: espacio 3D, exportación a Illustrator/vectorial y límites de gasto de IA (D-072).

### M1 — Cuentas, planes de acceso y funciones esenciales del Taller
Las personas reales inician sesión con su propia cuenta por invitación y cada una accede exactamente a lo que permite su rol o plan de acceso; APP_PASSWORD compartida ya no permite abrir la aplicación; las mesas, Backing y el archivo de Blender funcionan en el Taller.

- **SP-1 — Cuentas, sesiones y permisos aplicados en el servidor**: Las cuentas por invitación, con contraseñas cifradas mediante hash y sesiones de servidor revocables, reemplazan APP_PASSWORD compartida; cada página y API del piloto comprueba en el servidor el permiso requerido; los roles y los tres planes de acceso son conjuntos de permisos; el indicador local de acceso sin restricciones no se puede habilitar en producción; el primer administrador se crea mediante un comando de ejecución única. Cubre R1, R2, R3, R16.
- **SP-2 — Pantallas de inicio de sesión, invitación y administración** (UI: `cuentas-admin@v1`): Una persona inicia sesión con correo electrónico y contraseña, activa un enlace de invitación y acepta el aviso de tratamiento de datos; un administrador invita a personas, asigna un rol o plan de acceso, crea roles al elegir permisos y desactiva o elimina cuentas. Cubre R1, R3, R16.
- **SP-3 — Funciones esenciales del Taller: mesas rectangulares, Backing y exportación a Blender** (UI: `taller-esenciales@v1`): Un usuario agrega y edita una mesa rectangular con sus dimensiones y sillas, y la lista de compras lo refleja; el catálogo y el Taller muestran una categoría Backing que incluye todos los artículos para fiestas existentes; el archivo GLB exportado se abre en Blender con la misma distribución, las dimensiones en metros y los colores. Cubre R9, R10, R11.

### M2 — Trabajo guardado, gasto por usuario y herramientas del chat
Cada usuario con sesión iniciada guarda y vuelve a abrir proyectos y decoraciones desde cualquier navegador; cada llamada de IA con costo se atribuye a un usuario y una sesión; y el chat asistido consta de tres herramientas independientes cuyo acceso depende del plan.

- **SP-4 — Proyectos guardados** (UI: `proyectos@v1`): Un usuario guarda, enumera, vuelve a abrir y continúa proyectos del Taller almacenados en su cuenta; los empleados y administradores pueden abrir los proyectos de cualquier persona; al guardar de nuevo nunca se sobrescribe silenciosamente una versión anterior; al iniciar sesión por primera vez se ofrece importar las escenas guardadas en el navegador, sin pérdida de datos. Cubre R6, R7.
- **SP-5 — Decoraciones guardadas** (UI: `decoraciones@v1`): Un usuario guarda con un nombre una selección o composición de la escena en su biblioteca personal del servidor y la coloca en cualquiera de sus proyectos; se importan los elementos que ya están en la biblioteca propia del navegador. Cubre R8.
- **SP-6 — Gasto de IA por usuario y sesión** (UI: `gasto-ia@v1`): Cada llamada de IA con costo (Next y ai-api) se guarda con el usuario, la sesión de inicio de sesión, el elemento de trabajo (proyecto o conversación), la herramienta y el tipo (texto o imagen); los empleados y administradores ven los totales agrupados por proyecto o conversación y filtrados por usuario y tipo; un usuario no puede abrir esta vista. Cubre R4, R5.
- **SP-7 — Chat asistido como tres herramientas y explorador de decoraciones** (UI: `herramientas-chat@v1`): El chat asistido se convierte en un contador de globos, una calculadora de costos y un chat normal, cada uno con sus propias instrucciones y medición de gasto independiente, sin inventar cantidades ni precios; un explorador de decoraciones prediseñadas muestra las decoraciones 3D existentes; cada herramienta solo está disponible con su plan de acceso. Cubre R13, R16.

### M3 — Inglés / español
La interfaz usa el idioma del navegador durante la primera visita y luego la elección de la cuenta; el Taller 3D y la navegación se traducen completamente primero, seguidos por los textos de los productos, las pantallas restantes y las respuestas de IA.

- **SP-8 — Selector de idioma, Taller 3D y navegación en inglés** (UI: `idioma-taller@v1`): Un mecanismo de idioma con detección en la primera visita, un selector que recuerda la elección por cuenta y todas las cadenas del Taller 3D y la navegación en ambos idiomas. Cubre R12.
- **SP-9 — Textos de productos y decoraciones en inglés** (UI: `textos-producto@v1`): Los nombres y las descripciones en inglés de cada producto y decoración se generan una vez a partir del original en español, se almacenan y se muestran cuando el idioma es inglés, con el texto en español como alternativa; un administrador puede corregirlos. Cubre R12.
- **SP-10 — Pantallas restantes y respuestas de IA en inglés** (UI: `idioma-resto@v1`): Las pantallas de las herramientas del chat, el catálogo, la administración, el gasto y las estadísticas están completamente en inglés; la IA de la escena y las herramientas del chat responden en el idioma del usuario. Cubre R12.

### M4 — Módulos editables y chat → 3D
Los usuarios editan módulos y cuartetos más allá de sus colores, y el chat normal recomienda decoraciones 3D prediseñadas que se abren en el Taller.

- **SP-11 — Módulos y cuartetos editables** (UI: `modulos-editables@v1`): Un usuario edita un módulo o cuarteto de la escena más allá de sus colores (las ediciones exactas se acuerdan con el propietario en este subplan) y se actualizan las cantidades y la lista de compras. Cubre R15.
- **SP-12 — El chat normal recomienda decoraciones 3D prediseñadas** (UI: `chat-a-3d@v1`): En dos o tres mensajes, el chat normal define la necesidad y recomienda decoraciones 3D existentes que se abren en el Taller 3D como un nuevo proyecto, usando el catálogo y el motor reales. Cubre R13.

### M5 — Lanzamiento del piloto
El piloto funciona en producción con cuentas reales: existe el primer administrador, se publica cada subplan incluido, se supera una prueba de humo en producción y se enumeran los elementos recortados.

- **SP-13 — Lanzamiento del piloto en producción**: Cada subplan aprobado se publica en producción con sus migraciones, se crea el primer administrador, se supera en producción un flujo de extremo a extremo (invitar → activar → guardar proyecto y decoración → aparece el gasto → exportar GLB) y se registra la lista de recortes. Cubre R14.
