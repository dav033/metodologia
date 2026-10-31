# planes@v2 · r1 · Direction A — Fichas en fila (operational reading)

Status: exploration draft for SP-14. Not a contract, not approved. The owner compares directions; only the chosen one is finalised into `planes@v2.md`.

Files: `planes@v2.r1.dir-a.tsx` (entry) → `planes@v2.r1.dir-a.html` (521 KB, offline build, 2031 source files); thumbnails `planes@v2.r1.dir-a.html.candidate-1.html`, `.candidate-2.html`; axis evidence `planes@v2.r1.dir-a.json`.

## Approach — how this changes the existing surface

Base: published `/planes` at commit `0715a331` (`src/components/planes/ComparadorPlanes.tsx`, `comparador-planes.module.css`, `textos-planes.ts`, `src/lib/planes/catalogo.ts`), read with `git show` in `/home/david/dev/.pictures-wt/login-redirect`, plus owner screenshot `planes.png`.

Kept unchanged: the masthead (ring-and-dot mark, «Pictures Sempertex», «Idioma» native select), the heading row (H1 «Planes» / «Plans», back link «Volver al acceso» / «Back to sign in»), the administrator sentence «Un administrador asigna el plan.», the footer, the 1440px page width, Geist, and every `globals.css` token in both themes. When signed in, the shared 64px account bar and popup are those of the chosen `cuentas-admin@v2` (identity, «Plan» chip, Idioma ES/EN pair, Mi cuenta, Planes with `aria-current="page"`, Cerrar sesión), with the same dismissal behaviour: Escape returns focus to the trigger, an outside pointer closes it, and moving focus out closes it.

Removed (owner P-211): the «Comparar planes» / «Seleccionar para comparar» tabs, the «Ir a un plan» rail, the «Plan resaltado» marker and tint, the selection summary, and «Volver a la comparación completa». `/planes?vista=seleccionar` (view «legado») renders exactly the same page with the H1 «Planes».

Changed: the one 2×2 divided sheet becomes **four peer subscription cards in catalogue order**: Entusiasta, Designer, Designer Plus, Master Designer. Each card is a non-focusable `<article>` with these rows in order:

1. Plan name.
2. Price («Gratis» / «Free», or `20.000` + «COP / mes» in ES and `7` + «USD / month» in EN; the two currencies never appear together).
3. A hairline rule.
4. «Herramientas incluidas» with the list length (3 / 3 / 7 / 8).
5. The full cumulative tool list, with no accordion and no hide control.

The three unbuilt tools use a dashed-circle icon and «aún no disponible» / «not available yet» in `aviso`. Chat lines render the catalogue's `descripcion` exactly as published today («Chat asistido con límites.» / «…con límites más altos.»). Cards use CSS subgrid, so the name, price and list start line up across every row of cards. There is no CTA, badge, current-plan mark or default highlight.

Operational stance: one row at desktop puts all four complete lists and prices in the first 1280×900 viewport (Master Designer ends at y≈780), so the page reads like a dense working table while keeping ordinary card hierarchy. Hierarchy comes from type scale (price 28px, name 16px, rows 14px, labels 12px) and grouping (rule, row hairlines), not from colour.

## Interaction and motion detail

The grammar is precise quick cuts on the product's own `--ease-out` (`cubic-bezier(.23,1,.32,1)`), with no overshoot. All motion uses transform and opacity, and content stays readable during it (opacity never starts below .3).

