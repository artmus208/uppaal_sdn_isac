"""Mutation and semantic controls; no licensed engine is executed."""
import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import check as c

REPO = c.HERE.parents[2]


class AuditControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(REPO / c.MODEL).getroot()
        cls.query = (REPO / c.QUERY).read_text(encoding='utf-8')
        cls.capsule = json.loads((c.HERE / 'premises.json').read_text(encoding='utf-8'))

    def setUp(self):
        self.root = copy.deepcopy(type(self).root)
        self.cap = copy.deepcopy(self.capsule)

    def template(self, name='u0_phy_Template_ObsSenseReport'):
        return next(t for t in self.root.findall('template') if t.findtext('name') == name)

    def rejected(self, reason, query=None):
        with self.assertRaisesRegex(c.PremiseError, reason):
            c.audit(self.root, self.query if query is None else query, self.cap)

    def test_original_and_exact_diagnostic_transformation(self):
        cert = c.audit(self.root, self.query, self.cap)
        self.assertEqual(cert['counts'], {'original_processes': 51, 'removed_observers': 22,
                         'retained_processes': 29, 'global_helpers': 77, 'observer_edges': 74,
                         'broadcast_receive_edges': 8, 'committed_locations': 5})
        reduced = ET.fromstring(c.erase(self.root, cert))
        self.assertEqual(len(reduced.findall('template')), 29)
        self.assertEqual(reduced.findtext('declaration'), self.root.findtext('declaration'))
        originals = {t.findtext('name'): ET.tostring(t) for t in self.root.findall('template')}
        # indent() normalizes tails. Compare semantic trees after the same normalization.
        ET.indent(self.root, space='  ')
        originals = {t.findtext('name'): ET.tostring(t) for t in self.root.findall('template')}
        for t in reduced.findall('template'):
            self.assertEqual(ET.tostring(t), originals[t.findtext('name')])
        self.assertEqual(c.erase(type(self).root, cert), c.erase(type(self).root, cert))
        self.assertTrue({'u0_mac_c_obs_ack', 'u0_sdn_c_obs_rec'}.isdisjoint(c.HIDDEN))

    def test_observer_retained_write(self):
        self.template().find("transition/label[@kind='assignment']").text = 'c82_active = false'
        self.rejected('observer writes retained state')

    def test_observer_retained_clock_reset(self):
        self.template().find("transition/label[@kind='assignment']").text = 'c82_sample_age = 0'
        self.rejected('observer writes retained state')

    def test_observer_indirect_writer(self):
        self.template().find("transition/label[@kind='assignment']").text = 'c82_emit_request()'
        self.rejected('observer writes retained state')

    def test_observer_helper_reset_is_unsupported(self):
        self.template().find("transition/label[@kind='assignment']").text = 'u0_raise_app_service_request_seq()'
        self.rejected('observer helper update unsupported')

    def test_observer_invariant(self):
        ET.SubElement(self.template().find('location'), 'label', kind='invariant').text = 'c82_sample_age <= 5'
        self.rejected('observer invariant/rate unsupported')

    def test_observer_urgent(self):
        ET.SubElement(self.template().find('location'), 'urgent')
        self.rejected('urgent observer location')

    def test_missing_committed_exit(self):
        self.template().remove(self.template().findall('transition')[-1])
        self.rejected('committed exit must be complementary pair')

    def test_committed_exit_equality_gap(self):
        e = self.template().findall('transition')[-2]
        e.find("label[@kind='guard']").text = 'u0_phy_c_obs_sense < u0_phy_D_report'
        self.rejected('unsupported committed exit partition')

    def test_committed_exit_overlap(self):
        e = self.template().findall('transition')[-1]
        e.find("label[@kind='guard']").text = 'u0_phy_c_obs_sense <= u0_phy_D_report'
        self.rejected('committed exit gap/overlap')

    def test_committed_cycle(self):
        e = self.template().findall('transition')[-1]
        e.find('target').set('ref', e.find('source').get('ref'))
        self.rejected('committed cycle')

    def test_committed_observer_cannot_receive_production_action(self):
        e = self.template().findall('transition')[-1]
        ET.SubElement(e, 'label', kind='synchronisation').text = 'u0_phy_phy_kpi_report?'
        self.rejected('committed exit has side effects/sync')

    def test_committed_initial(self):
        self.template().find('init').set('ref', self.template().findall('location')[-1].get('id'))
        self.rejected('observer starts committed')

    def test_observer_binary_receive(self):
        self.template().find("transition/label[@kind='synchronisation']").text = 'c82_enqueue?'
        self.rejected('observer binary/urgent input')

    def test_urgent_broadcast_below_declaration_seal(self):
        d = self.root.find('declaration')
        d.text = d.text.replace('broadcast chan u0_phy_aos_ctrl_expired', 'urgent broadcast chan u0_phy_aos_ctrl_expired')
        self.cap['declaration_remainder'] = c.norm(c.functions(d.text)[1])
        self.rejected('observer binary/urgent input')

    def test_observer_sender(self):
        e = self.template().find("transition/label[@kind='synchronisation']")
        e.text = e.text.replace('?', '!')
        self.rejected('observer must receive')

    def test_observer_select(self):
        ET.SubElement(self.template().find('transition'), 'label', kind='select').text = 'i:int[0,1]'
        self.rejected('observer select unsupported')

    def test_production_hidden_guard(self):
        t = self.template('C82_ResultJob')
        t.find("transition/label[@kind='guard']").text = 'u0_app_service_request_seq'
        self.rejected('direct hidden dependency')

    def test_transitive_production_hidden_guard(self):
        t = self.template('C82_ResultJob')
        e = t.find("transition/label[@kind='guard']")
        e.text = 'u0_raise_app_service_request_seq()'
        self.rejected('side effect in guard')

    def test_hidden_read_in_production_helper(self):
        d = self.root.find('declaration')
        d.text = d.text.replace('return true;', 'return u0_app_service_request_seq;', 1)
        self.rejected('hidden read/write in non-recorder helper')

    def test_recording_helper_retained_side_effect(self):
        d = self.root.find('declaration')
        d.text = d.text.replace('u0_app_service_request_seq = true;', 'u0_app_service_request_seq = true; c82_active = false;', 1)
        self.rejected('recorder must affect hidden state only')

    def test_unknown_callable(self):
        self.template().find("transition/label[@kind='guard']").text = 'unrecognized_external()'
        self.rejected('unknown callable syntax')

    def test_local_hidden_shadow(self):
        t = self.template('C82_ResultJob')
        ET.SubElement(t, 'declaration').text = 'bool u0_app_service_request_seq;'
        self.cap['locals']['C82_ResultJob'] = c.norm(t.findtext('declaration'))
        self.rejected('local hidden shadow')

    def test_binding_change(self):
        s = self.root.find('system')
        s.text = s.text.replace('c82_job = C82_ResultJob();', 'c82_job = SharedLoad();')
        self.rejected('one instance per template required')

    def test_priority(self):
        s = self.root.find('system')
        s.text = s.text.replace('u0_phy_A_CH_0, u0_phy_A_SIG_0', 'u0_phy_A_CH_0 < u0_phy_A_SIG_0')
        self.rejected('process priority unsupported')

    def test_hidden_query(self):
        self.rejected('query not retained-state predicate', 'A[] u0_app_service_request_seq')

    def test_observer_query(self):
        self.rejected('query refers to erased observer', 'E<> u0_obs_app_ObsAdmission_0.Violation')

    def test_deadlock_query(self):
        self.rejected('deadlock is not a projected state predicate', 'A[] not deadlock')

    def test_hash_gate_does_not_publish_invalid_output(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'certificate.json'
            p = subprocess.run([sys.executable, str(c.HERE / 'check.py'), '--repo', d,
                                '--output', str(out)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertFalse(out.exists())

    def test_certificate_is_reproducible_across_hash_seeds(self):
        with tempfile.TemporaryDirectory() as d:
            outputs = []
            for seed in ('1', '19'):
                out = Path(d) / (seed + '.json')
                env = os.environ.copy()
                env['PYTHONHASHSEED'] = seed
                p = subprocess.run([sys.executable, str(c.HERE / 'check.py'), '--repo', str(REPO),
                                    '--output', str(out)], capture_output=True, env=env)
                self.assertEqual(p.returncode, 0, p.stderr.decode(errors='replace'))
                outputs.append(out.read_bytes())
            self.assertEqual(outputs[0], outputs[1])


class SemanticControls(unittest.TestCase):
    def test_committed_partition_at_deadline(self):
        from fractions import Fraction as F
        for x in (F(0), F(5)-F(1,1000), F(5), F(5)+F(1,1000), F(999)):
            self.assertEqual(int(x <= 5) + int(x > 5), 1)
        self.assertFalse(F(5) < 5 or F(5) > 5)

    def test_deadlock_can_be_masked_by_observer_step(self):
        # Finite toy LTS: P has no transitions/delay; O can take Idle->Violation.
        production = {'p': []}
        monitored = {('p', 'Idle'): [('p', 'Violation')], ('p', 'Violation'): []}
        self.assertFalse(production['p'])
        self.assertTrue(monitored[('p', 'Idle')])
        self.assertFalse(monitored[('p', 'Violation')])

    def test_zero_time_observer_cycle_masks_global_deadlock_and_liveness(self):
        # P is deadlocked. Every O state has an internal zero-time successor.
        p_edges = {'stuck': []}
        o_edges = {'Idle': ['Wait'], 'Wait': ['Idle']}
        self.assertFalse(p_edges['stuck'])
        self.assertTrue(all(o_edges.values()))
        path = ['Idle']
        for _ in range(100):
            path.append(o_edges[path[-1]][0])
        self.assertEqual(len(set(path)), 2)
        self.assertEqual(set(['stuck'] * len(path)), {'stuck'})

    def test_polling_can_miss_a_transient_trigger(self):
        # Legal interleaving: raise trigger, clear trigger, then poll.
        trigger = False
        observer = 'Idle'
        trigger = True
        trigger = False
        if trigger:
            observer = 'Wait'
        self.assertEqual(observer, 'Idle')

    def test_polling_can_start_the_clock_late(self):
        from fractions import Fraction as F
        event, poll, deadline = F(0), F(7), F(5)
        self.assertGreater(poll - event, deadline)
        observer_clock = F(0)  # reset at poll, not at event
        self.assertLessEqual(observer_clock, deadline)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, default=REPO)
    args, remainder = p.parse_known_args()
    REPO = args.repo
    unittest.main(argv=[sys.argv[0]] + remainder)
