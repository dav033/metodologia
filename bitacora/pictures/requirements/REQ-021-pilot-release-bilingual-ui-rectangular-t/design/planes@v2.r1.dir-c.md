# planes@v2 · r1 · Direction C — «Cartas al pie»

Status: exploration draft (not a contract, not approved). Stance: direct manipulation — same product shell,
in-place editing, progressive disclosure and tactile press/settle feedback on the changed controls.

Files: `planes@v2.r1.dir-c.tsx` (entry) → `planes@v2.r1.dir-c.html` (built offline, 527 KB, 1956 source files);
thumbnails `planes@v2.r1.dir-c.html.candidate-1.html` (chosen) and `.candidate-2.html`; axis evidence
`planes@v2.r1.dir-c.json`.

## Approach — how it changes the existing surface

Base: published `/planes` at commit `0715a331` (`src/app/planes/page.tsx`, `ComparadorPlanes.tsx`,
`comparador-planes.module.css`, `textos-planes.ts`, `src/lib/planes/catalogo.ts`), read with `git show` in
`/home/david/dev/.pictures-wt/login-redirect`, plus the current screenshot `planes.png`.

Kept unchanged: the page masthead (ring-and-dot mark, «Pictures Sempertex», «Idioma» native select ES/EN), the
heading row (H1 «Planes»/«Plans» with the back link at right), the administrator line «Un administrador asigna el
plan.» / «An administrator assigns the plan.», the footer «Pictures · Sempertex», the page width
`min(100% - 48px, 1440px)`, the catalogue data and the chat line using the catalogue description («Chat asistido con
límites.» / «… con límites más altos.»), the Check icon in `acento` for available tools and in `aviso` with the
«aún no disponible» / «not available yet» marker for unavailable ones. The signed-in shell is the 64 px account bar
with the cuentas-admin@v2 menu (chosen dir C), unchanged; the `/login` screen is unchanged apart from being the
place where its existing «Planes» link lives.

Removed (P-211): the «Comparar planes / Seleccionar para comparar» route tabs, the «Ir a un plan» rail, the default
«Plan resaltado» Entusiasta highlight and its accent bar, the pressed/selected state, the selection summary and
«Volver a la comparación completa». `?vista=seleccionar` renders exactly the same page (view «Consulta antigua»).

Changed: the 2×2 divided sheet becomes four **separate peer cards** in catalogue order. Each card: plan name
(18/600), price on its own line (30/600 tabular, «COP / mes» / «USD / month» at 13 px; «Gratis» / «Free» for
Entusiasta), a rule, «Herramientas incluidas», then the full cumulative list, always expanded. Cards keep their
natural height (`align-items:start`), but the identity block has one fixed height so the four prices share one
line; the longer Designer Plus and Master Designer lists simply hang lower. Cards are `article`s with no tabindex,
hover, press, badge or action.

Direct manipulation, honestly scoped: the brief forbids hiding tools and any card action, so the stance is applied
only to controls that already exist. The «Idioma» select **edits the page in place** — names, tool lists, labels
and every price switch without navigation, and the price figures roll (old value up and out, new value up from
below, settling with overshoot) so the COP⇄USD change is visible as a change, never both currencies at once.
Progressive disclosure is used for arrival only (cards land, then their rows), and in the existing account-menu
popup; it is deliberately **not** applied to the tool lists.

## Interaction and motion detail

Grammar shared with the chosen cuentas-admin@v2 dir C: presses compress quickly (90 ms,
`cubic-bezier(.4,0,.7,1)`), arrivals settle with a small overshoot (`cubic-bezier(.34,1.42,.64,1)`, 460 ms
expressive / 300 ms natural / 170 ms subtle).

- Load: cards drop and settle (`translateY(18px) scale(.97)` → rest, opacity from .4 so text stays legible),
  staggered 70 ms in catalogue order; tool rows follow 160 ms later at 35 ms each.
- Language change: the select presses and settles (`scale .92 → 1.04 → 1`); each price rolls on the profile spring
  (old exits in 140 ms); tool lists re-settle in place with no load delay.
- Back link: compresses to `.96` on press; chevron nudges −3 px on hover over an `acento-suave` wash.
- Account menu (unchanged, cuentas-admin@v2): trigger press `.95`, popup springs from the top-right corner;
  «Planes» carries `aria-current="page"` on `/planes`.
- States: skeleton cards (3/3/7/8 rows, gentle opacity breathe) for loading; the error panel settles in.
- Reduced motion / «Quieto» / `?still=1`: no travel, no breathe, prices swap instantly, content complete at once.
  Animations pause in a hidden tab. Verified: 25 running animations after load; mid-swap prices measured at
  `translateY(±16.5px)` with both values present; select `animationName = lang-settle`.

## Why it fits the existing product

