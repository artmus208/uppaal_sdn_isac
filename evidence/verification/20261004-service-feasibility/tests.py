"""Mutated premises and independent rational boundaries, not model checking."""
import copy
from fractions import Fraction
import json
import unittest
import xml.etree.ElementTree as ET
import check as sf


def template(root, name):
    return next(t for t in root.findall('template') if t.findtext('name')==name)


def edge_label(root, name, index, kind, transform):
    e = template(root,name).findall('transition')[index]
    lab = e.find("label[@kind='"+kind+"']")
    if lab is None:
        lab = ET.SubElement(e,'label',kind=kind)
    lab.text = transform(lab.text or '')


def location_label(root, name, loc, transform):
    item = next(l for l in template(root,name).findall('location') if l.findtext('name')==loc)
    item.find("label[@kind='invariant']").text = transform(item.findtext("label[@kind='invariant']"))


def declaration(root, old, new):
    d = root.find('declaration')
    assert old in d.text
    d.text = d.text.replace(old,new,1)


MUTATIONS = {
    'weaken_freshness':lambda r:edge_label(r,sf.APP,12,'guard',lambda x:x.replace('c82_sample_age<5','c82_sample_age<=5')),
    'reset_service_later':lambda r:edge_label(r,sf.APP,6,'assignment',lambda x:x+', c82_service_age=0'),
    'reset_admission_later':lambda r:edge_label(r,sf.APP,6,'assignment',lambda x:x+', u0_app_c_admission=0'),
    'reset_sample_at_dispatch':lambda r:edge_label(r,'SharedLoad',1,'assignment',lambda x:x+', c82_sample_age=0'),
    'reset_tx_later':lambda r:edge_label(r,sf.JOB,7,'assignment',lambda x:'c82_tx_age=0'),
    'terminal_escape':lambda r:template(r,sf.APP).findall('transition')[0].find('source').set('ref','u0_app_id7'),
    'post_emission_escape':lambda r:template(r,sf.APP).findall('transition')[6].find('target').set('ref','u0_app_id0'),
    'unbounded_accepted':lambda r:location_label(r,sf.APP,'Accepted',lambda x:'true'),
    'long_admission':lambda r:declaration(r,'u0_app_D_admission        = 15','u0_app_D_admission        = 50'),
    'shorter_period':lambda r:declaration(r,'u0_bus_T_mac_tick=5','u0_bus_T_mac_tick=4'),
    'repeat_measurement':lambda r:edge_label(r,sf.receipt.PHY,25,'guard',lambda x:x.replace('!c82_sampled','true')),
    'repeat_enqueue':lambda r:edge_label(r,'SharedLoad',5,'guard',lambda x:x.replace('!c82_enqueued','true')),
    'shortcut_rank':lambda r:declaration(r,'else c82_fifo_rank--;','else c82_fifo_rank=1;'),
    'rank_before_increment':lambda r:declaration(r,'u0_mac_queue_q++; c82_fifo_rank=u0_mac_queue_q;','c82_fifo_rank=u0_mac_queue_q; u0_mac_queue_q++;'),
    'external_rank_writer':lambda r:edge_label(r,sf.JOB,6,'assignment',lambda x:x+', c82_fifo_rank=0'),
    'fabricated_dispatch':lambda r:edge_label(r,sf.JOB,6,'assignment',lambda x:x+', c82_dispatched=true'),
    'hidden_helper_writer':lambda r:declaration(r,'void c82_queue_class() {','void c82_queue_class() { c82_sample_age=0;'),
    'restart_epoch':lambda r:edge_label(r,'SharedLoad',5,'assignment',lambda x:x+', tick=0'),
    'early_epoch_guard':lambda r:edge_label(r,'SharedLoad',0,'guard',lambda x:'tick>=0'),
    'remove_epoch_reset':lambda r:edge_label(r,'SharedLoad',1,'assignment',lambda x:x.replace('tick=0','tick=5')),
    'duplicate_service_edge':lambda r:template(r,'SharedLoad').append(copy.deepcopy(template(r,'SharedLoad').findall('transition')[1])),
    'changed_initial_sample_age':lambda r:declaration(r,'c82_sampled=false','c82_sampled=true'),
    'duplicate_app_instance':lambda r:setattr(r.find('system'),'text',r.findtext('system')+'\nsecond_app=u0_app_A_REQ();'),
    'shadow_rank':lambda r:ET.SubElement(template(r,sf.JOB),'declaration').__setattr__('text','int c82_fifo_rank=0;'),
    'stopwatch_tick':lambda r:location_label(r,'SharedLoad','Wait',lambda x:x+' && tick\'==0'),
    'unbounded_transport':lambda r:location_label(r,sf.JOB,'Transmitting',lambda x:'true'),
}


