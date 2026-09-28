#!/usr/bin/env python3
"""Static contract, local step evaluation and negative controls; NOT model checking."""
import copy
import itertools
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import generate as g


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def canonical(element):
    return (element.tag, tuple(sorted(element.attrib.items())), (element.text or '').strip(),
            tuple(canonical(e) for e in element))


def text(e, kind):
    return e.findtext(f"label[@kind='{kind}']") or ''


def unprefix(t, i):
    t = copy.deepcopy(t)
    for e in t.iter():
        if e.text:
            e.text = re.sub(rf'\bu{i}_', '', e.text)
        for k in ('id','ref'):
            if k in e.attrib:
                e.set(k, re.sub(rf'^u{i}_', '', e.get(k)))
    return t


def validate(root, n):
    source = ET.parse(g.ROOT / g.FROZEN / 'model.xml').getroot()
    templates = root.findall('template')
    names = [t.findtext('name') for t in templates]
    need(len(names) == 49*n+1 and len(set(names)) == len(names), 'unique process/template count')
    need(names.count('SharedLoad') == 1, 'one shared load server')
    ids = [x.get('id') for x in root.findall('.//location')]
    need(len(ids) == len(set(ids)), 'globally unique locations')
    for t in templates:
        local_ids = {x.get('id') for x in t.findall('location')}
        need(t.find('init').get('ref') in local_ids, 'init reference')
        for e in t.findall('transition'):
            need(e.find('source').get('ref') in local_ids and e.find('target').get('ref') in local_ids, 'edge reference')
    # Read exact old behavior independently of build()/renamed().
    for i in range(n):
        for old in source.findall('template'):
            name = old.findtext('name')
            if name == g.LOAD:
                continue
            matches = [t for t in templates if t.findtext('name') == f'u{i}_{name}']
            need(len(matches) == 1, f'private template {i}/{name}')
            new = matches[0]
            tokens = re.findall(r'\bu(\d+)_', ET.tostring(new, encoding='unicode'))
            need(all(int(k) == i for k in tokens), 'cross-entity state/clock/channel reference')
            need(canonical(unprefix(new,i)) == canonical(old), f'frozen template changed: {i}/{name}')
    decl = root.findtext('declaration')
    # Each private declaration block is exactly the old block after alpha-renaming.
    pos = decl.index('// Candidate abstract units')
    blocks = decl[pos:].split('// Candidate abstract units')
    need(len(blocks) == n+1, 'private declaration block count')
    for i, b in enumerate(blocks[1:]):
        restored = re.sub(rf'\bu{i}_', '', '// Candidate abstract units'+b).strip()
        need(restored == source.findtext('declaration').strip(), 'global state/function/clock isolation')
    expected_order = []
    old_bindings, old_system = source.findtext('system').split('system ')
    bindings = []
    for i in range(n):
        for line in old_bindings.splitlines():
            if line.strip() and not line.startswith(g.LOAD_PROCESS+' ='):
                name, rhs = line.split(' = ')
                bindings.append(f'u{i}_{name} = u{i}_{rhs}')
        for name in old_system.strip().rstrip(';').split(', '):
            if name != g.LOAD_PROCESS:
                expected_order.append(f'u{i}_{name}')
            elif i == 0:
                expected_order.append('shared_load')
    bindings.append('shared_load = SharedLoad();')
    expected_system = '\n'.join(bindings)+'\nsystem '+', '.join(expected_order)+';'
    need(root.findtext('system') == expected_system, 'instance bindings and broadcast receiver order')
    shared = next(t for t in templates if t.findtext('name') == 'SharedLoad')
    need(shared.findtext('declaration').splitlines()[0] == 'clock tick;', 'single shared epoch clock')
    locations = {l.get('id'):l for l in shared.findall('location')}
    need(len(locations) == 1+3*n, 'shared locations count')
    need(text(locations['shared_Wait'],'invariant') == 'tick <= u0_bus_T_mac_tick', 'shared period invariant')
    for i in range(n):
        for kind in ('Publish','Offer'):
            need(locations[f'shared_{kind}_{i}'].find('committed') is not None, 'zero-time delivery chain')
    edges = shared.findall('transition')
    need(len(edges) == 1+4*n, 'shared edge count')
    for i,e in enumerate(edges[:n]):
        need(locations[f'shared_Sample_{i+1}'].find('committed') is not None, 'staging is zero-time')
        need(e.find('source').get('ref') == ('shared_Wait' if i==0 else f'shared_Sample_{i}') and e.find('target').get('ref') == f'shared_Sample_{i+1}', 'sample staging chain')
        need(text(e,'guard') == ('tick == u0_bus_T_mac_tick' if i==0 else ''), 'sample staging guard')
        expected_select='pick_arrival:int[0,1], pick_m1:int[0,2], pick_m2:int[0,3], pick_m3:int[0,2], pick_m4:int[0,3], pick_m5:int[0,2], pick_m6:int[0,2]'
        need(text(e,'select')==expected_select, 'unchanged finite sample domains')
        need(text(e,'assignment')==', '.join(f'{name}_{i}=pick_{name}' for name in ['arrival']+[f'm{k}' for k in range(1,7)]), 'private sample scratch state')
    need(edges[n].find('source').get('ref') == f'shared_Sample_{n}' and edges[n].find('target').get('ref') == 'shared_Publish_0', 'atomic service step')
    selects = text(edges[n],'select')
    need(selects.startswith(f'server:int[-1,{n-1}]'), 'single bounded shared service selector')
    need('service:' not in selects, 'no independent service selectors')
    # Validate all shared notification channels and their intended receivers.
    endpoints = []
    for t in templates:
        for e in t.findall('transition'):
            if text(e,'synchronisation'):
                endpoints.append({'template':t.findtext('name'), 'channel':text(e,'synchronisation')})
    for i in range(n):
        pub, offer, skip = edges[n+1+3*i:n+4+3*i]
        target = f'shared_Publish_{i+1}' if i+1<n else 'shared_Wait'
        need((pub.find('source').get('ref'),pub.find('target').get('ref'),text(pub,'synchronisation')) ==
             (f'shared_Publish_{i}', f'shared_Offer_{i}', f'u{i}_bus_new_mac_sample!'), 'shared publication routing')
        need(text(offer,'synchronisation') == f'u{i}_mac_mac_tick!', 'shared tick routing')
        for e in (pub,offer,skip):
            need(not text(e,'guard') and not text(e,'select'), 'delivery must remain unconditional')
        for e in (offer,skip):
            need(e.find('source').get('ref') == f'shared_Offer_{i}' and e.find('target').get('ref') == target, 'delivery chain')
        need(not text(skip,'synchronisation') and text(skip,'assignment') == f'u{i}_bus_tick_missed=true', 'nonblocking per-entity missed tick')
        for channel, receiver in [(f'u{i}_mac_mac_tick?',f'u{i}_mac_Template_A_SCH'),(f'u{i}_bus_new_mac_sample?',f'u{i}_Boundary_B_KPI')]:
            receivers = {e['template'] for e in endpoints if e['channel']==channel}
            need(receivers == {receiver}, 'shared channel receiver binding')
    return shared, endpoints


