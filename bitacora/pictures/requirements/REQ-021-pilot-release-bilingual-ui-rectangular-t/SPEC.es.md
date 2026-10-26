---
id: REQ-021
status: ready
created: 2026-10-26
track: deep
---
# REQ-021 — Lanzamiento piloto: interfaz bilingüe, mesas rectangulares, Backing, espacio 3D, roles de administración, gasto en IA, guardar proyectos y decoraciones, exportar a Blender/Illustrator, cuartetos y módulos editables

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problema y objetivo
Propietario (2026-10-26): tres semanas para lanzar Pictures en una versión de **producción piloto** (fecha objetivo: 2026-11-16). Lista preliminar, en sus
palabras, «a grandes rasgos»: inglés; mesas rectangulares; Backing; añadir un espacio en 3D; la posibilidad de crear
administradores que puedan crear roles; revisar los tokens; guardar proyectos; guardar decoraciones; exportar a Blender y Adobe
Illustrator; poder modificar cuartetos y módulos.

**Criterios de éxito:** el día del piloto, usuarios externos reales inician sesión con su propia cuenta, crean y guardan proyectos y decoraciones 3D, y los empleados y administradores consultan el gasto en IA por usuario y administran roles; los elementos de «Nunca recortar» están disponibles y el resto se entrega o se recorta en el orden acordado.

## Usuarios / actores / partes interesadas
- **Usuario** (real, externo): usa el taller 3D de globos; no tiene acceso al panel de gastos.
- **Empleado interno**: lo mismo, además del panel de tokens y gastos.
- **Administrador**: todo lo anterior, además de la gestión de usuarios y roles.
- Propietario: David.

