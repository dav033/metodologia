STATUS: DONE

SUMMARY:  
Subplan publication facts now bind to the accepted audit attempt and accepted member-task attempts.  
Rework and affected revisions make facts stale; gates wait with a reason, and READY or undispatched reserved gates are demoted.  
Unaffected rebases can rebind the same version, commit, and manifest; changed work requires the next version.  
Schema-4 facts without identity still load but are treated as stale. Changes committed on `ev2/F4-3`.

CHANGES:  
[ subplans.py ](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/subplans.py) — bind publications to accepted work, validate published composition members, support idempotent rebinds, and clarify candidate-ID errors.  
[ transitions.py ](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/transitions.py), [dispatch.py](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/dispatch.py), [reservation.py](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/reservation.py), [views.py](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/views.py) — recheck gate facts and expose stale or unpublished reasons.  
[model.py](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/model.py) — load old schema-4 facts compatibly.  
[test_subplans.py](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/tests/test_subplans.py) — cover stale facts, gate boundaries, rebinding, audit acceptance, and legacy facts.  
[README.md](/home/david/dev/.engine-v2-wt/F4-3/skill/scripts/bt_scheduler_core/README.md), [modules.md](/home/david/dev/.engine-v2-wt/F4-3/skill/references/modules.md) — document publication identity and rebind rules.

VERIFICATION:  
`python -m unittest discover -s bt_scheduler_core/tests` → 0 (57.6 s; 310 tests)  
`python -m unittest discover -s tests -p 'test_flow*.py'` → 0 (24.3 s; 18 tests)  
`python -m unittest test_scheduler_subplan_adapter` → 0 (0.3 s; 1 test)  
`git diff --check` → 0  
`python -m unittest discover -s tests` → 1 (~16 min; 2,415 tests, 15 failures, 6 skipped; all 15 failures match the RULES.md baseline, no additional failures)

COMMITS:  
`3260baef5d5c54a2f082c141f8e398a7595473c2 fix: bind subplan publications to accepted work`

PROVENANCE: None.

CONCERNS: The worktree is clean; the branch is ahead 3 and behind 3 of `origin/main`. I left history unchanged.