"""Reproduce pinned final P1/P2 review inputs; static analysis, no UPPAAL execution."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.integrated.generator import generate
BASE='932f35b98fc1ab4564d59069f34266248f64c558'
sha=lambda b:hashlib.sha256(b).hexdigest()


def payload():
    c=generate(ROOT);xml=ET.fromstring(c.model_xml)
    # Execution HEAD may contain this report only; all model bytes must match base.
    paths=[p for p in (ROOT/'src/uppaal_mcp/integrated').glob('*.py')]
    for p in paths:
        assert p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT),str(p)
    prior=json.loads((ROOT/'evidence/instantiation/20260923-recovery-attempts/run.json').read_text())
    for k in ('model_hash','query_hash','generator_hash','parameter_set','instance_vector','source_hashes'):
        assert c.metadata[k]==prior[k],k
    selected=[
      ('C01-deadlock','A[] not deadlock','structural'),
      ('C01-queue','A[] !mac_queue_overflow_seen','structural'),
      ('C01-attempts','A[] !sdn_attempt_bad','structural'),
      ('attempt-protocol','A[] !sdn_attempt_protocol_error','recorder-validity'),
      ('C02-ack-elapsed','A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))','bounded-response-safety'),
      ('queue-nonempty','E<> mac_queue_q > 0','nonvacuity'),
      ('queue-full','E<> mac_queue_q == mac_queue_K && !mac_queue_overflow_seen','nonvacuity'),
      ('queue-overflow','E<> mac_queue_overflow_seen','negative-result-diagnostic'),
      ('attempt-start','E<> sdn_attempt_active','nonvacuity'),
      ('attempt-primary','E<> sdn_attempt_primary == 1','nonvacuity'),
      ('attempt-rollback','E<> sdn_attempt_rollback == 1','nonvacuity'),
      ('attempt-two','E<> sdn_attempt_total == 2','nonvacuity'),
      ('ack-start','E<> mac_obs_ack_active','nonvacuity'),
      ('ack-timeout','E<> mac_phy_ack_timeout','nonvacuity'),
      ('ack-unconditional-completion','mac_obs_ack_active --> !mac_obs_ack_active','completion-diagnostic-not-time-divergence-restricted'),
    ]
    symbols=set(re.findall(r'\b(?:mac_|sdn_)[A-Za-z0-9_]+\b',xml.findtext('declaration')))
    for _,q,_ in selected:
        assert set(re.findall(r'\b(?:mac_|sdn_)[A-Za-z0-9_]+\b',q))<=symbols,q
    query=''.join('// '+ident+' | '+kind+' | no verdict\n'+q+'\n' for ident,q,kind in selected)
    fullmap=[]
    for x in c.metadata['query_map']:
        matched=[ident for ident,q,_ in selected if q==x.get('candidate')]
        fullmap.append({'id':x['id'],'query':x.get('candidate'),'selected_as':matched,
                        'disposition':'selected' if matched else 'diagnostic_only_no_acceptance_claim'})
    params={'integration':c.metadata['parameter_set'],'layer_source_constants':c.metadata['source_parameters'],
            'attempt_recording':c.metadata['recovery_attempt_recording'],
            'time_unit':'abstract model unit; no physical calibration',
            'new_since_timing_inventory':{'queue':{'K':4,'L':1,'M':2,'H':4,'source':'accepted #43/#44'},
              'attempt_limits':{'primary':1,'rollback':1,'total':2,'source':'accepted #45/#46'},
              'attempt_saturation':{'primary':2,'rollback':2,'total':3,'source':'violation witness bounds, not allowed attempt limits'}}}
    refs=['AGENTS.md','CONTRIBUTING.md','manifests/v1.md','manifests/collaboration-v1.yaml','manifests/baselines/reviewer-r1.yaml',
          'evidence/validation/20260910-phy-revision/validation-report.md','evidence/validation/20260917-v03-timing/timing-inventory.json',
          'evidence/instantiation/20260907-p2-scope/model-scope-specification.md','evidence/instantiation/20260907-p2-scope/interface-contract.md',
          'evidence/instantiation/20260907-p2-scope/scheduler-analysis.md','evidence/instantiation/20260917-v03-contract-disposition/contracts.md',
          'evidence/instantiation/20260917-v03-contract-disposition/triage.md','evidence/instantiation/20260919-core-check-contract/README.md',
          'evidence/instantiation/20260922-queue-implementation/run.json','evidence/instantiation/20260923-recovery-attempts/run.json']
    refs += [p.relative_to(ROOT).as_posix() for p in paths]
    refs += ['levels_tex/samplepaper.tex']
    pins={p:sha((ROOT/p).read_bytes()) for p in sorted(refs)}
    for p in pins:assert sha(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT))==pins[p],p
    meta={k:c.metadata[k] for k in ('configuration_id','model_hash','query_hash','generator_hash','source_hashes','instance_vector','system_order','channels','recovery_attempt_recording','queue_abstraction')}
    meta.update(reviewed_commit=BASE,source_input_hashes=pins,selected_query_hash=sha(query.encode()),
                baseline_frozen=False,decision='proposed_for_user_acceptance',model_checking='not_run_by_this_review',
                process_count=len(c.metadata['system_order']),candidate_query_count=len(fullmap),selected_query_count=len(selected),
                checks=['all reviewed files equal pinned Git bytes','XML/query/generator/parameters/vector equal accepted #45 run',
                        'selected query variable references exist; not verifier parsing/type checking'])
    assert len(c.metadata['system_order'])==50
    return {'inputs.json':meta,'parameters.json':params,'query-disposition.json':fullmap,
            'selected-queries.q':query,'selected-queries.json':[{'id':i,'query':q,'role':k,'verdict':None} for i,q,k in selected]}


def main():
    data=payload()
    for name,value in data.items():
        raw=(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
        if '--check' in sys.argv:assert (HERE/name).read_bytes()==raw,name
        else:(HERE/name).write_bytes(raw)
    print('Static review input checks OK: pinned source, 50 processes, 15 selected queries, current configuration matches accepted #45. No model checking.')
if __name__=='__main__':main()
