# Отдельные corrections и scope

Owner каждой будущей correction — **artmus208**. Reviewer должен быть другим
лицом; кандидат не назначается автоматически. Код в этом чате не меняется.

Два последовательных deliverables:

1. [#35 — Recovery](https://github.com/artmus208/uppaal_sdn_isac/issues/35): функциональный failure-to-outcome контракт 20/10 и отдельно пассивный
   recorder; targeted original/recorder-only/functional-fixed diagnostics.
2. [#36 — Admission](https://github.com/artmus208/uppaal_sdn_isac/issues/36): пассивная корреляция APP/SDN начала и исхода, сохранение 15/5 и
   two-transport semantics; targeted diagnostics без изменения service policy.

Планируемые production scopes обоих пересекаются по integrated/adapt.py и могут
пересечься по boundary.py. Поэтому второй Issue блокируется до принятия/merge
первого и нового точного base; одновременного разрешения записи нет.

Проверка открытых GitHub Issues на 2026-09-17:

| Issue | Найденный scope | Решение |
|---|---|---|
| #19 | `src/uppaal_mcp/integrated/**` | Пересечение с adapt.py/boundary.py/generator.py. До correction требуется отдельное решение Integrator о передаче конкретных файлов, записанное в обеих задачах |
| #30 | `integrated/adapt.py` | #31 merged, но Issue остаётся open/claimed. Не считать старую резервацию автоматически снятой; явно освободить scope перед correction |
| #23 | `integrated/inputs.py` | В corrections этот файл не включать; pinned source inputs не меняются |
| #17, #32, #33 | Разные evidence directories | Пересечения нет |

Остальные открытые scopes просмотрены в сохранённом scope snapshot. Новые Issues
имеют статус blocked и только **proposed write scope**: это очередь работы,
не параллельные активные назначения на shared files. При активации повторить
проверку Issues/PRs и зафиксировать точный base. Самостоятельно снимать scopes
#19/#30 или объявлять независимое принятие #33 запрещено.

PHY measurement/observers, MAC polling/report, SDN rule/control/sensing и остальные
APP latches перечислены в triage.md как отдельные незакрытые correction needs.
Они не включаются «заодно» в два следующих patches. До их реализации сначала
создать отдельные scoped задачи и принять их endpoints/claim scope.

Порядок активации: независимое принятие #33 → освобождение scope → #35 → принятие/merge #35 → новый base и scope check → #36. Оба Issue созданы и назначены artmus208, status/blocked.
