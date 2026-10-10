# W4 training pass 1 - analysis (run 2026-10-10T09-30-37-267Z, haiku/cli, 2 refine turns, commit fb956d8c)

Sources: LEADERBOARD.md; `%LOCALAPPDATA%/demo-decoracion/entrenamiento/corridas/<run>/images (N).json` (only scores + final scene);
audit `corridas/registro/conversaciones/2026-10-10/entrenamiento-<run>-images-N.jsonl` (reader output, detection, every agent
call and tool call); code in `e7s` (scripts/entrenamiento, scripts/exp, src/lib/globos3d). Photos viewed. Read-only; nothing in the repo changed.

## 0. How the failure classes are produced (important)
- `capacidad_faltante` = the reader emitted >=1 piece of `tipo:"otro"` (lib-pasada.ts:111 `piezasOtro`; lib-fallos.ts:40). It is binary:
  any "otro" flags the photo, even pure scenery. 10/10 photos have one, so the class carries no ranking information yet.
- `compilacion` = `omitidas.length - otro` > 0 (lib-pasada.ts:113): pieces of the catalog that compile refused. Photos 25, 31, 33.
- Scores are FINAL only (no score before refine), so refine gain cannot be attributed. Run-to-run noise is large: photo 25 in run
  08-56 (1 turn, other commit) got proporciones 0.528 / IoU 0.59 with 88 detected / 664 armed; now 0.418 / 0.38 with 103 / 680.

## 1. What "capacidad_faltante" means per photo (21 "otro" pieces; agent text and notes)
| photo | "otro" pieces (reader) | real cause |
|---|---|---|
| 25 | pedestales acrilicos con platos; racimo rosa cromado cortado por el borde; florero con planta | catalog has `pedestales`/`base_pastel`; cropped cluster = racimo_piso off-frame; vase = scenery |
| 26 | panel de tela vino tras el arco (+ foil butterflies in notes) | catalog has `marco_tela`/cortinas; butterflies = no tool |
| 27 | mariposas rosas de papel; estante 3 niveles con cupcakes; cortinas de tela rosa | `carrito_dulces`, `cortina_flecos` exist; butterflies = no tool |
| 28 | mariposas de foil; globos sueltos y racimos al pie | loose balloons/clusters = `globo`/`racimo_piso` exist (mapping); foil = no tool |
| 29 | panel de castillo; arbol plateado; muneco de nieve+regalos; copos de nieve | true gaps (seasonal props, snowflake decals) |
| 30 | "ventanales y cesped detras del montaje, sin piezas de decoracion adicionales" | NOT a gap: reader noise, flagged anyway |
| 31 | flor de papel naranja; mesa dorada de postres con bandejas | `mesa_postres` exists (agent later added it itself); paper flower = no tool |
| 32 | "deck de madera y cerca de listones, casa y cielo" | NOT a gap: scenery noise |
| 33 | mesa alta dorada tapa redonda con dulces; synthetic "base_pastel sin mesa debajo" | `mesa_coctel`/`carrito_dulces` exist; support rule |
| 34 | cajas de regalo con monos; arcoiris de macrame | `mesa_regalos` exists (agent said so itself); macrame rainbow = no tool |

Ranking by number of photos (capability or tool actually missing, from agent text / omitidas / notes):
1. Fixed catalog backdrops cannot be recoloured and their colour is not shown (7 photos: 25,27,28,30,31,32,33). Tool errors:
   `cambiar_pieza ... «media luna» es un fondo fijo del catalogo: no cambia de medida ni de color` (25 x2, 31); agent: "ver_escena no
   muestra su color" (30), "el panel no tiene color propio editable, solo el texto lila" (28). Result: panel/pedestal colours stay wrong.
2. Catalog piece exists but the reader wrote "otro" (7 photos: 25,26,27,28,31,33,34; 9 pieces). The prompt tells it to use "otro" for
   "muebles que no estan en la lista" (prompt-lectura-foto.ts:52) but Haiku missed the mapping; the agent fixed it only in 31.
3. Wall/balloon decals: butterflies, paper flowers, snowflakes (5 photos: 26,27,28,29,31). `estampados.ts` has "mariposa"/"copo" prints but
   nothing places them on balloons or wall. Agent: "las mariposas doradas de foil no tienen formato en el taller" (26).
4. Scenery counted as missing capability (3 photos: 25 vase, 30, 32; 30 and 32 are flagged ONLY by this). Metric noise, not a gap.
5. Cake without a table/support (2 photos: 31,33): `no hay una mesa debajo donde apoyarlo` although a pedestal/white cylinder is under it.
6. Seasonal/boho props with no catalog entry (2: 29 tree/snowman/castle panel; 34 macrame rainbow).
7. Finish/colour gaps (3): "cobre cromado" not in the Sempertex table (32, 3 failed calls); confetti-gold balloons armed as plain "cristal" (27: "7 % frente al 14 %",
   30); range mismatch 160 vs 120 (see section 2).

