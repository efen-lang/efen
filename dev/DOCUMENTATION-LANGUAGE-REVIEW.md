# Редакционная проверка документации Efen

Проверяется весь раздел `docs/efen`: **112 статей Markdown**. Список составлен
по файлам репозитория, а не только по найденным английским словам.

## Порядок работы

Статьи проверяются группами в порядке ниже. Каждая статья читается целиком.
Правка терминов не считается завершённой проверкой понятности.

1. Проверить определение предмета статьи: что это, зачем нужно, как пользоваться.
2. Согласовать термины с другими статьями. Использовать принятые русские термины;
   новый или неоднозначный термин объяснять при первом употреблении.
3. Переписать тяжёлые предложения, кальки и смешение русской и английской речи.
   Идентификаторы и ключевые слова языка сохранять в кодовом оформлении.
4. Проверить ход объяснения и примеры: от простого случая к ограничениям.
   Различать смысл конструкции, представление в памяти и реализацию компилятора.
5. Сверить утверждения с действующими правилами. Исправлять противоречия в изложении;
   нерешённые вопросы не превращать редактурой в принятые решения.
6. Проверить ссылки, заголовки, таблицы и блоки кода. Сохранять прежние адреса
   переименованных разделов. После проверки отметить статью в списке.

## Статусы

- **Ожидает** — целиком ещё не проверена.
- **В работе** — есть исправления или начато чтение; проверка не завершена.
- **Проверена** — завершены чтение, редактура и проверка ссылок.

Это редакционная проверка документации. Она не подтверждает реализацию
описанных возможностей компилятором или выполнение примеров.

## Текущий шаг

Завершены группы «Типы и данные» и «Основы и абстракции»: **33 из 112**
статей. Следующая группа — выражения, функции и управление выполнением:
сначала `blocks/README.md`, `blocks/if.md`, `blocks/guard.md`, затем остальные
статьи группы по списку.

В `types/ownership.md` добавлены диаграмма общей модели, таблица прав
`read`/`edit`/`mut`/`out`/`own`, сравнение `copy`/`clone`/`take` и правила
параллельного доступа. Отрисовка диаграммы проверена Mermaid CLI.

## Журнал проверки

### Следующий проход по типам

Полностью прочитаны и отредактированы ещё восемь статей: встроенные контракты,
константы, словари, опциональные типы, владение, SIMD, строки и состояния типов.
Исправлены тяжёлые формулировки, оставшиеся английские заголовки и примеры,
которые противоречили собственному объяснению. Старые адреса переименованных
разделов сохранены; ссылки проверяются после каждой группы правок.

### Завершение раздела типов

Прочитаны целиком `types/collections.md` и `types/access-regions.md`.
В коллекциях добавлен краткий выбор формы хранения, пояснено различие между
методом `take(n)` и передачей владения, исправлены описание ленивых вычислений
и примеры итераторов. В областях доступа объяснение начинается с источника,
права и времени действия; уточнены правила `edit`, роли и выход за границы.

Сверка с `classes.md` выявила устаревшее утверждение в `ownership.md`:
право метода якобы выводилось из тела. Теперь указан действующий порядок —
методы объявляют `edit fn` или `mut fn`, без пометки используется `read`.
Вывод сводки действий из тела сохраняется и не смешивается с правом метода.

### Основы и абстракции

Прочитаны целиком все 13 статей группы. Согласованы определения класса,
структуры, контракта и интерфейса; убраны безусловные обещания бинарной
совместимости и отсутствия затрат. Статья об абстракциях объясняет,
что программируется в реализации и какие правила исходного кода сохраняются.

Переработаны объяснения представлений, параметров типов, пакетов параметров,
стратегий и неизменяемости. В примерах явно указаны права изменяющих методов,
владение сохраняемыми аргументами и отличие массива от растущего вектора.
Неполный пример CoW заменён объяснением требований к реализации типа.

