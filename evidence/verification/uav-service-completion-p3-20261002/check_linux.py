"""Independent Linux software/static checks; no native verifier queries."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
commands=[('coordination',[sys.executable,'-B','scripts/check_coordination.py']),('historical-hashes',[sys.executable,'-B','scripts/check_coordination.py','--audit-hashes','--commit','HEAD','--output',str(HERE/'checks-linux/historical-hashes.json')]),('candidate-generation',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/generate.py','--check']),('candidate-audit',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/audit.py']),('software-suite',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v']),('mcp-smoke',[sys.executable,'-B','-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),('examples',[sys.executable,'-B','-m','uppaal_mcp.cli','list-examples']),('diff-check',['git','-C',str(ROOT),'diff','--check','46bf268c66d6ec2c106ae4ce8e8d5f893315ad91'])]
(HERE/'checks-linux').mkdir(exist_ok=True)
results=[]
for name,cmd in commands:
    started=time.monotonic()
    with (HERE/f'checks-linux/{name}.stdout.txt').open('wb') as out,(HERE/f'checks-linux/{name}.stderr.txt').open('wb') as err:
        p=subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=err)
    results.append({'name':name,'command':cmd,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-started,'stdout':f'checks-linux/{name}.stdout.txt','stderr':f'checks-linux/{name}.stderr.txt','evidence_kind':'software_or_static_validation'})
    (HERE/'checks-linux/results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,p.returncode,flush=True)
