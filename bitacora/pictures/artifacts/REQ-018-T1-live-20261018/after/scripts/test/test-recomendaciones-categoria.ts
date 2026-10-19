import { strict as assert } from "node:assert";
import { bibliotecaVisible } from "@/lib/biblioteca-sempertex/biblioteca";
import { claveDeCategoria, vocabularioDeCategorias } from "@/lib/biblioteca-sempertex/categorias";
import type { DecoracionSempertex } from "@/lib/biblioteca-sempertex/esquemas";
import { preferenciasDeTexto, recomendarPorCategoria, TOPE_RECOMENDACIONES, type ConsultaCategoria } from "@/lib/biblioteca-sempertex/recomendaciones-categoria";
import { ideasEstrictasDeCategoria } from "@/lib/ia/guiado/ideas-guiadas";

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

console.log("test-recomendaciones-categoria: categoría estricta, alias genuinos, preferencias positivas/negativas, sin relleno, fuentes sucesivas.");
