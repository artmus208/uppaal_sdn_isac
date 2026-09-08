"""Deterministic candidate composition CLI: python -m uppaal_mcp.integrated.generator."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from . import boundary
from .adapt import adapt_layer
from .inputs import BASE, SOURCE, SPEC, load, sha
from .xmlutil import IDENT, RESERVED, TOKEN, normalize_order, rename


@dataclass(frozen=True)
class Composition:
    model_xml: str
    queries: str
    metadata: dict


def generate(root: Path | None = None) -> Composition:
    root = Path(root or (Path.cwd() if (Path.cwd()/SPEC).is_dir() else Path(__file__).resolve().parents[3])).resolve()
    vector, inventory, inputs, source_queries, provenance, context = load(root)
    nta = ET.Element('nta')
    declaration = ET.SubElement(nta, 'declaration')
    declarations = [boundary.DECLARATIONS]
    templates, process_map, symbol_maps, adaptations = {}, {}, {}, []
    for layer, source in inputs.items():
        key = 'stored:app' if layer == 'app' else f'generated:{layer}:with_observers'
        record = inventory['models'][key]
        retain = [g for g in vector['groups_in_system_order'] if g['source'] == key]
        processes = {p: f"{g['group']}_{p}_0" for g in retain for p in g['retain']}
        process_map[layer] = processes
        originals = {t.findtext('name'): t for t in source.findall('template')}
        converted = {}
        for name, qualified in processes.items():
            t = deepcopy(originals[record['instances'][name]])
            if t.findtext('parameter'):
                raise ValueError('parameterized templates are unsupported')
            t.find('name').text = layer + '_' + t.findtext('name')
            ids = {loc.get('id'): layer + '_' + loc.get('id') for loc in t.findall('location')}
            for loc in t.findall('location'):
                loc.set('id', ids[loc.get('id')])
            for node in t.iter():
                if node.tag in ('init', 'source', 'target'):
                    node.set('ref', ids[node.get('ref')])
                if node.tag == 'declaration' or node.tag == 'label' and node.get('kind') != 'comments':
                    node.text = rename(node.text or '', layer + '_')
            converted[qualified] = t
        before_decl = rename(source.findtext('declaration') or '', layer + '_')
        before = {p: ET.tostring(t, encoding='unicode') for p,t in converted.items()}
        after_decl = adapt_layer(layer, before_decl, converted)
        declarations.append(after_decl)
        for p,t in converted.items():
            after = ET.tostring(t, encoding='unicode')
            if before[p] != after:
                adaptations.append({'process':p,'before_xml':before[p],'after_xml':after})
        if before_decl != after_decl:
            adaptations.append({'scope':layer+'_declaration','before':before_decl,'after':after_decl})
        templates.update(converted)
        names = {token for token in TOKEN.findall(source.findtext('declaration') or '') if IDENT.fullmatch(token) and token not in RESERVED}
        symbol_maps[layer] = {s:layer+'_'+s for s in sorted(names)}
    boundary_templates = boundary.build()
    for name,t in boundary_templates.items():
        templates[f'boundary_{name}_0'] = t
    ordered = []
    for group in vector['groups_in_system_order']:
        for p in group['retain']:
            name=f"{group['group']}_{p}_0"
            ordered.append(name)
            normalize_order(templates[name])
            nta.append(templates[name])
    declaration.text='\n\n'.join(declarations)
    ET.SubElement(nta,'system').text='\n'.join(f"{p} = {templates[p].findtext('name')}();" for p in ordered) + '\nsystem '+', '.join(ordered)+';'
    query_map=[]
    for layer,queries in source_queries.items():
        for n,q in enumerate(queries,1):
            # Source queries tied to removed environments are recorded, not silently
            # rebound to a fabricated peer. Candidate query semantics require review.
            removed=vector['remove']['stored:app' if layer=='app' else f'generated:{layer}:with_observers']
            if any(re.search(rf'\b{re.escape(p)}\.',q) for p in removed):
                query_map.append({'id':f'{layer}-{n:02}','source':q,'status':'excluded_removed_environment'})
                continue
            query_map.append({'id':f'{layer}-{n:02}','source':q,
                              'candidate':rename(q,layer+'_',process_map[layer]),'status':'candidate_unverified'})
    for p in ordered:
        if 'obs_' in p:
            query_map.append({'id':'reach-'+p,'candidate':f'E<> {p}.Violation','status':'candidate_unverified'})
    for n,q in enumerate(['A[] not bus_protocol_error','E<> app_Req_0.Accepted','E<> bus_admission_timeout',
                          'E<> bus_schedule_loss','E<> bus_fault_delivered','A[] not deadlock'],1):
        query_map.append({'id':f'integrated-{n:02}','candidate':q,'status':'candidate_unverified'})
    queries=''.join(f"// {q['id']} -- candidate, no verdict\n{q['candidate']}\n" for q in query_map if 'candidate' in q)
    # Empty embedded query list prevents accidental implicit model checking when
    # requesting compile-only diagnostics with this XML alone.
    ET.SubElement(nta,'queries')
    ET.indent(nta,space='  ')
    xml='<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(nta,encoding='unicode',short_empty_elements=False)+'\n'
    channels={}
    for m in re.finditer(r'\b(broadcast\s+)?chan\s+([^;]+);', declaration.text):
        for name in m[2].split(','):
            name=name.strip()
            channels[name]={'kind':'broadcast' if m[1] else 'binary','senders':[],'receivers':[]}
    for p,t in templates.items():
        for tr in t.findall('transition'):
            sync=tr.findtext("label[@kind='synchronisation']")
            if sync:
                name, direction=sync[:-1].strip(),sync[-1]
                if name not in channels:
                    raise ValueError(f'undeclared channel: {p}: {sync}')
                channels[name]['senders' if direction=='!' else 'receivers'].append(p)
    for record in channels.values():
        for endpoint in ('senders','receivers'):
            record[endpoint]=sorted(set(record[endpoint]))
    implementation_sources={p.relative_to(root).as_posix():sha(p.read_bytes())
                            for p in sorted((root/'src/uppaal_mcp/integrated').glob('*.py'))}
    metadata={'schema_version':1,'issue':19,'configuration_id':'p2-single-uav-abstract-v1-candidate',
              'status':'candidate_not_scientifically_accepted','base_commit':BASE,'input_source_commit':SOURCE,
              'baseline_id':'reviewer-r1-candidate','frozen':False,'verification_status':'not_run',
              'model_hash':sha(xml.encode()),'query_hash':sha(queries.encode()),'source_hashes':provenance,
              'context_document_hashes':context,
              'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
              'implementation_sources':implementation_sources,
              'generator_hash':sha(''.join(f'{v}  {k}\n' for k,v in sorted(implementation_sources.items())).encode()),
              'generator_hash_construction':'sha256 of implementation_sources sha256/path records in sorted path order',
              'instance_vector':vector,'system_order':ordered,'symbols':symbol_maps,'process_map':process_map,
              'channels':channels,'query_map':query_map,'adaptations':adaptations,
              'parameter_set':vector['parameter_policy'],
              'source_parameters':{layer:dict(re.findall(r'const int\s+(\w+)\s*=\s*(\d+)\s*;', src.findtext('declaration') or '')) for layer,src in inputs.items()},
              'limitations':['abstract one-link one-session envelope; no physical calibration',
                 'APP Crit and Agg remain zero-transition placeholders',
                 'source policy location/selected-value disagreement and zero-time cycles retained',
                 'oldest-outstanding event latches coalesce repeated monitoring events until a response',
                 'measurement skipped while raw classifier/report pipeline is pending; new sample invalidates old transport',
                 'no scientific P1/P2 acceptance, Gate 1, model-checking or scalability claim']}
    return Composition(xml,queries,metadata)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=generate()
    args.output.mkdir(parents=True,exist_ok=False)
    artifacts={'model.xml':result.model_xml,'queries.q':result.queries,
               'composition.json':json.dumps(result.metadata,indent=2,ensure_ascii=False)+'\n'}
    for name,contents in artifacts.items():
        (args.output/name).write_bytes(contents.encode('utf-8'))
    (args.output/'SHA256SUMS').write_bytes(''.join(f'{sha(v.encode())}  {k}\n' for k,v in artifacts.items()).encode())
    print(json.dumps({'output':str(args.output),'processes':len(result.metadata['system_order']),
                      'model_hash':result.metadata['model_hash'],'query_hash':result.metadata['query_hash'],
                      'verification_status':'not_run'}))


if __name__=='__main__':
    main()
