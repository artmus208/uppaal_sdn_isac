"""Offline integrity, formula, provenance, scope and budget audit. No UPPAAL."""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from prepare import HERE, ROOT, SCOPE, BASE, M_PATH, M_HASH, digest, products, derive

def require(condition,message):
    if not condition: raise ValueError(message)

def audit_preparation():
    pins=json.loads((HERE/'input-pins.json').read_text())
    for name,h in pins['files'].items():
        require(digest((ROOT/name).read_bytes())==h,'Input drift: '+name)
    for name,data in products().items():
        require((HERE/name).read_bytes()==data,'Prepared product drift: '+name)
    inv=json.loads((HERE/'query-inventory.json').read_text())
    require([i['slot'] for i in inv]==list(range(1,7)),'Six ordered slots required')
    require(sum(i['cap_seconds'] for i in inv)==1500,'Allocation differs from 1500 s')
    require(len({i['model_hash'] for i in inv[:5]})==1,'Slots 1–5 differ in domain')
    require(inv[5]['model_hash']==M_HASH and inv[5]['model_path']==M_PATH,'Q6 must use M')
    for i in inv:
        b=(ROOT/i['query_path']).read_bytes()
        require(b.endswith(b'\n') and b.count(b'\n')==1 and b'\r' not in b and not b.startswith(b'\xef\xbb\xbf'),'Query encoding')
        require(digest(b)==i['query_hash'] and b.decode().strip()==i['formula'],'Formula/hash identity')
        require('c82_sample_age' not in i['formula'],'Do not test advancing sample age after Completed')
    model,changes=derive((ROOT/M_PATH).read_bytes())
    original=ET.parse(ROOT/M_PATH).getroot();candidate=ET.fromstring(model)
    require(original.findtext('system')==candidate.findtext('system'),'Composition changed')
    require(len(candidate.findtext('system').split('system ')[-1].strip(' ;\n').split(','))==51,'Process count')
    if (HERE/'execution/model.xml').exists():
        require((HERE/'execution/model.xml').read_bytes()==model,'Materialized model differs')
        approval=json.loads((HERE/'execution/approval.json').read_text())
        require(approval.get('hnom_restrictions_and_materialization_approved') is True,'Unapproved materialization')
    seal=json.loads((HERE/'seal.json').read_text())
    for name,h in seal.items():
        require(digest((HERE/name).read_bytes())==h,'Preparation seal mismatch: '+name)
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    require(all(p.startswith(SCOPE+'/') for p in changed),'Out-of-scope tracked diff')
    return dict(kind='static/software only',queries=6,processes=51,changed_external_elements=len(changes),
                input_hashes=len(pins['files']),sealed_files=len(seal),search_allocation_seconds=1500,
                model_hash=M_HASH,prospective_hnom_hash=digest(model))

def audit_execution():
    execution=HERE/'execution'
    if not (execution/'session.json').exists():
        return dict(native_execution='not_executed',attempts=0,verdicts=[None]*6)
    from driver import parse_verdict
    session=json.loads((execution/'session.json').read_text())
    ledger=json.loads((execution/'ledger.json').read_text())
    inventory=json.loads((HERE/'query-inventory.json').read_text())
    require(len(ledger)==6,'Execution ledger size')
    attempts=sum(bool(x['attempt_consumed']) for x in ledger)
    require(attempts<=6,'Too many attempts')
    total=0;overruns=[];gaps=[];prior_end=None
    for slot,planned in zip(ledger,inventory):
        require(slot['slot']==planned['slot'] and slot['query_hash']==planned['query_hash'],'Ledger identity')
        if not slot['attempt_consumed']:
            require(slot['status']=='not_executed' and slot['verdict'] is None,'Unexecuted verdict')
            continue
        path=execution/'runs'/slot['run_id']/'result.json'
        if not path.exists():
            require(slot['status'] in ['interrupted','error'] and slot['verdict'] is None,'Missing result mislabeled')
            gaps.append('Missing completed result for '+slot['run_id']);continue
        r=json.loads(path.read_text())
        for key in ['slot','model_hash','query_hash','formula','cap_seconds','model_path','query_path']:
            require(r[key]==planned[key],'Run identity mismatch: '+key)
        require(r['tool_version']==session['tool_version'] and bool(r['tool_version']),'Actual version provenance')
        require(r['executable_sha256']==session['executable_sha256'],'Tool binary identity')
        require(r['source_commit']==r['execution_source_commit'],'Execution commit mismatch')
        subprocess.run(['git','merge-base','--is-ancestor',r['execution_source_commit'],'HEAD'],cwd=ROOT,check=True)
        for key in ['model','query']:
            blob=subprocess.check_output(['git','show',r['source_commit']+':'+r[key+'_path']],cwd=ROOT)
            require(digest(blob)==r[key+'_hash'],'Input not in execution commit')
        for name,h in r['artifacts'].items():
            require(digest((ROOT/name).read_bytes())==h,'Raw artifact drift: '+name)
        directory=path.parent
        stdout=(directory/'stdout.txt').read_text(errors='replace') if (directory/'stdout.txt').exists() else ''
        stderr=(directory/'stderr.txt').read_text(errors='replace') if (directory/'stderr.txt').exists() else ''
        parsed=parse_verdict(r['exit_code'],stdout,stderr)
        if not r.get('cleanup_confirmed'):gaps.append('Missing confirmed cleanup for '+slot['run_id'])
        require(r['status']!='success' or parsed is not None,'Success without an explicit machine verdict')
        require(r['verdict']==(parsed if r['status']=='success' else None),'Verdict/status mismatch')
        require(slot['status']==r['status'] and slot['verdict']==r['verdict'],'Ledger/result mismatch')
        if prior_end is not None:require(r['monotonic_start']>=prior_end,'Overlapping attempts')
        prior_end=r['monotonic_end'];total+=r['wall_seconds']
        if r['wall_seconds']>planned['cap_seconds']:overruns.append(slot['slot'])
    if total>1500:overruns.append('aggregate')
    if session['whole_native_wall_seconds']>1800:overruns.append('whole_session')
    require(abs(total-session['total_search_wall_seconds'])<0.01 or bool(gaps),'Wall aggregate mismatch')
    return dict(native_execution=session['status'],attempts=attempts,search_wall_seconds=total,budget_compliant=not overruns,
                budget_overruns=overruns,coverage_gaps=gaps,verdicts=[x['verdict'] for x in ledger])

def audit_check_logs():
    path=HERE/'checks/check-results.json'
    if not path.exists():return {'status':'not_yet_recorded'}
    summary=json.loads(path.read_text());count=0
    for record in summary['commands']:
        for log in record['logs']:
            require(digest((ROOT/log['path']).read_bytes())==log['sha256'],'Check log drift: '+log['path'])
            count+=1
    return dict(log_hashes=count,recorded_failures=summary['failed'])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path)
    a=ap.parse_args();result=dict(preparation=audit_preparation(),execution=audit_execution(),checks=audit_check_logs())
    out=json.dumps(result,indent=2)+'\n'
    if a.output:
        with a.output.open('x') as f:f.write(out)
    print(out,end='')

if __name__=='__main__':main()
