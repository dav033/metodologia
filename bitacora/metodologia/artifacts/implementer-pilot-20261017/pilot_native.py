"""Native CLI adapters; retain final artifacts/usage, never raw reasoning streams."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from pilot_common import ROOT, bt_profiles, bt_quota_live, bt_usage


def quota(route: dict) -> dict:
    return bt_quota_live.read_row(route['profile'], route['provider'], timeout=20)


def numeric(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    return {k: numeric(v) if isinstance(v, dict) else v
            for k, v in value.items() if isinstance(v, (int, float, dict)) and not isinstance(v, bool)}


def extract(provider: str, stream: str) -> dict:
    final_usage, partial, models, calls, messages = None, {}, set(), [], {}
    answer, result_status, errors, effort_reported = '', None, [], set()
    turns = 0
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if provider == 'codex':
            if event.get('type') == 'turn.completed':
                final_usage = numeric(event.get('usage'))
                turns += 1
            if event.get('type') in ('error', 'turn.failed'):
                errors.append(str(event.get('message') or event.get('error') or '')[:1000])
            item = event.get('item') or {}
            if not isinstance(item, dict) or event.get('type') != 'item.completed':
                continue
            if item.get('type') == 'agent_message':
                answer = item.get('text', '')
            if item.get('type') in ('command_execution', 'mcp_tool_call', 'web_search', 'file_change'):
                calls.append({'type': item['type'], 'command': str(item.get('command', ''))[:4000],
                              'exit_code': item.get('exit_code'), 'status': item.get('status')})
        else:
            msg = event.get('message') or {}
            if isinstance(msg, dict):
                if msg.get('model'):
                    models.add(msg['model'])
                if msg.get('id') and msg.get('usage'):
                    messages[msg['id']] = numeric(msg['usage'])
                for block in msg.get('content', []):
                    if not isinstance(block, dict) or block.get('type') != 'tool_use':
                        continue
                    inp = block.get('input') or {}
                    calls.append({'type': block.get('name'), 'id': block.get('id'),
                                  **{k: str(inp[k])[:4000] for k in ('command', 'file_path', 'path') if k in inp}})
            if event.get('type') == 'system' and event.get('subtype') == 'init':
                if event.get('model'):
                    models.add(event['model'])
                for key in ('effort', 'reasoning_effort'):
                    if event.get(key):
                        effort_reported.add(str(event[key]))
            if event.get('type') == 'result':
                final_usage = numeric(event.get('usage'))
                answer = event.get('result', '')
                result_status = event.get('subtype')
                turns = event.get('num_turns')
                if event.get('is_error'):
                    errors.extend(str(v)[:1000] for v in event.get('errors', []))
                    errors.append(str(answer)[:1000])
    for usage in messages.values():
        for key, value in usage.items():
            if isinstance(value, (int, float)):
                partial[key] = partial.get(key, 0) + value
    raw = final_usage if final_usage is not None else partial or None
    data = raw or {}
    mapped = {'input_tokens': data.get('input_tokens'), 'output_tokens': data.get('output_tokens'),
              'cache_read_tokens': data.get('cached_input_tokens') if provider == 'codex'
              else data.get('cache_read_input_tokens'),
              'cache_write_tokens': data.get('cache_creation_input_tokens'),
              'reasoning_tokens': data.get('reasoning_output_tokens'),
              'source': provider + '-stream-json',
              'quality': 'complete' if final_usage is not None else 'partial'}
    return {'response_text': answer, 'usage_reported': raw,
            'usage': bt_usage.normalize(mapped, provider), 'observed_models': sorted(models),
            'observed_efforts': sorted(effort_reported), 'tool_calls': calls,
            'native_result_status': result_status, 'turns': turns,
            'provider_errors': errors, 'has_final_usage_event': final_usage is not None}


def commands(route: dict) -> list[str]:
    if route['provider'] == 'codex':
        return ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--skip-git-repo-check', '--sandbox', 'workspace-write',
                '--model', route['model'], '-c', f'model_reasoning_effort="{route["effort"]}"',
                '-c', 'web_search="disabled"', '-c', 'approval_policy="never"', '--json', '-']
    tools = 'Read,Grep,Glob,Edit,Write,Bash'
    return ['claude', '--print', '--model', route['model'], '--effort', route['effort'],
            '--safe-mode', '--restricted', '--strict-mcp-config', '--tools', tools,
            '--allowedTools', tools, '--no-session-persistence', '--permission-mode', 'acceptEdits',
            '--permission-prompts', 'none', '--max-turns', '45',
            '--output-format', 'stream-json', '--verbose']


def environment(route: dict) -> dict:
    bt_profiles.authorize(route['profile'], 'metodologia')
    env = {k: v for k, v in os.environ.items()
           if k not in ('CLAUDECODE', 'CLAUDE_CONFIG_DIR', 'CODEX_HOME',
                        'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'PYTHONPATH', 'PYTHONHOME')
           and not k.startswith(('BITACORA_', 'CODEX_'))}
    env.update(bt_profiles.env_of(route['profile']))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def wrapped(route: dict, cwd: Path, env: dict) -> list[str]:
    profile_home = env.get('CODEX_HOME') if route['provider'] == 'codex' else env.get('CLAUDE_CONFIG_DIR')
    if not profile_home:
        raise ValueError('Pinned profile must identify its configuration directory')
    # Mask every benchmark oracle/reference and all sibling work directories.
    # Only CLI state and this cell are writable. Native child sandbox remains enabled.
    return ['bwrap', '--ro-bind', '/', '/', '--tmpfs', str(ROOT.parent.resolve()),
            '--tmpfs', '/tmp', '--bind', str(cwd), '/tmp/work',
            '--bind', profile_home, profile_home,
            '--chdir', '/tmp/work', '--proc', '/proc', '--dev', '/dev',
            '--unshare-pid', '--die-with-parent', *commands(route)]


def sanitize(text: str) -> str:
    return re.sub(r'(?i)(sk-[A-Za-z0-9_-]+|bearer\s+\S+)', '<redacted>', text)


def invoke(route: dict, cwd: Path, prompt: str, deadline: int = 1500) -> dict:
    env = environment(route)
    argv = wrapped(route, cwd, env)
    began = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(prompt, timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    result = extract(route['provider'], stdout)
    result.update(exit_code=proc.returncode, elapsed_seconds=round(time.monotonic() - began, 3),
                  status='timeout' if timed_out else 'completed' if proc.returncode == 0 else 'cli_error',
                  argv=argv, stderr_excerpt=sanitize(stderr[-1800:]))
    if result['observed_models'] and result['observed_models'] != [route['model']]:
        result['status'] = 'model_identity_mismatch'
    if result['observed_efforts'] and result['observed_efforts'] != [route['effort']]:
        result['status'] = 'effort_identity_mismatch'
    if result['provider_errors'] and result['status'] == 'completed':
        result['status'] = 'provider_error'
    if route['provider'] == 'claude' and result['native_result_status'] not in (None, 'success'):
        result['status'] = 'native_' + result['native_result_status']
    combined = '\n'.join([stderr, *result['provider_errors'], result['response_text']]).lower()
    result['limit_detected'] = any(s in combined for s in (
        'usage limit', 'rate limit', 'out of credits', 'hit your limit', 'quota exceeded'))
    return result
