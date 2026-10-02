"""Read-only offline evidence audit. No verifier execution."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.verifyta import parse_verifyta_outcomes,summarize_status

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,msg):
    if not v:raise ValueError(msg)
def audit():
    a=read(HERE/'assignment.json');ledger=read(HERE/'query-ledger.json');records=read(HERE/'results.json')['queries'];env=read(HERE/'environment.json')
    require(len(records)==len(ledger['queries'])==11,'eleven input identities')
    require(len({r['run_id'] for r in records})==11,'unique run IDs')
    require(env['memory_stop_bytes']==min(env['physical_ram_bytes']//2,8*1024**3)//1024**2*1024**2,'RAM budget')
    require(sha(ROOT/'manifests/baselines/uav-service-completion-r1.yaml')==a['manifest_hash'],'manifest hash')
    checked=0;statuses={}
    for l,r in zip(ledger['queries'],records):
        q=HERE/l['queue_path'];cfg=read(q/'queue.json')
        require(l['query_id']==r['query_id'] and l['run_id']==r['run_id'],'ordered identity')
        require(sha(ROOT/l['query_path'])==sha(q/'query-001.q')==l['query_hash']==r['query_hash'],'exact accepted query bytes')
        require(sha(q/'queries.q')==l['query_hash'],'original query snapshot')
        require(sha(q/'model.xml')==a['model_hash']==r['model_hash'],'model identity')
        require(cfg['options']==['-o','0','-t','0'] and cfg['timeout_seconds']==600 and cfg['memory_stop_bytes']==env['memory_stop_bytes'],'exact search/budget')
        require(len(cfg['tasks'])==1 and cfg['tasks'][0]['query']==l['formula']==r['formula'],'formula identity')
        attempts=list(q.glob('attempts/*/attempt.json'));require(len(attempts)<=1,'one attempt only')
        require(r['status']==l['status'] and r['verdict']==l['verdict'],'ledger/result status')
        statuses[r['status']]=statuses.get(r['status'],0)+1
        if not l['attempt_consumed']:
            require(not attempts and r['status']=='not_executed' and r['verdict'] is None,'unexecuted input')
            require(all(r[k] is None for k in ('start_utc','end_utc','wall_seconds','cpu_seconds','peak_rss_bytes')),'no invented unexecuted measurements')
            continue
        p=read(q/'provenance.json');require(p['execution_source_commit']==l['execution_source_commit']==r['execution_source_commit'],'source commit')
        require(p['assignment']==a and p['environment']==env,'pinned provenance')
        git='C:/Program Files/Git/bin/git.exe' if sys.platform=='win32' else 'git'
        for filename,expected in [(HERE/'driver.py',p['driver_hash']),(ROOT/'src/uppaal_mcp/verification_manager.py',p['manager_hash'])]:
            content=subprocess.run([git,'-C',str(ROOT),'show',p['execution_source_commit']+':'+filename.relative_to(ROOT).as_posix()],capture_output=True,check=True).stdout
            require(hashlib.sha256(content).hexdigest()==expected,'committed execution code')
        committed_ledger=subprocess.run([git,'-C',str(ROOT),'show',p['execution_source_commit']+':'+(HERE/'query-ledger.json').relative_to(ROOT).as_posix()],capture_output=True,check=True).stdout
        reserved=next(x for x in json.loads(committed_ledger)['queries'] if x['query_id']==l['query_id'])
        require(reserved['attempt_consumed'] and reserved['status']=='reserved','durable pre-start reservation')
        if not attempts:
            require(r['status']=='error' and r['verdict'] is None,'failed manager preflight only');continue
        raw=read(attempts[0].parent/'result.json');folder=attempts[0].parent
        for name,expected in read(folder/'hashes.json').items():require(sha(folder/name)==expected,'raw attempt hash '+name)
        require(raw['model_hash']==r['model_hash'] and raw['query_hash']==r['query_hash'] and raw['formula']==r['formula'],'raw formula identity')
        require(raw['run_id']==r['manager_attempt_id'] and raw['status']==r['status'] and raw['verdict']==r['verdict'],'raw verdict identity')
        require(raw['tool_version']==r['tool_version']==a['tool_version'],'full actual tool version')
        require(cfg['executable_hash']==a['executable_hash']==r['executable_hash'],'executable identity')
        require(raw['command'][1:5]==['-o','0','-t','0'] and Path(raw['command'][-1]).name=='query-001.q' and Path(raw['command'][-2]).name=='model.xml','actual flags')
        session=read(q/'sessions'/raw['session']/'session.json');require(session['queue_hash']==sha(q/'queue.json') and session['hardware']['manager_hash']==p['manager_hash'],'session provenance')
        out=(folder/'stdout.txt').read_text(encoding='utf-8',errors='replace');err=(folder/'stderr.txt').read_text(encoding='utf-8',errors='replace')
        if raw['status']=='success':
            outcomes=parse_verifyta_outcomes(out,[r['formula']]);status=summarize_status(raw['returncode'],outcomes,out,err,expected_query_count=1)
            require(status==('satisfied' if r['verdict']=='satisfied' else 'not_satisfied'),'explicit machine result')
        else:require(r['verdict'] is None,'inconclusive must have null verdict')
        for item in r['raw_files']:require(sha(HERE/item['path'])==item['sha256'],'registry raw hash '+item['path'])
        require(r['wall_seconds']==raw['elapsed_seconds'] and r['cpu_seconds']==raw['cpu_seconds'] and r['peak_rss_bytes']==raw['peak_rss_bytes'],'measurement provenance')
        checked+=1
    if (HERE/'artifacts-sha256.json').exists():
        for name,h in read(HERE/'artifacts-sha256.json').items():require(sha(HERE/name)==h,'artifact integrity '+name)
    return {'audit':'ok','kind':'offline_static_evidence_integrity','queries':11,'attempts_audited':checked,'statuses':statuses,'new_verifier_executions':0,'acceptance_status':'pending_independent_review'}
if __name__=='__main__':print(json.dumps(audit(),indent=2))
