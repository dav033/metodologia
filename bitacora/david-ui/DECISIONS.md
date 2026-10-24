# david-ui — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — One Next.js app as catalog + shadcn registry, Base UI, kit-only catalog
- **Date:** 2026-10-22 · **Status:** Accepted
- **Context:** Owner's inventory v4 (93 candidate entries from shadcn/ui, Animate UI, Bencho UI, React Bits Free) needs a home, a distribution path and a primitive family.
- **Decision:** Private repo `~/dev/david-ui` (GitHub `dav033/david-ui`): one Next.js 16 app that is the private catalog (owner login) and a shadcn registry `@david-ui` (bearer token), deployed on Netlify. Base UI is the only primitive family. The catalog app is built only from kit components; a missing piece is added from shadcn, else created as an own animated component. Sources whose license forbids copying are reimplemented clean-room.
- **Alternatives:** private npm package — rejected, copy-in lets each project adapt pieces; local-only catalog — rejected, agents and other machines need the registry; Radix — rejected, Base UI favored by the inventory and already used in dav033-demos.
- **Consequences:** + one source of truth (manifest) feeds catalog, registry and agent index; − Animate UI pieces without a Base UI variant need manual integration.
- **Source:** [day log](2026-10/W4/2026-10-22.md) · REQ-001

## D-002 · 2026-10-24 · Wipe REQ-001 execution and restart on schema 1.3.0 subplans
- **Context:** REQ-001 r4 was held at 18/32 after long rework under the pre-subplan engine; Engine v2 (subplans, Designer contracts) is now the default.
- **Decision:** Owner order: delete all execution progress and every artifact of it — run state, executor worktrees, local repo `~/dev/david-ui`, GitHub `dav033/david-ui`, Netlify site `david-ui-private`, `~/.config/david-ui/prod.env`, Codex trust entry, cerebro registry rule. Keep SPEC and rewrite the plan as revision 10 on schema 1.3.0; it recreates repo, remote and site from zero and needs fresh owner approval.
- **Alternatives:** resume r4 on v2 — rejected by the owner; delete the whole bitácora project — not asked (interpretation of "adáptalo"), easy to do later.
- **Consequences:** + clean start with subplans and approved UI contracts; − all built code is gone (no backup kept, by owner order).
- **Source:** [dev day log](../dev/2026-10/W4/2026-10-24.md) session `1fbc12c7` · REQ-001
