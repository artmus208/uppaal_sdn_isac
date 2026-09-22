"""Actual MAC load transition with explicit diagnostic input restrictions.

Not the complete network: peers are removed, nonqueue selections are held at
zero, and initial queue/mode plus arrival/service choices are case parameters.
"""
import xml.etree.ElementTree as ET
from uppaal_mcp.integrated.xmlutil import label, set_label


def focused(xml, *, q=0, mode=0, arrival=None, service=None, clipped=False):
    nta = ET.fromstring(xml)
    for t in list(nta.findall('template')):
        if t.findtext('name') != 'Boundary_E_MAC_LOAD':
            nta.remove(t)
    declaration = nta.findtext('declaration')
    declaration = declaration.replace('mac_queue_q=0;',f'mac_queue_q={q};')
    declaration = declaration.replace('mac_queue_overflow_seen=false;',
                                      f'mac_queue_overflow_seen={str(q==5).lower()};')
    declaration = declaration.replace('mac_scheduleMode = mac_SCH_IDLE;',f'mac_scheduleMode = {mode};')
    declaration = declaration.replace('mac_queueClass = mac_Q_EMPTY;',f'mac_queueClass = {min(q,4)};')
    nta.find('declaration').text = declaration
    load = nta.find('template')
    sample = load.find('transition')
    restrictions = [f'm{i} == 0' for i in range(1,7)]
    if arrival is not None:
        restrictions.append(f'arrival == {arrival}')
    if service is not None:
        restrictions.append(f'service == {service}')
    set_label(sample,'guard',label(sample,'guard')+' && '+' && '.join(restrictions))
    if clipped:
        # Deliberately incorrect negative control: suppress the overflow witness.
        set_label(sample,'assignment',label(sample,'assignment').replace(
            'mac_queue_q > mac_queue_K ? mac_queue_q',
            'mac_queue_q >= mac_queue_K ? mac_queue_q'))
    nta.find('system').text = 'load=Boundary_E_MAC_LOAD();\nsystem load;'
    ET.indent(nta)
    return ET.tostring(nta,encoding='utf-8',xml_declaration=True,short_empty_elements=False)+b'\n'


def cases(xml):
    safe = 'A[] !mac_queue_overflow_seen'
    overflow = 'E<> mac_queue_overflow_seen'
    mapping = ('A[] ((mac_queue_q == 0 imply mac_queueClass == mac_Q_EMPTY) && '
               '(mac_queue_q == 1 imply mac_queueClass == mac_Q_LOW) && '
               '(mac_queue_q == 2 imply mac_queueClass == mac_Q_MED) && '
               '(mac_queue_q == 3 imply mac_queueClass == mac_Q_HIGH) && '
               '(mac_queue_q >= 4 imply mac_queueClass == mac_Q_CRIT))')
    yield 'empty', focused(xml,arrival=0), [(safe,True),('A[] mac_queue_q == 0',True)], 'empty queue, no arrivals'
    yield 'fill', focused(xml,arrival=1,service=0), [
        (safe,False),(overflow,True),('E<> mac_queue_q == 4 && !mac_queue_overflow_seen',True),
        ('E<> mac_queue_overflow_seen && bus_time == 25',True),
        ('A[] (bus_time < 25 imply !mac_queue_overflow_seen)',True),
        ('A[] (mac_queue_overflow_seen imply mac_queue_q == 5)',True),
        (mapping,True)], 'five admitted work units with no service, expected violation'
    yield 'full-arrival', focused(xml,q=4,arrival=1,service=0), [(safe,False),(overflow,True)], 'arrival at capacity remains enabled'
    yield 'simultaneous', focused(xml,q=4,mode=1,arrival=1,service=1), [
        (safe,True),('A[] mac_queue_q == 4',True),('E<> bus_time >= 15',True)], 'old service before arrival at capacity'
    yield 'overflow-retained', focused(xml,q=5,mode=3,arrival=0,service=1), [
        ('A[] mac_queue_overflow_seen && mac_queue_q == 5',True),
        ('E<> bus_time >= 15',True)], 'post-overflow service cannot erase witness'
    for mode in range(5):
        yield f'service-mode-{mode}', focused(xml,q=4,mode=mode,arrival=0), [
            (safe,True),('E<> mac_queue_q == 0',mode in (1,3)),
            ('E<> mac_queue_q == 4 && bus_time >= 15',True)], 'optional service; only COMM and JOINT eligible'
    yield 'clipped-mutant', focused(xml,arrival=1,service=0,clipped=True), [
        (safe,True),(overflow,False)], 'deliberate broken saturation at K; reachability detects false safety'
