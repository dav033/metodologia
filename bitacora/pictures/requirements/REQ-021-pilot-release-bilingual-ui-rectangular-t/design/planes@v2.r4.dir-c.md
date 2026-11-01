# planes@v2 · r4 · Direction C — «Cartas al pie»

Status: draft exploration; not approved and not an implementation contract. SP-14, R17–R20. This revision keeps r3's existing product shell, composition, navigation, motion and the inert «Escoger» / «Choose» button, and applies the owner's comment of 2026-10-31T19:13 (direction C): «el botón tiene que estar abajo del todo». The r4 UI brief is identical to r3's; no other behavioural delta applies.

## What changed from r3

- The «Escoger» / «Choose» button moved from under the price to the very bottom of each card, after the complete tool list, in a card foot (`.card-foot`, 20 px above, pushed down with `margin-top:auto`).
- Cards in the same grid row now stretch to the row height (`align-items:stretch`, flex column) so every button lands on one shared bottom line: one line for all four at ≥1100 px, one line per row in the 2×2 layout; in one column each button is the card's last element. Prices still share one line through the equal-height identity block.
- The button stays purely visual (r3): focusable, plan in its accessible name, press motion only; no status, navigation, request, pressed state or account change.

## Approach and composition

The existing `/planes` masthead (ring-and-dot mark, «Idioma» select), heading row with back link, administrator statement and footer remain. The signed-in account bar follows cuentas-admin@v2; the sign-in screen and the account menu keep their single existing plans entry. Four peer articles in catalogue order show name, monthly price (COP / mes in Spanish, USD / month in English; Entusiasta «Gratis» / «Free»), the complete cumulative catalogue tool list with the explicit «aún no disponible» / «not available yet» marker, and, at the very bottom, the inert «Escoger» / «Choose» button. Catalogue wording, including chat punctuation and limits without numbers, is kept. Master Designer's «Taller 3D» covers the editor and the decorations explorer. Legacy `?vista=seleccionar` queries show this same page with no selection mode, pressed plan or highlighted card. The back link «Volver al acceso» / «Back to sign in» goes to `/login` for both session states, as in the host; no origin tracking.

## Eight axes

| Axis | Direction C |
|---|---|
| Concept | Direct in-place language change over four peer informational articles; each carries an owner-requested «Escoger» / «Choose» button that is purely visual and does nothing. |
| Layout | Published shell without comparison navigation; four cards stretched to their row, shared price line and shared button line at the card bottom; four columns ≥1100 px, two at 640–1099 px, one below 640 px. |
| Navigation | Existing back to `/login`, language select, account menu and sign-in plans link; the card button navigates nowhere; no tabs, index, origin tracking or comparison summary. |
| Typography | Product Geist: 24 px heading, 18 px names, 30 px tabular prices (26 px phone), 13 px units, 14 px tools, 12 px section label and unavailable marker. |
| Density | 24 px card padding (20 px phone), 16 px gaps (12 px phone), 6 px row rhythm, expanded lists, row-equal card heights and a 20 px minimum gap above the bottom button. |
| Components | Existing masthead, native language select, back link, cards and Check list; shadcn Button (`@/components/ui/button`, outline restyled to product tokens, no handler) in each card foot; cuentas-admin@v2 account menu and login link. |
| Colour | Existing globals.css tokens: `--fondo`, `--superficie`, `--borde-suave`, `--texto`, `--texto-suave`, `--acento`, `--acento-suave`, `--sobre-acento`, `--aviso`; all four cards and buttons use identical peer styling in both themes; no highlighted card. |
| Motion | r1/r2 press/settle grammar: staggered card and row arrival, language-select settle and price roll, back-link and card-button press (scale .97, 90 ms). Reduced motion and Quieto remove travel; content remains available. |

## States and verification targets

Mockup switches cover public plans, signed-in plans, legacy query, login entry and account-menu entry; states cover Spanish, English and internal employee; theme and motion controls remain. The static `PLANES` catalogue is validated at module load; no catalogue-specific loading, empty success, runtime error or retry state is invented, and existing host error handling stays outside this design. Responsive targets: 360, 390, 768 and 1280 px without horizontal page scrolling or clipped lists; visible focus; light/dark and reduced-motion parity. These are design targets, not a claim of WCAG conformance.

| ID | Width | State | Observable criterion |
|---|---|---|---|
| C-01 | 360–1280 px | public ES/EN | Four peer cards in catalogue order with all catalogue tools and explicit unavailable markers. |
| C-02 | 360–1280 px | ES / EN | Only COP / mes or USD / month appears; the free plan reads Gratis / Free. |
| C-03 | 360–1280 px | public or signed in | Each card has a keyboard-focusable «Escoger» / «Choose» button whose accessible name includes its plan; it is the card's last element, below the full tool list. |
| C-03b | ≥640 px | public or signed in | Buttons of cards in the same row share one bottom edge (within 1 px) and sit at the same distance from the card bottom. |
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
- Extra check (Playwright, reduced motion): at 1280 px all four button bottoms at y=858, 25 px above each card bottom; at 800 px row 1 at 624 and row 2 at 1203; at 390 px each button is 21 px from its card bottom; in every case the card's last child is `.card-foot` and the button lies below the tool list; no horizontal overflow. After a click and Enter at 1280 px, `.app` markup and URL unchanged and 0 `role=status` nodes.
