# Brief de interfaz — SP-4 · Proyectos guardados

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Un usuario guarda, lista, vuelve a abrir y continúa proyectos del Taller almacenados en su cuenta; empleados y administradores pueden abrir los proyectos de cualquier persona; un guardado posterior nunca sobrescribe silenciosamente uno anterior; las escenas guardadas en el navegador se ofrecen para importar al iniciar sesión por primera vez, sin pérdida de datos.

## Requisitos que cubre

- R6: Cuando un usuario guarda un proyecto, el sistema debe almacenarlo en el servidor bajo su cuenta; empleados y administradores deben poder abrir cualquier proyecto.
- R7: Cuando un usuario inicia sesión por primera vez y hay escenas guardadas en el navegador, el sistema debe ofrecer importarlas sin pérdida de datos.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-3 and SP-4 (round 9 answered)»

## Criterios de producto

- El usuario nombra, guarda, lista y vuelve a abrir proyectos con su escena completa sin cambios entre navegadores; una respuesta obsoleta nunca indica que los cambios pendientes ya se guardaron.
- Dos copias abiertas no pueden sobrescribirse silenciosamente: un 409 detiene el guardado automático, conserva la escena local sin enviar y ofrece cargar la versión del servidor o guardar una copia propia; el personal y los administradores leen originales de otras personas sin permiso de escritura y solo pueden guardar una copia propia con taller.usar.
- El primer guardado con nombre es explícito y las ediciones posteriores se guardan automáticamente; la búsqueda de la lista de proyectos encuentra coincidencias autorizadas más allá de la primera página cargada, los cambios de filtro restablecen la paginación y las respuestas obsoletas de consultas no reemplazan los resultados actuales.
- A una cuenta con sesión iniciada y una escena heredada del navegador se le ofrece una importación explícita; si la acepta, se crea exactamente un proyecto propio incluso tras reintentar; si la rechaza o falla la validación, se conservan los datos locales sin procesar, y ninguna cuenta recibe automáticamente una escena heredada.
- La lista de proyectos, los estados de guardado/sin conexión/conflicto, la vista de solo lectura de proyectos ajenos y el aviso de importación coinciden con proyectos@v1 aprobado en los anchos de teléfono, tableta y escritorio, con el comportamiento del teclado y del foco verificado.
- «Escena nueva», una plantilla o «Abrir en Escena» inician un proyecto nuevo sin guardar: el proyecto abierto conserva su última revisión guardada (primero se guardan sus cambios pendientes o se pregunta al usuario antes de descartar una escena nunca guardada), la escena nueva no queda vinculada a ningún proyecto y no se envía nada al servidor hasta el primer guardado con nombre.

## Flujos de usuario

1. Primer guardado y guardado automático
   1. Crea una escena en el Taller 3D
   2. La guarda con un nombre por primera vez
   3. Sigue editándola; los cambios posteriores se guardan automáticamente con un estado visible y un control Guardar ahora
2. Iniciar un proyecto nuevo
   1. Desde un proyecto abierto, elige «Escena nueva», una plantilla o «Abrir en Escena» en un elemento de la biblioteca
   2. Primero se guardan los cambios pendientes del proyecto abierto; se pregunta antes de descartar una escena nunca guardada
   3. Obtiene un proyecto nuevo sin guardar, llamado «Escena nueva» y sin vínculo a un proyecto guardado
   4. Lo guarda con un nombre por primera vez; el guardado automático comienza después
3. Volver a abrir en otro navegador
   1. Abre /proyectos en otro navegador con sesión iniciada en la misma cuenta
   2. Busca en la lista o la recorre
   3. Abre el proyecto y obtiene la escena completa y su nombre
4. Guardados en conflicto
   1. Dos copias abiertas del mismo proyecto se guardan desde la misma revisión
   2. El segundo guardado muestra un conflicto, detiene el guardado automático y conserva el borrador local
   3. Elige cargar la versión del servidor o guardar una copia propia
5. Sin conexión
   1. Edita cuando se pierde la conexión
   2. Ve que el trabajo aún no está guardado
   3. Reintenta cuando vuelve a estar en línea
6. El personal abre el proyecto de otra persona
   1. Un empleado o administrador filtra la lista por propietario
   2. Abre el proyecto en modo de solo lectura
   3. Guarda una copia propia (solo con el permiso del Taller)
7. Importar una escena guardada en el navegador
   1. Inicia sesión mientras hay una escena heredada taller3d:escena:v1 en este navegador
   2. Se le pregunta si quiere importarla a esta cuenta
   3. Acepta (se crea un proyecto incluso después de reintentos) o rechaza (los datos locales se conservan)
   4. Si los datos no son válidos, ve el motivo y puede descargar el original

## Pantallas y estados

