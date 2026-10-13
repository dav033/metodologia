# REQ-001 final review — session 11

## Scope and independence
- Baseline `3ea1a97`; reviewed HEAD `c1a524d`, complete feature diff (22 files, +2059/-25).
- Two native fresh-context read-only reviewer agents: axes `spec` and `standards`. They received SPEC/PLAN, the diff, and governing scope. No code/tests were changed by reviewers.
- Spec initially approved its static pass; after explicit reassessment of the previously reproduced M3 findings, both reviewers independently returned CHANGES_NEEDED.

## Correctness findings accepted
1. P-011 (medium, R5): reversing a section move during its exit can leave the recovered desktop/mobile shared title permanently `visibility:hidden` when its projection box is zero-size. The M3 audit reproduced the defect; both reviewers require a real-Motion regression and restoration while preserving title layout IDs.
2. P-009 (spec medium / standards low, R6): the entering checkbox label can resolve to an exiting inert checkbox sharing the same DOM ID. Each mounted instance needs its own DOM ID and a regression for label association/activation while both sections coexist. Shared title IDs remain unchanged: sharing them is the intentional animation contract.

## Findings outside these corrections
- No further security, contract, layering, scope or R1–R7 defects identified in the whole diff.
- Pixel-level motion remains unverified under the approved headless lab constraints (P-005). Existing design/measurement proposals remain in PENDING rather than expanding this change.

## Follow-up gates
- Regression implementation and exact final Verification: in progress; logs `REQ-001-final-session11-red.log` and `REQ-001-final-session11-green.log`.
- Focused spec/standards re-review and staged antagonist gate: pending, before the feature-branch correction commit.
