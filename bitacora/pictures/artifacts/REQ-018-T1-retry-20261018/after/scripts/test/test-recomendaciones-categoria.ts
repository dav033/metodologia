import { strict as assert } from "node:assert";
import { bibliotecaVisible } from "@/lib/biblioteca-sempertex/biblioteca";
import { claveDeCategoria, vocabularioDeCategorias } from "@/lib/biblioteca-sempertex/categorias";
import type { DecoracionSempertex } from "@/lib/biblioteca-sempertex/esquemas";
import { analizarPolaridad, formasLexicasEstrictas } from "@/lib/biblioteca-sempertex/preferencias-texto";
import { preferenciasDeTexto, recomendarPorCategoria, TOPE_RECOMENDACIONES, type ConsultaCategoria } from "@/lib/biblioteca-sempertex/recomendaciones-categoria";
import { generoDeDecoracion, ideasEstrictasDeCategoria } from "@/lib/ia/guiado/ideas-guiadas";

/**
 * REQ-018 T1: recomendación estricta por categoría (evento). Sin red ni modelo: catálogos controlados que se construyen
 * a partir de un registro real (solo para tener una forma válida) y la biblioteca visible real para los anclajes.
 *
 *   node --import=tsx scripts/test/test-recomendaciones-categoria.ts
 */

const base = bibliotecaVisible()[0]!;
let contador = 0;
function idea(titulo: string, tematica: string, eventos: string[], extra: Partial<Pick<DecoracionSempertex, "edad">> & { id?: string } = {}): DecoracionSempertex {
  contador += 1;
  return { ...base, id: extra.id ?? `deco-real-fx${contador}`, titulo, tematica, eventos, edad: extra.edad === undefined ? null : extra.edad };
}
const ids = (catalogo: DecoracionSempertex[], consulta: ConsultaCategoria): string[] => recomendarPorCategoria(catalogo, consulta).ideas.map((item) => item.id);
const titulos = (catalogo: DecoracionSempertex[], consulta: ConsultaCategoria): string[] => recomendarPorCategoria(catalogo, consulta).ideas.map((item) => item.titulo);

const bodaBlancoDorado = idea("Arco blanco y dorado", "Blanco y dorado", ["Boda"]);
const bodaNegroDorado = idea("Arco negro y dorado", "Elegante negro y dorado", ["Boda"]);
const bodaBlancoDoradoNude = idea("Aro blanco, dorado y nude", "Blanco, dorado y nude", ["Boda", "Bautizo"]);
const bodaOroRosa = idea("Semiarco blanco y oro rosa", "Romántico oro rosa", ["Matrimonio"]);
const cumpleBlancoDorado = idea("Arco blanco y dorado de cumpleaños", "Blanco y dorado", ["Cumpleaños"]);
const comunion = idea("Arco celeste y blanco", "Celeste y blanco", ["Primera comunión"]);
const bautizoAzul = idea("Semiarco azul y blanco", "Azul y blanco", ["Bautizo"]);
const babyNina = idea("Guirnalda rosa", "Baby shower niña", ["Baby shower"]);
const babyNino = idea("Guirnalda azul", "Azul y plateado", ["Baby shower"]);
const dinos = idea("Semiarco de dinosaurios", "Infantil de dinosaurios", ["Cumpleaños"], { edad: { min: 2, max: 12 } });
const cumpleAdulto = idea("Columnas negras y doradas", "Elegante negro y dorado", ["Cumpleaños", "Graduación"], { edad: { min: 18, max: 70 } });
const halloween = idea("Sombrero de bruja", "Halloween negro, plata y naranja", ["Halloween", "Cumpleaños"]);
const futbol = idea("Columna de fútbol", "Fútbol verde lima, negro y blanco", ["Cumpleaños", "Fiesta de fútbol"]);
const navidad = idea("Aro navideño", "Navidad verde salvia", ["Navidad", "Novena navideña", "Fiesta de fin de año"]);
const primerCumple = idea("Guirnalda pastel", "Pastel rosa", ["Primer cumpleaños"]);
const catalogo = [bodaBlancoDorado, bodaNegroDorado, bodaBlancoDoradoNude, bodaOroRosa, cumpleBlancoDorado, comunion, bautizoAzul, babyNina, babyNino, dinos, cumpleAdulto, halloween, futbol, navidad, primerCumple];