# Restricted expression parser for the emitted load-step C-like expressions.
# It executes guards/ordered assignments extracted from XML, not a duplicate step.
TOKEN = re.compile(r'\s*(\d+|[A-Za-z_]\w*|&&|\|\||==|!=|<=|>=|[?:()+\-<>!])')
OPS = [['||'], ['&&'], ['==','!='], ['<','>','<=','>='], ['+','-']]


def parse(s):
    tokens=[]; pos=0
    while pos<len(s):
        m=TOKEN.match(s,pos)
        need(m is not None, f'unsupported expression: {s[pos:]}')
        tokens.append(m[1]); pos=m.end()
    p=0
    def expr(level=0):
        nonlocal p
        if level == len(OPS):
            tok=tokens[p]; p+=1
            if tok == '(':
                node=ternary(); need(tokens[p]==')','closing paren'); p+=1
            elif tok == '!':
                node=('!',expr(level))
            else:
                node=tok
            return node
        node=expr(level+1)
        while p<len(tokens) and tokens[p] in OPS[level]:
            op=tokens[p]; p+=1; node=(op,node,expr(level+1))
        return node
    def ternary():
        nonlocal p
        node=expr()
        if p<len(tokens) and tokens[p]=='?':
            p+=1; yes=ternary(); need(tokens[p]==':','ternary colon'); p+=1
            node=('?',node,yes,ternary())
        return node
    node=ternary(); need(p==len(tokens),'trailing expression'); return node


