"""Passivity and event coverage relative to accepted #44 bytes, not model checking."""
import hashlib
import json
from pathlib import Path
import re
import tarfile
import unittest
import xml.etree.ElementTree as ET
from uppaal_mcp.integrated.adapt import RECOVERY_ATTEMPTS
from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.integrated.xmlutil import label, set_label, source_name

ROOT = Path(__file__).resolve().parents[1]
CALL = re.compile(r'(?:, )?sdn_attempt_(?:start|finish|dispatch)\([^)]*\)')


def shape(x):
    return x.tag, x.attrib, (x.text or '').strip(), [shape(c) for c in x]


class RecoveryAttemptsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composition = generate(ROOT)
        cls.xml = ET.fromstring(cls.composition.model_xml)

    def test_erasing_attempts_recovers_accepted_composition(self):
        p=ROOT/'evidence/instantiation/20260922-queue-implementation'
        pub=json.loads((p/'publication.json').read_text())
        with tarfile.open(p/pub['archive']) as t:
            raw=t.extractfile(pub['run_id']+'/integrated-parser.xml').read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),json.loads((p/'run.json').read_text())['model_hash'])
        actual=ET.fromstring(self.composition.model_xml)
        actual.find('declaration').text=actual.findtext('declaration').replace(RECOVERY_ATTEMPTS,'')
        for tr in actual.findall('template/transition'):
            before=label(tr,'assignment')
            if 'sdn_attempt_' in before:
                set_label(tr,'assignment',CALL.sub('',before))
        self.assertEqual(shape(actual),shape(ET.fromstring(raw)))

    def test_every_actual_event_has_exactly_one_call_and_no_other_writer(self):
        counts=dict(start=0,finish=0,primary=0,rollback=0)
        for t in self.xml.findall('template'):
            for tr in t.findall('transition'):
                a=label(tr,'assignment');sync=label(tr,'synchronisation')
                for kind in ('guard','synchronisation','select'):
                    self.assertNotIn('sdn_attempt_',label(tr,kind))
                if t.findtext('name')!='sdn_Template_A_REC':
                    self.assertNotIn('sdn_attempt_',a);continue
                expected=[]
                if 'sdn_obs_rec_start()' in a:
                    self.assertEqual(source_name(t,tr),'StableConfig')
                    expected.append('sdn_attempt_start()');counts['start']+=1
                if 'sdn_obs_rec_finish()' in a:
                    expected.append('sdn_attempt_finish()');counts['finish']+=1
                if sync in ('bus_rec_policy_request!','bus_rec_flow_request!'):
                    expected.append('sdn_attempt_dispatch(false)');counts['primary']+=1
                if sync=='bus_rollback_request!':
                    expected.append('sdn_attempt_dispatch(true)');counts['rollback']+=1
                self.assertCountEqual(re.findall(r'sdn_attempt_\w+\([^)]*\)',a),expected)
        self.assertEqual(counts['start'],2)
        self.assertEqual(counts['primary'],2)
        self.assertGreater(counts['rollback'],0)
        self.assertGreater(counts['finish'],0)
        for inv in self.xml.findall("template/location/label[@kind='invariant']"):
            self.assertNotIn('sdn_attempt_',inv.text or '')

    def test_candidate_queries_and_metadata_do_not_claim_verification(self):
        m=self.composition.metadata
        self.assertEqual(m['recovery_attempt_recording']['limits'],dict(primary=1,rollback=1,total=2))
        q={x['id']:x for x in m['query_map'] if x['id'].startswith('recovery-attempts-')}
        self.assertEqual(len(q),6)
        self.assertTrue(all(x['status']=='candidate_unverified' for x in q.values()))
        self.assertEqual(m['verification_status'],'not_run')

if __name__=='__main__':unittest.main()
