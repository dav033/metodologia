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
- R1. Cuando un administrador invita a una dirección de correo electrónico, el sistema deberá permitir que esa persona cree una contraseña e inicie sesión; no deberá existir el registro abierto.
- R2. El sistema deberá aplicar roles y permisos en el servidor para cada página y API del piloto.
- R3. Cuando un administrador crea un rol, el sistema deberá permitirle seleccionar sus permisos de una lista definida; deberán existir los tres roles iniciales.
- R4. Cuando se complete una llamada de IA con costo, el sistema deberá guardar los tokens y el costo estimado asociados al usuario y la sesión.
- R5. Mientras la sesión esté iniciada como empleado o administrador, el sistema deberá mostrar los totales de gastos por sesión, tipo y usuario.
- R6. Cuando un usuario guarda un proyecto, el sistema deberá almacenarlo en el servidor bajo su cuenta; los empleados y administradores deberán poder abrir cualquier proyecto.
- R7. Cuando un usuario inicia sesión por primera vez y tiene escenas guardadas en el navegador, el sistema deberá ofrecerle importarlas sin pérdida de datos.
- R8. Cuando un usuario guarda una composición como decoración, el sistema deberá añadirla a su biblioteca personal.
- R9. Cuando un usuario añade una mesa rectangular, el sistema deberá permitirle configurar su tamaño y número de sillas, y actualizar la lista de compras.
- R10. Cuando un usuario exporta a GLB, el sistema deberá generar un archivo que Blender abra con la distribución, los tamaños y los colores de la escena.
- R11. El catálogo deberá tener una categoría Backing que incluya los artículos de fiesta existentes de esos tipos.
- R12. Cuando se cambia o detecta el idioma, el sistema deberá mostrar en ese idioma la interfaz, las respuestas de la IA y el texto de los productos.
- R13. El chat asistido deberá dividirse en una calculadora de costos, un contador de globos y un chat normal; el chat normal deberá conectarse al taller 3D.
- R14. Si alguno de los requisitos R1–R13 no se termina para la fecha límite, se deberá aplicar el orden de recorte de la sección Prioridades; los elementos que nunca se recortan deberán entregarse.

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
- **Orden de recorte si falta tiempo (acordado por el propietario, ronda 3):** 1) idioma: primero el Taller 3D y la navegación, el resto después del piloto; 2) cuartetos y módulos editables más allá de los colores; 3) mejoras del chat más allá de la separación y la confiabilidad. **Nunca recortar:** cuentas, roles y permisos, proyectos y decoraciones guardados, gasto por usuario, mesas rectangulares, exportación a Blender, Backing. Un plan cubre todo; lo redacta una sesión dedicada de Planner Opus 5.5 high, no la sesión de HQ.
- **Chat asistido (ronda 3):** se divide en tres herramientas —calculadora de costos, contador de globos y chat «normal»—, además de una integración básica chat↔3D: en 2–3 mensajes, el chat define lo que se necesita y recomienda decoraciones 3D ya creadas.
- **Añadido al alcance en la ronda 2:** el chat asistido (asesor / chat guiado) está incluido: se desglosará, dividirá y mejorará (detalles pendientes). Los límites de gasto de IA quedan fuera por ahora: solo se mide y muestra el gasto.
- **Must:** cuentas con tres roles iniciales (usuario, empleado interno, administrador) y un editor de administración para crear roles y elegir permisos (propietario, ronda 2); gasto en IA por usuario con límite y panel para empleados y administradores (principalmente en el Taller 3D); guardar proyectos; guardar decoraciones; mesas rectangulares; exportar a Blender.
- **Should:** cambio entre inglés y español en toda la aplicación (interfaz, respuestas de la IA, productos), con detección automática; módulos y cuartetos editables; categoría Backing.
- **Para más adelante:** espacio 3D a partir de una foto; exportación vectorial para Illustrator.
- Tensión por resolver: el propietario quiere que el selector de idioma abarque TODO (no solo los flujos principales), aunque tiene prioridad Should.

## Cronograma y dependencias
- Fecha límite del propietario: producción piloto en tres semanas desde 2026-10-26 (aproximadamente 2026-11-16). No es una corrección de emergencia: es trabajo planificado.
- Se solapa con REQ-004 cancelado (usuarios y gastos), REQ-005 cancelado (decoraciones desde cero), REQ-006 cancelado (foto del lugar a 3D) y REQ-011 terminado (estudio de módulos), REQ-012 terminado (mesas y sillas).

## Supuestos
- El inicio de sesión usa correo electrónico y contraseña, con invitación por correo electrónico (el propietario eligió «con invitación», no el mecanismo). Revisar si se prefiere un proveedor de identidad.
- «Exportar a Blender» significa usar el GLB existente, verificarlo y corregirlo; no crear un formato nuevo.
- «Modificar cuartetos y módulos» significa editar más que los colores; las modificaciones específicas aún no se han definido.
- Se conservan las cotizaciones compartidas existentes y la tabla de cuentas del asesor; solo se migran los datos necesarios.

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
- Ronda 1 (2026-10-26): usuarios piloto = usuarios externos reales + empleados internos + administradores; se aceptaron las prioridades propuestas; «tokens» = gasto en IA por usuario, visible para empleados y administradores (total de la sesión, gasto en generación de imágenes); Backing = una categoría del catálogo que agrupa accesorios para fiestas (aros metálicos, pedestales, panel redondo, media luna, arcos chiara); idioma: selector EN/ES, detección automática, que abarca respuestas de IA, productos e interfaz.
- Ronda 2 (2026-10-26): el chat asistido está incluido en el alcance (se dividirá, separará y mejorará); un administrador invita a las cuentas externas, no hay registro abierto; el administrador puede crear roles y elegir permisos desde el piloto; por ahora no hay límites de gasto (solo se mide y muestra); los nombres y las descripciones de productos en inglés se generan una vez con IA a partir de la fuente en español, se almacenan en la base de datos y un administrador puede editarlos.


### Ronda 3 (2026-10-26)
- P: Chat asistido → R: tres herramientas (calculadora de costos, contador de globos, chat «normal») + integración básica entre chat y 3D (2–3 mensajes para definir la necesidad; recomienda decoraciones 3D existentes).
- P: Espacio 3D → R: no se agrega a este plan.
- P: Quién ve los proyectos guardados → R: cada usuario ve los suyos; los empleados y administradores los ven todos; las escenas guardadas en el navegador se importan al iniciar sesión.
- P: Decoración guardada → R: una composición creada en la escena y guardada en la biblioteca personal del usuario para otros proyectos (la publicación en la biblioteca global se hará más adelante).
- P: Qué se recorta si falta tiempo → R: seguir el orden indicado arriba.
