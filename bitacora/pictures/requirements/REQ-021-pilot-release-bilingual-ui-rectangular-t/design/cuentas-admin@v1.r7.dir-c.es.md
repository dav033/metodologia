---
name: Mesa de pases
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
subplan: SP-2
requirements: [R1, R3, R16]
revision: r7.dir-c
owner: David
created: 2026-10-26
chosen_thumbnail: cuentas-admin@v1.r7.dir-c.html.candidate-2.html
---
# Mesa de pases — dirección C

## 1. Identidad y alcance

Exploración táctil de SP-2; pendiente de elección del owner. No es el contrato canónico ni una aprobación. Se entregan dos miniaturas, el TSX, su HTML autónomo y notas Markdown/JSON. Ningún archivo compartido, histórico, plan o repositorio productivo se modifica.

Fuentes: `SPEC.md`, `PLAN.md`, `PLAN.json` revisión 1 y `cuentas-admin@v1.r7.behavior.md`. Consumidores previstos: T2.1 fija el contrato elegido; T2.3 acceso/activación/restablecimiento/aviso; T2.4 Mi cuenta/menú; T2.5 cuentas/invitaciones/roles; T2.7 revisión visual. T2.2 aporta APIs, T2.6 comprueba el recorrido y T2.8 audita. Esta exploración no los autoriza a implementar.

La SPEC vigente prevalece sobre el R3 inicial de tres roles: las rondas 6–7 y T1.2 definen **cinco roles del sistema**, incluidos los tres planes, y un único rol por cuenta.

## 2. Concepto y gesto memorable

El acceso es una ficha material sobre la mesa de montaje. Una junta perforada une el talón de Pictures con el formulario: ambos comparten marco y eje. El cuarteto de globos se asienta con un resorte. En administración, las fichas de personas repiten la junta entre identidad y alcance; los permisos se seleccionan en alojamientos de herramienta.

La metáfora pertenece al producto: globos, cuartetos, montaje, herramientas y acceso a esas herramientas. Los alojamientos se pulsan con ratón, toque o teclado; no requieren arrastrar. La composición evita inventar un juego o pasos de negocio.

## 3. Miniaturas y elección

Se dibujaron **antes del TSX completo**, desde los requisitos:

- [C1 — Credencial inclinada](cuentas-admin@v1.r7.dir-c.html.candidate-1.html): credencial separada a la izquierda y formulario abierto a la derecha. Explora materialidad pero rompe el vínculo de los ejes y hace más decorativa la identidad.
- [C2 — Pase unido](cuentas-admin@v1.r7.dir-c.html.candidate-2.html): un marco con talón y formulario, perforación compartida y pie del mismo ancho. **Elegida** por su alineación, relación con el montaje y reflujo claro a una columna.

Las miniaturas son composiciones HTML deliberadamente pequeñas, no sustitutos del mockup de componentes reales. Su texto abreviado no define comportamiento. El mockup completo usa el constructor real; no fue necesario el mecanismo alternativo de fragmentos.

## 4. Por qué no es la composición por defecto

La identidad, el formulario y el pie no son tres bloques flotantes: forman un pase continuo. La perforación cambia de vertical a horizontal en teléfono. Cuentas usa fichas partidas por acceso, no un panel de control con métricas decorativas. Los permisos son piezas seleccionables dentro de grupos de herramientas. La navegación de administración ocupa una bandeja horizontal; en roles aparece un registro local y en móvil un selector.

No se encontraron notas `*dir*.md` de subplanes hermanos en los árboles de requisitos consultados al explorar. Por ello no se afirma una comparación entre direcciones aún ausentes. La continuidad demostrable es con el sistema existente de **ambos repositorios**, no con una supuesta dirección hermana: Geist, índigo, superficies claras/oscuras y vocabulario de Pictures. La geometría y el movimiento deberán compararse con las otras exploraciones cuando estén disponibles.

## 5. Ocho ejes y evidencia

