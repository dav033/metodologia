import assert from "node:assert/strict";
import { ideasEstrictasDeCategoria, ideasGuiadas, ideasRealesDeOpcion, ideasYaVistas, tematicaFielAlCliente } from "../../src/lib/ia/guiado/ideas-guiadas";
import { esPedidoParecidasAFoto, ideasParecidasAFoto, pedidoDeIdeas } from "../../src/lib/ia/guiado/pedido-ideas";

/**
 * Probador (2026-10-07, guiada-20261007-000432-mi8qhp): boda «elegante en blanco y dorado».
 *  1. `guardar_brief_guiado` guardó «Blanco, dorado y nude» (nude no lo pidió).
 *  2. La búsqueda dio 1 exacta y no completó con las parecidas reales de boda.
 *  3. Con la foto de una columna, «Prefiero ver ideas parecidas» devolvió el mismo aro (`conPieza: 0`).
 * Sin coste: la biblioteca real, sin modelo ni red.
 *
 *   npx tsx scripts/test/test-ideas-boda-guiada.ts
 */

const BODA = "me caso en diciembre, quiero algo elegante en blanco y dorado para la entrada del salón";

// ── 1. La temática guardada es la del cliente ───────────────────────────────────────────────────────────────────────
assert.deepEqual(tematicaFielAlCliente("Blanco, dorado y nude", [BODA]), { tematica: "Blanco y dorado", quitados: ["nude"] });
assert.deepEqual(tematicaFielAlCliente("Elegante blanco y dorado", [BODA]), { tematica: "Elegante blanco y dorado", quitados: [] }, "lo que dijo, igual");
assert.equal(tematicaFielAlCliente("Romántico rosa y dorado", [BODA]).tematica, "Romántico blanco y dorado", "el estilo queda, los colores son los suyos");
assert.equal(tematicaFielAlCliente("Unicornio rosa y lila", ["cumple de mi hija de 6, le encantan los unicornios"]).tematica, "Unicornio", "sin colores dichos, solo el motivo");
assert.equal(tematicaFielAlCliente("Rosa y azul", ["unicornio en rosa, lila, celeste y dorado"]).tematica, "Rosado, lila, celeste y dorado", "con el tono que dijo («celeste», no «azul»)");
assert.equal(tematicaFielAlCliente("Blanco, dorado y nude", ["Blanco, dorado y nude"]).tematica, "Blanco, dorado y nude", "si eligió esa temática en las opciones, es suya");

// ── 2. Categoría estricta: solo diseños de boda que cumplen lo pedido, sin relleno con parecidas ─────────────────────
// (REQ-018: antes se completaba hasta tres con «parecidas»; ahora cada resultado es una coincidencia real.)
const IDEA_ARO = "deco-real-28-aro-blanco-dorado-y-nude";
const IDEA_SEMIARCO = "deco-real-13-images-28"; // título «blanco y oro rosa», temática «Romántico rosa y dorado»: ambos colores literales
for (const [tematica, esperadas] of [["Blanco y dorado", [IDEA_SEMIARCO, IDEA_ARO]], ["Blanco, dorado y nude", [IDEA_ARO]]] as const) {
  const resultado = ideasEstrictasDeCategoria({ evento: "Boda", edad: 0, tematica, ultimoUsuario: BODA });
  const titulos = resultado.ideas.map((idea) => idea.titulo);
  assert.deepEqual(resultado.ideas.map((idea) => idea.id), esperadas, `${tematica}: solo diseños de boda con esos colores, sin parecidas (${titulos.join(" | ")})`);
  assert.ok(resultado.ideas.every((idea) => idea.coincidencia === "exacta" && idea.eventos.some((evento) => /boda/i.test(evento))), `${tematica}: exacta y de boda`);
}
const bodaSinPreferencias = ideasEstrictasDeCategoria({ evento: "Boda" }).ideas;
assert.ok(bodaSinPreferencias.length >= 3 && bodaSinPreferencias.every((idea) => idea.eventos.some((evento) => /boda/i.test(evento))), "boda sola: todos los diseños de boda, ninguno de otro evento");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Boda", edad: 0, tematica: "Elegante blanco y negro" }).ideas, [], "ningún diseño de boda blanco y negro: vacío, no parecidas de graduación");
// La búsqueda legacy y sus «parecidas» siguen para los demás consumidores (opciones, foto), pero no son la ruta de la categoría activa.
assert.ok(ideasGuiadas({ evento: "Boda", edad: 0, tematica: "Blanco y dorado", ultimoUsuario: BODA }).ideas.length >= 3, "legacy intacto");
// Las opciones siguen contando solo exactas (las parecidas no hacen que una opción «exista»).
assert.equal(ideasRealesDeOpcion("Blanco, dorado y nude", { evento: "Boda" }), 1);

// ── 3. «Prefiero ver ideas parecidas» a la foto de una columna ───────────────────────────────────────────────────────
const FOTO = "Muéstrame ideas parecidas a mi foto: Veo una columna en blanco mate y dorado cromado. ¿Te armo el plan con estas piezas?";
assert.ok(esPedidoParecidasAFoto(FOTO));
assert.equal(esPedidoParecidasAFoto("Muéstrame otras ideas con columnas"), false);
const pedido = pedidoDeIdeas(FOTO);
assert.ok(pedido?.piezas.includes("columna"));
for (const tematica of ["Blanco, dorado y nude", "Blanco y dorado"]) {
  const vistas = ideasYaVistas({ evento: "Boda", edad: 0, tematica, mensajesPrevios: [BODA, "algo así me encanta"] });
  assert.ok(vistas.has("deco-real-28-aro-blanco-dorado-y-nude"), "el aro ya lo vio");
  const parecidas = ideasParecidasAFoto({ texto: FOTO, piezas: pedido!.piezas, evento: "Boda", edad: 0, excluir: vistas });
  const titulos = parecidas.ideas.map((idea) => idea.titulo);
  assert.ok(!parecidas.ideas.some((idea) => vistas.has(idea.id)), `${tematica}: ninguna repetida (${titulos.join(" | ")})`);
  assert.ok(parecidas.ideas.length >= 3, `${tematica}: hay ideas parecidas (${titulos.join(" | ")})`);
  assert.ok(parecidas.conPieza >= 2, `${tematica}: primero las columnas (${titulos.join(" | ")})`);
  assert.ok(parecidas.ideas[0]!.piezas.some((pieza) => pieza.estructura.startsWith("columna")), `${tematica}: la primera es una columna`);
  assert.equal(parecidas.ideas[0]!.titulo, "Columnas negras y doradas", "columna y dorado antes que una columna de otros colores");
  assert.ok(!titulos.includes("Columna arcoíris con cinta dorada"), "una columna infantil no es parecida para una boda");
  if (vistas.has("deco-real-01-305")) assert.ok(!titulos.includes("Arco de entrada blanco y negro"), "ni el gemelo de una idea ya vista («Arco de entrada en blanco y negro»)");
  assert.equal(titulos[1], "Dos columnas rosa, lila y dorado", "las dos columnas con dorado antes que el semiarco lila sin dorado");
  assert.ok(parecidas.ideas.every((idea) => idea.coincidencia === "cercana"), "todas «Parecida»");
}

console.log("test-ideas-boda-guiada: temática fiel al cliente (sin «nude»), categoría de boda estricta sin relleno, parecidas a la foto sin repetir y con su estructura primero.");
