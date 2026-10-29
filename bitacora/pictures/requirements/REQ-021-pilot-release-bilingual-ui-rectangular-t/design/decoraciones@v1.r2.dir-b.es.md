---
name: Bandeja de escena
status: draft
kind: exploration
subplan: SP-5
contract_target: decoraciones@v1
revision: r2
direction: b
---

# Bandeja de escena

Solo exploración de planificación. Esta propuesta no está aprobada ni crea o reemplaza el contrato canónico. El propietario elige entre las propuestas antes de que un finalizador redacte `decoraciones@v1`.

## Enfoque y superficie existente

El área modificada es la biblioteca personal de decoraciones del Taller 3D existente, no una página nueva. Se conservan el contexto de la escena, la barra de herramientas, la terminología de guardar escena/guardar pieza, el contexto de escena/IA y los controles de foto realista y lista de compras. La biblioteca personal se ubica en una bandeja debajo del lienzo y la vista previa de la decoración seleccionada, la ocasión y la acción para colocarla se mantienen en un inspector a la derecha. Para guardar, se usa el mismo inspector en el lugar, de modo que el proyecto actual sigue visible. Una miniatura selecciona un elemento; la acción de acento lo agrega a la escena actual. Esto reduce las acciones repetidas en cada elemento y conserva una relación espacial entre la biblioteca, el objeto seleccionado y su destino.

El encabezado de anillos y puntos de Pictures/Sempertex, los controles de cuenta/idioma, el título de tarea, la navegación neutra entre Taller 3D / Proyectos, los roles de formas redondeadas y el pie reutilizan la terminología del módulo hermano. Los botones de herramientas existentes y de rutas del módulo hermano informan explícitamente que están en el contexto de Mockup, en lugar de simular la navegación de un producto en funcionamiento.

Fuentes de solo lectura inspeccionadas: `src/app/globals.css` de ambos repositorios, `src/app/layout.tsx` de t12, `src/components/ui/shell/CabeceraApp.tsx`, `src/components/tres-d/Taller3D.tsx` y `Biblioteca.tsx`; el Markdown canónico y el HTML compilado de cuentas-admin, planes y proyectos del módulo hermano; el archivo de origen seleccionado de proyectos `proyectos@v1.r12.dir-c.tsx` para el mapeo compartido de estructura/tokens/fuentes. El comportamiento se basa en `decoraciones@v1.r2.behavior.md` y en «Behavior — SP-5 (round 11 answered)» de SPEC. Los consumidores de interfaz de SP-5 siguen siendo T5.1, T5.3 y T5.5; aquí no se diseña trabajo exclusivo de ingeniería.

## Dos miniaturas y una elección

- Propuesta 1: `decoraciones@v1.r2.dir-b.html.candidate-1.html` — la biblioteca ocupa un panel lateral y la acción para colocar se ubica en la parte inferior. Queda menos espacio para los detalles del elemento seleccionado y la selección queda separada de la acción.
- **Propuesta elegida 2:** `decoraciones@v1.r2.dir-b.html.candidate-2.html` — bandeja de biblioteca debajo de la escena, vista previa/acciones del elemento seleccionado junto a ella. La maqueta completa agrega a esta composición la barra de herramientas heredada, controles reales, inspectores de estado, filtros y adaptación responsiva.

Ambas composiciones estáticas en miniatura se dibujaron primero y se renderizaron/inspeccionaron visualmente a 1280 px antes de construir la página completa. Son bocetos, no un sustituto auditado de la maqueta completa.

## Ocho ejes

