"""Save reproducible software/static commands and logs; never invoke verifyta."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import HERE, ROOT, SCOPE, digest, encoded

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);args=ap.parse_args()
    out=HERE/'checks'/args.run_id;out.mkdir()
    commands=[
      ('proposal',[sys.executable,'-B',SCOPE+'/prepare.py','--check']),
      ('portable-software-controls',[sys.executable,'-B','-m','unittest','discover','-s',SCOPE,'-p','test_protocol.py','-v']),
      ('coordination',[sys.executable,'-B','scripts/check_coordination.py']),
      ('historical-hashes',[sys.executable,'-B','scripts/check_coordination.py','--audit-hashes','--commit','HEAD','--output',str(out/'historical-hashes.json')]),
      ('candidate-generation',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/generate.py','--check']),
      ('candidate-audit',[sys.executable,'-B','evidence/instantiation/uav-service-completion-candidate/audit.py']),
      ('baseline-operational',[sys.executable,'-B','evidence/governance/uav-service-completion-baseline-20261002/check.py','--operational']),
      ('full-suite',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v']),
      ('mcp-smoke',[sys.executable,'-B','-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
      ('cli-examples',[sys.executable,'-B','-m','uppaal_mcp.cli','list-examples']),
      ('pip-check',[sys.executable,'-m','pip','check']),
      ('offline-audit',[sys.executable,'-B',SCOPE+'/audit.py','--output',str(out/'offline-audit.json')]),
      ('diff-check',['git','diff','--check']),
    ]
    records=[]
    for name,command in commands:
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        result=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=180)
        paths=[]
        for kind,data in [('stdout',result.stdout),('stderr',result.stderr)]:
            path=out/(name+'.'+kind+'.txt');path.write_bytes(data)
            paths.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(data)))
        records.append(dict(name=name,command=command,started_at_utc=started,exit_code=result.returncode,logs=paths))
        print(name,result.returncode,flush=True)
        (out/'commands.json').write_bytes(encoded(records))
    summary=dict(kind='software/static only, not verification',run_id=args.run_id,
                 source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 commands=records,failed=[r['name'] for r in records if r['exit_code']],
                 skipped=['UPPAAL version/help and all queries: this command records software/static checks only'])
    (HERE/'checks/check-results.json').write_bytes(encoded(summary))
    return bool(summary['failed'])

if __name__=='__main__':sys.exit(main())
