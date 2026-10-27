# cuentas-admin@v1 · r8 · dirección A — Mesa de acreditación

Estado: **exploración** (no es un contrato ni está aprobada). Base: operativa/editorial: información de trabajo densa,
jerarquía tipográfica asimétrica y secuenciación cinética precisa. Fuente del comportamiento:
`cuentas-admin@v1.r8.behavior.md` (SP-2, R1/R3/R16); nada de lo que aparece aquí la modifica.

Archivos: `cuentas-admin@v1.r8.dir-a.tsx` (entrada) → `cuentas-admin@v1.r8.dir-a.html` (compilación sin conexión),
`cuentas-admin@v1.r8.dir-a.json` (ejes + evidencia de selectores), miniaturas `….html.candidate-1.html` /
`….html.candidate-2.html`.

## Concepto

Antes de un evento de Sempertex, alguien se encarga de la mesa de acreditación: una lista de personas identificadas,
lo que cada una puede usar y las acreditaciones que se entregan una sola vez. Las pantallas de acceso de Pictures son esa mesa, con el estilo de una página de redacción. Cada
persona es una línea delimitada en un registro; cada permiso queda escrito con una marca o una cruz; cada invitación
o enlace de restablecimiento es una acreditación de un solo uso con un comprobante sellado. El único objeto sobre la mesa es un globo metalizado
que oscila y sigue haciéndolo lentamente: el mundo del producto en una pieza discreta.

**Elemento memorable:** el título condensado de gran tamaño (*Accesos*, *Roles*, *Tu próximo montaje.*), con un tamaño de 108–112px
frente a datos tabulares de 12px, y una línea gruesa de tinta que se dibuja al aparecer; toda la hoja entra de lado con
cada cambio de vista, como una página que se va componiendo.

**Por qué se aparta de la opción predeterminada:** la versión segura de estas pantallas sería una tarjeta centrada sobre una página blanca con tinte morado y una
tabla de datos genérica. Esta dirección elimina la tarjeta centrada (el inicio de sesión se convierte en una composición tipográfica de dos columnas), elimina
el morado (papel salvia + un acento viridiano), usa una tipografía grotesca condensada para títulos con un contraste de escala marcado y
convierte la administración de cuentas en un registro con una barra de acciones acoplada, en lugar de menús por fila.

## Ocho ejes

