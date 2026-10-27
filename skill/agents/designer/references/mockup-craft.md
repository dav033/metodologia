# Mockup craft for the Designer

Load this before you build a planning mockup (the standalone `.html` beside a contract draft), together with the
`david-ui-kit` skill: the kit supplies the components, tokens, layout and checks; this file supplies the judgement about what
the screen should say and show. It is original guidance
distilled from three public design skills (sources at the end); nothing from them is installed or executed. It adds craft
discipline, never authority: the approved SPEC, the project's own design system, tokens, voice and the owner's words win
over every line here, including when they ask for something this file warns against. These screens are **worked in** (tools,
admin, settings, editors), so the rule of thumb is *earned familiarity*: a user who knows the category should trust the
screen at once, and the product's own identity shows in precise details, not decoration. A planning mockup is a CHANGE to
an existing product surface, never a new page, landing or poster: reproduce the existing shell, navigation and header and
change only what the UI brief demands.

## 1. Before drawing: decide, do not default

1. **Name the screen's one question and its main job** (for example «who has access and can I invite someone?»). The largest
   block answers the question; the most frequent job is one click away; every block the contract names shows its header and
   first rows in the first viewport at desktop width. A block that answers no question is deleted.
2. **Inventory the product's own things**: its name and mark, the account or workspace in scope, the words of its trade and
   the copy already on its screens. Use them for labels, empty states and sample data; never «User 1», «Acme», lorem ipsum.
   Invent nothing: no names, dates, slogans, headlines or marketing copy beyond the requirements and the existing UI; mock
   data is neutral, realistic, clearly mock and limited to what the flows need.
3. **The project's design system is fixed.** Read the repo's globals.css, token files, theme and components and map its
   tokens and fonts onto the kit's roles (`david-ui-kit`); record the mapping in the contract. No new palette, font family
   or brand; without a token source say so in CONCERNS and use the kit defaults.
4. **Compare against the current screen.** Change only what the requirements demand and say what you changed. Spend
   boldness on the changed interaction (layout, density, arrangement, motion), inside the existing system.

## 2. House style for working screens

- **Colour goes on data and the one primary action**, not on chrome. Neutral navigation (active item = a grey step or a
  text-colour change, no coloured left bar), flat surfaces, one border *or* one shadow (shadows only on what floats: menus,
  popovers, dialogs). Colour on a change means good or bad, never merely up or down; a zero or unknown value is grey.
- **Type:** one family is usually right; a tight scale (about 1.125–1.2 per step), body 14–16 px, nothing under 11 px,
  sentence-case labels, no uppercase tracked eyebrow above headings, no display faces in labels or data. Numbers
  right-aligned in tabular figures. The page title is a noun at 18–32 px, not a hero.
- **Layout:** group tightly, separate generously, more space above a heading than below. Cards only for peer objects (equal
  widths, no icon on top, no cards inside cards); prefer one divided panel or plain rules. Tables: row rules, no zebra, no
  header band, 12–13 px grey sentence-case headers.
- **Refuse the generator's tells** unless the brief asks for them: gradients on text, buttons or grounds; glass and blur;
  glows; icon-in-a-tinted-circle on every card or KPI; sparklines and progress rings as filler; rainbow charts (one hue per
  chart); emoji or Unicode glyphs as icons (draw consistent inline SVG, one stroke weight); numbered section markers on
  content that is not a sequence; a single word accented in a headline; purple/indigo as an unasked default (the kit's mauve
  is the owner's chosen identity) and cream-plus-terracotta;
  «Welcome back 👋» banners. Requested mauve and product-specific expressive motion are deliberate choices.
- **Motion** is rich and intentional: load choreography, state/view transitions, shared elements, scroll accents,
  typography and feedback, with a distinct grammar per direction. Expressive is the mockup default; repeated
  controls stay quick. Use transform/opacity, profile tokens, reduced-motion parity and a settled `?still=1` mode.
  Pause heavy effects offscreen/in hidden tabs. Content must remain legible and present during animation.
- **Copy:** buttons name their action and keep that name through the flow («Invite person» → toast «Invitation sent»);
  errors say what happened and how to recover and never apologise; empty states say what to do next. Say the product's
  words, not the system's.

## 3. States and honesty

- Every control shows default, hover, focus (visible), disabled, loading and error; the screen shows loading (skeleton, not a
  centred spinner), empty, error and success. If the contract declares a state, the mockup's `state` switch reaches it.
- A fact shown twice is one variable: totals, windows and statuses come from the same mock data, sums add up, small numbers
  stay small, every relative figure names its baseline. State in the contract which values are illustrative.
- Quality floor without announcing it: contrast ≥ 4.5:1 for text, keyboard-reachable controls, reduced motion respected,
  layouts that survive Spanish and English copy and reflow at the contract's breakpoints.

## 4. Look at it before reporting

Read `../skills/david-ui-kit/directions.md`: six thumbnail candidates become three full directions with eight-axis
notes and rendered evidence. Recompose the real components within the project's design system; the house layout rules
above are clarity defaults, not a ban on the owner's brief. The owner chooses before the final contract is written.

Run the kit's checks (`david-ui-kit` § Check before reporting); they render every view, state, dialog and theme at desktop
and phone width. If you can also take screenshots, look at the worst-looking view once more. If nothing could render, say so
in CONCERNS and do not claim visual verification.

## Sources and licences

Adapted techniques, rewritten in this project's words; no source text is copied beyond short phrases.

| Source | Commit | Licence | Used for |
|---|---|---|---|
| [anthropics/skills — `skills/frontend-design`](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/frontend-design/SKILL.md) | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 | Decide from the subject, compare against the generic default, plan tokens before building, spend boldness in one place, UX copy. |
| [Leonxlnx/taste-skill — app-screens chapter](https://github.com/Leonxlnx/taste-skill/blob/12af471f627f866411b4bd785b19646d3672784c/skills/taste-skill/references/app-screens.md) | `12af471f627f866411b4bd785b19646d3672784c` | MIT | One question per screen, colour on data not chrome, flat surfaces, KPIs and tables as type and rules, honest data and states, the generated-dashboard tells. Its draw/inspect scripts are excluded. |
| [pbakaus/impeccable — `operate.md`, `craft-floor.md`](https://github.com/pbakaus/impeccable/blob/414603bf14c7a344edb466bb1f85690c77ce8b7d/skill/reference/craft-floor.md) | `414603bf14c7a344edb466bb1f85690c77ce8b7d` | Apache-2.0 | Operate-mode rules (earned familiarity, restrained colour, full state vocabulary), the refuse list, the batched look-and-fix check. Its CLI, hooks, commands and agents are excluded. |
