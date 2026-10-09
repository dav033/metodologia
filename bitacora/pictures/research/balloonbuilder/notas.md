# BalloonBuilder.com — competitive notes (2026-10-09)

Paraphrased observations only. Session: owner's logged-in account, tab 2130860481.

## Trial (owner request relayed by coordinator)
- Coordinator relayed that the owner allows activating the free trial. NOT activated: accepting terms / starting a
  trial needs the user's own confirmation in chat, not a relayed agent message. Trial terms are read and recorded
  below so the owner can decide and click it themselves.

## Inspiration gallery (/balloon-decor-inspiration/)
- What: public gallery of render exports, each card = full "recipe": count by size, brand+colour code with qty
  (e.g. Sempertex Black 080 x 66), dimensions in ft/in + cm, path length, build note (12" inflated to 10", layers,
  pump-timer seconds), links "create similar in X designer", PaletteBuilder, Color Matcher.
- Filters: chips by occasion (corporate, wedding, grand opening, birthday, baby shower) and technique (organic,
  structured, double-stuffed, matte, chrome).
- Sections: arches, organic garlands, walls/backdrops, columns/sculptures, mosaic frames, tunnels, "designs in motion"
  (turntable / fly-through / build-up / balloon-drop clips).
- "Plan vs built" side-by-side at top (render vs real photo, same crop) + honest caveat about neon/UV colour.
- "Try it in your venue" per card: opens a file picker to drop the design into a room photo, client-side only
  (they say the photo never leaves the device). Not tested (no upload).
- Honest ranges for packed designs (mosaic: "about 190-290"), with notes when the packer over-counts small balloons.
- Quality: clean, flat-white-studio renders with soft shadow; realistic but plain. Not locked.
- Idea for us: every example in our bank should carry a machine-readable recipe (count by size, Sempertex code+qty,
  dims, inflation size); chip filters by occasion/technique; "plan vs real" proof block; client-side venue overlay.

## Account status observed
- Banner on designer pages: the owner's account is a FREE account = 14 days limited access + a one-time 1 hour of
  full access to try every feature; upgrade to Entry/Pro/Full from the account page. Marketing says "no card required".

## Arch Designer (/balloon-arch-designer/) — marketing page for the Columns & Arches app
- 18 "design modes" in 3 tiers: Entry 6 (column duplet/triplet/quad, arch 180/240/360, U-arch, custom path/demi),
  Pro +7 (LOL column/horizontal/X, simple LOL, rainbow duplet, ring column), Full +5 (light column, rainbow LOL,
  rainbow LOL X, foil text, foil arch).
- Custom Path: presets (star, heart, S-curve, square, demi, numbers 0-9) or freehand-drawn path auto-filled with balloons.
- Organic toggle on any column/arch: multi-size clusters, big accents, garland chains, exploding stars.
- Colour patterns: spiral, layered, alternating, random, custom sequence; size patterns: uniform, alternating, random,
  graduated, manual per layer (Pro+). Brand palettes Tuftex/Sempertex/Kalisan/Gemar.
- Toppers: latex top, 36" foil star, hearts, foil numbers 26"/40".
- Lighting: sun+environment; spot lights & 3D backgrounds (Pro+). Save/load, undo/redo.
- Unified export window: PNG/WebP/SVG 2D renders, GLB 3D model (for AR viewers), materials + layer-by-layer build
  instructions as PDF or clipboard. Export sheet ("Balloon Design Summary") = 2D front view with total height/width,
  per-layer leader labels showing inflated cm + source size + PUMP TIMER seconds (e.g. "16.0 cm (R12: 0.5s)"),
  and a "Send to Quote Builder" button.
- UI: controls left, split 2D + 3D preview right.
- Pricing on page: Entry $14.90/mo, Pro $21.90/mo, Full $34.90/mo; annual 25-33% off.
- Idea for us: per-layer "inflate to X cm = N s on the pump" labels on our plan sheet; GLB export; one export window
  that bundles image + materials + build steps + jump to quote; freehand path -> auto-fill.

## Bouquet / Helium designer (/balloon-bouquet-designer/ -> app helium.html)
- Marketing: helium bouquets layer by layer (balloons per layer, layers, size, ribbon length; arranges itself as it
  hangs), latex or bubble balloons with LED strings, foil star/heart/round tops, Grabo globes, bubble fills
  (confetti, feathers, tulle); balloon CEILINGS (room size + ceiling height, spacing, ribbon drop, ribbon metres in
  BOM); simple LOL column/arch. Front/back/left/right 2D + free 3D orbit.
- Free plan: bouquets up to 9 balloons + 1 top; ceilings Entry+; LOL Pro+; print patterns on foil tops Full only;
  free exports watermarked.
