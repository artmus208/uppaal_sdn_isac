Агент в другом контекстном окне начал идти по порядку этого плана. Он сделал некоторые изменения в файле src/uppaal_mcp/integrated/adapt.py

```
13 unmodified lines
RECOVERY_RECORDING = '''
// Passive episode recording: only A_REC writes these variables.
bool sdn_obs_rec_active = false, sdn_obs_rec_late = false;
bool sdn_obs_rec_protocol_error = false;
void sdn_obs_rec_start() {
if (sdn_obs_rec_active) sdn_obs_rec_protocol_error = true;
else { sdn_obs_rec_active = true; sdn_c_obs_rec = 0; }
}
void sdn_obs_rec_finish() {
if (!sdn_obs_rec_active) sdn_obs_rec_protocol_error = true;
sdn_obs_rec_active = false;
}
'''

RECOVERY_OUTCOME = '''
// Local failure is distinct from later report delivery.
// 0: no failure, 1: dispatch/recovery-stage timeout, 2: rollback timeout.
int[0,2] sdn_recovery_failure_kind = 0;
bool sdn_recovery_report_pending = false;
'''


def record_recovery(t):
"""Instrument actual episode events without restricting functional edges.

Called after typed-channel adaptation and (separately) recovery policy edits.
Finish edges are binary receives or local edges, never broadcast receives.
"""
for tr in list(t.findall('transition')):
if label(tr, 'synchronisation') in ('sdn_link_failure?', 'sdn_node_failure?'):
append_update(tr, 'sdn_obs_rec_start()')
target = tr.find('target').get('ref')
if source_name(t, tr) not in ('StableConfig', 'RecoveryFailed') and target in (
loc_id(t, 'StableConfig'), loc_id(t, 'RecoveryFailed')):
guard = label(tr, 'guard') or 'true'
append_update(tr, 'sdn_obs_rec_finish()')
late = deepcopy(tr)
deadline = '(sdn_D_recovery + sdn_D_rollback)'
set_label(tr, 'guard', f'({guard}) && sdn_c_obs_rec <= {deadline}')
set_label(late, 'guard', f'({guard}) && sdn_c_obs_rec > {deadline}')
append_update(late, 'sdn_obs_rec_late = true')
t.append(late)


def recovery_policy(t):
"""Explicit functional 20/10 contract, independent of passive recording."""
detected = next(l for l in t.findall('location') if l.findtext('name') == 'FailureDetected')
inv = ET.SubElement(detected, 'label', kind='invariant')
inv.text = 'sdn_c_rec <= sdn_D_recovery'
failed = ('sdn_recoveryClass = sdn_REC_FAILED, sdn_sdnReason = sdn_SDN_RECOVERY_FAILED, '
'sdn_serviceImpact = sdn_IMPACT_FAILED, sdn_link_failure_pending = false, '
'sdn_node_failure_pending = false, sdn_optimistic_reconfig = false, '
'bus_rec_policy_open = false, sdn_failure_report_sent = false, '
'sdn_recovery_report_pending = true')
for tr in t.findall('transition'):
if label(tr, 'synchronisation') in ('sdn_link_failure?', 'sdn_node_failure?'):
append_update(tr, 'sdn_recovery_failure_kind = 0')
if tr.find('target').get('ref') == loc_id(t, 'RecoveryFailed'):
# The outcome cannot depend on a binary failure-report receiver.
set_label(tr, 'synchronisation', '')
set_label(tr, 'assignment', failed + ', sdn_recovery_failure_kind = 2')
for phase in ('FailureDetected', 'StandbySwitch', 'ReactiveReembedding'):
edge(t, phase, 'RecoveryFailed', guard='sdn_c_rec == sdn_D_recovery',
update=failed + ', sdn_recovery_failure_kind = 1')
edge(t, 'RecoveryFailed', 'RecoveryFailed', guard='sdn_recovery_report_pending',
sync='sdn_failure_report!',
update='sdn_recovery_report_pending = false, sdn_failure_report_sent = true')


def recovery_observer(t):
"""Read-only bad-state witness; producer-owned clocks survive scheduler delay."""
for node in list(t):
if node.tag == 'transition' or (node.tag == 'location' and node.findtext('name') == 'Wait'):
t.remove(node)
edge(t, 'Idle', 'Violation', guard='sdn_obs_rec_late || sdn_obs_rec_protocol_error')
edge(t, 'Idle', 'Violation',
guard='sdn_obs_rec_active && sdn_c_obs_rec > sdn_D_recovery + sdn_D_rollback')


def adapt_layer(layer, declaration, templates):
6 unmodified lines
declaration = declaration.replace('sdn_telemetryClass = sdn_TEL_FRESH', 'sdn_telemetryClass = sdn_TEL_MISSING')
declaration += RECOVERY_RECORDING + RECOVERY_OUTCOME
if layer == 'app':
22 unmodified lines
original = process.removeprefix(prefix).removesuffix('_0')
if layer == 'sdn' and original == 'ObsRecovery':
recovery_observer(t)
if layer == 'mac' and original == 'ObsPhyAck':
87 unmodified lines
append_update(tr, 'bus_mac_report_consumed = true')
if layer == 'sdn' and original == 'A_REC':
recovery_policy(t)
record_recovery(t)
if layer == 'mac' and original == 'A_SCH':

```
Сообщения агента до использования лимита по токенам:
```
Начну с #35: проверю назначения и пересечения scope, зафиксирую базовый commit и условия приёмки. Затем реализую recovery-контракт и выполню целевые проверки.

Used GitHub and Uppaal integrations, ran commands
Fetched issue on issue #35
Fetched issue on issue #19
Fetched issue on issue #30
Ran pwd git status --short --branch cat AGENTS.md CONTRIBUTING.md manifests/v1.md manifests/collaboration-v1.yaml manifests/baselines/reviewer-r1.yaml
Ran ls -d /tmp/uppaal-issue-* /tmp/issue33-venv /mnt/d/UPPAAL/app/bin/verifyta.exe 2>/dev/null command -v verifyta ls /mnt/d
Fetched issue comments on artmus208/uppaal_sdn_isac#19
Uppaal version
Ran git clone --no-hardlinks /mnt/c/users/musta/desktop/pysources/mcp_uppaal /tmp/uppaal-issue-35
Fetched issue comments on artmus208/uppaal_sdn_isac#30
Ran git fetch https://github.com/artmus208/uppaal_sdn_isac.git read
Ran git rev-parse FETCH_HEAD git switch -c codex/artmus208/35-recovery-contract FETCH_HEAD git remote set-url origin https://github.com/artmus208/uppaal_sdn_isac.git git config user.name artmus208 git config user.email 59034340+artmus208@users.noreply.github.com rg --files -g AGENTS.md sed -n '1,210p' src/uppaal_mcp/integrated/adapt.py cat evidence/instantiation/20260917-v03-contract-disposition/contracts.md
Ran ls '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe' ls -d /tmp/issue33-venv /tmp/uppaal-issue-33 2>/dev/null sed -n '1,220p' evidence/instantiation/20260916-ack-observer/record.py
Ran git fetch origin read
Ran git -c http.proxy= -c https.proxy= fetch origin read
Ran ls -d /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal* /mnt/d/uppaal* 2>/dev/null

PR #37 уже принят независимым review и включён в read. verifyta доступен: команда версии вернула UPPAAL 5.0.0. Это позволяет перейти к реализации и реальным целевым прогонам.

Начну #35 от commit 44ff0e3. Передачу общих файлов зафиксирую в #19, #30 и #35 по твоему поручению идти по плану; #36 пока останется в очереди.

Used GitHub integration, edited a file, read files, ran commands
Updated issue on artmus208/uppaal_sdn_isac#19
Updated issue on artmus208/uppaal_sdn_isac#30
Updated issue on artmus208/uppaal_sdn_isac#35
Ran git switch -c codex/artmus208/35-recovery-contract 44ff0e336c7bfc88e3ebe3da3d05699c2acef62f git config http.proxy '' rg --files evidence/instantiation/20260916-ack-observer tests | rg 'ack|record' cat src/uppaal_mcp/integrated/adapt.py sed -n '1,200p' tests/test_integrated_ack_observer.py

Read boundary.py
Read check.py
Read check.py
Edited file
adapt.py+85-0
Ran PYTHONPATH=src python3 - <<'PY' from uppaal_mcp.integrated.generator import generate c=generate();print(c.metadata['model_hash']);print(len(c.model_xml)) PY
```

