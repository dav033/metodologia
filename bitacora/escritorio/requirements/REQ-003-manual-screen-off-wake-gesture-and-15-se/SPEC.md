---
id: REQ-003
title: Manual screen-off wake gesture and 15-second idle timeout
status: planned
created: 2026-10-13
track: standard
---

# REQ-003 — Manual screen-off wake gesture and 15-second idle timeout

## Problem & goal
David wants a shorter idle screen-off choice and a deliberate wake gesture for manual panel shutdown, while preventing ordinary keyboard activity from waking the panel or reaching the focused application.

**Success looks like:** the Energy menu offers a 15-second idle timeout; manual screen-off ignores ordinary keyboard input and restores the panel only after three Super taps; automatic idle screen-off retains its existing wake behavior.

## Users / actors / stakeholders
- David, on the local Hyprland desktop.
- Hyprland keybindings, Hypridle, and the existing remote-display panel wrappers.

## Scope (in)
### US-1 (P1, Must) — Add a 15-second idle timeout
As David, I want to choose 15 seconds in Energy so that the panel can turn off sooner during inactivity.
**Acceptance:** The Energy menu adds exactly one new timeout preset, 15 seconds, stores `timeout = 15` in Hypridle configuration, and preserves all existing minute presets.

### US-2 (P1, Must) — Guard manual screen-off
As David, I want ordinary keys ignored while the panel is manually off and Super ×3 to wake it so accidental input cannot wake the screen or reach an application.
**Acceptance:** Manual screen-off consumes normal keyboard input. Three distinct taps of the existing Super launcher key within the chosen gesture window turn the panel on and restore normal input. A failed panel-off action must not leave input trapped; a failed panel-on attempt must remain retryable.

### US-3 (P1, Must) — Keep automatic wake behavior
As David, I want the existing idle timeout to keep waking normally so the new gesture applies only to manual screen-off.
**Acceptance:** When the panel was turned off by Hypridle, its current activity-driven resume behavior remains unchanged.

## Out of scope
- Changing the existing 15-minute default or the other timeout presets.
- Changing automatic idle wake behavior, suspension scheduling, profile controls, lid/stream behavior, or physical power-button policy.
- Activating or restarting Hyprland/Hypridle or actually turning the panel off during implementation.

## Requirements
- R1. When David selects the new timeout entry, the system shall persist a 15-second timeout in `hypridle.conf` and retain the existing minute choices.
- R2. When David selects manual screen-off, the system shall enter a dedicated input-guard state before turning off the physical panel through the existing wrapper.
- R3. While manual input-guard state is active, ordinary keyboard keys shall neither wake the panel, reach the focused application, nor trigger desktop shortcuts.
- R4. While manual input-guard state is active, three distinct taps of the existing left Super launcher key within 3 seconds shall turn on the physical panel and restore normal keyboard behavior.
- R5. If manual panel-off fails, the system shall clear the guard and restore the normal keymap. If panel-on fails, the guard shall remain active so the Super gesture can be retried.
- R6. When Hypridle turns the panel off automatically, normal activity-driven wake behavior shall remain unchanged.
- R7. The physical power button retains its current `logind` handling: a short press powers off the machine, including while manual screen-off is active.

## Edge cases & errors
- A fourth or held Super key must not be treated as additional taps; count separate press/release cycles.
- An incomplete Super sequence expires after 3 seconds and does not wake the panel.
- Failed wrapper commands must notify or otherwise leave an observable error and must not strand the input guard.
- A Hyprland config reload or session restart while manual guard is active must not leave a stale lock state that prevents future input.

## Constraints
- Preserve the existing `remote-headless` panel/stream/lid policy; do not duplicate low-level monitor commands.
- Integrate with the existing `modal.lua` wrapper, which marks many global bindings universal across submaps; an ordinary-key guard must suppress those actions too.
- Keep user-facing messages and comments in Spanish; use existing user-level tools and no root privileges.
- Do not trigger runtime reloads, profile changes, panel actions, or service restarts during implementation.

## Priorities & phases
- Must: the 15-second preset, manual input guard, Super ×3 wake, automatic wake unchanged.
- Must: isolated tests prove action routing and failure recovery without real panel or compositor changes.

## Timeline & dependencies
- Depends on the current Energy Rofi mode, `hypridle.conf`, existing screen wrappers, and Hyprland 0.56 Lua config.

## Assumptions
- “Super ×3” means three left-Super taps, matching the existing Super-alone launcher binding, released separately within 3 seconds.
- “Normal keys do nothing” applies while manual screen-off is active. Automatic timeout wake remains as it is today, consistent with “solo al manual”.
- Do not rebind or intercept the physical power button; its current short-press action is machine poweroff.

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
- 2026-10-13: David chose only the 15-second idle preset; retain existing minute choices.
- 2026-10-13: David chose Super ×3 only for manual screen-off; automatic timeout keeps existing wake behavior.
- 2026-10-13: While manual screen-off is active, ordinary keys must do nothing and Super ×3 is the wake gesture; the physical power button remains `logind` poweroff (confirmed effective state: `HandlePowerKey=poweroff`).
- 2026-10-13: David declined changing physical power-button behavior to wake the panel; preserve the current machine-poweroff action.