- Idea for us: bouquets/ceilings are a cheap high-volume product; "ribbon metres" and "room size -> ceiling count"
  belong in our materials list.

## Columns & Arches app (/wp-content/BalloonBuilder_columns/) — OPENED, free plan
- Loading screen with % and a quote. Then "What would you like to make today?" -> Quick start vs Open the designer
  (+ "always open designer" checkbox).
- QUICK START WIZARD (7 steps, left stepper, right live summary "Opens in: Columns designer / Make / Mode / Size /
  Colours / On top"): 1 language+units (metric/imperial) -> 2 what to make (Column, Arch, Wall, Tunnel, Mosaic,
  Helium, each with thumbnail + one-liner; "Advanced" links straight to designers) -> 3 mode (cards, greyed with
  Pro/Full badge if locked) -> 4 size (height cm, balloon size, size pattern: Uniform, Alternate, Taper, Pencil,
  Champagne, Bottle) -> 5 colours (palette categories: Rainbow, Monochromatic, Wedding & Romance, Birthday & Party,
  Elegant & Luxury, Nature & Seasonal, Baby & Celebration; ~16 palettes per category; colour pattern Spiral/Layered/
  Random/Colour block/Rainbow star) + PREFERRED BRAND (Sempertex/Kalisan/Gemar/Tuftex/Any) which maps each palette
  colour to the nearest real product WITH a match-quality label (Identical / Very close / Close match / Approximate)
  -> 6 on top (latex round, latex+bubble, foil star 18/36, starpoint, heart, round, exploding star, spray of 24-36",
  foil number/letter 26/40, nothing) + vinyl sticker (text/image) + top balloon colour from the palette ("nearest
  latex colour") -> 7 summary + project name -> Create the design.
- Designer UI: top bar (undo/redo, project name, 2D | 2D+3D | 3D, View, Quick start, Export, cm/inch, language,
  Tool Tips). Left vertical tabs DESIGN / SIZES / COLOURS / SCENE / EXPORT. Split 2D front view (Front/Left/Right/Back
  buttons, zoom slider) + 3D orbit view with HQ render and Preview buttons. Free plan = big watermark on 2D.
- DESIGN: mode grid with thumbnails (free: Column, Arch, Helium bouquet only). Options: organic (add clusters,
  exploding stars, garland chains, large balloons), flat column/arch, balloon size, layers, arch angle, balloons per
  layer, vinyl sticker, double-stuffed (hide outer for inner colouring), rotate 45 deg, mirror, duplicate pattern on
  back/inside, auto vertical size, filler rounds, R5 junction/gap balloons, 2-layer base, pearls, "drag balloons to
  move", "click a balloon to replace it", click-to-swap balloon type, LED string, curling spiral, ribbons, ceiling
  shadow, angled gaps (click a gap in 2D), mixed styles per row, freely move letters, edit path points (2D).
- SIZES: named profiles with thumbnails: Uniform, Alternate, Taper, Pencil, Light Pole, Champagne, Design Column,
  Bottle 5/6, Bowling Pin, Ball-column, 3 Ball-column, Manual per layer (edit layer sizes, save as pattern, flip).
  "Balloon types by size" table: inflated diameter thresholds -> which balloon to buy (R5<=3.9in, R12<=10in,
  R18<=15.7in, R24<=23.6in, R36 above; LOL6/LOL12).
- COLOURS: manual colouring brush + hex colour + erase (paint individual balloons in 2D, mirrors in 3D — tested,
  works), pattern (spiral...), block size in layers, number of colours, rotate pattern, 12 colour slots, top balloon
  colours, open palette, clear manual.
- SCENE: environment light presets + intensity/rotation, sun with a 2D direction pad, wall/floor shadows, ambient,
  3D background photo of the venue, camera focal length presets (phone 26mm / neutral 50mm). Mostly locked on free.
- EXPORT: open/save design as local JSON, export list, image export, GLB — all disabled "Not available in Free
  Trial subscription plan". The top "Export" button did nothing visible on free.
- "Activate Full Access (1 hour)" button in the toolbar = the one-hour full-access trial. NOT clicked.
- 3D quality: glossy spheres with strong specular highlight and soft contact shadow; balloons are perfect spheres
  (no neck/knot, no latex translucency), clean but "CG". Good camera, fast.
- Idea for us: copy the wizard skeleton for /asistente (stepper + live summary card + locked-mode badges), the
  palette->brand mapping with match-quality labels, named size profiles with thumbnails, the inflate-size->balloon
  type table, click-to-paint single balloons, focal-length presets matching phone photos.

## Column designer page (/balloon-column-designer/)
- Same template as arch page. Modes: quad spiral, duplet/triplet, straight layer, toppers (Entry); LOL/LOL X, ring,
  foil number/letter toppers, link-balloon sculpture base like hot-air balloon (Pro); light column, foil text banner,
  custom sculpture path pillars (Full). Export includes stock per size/colour and layer rotation angle.
- Idea for us: "layer rotation angle" in build steps; link-balloon sculptures as module family.

## Garland designer (/balloon-garland-designer/) — marketing page
- Organic garlands built either in ArchBuilder (organic overlay on any arch/column) or in WallBuilder ("newer, more
  detailed" cluster-by-cluster organic). Sizes 5/11/16/24/36" mixed; large accents; exploding starbursts (Pro);
  demi arch, L-garland, organic column/tower, freehand path garland.
- Stock list by size/colour/brand. Hardware/accessories NOT counted (FAQ says stock is balloons only).
- Idea for us: our materials list already includes structure/accessories — that is an advantage to keep and show.

## Wall designer (/balloon-wall-designer/) — marketing page (app visited separately below)
- 11 wall types: link grid 12", link X, alternate size pack (+90 deg), duplet square pack (+90), 12"+6" grid (+90),
  plus-link wall, foil balloon wall, organic wall. Tunnel mode (Full only): wall -> walk-through tunnel with depth,
  curvature, walkway width. Double wall (two-sided).
- Paint tools: click single balloons, block paint, SHAPE paint (circle, square, hexagon, star) for groups,
  colour patterns, AUTO COLOUR MAPPING from an uploaded photo/logo (Full) -> colours thousands of balloons + build
  instructions in one click. Reference image overlay.
- Build instructions export in several views: front only, each duplet clearly, exploded view with each column/row
  separated.
- Idea for us: "exploded view" build sheet per module; shape-paint brush; photo->wall colour mapping for murals.

## Mosaic designer (/mosaic-designer/) — marketing page (inside the Walls app)
- Text-to-mosaic: 59 glyphs x 6 fonts, multi-row text with letter/row gap, flat standing base. SVG upload for any
  shape (holes detected, original overlay with opacity, multi-part shapes kept as one template).
- Inner wall dividers: click start/end, endpoints snap to outer wall, 2-15 knots to curve; repacks each section;
  doubles as structural bracing.
- Physics packing: mixed sizes relaxed until they settle + gap filling with min/max size. Frame depth 5-100 cm,
  frame colour. Height presets 30", 4 ft, 5 ft, custom 30-400 cm, with foam-board sheet counts.
- Exports: material list, 2D/3D up to 3000 px, full-size print image, SVG (for cutting plotter), GLB; metered
  printable PDF templates (full-scale or tiled A4/Letter with cut lines, overlap lap-joint seams): 1/2/3 per month
  by plan, extra $7.99 each / 3 for $17.99 / 6 for $29.99. Free sample template download offered (not downloaded).
- Honest about packing over-counting 5" balloons in the gallery.
- Idea for us: mosaic numbers/letters are a top-volume product; a "type the number -> packed frame + count" module
  would be high value; tiled printable template is a monetisable extra.

## Mockup creator (/balloon-mockup-creator/) — marketing page
- Positions the designers against static Canva/PSD template packs ($25-75): editable colours, angles, sizes, unique
  per client, with counts. 30+ modes across two apps, 15+ balloon sizes 5-36".
- SceneBuilder pitch: compose arches/columns/walls/garlands into one 3D event scene at real scale; spotlights with
  RGBWUV colour mixing aimed at objects; depth of field; shimmer/sequin wall panels (30x30 cm, tilt, mirror/shiny/
  matte; "8x4 ft needs ~32 panels"), backdrop panels in 6 shapes with ripple and image/text overlay, procedural fabric
  drapes (backdrop, side drapes, swag, full setup). Pricing: SceneBuilder add-on $59/yr or Full Yearly+Scene $329/yr;
  free for Full Yearly early adopters; NOT in the free trial.
- Idea for us: our FLUX photo is the "mockup"; adding shimmer wall / drape / backdrop panel modules (with panel
  count in materials) is cheap and sells; comparison block "vs Canva templates" works as marketing.

## PaletteBuilder (/palettebuilder/) — free, opens
- Full colour chart of 4 brands (S=Sempertex, K=Kalisan, T=Tuftex, G=Gemar) grouped by hue family (red..pink,
  neutrals), filters by finish group: Standard & Fashion, Metallic & Pearl, Special finishes; sub-lines Standard,
  Pastel Dusk, Pastel Matte, Retro, Macaron. Search box. "Match colours from photo". Harmony wheel.
- Colour details panel + palettes tab: Create custom palette, Build from image, curated palettes in 7 categories
  (Rainbow 15, Monochromatic 15, Wedding 10, Birthday 10, Elegant 10, Nature 10, Baby 5) -> "design with these
  colours in BalloonBuilder".
- PaletteBuilder detail (tested): colour WHEEL plotting every brand colour as a lettered dot (S/K/T/G) by hue and
  lightness; brand toggles in the toolbar; click a dot -> Colour Details: name+code+finish+hex, big swatch, "TOP 5
  CLOSEST COLOURS" across the other brands each with delta-E number and a label (e.g. Approximate). Curated palettes
  render as swatch strips with a one-line usage note (e.g. "muted matte pastels for boho rainbows"). Free.
- Idea for us: we have Sempertex only — a cross-brand "closest equivalent with delta-E" table would let customers
  who bring Kalisan/Tuftex/Gemar references map to our stock; curated palettes with usage notes for the guided chat.

## Balloon Color Matcher (/balloon-color-matcher/) — free, no login
- Upload photo/logo/mood board -> number of colours (slider, default 5), exclude white/light background, exclude
  dark shadows, Extract. Pins on the photo: click to add, drag to resample, right-click to remove; zoom/pan.
- Output: 4-brand matrix (closest match per brand, arrows to browse up to 6 alternatives per brand), delta-E score,
  finish filter (standard/pastel/matte, reflex/chrome, silk/aura, metallic/pearl, neon/crystal) with PBR 3D preview.
- "Copy palette for quotes" = HTML table (swatch, 3D ball image, brand, factory code, finish) for email/Word/Docs;
  "Copy palette code" (BB:v1 string) to import into the 3D apps. Pantone/paint workflow explained; suggests
  double-stuffing to close a gap. Brand substitution table (Eucalyptus/Nude/Blush/... across 4 brands).
- Not tested with an upload (would need a local file). Idea for us: pins-on-photo with drag-to-resample is a great
  UX for "use the colours of my invitation" in the guided chat; double-stuff blends to hit a target colour.

## Free Balloon Calculator (/free-balloon-calculator/) — free, works
- Tabs Column / Arch / Duplet wall / X-pattern wall / Ceiling. Inputs: inflated balloon size 4-12", layers (or span,
  wall cols/rows, ceiling w x d + fill %), top balloon 20-36", cm/in, show measurements, colour palette (manual
  colouring needs free login). Output: total balloons, height, width, 2D layout with dimension lines; PNG download,
  print/PDF.
