"""Canonical typed contracts (Pydantic v2) for the data that crosses component boundaries (REQ-030 M1).

One model per contract is the source of truth; JSON Schema is generated from it (`bt_contracts.schemas`) and the
remote TypeScript types are checked against the generated schema. Legacy stdlib code keeps its own readers; tests
validate what those producers emit against these models. Importing this package needs the uv-managed environment
(pydantic); the hook and bitácora CLI paths must never import it.
"""
