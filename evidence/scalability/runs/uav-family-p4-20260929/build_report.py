"""Build completed/censored tables from retained records without changing verdicts."""
import csv
import json
from pathlib import Path
import statistics
import re
import sys
from collections import Counter,defaultdict
root=Path(sys.argv[1]); here=root/'evidence/scalability/runs/uav-family-p4-20260929'
r=json.loads((here/'campaign-002/runs.json').read_bytes());s=json.loads((here/'campaign-002/settings.json').read_bytes())
assert s['status'] in ('completed', 'stopped'), 'campaign still active'
q=[x for x in r if x['phase']=='model-checking']; groups=defaultdict(list)
for x in q: groups[(x['N'],x['query_id'])].append(x)
rows=[]
for (n,qid),cells in sorted(groups.items()):
    completed=[x['runtime_seconds'] for x in cells if x['status']=='success']
    counts=Counter(x['status'] for x in cells)
    category='fixed-u0' if qid in ('u0-queue-safety','u0-queue-full') else ('service-coverage' if re.fullmatch(r'u\d+-service',qid) else 'growing-global-predicate')
    rows.append(dict(N=n,query_id=qid,query_category=category,scheduled=len(cells),completed=counts['success'],timeout=counts['timeout'],memory_limit=counts['memory_limit'],not_started=counts['not_started'],other=sum(v for k,v in counts.items() if k not in ('success','timeout','memory_limit','not_started')),completed_median_seconds=statistics.median(completed) if completed else None,completed_min_seconds=min(completed) if completed else None,completed_max_seconds=max(completed) if completed else None,max_observed_memory_bytes=max((max(x.get('peak_private_bytes',0),x.get('peak_reported_working_set_bytes',0)) for x in cells),default=0),verdicts=dict(Counter(x['property_verdict'] for x in cells if x['status']=='success'))))
summary={'kind':'bounded_verifier_cost_observations','campaign_status':s['status'],'baseline_id':s['baseline_id'],'baseline_manifest_sha256':s['baseline_manifest_sha256'],'source_commit':s['source_commit'],'query_counts':dict(Counter(x['status'] for x in q)),'all_phase_counts':dict(Counter(x['status'] for x in r)),'budget_charged_seconds_including_prior':s['used_seconds'],'query_groups':rows,'scope':'N=1..4 exact finite models; not working-network scalability; no closure of R03/R04/C06','timing_scope':'fresh-process native verifier wall time including compilation/trace writing; not pure engine search time'}
preparation=[]
for phase in ('generation','compile','load-and-parse'):
    for x in r:
        if x['phase']!=phase: continue
        entry={k:x.get(k) for k in ('run_id','repeat','N','phase','status','runtime_seconds')}
        if phase=='generation' and x['status']=='success':
            details=json.loads((here/'campaign-002'/x['cell_id']/'stdout.txt').read_bytes())
            entry.update({k:details[k] for k in ('snapshot_preparation_seconds','generator_subprocess_seconds','copy_and_compare_seconds')})
        preparation.append(entry)
coverage=[]
for repeat in (1,2,3):
    for n in (1,2,3,4):
        cells=[x for x in q if x['repeat']==repeat and x['N']==n and re.fullmatch(r'u\d+-service',x['query_id'])]
        observed=[x['runtime_seconds'] for x in cells if x.get('runtime_seconds') is not None]
        counts=Counter(x['status'] for x in cells)
        coverage.append(dict(repeat=repeat,N=n,scheduled=len(cells),status_counts=dict(counts),all_completed=counts['success']==n,observed_runtime_sum_seconds=sum(observed) if observed else None,observed_runtime_max_seconds=max(observed) if observed else None))
