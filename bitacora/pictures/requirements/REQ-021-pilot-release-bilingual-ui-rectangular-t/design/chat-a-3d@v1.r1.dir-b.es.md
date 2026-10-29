# Escena junto al chat — SP-12, direction B

Status: **draft exploration; unapproved**. Candidate for `chat-a-3d@v1`, revision r1. Owner: David. Scope: SP-12 / R13, exactly `chat-a-3d@v1.r1.behavior.md`. This direction does not create or amend the canonical contract, SPEC, PLAN or production code. Owner selection and plan approval remain pending.

## Approach and existing surface

Change the existing normal guided chat at `/asistente`, located in t12 `src/app/asistente/page.tsx` and `src/components/guiado/VistaGuiada.tsx`. Its current decoration ideas live in `CarruselDecoraciones.tsx`, its composer in `Compositor.tsx` and its chrome in `src/components/ui/shell/CabeceraApp.tsx` / `MenuApp.tsx`. The asesor repository's corresponding guided surface and separate `src/components/asesor/ChatView.tsx` were inspected read-only; this design targets `/asistente`, not `/asesor`.

The changed area becomes a conversation column beside one enlarged recommendation and a local preview index. The conversation records the need; the enlarged scene lets the person inspect the same gallery decoration before opening it. This is an arrangement of the existing chat and recommendation cards inside the product, without a new landing page, catalogue browser, inspector for editing, search/filter feature or pricing flow.

Preserve the chosen sibling Pictures/Sempertex ring-and-dot masthead, account disclosure, language control, neutral horizontal route rule, Geist typography, rounded surfaces and pill controls. The local Chat route is the current `/asistente` destination; Taller 3D and Proyectos retain their sibling destinations. Account navigation and other tools are contextual mock controls, with explicit Mockup feedback. The workshop arrival is a bounded context fixture showing Escena nueva / Sin guardar todavía; actual editor and save behavior belong to `proyectos@v1`.

## Thumbnail comparison

The two thumbnail HTMLs were written before the full TSX:

- **Chosen: candidate 1**, `chat-a-3d@v1.r1.dir-b.html.candidate-1.html`: conversation on the left, enlarged scene on the right, compact preview index below it. At 1280px the conversation and first recommendation remain visible together.
- Candidate 2, `chat-a-3d@v1.r1.dir-b.html.candidate-2.html`: enlarged scene beside a vertical preview index, conversation below both. In its rendered 1280px thumbnail, the conversation falls below the first viewport. It is weaker for the short conversational task.

Thumbnails are composition sketches, with repeated illustrative art. The complete direction differentiates the three illustration shapes, uses real installed controls, supports both themes and includes all declared states.

## Why this fits Pictures

The shared header, neutral route navigation and rounded papers match `cuentas-admin@v1`, `planes@v1` and `proyectos@v1`. The latter's scene preview and account-versus-browser vocabulary remain recognizable. Only the recommendation area's hierarchy changes: a larger selected preview and a compact in-page selector instead of an isolated carousel. Names stay readable and wrap; counts stay beside the decoration they describe. The conversation never becomes a form or a multi-step wizard.

## Eight axes

| Axis | Rendered expression |
|---|---|
| Concept | The short conversation and its selected gallery scene remain adjacent on wide screens. |
| Layout | At 1100px+, 280–340px chat column + flexible scene area; enlarged selected card above a three-card preview index. |
| Navigation | Shared route rule; local native preview buttons with `aria-pressed`, current-preview label and focus retained on selection; authorized open actions remain on every card. |
| Typography | Product Geist Sans: 24px H1, 20px selected decoration, 18px panel headings, 14–15px body, 12–13px metadata. Inherited Geist Mono wordmark only; tabular balloon counts. |
| Density | Compact conversation and indexed cards; one enlarged preview. Tablet index changes arrangement to avoid squeezed cards; phone cards have a horizontal preview/text composition. |
| Components | Actual Button/Input/Skeleton/Dialog from the installed kit; native account details and language select; custom semantic preview buttons and labelled illustrative SVGs. |
| Colour | Exact existing project tokens and chosen-sibling semantic role mapping; acento for open action and focus, neutral navigation and drawings, error text plus explicit words for failure. |
| Motion | Opposed docking, a finite card seating cascade and scene transfer; profile-aware timings, no continuous ambient animation, reduced/still parity. |

