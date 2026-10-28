# Provenance

- Source: https://github.com/dbos-inc/agent-skills, path `skills/dbos-python`, commit
  `0bfe1ddab6b3f38b7925e4af8f10c41aed3ede96` (2026-10-28), MIT license (LICENSE copied alongside).
- Reviewed 2026-10-28 for REQ-030: Markdown only, no scripts or hooks; copied by hand instead of `npx skills add`.
- The skill text targets DBOS 3.4. This repository pins `dbos==3.3.0`, where `DBOS.patch` still requires
  `enable_patching=True` in the configuration (3.4 makes it implicit). `bt_durable` sets it explicitly.
