from textwrap import dedent as D

CASE = dict(id='I3',title='Refactor deterministic dependency scheduler',difficulty=3,
 prompt='''Refactor the dependency scheduler across app.graph and app.scheduler without changing its public API. Only app/ may change; test_public.py is protected. Use stdlib only, and optionally add tests under app/.
Export Scheduler from both app and app.scheduler. Scheduler(jobs,max_parallel=2) accepts a mapping of nonempty string job IDs to iterables of dependency IDs. IDs are guaranteed valid strings. Snapshot input; duplicate dependencies are harmless. Reject any unknown dependency or cycle (including disconnected cycles and self-loops) with ValueError during construction, before any dispatch. Validate max_parallel as integer excluding bool, at least 1, otherwise ValueError. Empty graph is valid.
ready() returns ALL currently eligible pending job IDs in lexicographic order, independent of capacity; it never changes state. A job is eligible only when every dependency succeeded. start(job_id) returns None and transitions an eligible pending job to running iff running count is below max_parallel. Otherwise raise ValueError without changing any state (including unknown IDs). finish(job_id,success=True) returns None and accepts ONLY running jobs; unknown/non-running IDs raise ValueError without mutation. Success is guaranteed bool. On success change to succeeded. On failure change to failed and transitively mark every still-pending descendant blocked; unrelated jobs continue. A job with even one failed/blocked dependency must become blocked immediately, including when its other dependencies are still running. Preserve completed states. statuses() returns a fresh dict ID->state, with states pending/running/succeeded/failed/blocked. done() is true exactly when no pending or running jobs remain; blocked counts as terminal. Calls are single-threaded. Preserve max_parallel public attribute. app.graph.validate_graph(jobs) returns a fresh dict of dependency sets and performs graph validation; Scheduler must continue working when dependencies are generators. Support chains of at least 1,200 jobs without recursion-limit failures. No automatic execution is required; callers explicitly start and finish jobs.''',
 starter={'app/__init__.py':'from .scheduler import Scheduler\n',
 'app/graph.py':D('''\
 def validate_graph(jobs):
     return {job:set(deps) for job,deps in jobs.items()}
 '''), 'app/scheduler.py':D('''\
 from .graph import validate_graph
 class Scheduler:
     def __init__(self,jobs,max_parallel=2):
         self.jobs=validate_graph(jobs)
         self.max_parallel=max_parallel
         self.state={job:'pending' for job in self.jobs}
     def ready(self):
         return [job for job,deps in self.jobs.items() if self.state[job]=='pending' and all(self.state.get(dep)=='succeeded' for dep in deps)]
     def start(self,job_id):
         if job_id not in self.ready(): raise ValueError('not ready')
         self.state[job_id]='running'
     def finish(self,job_id,success=True):
         if self.state.get(job_id)!='running': raise ValueError('not running')
         self.state[job_id]='succeeded' if success else 'failed'
     def statuses(self): return dict(self.state)
     def done(self): return all(v in ('succeeded','failed','blocked') for v in self.state.values())
 '''), 'test_public.py':D('''\
 import unittest
 from app import Scheduler
 class Public(unittest.TestCase):
     def test_chain(self):
         s=Scheduler({'a':[],'b':['a']})
         self.assertEqual(s.ready(),['a'])
         self.assertIsNone(s.start('a')); self.assertFalse(s.done())
         self.assertIsNone(s.finish('a')); self.assertEqual(s.ready(),['b'])
         s.start('b'); s.finish('b'); self.assertTrue(s.done())
     def test_empty(self):
         self.assertTrue(Scheduler({}).done())
 ''')},
 reference={'app/graph.py':D('''\
 def validate_graph(jobs):
     graph={job:set(deps) for job,deps in jobs.items()}
     for deps in graph.values():
         if not deps.issubset(graph): raise ValueError('unknown dependency')
     remaining={job:len(deps) for job,deps in graph.items()}
     children={job:[] for job in graph}
     for job,deps in graph.items():
         for dep in deps: children[dep].append(job)
     ready=[job for job,n in remaining.items() if not n]
     visited=0
     while ready:
         node=ready.pop(); visited+=1
         for child in children[node]:
             remaining[child]-=1
             if not remaining[child]: ready.append(child)
     if visited!=len(graph): raise ValueError('dependency cycle')
     return graph
 '''), 'app/scheduler.py':D('''\
 from .graph import validate_graph
 class Scheduler:
     def __init__(self,jobs,max_parallel=2):
         if type(max_parallel) is not int or max_parallel<1: raise ValueError('invalid max_parallel')
         self.jobs=validate_graph(jobs)
         self.max_parallel=max_parallel
         self.state={job:'pending' for job in self.jobs}
     def ready(self):
         return sorted(job for job,deps in self.jobs.items() if self.state[job]=='pending' and all(self.state[dep]=='succeeded' for dep in deps))
     def start(self,job_id):
         if job_id not in self.ready() or sum(v=='running' for v in self.state.values())>=self.max_parallel:
             raise ValueError('not ready or full')
         self.state[job_id]='running'
     def finish(self,job_id,success=True):
         if self.state.get(job_id)!='running': raise ValueError('not running')
         self.state[job_id]='succeeded' if success else 'failed'
         if not success:
             changed=True
             while changed:
                 changed=False
                 for job,deps in self.jobs.items():
                     if self.state[job]=='pending' and any(self.state[dep] in ('failed','blocked') for dep in deps):
                         self.state[job]='blocked'; changed=True
     def statuses(self): return dict(self.state)
     def done(self): return all(v in ('succeeded','failed','blocked') for v in self.state.values())
 ''')},
 private_tests={'test_private.py':D('''\
 import itertools
 import unittest
 from app import Scheduler
 from app.scheduler import Scheduler as Direct
 from app.graph import validate_graph
 class Private(unittest.TestCase):
     def test_unknown_dependency(self):
         with self.assertRaises(ValueError): Scheduler({'a':['missing']})
         with self.assertRaises(ValueError): validate_graph({'a':['missing']})
     def test_cycles_before_dispatch(self):
         for graph in [{'a':['a']},{'a':['b'],'b':['a']},{'z':[],'a':['b'],'b':['c'],'c':['a']}]:
             with self.subTest(graph=graph):
                 with self.assertRaises(ValueError): Scheduler(graph)
                 with self.assertRaises(ValueError): validate_graph(graph)
     def test_deterministic_permutations(self):
         for order in itertools.permutations(['c','a','b']):
             s=Scheduler({name:[] for name in order})
             self.assertEqual(s.ready(),['a','b','c'])
             self.assertEqual(s.ready(),['a','b','c'])
             self.assertEqual(set(s.statuses().values()),{'pending'})
     def test_capacity_and_reuse(self):
         s=Scheduler({'a':[],'b':[],'c':[]},1)
         s.start('a'); before=s.statuses()
         self.assertEqual(s.ready(),['b','c'])
         with self.assertRaises(ValueError): s.start('b')
         self.assertEqual(s.statuses(),before)
         s.finish('a'); s.start('b'); self.assertEqual(s.statuses()['b'],'running')
     def test_parallel_diamond(self):
         s=Scheduler({'root':[],'left':['root'],'right':['root'],'end':['right','left']},2)
         s.start('root'); s.finish('root'); self.assertEqual(s.ready(),['left','right'])
         s.start('right'); s.start('left'); s.finish('right'); self.assertEqual(s.ready(),[])
         s.finish('left'); self.assertEqual(s.ready(),['end'])
     def test_failure_transitive(self):
         s=Scheduler({'root':[],'child':['root'],'leaf':['child'],'other':[]})
         s.start('root'); s.finish('root',False)
         self.assertEqual(s.statuses(),{'root':'failed','child':'blocked','leaf':'blocked','other':'pending'})
         self.assertEqual(s.ready(),['other']); s.start('other'); s.finish('other'); self.assertTrue(s.done())
     def test_failure_while_other_parent_running(self):
         s=Scheduler({'a':[],'b':[],'c':['a','b'],'d':['c']})
         s.start('a'); s.start('b'); s.finish('a',False)
         self.assertEqual(s.statuses()['c'],'blocked'); self.assertEqual(s.statuses()['d'],'blocked')
         self.assertFalse(s.done()); s.finish('b'); self.assertTrue(s.done())
     def test_invalid_transitions_atomic(self):
         s=Scheduler({'a':[],'b':['a']})
         for method,name in [('start','b'),('start','missing'),('finish','a'),('finish','missing')]:
             before=s.statuses()
             with self.assertRaises(ValueError): getattr(s,method)(name)
             self.assertEqual(s.statuses(),before)
         s.start('a')
         with self.assertRaises(ValueError): s.start('a')
         s.finish('a')
         with self.assertRaises(ValueError): s.finish('a',False)
         self.assertEqual(s.statuses()['a'],'succeeded')
     def test_validate_capacity(self):
         for bad in [0,-1,True,1.5,'2',None]:
             with self.assertRaises(ValueError): Scheduler({},bad)
         self.assertEqual(Scheduler({},3).max_parallel,3)
     def test_snapshot_and_duplicates(self):
         graph={'a':[],'b':['a','a']}; s=Scheduler(graph)
         graph['b'].append('missing'); graph['a'].append('b')
         s.start('a'); s.finish('a'); self.assertEqual(s.ready(),['b'])
         states=s.statuses(); states['b']='failed'; self.assertEqual(s.statuses()['b'],'pending')
     def test_generators_and_exports(self):
         self.assertIs(Scheduler,Direct)
         s=Scheduler({'b':iter(['a']),'a':iter([])})
         s.start('a'); s.finish('a'); self.assertEqual(s.ready(),['b'])
         self.assertEqual(validate_graph({'b':['a','a'],'a':[]}),{'b':{'a'},'a':set()})
     def test_long_chain(self):
         graph={str(i):[str(i-1)] if i else [] for i in range(1200)}
         s=Scheduler(graph); s.start('0'); s.finish('0',False)
         self.assertTrue(s.done()); self.assertEqual(sum(v=='blocked' for v in s.statuses().values()),1199)
 ''')})