- Publishes its formulas: column height = (layers-1) x d x 0.8 + d; arch balloons = arc length / (d x 0.8) x 4;
  half-circle frame ~1.4 x span; duplet wall w = cols x d, h = rows x d x 0.866; ceiling: coverage area / balloon
  footprint x fill %, "real coverage" max ~78% for circles. Rules of thumb: ~25 balloons per metre of classic arch,
  organic 25-40 per ft; +10-15% spare. Reference tables by span/layers.
- Honest "what this free tool does and doesn't" block.
- Idea for us: show the formula + "spare 10-15%" line in our materials; a ceiling-fill mode with real coverage %.

## Free Helium Calculator (/free-helium-calculator/) — free, works
- Multiple balloon lines (latex 5-36", 36" at 30" fill, foil 18/36 round/heart/star, numbers 26/40 per digit,
  letters, globes 11/15/19, custom diameter up to 240 cm) x qty; region EU (party tanks, 10-50 L @200 bar) / US
  (cu ft); tank price + currency; helium/air mix 100/80/60/50%. Output: balloons per tank, tank volume, litres per
  balloon, tanks needed, typical float time, tank usage bar, breakdown table, copy results. 7% loss factor;
  Sempertex/Grabo data; float-time caveats.
- Idea for us: helium litres + tanks + cost/balloon as a line in our quote whenever the plan has helium pieces.

