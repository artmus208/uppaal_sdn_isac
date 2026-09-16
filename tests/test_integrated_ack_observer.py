"""Concrete ACK regressions and noninterference checks; not model checking."""
from copy import deepcopy
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.integrated.replay import Replay, expression
from uppaal_mcp.integrated.xmlutil import label, loc_id, set_label

ROOT = Path(__file__).resolve().parents[1]
MAC = 'mac_A_SCH_0'
OBS = 'obs_mac_ObsPhyAck_0'


class AckObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composition = generate(ROOT)

    def replay(self, xml=None):
        r = Replay(xml or self.composition.model_xml, processes=[MAC, OBS])
        r.locations[MAC] = loc_id(r.processes[MAC], 'ApplySchedule')
        return r

    def take(self, r, sync=None, target=None):
        choices = r.candidates(MAC, sync=sync, target=target)
        self.assertEqual(len(choices), 1)
        r.take([(MAC, choices[0], {})])

    def send(self, r):
        self.take(r, sync='mac_mac_schedule_cmd!')

    def assert_safe(self, r):
        self.assertEqual(r.candidates(OBS, target='Violation'), [])

    def test_preparation_does_not_start_observation(self):
        r = self.replay()
        r.values['mac_phy_command_pending'] = True
        r.advance(10)
        self.assert_safe(r)
        self.send(r)
        self.assertEqual(r.values['mac_c_obs_ack'], 0)
        self.assertTrue(r.values['mac_obs_ack_active'])

    def test_timely_ack_and_timeout_survive_delayed_observer(self):
        for outcome, delay in [('ack', 0), ('ack', 1), ('ack', 3), ('timeout', 3)]:
            with self.subTest(outcome=outcome, delay=delay):
                r = self.replay()
                self.send(r)
                r.advance(delay)
                if outcome == 'ack':
                    self.take(r, sync='mac_phy_ack?')
                else:
                    self.take(r, target='ScheduleFailure')
                r.advance(10)
                self.assertFalse(r.values['mac_obs_ack_active'])
                self.assert_safe(r)

    def test_successive_commands_reset_only_at_send(self):
        r = self.replay()
        for delay in [1, 3, 0, 2]:
            r.locations[MAC] = loc_id(r.processes[MAC], 'ApplySchedule')
            self.send(r)
            self.assertEqual(r.values['mac_c_obs_ack'], 0)
            r.advance(delay)
            self.take(r, sync='mac_phy_ack?')
            r.advance(5)
            self.assert_safe(r)

    def test_late_completion_is_retained_across_next_send(self):
        # Negative control: extend functional deadline only. Monitoring still
        # measures the stated three units; no observer step is taken before ACK.
        xml = ET.fromstring(self.composition.model_xml)
        sch = next(t for t in xml.findall('template') if t.findtext('name') == 'mac_Template_A_SCH')
        for inv in sch.findall("location/label[@kind='invariant']"):
            if 'mac_c_phy_ack' in inv.text:
                inv.text = 'mac_c_phy_ack <= 4'
        for tr in sch.findall('transition'):
            set_label(tr, 'guard', label(tr, 'guard').replace('mac_c_phy_ack <= mac_D_phy_ack', 'mac_c_phy_ack <= 4'))
        r = self.replay(ET.tostring(xml, encoding='unicode'))
        self.send(r)
        r.advance(3.5)
        self.assertTrue(r.candidates(OBS, target='Violation'))
        self.take(r, sync='mac_phy_ack?')
        self.assertTrue(r.values['mac_obs_ack_late'])
        r.locations[MAC] = loc_id(r.processes[MAC], 'ApplySchedule')
        self.send(r)
        self.assertEqual(r.values['mac_c_obs_ack'], 0)
        self.assertTrue(r.candidates(OBS, target='Violation'))

    def test_completion_partition_preserves_functional_edges(self):
        adaptation = next(a for a in self.composition.metadata['adaptations'] if a.get('process') == MAC)
        before, after = [ET.fromstring(adaptation[k]) for k in ('before_xml', 'after_xml')]
        original = [tr for tr in before.findall('transition') if tr.find('source').get('ref') == loc_id(before, 'WaitPHYAck')]
        for tr in original:
            copies = [x for x in after.findall('transition') if
                      x.find('source').get('ref') == tr.find('source').get('ref') and
                      x.find('target').get('ref') == tr.find('target').get('ref') and
                      label(x, 'synchronisation') == label(tr, 'synchronisation')]
            self.assertEqual(len(copies), 2)
            for functional_age in [0, 1, 3, 4]:
                for observed_age in [0, 1, 3, 3.5, 4]:
                    values = {'mac_c_phy_ack': functional_age, 'mac_c_obs_ack': observed_age, 'mac_D_phy_ack': 3}
                    enabled = sum(bool(expression(label(x, 'guard'), values)) for x in copies)
                    self.assertEqual(enabled, int(bool(expression(label(tr, 'guard'), values))))
            for x in copies:
                self.assertTrue(label(x, 'assignment').startswith(label(tr, 'assignment')))
        obs = next(t for t in ET.fromstring(self.composition.model_xml).findall('template') if t.findtext('name') == 'mac_Template_ObsPhyAck')
        self.assertFalse(obs.findall("location/label[@kind='invariant']"))
        self.assertFalse(obs.findall('location/committed'))
        self.assertFalse(obs.findall('location/urgent'))
        for tr in obs.findall('transition'):
            self.assertFalse(label(tr, 'assignment'))
            self.assertFalse(label(tr, 'synchronisation'))


if __name__ == '__main__':
    unittest.main()
