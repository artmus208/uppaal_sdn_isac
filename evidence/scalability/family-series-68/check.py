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
    expected_header = '\n'.join([f'const int FAMILY_N={n};', f'int[-1,{n-1}] family_last_server=-1;'] + [f'bool family_grant_{i}=false;' for i in range(n)])
    need(decl[:pos].strip() == expected_header, 'family declarations and grant initialization')
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
    local_declarations = ['clock tick;'] + [f'int[0,{hi}] {name}_{i}=0;' for i in range(n) for name,hi in [('arrival',1),('m1',2),('m2',3),('m3',2),('m4',3),('m5',2),('m6',2)]]
    need(shared.findtext('declaration').splitlines() == local_declarations, 'shared clock and isolated bounded scratch state')
    locations = {l.get('id'):l for l in shared.findall('location')}
    need(len(locations) == 1+3*n, 'shared locations count')
    need(shared.find('init').get('ref') == 'shared_Wait', 'initial shared wait')
    need(locations['shared_Wait'].find('committed') is None and locations['shared_Wait'].find('urgent') is None, 'shared wait permits time passage')
    for name,location in locations.items():
        if name != 'shared_Wait':
            need(not text(location,'invariant') and location.find('urgent') is None, 'unconstrained committed delivery/staging')
    need(text(locations['shared_Wait'],'invariant') == 'tick <= u0_bus_T_mac_tick', 'shared period invariant')
    for i in range(n):
        for kind in ('Publish','Offer'):
            need(locations[f'shared_{kind}_{i}'].find('committed') is not None, 'zero-time delivery chain')
    edges = shared.findall('transition')
    need(len(edges) == 1+4*n, 'shared edge count')
    for i,e in enumerate(edges[:n]):
        need(not text(e,'synchronisation'), 'staging has no channel side effects')
        need(locations[f'shared_Sample_{i+1}'].find('committed') is not None, 'staging is zero-time')
        need(e.find('source').get('ref') == ('shared_Wait' if i==0 else f'shared_Sample_{i}') and e.find('target').get('ref') == f'shared_Sample_{i+1}', 'sample staging chain')
        need(text(e,'guard') == ('tick == u0_bus_T_mac_tick' if i==0 else ''), 'sample staging guard')
        expected_select='pick_arrival:int[0,1], pick_m1:int[0,2], pick_m2:int[0,3], pick_m3:int[0,2], pick_m4:int[0,3], pick_m5:int[0,2], pick_m6:int[0,2]'
        need(text(e,'select')==expected_select, 'unchanged finite sample domains')
        need(text(e,'assignment')==', '.join(f'{name}_{i}=pick_{name}' for name in ['arrival']+[f'm{k}' for k in range(1,7)]), 'private sample scratch state')
    need(edges[n].find('source').get('ref') == f'shared_Sample_{n}' and edges[n].find('target').get('ref') == 'shared_Publish_0', 'atomic service step')
    need(not text(edges[n],'synchronisation'), 'atomic service has no channel side effects')
    selects = text(edges[n],'select')
    need(selects == f'server:int[-1,{n-1}]', 'single bounded shared service selector')
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
        need(not text(pub,'assignment') and not text(offer,'assignment'), 'notification edges have no additional writes')
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


def identifiers(node):
    if isinstance(node, str):
        return set() if node.isdecimal() or node in ('true', 'false') else {node}
    return set().union(*(identifiers(child) for child in node[1:]))


FIELDS = ('bufferClass','delayClass','dropClass','resourceClass','sensingDemand','commDemand')
SAMPLE_DOMAINS = (range(3), range(4), range(3), range(4), range(3), range(3))


