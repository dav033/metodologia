# Learnings

## Confirmed

- **LG-002 · preference** The owner wants problems settled by three subagents arguing different alternatives and a clean judge, not by asking him
  - 2026-10-12T22:51:51.541601-05:00 · REQ-006: explicit instruction when leaving the autonomous loop on 2026-10-12

- **LG-001 · convention** An independent audit by another provider finds defects the builder's own tests do not: the first adversarial pass on the router returned 21 verified findings
  - 2026-10-12T22:51:51.423242-05:00 · REQ-006/audit1: delegation D-20261012-223148-cfc7 (codex-luis gpt-6-luna xhigh): 4 high, 16 medium, 1 low; 18 fixed the same session

## Candidates

_None._

## Rejected

- **LG-003 · tooling** bitacora.py trace only reads requirement lines written '- R1. text'; a SPEC that writes '- **R1 — Title.** text' makes every covers: R<n> an unknown-ref error.
  - 2026-10-13T01:09:32.543784-05:00 · REQ-001/M3-audit: bt_trace.py _requirements regex '^\s*-\s+(R\d+)\.\s+(.+)$' vs REQ-001 SPEC: 14 unknown-ref diagnostics (M3 audit).
  - 2026-10-13T01:35:10.258890-05:00 · owner rejection: defect fixed in bt_trace (requirement-line styles); no longer something a session must know. I had marked it confirmed by mistake: confirming is the owner's call
