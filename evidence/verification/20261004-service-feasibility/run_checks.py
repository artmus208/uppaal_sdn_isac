"""Record software/static checks in a new directory; no native engine calls."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCOPE = HERE.relative_to(ROOT).as_posix()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    if not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id):
        raise ValueError('run-id must use lowercase alphanumerics and hyphens')
    out = HERE/'checks'/args.run_id
    out.mkdir(parents=True,exist_ok=False)
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
    commands = [
        ('premises',[sys.executable,'-B',SCOPE+'/check.py','--check']),
        ('scoped-tests',[sys.executable,'-B',SCOPE+'/tests.py']),
        ('causal-proof',[sys.executable,'-B','evidence/verification/20261004-completion-safety-proof/check.py','--check']),
        ('coordination',[sys.executable,'-B','scripts/check_coordination.py']),
        ('baseline-hashes',[sys.executable,'-B','scripts/check_coordination.py','--audit-hashes','--commit','HEAD',
                           '--output',(out/'baseline-hashes.json').relative_to(ROOT).as_posix()]),
        ('pip-check',[sys.executable,'-m','pip','check']),
        ('mcp-smoke',[sys.executable,'-B','-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
        ('cli-smoke',[sys.executable,'-B','-m','uppaal_mcp.cli','list-examples']),
        ('full-suite',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v']),
    ]
    versions = {}
    for name in ['mcp','PyYAML','uppaal-mcp']:
        try:
            versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name]='not_installed'
    record = {'run_id':args.run_id,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'python':platform.python_version(),'os':platform.system(), 'architecture':platform.machine(),
              'packages':versions,'evidence_kind':'software_tests_and_static_validation',
              'native_execution':False,'model_checking_verdict':None,
              'log_policy':'stdout/stderr UTF-8 copies redact workspace/user/temp/runtime paths; no hostname recorded',
              'commands':[]}
    replacements = [(str(ROOT),'<workspace>'),(str(ROOT).replace('\\','/'),'<workspace>')]
    for key in ['USERPROFILE','TEMP','TMP']:
        if os.environ.get(key):
            replacements.append((os.environ[key],'<'+key.lower()+'>'))
    replacements.append((sys.base_prefix,'<python-runtime>'))
    def redact(data):
        text=data.decode('utf-8',errors='replace')
        for path, token in sorted(replacements,key=lambda pair:-len(pair[0])):
            text=text.replace(path,token).replace(path.replace('\\','/'),token)
        return text.encode('utf-8')
    for name, command in commands:
        started=time.monotonic()
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True)
        logs={}
        for stream,data in [('stdout',p.stdout),('stderr',p.stderr)]:
            data=redact(data)
            path=out/(name+'.'+stream+'.txt')
            path.write_bytes(data)
            logs[stream]={'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest()}
        display=['<python>']+command[1:]
        record['commands'].append({'name':name,'command':display,'exit_code':p.returncode,
                                   'runtime_seconds':round(time.monotonic()-started,6),'logs':logs})
        (out/'record.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
        print(name,p.returncode,flush=True)
    return 1 if any(c['exit_code'] for c in record['commands']) else 0


if __name__=='__main__':
    raise SystemExit(main())
