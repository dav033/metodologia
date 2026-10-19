# Isolated M3 technical smoke

## Requirements
- R1. Real M1/M2/M3 dispatch a native agent in an actual Git worktree; implement the specified standalone normalizeTags function and tests; preserve a restorable binary-safe patch without commits/push. External verifier checks values,invalid inputs,source stability and replay.
- R2. M1 alone accepts actual evidence and promotes a successor without launching it.

Owner requested testing the M3 flow; no Pictures feature task,T2 of REQ-018,canonical integration,commit,push,deploy or global config change is approved. Runtime root and repository clone are disposable but retained.
