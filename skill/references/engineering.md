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
- **File size: > 500 lines is an alert.** If you're about to add code to a file that's already over (or near) 500
  lines, split it by responsibility **first** — that's in scope even on "hazlo directo": put your new code in its
  own module and move the part it belongs to with it. Only a one-line fix may leave the split as a Proposal. Aim
  for files well under 300; functions over ~50 lines are a smell too. The user strongly dislikes giant files; a
  hook warns you when a file crosses the line (after every edit, and after shell commands inside a git work tree).
  Prefer the Edit/Write tools for code anyway: the shell check compares with HEAD and cannot see a change you
  commit in the same command.
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

For module interfaces, seams and abstractions (deep versus shallow), load [`design-vocabulary.md`](design-vocabulary.md);
for an explicit request to find architecture improvements, [`improve-architecture.md`](improve-architecture.md).

**Feature-first.** Organize by business feature, not by technical type. A feature folder owns everything about
that feature and exposes a small public API; nothing outside the feature imports its internals.

```
src/features/<feature>/
  domain/          entities, value objects, business rules (no framework, no DB, no HTTP)
  application/     use cases / services orchestrating the domain, their DTOs
  infrastructure/  repositories, API clients, DB access
  presentation/    UI (frontend) or controllers (backend)
  index.ts         public API
src/shared/        truly cross-feature code only (ui kit, errors, utils, config)
```

Scale it to the size: a small backend feature is one flat folder; add the layer folders when it grows (Next.js
features always use them). Each stack names the layers its own way; the architecture tests (§9) check them:

| Layer | Next.js | NestJS | FastAPI |
|---|---|---|---|
| presentation | `presentation/` | `*.controller.ts` | `router.py` |
| application (+ DTOs) | `application/` | `*.service.ts`, `*.facade.ts`, `dto/` | `service.py`, `schemas.py` |
| domain | `domain/` | `domain/` | `domain.py` |
| infrastructure | `infrastructure/` | `*.repository.ts`, `*.entity.ts` | `repository.py`, `models.py` |
| wiring (any own layer) | — | `*.module.ts` | `dependencies.py` |
| public API | `index.ts`, `index.server.ts` | `index.ts` | `__init__.py` with `__all__` |

**Dependency rules** (checkable):
- Imports are one-way: entry points (routes, `app.module`, `main`) → features → shared. `shared` never imports
  features; features never import entry points.
- `domain` imports only domain code and shared errors/utils: no framework, ORM or HTTP.
- `presentation` never imports `infrastructure`: components, controllers and routers don't touch repositories,
  ORM entities or API clients.
- `application` may call its own feature's infrastructure directly (concrete repository, API client). An
  interface (port) only when a second real implementation exists (§2).
- Public API: `index.ts` with explicit named exports, never `export *`. No `index.ts` barrels inside layer folders
  or in `shared/`: import the file directly. Server-only exports go in `index.server.ts`.
- Not everything is a feature: code with one consumer (one route, one endpoint) stays next to it until a second
  consumer exists.
- Pass dependencies in, don't create them inside; return results rather than causing hidden side effects.

**Between features.** Frontend: features never import each other; compose them in the route (`app/`).
Backend: a feature reaches another only through its facade (exported by its public API) or through events.
Reference other features' records by ID. Each feature owns its tables (table-name prefix); no joins into another
feature's tables in write paths, no transaction spanning two features.

**Frontend.** Atomic Design (atoms/molecules/organisms) applies only to `shared/ui`, the domain-free design
system. Feature presentation is flat, files named for what they are (`order-table.tsx`); no `templates/` or
`pages/` folders (layouts and route files are those). Route-only UI lives in the route's `_components/`. Routes
are thin: `page.tsx` reads params, calls feature public APIs and composes. Components are props in, events out;
logic goes to hooks and the application layer; past ~150 lines a component is usually two. Data access, client
boundary, server state and errors: `stacks/nextjs.md`.

**Backend API contract** (NestJS and FastAPI; how-to in the stack files):
- **Versioning:** `/v1` prefix from day one; changes are additive only. A breaking change is a new version plus a
  DECISIONS.md entry.
- **Errors:** one shape, RFC 9457 `application/problem+json` (`type`, `title`, `status`, `detail`, `code`,
  `request_id`). `code` is stable UPPER_SNAKE and part of the API. No stack traces in responses. Domain and
  application code throw domain errors, never HTTP exceptions; one handler maps them. Unknown errors → 500, logged
  with the `request_id`. Check permission before existence, so a 404 never leaks what a 403 would hide.
- **Pagination:** every list endpoint is cursor-paginated from day one: `{ items, next_cursor }`, opaque cursor,
  `limit` with a documented default and max (above max is clamped, invalid is a 400); `next_cursor` is null only
  at the end.
- **Idempotency:** POSTs with side effects (create, charge, send, paid LLM call) accept an `Idempotency-Key`
  header; store key + request hash + response under a unique constraint; same key with another body → 422.
