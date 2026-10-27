# Distinct directions, one existing product

The SPEC, the owner and the existing product define the identity; directions never redefine it. Every direction
is a CHANGE to the existing product surface named in the UI brief, never a new page, landing or poster: reproduce
the existing shell, navigation and header and change only what the requirements demand. The repo's tokens, font
families and components are fixed (read its globals.css, token files, theme and components). Directions differ in
layout/composition, hierarchy, density, component arrangement, in-page navigation and motion within that system.
No new palette, font family or brand; with no token source in the repo, say so in CONCERNS and use the kit defaults.
A palette/font swap on one skeleton fails, and so does a palette/font change on a new skeleton.

## Explore → compare → choose → finalise

1. Read the UI brief (`behavior.md`) and the chosen/finalised contracts of sibling subplans (the brief lists
   them). Reuse their app shell, navigation structure, tokens and component vocabulary, or the existing product's
   when none exist; differ only in what is specific to this subplan. The three directions of one subplan still
   differ among themselves. Name the product's trade in concrete things and verbs for labels and mock data.
2. Each of the three independent Designers receives a stance (a layout/interaction approach). Sketch two HTML
   thumbnail compositions FIRST (six candidates total), then build the stronger one at full fidelity. Keep both
   thumbnails as evidence. The stance is a starting hypothesis, never an order to copy a template or brand.
3. Name the direction, its approach to the changed area and why it fits the existing product. A memorable move is
   allowed only as an interaction/motion detail inside the existing surface. Write the eight-axis table: concept
   (the approach), layout/composition, navigation, typography (hierarchy with the existing fonts and scale),
   density/shape, components (arrangement of the existing ones), colour (use of the existing tokens on data and the
   primary action, no new values), motion (easing, durations, choreography, triggers). Every claim must describe
   something present in the mockup.
4. JSON note: `name`, `axes` (eight nonempty strings), `evidence` (selector arrays for layout, navigation,
   typography, motion). Selectors identify rendered evidence; motion selectors must animate or transition.
   Do not point all four axes at `body`. Build and audit both themes at 1280/390; write actual results.
5. The system runs `kit/compare_directions.py A.html B.html C.html --json` offline. It checks the DOM geometry,
   navigation, density, actual keyframes/easing and selector evidence; fonts/scale are reported but do not count,
   since directions share the product's typography. Same geometry fails even if colours differ. Three colliding
   axes among layout, navigation, density and motion fail. Missing measurements fail closed. Inspect screenshots too:
   a numeric pass alone does not prove taste. The chooser displays pair metrics and axis tables.
6. The owner chooses; only then a finalizer writes the canonical twelve-section contract and chosen HTML.
   No direction may approve itself. Failed siblings remain visible. The final contract is one behavioural source
   of truth; unchosen revision-specific files remain immutable and viewable.
7. Iterate instead of regenerating: `design iterate REQ-NNN ref@vN --direction a --comments "..."` (or
   «Iterar esta dirección», or feedback that targets one direction) starts ONE Designer that reads that direction's
   html/tsx/md/json, applies the comments and writes `design/<ref>.r<N+1>.dir-<key>.*`. Keep its name, composition,
   navigation and motion except what the comments change; keep the eight-axis note and evidence JSON valid; rebuild,
   run `contrast.py` and `kit/audit_mockup.py`. No thumbnails. The result is a single-direction choice: only its
   selector evidence is checked (no pairwise distinctness); the owner iterates again or chooses it.
8. A plan change never restarts chosen work. Once the owner chose a direction, a change in the UI brief amends it
   (`design amend REQ-NNN ref@vN`, «Actualizar diseño», or `design sync`): the Designer gets the previous/new brief
   diff and revises the finalised contract and mockup (`design/<ref>.amend-<N>.*`, copied over the canonical pair
   only when valid) or, while choosing an iteration of the chosen direction, iterates it with the delta. Directions
   are regenerated only before any choice, or with `--fresh` / «Rehacer diseño».

## Anti-slop critique, before reporting

- Put the mockup next to the current screen. If a user of the product would not recognise it as the same app
  (shell, navigation, header, tokens, fonts), it fails. Avoid identical card grids and ornamental KPI tiles.
