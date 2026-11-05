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

Завершить раздел «Типы и данные», затем перейти к основам и абстракциям.
Проверены 10 из 112 статей; остальные правки в разделе типов пока проходят проверку.
Определение контракта и связанные термины в словаре исправляются вместе с типами.

## 1. Типы и данные

| Документ | Статус |
|---|---|
| [types/README.md](../docs/efen/types/README.md) | Проверена |
| [types/access-regions.md](../docs/efen/types/access-regions.md) | В работе |
| [types/basic-types.md](../docs/efen/types/basic-types.md) | Проверена |
| [types/built-in-contracts.md](../docs/efen/types/built-in-contracts.md) | В работе |
| [types/collections.md](../docs/efen/types/collections.md) | В работе |
| [types/constants.md](../docs/efen/types/constants.md) | В работе |
| [types/dictionaries.md](../docs/efen/types/dictionaries.md) | В работе |
| [types/enum.md](../docs/efen/types/enum.md) | Проверена |
| [types/function-type.md](../docs/efen/types/function-type.md) | Проверена |
| [types/optional.md](../docs/efen/types/optional.md) | В работе |
| [types/ownership.md](../docs/efen/types/ownership.md) | В работе |
| [types/projection.md](../docs/efen/types/projection.md) | Проверена |
| [types/refinement-types.md](../docs/efen/types/refinement-types.md) | Проверена |
| [types/simd.md](../docs/efen/types/simd.md) | В работе |
| [types/strings.md](../docs/efen/types/strings.md) | В работе |
| [types/tuples.md](../docs/efen/types/tuples.md) | Проверена |
| [types/type.md](../docs/efen/types/type.md) | Проверена |
| [types/typestate.md](../docs/efen/types/typestate.md) | В работе |
| [types/value-parameterized-types.md](../docs/efen/types/value-parameterized-types.md) | Проверена |
| [types/variant.md](../docs/efen/types/variant.md) | Проверена |

## 2. Основы и абстракции

| Документ | Статус |
|---|---|
| [README.md](../docs/efen/README.md) | Ожидает |
| [abstractions.md](../docs/efen/abstractions.md) | Ожидает |
| [classes.md](../docs/efen/classes.md) | Ожидает |
| [contracts.md](../docs/efen/contracts.md) | В работе |
| [disposable.md](../docs/efen/disposable.md) | Ожидает |
| [generics.md](../docs/efen/generics.md) | Ожидает |
| [glossary.md](../docs/efen/glossary.md) | В работе |
| [immutability.md](../docs/efen/immutability.md) | Ожидает |
| [interfaces.md](../docs/efen/interfaces.md) | Ожидает |
| [representations.md](../docs/efen/representations.md) | Ожидает |
| [strategies.md](../docs/efen/strategies.md) | Ожидает |
| [structs.md](../docs/efen/structs.md) | Ожидает |
| [type-aliases.md](../docs/efen/type-aliases.md) | Ожидает |

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