class Premises(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.fromstring((sf.ROOT/sf.MODEL).read_bytes())
        cls.capsule = json.loads((sf.HERE/'premises.json').read_text(encoding='utf-8'))

    def test_exact_premises(self):
        cert = sf.analyze(self.root,self.capsule)
        self.assertEqual(cert['transitions_scanned'],884)
        self.assertEqual(cert['nonterminal_invariants']['RequestPending'],
                         'u0_app_c_admission<=u0_app_D_admission')

    def test_outer_dependency_and_certificate(self):
        expected = json.loads((sf.HERE/'certificate.json').read_text(encoding='utf-8'))
        self.assertEqual(sf.run(),expected)

    def test_layout_only_change_does_not_change_semantics(self):
        r = copy.deepcopy(self.root)
        template(r,sf.APP).find('location').set('x','999')
        sf.analyze(r,self.capsule)
        self.assertNotEqual(sf.sha(ET.tostring(r)),sf.receipt.MODEL_HASH)


def add_mutation(name, mutate):
    def test(self):
        r = copy.deepcopy(self.root)
        mutate(r)
        self.assertNotEqual(ET.tostring(r),ET.tostring(self.root),'mutation did nothing')
        with self.assertRaises(sf.receipt.PremiseError):
            sf.analyze(r,self.capsule)
    setattr(Premises,'test_mutation_'+name,test)


for name, mutate in MUTATIONS.items():
    add_mutation(name,mutate)


class Arithmetic(unittest.TestCase):
    def test_rank_two_even_zero_other_costs_is_stale(self):
        self.assertEqual(sf.age(2),5)
        self.assertFalse(sf.age(2)<5)

    def test_rank_three_four_lower_bounds(self):
        self.assertEqual(sf.age(3),10)
        self.assertEqual(sf.age(4),15)

    def test_one_skip_exhausts_budget(self):
        self.assertEqual(sf.age(1,skipped=1),5)

    def test_transport_boundary_independent_expected(self):
        self.assertEqual(sf.age(1,phase=Fraction(7,2),transport=1),Fraction(9,2))
        self.assertEqual(sf.age(1,phase=4,transport=1),5)
        self.assertGreater(sf.age(1,phase=Fraction(9,2),transport=1),5)

    def test_launch_delay_is_part_of_age(self):
        self.assertEqual(sf.age(1,enqueue=1,phase=2,launch=1,transport=1),5)

    def test_rank_phase_skip_sweep_against_explicit_decision_times(self):
        # Independent list of epoch timestamps, not a transcription of age().
        for rank in range(1,5):
            for phase in [Fraction(0),Fraction(1,2),Fraction(5)]:
                for skipped in range(4):
                    decision_times=[phase+5*i for i in range(rank+skipped)]
                    dispatch=decision_times[-1]
                    self.assertEqual(sf.age(rank,phase=phase,skipped=skipped),dispatch)

    def test_invalid_contract_values_rejected(self):
        for kwargs in [dict(rank=0),dict(rank=1,skipped=-1),dict(rank=1,launch=-1),
                       dict(rank=1,period=0),dict(rank=1,skipped=Fraction(1,2))]:
            with self.assertRaises(sf.receipt.PremiseError):
                sf.age(**kwargs)

    def test_strict_vs_inclusive_boundaries(self):
        self.assertFalse(Fraction(5)<5)
        self.assertTrue(Fraction(40)<=40)
        self.assertFalse(Fraction(40)<40)


if __name__=='__main__':
    unittest.main(verbosity=2)