- No invented content: no invented names, dates, slogans, headlines, hero titles or marketing copy. Copy comes from
  the requirements and the existing UI; mock data is neutral, realistic, clearly mock and only what the flows need.
- Default eyebrow, purple gradient, cream/terracotta, glowing text, rainbow charts or endless fade-up sequences
  need an explicit product reason. The project's own tokens win; the kit's mauve applies only without them.
- Type must express hierarchy; data and controls stay legible. No meaningless badges, fake proof or filler icons.
- Critique with observable facts: clipped control, competing primary actions, unequal padding, unreadable label,
  repeated skeleton. Do not invent claims about usability without evidence. Fix mechanics before ornament.

## Rich motion with a point of view

Use load choreography, staggered groups, view/state and shared-element transitions, hover/press/focus,
scroll-driven accents, animated typography, success/error and empty-state delight. Choose a grammar per direction:
precise quick cuts, elastic spatial springs, or tactile compressed/settling gestures are different languages.
Write timing and easing tokens; profile subtle/natural/expressive scales them. Expressive is the mockup default.
Repeated interactions: roughly 120–250ms; showcase sequences can be longer if content remains immediately available.
Avoid scale(0), repeated bouncing and one generic fade-slide on every element. Interruptible gestures use springs.
Transform/opacity first. GSAP/Motion are installed and bundled offline. Pause heavy effects offscreen or when the
tab is hidden. Under reduced motion or `?still=1`, remove travel/parallax and infinite effects, show final content,
keep feedback immediate. No flashing, hidden content, lost focus or low contrast at intermediate frames.

## Sources, distilled locally (no runtime network)

These are adapted techniques in our own words. Research/ranking with the full source inventory is preserved in
`designer-kit-phase4.research.md` in the methodology bitácora; no upstream source is executed by the Designer.

| Source | Pinned revision | Adopted / limit |
|---|---|---|
| alchaincyf/huashu-design | 4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1 | Best fit: six thumbnails → three directions, facts-only critique. Shared product identity wins over novelty; siblings are reused, not avoided. |
| Leonxlnx/taste-skill | 12af471f627f866411b4bd785b19646d3672784c | Product concept, direction critique, app-screen hierarchy. Do not copy house bans that conflict with owner tokens. |
| pbakaus/impeccable | 414603bf14c7a344edb466bb1f85690c77ce8b7d | World-building, working-screen clarity, deliberate animation/delight. Exclude CLI/hook ceremony. |
| Nutlope/hallmark | 7ec868225c6caa040558c321ee0fefa0e73f83a8 | Floor/reflex/finish checks and per-theme material/motion. No branding stamp. |
| emilkowalski/skills | 2d228630ba1446365f614a108cb8252f1feda202 | Interaction easing, interruptible springs, duration by frequency. Short controls do not forbid showcase choreography. |
| oil-oil/oil-ui | c60d91d0ebdcfb96cac6f3988823291549ea6190 | Distinct skeleton/type/visual/motion, direction card and squint test. |
| LottieFiles/motion-design-skill | f9a8a041b85185ee4881b3471d3415e939aac772 | Choreography and per-direction motion personality. |
| zanwei/design-dna | 593e39bc9e3652734653bd75544a333d7d43615e | Separate measurable tokens from qualitative claims; rendered comparison. |
| Gesso-Build/skills | 1c3908b7efb56ec24624436dea5c32a371eb487c | Mechanical guards beat adjectives; reject blanket underline bans. |
| miqdadbadjuber/anti-slop | 5ca57fe37c60670064abf3beae775e3dad6687a1 | Generator tells and energy/rhythm/motion dials; avoid copying its large checklist. |
| anthropics/skills frontend-design | dbd4588f9e1033efb41dad4bef2f7947c8993d44 | Subject-driven direction; one memorable interaction detail, never a new identity. |

Reference libraries such as awesome-design-md and awesome-claude-design are stance pools, not design methods.
The deeper research rejected derivative lists/product funnels and sources whose video-film advice did not fit UI.
Borrow structure or motion craft, never a brand's marks or a claim that this product is that brand.
