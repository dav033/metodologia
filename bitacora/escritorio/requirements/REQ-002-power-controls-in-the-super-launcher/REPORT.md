# REQ-002 Report

## Built
- Added an Energy tab to the Super launcher for all five existing profiles, physical panel off/on, 5/10/15/20/30/45/60-minute idle timeout choices, and custom/15/30/60-minute suspension with cancellation.
- Replaced the left artwork with profile, CPU, RAM, root disk, NVIDIA RTX A3000, and Intel integrated graphics status sampled when Rofi opens.
- Preserved existing helpers and remote-display behavior. Timeout-disabled state and owned timer IDs are kept under XDG state.

## Verification evidence
- `bash -n` passed for the launcher and both new shell scripts.
- `rofi -dump-config` and `rofi -dump-theme` parsed; `rofi -help` detected the `energia` script mode.
- A mocked Rofi launch parsed the dynamic dashboard theme and included the current profile plus CPU/RAM/disk and both GPU panels.
- Mocked action tests confirmed all five profiles and both panel controls call existing wrappers and do not leak command output into Rofi rows.
- Isolated timeout/timer tests passed for setting 30/10 minutes, disabling/re-enabling via the condition, custom 37-minute scheduling, invalid zero rejection, failed timer creation preserving the previous schedule, stop failure retaining all owned timer IDs, cancellation retry, and `systemctl is-active` query failures preserving the timer manifest during both replacement and cancellation. Confirmed unknown units clear stale tracking. No real suspend or panel action was invoked.
- `estado-sistema.sh` median was 183 ms across five runs. `shellcheck` was unavailable.
- `hypridle.service` remains active; no daemon restart or profile change was triggered. The file retains `timeout = 900` (15 minutes) until the user selects a value in the menu.

## Rulings
- The Energy script is auto-discovered from Rofi's `scripts/` directory; local `rofi -help` and the user's screenshot confirm this mode is present.
- Numeric timeouts live in `hypridle.conf`; disabling the listener uses an XDG state marker checked by Hypridle's `condition_cmd`, avoiding a dangerous zero-second timeout.
- Suspension timers use feature-prefixed transient units and a state manifest; an unsuccessful replacement does not discard the previous unit, and cancellation retains the manifest when stopping fails or systemd status cannot be queried. Inactive/unknown units are only cleared after systemd responds.
- Metrics are a snapshot from launcher open, not continuous polling. Typed delays are capped at 7 days.

## Needs your eyes
- None; this is local desktop UI and shell glue using existing wrappers.

## Proposals
- None.

## Pending
- Reopen the launcher (close the already-open Rofi window, then press Super) to see the newly rendered dashboard; the current Rofi instance keeps the theme loaded from when it opened.

## Walkthrough
- Bare Super still invokes `lanzador.sh`, which now gathers one status snapshot before starting Rofi.
- `estado-sistema.sh` maps the active profile and samples `/proc`, `/`, NVIDIA SMI and Intel DRM frequency.
- `lanzador.sh` escapes those values for Pango/Rasi and injects them into the left dashboard textboxes.
- Rofi's Energy tab runs the auto-discovered `scripts/energia` script mode.
- Profile and panel changes go through the established user wrappers, preserving privileged policy and remote-display handling.
- A timeout choice edits only the single configured listener, writes the disabled marker if requested, and restarts `hypridle.service` as part of that explicit menu action.
- Suspension timers are transient systemd user units with a state manifest so replacement and cancellation target only this feature's schedules.
- Recheck the screen timeout if the `condition_cmd` config shape changes; missing NVIDIA/Intel metrics fall back to an explicit status.
