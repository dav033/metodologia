"""Six planning trials. Each plan was written after inspecting the real repository named in `ROOTS` (2026-10-14);
every `file:` reference below was opened by the planner. PLAN.md text is authored by hand (the human narrative) and
PLAN.json is emitted from the compact task definitions, so `check` really compares two independently written views."""
from __future__ import annotations

from pathlib import Path

HOME = Path.home()
ROOTS = {
    "trainingapp": HOME / "dev" / "trainingapp",
    "metodologia": HOME / "dev" / "metodologia",
}


def ev(**dims):  # dimension -> (justification, [refs])
    return {d: {"justification": j, "evidence": refs} for d, (j, refs) in dims.items()}


def task(tid, milestone, title, objective, repo, after, cx, scope, minutes, risk, coupling, conf, rationale, paths,
         shared, accept, verify, evidence, **extra):
    return {"id": tid, "milestone_id": milestone, "title": title, "objective": objective, "repository": repo,
            "after": after, "complexity": cx, "scope": scope, "estimated_minutes": minutes, "risk": risk,
            "coupling": coupling, "confidence": conf, "estimate_rationale": rationale,
            "classification_evidence": evidence, "expected_paths": paths, "shared_resources": shared,
            "acceptance_criteria": accept, "verification": verify, **extra}


def cmd(value, purpose, **kw):
    return {"type": "command", "value": value, "purpose": purpose, **kw}


def manual(value, purpose, expected):
    return {"type": "manual", "value": value, "purpose": purpose, "expected": expected}


TRIALS: dict[str, dict] = {}

# ---------------------------------------------------------------------------------------------------------------
# 1. Sensitive, small, well understood: low complexity, high risk, isolated_fix
# ---------------------------------------------------------------------------------------------------------------
TRIALS["TRAIN-1-session-expiry"] = dict(
    repo="trainingapp", intent="sensitive-small-fix",
    spec="""# TRAIN-1 — Browser sessions must expire on the server

The API sets `Max-Age=28800` on the `training_session` cookie but keeps the session in an in-memory `Map` forever, so a
copied cookie value stays valid after the browser dropped it. Sessions must stop being accepted 8 hours after creation
(server-side), and expired entries must not accumulate.

## Requirements
- R1. A session older than 8 h is rejected by `requireAuth`, `requireMutation` and the WebSocket upgrade.
- R2. Valid sessions and the MCP bearer token keep working unchanged.
- R3. Expired sessions are removed from memory.
""",
    plan_md="""---
status: approved
---
# Plan — TRAIN-1

### M1 — Server-side session expiry
- [ ] T1 — Add auth session tests · repo: trainingapp · files: apps/api/test/auth.test.ts · verify: `npm run test -w @training/api`
- [ ] T2 — Expire sessions after eight hours · repo: trainingapp · after: T1 · files: apps/api/src/http/auth.ts · verify: `npm run test -w @training/api`
- [ ] T3 — Document the session lifetime · repo: trainingapp · after: T2 · files: docs/api-contract.md
""",
    milestones={"M1": ("Server-side session expiry", ["A session older than eight hours is rejected on every path that reads it, with tests proving it"])},
    tasks=[
        task("T1", "M1", "Add auth session tests",
             "Create tests that pin current session behaviour and fail for an expired session",
             "trainingapp", [], "low", "small_change", 30, "low", "low", "high",
             "No auth tests exist yet; auth.ts is 100 lines with one Map, so the tests are short but must build sessions by hand",
             ["apps/api/test/auth.test.ts"], [],
             ["A valid signed session is accepted", "A tampered signature is rejected", "A session created more than eight hours ago is rejected"],
             [cmd("npm run test -w @training/api", "node --test over apps/api/test/*.test.ts (script exists in apps/api/package.json)")],
             ev(complexity=("Plain unit tests against exported pure-ish functions of auth.ts, no new design", ["file:apps/api/src/http/auth.ts", "file:apps/api/package.json"]),
                scope=("One new test file and nothing else changes in the repository", ["file:apps/api/test/repository.test.ts"]),
                duration=("Existing repository.test.ts shows the harness; sessions need hand-built cookies and time control", ["file:apps/api/test/repository.test.ts", "file:apps/api/src/http/auth.ts"]),
                risk=("Tests only; a wrong test cannot affect production behaviour", ["file:apps/api/test/repository.test.ts"]),
                coupling=("Only reads exported auth functions; T2 will make the new case pass", ["task:T2"]),
                confidence=("auth.ts and the test harness were read completely and are both short", ["file:apps/api/src/http/auth.ts", "file:apps/api/test/repository.test.ts"]))),
        task("T2", "M1", "Expire sessions after eight hours",
             "Reject and purge sessions older than the cookie lifetime in validSignedSession",
             "trainingapp", ["T1"], "low", "isolated_fix", 25, "high", "medium", "high",
             "Two-line comparison in one function, sensitive because every authenticated route and the WebSocket upgrade use it",
             ["apps/api/src/http/auth.ts"], ["session-cookie-contract"],
             ["Sessions older than 28800 seconds are not accepted by requireAuth, requireMutation or the upgrade handler", "The expired entry is deleted from the sessions map", "Fresh sessions and the MCP bearer token behave as before"],
             [cmd("npm run test -w @training/api", "T1 tests now pass", created_by="T1"),
              cmd("npm run typecheck -w @training/api", "tsc --noEmit still clean")],
             ev(complexity=("One comparison against createdAt in a function that already looks the session up", ["file:apps/api/src/http/auth.ts"]),
                scope=("A single function changes; the cookie Max-Age already defines the intended lifetime", ["file:apps/api/src/http/auth.ts"]),
                duration=("Tiny edit plus running the tests T1 added and the type check of one workspace", ["file:apps/api/package.json"]),
                risk=("Authentication code: a wrong comparison locks every user out or keeps accepting expired sessions", ["file:apps/api/src/http/auth.ts", "file:apps/api/src/ws/server.ts"]),
                coupling=("The WebSocket server calls sessionFromRequest from the same module and the web client relies on the 401 to recreate its session", ["file:apps/api/src/ws/server.ts", "file:apps/web/lib/api/client.ts"]),
                confidence=("Every caller of sessionFromRequest was read and the cookie lifetime is a literal in the same file", ["file:apps/api/src/http/auth.ts", "file:apps/api/src/ws/server.ts"]))),
        task("T3", "M1", "Document the session lifetime",
             "State in the API contract document that sessions expire eight hours after creation",
             "trainingapp", ["T2"], "low", "small_change", 15, "low", "low", "high",
             "Prose in an existing document that already describes sessions and CSRF",
             ["docs/api-contract.md"], [],
             ["docs/api-contract.md states the eight hour server-side session lifetime"],
             [manual("read docs/api-contract.md section on sessions", "check the statement exists", "the document says sessions expire eight hours after creation")],
             ev(complexity=("Documentation of behaviour that T2 has already fixed", ["task:T2"]),
                scope=("One sentence or short section in one existing document", ["file:docs/api-contract.md"]),
                duration=("The document is short and the change is one paragraph", ["file:docs/api-contract.md"]),
                risk=("A documentation slip is cosmetic and reviewed in the diff", ["file:docs/api-contract.md"]),
                coupling=("It only describes the contract T2 implements and is ordered after it", ["task:T2"]),
                confidence=("The document exists and the behaviour it must describe is fixed by T2", ["file:docs/api-contract.md", "task:T2"]))),
    ],
    expect=dict(
        classify={"T2": dict(complexity="low", risk="high", scope="isolated_fix")},  # AC-04 on a real plan
        critical_path=["T1", "T2", "T3"],
    ),
)

