> SUPERSEDED 2026-10-13: the real bitácora from the other clone reached origin (c1e39c0); use it, not this file.

# Reconstruction of pictures state, 2026-10-09 -> 2026-10-11 (written 2026-10-13)

Source: `git log origin/main` at 65edd83b (112 commits since Oct 9 on main; ~1063 across all refs). Bitacora from the
other machine is lost, so ids below come from commit subjects only. Status: DONE = merged to main, OPEN = no evidence,
PARTIAL, UNKNOWN. Branch heads e4n/e4m/e3-rapido/e4x/e4y/e4z are not in the local repo refs (P-068); f1198efd is not an object here.

## 1. Existing PENDING / SUMMARY items
| Item | Status | Evidence |
|---|---|---|
| P-010 photo-reading + e3-rapido f1198efd | UNKNOWN | f1198efd absent; photo work reached main via aee7b5a5 (photo fidelity merge) |
| P-015 / REQ-002 go-live | DONE (SUMMARY says LIVE 10-09) | migrations 028+029 exist; 034 "applied" in d4b4020d; P-015 eval gate not provable from git |
| P-018 photo fidelity (e4n) | DONE (merged) | aee7b5a5, 49e66620, ce65883a; later 59a06582 and 9f86d67b (P-067) keep tuning |
| P-021 refine acceptance (e4m) | PARTIAL | calibration fa0246e2 (10-08); no merge named; P-022 labelling not evidenced |
| P-029 CI health | DONE | 870ca99b (P-029, P-036, D-031); 77b4af27 python-quality green; 6274a079 `npm run gate` in CI |
| P-031 AI panel B (e4x) | DONE | bddcc98d, 01e7a977, 3bb9b5fc merge (hotfix prerender) |
| P-033 prerender guard | DONE | 53502782 (partial guard), 082a34fb (P-037 also server components) |
| P-026 pampas | DONE | 96ea2038 merge feat/pampas, 725e71d4, 63a3a67e |
| P-025 / P-019 / P-020 / P-028 / P-024 | DONE (already closed) | P-028 a0fad72a; others closed in bitacora |
| P-034 BalloonBuilder ideas | PARTIAL | e7109cc8 (PRO-02/03/13), c69e307b (tanda 2: recipe, size profiles, light/lens), 888637d0 + df620c43 (build sheet) |
| P-035 pricing policy | DONE | closed by D-026; unified quote 81718d69 (D-038) |
| P-007 split Taller3D.tsx | OPEN | src/components/tres-d/Taller3D.tsx = 990 lines at main |
| P-008 split organico.ts / escena.ts | PARTIAL | 90a73677 modules organico; organico.ts 1160, escena.ts 826 lines still large |
| P-017 gold cursive "Love" black | UNKNOWN | foil letters fixes 49e66620, 65edd83b (foil tone); no explicit close |
| P-023 confetti colour as data | UNKNOWN | no commit names it (ce65883a/f43d9ce4 touch confetti only) |
| P-016 / P-022 refine round, A/B labelling | OPEN | owner task; no evidence |
| P-014 14 items without ficha | OPEN | no commit |
| P-030 orphan `taller_taxonomia` | OPEN | no commit; 034 touched RAG partition only |
| P-002 FLUX color fidelity | PARTIAL | 1421391a, 9f8687a7 (metallics keep tint), 9f86d67b; residual dE not measured |
| P-003 idea digitization | OPEN/UNKNOWN | last lots 23-24 on 10-08; 28 ideas + 18 official in a7014966, 46 ideas in b22e4eef |
| P-027 burgundy chrome | UNKNOWN | 9f86d67b "malva espejo" is a different colour |
| P-004,P-005,P-006,P-011,P-013,P-032 | OPEN | no commits (P-011 pampas "tupida" 63a3a67e unrelated) |
| REQ-001 photo -> scene | DONE core, tuning continues | aee7b5a5, 49e66620, ad6a3710, 59a06582, 9f86d67b |
| REQ-002 RAG | DONE | 2ab654c5, e030927c, d4b4020d |
| REQ-003 scene agent v2 | DONE | a3f8d556 merge integ/req-003; paid eval + P-013 still open |
| REQ-004 users + AI spend ledger | PARTIAL | 392fff68 hourly spend caps (migration 035), 19221c7d admin session, `/login`; ledger/dashboard not evidenced |
| REQ-005 decorations from scratch | OPEN | no commit named REQ-005 |
| REQ-006 venue photo -> 3D | OPEN | no commit |
| REQ-007 engine behind guided journey | DONE (phases 0-6, W7) | d6092e8f, b237e018, c4779ecf, edaa49e5, d05a52b8, d00efff2, a7014966; D-039 b5f32b06 removed solo-guiada mode; rollback 7aafc12c (P-045) |
| REQ-008 complex events / salon | DONE (merged) | 8c1701fd, 4ff9bdd4, e8c0e4a7, 55475888, 65edd83b (mantel del salon) |
| REQ-009 voice | DONE | fb8477b6, dca3aebd; Vercel env VOZ_* state unknown |
| REQ-010 AI feedback | DONE | 3a8f56e2, 56207a3b, 58a14047, e4216c98 (migration 030 applied status unknown) |
| REQ-011 module studio | DONE | 03049ca7, 775e4b53, 14698850; migration 031 |