// ── 1. Solo categoría: eventos completos y alias genuinos, en orden de la fuente, sin relleno ──────────────────────────
assert.deepEqual(ids(catalogo, { categoria: "Boda" }), [bodaBlancoDorado.id, bodaNegroDorado.id, bodaBlancoDoradoNude.id, bodaOroRosa.id], "boda + matrimonio (alias), nada de otro evento");
assert.deepEqual(ids(catalogo, { categoria: "casamiento" }), ids(catalogo, { categoria: "boda" }), "alias de la misma celebración");
assert.deepEqual(ids(catalogo, { categoria: "es para una BODA!" }), ids(catalogo, { categoria: "boda" }), "mayúsculas, signos y frase");
assert.deepEqual(ids(catalogo, { categoria: "Bautizo" }), [bodaBlancoDoradoNude.id, bautizoAzul.id], "bautizo no es primera comunión");
assert.deepEqual(ids(catalogo, { categoria: "primera comunión" }), [comunion.id], "comunión no es bautizo");
assert.deepEqual(ids(catalogo, { categoria: "Navidad" }), [navidad.id], "un solo resultado: sin relleno hasta cuatro o seis");
assert.deepEqual(ids(catalogo, { categoria: "novena" }), [navidad.id], "novena es Navidad");
assert.deepEqual(ids(catalogo, { categoria: "Fiesta de fin de año" }), [navidad.id], "etiqueta completa descubierta en la fuente");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños" }), [cumpleBlancoDorado.id, dinos.id, cumpleAdulto.id, primerCumple.id], "motivos ajenos (Halloween, fútbol) fuera; primer cumpleaños es cumpleaños");
assert.deepEqual(ids(catalogo, { categoria: "primer cumpleaños" }), [primerCumple.id], "la etiqueta más larga manda");
assert.ok(recomendarPorCategoria(catalogo, { categoria: "Boda" }).ideas.every((item) => item.coincidencia === "exacta"), "todo lo emitido es exacta");
assert.equal(recomendarPorCategoria(catalogo, { categoria: "Boda" }).estado, "coincidencias");

// ── 2. Categoría desconocida, ambigua, genérica o sin registros: vacío honesto (nunca fiesta general) ─────────────────────
for (const categoria of ["jubilación", "fiesta", "fiesta de empresa", "celebración", ""]) {
  const resultado = recomendarPorCategoria(catalogo, { categoria });
  assert.deepEqual(resultado.ideas, [], `«${categoria}»: sin diseños`);
  assert.equal(resultado.estado, "categoria_desconocida", `«${categoria}»: categoría desconocida`);
}
assert.equal(recomendarPorCategoria(catalogo, { categoria: "boda o cumpleaños" }).estado, "categoria_ambigua");
assert.deepEqual(ids(catalogo, { categoria: "boda o cumpleaños" }), [], "dos categorías competidoras no se adivinan");
assert.equal(recomendarPorCategoria([bodaBlancoDorado], { categoria: "graduación" }).estado, "vacio", "alias conocido pero sin registros: vacío, no desconocida");
assert.deepEqual(recomendarPorCategoria([], { categoria: "boda" }), { estado: "vacio", ideas: [] }, "catálogo vacío");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "spiderman" }), [], "personaje ausente: vacío, sin colores típicos");

// ── 3. Mismo color, otro evento: el evento manda ─────────────────────────────────────────────────────────────────────
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "blanco y dorado" }), [bodaBlancoDorado.id, bodaBlancoDoradoNude.id], "blanco Y dorado en boda: ni negro/dorado ni cumpleaños blanco/dorado; oro rosa no es dorado");
assert.ok(!ids(catalogo, { categoria: "boda", tematica: "blanco y dorado" }).includes(cumpleBlancoDorado.id));
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "Blanco, dorado y nude" }), [bodaBlancoDoradoNude.id], "nude pedido: solo quien lo lleva");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "blanco y dorado" }).length, 2, "nude no se infiere ni se exige si no se pidió; es un color extra permitido");

