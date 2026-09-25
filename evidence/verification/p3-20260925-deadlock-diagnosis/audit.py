"""Audit archived diagnostic controls without running UPPAAL."""
import hashlib, importlib.util, json, pathlib, tarfile, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('evidence_audit',ROOT/'evidence/verification/p3-20260923/audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
rows=json.loads((HERE/'comparison.json').read_text())
for n,(row,expected) in enumerate(zip(rows,[(2,0),(2,1),(1,0)]),1):
 rid=f'p3-20260925-deadlock-diag-{n:03d}'
 summary=ROOT/'evidence/verification/p3-20260923'/rid
 archive=json.loads((summary/'archive.json').read_text());path=ROOT/archive['archive']
 assert hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256']
 with tempfile.TemporaryDirectory() as tmp:
  with tarfile.open(path) as t:t.extractall(tmp,filter='data')
  raw=pathlib.Path(tmp)/rid;audit.audit(raw)
  for name in ['run.json','results.json','run.yaml']:assert (raw/name).read_bytes()==(summary/name).read_bytes()
  run=json.loads((raw/'run.json').read_text());result=json.loads((raw/'results.json').read_text())[0]
  assert row['result']==result
  assert (run['search_order'],run['state_representation'])==expected
  assert run['seed']==20260925 and run['trace_kind']==0 and run['limits']['per_query_seconds']==60
  assert run['source_commit']=='0a5dca04cfe37f5d7dae533c43ef6c49deca2fd5' and run['source_tree_clean_at_start']
  config=json.loads((raw/'01-C01-deadlock.config.json').read_text());native=json.loads((raw/'01-C01-deadlock.native.json').read_text())
  assert config['arguments']==result['exact_command'][1:]
  for k,v in native.items():assert result[k]==v,k
  assert result['status']=='timeout' and result['verdict'] is None and result['trace_paths']==[]
  assert (raw/result['stderr_path']).read_bytes()==b''
  assert result['runtime_seconds']>=60 and result['peak_working_set_bytes']<2147483648
assert len(rows)==3
assert len({r['result']['model_hash'] for r in rows})==len({r['result']['query_hash'] for r in rows})==len({r['result']['tool_version'] for r in rows})==1
print('Three control archives, native results, metadata copies, exact commands and unchanged inputs match. All timeout/null; no positive verification claim.')
