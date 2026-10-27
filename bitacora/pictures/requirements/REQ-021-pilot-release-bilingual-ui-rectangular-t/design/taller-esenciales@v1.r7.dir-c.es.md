---
name: Molde de montaje
contract: taller-esenciales@v1
revision: r7
direction: C
status: exploration (not a contract, not approved)
seed: Tactile/playful — material and tool metaphors, direct manipulation, spring and press feedback
---

# Molde de montaje — direction C

Exploración para SP-3 (R9 mesas rectangulares, R10 exportación GLB a Blender, R11 grupo Backing). La fuente de comportamiento compartida es `taller-esenciales@v1.r7.behavior.md`; esta nota no la modifica. Maqueta:
`taller-esenciales@v1.r7.dir-c.html`, entrada `taller-esenciales@v1.r7.dir-c.tsx`.

## Concepto

Un decorador arma un evento como un taller prensa el látex en un molde: cada tipo de mesa y cada elemento de Backing es una **ranura de silueta** en un único molde blando de silicona, y la composición se asienta en un pozo de escena redondeado a su lado.
Al presionar una ranura, la pieza se coloca en su tamaño real por defecto (rectangular 240 × 90 × 75 cm) y se abre el inspector existente; las sillas se acomodan de forma independiente alrededor de la mesa, una línea de medición se despliega debajo de ella, y la lista y la exportación GLB leen del mismo modelo simulado. La pantalla responde «¿qué cabe, a qué tamaño y qué necesito llevar?».

## Movimiento memorable

**Siluetas que se presionan.** El catálogo no es una cuadrícula de tarjetas con imágenes; cada pieza es su propio contorno presionado en una ranura redondeada (redonda, cuadrada, ovalada, cóctel, media luna, serpentina, en U, más los siete elementos de Backing). Al pasar el cursor, la ranura se eleva e inclina; al presionar, sus esquinas se comprimen (el border-radius cambia con un resorte), y la escena responde con un chasquido tipo látex de la mesa (compresión → sobreimpulso → asentamiento) y las sillas acomodándose una por una.

## Por qué no la opción por defecto

- Sin barra lateral, sin tarjetas de KPI, sin morado: la lógica de color es molde azul frío + acción rojo cereza, con látex girasol y rosa metalizado únicamente en los materiales de la escena. El tema oscuro es azul marino con acciones en rosa metalizado de alto contraste.
- La tipografía tiene carácter: display redondeado ExtraBold (M PLUS Rounded 1c) para títulos y el objeto `.glb`, Adwaita Sans para el texto de trabajo, cifras tabulares para las medidas.
- El movimiento es una gramática táctil (resortes de compresión/asentamiento), no fade-up: distinta de los cortes rápidos de las direcciones hermanas (A, registro teal/reglado) y de los barridos espaciales (B).
- Registro de estilos: `cuentas-admin r7 dir-c` (Mesa de pases) y `proyectos r8 dir-c` (Archivo de muestrarios) usan contadores de pases y muestras archivadas; esta dirección no repite su composición ni su navegación.

## Ocho ejes

