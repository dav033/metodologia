"""Pinned tool-free Claude reasoning boundary; worker providers are independent."""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from bt_orchestration_contract import ACTION_SCHEMA, byte_size, encode
from bt_orchestration_terminal import TerminalError, run_child

VERSION = '2.1.299'
HAIKU_MODEL = 'claude-haiku-5-5'


class ProviderError(TerminalError):
    """An unverified provider must never dispatch an action."""


class ProviderFailure(ProviderError):
    """A verified boundary reported provider failure/quota rather than an action."""


def executable() -> str:
    found = shutil.which('claude')
    if not found:
        raise ProviderError('REASONING_CAPACITY_UNAVAILABLE: verified Claude executable not available')
    return str(Path(found).resolve())


def check_capabilities() -> None:
    try:
        result = subprocess.run([executable(), '--version'], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProviderError('REASONING_CAPABILITY_UNAVAILABLE: version probe failed') from exc
    if result.returncode or result.stdout.strip().split()[:1] != [VERSION]:
        raise ProviderError(f'UNSUPPORTED_REASONING_VERSION: require Claude {VERSION}')


def parse_stream(text: str) -> tuple[str, dict]:
    if len(text.encode()) > 65536:
        raise ProviderError('OVERSIZED_REASONING_OUTPUT')
    try:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    except ValueError as exc:
        raise ProviderError('INVALID_REASONING_JSON') from exc
    if not rows or len(rows) > 64 or any(not isinstance(row, dict) for row in rows):
        raise ProviderError('INVALID_REASONING_EVENTS')
    inventories = [row for row in rows if row.get('type') == 'system' and row.get('subtype') == 'init']
    if len(inventories) != 1 or rows[0] is not inventories[0]:
        raise ProviderError('MISSING_REASONING_INVENTORY')
    inventory = inventories[0]
    if (inventory.get('claude_code_version') != VERSION or inventory.get('model') != HAIKU_MODEL
            or inventory.get('tools') != ['StructuredOutput']
            or any(inventory.get(field) != [] for field in ('mcp_servers', 'skills', 'slash_commands'))):
        raise ProviderError('UNSAFE_REASONING_INVENTORY: tool-free boundary required')
    session = inventory.get('session_id')
    if not isinstance(session, str) or not session or len(session) > 128:
        raise ProviderError('INVALID_PROVIDER_SESSION')
    for row in rows:
        if row.get('session_id', session) != session:
            raise ProviderError('MISMATCHED_PROVIDER_SESSION')
        if row.get('type') == 'assistant':
            message = row.get('message')
            if not isinstance(message, dict) or not isinstance(message.get('content'), list):
                raise ProviderError('INVALID_ASSISTANT_EVENT')
            for block in message['content']:
                if not isinstance(block, dict) or (block.get('type') == 'tool_use'
                                                   and block.get('name') != 'StructuredOutput'):
                    raise ProviderError('UNSAFE_REASONING_TOOL')
    results = [row for row in rows if row.get('type') == 'result']
    if len(results) != 1:
        raise ProviderError('REASONING_FAILED: no successful structured result')
    if results[0].get('is_error') is not False or results[0].get('subtype') != 'success':
        detail = results[0].get('result') or results[0].get('errors') or results[0].get('subtype')
        if byte_size(detail) > 4096:
            raise ProviderError('OVERSIZED_PROVIDER_FAILURE')
        raise ProviderFailure('REASONING_FAILED: ' + encode(detail))
    action = results[0].get('structured_output')
    if not isinstance(action, dict) or byte_size(action) > 4096:
        raise ProviderError('INVALID_STRUCTURED_ACTION')
    return session, action


def reason(package: dict, workdir: Path, environ: dict[str, str], route: dict,
           should_stop: Callable[[], bool], on_start: Callable | None = None,
           schema: dict | None = None, timeout: float = 120) -> tuple[dict, dict]:
    check_capabilities()
    argv = [executable(), '--print', '--safe-mode', '--tools', '', '--strict-mcp-config',
            '--disable-slash-commands', '--no-session-persistence', '--output-format', 'stream-json', '--verbose',
            '--model', route['model'], '--effort', 'medium', '--max-turns', '3',
            '--json-schema', encode(schema or ACTION_SCHEMA)]
    transport = run_child(argv, package, workdir, environ, timeout=timeout, output_bytes=65536,
                          input_bytes=package['policy']['entry_bytes'] + package['policy']['runtime_bytes'],
                          should_stop=should_stop, on_start=on_start)
    if transport['stopped'] or transport['timed_out'] or transport['overflow'] or transport['rc'] != 0:
        return transport, {}
    try:
        session, action = parse_stream(transport['text'])
    except ProviderFailure as exc:
        transport.update(rc=1, text=str(exc))
        return transport, {}
    transport['provider_session_id'] = session
    return transport, action
