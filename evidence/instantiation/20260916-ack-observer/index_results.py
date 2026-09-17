"""Index immutable run evidence; does not run or invent verification results."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
records = []
for directory in sorted((HERE/'runs').iterdir()):
    for line in (directory/'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert sha((directory/name).read_bytes()) == digest, (directory, name)
    run = json.loads((directory/'run.json').read_text())
    commands = json.loads((directory/'commands.json').read_text())
    for cmd in commands:
        if cmd['name'] not in ('old', 'fixed', 'late_timeout', 'late_ack', 'no_completion', 'zero_time', 'late_then_zero'):
            continue
        name = cmd['name']
        model, query = directory/(name+'.xml'), directory/(name+'.q')
        verdicts = re.findall(r'-- Formula is (NOT satisfied|satisfied)\.', (directory/cmd['stdout']).read_text())
        assert verdicts == cmd['verdicts']
        record = dict(cmd, run_id=directory.name+'-'+name, source_commit=run['source_commit'],
                      model_hash=sha(model.read_bytes()), query_hash=sha(query.read_bytes()),
                      tool_version=run['tool_version'], environment_reference=str((directory/'run.json').relative_to(HERE)),
                      model_path=str(model.relative_to(HERE)), query_path=str(query.relative_to(HERE)),
                      parameter_set={'monitor_deadline':3,'functional_deadline':None if name=='no_completion' else 4 if name.startswith('late_') else 3,
                                     'bridge_deadline':4 if name in ('late_ack','late_then_zero') else 1},
                      instance_vector={'scheduler':1,'bridge':1,'observer':1,'replacement_test_peer':1},
                      artifact_directory=str(directory.relative_to(HERE)),
                      evidence_class='focused corrective diagnostic; not full integrated-model verification')
        record['result_per_query'] = []
        for i, query_text in enumerate(query.read_text().splitlines(),1):
            trace = directory/(name+'-trace-'+str(i))
            record['result_per_query'].append({'query':query_text, 'expected':cmd['expected'][i-1], 'requirement':cmd.get('requirements', ['Историческая проверка; см. README']*len(cmd['expected']))[i-1], 'verdict':verdicts[i-1] if i<=len(verdicts) else 'not_available',
                       'trace_reference':str(trace.relative_to(HERE)) if trace.exists() else None})
        records.append(record)
(HERE/'results-index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(f'Indexed {len(records)} distinct configuration runs; all saved file hashes and raw verdicts match.')

rows = ['# Соответствие сценариев и результатов', '',
        'Это целевые диагностические композиции. Отсутствие Violation не доказывает обязательного завершения при остановке времени или бесконечных переходах без продвижения времени.', '',
        '| Сценарий | Требование | Точный запрос | Ожидание | Факт | run_id |',
        '|---|---|---|---|---|---|']
for record in records:
    for q in record['result_per_query']:
        rows.append(f"| {record['name']} | {q['requirement']} | `{q['query']}` | {q['expected']} | {q['verdict']} | {record['run_id']} |")
(HERE/'review-matrix.md').write_text('\n'.join(rows)+'\n', encoding='utf8')
