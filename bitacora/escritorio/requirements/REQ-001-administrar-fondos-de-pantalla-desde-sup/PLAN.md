---
req: REQ-001
status: done
created: 2026-10-11
---
# Plan — REQ-001 — Administrar fondos de pantalla desde Super+B

## Approach
Keep wallpaper and timer rules in the existing `fondo` command. Add validated persisted rotation preferences, safe trash-based removal, and timer reconfiguration there; keep QML as the selector UI that calls those commands. Configure the existing user timer through an app-owned drop-in, with the service checking the saved enabled flag before rotating.

## Global constraints
- Limit deletion to supported wallpaper files under `~/Fondos`; immediately move the selected image to `gio trash`.
- Keep the existing new-image watcher, day/night selection, preview/accept/cancel flow, and filters intact.
- Keep enabled + 30-minute rotation as the default; offer 15, 30, 60, and 120 minutes.
- Use the existing Catppuccin Mocha palette and mauve accent.
- Preserve unrelated local configuration and do not commit.

## Tasks
- [x] T1 — Add validated preferences, direct-to-trash removal, and timer configuration to `fondo` · files: `~/.local/bin/fondo`, `~/.config/systemd/user/fondo-rotar.service` · verify: `bash -n ~/.local/bin/fondo` and inspect state output · covers: R2, R3, R4, R5, R6
- [x] T2 — Add in-selector deletion and rotation controls, then refresh/handle current and empty states · files: `~/.config/quickshell/fondos/shell.qml` · after: T1 · verify: inspect the live selector; exercise delete/current/empty behavior through isolated `fondo` invocations · covers: R1, R2, R3, R4, R7
- [x] T2 follow-up — Keep the selector at the deleted item’s list position when its model and current-wallpaper state refresh, so cleanup can continue without moving focus to the desktop replacement.
- [x] T3 — Apply the chosen interval to the systemd user timer and verify it survives selector close/reopen · files: `~/.config/systemd/user/fondo-rotar.timer.d/interval.conf` · after: T1, T2 · verify: `systemctl --user cat fondo-rotar.timer` and inspect saved preferences · covers: R4, R5
- [x] T4 — Add Firefox-only Alt+1/Alt+2 tab navigation binds · files: `~/.config/hypr/atajos.lua` · verify: reload Hyprland and inspect the active bindings · covers: R8, US-4

## Verification
- `bash -n ~/.local/bin/fondo`.
- Run QML validation if `qmllint` is installed; otherwise report it unavailable.
- `bash -n ~/.local/bin/fondo`, `qmllint ~/.config/quickshell/fondos/shell.qml`, and `systemd-analyze --user verify` for the user timer/service all passed.
- The real Super+B selector rendered the rotation controls and direct-delete button; Escape closed it without changing the current wallpaper.
- Isolated filesystem checks verified direct-to-trash removal, replacement when the removed image was active, clearing the current path when the last image was removed, and rejecting a file outside `~/Fondos`.
- CLI checks selected each interval and both rotation states; the timer is active at 30 minutes and `fondo-nuevo.path` remains active. Current saved preference is paused at 30 minutes.
- Hyprland reloaded successfully and exposes both Alt bindings with the Firefox-focused callback. Temporary Firefox keypress checks did not produce a reliable end-to-end result; it remains a manual spot-check.
- Do not add or run automated test suites unless requested.

## Rulings
- Persist settings in a small app-owned config file with strict values, rather than treating QML or systemd as the source of truth — one owner for validation and predictable defaults; cost if wrong: low.
- Keep the timer installed and let the service skip rotation when disabled — avoids changing systemd enablement links while ensuring no scheduled wallpaper changes; cost if wrong: low.
- Move deleted images to desktop trash — satisfies removal while allowing recovery; cost if wrong: low.
- Delete immediately without a confirmation prompt — David changed this after approving the original plan; cost if wrong: low because the image remains recoverable from trash.
- Translate Alt+1/Alt+2 only when the focused window class contains `firefox`, then target `activewindow` — avoids changing a background Firefox window or another app; cost if wrong: low.

## Progress log
- 2026-10-11: Inspected existing selector, wallpaper command, and user units. Current rotation is enabled every 30 minutes; new images are applied by a separate active path watcher.
- 2026-10-11: Confirmed the requested deletion, rotation controls, and preservation of new-image behavior with David. Spec and plan are ready for approval.
- 2026-10-11 18:19 plan APPROVED (terminal)
- 2026-10-11: Implemented preference handling, trash removal, timer reconfiguration, selector controls, and focused-Firefox tab binds.
- 2026-10-11: First rapid interval loop hit systemd's timer start limit; added `reset-failed` before restart. Repeated interval/toggle checks then passed and the timer returned active.
- 2026-10-11: David changed deletion to immediate trashing without a prompt. No real wallpaper was deleted; delete behavior was verified in isolated temporary folders.
- 2026-10-11: Visual selector check and static/unit checks passed. Temporary Firefox keypress checks did not produce a reliable end-to-end result; active Hyprland bindings were reloaded and inspected. Follow-up spot-check is recorded in PENDING.