## Alcance (incluido)
### US-1 (P1, Must) — Cuentas, roles y permisos
Como administrador, invito a usuarios externos reales y empleados internos, y creo roles seleccionando permisos, para que cada persona vea solo lo permitido por su rol.
**Criterios de aceptación:**
- Dado un administrador, cuando invita a una dirección de correo electrónico, esa persona puede establecer una contraseña e iniciar sesión; no hay registro abierto.
- Dados tres roles iniciales (usuario, empleado interno, administrador), cuando el administrador crea un rol y selecciona permisos, los usuarios con ese rol reciben exactamente esos permisos y ninguno adicional.
- Dado un usuario sin un permiso, cuando abre esa página o llama a esa API, el acceso se deniega en el servidor, no solo se oculta en la interfaz.
- Dado el inicio de sesión compartido anterior con `APP_PASSWORD`, cuando el piloto está disponible, este ya no concede acceso al piloto.
### US-2 (P1, Must) — Gasto en IA por usuario
Como empleado o administrador, consulto cuántos tokens y cuánto dinero ha consumido la IA, por usuario y sesión, desglosados por tipo (texto, generación de imágenes), principalmente en el Taller 3D.
**Criterios de aceptación:**
- Dada cualquier llamada de IA con costo realizada por un usuario con sesión iniciada, cuando se completa, sus tokens y costo estimado se guardan asociados a ese usuario y sesión.
- Dado un empleado o administrador, cuando abre la vista de gastos, ve los totales por sesión y tipo, y puede filtrar por usuario; un usuario normal no puede abrirla.
- Este plan no incluye límites ni bloqueos (propietario).
### US-3 (P1, Must) — Guardar proyectos
Como usuario, guardo, vuelvo a abrir y continúo mis proyectos 3D desde cualquier navegador.
**Criterios de aceptación:**
- Dado un usuario con sesión iniciada, cuando guarda, el proyecto se almacena en el servidor bajo su cuenta y se vuelve a abrir de forma idéntica.
- Dados empleados y administradores, cuando consultan la lista de proyectos, pueden abrir el proyecto de cualquier usuario; un usuario normal solo ve los suyos.
- Dadas escenas guardadas en el navegador (`taller3d:escena:v1`), cuando el usuario inicia sesión por primera vez, se le ofrece importarlas y no se pierde nada.
### US-4 (P1, Must) — Guardar decoraciones
Como usuario, guardo en mi biblioteca personal una composición creada en la escena y la reutilizo en otros proyectos.
**Criterios de aceptación:**
- Dada una selección o composición en la escena, cuando la guardo con un nombre, aparece en mi biblioteca y puedo colocarla en cualquiera de mis proyectos.
- La publicación en la biblioteca global queda fuera de este plan.
### US-5 (P1, Must) — Mesas rectangulares
Como usuario, creo y edito mesas rectangulares en el Taller 3D, con sillas, manualmente y mediante la IA.
**Criterios de aceptación:**
- Dada la interfaz del Taller, cuando añado una mesa rectangular, puedo elegir su tamaño y número de sillas, y la lista de compras se actualiza. (El motor ya lo admite; se debe verificar el flujo de la interfaz.)
### US-6 (P1, Must) — Exportar a Blender
Como usuario, exporto mi escena a un archivo que Blender abre con los elementos colocados correctamente.
**Criterios de aceptación:**
- Dada una escena, cuando la exporto a GLB, Blender la importa con la misma distribución, tamaños y colores; esto se verifica mediante una comprobación manual documentada y una prueba automatizada de la exportación.
### US-7 (P1, Must) — Categoría Backing
Como usuario, encuentro los artículos de fiesta (aros metálicos, pedestales, panel redondo, media luna, arcos chiara y similares) en una categoría del catálogo llamada Backing.
**Criterios de aceptación:**
- Dado el catálogo, cuando abro Backing, se muestran todos los artículos existentes de esos tipos y se pueden añadir a la escena; ningún artículo desaparece de su ubicación actual.
### US-8 (P2, Should) — Inglés / español en toda la aplicación
Como usuario, cambio entre inglés y español, detectados automáticamente según el navegador la primera vez, y todo cambia: la interfaz, las respuestas de la IA, los nombres y las descripciones de los productos.
**Criterios de aceptación:**
- Dada una primera visita con el navegador en inglés, cuando carga la aplicación, se muestra en inglés; el selector permite volver a cambiar el idioma y la elección se recuerda por cuenta.
- Dados los nombres y las descripciones de los productos, cuando el idioma es inglés, se muestra el texto en inglés generado una vez a partir del texto fuente en español; un administrador puede corregirlo.
- Dadas las conversaciones con la IA, cuando el idioma es inglés, responden en inglés.
- No queda ningún texto en español en las pantallas que el plan marque como terminadas; el plan especifica qué pantallas cubre (orden de recorte: primero el Taller 3D y la navegación).
### US-9 (P2, Should) — Módulos y cuartetos editables
Como usuario, modifico cuartetos y otros módulos en el Taller 3D, además de los colores (actualmente solo se pueden editar los colores).
**Criterios de aceptación:**
- Dado un módulo en la escena, cuando lo edito, el cambio se aplica a ese módulo y se actualizan las cantidades y la lista de compras. El Planner debe acordar con el propietario las modificaciones específicas (forma, separación, posiciones de los globos).
### US-10 (P2, Should) — Separación del chat asistido e integración chat↔3D
Como usuario, uso tres herramientas separadas en lugar de un solo chat: una calculadora de costos, un contador de globos y el chat «normal»; el chat y el taller 3D están conectados.
**Criterios de aceptación:**
- Dadas las tres herramientas, cuando abro cada una, cumple una función con sus propias instrucciones y el gasto se mide por separado.
- Dado el chat normal, cuando describo lo que necesito en dos o tres mensajes, define la necesidad y recomienda decoraciones 3D ya creadas que puedo abrir en el taller.
- El chat nunca inventa cantidades ni precios (usa el motor y el catálogo real).

## Fuera del alcance
- Espacio 3D (añadir o definir espacios en 3D): decisión del propietario, ronda 3: fuera de este plan.
- Para más adelante (acordado por el propietario el 2026-10-26): espacio 3D a partir de una foto del lugar; exportación vectorial para Illustrator.

