# Quota relay (interactive sessions)

When an interactive session's own 5 h window is nearly spent, the agent writes a handoff and stops, and the best
other account starts in the SAME terminal pane with the handoff as context. Marathon and delegated sessions are
never touched (any of `BITACORA_RUN/TASK/SESSION/DELEGATION` in the environment makes the hook a no-op); the
supervisor already handles limits there.

## How it works

1. Hook `bitacora.py hook relay` (UserPromptSubmit, PostToolUse, Stop). Reads the current profile's live 5 h reading
   (`bt_quota_live`, read-only, cached 120 s, never blocks more than 6 s, fails open). At or above the threshold it adds
   context telling the agent (Spanish) to finish the atomic step and run `bitacora.py relay handoff --session <id>` with a
   summary on stdin (`Next` section included). Re-warns at most every 10 min per session; urgent wording at >= 99 %
   or HTTP 429. `Stop` marks the end of the turn.
2. `relay handoff [--to PROFILE]` writes `~/bitacora/<project>/relay/RELAY-<ts>.md` (else `.state/relay/`): summary, cwd,
   branch, bounded `git status --short` and last commits, origin profile/session, a note that nothing was re-verified.
   The successor comes from the router (`bt_agents.candidates`): other account than the current one, `work_only` and
   cooling honoured, claude/codex only. It then spawns the detached helper `relay launch`.
3. `relay launch` validates the successor command, the multiplexer binary (kitty: `kitty @ ls`) and the pane BEFORE
   touching anything, then waits (max 10 min) for the Stop-hook marker `turn-ended-<session>`, which must be newer than
   the handoff file (handoff deletes any stale one). No marker (Stop hook not installed) means MANUAL: nothing is
   ever closed on a guess. It then ends the client with SIGTERM (then SIGINT) only if `relay.exit_current` is true and the pid was
   verified (name + start time), waits until it is gone, and types
   `cd '<cwd>' && env -u ... K='v' <bin> '<prompt>'` (valid in fish and bash; values with backslashes or control
   characters are refused). Once only per handoff (marker `.state/relay/launched/`), refuses a missing cwd.
4. `relay cancel` aborts the pending relaunch. Log: `.state/relay/relay.log`. Telemetry:
   `.state/events/relay-YYYY-MM.jsonl` (warned, handoff, launched, failed, manual, cancelled).

## Automatic handoff at the end of the turn (`relay.auto`)

The warning above asks the agent to write the summary. An agent can ignore it, so the `Stop` hook is a fallback: when
the turn ends, no handoff was written yet and the current profile is at or above the threshold, the hook writes the
handoff itself. The summary is built from the last user request and the last assistant answer in the transcript
(bounded, marked as data) plus the git state, and says it was generated and not verified. It then runs the same
successor and launcher machinery (one successor per session; supervised sessions are never touched). Switch it off with
`config set relay.auto false`; the cooperative warning still works. Telemetry event: `auto`.

## Primary path: the parent launcher (`relay_run.py`)

The wrappers generated with `bitacora.py profiles wrapper <profile> --relay` run the agent under
`scripts/relay_run.py <profile> -- <agent argv>`: the agent is a CHILD in the foreground (inherits the tty; SIGINT,
SIGTERM, SIGHUP, SIGWINCH are forwarded; the terminal is restored). It exports `METODOLOGIA_RELAY_WRAPPER=<launcher pid>`.
Nothing is ever typed, so it works the same locally and over ssh, with or without zellij/tmux/kitty.

1. `relay handoff` finds the client: its `/proc/<pid>/environ` names the launcher AND the client's ppid is that pid AND
   the launcher's command line is `relay_run.py`; both start times are pinned (a recycled pid fails). Claude Code hosts
   sessions in a daemon but the visible client is the launcher's child, so the proof holds over ssh.
2. `relay launch` validates the successor first (binary resolvable and absolute, cwd exists), writes
   `.state/relay/next-<launcher pid>.json` (0600, argv list + account selectors + cwd + `created`) BEFORE anything is
   signalled, waits for the Stop marker, re-verifies the proof, then SIGTERM (then SIGINT) to the client only.
   Any failure removes the file and falls to the multiplexer path, then to manual.
3. When the client exits the launcher takes the file (atomic rename; second reader finds nothing), requires owner-only
   mode, `created` < 15 min, not cancelled, absolute executable argv[0], existing cwd, and runs the successor as a list
   (never a shell string), only `CLAUDE_CONFIG_DIR`/`CODEX_HOME` overlaid. The successor runs under the same launcher;
   `relay.max_chain` (3) bounds the chain. No file: the launcher exits with the child's code.

`relay wrap-status [--dir D] [--apply]` lists which wrappers (claude, claude-work, codex…) already use the launcher and
prints the regeneration commands; dry run by default, `--apply` only rewrites wrappers generated by metodologia.