def step_program(shared, n):
    """Establish separability before using factored local truth tables.

    The guard is exactly the contract conjunction. Ordered updates may read
    only their own queue/constant/scratch fields and the shared server selector.
    Direct sample mappings and recorder updates are checked independently.
    Thus varying another entity cannot change a local update at fixed server.
    This is a local-expression argument, never a reachable-state/model proof.
    """
    edge=next(e for e in shared.findall('transition') if text(e,'select').startswith('server:'))
    guard=parse(text(edge,'guard')); updates=program(text(edge,'assignment'))
    clauses=['tick == u0_bus_T_mac_tick'] + [
        f'(server != {i} || (u{i}_mac_queue_q > 0 && (u{i}_mac_scheduleMode == u{i}_mac_SCH_COMM || u{i}_mac_scheduleMode == u{i}_mac_SCH_JOINT)))'
        for i in range(n)]
    need(guard == parse(' && '.join(clauses)), 'exact shared service eligibility guard')
    expected_targets=[]
    for i in range(n):
        expected_targets += [f'u{i}_mac_queue_q', f'u{i}_mac_queue_overflow_seen', f'u{i}_mac_queueClass']
        expected_targets += [f'u{i}_mac_{field}' for field in FIELDS]
        expected_targets += [f'u{i}_bus_mac_age', f'u{i}_bus_mac_valid', f'family_grant_{i}']
    expected_targets += ['family_last_server', 'tick']
    need([name for name,_ in updates] == expected_targets, 'exact ordered service write set')
    for name, expression in updates:
        match=re.match(r'u(\d+)_', name)
        if match:
            i=int(match[1])
            dependencies = {
                f'u{i}_mac_queue_q': {f'u{i}_mac_queue_q',f'u{i}_mac_queue_K','server',f'arrival_{i}'},
                f'u{i}_mac_queue_overflow_seen': {f'u{i}_mac_queue_overflow_seen',f'u{i}_mac_queue_q',f'u{i}_mac_queue_K'},
                f'u{i}_mac_queueClass': {f'u{i}_mac_queue_q'} | {f'u{i}_mac_{field}' for field in ('queue_L','queue_M','queue_H','Q_EMPTY','Q_LOW','Q_MED','Q_HIGH','Q_CRIT')},
                f'u{i}_bus_mac_age': set(), f'u{i}_bus_mac_valid': set(),
                **{f'u{i}_mac_{field}':{f'm{k}_{i}'} for k,field in enumerate(FIELDS,1)}}
            need(identifiers(expression) <= dependencies[name], 'per-entity service expression separability')
        elif name.startswith('family_grant_'):
            i=int(name.rsplit('_',1)[1])
            need(expression == parse(f'server == {i}'), 'grant records exactly one selected entity')
        else:
            need(expression == ('server' if name=='family_last_server' else '0'), 'shared recorder and clock update')
    mapping=dict(updates)
    for i in range(n):
        for k,field in enumerate(FIELDS,1):
            need(mapping[f'u{i}_mac_{field}'] == f'm{k}_{i}', 'exact private sampled class mapping')
        need(mapping[f'u{i}_bus_mac_age'] == '0' and mapping[f'u{i}_bus_mac_valid'] == 'true', 'sample metadata update')
    return guard, updates


def sample_state(n, server=-1):
    state={'tick':5, 'server':server}
    for i in range(n):
        state.update(constants(f'u{i}_'))
        state.update({f'u{i}_mac_queue_q':1, f'u{i}_mac_scheduleMode':1,
                      f'u{i}_mac_queue_overflow_seen':bool(i%2), f'arrival_{i}':0})
        state.update({f'm{k}_{i}':(i+k)%len(domain) for k,domain in enumerate(SAMPLE_DOMAINS,1)})
    return state


