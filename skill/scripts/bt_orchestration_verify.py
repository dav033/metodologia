"""Bounded verification output using the proven foreground process lifecycle."""
from __future__ import annotations

import os
from pathlib import Path

import bt_runstate as rs
from bt_orchestration_identity import track
from bt_orchestration_terminal import run_child


def run_check(command: str, cwd: Path, evidence: Path, project: str, rdir: Path, state: dict) -> tuple[bool, str]:
    if (rs.load(rdir) or {}).get('control') == 'stop':
        return False, 'VERIFY_STOPPED: no command dispatched'
    try:
        result = run_child(['/bin/sh', '-c', command], {}, cwd,
                           {**os.environ, 'BITACORA_PROJECT': project, 'BITACORA_RUN': state['req'],
                            'BITACORA_EXECUTION_POLICY': 'restricted-v1'},
                           timeout=600, output_bytes=65536, send_input=False,
                           should_stop=lambda: (rs.load(rdir) or {}).get('control') == 'stop',
                           on_start=lambda pid, instance: track(rdir, project, state, pid, instance))
    finally:
        track(rdir, project, state, None, None)
    if result['stopped']:
        rs.update(rdir, lambda current: current.update(control='stop'))
    # Append distinct checks (FINAL/audit), retaining the whole bounded evidence.
    if evidence.exists() and evidence.stat().st_size + len(result['text'].encode()) > 262144:
        return False, 'VERIFY_EVIDENCE_CAP: inspect ' + str(evidence)
    with evidence.open('a', encoding='utf-8') as stream:
        stream.write(command + '\n' + result['text'] + '\n')
    if result['overflow'] or result['timed_out'] or result['stopped']:
        code = 'VERIFY_OUTPUT_CAP' if result['overflow'] else 'VERIFY_TIMEOUT' if result['timed_out'] else 'VERIFY_STOPPED'
        return False, code + ': inspect ' + str(evidence)
    if result['rc'] == 0:
        return True, 'Verification passed; evidence: ' + str(evidence)
    detail = result['text']
    if len(detail.encode()) > 2000:
        return False, 'VERIFY_FAILED_LARGE_RESULT: full bounded evidence at ' + str(evidence)
    return False, detail