| Eje | Decisión observable | Evidencia |
|---|---|---|
| Concepto | Pase de herramientas unido por una perforación; cuarteto de globos como material del Taller. | `.pass-stub`, `.material-mark`, `.plan-cell` |
| Composición | Acceso de 928 px con talón de 340 px; cuentas en tres zonas; roles en registro + tablero. | `.access-pass`, `.pass-body`, `.account-ticket`, `.roles-layout` |
| Navegación | Idioma en la cabecera pública; bandeja Cuentas/Roles y menú personal al entrar; selector de rol en móvil. | `.topline`, `.top-tools`, `#language`, `.tray-links`, `.role-picker` |
| Tipografía | Geist Variable incrustada; títulos 32/28 px, talón 32/20, nombres 16, campos 15, metadatos 12–13. | `.product h1`, `.stub-title`, `.person-data strong`, `.field` |
| Densidad y forma | Padding de marcos 24–40 px; controles 44–48 px; personas con 22–24 px; bordes de piezas de 10–24 px de radio. | `.pass-body`, `.form-surface`, `.person-cell`, `.permission-socket` |
| Componentes | Controles reales restilizados; perforación, fichas y alojamientos son composiciones propias. | `[data-slot=input]`, `[data-slot=checkbox]`, `.account-ticket`, `.permission-socket` |
| Color | Marca existente en primario y permisos elegidos; verde significa cuenta activa/éxito; estados incluyen texto. | `.press`, `.permission-socket[data-selected=true]`, `.ticket-status.active` |
| Movimiento | Asentamiento, giro elástico del cuarteto, encaje escalonado de personas y compresión al pulsar. Nunca oculta datos durante el viaje. | `.access-pass`, `.material-mark`, `.account-ticket`, `.press` |

El JSON incluye solo selectores que están presentes y son medibles en la vista inicial. El resorte de Motion del SVG aplica transforms mediante su motor; el comprobador de selectores no lo reconoce como una animación WAAPI/CSS. Por eso la evidencia automática de movimiento referencia el asentamiento CSS real y el control con transición de presión, y no ese SVG.

## 6. Sistema visual y componentes reales

Se leyeron `src/app/globals.css` y `src/app/login/LoginForm.tsx` en `t12` y `asesor`, además del uso de Geist en el layout. No se copió la maqueta anterior.

| Token Pictures | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--superficie-2` | `--secondary`, `--accent` | `#efe9f8` / `#242733` |
| `--texto` | `--foreground`, texto de superficies | `#1c1425` / `#f4f5f7` |
| `--acento` | `--primary`, `--ring` | `#6d3fe0` / `#9479ff` |
| `--sobre-acento` | `--primary-foreground` | blanco / `#120b24` |
| `--borde` | `--border` decorativo | `#e3daef` / `#383c48` |
| `--texto-tenue` existente | `--input`, borde interactivo reforzado | `#766c85` / `#8a91a0` |

Propuestas de esta exploración: reutilizar el color de texto tenue como borde de controles, sin oscurecer todos los separadores; texto secundario oscuro `#a5acb9` frente al `#9aa1ad` del repositorio. El índigo y el contraste de texto sobre primario se conservan. El mapeo se declara una vez por tema.

Inventario real: `shadcn:button` default/outline/ghost/destructive (`@/components/ui/button`); `shadcn:input` email/password/text (`@/components/ui/input`); `shadcn:checkbox` checked/unchecked/disabled (`@/components/ui/checkbox`, primitiva Animate UI); `shadcn:dialog` (`@/components/ui/dialog`); `shadcn:alert-dialog` destructivo (`@/components/ui/alert-dialog`); `shadcn:dropdown-menu` cuenta/acciones (`@/components/ui/dropdown-menu`, Animate UI). Diálogos y menús usan sus primitivas reales, no una simulación visual.

Son propios: ficha perforada, estado semántico con `role=alert/status`, tablero de permisos, esqueleto CSS y selectores nativos de producto. No se usa Bencho ni React Bits: no aportan una interacción necesaria a este trabajo. La fuente local `@fontsource-variable/geist` y SVG inline se incluyen en el HTML. Sin paquetes instalados ni recursos descargados.

## 7. Vistas, requisitos y recorridos