| Eje | Decisión renderizada |
|---|---|
| concepto | Mantener el Taller actual como superficie de trabajo: elegir una decoración guardada debajo del lienzo, inspeccionarla junto al lienzo y luego colocar una copia en la escena actual. |
| diseño | Encabezado existente de Pictures, título y regla de navegación entre Taller 3D / Proyectos; el área modificada del taller tiene una barra de herramientas de 56 px, un lienzo flexible sobre una bandeja de biblioteca y un inspector de detalles de 280 px. Por debajo de 768 px, el inspector aparece después de la bandeja; por debajo de 640 px, la barra desaparece. |
| navegación | La navegación con botones activos Mi biblioteca / En este navegador cambia el alcance de la bandeja sin salir del Taller; el personal también cuenta con un selector nativo etiquetado como Propietario. Al seleccionar una miniatura cambia el inspector; en el teléfono, la selección enfoca y muestra ese inspector. |
| tipografía | Se heredan Geist Sans incrustada, cuerpo de 15 px, H1 de 24 px/600, encabezados del inspector y la biblioteca de 18 px/600, nombres de mosaico de 14 px/600 y metadatos de 12–13 px. Geist Mono se conserva en los metadatos del encabezado de Sempertex. |
| densidad | Tres miniaturas compactas por fila de bandeja en escritorio; dos entre 768 y 1099 px y en teléfonos, con márgenes internos amplios de panel de 24 px en escritorio/20 px en teléfono. Un inspector contiene las acciones detalladas en lugar de repetirlas en cada miniatura. |
| componentes | Button, Input y Skeleton reales de shadcn/Base UI, Dialog y AlertDialog respaldados por Animate UI, botones de alcance nativos, selectores nativos y el control de cuenta heredado. SVG en línea ilustra las miniaturas de escenas/piezas; nunca simula un renderizador. |
| color | Tokens exactos claros/oscuros de Pictures globals.css mapeados a roles del kit, incluidos fondo, superficie, texto, acento y roles de lienzo/panel del Taller. El color primario identifica las acciones de colocación/guardado; los bordes de controles usan el alias accesible heredado texto-tenue. |
| movimiento | Entrada espacial finita: la bandeja de biblioteca sube 24 px, el inspector entra 32 px desde la derecha y la vista previa seleccionada se acomoda con escala/rotación; la colocación se integra al lienzo con un resorte. Transición elástica expresiva de 520 ms y gestos de control de 170 ms; reducción natural/sutil de escala. La configuración de movimiento reducido del sistema operativo, Quieto y still=1 hacen que los elementos se establezcan de inmediato; los efectos CSS se pausan en pestañas ocultas. |

## Cobertura de comportamiento

| Vista o estado | Comportamiento visible |
|---|---|
| `library` | Biblioteca de la cuenta personal, búsqueda por nombre, filtro de ocasión, miniaturas de escenas/piezas, vista previa detallada y Añadir a mi escena. La escena existente permanece visible. |
| `save-scene` / `save-piece` | El inspector muestra la escena completa o la pieza seleccionada, campos etiquetados Nombre/Ocasión, Guardar/Cancelar. La validación de nombre vacío mantiene abierto el formulario. |
| `staff` | Propietario permite seleccionar la cuenta ilustrada. Los detalles ajenos indican claramente Cuenta de ejemplo · Solo lectura; no aparecen controles de edición/eliminación. Añadir copia a mi escena coloca una copia en la escena actual propia del miembro del personal. El original no cambia. Los botones para guardar pieza/escena corresponden a esa escena propia y abren explícitamente el inspector para guardar en la cuenta propia. |
| Alcance local | Grupo separado En este navegador con el ejemplo Mi escena y una explicación de que solo se guarda localmente. No hay acción de importación, progreso de importación, error de importación, lista combinada ni migración automática. No se rediseña la edición heredada. |
| `loading` | Esqueletos de la bandeja de cuenta y Cargando biblioteca; no se muestran resultados anteriores ni detalles del elemento seleccionado. El grupo local sigue disponible por separado. |
| `empty` | Lista de cuenta vacía con una acción siguiente para guardar una escena; no se inventan elementos guardados. La vista vacía de otra cuenta no ofrece acciones para modificar su colección. |
| `error` | No se pudo cargar la biblioteca de la cuenta; opción explícita Reintentar. La escena del proyecto permanece visible. |
| `no-results` | No hay coincidencias, con una acción para borrar la búsqueda. La búsqueda ingresada y el filtro de ocasión también funcionan. |
| `saving` | Guardando… y controles para cancelar/enviar de nuevo deshabilitados; no se afirma que se haya guardado. La operación de demostración solo termina mediante una confirmación simulada. El estado del inspector sigue pendiente hasta que cambie. |
| `saved` | Guardado en tu biblioteca solo en el ejemplo confirmado o después de la confirmación de demostración; Ver en mi biblioteca vuelve al elemento guardado. |
| `save-error` | Se conservan los valores del formulario y la escena; se muestra el error explícitamente y la opción Reintentar; al reintentar se pasa al estado pendiente y luego al guardado confirmado. |
| `account-switch` | Se borra toda la región de datos del taller: sin miniaturas anteriores, detalles seleccionados ni escena. La continuación muestra la lista vacía de la siguiente cuenta. El cierre de sesión usa este ejemplo de borrado sin afirmar que exista un flujo real de autenticación. |
| `no-access` | No se muestran metadatos de decoración, lienzo ni biblioteca. Se explica que la biblioteca requiere acceso al Taller. |
| diálogo `edit` | Formulario de nombre/ocasión exclusivo del propietario, validación etiquetada, guardado pendiente y confirmación simulada. No se inventa silenciosamente una actualización del contenido de la escena. |
| diálogo `delete` AlertDialog | Confirmación exclusiva del propietario, cancelar/Escape y eliminación pendiente. El elemento original de la biblioteca se elimina del ejemplo en memoria al confirmarse. Las copias ya colocadas se presentan como independientes. |

