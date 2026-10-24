# Task F5-docs — Engine v2 closure documentation

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding; docs-only task, so no full-suite requirement beyond the
doc/static tests listed below). Your worktree is branch `ev2/F5-docs` from `ev2/close-F4` (`53b83af55`: main + all F4).
Authority: PROMPT.md §F5 item 2 and CONTRACT.md in `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/`.
Own ONLY these docs: `skill/references/modules.md`, `skill/references/plan-contract.md`, `skill/references/agents.md`,
`skill/references/subagents.md`, `skill/SKILL.md` (routing table only), `skill/references/third-party-notices.md`,
`README.md`. No code changes.

Make them truthful against the CODE as it is now (read the code; never document something not implemented):
- plan schema 1.3.0 is the default (functional subplans, composition gates, UI/Designer contracts, verification
  `environment`/`requires`/`authorization_needed`); 1.2.0 remains a loadable legacy revision;
- the eight agent roles including `designer` and the visual review axis; where each role's private skills live and how
  they are installed (`install_agents.py`, symlink-safe);
- module map: `bt_composition` (composition engine), M1 state schema 9 (subplan version facts, composition facts and
  holds, NEEDS_REVIEW holds, code-attempt accounting), M3 subplan lines/Designer gate, M5 reason-aware recovery, M6
  verification metadata/evidence identity, owner composition runtime (`bt_scheduler_owner_*`), trusted verification
  authority (operator files: env/`~/.config/flow/secrets.env` NAMES and `<bitacora>/<project>/verification-policy.json`,
  decision D-126), external research store in `bt_knowledge`, D-10 benchmark (`bt_engine_benchmark`);
- SKILL.md routing: add rows only where a new situation needs a reference (e.g. composition/subplan runs, verification
  policy, Designer); keep the table short; SKILL.md must stay concise;
- third-party-notices: every adapted upstream source keeps repository, path, commit SHA and licence (check nothing added
  by F2/F3 is missing).
Run: `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_agent_skills_static` and every doc/readme
consistency test you can find (`grep -l "README\|modules.md\|SKILL.md" skill/scripts/tests/test_*.py`), plus
`python -m unittest discover -s tests -p 'test_legacy_collection.py'` if docs are collected. Report what you verified.
