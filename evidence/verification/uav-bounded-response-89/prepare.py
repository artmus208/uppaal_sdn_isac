"""Deterministic proposal only; no verifier calls and no XML file by default."""
from pathlib import Path
import argparse
import copy
import difflib
import hashlib
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
M_PATH = 'evidence/instantiation/uav-service-completion-candidate/model.xml'
M_HASH = 'b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02'
BASE = '452571598d4a5c1e070dace3a918ea737904e239'
SCOPE = HERE.relative_to(ROOT).as_posix()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(obj):
    return (json.dumps(obj, indent=2, sort_keys=True) + '\n').encode()

def tree(node):
    return (node.tag, sorted(node.attrib.items()), (node.text or '').strip(), [tree(c) for c in node])

def derive(source):
    if digest(source) != M_HASH:
        raise ValueError('Original M hash mismatch')
    text = source.decode('utf-8')
    expected = ET.fromstring(source)
    changes = []
    # Edit exact original bytes, without reserializing unrelated XML.
    for name in ['u0_Boundary_E_PHY_INPUT', 'SharedLoad', 'u0_Boundary_E_FAULT']:
        pattern = r'  <template>\n    <name>' + name + r'</name>[\s\S]*?  </template>'
        block = re.search(pattern, text).group()
        original = block
        template = expected.find("template[name='%s']" % name)
        original_transitions = template.findall('transition')
        transition_blocks = list(re.finditer(r'    <transition(?: [^>]*)?>[\s\S]*?</transition>\n', block))
        if len(transition_blocks) != len(original_transitions):
            raise ValueError('Transition byte/structure mismatch')
        for index, (match, tr) in reversed(list(enumerate(zip(transition_blocks, original_transitions)))):
            before = match.group()
            after = before
            src, dst = tr.find('source').get('ref'), tr.find('target').get('ref')
            select = tr.find("label[@kind='select']")
            if name == 'u0_Boundary_E_PHY_INPUT' and select is not None:
                assign = tr.findtext("label[@kind='assignment']")
                field = re.fullmatch(r'p(\d+)=value', assign)
                value = 2 if field and field[1] == '0' else 0
                new = f'value:int[{value},{value}]' if field else 'miss:int[0,0], scenario:int[0,0]'
                after = before.replace('>' + select.text + '</label>', '>' + new + '</label>')
                changes.append(dict(template=name, transition_index=index, source=src, target=dst,
                                    kind='select', before=select.text, after=new))
                select.text = new
            elif name == 'SharedLoad' and select is not None and 'pick_arrival:' in select.text:
                new = re.sub(r'int\[0,\d+\]', 'int[0,0]', select.text)
                after = before.replace('>' + select.text + '</label>', '>' + new + '</label>')
                changes.append(dict(template=name, transition_index=index, source=src, target=dst,
                                    kind='select', before=select.text, after=new))
                select.text = new
            elif name == 'u0_Boundary_E_FAULT' and '_Before_' in src and any('_'+k+'_' in dst for k in ['Rule','Link','Node']):
                if tr.findtext("label[@kind='guard']") != 'u0_bus_time >= 12 && u0_bus_time <= 13':
                    raise ValueError('Unexpected injection guard')
                changes.append(dict(template=name, transition_index=index, source=src, target=dst,
                                    kind='remove_external_injection_edge', before=before, after=''))
                after = ''
                template.remove(tr)
            block = block[:match.start()] + after + block[match.end():]
        text = text.replace(original, block, 1)
    output = text.encode('utf-8')
    if tree(expected) != tree(ET.fromstring(output)):
        raise ValueError('Unlisted structural change')
    if (len(changes), sum(c['kind'] == 'select' for c in changes),
        sum(c['kind'] == 'remove_external_injection_edge' for c in changes)) != (40,25,15):
        raise ValueError('Unexpected restriction inventory')
    changes.sort(key=lambda c: (c['template'], c['transition_index']))
    return output, changes

def queries():
    body = json.loads((HERE/'inputs/issue-89.json').read_text())['body']
    s = re.search(r'`S`:\s*~~~uppaal\s*(.*?)\s*~~~', body, re.S)[1]
    g = re.search(r'`G` —.*?~~~uppaal\s*(.*?)\s*~~~', body, re.S)[1]
    q = {i: re.search(r'Q%d:\s*~~~uppaal\s*(.*?)\s*~~~' % i, body, re.S)[1] for i in [2,5,6]}
    q.update({1: f'E<> {s}', 3: f'E<> ({g} && c82_service_age<=c82_D_service)',
              4: f'{s} --> ({g} && c82_service_age<=c82_D_service)'})
    return {i: (q[i]+'\n').encode('utf-8') for i in range(1,7)}

def products():
    source = (ROOT/M_PATH).read_bytes()
    candidate, changes = derive(source)
    h = digest(candidate)
    patch = ''.join(difflib.unified_diff(source.decode().splitlines(True), candidate.decode().splitlines(True),
                                      fromfile=M_PATH, tofile=SCOPE+'/execution/model.xml')).encode()
    inventory = [dict(slot=i, model='M' if i==6 else 'Hnom', model_hash=M_HASH if i==6 else h,
                      model_path=M_PATH if i==6 else SCOPE+'/execution/model.xml',
                      query_path=SCOPE+f'/queries/Q{i}.q', query_hash=digest(data),
                      formula=data.decode().strip(), cap_seconds=600 if i==4 else 180)
                 for i,data in queries().items()]
    out = {'hnom/proposed.patch':patch, 'hnom/changes.json':encoded(changes),
           'hnom/prospective-model.json':encoded(dict(model_hash=h, source_hash=M_HASH, patch_sha256=digest(patch),
                 materialized=False, restrictions_approved=False, process_count=51,
                 note='Computed in memory for review. Not a frozen baseline or an execution authorization.')),
           'query-inventory.json':encoded(inventory)}
    out.update({f'queries/Q{i}.q':data for i,data in queries().items()})
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    for path, data in products().items():
        dest=HERE/path
        if args.check:
            if dest.read_bytes() != data:
                raise ValueError('Non-reproducible product: '+path)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    print('Proposal reproducible; no derived XML file or verifier invocation.')

if __name__ == '__main__':
    main()
