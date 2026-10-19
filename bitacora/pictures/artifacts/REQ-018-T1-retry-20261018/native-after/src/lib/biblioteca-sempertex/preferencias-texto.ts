import { ALIAS_COLORES_V2, TONOS_V2 } from "@/lib/rag/taxonomy/v2";
import { normalizarBusqueda } from "./biblioteca";

/**
 * Dueño único de dos reglas de la recomendación ESTRICTA (REQ-018, SPEC «Matching and decision contract» 3): la polaridad
 * de lo que el cliente escribe («sin negro y con dorado») y las formas léxicas de un término de estilo. Funciones puras,
 * sin dependencia de la búsqueda legacy ni de sus grupos de afinidad. Consumidores: `recomendaciones-categoria.ts` y la
 * interpretación del género de baby shower en `ia/guiado/ideas-guiadas.ts`.
 */

export const PALABRAS_GENERO = new Set(["nino", "ninos", "nina", "ninas", "boy", "girl", "varon", "varoncito", "nena", "neutro", "neutra", "neutros", "neutral", "unisex"]);
export const PALABRAS_RELLENO = new Set([
  "y", "e", "o", "u", "de", "del", "la", "las", "el", "los", "en", "con", "para", "por", "un", "una", "unos", "unas", "mi", "mis", "su", "tu",
  "que", "a", "al", "se", "lo", "me", "es", "quiero", "quisiera", "gustaria", "algo", "tipo", "estilo", "tono", "tonos", "color", "colores",
  "fiesta", "decoracion", "decoraciones", "globos", "idea", "ideas", "ano", "anos", "lleve", "lleven", "usar", "uses", "tenga", "tengan",
]);

const normalizados = (formas: Iterable<string>): string[] => [...new Set([...formas].map(normalizarBusqueda).filter(Boolean))].sort((a, b) => b.length - a.length);
export const ALIAS_TONOS = normalizados(Object.values(TONOS_V2).flatMap((tono) => tono.aliases));
export const ALIAS_COLORES = normalizados(ALIAS_COLORES_V2.flatMap((color) => color.aliases));

const PALABRAS_DE_CORTE = /[.;,!?¿¡\n]/;
const MARCADORES_NEGATIVOS = [["sin"], ["nada", "de"], ["evita"], ["evitar"], ["excepto"], ["menos"], ["ni"], ["no", "quiero"], ["no", "quieres"], ["no", "me", "gusta"], ["no", "me", "gustan"], ["no", "lleve"], ["no", "uses"], ["no", "usar"], ["no", "con"]];
const MARCADORES_POSITIVOS = [["con"], ["pero"], ["aunque"], ["si"], ["quiero"], ["quisiera"], ["me", "gusta"], ["me", "gustan"], ["me", "gustaria"], ["gustaria"]];
/** «no» solo niega lo que le sigue si lo que le sigue es un color, un tono o un género («no negro», «no niña»). */
const NEGABLES = [...ALIAS_TONOS, ...ALIAS_COLORES, ...PALABRAS_GENERO].map((forma) => forma.split(" "));
const MARCADORES = [
  ...MARCADORES_NEGATIVOS.map((palabras) => ({ palabras, negativo: true })),
  ...MARCADORES_POSITIVOS.map((palabras) => ({ palabras, negativo: false })),
].sort((a, b) => b.palabras.length - a.palabras.length);

function empiezaCon(palabras: readonly string[], posicion: number, forma: readonly string[]): boolean {
  return forma.every((palabra, desplazamiento) => palabras[posicion + desplazamiento] === palabra);
}

function marcadorEn(palabras: readonly string[], posicion: number): { largo: number; negativo: boolean } | null {
  const marcador = MARCADORES.find((candidato) => empiezaCon(palabras, posicion, candidato.palabras));
  if (marcador) return { largo: marcador.palabras.length, negativo: marcador.negativo };
  if (palabras[posicion] === "no" && NEGABLES.some((forma) => empiezaCon(palabras, posicion + 1, forma))) return { largo: 1, negativo: true };
  return null;
}

export type TextoConPolaridad = {
  /** Lo que el cliente pide: el texto sin las cláusulas negadas ni los marcadores de polaridad. */
  positivo: string;
  /** Términos que el cliente descarta, uno por elemento, sin relleno («sin negro ni rosa» → negro, rosa). */
  negativos: string[];
};

