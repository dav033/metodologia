"""Owner role policy integration: family quotas, pins, complex labels and recovery."""
from __future__ import annotations

import argparse
import io
import json
import tempfile
import time
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bt_agents
import bt_cli_planner
import bt_delegate
import bt_delegate_modes
import bt_role_policy
import bt_role_routing
import bt_subscriptions
import install_agents
from test_agents import AgentTests


class RoleRoutingTests(AgentTests):
    def setUp(self):
        super().setUp()
        self.pool = ['claude', 'codex-named']
        self.samples = {}
        for target, name, value in [(bt_subscriptions, 'load', lambda *a: self.samples),
                                     (bt_subscriptions, 'ensure_fresh', lambda *a, **k: None)]:
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def usage(self, profile, used):
        self.samples[bt_agents.account_key(profile)] = {
            'status': 'ok', 'observed_at': time.time(),
            'windows': {'five_hour': {'used_percent': used, 'resets_at': time.time() + 3600,
                                     'window_minutes': 300},
                        'seven_day': {'used_percent': 0, 'resets_at': time.time() + 7*86400,
                                      'window_minutes': 10080}}}

    def route(self, role='runner', **kwargs):
        return bt_agents.route('personal-project', {'pool': self.pool}, 0, role=role, **kwargs)

    def test_inverse_quota_imbalance_switches_family_and_exact_role_configuration(self):
        self.usage('claude', 90)
        self.usage('codex-named', 10)
        chosen = self.route()
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('codex', 'gpt-6-luna', 'high'))
        self.usage('claude', 10)
        self.usage('codex-named', 90)
        chosen = self.route()
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('claude', 'sonnet', 'low'))

    def test_equal_quota_uses_role_default_without_exploration_or_quality(self):
        with patch.object(bt_agents, '_stats', side_effect=AssertionError('history must not change role choice')):
            self.assertEqual(self.route('implementer')['agent'], 'claude')
            self.assertEqual(self.route('researcher')['agent'], 'codex')

    def test_design_routes_to_designer_without_reviewer_independence(self):
        chosen = bt_agents.route('personal-project', {'pool': self.pool}, 0, kind='design',
                                 avoid_providers={'claude'})
        self.assertEqual(chosen['role'], 'designer')
        self.assertEqual(chosen['agent'], 'claude')

    def test_the_designer_keeps_opus_while_it_has_quota_and_falls_back_to_terra(self):
        """D-151 (pictures REQ-021): quota-first ranking sent every design to Codex Sol while Opus had room; the owner
        wants Opus first whenever its account can run, and Codex Terra only when it cannot."""
        self.usage('claude', 60)
        self.usage('codex-named', 5)                          # Codex has more headroom, Opus still has quota
        chosen = self.route('designer')
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('claude', 'opus', 'high'))
        self.usage('claude', 95)                              # Opus near its limit: Terra, never Sol
        chosen = self.route('designer')
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('codex', 'gpt-6.1-terra', 'high'))

    def test_the_solver_keeps_opus_while_it_has_quota_and_falls_back_to_codex_sol(self):
        """REQ-031: the Solucionador is Claude Opus high, ranked like the Designer (owner order while quota allows)."""
        self.usage('claude', 60)
        self.usage('codex-named', 5)
        chosen = self.route('solver')
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('claude', 'opus', 'high'))
        self.usage('claude', 100)
        chosen = self.route('solver')
        self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), ('codex', 'gpt-6.1-sol', 'high'))

    def test_explicit_complexity_changes_explorer_and_reviewer_only_to_approved_models(self):
        normal = self.route('explorer', risk='high')
        complex_route = self.route('explorer', complexity='L')
        self.assertEqual(normal['model'], 'gpt-6-luna')
        self.assertEqual(complex_route['model'], 'gpt-6.1-sol')
        self.assertEqual(self.route('reviewer', complexity='L')['effort'], 'high')
        self.assertEqual(self.route('reviewer', risk='high')['effort'], 'medium')
        self.assertEqual(self.route('runner', complexity='L')['effort'], 'low')
        self.assertEqual(self.route('implementer', complexity='L')['model'], 'sonnet')
        self.assertEqual(self.route('planner', complexity='L')['model'], 'opus')

    def test_implementer_quota_selection_and_default_on_ties(self):
        for claude_used, codex_used, expected in (
            (20, 60, ('claude', 'sonnet', 'medium')),
            (60, 20, ('codex', 'gpt-6-luna', 'high')),
            (20, 20, ('claude', 'sonnet', 'medium')),
            (100, 20, ('codex', 'gpt-6-luna', 'high')),
            (20, 100, ('claude', 'sonnet', 'medium')),
        ):
            with self.subTest(claude=claude_used, codex=codex_used):
                self.usage('claude', claude_used)
                self.usage('codex-named', codex_used)
                chosen = self.route('implementer')
                self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), expected)

    def test_high_complexity_implementer_prefers_sonnet_medium_while_quota_allows(self):
        for label in ('L', 'high', 'high_complexity'):
            for claude_used, codex_used, expected in (
                (20, 60, ('claude', 'sonnet', 'medium')),
                (60, 20, ('claude', 'sonnet', 'medium')),
                (20, 20, ('claude', 'sonnet', 'medium')),
                (90, 20, ('codex', 'gpt-6-luna', 'high')),
                (100, 20, ('codex', 'gpt-6-luna', 'high')),
            ):
                with self.subTest(complexity=label, claude=claude_used, codex=codex_used):
                    self.usage('claude', claude_used)
                    self.usage('codex-named', codex_used)
                    chosen = self.route('implementer', complexity=label)
                    self.assertEqual((chosen['agent'], chosen['model'], chosen['effort']), expected)

    def test_account_within_a_family_is_chosen_by_its_own_quota_not_pool_order(self):
        import bt_profiles
        bt_profiles.add('codex-light', 'codex', {'CODEX_HOME': str(self.codexdir) + '-light'})
        self.usage('codex-named', 46)
        self.usage('codex-light', 17)
        rows, _ = bt_role_routing.candidates('personal-project', ['codex-named', 'codex-light'], 0, 'test', 'runner')
        self.assertEqual(rows[0]['profile'], 'codex-light')

    def test_recent_sessions_spread_a_plan_across_accounts_of_similar_quota(self):
        import bt_profiles
        bt_profiles.add('codex-b', 'codex', {'CODEX_HOME': str(self.codexdir) + '-b'})
        for profile in ('codex-named', 'codex-b'):
            self.usage(profile, 20)
        pool = ['codex-named', 'codex-b']
        served = []
        recent: dict[str, int] = {}
        for _ in range(6):
            with patch.object(bt_role_routing, 'recent_sessions', return_value=dict(recent)):
                rows, _ = bt_role_routing.candidates('personal-project', pool, 0, 'test', 'runner')
            served.append(rows[0]['profile'])
            recent[rows[0]['account']] = recent.get(rows[0]['account'], 0) + 1
        self.assertEqual(set(served), set(pool))
        self.assertLessEqual(abs(served.count('codex-named') - served.count('codex-b')), 1)

    def test_scheduler_sessions_in_executor_ledgers_count_as_load(self):
        import sqlite3

        ledger = bt_agents.STATE / 'executor' / 'run-1' / 'ledger.db'
        ledger.parent.mkdir(parents=True)
        with sqlite3.connect(ledger) as db:
            db.execute('CREATE TABLE attempts (route TEXT, created REAL, rejection TEXT)')
            now = time.time()
            route = json.dumps({'profile': 'codex-named', 'provider': 'codex'})
            db.executemany('INSERT INTO attempts VALUES (?,?,?)', [
                (route, now - 60, None), (route, now - 120, None),          # two sessions in the window
                (route, now - 60, '{"code":"x"}'),                          # rejected before it started: not load
                (route, now - 9 * 3600, None),                              # older than the quota window
            ])
        counts = bt_role_routing.recent_sessions(time.time())
        self.assertEqual(counts, {bt_agents.account_key('codex-named', 'codex'): 2})

    def test_load_never_overrides_a_blocked_or_exhausted_account(self):
        self.usage('claude', 10)
        self.usage('codex-named', 95)
        with patch.object(bt_role_routing, 'recent_sessions', return_value={bt_agents.account_key('claude'): 5}):
            self.assertEqual(self.route('implementer')['agent'], 'claude')

    def test_complexity_alternative_still_respects_quota_fallback(self):
        self.usage('claude', 90)
        self.usage('codex-named', 10)
        self.assertEqual(self.route('researcher', complexity='L')['agent'], 'codex')

    def test_work_only_accounts_and_aliases_cannot_bias_family(self):
        import bt_profiles
        bt_profiles.add('codex-alias', 'codex', {'CODEX_HOME': str(self.codexdir)})
        rows, _ = bt_role_routing.candidates('personal-project',
            ['claude-work', 'codex-named', 'codex-alias', 'claude'], 0, 'test', 'runner')
        self.assertEqual(len(rows), 2)
        self.assertNotIn('claude-work', [r['profile'] for r in rows])

    def test_cooldown_and_exhaustion_leave_only_the_approved_alternative(self):
        self.usage('codex-named', 100)
        self.assertEqual(self.route()['agent'], 'claude')
        bt_agents.quota_mark('claude', 'claude', time.time() + 200)
        with self.assertRaises(bt_agents.NoRoute):
            self.route()

    def test_independent_audit_and_busy_accounts_stay_priorities(self):
        self.usage('claude', 10)
        self.usage('codex-named', 70)
        self.assertEqual(self.route('reviewer', avoid_providers={'claude'})['agent'], 'codex')
        self.assertEqual(self.route(busy={bt_agents.account_key('claude')})['agent'], 'codex')

    def test_pinned_model_is_never_silently_replaced(self):
        chosen = bt_agents.route('personal-project', {'pool': self.pool, 'model': 'gpt-6-astra'}, 0, role='planner')
        self.assertEqual((chosen['agent'], chosen['model']), ('codex', 'gpt-6-astra'))
        fixed = bt_agents.route('personal-project', {'agent': 'codex', 'model': 'gpt-6-astra'}, 0, role='planner')
        self.assertEqual(fixed['model'], 'gpt-6-astra')

    def test_pinned_model_also_pins_the_approved_role_effort_across_failure_tiers(self):
        for agent, model, expected in [('claude', 'sonnet', 'medium'), ('codex', 'gpt-6-luna', 'high')]:
            for tier in range(3):
                chosen = bt_agents.route('personal-project', {'agent': agent, 'model': model, 'model_pinned': True},
                                         tier, role='implementer')
                self.assertEqual((chosen['model'], chosen['effort']), (model, expected))

    def test_failure_tier_does_not_replace_role_model_or_effort(self):
        low = self.route('implementer')
        high = bt_agents.route('personal-project', {'pool': self.pool}, 2, role='implementer',
                               avoid_providers={'claude'})
        self.assertEqual((low['model'], low['effort']), (high['model'], high['effort']))

    def test_planner_cli_without_pins_uses_quota_aware_role_selection(self):
        args = argparse.Namespace(profile=None, provider=None, model=None, effort=None, complexity='L',
                                  req=None, repo=[], timeout=30)
        result = SimpleNamespace(stderr='', response='prepared plan', returncode=0)
        with patch.object(bt_agents, 'pool_for', return_value=self.pool), \
                patch.object(bt_cli_planner, 'invoke', return_value=result) as invoke, \
                patch('sys.stdin', io.StringIO('Plan a bounded change')), redirect_stdout(io.StringIO()):
            code = bt_cli_planner.dispatch(args, 'personal-project', self.base, self.root)
        request = invoke.call_args.args[0]
        self.assertEqual(code, 0)
        self.assertEqual((request.provider, request.model, request.effort), ('claude', 'opus', 'high'))

    def test_pinned_delegation_role_defaults_precede_old_tiers_and_keep_complexity_alias(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(bt_delegate, 'DIR', Path(temporary) / 'delegations'):
            order = bt_delegate.create('personal-project', 'Locate a symbol', 'codex-named', None,
                Path(temporary), [], None, 2, None, None, tier=0, role='explorer', complexity='high_complexity')
            self.assertEqual((order['model'], order['effort'], order['complexity']), ('gpt-6.1-sol', 'medium', 'L'))
            order = bt_delegate.create('personal-project', 'Review a diff', 'claude', None,
                Path(temporary), [], None, 2, None, None, kind='audit', tier=2, role='reviewer')
            self.assertEqual((order['model'], order['effort']), ('sonnet', 'medium'))

    def test_pinned_retry_keeps_original_profile_provider_and_model(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(bt_delegate, 'DIR', Path(temporary) / 'delegations'):
            order = bt_delegate.create('personal-project', 'Execute checks', 'claude', None, Path(temporary),
                                       [], None, 2, None, None, role='runner')
            def outcome(d, current, cmd):
                self.assertEqual((current['profile'], current['model'], current['effort']), ('claude', 'sonnet', 'low'))
                return {'status': 'failed' if current['attempt'] == 1 else 'verified', 'summary': 'fixture'}
            with patch.object(bt_delegate, '_attempt', side_effect=outcome), \
                    patch.object(bt_delegate_modes, '_route', side_effect=AssertionError('pinned retry rerouted')):
                result = bt_delegate_modes.execute(order['id'], None, retries=1)
            self.assertEqual(result['status'], 'verified')
            self.assertEqual(len(result['attempts']), 2)

    def test_quota_recovery_uses_requested_effort_not_previous_provider_effort(self):
        order = {'project': 'personal-project', 'auto': True, 'role': 'runner', 'kind': 'test', 'tier': 0,
                 'agent': 'codex', 'profile': 'codex-named', 'model': 'gpt-6-luna', 'effort': 'high'}
        self.usage('codex-named', 100)
        with patch.object(bt_agents, 'pool_for', return_value=self.pool):
            chosen = bt_delegate._next_route(order)
        self.assertEqual((chosen['model'], chosen['effort']), ('sonnet', 'low'))

    def test_delegation_persists_role_and_explicit_complexity_and_loads_instructions(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(bt_delegate, 'DIR', Path(temporary) / 'delegations'), \
                patch.object(bt_agents, 'pool_for', return_value=self.pool):
            order = bt_delegate.create('personal-project', 'Execute the checks', None, None, Path(temporary),
                                       [], None, 2, None, None, role='runner', complexity='L')
            self.assertEqual((order['role'], order['model'], order['effort']), ('runner', 'sonnet', 'low'))
            saved = json.loads((bt_delegate.path_of(order['id']) / 'TASK.json').read_text())
            self.assertIsNone(saved['requested_effort'])
            self.assertIn('## Role: runner', bt_delegate._prompt(order, Path(temporary) / 'RESULT.json'))


class NativeRoleInstallTests(unittest.TestCase):
    def test_generated_native_roles_have_explicit_approved_model_and_effort(self):
        for role in bt_role_policy.ROLES:
            source = install_agents.SRC / f'{role}.md'
            meta, lines, body = install_agents.parse(source)
            for provider in ('claude', 'codex'):
                option = bt_role_policy.native_option(role, provider)
                if option is None:
                    continue
                with self.subTest(role=role, provider=provider):
                    if provider == 'codex':
                        rendered = tomllib.loads(install_agents.generated_codex(meta, body))
                        self.assertEqual((rendered['model'], rendered['model_reasoning_effort']), option)
                    else:
                        text = install_agents.generated_claude(meta, lines, body)
                        self.assertIn(f'model: {option[0]}\n', text)
                        self.assertIn(f'effort: {option[1]}\n', text)