## Requisitos
- R1. Cuando un administrador invita una dirección de correo electrónico, el sistema debe permitir que esa persona cree una contraseña e inicie sesión; no debe existir el registro abierto.
- R2. El sistema debe aplicar roles y permisos en el servidor para cada página y API del piloto.
- R3. Cuando un administrador crea un rol, el sistema debe permitirle elegir sus permisos de una lista definida; deben existir los tres roles iniciales.
- R4. Cuando se completa una llamada de IA con costo, el sistema debe guardar los tokens y el costo estimado asociados al usuario y la sesión.
- R5. Mientras la sesión esté iniciada como empleado o administrador, el sistema debe mostrar los totales de gasto por sesión, tipo y usuario.
- R6. Cuando un usuario guarda un proyecto, el sistema debe almacenarlo en el servidor bajo su cuenta; los empleados y administradores deben poder abrir cualquier proyecto.
- R7. Cuando un usuario inicia sesión por primera vez con escenas guardadas en el navegador, el sistema debe ofrecer importarlas sin pérdida de datos.
- R8. Cuando un usuario guarda una composición como decoración, el sistema debe agregarla a su biblioteca personal.
- R9. Cuando un usuario agrega una mesa rectangular, el sistema debe permitirle configurar sus dimensiones y sillas, y actualizar la lista de compras.
- R10. Cuando un usuario exporta a GLB, el sistema debe generar un archivo que Blender pueda abrir con la distribución, las dimensiones y los colores de la escena.
- R11. El catálogo debe tener una categoría Backing que incluya los artículos para fiestas existentes de esos tipos.
- R12. Cuando se cambia o detecta el idioma, el sistema debe mostrar la interfaz, las respuestas de IA y el texto de los productos en ese idioma.
- R13. El chat asistido debe dividirse en una calculadora de costos, un contador de globos y un chat normal; el chat normal debe conectarse con el Taller 3D.
- R14. Si alguno de R1–R16 no está terminado para su fecha límite, se debe aplicar el orden de recortes de Priorities; los elementos que nunca se recortan deben publicarse.
- R15. Cuando un usuario edita un módulo o cuarteto de la escena más allá de sus colores, el sistema debe aplicar la edición solo a ese módulo y actualizar las cantidades y la lista de compras.
- R16. Cuando un administrador asigna un plan de acceso a una cuenta externa, el sistema debe otorgar exactamente las herramientas de ese plan: el Plan 1, el chat asistido y el contador de globos; el Plan 2 agrega la calculadora de costos y el explorador de decoraciones prediseñadas; el Plan 3 agrega el Taller 3D.

## Contrato de interfaz / diseño (opcional)
<!-- Incluir cuando el requisito abarque una interfaz para usuarios. Registrar los usuarios, los flujos/vistas compatibles,
el sistema de diseño o la dirección visual existentes y las restricciones de accesibilidad pertinentes. El plan define
los subplanes de interfaz; Designer redacta un contrato versionado y el propietario aprueba cada versión antes de
implementar la interfaz. -->
- Alcance de la interfaz / usuarios: Taller 3D y pantallas de administración para usuarios externos reales, empleados y administradores.
- Dirección visual / sistema existente: diseño actual de la aplicación; Designer propone vistas de administración y gastos coherentes con este.
- Restricciones de accesibilidad o interacción: Designer las definirá para cada subplan.

## Casos límite y errores
- Se elimina a un usuario o pierde un permiso mientras tiene la sesión iniciada: el acceso finaliza en la siguiente solicitud.
- No se pueden importar escenas guardadas en el navegador que usan un esquema anterior: el usuario conserva el original y ve el motivo.
- Dos sesiones guardan el mismo proyecto: el guardado posterior no sobrescribe silenciosamente el anterior.
- La generación con IA falla a mitad del proceso: solo se registra el gasto correspondiente a lo facturado.
- Un producto todavía no tiene texto en inglés: se muestra el texto en español en lugar de dejar el campo vacío.

## Restricciones
- Next.js en Vercel, ai-api en Python en un VPS, Neon Postgres; migraciones en `scripts/migrations/`. El trabajo parte de `origin/main` en un worktree nuevo, nunca en el checkout con cambios locales `~/dev/pictures`.
- Seguridad: aplicación de roles en el servidor; contraseñas con hash; solo cuentas invitadas; datos personales de usuarios externos reales.
- Fecha límite aproximada: 2026-11-16 (producción piloto); plan dimensionado para tres semanas.

## Contrato de interfaz / diseño
_Si el alcance incluye un subplan de interfaz: identifica a sus usuarios y su tarea principal, la dirección visual, el sistema de diseño existente o las restricciones de marca, los estados y puntos de interrupción compatibles, y los requisitos de accesibilidad. Planner asigna a Designer un contrato versionado; el propietario aprueba cada versión antes de implementar la interfaz. Omitir o marcar como no aplicable si no hay un subplan de interfaz._

