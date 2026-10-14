# Learnings

## Confirmed

- **LG-002 · preference** The owner wants problems settled by three subagents arguing different alternatives and a clean judge, not by asking him
  - 2026-10-12T22:51:51.541601-05:00 · REQ-006: explicit instruction when leaving the autonomous loop on 2026-10-12

- **LG-001 · convention** An independent audit by another provider finds defects the builder's own tests do not: the first adversarial pass on the router returned 21 verified findings
  - 2026-10-12T22:51:51.423242-05:00 · REQ-006/audit1: delegation D-20261012-223148-cfc7 (codex-luis gpt-6-luna xhigh): 4 high, 16 medium, 1 low; 18 fixed the same session

## Candidates

- **LG-004 · preference** Pick the best model for the situation regardless of which provider hosts the current session: no preference for the active account; route through the router/delegate (best measured route for the kind), and audits go to a different provider than the builder
  - 2026-10-13T12:01:18.599649-05:00 · REQ-015: Session 553c2466: all subagents were Claude because the host Agent tool only offers Claude; bt_agents.py also ranked non-Claude audit routes last (uncommitted change); owner asked why no Codex

- **LG-005 · preference** When the owner says 'trabajo autónomo': settle open decisions with 3 haiku-medium subagents each defending one solution plus a haiku-max judge, and announce to the owner that the directive was understood and the debate agents will be launched; irreversible/external/spend actions still wait for him
  - 2026-10-13T12:22:59.496857-05:00 · REQ-015: Owner instruction 2026-10-13 in session 47f58a4d

- **LG-006 · tooling** Marathon worktrees need node_modules (symlink to the main checkout); without it the integration verify 'npx jest' stops at the npx install prompt and the task fails for an environment reason
  - 2026-10-14T12:51:54.965068-05:00 · REQ-005/T1: REQ-005 M1 failed three integration attempts with 'Need to install the following packages: jest@30.5.2'; passed once the integration worktree had the node_modules symlink

## Rejected

- **LG-003 · tooling** bitacora.py trace only reads requirement lines written '- R1. text'; a SPEC that writes '- **R1 — Title.** text' makes every covers: R<n> an unknown-ref error.
  - 2026-10-13T01:09:32.543784-05:00 · REQ-001/M3-audit: bt_trace.py _requirements regex '^\s*-\s+(R\d+)\.\s+(.+)$' vs REQ-001 SPEC: 14 unknown-ref diagnostics (M3 audit).
  - 2026-10-13T01:35:10.258890-05:00 · owner rejection: defect fixed in bt_trace (requirement-line styles); no longer something a session must know. I had marked it confirmed by mistake: confirming is the owner's call
