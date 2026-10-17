# Canonical fixture provenance

Generated for REQ-024 T4 on 2026-10-16 from the frozen T1 Planner V2 source snapshot.

- Repository HEAD recorded by T1: `196196ef427ab1f066d22faaeece2a40f8aa182c`.
- T1 snapshot SHA-256 for `bt_planner/contract.py`: `2ed0e93371ec68dcbe6bed5a3cc90ad49fad971e866a3bf12f1be88bfa80cbe2`.
- The working file had the same SHA-256 and `git diff -- skill/scripts/bt_planner/contract.py` was empty when these fixtures were generated.
- The 1.2.0 document is serialized by the pre-change 1.x reader to pin its current bytes; this does not claim that the old reader validates the proposed 1.2.0 semantics.
- `test_contract_golden.py` pins the input and canonical-output hashes for each version and compares exact canonical bytes.
- Before the T6 contract edit, exact legacy validation reports were captured for the 1.0.0 and 1.1.0 inputs. `test_extensions.py` pins their SHA-256 values and compares both error and warning lists; the report fixtures are `validation-1.0.0.json` and `validation-1.1.0.json`.