Устаревшие формы условного владения и записи в `classes.md`, `disposable.md`
и связанных пояснениях приведены к `ensures taken(...)` / `ensures written(...)`
по уже принятой [таблице перехода](../docs/efen/conditions.md#условия-функции-только-requires-и-ensures).
Это синхронизация документации с действующей записью, а не новое решение языка.
Статьи о внешнем коде будут отдельно проверены в группе памяти.

Исправлены записи словаря о правах методов, `thread` и `static`, размеченных
и структурных объединениях. Сохранены адреса переименованных разделов,
проверены ссылки и блоки Markdown. В `types/access-regions.md` добавлен
отсутствовавший заголовок для существующей ссылки на временные значения.

### Вопросы, которые нельзя решить одной редактурой

- В `types/strings.md` изменение строки разрешено только у `var`, а общая
  модель в `types/ownership.md` допускает запись через `let`, если это разрешает
  тип. Требуется подтвердить, является ли ограничение строк отдельным правилом.
  До решения оба правила сохранены в своих документах.
- Пример `TypeContract` в `types/built-in-contracts.md` содержит имена элементов
  `TypeKind` с заглавной буквы, тогда как статья о перечислениях требует строчную.
  Требуется сверить пример с действующей моделью метаданных. Имена не переименованы
  редакторской правкой.

## 1. Типы и данные

| Документ | Статус |
|---|---|
| [types/README.md](../docs/efen/types/README.md) | Проверена |
| [types/access-regions.md](../docs/efen/types/access-regions.md) | Проверена |
| [types/basic-types.md](../docs/efen/types/basic-types.md) | Проверена |
| [types/built-in-contracts.md](../docs/efen/types/built-in-contracts.md) | Проверена |
| [types/collections.md](../docs/efen/types/collections.md) | Проверена |
| [types/constants.md](../docs/efen/types/constants.md) | Проверена |
| [types/dictionaries.md](../docs/efen/types/dictionaries.md) | Проверена |
| [types/enum.md](../docs/efen/types/enum.md) | Проверена |
| [types/function-type.md](../docs/efen/types/function-type.md) | Проверена |
| [types/optional.md](../docs/efen/types/optional.md) | Проверена |
| [types/ownership.md](../docs/efen/types/ownership.md) | Проверена |
| [types/projection.md](../docs/efen/types/projection.md) | Проверена |
| [types/refinement-types.md](../docs/efen/types/refinement-types.md) | Проверена |
| [types/simd.md](../docs/efen/types/simd.md) | Проверена |
| [types/strings.md](../docs/efen/types/strings.md) | Проверена |
| [types/tuples.md](../docs/efen/types/tuples.md) | Проверена |
| [types/type.md](../docs/efen/types/type.md) | Проверена |
| [types/typestate.md](../docs/efen/types/typestate.md) | Проверена |
| [types/value-parameterized-types.md](../docs/efen/types/value-parameterized-types.md) | Проверена |
| [types/variant.md](../docs/efen/types/variant.md) | Проверена |

## 2. Основы и абстракции

| Документ | Статус |
|---|---|
| [README.md](../docs/efen/README.md) | Проверена |
| [abstractions.md](../docs/efen/abstractions.md) | Проверена |
| [classes.md](../docs/efen/classes.md) | Проверена |
| [contracts.md](../docs/efen/contracts.md) | Проверена |
| [disposable.md](../docs/efen/disposable.md) | Проверена |
| [generics.md](../docs/efen/generics.md) | Проверена |
| [glossary.md](../docs/efen/glossary.md) | Проверена |
| [immutability.md](../docs/efen/immutability.md) | Проверена |
| [interfaces.md](../docs/efen/interfaces.md) | Проверена |
| [representations.md](../docs/efen/representations.md) | Проверена |
| [strategies.md](../docs/efen/strategies.md) | Проверена |
| [structs.md](../docs/efen/structs.md) | Проверена |
| [type-aliases.md](../docs/efen/type-aliases.md) | Проверена |

## 3. Выражения, функции и управление выполнением

| Документ | Статус |
|---|---|
| [blocks/README.md](../docs/efen/blocks/README.md) | Ожидает |
| [blocks/guard.md](../docs/efen/blocks/guard.md) | Ожидает |
| [blocks/if.md](../docs/efen/blocks/if.md) | Ожидает |
| [blocks/index.md](../docs/efen/blocks/index.md) | Ожидает |
| [blocks/loops.md](../docs/efen/blocks/loops.md) | Ожидает |
| [blocks/match.md](../docs/efen/blocks/match.md) | Ожидает |
| [blocks/try-catch.md](../docs/efen/blocks/try-catch.md) | Ожидает |
| [closure.md](../docs/efen/closure.md) | Ожидает |
| [comments.md](../docs/efen/comments.md) | Ожидает |
| [destructuring.md](../docs/efen/destructuring.md) | Ожидает |
| [flow.md](../docs/efen/flow.md) | Ожидает |
| [functions.md](../docs/efen/functions.md) | Ожидает |
| [is.md](../docs/efen/is.md) | Ожидает |
| [operators.md](../docs/efen/operators.md) | Ожидает |
| [throws.md](../docs/efen/throws.md) | Ожидает |

## 4. Память, доступ и взаимодействие с внешним кодом

| Документ | Статус |
|---|---|
| [code-regions.md](../docs/efen/code-regions.md) | Ожидает |
| [context-and-effects.md](../docs/efen/context-and-effects.md) | Ожидает |
| [foreign.md](../docs/efen/foreign.md) | Ожидает |
| [memory/README.md](../docs/efen/memory/README.md) | Ожидает |
| [memory/addresses-defects.md](../docs/efen/memory/addresses-defects.md) | Ожидает |
| [memory/addresses.md](../docs/efen/memory/addresses.md) | Ожидает |
| [memory/allocator.md](../docs/efen/memory/allocator.md) | Ожидает |
| [memory/checking-build.md](../docs/efen/memory/checking-build.md) | Ожидает |
| [memory/classes-internal.md](../docs/efen/memory/classes-internal.md) | Ожидает |
| [memory/columnar-layouts.md](../docs/efen/memory/columnar-layouts.md) | Ожидает |
| [memory/examples/README.md](../docs/efen/memory/examples/README.md) | Ожидает |
| [memory/index.md](../docs/efen/memory/index.md) | Ожидает |
| [memory/layout-examples/README.md](../docs/efen/memory/layout-examples/README.md) | Ожидает |
| [memory/layout-examples/array-contracts.md](../docs/efen/memory/layout-examples/array-contracts.md) | Ожидает |
| [memory/layout-examples/chunked-array.md](../docs/efen/memory/layout-examples/chunked-array.md) | Ожидает |
| [memory/layout-examples/contiguous-array.md](../docs/efen/memory/layout-examples/contiguous-array.md) | Ожидает |
| [memory/layout-examples/doubly-linked-array.md](../docs/efen/memory/layout-examples/doubly-linked-array.md) | Ожидает |
| [memory/layout-examples/dynamic-array.md](../docs/efen/memory/layout-examples/dynamic-array.md) | Ожидает |
| [memory/layout-examples/singly-linked-array.md](../docs/efen/memory/layout-examples/singly-linked-array.md) | Ожидает |
| [memory/layout-representations.md](../docs/efen/memory/layout-representations.md) | Ожидает |
| [memory/pointer.md](../docs/efen/memory/pointer.md) | Ожидает |
| [memory/prior-art.md](../docs/efen/memory/prior-art.md) | Ожидает |
| [memory/system.md](../docs/efen/memory/system.md) | Ожидает |
| [memory/viper-proof-model.md](../docs/efen/memory/viper-proof-model.md) | Ожидает |
| [memory/viper-proof-plan.md](../docs/efen/memory/viper-proof-plan.md) | Ожидает |
| [memory/viper-verification-backend.md](../docs/efen/memory/viper-verification-backend.md) | Ожидает |
| [memory.md](../docs/efen/memory.md) | Ожидает |
| [shared.md](../docs/efen/shared.md) | Ожидает |

## 5. Метапрограммирование и расширение языка

| Документ | Статус |
|---|---|
| [aspects/README.md](../docs/efen/aspects/README.md) | Ожидает |
| [aspects/aspect.md](../docs/efen/aspects/aspect.md) | Ожидает |
| [aspects/compile-time/README.md](../docs/efen/aspects/compile-time/README.md) | Ожидает |
| [aspects/compile-time/class.md](../docs/efen/aspects/compile-time/class.md) | Ожидает |
| [aspects/compile-time/index.md](../docs/efen/aspects/compile-time/index.md) | Ожидает |
| [aspects/members-resolving.md](../docs/efen/aspects/members-resolving.md) | Ожидает |
| [aspects/metadata.md](../docs/efen/aspects/metadata.md) | Ожидает |
| [compile-time/README.md](../docs/efen/compile-time/README.md) | Ожидает |
| [compile-time/compiler-plugins.md](../docs/efen/compile-time/compiler-plugins.md) | Ожидает |
| [compile-time/index.md](../docs/efen/compile-time/index.md) | Ожидает |
| [compile-time/metafunctions.md](../docs/efen/compile-time/metafunctions.md) | Ожидает |
| [compile-time/plugins.md](../docs/efen/compile-time/plugins.md) | Ожидает |
| [decorators-examples.md](../docs/efen/decorators-examples.md) | Ожидает |
| [decorators.md](../docs/efen/decorators.md) | Ожидает |

## 6. Сборка, среда выполнения и остальные темы

| Документ | Статус |
|---|---|
| [build-config.md](../docs/efen/build-config.md) | Ожидает |
| [certification.md](../docs/efen/certification.md) | Ожидает |
| [compilation-modes.md](../docs/efen/compilation-modes.md) | Ожидает |
| [conditions.md](../docs/efen/conditions.md) | Ожидает |
| [diagnostic-groups.md](../docs/efen/diagnostic-groups.md) | Ожидает |
| [dialects.md](../docs/efen/dialects.md) | Ожидает |
| [function-call-syntax.md](../docs/efen/function-call-syntax.md) | Ожидает |
| [generators.md](../docs/efen/generators.md) | Ожидает |
| [index.md](../docs/efen/index.md) | Ожидает |
| [layers.md](../docs/efen/layers.md) | Ожидает |
| [packages.md](../docs/efen/packages.md) | Ожидает |
| [philosophy.md](../docs/efen/philosophy.md) | Ожидает |
| [runtime/README.md](../docs/efen/runtime/README.md) | Ожидает |
| [runtime/index.md](../docs/efen/runtime/index.md) | Ожидает |
| [runtime/lang-roles.md](../docs/efen/runtime/lang-roles.md) | Ожидает |
| [runtime/memory.md](../docs/efen/runtime/memory.md) | Ожидает |
| [signing.md](../docs/efen/signing.md) | Ожидает |
| [superpolymorphism.md](../docs/efen/superpolymorphism.md) | Ожидает |
| [tests/README.md](../docs/efen/tests/README.md) | Ожидает |
| [tests/tests.md](../docs/efen/tests/tests.md) | Ожидает |
| [visibility.md](../docs/efen/visibility.md) | Ожидает |
| [сonditional_compilation.md](../docs/efen/сonditional_compilation.md) | Ожидает |

