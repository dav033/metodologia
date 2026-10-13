# BalloonBuilder — tracker de ideas (ranking de notas.md)

Fuente: `notas.md` (sección «Top ideas to copy/adapt (ranked)», 1–15) y, para 16–19, las ideas «Idea for us» y la
sección FULL de Columns & Arches que no están en ese ranking. Estado comprobado en código del worktree
`C:/Users/davidt/Downloads/e7q` (rama `feat/hoja-armado`, desde origin/main 15c74eb7) el 2026-10-10.

Estados: **hecha** (verificada en código, con el archivo), **en curso**, **no empezada** (no verificada en código o sin
rastro: por defecto no empezada). Tamaño S/M/L según notas.md.

| # | Idea | Tam. | Estado | Nota |
|---|---|---|---|---|
| 1 | Shell de asistente por pasos (stepper + tarjeta de resumen + insignias bloqueadas) para /asistente | M | no empezada | Sin verificar en el taller 3D; es de la guiada, no del visor |
| 2 | Paleta → Sempertex con etiqueta de coincidencia y ΔE | S/M | no empezada | No hay ΔE en `src/lib` fuera de los lotes de ideas |
| 3 | Hoja de armado por capa: anillos numerados, color, cm y segundos de bomba | M | en curso | Esta tarea: `HojaArmadoEscena.tsx`, `hoja-armado*.ts` |
| 4 | Tarjeta de receta por ejemplo (conteo, código × cantidad, medidas, inflado) | S/M | hecha | `TarjetaReceta.tsx`, `receta-idea.ts` (c69e307b). Chips por ocasión/técnica no verificados |
| 5 | Cotización en 3 niveles + recargos (entrega, montaje, urgencia, exterior) | M | no empezada | Sin rastro en el taller |
| 6 | Vista de margen para el decorador (costo, horas, margen %) | M | no empezada | |
| 7 | Color de foto/invitación con pines arrastrables → Sempertex más cercano | M | no empezada | `BuscarPorFoto.tsx` busca por foto, no mapea color |
| 8 | Módulo de números y letras de mosaico (tipear → marco empacado + conteo) | L | no empezada | Fuera de alcance del perfil profesional (PRO backlog); solo hay detección |
| 9 | Perfiles de tamaño con nombre (taper, lápiz, champagne, botella…) | S/M | hecha | `SelectorPerfilTamano.tsx`, `usePerfilesTamano.ts` |
| 10 | Pintar globo a globo + contador en vivo por color | M | no empezada | Pintar existe (`herramientas-escena-pintar.ts`); el contador en vivo no verificado |
| 11 | Línea de helio en la lista (litros, tanques, cinta, 7 % de pérdida) | S | hecha | `SeccionHelio.tsx`, `helio-cinta.ts` (`PERDIDA_HELIO = 0,07`). PRO-02 del backlog está desactualizado |
| 12 | Presets de cámara (lente 26 mm) y de luz (cálida, fría, UV) en el visor | S | hecha | `ambiente-visor.ts` (`LENTES_VISOR`, `NOMBRES_LUZ_VISOR`), `SelectorAmbienteVisor.tsx` |
| 13 | Galería «plano vs. armado» en la portada | S | no empezada | |
| 14 | Exportar GLB o PNG transparente del módulo 3D | M | no empezada | La captura existe (`CapturaRender.tsx`); no es transparente ni GLB |
| 15 | Elementos de fondo: paneles brillantes, drapeados, número de paneles | M | no empezada | Hay escenografía (`escenografia.ts`); drapeados no verificados |
| 16 | Modo de relleno de techo con % de cobertura real | S/M | no empezada | notas.md, «Helium Ceiling» |
| 17 | Recetas listas como línea de producto (diseño + materiales + hoja) | S | no empezada | notas.md, «Idea for us» de Quote Builder |
| 18 | Silueta de anillo: editor de sección por pares de capas | L | no empezada | notas.md, «Ring column» (Cross-section shape editor) |
| 19 | Racimos orgánicos: racimos, estrellas explosivas, cadena de garland, globos grandes de acento | M | no empezada | Hay estructuras orgánicas (`organico.ts`); el toggle de racimos y cadena no verificado |
