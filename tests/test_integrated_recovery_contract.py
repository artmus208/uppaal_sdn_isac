"""Structural noninterference/provenance checks; machine diagnostics live in #35 evidence."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from uppaal_mcp.integrated.adapt import record_recovery, recovery_policy
from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.integrated.replay import expression
from uppaal_mcp.integrated.xmlutil import label, source_name, loc_id

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'evidence/instantiation/20260917-recovery-contract/diagnostics.py'
spec = importlib.util.spec_from_file_location('recovery_diagnostics', PATH)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


class RecoveryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # GitHub Actions uses a shallow checkout. The immutable historical XML
        # is already tracked; pin its bytes without requiring an ancestor object.
        original = (ROOT / diag.BASE_MODEL).read_bytes()
        if hashlib.sha256(original).hexdigest() != 'f4c439704d9c5a358b06744dfb25728564c8c26c72923fd6f3307860aedfb446':
            raise ValueError('Historical recovery input hash mismatch')
        cls.old = ET.fromstring(original)
        cls.new = ET.fromstring(generate(ROOT).model_xml)

    def core(self, root):
        return deepcopy(next(t for t in root.findall('template') if t.findtext('name') == diag.REC))

    def test_recorder_partition_erases_to_original_functional_edges(self):
        before = self.core(self.old)
        after = deepcopy(before)
        record_recovery(after)
        # Invariants, locations, init, declarations, channel identities unchanged.
        self.assertEqual([ET.tostring(x) for x in before if x.tag != 'transition'],
                         [ET.tostring(x) for x in after if x.tag != 'transition'])
        for tr in before.findall('transition'):
            copies = [x for x in after.findall('transition') if
                      x.find('source').attrib == tr.find('source').attrib and
                      x.find('target').attrib == tr.find('target').attrib and
                      label(x, 'synchronisation') == label(tr, 'synchronisation')]
            end = source_name(before, tr) not in ('StableConfig', 'RecoveryFailed') and tr.find('target').get('ref') in (loc_id(before, 'StableConfig'), loc_id(before, 'RecoveryFailed'))
            self.assertEqual(len(copies), 2 if end else 1)
            for x in copies:
                assignments = label(x, 'assignment')
                for update in (', sdn_obs_rec_finish()', ', sdn_obs_rec_start()', ', sdn_obs_rec_late = true'):
                    assignments = assignments.replace(update, '')
                self.assertEqual(assignments, label(tr, 'assignment'))
            if end:
                for core_age in (0, 10, 20, 30, 31):
                    for age in (0, 29, 30, 30.5, 31, 100):
                        values = dict(sdn_c_rec=core_age, sdn_c_rollback=core_age, sdn_c_obs_rec=age, sdn_D_recovery=20, sdn_D_rollback=10)
                        self.assertEqual(sum(bool(expression(label(x, 'guard'), values)) for x in copies),
                                         int(bool(expression(label(tr, 'guard') or 'true', values))))

    def test_fallback_is_local_in_all_three_dispatch_phases(self):
        t = self.core(self.new)
        for phase in ('FailureDetected', 'StandbySwitch', 'ReactiveReembedding'):
            loc = next(l for l in t.findall('location') if l.findtext('name') == phase)
            self.assertEqual(loc.findtext("label[@kind='invariant']"), 'sdn_c_rec <= sdn_D_recovery')
            failures = [x for x in t.findall('transition') if source_name(t, x) == phase and x.find('target').get('ref') == loc_id(t, 'RecoveryFailed')]
            self.assertEqual(len(failures), 2)
            for x in failures:
                self.assertEqual(label(x, 'synchronisation'), '')
                self.assertIn('sdn_recovery_failure_kind = 1', label(x, 'assignment'))
                self.assertIn('sdn_c_rec == sdn_D_recovery', label(x, 'guard'))

    def test_report_is_separate_from_local_rollback_failure(self):
        t = self.core(self.new)
        fail = [x for x in t.findall('transition') if source_name(t, x) == 'Rollback' and x.find('target').get('ref') == loc_id(t, 'RecoveryFailed')]
        self.assertEqual(len(fail), 2)
        for x in fail:
            self.assertFalse(label(x, 'synchronisation'))
            self.assertIn('sdn_recovery_failure_kind = 2', label(x, 'assignment'))
            self.assertIn('sdn_failure_report_sent = false', label(x, 'assignment'))
        report = [x for x in t.findall('transition') if label(x, 'synchronisation') == 'sdn_failure_report!']
        self.assertEqual(len(report), 1)
        self.assertEqual(source_name(t, report[0]), 'RecoveryFailed')
        self.assertNotIn('sdn_obs_rec_', label(report[0], 'assignment'))

    def test_only_recovery_templates_change_and_observer_is_passive(self):
        old = {t.findtext('name'): t for t in self.old.findall('template')}
        new = {t.findtext('name'): t for t in self.new.findall('template')}
        self.assertEqual(set(old), set(new))
        # Ignore pretty-print whitespace, retain every semantic attribute/label.
        def shape(x):
            return (x.tag, x.attrib, (x.text or '').strip(), [shape(c) for c in x])
        for name in old.keys() - {diag.REC, diag.OBS}:
            self.assertEqual(shape(old[name]), shape(new[name]), name)
        obs = new[diag.OBS]
        self.assertFalse(obs.findall("location/label[@kind='invariant']"))
        self.assertFalse(obs.findall('location/committed') + obs.findall('location/urgent'))
        for tr in obs.findall('transition'):
            self.assertFalse(label(tr, 'assignment') or label(tr, 'synchronisation'))
        # Wrong typed ACKs cannot complete another phase.
        t = new[diag.REC]
        for phase, ch in [('StandbySwitch', 'bus_rec_policy_ack?'), ('ReactiveReembedding', 'bus_rec_flow_ack?'), ('Rollback', 'bus_rec_rollback_ack?')]:
            acks = {label(x, 'synchronisation') for x in t.findall('transition') if source_name(t, x) == phase and label(x, 'synchronisation').endswith('_ack?')}
            self.assertEqual(acks, {ch})

    def test_policy_and_recording_compose_as_separate_layers(self):
        t = self.core(self.old)
        recovery_policy(t)
        record_recovery(t)
        actual = self.core(self.new)
        def transitions(x):
            return sorted((source_name(x, tr), tr.find('target').get('ref'), label(tr, 'guard'), label(tr, 'synchronisation'), label(tr, 'assignment')) for tr in x.findall('transition'))
        self.assertEqual(transitions(t), transitions(actual))


if __name__ == '__main__':
    unittest.main()