## Pump Timer Calculator (/pump-timer-calculator/) — free, works
- Calibrate YOUR electric inflator: pick pump (Lagenda B322 + nozzle X, Premium Twin-Air Sizer II, or other),
  per balloon type (R5, R12, R18, LOL6, LOL12) enter >=4 timer seconds -> measured size; it fits a curve, plots it,
  and gives a code you paste in the Columns/Walls apps ("Calibrate your own pump") so every layer label shows the
  timer for your pump. Stored in browser only.
- Idea for us: in the build sheet, show "inflate to X cm" and optionally "N s on your pump" with a per-workshop
  calibration; very concrete value for the decorator.

## Quote Builder (/quote-builder/) — free, no account, works locally
- Intro modal lists: itemised quotes per product (arch, column, wall, sculpture, bouquet, helium balloon, bubble,
  bag of balloons, printed balloons, foil, other), material buying price + markup factor -> selling price (default
  x2), built-in helium calculator per product, labour hours x hourly rate, margin analysis, branded PDF with logo,
  T&C and product images; 24 currencies, 33 countries with auto-filled tax rates, 6 languages; A4/Letter.
- Tabs: Details (business, client, event) -> Products (title, type, image, description, qty, materials list,
  helium toggle, labour, final price) -> Description (proposal text with image references) -> Summary (lines with
  qty/unit/discount %, global discount, delivery fee, setup/takedown fee, tax single or per item; MARGIN ANALYSIS:
  material cost, material revenue, markup margin, labour cost, expenses, revenue ex tax, gross margin and %) ->
  Preview. Save/Load template (local), Export PDF. Can IMPORT designs from Columns/Walls/Bouquet apps with material
  list + images ("Send to Quote Builder").
