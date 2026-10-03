"""Native Windows software evidence with raw unittest log; never executes verifyta."""
import argparse
import datetime
import json
from pathlib import Path
import sys
import unittest
from prepare import HERE,digest,encoded
import windows_native as win

def main():
    win.native()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--source-commit',required=True,help='Exact git rev-parse HEAD, independently bound by source file hashes')
    args=ap.parse_args()
    args.output.mkdir(parents=True)
    sources={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))}
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    host=win.identity()
    cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    pe=win.pe_info(cfg['verifyta_path']) # Read bytes only; not even -v/-h is executed.
    if pe['sha256']!=cfg['executable_sha256']:raise ValueError('Pinned PE hash mismatch')
    log=args.output/'unittest.txt'
    with log.open('x',encoding='utf-8',newline='\n') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(HERE),'test_*.py'))
    after={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))}
    record=dict(kind='native Windows synthetic/software tests; zero verifier execution',source_commit=args.source_commit,
                source_files=sources,source_unchanged=sources==after,command=[sys.executable,*sys.argv],
                started_at_utc=started,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                host=host,verifyta_read_only_pe=dict(path=cfg['verifyta_path'],**pe),
                tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=result.skipped,
                successful=result.wasSuccessful() and not result.skipped and sources==after,
                logs=[dict(path='unittest.txt',sha256=digest(log.read_bytes()))])
    (args.output/'record.json').write_bytes(encoded(record))
    print(json.dumps({k:record[k] for k in ['tests_run','failures','errors','skipped','successful']}))
    return 0 if record['successful'] else 1

if __name__=='__main__':sys.exit(main())
