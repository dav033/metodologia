# Concise communication, tool output and design interviews

Adapted for metodologia from the pinned sources below. Modified instructions are deliberate: existing language,
progress, approval and verification rules govern. These are local prompts, not dependencies on other skills.
Load the relevant section only; license texts are reference material, not agent instructions.

## Caveman: smaller answers, intact meaning

Source excerpts:

> Code blocks unchanged. Commands, paths, API names exact.

> A dropped negation costs more than every token saved. Clarity beats compression.

Use this reporting prompt:

```text
Lead with the result or current finding. Explain its cause or implication once. Give the next action only when
one remains. Remove greetings, repeated plans, filler and closing offers; retain the required Aye prefix.
Use natural Spanish and familiar technical terms. Keep commands, paths, identifiers, error text, quantities,
units, conditions and negations exact. Distinguish executed, failed, blocked and unverified checks.
Show relevant changed lines with enough context instead of dumping an existing file. Preserve useful comments.
For a question, authorization, ordered risky procedure or confused reader, use complete, unambiguous sentences.
Keep documentation durable and readable; do not apply a telegraphic voice to code, comments, specs or reports.
Meet the harness's progress-update rules. Never trade away evidence to make a response shorter.
```

Use ordinary concise prose by default. No permanent persona, invented abbreviations, arbitrary sentence limit,
extra mode announcements or claimed token-saving percentage. If the user asks for more detail, provide it.

## RTK: reduce noisy output without losing evidence

Source excerpts:

> Truncated results state their recovery path in their own output.

> `rtk proxy <cmd>` — run a command unfiltered, still tracked.

RTK is a CLI, not a prompt-only skill. Its availability and supported commands depend on the installed version.
In a POSIX shell, `command -v rtk` checks discovery; then inspect `rtk --version` and the relevant `--help`.
An existing hook may already wrap commands: do not add a second prefix. If hooks cannot be inspected, invoke
supported RTK commands explicitly without claiming transparent interception is active.

Useful candidates, subject to installed help and the task's permissions:

| Need | Candidate | When raw output matters |
|---|---|---|
| Repository overview | `rtk git status`, `rtk git log -n 10` | Exact machine-readable state |
| Large change overview | `rtk git diff` | Read the original diff before approving a change or patching from it |
| Test/build diagnostics | `rtk test <command>`, `rtk npm test`, `rtk cargo test` | Recover complete failures when condensed output is insufficient |
| Search or file overview | `rtk grep <pattern> <path>`, `rtk read <path>` | Contracts, instructions and code being changed need exact relevant text |
| Output recovery | `rtk recall <id>` if advertised; an emitted saved-output path | Read the existing record first; a missing record is not permission to re-execute |

Use this command-selection prompt:

```text
Choose the smallest relevant inspection before running a command. If RTK is available and supports this command,
use its filter when output would be noisy; otherwise use the native tool. Preserve argv boundaries, working
directory, environment and the observed process exit code. RTK does not grant permission for the underlying action.
Treat condensed output as a summary, not proof that omitted lines are irrelevant. A nonzero exit remains failure.
When diagnostics are missing, contradictory or truncated, read the emitted recovery record with the supported
recall command or saved path. If no usable record exists, use the raw result from the tool or an unfiltered
execution only when repeating the underlying operation is safe and already authorized. Never rerun a migration,
deploy, payment or other side effect merely to recover its output. Report unavailable evidence honestly.
If you manually filter output, retain failures and totals and preserve the original command's exit status;
do not replace it with the successful status of head, tail, grep or another filter.
```

Do not prefix every command blindly or filter all instruction files. Do not install RTK, run `rtk init`, edit
global hooks/configuration, start proxies or enable telemetry as a consequence of this guidance. Those actions
require their own authorization. Existing native tools and the `runner` role remain usable without RTK.
`rtk gain` reports RTK's estimates for command output; it does not establish total billing savings.

RTK belongs to this framework as an optional executable, not another installed skill. The repository owns its
pinned installer: `python <repo>/install.py --rtk-only` installs the measured Linux x86_64 build without running
the rest of setup; `--with-rtk` includes it in a deliberately requested full setup. Neither path calls `rtk init`.
See the repository README's RTK section for the reproducible benchmark. Local measurements favored verbose
test output and Git history; already-quiet tests saved less, and a small diff barely benefited. Prefer native
targeted output when it is already sufficient. Full recovery of a failed test log can consume the initial saving;
request relevant saved lines with `rtk recall --grep`/`--from`/`--lines` when supported, keeping exact evidence
accessible.

