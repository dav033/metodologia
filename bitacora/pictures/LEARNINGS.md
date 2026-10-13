# Learnings

## Confirmed

_None._

## Candidates

- **L-001 · pitfall** A pending item written from a test's assumption (P-042 'undo') can describe a feature that does not exist in the UI: check for the consumer before planning files, and decide the entry point instead of escalating on tier alone.
  - 2026-10-13T15:24:46.148088-05:00 · REQ-016/T1: REQ-016 T1: no undo existed in the guided UI; the haiku attempt escalated, the standard attempt designed «Deshacer» (D-045) in one session

- **L-002 · pitfall** Global colour-card priority can change after a partial replacement, so last-order replay must preserve resolution for originally selected untouched pieces as well as changed pieces.
  - 2026-10-13T18:32:27.705325-05:00 · REQ-016/M2-audit: REQ-016 M2 audit regression test-ultima-orden-color-replay-selection.ts fails: identical rosado to rojo reflex order first replaces 009, then untouched 011; independent antagonist confirms P-082.

- **L-003 · pitfall** Colour replay regressions must thread returned signed history; a green unknown-history property test can miss drift caused by removing exact-card colours on other selected pieces.
  - 2026-10-13T18:51:37.389893-05:00 · REQ-016/M2-audit: REQ-016 M2: old gate passed while P-082 changed 011 to 915; fb872bce registers the failing reproduction and adds returned-history property coverage, seed 20261009/40 green.

## Rejected

_None._
