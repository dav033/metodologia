---
id: REQ-002
status: done
---

# Approach
Add the Energy Rofi script mode and replace the launcher artwork with a live system dashboard sampled at open. Keep profile and panel control behind existing wrappers; persist the timeout choice safely and manage only named suspension timers owned by this menu.

# Global constraints
- Spanish user-facing strings; keep existing Rofi theme and launcher behavior.
- Preserve all current local config and remote/lid/stream semantics.
- Do not push, commit, delete, or activate desktop/system state during implementation.
- Only modify the exact Rofi and user helper/config files needed; log in escritorio bitácora.

# Verification
- `bash -n` on new/changed shell scripts.
- Rofi `-dump-config` and `-dump-theme` parse the updated config and dynamic dashboard injection; `rofi -help` lists the auto-discovered `energia` script.
- Isolated mocked tests cover wrapper mappings, timeout persistence/disable gate, timer replacement/failure/cancellation, and invalid input without real system effects.
- Confirm `hypridle.service` remains active and no runtime restart, profile change, panel action, or suspend was triggered during implementation.

# Tasks
1. Implement the Energy Rofi tab with all existing profile and screen controls. — done
2. Persist timeout choices and safely schedule, replace, and cancel the feature-owned suspend timer. — done
3. Replace the left image with an escaped, live-on-open profile/resource dashboard for CPU, RAM, root disk, NVIDIA and Intel graphics. — done
4. Run shell, Rofi parsing, wrapper mapping, and isolated state/timer tests. — done

# Rulings
- Use existing helpers `perfil`, `remote-headless`, `remote-screen-on` rather than duplicate low-level policy — avoids bypassing thermal and remote-display behavior.
- Use a single named transient timer owned by this feature — scheduling a new delay replaces the prior one and cancellation cannot affect unrelated timers.
- Keep current timeout at 15 minutes until changed through the menu — avoids changing existing behavior.
- Store timeout-disabled state and owned timer names under XDG state; keep the numeric idle timeout in `hypridle.conf`.
- Sample dashboard metrics once when the launcher opens; measured helper median was 183 ms across five runs, avoiding polling while Rofi stays open.
- Bound typed suspend delays to 1–10080 minutes (7 days) and keep the prior schedule until the replacement has been created; retain all owned timer names if a stop operation fails.
- 2026-10-12 21:40 plan APPROVED (terminal)


# Progress log
- 2026-10-12: Implemented Energy mode and dashboard. `bash -n`, Rofi config/theme parsing, mode autodiscovery, dashboard injection, wrapper routing, and isolated timeout/timer failure-path tests passed. The live `hypridle` daemon was not restarted; it remains active with its current 900-second timeout until a menu timeout choice is made.
