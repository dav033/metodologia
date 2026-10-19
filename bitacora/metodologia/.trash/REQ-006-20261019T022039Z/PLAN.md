---
status: review
---
# Plan — REQ-006 Automatic requirement-to-milestones flow with learning

## Tasks

### M1 — Hand-off with a risk gate and background execution (R1, R2, R3, R9)
- [ ] T1 — `bt_config.py`: machine config in `.state/config.json` (executor_display, approval limits, promotion threshold) + `bitacora.py config get|set` · repo: skill · covers: R9 · verify: `python3 -I -m unittest discover -s skill/scripts/tests -p "test_config.py"`
- [ ] T2 — `bt_handoff.py`: validate plan, compute the risk gate with reasons, `bitacora.py handoff REQ-NNN [--dry-run]` (approve + launch background, or set review and explain) · repo: skill · after: T1 · covers: R1, R2, R3 · verify: `python3 -I -m unittest discover -s skill/scripts/tests -p "test_handoff.py"`

### M2 — Milestone as the session unit (R4, R5, R10)
- [ ] T3 — Parse `### Mn — title` groups into task `milestone` field (RUN.json + sync_plan), no change without groups · repo: skill · after: T2 · covers: R4, R10 · verify: `python3 -I -m unittest discover -s skill/scripts/tests -p "test_milestones.py"`
- [ ] T4 — Supervisor: one session per milestone (prompt lists its pending tasks), settle each task, continue unfinished milestone next session; concurrency over disjoint repo sets · repo: skill · after: T3 · covers: R4, R5 · verify: `python3 -I -m unittest discover -s skill/scripts/tests`

### M3 — Learning with evidence (R6, R7, R8)
- [ ] T5 — `bt_learn.py`: store, scopes, evidence, promotion, secret refusal, `bitacora.py learn add|list|confirm|reject` · repo: skill · after: T1 · covers: R6 · verify: `python3 -I -m unittest discover -s skill/scripts/tests -p "test_learn.py"`
- [ ] T6 — Inject confirmed learnings + candidate count at session start; milestone prompt instructs proposing learnings and recording decisions · repo: skill · after: T4, T5 · covers: R7, R8 · verify: `python3 -I -m unittest discover -s skill/scripts/tests -p "test_learn.py"`

### M4 — Skill wiring, docs, decision and real-agent proof (R10)
- [ ] T7 — SKILL.md / requirements.md / execution.md: automatic sizing rules, handoff step, normal-session entry, learning duties; D-003 in DECISIONS.md · repo: skill · after: T6 · covers: R10 · verify: `python3 -I -m unittest discover -s skill/scripts/tests`
- [ ] T8 — Real-agent run (`ops_e2e_check.py` extended: two milestones, auto hand-off, learning proposed) · repo: skill · after: T7 · covers: R3, R4, R8 · verify: `python3 skill/scripts/ops_e2e_check.py`
