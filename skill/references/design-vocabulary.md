# Design vocabulary: deep modules, seams, leverage

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/codebase-design/SKILL.md, DEEPENING.md and
DESIGN-IT-TWICE.md. Adapted here: the terms, the deletion test, the dependency categories and design-it-twice.
Original here: precedence, the no-ban rule, the mapping to engineering.md and the subagent limits. Not imported: the
list of forbidden words, the "rejected framings" essay and any fixed number of sub-agents. License: `third-party-notices.md`.

## Load when

- You design or review a module's interface, decide where a seam goes, or judge whether an abstraction earns its
  place (`engineering.md` §2 "Abstraction yes, over-engineering no").
- A `standards` review or the antagonist needs a precise word for a design finding ("shallow", "leaks across the seam").
- You are running [`improve-architecture.md`](improve-architecture.md).

Do not load it for edits that follow an existing pattern, bug fixes or copy changes.

## Precedence

`engineering.md` and the repo's own conventions govern; this is shared vocabulary plus review questions, not a new
rule set. Use the repo's words for its domain. Ordinary words (service, component, API, boundary) stay valid
when the repo uses them: there is no ban. Reach for the terms below when plain words would be ambiguous.

## Terms

| Term | Meaning | Not to be confused with |
|---|---|---|
| **Module** | Anything with an interface and an implementation, at any scale (function, class, package, slice) | "unit", "component" when you mean any scale |
| **Interface** | Everything a caller must know: signature, invariants, ordering, error modes, config, performance | only the type signature |
| **Depth** | Behaviour a caller can exercise per unit of interface learned. Deep = much behaviour, small interface | a ratio of lines of code |
| **Seam** | A place where behaviour can change without editing in that place; where an interface lives | "boundary" (bounded context in DDD) |
| **Adapter** | A concrete thing satisfying an interface at a seam; names a role, not substance | the module's implementation |
| **Leverage** | What callers gain from depth: one implementation pays back across N call sites and M tests | |
| **Locality** | What maintainers gain: change, bugs and verification concentrate in one place | |

## Questions that make a design reviewable

- **Deletion test.** Imagine deleting the module. Complexity vanishes: it was a pass-through, remove it.
  Complexity reappears in N callers: it was earning its keep.
- **Interface is the test surface.** Callers and tests cross the same seam. A test that must reach past the
  interface means the module has the wrong shape (see [`test-seams.md`](test-seams.md)).
- **One adapter is a hypothetical seam; two are a real one.** This is `engineering.md` §2 stated once more: no
  port unless production plus a test double (or a second real implementation) exist.
- **Can the interface shrink?** Fewer methods, simpler parameters, more hidden inside. Dependencies passed in,
  results returned instead of hidden side effects (already `engineering.md` §3).
- **Internal seams stay internal.** Do not widen a public interface just because a test wants access.

## Dependencies decide how to test across a seam

| Category | Example | Treatment |
|---|---|---|
| In-process | pure computation, in-memory state | merge modules, test through the new interface; no port |
| Local-substitutable | Postgres with a local stand-in | test with the stand-in; seam stays internal |
| Remote but owned | your own service over the network | port at the seam; HTTP adapter in production, in-memory in tests |
| True external | payments, email, third-party API | inject a port; a fake or mock adapter in tests |

When a deepening replaces shallow modules, replace their tests with tests at the new interface; do not stack both.
Never delete or weaken a test without saying so (`engineering.md` §5).

## Design it twice (optional)

Only for an interface that is hard to reverse or will have many callers. Draft two or three radically different
interfaces (minimal entry points; maximum flexibility; optimized for the most common caller). Each draft states
the interface with invariants and errors, a caller example, what it hides, its dependency strategy and where
leverage is thin. Compare on depth, locality and seam placement, then recommend one, or a hybrid, with a reason.
Read-only subagents may draft in parallel within the limits of `subagents.md`; without subagent support draft them
yourself in turn. Record the chosen design and the rejected ones in DECISIONS.md when it meets the criteria in
`engineering.md` §3. Out-of-scope redesigns are Proposals, never edits (`engineering.md` §1).