// ── 4. Preferencias: temática, colores, tonos, negativas, solo-colores ──────────────────────────────────────────────────
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "romántico" }), [bodaOroRosa.id], "estilo evidenciado en título/temática");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "romántico rosa y dorado" }), [], "oro rosa no satisface dorado literal; rosa suelto tampoco");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "elegante" }), [bodaNegroDorado.id], "elegante literal");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "gótico" }), [], "estilo desconocido sigue sin satisfacerse");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "dinosaurios" }), [dinos.id], "motivo con evidencia");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "dino" }), [dinos.id], "alias léxico existente");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", mensaje: "mi hijo quiere dinosaurios" }), [dinos.id], "motivo nombrado en el último mensaje");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "negro y dorado" }), [cumpleAdulto.id], "colores del cumpleaños; Halloween (negro) fuera por motivo ajeno");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "Halloween" }), [halloween.id], "el motivo nombrado lo admite");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", tematica: "fútbol" }), [futbol.id]);
assert.deepEqual(ids(catalogo, { categoria: "baby shower", tematica: "celeste" }), [], "celeste no se cumple con azul a secas");
const celeste = idea("Semiarco celeste", "Celeste y blanco", ["Baby shower"]);
assert.deepEqual(ids([...catalogo, celeste], { categoria: "baby shower", tematica: "celeste" }), [celeste.id], "el tono literal sí");
assert.deepEqual(ids([...catalogo, celeste], { categoria: "baby shower", tematica: "azul" }), [babyNino.id, celeste.id], "azul admite azul y celeste (su familia)");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "blanco y dorado", mensaje: "sin nude" }), [bodaBlancoDorado.id], "negativa literal excluye");
assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "no quiero negro" }), [bodaBlancoDorado.id, bodaBlancoDoradoNude.id, bodaOroRosa.id], "la negativa no cuenta como petición positiva");
assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "nada de elegante" }), [bodaBlancoDorado.id, bodaBlancoDoradoNude.id, bodaOroRosa.id], "negativa de estilo literal");
assert.deepEqual(ids(catalogo, { categoria: "boda", tematica: "blanco y dorado", mensaje: "solo blanco y dorado" }), [bodaBlancoDorado.id], "solo-colores rechaza colores extra");

// ── 5. Edad ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", edad: 6 }), [cumpleBlancoDorado.id, dinos.id, primerCumple.id], "edad dentro de rango; sin restricción de edad también vale");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", edad: 40 }), [cumpleBlancoDorado.id, cumpleAdulto.id, primerCumple.id]);
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños", edad: 0 }), ids(catalogo, { categoria: "cumpleaños" }), "edad 0 = desconocida, sin filtro");
assert.deepEqual(ids(catalogo, { categoria: "cumpleaños" }), ids(catalogo, { categoria: "cumpleaños", edad: undefined }));

// ── 6. Identidad: se filtra antes de deduplicar y de topar a seis ──────────────────────────────────────────────────────
const muchos = Array.from({ length: 9 }, (_, indice) => idea(`Semiarco boda ${indice}`, "Boda clásica", ["Boda"]));
assert.equal(ids(muchos, { categoria: "boda" }).length, TOPE_RECOMENDACIONES, "tope de seis");
assert.deepEqual(ids(muchos, { categoria: "boda" }), muchos.slice(0, 6).map((item) => item.id), "orden de la fuente");
const gemelo = idea("Arco de entrada blanco y negro", "Elegante blanco y negro", ["Boda"], { id: "deco-real-gemelo-a" });
const gemeloOtro = idea("Arco de entrada en blanco y negro", "Elegante blanco y negro", ["Boda"], { id: "deco-real-gemelo-b" });
const repetido = { ...gemelo };
assert.deepEqual(ids([gemelo, repetido, gemeloOtro], { categoria: "boda" }), ["deco-real-gemelo-a"], "ID repetido y título equivalente salen una vez");
const duplicadosAjenos = Array.from({ length: 8 }, (_, indice) => idea("Arco repetido", "Boda clásica", [indice < 7 ? "Cumpleaños" : "Boda"]));
assert.deepEqual(ids(duplicadosAjenos, { categoria: "boda" }), [duplicadosAjenos[7]!.id], "los de otro evento no consumen el tope ni la deduplicación");
assert.ok(titulos([idea("Cumpleaños especial", "Boda clásica", ["Boda"])], { categoria: "boda" })[0] === "Cumpleaños especial", "el título no se reescribe");

