# REQ-001 — Plan

Each step: implement → tests → verify in `e3-verif` (tsc + tests) → push to main → day log.

1. **Organic stroke** (`trazo-organico.ts`): wall-plane path with per-point thickness → `OpcionesOrganico`; piece
   `organico` carries its parameters (`trazo`) so it re-builds and is editable; AI tool `trazo_organico`
   (points in cm or named silhouettes: swag, arc, corner, half-arch-left/right, asymmetric-arch, L).
2. **Column types**: `tipoColumna: irregular | libre` on organic columns; freeform = stacked clusters with
   offsets and bulges; solo-editor chips (Clásica · Irregular · Forma libre); AI by name.
3. **Foliage** in the flower system (monstera, palm, fern, eucalyptus, dried gold leaf) + viewer meshes.
4. **Cluster decoration** (R-5 grapes, collar) and **orbz + fringe**.
5. **Backdrop catalog** (round, half moon, chiara set, pedestal set, curtain with lights, sign board).
6. **Digitize the 13 photos** as Library sets with fidelity notes.
7. **Photo reading**: schema + Gemini vision prompt (`lectura-foto.ts`, route `/api/escena-foto`), compiler
   reading → scene (`compilar-lectura.ts`), tests with hand-written readings of the 13 photos.
8. **UI**: attach photo in the AI bar; progress; result replaces/adds to the scene (undo).
9. **Refinement loop**: capture + photo → scene agent with tools, ≤ 2 rounds.
10. **Evaluation** on the 13 photos (paid, cap US$1.50): side-by-side sheet, fidelity table, fixes.
