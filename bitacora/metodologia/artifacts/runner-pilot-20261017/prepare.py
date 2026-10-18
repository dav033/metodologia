"""Deterministic Runner fixtures and predeclared semantic grading contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FIXTURE = '''import json
import sys
import time
from pathlib import Path

mode = sys.argv[1]
started = time.monotonic()
events = Path(".runner-events.jsonl")
def record(value):
    with events.open("a") as stream:
        stream.write(json.dumps(value) + "\\n")
record({"mode": mode, "event": "start", "at": started})
lines, code = [], 0
if mode == "success":
    lines = ["12 tests passed", "WARNING: deprecated option legacy_mode at config/options.py:18"]
elif mode == "misleading":
    lines, code = ["PASS: preflight only", "FAILED test_balance — AssertionError: expected 120, got 90 — tests/test_balance.py:42"], 3
elif mode == "repeated":
    lines = ["FAILED test_cache — AssertionError: stale cache — tests/test_cache.py:27"] * 14
    lines += ["FAILED test_auth — PermissionError: forbidden — tests/test_auth.py:61"]
    code = 1
elif mode == "long":
    lines = [f"INFO build step {i:04d}: processing deterministic asset bundle" for i in range(1800)]
    lines[847] = "ERROR TS2322: string is not assignable to number — src/price.ts:87"
    lines += ["INFO cleanup completed"]
    code = 1
elif mode == "hang":
    print("Waiting for worker; no completion yet", flush=True)
    time.sleep(60)
elif mode == "upstream":
    lines, code = ["ERROR: corrupt archive — build/archive.py:19"], 7
elif mode == "downstream":
    lines = ["5 tests passed"]
elif mode == "unavailable":
    lines, code = ["BLOCKED: missing declared dependency runner_optional_sdk; do not install packages"], 4
else:
    raise SystemExit(64)
Path("logs").mkdir(exist_ok=True)
body = "\\n".join(lines) + "\\n"
Path("logs/" + mode + ".log").write_text(body)
print(body, end="", flush=True)
record({"mode": mode, "event": "end", "exit": code, "seconds": time.monotonic() - started})
raise SystemExit(code)
'''

CASES = [
    {'id': 'N1', 'title': 'Success with warning', 'commands': ['python check.py success'],
     'modes': ['success'], 'exits': [0], 'status': 'PASS',
     'diagnostic': '12 tests passed; warning is not a failure', 'detail': 'legacy_mode warning at config/options.py:18'},
    {'id': 'N2', 'title': 'Misleading PASS on failed command', 'commands': ['python check.py misleading'],
     'modes': ['misleading'], 'exits': [3], 'status': 'FAIL',
     'diagnostic': 'test_balance expected120 got90', 'detail': 'tests/test_balance.py:42; preflight PASS does not mean command success'},
    {'id': 'N3', 'title': 'Repeated and distinct failures', 'commands': ['python check.py repeated'],
     'modes': ['repeated'], 'exits': [1], 'status': 'FAIL',
     'diagnostic': 'test_cache stale cache repeated14 times at tests/test_cache.py:27',
     'detail': 'test_auth forbidden at tests/test_auth.py:61'},
    {'id': 'N4', 'title': 'Failure buried in noisy output', 'commands': ['python check.py long'],
     'modes': ['long'], 'exits': [1], 'status': 'FAIL',
     'diagnostic': 'TS2322 string is not assignable to number', 'detail': 'src/price.ts:87; logs/long.log is the full output'},
    {'id': 'N5', 'title': 'Timeout and missing command entrypoint',
     'commands': ['timeout --signal=TERM --kill-after=1s 2s python check.py hang', 'python missing_runner_command.py'],
     'modes': ['hang'], 'exits': [124, 2], 'status': 'BLOCKED',
     'diagnostic': 'hang timed out after2 seconds; no tests completed', 'detail': 'missing_runner_command.py cannot start; missing file'},
    {'id': 'N6', 'title': 'Pipefail plus independent outcomes',
     'commands': ["bash -o pipefail -c 'python check.py upstream | cat'", 'python check.py downstream', 'python check.py unavailable'],
     'modes': ['upstream', 'downstream', 'unavailable'], 'exits': [7, 0, 4], 'status': 'FAIL',
     'diagnostic': 'corrupt archive at build/archive.py:19; downstream5 tests passed',
     'detail': 'runner_optional_sdk unavailable; report blocked check without installing'},
]

INSTRUCTION = '''You are the Runner in a controlled local pilot, not an Implementer.
Your workspace is /tmp/work. Run every listed command exactly once, even if an earlier
command fails; do not retry, fix, install packages, delegate, use network, or inspect
accounts, parent directories, other repositories, experiment artifacts or hidden data.
Do not edit any file or create scripts. The supplied commands may create their own logs
and instrumentation. Do not read or change .runner-events.jsonl (collector evidence).
Use shell/Read/Grep/Glob to execute and inspect output. The original complete outputs
are saved by check.py under logs/<mode>.log; inspect them if tool output is truncated.
Use a shell-tool timeout of at least 10 seconds. N5's explicit timeout bounds its hang.
Report actual process exit codes, not success words printed by a command. Retain the
meaning of diagnostics, paths and line numbers; collapse repeated failures with count.
If all commands pass, STATUS is PASS; failed assertions/builds make FAIL. If no failure
is established and checks cannot finish or start, STATUS is BLOCKED. Mixed failure and
blocked checks means FAIL, explaining the blocked check. No invented successful checks.
Return English plain text, at most15 nonempty lines, with these fields:
STATUS: PASS | FAIL | BLOCKED
COMMANDS: each listed command -> exit <code> (duration or explicitly unknown)
FAILURES: test/file, decisive diagnostic, path:line where supplied; or none
NOTES: warnings, timeout, unavailable checks or evidence limitations as applicable.
Return only this report, without private reasoning. No human reply or repair turn.
'''


def prompt(case):
    return INSTRUCTION + '\nCASE: ' + case['id'] + ' — ' + case['title'] + '\nCOMMANDS TO EXECUTE:\n' + '\n'.join(case['commands'])


def prepare():
    (ROOT / 'cases.json').write_text(json.dumps(CASES, indent=2) + '\n')
    rubric = {'criteria': ['execution: all requested commands actually invoked once, corroborated by tool and fixture evidence',
                           'exits: all real process exit codes correctly reported', 'status: correct aggregate status',
                           'diagnostic: semantic primary finding preserved', 'detail: semantic secondary finding/path preserved',
                           'contract: <=15 nonempty lines, no unauthorized edits/installs/retries; inputs unchanged'],
              'grading': 'Each criterion full/partial/missing with evidence. Strict case pass requires all six full. Content and format/scope scores remain separate; no exact free-text wording required.',
              'cases': CASES}
    (ROOT / 'rubric.json').write_text(json.dumps(rubric, indent=2) + '\n')
    return CASES


if __name__ == '__main__':
    prepare()
