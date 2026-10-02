"""Contract controls evaluate the emitted receipt guard; no engine verdicts."""
import copy
import itertools
import re
import unittest
import xml.etree.ElementTree as ET

import generate


def expression(text):
    text=' '.join(text.split())
    return re.sub(r'!(?!=)', ' not ', text.replace('&&',' and ').replace('||',' or ')).strip()


def functions(declaration, values):
    # Evaluate the actual side-effect-free model functions, with a closed namespace.
    env=dict(values)
    for name,params,body in re.findall(r'bool (c82_\w+)\(([^)]*)\)\s*\{\s*return ([\s\S]*?);\s*\}',declaration):
        args=[p.split()[-1] for p in params.split(',') if p.strip()]
        def fn(*vals, args=args,body=body):
            return eval(expression(body), {'__builtins__':{}},dict(env,**dict(zip(args,vals))))
        env[name]=fn
    return env


def healthy():
    names=re.findall(r'\bc82_\w+\b',generate.RECEIPT)
    state={n:1 for n in names}
    for n in ['received','cancelled','sensing_failed','tx_lost','queue_failed','outcome']:
        state['c82_'+n]=0
    for n in ['pd','fa','miss','acc','cov']:
        state['c82_'+n]=0;state['c82_req_'+n]=2
    state.update(c82_req_fresh=2,c82_req_update=2,c82_service_age=12,
                 c82_D_service=40,c82_sample_age=1)
    return state


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated=generate.outputs();cls.root=ET.fromstring(cls.generated['model.xml'])
        cls.templates={t.findtext('name'):t for t in cls.root.findall('template')}
        cls.app=cls.templates['u0_app_A_REQ']
        cls.completed=next(l.get('id') for l in cls.app.findall('location') if l.findtext('name')=='Completed')
        cls.receipts=[e for e in cls.app.findall('transition') if e.find('target').get('ref')==cls.completed]

    def accepts(self, state):
        env=functions(self.root.findtext('declaration'),state)
        return any(eval(expression(generate.label(e,'guard').text),{'__builtins__':{}},env) for e in self.receipts)

    def test_deterministic_and_pinned(self):
        self.assertEqual(generate.outputs(),self.generated)
        bad=bytearray(generate.SOURCE.read_bytes());bad[-2]^=1
        with self.assertRaises(ValueError):generate.compile_model(bytes(bad))

    def test_full_composition_and_unchanged_templates(self):
        original=ET.fromstring(generate.SOURCE.read_bytes())
        changed={'u0_app_A_REQ','u0_phy_Template_A_SQ','SharedLoad','u0_Boundary_E_SERVICE'}
        self.assertEqual(len(self.root.findall('template')),51)
        for t in original.findall('template'):
            if t.findtext('name') in changed:continue
            a=copy.deepcopy(t);b=copy.deepcopy(self.templates[t.findtext('name')])
            ET.indent(a,space='  ');ET.indent(b,space='  ')
            self.assertEqual(ET.tostring(a),ET.tostring(b),t.findtext('name'))

    def test_nta_template_element_order(self):
        rank={'name':0,'parameter':1,'declaration':2,'location':3,'init':4,'transition':5}
        for t in self.root.findall('template'):
            self.assertEqual([rank[x.tag] for x in t],sorted(rank[x.tag] for x in t))

    def test_healthy_receipt_and_age_equalities(self):
        for service_age,sample_age in itertools.product([0,39.999,40,40.001],[0,4.999,5,9.999,10]):
            state=dict(healthy(),c82_service_age=service_age,c82_sample_age=sample_age)
            self.assertEqual(self.accepts(state),service_age<=40 and sample_age<5,(service_age,sample_age))

    def test_fake_wrong_duplicate_missing_and_failed_events(self):
        self.assertTrue(self.accepts(healthy()))
        for n in ['request_id','admitted_id','job_id','sample_id','sample_request_id','tx_request_id','tx_sample_id',
                  'active','admitted','sampled','enqueued','dispatched','attempted']:
            with self.subTest(n=n):self.assertFalse(self.accepts(dict(healthy(),**{'c82_'+n:0})))
        for n in ['received','cancelled','sensing_failed','tx_lost','queue_failed','outcome']:
            with self.subTest(n=n):self.assertFalse(self.accepts(dict(healthy(),**{'c82_'+n:1})))

    def test_every_stored_quality_combination(self):
        for vals in itertools.product(range(3),repeat=5):
            state=dict(healthy(),**dict(zip(['c82_pd','c82_fa','c82_miss','c82_acc','c82_cov'],vals)))
            self.assertEqual(self.accepts(state),vals==(0,0,0,0,0),vals)

    def test_quality_does_not_use_later_global_kpis(self):
        state=healthy()
        for n in ['pdClass','falseAlarmClass','missedDetectionClass','accuracyClass','coverageClass',
                  'detectionFreshnessClass','updatePeriodClass']:
            state['u0_app_'+n]=2
        state.update(u0_phy_PdClass=2,u0_phy_RfaClass=2)
        self.assertTrue(self.accepts(state))
        state['c82_pd']=2;state['u0_app_pdClass']=0;state['u0_phy_PdClass']=0
        self.assertFalse(self.accepts(state))

    def test_timer_termination_grant_and_ack_cannot_complete(self):
        self.assertEqual(len(self.receipts),4)
        for e in self.receipts:
            self.assertEqual(generate.label(e,'synchronisation').text,'c82_result_delivery?')
        for t in self.root.findall('template'):
            for e in t.findall('transition'):
                sync=generate.label(e,'synchronisation')
                self.assertFalse(sync is not None and sync.text=='u0_app_service_complete!')
                assignment=generate.label(e,'assignment')
                if assignment is not None and 'c82_success=true' in assignment.text:
                    self.assertIn(e,self.receipts)

    def test_admission_rejection_cannot_overwrite_cancellation(self):
        rejected=next(l.get('id') for l in self.app.findall('location') if l.findtext('name')=='Rejected')
        for e in self.app.findall('transition'):
            if e.find('target').get('ref')==rejected:
                self.assertIn('c82_active',generate.label(e,'guard').text)

    def test_clock_resets_and_retrospective_completion(self):
        decl=self.root.findtext('declaration')
        self.assertEqual(decl.count('c82_service_age=0'),1)
        self.assertEqual(decl.count('c82_sample_age=0'),1)
        measurement=[e for e in self.templates['u0_phy_Template_A_SQ'].findall('transition')
                     if (generate.label(e,'assignment') is not None and 'c82_store_measurement()' in generate.label(e,'assignment').text)]
        self.assertEqual(len(measurement),1)
        self.assertIn('c82_measure_age==u0_phy_D_sense',generate.label(measurement[0],'guard').text)
        for e in self.receipts:
            self.assertIn('c82_receipt_timely=true',generate.label(e,'assignment').text)
        query=self.generated['queries/completion-safety.q'].decode()
        self.assertNotIn('c82_service_age',query);self.assertNotIn('c82_sample_age',query)

    def test_queue_original_capacity_update_and_result_insert(self):
        old=ET.fromstring(generate.SOURCE.read_bytes()).findall('template')[49].findall('transition')[1]
        new=self.templates['SharedLoad'].findall('transition')[1]
        self.assertEqual(generate.label(new,'assignment').text,'c82_mac_service(server), '+generate.label(old,'assignment').text)
        self.assertEqual(generate.label(new,'guard').text,generate.label(old,'guard').text)
        decl=self.root.findtext('declaration')
        self.assertIn('c82_fifo_rank=u0_mac_queue_q',decl)
        self.assertIn('u0_mac_queue_q=u0_mac_queue_K+1',decl)
        self.assertIn('u0_mac_queue_q<=u0_mac_queue_K && c82_fifo_rank>0',decl)
        for q in range(6):
            for grant,arrival in itertools.product([0,1],repeat=2):
                if grant and q==0:continue
                updated=q if q>4 else q-grant+arrival
                self.assertTrue(0<=updated<=5)
                if q==5:self.assertEqual(updated,5)

    def test_added_bounded_locations_have_failure_exits(self):
        for template,name,exit_name in [('u0_app_A_REQ','Accepted','ServiceTimeout'),
                  ('u0_app_A_REQ','AcceptedDegraded','ServiceTimeout'),
                  ('u0_phy_Template_A_SQ','JobMeasuring','SensingQoSOk'),
                  ('C82_ResultJob','Transmitting','Done')]:
            t=self.templates[template];loc={l.findtext('name'):l for l in t.findall('location')}
            self.assertIsNone(loc[name].find('committed'));self.assertIsNone(loc[name].find('urgent'))
            self.assertTrue(loc[name].findall('label'))
            exits=[e for e in t.findall('transition') if e.find('source').get('ref')==loc[name].get('id') and e.find('target').get('ref')==loc[exit_name].get('id')]
            self.assertTrue(exits)


if __name__=='__main__':unittest.main()
