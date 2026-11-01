# Solucionador 20261101-021846-6343 — pictures REQ-021 r35, T10.5:d1@k1

## Trigger
`T10.5:d1` (MANUAL_EVIDENCE_REQUIRED, round 1): the second T10.5 acceptance criterion (observation of the configured AI
provider: English conversation -> English reply, Spanish -> Spanish) is NOT_RUN. Attempt a1 ran
`npm run idioma:test-integracion-resto` with exit 0 on candidate a38776b4633ef2d3a9644a652e5c34d413bd719a (controlled
`google.genai` fixture, 8 screens, role/dictionary coverage, Spanish `buscar_catalogo_rag` call).

## Origin
Not a system defect. The decision is the designed manual-evidence gate (D-195/D-196): the harness cannot and must not
attest a live provider (D-078 rule), and retry/retry_other_route cannot produce the observation; `reverify` is valid only
after a receipt. No engine, plan or environment fault was found: status shows T10.5 `needs_decision`, run r35 running,
no other block. The path to unblock already exists: the card's «Probar esto» (D-196) + `bt-durable attest`.

Why I did not make the observation myself: it needs real Gemini requests (configured locally, owner's key). Precedent D-078
and the solver's rule treat that as a spending boundary needing owner authorization; the owner's 2026-10-31 ~16:30
authorization (two text turns) was given for the then candidate 44acfe97 and does not extend to a38776b4.

Relevant history: that earlier observation (`RUN.notes/T10.5.manual-observation.md`) found the criterion NOT met on
44acfe97 (English conversation showed the Spanish template `fraseCercanasPorColor`); T10.44/T10.441/T10.45 repairs
followed. `fraseCercanasPorColor` still exists in `respuesta-guiada.ts` on a38776b4, so the fresh observation is needed to know
whether the visible reply is now English; it may fail again, in which case «No funciona» -> retry_with_note.

## Fix / rule
None: no code, plan, decision answer, retry, stop, attestation or paid call by this session. Decision T10.5:d1@k1 left open.

## Could not do
The observation itself (owner authorization), see question in result.json.
