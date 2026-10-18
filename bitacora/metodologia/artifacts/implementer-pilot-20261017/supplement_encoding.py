"""Supplemental I6 oracle for the prompt's unspecified outbox.body encoding.

The frozen cases and candidate implementations remain untouched. Only six exact
assertions change: four callback-event list comparisons and one full outbox-row
comparison accept raw result or JSON with exact result and optional id/job_id; the inbox
comparison checks the exact first callback body, preserving its original dedupe
and first-value semantics. All job values, row metadata, ordering, lengths,
transaction/fault assertions, and delivery counts remain exact. Allowed JSON
keysets are only {result}, {id,result}, or {job_id,result}; supplied identity
must match the separately checked outbox/callback event id. Extra fields fail.
"""
from copy import deepcopy


_HELPER = '''    def assertEventRows(self, actual, expected):
        import json
        # Only positions (event id, event body) participate; remaining columns
        # retain exact comparison. Ordering and length stay unchanged.
        normalized=[]
        for index,row in enumerate(actual):
            if index>=len(expected) or len(row)<2:
                normalized.append(row)
                continue
            wanted=expected[index]
            body=row[1]
            valid=body==wanted[1]
            if not valid and isinstance(body,str):
                try:
                    decoded=json.loads(body)
                except (ValueError,TypeError):
                    decoded=None
                valid=(
                    isinstance(decoded,dict)
                    and set(decoded) in ({'result'},{'id','result'},{'job_id','result'})
                    and decoded.get('result')==wanted[1]
                    and decoded.get('id',wanted[0])==wanted[0]
                    and decoded.get('job_id',wanted[0])==wanted[0]
                )
            normalized.append((row[0],wanted[1] if valid else body,*row[2:]))
        self.assertEqual(normalized,expected)
'''

# Every replacement is asserted to match exactly once, so a frozen-source drift
# fails loudly rather than silently weakening an unrelated assertion.
_REPLACEMENTS = (
    ("self.assertEqual(seen,[('a','recovered')])",
     "self.assertEventRows(seen,[('a','recovered')])"),
    ("self.assertEqual(seen,[('a','ok'),('a','ok')])",
     "self.assertEventRows(seen,[('a','ok'),('a','ok')])"),
    ("self.assertEqual(observed,[('a','a-result'),('b','b-result')])",
     "self.assertEventRows(observed,[('a','a-result'),('b','b-result')])"),
    ("self.assertEqual(replay,[('b','b-result'),('c','c-result')])",
     "self.assertEventRows(replay,[('b','b-result'),('c','c-result')])"),
    ("self.assertEqual(c.execute('SELECT * FROM outbox').fetchall(),[('a','ok',0)])",
     "self.assertEventRows(c.execute('SELECT * FROM outbox').fetchall(),[('a','ok',0)])"),
    ("self.assertEqual(c.execute('SELECT * FROM inbox').fetchall(),[('a','ok')])",
     "self.assertEqual(c.execute('SELECT * FROM inbox').fetchall(),[('a',seen[0][1])])"),
)


def adjusted_case(case: dict) -> dict:
    """Return a copy with supplemental I6 private_tests; all other data unchanged."""
    if case.get('id') != 'I6':
        raise ValueError('Supplement applies only to frozen I6')
    adjusted=deepcopy(case)
    name='test_private.py'
    source=adjusted['private_tests'][name]
    for before,after in _REPLACEMENTS:
        if source.count(before)!=1:
            raise ValueError('Frozen I6 assertion drift: '+before)
        source=source.replace(before,after,1)
    anchor='class QueueTests(unittest.TestCase):\n'
    if source.count(anchor)!=1:
        raise ValueError('Frozen I6 class drift')
    adjusted['private_tests'][name]=source.replace(anchor,anchor+_HELPER,1)
    return adjusted
