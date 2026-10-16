# METH-4 — Show the PLAN.json quality summary where the plan is reviewed

The owner approves plans on the web review page and in the terminal but cannot see classification, critical path or
evidence gaps there; `bt_planner report` exists only as a module command. Show the summary in both places.

## Requirements
- R1. `bitacora.py plan-json report REQ-NNN` prints the summary through the adapter.
- R2. The web plan review page shows critical path, widest level and low-confidence tasks when PLAN.json exists.
- R3. Plans without PLAN.json render exactly as before.