JSON selector evidence is in `chat-a-3d@v1.r1.dir-b.json`. Each selector matches rendered elements. Motion selectors own actual CSS keyframes; they do not merely point at a static container.

## Interaction and motion detail

The conversation docks from x=-18px while the scene stage docks from x=+26px, using cubic-bezier(.16,1,.3,1). Compact cards seat from y=16px and rotate(.6deg), overshoot to y=-2px, then settle, offset 65ms per card. Selecting a preview retains the invoking button's keyboard focus, updates its pressed/current label and seats the replacement scene from x=24px / scale(.975). The enlarged name/count is announced politely. Selection never changes gallery data or creates a project.

Expressive uses 580ms / 180ms / 65ms entrance, control and stagger timings; natural 360/140/35ms; subtle 180/100/12ms. Existing pill controls retain the sibling's quick press and icon feedback. `useMotionProfile()` supplies the selected profile and reduced flag. OS reduced motion, Quieto and `?still=1` remove all travel/transitions while preserving content/actions; hidden tabs pause CSS animation. Entrances are finite and maintain readable text throughout. The actual installed Animate UI/Base UI dialog supplies focus containment for the existing restart confirmation.

Opening the selected card or any indexed card uses that card's identity and represents `/3d?decoracion=<id>` as a **new unsaved project**. The local fixture displays the encoded route as Mockup evidence and preserves the chosen decoration through the view change. It makes no network request and does not persist a project. People without `decoraciones.explorar` get the identical cards and preview selection with **no open action, disabled replacement, upgrade prompt or plan mention in the recommendation area**. Account-menu Planes remains inherited shell context.

The existing Empezar de nuevo action retains a confirmation dialog, Cancelar and focus return. Sending a blank composer is disabled; the illustrative conversation progresses from occasion to size/colours and then recommendations. Arbitrary text is not interpreted: the interface explicitly marks example replies, and the fixture never calls an assistant/model.

## Fixed design system and actual components

Sources: both repositories' `src/app/globals.css`, font setup in `src/app/layout.tsx`, current shared shell, guided controls, and the three supplied sibling contracts and HTMLs. The full TSX directly carries forward the sibling `proyectos@v1.r12.dir-c.tsx` shared masthead/navigation CSS and its token mapping; its project-list and workshop operations are not imported.

| Project source | Kit responsibility | Light / dark |
|---|---|---|
| fondo | background | #faf9fc / #0b0c10 |
| superficie | card, popover, sidebar | #ffffff / #16181f |
| superficie-suave | selected local surface | #faf8fd / #1c1e26 |
| superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| texto | foregrounds | #1c1425 / #f4f5f7 |
| texto-suave | supporting copy, muted foreground | #6b6178 / #9aa1ad |
| texto-tenue | accessible control boundary | #766c85 / #8a91a0 |
| acento / sobre-acento | primary and primary foreground | #6d3fe0 / #ffffff; dark #9479ff / #120b24 |
| acento-hover | hover | #5530b8 / #a58dff |
| borde / borde-suave | decorative outlines/rules | #e3daef / #efe9f8; dark #383c48 / #2a2d38 |
| error / error-suave | error text/source surface | #b23a45 / #ffeaec; dark #ff979f / #43252a |
| taller-visor / taller-panel | inherited workshop arrival context | #ebe7f1 / #faf9fc; dark #1a1722 / #16131d |