## Prioridades y fases
- **Planes de acceso (propietario, ronda 4):** tres planes para usuarios externos. Plan 1: chat asistido + contador de globos. Plan 2: plan 1 + costos (calculadora) + exploración de decoraciones prediseñadas. Plan 3: plan 2 + el modelo 3D (Taller 3D). Se mantienen los roles del personal (empleado interno, administrador); la relación entre planes, roles y permisos se define en el subplan de cuentas.
- **Orden de recorte si falta tiempo (acordado por el propietario, ronda 3):** 1) idioma: primero Taller 3D y navegación, el resto después del piloto; 2) cuartetos/módulos editables más allá de los colores; 3) mejoras del chat más allá de la división y la confiabilidad. **Nunca recortar:** cuentas, roles y permisos, proyectos y decoraciones guardados, gasto por usuario, mesas rectangulares, exportación a Blender, Backing. Un plan cubre todo; lo redactará una sesión dedicada de Planner Opus 5.5 de alto nivel, no la sesión de HQ.
- **Chat asistido (ronda 3):** dividir en tres herramientas: calculadora de costos, contador de globos y el chat «normal»; además, una integración básica entre chat y 3D: en 2–3 mensajes, el chat define qué se necesita y recomienda decoraciones 3D ya creadas.
- **Añadido al alcance en la ronda 2:** el chat asistido (asesor / chat guiado) está IN: se desglosará, dividirá y mejorará (detalles pendientes). Los límites de gasto en IA están OUT por ahora: solo medir y mostrar el gasto.
- **Debe incluir:** cuentas con tres roles iniciales (usuario, empleado interno, administrador) y un editor para que el administrador cree roles y elija permisos (propietario, ronda 2); gasto en IA por usuario con límite y panel para empleado/administrador (principalmente en Taller 3D); guardar proyectos; guardar decoraciones; mesas rectangulares; exportación a Blender.
- **Debería incluir:** cambio entre inglés y español para toda la aplicación (interfaz, respuestas de IA, productos), con detección automática; módulos y cuartetos editables; categoría Backing.
- **Más adelante:** espacio 3D a partir de una foto; exportación vectorial para Illustrator.
- Tensión por resolver: el propietario quiere que el cambio de idioma abarque TODO (no solo los flujos principales), aunque está clasificado como Debería incluir.

## Cronograma y dependencias
- Fecha límite del propietario: producción piloto en tres semanas desde 2026-10-26 (aproximadamente 2026-11-16). No es una corrección de emergencia: es trabajo planificado.
- Se solapa con REQ-004 cancelado (usuarios y gastos), REQ-005 cancelado (decoraciones desde cero), REQ-006 cancelado (foto del lugar a 3D) y REQ-011 terminado (estudio de módulos), REQ-012 terminado (mesas y sillas).

## Supuestos
- Las invitaciones son enlaces de un solo uso que el administrador copia y envía por su cuenta (ronda 4); este plan no incluye un servicio de correo electrónico.
- No hay indicadores de funcionalidad. Cada hito, una vez aprobados todos sus subplanes, se integra en `main` y despliega `demo-decoracion.vercel.app`, que será el entorno de pruebas hasta el día del piloto y, desde entonces, el entorno de producción (ronda 6).
- El desarrollo local no tiene restricciones de credenciales ni de roles solo con `AUTH_LOCAL_SIN_RESTRICCIONES=1` en `next dev` sobre loopback; en cualquier otro entorno, la aplicación se niega a iniciar. El propietario crea al primer administrador de producción mediante un comando de un solo uso.
- La traducción única de productos y decoraciones al inglés usa las cuentas Claude del propietario con Haiku 5.5 (sin clave de Gemini ni límite en USD).
- `/asesor` y `/happie` conservan su propio inicio de sesión y quedan fuera de las nuevas cuentas del piloto.
- El inicio de sesión usa correo electrónico y contraseña, con invitación por correo electrónico (el propietario eligió «invitado», no el mecanismo). Revisar si se prefiere un proveedor de identidad.
- «Exportación de Blender» se refiere al GLB existente, verificado y corregido, no a un formato nuevo.
- «Modificar cuartetos y módulos» significa editar más que los colores; aún no se especifican las ediciones exactas.
- Se conservan las cotizaciones compartidas existentes y la tabla de cuentas de asesores; solo se migran los datos necesarios.

