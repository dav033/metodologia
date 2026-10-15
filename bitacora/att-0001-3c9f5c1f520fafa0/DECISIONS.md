# att-0001-3c9f5c1f520fafa0 — Decision log

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

## D-001 — Greeting format and empty-input rule
- **Date:** 2026-10-15 · **Status:** Accepted
- **Context:** T1 required a "Hello" greeting but did not fix the exact text or whether whitespace-only names are empty.
- **Decision:** `greet(name)` returns `Hello, <name>!` after trimming; whitespace-only input raises `ValueError`.
- **Alternatives:** `Hello <name>` or `Hello, <name>` without `!` — no spec to support them.
- **Consequences:** + simple, tested. − format is a guess until the owner confirms (P-001).
- **Source:** [day log](2026-10/W3/2026-10-15.md) · T1
