"""Build shared research inputs and a separate coordinator rubric, before freeze."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def save(name, data):
    (ROOT / name).write_text(json.dumps(data, indent=2) + '\n')


SPECS = [
    ('R1', 'frozen', 'Python 3.13 structured concurrency', [('asyncio313', [(290, 416), (508, 599)])], [
        ('Compare TaskGroup and gather for a failed child.', 'TaskGroup cancels other children on a non-CancelledError failure; gather default propagates first exception without cancelling other awaitables.'),
        ('Explain what each construct waits for.', 'TaskGroup waits for all children at exit, including cancellation cleanup; gather success aggregates in input order.'),
        ('Describe grouped exception handling and exceptions to it.', 'TaskGroup groups failures in ExceptionGroup/BaseExceptionGroup; KeyboardInterrupt/SystemExit are reraised after cleanup.'),
        ('Describe an individually cancelled child in gather.', 'Treat as CancelledError; gather itself is not cancelled; other children are not cancelled.'),
        ('Explain why swallowing CancelledError is dangerous.', 'Structured concurrency uses cancellation internally and can misbehave if swallowed; propagate after cleanup, uncancel if truly suppressed.'),
        ('Recommend a construct for all-or-cancel sibling work, with a version caveat.', 'Use TaskGroup, added Python3.11, not gather as equivalent safety; bound to supplied3.13 docs.')]),
    ('R2', 'frozen', 'SQLite context managers across Python versions', [('sqlite311', [(250, 310), (600, 630), (2125, 2175)]), ('sqlite313', [(250, 370), (495, 520), (560, 635), (2375, 2455), (2640, 2695)])], [
        ('Does with sqlite3.connect close the connection in either version?', 'No. Connection context manager handles transactions, not closure, in both3.11 and3.13.'),
        ('What are transaction success/error exit semantics?', 'Commit open transaction on success; rollback on exception or failed commit; does not itself open transactions.'),
        ('How should deterministic closure be achieved?', 'Explicit close in finally or contextlib.closing, combined with a transaction context if needed.'),
        ('Which version introduces unclosed-connection ResourceWarning?', 'Python3.13; separate warning from actual lifetime correctness.'),
        ('Can the new autocommit parameter be used unchanged on3.11?', 'No, added3.12. Distinguish legacy isolation_level control and SQLite own autocommit state.'),
        ('Recommend a compatible migration and state uncertainty.', 'Keep explicit closure and explicit transaction semantics; do not infer exact runtime SQLite version or claim warnings prove absence of leaks.')]),
    ('R3', 'frozen', 'Node24.10 HTTP timeout distinctions', [('node2410http', [(1828, 1966)])], [
        ('What does headersTimeout measure and default to?', 'Complete HTTP headers; min(requestTimeout,60000) milliseconds.'),
        ('What does requestTimeout measure and default to?', 'Entire incoming request;300000 milliseconds; not a handler execution deadline.'),
        ('What do those expired parsing/request deadlines do?', 'Respond408 without forwarding to request listener, then close connection.'),
        ('What does server.timeout measure and default to?', 'Socket inactivity;0 disables timeout; not total business-work duration.'),
        ('What happens when a timeout listener is supplied?', 'Handle timed-out sockets explicitly when a timeout callback/listener is assigned.'),
        ('Does setting these prove a300s application-operation deadline?', 'No. Need a separate bounded application operation/cancellation strategy; cite scope, do not invent a built-in automatic handler cancellation guarantee.')]),
    ('R4', 'frozen', 'PostgreSQL17 concurrent unique-index incident', [('pg17index', [(600, 711)])], [
        ('Can CREATE INDEX CONCURRENTLY run inside a transaction block?', 'No; ordinary CREATE INDEX can.'),
        ('Does CONCURRENTLY imply no waiting or zero impact?', 'No; avoids blocking normal writes but waits for relevant transactions/snapshots and does extra scans/work.'),
        ('What can be left after a failed concurrent build?', 'INVALID index, ignored for queries yet incurring update overhead.'),
        ('Can uniqueness be enforced before validity or after failure?', 'Yes, starts at second scan; invalid unique index may continue enforcement after failure.'),
        ('Describe documented recovery without executing anything.', 'Inspect invalid index; documented drop/retry or REINDEX INDEX CONCURRENTLY; proposal only, no execution.'),
        ('Can two concurrent builds target the same table at once?', 'Only one concurrent index build per table; bound answer to17, no guaranteed uninterrupted deployment.')]),
    ('R5', 'live', 'Node release policy as of2026-10-17', [], [
        ('Retrieve and cite the official Node release schedule.', 'Use current official nodejs/Release schedule or official release page; do not claim retrieval from prior knowledge.'),
        ('State Node24 LTS start, maintenance and end dates.', 'Schedule snapshot: LTS2025-10-28, maintenance2026-10-20, end2028-04-30.'),
        ('State Node26 LTS date and whether it is LTS as of2026-10-17.', 'LTS scheduled2026-10-28; not LTS yet on target date.'),
        ('Identify Node22 support status as of the target date.', 'Maintenance LTS; end2027-04-30, verify schedule.'),
        ('Recommend24 or26 for a deployment requiring LTS now.', '24 satisfies LTS on target date;26 does not yet. Explain upcoming24 maintenance and26 planned LTS.'),
        ('Distinguish schedule from verified installed patch/security guarantees.', 'Do not invent latest installed version or guarantee future dates. Note schedule projections and inaccessible sources honestly.')]),
    ('R6', 'live', 'uv locked versus frozen production synchronization', [], [
        ('Retrieve official uv documentation for lock freshness.', 'Cite official Astral sync/reference docs or upstream docs; disclose inability to retrieve.'),
        ('What does --locked do when the lockfile needs updating?', 'Require up-to-date lock; error rather than silently update.'),
        ('What does --frozen change?', 'Use existing lockfile without checking freshness; not a freshness guarantee.'),
        ('Do either flags by themselves guarantee no network?', 'No. Downloads may be needed; --offline is the separate network-disabling option and missing cache can fail.'),
        ('What is the default exact-sync behavior and how to retain extra packages?', 'Exact sync removes extraneous packages; --inexact retains them. Distinguish these from lock freshness.'),
        ('Recommend a production sync policy and state unverified environment facts.', 'For freshness choose uv sync --locked; add --offline only for deliberately populated cache. Do not promise uncached success, hidden credentials or exact current uv installation.')]),
]


def prepare():
    if (ROOT / 'protocol.json').exists():
        raise RuntimeError('Already frozen; never rebuild a started pilot')
    manifest = {r['id']: r for r in json.loads((ROOT / 'source-manifest.json').read_text())}
    cases, rubric = [], []
    for cid, mode, title, selections, criteria in SPECS:
        docs = {}
        for sid, ranges in selections:
            lines = (ROOT / 'sources' / f'{sid}.txt').read_text().splitlines()
            text = f'Source: {manifest[sid]["url"]}\nOriginal source line numbers follow.\n'
            for start, end in ranges:
                text += '\n' + '\n'.join(f'{i:05d} | {lines[i-1]}' for i in range(start, min(end, len(lines)) + 1)) + '\n'
            docs[f'docs/{sid}.txt'] = text
        questions = [{'id': f'C{i}', 'question': q} for i, (q, _) in enumerate(criteria, 1)]
        cases.append({'id': cid, 'mode': mode, 'title': title, 'questions': questions, 'documents': docs})
        rubric.append({'case': cid, 'criteria': [{'id': f'C{i}', 'expected': a} for i, (_, a) in enumerate(criteria, 1)]})
    save('cases.json', cases)
    save('rubric.json', rubric)
    return cases


if __name__ == '__main__':
    print('Prepared', len(prepare()), 'cases; no native calls')
