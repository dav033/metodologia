# Designer kit phase 4: anti-slop, directions and motion research

Research for `designer-kit-phase4.md`, including its ADDENDUM. Date: 2026-10-26. All repos were cloned with
`git clone --depth 1` into `/tmp/claude-1000/antislop/<owner>_<repo>` (scratch: deleting it loses nothing,
because the commits are pinned below). Everything here is a paraphrase in our own words, with short quotes
only. The Designer must not need to open these repos at run time: distil from this file into
`david-ui-kit` / `mockup-craft` references.

Source ids used below: **HS** huashu-design, **TS** taste-skill, **IM** impeccable, **HM** hallmark,
**AF** anthropics frontend-design, **AS** miqdad anti-slop, **EK** emilkowalski/skills, **OIL** oil-ui,
**LF** LottieFiles motion, **DD** design-dna, **GS** Gesso slop guards, **AU** auteur, **XI** plugin87 (XIAS),
**UC** ui-craft, **GJ** genjutsu, **ED** elayadesign design-to-motion, **TR** Trystan Claude Design prompt,
**BY** baoyu-design, **SS** styleseed, **DE** AgentsORG design-engineering, **IB** ibelick ui-skills,
**KZ** kylezantos motion principles, **GSAP** greensock skills, **IA** iart-ai, **MD** motion.dev skill,
**FX** frankxai, **VA** VoltAgent awesome-design-md, **RG** rohitg00 awesome-claude-design.

## 1. Sources

Stars are from `gh api` on 2026-10-26.

| Id | Repo | ★ | Licence | Pinned commit | What we take |
|---|---|---|---|---|---|
| HS | alchaincyf/huashu-design | 26.9k | MIT | 4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1 | 6 candidates → 6 thumbnails → 3 full directions; 3 seed logics; look ledger; rendered `design_lint.py` (fingerprint, compare, families); 84-style specimen library; colour derivation protocol; concept-first critique with a veto; animation grammar (expo-out, focus = dim + blur, "stop dead" ending) |
| TS | Leonxlnx/taste-skill | 103.0k | MIT | 12af471f627f866411b4bd785b19646d3672784c | dealt directions plus "choose the one that carries the subject's idea"; idea sentence and competitor test; dated tells registry; app-screen chapter (product "face", one question, honest states); motion tokens and budget; Awwwards-weighted critique with caps |
| IM | pbakaus/impeccable | 89.3k | Apache-2.0 | 414603bf14c7a344edb466bb1f85690c77ce8b7d | world-building: 7 candidates from the audience's culture, rut + predictable opposite, ≥3 material families; Operate mode (the world lends only type, palette, density and one signature move); colour strategy tiers; direction contract; challenger "donation" of discipline, not clothes; animate/delight theses |
| HM | Nutlope/hallmark | 36.6k | MIT | 7ec868225c6caa040558c321ee0fefa0e73f83a8 | gate catalog (Floor/Reflex/Finish, M/R/J classes); per-theme "material" line and a motion line per theme; app-screen rules (4 data states, motion is state); pre-emit PHESRV critique; mirror test; 12 ways to open a section without an eyebrow |
| AF | anthropics/skills `skills/frontend-design` | 184.0k | Apache-2.0 (folder LICENSE.txt) | dbd4588f9e1033efb41dad4bef2f7947c8993d44 | the 5 named convergence clusters; plan → review against brief → build; "spend your boldness in one place" |
| AS | miqdadbadjuber/anti-slop | 7.3k | MIT | 5ca57fe37c60670064abf3beae775e3dad6687a1 | Tell/Why/Fix catalog incl. App & Dashboard tells; ENERGY/RHYTHM/MOTION dials at 3 levels; "draft without direction" label |
| EK | emilkowalski/skills | 50.2k | MIT | 2d228630ba1446365f614a108cb8252f1feda202 | frequency → animate-or-not; strong custom curves; duration table; never scale(0); origin-aware popovers; press scale .97; blur to mask crossfades; @starting-style; springs for interruptible gestures |
| OIL | oil-oil/oil-ui | 2.4k | MIT | c60d91d0ebdcfb96cac6f3988823291549ea6190 | direction card fields; distinctness rules ("of skeleton, type, colour, main visual, any two directions share at most one"); squint test on block masses; category-template list; motion "feel" = onomatopoeia + a real object, with spring numbers; overshoot scales with area |
| LF | LottieFiles/motion-design-skill | 2.5k | MIT | f9a8a041b85185ee4881b3471d3415e939aac772 | 4 motion personalities with duration palettes; choreography rules (lead with hero, one origin, 1/3 rules, stagger patterns); dashboard/modal/list recipes; distance-duration scaling |
| DD | zanwei/design-dna | 2.0k | MIT | 593e39bc9e3652734653bd75544a333d7d43615e | DNA JSON schema (design_system / design_style / visual_effects); k-means palette with coverage; verify by ΔE |
| GS | Gesso-Build/skills | 93 | MIT | 1c3908b7efb56ec24624436dea5c32a371eb487c | ~73 deterministic guards with exact detection conditions; opt-out with a written reason; per-rule score cap |
| AU | agiwhitelist/auteur | 1.0k | MIT | 9bca227df9877e60dc45d49783c8cbd885eccd9b | 7-field commit sheet: reflex check a/b/c, "house tells broken", background L as a number, motion budget ≤3 families; motionqa (FPS at DPR 2, long tasks) |
| XI | plugin87/ux-ui-agent-skills | 3.0k | MIT | 594b26204d92cbf02e635195e5ebe0d83c7ed3ac | rendered gates, notably the reduced-motion PARITY check, screen economy and the taste audit; "a missing browser is not a pass" |
| ED | elayadesign/ai-design-skills (own search) | 8.0k | MIT | 5e578402da175cdc539c900e4b09ceecfadcb37c | design-to-motion: load choreography table per element kind; **story loops** (every data visual acts out what it does); `?still` frame; motion checks (rest frame equals landed frame) |
| UC | educlopez/ui-craft | 401 | MIT | 49b751742b013ebb3e0495eb7992423185f04be0 | 5 duration tokens; "when rules break"; exit at ~75%; suppress entrance on first paint for toggles; skeleton after 200 ms |
| GJ | AThevon/genjutsu | 687 | MIT (LICENSE file) | 1f518a71378b15d423389e546e767cffc86e14c3 | visual + interaction thesis (4 required fields each); `Allowed patterns:` line; tells in 4 families; designer lenses (Kowalski / Krehel / Tompkins) |
| TR | Trystan-SA/claude-design-system-prompt | 2.0k | MIT | 3c3ddb07d7aa3fef051d83608596470c95cfd8fe | variations ordered basic → bold; one file, many variants, with captions and a pick |
| BY | JimLiu/baoyu-design | 4.5k | MIT | 6530033592bf7fa58bc1a5a2a2ad278da45213a9 | design canvas with artboards for side-by-side variants (Claude Design port) |
| SS | bitjaru/styleseed | 990 | MIT | bf7df20ef467ef81dde17d7c029c7f9619e69dbe | three named direction slots: native / signature / experimental; ≥2 structural axes must vary |
| DE | AgentsORG/design-engineering | 35 | MIT | df866a457488f47bb5dccf679c4d68889dfa6a9f | transition catalog: 280 ms 5-stop error shake, cross-blur, enter with more properties than exit |
| IB | ibelick/ui-skills (own search) | 10.2k | MIT | 59193a75432e5f41c6980f53b9e6a7bd56919947 | baseline-ui on our exact stack (Base UI, motion/react, Tailwind, `h-dvh`, `tabular-nums`, z-index scale) |
| KZ | kylezantos/design-motion-principles | 1.4k | MIT | 4a9ca879f24a361f4dca4174fe2da0f67b5ddee3 | lens weighting by product type (SaaS dashboard: Emil primary, Jakub secondary, Jhey for empty states) |
| GSAP | greensock/gsap-skills | 17.2k | MIT | aed9cfd3277740755f6bfc1155c7aa645403b760 | useGSAP scope + cleanup; matchMedia for reduced motion; Flip; SplitText (all plugins now free); quickTo; performance rules |
| IA | iart-ai/web-animation-skills | 59 | MIT | b6dba3eb759726845a44163ff0bad70dd9e7fbb6 | micro-interaction defaults (motion/react springs 400/30, AnimatePresence popLayout, layout); 60 fps rules |
| IA2 | iart-ai/motion-skills | 1.0k | MIT | 238dfc55aac123d4649be39adfe58c43193ca349 | index of 19 packs only; nothing to take |
| MD | 199-biotechnologies/motion-dev-animations-skill | 212 | MIT | 3feedfb4dba8adae40fc9a5f9a23e3dda2121205 | spring parameter intuition table; whileInView once/amount |
| FX | frankxai/awesome-motion-design-agent-skills | 83 | CC0-1.0 | b45d60fa5b0f7b7d07331572416b80e17dcfd203 | SITE_MOTION_SPEC template (still-frame gate, beat sequence, reduced-motion replacement) |
| VA | VoltAgent/awesome-design-md | 123.7k | MIT | 3b605329240ce735b510037cca322f1831fdd7f8 | 84 brand DESIGN.md files as stance material (§9); note: almost no motion data |
| RG | rohitg00/awesome-claude-design | 1.2k | MIT | 7f60ee56b9340f8c2671a08c2d8aab4037546a64 | aesthetic-family grouping; "remix" recipes (brand A × brand B); 3-designer-debate prompt |

