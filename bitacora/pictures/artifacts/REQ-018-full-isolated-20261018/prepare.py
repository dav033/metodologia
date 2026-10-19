"""Prepare an isolated approved product run without hooks or Git commits."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from child_guards import install

from bt_planner import sync
from bt_scheduler_executor import handoff, gitutil
from bt_scheduler_executor.model import Workspace

ART = Path(__file__).resolve().parent
CANON = Path('/home/david/dev/pictures')
REQ = CANON.parent/'metodologia/bitacora/pictures/requirements/REQ-018-category-based-recommendations-of-assemb'


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def inventory():
    names = gitutil.run(CANON, ['ls-files', '-z', '--cached', '--others', '--exclude-standard'], binary=True).split(b'\0')
    result = {}
    for raw in names:
        if not raw:
            continue
        name = os.fsdecode(raw)
        if any(part.startswith('.env') and not part.endswith('.example') for part in Path(name).parts):
            raise RuntimeError('Unexpected nonignored environment file; refusing to copy')
        p = CANON/name
        if p.is_symlink():
            result[name] = {'link': os.readlink(p)}
        elif p.is_file():
            result[name] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mode': p.stat().st_mode & 0o777}
        else:
            result[name] = {'absent': True}
    return result


def main():
    ROOT = Path(tempfile.mkdtemp(prefix='req018-full-', dir='/home/david/bitacora/pictures/.state'))
    install(ROOT)
    before = inventory()
    save(ROOT/'canonical-inventory.json', before)
    save(ROOT/'canonical-git.json', {'head': gitutil.run(CANON, ['rev-parse', 'HEAD']),
         'status': gitutil.run(CANON, ['status', '--porcelain=v1']),
         'refs': gitutil.run(CANON, ['show-ref']), 'commits': gitutil.run(CANON, ['rev-list', '--all', '--count'])})
    repo = ROOT/'repository'
    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--no-hardlinks', '--no-checkout', str(CANON), str(repo)], check=True, capture_output=True)
    base = gitutil.run(repo, ['rev-parse', 'HEAD'])
    for name, info in before.items():
        if info.get('absent'):
            continue
        target = repo/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if 'link' in info:
            target.symlink_to(info['link'])
        else:
            shutil.copy2(CANON/name, target)
    gitutil.run(repo, ['read-tree', 'HEAD'])
    manifest = handoff.capture(Workspace(str(repo), '(detached)', base, str(repo)), ROOT/'baseline',
        dirname='baseline', attempt_id='baseline', when=time.time(), patch_max=32*1024*1024, mode='patch')
    save(ROOT/'baseline-manifest.json', manifest)
    prior = ART.parent/'REQ-018-T1-retry-20261018'
    hashes = json.loads((prior/'final-source-hashes.json').read_text())
    for name, digest in hashes.items():
        source = prior/'after'/name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
        target = repo/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    candidate = handoff.capture(Workspace(str(repo), '(detached)', base, str(repo)), ROOT/'candidate-t1',
        dirname='candidate-t1', attempt_id='candidate-t1', when=time.time(), patch_max=32*1024*1024, mode='patch')
    save(ROOT/'candidate-manifest.json', candidate)
    assert inventory() == before
    rdir = ROOT/REQ.name
    rdir.mkdir()
    for name in ('SPEC.md', 'PLAN.md', 'PLAN.json'):
        text = (REQ/name).read_text()
        if name == 'PLAN.md':
            text = text.replace('status: draft', 'status: approved', 1)
        if name == 'SPEC.md':
            text = text.replace('status: cancelled (2026-10-18, owner)', 'status: approved-isolated', 1)
        banner = ('\n\nExecution authorization: owner revoked REQ-018 cancellation for this isolated full product run. '
                  'Historical planning-only and cancellation notes are preserved below as history, superseded only for '
                  'this isolated run. No canonical integration, commits, commit-tree, push, merges, deployment or deletion.\n\n')
        if name != 'PLAN.json':
            split = text.find('---', 4) if text.startswith('---') else -1
            text = text[:split+3]+banner+text[split+3:] if split >= 0 else banner+text
        (rdir/name).write_text(text)
    result = sync.approve_freeze(rdir, repo_roots={'pictures': repo})
    save(ROOT/'freeze.json', result)
    save(ART/'runtime.json', {'root': str(ROOT), 'requirement': str(rdir), 'base_sha': base,
        'candidate_files_verified': hashes, 'canonical_inventory_count': len(before),
        'plan_semantically_equal_to_prior_t1': json.loads((REQ/'PLAN.json').read_text()) == json.loads((Path('/home/david/.local/tmp/req018-t1-retry-wbv54qd_')/REQ.name/'PLAN.json').read_text())})
    print(ROOT, flush=True)


if __name__ == '__main__':
    main()