Geist Sans and Geist Mono are embedded from the existing t12 `.next/static/media` WOFF2 assets; no package/asset download. Shared panel/inset/field/pill radii remain 32/24/18/999px. Semantic roles for success, warning, charts and destructive foreground are inherited from the chosen sibling for complete kit contrast validation, without adding visible unrelated data or colours.

| Component, source:id variant state | Real import / role |
|---|---|
| shadcn:button default ready/hover/focus/pressed/disabled/busy | `@/components/ui/button`; authorized enlarged open and send |
| shadcn:button outline ready/hover/focus/pressed/disabled | same; indexed open, recovery, restart and cancellation |
| shadcn:input text empty/filled/focus | `@/components/ui/input`; labelled composer |
| shadcn:skeleton scene loading | `@/components/ui/skeleton`; reserved image/name/count geometry, no fabricated values |
| shadcn:dialog restart open/closed | `@/components/ui/dialog`; installed Animate UI/Base UI enhancement |
| custom:preview-index native unselected/selected/focus | `.card-preview`, full name/count, `aria-pressed`, current-preview label |
| custom:scene-preview SVG illustrative/unavailable | `.scene-art`; no WebGL, generated thumbnail or exact scene-fidelity claim |
| native:details account open/closed | inherited account disclosure, Escape/outside dismissal |
| native:select language es/en | labelled `#language`; fixture-only language expansion, no preference persistence |
| kit:planning-controls view/state/scene/theme/motion | `mountMockup/useMockup` from `@kit/mockup`; native selectors outside the product |

## Data provenance and language

Read-only local evaluation with installed t12 `tsx --conditions=react-server` imported `BIBLIOTECA_FABRICA` and `productosDe`. Each number is `productosDe(item).totalGlobos`, not a handwritten estimate or a count of the decorative SVG circles:

| Actual catalogue identity | Actual source name | Engine total |
|---|---|---|
| escena:arco_organico_columnas_guirnalda | Arco orgánico con dos columnas y guirnalda | 530 |
| escena:pared_fondo_columnas | Pared de globos al fondo y dos columnas | 346 |
| escena:techo_racimos | Techo con tiras y flores colgando | 188 |

The fixture's two customer messages are neutral examples, not a recommender ranking test. All preview images are labelled illustrative mock SVGs; they neither reproduce 530 balloons nor claim to be the actual gallery render. Production must use the gallery's matching preview and the engine's count. Names/counts share a single fixture variable across cards, enlarged preview and workshop context. English translations in this exploration are provisional translations of those actual source labels, pending the gallery localization decision below; implementation must consume localized gallery data rather than ask the chat to invent or translate names.

## Views, flows and states

Native Vista exposes chat with opening permission, chat with recommendations only, and workshop arrival context. Native Estado exposes every state below. Native Diálogo independently reaches restart confirmation. Tema offers light/dark, Movimiento all profiles/Quieto, and product Idioma ES/EN. Workshop is context only: its appearance remains the successful handoff for every Estado selection; chat states do not invent workshop failures.

| State | Presentation and recovery |
|---|---|
| ready | Three existing decoration cards; first scene initially enlarged; selecting another keeps it in place. |
| two-results | Two cards, same hierarchy, no empty third slot or fabricated third match. |
| initial | Existing greeting/occasion prompt, neutral recommendation placeholder, example Cumpleaños reply. Reset disabled because there is no conversation to clear. |
| conversation | First user reply, short size/colour question, composer focused by the supporting reply action; no fabricated recommendation. |
| loading | Reserved scene/name/count skeleton and Buscando decoraciones; composer remains writable, send becomes Detener. |
| empty | No hay coincidencias, no cards; action focuses the composer to refine the need. |
| error | No pudimos cargar las decoraciones, explicit Intentar de nuevo restores the example result. |
| offline | Sin conexión, connection/retry wording; existing example conversation retained, no fresh result claim. |
| preview-error | Selected preview unavailable with retry; actual name/count remain visible. The mock's indexed drawings remain illustrative context. |
| count-error | Conteo no disponible; no substituted zero/estimate; explicit retry. Authorized opening is disabled pending the count, subject to owner question Q1. |
| opening | Abriendo… on the enlarged action and duplicate opening controls disabled. The state is explicitly inspectable; the regular action directly demonstrates successful arrival. |
| unavailable | Decoración no disponible; return to recommendations, no replacement name invented. |
| restart dialog | Se borrará esta conversación, Cancelar and Empezar de nuevo. Cancellation/Escape retain the conversation and return focus; confirmation returns to initial. |