Los inspectores nativos están fuera de la raíz del producto y corresponden a `view`, `state`, `scene`, `theme` y `motion` del entorno de ejecución real. Exponen todos los estados declarados; el significado de cada estado depende del contexto: loading/empty/error afectan la bandeja de cuenta, los estados de guardado afectan los formularios del propietario, los elementos ajenos del personal siguen siendo de solo lectura, y account-switch/no-access tienen prioridad sobre el contenido y los diálogos. El alcance local se abre mediante su botón visible; la expansión de español/inglés usa el control de idioma etiquetado. No se declara ni está presente ningún estado de importación.

## Tokens, componentes y detalles de interacción

Usar el mapeo del proyecto heredado de proyectos@v1, no los valores predeterminados del kit: fondo claro/oscuro `#faf9fc/#0b0c10`, superficie `#ffffff/#16181f`, texto `#1c1425/#f4f5f7`, texto-suave `#6b6178/#9aa1ad`, texto-tenue `#766c85/#8a91a0`, acento `#6d3fe0/#9479ff`, sobre-acento `#ffffff/#120b24`, y todos los roles existentes de éxito/error/advertencia y del Taller. El TSX contiene el mapeo completo de ambos temas. Los bordes de controles usan texto-tenue; las líneas decorativas usan borde. Los archivos WOFF2 locales incrustados de Geist Sans/Mono provienen de la compilación Next existente de t12. Los radios de paneles/campos/etiquetas reutilizan los valores del módulo hermano de 32/18/999 px, con superficies de taller/márgenes internos de 24 px. No hay una paleta, tipografía ni recurso externo nuevos.

Componentes reales del manifiesto instalado: `shadcn:button outline|default default|hover|focus|disabled|busy` de `@/components/ui/button`; `shadcn:input default|invalid|disabled` de `@/components/ui/input`; `shadcn:skeleton loading` de `@/components/ui/skeleton`; `shadcn:dialog open|closed` de `@/components/ui/dialog`; `shadcn:alert-dialog open|closed` de `@/components/ui/alert-dialog`. Los diálogos instalados usan primitivas de Animate UI/Base UI. Las importaciones de montaje/entorno de ejecución son `@kit/mockup` y `@kit/motion`; la colocación también consulta `useMotionProfile` para la configuración de resorte/movimiento reducido de Motion. La estructura, la navegación por alcance, la selección de miniaturas, el inspector y el SVG de escena son composiciones personalizadas; no se presentan como componentes independientes instalados.

La característica espacial es un cambio interrumpible de selección a inspector y la colocación de una copia en el lienzo existente; los efectos de entrada CSS finitos mueven la bandeja hacia arriba y el inspector desde el costado. El contenido sigue siendo opaco/legible durante el movimiento. La respuesta visual al presionar/pasar el cursor es breve; no hay ciclos ambientales, solicitudes fetch ni mensajes que dependan solo de la animación. El movimiento reducido del sistema operativo, Quieto y `?still=1` conservan todos los estados/acciones finales sin desplazamiento; los cambios de visibilidad pausan los efectos CSS.