// ── 7. Fuentes sucesivas: altas, cambios y bajas se reflejan sin tocar código ni listas ─────────────────────────────────
const inicial = [idea("Arco jubilación", "Elegante azul", ["Jubilación"])];
const nuevo = idea("Aro de jubilación dorado", "Dorado", ["Jubilación"], { id: "deco-real-nueva-jubilacion" });
assert.equal(recomendarPorCategoria(catalogo, { categoria: "jubilación" }).estado, "categoria_desconocida", "antes de la alta no existe");
assert.deepEqual(ids(inicial, { categoria: "jubilación" }), [inicial[0]!.id], "una etiqueta nueva se descubre sin tabla de alias");
assert.deepEqual(ids([...inicial, nuevo], { categoria: "jubilación" }), [inicial[0]!.id, nuevo.id], "alta");
assert.deepEqual(ids([...inicial, nuevo], { categoria: "jubilación", tematica: "dorado" }), [nuevo.id]);
const modificado = { ...nuevo, eventos: ["Boda"] };
assert.deepEqual(ids([...inicial, modificado], { categoria: "jubilación" }), [inicial[0]!.id], "cambio de evento");
assert.deepEqual(ids([...inicial, modificado], { categoria: "boda" }), [modificado.id], "cambio de evento: aparece en la nueva categoría");
assert.deepEqual(ids([...inicial, { ...nuevo, tematica: "Plateado", titulo: "Aro plateado" }], { categoria: "jubilación", tematica: "dorado" }), [], "cambio de título/temática");
assert.deepEqual(ids(inicial, { categoria: "jubilación" }), [inicial[0]!.id], "baja (oculta como ejemplo): deja de salir");
assert.deepEqual(ids([], { categoria: "jubilación" }), []);
assert.equal(claveDeCategoria("jubilacion", vocabularioDeCategorias([inicial[0]!])), "jubilacion", "la etiqueta nueva es su propia clave");

// ── 8. Preferencias leídas del texto ───────────────────────────────────────────────────────────────────────────────────
assert.deepEqual(preferenciasDeTexto({ tematica: "rosa, lila, celeste y dorado" }), { estilos: [], colores: ["rosado", "lila", "dorado"], tonos: ["celeste"], excluir: [], soloColores: false });
assert.deepEqual(preferenciasDeTexto({ mensaje: "quiero blanco pero sin negro ni rosa" }).excluir, ["negro", "rosa"], "la cláusula negativa se guarda literal, término a término");
assert.deepEqual(preferenciasDeTexto({ mensaje: "quiero blanco pero sin negro ni rosa" }).colores, ["blanco"], "lo negado no es positivo");
assert.equal(preferenciasDeTexto({ mensaje: "solo dorado" }).soloColores, true);
assert.equal(preferenciasDeTexto({ mensaje: "solo quiero ver bodas" }).soloColores, false);
assert.deepEqual(preferenciasDeTexto({ tematica: "Niña romántico", ignorar: [] }).estilos, ["romantico"], "las palabras de género no son estilo");