- **Load:** cards cut up 8px from opacity .6, left to right (220ms, 40ms stagger). Each card's header rule then draws from the left (`scaleX`, 308ms). Tool rows slide 6px with a 16ms stagger.
- **Language change** (masthead Idioma select or the menu's ES/EN pair): only the price figure animates. It cuts vertically, old value up and out (120ms), new value in from below (160ms), staggered 25ms per card left to right, inside a clipped 44px price box. Names and tools swap instantly.
- **Feedback:** the back-link chevron nudges −3px on hover and −5px on press (120ms). Retry and the menu controls compress (90ms). The account popup keeps the cuentas-admin@v2 spring from the trigger's corner.
- **Profiles:** expressive 220/40/16ms, natural 170/28/10ms, subtle 120/14/6ms. «Quieto», `?still=1` and OS reduced motion remove every animation and show the final layout at once. Skeleton pulsing stops under reduced motion. Animations pause while the tab is hidden.

## Views and states in the mockup

Views:

- `planes`: ES, signed out.
- `planes-en`: EN, USD.
- `planes-sesion`: signed in, with the account bar.
- `legado`: `/planes?vista=seleccionar`.
- `acceso`: the unchanged sign-in card with its «Planes» link.

States:

- `listo`.
- `cargando`: four skeleton cards, `aria-busy`, status «Cargando planes…».
- `error`: the «Catálogo no disponible» state with `role=alert`, «No se pudieron cargar los planes», «Vuelve a intentarlo para consultar los planes.» and «Reintentar». This copy is reused from approved planes@v1.

Scene: `menu`, the account popup, which applies only on `planes-sesion`. Theme: Claro / Oscuro.

Flows that work in the mockup: the sign-in link «Planes» leads to the plans page, and «Volver al acceso» leads back to sign-in. Language switching works from the masthead select or the menu pair. The menu opens and closes with click, Escape, an outside pointer or focus leaving it.

## Why it fits the existing product

It is the published page with its comparison layer removed. The masthead, heading row, back link, administrator sentence, tokens, font, check icon, `aviso` marker and 24px card radius all come from the current code and the approved v1 roles. The signed-in menu is copied from the chosen sibling contract. The only new arrangement is the four-up card row, which is what P-211 asks for («tipo las cartas de subscripciones normales»).

## Eight-axis table

| Axis | Direction A |
|---|---|
| Concept | Operational reading: four peer subscription cards with complete lists, all in the first desktop viewport; comparison layer removed. |
| Layout | 4 columns at ≥1100px, 2×2 at 640–1099px, 1 column below 640px; each card spans 5 subgrid rows so headers align across a row. |
| Navigation | No in-page navigation; published masthead and back link; signed-in pages keep the cuentas-admin@v2 account bar and menu (Planes `aria-current`). |
| Typography | Geist: H1 24/600, name 16/600, price 28/650 tabular with 12px currency/month suffix, tools heading 12/550 + count, rows 14/1.45, marker 12px. |
| Density | 20px card padding, 8px rows with hairlines, 16px gaps; 8 tools + 3 markers fit a 900px viewport. |
| Components | `<article>` cards; lucide Check / CircleDashed; shadcn Skeleton, Button (outline Retry), Input (sign-in); custom account trigger/popup from cuentas-admin@v2. |
| Colour | Existing tokens only: superficie/fondo, borde edge, borde-suave rules, acento on checks and focus, aviso on unavailable items, error on the failure heading; no highlighted card. |
| Motion | Quick cuts on `--ease-out`: staggered card cut, rule draw, row slide, per-card vertical price cut on language change; reduced-motion parity. |

## Chosen thumbnail

- **Candidate 1 — chosen: «Fichas en fila».** Four equal cards with subgrid-aligned headers. It is the closest to conventional subscription cards, and it shows every list and price at once.
- **Candidate 2 — not chosen: «Libro de filas».** One wide row per plan, with the tools in two columns. It is denser, but it reads as a ledger or table rather than the cards the owner asked for, and its two-column lists break the cumulative reading order.

## Audit (actual output)

- Build: `built …/planes@v2.r1.dir-a.html (521 KB, 2031 source files, offline)`.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- `audit_mockup.py` first run: `RESULT: FAIL — alignment 1` (the sign-in footer's mock note was right-aligned in the centred column). Fixed by stacking that footer.
- `audit_mockup.py` rerun: `audit: planes@v2.r1.dir-a.html — 80 renders (80 combinations planned), 2396 text measurements, 138 focus stops` / `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Screenshots inspected: 1280 light (signed out), 1280 dark (signed in, menu open), 768 light EN, 390 dark full page, 390 light with the menu, and a mid-swap frame of the price cut. `scrollWidth` equals the viewport at every width; no clipped tool line.
- Not verified: 360px was not screenshotted separately; the layout is fluid below 640px. `compare_directions.py` was not run because it needs the sibling directions.

## Open questions for the owner

- Q: Should the tool count beside «Herramientas incluidas» (3 / 3 / 7 / 8) stay? It is derived from the catalogue, but it could be dropped for a plainer card.
- Q: The published architecture reads a static, import-validated catalogue and has no runtime loading or error boundary on /planes. Should the contract keep v1's loading and «No se pudieron cargar los planes» states, or declare them inapplicable?
- Q: When signed in, the page masthead keeps its «Idioma» select while the account menu also has ES/EN (round 15). Should both remain, or should the masthead select be hidden when signed in?
- Q: The signed-in back link reuses v1's «Volver» / «Back» to return to the previous page. Is that right, or should it be omitted when signed in, leaving browser back and the menu?
- Q: Chat lines show the catalogue's `descripcion` with a trailing period («Chat asistido con límites.»), as published. Keep the period or drop it?
