# Implementer assignment correction — D-072

Owner requested fixing the inappropriate promotion of Luna high for high-complexity implementation. Sonnet medium stays the ordinary preference; Luna high remains an approved quota/availability alternative. Complexity neither reverses those choices nor inserts role-priority ahead of quota for Implementer. Other role choices and explicit pins are unchanged.

Regression first failed with10 subcases across2 tests. After correction,115 targeted tests passed across policy/router/M2, agents, marathon ladder, Planner and Scheduler runtime suites. Ruff, whitespace and offline wheel build pass; built wheel contains exact changed sources, and installed editable runtime resolves these sources. Initial combined consumer command refused a real-bitacora root due existing import order; fresh-process suites passed without weakening the guard.

Actual frozen Pictures REQ-018: two order-variant runs/12 simulated tasks pass. With Claude20% and Codex60% used, T1–T5 Sonnet medium and T6 Sonnet low. Ten-scenario matrix also passes20 runs/80 simulated tasks; only scenario08 changes from the historical matrix (high Implementer now Sonnet medium when Claude has more headroom). Historical artifacts preserved.

No paid/native model calls, implementation of Pictures, other-role policy changes, commits or pushes. No full repo suite or separate static type check was run. P-117/P-118 are unchanged, separate follow-ups.