// ── 9. Biblioteca real: anclajes del SPEC (no son listas de elegibilidad) ──────────────────────────────────────────────
const real = bibliotecaVisible();
const deBoda = ideasEstrictasDeCategoria({ evento: "Boda" }, real).ideas.map((item) => item.id);
assert.ok(deBoda.includes("deco-real-28-aro-blanco-dorado-y-nude"), "AC1: boda sin preferencias incluye el aro de una sola estructura");
assert.deepEqual(deBoda, real.filter((item) => item.eventos.some((evento) => /boda/i.test(evento))).map((item) => item.id), "boda = los registros con evento Boda, en orden");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Navidad" }, real).ideas.map((item) => item.id), ["deco-real-27-aro-navideno-verde-salvia"], "AC2 Navidad");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Bautizo" }, real).ideas.map((item) => item.id), ["deco-real-28-aro-blanco-dorado-y-nude"], "AC2 Bautizo (no comunión)");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Boda", tematica: "blanco y dorado" }, real).ideas.map((item) => item.id), ["deco-real-13-images-28", "deco-real-28-aro-blanco-dorado-y-nude"], "AC3 con la biblioteca real: blanco (título) y dorado (temática) literales; sin negro/dorado ni cumpleaños");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Cumpleaños", tematica: "Spiderman" }, real).ideas, [], "AC4 Spiderman");
assert.equal(ideasEstrictasDeCategoria({ evento: "jubilación" }, real).estado, "categoria_desconocida", "AC4 jubilación");
assert.equal(ideasEstrictasDeCategoria({}, real).estado, "categoria_desconocida", "sin categoría no hay recomendaciones");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Boda" }).ideas.map((item) => item.id), deBoda, "el adaptador usa la biblioteca visible por defecto");

// Género de baby shower: solo dentro de los candidatos del evento.
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "es una niña" }, catalogo).ideas.map((item) => item.id), [babyNina.id]);
assert.equal(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "es una niña" }, catalogo).genero, "nina");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", tematica: "Niño" }, catalogo).ideas.map((item) => item.id), [babyNino.id], "azul sin palabra de género es de niño");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower" }, catalogo).ideas.map((item) => item.id), [babyNina.id, babyNino.id], "sin género no se filtra");
assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Cumpleaños", ultimoUsuario: "es para mi niña" }, catalogo).genero, null, "el género de bebé solo aplica a baby shower");

// El buscador legacy conserva su relleno: no se vuelve la ruta de la categoría activa.
assert.equal(ideasEstrictasDeCategoria({ evento: "jubilación" }, real).ideas.length, 0, "la categoría activa nunca cae al buscador legacy con relleno");


// ── 10. Causas raíz del rechazo previo (afinidad ≠ equivalencia léxica, polaridad, estilos desconocidos, género negado) ──
// Se recolectan todos los fallos para que una sola ejecución muestre cada causa.
const fallos: string[] = [];
function caso(nombre: string, comprobacion: () => void): void {
  try { comprobacion(); } catch (error) { fallos.push(`${nombre}: ${error instanceof Error ? error.message.split("\n")[0] : String(error)}`); }
}