La semántica de los diálogos, el fondo inerte y la contención del teclado provienen de las primitivas reales. Escape/cancelar devuelve el foco al control que abrió el diálogo. Si la eliminación quita ese control, el foco pasa al encabezado de la biblioteca. En el teléfono, la selección muestra/enfoca el encabezado del inspector; las acciones de guardado muestran/enfocan el encabezado del formulario correspondiente. El estado se comunica con texto y semántica de estado cortés o alerta; los campos tienen etiquetas y texto de error asociado. Los contornos de foco visibles de 3 px y los controles de 44 px siguen el objetivo del módulo hermano. Estas comprobaciones no certifican el cumplimiento completo de WCAG, la salida de lectores de pantalla ni el comportamiento de teclado de WebGL en producción.

## Decisiones de diseño adaptable

- 1100px+: margen heredado de 40px en el contenedor; barra lateral de 56px, área de trabajo y bandeja flexibles e inspector de 280px. Tres miniaturas por fila de la bandeja; la búsqueda y la ocasión comparten una fila. El área de trabajo, los controles de la biblioteca y el inspector forman parte del mismo documento de trabajo desplazable.
- 768–1099px: margen de 24px en el contenedor; barra lateral de 48px e inspector de 256px; dos miniaturas y controles de búsqueda y filtro apilados.
- 640–767px: la barra lateral permanece; el inspector pasa debajo de la bandeja, dentro de la columna del área de trabajo; las vistas previas aumentan de tamaño y los controles comparten filas cuando caben.
- 360–639px: margen de 20px en el contenedor, encabezado y navegación de rutas con ajuste de línea, barra de herramientas oculta, lienzo, bandeja e inspector apilados, controles para guardar de ancho completo, dos miniaturas y filtros apilados. Los paneles usan márgenes internos de 20px; los diálogos ocupan el tamaño de la ventana gráfica menos 40px, tienen 24px de relleno y desplazamiento vertical interno accesible. La altura completa del documento de trabajo usa desplazamiento vertical normal, sin paneles recortados.

Los controles nativos, los nombres largos y las etiquetas ES/EN se ajustan sin provocar desbordamiento horizontal de la página. En anchos reducidos, al elegir un elemento o iniciar el guardado, se muestra su inspector en vez de requerir un panel lateral oculto. Los puntos de control principales de la auditoría son 390/768/1280px, en ambos temas.

## Observaciones de aceptación de la interfaz renderizada

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-01 | 1280px | normal | El área de trabajo queda encima de la bandeja de la biblioteca; la vista previa y las acciones del elemento seleccionado ocupan el inspector derecho. |
| B-02 | 390px | normal | El área de trabajo, la bandeja y el inspector se apilan en dos columnas de miniaturas, sin desplazamiento horizontal de la página. |
| B-03 | Todos los auditados | personal | Se muestran el propietario externo y Solo lectura; Editar y Eliminar no aparecen. |
| B-04 | Todos los auditados | guardando | Se muestra Guardando, sin la confirmación Guardado. |
| B-05 | Todos los auditados | error al guardar | El formulario y la opción para volver a intentar siguen visibles. |
| B-06 | Todos los auditados | ámbito local | En este navegador sigue siendo un grupo separado, sin acción de importación. |
| B-07 | Todos los auditados | cambio de cuenta | No se muestran miniaturas de bibliotecas anteriores, el inspector de detalles ni el lienzo del proyecto. |
| B-08 | Todos los auditados | movimiento reducido/sin movimiento | El contenido final y todas las palabras de estado siguen visibles, sin movimiento de entrada activo. |

## Verificación y límites honestos

Compilación offline final: código de salida 0, 637 KB, 2.135 archivos fuente incluidos. No se instalaron paquetes, descargaron recursos, iniciaron servidores, editaron repositorios, escribieron contratos canónicos ni crearon directorios de vista previa. El resultado usa CSS/JS en línea y fuentes locales incrustadas; la prueba del navegador detectó cero solicitudes HTTP(S) externas y cero errores de JavaScript en la página.

`contrast.py`: código de salida 0 — `contrast: 158 pairs checked in light and dark, all pass`.