It is the same page a current visitor knows — same masthead, title row, administrator line, footer, tokens, Geist
and Check icons — minus the comparison machinery the owner removed. Separate peer cards are the conventional
subscription-card reading P-211 asks for; the motion language is the one the owner already chose for the account
surface, so the plans entry in the menu and the page it opens feel like one product.

## Eight axes

| Axis | Direction C |
|---|---|
| Concept | Direct manipulation limited to existing controls: the Idioma select edits names, tools and COP⇄USD prices in place; cards are articles, never controls. |
| Layout | Published shell minus tabs/rail; four separate peer cards, natural height, one shared price line; 4 columns ≥1100 px, 2×2 at 640–1099 px, 1 column below 640 px. |
| Navigation | None in-page (no tabs, index, anchors, summary). Vertical scroll; back link; Idioma select; unchanged account menu with Planes `aria-current`; sign-in Planes link. |
| Typography | Geist product scale: H1 24/600, name 18/600, price 30/600 tabular (26 on phone) + 13 px unit, 12 px section label, 14 px rows, 12 px unavailable marker. |
| Density | Comfortable: 24 px card padding (20 phone), 16 px gaps (12 phone), 6 px row rhythm, 96 px identity block; lists always fully expanded. |
| Components | Native select, back link, ruled card + Check list, shadcn Skeleton (loading), shadcn Button (retry), cuentas-admin@v2 MenuCuenta, LoginForm Planes link. |
| Colour | globals.css tokens in both themes; `acento` only on available checks and focus; `aviso` on unavailable; `error`/`error-suave` for the error; no tinted or highlighted card. |
| Motion | Tactile press/settle: card drop-and-settle stagger 70 ms, rows 35 ms; select press-settle and price roll on language change; back-link press .96; reduced motion swaps instantly. |

## Chosen thumbnail

Candidate 1 «Cartas al pie» (four peer cards at natural height on one price line) over candidate 2 «Ficha de
planes» (one ruled sheet with four rows, tools in two columns). Candidate 2 echoes the Mi cuenta sheet but reads as
a list, not as the conventional subscription cards P-211 asks for, and its two-column tool grid breaks the
cumulative reading order on narrow widths.

## Mockup controls

«Vista»: Planes · sin sesión (`/planes`) · Planes · con sesión · Consulta antigua (`/planes?vista=seleccionar`) ·
Acceso · enlace a Planes (`/login`) · Menú de cuenta · enlace a Planes. «Estado»: Catálogo · español (COP) ·
Navegador en inglés (USD) · Con sesión · Empleado interno · Cargando · Catálogo no disponible. «Tema» claro/oscuro;
«Movimiento» expresivo/natural/sutil/quieto. ES/EN is also switched in the product (Idioma select or menu pair).
The sign-in Planes link opens the signed-out page; the menu's Planes opens the signed-in page; the signed-out back
link returns to `/login`. A dashed «Ruta …» strip marks the route (mockup chrome). Mock accounts use `@prueba.local`.

## Audit (real results)

- Builder: `built … planes@v2.r1.dir-c.html (527 KB, 1956 source files, offline)`.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- `audit_mockup.py`: 100 renders, 3428 text measurements, 218 focus stops —
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
  (two earlier runs failed on the mockup route strip's alignment on `/login`; fixed).
- Screenshots inspected at 1280/390 (both themes, all views), 768 and 360 (normal/error/loading): no horizontal
  overflow (`scrollWidth` equals viewport at every width), full lists visible, prices on one line at 1280.
- `compare_directions.py dir-a dir-b dir-c` (siblings as found on disk): `RESULT: PASS`, all four evidence groups ok.

## Concerns

- No loading or error boundary exists for `/planes` today (no `loading.tsx`/`error.tsx`; the catalogue is a static
  module validated at import, so an invalid catalogue fails the render). The skeleton and error states are drawn
  for whatever the existing architecture renders and never show partial plans or prices.
- On phones the unchanged `/login` places the theme toggle (absolute top-right) over the header's Idioma select
  when the form is taller than the viewport; the mockup adds top padding to avoid drawing that overlap. Not in
  this subplan's scope.

## Open questions

- Q: What does the back link say and do for a signed-in visitor? Today it is always «Volver al acceso» → `/login`;
  this mockup proposes «Volver» / «Back» returning to the previous page.
- Q: Signed in, should `/planes` keep its own Idioma select when the account menu already carries the ES/EN pair?
  This mockup keeps it (it is the page's existing control).
- Q: Is a dedicated loading/error state wanted for `/planes`, or does it stay a static server render? If wanted,
  is «Reintentar» / «Retry» with the generic request-failed copy acceptable?
- Q: Unavailable tools keep the existing Check icon in `aviso` colour plus the marker; should the icon change so a
  tick does not suggest the tool works today?
