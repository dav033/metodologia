"""Validate planning structure only; never execute migration tasks."""
from pathlib import Path
import json
import re
import sys

root = Path('/home/david/dev/metodologia')
dossier = Path(__file__).resolve().parent.parent
registered = dossier.parent / 'requirements/REQ-007-engineering-workspace-migration-without'
sys.path.insert(0, str(root / 'skill/scripts'))
import bt_runstate

tasks = bt_runstate.parse_plan(registered / 'PLAN.md')
ids = {task['id'] for task in tasks}
position = {task['id']: i for i, task in enumerate(tasks)}
text = (registered / 'PLAN.md').read_text()
covered = set(re.findall(r'\bR\d+\b', ' '.join(re.findall(r'covers: ([^\n]+)', text))))
result = {
    'task_count': len(tasks),
    'milestones': bt_runstate.milestones(registered / 'PLAN.md'),
    'missing_dependencies': [(task['id'], dep) for task in tasks for dep in task['after'] if dep not in ids],
    'nonprior_dependencies': [(task['id'], dep) for task in tasks for dep in task['after']
                              if position.get(dep, len(tasks)) >= position[task['id']]],
    'uncovered_requirements': sorted({f'R{i}' for i in range(1, 14)} - covered),
    'all_tasks_unchecked': all(not task['done'] for task in tasks),
    'spec_copy_equal': (dossier / 'SPEC.md').read_bytes() == (registered / 'SPEC.md').read_bytes(),
    'plan_copy_equal': (dossier / 'PLAN.md').read_bytes() == (registered / 'PLAN.md').read_bytes(),
}
print(json.dumps(result, indent=2))
if (result['missing_dependencies'] or result['nonprior_dependencies'] or result['uncovered_requirements']
        or not all(result[key] for key in ('all_tasks_unchecked', 'spec_copy_equal', 'plan_copy_equal'))):
    raise SystemExit(1)
