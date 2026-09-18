# Результаты проверок

Полный software suite: **163 tests, OK, 0 skips** вне sandbox, Python 3.12,
изолированное editable окружение `/tmp/issue33-venv`. Первый sandbox запуск:
163 tests, одна ошибка TimeoutError при MCP stdio initialize; этот журнал сохранён
отдельно. Это ограничение запуска, а не скрытый пропуск теста.

Static 43/14 + 9 XML templates, coordination, MCP construction, list-examples,
pip check и diff check — exit 0. Точные команды, source commit, environment,
hashes и исходные журналы: [checks.json](checks.json), [logs/](logs/).
Строки о намеренных несовпадениях hashes в suite log относятся к negative fixtures.

Initial read-only review #32: audit.py exit 0, четыре check_audit.py tests OK;
raw log той предварительной проверки не сохранялся. Это явно отделено от
сохранённых журнальных проверок #33. Ни один из этих checks не является UPPAAL
verification. Новых verifier runs нет; старые #31 не повторялись.

Опубликованный checkpoint `d5ba21d9e278f777aa5cedc95a34ad7b24bf2385` имеет
байтово идентичное дерево локальному checkpoint, на котором запущен suite.
Полный SHA локального source checkpoint указан в checks.json. Последующее
дополнение содержит только журналы, ссылки на follow-up Issues и handoff;
production source/test files не изменялись.