## 2. "compilacion" cases (3: 25, 31, 33) - none is a tool-validation/schema problem
- 25: `Pieza 3 (racimo_piso): Grosor de 161 cm fuera de rango (12 a 160 cm).` The orchid cluster (174 cm wide) is dropped by compile; the agent then tries
  `agregar_pieza columna_organica grosor_cm 160` -> `ok=false ... va de 30 a 120 cm` (herramientas-escena.ts:180). Two different limits for the same shape; the
  final scene has a 119 cm cluster vs 174 cm in the photo (agent: "sale de 119 cm de ancho frente a los 174 cm").
- 31 and 33: `Pieza 5/4 (pastel): no hay una mesa debajo donde apoyarlo.` (sobre-mesa-lectura.ts:56). In both photos the cake stands on a pedestal / white
  cylinder; `tapaBajo` only considers tables with a top surface.
- 33 also lost one reader call: attempt 1 `piezas.3.tipo: Invalid discriminator value` (retry fixed it, +1 call).
- P-050 (ajustar_tamanos formats T-260/LOL-12): NOT reproduced. 62 scene-tool calls in the pass, 9 ajustar_tamanos, all `ok=true`; 7 failures
  (11 %): 3 fixed-fondo recolour, 3 colour-name not found, 1 range. No zod/schema errors in tools.

## 3. Why 664-734 armed vs 88-103 detected - the scene is too dense, the metric is also biased, the detector is roughly right
armed/detected: 25: 680/103 (6.6x), 26: 299/107, 27: 171/58, 28: 734/68 (10.8x), 29: 201/85, 30: 288/73, 31: 170/98, 32: 294/63, 33: 154/50, 34: 117/58.
- Detector is not undercounting. Counting by eye: photo 25 ~60-70 visible balloons (detector 103), 26 ~75-85 (107), 27 ~55 (58), 29 ~65-70 (85). If anything it
  overcounts 10-40 % (9 overlapping tiles: tile answers sum to 172 for photo 25, merged to 103) and it varies between runs (88 vs 103 for the same photo).
- The armed side counts every balloon of the 3D volume, hidden ones included: `armadoDeEscenaEnLaFoto` maps all `armada.globos` to discs with no occlusion
  test (scripts/exp/medir-proporciones.ts:44). The compiled garlands are thick: ver_escena for photo 25 "295 globos ... partes: trazo 125, trazo/relleno 170" (58 % filler);
  photo 32 "R-12 156 [...]" with 62 filler. A 3-layer garland yields ~3x the visible count even at perfect scale: photo 27 has scale ratio 1.00 and still 2.9x.
  So "globosArmados" is the wrong metric (visible count is the comparable one); IoU masks ignore hidden discs but median-diameter, silhouette and colour-zone terms do not.
- Scale inflation multiplies it. Balloon-derived scale replaces the reader's (medir-con-detecciones.ts:299-306; anchor = median tier assumed R-12, medir-tamanos.ts:151):
  read -> measured cm: 25 300->694, 26 200->498, 28 250->457, 32 220->490, 34 225->412, 33 300->417, 31 220->298, 30 300->352; 27/29 ~equal. In 6/10 it grows >=1.35x.
  Yet the reader's own references give ~200-230 cm in those photos ("pedestales ~75 cm ocupan 0,38" -> 197 cm; "panel 1,5 m ocupa ~0,7" -> 214 cm).
  Consequence: sala alto 687 cm (25), 485 (32), 451 (28), garland 431 cm tall (25), 399x329 cm with 714 balloons (28). `escalaPorMesas` only trusts tables
  (escala-por-muebles.ts:11), not panel_redondo/pedestales/tables-as-references, so the reference never corrects the balloons.
- Which is wrong? The scene (too big and too deep) AND the comparison (hidden balloons counted). Truth for scale is unknown; the two sources disagree 1.8-2.5x in 5 photos.

## 4. Agent behaviour
- Blind: no image or render in any of the 62 tool/model turns (message content types are text/tool_use/tool_result only). It compares text numbers with the textual reading,
  so it cannot see silhouette, position or colour zones. Result: photos 26 and 29 end after 1 turn with "No cambie nada" while colores = 0.145 / 0.338, zonas 0.00.
- `convergio` is true when a turn only calls `ver_escena` (lib-pasada.ts:~150), so 26, 29 and 33 count as converged after 1 turn; 25, 28, 31, 32, 34 hit the 2-turn cap still editing.
- False "tool unavailable": 33 (`la herramienta cambiar_pieza no esta disponible en esta sesion`, though it is in the list of 44 tools) and 32 (`ver_pieza no esta disponible`).
  Those two calls also show 128K input tokens vs ~65K normal and 3-4 internal CLI turns: probable transport artefact; needs a look at the cli transport (lib-transporte.ts).
