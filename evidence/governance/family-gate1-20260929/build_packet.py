#!/usr/bin/env python3
"""Build/check an unaccepted family Gate 1 proposal; never runs UPPAAL."""
import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='52c5c8d94122f5fbd2a7b689fd9e764583de3226'
FAMILY=Path('evidence/scalability/family-series-68')
SERVICE=Path('evidence/scalability/service-reachability-20260929')
OLD_INDEX=FAMILY/'checks/diagnostic-001/runs.json'
NEW_INDEX=SERVICE/'runs/service-002/runs.json'


def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(data):return (json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
def require(ok,message):
    if not ok:raise ValueError(message)


def build():
    pins={}
    def read(path):
        path=Path(path);data=(ROOT/path).read_bytes()
        original=subprocess.check_output(['git','show',BASE+':'+path.as_posix()],cwd=ROOT)
        require(data==original,'Input differs from accepted base: '+str(path))
        pins[path.as_posix()]=sha(data)
        return data
    def obj(path):return json.loads(read(path))
    pointer=obj('manifests/current.json')
    for p in [pointer['scientific_plan'],pointer['collaboration_manifest'],pointer['baseline_manifest'],
              'CONTRIBUTING.md','CONTRIBUTING-v2.md','AGENTS.md',FAMILY/'PROTOCOL.md',FAMILY/'CONTRACT.md',
              FAMILY/'p4-plan.json',FAMILY/'generate.py',FAMILY/'query_schema.py',FAMILY/'gate-candidate.json',
              SERVICE/'RESULTS.md',SERVICE/'NEXT.md']:
        read(p)
    for p in obj(FAMILY/'inputs.json')['files']:read(p)
    attempts=[]
    for index in [OLD_INDEX,NEW_INDEX]:
        for rec in obj(index):
            if rec.get('run_kind')=='behavior' or (index==NEW_INDEX and rec.get('N')):
                attempts.append((index.as_posix(),rec))
    require(len(attempts)==36,'Expected 26 original + 10 service attempts')
    versions={rec['tool_version'] for _,rec in attempts}
    require(len(versions)==1,'Tool version mismatch')
    models=[];rows=[]
    for n in range(1,5):
        folder=FAMILY/f'generated/n{n}';meta=obj(folder/'metadata.json')
        files={}
        for name,digest in meta['files'].items():
            path=folder/name
            require(sha(read(path))==digest,'Model metadata mismatch: '+str(path))
            files[name]={'path':path.as_posix(),'sha256':digest}
        for name,digest in meta['generator_source_files'].items():
            require(sha(read(FAMILY/name))==digest,'Generator source mismatch')
        models.append({'N':n,'process_count':49*n+1,'files':files,
                       'source_hash':meta['source_hash'],'generator_hash':meta['generator_hash'],
                       'generator_source_files':{(FAMILY/k).as_posix():v for k,v in meta['generator_source_files'].items()},
                       'metadata_reference':(folder/'metadata.json').as_posix()})
        for q in obj(folder/'p4-queries.json'):
            path=folder/q['path'];query=read(path).decode().strip()
            require(query==q['query'],'Query/schema mismatch')
            refs=[]
            for index,rec in attempts:
                if rec['N']!=n or rec['query_hash']!=sha(read(path)):continue
                require(rec['model_hash']==files['model.xml']['sha256'],'Evidence model mismatch')
                refs.append({'index':index,'run_id':rec['run_id'],'status':rec['status'],
                             'property_verdict':rec['property_verdict'],'model_hash':rec['model_hash'],
                             'query_hash':rec['query_hash'],'tool_version':rec['tool_version'],
                             'source_commit':rec['source_commit']})
            verdicts=sorted({r['property_verdict'] for r in refs if r['status']=='success' and r['property_verdict']})
            rows.append({'N':n,'query_id':q['id'],'query_path':path.as_posix(),'formula':query,
                         'model_hash':files['model.xml']['sha256'],'query_hash':sha(read(path)),
                         'role':q['role'],'claim_scope':q['claim_scope'],'nonvacuity':q['nonvacuity'],
                         'attempts':refs,'observed_verdicts':verdicts,
                         'evidence_state':'explicit_result' if verdicts else 'open_no_verdict' if refs else 'not_attempted',
                         'disposition_status':'proposed_only','requirement_closed':False})
    packet={'kind':'family_gate_1_decision_proposal','issue':72,'proposed_baseline_id':'uav-family-r1-20260929',
            'status':'proposed','frozen':False,'gate_1_accepted':False,'claim_narrowing_accepted':False,
            'p4_execution_authorized':False,'current_pointer_changed':False,
            'base_ref':'read','base_commit':BASE,'model_candidate_commit':'a51a77e7852aee514bb0217a17d970fcf94cb704',
            'historical_baseline':{'id':'reviewer-r1-gate1-20260923','path':pointer['baseline_manifest'],
                                   'status':'accepted_unchanged','automatic_P3_transfer':False},
            'family_domain':[1,2,3,4],'models':models,'tool_version':next(iter(versions)),
            'protocol_reference':(FAMILY/'PROTOCOL.md').as_posix(),
            'protocol_status':'accepted_as_preparation_only; future execution requires separate authorization',
            'decisions':{'candidate_acceptance':'https://github.com/artmus208/uppaal_sdn_isac/pull/69#issuecomment-5889994466',
                         'diagnostic_report_acceptance':'https://github.com/artmus208/uppaal_sdn_isac/pull/71#issuecomment-5890111952',
                         'new_gate_decision':None,'claim_scope_disposition':None},
            'required_next_decisions':['independent approval of exact family freeze scope',
                'explicit P1/P2 applicability review for this family or a separately accepted validation task; historical acceptance is not automatic transfer',
                'explicit disposition of unresolved nonvacuity before any dependent P4 claim',
                'manifest-specific governance activation scope and selected-baseline compatibility',
                'separate P4 Issue with accepted baseline, host, query roles and measurement protocol'],
            'does_not_close':['R03','R04','C06']}
    validate(packet,rows)
    lines=['# Existing query evidence — no new verifier runs','',
           'Each row links to exact run identities, model/query hashes and tool version in query-dispositions.json. Timeout is not a property verdict. Rows with no attempt are not inferred from similar formulas.','',
           '| N | Query | Attempts | Explicit verdicts | Evidence state |','|---:|---|---:|---|---|']
    for row in rows:lines.append(f"| {row['N']} | {row['query_id']} | {len(row['attempts'])} | {', '.join(row['observed_verdicts']) or 'none'} | {row['evidence_state']} |")
    outputs={'baseline-candidate.json':encoded(packet),'query-dispositions.json':encoded(rows),
             'input-hashes.json':encoded({'base_commit':BASE,'algorithm':'sha256 exact bytes','files':pins}),
             'QUERY_TABLE.md':('\n'.join(lines)+'\n').encode()}
    return outputs,packet,rows


def validate(packet,rows):
    require(packet['status']=='proposed' and not packet['frozen'],'Accidental activation')
    for name in ('gate_1_accepted','claim_narrowing_accepted','p4_execution_authorized','current_pointer_changed'):
        require(packet[name] is False,'Unauthorized decision: '+name)
    require(packet['decisions']['new_gate_decision'] is None and packet['decisions']['claim_scope_disposition'] is None,'Decision invented')
    require(packet['family_domain']==[1,2,3,4],'Unexpected domain')
    require(len(rows)==30 and len({(r['N'],r['query_id']) for r in rows})==30,'Query coverage')
    sources={}
    for path in (OLD_INDEX,NEW_INDEX):
        for r in json.loads((ROOT/path).read_text()):sources[(path.as_posix(),r['run_id'])]=r
    used=[]
    for row in rows:
        require(sha((ROOT/row['query_path']).read_bytes())==row['query_hash'],'Query hash drift')
        require((ROOT/row['query_path']).read_text().strip()==row['formula'],'Formula drift')
        require(row['requirement_closed'] is False and row['disposition_status']=='proposed_only','Invented disposition')
        for ref in row['attempts']:
            raw=sources[(ref['index'],ref['run_id'])];used.append(ref['run_id'])
            for key in ('status','property_verdict','model_hash','query_hash','tool_version','source_commit'):
                require(ref[key]==raw[key],'Evidence altered: '+key)
            require(ref['model_hash']==row['model_hash'] and ref['query_hash']==row['query_hash'],'Cross-model/query transfer')
            require(ref['status']=='success' or ref['property_verdict'] is None,'Verdict on incomplete run')
        expected=sorted({x['property_verdict'] for x in row['attempts'] if x['status']=='success' and x['property_verdict']})
        require(row['observed_verdicts']==expected,'Unsupported query conclusion')
        state='explicit_result' if expected else 'open_no_verdict' if row['attempts'] else 'not_attempted'
        require(row['evidence_state']==state,'Incorrect evidence state')
    require(len(used)==36 and len(set(used))==36,'Missing/duplicated attempts')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true');ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args();outputs,packet,rows=build()
    for name,data in outputs.items():
        if args.write:(HERE/name).write_bytes(data)
        else:require((HERE/name).read_bytes()==data,'Generated proposal drift: '+name)
    rejected=0
    if args.self_test:
        mutations=[lambda p,r:p.update(frozen=True),lambda p,r:p.update(gate_1_accepted=True),
                   lambda p,r:p.update(claim_narrowing_accepted=True),lambda p,r:p.update(p4_execution_authorized=True),
                   lambda p,r:r.pop(),lambda p,r:r[0].update(model_hash='0'*64),
                   lambda p,r:r[0]['attempts'][0].update(property_verdict='satisfied'),
                   lambda p,r:r[0].update(observed_verdicts=['satisfied'])]
        for mutate in mutations:
            p=copy.deepcopy(packet);rr=copy.deepcopy(rows);mutate(p,rr)
            try:validate(p,rr)
            except ValueError:rejected+=1
            else:raise ValueError('Mutation accepted')
    print(json.dumps({'kind':'static_proposal_audit_not_verification','models':4,'queries':len(rows),
          'scientific_attempts':sum(len(r['attempts']) for r in rows),
          'explicit_result_queries':sum(r['evidence_state']=='explicit_result' for r in rows),
          'open_queries_with_attempts':sum(r['evidence_state']=='open_no_verdict' for r in rows),
          'not_attempted_queries':sum(r['evidence_state']=='not_attempted' for r in rows),
          'input_hashes':len(json.loads(outputs['input-hashes.json'])['files']),
          'rejected_mutations':rejected,'gate_accepted':False},indent=2))
