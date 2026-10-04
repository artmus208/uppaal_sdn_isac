"""Runner-only six-slot native Windows campaign, disabled without a concrete Issue decision."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time

from guard import Guard
import windows_native as win
from prepare import HERE, ROOT, M_PATH, M_HASH, SCOPE, BASE, derive, digest, encoded

EXEC=HERE/'execution'

def runner_branch(approval):
    """Use declared accounts; authorization comes from the recorded decision."""
    for field in ('approver','runner'):
        account=approval.get(field)
        if not isinstance(account,str) or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',account):
            raise ValueError('Explicit GitHub account required: '+field)
    return 'codex/'+approval['runner']+'/89-uav-bounded-response-runs'

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(path,data):
    """Atomic, fsynced data; watchdog does not read this file."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp')
    with open(temp,'xb') as f:
        f.write(encoded(data));f.flush();os.fsync(f.fileno())
    if os.name=='nt':
        win.checked(win.move(str(temp),str(path),0x1|0x8)) # REPLACE_EXISTING | WRITE_THROUGH
    else:
        os.replace(temp,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

def git(*args,timeout=30):
    # Porcelain status uses leading spaces as fixed-width status columns.
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,timeout=timeout).rstrip('\r\n')

def file_index(directory):
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(Path(directory).rglob('*'))
            if p.is_file() and p.name!='result.json'}

def checkpoint(label,branch):
    # Do not commit anything outside the sequentially delegated execution scope.
    if git('branch','--show-current')!=branch:raise ValueError('Use the declared Runner branch')
    paths=git('status','--porcelain','--untracked-files=all').splitlines()
    if any(not x[3:].startswith(SCOPE+'/execution/') for x in paths):
        raise RuntimeError('Dirty paths outside Runner execution scope')
    git('add','--',SCOPE+'/execution')
    git('commit','-m','P3: '+label+' (#89)')
    head=git('rev-parse','HEAD')
    # Mandatory pre-export evidence checks from AGENTS.md, retained in console.
    for args in [('status','--short','--branch'),('log','-1','--oneline','--decorate'),('remote','-v')]:
        print(git(*args),flush=True)
    recovery=EXEC/'recovery';recovery.mkdir(exist_ok=True)
    bundle=recovery/(head+'.bundle')
    git('bundle','create',str(bundle),branch,timeout=60)
    git('bundle','verify',str(bundle),timeout=30)
    return head

def parse_verdict(returncode,stdout,stderr):
    """Fail closed: one indexed formula, exactly one verdict, no fatal diagnostics."""
    text=stdout+'\n'+stderr
    if returncode!=0 or re.search(r'(?im)(?:^|\n)\s*(?:error|fatal|exception)|syntax error|license.*(?:fail|error|invalid)|out of memory',text):
        return None
    headers=re.findall(r'Verifying formula\s+(\d+)\s+at line',text,re.I)
    verdicts=re.findall(r'Formula is (NOT satisfied|satisfied)\.',text)
    if headers!=['1'] or len(verdicts)!=1:
        return None
    return verdicts[0]=='satisfied'

def verify_native_inputs(a,cfg,root):
    host=win.identity()
    for field in ['os','native_host','machine_guid_sha256','python_path','python_sha256','python_version']:
        if a.get(field)!=host[field]:raise ValueError('Native Windows identity mismatch: '+field)
    if Path(a['persistent_checkout']).resolve()!=root or str(root).startswith('//') or root.anchor.startswith('\\\\') or root.drive=='' or 'temp' in [x.casefold() for x in root.parts]:
        raise ValueError('Runner requires a declared persistent Windows drive checkout, not WSL/UNC/temp')
    tool=Path(a['verifyta_path']).resolve(strict=True)
    if str(tool).casefold()!=cfg['verifyta_path'].casefold():raise ValueError('Verifier path differs from Windows preparation')
    actual=win.pe_info(tool)
    if actual['sha256']!=a['executable_sha256'] or actual['sha256']!=cfg['executable_sha256']:
        raise ValueError('Executable hash mismatch')
    return tool

def verify_approval(a):
    inv=json.loads((HERE/'query-inventory.json').read_text(encoding='utf-8'))
    prospective=json.loads((HERE/'hnom/prospective-model.json').read_text(encoding='utf-8'))
    if a.get('native_execution_authorized') is not True or a.get('hnom_restrictions_and_materialization_approved') is not True:
        raise ValueError('Separate domain/materialization and native execution approval required')
    runner_branch(a)
    if not re.fullmatch(r'https://github.com/artmus208/uppaal_sdn_isac/issues/89#issuecomment-\d+',a.get('decision_url','')):
        raise ValueError('Exact Issue #89 decision URL required')
    prep=a['preparation_head']
    if not re.fullmatch('[0-9a-f]{40}',prep): raise ValueError('Exact preparation commit required')
    git('merge-base','--is-ancestor',prep,'HEAD')
    if git('show',prep+':'+SCOPE+'/seal.json') != (HERE/'seal.json').read_text(encoding='utf-8').strip():
        raise ValueError('Preparation seal differs from decision checkpoint')
    if a['hnom_hash']!=prospective['model_hash'] or a['hnom_patch_hash']!=prospective['patch_sha256']:
        raise ValueError('Approved Hnom hash/diff mismatch')
    if a['query_hashes']!=[x['query_hash'] for x in inv]:raise ValueError('Query approval mismatch')
    cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    if a['config_hash']!=digest((HERE/'config.json').read_bytes()):raise ValueError('Configuration approval mismatch')
    tool=verify_native_inputs(a,cfg,ROOT)
    if a['expected_version_identity']!='UPPAAL 5.0.0 rev. 714BA9DB36F49691':
        raise ValueError('Version change requires separate protocol revision')
    return inv,cfg,tool

