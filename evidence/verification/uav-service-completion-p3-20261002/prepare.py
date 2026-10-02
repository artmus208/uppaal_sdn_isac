"""Read-only prerequisites and queue initialization; never executes a query."""
import ctypes, hashlib, json, os, platform, subprocess, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='46bf268c66d6ec2c106ae4ce8e8d5f893315ad91'
BRANCH='codex/carwasher/87-uav-completion-verification'
GIT='C:/Program Files/Git/bin/git.exe'
VERIFIER=Path('D:/UPPAAL/app/bin/verifyta.exe')
ORDER='admitted measurement enqueue attempt success loss timeout cancel deadline-equality completion-safety deadlock'.split()
def save(name,v):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def api(path,data=None):
    credentials=subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    token=dict(x.split('=',1) for x in credentials.stdout.splitlines() if '=' in x)['password']
    req=urllib.request.Request('https://api.github.com/'+path,headers={'Authorization':'Bearer '+token,'User-Agent':'issue87-carwasher','Accept':'application/vnd.github+json'},data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def main():
    assert os.name=='nt','Windows native Python required on this host'
    profile=api('user');assert profile['login']=='carwasher'
    save('preflight/identity.json',{'login':profile['login'],'id':profile['id'],'connector_login_read_only':'vadimnbkg'})
    issue=api('repos/artmus208/uppaal_sdn_isac/issues/87');save('preflight/issue87.json',issue)
    assert [a['login'] for a in issue['assignees']]==['carwasher']
    for n in (64,84):
        comments=api(f'repos/artmus208/uppaal_sdn_isac/issues/{n}/comments?per_page=100');save(f'preflight/issue{n}-comments.json',comments)
        for c in comments:
            if c['id'] in (5878071165,5946722646,5947256320):print(c['html_url'],c['user']['login'],c['body'])
    opened=api('repos/artmus208/uppaal_sdn_isac/issues?state=open&per_page=100');save('preflight/open-issues.json',opened)
    assert not any('uav-service-completion-p3-20261002' in (i.get('body') or '') for i in opened if i['number']!=87)
    claim=json.loads((HERE/'preflight/claim.json').read_text()) if (HERE/'preflight/claim.json').exists() else api('repos/artmus208/uppaal_sdn_isac/issues/87/comments',{'body':f'Owner carwasher starts the assigned P3 bounded campaign. Branch `{BRANCH}`; exact base `{BASE}` (`origin/read`); write scope `evidence/verification/uav-service-completion-p3-20261002/**`; explicitly selected baseline `uav-service-completion-r1-20261002`. Local native Git credentials confirmed carwasher; connector vadimnbkg used read-only. Separate clean clone on Windows D:; original dirty checkout preserved. Active scope recheck saved in evidence; #39/#80 remain unchanged. At most one attempt per accepted query, sequential, 600 s each, sampled memory min(50% native physical RAM, 8 GiB). No verification claim or gate acceptance.'});save('preflight/claim.json',claim)
    manifest=ROOT/'manifests/baselines/uav-service-completion-r1.yaml';assert sha(manifest)=='4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d'
    m=json.loads(manifest.read_text());checks=[]
    def walk(v):
        if isinstance(v,dict):
            if 'path' in v and 'sha256' in v:
                actual=sha(ROOT/v['path']);checks.append({'path':v['path'],'expected':v['sha256'],'actual':actual});assert actual==v['sha256'],v['path']
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(m)
    inventory=json.loads((ROOT/m['hashing']['input_inventory']['path']).read_text())
    for p,h in inventory['files'].items():
        actual=sha(ROOT/p)
        pinned=subprocess.run([GIT,'-C',str(ROOT),'show',m['repository']['input_commit']+':'+p],capture_output=True,check=True).stdout
        assert hashlib.sha256(pinned).hexdigest()==h,p
        accepted_operational=(p=='manifests/collaboration-v2.yaml' and actual=='fcce78b4ef3286e3e618de9cf107bcd4ed343908f3facec614f33e8d324cf97e')
        checks.append({'path':p,'expected_scientific_commit':h,'actual_checkout':actual,'scientific_blob_matches':True,'accepted_operational_delta':accepted_operational})
        assert actual==h or accepted_operational,p
    save('preflight/input-audit.json',{'manifest_hash':sha(manifest),'scope':m['scope'],'checks':checks,'kind':'static_validation'})
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(k,ctypes.c_ulonglong) for k in ('total_physical','available_physical','total_page','available_page','total_virtual','available_virtual','extended')]
    mem=Memory();mem.length=ctypes.sizeof(mem);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    limit_mib=min(mem.total_physical//2,8*1024**3)//1024**2
    env={'captured_at':datetime.now(timezone.utc).isoformat(),'os':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'python':sys.version,'executable':sys.executable,'physical_ram_bytes':mem.total_physical,'memory_mib':limit_mib,'memory_stop_bytes':limit_mib*1024**2,'calculation':'floor(min(total_physical_bytes/2,8589934592)/1048576)','monitor':'native WorkingSet/PeakWorkingSet sampled every second, not hard allocation cap'}
    hardware=subprocess.run(['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json'],capture_output=True)
    (HERE/'preflight/hardware.stdout.txt').write_bytes(hardware.stdout);(HERE/'preflight/hardware.stderr.txt').write_bytes(hardware.stderr)
    env['hardware_command_exit']=hardware.returncode;save('environment.json',env)
    executable_hash=sha(VERIFIER)
    with (HERE/'preflight/version.stdout.txt').open('wb') as out,(HERE/'preflight/version.stderr.txt').open('wb') as err:
        v=subprocess.run([str(VERIFIER),'--version'],cwd=VERIFIER.parent,stdout=out,stderr=err,timeout=20)
    version=(HERE/'preflight/version.stdout.txt').read_text(errors='replace')
    save('preflight/verifier.json',{'command':[str(VERIFIER),'--version'],'cwd':str(VERIFIER.parent),'exit_code':v.returncode,'tool_version':version or None,'executable_hash':executable_hash,'version_matches':v.returncode==0 and '5.0.0' in version and '714BA9DB36F49691' in version})
    print('VERSION:',version,'MEMORY MiB:',limit_mib)
    assignment={'issue':issue['html_url'],'process':'P3','owner':'carwasher','reviewer_proposed':'artmus208','base_ref':'origin/read','base_commit':BASE,'branch':BRANCH,'target':'read','write_scope':str(HERE.relative_to(ROOT)).replace('\\','/')+'/**','baseline_id':m['metadata']['id'],'scientific_input_commit':m['repository']['input_commit'],'manifest_hash':sha(manifest),'model_hash':m['model']['sha256'],'parameters':{k:json.loads((ROOT/v['path']).read_text()) for k,v in m['parameters'].items() if k!='inventory'},'instance_vector':json.loads((ROOT/m['instance_vector']['path']).read_text()),'assumptions':m['assumptions'],'boundaries':m['boundaries'],'maximum_attempts_per_query':1,'timeout_seconds':600,'maximum_total_search_seconds':6600,'flags':['-o','0','-t','0'],'tool_version':version or None,'executable_hash':executable_hash,'activation_refs':['https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165','https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646','https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320']}
    save('assignment.json',assignment)
    ledger=[]
    sys.path.insert(0,str(ROOT/'src'))
    from uppaal_mcp.verification_manager import initialize
    selected={q['id']:q for q in m['query_set']['files']}
    for index,qid in enumerate(ORDER,1):
        q=selected[qid];run_id=f'issue87-{index:02d}-{qid}-attempt01-20261002'
        directory=HERE/'runs'/run_id
        initialize(directory,ROOT/m['model']['path'],ROOT/q['path'],VERIFIER,600,limit_mib)
        identical=sha(directory/'query-001.q')==q['sha256'] and sha(directory/'model.xml')==m['model']['sha256']
        ledger.append({'query_id':qid,'run_id':run_id,'query_path':q['path'],'query_hash':q['sha256'],'formula':q['formula'],'queue_path':directory.relative_to(HERE).as_posix(),'queue_query_hash':sha(directory/'query-001.q'),'queue_model_hash':sha(directory/'model.xml'),'queue_bytes_identical':identical,'attempt_consumed':False,'status':'not_executed','verdict':None,'reason':'Prepared only; execution prerequisites pending'})
    save('query-ledger.json',{'campaign_status':'prepared','queries':ledger})
    assert all(q['queue_bytes_identical'] for q in ledger),'Normalization mismatch: do not execute'
if __name__=='__main__':main()
