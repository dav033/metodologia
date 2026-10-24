# Public adversarial techniques

These are narrowly adapted reference techniques, not imported workflows or permissions. The three private
Antagonist skills and Metodología's policy remain authoritative. Upstream files were read at the pinned commits
below; each repository's license was verified at that same commit. No upstream text or code is copied here.

| Source | Commit SHA | License | Borrow | Exclude |
|---|---|---|---|---|
| [PriNova/pi-agent-codebase-workflows — arch-code-review](https://github.com/PriNova/pi-agent-codebase-workflows/blob/35cad6fb3a3e559a2519beed3887cb02497de5b2/skills/arch-code-review/SKILL.md) | `35cad6fb3a3e559a2519beed3887cb02497de5b2` | MIT (`LICENSE`) | Invariant-first checks of ownership boundaries, dependency rules, persistence, side effects, contract compatibility and architecture drift. Use for architecture and shared-contract changes. | Its structured YAML artifact system, requirement to reject Markdown contracts, writes, verdicts and workflow assumptions. Use Metodología's actual contracts and Explorer evidence. |
| [UnitOneAI/SecuritySkills — threat-modeling](https://github.com/UnitOneAI/SecuritySkills/blob/70bc259bb01abb3015ad2ad859ad5253cbf0bcab/skills/appsec/threat-modeling/SKILL.md) | `70bc259bb01abb3015ad2ad859ad5253cbf0bcab` | MIT (`LICENSE`) | A focused STRIDE lens for concrete assets, trust boundaries, attack surfaces, data flows and existing controls when the diff changes a security boundary. | Automatic invocation, report creation, delegated agents, penetration testing or destructive/production actions. Unverified threats stay hypotheses. |
| [vibeeval/vibecosystem — premortem](https://github.com/vibeeval/vibecosystem/blob/3b763b1fb288f57bfa3cce76ef18184b96461a78/skills/premortem/SKILL.md) | `3b763b1fb288f57bfa3cce76ef18184b96461a78` | MIT (`LICENSE`) | A brief, localized pre-mortem for composition, migrations, rollback, operation ordering and downstream contracts; verify each suspected failure and check existing mitigations. | `Task`, questions, todo/report artifacts, execution blocking or presenting a plausible risk as a proven defect. Do not repeat per commit when audit coverage applies. |
| [ultimatile/development-skills — codex-contract-test-review](https://github.com/ultimatile/development-skills/blob/f68aaf63fa077906a7e4d62e9747d262a4c9c4fd/skills/codex-contract-test-review/SKILL.md) | `f68aaf63fa077906a7e4d62e9747d262a4c9c4fd` | MIT (`LICENSE`) | For changed tests of critical contracts or recurring bugs, check whether the test exercises the claimed invariant and would fail on the motivating broken behavior. Treat a gap as missing evidence. | A separate Codex review/session, added review loop, test authoring or broad test-design review. |

## Application

Select only the lens matching the diff. Keep every finding tied to a concrete trigger, consequence and `path:line`;
discard suspicions that existing code or tests already prevent. Preserve Antagonist's read-only tools, one pass,
eight-finding cap and existing output contract. The coordinator/M6 owns triage and acceptance.