// Causa 1: la afinidad semántica no prueba el estilo ni el motivo. Solo valen las variantes léxicas genuinas.
const eleganteSoloColores = idea("Arco negro y dorado", "Negro y dorado", ["Boda"]);
const eleganteLiteral = idea("Arco clásico", "Elegante blanco", ["Boda"]);
const romanticoSoloOroRosa = idea("Semiarco blanco y oro rosa", "Oro rosa", ["Boda"]);
const romanticoLiteral = idea("Semiarco pastel", "Romántico", ["Boda"]);
const arcoirisIdea = idea("Arco arcoíris", "Arcoíris", ["Cumpleaños"]);
const unicornioIdea = idea("Arco de unicornios", "Unicornio", ["Cumpleaños"]);
const margaritasIdea = idea("Arco de margaritas", "Margaritas", ["Boda"]);
const tulipanesIdea = idea("Arco de tulipanes", "Tulipanes", ["Boda"]);
const estilos = [eleganteSoloColores, eleganteLiteral, romanticoSoloOroRosa, romanticoLiteral, arcoirisIdea, unicornioIdea, margaritasIdea, tulipanesIdea];
caso("elegante no es negro y dorado (temática)", () => assert.deepEqual(ids(estilos, { categoria: "boda", tematica: "elegante" }), [eleganteLiteral.id]));
caso("elegante no es negro y dorado (mensaje)", () => assert.deepEqual(ids(estilos, { categoria: "boda", mensaje: "quiero un estilo elegante" }), [eleganteLiteral.id]));
caso("romántico no es oro rosa", () => assert.deepEqual(ids(estilos, { categoria: "boda", tematica: "romántico" }), [romanticoLiteral.id]));
caso("romántica es variante léxica de romántico", () => assert.deepEqual(ids(estilos, { categoria: "boda", tematica: "romántica" }), [romanticoLiteral.id]));
caso("unicornio no es arcoíris", () => assert.deepEqual(ids(estilos, { categoria: "cumpleaños", tematica: "unicornio" }), [unicornioIdea.id]));
caso("unicornios es variante de unicornio", () => assert.deepEqual(ids(estilos, { categoria: "cumpleaños", mensaje: "quiere unicornios" }), [unicornioIdea.id]));
caso("arcoíris no es unicornio", () => assert.deepEqual(ids(estilos, { categoria: "cumpleaños", tematica: "arcoíris" }), [arcoirisIdea.id]));
caso("arco iris es variante de arcoíris", () => assert.deepEqual(ids(estilos, { categoria: "cumpleaños", tematica: "arco iris" }), [arcoirisIdea.id]));
caso("tulipanes no es margaritas", () => assert.deepEqual(ids(estilos, { categoria: "boda", tematica: "tulipanes" }), [tulipanesIdea.id]));
caso("tulipán es singular de tulipanes", () => assert.deepEqual(ids(estilos, { categoria: "boda", tematica: "tulipán" }), [tulipanesIdea.id]));
caso("dino sigue siendo variante de dinosaurios", () => assert.deepEqual(ids([dinos], { categoria: "cumpleaños", tematica: "dinos" }), [dinos.id]));
caso("sin elegante no excluye lo solo negro y dorado", () => assert.deepEqual(ids(estilos, { categoria: "boda", mensaje: "sin elegante", tematica: "negro y dorado" }), [eleganteSoloColores.id]));

// Causa 2: la polaridad es un dato estructurado por cláusula; los marcadores repetidos y los regresos a positivo se conservan.
const florBoda = idea("Arco de flores", "Flores blancas", ["Boda"]);
const goticoBoda = idea("Arco gótico negro", "Gótico", ["Boda"]);
const polaridad = [bodaBlancoDorado, bodaNegroDorado, florBoda, goticoBoda, bodaBlancoDoradoNude];
caso("sin flores y sin gótico: dos negativas", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "sin flores y sin gótico" }).excluir, ["flores", "gotico"]));
caso("sin flores y sin gótico filtra ambas", () => assert.deepEqual(ids(polaridad, { categoria: "boda", mensaje: "sin flores y sin gótico" }), [bodaBlancoDorado.id, bodaNegroDorado.id, bodaBlancoDoradoNude.id]));
caso("sin negro y con dorado: dorado es positivo", () => {
  const preferencias = preferenciasDeTexto({ mensaje: "sin negro y con dorado" });
  assert.deepEqual(preferencias.excluir, ["negro"]);
  assert.deepEqual(preferencias.colores, ["dorado"]);
});
caso("sin negro y con dorado filtra", () => assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "sin negro y con dorado" }), [bodaBlancoDorado.id, bodaBlancoDoradoNude.id]));
caso("no quiero negro pero sí dorado", () => {
  const preferencias = preferenciasDeTexto({ mensaje: "no quiero negro pero sí dorado" });
  assert.deepEqual(preferencias.excluir, ["negro"]);
  assert.deepEqual(preferencias.colores, ["dorado"]);
  assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "no quiero negro pero sí dorado" }), [bodaBlancoDorado.id, bodaBlancoDoradoNude.id]);
});
caso("sin negro ni rosa", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "sin negro ni rosa" }), { estilos: [], colores: [], tonos: [], excluir: ["negro", "rosa"], soloColores: false }));
caso("negativas repetidas por cláusula", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "no quiero negro, no quiero rosa" }).excluir, ["negro", "rosa"]));
caso("negativa y petición del mismo mensaje", () => {
  const preferencias = preferenciasDeTexto({ mensaje: "no quiero negro y quiero dorado" });
  assert.deepEqual([preferencias.excluir, preferencias.colores], [["negro"], ["dorado"]]);
});
caso("control mixto: blanco y dorado pero sin nude", () => assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "quiero blanco y dorado pero sin nude" }), [bodaBlancoDorado.id]));
caso("control positivo puro no excluye nada", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "con dorado y con blanco" }).excluir, []));