# ---------------------------------------------------------------------------------------------------------------
# 2. Mechanical, wide: low complexity, large_change, high coupling -> must be ordered
# ---------------------------------------------------------------------------------------------------------------
TRIALS["TRAIN-2-package-scope"] = dict(
    repo="trainingapp", intent="mechanical-large-change",
    spec="""# TRAIN-2 — Rename the npm scope `@training/*` to `@trainingapp/*`

Workspace packages are named `@training/web`, `@training/api` and `@training/contracts`. Rename the scope everywhere it
is referenced (manifests, imports, scripts, deployment files) without changing behaviour.

## Requirements
- R1. No file outside node_modules and lockfile history references `@training/`.
- R2. `npm run build`, `npm run typecheck` and `npm test` succeed from the repository root.
- R3. The Docker build of the API and the Netlify build command keep working.
""",
    plan_md="""---
status: approved
---
# Plan — TRAIN-2

### M1 — Rename
- [ ] T1 — Inventory every reference of the old scope · repo: trainingapp · verify: `grep -rn "@training/" . --include=* --exclude-dir=node_modules --exclude-dir=.next --exclude=package-lock.json`
- [ ] T2 — Rename the contracts package and its API consumers · repo: trainingapp · after: T1 · files: packages/contracts/package.json, apps/api/package.json, apps/api/src/app.ts, apps/api/src/repositories/project-repository.ts, apps/api/Dockerfile · resources: workspace-package-scope
- [ ] T3 — Rename the web package and its imports · repo: trainingapp · after: T2 · files: apps/web/package.json, apps/web/lib/types.ts · resources: workspace-package-scope
- [ ] T4 — Rename root scripts and the Netlify build command · repo: trainingapp · after: T3 · files: package.json, netlify.toml · resources: workspace-package-scope

### M2 — Verify
- [ ] T5 — Regenerate the lockfile and verify the whole build · repo: trainingapp · after: T4 · files: package-lock.json · verify: `npm run build`
""",
    milestones={"M1": ("Rename", ["No source, manifest or deployment file references the old scope"]),
                "M2": ("Verify", ["The workspace installs, builds, type-checks and tests with the new scope"])},
    tasks=[
        task("T1", "M1", "Inventory every reference of the old scope",
             "List every file that mentions the old scope so the rename tasks cover all of them",
             "trainingapp", [], "low", "isolated_fix", 15, "low", "low", "high",
             "A grep over the repository, excluding node_modules and the lockfile, already returned 17 matches in 9 files",
             [], [],
             ["Every file that references @training/ outside node_modules is listed in the task notes", "Dockerfile and deployment files are included, not only package manifests"],
             [cmd('grep -rn "@training/" . --exclude-dir=node_modules --exclude-dir=.next --exclude=package-lock.json', "the inventory itself")],
             ev(complexity=("A search with a known pattern; no design choice involved", ["command:grep -rn '@training/' . -> 17 lines in 9 files"]),
                scope=("Read-only inventory, nothing in the repository changes", ["file:package.json"]),
                duration=("One grep and a review of 17 lines", ["command:grep -rn '@training/' . -> 17 lines in 9 files"]),
                risk=("Read-only task with no side effects", ["file:package.json"]),
                coupling=("Feeds T2 to T4 but changes nothing they touch", ["task:T2", "task:T3", "task:T4"]),
                confidence=("The grep was already run and listed manifests, sources, Dockerfile and netlify.toml", ["command:grep -rn '@training/' . -> 17 lines in 9 files", "file:apps/api/Dockerfile"]))),
        task("T2", "M1", "Rename the contracts package and its API consumers",
             "Make the contracts package and every API file use the new scope while keeping the API buildable",
             "trainingapp", ["T1"], "low", "large_change", 30, "medium", "high", "high",
             "Four manifests/sources plus the API Dockerfile; mechanical, but the package name is a contract of the workspace",
             ["packages/contracts/package.json", "apps/api/package.json", "apps/api/src/app.ts",
              "apps/api/src/repositories/project-repository.ts", "apps/api/Dockerfile"], ["workspace-package-scope"],
             ["packages/contracts/package.json is named @trainingapp/contracts", "API imports and Dockerfile build steps use the new scope"],
             [cmd("npm run typecheck -w @trainingapp/api", "the API compiles against the renamed contracts package")],
             ev(complexity=("Find and replace of a known string in known files with no semantic decisions", ["file:packages/contracts/package.json", "file:apps/api/src/app.ts"]),
                scope=("Five files across two workspaces, extensive but uniform", ["file:apps/api/Dockerfile", "file:apps/api/package.json"]),
                duration=("Five small edits plus a lockless typecheck of one workspace", ["file:apps/api/package.json"]),
                risk=("A missed reference breaks installs or the Docker build, found by the build in T5", ["file:apps/api/Dockerfile"]),
                coupling=("Web, root scripts and Netlify all resolve the same package names, so the three rename tasks must be sequenced", ["task:T3", "task:T4"]),
                confidence=("All references in these files came from the grep inventory", ["command:grep -rn '@training/' . -> 17 lines in 9 files", "file:apps/api/src/repositories/project-repository.ts"]))),
        task("T3", "M1", "Rename the web package and its imports",
             "Make the web workspace and its type imports use the new contracts scope",
             "trainingapp", ["T2"], "low", "small_change", 20, "medium", "high", "high",
             "Two files in apps/web; it only compiles once T2 has renamed the package it imports",
             ["apps/web/package.json", "apps/web/lib/types.ts"], ["workspace-package-scope"],
             ["apps/web/package.json is named @trainingapp/web and depends on @trainingapp/contracts", "apps/web/lib/types.ts imports from @trainingapp/contracts"],
             [cmd("npm run typecheck -w @trainingapp/web", "web compiles against the renamed contracts package")],
             ev(complexity=("Replace a known string in two files", ["file:apps/web/package.json", "file:apps/web/lib/types.ts"]),
                scope=("Two files of one workspace", ["file:apps/web/package.json"]),
                duration=("Two edits and a type check of the web workspace", ["file:apps/web/package.json"]),
                risk=("A wrong import name fails the type check immediately", ["file:apps/web/lib/types.ts"]),
                coupling=("It imports the package T2 renames and shares the workspace scope with T4", ["task:T2", "task:T4"]),
                confidence=("Both files are listed in the inventory and are small", ["command:grep -rn '@training/' . -> 17 lines in 9 files"]))),
        task("T4", "M1", "Rename root scripts and the Netlify build command",
             "Update the root npm scripts and the Netlify build command to the new workspace names",
             "trainingapp", ["T3"], "low", "small_change", 15, "medium", "high", "high",
             "Seven script lines in package.json and one command in netlify.toml",
             ["package.json", "netlify.toml"], ["workspace-package-scope"],
             ["Every -w argument in package.json scripts names a renamed workspace", "netlify.toml builds @trainingapp/web"],
             [cmd('grep -c "@training/" package.json netlify.toml', "no old scope remains in these two files (count 0 per file)")],
             ev(complexity=("Eight literal replacements in two files", ["file:package.json", "file:netlify.toml"]),
                scope=("Two configuration files in the repository root", ["file:netlify.toml"]),
                duration=("Eight single-line edits and one grep", ["file:package.json"]),
                risk=("Netlify build breaks silently if a name is wrong, so T5 builds the whole workspace", ["file:netlify.toml"]),
                coupling=("The scripts call the workspaces that T2 and T3 renamed", ["task:T2", "task:T3"]),
                confidence=("Both files were read and every occurrence was in the inventory", ["file:package.json", "file:netlify.toml"]))),
        task("T5", "M2", "Regenerate the lockfile and verify the whole build",
             "Refresh package-lock.json for the new names and prove the workspace builds and tests",
             "trainingapp", ["T4"], "medium", "small_change", 30, "medium", "low", "medium",
             "npm install rewrites the lockfile for renamed workspaces; the build and test run dominate the time",
             ["package-lock.json"], ["package-lock.json"],
             ["package-lock.json contains no @training/ names", "npm run build, npm run typecheck and npm test succeed from the root"],
             [cmd("npm run build", "contracts, api and web build in order"), cmd("npm run typecheck", "all workspaces type-check"),
              cmd("npm test", "all workspace tests pass")],
             ev(complexity=("Needs a judgement on how npm rewrites the lockfile for renamed workspaces and what to do if it hoists differently", ["file:package-lock.json", "file:package.json"]),
                scope=("One generated file changes, validated by the whole build", ["file:package-lock.json"]),
                duration=("An install, a three workspace build and the tests; a Next build is the slow part", ["file:package.json"]),
                risk=("A lockfile rewrite can change resolved versions unnoticed, so the diff must be reviewed", ["file:package-lock.json"]),
                coupling=("Runs after every rename task and nothing else edits the lockfile", ["task:T4"]),
                confidence=("The scripts exist but the install behaviour with renamed workspaces was not tried", ["file:package.json", "assumption:npm updates workspace names in the lockfile without version drift"]))),
    ],
    expect=dict(critical_path=["T1", "T2", "T3", "T4", "T5"],
                covers_inventory=("grep -rl '@training/'", ["T2", "T3", "T4", "T5"])),
)

