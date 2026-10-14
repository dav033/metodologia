# Test seams: vertical tests at agreed public interfaces

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/tdd/SKILL.md, tests.md and mocking.md, plus the
seam step of skills/engineering/to-spec/SKILL.md. Adapted here: pre-agreed seams, vertical slices, the three
anti-patterns, mocking at boundaries. Original here: seams are agreed through the plan gate instead of a question
per test, and refactoring is allowed when needed. Not imported: "refactoring is not part of the loop", asking the
user before every seam and "one assertion per test". License: `third-party-notices.md`.

## Load when

You write or plan tests for business logic or a bug fix (`engineering.md` §5), define the verification of a plan
task, review whether tests are coupled to implementation, or decide where a regression test belongs. Not for
copy, config or styling changes. The test-volume rules of `engineering.md` §5 still apply: confidence to change
code, not a test count.

## 1. Agree the seams before writing tests

A **seam** is the public interface where behaviour is observed without reaching inside (`design-vocabulary.md`).

- Propose them in the plan's Approach: existing seams over new ones, the highest seam that still exercises the
  behaviour, as few as possible (one is the ideal). For each, one line: what it catches and what it misses.
- The owner approves them with the plan, at the one approval gate. After that do not ask per test. If a task
  needs a seam the plan lacks, take the highest existing public one, record the choice under Rulings in PLAN.md,
  and interrupt only when it would change a public contract.
- Write seams as free text in the plan or task detail. No parser consumes a `seam:` field; do not claim RUN
  enforces one. If tooling later parses it, that is a versioned change, not an assumption.

## 2. Work in vertical slices

One failing test at one seam (watch it fail before writing code: every slice starts red; characterization tests of
existing behaviour are the only exception and are labelled as such), then only enough code to pass it, then the next test, each informed by what the last
taught you. Do not write all tests first: bulk tests verify imagined behaviour and lock in structure before you
understand the implementation. Do not add speculative behaviour for tests you have not written.

## 3. What a good test is

- It states behaviour a caller cares about ("user can check out with a valid cart"), through public API only.
- It survives any refactor that preserves behaviour; if it breaks on one, it was testing past the interface.
- It verifies through the interface (create then read back), not through a side channel such as a raw DB query.
- Expected values come from an independent source: a literal, a worked example, the spec.

## 4. Anti-patterns to reject in review

| Pattern | Tell |
|---|---|
| Implementation-coupled | mocks internal collaborators, tests private methods, asserts call counts or order |
| Tautological | the expectation recomputes the value the way the code does; passes by construction |
| Horizontal | a batch of tests written ahead of any implementation |

## 5. Mocking

Mock at system boundaries only: external APIs, time and randomness, sometimes the file system, and the database
only when no real test database or local stand-in exists. Never mock your own modules or internal collaborators.
Pass external dependencies in rather than creating them inside. Prefer one narrow function per external operation
over a generic fetcher with conditional logic, so each fake returns one shape.

## 6. Bugs

A bug fix starts with a test at the seam that reproduces the real failing pattern (`engineering.md` §5). If the
only reachable seam is too shallow to reproduce it, do not write a test that gives false confidence: record that no
correct seam exists as the finding, and propose the structural change (`improve-architecture.md`).
See [`diagnosing-bugs.md`](diagnosing-bugs.md) for the reproduction step.

## 7. Refactoring

Refactor only when it is needed: the code under change blocks a clean green step, or the task asks for it. There
is no mandatory refactor phase and no rule that it must wait for review. Keep it behaviour-preserving, with tests
green before and after, and in a separate commit from the behavior change (`engineering.md` §2). Refactoring
outside the scope of the task is a Proposal (`engineering.md` §1). In a plan, name the refactor you expect (if any)
as its own behaviour-preserving step done when it blocks a green slice, not as "maybe later" nor as a review item.