A `claude` started WITHOUT the wrapper, and sessions already open when the wrapper was installed, are not under a
launcher: they fall to the multiplexer path (zellij/tmux/kitty) or to manual.

## Finding the pane

Claude Code hosts sessions in a background daemon, so the session and its hooks carry no `ZELLIJ_PANE_ID` /
`TMUX_PANE` / `KITTY_WINDOW_ID`. Order: (1) those variables in the hook environment; (2) the attached client found
through `<config>/sessions/*.json` (`parkedJobId` of the client = `jobId` of the session), reading the CLIENT's
`/proc/<pid>/environ`; (1) requires the nearest agent ancestor to be a terminal client (tty, not a daemon/host helper, not under ssh).
There is no scan: a Claude session with no session record, or Codex outside a multiplexer, is MANUAL. Several candidates,
nested multiplexers (two variables set), an ssh ancestry, no multiplexer variable or a client not tied to the session means MANUAL:
nothing is typed or killed; the owner gets the exact command and a desktop notification.

zellij: `zellij action write-chars --pane-id terminal_N <cmd>` then `write --pane-id terminal_N 13`. tmux:
`send-keys -t %N -l <cmd>` then `Enter`. kitty: `kitty @ send-text --match id:N --stdin` then `\r`; needs, in
`kitty.conf` (never edited by the skill): `allow_remote_control yes` and `listen_on unix:/tmp/kitty`.

## Settings (`bitacora.py config set KEY VALUE`)

`relay.enabled` (false), `relay.threshold_percent` (92; 85 on David's machine), `relay.exit_current` (true: close the old client itself), `relay.max_chain` (3: successors one launcher may run), `relay.auto` (true: see below).

## Enable on this machine

Wrappers (`bitacora profiles wrapper <profile> --relay --dir ~/.local/share/metodologia/bin`) exist for
claude-personal, claude-work, codex-1 and codex-luis. `~/.config/fish/conf.d/61-relevo.fish` defines the fish
functions `claude`, `claude-work`, `codex1` and `codex-luis` so every interactive start (including the `agente`
launcher) runs under `relay_run.py`; `command claude` bypasses it. Relay hooks are in the settings of both Claude
accounts and in both Codex `hooks.json` files (Codex asks once to approve hooks with `/hooks`).

## Enable

1. `python3 <skill>/scripts/bitacora.py relay install --dry-run` prints the JSON; add it to each profile's
   `settings.json` (`~/.claude/settings.json`, `~/.claude-work/settings.json`) by hand, or merge it with
   `relay install --settings <file>` (idempotent, keeps a `.bak`):

```json
{"hooks": {
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 <skill>/scripts/bitacora.py hook relay", "timeout": 8}]}],
  "PostToolUse":      [{"hooks": [{"type": "command", "command": "python3 <skill>/scripts/bitacora.py hook relay", "timeout": 8}]}],
  "Stop":             [{"hooks": [{"type": "command", "command": "python3 <skill>/scripts/bitacora.py hook relay", "timeout": 8}]}]
}}
```

2. `bitacora.py config set relay.enabled true`.

## Limits

Needs the relay wrapper (primary) or zellij/tmux/kitty with remote control; the agent must cooperate (it is told by context, not forced);
the relay starts the successor with the default model of its profile; Codex: no hook is wired, run
`bitacora.py relay handoff` by hand. The Stop hook is REQUIRED for the automatic relaunch. After the old
client exits the helper waits one second and types; it cannot verify that the shell prompt is ready (a slow shell
start could swallow the first characters). Any failure after the client was closed falls back to MANUAL (log,
notification, exact command).

Pane proof: before closing anything the helper checks that the pane exists and belongs to the client. The client's own
environment must carry the same pane variable; tmux `display -p '#{pane_pid}'` must be the client or an ancestor; kitty
`@ ls` must list the window exactly once with the client in its foreground processes; zellij `action list-panes --json`
must list the pane (ownership there rests on the environment match; the JSON shape was not exercised against a live
zellij). A session record must match the client's /proc start time. A reading with an error status (HTTP 429 included)
is unknown, never a percentage.

Other rules: a newer handoff supersedes the pending one; one successor per session (marker `launched/session-<id>`);
session ids must match `^[\w.-]+$`; only ZELLIJ_SESSION_NAME / TMUX / KITTY_LISTEN_ON reach the helper from `--mux-env`; `relay handoff` and `relay launch` do nothing when `relay.enabled` is false or the session is supervised
(`relay handoff --force` only writes the file and prints the manual command, never schedules or closes anything);
`--to` refuses the account being left and cooling accounts; handoffs, state and log are owner-only (0600); the handoff
marks its content as untrusted data and fences it safely.
