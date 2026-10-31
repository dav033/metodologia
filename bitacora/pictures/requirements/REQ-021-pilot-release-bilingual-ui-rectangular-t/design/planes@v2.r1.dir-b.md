# planes@v2 · r1 · Direction B — «Estantería» (spatial shelf)

Status: **exploration draft** for SP-14, not a contract and not approved. The owner chooses among directions A/B/C;
only the chosen direction's finalizer writes `planes@v2.md`. `planes@v1` stays immutable history.

Files: `planes@v2.r1.dir-b.tsx` (entry) → `planes@v2.r1.dir-b.html` (self-contained, 524 KB, offline build),
thumbnails `planes@v2.r1.dir-b.html.candidate-1.html` (chosen) and `.candidate-2.html`, axis note `planes@v2.r1.dir-b.json`.

## Approach — how this changes the existing surface

Base: published `/planes` at commit `0715a331` (`ComparadorPlanes.tsx`, `comparador-planes.module.css`,
`textos-planes.ts`, `catalogo.ts`; screenshots `planes.png`, `seleccionar.png`). Kept unchanged: the masthead
(ring-and-dot brand «Pictures Sempertex», «Idioma» select), H1 «Planes»/«Plans», «Volver al acceso»/«Back to sign in»,
the existing factual sentence «Un administrador asigna el plan.», footer «Pictures · Sempertex», and — with a
session — the shared signed-in account bar and popup exactly as composed by the chosen `cuentas-admin@v2`
(identity, Plan chip, Idioma ES/EN pair, Mi cuenta, Planes with `aria-current="page"`, Cerrar sesión).

Removed (owner P-211): «Comparar planes»/«Seleccionar para comparar» tabs, the «Ir a un plan» side index, the
highlighted default plan and «Plan resaltado» marker, `aria-pressed` plan buttons, the selection summary and
«Volver a la comparación completa». `?vista=seleccionar` renders the identical page (H1 stays «Planes»).

Added in their place: **one shelf of four peer subscription cards** in catalogue order. Each card is a semantic
`article` with a header (plan name `h2`, monthly price), «Herramientas incluidas» `h3` and the complete cumulative
`ul` of tools — no button, link, badge, tint, CTA or hide control on any card. Spanish shows «Gratis» and
«20.000 COP / mes»; English «Free» and «7 USD / month»; never both currencies.

The spatial idea: the catalogue is cumulative, so at desktop and tablet every card spans the same 11 subgrid rows
(name, price, tools heading, 8 tool rows). Each tool lands on the same shelf row in every card that includes it
(«Contador de globos» is row 2 everywhere, «Taller 3D» is row 8 only in Master Designer). Growth is read by position,
without any comparison control. Shorter plans keep empty rows below their list so rows stay aligned; on phones the
empty rows disappear and each card flows on its own.

## Interaction and motion detail

Grammar: **spatial glide**, `cubic-bezier(.16,1,.3,1)`, 620ms expressive / 380ms natural / 180ms subtle.

- **Deal on load.** Cards are dealt from behind the first card to their own cell (WAAPI translate from card 1's box,
  slight scale .96→1, 70ms stagger; card 1 on top). It works in every layout: sideways at 4 columns, diagonally at 2×2,
  downward on phones. Cards are opaque and fully legible while travelling.
