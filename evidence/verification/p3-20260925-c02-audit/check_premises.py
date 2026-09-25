"""Pinned syntactic premises of the C02 proof, NOT a model checker or general slicer."""
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT/'evidence/governance/20260906-baseline/gate1-20260923/model.xml'
REDUCED = ROOT/'evidence/verification/p3-20260924-c02-reduced/model.xml'
EXPECTED = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
V = {'mac_obs_ack_active','mac_obs_ack_late','mac_c_phy_ack','mac_c_obs_ack'}
pattern = re.compile(r'\b('+'|'.join(sorted(V))+r')\b')
norm = lambda s: re.sub(r'\s+', '', s or '')

def verify(root, abstract):
    declarations = root.findtext('declaration')
    assert 'const int mac_D_phy_ack = 3;' in declarations
    retained_lines = [line.strip() for line in declarations.splitlines() if pattern.search(line)]
    assert retained_lines == [
        'clock mac_c_sched, mac_c_phy_ack, mac_c_queue, mac_c_buf, mac_c_report;',
        'clock mac_c_obs_ack, mac_c_obs_queue, mac_c_obs_sensing, mac_c_obs_buf, mac_c_obs_report;',
        'bool mac_obs_ack_active = false;', 'bool mac_obs_ack_late = false;']
    # This also excludes passing retained variables by reference in global functions.
    for t in root.findall('template'):
        assert not pattern.search((t.findtext('declaration') or '')+(t.findtext('parameter') or ''))
    system = root.findtext('system')
    assert re.findall(r'(\w+)\s*=\s*mac_Template_A_SCH\s*\(\s*\)', system) == ['mac_A_SCH_0']
    assert re.search(r'\bsystem\s+([^;]+)', system).group(1).split(',').count(' mac_A_SCH_0') == 1
    sch = next(t for t in root.findall('template') if t.findtext('name') == 'mac_Template_A_SCH')
    loc = {l.get('id'):l.findtext('name') for l in sch.findall('location')}
    assert loc[sch.find('init').get('ref')] == 'Idle'
    wait = next(l for l in sch.findall('location') if l.findtext('name') == 'WaitPHYAck')
    assert norm(wait.findtext("label[@kind='invariant']")) == 'mac_c_phy_ack<=mac_D_phy_ack'
    edges = sch.findall('transition')
    assert len(edges) == 17
    writes = []
    for t in root.findall('template'):
        for index, edge in enumerate(t.findall('transition')):
            for label in edge.findall('label'):
                if label.get('kind') == 'assignment' and pattern.search(label.text or ''):
                    assert t is sch, 'Other template modifies/passes a retained variable'
                    retained = []
                    for part in (label.text or '').split(','):
                        if pattern.search(part):
                            assert re.fullmatch(r'(?:'+ '|'.join(V)+r')=(?:0|true|false)',norm(part)), 'Nonliteral write or reference argument'
                            retained.append(norm(part))
                    writes.append((index,retained))
    assert writes == [
        (2,['mac_c_phy_ack=0']), (4,['mac_c_phy_ack=0']),
        (5,['mac_c_phy_ack=0','mac_c_obs_ack=0','mac_obs_ack_active=true']),
        (6,['mac_obs_ack_active=false']), (7,['mac_obs_ack_active=false']),
        (9,['mac_obs_ack_active=false','mac_obs_ack_late=true']),
        (10,['mac_obs_ack_active=false','mac_obs_ack_late=true'])]
    crossed=[]
    for n,e in enumerate(edges):
        a,b=loc[e.find('source').get('ref')],loc[e.find('target').get('ref')]
        if (a=='WaitPHYAck') != (b=='WaitPHYAck'): crossed.append(n)
        if a==b=='WaitPHYAck':
            assert not pattern.search(e.findtext("label[@kind='assignment']") or '')
    assert crossed == [5,6,7,9,10]
    assert loc[edges[2].find('source').get('ref')] != 'WaitPHYAck'
    assert loc[edges[4].find('source').get('ref')] != 'WaitPHYAck'
    assert edges[5].findtext("label[@kind='synchronisation']") == 'mac_mac_schedule_cmd!'
    for n in [6,9]:
        assert loc[edges[n].find('target').get('ref')] == 'Idle'
        assert edges[n].findtext("label[@kind='synchronisation']") == 'mac_phy_ack?'
    for n in [7,10]:
        assert loc[edges[n].find('target').get('ref')] == 'ScheduleFailure'
        assert edges[n].findtext("label[@kind='synchronisation']") is None
    guards = {
        5:'', 6:'(mac_c_phy_ack<=mac_D_phy_ack)&&mac_c_obs_ack<=mac_D_phy_ack',
        7:'(mac_c_phy_ack==mac_D_phy_ack)&&mac_c_obs_ack<=mac_D_phy_ack',
        9:'(mac_c_phy_ack<=mac_D_phy_ack)&&mac_c_obs_ack>mac_D_phy_ack',
        10:'(mac_c_phy_ack==mac_D_phy_ack)&&mac_c_obs_ack>mac_D_phy_ack'}
    for n,g in guards.items(): assert norm(edges[n].findtext("label[@kind='guard']")) == g
    # No stopwatch dynamics for either retained clock.
    for label in root.iter('label'):
        if pattern.search(label.text or ''): assert "'" not in (label.text or '')
    t = abstract.find('template'); ae=t.findall('transition')
    assert len(abstract.findall('template'))==1 and len(t.findall('location'))==2 and len(ae)==7
    assert t.find('init').get('ref')=='idle'
    assert norm(abstract.findtext('declaration'))=='constintmac_D_phy_ack=3;clockmac_c_phy_ack,mac_c_obs_ack;boolmac_obs_ack_active=false,mac_obs_ack_late=false;'
    assert norm(t.findtext("location[@id='wait']/label[@kind='invariant']"))=='mac_c_phy_ack<=mac_D_phy_ack'
    assert norm(abstract.findtext('system'))=='Ack=C02Ack();systemAck;'
    for abstract_edge,n in zip(ae[:5],crossed):
        assert abstract_edge.find('source').get('ref')==('idle' if n==5 else 'wait')
        assert abstract_edge.find('target').get('ref')==('wait' if n==5 else 'idle')
        assert norm(abstract_edge.findtext("label[@kind='guard']"))==guards[n]
        assert norm(abstract_edge.findtext("label[@kind='assignment']"))==','.join(dict(writes)[n])
        assert abstract_edge.find("label[@kind='synchronisation']") is None
    for edge,location in zip(ae[5:],['idle','wait']):
        assert edge.find('source').get('ref')==edge.find('target').get('ref')==location
        assert not [l for l in edge.findall('label') if l.get('kind')!='comments']
    return {'scheduler_edges':17,'retained_write_edges':[n for n,_ in writes],
            'boundary_edges':crossed,'scheduler_instances':1,
            'static_premises':'matched pinned declarations, writers, clocks, guards, mappings and stutter edges'}

