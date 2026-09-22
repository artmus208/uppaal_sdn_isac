"""Run immutable #43 diagnostics from a clean source commit; no P3/Gate claims."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(HERE))
import diagnostics
from uppaal_mcp.integrated.generator import generate

spec = importlib.util.spec_from_file_location('ack_runner',ROOT/'evidence/instantiation/20260916-ack-observer/check.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.ROOT = ROOT
sha = lambda b: hashlib.sha256(b).hexdigest()


def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id',required=True)
    p.add_argument('--verifyta',required=True)
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):
        p.error('simple unused run-id required')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):
        raise SystemExit('Commit changes first; clean source tree required.')
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    out = HERE/'runs'/args.run_id
    out.mkdir(parents=True,exist_ok=False)
    env = {k:v for k,v in os.environ.items() if not k.startswith('UPPAAL_')}
    env['PYTHONDONTWRITEBYTECODE']='1'
    commands=[]
    results=[]
    def execute(name,cmd,expected=None,limit=60):
        stdout,record=runner.run_command(out,name,cmd,expected,limit,env)
        commands.append(record)
        dump(out/'commands.json',commands)
        print(name,record['status'],record['verdicts'],flush=True)
        return stdout,record
    version,vr=execute('version',[args.verifyta,'--version'])
    version=version.decode(errors='replace')
    c=generate(ROOT)
    metadata=dict(c.metadata)
    metadata.pop('adaptations',None)
    dump(out/'composition.json',metadata)
    paths=lambda x: runner.winpath(x) if args.verifyta.lower().endswith('.exe') else str(x)
    cases=[('integrated-parser',c.model_xml.encode(),[('E<> true',True)],
            'Full model engine load only; no full-model capacity result')]
    cases.extend(diagnostics.cases(c.model_xml))
    for name,xml,queries,scope in cases:
        model=out/(name+'.xml'); query=out/(name+'.q')
        model.write_bytes(xml)
        qb=('\n'.join(q for q,_ in queries)+'\n').encode()
        query.write_bytes(qb)
        expected=['satisfied' if v else 'NOT satisfied' for _,v in queries]
        _,record=execute(name,[args.verifyta,'-q','-t','1','-f',paths(out/(name+'-trace')),paths(model),paths(query)],expected)
        record.update(run_id=args.run_id+'-'+name,source_commit=commit,
                      model_hash=sha(xml),query_hash=sha(qb),tool_version=version,
                      model_path=model.name,query_path=query.name,scope=scope,
                      per_query=[{'query':q,'expected':e,'actual':record['verdicts'][i] if i<len(record['verdicts']) else None}
                                 for i,((q,_),e) in enumerate(zip(queries,expected))],
                      peak_memory='not_available',states_explored='not_available')
        if vr['status']!='success' or not version.strip():
            record['status']='error'
        results.append(record)
        dump(out/'results-index.json',results)
        dump(out/'commands.json',commands)
    execute('software',[sys.executable,'-m','unittest','discover','-s','tests','-v'],limit=150)
    execute('coordination',[sys.executable,'scripts/check_coordination.py'])
    execute('mcp',[sys.executable,'-c','from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'])
    execute('examples',[str(Path(sys.executable).parent/'uppaal-verifyta'),'list-examples'])
    execute('pip',[sys.executable,'-m','pip','check'])
    execute('diff',['git','diff','--check','79f59d8b9d59375371bae6f5521e7d2619fcb2a0',commit])
    cpu=next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),'not_available')
    record={'run_id':args.run_id,'source_commit':commit,'source_tree_clean_at_start':True,
            'base_commit':'79f59d8b9d59375371bae6f5521e7d2619fcb2a0','produced_by':'vadimnbkg',
            'tool_version':version,'operating_environment':platform.platform(),'python':sys.version,
            'hardware':{'cpu_model':cpu,'logical_cpu_count':os.cpu_count(),
                        'ram_bytes':os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES'),
                        'scope':'WSL host; Windows verifyta via interop'},
            'parameter_set':c.metadata['parameter_set'],'instance_vector':c.metadata['instance_vector'],
            'generator_hash':c.metadata['generator_hash'],'model_hash':c.metadata['model_hash'],
            'query_hash':c.metadata['query_hash'],'source_hashes':c.metadata['source_hashes'],
            'limits':{'per_verifier_seconds':60,'software_seconds':150,'memory':'no explicit cap'},
            'runner_exit_code':runner.run_exit_code(commands),
            'claim_limits':'Restricted MAC-load diagnostics and deliberate mutant only. Full model uses E<> true only; no C01/Gate 1/P3 acceptance.'}
    dump(out/'run.json',record)
    (out/'SHA256SUMS').write_text(''.join(f'{sha(f.read_bytes())}  {f.name}\n' for f in sorted(out.iterdir()) if f.is_file()))
    return record['runner_exit_code']


if __name__=='__main__':
    raise SystemExit(main())
