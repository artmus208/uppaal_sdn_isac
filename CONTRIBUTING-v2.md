# Совместная работа по научному плану v2

Это текущее руководство, выбранное полем `contributing_guide` в
[manifests/current.json](manifests/current.json). Указатель также выбирает
[manifests/v2.md](manifests/v2.md), coordination contract и frozen baseline.
Он описывает конфигурацию checkout; применение перехода к новым задачам требует
решения Integrator с commit и временем после слияния activation PR в `read`
(ссылка `activation_issue` в указателе). Подготовка ветки такого решения не заменяет.

Общие правила ролей, изоляции, установки, проверки, write scope и handoff остаются
в [CONTRIBUTING.md](CONTRIBUTING.md), разделы 1–12. Этот файл сам является
историческим входом генератора и сохраняется побайтно. Его ссылки на текущие
версии scientific plan/coordination contract заменяются указателем `current.json`.
При расхождении текущих указаний о версии руководствуйся этим документом и
[AGENTS.md](AGENTS.md); научные предпосылки старых результатов сохраняются.

Перед началом задачи прочитай current pointer, выбранные им план, contract,
baseline и решение активации, затем назначенный Issue. Текущие назначения и
блокеры хранятся в Issues. Новое правило неопределённости (§1.1 плана) разрешает
продолжать независимую работу при открытом утверждении; обязательные зависимости
и gates меняются только явной disposition.

Исторические v1, collaboration-v1, CONTRIBUTING и baseline продолжают
использоваться для воспроизведения старой конфигурации. Глобальная замена
версий внутри generation inputs запрещена. Старые evidence проверяются на
зафиксированных в них commits; их прежние scope audits не являются проверкой
будущих operational изменений.

## Проверки перехода

Обычная структурная проверка остаётся без внешних Python-зависимостей:

```bash
python scripts/check_coordination.py
```

Она проверяет выбранный контракт и отдельно historical pins. Для полного
baseline hash audit требуется PyYAML и ещё не существующий output path:

```bash
python -m pip install PyYAML
python scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/baseline-audit-new.json
```

Установка, полный `python -m unittest discover -s tests -v`, smoke checks и поля
PR/handoff сохраняются из CONTRIBUTING.md. Новые regression tests проверяют
ошибки pointer, ownership/dependencies и точное воспроизведение frozen XML/queries.
Статические проверки и воспроизведение XML не являются model checking.

Порядок активации и карта существующих Issues:
[evidence/governance/20260928-v2-activation/README.md](evidence/governance/20260928-v2-activation/README.md).
