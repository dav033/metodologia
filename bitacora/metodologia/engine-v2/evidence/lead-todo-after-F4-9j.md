- Executor README must document `PLAN_SCHEMA_CAPABILITIES` (added by lead 7061f3bde without running the executor module
  suite): test_readme.test_every_public_name_is_documented + test_isolation lone-copy fail on close-F4. Add after the
  value-types line (~README.md:52): "`PLAN_SCHEMA_CAPABILITIES` — plan schemas M3 consumes (1.0.0–1.3.0; 1.3.0 adds
  subplan integration lines, the Designer base-tree gate and the `composition_base` seam)." Then rerun executor suite.
- Rebuild close-F4 from origin/main + ev2/F4-9 + ev2/F4-8; root + 9 modules; push.
