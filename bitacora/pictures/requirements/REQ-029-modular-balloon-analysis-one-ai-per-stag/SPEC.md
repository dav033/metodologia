---
id: REQ-029
status: in-progress
created: 2026-11-11
track: standard
---
# REQ-029 — Modular balloon analysis: one AI per stage, exact rings for classic columns and arches, assisted training

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The Contador answers every photo with one statistical blend (detector + CountGD + CountGD++ x thickness, ±30 %). For geometric
structures (classic columns and arches) the total follows from the construction (rings x balloons per ring), and the owner
expects EXACT values there. On 2026-11-11 a ring-density network and length/size formulas were tried on the 20 labelled real
pieces of Entrenamiento › Conteo de anillos: best 9/19 exact with the person's clicks, 7/19 without. They measure lengths;
nobody counts the rings one by one.

Owner's directive (session 1b10587f, 2026-11-11 19:30, `/goal`): find the best way to raise the reliability of balloon
detection; modularise the analysis so each structure has its own way of extracting its balloons; split the work between AIs
(one recognises every structure, one goes structure by structure and extracts the balloons of the body, one takes the loose
balloons, and so on); design a training that is as easy, fast and reliable as possible for tomorrow; priority: 100 % on
geometric structures, simple arches and columns.

**Success looks like:** on the labelled real pieces (and on every later labelled piece), classic columns and arches read by
the modular analyser give the exact ring count; a read the analyser calls exact is never wrong; reads it cannot guarantee
are shown as a proposal to confirm with one tap. The training section proposes the marks so a person only confirms or
corrects, and every confirmation is measured against the proposal.

## Users / actors / stakeholders
- Sempertex/Pictures staff who label examples in Entrenamiento (tomorrow's session) and users of the Contador.
- Owner (David): wants exact values for geometric structures, no permission questions (memory `pictures-sin-pedir-permiso`).

## Scope (in)
### US-1 (P1, Must) — Structures first
As a user, the photo is split into its structures (classic column, classic arch, organic garland, wall, figure, bouquet,
loose balloons, other), each with its box, before anything is counted.
**Acceptance:** type and separation correct on the labelled photos (pairs of columns are two structures).
### US-2 (P1, Must) — Each classic column/arch read by its own module
As a user, each classic column or arch is cropped, its balloons are marked one by one (body / topper / long / other) and the
rings come from geometry: levels along the axis, an integer.
**Acceptance:** exact rings on the labelled real pieces; exact on synthetic columns with known rings; a read flagged exact
is never wrong on those sets; mixed-size bodies, collars and aligned columns are reported as such.
### US-3 (P1, Must) — Assisted training
As a labeller, I upload a photo, the system proposes pieces and one point per ring, and I only confirm or correct.
**Acceptance:** proposal appears in the existing ring editor; the saved example keeps both the proposal and the final marks;
an accuracy summary per module can be computed from the saved examples.
### US-4 (P2, Should) — Exact path in the Contador
When every structure of a photo is a classic piece read as exact, the Contador returns rings x balloons per ring (plus toppers
and loose balloons) instead of the statistical blend; otherwise the current count stays, unchanged.
### US-5 (P3, Could) — Loose balloons and non-classic structures as modules
Loose balloons through the existing marking tool restricted to what is outside the structures; organic garlands, walls and
figures keep the statistical count until their own module exists.

## Out of scope
- Replacing the statistical blend for organic structures. Per-balloon colours and sizes. Training or replacing the detector.
- Any model other than `gemini-3.6-flash` for vision (owner rule, 2026-11-10).

## Requirements
- R1. Stage 1 returns structures `{tipo, box_2d, completa, remate}`; it never counts.
- R2. Stage 2 marks every visible balloon of ONE structure crop with `parte` in cuerpo | remate | largo | otro.
- R3. The linear module returns rings, sub-type (espiral | alineada | mixta), collar and toppers, and its own checks
  (comb residual, empty levels, margin to the next N, agreement between gap read and comb read).
- R4. A read is exact only when independent views of the same crop (plain, mirrored, zoomed) agree and the checks pass.
- R5. Balloons per ring defaults to 4 and is stated as an assumption (frontal photos cannot tell 4 from 5).
- R6. Provider answers are validated at runtime; every stage has a deadline; failures fall back to today's count.
- R7. The training section stores proposal and final marks; no frozen data copies in the repository.

## UI / design contract
Entrenamiento › Conteo de anillos keeps its editor; it gains «Proponer con IA» and a state per piece (exacta / revisar).
Components from `@bitacora/ui`; sober UI (memory `pictures-ui-sobria`).

## Edge cases & errors
- Toppers made of many things (sprays of long balloons with round tips, bubbles with balloons inside, character arms).
- Collar of small balloons under the topper: reported, not counted as a ring of the body.
- Aligned columns (large clusters stacked without nesting): a hidden small spacer ring per visible ring; always «revisar».
- Bodies with two balloon sizes; structures cut by the photo border (`completa: false`): never exact.
- Tiny photos (the labelled set is 220–447 px wide): crops are upscaled before marking.

## Constraints
- Web tier owns the Gemini calls today (`marcar-globos.ts` precedent: the Python ai-api on advin is behind main and must not
  be restarted without notice); the geometry gets ONE owner.
- Lab lane: `~/dev/pictures-infra/conteo/lab/bi-modular/` (outside the repo). No sealed/test split is opened.

## Priorities & phases
- M1 Lab proof: pipeline + numbers on the 20 real pieces, synthetic columns, extra real photos.
- M2 Application: analyser module + API, proposal in Entrenamiento, storage of proposals.
- M3 Contador exact path for classic pieces (behind the exact gate), deploy, report.

## Assumptions (made without asking, per the owner's standing instruction)
- "Estructuras geométricas" = classic columns and arches built from stacked clusters; walls come later.
- The labellers' convention is the truth: rings of the body, 4 per ring; the small collar under a topper is not a ring.
- A read that is not exact is shown for confirmation instead of being hidden; 100 % refers to what is shown as exact.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| UI / design direction | Covered (existing editor) |
| Priorities & phases | Covered |
| Timeline | Tonight for M1–M2; M3 as far as evidence allows |

## Clarifications
No interview round: the owner asked for autonomous work with no permission questions (`/goal`, 2026-11-11).