The scheduler applies this guidance through `prompts.rtk` and `prompts.concise` (both default on).
RTK guidance appears only when PATH discovery succeeds; verification commands and M6 output are always RAW.
Concise retry history compares exact failure text, keeps all distinct failures and the first/latest full text of repeats.
Prompt line budgets reduce repeated lines with counts, never unique evidence; structured audit observations and manual-review verdict evidence are not condensed. Older history records may already be truncated; new records retain full text.
Turning either setting off restores its legacy prompt behavior; neither setting installs tools or changes verification.

## Grill Me: investigate facts, interview decisions

Source excerpts:

> Word each question so "yes" accepts your recommended answer.

> Finding _facts_ is your job, never the user's.

Use this design-review prompt with [requirements.md](requirements.md) §4:

```text
Map the unresolved decisions and their dependencies. Investigate facts from available files/tools yourself.
Ask the current frontier: only questions whose prerequisites are settled. Number them, recommend an answer and
state the concrete trade-off. Word the recommendation so yes accepts it. Keep dependent questions for later.
After each answer, update the tree instead of repeating a fixed questionnaire. Challenge assumptions that could
change scope, cost, correctness or verification; do not challenge settled choices just to prolong the interview.
Finish with decided branches, explicit deferrals and assumptions. Honor the user's request to proceed and the
existing Quick track. Confirm the resulting understanding through the normal plan approval, without a new gate.
```

Upstream `grill-me` delegates to `grilling`; metodologia embeds the useful behavior directly. Current upstream
uses frontier rounds, so keep metodologia's existing rounds instead of introducing a competing one-question flow.

## Sources and license boundary

Selected excerpts above are copied; surrounding prompts are adapted and modified for David's methodology.
No upstream binaries, runtime code, hooks or installers are included. Retained notices and full applicable
license texts: [third-party-notices.md](third-party-notices.md).

| Project | Pinned revision | Source files | Applicable license |
|---|---|---|---|
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | `2e08b9177c07bb7249a8a2d1a6758e5db281d002` | [Caveman skill](https://github.com/JuliusBrussee/caveman/blob/2e08b9177c07bb7249a8a2d1a6758e5db281d002/plugins/caveman/skills/caveman/SKILL.md), [licensing](https://github.com/JuliusBrussee/caveman/blob/2e08b9177c07bb7249a8a2d1a6758e5db281d002/LICENSING.md) | Apache-2.0; retained legacy MIT notice |
| [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | `311ebcbfd8efdb09b03219e7615a153b5b5e3c97` | [Awareness prompt](https://github.com/rtk-ai/rtk/blob/311ebcbfd8efdb09b03219e7615a153b5b5e3c97/hooks/rtk-awareness-full.md), [usage and recovery](https://github.com/rtk-ai/rtk/blob/311ebcbfd8efdb09b03219e7615a153b5b5e3c97/README.md) | Apache-2.0 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `49dd158d1076134a641b33efb035946536778336` | [Grill Me entrypoint](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/productivity/grill-me/SKILL.md), [grilling prompt](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/productivity/grilling/SKILL.md) | MIT |


## Clickable ids

`bitacora-web` resolves short links: `/go/<project>/REQ-005`, `/go/<project>/REQ-005/T4` (opens that task in the plan),
`/go/P-013`, `/go/D-045`, `/go/LG-001` (a bare id works when only one project has it; otherwise the page lists the
projects). In chat, write `[REQ-005](http://127.0.0.1:8765/go/metodologia/REQ-005)` so the terminal makes it clickable
(Claude Code renders markdown links as OSC 8 hyperlinks; check the port with `BITACORA_PORT`, default 8765). The
CLI (`pending`, `context`, `plan-status`) wraps ids in OSC 8 itself when stdout is an interactive terminal
(`BITACORA_LINKS=0` disables it, `=1` forces it). For ids in plain text that nobody linked, the kitty shortcut
`ctrl+shift+i` (`bt-go`) highlights every visible id and opens `/go/<id>`.
