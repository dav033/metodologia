# REQ-025 R2 — Visual check of the render control in the running app

Write your report in Spanish. Owner's ruling: no methodology flow. Repo `/home/david/dev/pictures-wt/pilot`; dev server `http://127.0.0.1:3010` (local administrator, no login; it reads the shared DB through a tunnel that sometimes drops for a minute — retry, do not conclude from a single 500).
Check with headless Chromium (`/usr/bin/chromium`, or Playwright from node_modules if present) and screenshots under `/home/david/.cache/render-trabajos/capturas/`:
1. `/3d/decoraciones/plantillas`: each card shows the render state chip (e.g. «Ya tiene sus 14 vistas» for Aniversario arco perla m-c90e9446 / Boda nube perla m-64e6b976; «En cola» for Arcoíris m-dedc61cd, job 53e1edde-…) and the colour select + button.
2. `/asistente?plantilla=plantilla:m-c90e9446`: the chat opens the template with its views; the render control appears in the scene panel for the administrator and shows «Ya tiene sus 14 vistas».
3. `/3d` Taller 3D with a scene loaded: the «Renderizar 14 vistas» section opens and asks the state without errors.
4. `/3d/render`: list + machine state.
Fix layout or behaviour bugs you find in `src/components/render/*` and the mounting code (`src/components/guiado/ensamble/PanelEnsamble.tsx`, `src/components/tres-d/Taller3D.tsx`, `src/components/tres-d/galeria/TodasLasPlantillas.tsx`, `src/app/3d/render/page.tsx`), sober white UI, `@bitacora/ui` components. Do NOT create or cancel render jobs except one of your own for testing (cancel it after); never cancel 53e1edde-9342-4e32-8bc6-548406adce0d. `npx tsc --noEmit` + `npx eslint` on touched files; no test suites. Do not commit. Report with screenshot paths and changed files.