| Eje | Esta dirección (presente en la maqueta) |
|---|---|
| Concepto | Molde de montaje de silicona reutilizable: las siluetas son piezas que se encajan alrededor de una composición a escala real, con contornos de látex y foil. |
| Layout | Un molde amplio `.work-mould` (1.25 : 1): pozo de escena `.scene-frame` (radio de 64px) a la izquierda, `.slot-grid` de dos columnas a la derecha; ≤1050px más compacto; ≤760px se apila con las herramientas primero y la escena después. |
| Navegación | Cuatro pestañas de pestillo `.mould-nav` (Mesas, Backing, Lista, Exportar) con una forma moldeada para la activa; al agregar una mesa se entra al Inspector (Mesas sigue como actual); «Tipos» regresa. |
| Tipografía | Display redondeado Mplus 1c ExtraBold clamp(36px, 4.4vw, 62px), encabezados de sección de 24–25px, cuerpo en Adwaita Sans de 14–15px, medidas tabulares de 18–20px. |
| Densidad / forma | Generosa: relleno del molde de 28px en escritorio, 20px en teléfono; ranuras de 132px+ con radios asimétricos de 28/14px; objetivos de 44px+; reglas de tabla para la lista. |
| Componentes | `Button`, `Input`, `Skeleton`, `Dialog` (escala y ayuda de exportación) reales de shadcn/Base UI, resorte de Motion; siluetas SVG y escena personalizadas; selects nativos para tipo de mesa, ubicación e idioma. |
| Color | Claro: fondo `#e4eef4`, acción/selección cereza `#a11935`, látex `#efcb56`, foil `#eab0bb`. Oscuro: azul marino `#15252e`, acción `#ff97ac`. Los roles del proyecto se asignan una vez por tema. |
| Movimiento | Encaje y liberación elásticos: el molde se asienta (620ms, sobreimpulso cubic-bezier(.2,1.5,.45,1)), las ranuras se asientan con desfases de 45ms, los globos se asientan y luego flotan (4.2s, en pausa fuera de pantalla/ocultos/con hover), la mesa chasquea (compresión de 720ms), las sillas encajan con 35ms de separación, la línea de medición se despliega, Backing se asienta, el estado se sella, la caja de exportación se mece, el skeleton respira. Presión/hover/foco 120–200ms. Los perfiles sutil/natural acortan; el movimiento reducido y `?still=1` eliminan toda animación con el mismo contenido. |

## Miniaturas

- **Candidato 1 — Molde de montaje** (`…dir-c.html.candidate-1.html`): un molde que contiene el pozo de escena y las ranuras de siluetas lado a lado. **Elegido.**
- **Candidato 2 — Banco de inflado** (`…dir-c.html.candidate-2.html`): un escenario arqueado con un manómetro de bomba para las sillas y una bandeja inferior tipo cajón con piezas de almohada. Descartado: la bandeja inferior se convierte en un dock que oculta las medidas y la lista en teléfonos, y el manómetro duplica el conteo de sillas del inspector.

## Vistas y estados cubiertos

Vistas: Mesas, Inspector, Backing (búsqueda, siete elementos con dimensiones), Lista de compras (cantidades y dimensiones, sin precios de alquiler), Exportar GLB. Estados: Normal, Cargando (skeleton), Vacío, Error (reintento, escena intacta), Éxito, Capacidad excedida (8 de 40 sillas; la lista cuenta las sillas colocadas), Medida inválida (conserva el último tamaño válido), Sin permiso (edición deshabilitada). Diálogo: «Escala y exportación» (cm → m). El select de idioma muestra una vista previa del texto en inglés.

## Auditoría (resultados reales, 2026-10-27)

- Build: `bitacora.py components mockup build` → compilado sin conexión (6440 KB, 2126 archivos fuente).
- `contrast.py`: 158 pares verificados en claro y oscuro, todos aprueban.
- `audit_mockup.py`: 180 renderizados, 8100 mediciones de texto, 952 paradas de foco —
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- `compare_directions.py` contra r7 dir-a/dir-b: **no ejecutado** — sus notas JSON aún no existían. Ejecutado contra
  r6 dir-a, r6 dir-b y este archivo: `ok: true`, similitud de layout 0.018 / 0.023, sin tipografía, navegación
  ni movimiento compartidos; `evidence_ok: true`, se encontró cada selector del JSON y cada selector de movimiento está animado.
- Capturas inspeccionadas a 1280 (Mesas en claro, Inspector + Capacidad en oscuro, Lista en oscuro) y 390 (Backing en claro,
  Exportar + Éxito en oscuro).

## Límites y preguntas abiertas

- La escena es una ilustración de composición 2D; el producto mantiene su visor 3D. Las siluetas son SVG personalizados.
- P: ¿Las tarjetas de tipo de mesa deben mostrar solo la silueta, o también la miniatura 3D existente cuando esté disponible?
- P: ¿Un select de ubicación de sillas (alrededor / un lado / dos lados / cabeceras / frente al escenario) está dentro del alcance de SP-3, o el inspector existente ya lo cubre sin cambios?
- P: ¿La vista de exportación debe indicar la escala cm → m en línea (como aquí) o solo en el diálogo de ayuda?
