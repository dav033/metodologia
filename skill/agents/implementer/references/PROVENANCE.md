# Implementer adaptation provenance

Upstream files were read as data at the pinned `HEAD` commits below. Only principles were adapted; upstream text,
code, hooks, runtimes and installers were not copied or executed.

| Repository | Path | Commit SHA | License at pinned revision | Adapted into |
|---|---|---|---|---|
| `DietrichGebert/ponytail` | `skills/ponytail/SKILL.md` | `09c434ab73ca43761c5d8b0c5d341926c2fba710` | MIT (`LICENSE`) | `skill/agents/implementer.md`: minimal complete implementation, reuse, no speculative work, preserve requirements and checks. |
| `JuliusBrussee/caveman` | `skills/caveman/SKILL.md` | `b4531dfc05a3ef0ba93b57e8bfa5f48564a4b4d6` | Apache-2.0 at this revision (`LICENSE`, `LICENSING.md`, `NOTICE`); `LICENSING.md` records MIT terms for pre-3.0.0 adoption-surface contributions. | `skill/agents/implementer.md`: concise reporting while preserving technical facts, structured fields and persisted artifacts. |

The methodology master (§§18.3, 20.7) describes the Caveman skill as MIT under the earlier split-license regime.
The pinned current HEAD states Apache-2.0 applies from 3.0.0 onward. This adaptation follows the license
information at the fetched revision; it uses independently worded principles rather than copied skill text.
