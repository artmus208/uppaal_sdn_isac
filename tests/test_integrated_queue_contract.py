"""Concrete queue edge regressions, not timed-automata model checking."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.integrated.replay import Replay
from uppaal_mcp.integrated.xmlutil import label, source_name

ROOT = Path(__file__).resolve().parents[1]
PROCESS = 'boundary_E_MAC_LOAD_0'


class QueueContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composition = generate(ROOT)
        cls.xml = ET.fromstring(cls.composition.model_xml)

    def replay(self, q=0, mode=1, overflow=False):
        return Replay(self.composition.model_xml,
                      {'mac_queue_q':q, 'mac_scheduleMode':mode,
                       'mac_queue_overflow_seen':overflow}, processes=[PROCESS])

    def selection(self, arrival, service):
        return dict(arrival=arrival, service=service, **{f'm{i}':0 for i in range(1,7)})

    def tick(self, replay, arrival, service):
        replay.advance(5)
        selected = self.selection(arrival, service)
        edges = replay.candidates(PROCESS, target='Publish', select=selected)
        self.assertEqual(len(edges), 1)
        replay.take([(PROCESS, edges[0], selected)])
        replay.take([(PROCESS, replay.candidates(PROCESS, target='Offer')[0], {})])
        # Losing the scheduler tick cannot undo the preceding load event.
        replay.take([(PROCESS, replay.candidates(PROCESS, target='Wait', sync='')[0], {})])

    def test_every_queue_mode_arrival_service_boundary(self):
        for q in range(6):
            for mode in range(5):
                for arrival in range(2):
                    for service in range(2):
                        with self.subTest(q=q, mode=mode, arrival=arrival, service=service):
                            r = self.replay(q, mode, overflow=(q==5))
                            r.advance(5)
                            choice = self.selection(arrival, service)
                            edges = r.candidates(PROCESS, target='Publish', select=choice)
                            allowed = service <= q and (service==0 or mode in (1,3))
                            self.assertEqual(bool(edges), allowed)
                            if not allowed:
                                continue
                            r.take([(PROCESS, edges[0], choice)])
                            expected = 5 if q==5 else q-service+arrival
                            self.assertEqual(r.values['mac_queue_q'], expected)
                            self.assertEqual(r.values['mac_queue_overflow_seen'], expected==5)
                            self.assertEqual(r.values['mac_queueClass'], [0,1,2,3,4,4][expected])

    def test_full_queue_arrival_is_enabled_and_records_overflow(self):
        r = self.replay(q=4, mode=0)
        self.tick(r, arrival=1, service=0)
        self.assertEqual(r.values['mac_queue_q'],5)
        self.assertTrue(r.values['mac_queue_overflow_seen'])
        self.assertTrue(r.values['bus_tick_missed'])
        self.assertIn('int[0,mac_queue_K+1] mac_queue_q=0;',self.xml.findtext('declaration'))

    def test_optional_service_permits_filling_from_empty(self):
        r = self.replay(mode=1)
        for expected in range(1,6):
            self.tick(r,1,0)
            self.assertEqual(r.values['mac_queue_q'],expected)
        r.values['mac_scheduleMode']=3
        for _ in range(3):
            self.tick(r,0,1)
            self.assertEqual(r.values['mac_queue_q'],5)
            self.assertTrue(r.values['mac_queue_overflow_seen'])

    def test_service_before_arrival_at_capacity_and_empty_no_underflow(self):
        full = self.replay(q=4,mode=3)
        self.tick(full,1,1)
        self.assertEqual(full.values['mac_queue_q'],4)
        self.assertFalse(full.values['mac_queue_overflow_seen'])
        empty = self.replay()
        self.tick(empty,0,0)
        self.assertEqual(empty.values['mac_queue_q'],0)

    def test_only_load_tick_writes_queue_and_class(self):
        writers = []
        for t in self.xml.findall('template'):
            for tr in t.findall('transition'):
                if any(re.search(r'(?:^|,)\s*'+name+r'\s*=(?!=)',label(tr,'assignment'))
                       for name in ('mac_queue_q','mac_queue_overflow_seen','mac_queueClass')):
                    writers.append((t.findtext('name'),source_name(t,tr)))
        self.assertEqual(writers,[('Boundary_E_MAC_LOAD','Wait')])
        # Thus neither ACK, QueueDraining nor resource_reject can dequeue.

    def test_nonqueue_samples_and_offer_protocol_are_preserved(self):
        r = self.replay()
        r.advance(5)
        selected = dict(arrival=0,service=0,m1=2,m2=3,m3=2,m4=3,m5=2,m6=2)
        tr = r.candidates(PROCESS,target='Publish',select=selected)[0]
        r.take([(PROCESS,tr,selected)])
        for name,value in [('bufferClass',2),('delayClass',3),('dropClass',2),
                           ('resourceClass',3),('sensingDemand',2),('commDemand',2)]:
            self.assertEqual(r.values['mac_'+name],value)
        self.assertEqual(r.values['mac_queue_q'],0)  # B_OVERFLOW is independent.
        self.assertTrue(r.values['bus_mac_valid'])
        self.assertEqual(r.values['bus_mac_age'],0)
        t = r.processes[PROCESS]
        self.assertEqual([source_name(t,x) for x in t.findall('transition')],
                         ['Wait','Publish','Offer','Offer'])
        self.assertEqual([label(x,'synchronisation') for x in t.findall('transition')],
                         ['', 'bus_new_mac_sample!', 'mac_mac_tick!', ''])
        self.assertEqual(len(t.findall('location/committed')),2)

    def test_metadata_and_candidate_properties_expose_new_semantics(self):
        m = self.composition.metadata
        self.assertEqual(m['parameter_set']['mac_queue'],dict(K=4,L=1,M=2,H=4))
        self.assertEqual(m['configuration_id'],'p2-single-uav-abstract-v2-queue-candidate')
        self.assertFalse(m['queue_abstraction']['service_guaranteed'])
        self.assertEqual(m['verification_status'],'not_run')
        self.assertEqual(len(m['system_order']),50)
        queries = {q['id']:q for q in m['query_map'] if q['id'].startswith('queue-')}
        self.assertEqual(set(queries),{'queue-capacity','queue-nonempty','queue-full','queue-overflow'})
        self.assertEqual(queries['queue-capacity']['candidate'],'A[] !mac_queue_overflow_seen')
        self.assertTrue(all(q['status']=='candidate_unverified' for q in queries.values()))


if __name__ == '__main__':
    unittest.main()
