---
id: REQ-001
status: done
created: 2026-10-11
track: standard
---
# REQ-001 — Administrar fondos de pantalla desde Super+B

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The current Super+B selector lets David preview and choose wallpapers, but managing the collection and its automatic rotation requires separate tools/configuration. Add those controls in the selector.

**Success looks like:** David can remove a wallpaper, enable or pause automatic rotation, and choose its interval without leaving Super+B; adding a new image continues to apply it automatically.

## Users / actors / stakeholders
- David, the sole desktop user.

## Scope (in)
### US-1 (P1, Must) — Manage wallpapers in the selector
As David, I want to remove the highlighted wallpaper from the Super+B selector so that I can curate the collection there.
**Acceptance:**
- Given a wallpaper is highlighted, when David chooses delete, then the selector immediately moves that image to the desktop trash without another prompt.
- Given deletion succeeds, then the image disappears from the selector and cannot be selected for future rotation.
- After deletion, keep the selector at the deleted image's list position (the next image now in that slot, or the previous last image) so David can continue cleaning without jumping to the active desktop wallpaper.
- Given deletion fails, then the image remains in the collection and the selector reports the outcome.

### US-2 (P1, Must) — Configure automatic rotation
As David, I want to pause or enable rotation and choose how often it changes so that the desktop behaves on my schedule.
**Acceptance:**
- Given the selector is open, when David toggles automatic rotation, then the choice is saved and reflected in the user timer.
- Given rotation is enabled, when David selects 15, 30, 60, or 120 minutes, then the timer uses that interval and retains it across sessions.
- Given rotation is disabled, then no automatic rotation occurs; manual selection and the existing automatic application of newly added images continue to work.
- The initial enabled state and interval remain enabled and 30 minutes, matching the current setup.

### US-3 (P1, Must) — Preserve existing selection and add flow
As David, I want the current preview/selection flow and automatic application of new images to keep working while I manage rotation.
**Acceptance:**
- Given David opens Super+B, the existing preview, accept, and cancel behavior remains available.
- Given a new supported image is added to `~/Fondos`, the existing path watcher still applies it automatically regardless of the rotation toggle.

### US-4 (P1, Must) — Navigate Firefox tabs with Alt+1/Alt+2
As David, I want Alt+1 to advance to the next Firefox tab and Alt+2 to return to the previous tab so that I can reuse my former browser shortcuts.
**Acceptance:**
- Given a Firefox window is the shortcut target, when David presses Alt+1, then Firefox selects the next tab.
- Given a Firefox window is the shortcut target, when David presses Alt+2, then Firefox selects the previous tab.
- Given another application is active, when David presses either shortcut, then the shortcut is not sent to that application.

## Out of scope
- Changing which image formats or directories qualify for rotation.
- Changing automatic day/night selection, visual theme generation, or shortcuts other than the requested Firefox tab shortcuts.
- Arbitrary/custom rotation intervals beyond 15, 30, 60, and 120 minutes.

## Requirements
- R1. When David opens the selector with Super+B, the system shall show wallpaper management and rotation controls in that selector.
- R2. When David requests deletion of the highlighted wallpaper, the system shall immediately move only that image from `~/Fondos` to the desktop trash without a confirmation prompt.
- R3. When deletion succeeds, the system shall refresh the selector and ensure a deleted active wallpaper is not left recorded as the current image.
- R4. When David changes the rotation toggle or interval, the system shall persist the setting and apply it to the user-level rotation timer.
- R5. When rotation is disabled, the system shall not change wallpapers on the scheduled timer.
- R6. When a supported image is added to `~/Fondos`, the existing automatic-new-image behavior shall continue regardless of scheduled rotation state.
- R7. The selector shall retain its existing preview, accept, cancel, and keyboard navigation behavior.
- R8. When David presses Alt+1 or Alt+2 while Firefox is focused, Hyprland shall send Ctrl+Tab or Ctrl+Shift+Tab to that active window; when another application is focused, it shall not send either shortcut.

## Edge cases & errors
- The collection is empty after deletion: show the empty-state text and keep rotation enabled/disabled as configured.
- The selected image was the active wallpaper: the desktop may choose a replacement, but the selector keeps its list position instead of jumping to that replacement.
- The selected image is the current wallpaper: after deletion, select another eligible image if one remains; otherwise clear the recorded current path and show the empty state.
- The file has disappeared or trashing fails: keep the UI consistent with the actual filesystem and report failure.
- Invalid or missing persisted preferences: use enabled with a 30-minute interval and report malformed configuration for diagnosis.
- A timer update fails: keep the prior persisted preference and show an error rather than claiming success.

## Constraints
- This is a personal Linux desktop configuration: Quickshell/QML, Bash, `awww`, `systemd --user`, and `gio trash`.
- Keep operations constrained to supported image files inside `~/Fondos`; preserve the `movil/` and portrait filters for selection/rotation.
- Reuse the existing Catppuccin Mocha palette and lila accent.
- Do not alter unrelated user configuration or the existing new-image watcher.

## Priorities & phases
- Must: direct-to-trash deletion, enable/disable rotation, interval choices, preserve existing flows.
- MVP: all controls inside the current Super+B selector.

## Timeline & dependencies
- No external dependencies or deadline. Plan approval was received and implementation completed on 2026-10-11.

## Assumptions
- Deletion means immediately moving the chosen image to the desktop trash, so it is recoverable without an extra prompt.
- The rotation choices are 15, 30, 60, and 120 minutes; 30 minutes remains the initial default.
- Deleting the active wallpaper immediately selects another eligible image; if none remains, the current-path state is cleared.
- Newly added images continue to become the current wallpaper even when scheduled rotation is paused, matching the existing behavior David asked to preserve.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
### Round 1 — 2026-10-11
- Q: Delete from the selector? → A: Yes; initially confirmation was requested, then David changed this to immediate deletion without a prompt.
- Q: Add controls to enable/disable rotation and choose an interval? → A: Yes; keep 30 minutes as the default.
- Q: Preserve automatic application when an image is added? → A: Yes.
- Q: Which browser should receive the Alt+1/Alt+2 tab navigation shortcuts? → A: Firefox.