| Eje | Qué incluye la maqueta |
|---|---|
| Concepto | Mesa de acreditación de eventos con estilo de redacción: líneas de registro con nombres, permisos por escrito, acreditaciones de un solo uso y un globo metalizado. |
| Diseño / composición | Cabecera → título de 108px con contador monoespaciado y globo → línea de tinta de 3px → pestañas → filtros → barra de trabajo de la persona elegida → registro de cinco columnas (persona/empresa, rol, estado, último acceso, acción). Roles: columna de índice + hoja de permisos. Inicio de sesión, activación, restablecimiento y aviso: composición tipográfica a la izquierda, formulario con líneas a la derecha; apilados en el teléfono. |
| Navegación | Dos pestañas de texto alineadas a la línea base (Cuentas, Roles) con subrayado dibujado, encabezado corriente monoespaciado a la derecha y resumen de cuenta en la esquina (nombre + rol), que abre Mi cuenta y Cerrar sesión. Las acciones son botones con nombre en la barra; no hay barra lateral, acople, tarjetas ni menús de tres puntos. |
| Tipografía / escala | Bricolage Grotesque Variable 800 al 76 % del ancho (108px en administración, 112px en autenticación, 64px en tableta, 58px en teléfono; encabezados de sección de 34px, títulos de diálogo de 30px); texto de trabajo en Instrument Sans Variable de 13–17px; datos tabulares monoespaciados en JetBrains Mono Variable de 12px para encabezados corrientes, contadores y marcas de tiempo. Todo está incrustado como URI de datos. |
| Densidad / forma | Seis personas por registro, 20px de relleno por fila, esquinas de 2px, controles de 44px, líneas de 1px más una línea de tinta de 3px; márgenes laterales de 48px en escritorio, 28px en tableta y 20px en teléfono. |
| Componentes distintivos | shadcn Button/Input/Skeleton; casilla de Animate UI, Dialog y AlertDialog con estilo cuadrado; selectores nativos (filtros, idioma del aviso, rol); registro personalizado, barra de trabajo, hoja de permisos con marcas y cruces como evidencia, sello de comprobante de acreditación y globo metalizado en CSS. |
| Lógica de color | Propuesta. Claro: papel salvia `#edf1ec`, tinta `#111c17`, tarjeta `#ffffff`, acento viridiano `#0a5a4c` solo en la acción principal, el anillo de foco, el contador, la barra de la fila elegida y el subrayado del registro. Oscuro: noche de bosque `#0d1412` / `#17211d`, texto `#ecf3ef`, acento menta `#83d8bf`. Estados: hoja `#2f6413`/`#b9e394` activo, ámbar `#7a4d00`/`#f1cf7c` invitado, rojo `#a8202f`/`#ffabb6` destructivo, gris desactivado. Bordes de controles `#5c6d64` / `#8ea69a`. Se conservan los nombres de rol de Pictures (`--primary`, `--muted-foreground`, …); los valores no constituyen una migración de tokens. |
| Movimiento | Una familia de aceleración `cubic-bezier(.76,0,.24,1)` (registro tipográfico). Consulta la lista siguiente. |

### Inventario de movimiento (predeterminado expresivo; escala natural/sutil)

1. **Registro del título** — `h1` se desliza 22px y deja de estar inclinado desde −7° (580 / 340 / 210ms).
2. **Línea de tinta y subrayado del registro** — `.desk-nav:before` y `.register-head:after` aparecen mediante `scaleX`.
3. **Entrada de vista** — `.sheet` se vuelve a identificar por vista y entra 28px de lado en cada cambio de Vista.
4. **Registro de filas** — las filas `.person` se deslizan 14px con intervalos de 35ms; los puntos de estado crecen (`scaleY`) después.
5. **Acoplamiento de la barra** — `.working-line` y la hoja de permisos se asientan 9px.
6. **Sello de estado** — los avisos se vuelven a identificar por Estado y aparecen estampados desde −2°; el comprobante de acreditación de un solo uso hace lo mismo.
7. **Entrada de diálogo** — los diálogos y alertas entran con un desplazamiento lateral de 22px.
8. **Globo metalizado** — oscila de −12° a +13° y luego a 10°; después se balancea suavemente cada 7.2s. Se pausa cuando la pestaña está oculta.
9. **Microinteracciones** — los botones se elevan 2px al pasar el cursor, se presionan 1px y los iconos de flecha se desplazan ligeramente; el subrayado de pestañas aparece al pasar el cursor;
   las filas de roles se desplazan 3px. Los controles responden en 160 / 140 / 90ms.

Movimiento reducido (`prefers-reduced-motion`, `?still=1` o Movimiento = Quieto): se eliminan todas las animaciones y transiciones,
incluido el balanceo infinito; el contenido final, el foco y la respuesta aparecen de inmediato. Todo el movimiento
usa solo transformaciones, así el texto mantiene el contraste completo durante la animación.

## Vistas, estados y diálogos incluidos

