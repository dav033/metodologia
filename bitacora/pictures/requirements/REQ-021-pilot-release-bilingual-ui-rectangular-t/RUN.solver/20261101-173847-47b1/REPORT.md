# Solver 20261101-173847-47b1 — pictures REQ-021 r39

**Trigger:** three `resolution` requests (SP-5×SP-14, D-297 reconcile): SP-5's line cannot take SP-14's line in
`ComparadorPlanes.tsx`, `app/planes/page.tsx`, `comparador-planes.module.css`.

**Origin:** a genuine text conflict, not an engine defect. SP-14 (planes@v2) rewrote /planes as four informational cards
(`still` prop, no `selectionView`, local language state, native `#planes-language` select). SP-5 made language
server-owned (`getRequestLanguage`, no local state) and swapped the select for `SelectorIdioma`.

**Resolution (no code or ref touched, only the three `.resolved` files):**
- `page.tsx`: `getRequestLanguage()` (SP-5) + `still={query.still === "1"}` and the wide `searchParams` type (SP-14).
- `ComparadorPlanes.tsx`: SP-14's card grid and `still` class; language comes from the server prop (SP-5, no local state, no
  `useEffect`), persisted with `guardarIdioma` + `router.refresh()`. Kept SP-14's native `<select id="planes-language">`
  instead of `SelectorIdioma`: SP-14's contract/test (`scripts/test/lib/planes-ui-contract.ts`: no `button` inside `main`,
  `getByLabel(/Idioma|Language/)` + ArrowDown/Enter) would deterministically fail with SelectorIdioma's buttons. Unused imports dropped.
- CSS: SP-14's file with `.language select` kept (needed by the native select) and `margin-bottom: 12px`.

**Rule / risk:** no new rule; the engine behaved as designed. If the owner prefers the shared `SelectorIdioma` button group on
/planes, SP-14's contract (planes@v2) and its checks must change first (owner decision). Not verified by build/typecheck here:
the engine's next pass combines the lines and the subplan checks will.