# ---------------------------------------------------------------------------------------------------------------
# 3. Cross-contract change with an unknown consumer: high complexity/risk/coupling, research first, low confidence
# ---------------------------------------------------------------------------------------------------------------
TRIALS["TRAIN-3-project-list-contract"] = dict(
    repo="trainingapp", intent="cross-contract",
    spec="""# TRAIN-3 — `GET /v1/projects` returns list items, paginated

`GET /v1/projects` returns every project as a full snapshot (including `data_json`), while the web client types the
result as `ProjectListItem` (id, externalKey, name, revision, updatedAt). Return only list items with cursor pagination.
An MCP client in another repository (`trainingApp-mcp`, not part of this workspace) may read the same endpoint.

## Requirements
- R1. The response contains `projects` (list items only) and `nextCursor`.
- R2. Existing web screens keep working.
- R3. No consumer outside this repository is broken without notice.
""",
    plan_md="""---
status: approved
---
# Plan — TRAIN-3

### M1 — Decide and specify
- [ ] T1 — Find out who consumes the list endpoint outside this repository · repo: trainingapp · files: scripts/check-contract-drift.mjs, docs/api-contract.md
- [ ] T2 — Define the list response schema in contracts · repo: trainingapp · after: T1 · files: packages/contracts/src/project.ts, packages/contracts/test/project.test.ts · verify: `npm run test -w @training/contracts` · resources: projects-list-response

### M2 — Implement
- [ ] T3 — Paginate and slim the list endpoint · repo: trainingapp · after: T2 · files: apps/api/src/app.ts, apps/api/src/repositories/project-repository.ts, apps/api/test/list.test.ts · verify: `npm run test -w @training/api` · resources: projects-list-response
- [ ] T4 — Consume nextCursor in the web client and its two screens · repo: trainingapp · after: T3 · files: apps/web/lib/api/client.ts, apps/web/components/project-list.tsx, apps/web/components/project-tabs-bar.tsx · verify: `npm run typecheck -w @training/web` · resources: projects-list-response
- [ ] T5 — Document the new list contract · repo: trainingapp · after: T3 · files: docs/api-contract.md
""",
    milestones={"M1": ("Decide and specify", ["The external consumer question is answered and the new schema is specified and tested"]),
                "M2": ("Implement", ["API, web client and documentation agree on the new list response"])},
    tasks=[
        task("T1", "M1", "Find out who consumes the list endpoint outside this repository",
             "Decide, with evidence, whether anything outside this repository reads GET /v1/projects and what it needs",
             "trainingapp", [], "medium", "small_change", 45, "low", "low", "low",
             "The MCP repository is not in this workspace and the drift script only proves it holds a copy of the import schema",
             ["scripts/check-contract-drift.mjs"], [],
             ["A written decision states whether a backward-compatible view is required", "The decision lists what was checked and what could not be checked"],
             [manual("read scripts/check-contract-drift.mjs and ask the owner for the trainingApp-mcp repository", "gather evidence", "a decision note exists that names each consumer and whether it reads the list endpoint")],
             ev(complexity=("The outcome depends on a repository this workspace does not contain, so the reasoning is about what cannot be seen", ["file:scripts/check-contract-drift.mjs"]),
                scope=("A decision note only, no code changes", ["file:docs/api-contract.md"]),
                duration=("Reading a script and one question to the owner; the answer time is not under the plan's control", ["assumption:the owner can provide the trainingApp-mcp checkout the same day"]),
                risk=("Read-only, but a wrong answer makes T3 break an unseen consumer", ["file:scripts/check-contract-drift.mjs"]),
                coupling=("Its decision shapes T2 and T3 and touches no files they edit", ["task:T2", "task:T3"]),
                confidence=("No evidence of the consumer besides a path in a drift script, so the estimate is preliminary", ["file:scripts/check-contract-drift.mjs", "assumption:the MCP client lists projects through this endpoint"]))),
        task("T2", "M1", "Define the list response schema in contracts",
             "Add a zod schema for list items and the paginated response with tests, as the single definition both sides import",
             "trainingapp", ["T1"], "medium", "small_change", 40, "medium", "high", "medium",
             "Schemas follow the style of project.ts; the open point is whether a legacy view must be representable",
             ["packages/contracts/src/project.ts", "packages/contracts/test/project.test.ts"], ["projects-list-response"],
             ["ProjectListItemSchema and ProjectListResponseSchema are exported from the contracts package", "Tests accept a valid page and reject extra or missing fields"],
             [cmd("npm run test -w @training/contracts", "contract tests pass"), cmd("npm run typecheck -w @training/contracts", "compiles")],
             ev(complexity=("Schema design with strict objects like the existing ones plus a decision about a legacy shape", ["file:packages/contracts/src/project.ts", "file:packages/contracts/test/project.test.ts"]),
                scope=("Two files in one package", ["file:packages/contracts/src/index.ts"]),
                duration=("Schemas are about twenty lines; tests follow project.test.ts", ["file:packages/contracts/test/project.test.ts"]),
                risk=("Both API and web will import this definition, so a mistake propagates", ["file:packages/contracts/src/project.ts"]),
                coupling=("API, web and docs all depend on this schema and T3/T4 are ordered after it", ["task:T3", "task:T4"]),
                confidence=("The schema style is clear but T1 may change what must be representable", ["file:packages/contracts/src/project.ts", "task:T1"]))),
        task("T3", "M2", "Paginate and slim the list endpoint",
             "Return list items with a cursor from GET /v1/projects and cover it with API tests",
             "trainingapp", ["T2"], "high", "large_change", 90, "high", "high", "medium",
             "Public response shape change in app.ts and repository.ts, with unknown external consumers; needs ordering rules and tests from scratch",
             ["apps/api/src/app.ts", "apps/api/src/repositories/project-repository.ts", "apps/api/test/list.test.ts"], ["projects-list-response", "api-v1-compatibility"],
             ["GET /v1/projects returns projects as list items and a nextCursor", "A second request with nextCursor returns the following page without duplicates", "Behaviour for external consumers follows the T1 decision"],
             [cmd("npm run test -w @training/api", "new list tests and the existing suite pass", created_by="T3")],
             ev(complexity=("Cursor semantics over updated_at ordering with ties, plus a compatibility decision from T1", ["file:apps/api/src/repositories/project-repository.ts", "task:T1"]),
                scope=("Route, repository method and new tests across the API, visible to every client", ["file:apps/api/src/app.ts"]),
                duration=("Larger than a plain endpoint: ordering ties, tests and the compatibility branch", ["file:apps/api/src/repositories/project-repository.ts", "file:apps/api/test/repository.test.ts"]),
                risk=("A public response shape consumed outside this repository: breaking it fails clients we cannot test", ["file:apps/api/src/app.ts", "task:T1"]),
                coupling=("Web client and docs consume exactly this response, and the contracts schema defines it", ["task:T2", "task:T4", "task:T5"]),
                confidence=("The code is read, but the external consumer behaviour and tie ordering are not verified", ["file:apps/api/src/app.ts", "assumption:updated_at alone is enough as a cursor"]))),
        task("T4", "M2", "Consume nextCursor in the web client and its two screens",
             "Make listProjects, the project list and the tabs bar read list items and follow nextCursor",
             "trainingapp", ["T3"], "medium", "small_change", 60, "medium", "medium", "medium",
             "Three files; both screens call listProjects and render all projects at once today",
             ["apps/web/lib/api/client.ts", "apps/web/components/project-list.tsx", "apps/web/components/project-tabs-bar.tsx"], ["projects-list-response"],
             ["listProjects returns items and the next cursor", "Both screens still show every project, loading further pages when needed"],
             [cmd("npm run typecheck -w @training/web", "web compiles against the new response"),
              manual("open /projects in the web app with more than one page of projects", "see the list and the tabs bar", "all projects appear and none is duplicated")],
             ev(complexity=("Paging in two client components that currently fetch once", ["file:apps/web/components/project-list.tsx", "file:apps/web/components/project-tabs-bar.tsx"]),
                scope=("Three files in the web workspace", ["file:apps/web/lib/api/client.ts"]),
                duration=("Two components with their own refresh logic and a manual check", ["file:apps/web/components/project-list.tsx"]),
                risk=("A paging bug hides projects from the user without an error", ["file:apps/web/components/project-tabs-bar.tsx"]),
                coupling=("It consumes the response T3 produces and shares listProjects between two components", ["task:T3"]),
                confidence=("Call sites were found with grep, but the web workspace has no automated UI tests", ["file:apps/web/lib/api/client.ts", "file:apps/web/package.json"]))),
        task("T5", "M2", "Document the new list contract",
             "Describe the paginated list response in the API contract document",
             "trainingapp", ["T3"], "low", "small_change", 20, "low", "low", "high",
             "One existing document gains a short section",
             ["docs/api-contract.md"], [],
             ["docs/api-contract.md describes projects, nextCursor and the compatibility decision from T1"],
             [manual("read docs/api-contract.md", "check the section", "the document describes the paginated response and the compatibility note")],
             ev(complexity=("Documentation of behaviour fixed in T3", ["task:T3"]),
                scope=("A single section in one document", ["file:docs/api-contract.md"]),
                duration=("Short section matching the existing document style", ["file:docs/api-contract.md"]),
                risk=("Documentation only, reviewed in the diff", ["file:docs/api-contract.md"]),
                coupling=("Reads the final behaviour of T3 and is ordered after it", ["task:T3"]),
                confidence=("The document exists and its format is known", ["file:docs/api-contract.md"]))),
    ],
    expect=dict(critical_path=["T1", "T2", "T3", "T4"], low_confidence=["T1"],
                classify={"T3": dict(complexity="high", risk="high", coupling="high")}),
)

