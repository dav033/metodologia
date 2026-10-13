# escritorio — Decision log

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

## D-001 — Keep launcher power controls on existing user wrappers
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** The Super launcher needed local profile, screen, idle-timeout and suspend controls without changing the existing remote-display and thermal policy.
- **Decision:** Add a Rofi Energy mode that calls `perfil` and `remote-screen-off/on`, stores timeout-disabled state and owned suspend-unit names in XDG state, and only restarts Hypridle after an explicit timeout selection.
- **Alternatives:** Duplicate low-level power/display commands — rejected because it could bypass existing lid, stream and profile handling.
- **Consequences:** + one consistent user entry point and safe targeted cancellation / − dashboard metrics are sampled only when Rofi opens.
- **Source:** [2026-10-12](../2026-10/W3/2026-10-12.md) · REQ-002
