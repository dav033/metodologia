"""Control plane of the durable runtime: pure decisions (what is ready, what a failure is, what to do next).

Nothing here imports `dbos`; workflows call these functions with values loaded by steps, so the decisions are
deterministic on replay and can be tested without any database (test_durable_control_boundary enforces it)."""
