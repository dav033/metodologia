"""Pinned native Runner calls; preserve command evidence without private reasoning."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'implementer-pilot-20261017'
sys.path.insert(0, str(BASE))
from pilot_common import bt_subscriptions, digest, save
from pilot_native import environment, extract, quota, sanitize

__all__ = ['BASE', 'ROOT', 'ROUTES', 'bt_subscriptions', 'commands', 'digest', 'environment',
           'invoke', 'quota', 'save', 'wrapper']

ROUTES = [
    {'id': 'luna-high', 'provider': 'codex', 'profile': 'codex-luis', 'model': 'gpt-6-luna', 'effort': 'high'},
    {'id': 'luna-medium', 'provider': 'codex', 'profile': 'codex-luis', 'model': 'gpt-6-luna', 'effort': 'medium'},
    {'id': 'haiku-medium', 'provider': 'claude', 'profile': 'claude-work', 'model': 'claude-haiku-5-5', 'effort': 'medium'},
    {'id': 'sonnet-medium', 'provider': 'claude', 'profile': 'claude-work', 'model': 'claude-sonnet-5-5', 'effort': 'medium'},
]


def commands(route):
    if route['provider'] == 'codex':
        return ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--skip-git-repo-check', '--sandbox', 'workspace-write', '--model', route['model'],
                '-c', f'model_reasoning_effort="{route["effort"]}"', '-c', 'web_search="disabled"',
                '-c', 'approval_policy="never"', '--json', '-']
    allowed = 'Bash,Read,Grep,Glob'
    return ['claude', '--print', '--model', route['model'], '--effort', route['effort'],
            '--safe-mode', '--restricted', '--strict-mcp-config', '--tools', allowed,
            '--allowedTools', allowed, '--no-session-persistence', '--permission-mode', 'acceptEdits',
            '--permission-prompts', 'none', '--max-turns', '25', '--output-format', 'stream-json', '--verbose']


def wrapper(route, cwd, env):
    home = env.get('CODEX_HOME') if route['provider'] == 'codex' else env.get('CLAUDE_CONFIG_DIR')
    if not home:
        raise ValueError('Pinned profile home missing')
    return ['bwrap', '--ro-bind', '/', '/', '--tmpfs', str(ROOT.parent.resolve()),
            '--tmpfs', '/tmp', '--bind', str(cwd), '/tmp/work', '--bind', home, home,
            '--ro-bind', str(cwd / 'check.py'), '/tmp/work/check.py',
            '--ro-bind', str(cwd / 'TASK.md'), '/tmp/work/TASK.md',
            '--chdir', '/tmp/work', '--proc', '/proc', '--dev', '/dev',
            '--unshare-pid', '--die-with-parent', *commands(route)]


def evidence(stream):
    retained = []
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get('item')
        if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') in ('command_execution', 'file_change', 'mcp_tool_call'):
            retained.append({k: sanitize(str(item[k])) if isinstance(item[k], str) else item[k]
                             for k in ('type', 'command', 'exit_code', 'status', 'aggregated_output', 'changes') if k in item})
        message = event.get('message')
        if isinstance(message, dict):
            for block in message.get('content', []):
                if isinstance(block, dict) and block.get('type') in ('tool_use', 'tool_result'):
                    retained.append(json.loads(sanitize(json.dumps(block))))
    return retained


def invoke(route, cwd, prompt, deadline=300):
    env = environment(route)
    argv = wrapper(route, cwd, env)
    began = time.monotonic()
    process = subprocess.Popen(argv, cwd=cwd, env=env, text=True, start_new_session=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = process.communicate(prompt, timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    row = extract(route['provider'], stdout)
    row.update(exit_code=process.returncode, seconds=round(time.monotonic() - began, 3), argv=argv,
               tool_evidence=evidence(stdout), stderr_excerpt=sanitize(stderr[-1800:]),
               status='timeout' if timed_out else 'completed' if process.returncode == 0 else 'cli_error')
    if row['observed_models'] and row['observed_models'] != [route['model']]:
        row['status'] = 'model_identity_mismatch'
    if row['observed_efforts'] and row['observed_efforts'] != [route['effort']]:
        row['status'] = 'effort_identity_mismatch'
    if row['provider_errors'] and row['status'] == 'completed':
        row['status'] = 'provider_error'
    if route['provider'] == 'claude' and row['native_result_status'] not in (None, 'success'):
        row['status'] = 'native_' + row['native_result_status']
    combined = '\n'.join([stderr, *row['provider_errors'], row['response_text']]).lower()
    row['limit_detected'] = any(s in combined for s in ('usage limit', 'rate limit', 'hit your limit', 'quota exceeded', 'out of credits'))
    return row
