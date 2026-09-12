# Словарь Efen

[Документация Efen](index.md) · [Amber glossary](https://github.com/limelight-lang/amber/blob/main/design/glossary.md)

Термины ниже описывают текущую модель языка. Физические структуры HIR и стадии
компиляции вынесены в отдельный словарь Amber.

| Термин | Значение | Подробнее |
|---|---|---|
| **ABI** | Набор бинарных соглашений о вызовах, layout, исключениях и времени жизни, общий для совместимых backend-путей. | [Режимы компиляции](compilation-modes.md) |
| **Ambient context** | Набор доступных в текущей области контекстных привязок. Чтение выполняется через `%`; требование отражается как `in Context`. | [Контексты и эффекты](context-and-effects.md) |
| **Aspect** | Compile-time расширение, которое участвует в построении абстракции через объявленный план и стадии. | [Аспекты](aspects/aspect.md), [построение класса](aspects/compile-time/class.md) |
| **Attribute** | Сохранённое в исходном HIR применение метакода к декларации. Может породить HIR или metadata, но само применение не удаляется. | [Metadata](aspects/metadata.md), [декораторы](decorators.md) |
| **Borrow / заимствование** | Временное невладеющее право доступа. Обычное чтение owning-поля заимствует; передачу владения выражает `take`. | [Ownership](types/ownership.md) |
| **Capability / право** | Статически известная возможность над значением: `own`, `read`, `write`, `shared`, `split` или `inspect`. | [Ownership](types/ownership.md) |
| **Class** | Runtime-абстракция с identity, поведением и определением класса, которое может выбирать физическую реализацию операций. | [Классы](classes.md) |
| **Compile-time code** | Efen-код, исполняемый компилятором для чтения, проверки или преобразования HIR. | [Compile-time API](compile-time/index.md) |
| **Contract** | Compile-time набор требований. Сам по себе не является runtime-типом и не создаёт VTBL. | [Контракты](contracts.md) |
| **Context** | Типизированная зависимость, доступная через ambient context и отражаемая в сигнатуре через `in`. | [Контексты и эффекты](context-and-effects.md) |
| **Decorator** | Атрибут, чьё выполнение преобразует помеченную декларацию или порождает дополнительный HIR. | [Декораторы](decorators.md), [metadata](aspects/metadata.md) |
| **Dependent type** | Тип, зависящий от конкретного значения или экземпляра. Полная модель dependent types и `Layout<T>` пока отложена. | [Адреса](memory/addresses.md) |
| **Dialect** | Frontend-уровень, который отображает другой исходный язык или профиль синтаксиса в семантику Efen и Amber HIR. | [Диалекты](dialects.md) |
| **Effect** | Статически отслеживаемое внешнее требование или действие, распространяемое по графу вызовов. | [Контексты и эффекты](context-and-effects.md) |
| **Family** | Открытый tagged carrier `Family<Base>`, куда проверенные новые виды могут добавляться без закрытого union всех вариантов. | [Адреса](memory/addresses.md), [колоночные layout](memory/columnar-layouts.md) |
| **Flow** | Монадическая последовательность вычислений. `<-` связывает значение контекста, а `return` завершает только сам `flow`. | [Flow](flow.md) |
| **HIR** | Высокоуровневое структурное представление программы после frontend. Тела проходят от нетипизированных C0/C1-форм к типизированным и проверенным поздним стадиям; это не машинные инструкции. | [Compile-time API](compile-time/index.md), [Amber HIR](https://github.com/limelight-lang/amber/blob/main/design/hir/README.md) |
| **Interface** | Runtime-тип с динамической диспетчеризацией. Проекция contract в interface создаётся только явной формой `interface I from C`. | [Интерфейсы](interfaces.md), [контракты](contracts.md#связь-контрактов-с-интерфейсами) |
| **`isolated`** | Граница, запрещающая неявно расширять набор внешних эффектов функции или региона. Не означает `pure` и не запрещает re-entry. | [Контексты и эффекты](context-and-effects.md) |
| **Layout** | Связь logical identities, populations и physical stores. Полный контракт `Layout<T>` остаётся отдельной открытой темой. | [Управление памятью](memory/index.md), [варианты storage](memory/layout-representations.md) |
| **Layer** | Compile-time архитектурная группа пакетов с отношениями `uses`, `exposes` и `provides`; runtime-сущностью не является. | [Слои](layers.md) |
| **Managed slot** | Режим конкретного storage-слота, где lifetime-операции строит выбранная модель управления, а не обычный borrow checker. Это не право типа и не исходный модификатор. | [Ownership](types/ownership.md) |
| **Metadata** | Типизированные compile-time данные декларации; отдельное решение определяет, какая добавленная metadata нужна runtime. | [Metadata](aspects/metadata.md) |
| **Metafunction** | Compile-time функция, возвращающая `InlineClosure` или преобразующая HIR. Шаблон и placeholders типизированы по её контракту; вставленный результат проходит обычные разрешение и проверки. | [Метафункции](compile-time/metafunctions.md) |
| **Module** | Файл и область имён внутри пакета; видимость модуля ограничивает доступность его деклараций. | [Пакеты и модули](packages.md) |
| **Naming register** | Регистр первой буквы определяет категорию имени: типы и контексты начинаются с заглавной, значения и варианты enum — со строчной. | [Лексическое правило](index.md#лексическое-правило-имён) |
| **Opaque type** | Номинальная identity со скрытой реализацией и явно ограниченной областью раскрытия. | [Дженерики](generics.md) |
| **Origin** | Статическая связь ссылки с местом или population, определяющая срок её допустимой жизни. Не путать с provenance сгенерированного HIR. | [Ownership](types/ownership.md), [адреса](memory/addresses.md) |
| **Ownership** | Обязанность управлять временем жизни ресурса и право передать эту обязанность. | [Ownership](types/ownership.md) |
| **Package** | Единица зависимости, конфигурации стратегий и межмодульной видимости. | [Пакеты](packages.md), [стратегии](strategies.md) |
| **Population / население** | Множество живых logical identities одного layout-instance; membership задаёт их logical lifetime. | [Адреса](memory/addresses.md) |
| **`provide`** | Пакет-локальный явный выбор именованной стратегии или связывание реализации. Не экспортируется потребителям пакета. | [Стратегии](strategies.md) |
| **Region** | Лексическая область с дополнительной статической гарантией: например, `nothrows`, `handles` или сохранение typestate. | [Области кода](code-regions.md) |
| **Representation** | Выбранная физическая форма конкретного логического типа. Не является квалификатором отдельной переменной. | [Репрезентации](representations.md) |
| **Resolver** | Compile-time механизм, который превращает логическое обращение к члену в HIR доступа или вызова. | [Разрешение членов](aspects/members-resolving.md) |
| **Strategy** | Отдельная реализация поведения `for Type`, участвующая в статическом разрешении без добавления физического метода типу. | [Стратегии](strategies.md) |
| **`StrategySelector`** | Встроенная compile-time точка расширения; `strategy for StrategySelector where ...` заменяет стандартный выбор стратегий для подходящих запросов. | [Стратегии](strategies.md#правила-выбора-стратегии) |
| **`take`** | Явная передача `own`, после которой исходное место пусто либо недоступно согласно его виду. | [Ownership](types/ownership.md#явное-извлечение) |
| **Typestate** | Проверяемое компилятором состояние значения, ограничивающее допустимые операции и переходы. | [Типы-состояния](types/typestate.md) |
| **Union** | Закрытый набор альтернатив с одной активной альтернативой. Union-поле имеет ту же семантику; layout выбирает компилятор. | [Enum и union](types/enum.md), [union в storage](memory/addresses.md) |
| **Witness** | Конкретная compile-time реализация contract или выбранная стратегия, которую компилятор сохраняет как основание разрешения. | [Контракты](contracts.md), [стратегии](strategies.md) |
| **`without Context`** | Граница вывода: требование `in Context` из блока не заражает окружающую функцию. Доступное значение контекста не удаляется. Название конструкции ещё может измениться. | [Контексты и эффекты](context-and-effects.md) |

## Термины, которые нельзя смешивать

| Не одно и то же | Граница |
|---|---|
| Contract и interface | Contract проверяет compile-time требования; interface является runtime-типом. |
| Layout и representation | Layout связывает identities и stores; representation выбирает физическую форму типа. |
| Origin и provenance | Origin ограничивает жизнь ссылки; provenance объясняет, какой metacode породил HIR. |
| Strategy и aspect | Strategy разрешает поведение; aspect участвует в построении абстракции и её HIR. |
| `isolated` и `without Context` | `isolated` закрывает весь вывод внешних эффектов; `without Context` закрывает одно контекстное требование. |
| Union и `Family<Base>` | Union закрыт; family допускает проверенные новые exact-виды. |
