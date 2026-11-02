# Solver report 20261101-172819-38f5 — pictures REQ-021 r39

**Trigger:** 11 reconcile resolution requests `SP-5×SP-2` (D-297): SP-5's line (carries SP-8 bilingual mechanism) vs SP-2's account redesign (`cuentas-admin@v2`).
**Origin:** two independent edits of the same account/public screens (SP-2 pre-SP-8 `?lang=` + `CabeceraCuentas`; SP-8 cookie/account language + `SelectorIdioma`). No engine defect; no code change in metodologia.

**Resolutions written** (`<state>/durable/composition/resolutions/<key>.resolved`), verified on a scratch clone (merge f71f204+1c51118): `tsc` clean except unrelated `@sempertex/happie-package-ia` errors, eslint clean, `idioma:test-cobertura` exit 0, `test-ui-admin-cuentas --solo lista|roles` pass.
- ListaCuentas: SP-2 card layout + `ESTADOS_CUENTA.es`. EditorRol: `lg:grid-cols-2` + `ETIQUETAS_PERMISO.es`.
- textos-acceso / textos-cuenta: `crearDiccionario` + `idiomaAccesoDesdeConsulta` / `accessIdentity`; removed duplicated `plans` keys (TS1117).
- activar, restablecer, aviso-datos, cuenta pages: language = `?lang` override over `getRequestLanguage()`; no `accept-language` in pages (SP-8 test); SP-2 `CabeceraCuentas` kept on activar/restablecer/aviso-datos.
- cuenta-actual: SP-2 `getAccountPresentation` + `language` from `getOwnAccount` (so `getRequestLanguage` keeps the saved account language); `getAccountLanguage` stays removed.
- MenuCuenta: SP-2 popup, language pair is `SelectorIdioma` (as `cuentas-admin@v2` §11 states), `?lang` read-only override kept, query-based buttons removed.
- login: SP-8 `SelectorIdioma`+`InterruptorTema language`; `CabeceraCuentas` NOT rendered (owner-approved SP-8 composed shell has none; two language controls would also leave `SelectorIdioma` dead under `?lang`).

**Not done / proposals (for the owner or Planner):**
1. `scripts/test/test-ui-mi-cuenta.ts:88` expects the menu EN button to navigate to `/cuenta?lang=en`; with `SelectorIdioma` it calls `/api/idioma` + refresh, so it fails (everything before it passes). Update to the SP-8 selector.
2. `scripts/test/test-ui-acceso.ts` login assertions (banner Pictures/Sempertex, `getByLabel("Language")` select) fail since login has no `CabeceraCuentas`.
3. git also conflicts on `package.json` (union of scripts) and `BarraCuenta.tsx` (keep ours, `getRequestLanguage`); the engine did not request them — if a next round asks, resolve that way.
4. `getCurrentAccount` now runs two account queries; fold `language` into `presentacion-cuenta.ts`.

No decision answered, nothing integrated. CG-9 reopens via the engine's next reconcile pass; if it stays rejected, `bt-durable retry-task pictures REQ-021 T99`.
