"""Frozen experiment contract and atomic artifact utilities."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = Path('/home/david/dev/metodologia/skill/scripts')
sys.path.insert(0, str(SCRIPTS))

import bt_profiles
import bt_quota_live
import bt_subscriptions
import bt_usage

__all__ = [
    'INSTRUCTION',
    'ROOT',
    'ROUTES',
    'SCRIPTS',
    'bt_profiles',
    'bt_quota_live',
    'bt_subscriptions',
    'bt_usage',
    'cases',
    'digest',
    'file_map',
    'materialize',
    'save',
]

ROUTES = [
    {'id': f'luna-{effort}', 'provider': 'codex', 'profile': 'codex-2',
     'model': 'gpt-6-luna', 'effort': effort}
    for effort in ('medium', 'high', 'xhigh')
] + [
    {'id': 'sol-medium', 'provider': 'codex', 'profile': 'codex-2',
     'model': 'gpt-6.1-sol', 'effort': 'medium'}
] + [
    {'id': f'haiku-{effort}', 'provider': 'claude', 'profile': 'claude-work',
     'model': 'claude-haiku-5-5', 'effort': effort}
    for effort in ('medium', 'high', 'xhigh')
] + [
    {'id': 'sonnet-medium', 'provider': 'claude', 'profile': 'claude-work',
     'model': 'claude-sonnet-5-5', 'effort': 'medium'}
]

INSTRUCTION = '''You are the Implementer in a controlled software engineering pilot.
You are not alone on this machine. Your entire editable repository is /tmp/work.
Implement the task in app/ only, using the Python standard library. You may add
your own tests in app/. Do not change test_public.py or any file outside app/.
You may read local task files, edit code and run Python/unittest locally. Do not
use network, install packages, delegate, inspect accounts/configuration, access
parent directories, other repositories, experiment artifacts or hidden tests.
Follow the supplied public API and behavior exactly. Handle errors explicitly.
Keep code modular and readable. Test your change and report actual results.
There is no human response during a cell: resolve ordinary implementation choices
yourself within this contract. Do not ask for confirmation. Do not stop at a plan.
Public check: python -m unittest discover -s . -p 'test_public.py' -v
Return a short English summary of changes and tests; do not include private reasoning.

TASK:
'''


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_map(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): digest(p.read_bytes())
            for p in sorted(root.rglob('*'))
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def materialize(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = root / name
        if target.is_absolute() and not target.is_relative_to(root):
            raise ValueError(f'Unsafe fixture path: {name}')
        if '..' in Path(name).parts:
            raise ValueError(f'Unsafe fixture path: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def cases() -> list[dict]:
    from fixtures_basic import CASES as basic
    from fixtures_durable import CASES as durable
    return basic + durable
