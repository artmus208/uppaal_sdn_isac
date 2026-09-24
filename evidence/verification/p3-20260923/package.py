"""Package a completed run, preserving raw bytes and adding the run.yaml contract."""
import hashlib,json,sys,tarfile
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
out=Path(sys.argv[1]).resolve()
r=json.loads((out/'run.json').read_text());results=json.loads((out/'results.json').read_text())
assert r['status']=='completed' and len(results)==r['result_count']
contract=dict(r)
contract.update(uppaal_version=r['tool_version'].splitlines()[0],verifyta_version_output='version.stdout.txt',
    operating_system=r['native_hardware']['os'],execution_environment=r['operating_environment']+'; native Windows verifyta via PowerShell/WSL interop',
    cpu_model=r['native_hardware']['cpu'][0]['Name'].strip(),logical_cpu_count=sum(x['NumberOfLogicalProcessors'] for x in r['native_hardware']['cpu']),ram_bytes=r['native_hardware']['ram_bytes'],resource_limit=r['limits'],query_hash=r['frozen_query_set_hash'],license_status='native executions recorded; evaluate each result status',
    started_at_utc=results[0]['started_at_utc'],finished_at_utc=results[-1]['finished_at_utc'],
    runtime_seconds=sum(x['runtime_seconds'] for x in results),
    peak_memory_bytes=max(x['peak_working_set_bytes'] for x in results),
    limitations=['states_explored not reported as a total by this build; progress Load is not substituted', 'Memory stop uses 50ms polling, not a hard allocation limit', 'Results require independent review; C06 conclusion additionally depends on P4'])
contract['results']=[]
for x in results:
    y=dict(x)
    y.update(peak_memory_bytes=x['peak_working_set_bytes'],
       counterexample_reference=x['trace_paths'] if x['verdict']=='violated' else [],
       stdout_sha256=sha((out/x['stdout_path']).read_bytes()),stderr_sha256=sha((out/x['stderr_path']).read_bytes()))
    contract['results'].append(y)
(out/'run.yaml').write_text(yaml.safe_dump(contract,allow_unicode=True,sort_keys=False))
(out/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
archive=out.parent/(out.name+'.tar.xz')
assert not archive.exists()
with tarfile.open(archive,'w:xz') as t:t.add(out,arcname=out.name)
with tarfile.open(archive) as t:
 for p in out.iterdir():
  if p.is_file():assert t.extractfile(out.name+'/'+p.name).read()==p.read_bytes(),p.name
summary=HERE/out.name;summary.mkdir(exist_ok=False)
for name in ['run.json','results.json','run.yaml']:(summary/name).write_bytes((out/name).read_bytes())
(summary/'archive.json').write_text(json.dumps({'archive':archive.relative_to(ROOT).as_posix(),'sha256':sha(archive.read_bytes()),'files':len(list(out.iterdir()))},indent=2)+'\n')
print('Verified archive',archive,'bytes',archive.stat().st_size)