def check_step(updates, state, n):
    after=execute(updates,state)
    need(sum(bool(after[f'family_grant_{i}']) for i in range(n))<=1,'shared capacity exceeded')
    need(after['family_last_server']==state['server'] and after['tick']==0,'epoch record/reset')
    for i in range(n):
        old=state[f'u{i}_mac_queue_q']
        q=old if old>4 else old-int(state['server']==i)+state[f'arrival_{i}']
        need(after[f'u{i}_mac_queue_q']==q,'wrong entity queue/service update')
        need(after[f'u{i}_mac_queue_overflow_seen']==(state[f'u{i}_mac_queue_overflow_seen'] or q>4),'sticky overflow lost')
        klass=0 if q==0 else 1 if q<=1 else 2 if q<=2 else 3 if q<4 else 4
        need(after[f'u{i}_mac_queueClass']==klass,'queue class derived before update')
        for k,field in enumerate(FIELDS,1):
            need(after[f'u{i}_mac_{field}']==state[f'm{k}_{i}'],'cross-entity sampled load')
        need(after[f'u{i}_bus_mac_age']==0 and after[f'u{i}_bus_mac_valid'],'entity sample metadata')
    return after


def evaluate_steps(shared,n):
    guard,updates=step_program(shared,n)
    guard_cases=allowed_cases=sample_cases=0
    # Exact dependency checks above justify per-entity factorization. Every local
    # occupancy/mode/arrival/sticky/server combination is covered, including q=5.
    for i in range(n):
        for q,mode,arrival,sticky,server in itertools.product(range(6),range(5),range(2),(False,True),range(-1,n)):
            state=sample_state(n,server)
            state.update({f'u{i}_mac_queue_q':q, f'u{i}_mac_scheduleMode':mode,
                          f'u{i}_mac_queue_overflow_seen':sticky,f'arrival_{i}':arrival})
            expected=server==-1 or (state[f'u{server}_mac_queue_q']>0 and state[f'u{server}_mac_scheduleMode'] in (1,3))
            need(bool(evaluate(guard,state))==expected,'shared eligibility differs from contract')
            guard_cases+=1
            if expected:
                check_step(updates,state,n)
                allowed_cases+=1
        for k,domain in enumerate(SAMPLE_DOMAINS,1):
            for value in domain:
                state=sample_state(n)
                state[f'm{k}_{i}']=value
                check_step(updates,state,n)
                sample_cases+=1
    outcomes=set()
    for server in range(-1,n):
        state=sample_state(n,server)
        after=check_step(updates,state,n)
        outcomes.add(tuple(after[f'u{i}_mac_queue_q'] for i in range(n)))
    expected_outcomes={tuple(0 if i==server else 1 for i in range(n)) for server in range(-1,n)}
    need(outcomes==expected_outcomes,'competition witness: only one queue may decrease per epoch')
    for time in (0,4,6):
        state=sample_state(n); state['tick']=time
        need(not evaluate(guard,state),'period guard')
    return {'method':'dependency-checked factored local truth tables', 'guard_cases':guard_cases,
            'allowed_update_cases':allowed_cases,'sample_domain_cases':sample_cases,
            'competition_outcomes':len(outcomes),'independent_sticky_flags':True,
            'scope':'local expressions only; not model checking or whole-system equivalence'}


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