summary['preparation']=preparation
summary['service_coverage_workloads']=coverage
(here/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
with (here/'query-observations.csv').open('w',newline='') as f:
    fields=['run_id','repeat','N','query_id','status','property_verdict','runtime_seconds','budget_charged_seconds','cpu_seconds','samples','maximum_sample_gap_seconds','peak_private_bytes','peak_reported_working_set_bytes','model_hash','query_hash','tool_version','source_commit']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in q:w.writerow({k:x.get(k) for k in fields})
lines=['# Результаты ограниченной серии P4 — Issue #76','',f"Статус campaign-002: **{s['status']}**. Учтённый бюджет: {s['used_seconds']:.3f} / 7200 секунд.",'','Baseline: `uav-family-r1-20260929`; manifest SHA256 `'+s['baseline_manifest_sha256']+'`.','Source commit запуска: `'+s['source_commit']+'`.','Хост: Windows 11 build 26200, Ryzen 5 1400; native memory measurements на каждый запуск.','',f"90 запланированных научных ячеек: `{dict(Counter(x['status'] for x in q))}`.",'','Исходные записи: [campaign-002/runs.json](campaign-002/runs.json). Каждая запись содержит run_id, status, model_hash, query_hash, tool_version, команду, stdout/stderr, память и ссылки на трассы.','[CSV наблюдений](query-observations.csv) сохраняет отдельные повторы. Положительные и отрицательные verdict относятся только к своим точным model/query hashes.','', '## Время по запросам','', 'Время — end-to-end native verifier, включая компиляцию и запись трассы. Медиана/диапазон приведены только для завершённых наблюдений **вместе** с числом цензурированных. При наличии таймаутов это не оценка безусловного времени. Отсутствие завершённых наблюдений обозначено —, а не нулём.','', '| Тип сравнения | N | Запрос | Завершено / 3 | Timeout | Memory stop | Не запущено | Медиана завершённых, с | Диапазон, с | Verdict завершённых |','|---|---:|---|---:|---:|---:|---:|---:|---|---|']
for x in sorted(rows,key=lambda row:(row['query_category'],row['query_id'],row['N'])):
    median='—' if x['completed_median_seconds'] is None else f"{x['completed_median_seconds']:.3f}"
    span='—' if x['completed_min_seconds'] is None else f"{x['completed_min_seconds']:.3f}–{x['completed_max_seconds']:.3f}"
    lines.append(f"| {x['query_category']} | {x['N']} | {x['query_id']} | {x['completed']} | {x['timeout']} | {x['memory_limit']} | {x['not_started']} | {median} | {span} | {x['verdicts']} |")
lines += ['', '## Наблюдаемая память', '', 'Максимум по трём попыткам, включая таймауты. Это наблюдаемый пик target process, а не память, необходимая для завершения запроса. Порог остановки 2048 MiB является выборочным; фактические интервалы измерений и overshoot сохранены в каждом run.', '', '| N | Запрос | Максимум private / reported working set, MiB |', '|---:|---|---:|']
for x in rows:
    lines.append(f"| {x['N']} | {x['query_id']} | {x['max_observed_memory_bytes']/1024**2:.2f} |")
lines += ['', '## Подготовительные фазы', '', '| Повтор | N | Фаза | Статус | Полное время, с | Генератор, с |', '|---:|---|---|---|---:|---:|']
for x in preparation:
    elapsed='—' if x['runtime_seconds'] is None else f"{x['runtime_seconds']:.3f}"
    generator='—' if 'generator_subprocess_seconds' not in x else f"{x['generator_subprocess_seconds']:.3f}"
    lines.append(f"| {x['repeat']} | {x['N']} | {x['phase']} | {x['status']} | {elapsed} | {generator} |")
lines += ['', 'Время генератора включает запуск Python и запись файлов; полное время фазы также включает восстановление pinned snapshot и сравнение. Подробные составляющие сохранены в SUMMARY.json. Compile/load измеряют отдельные свежие процессы.', '', '## Service coverage workload', '', 'Каждая строка объединяет N отдельных service-запросов одного повтора. Сумма и максимум — фактически наблюдавшееся время, включая цензурированные попытки; это не время решения всей задачи, если хотя бы один запрос не завершён.', '', '| Повтор | N | Завершено / N | Timeout | Не запущено | Наблюдаемая сумма, с | Наблюдаемый максимум, с |', '|---:|---:|---:|---:|---:|---:|---:|']
for x in coverage:
    counts=x['status_counts']; total='—' if x['observed_runtime_sum_seconds'] is None else f"{x['observed_runtime_sum_seconds']:.3f}"
    maximum='—' if x['observed_runtime_max_seconds'] is None else f"{x['observed_runtime_max_seconds']:.3f}"
    lines.append(f"| {x['repeat']} | {x['N']} | {counts.get('success',0)} / {x['N']} | {counts.get('timeout',0)} | {counts.get('not_started',0)} | {total} | {maximum} |")
lines += ['', '## Интерпретация и ограничения','', 'Лимит поиска — 60 с; наблюдаемые таймауты около 62 с включают остановку и ожидание завершения процесса. Консервативный общий бюджет дополнительно включает запуск/завершение monitor. Генерация, prelaunch probes и Git checkpoints в verifier budget не входят. Случайный порядок запусков и контроль фоновой нагрузки не применялись; различия времени сами по себе не доказывают закон роста сложности.', '', 'Fixed-u0 запросы сравниваются отдельно от глобальных предикатов, растущих с N. N запросов uI-service — отдельная coverage-нагрузка, а не один запрос. Не предполагается симметрия UAV из-за фиксированного порядка уведомлений.','', 'Таймаут/порог памяти означает отсутствие verdict и наблюдаемую границу выбранного бюджета; он не доказывает недостижимость, безопасность или универсальную границу масштабируемости. Все 30 service-попыток этой серии завершились таймаутом; достижимость обслуживания остаётся открытой. Даже отдельный положительный service verdict не установил бы fairness, SLA или полезное обслуживание после absorbing overflow.','', 'Серия относится к затратам verifier на конкретных полных моделях. Физическая калибровка, работоспособность сети и перенос старых P3 результатов не заявляются. Старые запуски на другом хосте не включаются в повторы. Сопоставление с работой Глониной и полная приёмка R03/R04/C06 остаются вне этого ограниченного отчёта.','', '## Сохранённая остановка подготовки','', 'campaign-001 остановлен на генерации из-за operational context hash drift до любых научных/compile/load запусков. Ошибка runner исправлена генерацией из pinned Git snapshot. Пользователь отдельно разрешил campaign-002; исходная попытка сохранена. Её 0.1355066079995595 с metadata включены в общий бюджет. Все 70 файлов генерации проверены побайтно, исторические inputs не изменялись.','', 'Generation subprocess timing, snapshot preparation and copy/compare записаны отдельно в stdout каждой generation-ячейки. Compile-only и load — отдельные подготовительные фазы и не доказывают свойства.','']
(here/'RESULTS.md').write_text('\n'.join(lines))
print(json.dumps(summary['query_counts']))
