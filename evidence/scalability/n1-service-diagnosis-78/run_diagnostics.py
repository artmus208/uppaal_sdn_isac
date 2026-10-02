#!/usr/bin/env python3
"""Single authorized three-query campaign. No retries or model modifications."""
import argparse
import base64
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SCOPE=HERE.relative_to(ROOT)
BASE='8237e8c2bec41aa1bb943cc33be1ac9586d03759'
APPROVED='701295a3339c9935bad1c6840e90fa8fc89dbb23'
MANIFEST='manifests/baselines/uav-family-r1.yaml'
MANIFEST_HASH='5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf'
BINARY_HASH='4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5'
EXE=Path('/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe')
PS=Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
DURABLE=Path('/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/evidence/scalability/n1-service-diagnosis-78/handoff')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False,sort_keys=True)+'\n');tmp.replace(p)
ACTIVE_BUDGET=None
def bound(seconds):return ACTIVE_BUDGET.timeout(seconds) if ACTIVE_BUDGET else seconds
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,timeout=bound(10)).strip()
def win(p):return subprocess.check_output(['wslpath','-w',str(p.resolve())],text=True,timeout=bound(3)).strip()


class Budget:
    def __init__(self):self.start=time.monotonic()
    def used(self):return time.monotonic()-self.start
    def require(self,reserve):
        if self.used()+reserve>300:raise RuntimeError('300-second total wall budget reserve exhausted')
    def timeout(self,nominal):
        self.require(nominal+10)
        return min(nominal,300-self.used()-10)


def pins():
    p=json.loads((HERE/'protocol.json').read_text())
    for rel in ['PROTOCOL.md','protocol.json']+[str(Path(q['path']).relative_to(SCOPE)) for q in p['queries']]:
        orig=subprocess.check_output(['git','show',APPROVED+':'+str(SCOPE/rel)],cwd=ROOT,timeout=bound(10))
        if (HERE/rel).read_bytes()!=orig:raise RuntimeError('Approved protocol/query drift: '+rel)
    if sha(ROOT/MANIFEST)!=MANIFEST_HASH or sha(ROOT/p['model'])!=p['model_hash'] or sha(ROOT/p['monitor'])!=p['monitor_hash']:
        raise RuntimeError('Model/manifest/monitor drift')
    if sha(EXE)!=BINARY_HASH:raise RuntimeError('Binary drift')
    for q in p['queries']:
        if sha(ROOT/q['path'])!=q['sha256']:raise RuntimeError('Query drift')
    approval=json.loads((HERE/'authorization.json').read_text())
    if approval['user_quote']!='Даю добро' or approval['approved_commit']!=APPROVED:raise RuntimeError('Authorization missing')
    manifest=json.loads((ROOT/MANIFEST).read_text())
    for item in manifest['models'][0]['files'].values():
        if sha(ROOT/item['path'])!=item['sha256']:raise RuntimeError('N=1 input pin drift: '+item['path'])
    return p,manifest


def native_result_path(config):
    # ConfigPath tool.config.json stores result tool.monitor.json (not tool.config.monitor.json).
    value=json.loads(config.read_text())['result']
    return Path(subprocess.check_output(['wslpath','-u',value],text=True,timeout=bound(3)).strip())


def cleanup(config):
    path=native_result_path(config)
    if not path.exists():return {'pid_available':False,'process_absence_confirmed':False}
    rec=json.loads(path.read_text(encoding='utf-8-sig'));pid=rec.get('process_id')
    if not pid or rec.get('process_reaped'):return {'pid_available':bool(pid),'process_absence_confirmed':bool(rec.get('process_reaped'))}
    # Guard native identity before killing an owned PID; confirm absence afterward.
    cp=win(config).replace("'","''")
    code=("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
          "$c=Get-Content -LiteralPath '"+cp+"' -Raw -Encoding UTF8|ConvertFrom-Json; "
          "$r=Get-Content -LiteralPath $c.result -Raw -Encoding UTF8|ConvertFrom-Json; "
          "$p=Get-Process -Id ([int]$r.process_id) -ErrorAction SilentlyContinue; "
          "if($p){$start=[DateTimeOffset]::Parse($r.started_at_utc).UtcDateTime; "
          "if($p.Path -ne $c.executable -or $p.StartTime.ToUniversalTime() -lt $start.AddSeconds(-1) -or $p.StartTime.ToUniversalTime() -gt $start.AddSeconds(5)){throw 'PID identity mismatch'}; "
          "& \"$env:SystemRoot\\System32\\taskkill.exe\" /PID $p.Id /T /F 2>&1|Out-Null; "
          "if(-not $p.WaitForExit(2000)){$p.Kill();$p.WaitForExit(2000)|Out-Null}}; "
          "$left=Get-Process -Id ([int]$r.process_id) -ErrorAction SilentlyContinue; "
          "if($left){throw 'Owned process remains alive'}; [Console]::Out.Write('PROCESS_ABSENT')")
    encoded=base64.b64encode(code.encode('utf-16le')).decode()
    r=subprocess.run([str(PS),'-NoProfile','-NonInteractive','-EncodedCommand',encoded],capture_output=True,timeout=10)
    (config.parent/'watchdog-cleanup.stdout.txt').write_bytes(r.stdout)
    (config.parent/'watchdog-cleanup.stderr.txt').write_bytes(r.stderr)
    return {'pid_available':True,'pid':pid,'cleanup_exit':r.returncode,'process_absence_confirmed':r.returncode==0 and b'PROCESS_ABSENT' in r.stdout}