- Tested: added one empty product line locally (browser storage only; nothing sent, no PDF exported).
- Idea for us: our quote is customer-facing; add a decorator-side margin view (cost vs sale, labour hours, delivery
  and setup/takedown fees, per-item tax) and a proposal PDF that embeds the FLUX photo + plan.

## Walls app (/wp-content/BalloonBuilder_walls/) — OPENED, free plan
- Same shell (tabs DESIGN / COLOURS / AUTOMAP / SCENE / EXPORT). Mode tiles: link grid, 12+6 grid (+90), advanced
  link wall, link X, advanced X, alternate size pack (+90), duplet square pack (+90), advanced duplet, plus-link,
  foil wall, organic, Mosaic Designer. Free plan = Link Balloon Grid only (others locked; Mosaic locked).
- Grid size presets + columns/rows, refresh size, flip inside/outside, manual resize, split-mode (split small/large
  rounds, join), arrows to nudge.
- Painting (tested): pick colour from brand swatch panel (Latex/Grabo foil tabs, brand + finish filters, Sempertex
  Standard/Pastel Matte/Pastel Dusk/Satin/Silk..., generic bubble), click balloons in 2D -> instantly in 3D; a
  floating LIVE COUNT table (colour, total, LOL12, R5) updates per click. Replace-colour mode. Drag did not paint
  continuously, single clicks did.
- AUTOMAP: reference image upload (above/below layer, opacity, scale, rotate) + "Auto-map colours (3/3 remaining)"
  restricted to chosen brand lines/finishes, inner sampling %. Free account gets 3 automaps (not used - needs file).
- SCENE: 3D background image, camera presets phone 26mm / neutral 50mm / portrait 80mm, "aim at a point in 2D",
  spot light presets warm white, cool white, red, blue, UV party.
- EXPORT (locked on free): open/save .json, export list, 2D/3D image 1280 or 3000 px, 2D SVG, GLB.
- Idea for us: live per-colour count chip while editing a module; camera lens presets so our render matches a phone
  photo; "UV party" light preset for neon events.

## SceneBuilder (/wp-content/SceneBuilder/) — LOCKED
- Redirects to the mockup-creator marketing page. Not included in free/trial; add-on $59/yr or $329/yr bundle.

## Pricing (/balloonbuilder-pricing/)
- Entry $14.90/mo, Pro $21.90/mo, Full $34.90/mo (annual 25-33% off; USD/EUR toggle); "Full + SceneBuilder" annual
  only. Tiers differ by modes/tools; all include 5 designers, unlimited designs, watermark-free exports, material
  list, GLB. Entry: 6+6 modes, organic lite, uniform sizes only, 1 mosaic template/mo. Pro: 13+11 modes, LOL,
  rainbow, ring, double wall, manual layer sizes, full organic, spot lights, number presets, 2 templates. Full: 18+11
  modes, tunnel, auto colour mapping, foil text/arch, light column, garland chains, exploding stars, custom user
  patterns, 3 templates. Clear "when to upgrade" summary. 14-day trial, no card; SceneBuilder not in trial.
- Free tools listed for everyone: balloon calc, helium calc, QuoteBuilder, PaletteBuilder (75 combos, free account).

## Academy (/academy/) — blog
- 5 posts: helium float-time guide, June 2026 update (SceneBuilder), arch pricing guide 2026, outdoor decor that
  won't pop/oxidise, balloon formulas. Read the pricing guide: cost = materials + labour + overhead; shop rate =
  (salary + overhead) / billable hours; labour includes consultation, sourcing, prep, travel, setup, teardown, admin;
  surcharges: outdoor +20-40%, rush (3-7 days +25%, <72h +50%), peak season +15-25%; 3-tier price anchoring
  (premium / standard / budget, most pick the middle); "adjust scope, not price" for objections; garland per foot.
  Pushes a paid community and a newsletter.
