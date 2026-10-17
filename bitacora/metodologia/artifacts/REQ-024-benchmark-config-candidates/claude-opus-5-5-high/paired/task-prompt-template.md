# REQ-024 matched-arm task prompt template

Plan the request in `{{INPUT_REQUEST}}` against the repository snapshot at `{{REPOSITORY_ROOT}}`. Write only the requested planning artifacts under `{{OUTPUT_DIRECTORY}}`. Do not read expected outputs, oracle candidates, or other benchmark cells. Do not use network or shell commands. The harness captures the written artifacts and performs `bt_planner check` and `bt_planner report` after the session; do not claim those checks passed. Return a concise list of artifacts created and unresolved assumptions.