/**
 * Separa lo pedido de lo descartado, cláusula a cláusula. Cada marcador fija la polaridad de lo que le sigue hasta el
 * siguiente marcador o signo de puntuación: «sin negro y con dorado» descarta negro y pide dorado; «no quiero negro
 * pero sí dorado» igual; «sin flores y sin gótico» descarta ambos. Los marcadores nunca quedan como términos literales.
 */
export function analizarPolaridad(texto: string | undefined): TextoConPolaridad {
  const positivos: string[] = [];
  const negativos: string[] = [];
  for (const clausula of (texto ?? "").split(PALABRAS_DE_CORTE)) {
    const palabras = normalizarBusqueda(clausula).split(" ").filter(Boolean);
    let negativo = false;
    let termino: string[] = [];
    const cerrar = (): void => { if (termino.length) negativos.push(termino.join(" ")); termino = []; };
    for (let posicion = 0; posicion < palabras.length;) {
      const marcador = marcadorEn(palabras, posicion);
      if (marcador) { cerrar(); negativo = marcador.negativo; posicion += marcador.largo; continue; }
      const palabra = palabras[posicion]!;
      posicion += 1;
      if (!negativo) { positivos.push(palabra); continue; }
      if (["y", "e", "o", "u"].includes(palabra)) cerrar();
      else if (!PALABRAS_RELLENO.has(palabra)) termino.push(palabra);
    }
    cerrar();
  }
  return { positivo: positivos.join(" "), negativos };
}

/** Grupos de formas de UNA misma palabra o expresión (variantes de escritura y de número), nunca de afinidad semántica. */
const VARIANTES_LEXICAS: ReadonlyArray<readonly string[]> = [
  ["dinosaurio", "dinosaurios", "dino", "dinos"],
  ["unicornio", "unicornios"],
  ["arcoiris", "arco iris"],
  ["princesa", "princesas"],
  ["superheroe", "superheroes", "super heroe", "super heroes"],
  ["flor", "flores", "floral", "florales"],
  ["navidad", "navideno", "navidena", "navidenos", "navidenas"],
  ["hawaiano", "hawaiana", "hawaianos", "hawaianas", "hawai"],
];

const LARGO_MINIMO = 3;

function conNumeroYGenero(forma: string): string[] {
  const formas = [forma, `${forma}s`, `${forma}es`];
  if (forma.endsWith("es") && forma.length - 2 >= LARGO_MINIMO) formas.push(forma.slice(0, -2));
  if (forma.endsWith("s") && forma.length - 1 >= LARGO_MINIMO) formas.push(forma.slice(0, -1));
  // El cambio -o/-a es género gramatical («romántico»/«romántica»), pero «niño» y «niña» son géneros distintos, no variantes.
  if (!PALABRAS_GENERO.has(forma) && forma.length > LARGO_MINIMO) {
    if (forma.endsWith("o")) formas.push(`${forma.slice(0, -1)}a`, `${forma.slice(0, -1)}as`);
    if (forma.endsWith("a")) formas.push(`${forma.slice(0, -1)}o`, `${forma.slice(0, -1)}os`);
  }
  return formas;
}

/**
 * Formas léxicas de un término de estilo, motivo o exclusión: él mismo, su número y género gramatical, y las variantes
 * de escritura conocidas («dino» → dinosaurio, dinos…). «elegante» no es «negro y dorado», «unicornio» no es «arcoíris»
 * y «tulipanes» no es «margaritas»: eso es afinidad, no equivalencia. Vacío si el término no tiene palabras.
 */
export function formasLexicasEstrictas(termino: string): string[] {
  const consulta = normalizarBusqueda(termino);
  if (!consulta) return [];
  const base = new Set(conNumeroYGenero(consulta));
  for (const grupo of VARIANTES_LEXICAS) if (grupo.some((forma) => base.has(forma))) grupo.forEach((forma) => base.add(forma));
  return [...base];
}

const FRASES_LEXICAS = [...new Set(VARIANTES_LEXICAS.flat().filter((forma) => forma.includes(" ")))].sort((a, b) => b.length - a.length);

/** Saca de un texto normalizado las expresiones léxicas de varias palabras («arco iris») para no partirlas en estilos sueltos. */
export function separarFrasesLexicas(texto: string): { frases: string[]; resto: string } {
  const frases: string[] = [];
  let resto = ` ${texto} `;
  for (const frase of FRASES_LEXICAS) {
    if (!resto.includes(` ${frase} `)) continue;
    frases.push(frase);
    resto = resto.replace(` ${frase} `, "  ");
  }
  return { frases, resto: resto.replace(/\s+/g, " ").trim() };
}