## 2. Ids in commits but missing from the bitacora
Requirements: **REQ-012** free furniture (tables/chairs decoupled, parametric tables, AI tools; 78638080, 386b0cdc).
**REQ-013** multi-repository catalogue sempertex/mobiliario/escenografia, 5 phases (6a760e21, d4b4020d mig 034, 318c5aaa, 8955d367, 3a390153).
Pending ids: P-036 deploy to VPS manual with gate; P-037 prerender guard on server components; P-038 Kontext max resumed by request_id;
P-040 pump table one row per size; P-041/P-046 real salon capacity, grouped equal pieces, frame chip; P-045 ordered rollback of GUIADA_MOTOR + 3D cutover notice;
P-047 colour resolver for 3D edit + property tests; P-049 cutover covers assembled/image, recalculates per proposal; P-050 ajustar_tamanos rejects T-/LOL- with valid sizes;
P-052 "rosa" does not alternate between two pinks; P-054 no scene-AI tool blocks >15 s; P-055 generation body test in CI; P-056 cutover notice + useCorte3d + motor3d:test in CI;
P-058 (cited in P-052 body, meaning unclear); P-066 curated ideas quoted with single quoter; P-067 owner photo uses measured colour split, glitter wall, mirror mauve.
Others: PRO-01/02/03/13 (build sheet, helium+tape, pump seconds, piece dimensions); W4 (AI-models-the-30-reference-photos training harness), W5 (Claude Haiku 5.5 local only, 8c397842; CLI transport a8247ecc), W7.
Decisions (not in DECISIONS.md beyond D-026/D-040): D-023 honesty tests "No pude:"; D-025 realistic image; D-027, D-029 (cited, unclear);
D-031 manual gated VPS deploy; D-035 (cited with quote parity test); D-036 Taller notices must not leak to guided client; D-038 single quote with per-balloon spares;
D-039 production same for everyone (no solo-guiada). Migrations 030-035 exist (feedback, module renders, runtime settings, anthropic provider, repositories, spend caps).
Tooling: `npm run gate`, `escena:test`, `e2e:humo`, `prod:pulso`, `motor3d:test`.

## 3. Where it stopped and best next work
Last commits (10-11 01:44 -> 05:28): CI gate (6274a079), `prod:pulso` and slow-flag fix (302d6e3d), P-067 owner photo colours (9f86d67b),
D-038/D-039 single quote across guided/Taller (d33219cd), hourly spend caps (392fff68), 107-phrase owner corpus through Taller tools with simulated model (0849a074),
and 65edd83b review of D-036 (notices, foil tone, 34" numbers, salon tablecloth). Theme: hardening and consistency after the engine became production default;
the corpus run still found defects, so the review loop was mid-flight. No work in progress is visible after 05:28.

Recommended next tasks:
1. (S) Reconcile the bitacora: add P-036..P-067, D-023..D-039, REQ-012/013, close done items above, then run `npm run gate` and `prod:pulso` on current main to confirm green. Also resolve P-068 (locate unpushed e4n/e4m/e3-rapido/e4y/e4z; likely already merged by integration).
2. (M) Finish the 107-phrase corpus follow-up: re-run it after 65edd83b, fix residual failures, then the paid scene-AI eval (REQ-003) and RAG photo-search eval (P-015 gate).
3. (L) Owner-driven product work with highest user value still open: REQ-004 remainder (AI spend ledger/dashboard on top of caps) or REQ-005/006, plus P-022 owner A/B labelling to re-enable photo refine. Needs owner pick; P-007/P-008 splits are a lower-priority S/M each.
