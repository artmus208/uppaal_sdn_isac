"""Execute all accepted P3 formulas on exact frozen XML, one native process each."""
import argparse,datetime,hashlib,json,os,platform,re,subprocess,sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PS='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
VERIFY='/mnt/d/UPPAAL/app/bin/verifyta.exe'
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def win(p):return subprocess.check_output(['wslpath','-w',str(p)],text=True).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);args=ap.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):raise ValueError('invalid run id')
 if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):raise ValueError('clean source tree required')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 baseline=ROOT/'manifests/baselines/reviewer-r1.yaml';m=yaml.safe_load(baseline.read_bytes())
 assert m['metadata']['frozen'] and m['gate_1']['passed']
 out=ROOT/'evidence/verification/runs'/args.run_id;out.mkdir(parents=True,exist_ok=False)
 subprocess.run([sys.executable,'-B','scripts/check_coordination.py','--audit-hashes','--commit',commit,'--output',str(out/'baseline-audit.json')],cwd=ROOT,check=True)
 cfg=m['verification_configuration'];model=ROOT/m['model_topology']['integrated_model']['path']
 queries=ROOT/cfg['canonical_query_set']['path'];specs=json.loads((queries.parent/'selected-queries.json').read_text())
 assert sha(model.read_bytes())==m['model_topology']['integrated_model']['sha256']
 assert sha(queries.read_bytes())==cfg['canonical_query_set']['sha256']
 version=subprocess.run([VERIFY,'--version'],capture_output=True,timeout=20)
 (out/'version.stdout.txt').write_bytes(version.stdout);(out/'version.stderr.txt').write_bytes(version.stderr)
 assert version.returncode==0 and cfg['uppaal']['version'] in version.stdout.decode()
 hardware=subprocess.run([PS,'-NoProfile','-Command',"[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false); $os=Get-CimInstance Win32_OperatingSystem; $cpu=Get-CimInstance Win32_Processor; @{os=$os.Caption;version=$os.Version;ram_bytes=([long]$os.TotalVisibleMemorySize*1024);cpu=@($cpu|Select-Object Name,NumberOfCores,NumberOfLogicalProcessors)}|ConvertTo-Json -Depth 4"],capture_output=True,timeout=30)
 (out/'hardware.stdout.json').write_bytes(hardware.stdout);(out/'hardware.stderr.txt').write_bytes(hardware.stderr)
 assert hardware.returncode==0
 identity={'run_id':args.run_id,'workstream_id':'P3','issue':39,'produced_by_github_handle':'vadimnbkg','reviewed_by_github_handle':None,'source_commit':commit,'base_commit':'adea99b05195191eec115621613d4190eba06bf0','source_tree_clean_at_start':True,'baseline_id':m['metadata']['id'],'baseline_manifest_sha256':sha(baseline.read_bytes()),'source_hash':m['hashing']['common_hashes']['source_hash']['value'],'generator_hash':m['hashing']['common_hashes']['generator_hash']['value'],'model_path':model.relative_to(ROOT).as_posix(),'model_hash':sha(model.read_bytes()),'frozen_query_set_hash':sha(queries.read_bytes()),'parameter_set':json.loads((ROOT/cfg['canonical_parameter_set']['path']).read_text()),'instance_vector':json.loads((ROOT/cfg['canonical_instance_vector']['path']).read_text()),'tool_version':version.stdout.decode(),'operating_environment':platform.platform(),'native_hardware':json.loads(hardware.stdout.decode('utf-8-sig')),'limits':{'per_query_seconds':60,'memory_stop_bytes':2147483648,'parallelism':1},'status':'running'}
 dump(out/'run.json',identity);results=[]
 for index,s in enumerate(specs,1):
  name=f'{index:02d}-{s["id"]}';q=out/(name+'.q');q.write_text(s['query']+'\n')
  command=['-t','1','-X',win(out/(name+'-trace')),win(model),win(q)]
  config={'executable':win(Path(VERIFY)),'arguments':command,'stdout':win(out/(name+'.stdout.txt')),'stderr':win(out/(name+'.stderr.txt')),'result':win(out/(name+'.native.json')),'timeout_seconds':60,'memory_stop_bytes':2147483648}
  cp=out/(name+'.config.json');dump(cp,config)
  wrapper=subprocess.run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',win(HERE/'native-run.ps1'),'-Config',win(cp)],capture_output=True,timeout=90)
  (out/(name+'.wrapper.stdout.txt')).write_bytes(wrapper.stdout);(out/(name+'.wrapper.stderr.txt')).write_bytes(wrapper.stderr)
  native=out/(name+'.native.json')
  if wrapper.returncode!=0 or not native.exists():raise RuntimeError('native wrapper failed: '+name)
  record=json.loads(native.read_text(encoding='utf-8-sig'))
  stdout=(out/(name+'.stdout.txt')).read_text();stderr=(out/(name+'.stderr.txt')).read_text()
  verdicts=re.findall(r'Formula is (NOT satisfied|satisfied|MAYBE satisfied)',stdout+'\n'+stderr)
  status=record['termination'];verdict=None
  if status=='completed':
   status='success' if record['exit_code']==0 and len(verdicts)==1 and not re.search(r'(?im)^(?:error|exception|fatal)\b',stdout+'\n'+stderr) else 'error'
   if status=='success':verdict={'satisfied':'satisfied','NOT satisfied':'violated','MAYBE satisfied':'inconclusive'}[verdicts[0]]
  record.update(run_id=args.run_id+'-'+name,property_id=s['id'],role=s['role'],formal_query=s['query'],status=status,verdict=verdict,model_hash=identity['model_hash'],query_hash=sha(q.read_bytes()),tool_version=identity['tool_version'],source_commit=commit,exact_command=[config['executable'],*command],query_path=q.name,stdout_path=name+'.stdout.txt',stderr_path=name+'.stderr.txt',trace_paths=[p.name for p in out.glob(name+'-trace*')],states_explored=None)
  results.append(record);dump(out/'results.json',results)
  print(name,status,verdict,record['runtime_seconds'],record['peak_working_set_bytes'],flush=True)
 identity['status']='completed';identity['result_count']=len(results);dump(out/'run.json',identity)
 (out/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
 print('Saved',out,flush=True)
if __name__=='__main__':main()
