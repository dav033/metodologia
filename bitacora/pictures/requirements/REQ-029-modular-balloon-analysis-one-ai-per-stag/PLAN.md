---
req: REQ-029
status: in-progress
created: 2026-11-11
---
# Plan — REQ-029 — Modular balloon analysis: one AI per stage, exact rings for classic columns and arches, assisted training

## Approach
Prove the method in a lab lane first (`~/dev/pictures-infra/conteo/lab/bi-modular`), port it once to the application as one
feature with a pure geometry module, use it first where it helps the training (proposals in Entrenamiento), then in the
Contador behind a flag and an exactness gate. Direct mode in one session (owner's `/goal`: no interview, no permission questions);
rulings recorded below and in D-110. Alternatives rejected: more training of the ring-density network (measured: no gain with
19 real pieces), length / balloon-size formulas (±1 by construction), a larger vision model (owner rule: gemini-3.6-flash only).

## Global constraints
- Only `gemini-3.6-flash`. No sealed or test split opened. No frozen data copies in the repository.
- A read is shown as exact only by consensus; everything else is a proposal. The statistical count stays the fallback.
- One owner of the ring geometry: `src/features/balloon-analysis/domain/linear-structure.ts`.

## Tasks
- [x] T1 — Lab: stage 1 (structures), stage 2 (marks with part), geometry (levels along the axis), consensus; numbers on the 20 labelled real pieces · verify: `python remedir.py` in the lane · covers: US-1, US-2
- [x] T2 — Lab: synthetic columns with known rings (60 images, 84 pieces), tiles for long pieces, review pass dropped · covers: US-2
- [x] T3 — Lab: recogniser on 247 pooled real photos; classic arches with a declared total; 12 arches labelled the same afternoon (unseen) · covers: US-1, US-2
- [x] T4 — App: feature `balloon-analysis` (domain, application, infrastructure), parity with the lab on 93 stored views · verify: `npm run analisis-globos:test` · covers: R1–R6
- [x] T5 — App: `POST /api/entrenamiento/anillos/propuesta`, editor filled from the proposal, add/remove a ring by tapping, proposal stored (migration 062), ring-click fix from `feat/entrenamiento-anillos` · covers: US-3, R7
- [x] T6 — App: Contador exact path for photos made only of classic pieces read as exact (`CONTADOR_ANALISIS_MODULAR=1`) · covers: US-4
- [x] T7 — Publish: main `8ee1caefc`, Vercel production with the flag, local 3010 updated; decision record 0010; D-110
- [ ] T8 — Check in production with a real session (P-319)
- [ ] T9 — Arches on photos of normal size: label, measure, improve the arch read (P-320)
- [ ] T10 — Loose balloons and the other structure modules (P-321); proposal-vs-final measurement in the section (P-322)

## Verification
Lab: `remedir.py` (20 real 19 exact, 14 called exact, 0 wrong; synthetic 83/84, 70 called exact, 0 wrong; arches 3–6/12, none
called exact). App: `npm run analisis-globos:test` (34 tests), `probar_api.py` against a local server (19/20, 13 exact, 0 wrong),
Contador on local 3010 (33, 41, 98 exact on labelled photos). Not verified: production with a session.

## Rulings
- "Geometric structures" taken as classic columns and arches of stacked clusters; walls later — cost if wrong: low (modules are additive).
- 4 balloons per ring assumed; the collar under a topper is not a ring; aligned columns always for review — cost if wrong: med (shown as assumption; a person can change 4/5 in the editor).
- Contador exact path switched on in production on the evidence of 97 exact calls with none wrong — cost if wrong: med (a wrong exact total on a customer photo; switch off with one env var).
- Migration 062 applied alone with its ledger row; 061 (WhatsApp) left for its owner — cost if wrong: low.
- Median of the views as the proposal when no two views agree — cost if wrong: low (always shown for review).

## Progress log
- 2026-11-11 19:30–20:10 lab: marks without tags 8/19; with part tags and end trimming 16/20; curved axis 18/20; three views 18/20, 16 exact all right.
- 2026-11-11 20:10–21:00 lab: synthetic 59/84 → tiles 75/84 → tile size from crop width and no review pass 83/84; real 19/20.
- 2026-11-11 21:00–22:10 app: feature, endpoint, editor; parity 93/93; 12 new arches exported and measured (weak on thumbnails).
- 2026-11-11 22:10–23:10 app: Contador path, publish, flag, 3010; documentation.
