# Документация Efen

[Корень репозитория](../../README.md) · [Словарь](glossary.md) · [Amber HIR](https://github.com/limelight-lang/amber/blob/main/design/README.md)

Efen — PHP-совместимый компилируемый язык с программируемыми compile-time
абстракциями. Эти документы описывают проект языка; они не подтверждают наличие
готовой реализации компилятора.

## Выберите маршрут

| Если нужно… | Читайте по порядку |
|---|---|
| Понять основную модель | [Абстракции](abstractions.md) → [типы](types/type.md) → [функции](functions.md) → [классы](classes.md) |
| Писать обычный Efen-код | [Вызовы](function-call-syntax.md) → [управляющие конструкции](blocks/index.md) → [коллекции](types/collections.md) → [ошибки](throws.md) |
| Расширять чужие типы | [Контракты](contracts.md) → [interfaces](interfaces.md) → [стратегии](strategies.md) → [разрешение членов](aspects/members-resolving.md) |
| Писать metaprogramming | [Compile-time API](compile-time/index.md) → [метафункции](compile-time/metafunctions.md) → [аспекты](aspects/aspect.md) → [metadata](aspects/metadata.md) |
| Разобраться в памяти | [Владение](types/ownership.md) → [представления](representations.md) → [обзор памяти](memory/index.md) → [компоновка и дескрипторы](memory/addresses.md) → [примеры](memory/layout-examples/) |
| Понять зависимости приложения | [Пакеты](packages.md) → [видимость](visibility.md) → [контексты и эффекты](context-and-effects.md) → [слои](layers.md) |
| Сопоставить язык с компилятором | [Режимы компиляции](compilation-modes.md) → [диалекты](dialects.md) → [Amber architecture](https://github.com/limelight-lang/amber/blob/main/design/architecture/README.md) |

## Карта понятий

```text
source syntax
├─ values and control flow
│  ├─ types, functions, closures
│  └─ if / match / loops / flow / generators
├─ abstraction model
│  ├─ contract ──explicit from──▶ interface
│  ├─ class / struct
│  └─ strategy / aspect / attribute
├─ static environment
│  ├─ package / visibility / layer
│  └─ context / effect / throws / region
└─ physical model
   ├─ ownership / origin / take
   └─ representation / layout / population
```

## Лексическое правило имён

Регистр первой буквы является частью грамматики и определяет вид имени:

- с заглавной буквы начинаются типы, состояния, populations `set` и контексты:
  `String`, `Point`, `Open`, `Entries`, `Logger`;
- со строчной буквы начинаются значения, функции, поля и варианты enum:
  `count`, `saveUser`, `width`, `north`.

После `%` действует то же правило: `%Logger` обозначает тип эффекта или
контракта, `%db` — поле активного контекста. Имя типа со строчной буквы или имя
варианта enum с заглавной является ошибкой компиляции, а не стилевым
предупреждением.

## Язык выражений и управление потоком

| Тема | Документы |
|---|---|
| Философия и канонический синтаксис | [Философия языка](philosophy.md) |
| Функции и вызовы | [Функции](functions.md), [синтаксис вызова](function-call-syntax.md), [function type](types/function-type.md) |
| Замыкания и генераторы | [Замыкания](closure.md), [генераторы](generators.md), [flow](flow.md) |
| Ветвления и циклы | [Control flow](blocks/index.md), [`is`](is.md), [деструктуризация](destructuring.md) |
| Ошибки и гарантии областей | [`throws`](throws.md), [try/catch](blocks/try-catch.md), [code regions](code-regions.md), [guard](blocks/guard.md) |
| Операторы и исходный текст | [Операторы](operators.md), [комментарии](comments.md), [conditional compilation](сonditional_compilation.md) |

## Типы и данные

| Тема | Документы |
|---|---|
| Основы типов | [Типы](types/type.md), [константы](types/constants.md), [алиасы](type-aliases.md), [refinement types](types/refinement-types.md) |
| Составные значения | [Tuple](types/tuples.md), [enum](types/enum.md), [optional](types/optional.md), [проекции](types/projection.md) |
| Коллекции и строки | [Коллекции](types/collections.md), [словари](types/dictionaries.md), [строки](types/strings.md) |
| Generics | [Generics](generics.md), [built-in contracts](types/built-in-contracts.md) |
| Состояния и ресурсы | [Typestate](types/typestate.md), [ownership](types/ownership.md), [disposable](disposable.md) |
| Проверка программ | [Тесты и failure-сценарии](tests/tests.md), [группы диагностик](diagnostic-groups.md) |

## Абстракции и расширяемость

| Тема | Документы |
|---|---|
| Общая модель | [Управляемые абстракции](abstractions.md), [классы](classes.md), [структуры](structs.md) |
| Контракты и интерфейсы | [Контракты](contracts.md), [interfaces](interfaces.md), [superpolymorphism](superpolymorphism.md) |
| Поведение без изменения типа | [Стратегии](strategies.md), [`StrategySelector`](strategies.md#правила-выбора-стратегии) |
| Преобразование деклараций | [Аспекты](aspects/aspect.md), [построение класса](aspects/compile-time/class.md), [member resolver](aspects/members-resolving.md) |
| Атрибуты и metadata | [Metadata](aspects/metadata.md), [декораторы](decorators.md), [примеры декораторов](decorators-examples.md) |

## Модули, зависимости и эффекты

| Тема | Документы |
|---|---|
| Поставка и имена | [Пакеты и модули](packages.md), [видимость](visibility.md) |
| Архитектурные границы | [Слои](layers.md), [группы диагностик](diagnostic-groups.md) |
| Ambient dependencies | [Контексты и эффекты](context-and-effects.md), [`without Context`](context-and-effects.md) |
| Исключения | [`throws`, `MustHandle`, `nothrows`](throws.md) |

## Ownership, memory и layout

Начинать этот раздел лучше с [memory guide](memory/index.md), а не с отдельных
примеров allocator.

| Уровень | Документы |
|---|---|
| Права и время жизни | [Ownership, borrow, origin и `take`](types/ownership.md) |
| Общая модель памяти | [Обзор](memory.md), затем тематический [memory guide](memory/index.md) |
| Логический тип и физическая форма | [Representations](representations.md) |
| Дескрипторы памяти и зависимые адреса | [Компоновка](memory/addresses.md), [примеры](memory/layout-examples/), [исторический разбор дефектов](memory/addresses-defects.md), [сравнение с другими системами](memory/prior-art.md) |
| Physical storage | [Columnar layouts](memory/columnar-layouts.md), [варианты representation](memory/layout-representations.md) |
| Verification boundary | [Efen → Viper](memory/viper-verification-backend.md) |
| Исторические низкоуровневые наброски | [Allocator](memory/allocator.md), [class internals](memory/classes-internal.md) |

`Layout<T>` и dependent types остаются отдельной отложенной темой. Документы о
Viper задают проект proof boundary, но не являются свидетельством выполненного
machine proof.

## Compile-time и toolchain

| Тема | Документы |
|---|---|
| API и generated HIR | [Compile-time API](compile-time/index.md), [метафункции](compile-time/metafunctions.md) |
| Конфигурация сборки | [Режимы компиляции](compilation-modes.md), [diagnostic groups](diagnostic-groups.md) |
| Другие frontend-языки | [Диалекты](dialects.md) |
| Runtime-facing API | [Runtime index](runtime/index.md), [runtime memory](runtime/memory.md) |
| Тестовые конструкции | [Tests](tests/tests.md) |
| Общий HIR и стадии | [Amber design](https://github.com/limelight-lang/amber/blob/main/design/README.md), [Amber glossary](https://github.com/limelight-lang/amber/blob/main/design/glossary.md) |

## Где искать ответ

| Вопрос | Источник истины |
|---|---|
| Как конструкция Efen ведёт себя сейчас? | Тематический документ в `docs/efen/` |
| Что означает термин? | [Словарь Efen](glossary.md) |
| Почему решение принято или отменено? | [Amber decision log](https://github.com/limelight-lang/amber/blob/main/dev/DECISIONS.md) |
| Что ещё предстоит спроектировать или реализовать? | [Amber plan](https://github.com/limelight-lang/amber/blob/main/dev/PLAN.md) и явно открытые разделы тематических документов |
| Как семантика хранится в HIR? | [Amber HIR guide](https://github.com/limelight-lang/amber/blob/main/design/hir/README.md) |
| Это уже работает в компиляторе? | Нужны код и runtime/compiler tests; одна документация этого не доказывает |