## Cobertura
| Tema | Estado |
|---|---|
| Objetivo y problema | Claro |
| Usuarios / actores | Claro |
| Alcance | Claro |
| Fuera del alcance | Claro |
| Flujos y comportamiento | Parcial |
| Casos límite | Claro |
| Criterios de aceptación | Claro |
| Restricciones | Claro |
| Interfaz / dirección de diseño | Aplazada |
| Prioridades y fases | Claro |
| Cronograma | Claro |

## Aclaraciones
- Ronda 1 (2026-10-26): los usuarios del piloto = usuarios externos reales + empleados internos + administradores; se aceptan las prioridades propuestas; «tokens» = gasto en IA por usuario, visible para el empleado y el administrador (total de la sesión, gasto en generación de imágenes); Backing = una categoría del catálogo que agrupa accesorios para fiestas (aros metálicos, pedestales, panel redondo, media luna, arcos chiara); idioma: selector EN/ES, detección automática, abarca respuestas de IA, productos e interfaz.
- Ronda 6 (2026-10-26, Planner, SP-1): los planes de acceso son roles (Usuario · Plan 1/2/3, Empleado interno, Administrador; un rol por cuenta; los administradores crean más roles al elegir permisos); permisos iniciales según lo propuesto (Plan 1: chat asistido, contador de globos, catálogo; Plan 2: + calculadora de costos, explorador de decoraciones prediseñadas; Plan 3: + Taller 3D, incluida la IA de escenas, planes de montaje, ficha de montaje, exportación, proyectos y decoraciones propios; Empleado interno: + proyectos de todos, gasto en IA, herramientas internas; Administrador: + usuarios, roles, correcciones de textos en inglés); sesión de 30 días, termina al cerrar sesión, desactivar la cuenta o cambiar la contraseña; mínimo de **8** caracteres para la contraseña; 5 intentos fallidos por correo electrónico en 15 min bloquean ese correo durante 15 min; restablecimiento de contraseña = enlace de un solo uso generado por un administrador (24 h), enlace de invitación de 7 días; primer administrador de producción: el propietario ejecuta personalmente el comando de un solo uso y también puede usar el modo local sin restricciones contra la base de datos de producción para crear administradores; producción del piloto = `demo-decoracion.vercel.app` desde el día del piloto (sin dominio nuevo); las pruebas permanecen en local y en las vistas previas de Vercel.
- Ronda 5 (2026-10-26, Planner): demo-decoracion.vercel.app es el entorno de pruebas, no el de producción; cada hito se integra en main después de que el propietario apruebe sus subplanes (producción = por confirmar en SP-13); base de datos de pruebas = Postgres en el VPS advin, preparada por la sesión de HQ (`PICTURES_REQ021_DATABASE_URL`, túnel en el puerto local 55433), sin rama de Neon; modo local sin restricciones mediante indicador en `.env`, rechazado fuera de `next dev` en loopback; primer administrador de producción davidt@sempertex.com mediante un comando de un solo uso (por confirmar); el agente redacta el texto sobre tratamiento de datos (Ley 1581, ES/EN), el propietario lo aprueba y el equipo legal de Sempertex lo revisa; faltan el enlace a la política y el correo de contacto; prueba de humo automatizada en el entorno desplegado con la cuenta piloto-e2e, sin IA de pago.
- Ronda 4 (2026-10-26, Planner): invitación = enlace de un solo uso que se puede copiar; tres planes de acceso (ver Prioridades); sin indicadores; gasto en IA almacenado tanto para la sesión de inicio de sesión como para el proyecto/conversación; recortes por fecha (9 nov, idioma; 11 nov, módulos; 12 nov, chat), con aprobación del propietario para cada subplan en menos de 24 h; traducción con las cuentas Claude y Haiku 5.5; administrador local sin restricciones mediante un indicador en `.env`.
- Ronda 2 (2026-10-26): el chat asistido está incluido (se debe desglosar, dividir y mejorar); un administrador invita a las cuentas externas, sin registro abierto; el administrador puede crear roles y elegir permisos desde el piloto; por ahora, sin límites de gasto (solo medir y mostrar); los nombres y las descripciones de productos en inglés se generan una sola vez con IA a partir de la fuente en español, se guardan en la base de datos y un administrador puede editarlos.