# ---------------------------------------------------------------------------------------------------------------
# 4. New self-contained feature in this repository (dogfood, pending P-021)
# ---------------------------------------------------------------------------------------------------------------
TRIALS["METH-4-plan-quality-in-review"] = dict(
    repo="metodologia", intent="new-feature",
    spec="""# METH-4 — Show the PLAN.json quality summary where the plan is reviewed

The owner approves plans on the web review page and in the terminal but cannot see classification, critical path or
evidence gaps there; `bt_planner report` exists only as a module command. Show the summary in both places.

## Requirements
- R1. `bitacora.py plan-json report REQ-NNN` prints the summary through the adapter.
- R2. The web plan review page shows critical path, widest level and low-confidence tasks when PLAN.json exists.
- R3. Plans without PLAN.json render exactly as before.
""",
    plan_md="""---
status: approved
---
# Plan — METH-4

### M1 — Terminal
- [ ] T1 — Expose the report action through the adapter and the plan-json command · repo: metodologia · files: skill/scripts/bt_plan_adapter.py, skill/scripts/bt_cli_plan.py · verify: `python3 -m unittest tests.test_plan_integration` · resources: plan-adapter-api

### M2 — Web review
- [ ] T2 — Render the summary block on the plan review page · repo: metodologia · after: T1 · files: skill/scripts/bt_page_req.py, skill/scripts/tests/test_plan_integration.py · verify: `python3 -m unittest tests.test_plan_integration` · resources: plan-adapter-api
- [ ] T3 — Document the new views in the plan contract reference · repo: metodologia · after: T2 · files: skill/references/plan-contract.md
""",
    milestones={"M1": ("Terminal", ["bitacora.py plan-json report prints the quality summary through the adapter"]),
                "M2": ("Web review", ["The plan review page shows the summary and legacy plans render unchanged"])},
    tasks=[
        task("T1", "M1", "Expose the report action through the adapter and the plan-json command",
             "Make `bitacora.py plan-json report REQ-NNN` run the module's report action via bt_plan_adapter",
             "metodologia", [], "low", "small_change", 25, "low", "low", "high",
             "The module already implements report; the adapter and argument parser each need one line and a test",
             ["skill/scripts/bt_plan_adapter.py", "skill/scripts/bt_cli_plan.py"], ["plan-adapter-api"],
             ["plan-json accepts the report action", "The report for a plan with PLAN.json prints JSON with critical_path and distribution"],
             [cmd("python3 -m unittest tests.test_plan_integration", "integration tests, run from skill/scripts")],
             ev(complexity=("Plumbing of an existing module action through two small files", ["file:skill/scripts/bt_cli_plan.py", "file:skill/scripts/bt_plan_adapter.py"]),
                scope=("Two files with one argument choice and one pass-through", ["file:skill/scripts/bt_cli_plan.py"]),
                duration=("Same shape as the earlier compat action wiring in the same files", ["file:skill/scripts/bt_cli_plan.py", "precedent:REQ-009/T4"]),
                risk=("Read-only report; a mistake changes output text only", ["file:skill/scripts/bt_cli_plan.py"]),
                coupling=("The web page task uses the same adapter surface", ["task:T2"]),
                confidence=("Both files are under 60 lines and were read", ["file:skill/scripts/bt_plan_adapter.py", "file:skill/scripts/bt_cli_plan.py"]))),
        task("T2", "M2", "Render the summary block on the plan review page",
             "Show critical path minutes, widest level and low-confidence tasks on the web plan review page",
             "metodologia", ["T1"], "medium", "full_feature", 75, "medium", "low", "medium",
             "A new block in a page renderer with HTML escaping and a legacy fallback, plus tests",
             ["skill/scripts/bt_page_req.py", "skill/scripts/tests/test_plan_integration.py"], ["plan-adapter-api"],
             ["The plan review page includes the summary when PLAN.json is valid", "A plan without PLAN.json renders the same bytes as before", "Values from PLAN.json are HTML-escaped"],
             [cmd("python3 -m unittest tests.test_plan_integration", "integration tests including the new page cases", created_by="T2")],
             ev(complexity=("Rendering in an existing page with escaping and a fallback path; page layout is not fully known", ["file:skill/scripts/bt_page_req.py"]),
                scope=("One renderer function plus tests: a self-contained user-visible feature", ["file:skill/scripts/bt_page_req.py"]),
                duration=("Comparable to adding a block to this page; needs a fixture plan and byte comparison for legacy", ["file:skill/scripts/bt_page_req.py", "file:skill/scripts/tests/test_plan_integration.py"]),
                risk=("Web UI for the owner; wrong output misleads review but nothing executes from it", ["file:skill/scripts/bt_page_req.py"]),
                coupling=("Shares the adapter surface with T1 and no other pending task edits the page", ["task:T1"]),
                confidence=("The page was read only partly; the exact insertion point is not fixed", ["file:skill/scripts/bt_page_req.py", "assumption:plan_panel() is the only place the plan tab is rendered (read its signature, not its body)"]))),
        task("T3", "M2", "Document the new views in the plan contract reference",
             "Describe the report command and the review page block in the plan contract reference",
             "metodologia", ["T2"], "low", "small_change", 15, "low", "low", "high",
             "A short paragraph in an existing reference file",
             ["skill/references/plan-contract.md"], [],
             ["plan-contract.md names the report action and the review page summary"],
             [manual("read skill/references/plan-contract.md", "check the paragraph", "report and the review page summary are described")],
             ev(complexity=("Documentation of behaviour already built", ["task:T2"]),
                scope=("One reference file gains a paragraph", ["file:skill/references/plan-contract.md"]),
                duration=("A paragraph in a file that already lists the plan-json actions", ["file:skill/references/plan-contract.md"]),
                risk=("Documentation only, reviewed in the diff", ["file:skill/references/plan-contract.md"]),
                coupling=("Describes T2 and is ordered after it", ["task:T2"]),
                confidence=("The file exists and its structure is known", ["file:skill/references/plan-contract.md"]))),
    ],
    expect=dict(critical_path=["T1", "T2", "T3"]),
)