// Causa 3: el estilo o la temática explícitos del cliente se conservan aunque el catálogo no los conozca.
caso("quiero un estilo gótico conservado", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "quiero un estilo gótico" }).estilos, ["gotico"]));
caso("quiero estilo gótico sin evidencia: vacío", () => assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "quiero estilo gótico" }), []));
caso("quiero temática X sin evidencia: vacío", () => assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "quiero temática vintage" }), []));
caso("quiero un estilo gótico con evidencia literal", () => assert.deepEqual(ids(polaridad, { categoria: "boda", mensaje: "quiero un estilo gótico" }), [goticoBoda.id]));
caso("el relleno conversacional no es estilo", () => {
  assert.deepEqual(preferenciasDeTexto({ mensaje: "hola, quiero algo bonito para mi hija" }).estilos, []);
  assert.deepEqual(ids(catalogo, { categoria: "boda", mensaje: "hola, es para mi hija" }), ids(catalogo, { categoria: "boda" }));
});
caso("el estilo termina antes del relleno posterior", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "quiero un estilo gótico para mi hija" }).estilos, ["gotico"]));
caso("estilo negado no es petición", () => assert.deepEqual(preferenciasDeTexto({ mensaje: "no quiero un estilo gótico" }).estilos, []));

// Causa 4: el género del baby shower consume los mismos hechos con polaridad.
const babyDerivadaNina = idea("Guirnalda fucsia", "Fucsia y rosa", ["Baby shower"]);
const babyNeutro = idea("Guirnalda blanca", "Blanco y dorado", ["Baby shower"]);
const bebes = [babyNina, babyDerivadaNina, babyNino, babyNeutro];
caso("no quiero niña no selecciona niña", () => {
  const resultado = ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "no quiero niña" }, bebes);
  assert.equal(resultado.genero, null);
  assert.deepEqual(resultado.ideas.map((item) => item.id), [babyNino.id, babyNeutro.id]);
});
caso("no quiero niña con temática guardada de niña", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", tematica: "Niña", ultimoUsuario: "no quiero niña" }, bebes).ideas.map((item) => item.id), [babyNino.id, babyNeutro.id]));
caso("sin niña y con azul: preferencias independientes", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "sin niña y con azul" }, bebes).ideas.map((item) => item.id), [babyNino.id]));
caso("no quiero niña ni plateado conserva la exclusión léxica", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "no quiero niña ni plateado" }, bebes).ideas.map((item) => item.id), [babyNeutro.id]));
caso("control: niño positivo", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "es un niño" }, bebes).ideas.map((item) => item.id), [babyNino.id]));
caso("control: niña positiva incluye la derivada", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "es una niña" }, bebes).ideas.map((item) => item.id), [babyNina.id, babyDerivadaNina.id]));
caso("control: neutro positivo", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "algo neutro" }, bebes).ideas.map((item) => item.id), [babyNeutro.id]));
caso("no quiero niño deja niña y neutro", () => assert.deepEqual(ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "no quiero niño" }, bebes).ideas.map((item) => item.id), [babyNina.id, babyDerivadaNina.id, babyNeutro.id]));
caso("biblioteca real: no quiero niña no admite diseños de niña", () => {
  const resultado = ideasEstrictasDeCategoria({ evento: "Baby shower", ultimoUsuario: "no quiero niña" }, real);
  assert.equal(resultado.genero, null);
  assert.ok(resultado.ideas.every((item) => generoDeDecoracion(item) !== "nina"), "ninguna idea de género niña");
});