### Ronda 3 (2026-10-26)
- P: Chat asistido → R: tres herramientas (calculadora de costos, contador de globos y chat «normal») + integración básica entre el chat y 3D (2–3 mensajes para definir la necesidad, recomienda decoraciones 3D existentes).
- P: Espacio 3D → R: no se agrega a este plan.
- P: Quién ve los proyectos guardados → R: cada usuario ve los suyos; los empleados y administradores los ven todos; las escenas guardadas en el navegador se importan al iniciar sesión.
- P: Decoración guardada → R: una composición creada en la escena y guardada en la biblioteca personal del usuario para otros proyectos (su publicación en la biblioteca global se hará más adelante).
- P: Qué se recorta si falta tiempo → R: el orden de recortes indicado arriba.

## Entradas
Solo ubicaciones, nunca valores. Subplan vacío = todo el plan. 

| Elemento | Subplan | Dónde se encuentra | Proveedor | Estado |
|---|---|---|---|---|
| Dónde se prueba cada subplan aprobado y cuándo se integra | all | ronda 5 q1: cada subplan se prueba localmente (Probar); cuando se aprueban todos los subplanes de un hito, se integra a `main`, se aplican las migraciones y Vercel (`demo-decoracion.vercel.app`, el entorno de pruebas) despliega; se despliega el VPS ai-api si tuvo cambios | Propietario | disponible |
| Entorno de producción del piloto (host, dominio, base de datos) | SP-13 | ronda 6 q5: `demo-decoracion.vercel.app` (proyecto de Vercel `dav033s-projects/demo-decoracion`, `DATABASE_URL` de Neon de su entorno Production) pasa a ser producción el día del piloto; no hay un dominio nuevo; hasta entonces es el entorno de pruebas y las pruebas se ejecutan localmente y en las vistas previas de Vercel | Propietario | disponible |
| Base de datos para verificaciones automatizadas y pruebas locales | all | `PICTURES_REQ021_DATABASE_URL` en `~/.config/flow/secrets.env`; Postgres 16 `req021-db` en advin, túnel `pictures-req021-db-tunnel.service` en el puerto local 55433 (TOOLS.md); aún no se han aplicado las migraciones | Propietario (HQ) | disponible |
| Base de datos Neon del entorno de pruebas | SP-13 | `DATABASE_URL` en el entorno Production de Vercel de `demo-decoracion` y `.env.local` (solo el nombre) | Propietario | disponible |
| Despliegue de `main` en Vercel (entorno de pruebas) | SP-13 | proyecto de Vercel `dav033s-projects/demo-decoracion`, integración con Git; CLI `vercel` con sesión iniciada como dav033 | Propietario | disponible |
| Despliegue de ai-api en el VPS | SP-6, SP-13 | `.github/workflows/deploy.yml` (`workflow_dispatch`, entorno `production`) mediante `gh` | Propietario | disponible |
| Indicador local sin restricciones: nombre y regla | SP-1 | ronda 5 q3 (aceptado): `AUTH_LOCAL_SIN_RESTRICCIONES=1` en `.env.local`, válido solo con `next dev` y solicitudes de loopback; en cualquier otro caso, la aplicación se niega a iniciar | Propietario | disponible |
| Primer administrador de producción: mecanismo y correo | SP-1, SP-13 | ronda 6 q4: el propietario ejecuta el comando de un solo uso `npm run cuentas:primer-admin` para `davidt@sempertex.com` en su propia terminal durante la publicación (el enlace de activación solo se muestra a él); también puede ejecutar la aplicación localmente en modo sin restricciones contra la base de datos de producción y crear administradores desde las pantallas de administración | Propietario | disponible |
| Texto de protección de datos (Ley 1581, ES/EN) | SP-2 | ronda 5 q6: redactado por el agente, aprobado por el propietario en SP-2 | Propietario | disponible |
| Razón social de Sempertex, URL de la política de privacidad y correo de contacto para ejercer derechos | SP-2 | ronda 5 q6 | Propietario | diferido: marcados como campos por completar en el texto; se indicó que Sempertex debe revisarlos legalmente antes de que se activen usuarios reales |
| Autorización para pruebas smoke automatizadas en el entorno desplegado | SP-13 | ronda 5 q7 (concedida: cuenta `piloto-e2e`, plan Usuario 3, sin IA de pago, eliminada después de cada prueba smoke); requiere una entrada correspondiente en `~/bitacora/pictures/verification-policy.json` (propiedad del operador, aún no creada) | Propietario | ubicación indicada |
| Traducción única al inglés con Haiku 5.5 | SP-9 | cuentas de Claude del propietario mediante la CLI de Claude Code (ronda 4 q6); sin clave de Gemini ni límite en USD | Propietario | disponible |