# ---------------------------------------------------------------------------------------------------------------
# 5. Investigation with unknown outcome: research task first, confidence low, no invented precision
# ---------------------------------------------------------------------------------------------------------------
TRIALS["METH-5-relay-test-wait"] = dict(
    repo="metodologia", intent="investigation",
    spec="""# METH-5 — The methodology suite waits on a real `zellij` call

The full methodology suite takes about 100 s and prints `Command 'zellij' timed out after 10 seconds` while the relay
tests run. `tests/test_relay.py` alone takes 7 s, so the wait is not in that file in isolation. Find the cause and, if it
is a test touching the host terminal multiplexer, make the suite independent of it.

## Requirements
- R1. The cause is identified with evidence (which test, which call, why 10 s).
- R2. If it is host dependence, the suite passes with no `zellij` on PATH and with one present.
- R3. Production relay behaviour does not change.
""",
    plan_md="""---
status: approved
---
# Plan — METH-5

### M1 — Find the cause
- [ ] T1 — Identify which test calls the real multiplexer and why it blocks · repo: metodologia · files: skill/scripts/bt_relay_launch.py, skill/scripts/bt_relay_client.py, skill/scripts/tests/test_relay.py

### M2 — Remove the host dependence
- [ ] T2 — Isolate the offending test from the host multiplexer · repo: metodologia · after: T1 · files: skill/scripts/tests/test_relay.py · verify: `python3 -m unittest tests.test_relay` · resources: relay-test-fixtures
- [ ] T3 — Prove the suite is independent of the host terminal · repo: metodologia · after: T2 · verify: `python3 -m unittest discover -s tests`
""",
    milestones={"M1": ("Find the cause", ["The call that blocks for ten seconds is identified with evidence"]),
                "M2": ("Remove the host dependence", ["The suite behaves the same with and without zellij on PATH"])},
    tasks=[
        task("T1", "M1", "Identify which test calls the real multiplexer and why it blocks",
             "Name the test, the call site and the reason for the ten second timeout, with a reproduction",
             "metodologia", [], "medium", "small_change", 60, "low", "low", "low",
             "Symptom known, cause unknown: two modules run zellij with timeout=10, and the isolated file does not reproduce it",
             ["skill/scripts/bt_relay_launch.py", "skill/scripts/bt_relay_client.py", "skill/scripts/tests/test_relay.py"], [],
             ["A written note names the test and the production function that spawns zellij", "The note states why the call blocks and how to reproduce it"],
             [manual("run python3 -m unittest discover -s tests with a timing flag and bisect by file", "locate the blocking test", "the offending test and call are named in the note")],
             ev(complexity=("Unknown cause across relay modules and tests; needs bisecting a 100 second suite", ["file:skill/scripts/bt_relay_launch.py", "file:skill/scripts/tests/test_relay.py"]),
                scope=("A diagnosis note; code changes belong to T2", ["file:skill/scripts/bt_relay_client.py"]),
                duration=("One full suite run is 100 s and bisecting takes several runs; the number is a guess", ["command:python3 -m unittest tests.test_relay -> 7.5 s", "assumption:three to five bisecting runs are enough"]),
                risk=("Read and run only, nothing is modified", ["file:skill/scripts/tests/test_relay.py"]),
                coupling=("Findings decide T2 and no file is edited here", ["task:T2"]),
                confidence=("The symptom was seen but the cause was not located; the estimate is preliminary", ["command:python3 -m unittest tests.test_relay -> 7.5 s", "assumption:the call comes from a test that does not stub the runner"]))),
        task("T2", "M2", "Isolate the offending test from the host multiplexer",
             "Make the identified test use an injected runner so it never starts the host's zellij",
             "metodologia", ["T1"], "low", "isolated_fix", 30, "low", "low", "low",
             "Likely a missing runner stub, but the fix depends on T1's finding",
             ["skill/scripts/tests/test_relay.py"], ["relay-test-fixtures"],
             ["The test passes with zellij absent from PATH and with it present", "No production file under skill/scripts changed"],
             [cmd("python3 -m unittest tests.test_relay", "the relay tests still pass and no longer wait on zellij")],
             ev(complexity=("Expected to be an injected runner like the other preflight tests already use", ["file:skill/scripts/tests/test_relay.py"]),
                scope=("One test in one file", ["file:skill/scripts/tests/test_relay.py"]),
                duration=("Small edit if the guess holds; unknown if T1 finds a production-level cause", ["assumption:the blocking test lacks a runner stub"]),
                risk=("Test-only change that cannot alter production relay behaviour", ["file:skill/scripts/tests/test_relay.py"]),
                coupling=("Depends on T1's finding and nothing else edits this file", ["task:T1"]),
                confidence=("The fix shape is guessed before the cause is known", ["file:skill/scripts/tests/test_relay.py", "assumption:no production change is required"]))),
        task("T3", "M2", "Prove the suite is independent of the host terminal",
             "Run the whole suite with and without zellij on PATH and record that both pass in similar time",
             "metodologia", ["T2"], "low", "small_change", 20, "low", "low", "medium",
             "Two full suite runs of about 100 s each plus recording the result",
             [], [],
             ["The suite passes with zellij hidden from PATH", "The suite passes with the host PATH", "No ten second timeout message is printed"],
             [cmd("python3 -m unittest discover -s tests", "full methodology suite"),
              manual("repeat the run with PATH set to exclude the directory containing zellij", "prove independence", "same result and no timeout message")],
             ev(complexity=("Running a suite twice and comparing the output", ["file:skill/scripts/tests/test_relay.py"]),
                scope=("No files change, this is a verification run", ["file:skill/scripts/tests/test_relay.py"]),
                duration=("Two runs of roughly 100 s observed earlier plus notes", ["command:python3 -m unittest discover -s tests -> 103 s"]),
                risk=("Read and run only", ["file:skill/scripts/tests/test_relay.py"]),
                coupling=("Follows T2 and edits nothing", ["task:T2"]),
                confidence=("The full suite duration was measured in this session", ["command:python3 -m unittest discover -s tests -> 103 s"]))),
    ],
    expect=dict(critical_path=["T1", "T2", "T3"], low_confidence=["T1", "T2"]),
)

