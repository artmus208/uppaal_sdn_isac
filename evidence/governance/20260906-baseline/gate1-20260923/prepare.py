"""Build a reviewable Gate 1 proposal from the accepted source; no gate decision."""
import hashlib,json,sys,subprocess,tarfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
BASE='a190e10df1b7ce4923f0d18c664b4eef8715eb58'
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.integrated.generator import generate
sha=lambda b:hashlib.sha256(b).hexdigest()
def item(p):
    p=Path(p); return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def dump(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    c=generate(ROOT)
    reviewed=ROOT/"evidence/governance/20260910-p1-p2-review/final-20260923"
    for name in ["selected-queries.q","selected-queries.json","parameters.json","query-disposition.json"]:
        assert (HERE/name).read_bytes()==(reviewed/name).read_bytes(),name
    accepted=json.loads((ROOT/'evidence/governance/20260910-p1-p2-review/final-20260923/inputs.json').read_text())
    for k in ['model_hash','query_hash','instance_vector']:
        assert c.metadata[k]==accepted[k],k
    assert (HERE/'model.xml').read_bytes()==c.model_xml.encode()
    assert (HERE/'candidate-queries.q').read_bytes()==c.queries.encode()
    source=json.loads((HERE/'generation.json').read_text())
    assert source['source_commit']==BASE
    for k in ['source_hashes','implementation_sources','generator_hash','parameter_set']:
        assert c.metadata[k]==source[k],k
    for p,h in {**source['source_hashes'],**source['implementation_sources']}.items():
        assert sha(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT))==h,p
        assert sha((ROOT/p).read_bytes())==h,p
    ev=ROOT/'evidence/instantiation/20260923-recovery-attempts'
    results=json.loads((ev/'results-index.json').read_text())
    engine=next(x for x in results if x['model_hash']==c.metadata['model_hash'])
    assert engine['status']=='success' and engine['exit_code']==0
    assert engine['per_query']==[{'query':'E<> true','expected':'satisfied','actual':'satisfied'}]
    archive=next((ev/'runs').glob('*.tar.xz'))
    with tarfile.open(archive) as t:
        raw=t.extractfile('recovery-attempts-20260923-001/version.stdout.txt').read()
    assert raw.decode()==engine['tool_version']
    (HERE/'verifyta-version.txt').write_bytes(raw)
    dump(HERE/'tool-evidence.json',{'evidence_class':'prior_engine_availability_not_C01_C02',
        'archive':item(archive),'results_index':item(ev/'results-index.json'),
        'record':engine,'version_stdout':item(HERE/'verifyta-version.txt')})
    vector={'configuration_id':'p2-single-uav-abstract-v2-queue-candidate',
        'time_unit':'abstract_model_unit','physical_time_scale_seconds':None,
        'entities':source['instance_vector']['entities'],'system_order':source['system_order'],
        'process_count':len(source['system_order']),
        'queue_abstraction':source['queue_abstraction'],
        'recovery_attempt_recording':source['recovery_attempt_recording'],
        'historical_vector':source['instance_vector'],
        'historical_status_note':'Original vector proposal label is provenance; acceptance is #15/#17/#19 and #47.'}
    dump(HERE/'instance-vector.json',vector)
    source_paths=sorted(p for p in source['source_hashes'] if not p.startswith('manifests/') and p!='CONTRIBUTING.md')
    gen_paths=sorted(source['implementation_sources'])
    def common(paths):return {'value':sha(''.join(f'{sha((ROOT/p).read_bytes())}  {p}\n' for p in paths).encode()),
      'construction':'sha256 of concatenated sha256sum records for the listed files in bytewise path order','inputs':paths}
    manifest={
      'schema_version':'1.0','kind':'model-baseline',
      'metadata':{'id':'reviewer-r1-gate1-20260923','status':'candidate','maturity':'accepted_inputs_pending_gate','frozen':False,'captured_on':'2026-09-23'},
      'repository':{'url':'https://github.com/artmus208/uppaal_sdn_isac','branch':'read','commit':BASE,
        'snapshot_basis':'exact_git_blobs','worktree_dirty_at_capture':False,'commit_is_exact_snapshot':True,
        'note':'Source commit pins generation inputs. Generated artifacts are committed separately in the governance PR.'},
      'supersedes':{'baseline_id':'reviewer-r1-candidate','historical_capture':item(HERE/'historical-candidate.yaml'),
        'historical_source_commit':'c731b79ca1a8a02cc158c2bee988023d8b8f0a4f'},
      'hashing':{'algorithm':'sha256','encoding_rule':'hash_exact_file_bytes',
        'common_hashes':{'source_hash':common(source_paths),'generator_hash':common(gen_paths)},
        'note':'Source aggregate covers pinned source inputs excluding governance documents. Generator aggregate is exactly the integrated metadata definition. Every imported layer source is included in source inputs.'},
      'coordination_inputs':{'scientific_plan':item(ROOT/'manifests/v1.md')},
      'source_inputs':[item(ROOT/p) for p in source_paths],
      'implementation_sources':[item(ROOT/p) for p in gen_paths],
      'manuscript':{'editable_source':item(ROOT/'levels_tex/samplepaper.tex'),
        'role':'Pinned revision context only; no manuscript build or final editorial acceptance claimed.'},
      'model_topology':{'declared_article_composition':'PHY || MAC || SDN || APP || ENV || OBS',
        'integrated_model':{'present':True,**item(HERE/'model.xml')},
        'interface_contract':{'present':True,**item(ROOT/'evidence/instantiation/20260907-p2-scope/interface-contract.md')},
        'contract_amendments':item(ROOT/'evidence/instantiation/20260917-v03-contract-disposition/contracts.md')},
      'verification_configuration':{'uppaal':{'version':engine['tool_version'].splitlines()[0],
        'version_output':item(HERE/'verifyta-version.txt')},
        'license':{'status':'observed_working_in_prior_run','evidence':item(HERE/'tool-evidence.json')},
        'accepted_verification_runs':[],
        'canonical_parameter_set':item(HERE/'parameters.json'),
        'canonical_instance_vector':item(HERE/'instance-vector.json'),
        'canonical_query_set':item(HERE/'selected-queries.q'),
        'candidate_query_set':item(HERE/'candidate-queries.q'),
        'query_disposition':item(HERE/'query-disposition.json'),
        'claim_scope':item(ROOT/'evidence/governance/20260910-p1-p2-review/final-20260923/README.md'),
        'readiness':'pending_gate_decision','note':'15 selected obligations/diagnostics; no full C01/C02 result claimed.'},
      'hardware':{'policy':'record_hardware_per_run'},
      'gate_1':{'status':'pending','passed':False,'P1_accepted':True,'P2_accepted':True,
        'acceptance_record':'https://github.com/artmus208/uppaal_sdn_isac/pull/47',
        'decision_record':'https://github.com/artmus208/uppaal_sdn_isac/issues/6',
        'remaining':['explicit_integrator_gate_decision'],
        'transition':'Only after explicit decision set metadata status=frozen/frozen=true and gate status=accepted/passed=true; retain exact input hashes.'}}
    assert manifest['hashing']['common_hashes']['generator_hash']['value']==source['generator_hash']
    (HERE/'proposed-baseline.yaml').write_text(yaml.safe_dump(manifest,allow_unicode=True,sort_keys=False))
    print('Proposal built: accepted model/query identity, source Git pins, full vector, parameters, 15 selected queries, prior tool evidence. Gate pending.')
if __name__=='__main__':main()