- Wasted effort on unfixable things: 25 removes and re-adds media luna and tapete to "turn them lilac" (catalog colour wins; 4 calls, no gain); 31 removes/re-adds the pedestal,
  moves the cake; 32 oscillates R-24: 16 -> 14 -> 24 -> 10 -> 14 across 4 `ajustar_tamanos` while the total jumps 254 -> 273 -> 184 -> 291 -> 265 (filler rebalancing).
- Good: recolours of the garland to the measured weights worked (25, 30, 32: "Cambie ... pesos [29,20,25,24,2]"); 31 recovered `mesa_postres` and the cake from the catalog (better mapper than the reader);
  honesty note appended by the app when a claim failed (31). Refine does not move IoU/zones, the metrics it cannot see.

## 5. Ranked fixes (tool/engine only; no hand-modelled scenes)
Free test for all: the audit has the raw reader output (`respuesta_ia lectura_foto_escena ... responder_json`), `cache-deteccion/*.json` has the 10 detections, and the final
scenes are in the run JSONs; replay measure -> compile -> `puntuarEscena` offline, no API calls.
1. Recolourable fixed fondos + colour visible (S/M). Problem: 7 photos, panel/pedestal/media luna colours stuck. Change: `cambiar_pieza colores` for escenografia
   (generators already take `hex`: panelRedondo/mediaLuna/pedestales) and show colour in `ver_escena`/`ver_pieza`. Gain: fondos IoU + colores, est. +0.03-0.08 proporciones, removes 5 wasted agent calls per photo. Test: tool property test (recolour then armarEscena hex).
2. Visibility-aware armed metric + persist full `medida` (S). Problem: 664-734 vs 88-103 is hidden-balloon counting; diametro/zonasColor/silueta biased. Change: depth-sort
   and drop discs >60 % covered in `armadoDeEscenaEnLaFoto`; add `globosArmadosVisibles`; store bordes/silueta/diametro razon and per-turn score (turn 0 and each turn) in the record. Gain: honest baseline (expect armed/detected 2-4x -> ~1-1.5x); enables attributing refine. Test: replay the 10 saved scenes.
3. Scale policy (S/M). Problem: balloon anchor inflates scale 1.8-2.5x in 5 photos. Change: extend `escalaPorMesas` to catalog-sized fondos (pedestales, panel_redondo 150, tables) and
   cap the balloon-derived scale to 1.5x the reader's unless a fixed-size fondo agrees; log both. Gain: sala/garland back to ~300-430 cm, counts down 2-3x, silhouette/bordes up (est. +0.05-0.10). Test: replay measurement with cached detections; check scale vs reference list above.
4. Density calibration (M). Problem: filler makes 3 layers (58 % relleno in 25). Change: after measuring, set `racimos`/relleno so the PROJECTED visible disc count ~ detected count (loop in compile, no model); cap thickness at measured grosor. Gain: counts and diameter razon, est. +0.05 proporciones. Test: replay, assert visible/detected in 0.8-1.3.
5. Reader-to-catalog resolver (S/M). Problem: 9 catalog pieces written as "otro" in 7 photos. Change: deterministic post-pass mapping "otro" descriptions to catalog ids (postres/cupcakes -> carrito_dulces/mesa_postres, tela/cortina -> marco_tela/cortina_flecos, regalos -> mesa_regalos, racimos al pie -> racimo_piso/globo, pedestales -> pedestales); drop pure-scenery "otro" (ventanal, cesped, deck, cielo, casa). Gain: capacidad_faltante falls to true gaps; fondos IoU. Test: table test over the 21 saved descriptions.
6. Compile/tool consistency (S). Problem: racimo_piso 12-160 vs tool 30-120 (25); cake on pedestal rejected (31, 33). Change: clamp with a note instead of omitting; use one range constant; let pedestales/cylinders and mesa_coctel count as support in `tapaBajo`. Gain: removes all 3 `compilacion` flags. Test: compile the 3 saved readings, expect 0 omitidas.
7. Closed loop in refine (M). Problem: blind agent, false convergence. Change: tool `comparar_con_foto` (engine-computed diff vs measured reading/detection: scale, tier %, colour by zone, bbox, fixable vs fixed items) injected at turn start; `convergio` only if the diff is under thresholds; turns 2 -> 4 only while the diff shrinks; investigate false "tool unavailable" in the cli transport. Gain: zonas/colores in 26, 29, 30. Test: scripted fake transport + replay of saved turns.
8. `ajustar_tamanos` stability (S). Problem: total balloons swing 184-291 when one tier changes (32). Change: hold total and fillers fixed unless `total` is given; return requested vs resulting percent. Gain: fewer wasted turns. Test: property test on total +-5 %.
Also (cheap, not ranked): split `capacidad_faltante` into mapping_miss / true_gap / scenery_noise so the leaderboard ranks gaps; true gaps to schedule later: foil/paper decals (5 photos), seasonal props (2).