| Vista / entrada prevista | Trabajo principal y salida | Trazabilidad |
|---|---|---|
| Iniciar sesión `/login` | Correo y contraseña. Mensaje idéntico para credenciales incorrectas, cuenta desconocida, desactivada o bloqueada; siempre indica esperar quince minutos tras varios fallos. Éxito conserva la regla de página solicitada permitida → primera herramienta permitida → Mi cuenta. | R1, T2.3 |
| Activación `/activar/[token]` | Nombre y correo invitados visibles; contraseña de 8 caracteres o más dos veces; aviso v1 ES/EN según navegador y aceptación sin premarcar. Se inicia sesión al activar. Enlace usado/vencido pide otro al administrador. | R1, R16, T2.3 |
| Restablecimiento `/restablecer/[token]` | Nueva contraseña y confirmación; enlace de un uso y 24 h. Éxito remite a iniciar sesión. Mismo mensaje de enlace inválido que activación. | R1, T2.3 |
| Aviso `/aviso-datos` | Bloqueo hasta aceptar la nueva versión; permite salir. El menú de Mi cuenta queda deshabilitado mientras falta aceptar. La selección de vistas de la barra de Mockup es una herramienta de planificación. | R1, T2.3 |
| Mi cuenta `/mi-cuenta` | Identidad, rol, aviso aceptado y fecha; contraseña actual + nueva + confirmación. Feedback de cierre de otras sesiones y nueva sesión de este navegador. | T2.4 |
| Cuentas `/admin/cuentas` | Nombre, correo, empresa, rol, estado, último acceso; búsqueda por nombre/correo y filtros por rol/estado. Menú por ficha cambia rol, desactiva/reactiva, genera enlace o pide eliminar. | R1, R16, T2.5 |
| Invitar persona | Nombre, correo, empresa opcional y un rol; muestra herramientas que abre el pase. Duplica correo → error recuperable. Enlace visible una vez con copiar y alternativa manual. | R1, R16, T2.5 |
| Roles `/admin/roles` | Cinco roles de sistema de solo lectura y ejemplo de rol propio. Plan 1 chat/contador/catálogo; Plan 2 añade costos/explorador; Plan 3 añade Taller/trabajo propio; empleado añade áreas internas; administrador añade cuentas/roles/correcciones. | R3, R16, T2.5 |
| Crear / editar rol | Nombre y checkboxes por herramienta, contador derivado y guardar. Cero permisos → `ROL_SIN_PERMISOS`. Un rol propio con cuentas asignadas muestra razón y eliminación deshabilitada. | R3, T2.5 |

Los diálogos nativos seleccionables son menú personal, cambiar rol, desactivar/reactivar, generar enlace y eliminar cuenta. El último administrador no permite cambio de rol, desactivación o eliminación. Camila ejemplifica `CUENTA_CON_TRABAJO`; Mariana permite confirmar borrado escribiendo su correo. Se explica conservar gasto de IA sin datos personales como «Cuenta eliminada». Crear un enlace invalida anteriores sin usar **del mismo tipo**; invitación dura 7 días y reset 24 h. El menú de todas las páginas autenticadas identifica nombre y rol, y ofrece Mi cuenta y cerrar sesión.

## 8. Estados y datos

La barra conserva `Mockup`, `view`/Vista, `state`/Estado, `scene`/Diálogo, `theme`/Tema y Movimiento. No se sustituyen los selectores nativos. El selector de idioma del producto permite ES/EN y parte del idioma del navegador.

| Estado seleccionable | Manifestación |
|---|---|
| Normal | Datos ilustrativos y controles operables. |
| Cargando | Esqueletos dentro del área de trabajo, sin spinner central ni información fingida. |
| Vacío / sin resultados | Formularios vacíos; cuentas sin personas con CTA; roles sin roles propios conservando los cinco del sistema. Búsquedas sin coincidencia permiten limpiar filtros. |
| Error | Resumen recuperable; rechazo genérico de login; correo existente al invitar. Se mantienen campos. |
| Éxito | Confirmación de sesión, activación, contraseña, aviso, enlace creado, cambio de cuenta o rol guardado, según la vista. |
| Validación | Campos señalados; mínimo de contraseña y coincidencia al enviar; selección de al menos un permiso. |
| Enlace usado o vencido | Misma explicación en activación y restablecimiento, sin revelar cuál caso ocurrió. En otras vistas no aplica. |
| Sin permiso | Mensaje y camino a Mi cuenta; autorización real permanece en servidor. |
| Sin conexión | Sin afirmar guardado; campos conservados, reintentar y acciones de guardado deshabilitadas. |
| Acción protegida | Login mantiene el mismo rechazo genérico; cuentas/roles explican la protección correspondiente. |

