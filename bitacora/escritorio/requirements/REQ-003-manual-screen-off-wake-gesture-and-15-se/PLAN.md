---
id: REQ-003
status: review
---

# Approach
Add one 15-second idle preset while preserving the current minute choices. Manual panel-off will enter a dedicated Hyprland input-guard state: ordinary keyboard events are consumed, existing global shortcuts are suppressed while that state is active, and three distinct left-Super taps within 3 seconds invoke the existing panel-on wrapper. A short physical power-button press remains handled by logind as poweroff. Automatic idle-off keeps its normal activity-driven resume path; its callbacks will ignore activity only while the manual-off marker is active so it cannot bypass the manual gesture.

## Global constraints
- Preserve the existing `remote-headless` lid/stream/panel ownership and physical power-button handling.
- The screen-off guard applies only to manual screen-off; automatic timeout wake remains activity-driven.
- Reuse existing wrappers and use only user-level files/tools; no sudo, commit, push, runtime reload, service restart, panel action or power action during implementation.
- Keep user-facing strings and comments in the personal desktop configuration in Spanish; preserve unrelated local changes.
- Treat failed screen-off and screen-on separately: undo the guard if off fails; retain a retryable guard if wake fails.

## Verification
- Run `bash -n` on changed shell scripts, `luac -p` on changed Lua modules and `hyprland --verify-config` against the current config.
- Isolated tests with mocked Hyprland/system wrappers verify 15-second persistence and the manual guard lifecycle: ordinary keys suppressed, taps 1–2 do not wake, tap 3 does, failed off restores input, failed on remains retryable, and auto-resume is suppressed only during manual-off.
- Confirm the Energy menu exposes only the new 15-second timeout addition and retains all existing minute choices; verify the physical power key is not rebound or inhibited.
- Do not restart Hyprland/Hypridle or exercise actual panel/power controls during implementation.

## Tasks
1. Add the 15-second timeout option and correct the status message to display seconds for values below one minute; test persisted value and all existing presets. — covers R1
2. Implement manual-off state, input submap, suppression of universal keybindings, three-tap Super wake, and safe rollback/retry using the existing panel wrappers; keep Hypridle auto-wake unchanged outside manual mode and preserve logind poweroff. — covers R2–R7
3. Add isolated state and binding tests, validate Bash/Lua/Hyprland configuration, and review the changed call paths. — covers R1–R7

## Rulings
- Use the existing left Super key because it is the key already bound to launch Rofi when tapped alone.
- Three taps must be separate press/release cycles within 3 seconds; this keeps a held key from counting as multiple taps.
- Track manual-off state in the session runtime directory and restore the guard from that state on config reload. Clear or roll back state on action failure.
- Suppress the existing `modal.lua` universal bindings while manual-off is active; a submap alone would not be sufficient because global bindings are intentionally universal across submaps.
- Keep automatic Hypridle wake activity-driven outside manual-off. Its resume hook must not re-enable the panel while the manual-off marker is active.
- Do not alter `HandlePowerKey=poweroff`; during manual-off the hardware power button remains a poweroff action, not a panel wake gesture.

## Progress log
- 2026-10-13: Spec clarified with David: add only 15 seconds; Super ×3 applies only to manual off; ordinary keys do nothing in manual-off; preserve the physical power button's current poweroff action. Plan awaits approval.
