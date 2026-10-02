"""Lossless raw/source archives and artifact inventory; no engine invocation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(data):return hashlib.sha256(data).hexdigest()


def dump(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def archive(path,entries):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data,compresslevel=9)


def pack():
    if (HERE/'raw-traces.zip').exists() or (HERE/'source-snapshots.zip').exists():
        raise FileExistsError('Immutable archives already exist; use audit.py to inspect them')
    sources={};source_index={}
    for path in sorted((HERE/'runs').glob('*/provenance.json')):
        provenance=json.loads(path.read_text());commit=provenance['source_commit']
        files=[]
        for name,expected in sorted(provenance['hashes'].items()):
            try:relative=Path(name).relative_to(ROOT)
            except ValueError:continue
            data=subprocess.check_output(['git','show',f'{commit}:{relative.as_posix()}'],cwd=ROOT)
            assert sha(data)==expected,(commit,name)
            entry='objects/'+expected;sources[entry]=data
            files.append({'path':relative.as_posix(),'hash':expected,'entry':entry})
        commit_data=subprocess.check_output(['git','cat-file','commit',commit],cwd=ROOT)
        entry='commits/'+commit;sources[entry]=commit_data
        source_index[path.parent.name]={'commit':commit,'commit_object':entry,'files':files,
             'source_hash':sha(json.dumps({f['path']:f['hash'] for f in files},sort_keys=True).encode())}
    archive(HERE/'source-snapshots.zip',sources);dump(HERE/'source-index.json',source_index)
    raw={};index={}
    for p in sorted((HERE/'runs').glob('*/*')):
        if p.suffix in ['.xtr','.jsonl'] or p.name in ['model.xml','stdout.txt']:
            rel=p.relative_to(HERE).as_posix();data=p.read_bytes();raw[rel]=data
            index[rel]={'sha256':sha(data),'bytes':len(data),'entry':rel}
    archive(HERE/'raw-traces.zip',raw);dump(HERE/'raw-index.json',index)
    for name in raw:(HERE/name).unlink()  # our new run files, preserved byte-for-byte in archive
    print('Archived',len(raw),'raw files and',len(sources),'source objects')


def seal():
    files={}
    for p in sorted(HERE.rglob('*')):
        rel=p.relative_to(HERE)
        if not p.is_file() or '.venv' in rel.parts or '__pycache__' in rel.parts:continue
        if p.name=='artifacts-sha256.json' or p.suffix=='.bundle':continue
        files[rel.as_posix()]=sha(p.read_bytes())
    dump(HERE/'artifacts-sha256.json',files);print('Sealed',len(files),'artifact hashes')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pack',action='store_true');parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    if args.pack:pack()
    if args.seal:seal()