Deshabilitado también se alcanza mediante consentimiento sin marcar, carga, email de confirmación incompleto, roles de sistema y rol asignado. Una combinación de selectores puede no ser aplicable a una vista; no inventa un caso de negocio nuevo. Datos obsoletos/parciales no se simulan como éxito: esta dirección no añade edición optimista ni resolución de concurrencia fuera del alcance de SP-2.

Cinco personas ficticias, una invitada y una desactivada; los totales y filtros derivan del mismo array. La vista previa de herramientas y el conteo derivan de los mismos permisos. Los nombres/correos enviados en invitación se reutilizan en su confirmación. No se envía correo ni se consulta ninguna API. La navegación de la barra remonta ejemplos y no persiste cuentas o roles.

## 9. Reflujo y accesibilidad

- **360–767 px:** margen exterior 20 px y padding de paneles 24 px; talón corto arriba, junta horizontal, una columna de formularios/permisos; ficha de cuenta apila identidad, acceso y acciones; selector nativo de roles. La cabecera puede envolver sin recortar.
- **768–1023 px:** talón de 270 px; cuentas en dos columnas y una franja de acciones; filtros en dos columnas; tablero de permisos en una columna.
- **≥1024 px:** pase de hasta 928 px, área de trabajo de hasta 1216 px con 32 px laterales; cuentas con tres zonas y roles en registro + tablero. Diálogos hasta 520 px; en teléfono ancho viewport menos 40 px, scroll interno y altura limitada.

Objetivos: WCAG 2.2 AA, texto 4.5:1 y bordes/foco 3:1, foco visible de 3 px, grupos semánticos `fieldset/legend`, etiquetas de todos los campos, errores y éxitos anunciables y estado expresado con texto además de color. Checkbox real animado, no checkbox visual nativo sin control del borde. Controles principales de 44–48 px y superficies de permiso enteras pulsables. El borrado usa AlertDialog real con fondo inerte; Cancelar devuelve el foco al botón de la persona. El teclado no depende de gestos de arrastre.

Reducir movimiento, Movimiento quieto y `?still=1` conservan contenido y acciones con feedback inmediato, sin viaje ni pulso de esqueleto. Los efectos finitos no se repiten; el esqueleto pausa al ocultar la pestaña. No hay efectos pesados continuos. No se afirma conformidad completa por haber pasado una auditoría; lectores de pantalla, zoom y backend requieren revisión del producto implementado.

## 10. Criterios visuales para comparar la dirección

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| C-01 | ≥1024 px | Acceso normal | Talón y formulario comparten un único marco de hasta 928 px. |
| C-02 | ≥1024 px | Acceso normal | El pie usa exactamente el mismo ancho y extremos del pase. |
| C-03 | 360–767 px | Acceso normal | La junta perforada aparece horizontal entre talón y formulario. |
| C-04 | Todos | Activación normal | El botón de activación está deshabilitado antes de aceptar el aviso. |
| C-05 | Todos | Enlace inválido | Activación y restablecimiento muestran el mismo mensaje para solicitar otro enlace. |
| C-06 | Todos | Error de inicio de sesión/protegido | Ambos rechazos contienen idéntico texto y la espera de quince minutos. |
| C-07 | ≥1024 px | Cuentas normal | Cada ficha distingue identidad, rol/estado y último acceso/acciones. |
| C-08 | 360–767 px | Cuentas normal | Esas tres zonas se apilan sin desplazamiento horizontal. |
| C-09 | 768–1023 px | Cuentas normal | Las acciones ocupan una franja debajo de las otras dos zonas. |
| C-10 | Todos | Eliminar con trabajo | CUENTA_CON_TRABAJO explica cómo conservar el trabajo y el botón Eliminar está deshabilitado. |
| C-11 | Todos | Rol del sistema | Se muestran casillas no editables y el texto Sistema · solo lectura. |
| C-12 | 360–767 px | Roles normal | Un selector nativo reemplaza el registro de seis botones. |
| C-13 | Todos, ambos temas | Normal | Los bordes de los campos de entrada, selectores y casillas se distinguen de sus superficies con una relación de contraste de 3:1 o más. |
| C-14 | Todos | Movimiento reducido | La ficha y los permisos están en su posición final, con acciones que se pueden habilitar de forma equivalente. |
| C-15 | Todos | Rol sin permisos | Guardar sin permisos produce ROL_SIN_PERMISOS. |
| C-16 | Todos | Cancelar diálogo | El foco vuelve al botón de acciones de la persona que abrió el diálogo. |

