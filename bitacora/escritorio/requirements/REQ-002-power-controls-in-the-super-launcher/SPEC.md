---
id: REQ-002
title: Power controls in the Super launcher
status: done
---

# Goal
Control the existing power profiles and screen/suspend timers from a new Energy tab in the Rofi launcher opened with Super.

# Users
David, on the local Hyprland desktop.

# Scope
- Add an Energy script mode/tab to the existing Rofi launcher.
- Replace the launcher’s left illustration with a dashboard showing the current energy profile and CPU, RAM, root-disk, discrete GPU and integrated GPU status, sampled when the launcher opens.
- Expose all existing user-facing power profiles (`bajo`, `medio`, `alto`, `silencio`, `auto`) through `~/.local/bin/perfil`.
- Offer immediate physical-panel off/on using the existing `remote-headless` wrapper, preserving the virtual output used by remote desktop.
- Set hypridle idle screen timeout to 5, 10, 15, 20, 30, 45 or 60 minutes, or disable the timeout; persist this in the existing config and restart hypridle only when selected in the menu.
- Schedule suspend after a user-entered whole number from 1 to 10080 minutes, offer 15/30/60-minute shortcuts, and allow cancellation. Use a named transient user systemd timer and `systemctl suspend`.

# Out of scope
Changing profile definitions, changing the 15-minute default, continuously refreshing dashboard metrics while Rofi stays open, suspending automatically on idle, changing lid/stream behavior, restarting Hyprland, or activating/restarting services during development.

# Assumptions
- The accepted proposed values in chat are approved: timeout choices above, and custom-minute suspend plus shortcuts/cancel.
- `alto` displays its documented thermal caution (can exceed 95°C under load).
- Custom suspension is capped at 10080 minutes (7 days) to bound accidental long-lived timers.
- Selecting a timeout applies it immediately by restarting `hypridle.service`; this is an explicit user action in the Energy menu.
- The disabled-timeout choice is persisted in an XDG state marker and enforced by Hypridle's `condition_cmd`; numeric timeout choices are persisted in `hypridle.conf`.
- GPU details use `nvidia-smi` and the Intel DRM frequency files available on this machine; unavailable metrics display an explicit fallback.
- Screen-off uses the established headless-output flow and may fail if the lid/output state prevents reactivation; report errors visibly.

# Acceptance criteria
1. When Rofi opens from Super, an Energy tab appears alongside existing modes; existing launcher modes remain available, and the left dashboard replaces the illustration with a profile and CPU/RAM/disk/GPU snapshot.
2. Selecting each profile invokes the existing `perfil` wrapper with the matching profile; errors are surfaced.
3. Screen off/on actions invoke the existing `remote-headless` commands and do not bypass its stream/lid handling.
4. Each numeric timeout choice persists the corresponding seconds value in `hypridle.conf`; disabled state is persisted in XDG state and checked by the configured Hypridle condition; current 15-minute behavior remains until a choice is made.
5. A valid suspend duration from 1 to 10080 minutes schedules a named user timer; invalid values are rejected; a failed replacement keeps the previous schedule; cancel removes only this feature's timer.
6. The system snapshot contains live values or explicit fallbacks for all five resource categories; dynamic dashboard theme injection parses with Rofi.
7. Shell syntax, Rofi config parsing, timer command behavior in an isolated test, and launcher mode rendering are verified without actually switching profiles, turning off the panel, restarting hypridle, or suspending the machine.

# Clarifications
- 2026-10-12: David accepted the proposed Energy menu, timeout presets, and custom suspension duration with quick choices/cancellation.
- 2026-10-12: David requested replacing the launcher illustration with a system dashboard for the active energy profile, CPU, RAM, disk and graphics adapters; metrics are sampled on launcher open.
