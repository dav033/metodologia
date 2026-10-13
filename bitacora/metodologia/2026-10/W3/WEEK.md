---
status: draft
---
# metodologia — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

## Highlights
- Reviewed the parent skill and integrated selected Caveman, RTK and Grill Me prompts (REQ-003).

## Done
- Concise communication, optional RTK recovery and decision-interview guidance integrated with pinned sources and licenses.
- Static validation, two independent reviews and conversational forward scenarios completed successfully.

## Decisions
- Preserve Spanish/Aye, existing permissions and frontier rounds; no runtime installation or global configuration changes.

## Not done / dropped
- Paid eval suite and real RTK execution were not run. RTK is absent from PATH.

## Carried over to next week
- Owner review of uncommitted REQ-001 through REQ-004 changes.

## A/B pilot
Two agents, same six scenarios: 30.38% fewer total tokens and 3.03% fewer output tokens for the new skill; equal manual quality. Final prose grew 3.28%; one fewer tool turn explains much of the total saving. Exploratory, no RTK compression measured.

## Additional efficiency study — REQ-004
Eight participants tested selective context and compact routing. Integrated selective context after matched screening (-5.55% total tokens) and held-out review (+0.86% total); rejected compact routing. Quality criteria held, collector 5/5 and both permission matrices 6/6 passed; independent reviews approved. Small-sample/cache limits and 1,155,195 participant-token overhead retained with evidence. No universal or monetary saving claimed.


## RTK — REQ-005
Pinned RTK 0.51.0 install path and use guidance now live in the methodology repo, with three paired measurements per command and recoverable evidence. Command-output reduction varied from negligible on a focused diff to 99.8% on verbose successful tests. Full log recovery erased savings; no session/billing benefit claimed. Installer tests 9/9; standards approved after the atomic-write fix; spec review of final recovery/hash checks approved.