def run(a):
    from audit import audit_preparation
    audit_preparation()
    branch=runner_branch(a)
    if git('branch','--show-current')!=branch:raise ValueError('Use the declared Runner branch')
    if git('status','--porcelain'):raise ValueError('Commit approval and offline inputs before starting')
    if git('remote','get-url','origin')!='https://github.com/artmus208/uppaal_sdn_isac.git':
        raise ValueError('Noncanonical remote')
    if (EXEC/'session.json').exists():raise ValueError('Session already used: no retry/resume')
    inv,cfg,tool=verify_approval(a)
    if win.existing_verifiers():raise RuntimeError('Existing native Windows verifier; do not overlap or kill it')
    host=win.identity();ram=host['physical_ram_bytes']
    mem=int(min(ram//2,8*1024**3)//1024**2)*1024**2
    model,changes=derive((ROOT/M_PATH).read_bytes())
    if (EXEC/'model.xml').read_bytes()!=model:raise ValueError('Approved materialized model mismatch')
    # Session is spent even if preflight fails. No implicit retries on re-entry.
    ledger=json.loads((HERE/'query-ledger.json').read_text(encoding='utf-8'))
    # An exclusive, never-deleted session claim blocks concurrent invocation.
    with open(EXEC/'session-claimed.json','x') as f:
        json.dump({'pid':os.getpid(),'claimed_at_utc':utc()},f);f.flush();os.fsync(f.fileno())
    session=dict(started_at_utc=utc(),monotonic_start=time.monotonic(),status='preflight',runner=a['runner'],
                 approver=a['approver'],runner_branch=branch,
                 preparation_head=a['preparation_head'],execution_initial_commit=git('rev-parse','HEAD'),
                 operational_base=BASE,scientific_input_commit='61386aa358805082b705dcd00c8cbfde5fb98248',
                 approval=a,physical_ram_bytes=ram,memory_limit_bytes=mem,
                 platform=platform.platform(),python=sys.version,host=platform.node(),
                 logical_cpu_count=os.cpu_count(),native_identity=host,processor=host['processor'],
                 executable=str(tool),executable_sha256=digest(tool.read_bytes()),tool_version=None,
                 total_search_wall_seconds=0.0,whole_session_cap_seconds=1800)
    save(EXEC/'session.json',session);save(EXEC/'ledger.json',ledger)
    guard=None;reason=None
    def stop_signal(*_):raise KeyboardInterrupt('Runner stop signal')
    signal.signal(signal.SIGTERM,stop_signal)
    try:
        # Independent process owns native children from the first preflight onward.
        guard=Guard(cfg['whole_session_seconds'])
        session['native_monotonic_start']=guard.deadline-cfg['whole_session_seconds']
        preflight={}
        for name,flag in [('version','-v'),('help','-h')]:
            directory=EXEC/'preflight'/name
            r=guard.run([tool,flag],directory,30,mem,cwd=tool.parent)
            save(directory/'result.json',r)
            if r['status']!='exited' or r['exit_code']!=0:raise RuntimeError(name+' preflight failed')
            preflight[name]=(directory/'stdout.txt').read_text(encoding='utf-8',errors='replace')+'\n'+(directory/'stderr.txt').read_text(encoding='utf-8',errors='replace')
        actual=preflight['version'].strip()
        session['tool_version']=actual
        save(EXEC/'session.json',session)
        if not re.search(r'UPPAAL.*5\.0\.0.*714BA9DB36F49691',actual,re.S):
            raise RuntimeError('Actual version differs from approved historical identity')
        helptext=preflight['help']
        # Compare exact approved options to their actual help descriptions.
        for pattern in cfg['help_required_patterns']:
            if not re.search(pattern,helptext,re.I|re.S):raise RuntimeError('Actual help does not confirm '+pattern)
        session['status']='running';save(EXEC/'session.json',session)
        checkpoint('retain actual native preflight',branch)
        for item in inv:
            slot=ledger[item['slot']-1]
            remaining=guard.deadline-time.monotonic()
            if remaining < item['cap_seconds']+cfg['minimum_slot_overhead_seconds']:
                reason='Insufficient whole-session budget for next full reserved slot';break
            if digest(tool.read_bytes())!=a['executable_sha256']:raise RuntimeError('Executable changed')
            if digest((ROOT/item['model_path']).read_bytes())!=item['model_hash']:raise RuntimeError('Model changed')
            if digest((ROOT/item['query_path']).read_bytes())!=item['query_hash']:raise RuntimeError('Query changed')
            slot.update(state='reserved',attempt_consumed=True,reserved_at_utc=utc())
            save(EXEC/'ledger.json',ledger)
            source=checkpoint('reserve slot '+str(item['slot']),branch)
            if git('status','--porcelain'):raise RuntimeError('Dirty execution source')
            directory=EXEC/'runs'/slot['run_id'];directory.mkdir(parents=True)
            command=[str(tool),*cfg['flags'],str(directory/'trace'),str(ROOT/item['model_path']),str(ROOT/item['query_path'])]
            record=dict(**item,run_id=slot['run_id'],source_commit=source,execution_source_commit=source,
                        preparation_head=a['preparation_head'],status='interrupted',verdict=None,
                        tool_version=actual,executable_sha256=a['executable_sha256'],command=command,
                        environment_reference=(EXEC/'session.json').relative_to(ROOT).as_posix(),
                        input_pins_reference=SCOPE+'/input-pins.json',started_at_utc=utc(),
                        states_explored=None,states_reason='Not parsed; raw stdout retained',
                        trace_classification=None,trace_interpretation='Pending Owner offline inspection')
            pins=json.loads((HERE/'input-pins.json').read_text(encoding='utf-8'))
            record.update(parameter_set=pins['parameters'],instance_vector=pins['instance_vector'],
                          scientific_input_commit=pins['scientific_input_commit'],operational_base=BASE,
                          os=session['platform'],python=session['python'],hardware_host=session['host'],
                          physical_ram_bytes=ram,memory_limit_bytes=mem)
            save(directory/'reservation.json',record)
            attempt_started=time.monotonic()
            try:
                r=guard.run(command,directory,item['cap_seconds'],mem,cwd=tool.parent)
            except BaseException as exc:
                now=time.monotonic()
                r=dict(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'error',
                       reason=repr(exc),exit_code=None,monotonic_start=attempt_started,monotonic_end=now,
                       wall_seconds=now-attempt_started,cpu_seconds=None,peak_rss_bytes=None,
                       metric_scope='Controller elapsed fallback; watchdog result unavailable',cleanup_confirmed=None)
            stdout=(directory/'stdout.txt').read_text(encoding='utf-8',errors='replace') if (directory/'stdout.txt').exists() else ''
            stderr=(directory/'stderr.txt').read_text(encoding='utf-8',errors='replace') if (directory/'stderr.txt').exists() else ''
            verdict=parse_verdict(r['exit_code'],stdout,stderr) if r['status']=='exited' else None
            status=('success' if verdict is not None else 'error') if r['status']=='exited' else r['status']
            record.update(r,status=status,verdict=verdict,finished_at_utc=utc(),artifacts=file_index(directory))
            save(directory/'result.json',record)
            slot.update(state='finished',status=status,verdict=verdict,result_path=(directory/'result.json').relative_to(ROOT).as_posix())
            session['total_search_wall_seconds']+=r['wall_seconds']
            save(EXEC/'ledger.json',ledger);save(EXEC/'session.json',session)
            checkpoint('retain slot '+str(item['slot'])+' evidence',branch)
            if status not in ['success','timeout','memory_limit']:
                reason='Series stopped on '+status;break
            if r['wall_seconds']>item['cap_seconds'] or session['total_search_wall_seconds']>1500:
                reason='Measured budget overrun; no further attempt';break
    except BaseException as exc:
        reason=repr(exc)
    finally:
        if guard is not None:
            try:guard.close()
            except BaseException as exc:reason=(reason or '')+'; watchdog cleanup: '+repr(exc)
        ended=time.monotonic()
        for slot in ledger:
            if slot['state']=='reserved':slot.update(state='finished',status='interrupted',verdict=None,reason=reason)
            elif slot['state']=='planned':slot.update(state='not_executed',status='not_executed',verdict=None,reason=reason or 'Not reached')
        session.update(status='stopped' if reason else 'finished',reason=reason,finished_at_utc=utc(),
                       monotonic_end=ended,whole_native_wall_seconds=ended-session.get('native_monotonic_start',session['monotonic_start']))
        session['whole_session_overrun']=session['whole_native_wall_seconds']>1800
        save(EXEC/'ledger.json',ledger);save(EXEC/'session.json',session)
        checkpoint('retain final native session disposition',branch)
    return 1 if reason else 0

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['materialize','run'])
    ap.add_argument('--approval',type=Path,required=True)
    args=ap.parse_args()
    a=json.loads(args.approval.read_text(encoding='utf-8'))
    if args.approval.resolve()!=EXEC/'approval.json':raise ValueError('Approval must be committed inside execution scope')
    if args.action=='materialize':
        # Same concrete approval is required; this operation never invokes verifier.
        verify_approval(a)
        model,_=derive((ROOT/M_PATH).read_bytes())
        with open(EXEC/'model.xml','xb') as f:f.write(model)
        print('Approved Hnom materialized; commit it before native execution.')
        return 0
    return run(a)

if __name__=='__main__':
    sys.exit(main())
