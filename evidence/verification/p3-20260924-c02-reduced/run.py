"""Four bounded native checks, with immutable run directories and raw provenance."""
import argparse, hashlib, json, platform, re, subprocess
from pathlib import Path
import build
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PS = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, v): p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
def win(p): return subprocess.check_output(['wslpath', '-w', str(p)], text=True).strip()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run-id', required=True); ap.add_argument('--verifyta', required=True); a = ap.parse_args()
    assert re.fullmatch(r'p3-20260924-c02-reduced-[A-Za-z0-9_-]+', a.run_id)
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT), 'Clean tree required'
    for name, data in build.generate().items(): assert (HERE / name).read_bytes() == data
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    out = HERE / 'runs' / a.run_id; out.mkdir(parents=True, exist_ok=False)
    verify = Path(a.verifyta).resolve(strict=True)
    v = subprocess.run([str(verify), '--version'], cwd=verify.parent, capture_output=True, timeout=20)
    (out / 'version.stdout.txt').write_bytes(v.stdout); (out / 'version.stderr.txt').write_bytes(v.stderr)
    assert v.returncode == 0 and b'UPPAAL 5.0.0 (rev. 714BA9DB36F49691)' in v.stdout
    hw = subprocess.run([PS, '-NoProfile', '-Command', '[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false); $os=Get-CimInstance Win32_OperatingSystem; @{os=$os.Caption;version=$os.Version;ram_bytes=([long]$os.TotalVisibleMemorySize*1024);cpu=@(Get-CimInstance Win32_Processor|Select-Object Name,NumberOfCores,NumberOfLogicalProcessors)}|ConvertTo-Json -Depth 4'], capture_output=True, timeout=30)
    (out / 'hardware.stdout.json').write_bytes(hw.stdout); (out / 'hardware.stderr.txt').write_bytes(hw.stderr); assert hw.returncode == 0
    meta = {'run_id': a.run_id, 'source_commit': commit, 'source_tree_clean_at_start': True, 'issue': 39,
            'full_model_hash': build.SOURCE_SHA, 'generator_path': str((HERE/'build.py').relative_to(ROOT)), 'generator_hash': sha(HERE/'build.py'),
            'parameter_set': {'mac_D_phy_ack': 3}, 'instance_vector': {'C02Ack': 1}, 'tool_version': v.stdout.decode(),
            'operating_environment': platform.platform(), 'hardware': json.loads(hw.stdout.decode('utf-8-sig')),
            'scope': 'experimental abstraction only; full baseline timeout remains unchanged', 'status': 'running'}
    dump(out / 'run.json', meta)
    results = []
    for name, modelname, queryname, expected in [('C02','model.xml','C02.q','satisfied'), ('active','model.xml','active.q','satisfied'), ('deadline','model.xml','deadline.q','satisfied'), ('negative-control','negative-control.xml','C02.q','violated')]:
        model, query = HERE/modelname, HERE/queryname
        command = ['-o', '0', '-t', '0', '-X', win(out/(name+'-trace')), win(model), win(query)]
        config = {'executable': win(verify), 'arguments': command, 'stdout': win(out/(name+'.stdout.txt')), 'stderr': win(out/(name+'.stderr.txt')), 'result': win(out/(name+'.native.json')), 'timeout_seconds': 30, 'memory_stop_bytes': 2147483648}
        cfg = out/(name+'.config.json'); dump(cfg, config)
        wrapper = subprocess.run([PS, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', win(ROOT/'evidence/verification/p3-20260923/native-run.ps1'), '-Config', win(cfg)], capture_output=True, timeout=60)
        (out/(name+'.wrapper.stdout.txt')).write_bytes(wrapper.stdout); (out/(name+'.wrapper.stderr.txt')).write_bytes(wrapper.stderr)
        assert wrapper.returncode == 0
        record = json.loads((out/(name+'.native.json')).read_text(encoding='utf-8-sig'))
        stdout, stderr = (out/(name+'.stdout.txt')).read_text(), (out/(name+'.stderr.txt')).read_text()
        verdicts = re.findall(r'Formula is (NOT satisfied|satisfied|MAYBE satisfied)', stdout+'\n'+stderr)
        status, verdict = record['termination'], None
        if status == 'completed':
            status = 'success' if record['exit_code'] == 0 and len(verdicts) == 1 and not re.search(r'(?im)^(error|exception|fatal)\b', stdout+'\n'+stderr) else 'error'
            if status == 'success': verdict = {'satisfied':'satisfied','NOT satisfied':'violated','MAYBE satisfied':'inconclusive'}[verdicts[0]]
        record.update(run_id=a.run_id+'-'+name, status=status, verdict=verdict, expected_verdict=expected,
                      model_path=str(model.relative_to(ROOT)), model_hash=sha(model), query_hash=sha(query), query=query.read_text().strip(),
                      tool_version=meta['tool_version'], source_commit=commit, command=[config['executable'],*command],
                      stdout_reference=name+'.stdout.txt', stderr_reference=name+'.stderr.txt', trace_paths=[p.name for p in out.glob(name+'-trace*')], states_explored=None)
        results.append(record); dump(out/'results.json', results)
        print(name, status, verdict, record['runtime_seconds'], flush=True)
    meta['status'] = 'completed'; dump(out/'run.json', meta)
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
    assert all(r['status']=='success' and r['verdict']==r['expected_verdict'] for r in results), 'Unexpected result: inspect raw logs'
if __name__ == '__main__': main()
