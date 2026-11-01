# T3.15 audit command notes

Audited commit: `3485dbb346b00b3968b3b950161198daa8581b40`.

- `git status --short --untracked-files=all`: clean.
- `git diff HEAD^ HEAD --name-status | wc -l`: 6,634 changed paths. The summary reports 6,631 deletions and 1,513,720 removed lines.
- `git cat-file -e HEAD:docs/req021/aprobacion-backing-mesas.json`: exit 128, path absent.
- `git cat-file -e HEAD:src/lib/globos3d`: exit 128, path absent.
- `git cat-file -e HEAD:src/lib/taller`: exit 128, path absent.
- `git show HEAD^:docs/req021/propuesta-backing-mesas.json | sha256sum`: `382e02dfc1d2afa57daae1164a59c960aaf80ba7836421a1182a12ab1ba6d476`; historical parent approval has the same `propuestaSha256`.
- Required audit-ledger command result is appended after execution.

No secrets, credentials, environment values, or application logs were recorded.
- `/usr/bin/python3 /home/david/dev/metodologia/skill/scripts/bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json`: exit 0, `OK: audit ledger contract is valid`. This validates ledger shape only; it does not clear F1.
