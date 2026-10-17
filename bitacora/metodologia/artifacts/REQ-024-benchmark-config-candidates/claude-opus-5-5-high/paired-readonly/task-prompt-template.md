# REQ-024 matched-arm task prompt template

Plan the request in `{{INPUT_REQUEST}}` against the repository snapshot at `{{REPOSITORY_ROOT}}`. Return exactly two labeled fenced blocks: `PLAN.md` and `PLAN.json`; include a `PLAN.mmd` block only if the Planner role's diagram skill says a diagram materially helps. The host captures these blocks into the output cell and runs the pinned `bt_planner check` and `bt_planner report` after the session. Do not run commands or claim validation passed. Do not inspect expected outputs, oracle candidates, or other benchmark cells.
