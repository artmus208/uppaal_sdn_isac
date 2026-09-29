"""No verifier calls: failure classification and exact approved workload."""
import importlib.util
from pathlib import Path
import json
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p4runner',HERE/'runner.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class RunnerTests(unittest.TestCase):
    def test_no_verdict_from_censoring_or_error(self):
        for state in ('timeout','memory_limit','error','monitor_error'):
            self.assertEqual(r.classify({'status':state},'-- Formula is satisfied.','model-checking'),(state,None))

    def test_success_requires_single_explicit_verdict(self):
        for stdout in ('', '-- Formula is satisfied.\n-- Formula is satisfied.'):
            self.assertEqual(r.classify({'status':'success'},stdout,'model-checking'),('verdict_error',None))
        self.assertEqual(r.classify({'status':'success'},'-- Formula is NOT satisfied.','model-checking'),('success','violated'))
        self.assertEqual(r.classify({'status':'success'},'-- Formula is satisfied.','load-and-parse'),('success','satisfied'))
        self.assertEqual(r.classify({'status':'success'},'','compile'),('success',None))

    def test_plan_matches_pinned_queries_and_order(self):
        r.pins()
        steps=r.plan(); self.assertEqual(len(steps),117)
        self.assertEqual(len({s['cell_id'] for s in steps}),117)
        models=json.loads((r.ROOT/r.MANIFEST).read_text())['models']
        scientific=[s for s in steps if s['phase']=='model-checking']; self.assertEqual(len(scientific),90)
        for repeat in (1,2,3):
            self.assertEqual([s['N'] for s in steps if s['repeat']==repeat and s['phase']=='compile'],[1,2,3,4])
            for n in (1,2,3,4):
                actual=[s['query_id'] for s in scientific if s['repeat']==repeat and s['N']==n]
                rows=json.loads((r.SOURCE/f'generated/n{n}/p4-queries.json').read_text())
                self.assertEqual(actual,[x['id'] for x in rows])
        for s in scientific:
            q=r.SOURCE/s['query']; m=models[s['N']-1]
            self.assertEqual(r.sha(q),m['files']['p4/'+s['query_id']+'.q']['sha256'])
            self.assertEqual(q.read_text().strip(),s['formula'])
            self.assertEqual(s['timeout_seconds'],60)
            self.assertEqual(s['memory_stop_bytes'],2*1024**3)
            self.assertEqual(s['arguments'][s['arguments'].index('-o')+1],'1')
            self.assertEqual(s['arguments'][s['arguments'].index('-r')+1],'68')

if __name__=='__main__': unittest.main()
