# Owner rejection reproduction — SP-2 v2

- Owner record: P-209, rejected 2026-10-31T12:34:09-05:00.
- Exact published commit: `6ec74192eb0175827a9005ae2c152955cb0d220d`.
- Frozen run: PLAN.r30.json. Approved task that owns the reported surface: **T2.4** (account menu and Mi cuenta). The repair must come before the approved visual-review task **T2.7**, and flow through existing SP-2 audit **T2.8** and composition gates.
- Reproduction session: `RUN.solver/20261031-123425-067d`.

## Commands and environment

```sh
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py --project pictures verify open REQ-021 SP-2
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py --project pictures verify serve REQ-021 SP-2 --login
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py --project pictures verify storage-state REQ-021 SP-2 --account test+administrador@pictures.test --out /home/david/.local/share/bitacora-solver/pictures/20261031-123425-067d/admin-storage.json
node /home/david/.local/share/bitacora-solver/pictures/20261031-123425-067d/reproduce-sp2.cjs
```

Official immutable version copy, HEAD confirmed and git status clean. Official servers ready on http://localhost:3000; real test administrator session, no local-access bypass. Playwright Chromium, Spanish locale. Storage state is private (0600), not an evidence attachment. No password changes or paid-provider calls.

## Observed versus expected

At both 1280x900 and 390x844 on `/cuenta?lang=es`:

| Action | Observed | Owner expectation |
|---|---|---|
| Click account trigger | Opens | Opens |
| Click trigger again | Closes | Closes |
| Click outside at viewport (8,200) | Stays open | Closes |
| Press Escape | Stays open | Closes |
| Account identity | Email fallback, no separate name value | Person's name visible |
| Identity labels | Rol; Aviso de datos aceptado with version/date | Plan; no notice-status detail |
| Password section | Existing three-field form | Complete account/password redesign |

Reproducer **exit 1** asserts the missing outside/Escape dismissals. No browser page errors. The owner's broader phrase “cannot close in any way” is partially reproduced: trigger toggle works in Chromium; outside click and Escape do not. First probe exited 2 because the mobile open menu overlaid the heading used as an outside target; the repeated probe uses a genuinely outside coordinate and completes both widths.

## Root cause and contract boundary

`src/components/cuentas/MenuCuenta.tsx` uses uncontrolled native `<details>` and has no outside-pointer or Escape dismissal. `scripts/test/test-ui-mi-cuenta.ts:84` opens the disclosure but never verifies closing it. Native details does not implement these popup dismissal interactions automatically.

`src/app/cuenta/page.tsx` and `textos-cuenta.ts` explicitly render role and accepted-notice version/date. `design/contracts/cuentas-admin@v1.md` F7 and V6 require identity/company/role and notice version/date; frozen T2.4 requires name and role. Relabeling all roles “Plan” would misrepresent administrator, staff and custom roles; catalogue-backed plans need distinction without changing permission semantics.

Name caveat: MenuCuenta and Mi cuenta already render `displayName?.trim() || email`. The operator-owned `pictures/verify-servers.json` test seed inserts no `display_name`; the product's own seed also omits it. The synthetic email fallback alone does not prove loss of an invited person's name. Validate a named account when implementing the repair; never invent a name or change authorization.

## Requested repair and prevention

Planner: preserve every existing acceptance/check/gate; do not retry an accepted snapshot as if it changes source. Add true browser regression for disclosure opening, repeated-trigger dismissal, outside dismissal, Escape and keyboard focus at phone/desktop, plus named and nameless accounts. Account/password UI must retain current-password validation, current-session renewal and other-session invalidation, permission-based administrator links, ES/EN and data-notice enforcement/storage.

Full redesign/removing a contract-required field/replacing role presentation changes the approved UI contract, so it is **not** a D-241 dependency-only bounded repair (which excludes UI changes). Prepare a SP-2 contract revision and exact owner-confirmation delta; only SP-2 needs re-confirmation for that delta. Re-run existing downstream composition checks on the resulting version; do not approve any owner version. Keep P-209 open until the owner approves a later published version.

## Artifacts

All under `/home/david/.local/share/bitacora-solver/pictures/20261031-123425-067d/`:

- `reproduce-sp2.cjs` — red-capable live version reproducer.
- `reproduction.json`, `reproduction.log` — complete two-width results, exit 1.
- `account-open-1280.png`, `account-open-390.png` — open menu and current account/password design.
- `account-after-escape-1280.png`, `account-after-escape-390.png` — disclosure remains open after Escape.

No source fix, commit, integration, later-version approval or passing product acceptance is claimed by this reproduction.