# ---------------------------------------------------------------------------------------------------------------
# 6. System-level requirement: a single full_system task must be refused, the decomposition accepted
# ---------------------------------------------------------------------------------------------------------------
TRIALS["TRAIN-6-postgres-migration"] = dict(
    repo="trainingapp", intent="full-system-decomposition",
    spec="""# TRAIN-6 — Move the Training API persistence from SQLite to PostgreSQL

The API stores projects and assets in SQLite through `better-sqlite3` (synchronous), with schema migration by
`PRAGMA user_version`, JSON validity enforced by a CHECK, consistent copies taken with `db.backup`, and a Docker/EC2
deployment that mounts the database file. Move persistence to PostgreSQL without losing data or availability.

## Requirements
- R1. All existing data is migrated and verified (row counts and content hashes).
- R2. The API behaves identically for clients, including revision conflicts.
- R3. Backups and rollback keep working on the new store.
""",
    plan_md="""---
status: approved
---
# Plan — TRAIN-6

### M1 — Decide and prepare
- [ ] T1 — Write the persistence port and decide the driver and migration strategy · repo: trainingapp · files: apps/api/src/repositories/project-repository.ts, apps/api/src/repositories/asset-repository.ts, apps/api/src/db/database.ts · resources: persistence-port
- [ ] T2 — Move repositories behind the port without changing storage · repo: trainingapp · after: T1 · files: apps/api/src/repositories/project-repository.ts, apps/api/src/repositories/asset-repository.ts, apps/api/src/services/asset-service.ts, apps/api/src/app.ts · verify: `npm run test -w @training/api` · resources: persistence-port

### M2 — Postgres implementation
- [ ] T3 — Implement the PostgreSQL schema and repositories · repo: trainingapp · after: T2 · files: apps/api/src/db/postgres.ts, apps/api/test/postgres-repository.test.ts · verify: `npm run test -w @training/api` · resources: persistence-port, database-schema
- [ ] T4 — Build the data migration and verification tool · repo: trainingapp · after: T2 · files: apps/api/src/migrate-sqlite-to-postgres.ts · resources: database-schema

### M3 — Cutover
- [ ] T5 — Adapt backup, compose and deployment scripts · repo: trainingapp · after: T3 · files: apps/api/src/backup.ts, ops/ec2/compose.yml, ops/ec2/deploy.ps1, ops/ec2/rollback.ps1, apps/api/Dockerfile · resources: deployment-contract
- [ ] T6 — Rehearse the migration on a copy and write the cutover runbook · repo: trainingapp · after: T4, T5 · files: docs/deployment.md
""",
    milestones={"M1": ("Decide and prepare", ["Storage is behind a port and the migration strategy is decided and written"]),
                "M2": ("Postgres implementation", ["A PostgreSQL implementation passes the same tests and a verified migration tool exists"]),
                "M3": ("Cutover", ["Deployment, backup and rollback support the new store and a rehearsal succeeded on a copy"])},
    tasks=[
        task("T1", "M1", "Write the persistence port and decide the driver and migration strategy",
             "Specify the repository port, choose the PostgreSQL driver and decide how data and downtime are handled",
             "trainingapp", [], "high", "small_change", 90, "high", "high", "low",
             "Architectural decisions with unknown deployment constraints: the EC2 host and database hosting are not visible from this workspace",
             ["apps/api/src/repositories/project-repository.ts", "apps/api/src/repositories/asset-repository.ts", "apps/api/src/db/database.ts"], ["persistence-port", "database-schema"],
             ["A decision record names the driver, the port methods and the migration and rollback strategy", "Open questions about hosting and downtime are listed for the owner"],
             [manual("review the decision record with the owner", "validate the strategy", "the owner accepts or amends the record")],
             ev(complexity=("Cross-cutting design: synchronous better-sqlite3 calls become asynchronous across repositories and routes", ["file:apps/api/src/repositories/project-repository.ts", "file:apps/api/src/app.ts"]),
                scope=("A design record; the code changes are in later tasks", ["file:apps/api/src/db/database.ts"]),
                duration=("Reading eleven call sites and drafting the record; owner review time is not included", ["file:apps/api/src/repositories/asset-repository.ts", "file:apps/api/src/services/asset-service.ts"]),
                risk=("Production data and availability depend on this decision", ["file:ops/ec2/compose.yml", "file:apps/api/src/db/database.ts"]),
                coupling=("Every later task consumes the port and schema decided here", ["task:T2", "task:T3", "task:T4"]),
                confidence=("Hosting for PostgreSQL and the downtime budget are unknown", ["file:ops/ec2/compose.yml", "assumption:a managed PostgreSQL is reachable from the EC2 host"]))),
        task("T2", "M1", "Move repositories behind the port without changing storage",
             "Introduce the async port and keep the SQLite implementation passing every existing test",
             "trainingapp", ["T1"], "high", "large_change", 120, "high", "high", "medium",
             "Routes in app.ts call repositories synchronously; making the port async touches routes, services and tests together",
             ["apps/api/src/repositories/project-repository.ts", "apps/api/src/repositories/asset-repository.ts", "apps/api/src/services/asset-service.ts", "apps/api/src/app.ts"], ["persistence-port"],
             ["All routes use the async port", "The existing API tests pass unchanged against SQLite", "No behaviour change is visible to clients"],
             [cmd("npm run test -w @training/api", "existing API tests"), cmd("npm run typecheck -w @training/api", "no type regressions")],
             ev(complexity=("A synchronous to asynchronous change across routes, repositories and services that must keep revision conflict semantics", ["file:apps/api/src/app.ts", "file:apps/api/src/repositories/project-repository.ts"]),
                scope=("Four source files and the route layer, extensive but behaviour preserving", ["file:apps/api/src/services/asset-service.ts"]),
                duration=("Eleven call sites in four files plus fixing awaits in every route; tests are few", ["file:apps/api/src/app.ts", "file:apps/api/test/repository.test.ts"]),
                risk=("Revision conflict and delete cascades are easy to break and only one test covers them", ["file:apps/api/test/repository.test.ts", "file:apps/api/src/repositories/project-repository.ts"]),
                coupling=("T3 implements the same port and both edit the repository layer", ["task:T3"]),
                confidence=("The code was read, but the test suite is thin and there are no route tests", ["file:apps/api/test/repository.test.ts", "assumption:no code outside apps/api calls the repositories"]))),
        task("T3", "M2", "Implement the PostgreSQL schema and repositories",
             "Provide a PostgreSQL implementation of the port with schema migration and tests equal to the SQLite ones",
             "trainingapp", ["T2"], "high", "full_feature", 180, "high", "high", "low",
             "New schema, driver, migrations and a test harness that needs a database; JSON validity and ON DELETE CASCADE must be reproduced",
             ["apps/api/src/db/postgres.ts", "apps/api/test/postgres-repository.test.ts"], ["persistence-port", "database-schema"],
             ["The PostgreSQL implementation passes the same repository tests as SQLite", "data_json validity and cascade deletion are enforced in PostgreSQL"],
             [cmd("npm run test -w @training/api", "repository tests against PostgreSQL", created_by="T3")],
             ev(complexity=("Reproducing SQLite semantics (JSON check, cascade, user_version migrations) in a different engine", ["file:apps/api/src/db/database.ts"]),
                scope=("A complete second storage implementation with its own tests", ["file:apps/api/src/db/database.ts"]),
                duration=("New driver, schema and test environment; no precedent in this repository", ["file:apps/api/package.json"]),
                risk=("Data integrity: a schema difference corrupts or loses project data", ["file:apps/api/src/db/database.ts"]),
                coupling=("Implements the port from T2 and defines the schema that T4 targets", ["task:T2", "task:T4"]),
                confidence=("No PostgreSQL exists in this workspace to try against", ["file:apps/api/package.json", "assumption:a docker postgres is available for tests"]))),
        task("T4", "M2", "Build the data migration and verification tool",
             "Copy projects and assets from SQLite to PostgreSQL and verify counts and content hashes",
             "trainingapp", ["T2"], "high", "large_change", 120, "high", "medium", "low",
             "One-shot tool with row counts and sha256 comparison; assets also live on the filesystem",
             ["apps/api/src/migrate-sqlite-to-postgres.ts"], ["database-schema"],
             ["The tool reports equal row counts and content hashes for projects and assets on a copy of production data", "The tool is idempotent or refuses to run twice"],
             [manual("run the tool against a copy of the production backup", "rehearse the migration", "counts and hashes match and the report says so")],
             ev(complexity=("Streaming copy with verification across two engines and a filesystem tree of assets", ["file:apps/api/src/backup.ts", "file:apps/api/src/db/database.ts"]),
                scope=("A new standalone tool and its report format", ["file:apps/api/src/backup.ts"]),
                duration=("backup.ts shows the checksum pattern but the copy and verification logic is new", ["file:apps/api/src/backup.ts"]),
                risk=("Operates on production data; an unverified copy loses records", ["file:apps/api/src/backup.ts"]),
                coupling=("Targets the schema from T3 and shares only that contract", ["task:T3"]),
                confidence=("Volume and asset size are unknown", ["file:apps/api/src/backup.ts", "assumption:the dataset fits in one transaction batch"]))),
        task("T5", "M3", "Adapt backup, compose and deployment scripts",
             "Back up PostgreSQL, provide its service or connection in compose, and keep rollback instructions valid",
             "trainingapp", ["T3"], "medium", "large_change", 90, "high", "medium", "low",
             "Four deployment files; hosting choice from T1 decides compose and backup commands",
             ["apps/api/src/backup.ts", "ops/ec2/compose.yml", "ops/ec2/deploy.ps1", "ops/ec2/rollback.ps1", "apps/api/Dockerfile"], ["deployment-contract"],
             ["backup.ts produces a restorable PostgreSQL dump plus assets and checksums", "rollback.ps1 states how to restore the previous store"],
             [manual("run the backup and restore it into an empty database", "prove restorability", "restored row counts equal the source")],
             ev(complexity=("Deployment, backup and rollback semantics change together and are documented only in PowerShell scripts", ["file:ops/ec2/deploy.ps1", "file:ops/ec2/rollback.ps1"]),
                scope=("Five files across application and operations", ["file:ops/ec2/compose.yml"]),
                duration=("Scripts are short but cannot be run locally against the real host", ["file:ops/ec2/deploy.ps1"]),
                risk=("Production deployment and rollback of a database engine", ["file:ops/ec2/deploy.ps1", "file:ops/ec2/rollback.ps1"]),
                coupling=("Uses the PostgreSQL implementation from T3 and the deployment files are shared with release flow", ["task:T3"]),
                confidence=("The EC2 host cannot be inspected from here", ["file:ops/ec2/compose.yml", "assumption:the compose file is the only deployment descriptor"]))),
        task("T6", "M3", "Rehearse the migration on a copy and write the cutover runbook",
             "Run the full migration and rollback on a copy and document the cutover steps with timings",
             "trainingapp", ["T4", "T5"], "high", "small_change", 120, "high", "high", "low",
             "A rehearsal on real data with timing and a written runbook; duration depends on data volume",
             ["docs/deployment.md"], ["deployment-contract", "database-schema"],
             ["The runbook lists every cutover and rollback step with a measured duration from the rehearsal", "The rehearsal report shows verified counts and hashes"],
             [manual("execute the runbook on a copy of production", "rehearse cutover and rollback", "both complete and the verification report is attached")],
             ev(complexity=("Coordinates every earlier task under failure scenarios", ["file:docs/deployment.md", "task:T4", "task:T5"]),
                scope=("A runbook and a rehearsal; no new production code", ["file:docs/deployment.md"]),
                duration=("Depends on a data volume that is not known yet", ["assumption:production data is small enough for a same-day rehearsal"]),
                risk=("Defines the actual production cutover procedure", ["file:docs/deployment.md"]),
                coupling=("Needs the migration tool and the adapted deployment scripts", ["task:T4", "task:T5"]),
                confidence=("Durations are unknown until the first rehearsal", ["file:docs/deployment.md", "assumption:rehearsal runs on EC2 with the same disk"]))),
    ],
    expect=dict(critical_path=["T1", "T2", "T3", "T5", "T6"], low_confidence=["T1", "T3", "T4", "T5", "T6"]),
    # first attempt a planner might make: one task for the whole migration
    naive_full_system=task("T1", "M1", "Migrate the persistence layer to PostgreSQL",
                           "Replace SQLite with PostgreSQL in the API, migrate the data and update deployment",
                           "trainingapp", [], "extreme", "full_system", 600, "high", "high", "low",
                           "Everything at once", ["apps/api/**", "ops/ec2/**"], ["persistence-port"],
                           ["The API runs on PostgreSQL in production with all data migrated"],
                           [manual("deploy and use the API", "see it work", "the API works")],
                           ev(complexity=("Replacing a persistence layer is architectural and touches every layer", ["file:apps/api/src/app.ts"]),
                              scope=("The whole persistence subsystem and its deployment", ["file:apps/api/src/db/database.ts"]),
                              duration=("Several days of work by one engineer including a rehearsal", ["assumption:multi-day effort"]),
                              risk=("Production data and availability are involved", ["file:ops/ec2/compose.yml"]),
                              coupling=("Touches the API, tools and deployment together", ["file:apps/api/src/backup.ts"]),
                              confidence=("Nothing was prototyped and hosting is unknown", ["assumption:hosting is available"]))),
)