Permission absence is represented by the readonly account view, not an error or upsell. No additional consent, payment, registration, editor operations, prices or plan comparison are introduced. Authentication refusals, quota management, counter/calculator internal states and save conflicts are owned by their existing subplans and are not fabricated here. Empty composer validation is a disabled submit rather than an invented error dialog.

## Responsive and accessibility targets

Supported range 360px upward; rendered checkpoints 390, 768 and 1280px in both themes. At 1100px+ use 40px outer gutters, sticky conversation and three compact cards below the stage. At 840–1099px use 24px gutters, a 280px conversation and vertical recommendation rows beside the stage. At 640–839px use 24px gutters, stacked conversation/stage and three preview-index columns. At 360–639px use 20px gutters, wrapping header/navigation, stacked conversation/stage and single-column compact cards with horizontal image/text. Selected name/count/action stack; all long labels wrap. No horizontal page scrolling. Vertical scrolling keeps the full conversation, alternatives and action reachable.

Target applicable WCAG 2.2 AA, without claiming product certification: semantic headings/articles/nav; native keyboard-operable preview buttons; accessible names that include the decoration; text current-preview status; `aria-pressed` selection; 44px controls; 3px accent focus ring with 4px offset; ≥4.5:1 body text and ≥3:1 meaningful control/focus boundaries. Status updates are polite; actionable failures use alert/retry. Decorative icons are hidden; SVGs have illustrative labels. The dialog traps focus and returns it on close. Reduced/still retains identical information and outcomes without travel. Actual assistant behavior, permissions, screen-reader experience and server guarantees require implementation review.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | All | All | Shared Pictures/Sempertex shell, fonts, tokens and neutral horizontal navigation remain visible. |
| B-AC-02 | 1100px+ | ready | Conversation is left of the enlarged scene, and the three-card preview index is below that scene. |
| B-AC-03 | 840–1099px | ready | Index uses compact horizontal rows; names and opening labels fit within the scene column. |
| B-AC-04 | 640–839px | ready | Conversation sits above the stage; the preview index has three columns. |
| B-AC-05 | 360–639px | ready | Conversation, stage and index stack without horizontal page overflow. |
| B-AC-06 | All | ready/two-results | Each card shows its preview, full source name and matching engine count; two results leave no third placeholder. |
| B-AC-07 | All | readonly | No open action or plan promotion appears in the recommendation area. |
| B-AC-08 | All | selection | Preview selection changes the enlarged scene/name/count and pressed marker, while focus stays on its button. |
| B-AC-09 | All | open | Opening any authorized card carries its identity into an Escena nueva / Sin guardar todavía context. |
| B-AC-10 | All | loading | Image/name/count skeletons and Buscando decoraciones appear without invented names/counts. |
| B-AC-11 | All | empty/error/offline/unavailable | The state includes visible explanation and the documented retry/refinement/recommendation recovery. |
| B-AC-12 | All | count-error | The missing count is labelled unavailable and never replaced with zero; duplicate opening is disabled pending recovery. |
| B-AC-13 | All | preview-error | Name/count remain available beside explicit preview failure and retry. |
| B-AC-14 | All | restart dialog | Cancel/Escape preserves the conversation and returns focus; confirmation clears it. |
| B-AC-15 | All | English | Existing names translated for the fixture and expanded controls wrap within the same hierarchy; counts do not change. |
| B-AC-16 | All | reduced/still | All content and controls remain available with no entrance or continuous motion. |