def invoke(script,config,nominal,budget):
    cmd=[str(PS),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',win(script),'-ConfigPath',win(config)]
    try:r=subprocess.run(cmd,capture_output=True,timeout=budget.timeout(nominal))
    except subprocess.TimeoutExpired as e:
        config.with_suffix('.wrapper.stdout.txt').write_bytes(e.stdout or b'')
        config.with_suffix('.wrapper.stderr.txt').write_bytes(e.stderr or b'')
        save(config.parent/'watchdog-cleanup.json',cleanup(config))
        raise RuntimeError('Native wrapper watchdog timeout; stopped, no retry') from e
    config.with_suffix('.wrapper.stdout.txt').write_bytes(r.stdout)
    config.with_suffix('.wrapper.stderr.txt').write_bytes(r.stderr)
    path=native_result_path(config)
    if not path.exists():raise RuntimeError('Native result missing, wrapper exit '+str(r.returncode))
    result=json.loads(path.read_text(encoding='utf-8-sig'))
    result.update(wrapper_command=cmd,wrapper_exit_code=r.returncode)
    if result.get('process_id') and not result.get('process_reaped'):
        cleaned=cleanup(config);save(config.parent/'watchdog-cleanup.json',cleaned)
        result.update(status='monitor_error',cleanup=cleaned)
        if not cleaned.get('process_absence_confirmed'):raise RuntimeError('Owned native child cleanup unconfirmed')
    return result


def hardware(folder,protocol,budget):
    config=folder/'hardware.config.json'
    save(config,{'mode':'probe','result':win(folder/'hardware.json')})
    h=invoke(ROOT/protocol['monitor'],config,15,budget)
    if h['wrapper_exit_code']!=0:raise RuntimeError('Hardware probe failed')
    if int(h['available_physical_ram_bytes'])<3*1024**3:raise RuntimeError('Less than 3 GiB free native RAM; no launch')
    if str(h['os_build'])!='19045' or not any('i5-8300H' in c for c in h['cpu_models']):raise RuntimeError('Host differs from approved Windows10/Intel')
    return h


def run_native(folder,exe,args,limit,memory,protocol,budget,metadata=False):
    config=folder/'tool.config.json'
    save(config,{'mode':'run','executable':win(exe),'arguments':args,'arguments_windows':subprocess.list2cmdline(args),'cwd':win(exe.parent),'compile_only':False,'timeout_seconds':limit,'memory_limit_bytes':memory,'sample_interval_ms':50,'stdout':win(folder/'tool.stdout.txt'),'stderr':win(folder/'tool.stderr.txt'),'samples':win(folder/'tool.memory.csv'),'result':win(folder/'tool.monitor.json')})
    return invoke(HERE/'metadata.ps1' if metadata else ROOT/protocol['monitor'],config,limit+20,budget)


def classify(raw,stdout,stderr):
    if raw['status']!='success':return raw['status'],None
    if raw.get('exit_code')!=0 or raw.get('wrapper_exit_code')!=0 or not raw.get('process_reaped') or not raw.get('samples'):
        return 'monitor_error',None
    if re.search(r'(?:^|\n)\s*(?:error|syntax error|type error|license error)\b',stdout+'\n'+stderr,re.I):return 'tool_error',None
    matches=re.findall(r'-- Formula is (NOT satisfied|satisfied)\.',stdout)
    indices=re.findall(r'Verifying formula (\d+)',stdout)
    if len(matches)!=1 or indices not in ([],['1']):return 'verdict_error',None
    return 'success','satisfied' if matches[0]=='satisfied' else 'violated'


def artifact(p):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
    if len(raw)>100000:
        packed=p.with_suffix(p.suffix+'.gz');packed.write_bytes(gzip.compress(raw,mtime=0));p.unlink();p=packed
    return {'path':str(p.relative_to(ROOT)),'sha256':h,'storage_sha256':sha(p),'encoding':'gzip' if p.suffix=='.gz' else 'raw'}


def checkpoint(label):
    git('add',str(SCOPE))
    if git('diff','--cached','--name-only'):git('commit','-m','P2: checkpoint '+label+' (#78)')
    status=git('status','--short','--branch');head=git('log','-1','--oneline','--decorate');remotes=git('remote','-v')
    if git('status','--porcelain'):raise RuntimeError('Unexpected dirty checkpoint')
    DURABLE.mkdir(parents=True,exist_ok=True);tmp=DURABLE/'execution-next.bundle'
    subprocess.run(['git','bundle','create',str(tmp),git('branch','--show-current')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,timeout=bound(20))
    subprocess.run(['git','bundle','verify',str(tmp)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=bound(10))
    tmp.replace(DURABLE/'execution.bundle');(DURABLE/'execution-checkpoint.txt').write_text(status+'\n'+head+'\n'+remotes+'\n')


def campaign(expected):
    global ACTIVE_BUDGET
    protocol,manifest=pins()
    if git('status','--porcelain') or git('rev-parse','HEAD')!=expected:raise RuntimeError('Expected clean published source required')
    folder=HERE/'runs/diagnostic-001';folder.mkdir(parents=True,exist_ok=False)
    meta=manifest['models'][0];version=None
    rows=[{'run_id':'n1-service-78-diagnostic-001-'+q['id'],'query_id':q['id'],'formula':q['query'],'status':'not_started','reason':'pending','property_verdict':None,'result_per_query':[],'source_commit':expected,'base_commit':BASE,'baseline_id':manifest['metadata']['id'],'baseline_manifest_sha256':MANIFEST_HASH,'model_path':protocol['model'],'model_hash':protocol['model_hash'],'query_path':q['path'],'query_hash':q['sha256'],'generator_hash':meta['generator_hash'],'source_hash':meta['source_hash'],'parameter_set':json.loads((ROOT/meta['files']['parameters.json']['path']).read_text()),'instance_vector':json.loads((ROOT/meta['files']['instance-vector.json']['path']).read_text()),'evidence_kind':'direct_model_checking','acceptance_status':'not_reviewed','tool_version':None} for q in protocol['queries']]
    settings={'status':'running','source_commit':expected,'working_tree_at_start':'clean','authorization_reference':'https://github.com/artmus208/uppaal_sdn_isac/issues/78','authorization_sha256':sha(HERE/'authorization.json'),'approved_protocol_commit':APPROVED,'protocol_hash':sha(HERE/'protocol.json'),'runner_hash':sha(Path(__file__)),'metadata_helper_hash':sha(HERE/'metadata.ps1'),'monitor_hash':protocol['monitor_hash'],'binary_hash':sha(EXE),'budget_seconds':300,'budget_measure':'one monotonic wall interval from before first native probe through final cleanup, including controls, metadata, probes, wrapper and checkpoints','controls':[],'metadata':[],'operating_environment':platform.platform(),'inherited_UPPAAL_flags_removed':True,'environment':{'target':'native Windows via WSL','LC_ALL':os.environ.get('LC_ALL'),'LANG':os.environ.get('LANG')},'started_at_utc':utc()}
    budget=Budget();ACTIVE_BUDGET=budget
    def persist():
        settings['elapsed_wall_seconds']=budget.used();save(folder/'settings.json',settings);save(folder/'runs.json',rows)
    persist()
    try:
        cases=[('normal',"[Console]::Out.Write('out'); [Console]::Error.Write('err'); Start-Sleep -Seconds 1",5,2*1024**3,'success'),('timeout','Start-Sleep -Seconds 10',1,2*1024**3,'timeout'),('memory','Start-Sleep -Seconds 10',5,1024**2,'memory_limit')]
        for name,code,limit,memory,want in cases:
            budget.require(65);cell=folder/'controls'/name;cell.mkdir(parents=True)
            h=hardware(cell,protocol,budget);budget.require(65)
            encoded=base64.b64encode(("$ProgressPreference='SilentlyContinue'; "+code).encode('utf-16le')).decode()
            raw=run_native(cell,PS,['-NoProfile','-NonInteractive','-EncodedCommand',encoded],limit,memory,protocol,budget)
            ok=raw['status']==want and raw['process_reaped'] and raw['samples']>0 and raw['wrapper_exit_code']==0
            if name=='normal':ok=ok and (cell/'tool.stdout.txt').read_bytes()==b'out' and (cell/'tool.stderr.txt').read_bytes()==b'err'
            if name=='memory':ok=ok and max(raw['peak_private_bytes'],raw['peak_reported_working_set_bytes'])>=memory
            settings['controls'].append({'name':name,'passed':bool(ok),'hardware':h,'monitor':raw});persist();print('control',name,ok,flush=True)
            if not ok:raise RuntimeError('Native monitor control failed')
        budget.require(65);checkpoint('diagnostic native controls')
        for option in ['--version','--help']:
            budget.require(65);cell=folder/option[2:];cell.mkdir();h=hardware(cell,protocol,budget);budget.require(65)
            raw=run_native(cell,EXE,[option],10,2*1024**3,protocol,budget,metadata=True)
            so=(cell/'tool.stdout.txt').read_text(errors='replace');settings['metadata'].append({'option':option,'hardware':h,'result':raw,'stdout':artifact(cell/'tool.stdout.txt'),'stderr':artifact(cell/'tool.stderr.txt')});persist()
            if raw['status']!='success' or raw['exit_code']!=0 or raw['wrapper_exit_code']!=0 or not raw['process_reaped']:raise RuntimeError('Metadata failed')
            if option=='--version':
                version=next((s.strip() for s in so.splitlines() if s.startswith('UPPAAL ')),None)
                if version!=manifest['tool_version']:raise RuntimeError('Actual version differs from approved baseline')
                settings['tool_version']=version
            elif not all(s in so for s in ['0:Breadth first','--exploration','--state-representation']):raise RuntimeError('Required search options missing')
        persist();budget.require(65);checkpoint('diagnostic metadata')
        for q,row in zip(protocol['queries'],rows):
            budget.require(65);cell=folder/q['id'];cell.mkdir();h=hardware(cell,protocol,budget);pins();budget.require(65)
            args=[win(cell/'trace') if a=='${OUT}/trace' else win(ROOT/a[8:]) if a.startswith('${ROOT}/') else a for a in q['arguments']]
            row.update(status='running',reason=None,tool_version=version,command=[win(EXE)]+args,hardware_description=h,operating_environment=settings['operating_environment'],environment_overrides={},inherited_UPPAAL_flags_removed=True,timeout_seconds=30,memory_limit_bytes=2*1024**3)
            persist();budget.require(65)
            raw=run_native(cell,EXE,args,30,2*1024**3,protocol,budget)
            so=(cell/'tool.stdout.txt').read_text(errors='replace');se=(cell/'tool.stderr.txt').read_text(errors='replace')
            status,verdict=classify(raw,so,se);row.update(raw);row.update(status=status,property_verdict=verdict,result_per_query=[{'formula':q['query'],'verdict':verdict}] if verdict else [])
            for k,label in [('states_explored','States explored'),('states_stored','States stored')]:
                match=re.search(label+r'\s*:\s*(\d+) states',so);row[k]=int(match[1]) if match else 'not_available'
            row.update(stdout=artifact(cell/'tool.stdout.txt'),stderr=artifact(cell/'tool.stderr.txt'),trace={'requested':True,'files':[artifact(p) for p in sorted(cell.glob('trace*')) if p.is_file()]},monitor_reference=str((cell/'tool.monitor.json').relative_to(ROOT)),memory_samples_reference=str((cell/'tool.memory.csv').relative_to(ROOT)))
            if verdict=='satisfied' and not row['trace']['files']:
                row.update(status='trace_error',raw_stdout_verdict=verdict,property_verdict=None,result_per_query=[])
                status='trace_error';verdict=None
            persist();print(q['id'],status,verdict,'wall',round(budget.used(),3),flush=True)
            budget.require(35);checkpoint(q['id'])
            if status not in ('success','timeout','memory_limit') or not raw['process_reaped'] or not raw['samples']:raise RuntimeError('Tool/monitor/verdict failure')
            if status=='success' and verdict=='violated' and q['id']!='d3-useful-grant':raise RuntimeError('Downstream necessary condition violated; protocol stop')
        budget.require(1)
        settings['status']='completed'
    except BaseException as exc:
        settings.update(status='stopped',error=type(exc).__name__+': '+str(exc))
        for row in rows:
            if row['status']=='running':row.update(status='monitor_error',reason=str(exc),property_verdict=None,result_per_query=[])
            if row['status']=='not_started':row['reason']='campaign stopped: '+str(exc)
        print('STOP',settings['error'],flush=True)
    finally:
        settings['finished_at_utc']=utc();settings['within_total_budget']=budget.used()<=300;persist()
        # Normal paths are reaped; any exceptional cleanup evidence is retained explicitly.
        # This final evidence-only transport occurs after execution cleanup.
        ACTIVE_BUDGET=None
        checkpoint('diagnostic execution '+settings['status'])
    return settings['status']


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['pins','run']);ap.add_argument('--expected-source')
    a=ap.parse_args()
    if a.action=='pins':print(json.dumps({'pins':'matched','queries':len(pins()[0]['queries'])}))
    elif not a.expected_source:ap.error('--expected-source published SHA is required')
    else:raise SystemExit(0 if campaign(a.expected_source)=='completed' else 2)
