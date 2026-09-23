"""Actual accepted A_REC with replacement peer; synthetic recorder misuse controls."""
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
from uppaal_mcp.integrated.xmlutil import template,edge,normalize_order
from uppaal_mcp.integrated.adapt import RECOVERY_ATTEMPTS

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('recovery35',ROOT/'evidence/instantiation/20260917-recovery-contract/diagnostics.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
SAFE='A[] !sdn_attempt_bad'
PROTOCOL='A[] !sdn_attempt_protocol_error'


def synthetic(events):
    nta=ET.Element('nta');ET.SubElement(nta,'declaration').text=RECOVERY_ATTEMPTS
    names=[f'S{i}' for i in range(len(events)+1)]
    t=template('RecorderDriver',[(n,'',True) if i<len(events) else n for i,n in enumerate(names)])
    for i,event in enumerate(events):edge(t,names[i],names[i+1],update='sdn_attempt_'+event)
    normalize_order(t);nta.append(t)
    ET.SubElement(nta,'system').text='driver=RecorderDriver(); system driver;'
    ET.SubElement(nta,'queries');ET.indent(nta)
    return ET.tostring(nta,encoding='utf-8',xml_declaration=True,short_empty_elements=False)+b'\n'


def cases(xml):
    for route in ('standby','reembed','direct'):
        primary=0 if route=='direct' else 1
        rollback=1 if route=='direct' else 0
        yield route,r.focused(xml,route=route,ack=1),[(SAFE,True),(PROTOCOL,True),
            (f'E<> fx_done == 1 && !fx_failed && sdn_attempt_primary == {primary} && sdn_attempt_rollback == {rollback} && sdn_attempt_total == 1 && !sdn_attempt_active',True)],'Actual recovery core with controlled peer; stale/wrong typed ACK offers retained.'
    yield 'before-dispatch-failure',r.focused(xml,dispatch=99,ack=None),[(SAFE,True),(PROTOCOL,True),
        ('E<> fx_done == 1 && fx_failed && sdn_attempt_total == 0 && !sdn_attempt_active',True)],'No transport dispatch before local failure.'
    yield 'primary-rollback',r.focused(xml,ack=None),[(SAFE,True),(PROTOCOL,True),
        ('E<> sdn_attempt_primary == 1 && sdn_attempt_rollback == 1 && sdn_attempt_total == 2',True)],'Primary then rollback dispatch, no ACK.'
    for ack in (0,1):
        yield f'repeated-{ack}',r.focused(xml,repeat=True,ack=ack),[(SAFE,True),(PROTOCOL,True),
            ('E<> fx_done == 2 && sdn_attempt_primary == 1 && sdn_attempt_total == 1 && !sdn_attempt_active',True)],'Two real episodes; reset on accepted new failure, includes zero-time completion.'
    for name,events,bad,protocol,tail in [
        ('duplicate-primary',['start()','dispatch(false)','dispatch(false)'],True,False,'sdn_attempt_primary == 2 && sdn_attempt_total == 2'),
        ('duplicate-rollback',['start()','dispatch(true)','dispatch(true)'],True,False,'sdn_attempt_rollback == 2'),
        ('third-total',['start()','dispatch(false)','dispatch(true)','dispatch(false)'],True,False,'sdn_attempt_total == 3'),
        ('outside',['dispatch(false)'],False,True,'sdn_attempt_total == 1'),
        ('duplicate-start',['start()','dispatch(false)','start()'],False,True,'sdn_attempt_total == 1'),
        ('stale-finish',['start()','finish()','finish()'],False,True,'!sdn_attempt_active'),
        ('sticky-reset',['start()','dispatch(false)','dispatch(false)','finish()','start()'],True,False,'sdn_attempt_total == 0 && sdn_attempt_active'),
        ('saturating',['start()']+['dispatch(false)','dispatch(true)']*5,True,False,'sdn_attempt_primary == 2 && sdn_attempt_rollback == 2 && sdn_attempt_total == 3'),
        ('protocol-sticky',['dispatch(false)','start()'],False,True,'sdn_attempt_total == 0 && sdn_attempt_active'),
    ]:
        yield name,synthetic(events),[(SAFE,not bad),(PROTOCOL,not protocol),
            (f'E<> driver.S{len(events)} && ({tail})',True)],'Synthetic recorder-event sequence, not production reachability; negative controls exercise actual monitor functions.'
