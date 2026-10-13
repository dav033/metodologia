---
id: REQ-003
status: in-progress
created: 2026-10-12
track: standard
---
# REQ-003 — Integrate Caveman, RTK and Grill Me

## Problem & goal
David requested repository research and integration of the most useful skills and prompts from Caveman, RTK and Grill Me into metodologia.

## Scope and requirements
- R1. Adapt Caveman's answer-first concision, exact technical payload and clarity exceptions into the parent skill without changing Spanish, Aye or required progress reporting.
- R2. Add optional RTK usage guidance with executable discovery, supported-command checks, exit-code evidence and recovery of original diagnostics; native commands remain available when RTK is absent.
- R3. Integrate Grill Me/grilling's decision-tree review, recomputed frontier, recommended answers and explicit understanding before planning; keep existing Quick track and user stop conditions.
- R4. Retain selected source prompts and attribution with pinned revisions and applicable license notices. Avoid importing unrelated frameworks or repository contents.
- R5. Verify links, skill structure, integration routing and isolated behavioral scenarios; document actual results.

## Acceptance
- Concise answers retain negations, numbers, units, commands and errors; questions and risky instructions remain unambiguous.
- Missing RTK leads to native commands, without installing binaries or hooks. A compressed failure remains a failure, and existing raw output is recovered before rerunning side effects.
- A dependent design question waits for its prerequisite; facts obtainable from files are explored instead of asked. An explicit request to proceed ends the interview with documented assumptions.
- All borrowed material has source path, revision, license and a clear adaptation boundary.

## Out of scope
Installing RTK/Caveman runtimes, hooks, proxies, changing global configuration, altering Git sync, committing or pushing; fixing findings from the previous review.

## Assumptions
- Grill Me refers to mattpocock/skills, the design-interview skill; Caveman to JuliusBrussee/caveman; RTK to rtk-ai/rtk.
- Natural concise Spanish is preferred over intentionally broken grammar.
- Existing local changes must remain intact.

## Sources researched
- JuliusBrussee/caveman @ 2e08b9177c07bb7249a8a2d1a6758e5db281d002: plugins/caveman/skills/caveman/SKILL.md and license files.
- rtk-ai/rtk @ 311ebcbfd8efdb09b03219e7615a153b5b5e3c97: hooks/rtk-awareness-full.md, hooks/rtk-awareness.md, README.md.
- mattpocock/skills @ 49dd158d1076134a641b33efb035946536778336: skills/productivity/grill-me/SKILL.md and skills/productivity/grilling/SKILL.md.
