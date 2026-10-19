from __future__ import annotations

import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path('/home/david/dev/metodologia')
SCRIPTS = ROOT / 'skill/scripts'
TESTS = SCRIPTS / 'tests'
sys.path[:0] = [str(SCRIPTS), str(TESTS)]

import bt_scheduler_quota_preflight as quota_module
import test_scheduler_decision_integration as integration

TEST_NAME = 'test_frozen_req017_dag_routes_by_fresh_account_quota_without_reserving'


def run_test(label: str) -> int:
    suite = unittest.TestSuite([integration.DecisionAssignmentIntegration(TEST_NAME)])
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    print(f'ISOLATION_LABEL={label}')
    print(f'ISOLATION_TESTS_RUN={result.testsRun}')
    print(f'ISOLATION_FAILURES={len(result.failures)}')
    print(f'ISOLATION_ERRORS={len(result.errors)}')
    return 0 if result.wasSuccessful() else 1


if sys.argv[1] == 'current':
    raise SystemExit(run_test('current quota module'))
if sys.argv[1] == 'head':
    source = subprocess.check_output(
        ['git', 'show', 'HEAD:skill/scripts/bt_scheduler_quota_preflight.py'],
        cwd=ROOT, text=True,
    )
    original_module = types.ModuleType('_quota_preflight_head_in_memory')
    original_module.__file__ = 'git show HEAD:skill/scripts/bt_scheduler_quota_preflight.py'
    exec(compile(source, original_module.__file__, 'exec'), original_module.__dict__)
    with patch.object(quota_module, 'refresh', original_module.refresh):
        raise SystemExit(run_test('HEAD quota refresh patched into memory'))
raise SystemExit('expected current or head')