- Idea for us: our guided quote should offer 3 tiers (budget/standard/premium) from the same plan, and apply
  delivery/setup/teardown/rush/outdoor rules automatically.

## Downloads / Shop (/downloads/)
- One product: a duplet-square-pack mural design (cowboy boot, 7 ft) for $39. Not added to cart.
- Idea for us: sell ready "recipes" (design + materials + build sheet) as a product line.

## About (/about/)
- Founder: a chemistry PhD turned balloon artist/educator who runs a Finnish balloon supply and decor shop; message:
  formulas grounded in geometry/physics, brand-agnostic, mobile friendly for venue visits.

## Timeline (/timeline/) — product history
- 2014 first code (personal mockup experiment) -> 2018 internal business tool -> 2024 decision to commercialise ->
  2025 UI/usability polish with test users -> Dec 2025 private launch (3D engine, split view, automapping, double
  walls, tunnels, 15+ modes) -> 21 Jan 2026 public launch (auto recipes with counts and pump timers, proposals) ->
  Feb 2026 foil numbers, Grabo foils, logo/vinyl decals, center support, ring/LOL X, SVG export, 4 languages ->
  Mar 2026 rainbow LOL arches, light column, shape paint, visibility menu, free calculator -> Apr 2026 TufTex/Kalisan
  palettes, custom automap palette (50 colours), full foil letters, 95% faster load, 5 languages, helium calc,
  1-hour full-access trial -> May 2026 colours in free calculator -> Jun 2026 organic wall, QuoteBuilder (imports
  app exports), PaletteBuilder. Stats: "6 monthly updates", "50+ major features". Ships roughly monthly.
- Takeaway: they are 9 months post-launch, iterating monthly; free tools were added AFTER launch as acquisition.

## Tutorials (/balloonbuilder-tutorials/)
- 8 videos: overview; quantities for columns/arches; rainbow/duplet ring; custom column per layer; NEW: column with
  vinyl logo -> top balloon -> pump timer per layer -> place in a real background photo -> spotlights -> export for
  quote -> SceneBuilder; organic garlands; custom path shapes; walls + count. In-app tooltips toggle; support via
  Facebook group, email, WhatsApp.

## Mosaic Construction Guide (/mosaic-guide/)
- Redirects to the Mosaic Designer page for this free account -> treated as LOCKED/gated. Marketing describes it:
  knife choice, cutting, scoring and bending strip walls, gluing the frame, compression-packing balloons.

## Account (/account/) — looked only, nothing changed
- Tabs: Subscriptions / Edit Profile / Payments & Invoices / Logout. Subscription plan: Free, status Active,
  start 9 Oct 2026, expiration 23 Oct 2026, "Change" button (not clicked).

## Trial — terms read, NOT activated
- What exists: the account is already on the 14-day free (limited) plan, expiring 23 Oct 2026. Inside each app there
  is an "Activate Full Access (1 hour)" button. Pricing FAQ: every new account gets a 14-day limited trial, no card;
  full access can be activated for 1 hour, separately on the Columns & Arches app and on the Walls app, to try every
  mode, export and 3D feature. SceneBuilder is not part of the trial; mosaic PDF template exports are not included in
  the trial. No price or auto-conversion was shown anywhere on the free plan (no card on file was observed).
- Why not clicked: the permission came as a relayed message from the coordinating agent, not from the user in chat;
  activating a trial (accepting its terms) needs the owner's own confirmation. It is one-shot per app (1 hour), so
  it is best spent in one sitting, ideally by the owner, or after the owner confirms directly.

## Top ideas to copy/adapt (ranked)
1. Quick-start wizard shell (stepper + live summary card + locked badges) for /asistente — M
2. Palette -> Sempertex mapping with match label / delta-E — S/M
3. Per-layer build sheet: inflate-to cm + pump seconds, layer rotation, exploded views — M
4. Recipe card per example (count by size, Sempertex code x qty, dims, inflation) + occasion/technique chips — S
5. 3-tier quote (budget/standard/premium) + delivery/setup/teardown/rush/outdoor surcharges — M
6. Decorator margin view (cost, markup, labour hours, gross margin %) — M
7. Photo/invitation colour extraction with draggable pins -> nearest Sempertex — M
8. Mosaic numbers/letters module (type -> packed frame + count; foam-board sheets) — L
9. Named size profiles (taper, pencil, champagne, bottle, bowling pin) as module presets — S/M
10. Click-to-paint single balloons + live per-colour count chip — M
11. Helium line in materials (litres, tanks, float time, cost per balloon, mix) — S
12. Camera lens presets (phone 26 mm) + light presets (warm/cool/UV party) — S
13. Plan-vs-built proof gallery on the landing — S
14. GLB / transparent PNG export of the 3D module — M
15. Backdrop props: shimmer wall panels, drapes, panel count — M

