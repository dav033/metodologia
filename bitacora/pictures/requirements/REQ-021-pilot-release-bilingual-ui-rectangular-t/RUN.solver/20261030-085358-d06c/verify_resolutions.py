"""Replay r26's immutable three conflicts using the real port, without live refs.

Without --reviewed this must fail with the original three conflicts.
With --reviewed it proves both merge orientations and exact reviewed contents.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path('/home/david/dev/pictures-wt/asesor')
sys.path.insert(0, '/home/david/dev/metodologia/skill/scripts')
from bt_composition_adapter import GitSubprocessPort


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reviewed', action='store_true')
    args = parser.parse_args()
    requests = [t['resolution'] for t in json.loads((HERE / 'triggers.json').read_text())]
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=True)
    reviewed = {}
    for r in requests:
        ours = git(REPO, 'cat-file', 'blob', r['blobs']['ours'])
        theirs = git(REPO, 'cat-file', 'blob', r['blobs']['theirs'])
        if r['path'].endswith('.tsx'):
            assert ours.replace('Volver a herramientas'.encode(), 'Volver al chat'.encode()) == theirs
        else:
            # Reviewed T7.4 refinement: default ambient identity remains; callers
            # recording returned usage may omit it to avoid duplicate billing rows.
            assert b'contextoUsoDeOperacion(input)' in ours
            assert b'...campoIdiomaChatTurn(input.idioma)' in ours
            assert b'omitirContextoUso: true' in ours
            helper = git(REPO, 'cat-file', 'blob', r['commits']['ours'] + ':src/lib/ia/nucleo/python-adapter/usage-context.ts')
            assert b'input.omitirContextoUso ? undefined : contextoUsoInternoActual()' in helper
            old_body = theirs[theirs.index(b'  const operationBodyWithoutUsage'):theirs.index(b'  try {', theirs.index(b'  const operationBodyWithoutUsage'))]
            assert old_body in ours, 'Keep signed usage envelope and body hashing unchanged'
        reviewed[r['path']] = ours
        if args.reviewed:
            (evidence / (r['key'] + '.resolved')).write_bytes(ours)
    commits = requests[0]['commits']
    assert all(r['commits'] == commits for r in requests)
    summary = {'commits': commits, 'orientations': []}
    with tempfile.TemporaryDirectory(prefix='solver-r26-replay-') as tmp:
        tmp = Path(tmp)
        clone = tmp / 'repo.git'
        subprocess.run(['git', 'clone', '--quiet', '--shared', '--bare', str(REPO), str(clone)], check=True)
        port = GitSubprocessPort(clone, tmp / 'workspaces')
        port.resolutions = evidence if args.reviewed else None
        port.request_resolutions = False
        for left, right in [('ours', 'theirs'), ('theirs', 'ours')]:
            result = port.merge_tree(commits['base'], commits[left], commits[right])
            item = {'left': left, 'right': right, 'tree': result.tree, 'conflicts': list(result.conflicts), 'blobs': {}}
            for r in requests:
                if r['path'] not in result.conflicts:
                    content = git(clone, 'cat-file', 'blob', result.tree + ':' + r['path'])
                    assert content == reviewed[r['path']], r['path']
                    item['blobs'][r['path']] = git(clone, 'rev-parse', '--verify', result.tree + ':' + r['path']).decode().strip()
            summary['orientations'].append(item)
            print(json.dumps(item))
        (evidence / ('resolved-replay.json' if args.reviewed else 'baseline-replay.json')).write_text(json.dumps(summary, indent=2) + '\n')
        assert all(not x['conflicts'] for x in summary['orientations']), 'Original r26 composition conflict reproduced'


if __name__ == '__main__':
    main()
