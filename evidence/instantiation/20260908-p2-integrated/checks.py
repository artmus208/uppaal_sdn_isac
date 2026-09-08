"""Record isolated software checks and compile-only diagnostics, never model checking."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--python',type=Path,required=True)
    parser.add_argument('--verifyta',type=Path)
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    output=args.output.resolve()
    # Resolving a venv executable symlink selects the base interpreter instead.
    python=str(args.python.absolute())
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONUTF8']='1'
    env.pop('PYTHONPATH',None)
    index=int(env.get('GIT_CONFIG_COUNT','0'))
    env[f'GIT_CONFIG_KEY_{index}']='core.autocrlf'
    env[f'GIT_CONFIG_VALUE_{index}']='false'
    env['GIT_CONFIG_COUNT']=str(index+1)
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    if status:
        raise RuntimeError('Commit implementation and recorder before recording final evidence: '+status)
    output.mkdir(parents=True,exist_ok=False)
    report={'run_id':output.name,'issue':19,'evidence_class':'software_and_compile_only_diagnostics',
            'verification_status':'not_run','cwd':str(ROOT),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'worktree_status_at_start':status,'operating_environment':platform.platform(),
            'python':python,'hardware':{'cpu':platform.processor(),'logical_cpu_count':os.cpu_count()},
            'environment_overrides':{'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1','core.autocrlf':'false'},
            'git_override_reason':'Exact-byte audit fixture isolation; process-only, no Git config changed.',
            'commands':[]}
    if os.name=='nt':
        hardware=subprocess.run(['powershell','-NoProfile','-Command',
            '$c=Get-CimInstance Win32_Processor; $m=Get-CimInstance Win32_ComputerSystem; [pscustomobject]@{cpu_model=($c.Name -join ", "); ram_bytes=$m.TotalPhysicalMemory} | ConvertTo-Json -Compress'],capture_output=True,timeout=20)
        try:report['hardware'].update(json.loads(hardware.stdout))
        except (ValueError,UnicodeError):report['hardware']['ram_bytes']='not_available'
    else:
        try:report['hardware']['ram_bytes']=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')
        except (ValueError,OSError,AttributeError):report['hardware']['ram_bytes']='not_available'
    commands=[]
    if args.install:
        commands.append(('install',[python,'-m','pip','install','-e','.','PyYAML'],{}))
    cli=str(Path(python).parent/('uppaal-verifyta.exe' if os.name=='nt' else 'uppaal-verifyta'))
    commands.extend([
        ('pip-check',[python,'-m','pip','check'],{}),
        ('versions',[python,'-c','import sys,importlib.metadata as m; print(sys.version); print("mcp="+m.version("mcp")); print("PyYAML="+m.version("PyYAML"))'],{}),
        ('generate',[python,'-B','-m','uppaal_mcp.integrated.generator','--output',str(output/'generated')],{}),
        ('coordination',[python,'-B','scripts/check_coordination.py'],{}),
        ('yaml',[python,'-c','import pathlib,yaml; files=sorted(pathlib.Path("manifests").rglob("*.yaml")); [yaml.safe_load(p.read_text(encoding="utf-8")) for p in files]; print(len(files),"YAML manifests parsed")'],{}),
        ('unit-tests',[python,'-B','-m','unittest','discover','-s','tests','-v'],{}),
        ('mcp-construction',[python,'-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'],{}),
        ('examples',[cli,'list-examples'],{}),
        ('diff-check',['git','diff','--check','dc7eeb05f1fd3f2a4775428b1cd250363893128d...HEAD'],{}),
    ])
    if args.verifyta:
        executable=str(args.verifyta.resolve())
        commands.extend([
            ('verifyta-version',[executable,'--version'],{}),
            ('verifyta-help',[executable,'--help'],{}),
            ('compile-only',[executable,str(output/'generated/model.xml'),str(output/'generated/queries.q')],{'UPPAAL_COMPILE_ONLY':'1'}),
        ])
    else:report['compile_only_status']='not_available: no executable supplied'
    for name,command,overrides in commands:
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        tick=time.monotonic()
        timeout=False
        try:
            p=subprocess.run(command,cwd=ROOT,env=dict(env,**overrides),capture_output=True,timeout=300 if name!='compile-only' else 60)
            code,stdout,stderr=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired as exc:
            code,stdout,stderr,timeout=None,exc.stdout or b'',exc.stderr or b'',True
        except OSError as exc:
            code,stdout,stderr=None,b'',str(exc).encode()
        record={'name':name,'command':command,'environment_overrides':overrides,'started_at_utc':started,
                'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'runtime_seconds':time.monotonic()-tick,'exit_code':code,'timeout':timeout,
                'status':'success' if code==0 else ('timeout' if timeout else 'error')}
        for stream,data in [('stdout',stdout),('stderr',stderr)]:
            path=output/f'{name}.{stream}.log';path.write_bytes(data)
            record[stream+'_path']=path.name;record[stream+'_sha256']=sha(data)
        report['commands'].append(record)
        if name=='verifyta-version':report['tool_version_output']=stdout.decode('utf-8',errors='replace')
        if name=='compile-only':report['compile_only_status']=record['status']
        generated=output/'generated/composition.json'
        if generated.exists():
            composition=json.loads(generated.read_bytes())
            report.update({key:composition[key] for key in ['model_hash','query_hash','generator_hash','parameter_set','instance_vector']})
        (output/'checks.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
        print(f'{name}: exit={code}; timeout={timeout}',flush=True)
    return int(any(r['exit_code']!=0 for r in report['commands']))


if __name__=='__main__':
    raise SystemExit(main())