## Aviso de tratamiento de datos (borrador v1, SP-2)
Redactado por el Planner (ronda 5 q6); el propietario lo aprueba en SP-2; el área legal de Sempertex debe revisarlo antes de que se activen usuarios externos reales. Los campos entre corchetes son datos que debe proporcionar el propietario; no se afirma nada más.

**ES** — Aviso de tratamiento de datos personales (versión 1)
[RAZÓN SOCIAL DE SEMPERTEX] tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a [CORREO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.

**EN** — Aviso de datos personales (versión 1)
[NOMBRE LEGAL DE SEMPTERTEX] tratará tus datos personales —nombre, correo electrónico, empresa (si la proporcionas), el rol y el plan que se te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el uso de inteligencia artificial. Los proyectos y decoraciones que guardes están vinculados a tu cuenta. Puedes acceder a tus datos, actualizarlos, corregirlos o solicitar su eliminación, y retirar esta autorización, escribiendo a [CORREO DE CONTACTO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta, confirmas que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley colombiana 1581 de 2012.

## Pruebas
Donde el propietario prueba cada subplan una vez construido (D-131). «Probar» abre localmente esa versión exacta; el túnel `pictures-req021-db-tunnel.service` debe estar activo y `.env.local` debe apuntar `DATABASE_URL` a la base de datos de prueba de REQ-021 (nunca a producción).

| Subplan | Dónde | Cómo | Resultado esperado |
|---|---|---|---|
| SP-1 | Local | 1) `npm run rag:migrate` y luego `npm run cuentas:sembrar-prueba` (escribir una contraseña; crea plan1@, plan2@, plan3@, empleado@ y admin@prueba.local). 2) `npm run dev`; luego, en otra terminal, `npm run cuentas:probar-acceso -- --base http://localhost:3000 --correo plan1@prueba.local` y lo mismo para plan3@, empleado@ y admin@. 3) Abrir http://localhost:3000/3d en el navegador sin la variable; luego agregar `AUTH_LOCAL_SIN_RESTRICCIONES=1` a `.env.local`, reiniciar `npm run dev` y volver a abrirla. 4) Con la variable aún configurada, ejecutar `npm run build`. | 2) Plan 1: chat y catálogo permitidos; costos, Taller 3D y administración denegados. Plan 3: Taller 3D permitido; administración denegada. Empleado: herramientas internas y gastos permitidos; usuarios y roles denegados. Administrador: todo permitido. 3) Sin la variable: redirige a /login (no puede iniciar sesión hasta que se integre SP-2); con la variable: el Taller se abre como «Administrador local». 4) La compilación se detiene con un error que menciona `AUTH_LOCAL_SIN_RESTRICCIONES`. |
| SP-2 | Local | Con la configuración de SP-1: 1) Ejecutar `npm run dev`, abrir http://localhost:3000/login e iniciar sesión como admin@prueba.local. 2) Abrir Administración → Cuentas, invitar a una persona nueva con el rol «Usuario · Plan 2» y copiar el enlace. 3) Abrir el enlace en una ventana privada: establecer una contraseña, leer y aceptar el aviso sobre el tratamiento de datos e iniciar sesión. 4) Volver como administrador, cambiar a esa persona a «Usuario · Plan 3», crear un rol personalizado con dos permisos e intentar eliminar «Administrador» y el rol que está en uso. 5) En la ventana privada, usar el menú de cuenta → Mi cuenta para cambiar la contraseña y luego cerrar sesión. | 2) El enlace aparece una sola vez con un botón para copiarlo. 3) El aviso aparece en el idioma del navegador; sin marcar la casilla, no se puede activar la cuenta; después de iniciar sesión, la persona ve el chat y la herramienta de costos, y /3d muestra «sin acceso». 4) Después de cambiar el rol, al volver a cargar /3d se abre el Taller; los roles del sistema son de solo lectura y el rol en uso no se puede eliminar; en ambos casos se muestra un motivo claro. 5) La contraseña nueva funciona y la anterior no. Las pantallas coinciden con el diseño aprobado `cuentas-admin@v1` en tamaños de teléfono y escritorio. |
