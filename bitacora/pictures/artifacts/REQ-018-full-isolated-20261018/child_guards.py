"""Process-local command guards for this owner-authorized isolated run.

These guard ordinary CLI invocations, not arbitrary filesystem syscalls. Source
tree/deletion verification remains mandatory before acceptance. No global config.
"""
from pathlib import Path


def install(root: Path) -> None:
    directory = root/'guard-bin'
    directory.mkdir(exist_ok=True)
    git = directory/'git'
    git.write_text('''#!/usr/bin/python3
import os,sys
allowed={'status','diff','log','show','rev-parse','ls-files','ls-tree','check-ignore','grep','describe','version','--version','help'}
args=sys.argv[1:]
i=0
while i<len(args) and args[i] in {'-C','--git-dir','--work-tree','-c'}:i+=2
command=args[i] if i<len(args) else ''
if command not in allowed:
    print('REQ-018: Git mutation blocked ('+command+')',file=sys.stderr);sys.exit(126)
os.execv('/usr/bin/git',['git',*args])
''')
    git.chmod(0o755)
    for name in ('rm', 'rmdir', 'unlink', 'shred'):
        command = directory/name
        command.write_text('#!/bin/sh\nprintf "%s\\n" "REQ-018: deletion commands prohibited; retain all files" >&2\nexit 126\n')
        command.chmod(0o755)