## 11. Construcción, auditoría e impacto

Compilación offline real ejecutada mediante ruta absoluta:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/cuentas-admin@v1.r7.dir-c.tsx --out <design>/cuentas-admin@v1.r7.dir-c.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <design>/cuentas-admin@v1.r7.dir-c.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <design>/cuentas-admin@v1.r7.dir-c.html --max-combos 540
```

Constructor: HTML autónomo de ~869 KB; librerías reales y Geist incrustadas, sin conexión de red. Contraste de tokens: `contrast: 158 pairs checked in light and dark, all pass`.

La auditoría inicial, basada en una muestra, detectó un rótulo aislado y el menú personal demasiado bajo. Se retiró el rótulo redundante, se ajustaron la altura y el relleno propios del activador real, y se volvió a generar la vista. También se mejoró la selección móvil de roles. Auditoría completa tras esos cambios: **540/540 renderizados**, 14 292 mediciones de texto y 1 633 paradas de foco.

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Ese es el resultado final sobre el HTML entregado, incluida la confirmación del rol al seleccionar Éxito. El medidor de evidencia devuelve `evidence_ok: true` para todos los selectores del JSON.

Se ejecutaron pruebas de interacción con Playwright, sin escribir datos de prueba: consentimiento y activación; búsqueda; bloqueo de eliminación cuando hay trabajo; retorno del foco; cambio a Plan 3; cero permisos; cinco roles del sistema con conteos derivados; igualdad del rechazo de inicio de sesión. Todas pasaron. Se comprobó el reflujo normal en las nueve vistas a 390, 768, 1024 y 1280 px: 36 combinaciones, sin desbordamiento. También pasaron 18 combinaciones de vista/tema a 360 px, la confirmación de eliminación por correo y la respuesta del selector Éxito en roles. No hubo errores de ejecución ni solicitudes http/https en esas pruebas. Se inspeccionaron capturas en memoria a 1280/390 px, en temas claro y oscuro, incluidas las vistas de acceso, activación larga, cuentas, roles y eliminación. No se crearon archivos de capturas fuera del alcance.

Los selectores del JSON se verificaron con el medidor real de direcciones durante esta exploración; no se ejecutó ni se afirma la comparación A/B/C, ya que faltan las otras dos direcciones asignadas. Las comprobaciones de la maqueta no prueban la autenticación, 403, la invalidación de tokens, las sesiones, la persistencia, la anonimización ni el envío de invitaciones; estos aspectos corresponden a T2.2/T2.6/T2.8.

Si el owner elige esta dirección, la adaptación visual afecta a T2.3, T2.4, T2.5 y T2.7. Clasificación: **cambio visual incompatible con una composición centrada en tarjeta**, por la estructura adaptable y la navegación; se conservan los comportamientos de la base compartida. No hay cambio de versión canónica ni impacto autorizado sobre otros subplanes. La persona finalizadora elegida escribirá el contrato de doce secciones después de la selección.

## 12. Preguntas y límites abiertos

Q: ¿Cuál es la razón social definitiva para [RESPONSABLE] del aviso de datos? Responsable: owner y revisión legal de Sempertex.
Q: ¿Qué correo/canal debe reemplazar [CONTACTO] en ambos idiomas? Responsable: owner y revisión legal de Sempertex.
Q: ¿Cuál es la URL aprobada para [ENLACE A POLÍTICA]? Responsable: owner y revisión legal de Sempertex.
Q: ¿El catálogo de T1.2 confirma esta agrupación visual de permisos o desglosa Taller, sus herramientas y trabajo propio en más opciones? Responsable: Planner/SP-1; el contrato final debe referenciar el catálogo exacto y no los identificadores ilustrativos del TSX.

Confirmado: acceso por invitación sin registro público; cinco roles de sistema; una cuenta/un rol; 8 caracteres; invitación de 7 días/restablecimiento de 24 h; protección del último administrador y del trabajo guardado; aviso versionado y aceptación obligatoria. La vista ES/EN demuestra el reflujo y el texto del aviso según el navegador, y no cambia los hitos de traducción del plan.

El texto legal de la maqueta sirve para visualizar el aviso y sus marcadores de posición: no se presenta como redacción legal aprobada ni sustituye el aviso completo que muestre T2.2. La exploración no añade políticas de negocio. La aprobación de la dirección y del contrato sigue pendiente del owner.
