"""Software/static checks only; no UPPAAL query execution."""
import os,subprocess,sys,time
from prepare import HERE,ROOT,GIT,BASE,save

def main():
    commands=[('coordination',[sys.executable,'-B','scripts/check_coordination.py']),('historical-hashes',[sys.executable,'-B','scripts/check_coordination.py','--audit-hashes','--commit','HEAD','--output',str(HERE/'checks/historical-hashes.json')]),('candidate-generation',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/generate.py','--check']),('candidate-audit',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/audit.py']),('candidate-controls',[sys.executable,'-B','-m','unittest','discover','-s','evidence/instantiation/uav-service-completion-candidate','-p','test_*.py','-v']),('software-suite',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v']),('mcp-smoke',[sys.executable,'-B','-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),('examples',[sys.executable,'-B','-m','uppaal_mcp.cli','list-examples']),('diff-check',[GIT,'-C',str(ROOT),'diff','--check',BASE])]
    results=[]
    (HERE/'checks').mkdir(exist_ok=True)
    for name,command in commands:
        started=time.monotonic()
        with (HERE/f'checks/{name}.stdout.txt').open('wb') as out,(HERE/f'checks/{name}.stderr.txt').open('wb') as err:
            p=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=err)
        results.append({'name':name,'command':command,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-started,'stdout':f'checks/{name}.stdout.txt','stderr':f'checks/{name}.stderr.txt','evidence_kind':'software_or_static_validation'})
        save('checks/results.json',results);print(name,p.returncode,flush=True)
if __name__=='__main__':main()
