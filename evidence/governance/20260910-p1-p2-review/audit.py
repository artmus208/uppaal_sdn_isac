"""Read-only candidate audit; no model checking and no Gate acceptance."""
import hashlib,json,subprocess,sys,platform,datetime,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.phy.alpha import classify_sample
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(name,value):
 (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
c=generate(ROOT)
(HERE/'model.xml').write_bytes(c.model_xml.encode());(HERE/'queries.q').write_bytes(c.queries.encode())
write('composition.json',c.metadata)
inputs=c.metadata['source_hashes'];generators={k:v for k,v in {**inputs,**c.metadata['implementation_sources']}.items() if k.startswith('src/')}
def aggregate(entries):return sha(''.join(f'{value}  {name}\n' for name,value in sorted(entries.items())).encode())
record={'status':'candidate_not_accepted','gate_1_accepted':False,'canonical_source_commit':'5fbcc80311776b85b6d9f28c4e06f4eee15a2ef2','materialized_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'materialized_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),'provenance_note':'Local materialization combines exact published #24 tree with all 32 exact #27 files; canonical commit history is unavailable through Git CLI. GitHub comparisons establish unchanged #24 merge and additive #27 scope.','manuscript_path':'levels_tex/samplepaper.tex','manuscript_hash':sha((ROOT/'levels_tex/samplepaper.tex').read_bytes()),'source_hash':aggregate(inputs),'source_hash_inputs':inputs,'generator_hash':aggregate(generators),'generator_hash_inputs':generators,'aggregate_construction':'SHA256 of sorted UTF-8 records: <sha256> two spaces <path> LF','model_hash':sha(c.model_xml.encode()),'query_hash':sha(c.queries.encode()),'parameter_set':c.metadata['parameter_set'],'source_parameters':c.metadata['source_parameters'],'instance_vector':c.metadata['instance_vector'],'manifests':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [ROOT/'manifests/v1.md',ROOT/'manifests/collaboration-v1.yaml',ROOT/'manifests/baselines/reviewer-r1.yaml']},'tool_version_reference':'verifier-version.json','verification_status':'not_run'}
write('candidate-inputs.json',record)
cases=[]
for key,output,t,expected in [('SINR_c','SINRClass',0,'OUTAGE'),('SINR_c','SINRClass',10,'LOW'),('SINR_c','SINRClass',25,'OK'),('Pd','PdClass',.5,'FAILED'),('Pd','PdClass',.9,'LOW'),('Rfa','RfaClass',.05,'HIGH'),('Rfa','RfaClass',.2,'CRITICAL'),('AoS_CTRL','AoSClass',10,'EXPIRED')]:
 actual=classify_sample({key:t})[output];cases.append({'input':key,'value':t,'expected':expected,'actual':actual});assert actual==expected
write('implementation-probes.json',{'threshold_equalities':cases,'omitted_measurements':classify_sample({}),'nonfinite_nan_input':classify_sample({k:math.nan for k in ['SINR_c','Pd','Rfa','AoS_CTRL']}),'out_of_domain_input':classify_sample({'Pd':2,'Rfa':-1,'AoS_CTRL':-1}),'interpretation':'Equality correction present. Missing/nonfinite/domain validation proposed by report is not implemented in the excluded demo mapper; these results do not describe the finite environment validity handling.'})
command=['/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe','--version']
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
 r=subprocess.run(command,capture_output=True,timeout=20);stdout,stderr,code=r.stdout,r.stderr,r.returncode
except (OSError,subprocess.TimeoutExpired) as e:
 stdout=b'';stderr=str(e).encode();code=None
(HERE/'verifier.stdout.txt').write_bytes(stdout);(HERE/'verifier.stderr.txt').write_bytes(stderr)
write('verifier-version.json',{'command':command,'started_at_utc':started,'environment':platform.platform(),'exit_code':code,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'actual_version_output':stdout.decode(errors='replace'),'claim':'version/availability only; not model checking or a new license smoke'})
print(json.dumps({'equalities':len(cases),'model_hash':record['model_hash'],'query_hash':record['query_hash'],'version_exit_code':code,'gate_1_accepted':False}))
