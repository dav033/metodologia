# Engineering standards: architecture, style, best practices

Read this before designing or writing code. These are the user's standards; general model defaults lose to them.

## Contents
1. Precedence: who wins
2. Hard rules
3. Architecture
4. Style
5. Testing
6. Verification & self-review
7. Debugging
8. Default stacks (→ `stacks/*.md`)
9. Tooling: make the rules enforceable

## 1. Precedence

In an **existing project**, its style is the starting recommendation, not a cage:

1. The repo's tooling (linter, formatter, typecheck, tests): always obeyed.
2. The repo's written conventions (AGENTS.md, CLAUDE.md, README, ADRs).
3. The patterns in existing code. Before writing something new, open 1–2 similar files and match their
   structure, naming, error handling and test layout.
4. These standards.

Refactoring toward these standards is welcome. **Inside the scope** of the current task (code you're touching
anyway, a file you're adding to), just do it, no need to ask: split the file you're editing, extract the
component you're modifying, fix the pattern in the module you're changing. **Outside the scope**, don't do it and
don't interrupt the user for it either: log it in PENDING.md as tech debt with a one-line proposal, and list it
under "Proposals" in your final report so the user can say yes in one go.

In a **new project**, these standards plus the default stack apply directly.

## 2. Hard rules

- **Code language: the repository's language wins.** In an existing repo, write identifiers, file names, comments
  and commit messages in the language the repo already uses (e.g. Spanish in a Spanish codebase) — one language
  per codebase, never mixed. In a new project, or a repo with no clear convention, use English. UI text in
  whatever language the product's users speak. Domain terms with no good translation may stay as-is,
  consistently.
- **Single responsibility.** Each module, class, function and component has one reason to change. If describing
  it needs "and", split it.
- **Modularize first.** Start new work as its own module/feature folder with a small public surface, not as more
  lines in an existing file.
- **File size: > 500 lines is an alert.** Stop and split by responsibility before adding more. Aim for files
  well under 300. Functions over ~50 lines are a smell too. The user strongly dislikes giant files; a post-edit
  hook will warn you when you cross the line.
- **Abstraction yes, over-engineering no.** Abstract when it removes real duplication or hides real complexity
  behind a smaller interface. Don't add layers, interfaces, factories, generics or config "for the future". A
  seam with one implementation is usually hypothetical; two real implementations make it real. Ask yourself:
  would a senior engineer call this overcomplicated?
- **Every changed line traces to the request.** Out-of-scope improvements become proposals, not changes (§1).
- **No obvious comments.** Don't narrate what the code says (`// increment counter`, `// constructor`). Comment
  the *why*: business rules, non-obvious constraints, workarounds with their reason, links to decisions.
- **Errors are never swallowed.** Typed errors with a code; translate them to HTTP/user messages in one place at
  the boundary.
- **Validate at the edges** (requests, env vars, external data, forms) with a schema; trust types inside.
- **No secrets in code.** Config through validated env vars; keep `.env.example` documented.
- **Structural and behavioral changes in separate steps/commits** (refactor, then change behavior) so each is easy
  to review and revert.

## 3. Architecture

**Feature-first.** Organize by business feature, not by technical type. A feature folder owns everything about
that feature and exposes a small public API (`index.ts`); other features import only from that entry point.

```
src/features/<feature>/
  domain/          entities, value objects, business rules (no framework, no DB, no HTTP)
  application/     use cases / services orchestrating the domain
  infrastructure/  repositories, API clients, DB access
  presentation/    UI (frontend) or controllers/DTOs (backend)
  index.ts         public surface
src/shared/        truly cross-feature code only (ui kit, errors, utils, config)
```

Scale it to the size: a small feature can be one folder with a few files; add the layers when the feature grows.
What never changes: business rules don't live in UI components or controllers, and the domain doesn't import
infrastructure.

**Frontend: Atomic Design** inside the shared UI kit and each feature's presentation layer:
- `atoms/` (button, input, badge) → `molecules/` (search field, form row) → `organisms/` (table with filters,
  header) → `templates/` (page layouts) → `pages` (the framework's routes, thin: compose and fetch, no logic).
- Atoms and molecules are presentational: props in, events out, no data fetching, no business rules.
- Logic goes to hooks (`useX`) and the application layer, not into components.
- A component that grows past ~150 lines is usually two components.

**Dependencies point inward:** presentation → application → domain; infrastructure implements interfaces the
application needs. Pass dependencies in, don't create them inside; return results rather than causing hidden side
effects. That is what makes code testable without heavy mocking.

**Data:** PostgreSQL by default. Schema changes only through migrations, never auto-sync. Constraints and
indexes in the database, not only in code.

**Decisions:** a choice that is hard to reverse, surprising without context, or the result of a real trade-off
goes to DECISIONS.md (see `documentation.md`). Read existing decisions before proposing to change something
settled.

## 4. Style

- Enforced by tooling first (formatter + linter, §9); this section covers what tools can't check.
- Names say what things are in the domain's language: `approveOrder`, not `handleData`. Booleans read as
  questions (`isActive`, `hasAccess`). No abbreviations except universal ones (`id`, `url`).
- Small functions at one level of abstraction. Early returns over nested ifs.
- Strict typing: TypeScript `strict: true`, no `any` (use `unknown` + narrowing); Python type hints everywhere.
- Prefer plain functions and data over classes unless the framework wants classes (NestJS) or there is real state.
- Imports sorted, no unused code, no commented-out code (git remembers).
- Commits: Conventional Commits with scope, imperative, in the repo's language: `feat(orders): add approval by amount`.

## 5. Testing

Always use the best method for the risk, but **don't bury a medium project under thousands of tests.** Tests are
there to give confidence to change code, not to hit a number.

- **TDD for business logic and bugs:** write the failing test first, then the code. Every bug fix starts with a
  test that reproduces it.
- **Test behavior through public interfaces,** not implementation details. A refactor that doesn't change
  behavior shouldn't break tests.
- **Shape:** many fast unit tests on the domain; a few integration tests per feature on the real boundaries
  (DB, API); a handful of end-to-end tests for the critical user journeys only (login, checkout, the core flow).
- **Skip:** trivial getters/mappers, framework glue, snapshot-everything UI tests, tests that recompute the
  expected value the same way the code does.
- **Mock only what you don't own** (third-party APIs, email, payments). For your own DB prefer a real test
  database or a local stand-in.
- Never weaken, skip or delete a test to make it pass. If a test is wrong, say so and fix it deliberately.

## 6. Verification & self-review

**No "done" without fresh evidence.** Run it, read the output, then claim.

| Excuse | Reality |
|---|---|
| "Should work now" | Run the tests / the app. |
| "The linter passed" | Linter ≠ typecheck ≠ tests ≠ it works. Run the ones that apply. |
| "It's a small change" | Small changes break builds too. Run the checks. |
| "I'll test it at the end" | Run typecheck and the relevant tests while you go; full suite at the end. |
| "The test was flaky" | Prove it (rerun, read the failure) before dismissing it. |

Before closing, review your own diff (the `reviewer` subagent for larger changes, see `subagents.md`) against this checklist:
- Every change traces to the request; nothing out of scope slipped in.
- No file crossed 500 lines; responsibilities still single.
- Layers respected: no business logic in UI/controllers, no infrastructure in domain.
- Errors handled at boundaries, inputs validated, no secrets, no leftover debug code.
- Tests cover the new behavior and pass; no test was weakened.
- No speculative abstractions, no obvious comments, no dead code.

## 7. Debugging

- Root cause before fixing (`runner` reproduces and distills the failure, `explorer` traces the code path):
  reproduce, read the actual error and stack trace, form a hypothesis, test it.
- After **three failed fix attempts**, stop patching: the problem is likely in the design or in an assumption.
  Step back, re-read the whole code path, question your assumptions, and change approach. Only bring it to the
  user if a second, different approach also fails — and then with what you learned and a concrete proposal.
- Log the root cause and fix in the day log; if it's a trap others could fall into, add it to ARCHITECTURE.md
  under conventions/constraints.

## 8. Default stacks

For new projects (in existing ones, the repo's stack wins):

| Product | Stack | Read |
|---|---|---|
| Web application | Next.js (frontend) + NestJS (API) + PostgreSQL | `stacks/nextjs.md`, `stacks/nestjs.md` |
| Landing page / marketing site | Astro | `stacks/astro.md` |
| AI product | Next.js (frontend) + FastAPI (Python, AI/back) + PostgreSQL | `stacks/nextjs.md`, `stacks/fastapi.md` |

Read only the stack file(s) for the code you're touching.

## 9. Tooling: make the rules enforceable

A rule a tool can check should be checked by the tool. On a new project, set this up in the first task; on an
existing one, use what's there and list what's missing as a proposal in your final report.

- **Formatter + linter:** Prettier + ESLint (TS) / ruff format + ruff check (Python). Include `max-lines` (warn at
  500), no-explicit-any, unused-imports, import sorting.
- **Architecture boundaries:** `eslint-plugin-boundaries` (or dependency-cruiser) so features import each other
  only through `index.ts` and the domain can't import infrastructure.
- **Typecheck:** `tsc --noEmit` / pyright or mypy.
- **One verify command:** `npm run verify` (lint + typecheck + test + build) or equivalent. Run it before
  claiming done.
- **CI** running the verify command on every push.

The `metodologia` skill also installs a post-edit hook that warns when an edited file passes 500 lines.