## Verification

All evidence below applies to the final revision-specific HTML. The real builder was available; no fallback, package installation, network fetch or production mutation was used.

| Check | Actual result |
|---|---|
| Installed library status | `installed=True built=True entries ok=96/96`. |
| Offline build | Exit 0; 631 KB, 2,126 source files, React/real installed controls/local fonts inlined. |
| Token contrast | Exit 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Required rendered audit | Exit 0: **234 renders / 234 planned combinations**, 6,942 text measurements, 584 focus stops, at 1280/390/768px in both themes, including the restart dialog. No sampling. |
| English rendered supplement | 216 base view/state/theme/width combinations; zero contrast, non-text, alignment, padding, overflow or unmeasured findings; no page errors or HTTP(S) requests. This supplement excludes dialog scenes; the required Spanish audit covers the dialog. |
| Focused interactions | Exit 0: `INTERACTIONS: PASS 9 groups; zero page errors and zero external HTTP(S) requests`. Includes result-count selection bounds, keyboard preview/focus, correct selected workshop identity, readonly absence of opening/plan copy, count/preview retry, restart Escape/cancel/focus/confirm, example conversation, loading stop and English counts. |
| Evidence selectors | All layout/navigation/typography/motion selectors in the JSON matched actual rendered elements. |
| Motion | At 120ms, 6 running expressive animations; 0 with OS reduced motion; 0 with `?still=1`. |
| Visual inspection | Both candidate thumbnails inspected at 1280px. Final HTML screenshots inspected at 1280/390px in light/Spanish and dark/English; the phone recommendation cards reflow with full wrapping names and actions. Screenshots stayed in memory; no extra files were written. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Earlier audit passes found centered-column alignment heuristics triggered by shrink-to-content metadata wrappers (35 findings, then 21 in the phone count-failure notice). Making the selected identity and failure text use their available flex space corrected those ambiguous groupings; the final unmodified audit reports zero findings. An initial interaction probe expected 530 after deliberately selecting the 346-balloon decoration; its expectation was corrected, and the final consolidated probe passes. No failing check is represented as a pass.

Reproduction commands:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html --widths 1280,390,768
```

The supplementary English, interaction, selector, motion and screenshot probes ran inline with cached Playwright/Chromium and wrote no additional artifacts. These checks validate this planning artifact only; recommendation accuracy, localized catalogue coverage, actual gallery image fidelity, permission enforcement, server routing and saving remain outside its evidence.

## Questions and assumptions

Q1 — Owner: if the engine count fails for a recommendation, should the card be omitted until it recovers, or remain as “Conteo no disponible” with opening disabled, as this exploration shows? The draft chooses the latter only as an inspectable recovery state; no count is invented.

Q2 — Owner / gallery localization owner: who supplies the gallery's English names, and what should appear when a localized name is missing? The HTML's English names are provisional translations for layout inspection, not confirmed catalogue entries or chat-generated names.

Assumptions carried for comparison: initially enlarge the first returned recommendation; local selection is presentational and changes no ranking; opening creates a new unsaved scene and delegates editor/save behavior to SP-4; retry outcomes and example replies are in-memory fixture transitions. These are reviewable design choices, not evidence of production behavior or owner approval. No preview directory, canonical contract, changelog or plan file is written by this exploration.

Impact: SP-12's future T12.1 contract copy, T12.3 recommendation UI and T12.5 visual review. Composition/interaction choice is undetermined until selection and owner approval. Gallery identity/count/language inputs and permission-map semantics are reused; no sibling contract is changed. Production authentication, recommendation ranking, gallery fidelity, localization fallback, routing and saved-project creation remain unverified here.
