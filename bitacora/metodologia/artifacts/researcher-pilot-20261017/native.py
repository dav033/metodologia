"""Pinned native research invocations; no routing, retries or raw reasoning logs."""
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
from pilot_native import environment, extract, quota, sanitize

__all__ = ['BASE', 'ROOT', 'ROUTES', 'commands', 'environment', 'invoke', 'quota', 'wrapper']

ROUTES = [
    {'id': 'sonnet-medium', 'provider': 'claude', 'profile': 'claude-work',
     'model': 'claude-sonnet-5-5', 'effort': 'medium'},
    {'id': 'sol-medium', 'provider': 'codex', 'profile': 'codex-2',
     'model': 'gpt-6.1-sol', 'effort': 'medium'},
    {'id': 'luna-high', 'provider': 'codex', 'profile': 'codex-2',
     'model': 'gpt-6-luna', 'effort': 'high'},
]


def commands(route, mode):
    if route['provider'] == 'codex':
        return ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--skip-git-repo-check', '--sandbox', 'workspace-write', '--model', route['model'],
                '-c', f'model_reasoning_effort="{route["effort"]}"',
                '-c', f'web_search="{"live" if mode == "live" else "disabled"}"',
                '-c', 'approval_policy="never"', '--json', '-']
    allowed = 'Read,Grep,Glob,Write' + (',WebSearch,WebFetch' if mode == 'live' else '')
    return ['claude', '--print', '--model', route['model'], '--effort', route['effort'],
            '--safe-mode', '--restricted', '--strict-mcp-config', '--tools', allowed,
            '--allowedTools', allowed, '--no-session-persistence', '--permission-mode', 'acceptEdits',
            '--permission-prompts', 'none', '--max-turns', '35',
            '--output-format', 'stream-json', '--verbose']


def wrapper(route, cwd, mode, env):
    home = env.get('CODEX_HOME') if route['provider'] == 'codex' else env.get('CLAUDE_CONFIG_DIR')
    if not home:
        raise ValueError('Explicit profile configuration directory is required')
    return ['bwrap', '--ro-bind', '/', '/', '--tmpfs', str(ROOT.parent.resolve()),
            '--tmpfs', '/tmp', '--bind', str(cwd), '/tmp/work', '--bind', home, home,
            '--chdir', '/tmp/work', '--proc', '/proc', '--dev', '/dev',
            '--unshare-pid', '--die-with-parent', *commands(route, mode)]


def evidence_events(stream):
    """Keep tool inputs/results, excluding assistant thinking and raw private streams."""
    calls, results = [], []
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get('item') or {}
        if (event.get('type') == 'item.completed' and isinstance(item, dict)
                and item.get('type') in ('web_search', 'mcp_tool_call')):
            calls.append({k: item[k] for k in ('type', 'status', 'action', 'query', 'queries', 'url', 'server', 'tool', 'arguments') if k in item})
        message = event.get('message') or {}
        if not isinstance(message, dict):
            continue
        for block in message.get('content', []):
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'tool_use':
                inp = block.get('input') or {}
                calls.append({'type': block.get('name'), 'id': block.get('id'),
                              'input': {k: str(inp[k])[:2500] for k in ('query', 'url', 'file_path', 'path', 'pattern') if k in inp}})
            if block.get('type') == 'tool_result':
                content = block.get('content', '')
                if isinstance(content, list):
                    content = '\n'.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text')
                if isinstance(content, str):
                    results.append({'tool_use_id': block.get('tool_use_id'), 'is_error': block.get('is_error', False),
                                    'text': sanitize(content[:18000])})
    return calls, results[:60]


def invoke(route, cwd, prompt, mode, deadline=600):
    env = environment(route)
    argv = wrapper(route, cwd, mode, env)
    began = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, text=True, start_new_session=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(prompt, timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    result = extract(route['provider'], stdout)
    calls, tool_results = evidence_events(stdout)
    result.update(exit_code=proc.returncode, seconds=round(time.monotonic() - began, 3),
                  argv=argv, stderr_excerpt=sanitize(stderr[-1800:]), research_tool_calls=calls,
                  tool_result_evidence=tool_results,
                  status='timeout' if timed_out else 'completed' if proc.returncode == 0 else 'cli_error')
    if result['observed_models'] and result['observed_models'] != [route['model']]:
        result['status'] = 'model_identity_mismatch'
    if result['observed_efforts'] and result['observed_efforts'] != [route['effort']]:
        result['status'] = 'effort_identity_mismatch'
    if result['provider_errors'] and result['status'] == 'completed':
        result['status'] = 'provider_error'
    if route['provider'] == 'claude' and result['native_result_status'] not in (None, 'success'):
        result['status'] = 'native_' + result['native_result_status']
    combined = '\n'.join([stderr, *result['provider_errors'], result['response_text']]).lower()
    result['limit_detected'] = any(v in combined for v in ('usage limit', 'rate limit', 'hit your limit', 'quota exceeded'))
    return result