`audit_mockup.py --widths 1280,390,768 --max-combos 240` final: código de salida 0; **288 renders / 288 planned combinations**, 9.594 mediciones de texto, 1.473 paradas de foco, sin muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

La primera auditoría completa detectó un problema de relleno de 11px en la miniatura para teléfono; se corrigió. La auditoría completa siguiente pasó; después de agregar el mecanismo alternativo para el foco al eliminar, se volvió a generar el HTML final y la auditoría completa volvió a pasar. El resultado anterior corresponde a ese HTML final. Un script de interacción inicial usó una espera fija demasiado corta antes de comprobar que se cerrara el diálogo; el script final espera el estado real y pasa sin cambiar el comportamiento del diálogo para satisfacer la prueba.

Validación de evidencia de `compare_directions.py` en una sola dirección: código de salida 0, `ok=true`, `evidence_ok=true`, sin selectores faltantes. Esto comprueba solo esta dirección; no se afirma nada sobre comparaciones por pares con las direcciones de otros diseñadores.

Recorrido final enfocado de Playwright: `INTERACTIONS: PASS — 13 groups; page_errors=0; external_requests=0`. Abarca búsqueda/filtro por ocasión, selección de miniatura, colocación, validación del nombre obligatorio, guardado pendiente y luego confirmado, edición de metadatos, cancelación/confirmación de eliminación y retorno del foco, reintento de guardado, modo de solo lectura/copia de contenido ajeno, guardado en la cuenta propia desde el contexto del personal, limpieza de la cuenta, separación local y copia en inglés. Prueba de movimiento a 120ms: 3 animaciones activas en modo expresivo, 0 con la opción del sistema para reducir movimiento, 0 con `?still=1`. Se inspeccionaron capturas en memoria: biblioteca clara a 1280px, biblioteca oscura a 390px, vista oscura de personal a 1280px y vista clara de guardar pieza a 390px. No se escribieron archivos de captura. También pasó una prueba de redistribución del contenido en inglés a 360px en tema claro y oscuro.

Las transiciones de estado, listas de fuentes, confirmaciones del servidor y geometría SVG están claramente etiquetadas como datos simulados. Este HTML no implementa ni demuestra persistencia del servidor, equivalencia tras recargar o en un segundo navegador, autorización de propiedad, aislamiento real al cambiar de cuenta, fallos de mutación en el backend, estado de guardado atómico, generación de miniaturas, fidelidad de escenas WebGL ni restricciones para eliminar cuentas. Esos aspectos siguen siendo cuestiones de implementación/integración. No se ejecutó ninguna suite de pruebas, tipos/lint o compilación de producción porque no se modificó ningún repositorio de producción.

## Preguntas abiertas, supuestos e impacto

P: ¿Editar una decoración también debe actualizar su composición, además del nombre y la ocasión? Esta exploración solo muestra la edición de metadatos; el propietario y el Planner deben definir la actualización del contenido antes de cerrar el contrato.

Confirmado: no se importan entradas locales del navegador; el acceso de personal a elementos externos es de solo lectura y colocarlos los copia a la escena propia del miembro del personal; solo el propietario modifica o elimina elementos del servidor; Master Designer y el personal acceden a la biblioteca mediante Taller; el estado de guardado espera la confirmación del servidor. No reabrir estas decisiones del propietario.

Supuestos: las ocasiones de ejemplo son General y Cumpleaños, tomadas de los controles existentes; los ejemplos neutrales son ilustraciones, no contenido real de clientes. Se conserva el comportamiento existente para insertar/copiar en la escena y la administración global del catálogo/de administración permanece separada. La restricción para eliminar cuentas pertenece a la superficie de cuentas y no constituye una pantalla adicional aquí. Las herramientas existentes y los destinos adyacentes mantienen sus contratos anteriores.

Impacto: solo SP-5; posible aporte para T5.1, la implementación de interfaz T5.3 y la revisión visual T5.5 tras la selección/finalización del propietario. La compatibilidad aún no se ha determinado, hasta que se elija una dirección; esta exploración sin aprobar no autoriza la implementación ni reemplaza ningún artefacto aprobado.