def evaluate(node, state):
    if isinstance(node,str):
        if node.isdecimal(): return int(node)
        if node in ('true','false'): return node=='true'
        return state[node]
    op=node[0]; a=evaluate(node[1],state)
    if op=='!': return not a
    if op=='?': return evaluate(node[2] if a else node[3],state)
    b=evaluate(node[2],state)
    return {'+':lambda:a+b,'-':lambda:a-b,'&&':lambda:bool(a and b),'||':lambda:bool(a or b),
            '==':lambda:a==b,'!=':lambda:a!=b,'<':lambda:a<b,'>':lambda:a>b,'<=':lambda:a<=b,'>=':lambda:a>=b}[op]()


def program(update):
    return [(s.split('=',1)[0].strip(),parse(s.split('=',1)[1].strip())) for s in update.split(',')]


def execute(prog,state):
    state=dict(state)
    for name,expr in prog: state[name]=evaluate(expr,state)
    return state


def constants(prefix):
    return {prefix+k:v for k,v in {'bus_T_mac_tick':5,'mac_queue_K':4,'mac_queue_L':1,'mac_queue_M':2,'mac_queue_H':4,
        'mac_Q_EMPTY':0,'mac_Q_LOW':1,'mac_Q_MED':2,'mac_Q_HIGH':3,'mac_Q_CRIT':4,
        'mac_SCH_IDLE':0,'mac_SCH_COMM':1,'mac_SCH_SENS':2,'mac_SCH_JOINT':3,'mac_SCH_CONSTRAINED':4}.items()}


def evaluate_steps(shared,n):
    edge=next(e for e in shared.findall('transition') if text(e,'select').startswith('server:'))
    guard=parse(text(edge,'guard')); updates=program(text(edge,'assignment'))
    count=0; outcomes=set()
    # Exhaustive queue/mode/arrival/service/old-sticky combinations, including overflow sentinel.
    for qs in itertools.product(range(6),repeat=n):
      for modes in itertools.product(range(5),repeat=n):
       for arrivals in itertools.product(range(2),repeat=n):
        for server in range(-1,n):
         for sticky in (False,True):
          state={'tick':5,'server':server}
          for i in range(n):
            state.update(constants(f'u{i}_'))
            state.update({f'u{i}_mac_queue_q':qs[i], f'u{i}_mac_scheduleMode':modes[i],
                          f'u{i}_mac_queue_overflow_seen':sticky,f'arrival_{i}':arrivals[i]})
            state.update({f'm{k}_{i}':(i+k)%3 for k in range(1,7)})
          expected = server==-1 or (qs[server]>0 and modes[server] in (1,3))
          need(bool(evaluate(guard,state)) == expected, 'shared eligibility differs from service contract')
          if not expected: continue
          after=execute(updates,state)
          need(sum(bool(after[f'family_grant_{i}']) for i in range(n))<=1,'shared capacity exceeded')
          for i in range(n):
            q=qs[i] if qs[i]>4 else qs[i]-int(server==i)+arrivals[i]
            need(after[f'u{i}_mac_queue_q']==q, 'wrong entity queue/service update')
            need(after[f'u{i}_mac_queue_overflow_seen']==(sticky or q>4), 'sticky overflow lost')
            klass=0 if q==0 else 1 if q<=1 else 2 if q<=2 else 3 if q<4 else 4
            need(after[f'u{i}_mac_queueClass']==klass,'queue class derived before update')
            for k,field in enumerate(('bufferClass','delayClass','dropClass','resourceClass','sensingDemand','commDemand'),1):
                need(after[f'u{i}_mac_{field}']==state[f'm{k}_{i}'], 'cross-entity sampled load')
            need(after[f'u{i}_bus_mac_age']==0 and after[f'u{i}_bus_mac_valid'], 'entity sample metadata')
          if n==2 and qs==(1,1) and modes==(1,1) and arrivals==(0,0):
            outcomes.add(tuple(after[f'u{i}_mac_queue_q'] for i in range(n)))
          count+=1
    if n==2:
        need(outcomes=={(1,1),(0,1),(1,0)}, 'competition witness; two independent queues would allow (0,0)')
    # Period cannot fire early or late under its guard.
    for time in (0,4,6):
        state['tick']=time; need(not evaluate(guard,state),'period guard')
    return count