if __name__=='__main__':
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest()==EXPECTED
    root,abstract=E.parse(MODEL).getroot(),E.parse(REDUCED).getroot()
    report=verify(root,abstract)
    # Sensitivity checks: do not silently tolerate the exact changes that would
    # invalidate the local proof. These are in-memory mutants, no verifier runs.
    mutations=[]
    for kind in ['missing-invariant','external-reset','missing-active-exit']:
        r=copy.deepcopy(root)
        sch=next(t for t in r.findall('template') if t.findtext('name')=='mac_Template_A_SCH')
        if kind=='missing-invariant':
            l=next(l for l in sch.findall('location') if l.findtext('name')=='WaitPHYAck');l.remove(l.find("label[@kind='invariant']"))
        elif kind=='external-reset':
            e=r.find('template/transition');E.SubElement(e,'label',kind='assignment').text='mac_c_obs_ack = 0'
        else: sch.findall('transition')[6].find("label[@kind='assignment']").text='mac_phy_command_pending = false'
        try: verify(r,abstract)
        except AssertionError: mutations.append(kind)
        else: raise AssertionError('Mutation not rejected: '+kind)
    report.update(kind='static proof-premise audit, NOT model checking',full_model_hash=EXPECTED,
                  reduced_model_hash=hashlib.sha256(REDUCED.read_bytes()).hexdigest(),rejected_mutations=mutations)
    print(json.dumps(report,indent=2))
