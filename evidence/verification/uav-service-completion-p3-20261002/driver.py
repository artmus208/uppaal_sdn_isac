"""One-shot scoped native campaign. Never use to audit or retry."""
import json, os, subprocess, sys, time
from pathlib import Path
from prepare import HERE,ROOT,GIT,BRANCH,VERIFIER,sha,save
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.verification_manager import sample

def git(*args):return subprocess.run([GIT,'-C',str(ROOT),*args],capture_output=True,text=True,check=True).stdout.strip()
def checkpoint(message):
    scope=HERE.relative_to(ROOT).as_posix()
    git('add','--',scope)
    git('commit','-m',message)
    print(git('status','--short','--branch'),git('log','-1','--oneline','--decorate'),git('remote','-v'),flush=True)
    assert 'github.com/artmus208/uppaal_sdn_isac' in git('remote','get-url','origin')
    git('push','-u','origin',BRANCH)
    assert not git('status','--porcelain')
    return git('rev-parse','HEAD')
def main():
    assert os.name=='nt'
    assert not git('status','--porcelain'),'Need clean committed execution source'
    ledger=json.loads((HERE/'query-ledger.json').read_text())
    assert ledger['campaign_status']=='prepared' and not any(q['attempt_consumed'] for q in ledger['queries']),'No restart/retry; inspect durable ledger and owned processes'
    pre=json.loads((HERE/'preflight/verifier.json').read_text());assert pre['version_matches']
    env=json.loads((HERE/'environment.json').read_text())
    assert Path(sys.executable).resolve()==Path(env['executable']).resolve(),'Use direct native Python, not a venv launcher'
    assert json.loads((HERE/'preflight/direct-python-memory-monitor.json').read_text())['sample_exceeds_32_mib']
    assert sha(VERIFIER)==pre['executable_hash']
    ps=subprocess.run(['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-Command','@(Get-Process verifyta -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True,check=True)
    assert ps.stdout.strip()=='0','Existing native verifier: do not overlap/kill'
    # Exercise native metrics on a Python sleep child, without any model/query.
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(3)'])
    try:
        metrics=sample(child);assert metrics['rss_bytes'] is not None and metrics['cpu_seconds'] is not None
    finally:child.terminate();child.wait()
    save('preflight/monitor.json',{'status':'available','sample':metrics,'kind':'native OS metrics probe on Python child; no verifier/query execution'})
    checkpoint('P3: preserve native monitor preflight (#87)')
    assignment=json.loads((HERE/'assignment.json').read_text())
    for q in ledger['queries']:
        queue=HERE/q['queue_path'];cfg=json.loads((queue/'queue.json').read_text())
        assert not list((queue/'attempts').glob('*')),'Prior attempt; do not retry'
        assert sha(queue/'model.xml')==assignment['model_hash']
        assert sha(queue/'query-001.q')==q['query_hash']==sha(ROOT/q['query_path'])
        assert cfg['options']==['-o','0','-t','0'] and cfg['timeout_seconds']==600 and cfg['memory_stop_bytes']==env['memory_stop_bytes']
        q.update(attempt_consumed=True,status='reserved',reason='Durable attempt reservation; interrupted attempt counts as used')
        ledger['campaign_status']='running';save('query-ledger.json',ledger)
        source=checkpoint('P3: reserve '+q['query_id']+' attempt 01 (#87)')
        command=[sys.executable,'-B','-m','uppaal_mcp.verification_manager','start',str(queue)]
        # Clean source check precedes writing owned runtime files.
        assert not git('status','--porcelain')
        save(q['queue_path']+'/provenance.json',{'execution_source_commit':source,'driver_hash':sha(__file__),'manager_hash':sha(ROOT/'src/uppaal_mcp/verification_manager.py'),'assignment':assignment,'environment':env,'manager_command':command,'init_command':[sys.executable,'-B','-m','uppaal_mcp.verification_manager','init',str(queue),'--model',str(ROOT/'evidence/instantiation/uav-service-completion-candidate/model.xml'),'--queries',str(ROOT/q['query_path']),'--verifyta',str(VERIFIER),'--timeout','600','--memory-mib',str(env['memory_mib'])]})
        print('START',q['query_id'],source,flush=True)
        with (queue/'manager.stdout.txt').open('wb') as out,(queue/'manager.stderr.txt').open('wb') as err:
            run=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=err)
        results=list(queue.glob('attempts/*/result.json'))
        if len(results)==1:
            result=json.loads(results[0].read_text());q.update(status=result['status'],verdict=result['verdict'],reason=None,result_path=results[0].relative_to(HERE).as_posix(),execution_source_commit=source,manager_exit_code=run.returncode)
        else:q.update(status='error',verdict=None,reason='Manager exited without exactly one result; inspect raw preflight/logs',manager_exit_code=run.returncode,execution_source_commit=source)
        stop=q['status'] not in ('success','timeout','memory_limit')
        if stop:
            ledger['campaign_status']='stopped'
            for remaining in ledger['queries']:
                if not remaining['attempt_consumed']:remaining.update(reason='Campaign halted after '+q['query_id']+': '+q['status'])
        elif q is ledger['queries'][-1]:ledger['campaign_status']='completed'
        save('query-ledger.json',ledger)
        checkpoint('P3: preserve '+q['query_id']+' '+q['status']+' evidence (#87)')
        print('END',q['query_id'],q['status'],q['verdict'],flush=True)
        if stop:break
if __name__=='__main__':main()