def singleton_correspondence(shared):
    source=ET.parse(g.ROOT/g.FROZEN/'model.xml').getroot()
    old=next(t for t in source.findall('template') if t.findtext('name')==g.LOAD).findall('transition')[0]
    og=parse(text(old,'guard')); op=program(text(old,'assignment'))
    new=next(e for e in shared.findall('transition') if text(e,'select').startswith('server:')); ng=parse(text(new,'guard')); np=program(text(new,'assignment'))
    count=0
    for q,mode,a,service in itertools.product(range(6),range(5),range(2),range(2)):
        st=constants(''); st.update({'tick':5,'mac_queue_q':q,'mac_scheduleMode':mode,'mac_queue_overflow_seen':False,'arrival':a,'service':service})
        st.update({f'm{k}': k%3 for k in range(1,7)})
        ns={('u0_'+k if k.startswith(('mac_','bus_')) else k):v for k,v in st.items() if k not in ['arrival','service'] and not re.fullmatch('m[1-6]',k)}
        ns.update({'server':0 if service else -1,'arrival_0':a,**{f'm{k}_0':k%3 for k in range(1,7)}})
        need(evaluate(og,st)==evaluate(ng,ns),'N=1 eligibility correspondence')
        if not evaluate(og,st): continue
        oa,na=execute(op,st),execute(np,ns)
        for name,_ in op:
            need(oa[name]==na['u0_'+name if name.startswith(('mac_','bus_')) else name], 'N=1 ordered update correspondence')
        count+=1
    return count


def negative_controls(root):
    controls=[]
    def reject(name, mutate):
        mutant=copy.deepcopy(root); mutate(mutant)
        try:
            shared,_=validate(mutant,2); evaluate_steps(shared,2)
        except (AssertionError,KeyError): controls.append(name)
        else: raise AssertionError('undetected mutation: '+name)
    def replace_first(r,tag,old,new):
        for e in r.iter(tag):
            if e.text and old in e.text:
                e.text=e.text.replace(old,new,1); return
        raise AssertionError('mutation anchor absent')
    reject('cross-entity queue state',lambda r:replace_first(r,'label','u0_mac_queue_q','u1_mac_queue_q'))
    reject('cross-entity clock',lambda r:replace_first(r,'label','u0_mac_c_phy_ack','u1_mac_c_phy_ack'))
    reject('cross-entity ACK',lambda r:replace_first(r,'label','u0_mac_phy_ack?','u1_mac_phy_ack?'))
    reject('cross-entity scratch input',lambda r:replace_first(r,'label','arrival_1=pick_arrival','arrival_0=pick_arrival'))
    reject('wrong shared tick destination',lambda r:replace_first(r,'label','u1_mac_mac_tick!','u0_mac_mac_tick!'))
    reject('wrong shared sample destination',lambda r:replace_first(r,'label','u1_bus_new_mac_sample!','u0_bus_new_mac_sample!'))
    reject('global clock alias',lambda r:replace_first(r,'declaration','clock u1_mac_c_sched','clock u0_mac_c_sched'))
    reject('independent second queue service',lambda r:replace_first(r,'label','u1_mac_queue_q-(server == 1 ? 1 : 0)','u1_mac_queue_q-(server == 0 ? 1 : 0)'))
    reject('lost zero-time delivery',lambda r:r.find("template[name='SharedLoad']/location[@id='shared_Publish_1']").remove(r.find("template[name='SharedLoad']/location[@id='shared_Publish_1']/committed")))
    reject('wrong instance binding',lambda r:replace_first(r,'system','u1_app_Req_0 = u1_app_A_REQ()','u1_app_Req_0 = u0_app_A_REQ()'))
    reject('duplicate shared server',lambda r:r.append(copy.deepcopy(r.find("template[name='SharedLoad']"))))
    return controls


def main():
    pins=g.inputs(); result={'evidence_kind':'static_validation','property_verdict':'not_applicable','sizes':{}}
    for n in (1,2):
        files=g.artifacts(n,pins)
        for name,data in files.items():
            need((g.HERE/'generated'/f'n{n}'/name).read_bytes()==data,'deterministic reproduction '+name)
        need(b'<queries></queries>' in files['model.xml'], 'UPPAAL empty queries serialization')
        root=ET.fromstring(files['model.xml'])
        shared,endpoints=validate(root,n)
        item={'processes':49*n+1,'load_step_cases':evaluate_steps(shared,n),'endpoint_count':len(endpoints)}
        if n==1: item['frozen_singleton_step_cases']=singleton_correspondence(shared)
        else: item['rejected_mutations']=negative_controls(root)
        result['sizes'][str(n)]=item
        (g.HERE/'generated'/f'n{n}'/'interface-inventory.json').write_bytes(g.encoded(endpoints))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
