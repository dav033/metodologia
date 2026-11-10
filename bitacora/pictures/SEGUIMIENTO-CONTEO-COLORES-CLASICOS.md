# Follow-up prompt: Contador colours, sizes and exact classic structures (after session 75f37b30, 2026-11-10)

Paste into a new session started in `~/dev/pictures-wt/pilot`:

---

Continue the Contador investigation of Pictures (REQ-026). Talk to me in Spanish. Work independently and with subagents; do not follow the full methodology ceremony. Nothing was changed in any repository or in production: everything so far is read-only analysis plus offline prototypes.

## Priority 1 (owner, 2026-11-10): classic columns and arches must be exact
They are arithmetic: rings × balloons per cluster + toppers + base. Today `src/lib/contador/formulas-estructura.ts` (main) ESTIMATES rings from height ÷ diameter (pitch 0.8 d) and rounds, always 4 per cluster, and only when the person picks the structure; in automatic mode the statistical model answers (production classic arch: 144, real 116 = 29 × 4).
- A subagent was prototyping ring COUNTING (centreline, layers along it, gate that abstains on non-classic photos) in `~/dev/pictures-infra/conteo/lab/at-color-tamano/clasicos/`. It may have died with the quota: read `clasicos/REPORTE.md` if it exists, otherwise the scripts there, and relaunch with the same brief (goal: share of photos with the exact total on 3D val classic renders and on real classic photos; overlays in `clasicos/overlays/`).
- Real classic photos (sha prefix, in `at-color-tamano/real/fotos/`): `3851fcd6` arch, truth 116; `06580b7e` two striped columns with toppers (system 51, by eye about 7 rings × 4 + 1 each); `f0d5491a` column (system 43, about 11 rings); `39cb3d64` two spiral columns with topper, collar and base (system 123).
- Expected product design: show the sum («29 racimos × 4 = 116») with rings and cluster size editable, because 4 vs 5 per cluster is not always visible from the front.

## Priority 2: colours and sizes (the users' actual complaint)
Measured on production (34 uploads, 17 photos, 6 accounts, 11 corrections, 5 genuine with system colours):
- Exact Sempertex code right in 23 of 27 corrected colours, but 235 of 688 balloons (34 %) under the wrong colour; misses are neighbours (Pastel Dusk Crema → Fashion Blanco, Amarillo Miel → Amarillo with the right code as second candidate, Reflex Dorado / Dorado Rosa split 28/28 vs 35/40). The correction form is prefilled with the system's numbers, so the real error is probably higher.
- The same photo gives different colours and size splits on every attempt; sizes are four vague classes, not inches; no colour × size table; corrections do not store sizes (no size truth at all).
- Cause: `services/ai-api/app/contador_foto.py` asks Gemini for global proportions of colours and of size classes in two independent reads and splits the total by them. The detector already gives one box per visible balloon.
- Two subagents were prototyping per-box colour (`at-color-tamano/color/`, scored on the corrections against production's 34 %) and per-box size in inches (`at-color-tamano/tamano/`, scored on val renders). Read their `REPORTE.md` and overlays if they exist; otherwise relaunch.
- Proposal pending the prototypes: colours and sizes counted per box (deterministic), Gemini only names each colour group, one-tap colour confirmation with top-3 Sempertex candidates, corrections that also store sizes and are not prefilled, cache by photo hash, warning for photos under 480 px (7 of the first 15 photos were).

## Prepared data (`~/dev/pictures-infra/conteo/lab/at-color-tamano/real/`)
`fotos/<sha256>.<ext>` (18 production photos), `cajas.json` (detector t2 boxes, raw and final), `correcciones.json`, `sistema.json` (every production answer), `detectar.py`.
Production DB read-only: `PICTURES_DB_APP_URL` in `~/.config/metodologia/pictures-db.env` (tables `contador_subidas`, `contador_correcciones`); photos in the object store (`~/.config/metodologia/pictures-almacen.env`, prefixes `contador-subidas/`, `contador-correcciones/`). Never print the secrets.

## Other facts
- The total of the same photo moved today (96 → 116, 294 → 301): at 15:21 UTC another session deployed VPS image `pictures-conteo:4` (CountGD++ on, commit 2fac7d707, about 17 s per photo). Coordinate with it before touching the VPS service.
- Totals on the genuine corrections: −9 %, 0 %, −5 %, −15 %, 0 %, +24 %.
- Day log: `~/bitacora/dev/2026-11/W3/2026-11-10.md`, session `75f37b30`. Earlier count hand-off: `~/bitacora/pictures/SEGUIMIENTO-CONTEO.md`.

---