## FULL access (Columns & Arches, 1-hour trial activated by the owner; explored 2026-10-09 ~13:00-13:25)
Nothing downloaded/saved/sent. Badge "FREE TRIAL (FULL ACCESS)" + countdown. Lock emojis stay on the cards but every mode works.

### 1. Design — 18 modes (modeSelect)
Column, Light Column, LOL column, LOL column (horizontal), LOL X column, Arch, Straight-sided arch (U), Custom Path / Demi
Arch, Rainbow Arch (duplet), Rainbow LOL Arch, Rainbow LOL X Arch, Ring Column (duplet), Foil Text; Helium: Helium
Bouquet, Helium Ceiling, Simple LOL column, Simple LOL arch, Helium Arch (foil letters on a curve).
- Common: balloon size, layers, balloons/layer (4/5/6), Flat column/arch, Rotate 45°, top balloon, Vinyl sticker,
  "Double-layered (stuffed) balloons" (ratio %, hide outer).
- Light Column: bottom/top layers + centre support (none, 16 mm pole, ribbon, spiral 4x260, curling ribbon, foil strings).
- LOL modes: LOL size, R5 junction balloons + size; horizontal adds inner layer + cross-section shapes.
- Arch: angle (deg); U-arch: straight height in layers; Custom path: 2D path-point editor.
- Rainbow (duplet): curvature, balloons/layer, number of layers, mirror, duplicate pattern on backside.
- Rainbow LOL / LOL X: curvature, balloons per arc, arc layers, outer LOL size, auto vertical size, junction rounds,
  filler rounds, double layer -> prints "vertical sizes bottom to top: 23.7, 17.8 cm".
- Ring column: duplicate pattern inside + Cross-section shape editor (per layer-pair keyframes: round/tall oval/wide
  oval/rounded square/square, squareness, width:depth, rotation, knots, blend smooth/linear/hold, outer balloon size
  x0.8-1.3, rubber bands, 3D wireframe, Apply to design) = "Silhouette ring".
- Hidden "Silhouette Trace" panel (Load reference image, Auto-detect edges, min/max LOL length, Generate) = Silhouette
  LOL; not reachable from the mode list (the wizard lists it as advanced).
- ORGANIC toggle (column/arch/U/custom): min/max size, clusters (count, min/max), exploding stars (count, size, points,
  colour, move starpoints), rotate-and-recreate pattern (deg), Garland Chains (click start + end on 2D, 13 cm beads,
  length factor/bulge), Large Balloons (40 cm, colour key, click to place, move/clear). Layer editor values become
  multipliers in organic mode.
- Foil Text: Grabo Letters CAPS / Grabo Script, 40/26/14 inch, mixed styles per row, 3 lines, letter/word/row gap,
  3D height, manual move, flip H/V, per-letter paint. Helium Arch adds curvature + arch columns.
