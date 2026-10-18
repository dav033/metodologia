# dev — Architecture

**Last verified:** _not yet_ against commit _—_ (created 2026-10-17).
**Audit status:** _not started_ · **Coverage:** _not assessed_ · **Independent review:** _not done_.
Re-check against the code and update both whenever you edit this file.

_Living document: the current truth, edited in place (C4 levels 1–2 + a lean arc42). The *why* of changes lives in
DECISIONS.md, risks and debt in PENDING.md. Keep it under 150 lines; delete sections that don't apply. For business
projects, sections 3–6 describe actors, steps, systems, documents and handoffs instead of containers and modules._

_Update it in the same commit when a container, a module's public API, an owned table, an external integration or
a key flow changes._

## 1. Goals and quality priorities
- Purpose (2 lines) and who uses it.
- Last confirmed with owner: YYYY-MM-DD.
- Top 3 quality goals, in priority order (e.g. correctness of money, cost per LLM call, time to change), and what
  we accept sacrificing for them.

## 2. Constraints and conventions
- Fixed constraints: hosting, budget, RAM, compliance, team size.
- Conventions not obvious from the code, and traps we fell into (link D-xxx).
- Rules a tool enforces: name the tool and its config file (architecture tests, linters).

## 3. Context (C4 level 1)
_The system, the people using it, the external systems (auth, payments, LLM providers, email) and what crosses
each arrow (data, protocol). Mermaid `flowchart` or a list._

## 4. Containers (C4 level 2)
_Diagram optional; the table is required._

| Container | Tech | Responsibility | Owns data | Talks to (protocol) |
|---|---|---|---|---|

## 5. Modules
_One table per backend container. Dependency rule in one line + pointer to the architecture-test config. A C4
level 3 diagram only for the one module that is hard to hold in your head._

| Module | Responsibility | Public API (facade / events) | Tables it owns | Depends on |
|---|---|---|---|---|

## 6. Key flows (max 3)
_The flows that cross containers or are easy to break (e.g. checkout, an LLM job). Numbered steps or a sequence
diagram, including failure and retry behaviour._

## 7. Cross-cutting concepts
_One short paragraph each, with the file where it lives: error contract and codes, auth/authorization,
pagination, idempotency, validation, config/env, logging, jobs/outbox, migrations, testing strategy._

## 8. Deployment
_Environments, where each container runs, how a release happens, how to roll back. Hosts and credentials
locations → TOOLS.md (no secrets here)._

## 9. Data (if non-trivial)
_Main entities and relationships, owning module, retention._

## 10. Decisions, risks, glossary
- Decisions that shape everything: D-xxx (DECISIONS.md).
- Risks and tech debt: PENDING.md.
- Glossary: domain terms, one line each.

_For a workspace audit, set status to `complete` or `partial` and summarize coverage here: every confirmed repo,
shared workspace docs, local checks, and independent review. Explain any gap and the next evidence needed. If the
owner confirms that no implementation repo exists yet, keep code analysis `not started` and audit status `partial`;
document only confirmed intent/process context. Keep the per-repo coverage matrix and detailed finding evidence in
the audit notes or report; this document remains the concise product-level current truth._