def negative_controls(root,n):
    controls=[]
    def reject(name, mutate):
        mutant=copy.deepcopy(root); mutate(mutant)
        try:
            shared,_=validate(mutant,n); evaluate_steps(shared,n)
        except AssertionError as error:
            controls.append({'mutation':name, 'rejection':str(error)})
        else:
            raise AssertionError('undetected mutation: '+name)
    def replace_first(r,tag,old,new):
        for e in r.iter(tag):
            if e.text and old in e.text:
                e.text=e.text.replace(old,new,1); return
        raise AssertionError('mutation anchor absent: '+old)
    last=n-1
    if n>=2:
        reject('cross-entity queue state',lambda r:replace_first(r,'label',f'u{last}_mac_queue_q','u0_mac_queue_q'))
        reject('cross-entity clock',lambda r:replace_first(r,'label',f'u{last}_mac_c_phy_ack','u0_mac_c_phy_ack'))
        reject('cross-entity ACK',lambda r:replace_first(r,'label',f'u{last}_mac_phy_ack?','u0_mac_phy_ack?'))
        reject('cross-entity scratch input',lambda r:replace_first(r,'label',f'arrival_{last}=pick_arrival','arrival_0=pick_arrival'))
        reject('cross-entity service scratch read',lambda r:replace_first(r,'label',f'+arrival_{last})','+arrival_0)'))
        reject('wrong shared tick destination',lambda r:replace_first(r,'label',f'u{last}_mac_mac_tick!','u0_mac_mac_tick!'))
        reject('wrong shared sample destination',lambda r:replace_first(r,'label',f'u{last}_bus_new_mac_sample!','u0_bus_new_mac_sample!'))
        reject('global clock alias',lambda r:replace_first(r,'declaration',f'clock u{last}_mac_c_sched','clock u0_mac_c_sched'))
        reject('two queues consume one selected slot',lambda r:replace_first(r,'label',f'u{last}_mac_queue_q-(server == {last} ? 1 : 0)',f'u{last}_mac_queue_q-(server == 0 ? 1 : 0)'))
        reject('two simultaneous grant records',lambda r:replace_first(r,'label',f'family_grant_{last}=(server == {last})',f'family_grant_{last}=(server == 0)'))
        reject('wrong instance binding',lambda r:replace_first(r,'system',f'u{last}_app_Req_0 = u{last}_app_A_REQ()',f'u{last}_app_Req_0 = u0_app_A_REQ()'))
    else:
        reject('ineligible singleton service',lambda r:replace_first(r,'label','server != 0 || (u0_mac_queue_q > 0','server != 0 || (u0_mac_queue_q >= 0'))
    for kind,index in [('Sample',n),('Publish',last),('Offer',last)]:
        path=f"template[name='SharedLoad']/location[@id='shared_{kind}_{index}']"
        reject('lost zero-time '+kind,lambda r,path=path:r.find(path).remove(r.find(path+'/committed')))
    reject('wrong selector bound',lambda r:replace_first(r,'label',f'server:int[-1,{last}]',f'server:int[-1,{n}]'))
    reject('wrong last-server recorder',lambda r:replace_first(r,'label','family_last_server=server','family_last_server=0'))
    reject('lost epoch reset',lambda r:replace_first(r,'label','family_last_server=server, tick=0','family_last_server=server, tick=1'))
    reject('duplicate shared server',lambda r:r.append(copy.deepcopy(r.find("template[name='SharedLoad']"))))
    return controls


def main():
    pins=g.inputs()
    result={'evidence_kind':'static_validation','property_verdict':'not_applicable','sizes':{}}
    for n in g.SIZES:
        files=g.artifacts(n,pins)
        for name,data in files.items():
            need((g.HERE/'generated'/f'n{n}'/name).read_bytes()==data,'deterministic reproduction '+name)
        need(b'<queries></queries>' in files['model.xml'],'UPPAAL empty queries serialization')
        root=ET.fromstring(files['model.xml'])
        shared,endpoints=validate(root,n)
        need(g.encoded(endpoints)==files['interface-inventory.json'],'exact interface inventory')
        item={'processes':49*n+1,'load_step':evaluate_steps(shared,n),'endpoint_count':len(endpoints),
              'rejected_mutations':negative_controls(root,n)}
        if n==1:
            item['frozen_singleton_step_cases']=singleton_correspondence(shared)
        if n in (1,2):
            item['prototype_exact_bytes']={}
            for name in ('model.xml','queries.q','queries.json'):
                old=(g.ROOT/g.PROTOTYPE/'generated'/f'n{n}'/name).read_bytes()
                need(old==files[name],f'N={n} differs from PR #67: {name}')
                item['prototype_exact_bytes'][name]={'equal':True,'sha256':g.sha(old)}
        result['sizes'][str(n)]=item
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