- **Tools slot in.** Each tool row slides 10px sideways into its shelf row (28ms per row, after its card's delay).
- **Reflow glide.** Crossing a breakpoint (1040px / 600px shelf width), every card glides from its old cell to its new
  one (manual FLIP: boxes recorded just before the column count changes; Motion's layout projection ignores window
  resizes, so it is not used).
- **Currency roll.** Switching ES↔EN (Idioma select, or the ES/EN pair in the account menu) rolls the old price up out
  of its slot and the new one in from below (spring 260/26). Names and tools swap in place.
- **Sticky card heads on phones.** In one column each card's head (name + price) sticks to the top while that card's
  tool list scrolls past. This keeps you oriented without an index. In the mockup the sticky offset is the planning bar
  height; in the product it is 0, because `/planes` has no fixed header.
- Repeated controls stay quick: back-link chevron nudge 180ms, menu trigger press `scale(.95)` 90ms, ES/EN `scale(.92)`.
- Reduced motion, «Quieto» and `?still=1` remove deal, slot-in, glide and roll (final content shown at once);
  hidden tabs pause CSS animation.

## Why it fits the existing product

It is the same `/planes` page with the same shell, tokens and Geist type. Only the plans area is recomposed.
«Cartas de suscripción normales» (P-211) is answered literally: four equal cards in one row is the category's
conventional pattern. Production already shows the whole cumulative list for every plan, and the shelf keeps that
property. It removes the reasons the old sheet needed an index and a highlight, so nothing comparison-like has to be
reintroduced. Colour stays on data: `acento` checks for available tools and `aviso` for «aún no disponible», as in
production.

## Eight axes

| Axis | Direction B |
|---|---|
| Concept | Spatial shelf: four peer cards whose tool rows align across cards because the catalogue is cumulative. Position conveys growth, with no comparison, highlight or selection. |
| Layout | Unchanged shell; shelf of 4 equal columns (shelf ≥1040px, i.e. 1280 desktop), 2×2 (≥600px, 768 tablet), 1 column (360/390). 4/2 columns: each card spans 11 shared subgrid rows; 1 column: natural flow. |
| Navigation | No tabs, index or selection. Phone: sticky card heads (name + price). Existing Volver al acceso, Idioma select, signed-in account menu (Planes `aria-current`). Legacy query renders the same shelf. |
| Typography | Geist only. H1 24/600; plan name 18/600; amount 30/650 tabular (26 phone) + 13px muted unit; tools heading 12/550 muted; tools 14/1.45; unavailable 12px aviso. |
| Density | 16px gutters, 24px card radius, 24/22px insets (20 phone), 6px tool rows; airy cards, compact lists; empty aligned rows at desktop/tablet only. |
| Components | Semantic `article` cards with `header`/`h2`/`h3`/`ul`; lucide `Check`; shadcn/Base UI `Button` (Reintentar) and `Skeleton` (loading); Motion `AnimatePresence` (price roll, account popup); native `select` (Idioma); account bar/menu from `cuentas-admin@v2`. |
| Colour | Exact `globals.css` tokens, both themes: `superficie` cards on `fondo`, `borde` edges, `borde-suave` head rule, `acento` checks/focus/retry, `aviso` unavailable, `error` icon in the error state. No highlighted card. |
| Motion | Spatial glide: deal from the first card's box, sideways tool slot-in, FLIP reflow glide across breakpoints, vertical currency roll on language switch; quick 90–180ms controls; reduced-motion parity. |

## Thumbnails

- **Candidate 1 — «Estantería» (chosen):** four equal cards in one row with aligned tool rows; 2×2 tablet; phone stack
  with sticky heads.
- **Candidate 2 — «Filas apaisadas»:** four full-width horizontal cards (identity left, tools in columns right).
  Rejected: it is close to the v1 plan-sheet the owner asked to replace. It reads less like a conventional
  subscription card, and on phones it collapses into the same stack as any other direction.

## Mockup controls

Vista: Sin sesión · desde Acceso / Con sesión · barra de cuenta / Con sesión · menú abierto / Visitante en inglés (USD)
/ Enlace antiguo ?vista=seleccionar. Estado: Listo / Cargando / Catálogo vacío / Error / Sin conexión (state copy from the
approved `planes@v1` §8; «Reintentar» shows loading, then the complete fixture, never a partial catalogue).
Tema: Claro/Oscuro. Movimiento: Expresivo/Natural/Sutil/Quieto. The footer carries «Mockup · datos simulados · URL …».

Mock data: catalogue fixture mirroring `src/lib/planes/catalogo.ts` (names, COP/USD prices, tools and availability;
chat rows use the catalogue descriptions «Chat asistido con límites.» / «… con límites más altos.», as production
does). The signed-in fixture «Cuenta Designer Plus / designerplus@prueba.local» comes from the chosen `cuentas-admin@v2`
mockup. Its plan is not marked on any card.

## Token mapping (project → kit roles)

`--fondo`→background, `--superficie`→card/popover, `--superficie-2`→muted, `--borde`→border, `--texto`→foreground,
`--texto-suave`→muted-foreground, `--texto-tenue`→input (select edge), `--acento`→primary/ring, `--sobre-acento`→
primary-foreground, `--error`→destructive, `--aviso` (unavailable marker). Light and dark values copied verbatim from
`src/app/globals.css` (`0715a331`). Fonts: Geist / Geist Mono WOFF2 from the t12 `.next/static/media` build, inlined.

## Audit (real results)

- Build: `bitacora.py components mockup build planes@v2.r1.dir-b.tsx --out planes@v2.r1.dir-b.html` → built
  524 KB, 1956 source files, offline.
- `contrast.py`: «contrast: 158 pairs checked in light and dark, all pass».
- `audit_mockup.py`: «audit: planes@v2.r1.dir-b.html — 100 renders (100 combinations planned), 2220 text measurements,
  200 focus stops» — **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**.
- `compare_directions.py dir-a dir-b dir-c --json`: ok true, evidence_ok true. Layout similarity B–A 0.112 and
  B–C 0.077. Motion differs in both pairs. Navigation and density are reported equal for all pairs, because
  P-211 removes all in-page navigation from every direction.
- Own Playwright checks: on load, 4 card deal animations and 21 tool-row animations run. The price roll is
  mid-flight 80ms after ES→EN (translateY ±21px). The reflow glide is mid-flight 100ms after 1280→760 (cards
  translated). The sticky head is pinned at the bar offset (147px) on a 390×560 phone. Screenshots inspected at
  1280 light/dark (menu open), 768 dark (legacy URL), 390 light (EN) and 390 dark (loading), plus the 1280 error
  state.

## Open questions

- Q: Is the aligned-row shelf acceptable when Entusiasta and Designer cards keep empty space below their three tools at desktop/tablet, or should short cards end at their content (rows then no longer align)?
- Q: For a signed-in visitor, should the existing «Volver al acceso» link stay as published (it points to /login), or does flow 2 «returns to the page they came from» require a different back target/label? The mockup keeps production's link.
- Q: With a session, language already lives in the account menu (round 15); should `/planes` keep its own «Idioma» select in the masthead as published? The mockup keeps both, bound to the same language.
- Q: The catalogue is a static, validated module, so loading/empty/error/offline states may never occur on `/planes`. Should the contract keep the `planes@v1` §8 recovery states or declare them inapplicable?
- Q: Unavailable tools keep production's `Check` icon in `aviso` plus «aún no disponible». Is that marker kept, or replaced by a non-check icon?

## Concerns

- None blocking. The sticky-head offset differs between mockup (planning bar) and product (0), as noted above.
  Fallback HTML was not used; the real builder ran. No package was installed or fetched.
