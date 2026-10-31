# planes@v2 · r3 · Direction C — «Cartas al pie»

Status: draft exploration; not approved and not an implementation contract. SP-14, R17–R20. This revision keeps r2's existing product shell, composition, navigation and motion and applies the owner's decision of 2026-10-31 (direction C): the «Escoger» / «Choose» button on each card does absolutely nothing when pressed. The r3 UI brief is identical to r2's; no other behavioural delta applies.

## What changed from r2

- The per-card «Escoger» / «Choose» button is purely visual. Pressing it (pointer, Enter or Space) shows only the press motion: no status message, no administrator sentence, no navigation, no request, no selection/pressed state and no account change. It stays a focusable `button` whose accessible name carries the plan («Escoger: Designer Plus» / «Choose: Designer Plus»).
- The r2 provisional feedback (administrator sentence in a `role="status"` under the button) and its open question are removed; the brief/SPEC conflict is resolved because the cards still have no functional action.
- Dead catalogue loading/error/retry copy and styles left over from r1 were removed from the source; no such state is shown (unchanged from r2).

## Approach and composition

The existing `/planes` masthead (ring-and-dot mark, «Idioma» select), heading row with back link, administrator statement and footer remain. The signed-in account bar follows cuentas-admin@v2; the sign-in screen and the account menu keep their single existing plans entry. Four peer articles in catalogue order show name, monthly price (COP / mes in Spanish, USD / month in English; Entusiasta «Gratis» / «Free»), the inert «Escoger» / «Choose» button, and the complete cumulative catalogue tool list with the explicit «aún no disponible» / «not available yet» marker. Catalogue wording, including chat punctuation and limits without numbers, is kept. Master Designer's «Taller 3D» covers the editor and the decorations explorer. Legacy `?vista=seleccionar` queries show this same page with no selection mode, pressed plan or highlighted card. The back link «Volver al acceso» / «Back to sign in» goes to `/login` for both session states, as in the host; no origin tracking.

## Eight axes

| Axis | Direction C |
|---|---|
| Concept | Direct in-place language change over four peer informational articles; each carries an owner-requested «Escoger» / «Choose» button that is purely visual and does nothing. |
| Layout | Published shell without comparison navigation; four natural-height cards, shared price line; four columns ≥1100 px, two at 640–1099 px, one below 640 px. |
| Navigation | Existing back to `/login`, language select, account menu and sign-in plans link; the card button navigates nowhere; no tabs, index, origin tracking or comparison summary. |
| Typography | Product Geist: 24 px heading, 18 px names, 30 px tabular prices (26 px phone), 13 px units, 14 px tools, 12 px section label and unavailable marker. |
| Density | 24 px card padding (20 px phone), 16 px gaps (12 px phone), 6 px row rhythm, expanded lists and natural card heights. |
| Components | Existing masthead, native language select, back link, cards and Check list; shadcn Button (`@/components/ui/button`, outline restyled to product tokens, no handler) per card; cuentas-admin@v2 account menu and login link. |
| Colour | Existing globals.css tokens: `--fondo`, `--superficie`, `--borde-suave`, `--texto`, `--texto-suave`, `--acento`, `--acento-suave`, `--sobre-acento`, `--aviso`; all four cards and buttons use identical peer styling in both themes; no highlighted card. |
| Motion | r1/r2 press/settle grammar: staggered card and row arrival, language-select settle and price roll, back-link and card-button press (scale .97, 90 ms). Reduced motion and Quieto remove travel; content remains available. |

## States and verification targets

Mockup switches cover public plans, signed-in plans, legacy query, login entry and account-menu entry; states cover Spanish, English and internal employee; theme and motion controls remain. The static `PLANES` catalogue is validated at module load; no catalogue-specific loading, empty success, runtime error or retry state is invented, and existing host error handling stays outside this design. Responsive targets: 360, 390, 768 and 1280 px without horizontal page scrolling or clipped lists; visible focus; light/dark and reduced-motion parity. These are design targets, not a claim of WCAG conformance.

| ID | Width | State | Observable criterion |
|---|---|---|---|
| C-01 | 360–1280 px | public ES/EN | Four peer cards in catalogue order with all catalogue tools and explicit unavailable markers. |
| C-02 | 360–1280 px | ES / EN | Only COP / mes or USD / month appears; the free plan reads Gratis / Free. |
| C-03 | 360–1280 px | public or signed in | Each card has a keyboard-focusable «Escoger» / «Choose» button whose accessible name includes its plan. |
| C-04 | 360–1280 px | button pressed (pointer, Enter, Space) | Only the press motion plays; the DOM, URL and focus target do not change; no status, message, navigation, request, pressed/selected state or account change. |
| C-05 | 360–1280 px | legacy query | The same cards appear without comparison, selected or highlighted plan. |
| C-06 | 360–1280 px | signed in or out | Back link identifies and returns to sign-in; page language control remains accessible. |
| C-07 | 360–1280 px | both themes / reduced motion | No page horizontal overflow or clipped tools; focus visible; reduced motion removes travel. |

## Impact and concerns

SP-14 `planes@v2` remains a breaking presentation/interaction revision from v1, affecting `/planes`, the plans link compositions and tasks T14.2, T14.3 and T14.5; T14.11 stays gated on independent owner approval. Shared account behaviour is unchanged. An inert, focusable button is announced to assistive technology as an actionable control that does nothing; this is the owner's explicit decision and is recorded here, not overridden. The brief's «no card action / no decorative purchase CTA» wording should be aligned with that decision in the plan so the visual reviewer (T14.5) does not flag the button.

## Open question for the owner

- Q: Should the SPEC/brief text («no card action is rendered», «do not add disabled or decorative purchase CTA») be amended to allow the inert «Escoger» / «Choose» button explicitly, so T14.2 and the T14.5 visual review accept it?

## Audit

- Offline builder: 525 KB, 1955 source files, offline.
- Contrast: 158 pairs checked in light and dark, all pass.
- 60 renders, 3036 text measurements, 150 focus stops.
- RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
- Extra check (Playwright, 1280 px): 4 buttons named «Escoger: Entusiasta … Master Designer»; after Enter on one and click on another, `.app` DOM and URL unchanged, 0 `role=status` nodes.
