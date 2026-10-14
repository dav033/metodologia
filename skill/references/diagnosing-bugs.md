# Diagnosing bugs: reproduction evidence before repair

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/diagnosing-bugs/SKILL.md. Adapted here: the feedback
loop as the core of debugging, red-capable reproduction, minimise, ranked falsifiable hypotheses, tagged
instrumentation, regression test at the right seam, cleanup. Original here: the record-before-repair rule, bounded
evidence gathering and the NEEDS_CONTEXT exit. Not imported: the absolute "no loop, no next phase" gate, the
"seconds, not minutes" requirement, "refuse to give up", and showing the hypothesis list for approval.
License: `third-party-notices.md`.

## Load when

Something is broken, throwing, failing, flaky or slow, a test fails for an unknown reason, or the owner says
"depura", "diagnostica", "por qué falla". It extends `engineering.md` §7; both apply. A clear one-line fix with an
obvious cause does not need the full discipline, only the record in step 1.

## Redact first

Commands, outputs and artifacts you show or log may carry secrets. Replace each with `<REDACTED>`, keep credentials
in environment variables rather than in the command, and quote only the lines that carry the signal.

## 1. Record the reproduction before any repair

Before you edit code to fix the bug, write down in the task note or PLAN Progress log, and in today's day log:

- the **exact command** that reproduces it (script path, test invocation, curl), and
- the output you **actually observed** when you ran it (redacted), including the exit status.

The command must be **red-capable**: it drives the real code path and asserts the owner's symptom, so it can go red
on this bug and green once fixed. "Runs without erroring" is not enough. Prefer deterministic and agent-runnable.
Speed helps but there is no universal time limit: a slow integration or distributed reproduction is valid when
recorded with its cost. Ways to build one, roughly in order: a failing test at the seam that reaches the bug; an
HTTP script against the dev server; a CLI run diffed against a known-good output; a headless browser script; a
replay of a captured payload; a throwaway harness; a property or fuzz loop; a bisection harness (`git bisect run`);
a differential run between versions. Let `runner` run it and distill the failure (`subagents.md`).

Then tighten it: faster, a sharper assertion on the specific symptom, more deterministic (pinned time, seeded
randomness, isolated state). For an intermittent bug, raise the reproduction rate (repeat, stress, narrow timing)
until it is debuggable.

## 2. When no fast deterministic reproducer exists

Reading code, logs and history to build the reproducer is part of the work. When it still cannot be built, do
**bounded** evidence gathering: read logs and captured artifacts, replay what was captured, bisect, add read-only
instrumentation, within a stated budget of steps or time. Then stop and report:

- what you tried and what each attempt showed;
- which hypotheses remain, labelled **unverified**;
- what is needed: access to the environment that reproduces it, a redacted artifact (log, HAR, dump), or
  permission for temporary production instrumentation.

Return `NEEDS_CONTEXT` (or `BLOCKED` when it is not yours to decide) with that evidence. Never claim "fixed" or
"verified" for a change that no red-capable command confirmed; say it is a candidate fix and name the missing proof.

## 3. Minimise, hypothesise, instrument

- Cut inputs, callers, config and steps one at a time, re-running the reproducer, until each remaining element is
  load-bearing. The minimal case becomes the regression test.
- Write 3-5 ranked hypotheses, each falsifiable: "if X is the cause, changing Y makes it disappear". One without a
  prediction is a guess; drop or sharpen it. Put the list in the day log; show it to the owner when they are in the
  conversation, never wait for them.
- Each probe maps to one prediction and changes one variable. Prefer a debugger or REPL over logs; never "log
  everything and grep". Tag every temporary log with a unique prefix such as `[DEBUG-a4f2]`.
- Performance: measure a baseline first, then bisect. Logs are usually the wrong tool.

## 4. Fix and prove

Write the regression test before the fix at a seam that exercises the real bug pattern (`test-seams.md` §6). Watch
it fail; if you forced red by mutating code or a fixture, `diff` against a pristine copy to prove the mutation
landed. Apply the fix, watch it pass, and re-run the original reproducer. After **three failed fix attempts** stop
patching and change approach (`engineering.md` §7).

## 5. Clean up before "done"

- The original reproducer no longer fails (fresh output, not memory).
- The regression test passes, or the absence of a correct seam is documented as a finding.
- `grep` the debug prefix: all tagged instrumentation removed; throwaway prototypes deleted.
- Root cause and the hypothesis that held are in the commit message and the day log; a trap others could hit goes
  to ARCHITECTURE.md under constraints.