Пожалуйста, повтори и продолжи работу предыдущего агента по данному контексту

p.s план:
Теперь следующий шаг — #35, затем #36, приёмка P1/P2 и заморозка baseline. PR #37 принят и merged; повторно обсуждать уже принятые контракты не нужно.

Этап	Конкретный результат
1. Разблокировать реализацию	Integrator передаёт нужные файлы из scopes #19/#30 в #35; фиксируем base commit и независимого reviewer
2. Выполнить #35 — recovery	Реализован контракт 20/10, исправлена регистрация событий, сохранены целевые результаты UPPAAL; review и merge
3. Выполнить #36 — admission	Исправлена корреляция запроса и исхода, сохранены проверки; review и merge
4. Принять P1/P2	Отдельные решения по V03/#15 и интегрированной модели; все оставшиеся замечания получили явную диспозицию
5. Пройти Gate 1	Governance PR фиксирует точные входы, hashes, параметры, экземпляры, queries, рабочий verifier/лицензию; независимый Integrator принимает frozen baseline
Чтобы опять не уйти в бесконечные итерации, до начала #35 нужно согласовать окончательный список блокеров из уже готового triage. Остальное откладывается только с обоснованием, почему не влияет на выбранную baseline и обязательные проверки. Это можно записать в GitHub без нового большого отчёта.

Остаток — две запланированные реализации, итоговая приёмка и freeze. Но назвать их достаточными можно лишь после решения по оставшемуся triage: review #37 прямо оставило эти вопросы открытыми.

Полную проверку свойств и масштабируемость делаем после Gate 1, в P3/P4.
