Неопределённость: 0.06.

**Цель**

Сделать generated UPPAAL-модель визуально читаемой в GUI: каждый автомат должен открываться как нормальная схема, где состояния, переходы, guards, sync и assignments разнесены логично, а человек без гадания понимает, что относится к чему.

**Главный принцип**

Не чинить руками в UPPAAL. Координаты должны генерироваться детерминированно из generator’а. Иначе это мусор, который сломается при следующем `phy-generate`.

**Задачи**

- [x] Добавить понятие layout mode в generator:
  - `--layout compact`
  - `--layout readable`
  - default лучше сделать `readable`, потому что текущий compact почти бесполезен глазами.

- [x] Расширить CLI `phy-generate`:
  ```bash
  phy-generate --layout readable
  ```

- [x] Расширить MCP tool `phy_generate_uppaal_model` параметром:
  ```text
  layout="readable"
  ```

- [x] Завести layout-слой в коде:
  ```text
  phy/layout.py
  ```
  Там должны жить координаты, правила размещения labels, bend-points, template maps.

- [x] Ввести единый coordinate convention:
  - X слева направо = развитие сценария
  - Y вверх = degradation/alerts
  - Y вниз = recovery/reporting/service paths
  - violation/deadlock/contract failure всегда справа
  - nominal/base state всегда слева

- [x] Для каждого template задать смысловые зоны:
  - `A_CH`: nominal, measurement, channel degraded classes, outage, contract violation
  - `A_SIG`: signal nominal, reconfiguring, signal limited, report path, violation
  - `A_BM`: beam lock, recovery, restored, handover assist, failed
  - `A_SQ`: sensing nominal, probability/freshness/resolution limited, failure
  - `A_PH`: aggregate normal, communication degraded, sensing degraded, joint degraded, failure
  - `ENV_*`: environment stimulus loops отдельно, без смешивания с PHY automata
  - `Obs*`: trigger, waiting, satisfied, violation

- [x] Разнести labels по типам:
  - guard сверху перехода
  - sync рядом с серединой ребра
  - assignment снизу перехода
  - invariant под location
  - длинные assignments переносить в несколько строк

- [x] Добавить bend-points для переходов:
  - self-loop не должен лежать поверх location
  - обратные переходы идут отдельной нижней/верхней дугой
  - несколько переходов между теми же состояниями не должны совпадать
  - переходы в violation идут отдельной правой магистралью

- [x] Добавить semantic grouping через комментарии в declarations:
  ```c
  // === A_CH: Channel classifier ===
  // === A_SIG: Signal classifier ===
  // === A_BM: Beam management ===
  ```

- [x] Добавить readable names/notes в XML, где это поддерживает UPPAAL:
  - template name
  - location name
  - branch purpose через label/comment, если не ломает verifyta

- [x] Генерировать `model_map.md` рядом с `model.xml`:
  - список templates
  - что делает каждый автомат
  - какие каналы слушает
  - какие каналы публикует
  - какие переменные пишет
  - какие переменные только читает

- [x] Генерировать `template_map.md`:
  - отдельно по `A_CH/A_SIG/A_BM/A_SQ/A_PH`
  - location -> смысл
  - transition -> причина
  - sync -> кто sender/receiver

- [x] Добавить `channels_map.md`:
  - `*_cmd` = handshake command
  - `*_report` = broadcast report
  - `*_degraded` / alerts = broadcast events
  - кто emits
  - кто listens

- [x] Добавить `--output-dir` export этих новых файлов:
  ```text
  model.xml
  queries.q
  contract.json
  model_map.md
  template_map.md
  channels_map.md
  ```

- [x] Обновить `phy-report`, чтобы он включал визуальную карту модели.

- [x] Добавить golden fixture для readable layout:
  ```text
  tests/fixtures/phy_model_article.readable.golden.xml
  ```

- [x] Добавить тесты, что layout не схлопывается:
  - location coordinates не одинаковые
  - labels имеют разные координаты
  - violation states справа
  - nominal states слева
  - self-loops имеют nails/bend-points
  - templates не имеют “всё на одной линии”

- [x] Добавить статический layout validator:
  ```text
  validate_generated_layout(model_xml)
  ```

- [x] Добавить проверку максимальной плотности:
  - не больше N labels в одной координате
  - не больше N locations на одной Y-линии без явного смысла
  - расстояние между locations минимум, например 180 px

- [x] Для сложных templates сделать не один большой автомат, а readable decomposition там, где это законно:
  - не ломая verifyta semantics
  - не меняя channels/state variables
  - только визуальное разнесение
  - принято решение не дробить UPPAAL instances физически: это ломает стабильные query names; decomposition сделан как semantic zones/layout/maps внутри существующих templates.

- [x] Добавить экспорт Graphviz/SVG как дополнительную человеческую карту:
  ```text
  phy-export-diagram
  ```
  UPPAAL GUI всё равно кривоват; SVG-карта может быть в разы понятнее.

- [x] Документировать workflow:
  ```bash
  phy-generate --layout readable --output-dir ...
  ```
  Потом открывать именно generated `model.xml`, а смысл смотреть в `model_map.md`.

**Definition of Done**

- `model.xml` открывается в UPPAAL GUI без наложенной каши.
- Каждый template читается без ручной раскладки.
- `A_CH/A_SIG/A_BM/A_SQ/A_PH` визуально различимы по структуре.
- Labels не лежат друг на друге.
- Есть `model_map.md`, где понятно, что к чему относится.
- Tests ловят регресс, если generator снова начнёт складывать всё в одну линию.