// Helper puro: variantes léxicas y polaridad, sin afinidad semántica.
caso("formas léxicas genuinas", () => {
  for (const forma of ["dinosaurio", "dinosaurios", "dino", "dinos"]) assert.ok(formasLexicasEstrictas("dino").includes(forma), forma);
  assert.ok(formasLexicasEstrictas("romántica").includes("romantico"));
  assert.ok(formasLexicasEstrictas("arco iris").includes("arcoiris"));
});
caso("formas léxicas sin afinidad", () => {
  assert.ok(!formasLexicasEstrictas("elegante").some((forma) => forma.includes("negro") || forma.includes("dorado")));
  assert.ok(!formasLexicasEstrictas("romantico").includes("oro rosa"));
  assert.ok(!formasLexicasEstrictas("unicornio").includes("arcoiris"));
  assert.ok(!formasLexicasEstrictas("tulipanes").includes("margaritas"));
  assert.ok(!formasLexicasEstrictas("nino").includes("nina"), "niño y niña no son variantes");
});
caso("polaridad estructurada", () => {
  assert.deepEqual(analizarPolaridad("sin negro y con dorado"), { positivo: "dorado", negativos: ["negro"] });
  assert.deepEqual(analizarPolaridad("sin flores y sin gótico"), { positivo: "", negativos: ["flores", "gotico"] });
  assert.deepEqual(analizarPolaridad("no quiero negro pero sí dorado"), { positivo: "dorado", negativos: ["negro"] });
  assert.deepEqual(analizarPolaridad("sin negro ni rosa"), { positivo: "", negativos: ["negro", "rosa"] });
  assert.deepEqual(analizarPolaridad(undefined), { positivo: "", negativos: [] });
});

caso("las comas no afirman colores de una enumeración negativa", () => {
  assert.deepEqual(analizarPolaridad("sin negro, rosa ni azul"), { positivo: "", negativos: ["negro", "rosa", "azul"] });
  const soloRosa = idea("Aro rosa", "Rosa", ["Boda"]);
  const soloDorado = idea("Aro dorado", "Dorado", ["Boda"]);
  assert.deepEqual(ids([soloRosa, soloDorado], { categoria: "Boda", mensaje: "sin negro, rosa ni azul" }), [soloDorado.id]);
});
caso("una afirmación explícita termina la enumeración negativa", () => {
  assert.deepEqual(analizarPolaridad("sin negro, con dorado"), { positivo: "dorado", negativos: ["negro"] });
  assert.deepEqual(analizarPolaridad("sin negro. Quiero dorado"), { positivo: "dorado", negativos: ["negro"] });
  assert.deepEqual(analizarPolaridad("sin flores, gótico"), { positivo: "", negativos: ["flores", "gotico"] });
});
caso("las frases léxicas anunciadas son una sola restricción", () => {
  for (const mensaje of ["quiero tema arco iris", "quiero un estilo arco iris", "quiero temática arco iris"]) {
    assert.deepEqual(preferenciasDeTexto({ mensaje }).estilos, ["arco iris"], mensaje);
    assert.deepEqual(ids([arcoirisIdea], { categoria: "Cumpleaños", mensaje }), [arcoirisIdea.id], mensaje);
  }
});
caso("la etiqueta temática no forma parte del término excluido", () => {
  for (const etiqueta of ["tema", "temática", "estilo", "motivo"]) {
    const mensaje = `no quiero ${etiqueta} gótico`;
    assert.deepEqual(preferenciasDeTexto({ mensaje }).excluir, ["gotico"], mensaje);
    assert.deepEqual(ids([goticoBoda, bodaBlancoDorado], { categoria: "Boda", mensaje }), [bodaBlancoDorado.id], mensaje);
  }
});
caso("solo-colores no introduce un estilo literal obligatorio", () => {
  for (const marcador of ["solo", "solamente", "únicamente", "exclusivamente"]) {
    const tematica = `${marcador} blanco y dorado`;
    const preferencias = preferenciasDeTexto({ tematica });
    assert.equal(preferencias.soloColores, true);
    assert.deepEqual(preferencias.estilos, []);
    assert.deepEqual(ids([bodaBlancoDorado, bodaBlancoDoradoNude], { categoria: "Boda", tematica }), [bodaBlancoDorado.id]);
  }
});

assert.deepEqual(fallos, [], `causas raíz sin corregir:\n- ${fallos.join("\n- ")}`);
console.log("test-recomendaciones-categoria: categoría estricta, alias genuinos, preferencias positivas/negativas, sin relleno, fuentes sucesivas.");
