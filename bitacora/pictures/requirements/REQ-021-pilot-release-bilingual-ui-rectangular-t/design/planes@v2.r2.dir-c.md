# planes@v2 · r2 · Direction C — «Cartas al pie»

Status: draft exploration; not approved and not an implementation contract. SP-14, R17–R20. This revision preserves r1's existing product shell and direction, and applies the r2 behavioral delta and the owner's request for an «Escoger» / «Choose» button on each card. The owner must resolve the explicit conflict between that request and the current brief's prohibition of card actions; the button's outcome below is a **prototype proposal**, not an approved product decision.

## Approach and composition

The existing `/planes` masthead, brand, language select, heading, back link, administrator statement and footer remain. The signed-in account bar follows cuentas-admin@v2; the sign-in and account menu retain their existing plans entries. Four peer articles in catalogue order show the complete cumulative catalogue lists, name, monthly price in COP for Spanish or USD for English, and the explicit unavailable marker. The published catalogue wording, including chat punctuation, is retained. Master Designer's Taller 3D covers the editor and decorations explorer. Legacy selection queries show this same page without selection mode or highlighted plan.

Each article adds a full-width, peer-styled «Escoger» / «Choose» button between price and tools. In this mockup activating it displays the existing factual administrator-assignment sentence below that button, announced as a status; no selection, purchase, request or account mutation is simulated. This is only a way to illustrate the requested button while its actual outcome and consistency with the brief remain undecided. It must not be treated as an approved behavior. The back link says «Volver al acceso» / «Back to sign in» and goes to `/login` for both session states, matching the existing host; no history/origin tracking is added. The page language control remains present, as does the signed-in menu language pair.

## Eight axes

| Axis | Direction C |
|---|---|
| Concept | Direct in-place language change; peer informational articles with a provisional per-card choose action requested by the owner. |
| Layout | Published shell without comparison navigation; four natural-height cards, shared price line; four columns ≥1100 px, two at 640–1099 px, one below 640 px. |
| Navigation | Existing back to `/login`, language select, account menu and sign-in plans link; no tabs, index, origin tracking or comparison summary. |
| Typography | Product Geist: 24 px heading, 18 px names, 30 px tabular prices (26 px phone), 13 px units, 14 px tools, 12 px section label and unavailable marker. |
| Density | 24 px card padding (20 px phone), 16 px gaps (12 px phone), 6 px row rhythm, expanded lists and natural card heights. |
| Components | Existing masthead, native language select, back link, cards and Check list; shadcn Button (`@/components/ui/button`) per card; cuentas-admin@v2 account menu and login link. |
| Colour | Existing globals.css tokens: `--fondo`, `--superficie`, `--borde-suave`, `--texto`, `--texto-suave`, `--acento`, `--acento-suave`, `--sobre-acento`, `--aviso`; semantic kit roles map to these in both themes. |
| Motion | r1 press/settle grammar: staggered card and row arrival, language-select settle and price roll, back-link and button press. Reduced motion and Quieto remove travel; content remains available. |

## States and verification targets

Mockup switches cover public plans, signed-in plans, legacy query, login entry and account-menu entry; state choices cover Spanish, English and internal employee. Theme and motion controls remain available. Static `PLANES` is validated at module load; no catalogue-specific loading, empty success, runtime error or retry state is invented. Existing host error handling remains outside this proposal. Invalid catalogue data must not produce partial successful plans. Responsive targets are 360, 390, 768 and 1280 px without horizontal page scrolling or clipped lists. Focus must remain visible; controls need keyboard activation and explicit accessible names. Light/dark and reduced-motion parity are required. These are design targets, not a claim of WCAG conformance.

| ID | Width | State | Observable criterion |
|---|---|---|---|
| C-01 | 360–1280 px | public ES/EN | Four peer cards appear in catalogue order with all catalogue tools and explicit unavailable markers. |
| C-02 | 360–1280 px | ES / EN | Only COP / mes or USD / month, respectively, appears; free plan reads Gratis / Free. |
| C-03 | 360–1280 px | public or signed in | Each card has a keyboard-focusable Escoger / Choose button with its plan in its accessible name. |
| C-04 | 360–1280 px | button activated in mockup | Existing administrator-assignment text appears in a status; account access is unchanged. This behavior remains provisional. |
| C-05 | 360–1280 px | legacy query | The same cards appear without comparison or selected-plan state. |
| C-06 | 360–1280 px | signed in or out | Back link identifies and returns to sign-in; page language control remains accessible. |
| C-07 | 360–1280 px | both themes / reduced motion | No page horizontal overflow or clipped tools; focus is visible and reduced motion removes travel. |

## Impact and concerns

SP-14 `planes@v2` is a breaking presentation/interaction revision from v1, affecting `/planes`, the plans link compositions and tasks T14.2, T14.3 and T14.5; T14.11 remains gated on independent owner approval. It does not alter shared account behavior. The new button conflicts with the current brief and SPEC acceptance prohibiting card actions; the change is not ready for implementation until resolved. Existing screenshots and product source establish the shell and token system; the visual outcome still needs owner review.

## Open question for the owner

- Q: What should «Escoger» / «Choose» do for each plan, and should the current no-card-action criterion be changed? The shown administrator statement is only provisional and does not select or request a plan.

## Audit

- Offline builder: 527 KB, 1955 source files.
- Contrast: 158 pairs checked in light and dark, all pass.
- 60 renders, 3036 text measurements, 150 focus stops.
- RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