- **Vista:** Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Aceptar nuevo aviso, Mi cuenta.
- **Estado:** Normal, Cargando (filas de esqueleto), Vacío / sin resultados, Error (un error de inicio de sesión siempre añade la espera de 15 minutos), Éxito, Validación (incluido `ROL_SIN_PERMISOS`), Sin permiso, Enlace usado o vencido (mismo mensaje para invitación y restablecimiento), Sin conexión, Cuenta con trabajo guardado (`CUENTA_CON_TRABAJO`).
- **Diálogo:** Invitar persona, Enlace de un uso (se muestra una sola vez, botón para copiar, alternativa si falla el portapapeles), Cambiar rol (protección del último administrador), Eliminar cuenta (escribir el correo; se rechaza si hay trabajo guardado o si es el último administrador; ofrece desactivación), Desactivar o reactivar, Regenerar enlace (invalida los enlaces anteriores sin usar del mismo tipo), Ayuda de acceso.
- Las duraciones mostradas provienen de la ronda 6 de SPEC: invitación, 7 días; restablecimiento, 24 h; contraseña, ≥ 8; bloqueo, 15 min. Las personas, empresas y marcas de tiempo son ilustrativas.

## Miniaturas

- **Candidato 1 — mesa de registro (elegido):** cabecera, título grande + contador, línea de tinta, pestañas y registro con líneas y la persona elegida resaltada. Responde la pregunta de la pantalla («¿quién tiene acceso y qué puedo hacer con esta persona?») en la primera vista y se adapta a roles e inicio de sesión.
- **Candidato 2 — barra lateral de elenco:** una columna izquierda «Elenco» con el título y las pestañas, una placa con la invitación más reciente y el directorio debajo. Rechazado: la placa empuja el registro por debajo del primer pliegue y la columna angosta del título desaprovecha la tipografía expresiva.

Ambas miniaturas se dibujaron antes de la compilación completa; después de compilar, se actualizaron su paleta y su combinación tipográfica a las opciones finales de salvia/viridiano y Bricolage/Instrument/JetBrains para que reflejen el mismo universo visual.

## Auditoría (resultados reales, 2026-10-27)

- Compilación: `bitacora.py components mockup build` → `cuentas-admin@v1.r8.dir-a.html` (1048 KB, 2150 archivos fuente, sin conexión).
- `kit/contrast.py`: **158 pares verificados en modo claro y oscuro; todos aprobados**.
- `kit/audit_mockup.py`: 476 renderizados (476 previstos), 12830 mediciones de texto, 1092 paradas de foco —
  **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**.
  Una ejecución anterior falló en alineación (una etiqueta de permiso larga se ajustaba en 390px); se corrigió al trasladar el alcance de Taller 3D al título de su grupo.
- `kit/compare_directions.py` (A, B, C): los pares A↔B y A↔C están bien (similitud de diseño 0.012; tipografía, navegación y movimiento diferentes); todos los selectores de evidencia de A coinciden. El resultado general informa `ok: false` porque el JSON de la dirección C nombra selectores que no están en su HTML (`.access-mat`, `.tool-tab`, `.balloon-piece`, …): es un problema de C, no de A.
- Se inspeccionaron capturas de pantalla en 1280 (Cuentas claro/oscuro, Roles oscuro, Iniciar sesión, diálogo Invitar, Mi cuenta) y 390 (Cuentas claro, Activar oscuro).

## Preguntas abiertas para el propietario

- P: ¿Es aceptable para el piloto una paleta ajena a Pictures (papel salvia + acento viridiano, menta en modo oscuro), o el contrato final debe volver a los tokens mauve de Pictures?
- P: Para quienes no tienen permisos de administración, ¿el menú de cuenta de la esquina es la única ruta a Mi cuenta (sin pestañas visibles), como se muestra aquí?
- P: ¿El administrador ve las cuentas como un registro con una sola barra de acciones acoplada (elige una fila y luego actúa), o prefiere acciones en cada fila?
- P: ¿El selector de idioma del aviso de datos debe permanecer visible (con el idioma del navegador como opción predeterminada) o estar oculto para mostrar solo el idioma del navegador?
- P: ¿El registro de cuentas debe mostrar el gasto de IA o el recuento de trabajo guardado de cada persona, para que el motivo por el que se rechaza una eliminación sea visible antes de abrir el diálogo?