### 1.1 Ranking: what is genuinely best and what is hype

1. **HS huashu-design**: the best fit. It is the only source with a tested multi-direction pipeline
   (blind-choice lessons written down), a ledger and a rendered linter that fingerprints and compares
   directions. Its key lesson: banning looks made output boring, so add options instead of bans (§3).
2. **TS taste-skill**: the most evidence-backed rules (a 247-site study and a 23-screen app study) and the
   best app-screen chapter for planning UI. Very strict house bans (no hairlines, no mono, no eyebrows):
   adopt the rules for app screens, and treat its page bans as defaults the brief can override.
3. **IM impeccable**: the best world-building method and the right limit for working screens ("the world
   lends type, palette, density and one signature move, never the layout or controls"). Heavy on tooling
   (concept-seed, comp gates) that we should not copy.
4. **EK emilkowalski/skills**: the best source for interaction motion; concrete numbers, short. Its "<300 ms"
   rule is for repeated UI, not for the showcase layer the owner wants.
5. **HM hallmark**: the best gate catalog, plus per-theme motion lines. Its stamp and log ceremony is overhead.
6. **OIL oil-ui**: excellent distinctness rules and motion-feel table (Chinese). Small and practical.
7. **ED elayadesign design-to-motion** (found in my own search): the missing piece for "lots of animation"
   in dashboard mockups: story loops and load choreography per element kind.
8. **GS Gesso**: the most mechanical rule set (exact thresholds), but static source analysis; port the
   conditions to computed styles. Some rules are wrong for us (it flags every underline, which hurts
   accessibility in prose).
9. **LF LottieFiles**: solid, compact motion tables; good for per-direction personality.
10. **XI plugin87**: strong rendered gates (reduced-motion parity is a must-have); the README is
    badge-heavy and the 2,144 "design systems" library is noise for us.
11. **AF frontend-design**: short and right; superseded in depth by 1–3.
12. **DD design-dna**: useful schema and measured palette; the qualitative half is unmeasurable prose.
13. **AU auteur**: the commit sheet is very good; its motion numbers are copied from Emil.
14. **AS anti-slop**: a good tell list and the 3 dials, but verbose and rule-number heavy.
15. **GJ genjutsu**: the thesis + `Allowed patterns:` idea is valuable; the rest duplicates others.
16. **UC ui-craft**: decent tokens; some advice conflicts with the stronger sources (it recommends
    "sparklines on all" KPI cards; TS found 0 of 23 real screens use them).
17. **KZ, DE, MD, GSAP, IA, IB, TR, BY, SS**: narrow or derivative. Take the specific item listed in the table.
    GSAP's official skill is accurate API guidance, not design. IB conflicts with the owner ("never add
    animation unless requested").
18. **Hype or nothing to take**: IA2 (an index of paid-product packs), FX (mostly strategy prose and
    provider routing, apart from one template), RG (mostly a curated mirror of VA plus marketing), and VA as
    a design method (it is a reference library, valuable only as stance material).

My own search (`gh search repos`, sorted by stars) found two things worth adding: **ED** (8k★) and **IB**
(10k★). I rejected, after reading descriptions or files: `bergside/awesome-design-skills` and
`Owl-Listener/designer-skills` (lists), `dominikmartn/nothing-design-skill` (one brand language),
`superdesigndev/superdesign-skill` (a product funnel), `senlindesign/taste-skill` and `h3nryprod01/design-taste`
(derivatives of TS/EK), `cth9191/motion-design` and similar (video films, not UI), and the many 0–20★
anti-slop repos (they are derivatives of TS/HM/AF).

## 2. Slop tells to refuse

Rule of use (HS, TS §8, GJ): a tell is a default nobody chose. A direction may keep one only by naming it in
its `Allowed patterns:` line with a reason drawn from the product (GJ, HM waivers, AU `auteur-allow`).
Removing tells is not enough: an emptied page is a tell too (TS "avoidance aesthetic"; AS "sterile default").
Fill the space with scale, real content, the product's own object or a colour field.

**Look families (HS lesson).** Warm paper + serif, near-black + one accent, hairline broadsheet, the
SaaS card kit and flat saturated neo-brutalism are legitimate looks. Each becomes a tell when it appears
regardless of subject (AF), when two of the three directions share it, or when it repeats the ledger
(HS). Do not ban the families. Gate on collisions.

### Colour
- Purple→blue, purple→pink or cyan-on-dark gradients anywhere, including gradient text. (HM 2a, TS, AS, GS)
- Gradient-filled headline or metric (`background-clip:text`). (GS gradient-text, TS, UC)
- A gradient fill on rounded tiles and buttons; two-hue "candy" tiles. (GS gradient-fill/multicolor-fill)
- Tailwind default swatches as the accent: indigo-500/violet-600, the violet band; emerald as the "safe" escape. (GS, HM 74)
- Cream ground + high-contrast serif + terracotta/clay accent (#F4F1EA / #D97757 family) when the brief did not ask for it. (AF, TS 3rd wave, HM 65, IM, HS)
- Near-black navy (#0D1117) + neon accent + glow. (HS forbidden zone, TS, AF)
- Glow: a coloured zero-offset halo, aurora or mesh blobs, blurred orbs behind text. (HM 29, GS dark-glow, IM craft-floor)
- An accent sprayed on chrome (nav pills, every button, tabs, links) instead of on data and one action. (TS app §13, AS)
- More than 4 hues on one screen, a hue per bar, a rainbow chart. (TS app, HS critique #3)
- Pure #000/#fff as surfaces, and zero-chroma greys next to a chromatic anchor. (HM 7a/22, XI, TR)
- A dark or saturated sidebar against a light canvas (0 of 17 real light screens). (TS app)
- Light or dark chosen by category ("dark = tech/premium") instead of by use scene. (IM, AS, AU)

### Type
- Inter, Roboto, Arial, system-ui as the display face; Fraunces, Playfair, Space Grotesk, Instrument Serif, DM Sans, Plus Jakarta, Geist as an unexamined reach. (HM 1, IM list, HS typography, GS)
- One word of a headline set apart by italic, colour, weight or underline. (AF, HM 38i/38iii, GS multicolor/mixed-style)
- Eyebrows: tiny tracked uppercase labels above headings, pill badges above the H1 ("New", "Beta"). (TS, HM 54/67, AF, IM, AS, GS)
- Monospace as costume for labels and captions when the content is not code, an ID or a measurement. (TS, HM 64, IM, AF)
- Nine near-equal sizes; heading-to-body ratio under about 2.5–3×. (TS, HS critique #2, XI taste audit)
- Display tracking tighter than -0.05em; body tracking ≥0.08em without caps; body leading under 1.25–1.3. (GS, HM 75, IM)
- Body text under 14px (web) / labels under 11–12px; prose wider than 75ch. (HS, HM 25/75, TS)

### Layout and structure
- Hero, logos, 3 icon features, testimonial, pricing, CTA, footer, in that order. (TS, AS, HM 8, AF)
- Three or more identical cards, each an icon in a tinted square + heading + text. (all sources)
- Card inside card; every section wrapped in a rounded card ("container soup"). (HM 4, GS nested-cards, RG, UC)
- One medium radius (12–16px) on everything; or over-rounded panels with a radius of 40–120px. (TS, GS over-rounded-card, AS)
- A soft grey shadow under every resting card; a 1px border plus a wide soft shadow on one surface ("ghost card"). (TS, GS ghost-card, HM F24)
- A thick coloured left stripe on cards, list rows or callouts that marks no state. (GS edge-stripe, IM, AS, TR)
- Every section separated the same way, with the same gap; neighbouring sections in the same layout family. (HM 9, TS critique pass 9)
- 01 / 02 / 03 index numbering on content that is not a sequence. (AF, TS, HS, GS)
- Centred everything (over ~72% of text blocks centred). (TS)
- Default dashboard shell: dark sidebar + top bar with search/bell/avatar + 4 KPI tiles + gradient area chart + zebra table. (TS app §14, AS, OIL)
- Bento grid used because it is the default, not because the content has unequal sizes. (AS, TS)
- Glass panels and floating blurred pill navigation. (TS, AS, IM)
- Decorative grid/dot/blueprint backgrounds and repeating stripes with nothing under them. (AS, GS, IM)

### Components and data
- KPI tiles: an icon in a coloured circle, a green "+12.5%" pill and a sparkline on each. (TS app, AS)
- Invented metrics, logos, testimonials, "trusted by 10,000+ teams", 99.9%, 10x; placeholder people (John Doe, Acme, "Sarah Chen updated a document"). (HM 46a, GS fabricated-precision, AS, TS)
- A fake product drawn from grey bars and donuts; a hand-drawn browser window or terminal frame. (TS, HM 47a/47c, AS, UC)
- A fat donut with slice labels; gridlines every 20px; a legend for a single series. (TS app)
- Saturated status chips with white text; uppercase tracked table headers; zebra rows. (TS app)
- Emoji as icons; generic "AI" sparkles, robots and orbs as feature icons. (all)
- A decorative status dot, a pulsing "LIVE" dot or blinking caret that marks nothing. (TS, HM 63, AS, GS live-clock-eyebrow, RG)
- Pagination under a 5-row overview list. (TS app)
- An empty chart with an illustration and "No data yet". (TS app, AS)

### Copy
- The genre lexicon: seamless, effortless, elevate, supercharge, unlock, unleash, empower, streamline, world-class, game-changer. (HM 19, GS benefit-speak, TS)
- "Not just X, it's Y"; tricolon adjectives; "Get started" / "Learn more" beside the primary; "Oops". (HM 19, GS)
- Middle-dot meta strings (A · B · C), "→" glued to every button, "WORD — fragment" labels, em-dash floods. (AF, HM 63, HS, GS)
- Category labels as headings ("Features", "Why us"); section heads that a competitor could reuse unchanged. (HM craft §6, TS)

### Motion
- The same fade-up on every block; a dozen staggered hero entrances. (TS, AF, IM, AS)
- Hover lift or zoom on every card and image; more than one hover effect per element. (TS, HM 11, GS hover-scale-image)
- Bounce or elastic easing on interface state, or cubic-bezier y outside 0–1, unless the direction declares a playful spring posture. (TS, HM 12, GS bounce-easing, UC)
- `transition: all`; animating width, height, top, left, margin or padding. (HM 10a, GS, all)
- Infinite loops that mean nothing (pulsing dots, floating shapes, shimmering text, rotating badges); loops that do not pause. (TS, HM, AS, GJ)
- Content hidden until a script runs, and reveals that fail and leave a blank band. (HM 62, TS, GS reveal-specificity-trap, XI parity)
- Scramble or typewriter text that holds words hostage; preloaders and counters; custom cursors; scroll hijacking. (TS)
- Animating keyboard-initiated or 100×/day actions. (EK)
- A slow fade-out ending; uniform tempo with no peak. (HS)

### Conflicts between sources (decide in the kit)
- **Skeleton shimmer**: TS says flat grey bars with no shimmer; UC and ED allow a subtle pulse or shimmer. The owner wants shimmer: allow one linear shimmer at the final geometry, shown after 200 ms, stopped under reduced motion, never a spinner on top.
- **Hairlines/mono**: TS bans them; HM allows mono when it is the theme's material (a measured reading); TS app allows 1px borders on working screens. Allow them in a direction only through `Allowed patterns:`.
- **Underlines**: GS flags all underlines; keep link underlines in prose (accessibility) and drop them in chrome.
- **Sparklines on KPIs**: UC says yes; TS's real-screen study says no. Follow TS by default.

## 3. Three directions

### 3.1 How the sources diverge on purpose
- **HS**: three seed logics, two candidates each: *best designer* (who would you hire with no budget limit? use
  their thinking, not their look), *real reference* (a verified excellent work in the same medium, screenshotted
  and broken into rules: grid columns, heading/body ratio, colour share, image/text relation) and *seconds
  roulette* (a random style from the specimen library). Thumbnail all six, then build the strongest three.
- **TS**: a script deals 3 researched directions out of 20. Hold each against the subject inventory and pick
  the one whose way of composing "can carry something only this client has". Never redraw for comfort.
- **IM**: an assigned direction plus dealt challengers. Fuse each challenger with the product's facts, then
  weigh it on audience identification and product clarity only. A declined challenger still donates its
  *discipline* (a palette's total commitment, a grid's density courage), never its clothes (a button shadow,
  a display face).
- **HM custom path**: "sketch three directions as far apart as you can make them, two lines each", then build
  the one a design lead would fight for. Before that, picture the page you would make anyway and its obvious
  twist: neither ships.
- **SS**: three slots named native (the category done superbly), signature (a product-specific move) and
  experimental. **TR**: by-the-book, refined, novel. **OIL**: at least one direction breaks the category
  template, and all three must be viable (no straw men put in to flatter the favourite).

### 3.2 Axes that must differ (the kit's axis table)
| Axis | What "different" means |
|---|---|
| Concept | a different item from the product's world becomes the device (§5); the competitor test still passes |
| Layout archetype / navigation | rail vs top bar vs command-first vs canvas-first vs split list-detail (IM operate comps 2–3; TS app shells: open plane, tinted frame + white sheet, ruled T-frame, icon rail, no sidebar) |
| Type | different families *and* scale strategy (huge ratio vs quiet exact; one family vs a pair with a role split) |
| Density / shape | sparse/medium/dense moved together (row pitch, padding, type size; TS app §10); square vs fully round vs soft, chosen once |
| Signature component treatment | the one element only this product has (TS "face"; IM "signature move", named concretely: "service health as a transit map") |
| Colour logic | strategy, not swatches: Restrained / Committed (30–60% of the surface) / Full palette / Drenched (IM); different hue family or monochrome per direction (OIL); background L as a number (AU) |
| Motion language | a different personality and feel (§4.7) |

**Hard rule (OIL)**: of {skeleton, type, colour, main visual}, any two directions may share at most one.
Core interaction and memorable moment must also differ, or the pair is "a re-skin" and is rejected.
**Squint test (OIL, TS)**: put the first viewports side by side and blur them. If the block masses fall in the
same places (big block left, small block right), the skeletons are the same, whatever the fonts and colours.

### 3.3 Seeds are stances, not palettes
- Phrase a seed as a way of working with the product: "operational/editorial-dense", "kinetic/expressive",
  "tactile/playful", "quiet instrument", "the printed artefact of this trade". Pull each from a different
  logic (HS) and from a different material family (IM).
- Stances may borrow from a brand language (§9) or a specimen (§10). Rule: take the system grammar (density,
  type relation, colour proportion, motion temperament), never the marks, names or exact palette. Derive the
  colours from the product (HS colour protocol: sample from brand, real images and cultural context;
  converge in OKLCH to 2–3 chromatic + 1 neutral ramp, hues ≥60° apart or L ≥0.3 apart; write one
  sentence "why this colour". "Can't write the sentence = you copied a recipe.")
- With a brand fixed: all directions stay inside it and vary skeleton, main visual and interaction (HS, OIL).
- At most one of the three may "go all the way" (whole page as a prop, a universal metaphor such as a
  metro map, terminal, newspaper front page or cockpit, everything at full saturation). Test: remove the
  device; if the information gets clearer, it was overdone (HS). For working screens a tool's own interface
  (terminal, scope, control panel) is costume (IM operate).

### 3.4 Self-critique and refusing a re-skin
- Write each direction as a card before building (HS card fields: logic and source; what is borrowed as
  concrete rules; protagonist material; skeleton in one line; where the boldness is spent; "where in the
  content the form comes from"). OIL adds: north star, protagonist + primary action, control grammar in one
  sentence, motion feel, "what this direction gives up".
- Guessability test (GJ, IM): if someone could write this thesis from the category alone, or from the
  category plus the list of things to avoid, it is the default. Rewrite it.
- Reflex check (AU): (a) what a generic AI does for this category; (b) what a generic AI *avoiding* (a)
  does; (c) our argued deviation from both. Plus "house tells broken": two of the Designer's own recurring
  habits, named, that this direction does not use.
- After rendering, run the compare gate (§6.3). If two directions collide, replace one with a spare
  thumbnail or change its skeleton, not its colours (HS).
- Present one file with a switcher and a one-line caption each, plus a recommendation (TR, BY). A caption
  you cannot write means the variant is not distinct.

## 4. Motion language

The owner wants rich motion. Reconcile this with the sources' restraint by layers: (1) the **showcase layer**
(load choreography, story loops, view transitions, scroll scenes) is rich; (2) the **interaction layer**
stays fast and exact; (3) everything degrades under reduced motion. Static first: the screen must be finished
without motion (TS, FX still-frame gate).

### 4.1 Easing families (CSS tokens)
| Token | Curve | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.23,1,0.32,1)` (EK) or quint `(0.22,1,0.36,1)` (TS, UC) | entrances, UI under 600 ms, hovers that move |
| `--ease-expo` | `cubic-bezier(0.16,1,0.3,1)` | reveals ≥ 600–800 ms, line rises, openings (TS, HS, ED, IM) |
| `--ease-in-out` | `cubic-bezier(0.77,0,0.175,1)` (EK) / `(0.76,0,0.24,1)` (TS) | things that travel while visible: wipes, panels, tab indicators, Flip |
| `--ease-drawer` | `cubic-bezier(0.32,0.72,0,1)` | sheets and drawers (EK, AU) |
| `--ease-exit` | `cubic-bezier(0.55,0.055,0.675,0.19)` | something leaving for good, short (TS); never on what the user waits for |
| `--ease-emph` | `cubic-bezier(0.05,0.7,0.1,1)` (MD3) / `(0.2,0,0,1)` | one emphasised element per viewport (UC, LF) |
| linear | `linear` | scroll-linked scrubbing, marquees, shimmer, progress |
| ease | `ease` | colour and opacity hover only |
No `ease-in` on UI (EK, UC). No overshoot on interface state except in a direction that declares a playful
spring posture (HM 12): then on the primary control and one character moment only.

### 4.2 Durations and staggers
- Press 100–160 ms (scale 0.95–0.98); hover colour 150–200 ms; hover that moves 300–400 ms; tooltips
  125–200 ms (wait 800–1000 ms on hover, 0 on focus, no delay on later hovers); menus and selects
  150–250 ms; modals and drawers 200–450 ms; view/page transitions 300–480 ms; reveals 600–900 ms; picture
  openings and wipes 1100–1300 ms. Exits at 60–75% of the entrance. Scale duration with distance
  (LF: 50px 0.8×, 200px 1.3×, full screen 1.8–2×).
- Staggers: characters 20–40 ms (headings of 1–3 words only); lines 75–110 ms; list items 30–80 ms; page
  section parts 60–90 ms; containers 80–90 ms. At most 4–6 visible steps per sequence; at most 1/3 of
  animated elements moving at once (LF). Never block input while a stagger plays (EK, UC).
- Frequency rule (EK): 100+/day (keyboard, command palette) means no animation; tens/day means minimal;
  occasional means standard; rare means expressive.

### 4.3 Choreography recipes
- **Page/app load**: the frame first (shell, static surfaces), then containers in reading order 80–90 ms apart;
  inside each: header → labels → values → visuals (ED). Settled by about 1.2 s on a page (TS); a
  showcase dashboard may take 2–2.5 s (ED). Nothing above the fold waits for scroll. Entrance kinds (ED):
  `up` y 10px + blur 4px; `left` x −10px for sidebar rows; `pop` scale 0.82–0.88 for icons, badges and
  avatars; `card` y 24px + scale 0.985 + blur 6px; `wipe` clip-path left→right for bars; `line/grow`
  scaleX/Y from the start edge for rules and timelines; `donut` conic sweep from 12 o'clock. Only lines and
  bars grow from zero.
- **Dashboard load (LF)**: skeletons 100 ms → hero metric 250 ms (100 ms delay) → cards stagger 50 ms → chart
  draws 300 ms with the cards. Numbers count from the previous value over 400–800 ms on ease-out, formatted
  with `Intl.NumberFormat`; announce only the final value (HM).
- **Story loops (ED)**: after the intro, each data visual acts out what it does, then returns exactly to the
  landed frame: a new item lands on a stack and the others step back; a scrubber glides across a line chart
  with a counting tooltip; bars breathe and settle; a highlight searches a calendar for a free slot and the
  event glides in; pulses travel along pipeline connectors; a cursor inspects table rows. Write the story in
  one sentence per visual before building. This is the main tool for "lots of animation" on planning screens.
- **View/state transitions**: shared element. The thing clicked becomes the next view's protagonist (OIL):
  list row → detail, button → panel, search icon → input. Use Motion `layout`/`layoutId`, GSAP Flip or the
  View Transitions API (≤480 ms). One direction per switch: if the card slides left, title, index and ground
  slide left too (OIL). The protagonist moves first; affected elements follow 40–80 ms later with smaller
  amplitude (OIL, LF).
- **Focus shift (HS)**: dim *and* blur what loses focus: `brightness(.5) saturate(.7) blur(4px)`, opacity
  ≥0.4, then a 150 ms flash where focus lands. Opacity alone leaves the background sharp.
- **Scroll-driven** (only where the screen scrolls): CSS `animation-timeline: view()` inside `@supports`,
  linear, locked to the scrollbar; parallax under 8% of the element; scale 0.94–1.15; reveals fire once at
  85–90% of the viewport (TS). Gotcha: `overflow:hidden` creates a scroller, so use `overflow:clip` on frames (TS).
  Heavy scenes: GSAP ScrollTrigger with `scrub:true`, at most two pinned stages, a line of text on every held screen.
- **Micro-interactions**: `:active` scale .97; never scale(0), start at .9–.97 + opacity 0 (EK); popovers
  scale from their trigger (`transform-origin: var(--transform-origin)` in Base UI), modals from the centre;
  enter with more properties than exit (DE); hover is one signal per element (HM 11); focus rings appear
  instantly, never animate (HM 15).
- **Skeleton**: final layout geometry, each value a bar at its real size, labels and headers shown at once,
  no layout shift when data lands (TS); shown after 200 ms (UC); optional shimmer (§2 conflicts).
- **Success/error**: routine saves are silent or a label swap ("Copied", 2.5 s), with no toast for visible
  effects (HM). A success check draws its stroke with no wobble (UC). Error: 280 ms shake at
  0/28.57/57.14/78.57/100% with ±4, ±4, ±2px, `cubic-bezier(.36,.07,.19,.97)` (DE), and the message in the
  reserved helper line. Optimistic update with a rollback over 220 ms (HM).
- **Empty states**: the frame and header stay, one sentence plus one action (TS, HM); a tiny product-world
  moment is allowed here (KZ: the "Jhey" lens belongs in empty states).
- **Ending a sequence**: hold the final frame; no fade-out tail (HS). Leave 100–200 ms of stillness after
  resolution before new motion (LF).

### 4.4 60 fps
Animate `transform`, `opacity`, and when smooth `filter`, `clip-path` and masks (HM, IM). Keep blur ≤ 8–14px and
never on body text at rest. `will-change` only during an animation. Do not drive many children from one CSS
variable on a parent (TS, EK). Pause loops off-screen and in hidden tabs. Use `gsap.quickTo` for
pointer-driven values. Accordion height: `grid-template-rows: 0fr→1fr` is the accepted exception. Measure on
a production build at DPR 2 (AU motionqa: min 50 fps, long tasks ≤50 ms).

### 4.5 Reduced motion
Under reduce: fewer and gentler, not none (TS, IM, EK). Keep opacity and colour changes and meaningful state
feedback; drop travel, scale, parallax, autoplay and loops; swap spatial transitions for a 150 ms crossfade
(HM). The reduced page *is* the finished page: every hidden start state lives inside
`@media (prefers-reduced-motion: no-preference)` or under an `html.js` class, so content is visible with no
JS (TS, HM 62). Motion: `<MotionConfig reducedMotion="user">`; GSAP: `gsap.matchMedia()` with a
`reduceMotion` condition (reverted automatically). Verify parity (§7): nothing visible at no-preference
may be invisible under reduce (XI).

### 4.6 Patterns for a self-contained mockup (React + Motion, GSAP allowed)
- **Motion**: variants with `staggerChildren`; `AnimatePresence` (`mode="popLayout"` for lists and toasts,
  `initial={false}` so toggles and tabs do not animate on first paint, UC); `layout`/`layoutId` for shared
  elements; `whileInView` with `viewport={{once:true, amount:0.3}}`; `useScroll`+`useTransform` for
  scroll-linked values; springs `{type:"spring", duration:0.5, bounce:0.2}` (bounce ≤0.25 for UI) or
  stiffness/damping per §4.7.
- **GSAP**: `useGSAP(() => {...}, {scope: rootRef})` (auto cleanup; wrap later handlers in `contextSafe`);
  timelines with labels and position parameters for the load sequence; `SplitText.create(el,{type:"lines",
  mask:"lines"})` for masked line rises (split after `document.fonts.ready`); `Flip.getState`→change→
  `Flip.from` for layout changes; ScrollTrigger only for scrubbed scenes. All plugins are free in the public
  `gsap` package. Watch `immediateRender` on stacked `from()` tweens.
- **CSS**: `@starting-style` for enter-from-`display:none`; `transition-behavior: allow-discrete`; same-document
  View Transitions; `linear()` to bake a spring curve (OIL: integrate the spring and sample 20–30 points).
- **Screenshot-safe**: support `?still` (or `data-still`) to render the landed frame for audits and thumbnails
  (ED). Use seeded randomness, never `Math.random`/`Date.now`, so captures are reproducible (HS seek rules).
  Settle or disable entrance motion before capturing (IM: a mid-animation element reads as missing).

### 4.7 A different motion character per direction
Assign each direction one personality and keep about 90% of its motion in it (LF). Name the feel as "a sound
+ an object from the product's world" (OIL), e.g. "a click like a magnet latching", "flow like poured honey".
| Character | Curves / springs | Durations | Signature moves |
|---|---|---|---|
| **Instrument** (Emil lens; LF corporate) | strong ease-out; springs 400+/30+, no overshoot | 100–250 ms; stagger 30–50 ms | translate 2–6px, no blur or scale; values tick; instant panels; motion only on state |
| **Cinematic / editorial** (Krehel lens; LF premium) | expo-out, in-out wipes; springs 150–250/15–25 | 300–600 ms reveals, 1.1 s openings; stagger 60–100 ms | y 8–16px + blur 4–8px; clip-path and mask reveals; masked line rises; shared-element morphs; slow focus dims |
| **Tactile / playful** (Tompkins lens; LF playful) | springs 300/8–15 on small objects; overshoot 10–20% small, ≤1–2% large | 150–400 ms | press squash, SVG stroke draws, pop entrances from scale .85, counting numbers, arcs not straight paths |
| **Kinetic / hard** (OIL "noisy" option; LF energetic) | `steps()` and linear jumps | 80–150 ms jumps | hard cuts, frame-skipping, snap from edge; only as a deliberate brand expression |
oil-ui's feel table: click 350–400/10–15 (buttons, switches); slide 250–300/20–25 (sheets, folds); flow
150–200/30–40 (page transitions, hero); slam 400–500/5–10 (confirm); rebound 300/8 (celebration);
float 100/25 (ambient). Heavy materials (stone, metal) lean to click/slam; light ones (paper, fabric,
balloons) lean to float/flow. HM themes show the idea in one line each, e.g. "a value changes when its source
does, a chart may draw once, no reveal" (an instrument) vs "the drum settles into its offset once on load,
never loops" (print).

## 5. World-building: identity from the product's world

- **Inventory first (TS)**: 8–12 things that belong to this product and no competitor: its name and what it
  means, its place, its numbers, the constraint it lives with, its materials and colours, its rituals and
  hours, the printed things of its world (ticket, label, timetable, manual). Search pictures from this list,
  not from the category.
- **Idea sentence (TS)**: "In this design, **[something only this product has]** becomes **[the device the
  direction calls for]**." Sources for the first blank: its output, its object or silhouette, its name, its
  place, its ritual, its artefact, its opposite. **Competitor test**: put the nearest competitor in the
  sentence; if it still works, the idea belongs to the category.
- **Candidate worlds (IM)**: name the product's mechanism, the audience's real scene and its cultural home;
  list the page this category always ships *and its predictable opposite* (both are the rut). Then list 7
  concrete systems, artefacts, places or rituals the audience knows by heart, each with why it can carry the
  mechanism and how it looks (ground, main colours, type voices, one signature). Include graphic traditions
  (notation, publications, identity programmes, data graphics). Ask what it would be as a physical object
  and what its world looked like before the web. Require ≥3 material families among the 7. Spend at most one
  candidate on the brief's literal metaphor.
- **Working screens (IM operate, TS app, HM app)**: the world lends only type, palette, density and one
  signature move. Never the layout, navigation or controls, which stay standard (shadcn/Base UI). It must
  read as a working product of its category before it reads as the world. The product still needs a face:
  its mark and scope in the shell, the brand hue on the main data element, its people and objects as
  themselves, and one element only it has (TS: an energy home's power flow, a leave planner's cover against
  the minimum). Name the screen's one question and one finding; the biggest block answers the question.
- **Material honesty (HM, HS)**: inventory real / pictures / absent. Never invent a fact; illustrative data is
  authored at full fidelity and reads as sample (IM: "truth binds claims, not demonstrations").
- **Form questions (HS)**: narrative role, viewing distance, visual temperature, capacity, visual motif; then
  one line "the form comes from <this part of the content>".
- **Example (Pictures: SEMPERTEX balloon decoration, 3D planner)**: inventory candidates are the balloon
  sizes and finishes (satin, metallic, crystal), the colour chart the decorators order from, the inflation
  and knot ritual, the event floor plan, the delivery van schedule and the garland as a modular chain. One
  idea: "the event's balloon count becomes the progress unit of the plan". A stance from print: the
  decorator's colour-chart swatch card as the selection control's grammar. Motion feel: "float like a
  helium balloon, tied off with a knot click".

## 6. Direction pipeline

### 6.1 huashu's mechanism, adapted
1. One question round (audience, core message, tone, format plus all references at once); missing answers
   become stated assumptions (HS phase 1). Restate the need; never ask "which direction?" before showing visuals.
2. A shared spec of *what to say* (not what it looks like), with fixed output size so directions are
   comparable; shared real assets and sample data.
3. Read the ledger and the owner's taste notes.
4. **Six candidates**: 2 × best designer (one bold, one restrained; vary beyond the usual names), 2 × real
   reference in the same medium (screenshot it, write the borrowed rules), 2 × roulette (seconds mod N over
   the specimen library; skip a style that matches the last 3 ledger entries). Write six direction cards.
5. **Six thumbnails** in one page (`thumbs.html`, ~480×300 each: real fonts, palette, skeleton and headline;
   details may be skipped). Look at the screenshot. Redraw a weak cell from another source (thumbnails are cheap).
6. **Pick three** in order: good on its own → mutually different (skeleton, temperature, look family) →
   no ledger collision → at most one overdone. Mixed logics are fine.
7. Build the three in parallel; each builder sees only the spec, its own card and the shared assets (no peeking).
8. Run lint, compare and ledger-check; present all three plus the three spare thumbnails; stop and wait
   for the owner. Record the shown versions, screenshot paths and the owner's exact words. Record mixes
   ("A's layout + C's colour") and taste remarks verbatim with their scope.

**Mapping to our system**: one Designer delegation per direction already gives isolation. Add a cheap
"thumbnail pass" (one delegation draws the 6 first-viewport thumbnails from 6 cards) before the 3 full
builds, and keep the 3 spares visible in the web chooser for "make this one instead".

**Look ledger**: one entry per delivered mockup: date, project/REQ/subplan, background class (light-neutral,
light-warm-paper, light-tinted, mid, dark-near-black, dark-tinted), display face, serif or not, top palette
with shares, layout vector, look families, source note (designer/reference/style id). HS prints repeated
traits (≥2 entries and ≥50%) and says "at least one direction must avoid this". Store it in the bitácora per
project plus a global file, not in the repo.

**Shared product identity vs ledger (recommendation)**: the first UI subplan of a product is an open round.
Once the owner chooses, that choice becomes the product's identity (HS exempts "iteration inside the same
project after a direction is chosen"; IM "a whole surface inside an established world: keep the visual
system fixed, derive structures from the content"). Later subplans default to **consistency**: the three
directions keep the chosen type, palette and control grammar and differ in structure, navigation, signature
element and motion choreography, and the ledger only stops them from repeating each other. The owner can ask
to re-explore. Then the ledger also blocks the previously chosen look for at least one direction.
Across products, the global ledger keeps projects from converging.

### 6.2 Design-DNA fields we can compute from a rendered mockup
Use DD's schema keys so a direction's DNA is comparable and readable. Measured (Playwright, computed styles,
screenshot):
- `color.measured_palette` (k-means k=8 over the screenshot, merged by ΔE, with coverage 0–1);
  `surface.background`; `accent.hex` and accent coverage %; `neutral.scale` (sorted L ramp); background
  class; pure #000/#fff use; count of distinct chromatic hues.
- `typography.font_families` weighted by text mass; `type_scale` (distinct sizes, max/body ratio, count
  of sizes); weights in use; line-height and tracking per role (display = largest text, body = longest
  paragraphs); uppercase-label count.
- `spacing.base_unit` (mode/GCD of margins, paddings and gaps); `section_rhythm` (gap variance);
  `content_density` (characters per 1000 px² of the viewport, interactive elements per viewport).
- `layout.alignment_tendency` (share of centred text blocks); distinct left edges; columns; max content width.
- `shape.border_radius` set (radii over boxes >120×60); `border_usage` (count of 1px borders over 200px
  wide); `elevation` (distinct box-shadow signatures, the most repeated radius+shadow pair).
- `motion`: the set of easing functions and durations from `document.getAnimations()` plus computed
  `transition-*`/`animation-*`; keyframe property sets; stagger estimate (start-time deltas between
  siblings); count of elements that move during load (TS inspector floor: ≥8, warn <16); presence of a
  reduced-motion block.
- `layout_vector` (HS: grey edge map resized to 32×20 and z-normalised) for skeleton similarity.
Written by the Designer (not measured): `design_style.aesthetic` (mood, metaphor, genre), `composition`,
`interaction_feel`, `brand_voice_in_ui`, plus the axis table.

### 6.3 Distinctness gate (`compare_directions.py`), proposed thresholds
From HS (tested): palette distance (area-weighted mean nearest OKLab distance, symmetric) < 0.06 means
"same palette"; layout-vector correlation > 0.55 means "same skeleton"; same background class + same serif
flag + same display face means "same look". Add: OIL's ≤1 shared of {skeleton, display face, colour family,
main visual}; type-scale strategy (|ratio difference| < 15% and same family means same type); a motion
collision if the easing sets have Jaccard ≥ 0.8 *and* the median durations are within 20% *and* the entrance
kinds match. Fail when any pair collides on 2 or more axes; with a brand lock (`--brand`) compare skeleton,
navigation and motion only. Show the per-pair table in the chooser.

## 7. Mechanical slop guards (rendered checks)

Run on the rendered mockup (Playwright, 1440×900 and 390×844, `?still` plus an animated pass). Each guard
has a grade: **FAIL** blocks, **WARN** needs an `Allowed patterns:` reason. Opt-out per element with
`data-slop-allow="<id> <reason>"` (GS). Every guard below is computable from the DOM, computed styles or
the screenshot.

**Colour**
1. `gradient-text` FAIL: any element with computed `background-clip:text` and transparent `color` or
   `-webkit-text-fill-color` (GS).
2. `violet-band` WARN: any computed colour (text, background, border) with OKLCH hue 280–310 / HSL 252–296,
   S ≥ .30, L .25–.88, or one of the ten Tailwind indigo/violet hexes (GS).
3. `gradient-surface` WARN: a rounded element whose `background-image` is a linear/radial/conic gradient
   with saturated stops (FAIL if stops are two hues >28° apart, or purple→blue/pink) (GS, HM 2a).
4. `glow` FAIL: a box-shadow/text-shadow/drop-shadow layer with saturation ≥ .4, blur ≥ 12px, alpha ≥ .15 (GS).
5. `cream-serif` WARN: body background in the warm cream band (L > .9, hue 40–110) and the largest text's
   first loaded face is a serif; add the clay accent within ΔE .07 of #D97757 (HS, GS, AF).
6. `dark-one-neon` WARN: background L < .2 and exactly one palette colour with chroma > .15 (HS families).
7. `accent-spray` WARN: accent hue pixels > 8% of a viewport on a working screen (HM 23), or the accent
   found on more than 2 kinds of chrome (nav item, tab, button, link).
8. `hue-count` WARN: more than 4 chromatic hue clusters on one screen; a chart whose bars each carry a
   different hue (TS).
9. `pure-black-white` WARN: computed #000 or #fff as a large surface (> 30% of the viewport) (HM 7a, XI).
10. `contrast` FAIL: text vs its resolved background (alpha-blended, walking `elementsFromPoint`) under
    4.5:1 (3:1 at ≥24px or ≥18.66px bold); focus ring and field edges under 3:1 (HS COLLECT_JS, HM 40).

**Type**
11. `eyebrow` FAIL: 3+ visible text runs ≤15px, uppercase (CSS or literal), letter-spacing ≥ 0.06em; or a
    short element immediately before the page's prose `<h1>` (GS hero-kicker-eyebrow, HS).
12. `accent-word` FAIL: an `h1`/`h2` (3+ words) containing a descendant ≤40% of its text whose computed
    colour, font-style or family differs from the heading (HS, GS).
13. `display-face` WARN: the largest text's face is Inter, Roboto, Arial, Helvetica or system-ui; WARN list
    for Fraunces, Playfair, Space Grotesk, Instrument Serif, Geist (HS, GS, IM).
14. `mono-costume` WARN: 4+ text runs ≤14px in a monospace face that are not inside `code`, `pre`,
    `[data-measure]` or tabular figures (HS, HM 64).
15. `type-scale` WARN: max text size / body size < 2.5 on a page (< 1.5 on a working screen); more than
    9 distinct font sizes (TS, XI).
16. `small-text` FAIL: text runs of ≥28 characters under 14px (not caption/footer/meta), or 3+ runs under
    11–12px (HS).
17. `tracking-leading` WARN: letter-spacing ≤ −0.05em; body letter-spacing ≥ .08em without uppercase;
    body line-height < 1.25 at 13–20px (GS).
18. `measure` WARN: paragraphs wider than ~80 rendered characters (measure in `ch` of the element's font) (XI).

**Chrome and copy**
19. `middle-dot` WARN: 2+ occurrences of `\s·\s` in visible text (HS).
20. `arrow-tail` WARN: 2+ links/buttons whose text ends in `→` (HS).
21. `numbered-markers` WARN: 2+ leaf elements whose whole text is a zero-padded index (`01`, `02.`) (GS, HS).
22. `word-dash-label` WARN: text matching `^[A-Z][A-Z\s]{1,20}\s—\s\S` (HS); `em-dash-flood` WARN: 3+ em dashes in visible copy (UC, GS).
23. `emoji-icon` FAIL: an emoji at the start of a button, link, heading, `li` or label (GS).
24. `lexicon` WARN: benefit-speak, "not just X", "Oops", fabricated precision (99.9%, 10x, "trusted by 10,000+"), lorem, John Doe/Acme (GS, HM 19).
25. `status-dot` WARN: an element ≤ 12px, round, with an infinite animation, next to a label, outside a `role=status` region (AS, GS live-clock-eyebrow).

**Layout and components**
26. `card-kit` WARN: the same `border-radius|box-shadow` signature on ≥4 elements (HS); FAIL `nested-card`: a
    card surface (radius + fill/border, holding a heading or ≥2 children) inside another card surface (GS).
27. `icon-card-row` WARN: 3+ sibling cards each opening with a lone svg/img, then a heading, then a paragraph (GS).
28. `edge-stripe` WARN: border-left/right ≥ 3px in a chromatic colour on a card or row with no state class/ARIA (GS).
29. `ghost-card` WARN: a 1px border plus a shadow with blur ≥ 24px and alpha ≤ .18 on one surface (GS, HM F24).
30. `radius-monotony` WARN: one radius value covers ≥ 90% of boxes > 120×60 and it is 9–16px (TS); `over-rounded`: a fill with radius 40–120px (GS).
31. `centred` WARN: > 72% of text blocks centred (TS).
32. `overflow` FAIL: horizontal scroll at 320–1920; any element past the viewport edge at 390 (HM 34, XI).
33. `kpi-tile-tell` WARN: in a stat tile (≤24 characters), an icon as the first child of the label, or an
    svg polyline sparkline in 3+ sibling KPI tiles (GS stat-label-icon, TS).
34. `placeholder-media` FAIL: broken images, stock-placeholder hosts (pravatar, placehold.co, randomuser),
    relative paths in a single-file deliverable (GS, HS).
35. `sameness` WARN: the layout vectors of consecutive vertical sections correlate > 0.55 (HS method applied per section).

**Motion**
36. `transition-all` FAIL and `layout-prop-animation` FAIL: computed `transition-property` contains `all`, or
    width/height/top/left/margin/padding/inset (HM 10a, GS).
37. `overshoot` WARN: any `cubic-bezier` y outside [0,1] in computed transition/animation timing (GS),
    unless the direction declares a playful posture.
38. `will-change` WARN: `will-change` naming anything outside transform/opacity/filter/clip-path, or set on
    more than 10 resting elements (GS, EK).
39. `uniform-reveal` WARN: ≥80% of entrance animations share one keyframe set, duration and easing (TS:
    "the same fade-up on every block").
40. `motion-floor` WARN: fewer than 8 elements move during load and interaction (TS inspector; the owner
    wants rich motion).
41. `reduced-motion` FAIL, rendered twice (no-preference vs reduce) (XI): (A) no reduce policy while motion
    exists; (B) under reduce, transforms/positions still animate longer than ~150 ms; (C) **parity loss**:
    any element visible at no-preference that is invisible under reduce.
42. `hidden-without-js` FAIL: load with JS disabled; any text node with computed opacity 0 or visibility
    hidden that is visible with JS (HM 62, TS).
43. `infinite-loop` WARN: an infinite animation with no pause on hover/focus and none stopped by
    reduce/off-screen; FAIL if an auto-rotating region > 5 s has no pause control (HM 18).
44. `blank-band` FAIL: after the reveal timeout, a screenshot strip > 200px tall where text was expected is
    empty (TS reveal failure).
45. `fps` WARN: production build at DPR 2, 4× CPU throttle: median fps < 50 or long tasks > 50 ms during the
    load sequence (AU motionqa).

## 8. Critique checklist (before the report)

1. **Concept veto (HS)**: can I say the idea in one sentence? Cover the names: does it still read as *this*
   product? Swap in a competitor: does it still work? If concept ≤5/10, the overall score caps at 6.
2. **One second, five seconds (TS)**: one thing seen at a glance; in 5 s a stranger knows what this is and
   what to do. Working screen: the biggest block answers the screen's one question; the main job is one click away.
3. **Squint**: 2–3 masses with clear size steps; one focal point per screen.
4. **Edges and frame**: 2–3 left edges reused; equal outer margins; no accidental holes.
5. **Type**: decisive scale jump; ≤5 sizes; measure 45–75ch; no orphan stubs.
6. **Colour**: name the proportions (ground, ink, accent); the accent lives on data and one action.
7. **Honesty**: no invented claims, sample data reads as sample and sums close; states drawn (loading, empty, error, full).
8. **Slop tells**: run §7; every WARN is fixed or has an `Allowed patterns:` reason.
9. **Direction distinctness**: the compare gate passes; the squint test on first viewports shows different
   masses; captions are writable.
10. **Motion**: one signature moment, entrance choreography varied by content kind, story loops on data
    visuals, feedback on every control, exits faster than entrances; the reduced-motion page complete; still frame finished.
11. **Phone**: its own composition at 390px, no sideways scroll, targets ≥44px.
12. **Write the round down** (TS format): seen in one second / idea / signature element / layout word per
    section / scores (design 40, usability 30, creativity 20, content 10) / caps / top three problems with the
    screenshot each is visible in. At most 3 rounds; do not round up.

## 9. Candidate stances from awesome-design-md

VA files describe tokens, type, components and do/don'ts; they carry almost no motion data (no motion section in
the 84 files), so the motion column below is our inference from each language's temperament. Use them as
starting stances: their grammar, never their marks, names, product imagery or exact hex values; derive
colours from the product (§3.3). Two file formats exist: YAML front matter + Overview/Colors/Typography/
Layout/Elevation/Shapes/Components/Do's/Responsive/Iteration Guide/Known Gaps (74 files), and an older
9-section form with an "Agent Prompt Guide" (10 files).

| Stance (VA file) | Type | Layout / density | Shape / colour logic | Motion character (inferred) |
|---|---|---|---|---|
| **Precision instrument** (linear.app) | custom sans 500–700, measured negative tracking; mono for IDs | dense; 4-step surface ladder on near-black; product panels framed in dark | hairline borders, radii 4–12; one muted accent on mark, focus and one CTA | Instrument: 120–200 ms, tiny translate, values tick |
| **Engineered flat** (ibm, Carbon) | one family; display at weight 300; slight positive body tracking | strict grid, 1px borders, square everything | radius 0; white + one grey step; one blue accent | Instrument / productive: linear-ish exacting moves, no spring |
| **Magazine editorial** (wired) | tall high-contrast serif display + humanist serif body + humanist sans meta (three-family ladder) | story grid ported from print; type carries identity | black/white; no accent beyond inline links | Cinematic: masked line rises, slow image openings |
| **Printing press / newsroom** (aljazeera) | one sans in dense weight stacks | photo + headline packed edge to edge; rules, no shadows | one saturated marker colour that never fills a control; urgent red reserved for live | Kinetic-light: fast reveals, a live timeline that ticks |
| **Rave-flyer timeline** (theverge) | brutally heavy display up to 100px+; mono timestamps on a rail | vertical stream on a dashed rule; saturated full-bleed colour tiles | 20–40px radii; acid accents as "hazard tape" on near-black | Kinetic: snappy colour flips, hard tile entrances |
| **Monochrome bookends + colour fields** (figma) | variable sans, oversized display, light body weight | chrome black/white; full-width pastel colour-block sections between | pills for every CTA; one black primary | Tactile: playful scale/slide inside colour fields |
| **Reverent product tiles** (apple) | quiet display/text pair | one viewport per tile, alternating light/dark, very low density | near-invisible UI; one quiet blue; one soft drop under the object only | Cinematic-slow: object-led scroll openings, nothing else moves |
| **Film title card** (spacex) | condensed uppercase display, tight leading | full-bleed photo/video per band, one headline, one ghost pill | black canvas, no brand colour, no cards | Cinematic: slow crossfades, scroll-led image holds |
| **Engineering sketchbook** (posthog) | workhorse sans with weight-only hierarchy, mono for code | marginalia illustrations around dense content | warm canvas (note: near the cream tell), olive ink, one loud yellow-orange pill | Tactile: mascots and stickers pop, hand-drawn underline draws |
| **Hardware faceplate** (nintendo-2001) | system bold sans | discrete beveled panels, chamfered corners, inset modules | metallic periwinkle chrome; three-voice contrast | Tactile / mechanical: click-and-slam presses, steps() LEDs |
| **Catalog-era tables** (dell-1996) | Arial Black / Times / Helvetica | bordered table frame, "ribbon cards", dense | flat 8-bit fills; stickers | Kinetic-hard: hard cuts, blink-free steps |
| **Nocturnal private bank** (mercury) | custom humanist display/text | marketing in an ink-violet night, product in day, night bracket on every page | one indigo for actions in both worlds (watch the violet tell) | Cinematic-calm: slow dusk-to-day transitions, soft lifts |
| **Claymation B2B** (clay) | rounded display at 500, never bolder | 3D illustration as main voltage; saturated single-colour feature cards | warm white (cream tell risk); soft radii | Tactile / playful: bouncy springs on small objects, squash on press |

For working screens, the strongest five as seeds are: precision instrument, engineered flat, newsroom,
rave-flyer timeline (as a timeline/activity view) and hardware faceplate (for a tool with physical
controls). Treat the posthog, mercury and clay stances as risky: they sit next to the cream or violet tells.

## 10. huashu specimen library: is a local copy worth it?

- **Path in the clone**: `/tmp/claude-1000/antislop/alchaincyf_huashu-design/assets/style-specimens/`
  (`web/` 20, `ppt/` 20, `info/` 20, `app/` 12, `east/` 12 = 84 styles, plus 5 overview sheets
  `sheet-<web|ppt|info|app|east>.jpg`). Text entries: `references/design-styles.md` (840 lines, Chinese:
  name, temperature bold/neutral/quiet, HTML-only fidelity %, reference works, fit, "visual DNA", HTML
  technique, open fonts, specimen path), plus its colour-derivation protocol and a "default forbidden zone".
- **Size and format**: 8.4 MB total; 89 JPG renders and 84 single-file HTML specimens (596 KB for all HTML;
  368 KB for web + app + east). Each HTML is a fixed 1200×750 board with inline CSS and a Google Fonts link,
  with Chinese fictional content. Licence MIT (repo root `LICENSE`).
- **Verdict: yes, a selective copy.** Copy `web/` (20) and `app/` (12) HTML + JPG and the two sheets (about
  3.1 MB; or 0.37 MB HTML-only plus the 0.39 MB sheets) under the kit workspace, together with an English
  index (one line per style: name, temperature, fidelity, what defines it, when it fits). Skip `ppt/` and
  `info/`, which do not apply to planning mockups. `east/` is optional (Chinese/East-Asian typography; only
  if a product needs it). Keep huashu's own warning: hexes and font names in entries are anchors, not
  recipes. Re-derive colours and run the overused-face list. Specimens feed the roulette seed (§6.1) and
  give the Designer a real rendered example, because "a model that only reads the style name builds its
  average impression of it" (HS).

## 11. Not adopted, and why
- Script-dealt directions as a hard gate (TS `draw.mjs`, IM `concept-seed`): our three parallel delegations
  with the 6-thumbnail pass do the same job without a vendor library; keep the idea that a random seed
  breaks the designer's default.
- Comp-led image-generation gates (IM), stamps and logs in CSS (HM), video export pipelines (HS, ED part C,
  IA2, FX), sound design (DE, HS): out of scope for self-contained HTML mockups.
- TS's absolute page bans (no hairlines, no mono anywhere, no eyebrows ever) as hard FAILs: kept as WARNs
  overridable through `Allowed patterns:`, per HS's blind-test lesson that over-banning makes output boring.
- IB's "never add animation unless requested" and EK's "<300 ms for everything": they apply to the
  interaction layer only; the owner explicitly wants a rich showcase layer.
