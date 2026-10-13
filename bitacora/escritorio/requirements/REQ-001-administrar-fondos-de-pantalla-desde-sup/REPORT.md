# Report — REQ-001 — Administrar fondos de pantalla desde Super+B

## Built
- Added immediate, recoverable wallpaper removal from the Super+B selector. The highlighted image moves to desktop trash; deleting the active image chooses another eligible image or clears the saved path if none remain.
- After a successful delete, the selector keeps the deleted item's list position, even if the active desktop wallpaper changes; it selects the next image in that slot so cleanup can continue.
- Added persisted rotation pause/resume and 15, 30, 60, and 120-minute choices. `fondo` validates the settings and reconfigures the existing user timer. New-image auto-apply remains a separate active path watcher.
- Added Alt+1 (next tab) and Alt+2 (previous tab) in Hyprland. The callback sends Ctrl+Tab / Ctrl+Shift+Tab only when the focused window class contains `firefox`.

## Verification evidence
- `bash -n ~/.local/bin/fondo` — passed.
- `qmllint ~/.config/quickshell/fondos/shell.qml` — passed.
- `systemd-analyze --user verify ~/.config/systemd/user/fondo-rotar.timer ~/.config/systemd/user/fondo-rotar.service` — passed.
- Exercised each interval and both rotation states through the `fondo` command. Final configured interval is 30 minutes; current preference is paused. `fondo-rotar.timer` and `fondo-nuevo.path` are active.
- In isolated temporary folders, verified direct-to-trash deletion, replacement after deleting the active image, clearing the current path after deleting the last image, and rejection of `/etc/hosts`. No real wallpaper was deleted; temporary fixtures were cleaned.
- Opened Super+B on the desktop and inspected the controls. Escape closed the selector without changing the saved wallpaper.
- Reloaded Hyprland and confirmed both Alt bindings are active with Alt's modifier mask and the Firefox-focused Lua callback. Temporary Firefox keypress checks did not produce a reliable end-to-end result, so the final Alt+1/Alt+2 tab effect remains a manual spot-check.
- The first rapid interval loop hit systemd's start limit. Adding `systemctl --user reset-failed fondo-rotar.timer` before restarting fixed it; all subsequent interval/toggle checks passed.
- No automated test suite was added or run.

## Rulings
- Deletion is immediate at David's request and uses desktop trash so the file remains recoverable.
- Timer preferences use a strict app-owned config and a systemd timer drop-in. The timer stays enabled; its service skips scheduled changes when rotation is paused.
- The current live preference is paused at 30 minutes. This state was preserved at close.

## Needs your eyes
- During normal Firefox use, press Alt+1 and Alt+2 once to confirm next/previous tab behavior (P-001). The personal profile was not opened by the test flow.

## Proposals
- None.

## Pending
- P-001 — Manually spot-check the Firefox tab shortcuts.

## Walkthrough
1. Super+B opens `~/.config/quickshell/fondos/shell.qml`.
2. The selector reads `fondo estado` and `fondo listar` for the current image, rotation preference, and eligible wallpapers.
3. Delete sends the highlighted path to `fondo eliminar`; the CLI validates it is an eligible image under `~/Fondos`, then uses `gio trash`.
4. Rotation controls call `fondo configurar-rotacion`, which atomically writes preferences and the systemd interval drop-in, reloads systemd, and restarts the timer.
5. `fondo-rotar.service` calls `fondo rotar`; this exits without changing the image while paused. `fondo-nuevo.path` remains independent and still applies new images.
6. Hyprland's Alt+1/Alt+2 callbacks first inspect the focused window class; only Firefox gets Ctrl+Tab or Ctrl+Shift+Tab.