- **Background work:** fire-and-forget (FastAPI `BackgroundTasks`, an un-awaited promise) only for work you can
  afford to lose. Retries, long jobs, money or LLM cost → a queue or a DB job table with a status endpoint. Events
  that must follow a DB write go through an outbox row written in the same transaction; consumers are idempotent
  (dedupe by event ID).

**Data:** PostgreSQL by default. Schema changes only through migrations, never auto-sync. Migrations are
reversible (or state why not), named date + slug, and run as an explicit deploy step, never on app boot. Explicit
naming convention for PK/FK/unique/check/index constraints; snake_case tables and columns; `_at` for timestamps
(`timestamptz`), `_date` for dates. Constraints and indexes in the database, not only in code.
- Repositories: single-purpose methods named for the question (`findByEmail`, `listOverdueByCustomer`), no
  catch-all criteria object.
- Decide once per project, in DECISIONS.md, whether the ORM entity is the domain entity (default for CRUD-ish
  features) or maps to a pure domain entity (when real invariants exist).

**Monolith first.** One deployable API per product (plus the FastAPI process when Python is needed). Split out a
service only on a trigger recorded in DECISIONS.md (independent scaling, different runtime, separate deploy
cadence or team), and only for a feature that already talks through its facade/events.

**Not adopted by default** (only inside a genuinely complex feature, via DECISIONS.md): CQRS/command bus, a value
object for every primitive, separate domain and persistence models everywhere.

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

- **Seams:** where tests attach and what to mock is in [`test-seams.md`](test-seams.md); load it when planning or
  writing tests for business logic or a bug fix.
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
- **Test oracles** (REQ-021 T1.7: a permission matrix whose expected values were read from the implementation's own route
  map, sending only GET and counting 405/5xx as allowed, so it could not fail on the defects the audit then found):
  the expected value of a test over permissions, money, identity or isolation comes from the SPEC or a table the
  owner approved, never from the code under test. Such a matrix covers every role × every method (GET and the writing
  methods) and asserts the denied cases explicitly with the exact status (401/403); a 405, a redirect or a 5xx is a
  failure, not "access refused". The Reviewer checks this on `test` tasks; `plan-json check` warns when a test task
  over a security-sensitive task does not state it.

## 6. Verification & self-review

For UI subplans, include conformance with the owner-approved versioned design contract in the completion check.
The Reviewer runs the `visual` axis against the rendered application and declared breakpoint × state coverage;
Runner screenshots are evidence inputs, not a visual verdict. A missing or unapproved contract means UI work is
not ready to start.

**No "done" without fresh evidence.** Run it, read the output, then claim.

For interfaces or product copy, also apply [`interface-quality.md`](interface-quality.md). For a substantive
diff review, use the evidence protocol in [`subagents.md`](subagents.md#evidence-for-diff-reviews); it strengthens
the existing spec/standards review, without adding another review stage.

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
- Layers respected: no business logic in UI/controllers, no infrastructure in domain; architecture tests pass.
- Backend contract held (§3): cross-feature facade/events, error shape, pagination, idempotency.
- Errors handled at boundaries, inputs validated, no secrets, no leftover debug code.
- ARCHITECTURE.md still true (modules, public APIs, owned tables, integrations, key flows).
- Tests cover the new behavior and pass; no test was weakened.
- For a UI subplan, implementation conforms to the owner-approved contract version and Reviewer `visual` findings
  have been resolved or accepted through the existing audit process.
- No speculative abstractions, no obvious comments, no dead code.

## 7. Debugging

For a broken, failing, flaky or slow behavior, follow [`diagnosing-bugs.md`](diagnosing-bugs.md) before any repair.

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
- **Architecture tests:** a boundary rule no tool checks is a suggestion. Copy the tested templates from the
  skill's `templates/arch/` (paths match the stack layouts; each file says what it checks and how to install it):

  | Stack | Files | Command |
  |---|---|---|
  | Next.js | `nextjs/eslint-boundaries.config.mjs` + `nextjs/.dependency-cruiser.cjs` | `eslint` + `depcruise src` |
  | NestJS | `nestjs/.dependency-cruiser.cjs` + `nestjs/eslint-arch.config.mjs` | `depcruise src` + `eslint` |
  | FastAPI | `fastapi/importlinter.toml` (into `pyproject.toml`) | `lint-imports` |

  Not tool-checkable, so reviewed (the antagonist checks them): thin routes, data access only through the DAL,
  error shape, permission before existence, pagination, idempotency, async misuse.
- **Typecheck:** `tsc --noEmit` / pyright or mypy.
- **One verify command:** `npm run verify` (lint + typecheck + arch + test + build) or equivalent. Run it before
  claiming done.
- **CI** running the verify command on every push.

The `metodologia` skill also installs a hook (`file_guard.py`) that warns when a source file passes 500 lines: after
edits, and after shell commands for files git shows over the limit that were not over it at HEAD (or grew while
already over). Durable runs apply the same rule to each attempt's snapshot commit.
