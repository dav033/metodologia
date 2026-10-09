# REQ-002 — Plan (approved direction 2026-10-08: "embeddings for everything, well planned" + many celebration categories)

## 0. Taxonomy (before any index)
Two independent axes, each a closed list with id, Spanish name, English name, synonyms/misspellings and parent group:
- **Celebración / ocasión** (what is celebrated) — ~60 entries, grouped:
  - Vida y familia: cumpleaños (+ 1er cumpleaños, cumpleaños infantil, cumpleaños adulto, 18/30/40/50/60+), baby shower,
    revelación de género, bienvenida bebé / nacimiento, bautizo, primera comunión, confirmación, bar/bat mitzvah,
    quince años (quinceañera), sweet sixteen, graduación (preescolar, colegio, universidad), despedida de soltera,
    despedida de soltero, compromiso / pedida de mano, boda, aniversario (bodas de plata, de oro), jubilación,
    bienvenida / regreso a casa, despedida, recuperación / «ponte bien», fiesta de bebé de 6 meses (half birthday).
  - Fechas del calendario: año nuevo, día de reyes, san valentín / amor y amistad, carnaval, día de la mujer,
    san patricio, pascua, día del niño, día de la madre, día del padre, día del maestro, día de la secretaria,
    independencia / fiestas patrias (generic + per country: 4 de julio, 16 de septiembre, 20 de julio…), halloween,
    día de muertos, acción de gracias, black friday, navidad, hanukkah, diwali, año nuevo chino, ramadán / eid,
    orgullo (pride), oktoberfest.
  - Deporte y eventos: mundial / fútbol, super bowl, olimpiadas, carrera / meta.
  - Empresa y comercio: inauguración / apertura, aniversario de empresa, lanzamiento de producto, evento corporativo,
    feria / stand, vitrina / escaparate, temporada de ventas, conferencia.
  - Comunión religiosa genérica, baby/bridal brunch, noche de chicas, pijamada, fiesta de piscina / verano,
    fiesta de jardín, fiesta temática (any theme), fiesta neón / glow, fiesta de disfraces.
- **Temática / estilo** (how it looks) — ~50: dinosaurios, safari / jungla, tropical / hawaiana (luau), unicornio,
  princesas, superhéroes, sirenas, espacio / astronautas, piratas, granja, bosque encantado, mariposas, flores / jardín,
  arcoíris, boho, minimalista, elegante / lujo, vintage, rústico, neón, glam dorado, náutico, circo / carnaval, frutas
  (cítricos, sandía), dulces / candy, deportes, videojuegos, música / disco, Hollywood / cine, París, México / fiesta
  mexicana, vaquero / western, fantasía / hadas, Frozen-like invierno, estrellas / noche, corazones, pastel / macaron,
  monocromático, bicolor (named pairs), metálico / cromado, transparente / burbujas, orgánico natural (verdes y hojas).
  Licensed characters are NOT categories (no brands); they map to their theme (e.g. snow queen → «invierno»).
Plus facets already structured: tipo de pieza, formatos, partes, colores, productos, medidas, fuente.
Module `taxonomia-celebraciones.ts` (single source; the glossary and the RAG read it). Old ids migrate (fix: the owner
references used `cumpleanos`/`graduacion` vs list `cumpleaños`/`grado`).

## 1. Classification of every item
- Rules first (source titles, Sempertex idea occasions, names) → confident tags.
- Then a reviewed model pass — **Claude Sonnet 5.5 subagents at medium effort, NOT paid API calls** (owner,
  2026-10-08, D-011): batches of fichas + rule tags → celebraciones + temáticas with confidence and a short reason;
  low confidence → «general». Output merged into a versioned JSON in the repo's data path; disagreements with the
  rules listed for review.
- Owner review sheet (artifact) to correct tags in bulk.

## 2. Fichas (the text that is embedded)
TS extractor `scripts/taller/extraer-biblioteca.ts`: builds every item (incl. derived pieces) → JSONL with id, tipo,
nombre, facets (from `inventarioDe` + parts contract), medidas, productos, celebraciones, temáticas, fuente, foto url,
and a Spanish **ficha** (what it is, silhouette, parts → formats/colours/counts, products, measures, occasions, theme).

## 3. Embeddings for everything (Python, batch)
- **Text**: one vector per ficha (gemini-embedding, 768, RETRIEVAL_DOCUMENT); queries with RETRIEVAL_QUERY.
- **Image**: one vector per item image — the source photo (Sempertex/owner/web) AND a standard 3D render of the item
  (captured headless from the workshop viewer, same camera per type) so that photo↔photo and photo↔render both work.
  Multimodal embedding model chosen by a short benchmark (researcher agent) on the 13 owner photos: does each find its
  own reference/template in top-3?
- Incremental by content hash; costs declared and capped per run; all calls via `registrarGemini`/telemetría.

## 4. Database (Neon, new migration)
`taller_items`, `taller_items_partes`, `taller_items_embeddings` (modelo, tipo texto|imagen, vector), `taller_taxonomia`
(celebraciones/temáticas with synonyms), `taller_items_propios` (owner-saved items, moved from localStorage).

## 5. Retrieval (Next, one SQL)
`src/lib/taller/buscar.ts` + `/api/taller/buscar`: FTS (Spanish) + trigram + text vector + (if a photo) image vector,
RRF fusion, hard filters (tipo, celebración, temática, formatos, partes, colores, medidas, fuente, propietario), glossary
+ taxonomy normalisation; optional Python rerank (existing). Flag `TALLER_RAG_ENABLED`, fallback to in-memory search.

## 6. Consumers
Scene AI tools (`buscar_en_biblioteca` → RAG; new filters by celebración/temática/partes), photo→scene (reading facets +
photo vector → closest templates as starting point), Library panel (search + celebration/theme filters), owner's items.

## 7. Evaluation
Gold set: 40 owner-style queries + the 13 photos → expected items; metrics recall@5 / MRR; must beat today's keyword
search before switching the flag on.