- Lista de /proyectos: vacía, cargando, resultados, búsqueda sin coincidencias, página siguiente, error al cargar la página siguiente con opción para reintentar
- Filtro por propietario para empleados y administradores
- Diálogo del primer guardado con nombre
- Proyecto nuevo sin guardar después de «Escena nueva», una plantilla o «Abrir en Escena»: nombre «Escena nueva», estado de pendiente de guardar, el primer guardado solicita un nombre
- Estado de guardado en el encabezado del Taller (amplía los textos actuales «Guardado» / «Guardando…» / «Sin guardar» junto al nombre de la escena): guardando, guardado en la cuenta, no guardado (sin conexión), error, conflicto
- Panel de conflicto: cargar la versión del servidor o guardar una copia propia; se conserva el borrador local
- Vista de solo lectura del proyecto de otra persona con la acción Guardar copia
- Aviso de importación heredada: aceptar, rechazar, datos no válidos con explicación y opción para descargar
- Anchos para teléfono, tableta y escritorio

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/3d`, `/proyectos (new)`, `/proyectos/[id] (new)`
- paths: `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `src/components/tres-d/guardado-escena.ts`, `src/components/tres-d/guardado-conversacion.ts`, `src/components/tres-d/imagenes-guardadas.ts`, `src/app/api/decoraciones/route.ts`
- components: `Taller3D`, `ExportarEscenaTaller`, `MenuCuenta (planned by SP-2 T2.4)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Leído en origin/main a9f3d6e5. Ya existe: la cabecera de Taller tiene un nombre de escena editable en línea («Escena nueva» de forma predeterminada) y un texto de estado de guardado «Guardado» / «Guardando…» / «Sin guardar (el navegador no deja)», que actualmente se refiere al almacenamiento del navegador: una escena por navegador en la clave de localStorage taller3d:escena:v1, guardada 500 ms después del último cambio (guardado-escena.ts; las entradas no válidas o antiguas se descartan silenciosamente). Las plantillas, «Sala vacía» y la apertura de un elemento de la biblioteca reemplazan esa única escena. La conversación de IA es una entrada separada de localStorage y las imágenes generadas están en IndexedDB. No existe: almacenamiento de escenas en el servidor, una lista de proyectos o la ruta /proyectos, identidad de proyecto, conflictos, importación ni una vista de solo lectura; /api/decoraciones es la biblioteca global de decoraciones de las pantallas de administración (ámbito de SP-5), no de proyectos. Por tanto, el estado de guardado y el nombre de la escena son elementos existentes que SP-4 amplía para proyectos en el servidor; la lista, el diálogo del primer guardado, el panel de conflictos, la vista de solo lectura y el aviso de importación son nuevos. Confirmado por el propietario el 2026-10-27: «Escena nueva», una plantilla o «Abrir en Escena» (Biblioteca.tsx) inician un proyecto nuevo sin guardar; primero se guardan los cambios pendientes del proyecto abierto y, si la escena nunca se ha guardado, se pregunta antes de descartarla. No hay capturas de pantalla almacenadas en el repositorio.

## No debe cambiar

- Solo el nombre del proyecto y la escena completa se transfieren entre navegadores; la conversación de IA y las imágenes generadas permanecen en el navegador
- Los datos originales del navegador nunca se borran ni modifican por una importación, un rechazo o un fallo
- No hay interfaz para eliminar, transferir ni consultar el historial de versiones
- Las herramientas de edición de Taller, el shell, la navegación y los tokens de diseño, excepto el estado de guardado, la lista de proyectos y el aviso de importación
- Un miembro del personal nunca edita el original de otra persona

## Reglas de copy

- Interfaz en español; cada cadena nueva en src/components/proyectos/textos-proyectos.ts para su traducción posterior
- No inventar textos: las palabras de estado describen únicamente el estado real (guardado, guardando, sin guardar, conflicto)
- Nunca indicar que el trabajo está guardado antes de que el servidor confirme esa revisión
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T4.1 — Copiar el contrato de diseño aprobado para proyectos guardados
- T4.4 — Implementar la lista de proyectos y el guardado de Taller seguro frente a conflictos
  - Objetivo: El usuario asigna nombres a los proyectos, los guarda, los consulta en una lista y los vuelve a abrir con la escena completa intacta entre navegadores; los cambios pendientes nunca se muestran como guardados por una respuesta obsoleta. Propietario, 2026-10-27: «Escena nueva», una plantilla o «Abrir en Escena» desde la biblioteca inician un proyecto nuevo sin guardar llamado «Escena nueva».
- T4.5 — Implementar una importación de escenas heredadas sin pérdida de datos e idempotente
- T4.8 — Revisar las interfaces renderizadas de proyectos e importación

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas ajenas a la interfaz (ui:false, que no sean de diseño o revisión), verificación, expected_paths, shared_resources, classification y estimates, digest, criterios de aceptación exclusivos de ingeniería. Tareas omitidas: T4.2, T4.3, T4.6, T4.7, T4.9, T4.31.
