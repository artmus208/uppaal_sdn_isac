"""Conservative aggregate 6600-second guard; never starts/retries a query."""
import json,os,sys,time
from datetime import datetime,timezone
from prepare import HERE,ROOT,save
sys.path.insert(0,str(ROOT/'src'))
from uppaal_mcp.verification_manager import save as manager_save

def main():
    assert os.name=='nt'
    while True:
        ledger=json.loads((HERE/'query-ledger.json').read_text())
        if ledger['campaign_status'] in ('stopped','completed'):return
        q=ledger['queries'][-1]
        if q['status']=='reserved':
            folder=HERE/q['queue_path'];status=json.loads((folder/'status.json').read_text())
            if status.get('phase')=='running':
                previous=[json.loads(p.read_text()) for p in HERE.glob('runs/*/attempts/*/result.json') if folder not in p.parents]
                elapsed=sum(r['elapsed_seconds'] for r in previous)+status['elapsed_seconds']
                # Reserve 3 seconds for sampled stop/termination/result serialization.
                if elapsed>=6597:
                    request={'requested_at_utc':datetime.now(timezone.utc).isoformat(),'reason':'Conservative aggregate wall-time budget stop; configured query timeout unchanged','prior_attempt_wall_seconds':sum(r['elapsed_seconds'] for r in previous),'last_reported_query_wall_seconds':status['elapsed_seconds'],'maximum_total_seconds':6600,'termination_margin_seconds':3,'run_id':q['run_id'],'command_equivalent':[sys.executable,'-B','-m','uppaal_mcp.verification_manager','stop',str(folder)]}
                    save('budget-stop.json',request)
                    manager_save(folder/'control.json',{'action':'stop'})
                    print(json.dumps(request),flush=True);return
        time.sleep(.1)
if __name__=='__main__':main()