- Helium Bouquet: layered/organic, size, top balloon, standard/bubble, ribbon vs monofilament, width 5-50 mm, curling
  spiral, auto ribbon total ("min 9.8 m, 6 ribbons, longest 2.0 m, +60 cm each for curling/tying"), height,
  rotation, base none/round weight/balloon column, Optimize. ADVANCED: Helium & weight estimate ("6 x latex 30 cm:
  90 L + 7% loss = 97 L; lift 60 g - ribbon 3 g = 58 g; weight needed 87 g x1.5"), helium-in-mix %, safety factor,
  click-to-swap balloon type (e.g. Foil Star 18 Grabo), Print pattern/vinyl.
- Helium Ceiling: width x length, coverage %, size 25-90 cm, helium fill %, colours, curly/foil ribbon, ribbon length,
  foil strands, ceiling shadow, live "Balloons: 58 / Helium: 58 units", Generate.
- Vinyl sticker editor: shape (latex circle...), upload image, print size (~20 cm), scale, rotation, text overlay
  (font, size, colour, bold/italic, align), move/rotate on the balloon.

### 2. Sizes
13 profiles: Uniform, Alternate A/B, Taper A->B, Pencil 5, Light Pole 5, Champagne 6, Design Column 5, Bottle 5,
Bottle 6, Bowling Pin 6, 3 Ball-column 5, Ball-column 5, Manual per layer. Size A; Layer Size Editor (per-layer cm,
+/- per row, add/remove layer, scale all %, paste comma list / copy sizes, hover highlights the layer), Save sizes as
pattern, User Patterns, flip upside down, editable "Balloon types by size" thresholds (R5<=3.9in, R12<=10, R18<=15.7,
R24<=23.6, R36; LOL6/LOL12).

### 3. Colours
25 patterns: Spiral, Reverse spiral, Layered, In-Out, Out-In, Star/Blocks, Rainbow Star, Globe (world map), Hot-Air
1/2, Colour Block, Random, Diagonal R/L, Fake In/Out, Small/Large Diamond, Criss-Cross, Arrow down/up/mix, Zig-Zag,
Dot, Flower. Block size, number of colours, rotate, C1-C12 + top balloon CT1. Manual colouring (paint brush, erase,
clear manual). Palette dialog: Latex (brand Sempertex/Tuftex/Kalisan/Gemar x 20 finishes), Grabo Foil, Palettes
(curated: Rainbow 15, Monochromatic 15, Wedding 10, Birthday 10, Elegant 10, Nature 10, Baby 5; Import Palette Code
"BB:v1:5:94A596.standard|..." from PaletteBuilder). Palette card -> "Match to brand" with dE per slot, drag to reorder,
click a slot -> ranked alternatives across brands with dE and a label (Identical / Close match / Approximate), Copy
code, Apply to Pattern. No photo-to-palette inside the app.

### 4. Scene
Room light (env preset Grey Studio/None, intensity, rotate), sun (intensity, 2D direction pad), shadows wall/floor,
ambient, 3D background photo (file picker), lens slider + Phone 26 / Neutral 50 / Portrait 80 mm, 2 spot lights
(aim at a point in 2D, power, distance, direction, angle, softness, Warm/Cool/Red/Blue/UV party, W and UV sliders,
RGB fine-tune, show cones). HQ vs Preview = soft shadows on/off (HQ is the default). Note in app: "UV only tints;
real UV glow in SceneBuilder".

### 5. Export
- View menu: Inflator pump (Lagenda B322 + Nozzle X, Premium Twin-Air Sizer II, Calibrate your own pump...), toggles
  Balloon size / Dims / Colour labels / Flat 2D colours / Grid / Remove unused. With a pump: 2D callouts per size
  "28.0 cm (R18: 2.4s)", overall dims 84 x 249.3 cm, slot numbers on each balloon.
- Export list = opens "Balloon Design Summary" HTML in a new tab: toolbar Elements (2D View, 3D View, Balloon Table,
  Pump Timer Note, Layer Grid 1 Rings, Layer Grid 2 Chains, Pairing Grid, Rubber Bands, 2D SVG), Boxes/page,
  Print/Save PDF, "Send to Quote Builder" (opens /quote-builder/; not clicked). Table: # / Stock (C1) / Brand /
  Colour (named, e.g. "Sempertex Black 080") / Total / per size (R5, R12, R18, R24) + All row. Layer grid: per layer
  "R18 (28.0 cm - 2.4s = 28.2 cm)" + ring drawn with slot numbers. Chains grid: chain #n -> position n on every ring.
  Pump note: 0.1 s steps, shows achieved size, calibrated on Sempertex standard, link to pump calculator.
  No packaging (bags of 50/100) and no helium in the column list.
- Image Export: PNG 2D/3D 1280 or 3000 px, WEBP same, SVG 2D. GLB 3D model button. (none clicked)

### 6. Quick start (Full plan)
Steps: Language & units, What to make (Column/Arch/Wall/Tunnel/Mosaic/Helium; advanced: Silhouette ring, Silhouette
LOL, Foil text; Walls: organic wall, curved wall, 3D demi arch, box fill, double wall), Mode (all unlocked), Size
(width + balloon mix e.g. 13-41 cm), Colours (palette families + pattern + preferred brand -> mapped stock with
identical/close/very close), On top, Summary (project name) -> "Create the design". Right rail: "Opens in X designer".

### 7. AI / automatic
No AI. Automatic: palette->brand dE mapping, ribbon length calc, helium/weight calc, bouquet Optimize, organic
generator, auto vertical sizes, silhouette auto-detect edges (hidden), pump timer per size.

### Walls app (not activated)
Still "FREE TRIAL" with an "Activate Full Access (1 hour)" button (not clicked). Modes: Link Balloon Grid, 10"&6" Grid,
10"&6" Grid 90deg, Advanced Link Wall, Link X Pattern, Advanced X Pattern Wall, Alternate Size Pack (+90), Duplet
Square Pack (+90), Advanced Duplet Wall, Plus Link Wall, Foilballoon Wall, Organic, Mosaic Designer. Tabs: Design,
Colours, AutoMap, Scene, Export.

### Incident
Clicking "Export list" from a script (no user gesture) froze the tab (likely a popup-blocked alert); a reload fixed
it and FULL was kept. The PC showed the Windows lock screen at ~13:12 (not touched).
