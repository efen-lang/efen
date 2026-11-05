# Diagnostic Groups

Система диагностических групп Efen компилятора, вдохновлённая Swift.

## Концепция

Группы диагностик - это **теги**, которые:
- Классифицируют ошибки по категориям
- Позволяют управлять поведением компилятора
- Помогают найти документацию

## Использование в коде

### Одна группа
```cpp
diagnosticEngine.error(loc, "name is both a module and a package")
    .withGroup(DiagnosticGroup::Package);
```

### Несколько групп (как теги)
```cpp
diagnosticEngine.error(loc, "name is both a module and a package")
    .withGroups({DiagnosticGroup::Package, DiagnosticGroup::Declaration});
```

## Вывод компилятора

```
error: 'model' names both module 'model' of this package and package 'model' [#Package] [#Declaration]
 --> server/routes.efen:3:5
  |
3 | use model
  |     ^^^^^
```

## Управление через флаги

Те же уровни задаёт секция `diagnostics` конфигурации сборки; флаги действуют поверх неё. Коды плагинов
компилятора управляются так же ([плагины компилятора](compile-time/compiler-plugins.md#диагностики)).

```bash
# Сделать все ошибки Package критическими
efen build -Werror Package

# Подавить предупреждения о deprecated
efen build -Wno-warn DeprecatedFeature

# Показать группы в выводе (по умолчанию включено)
efen build -print-diagnostic-groups
```

## Доступные группы

### Style diagnostics `S`

Диагностики с кодом `S` задают единый стиль исходного Efen, но не изменяют
грамматику языка. Parser принимает все валидные формы и строит одинаковый HIR,
после чего frontend сообщает отклонение от канонической записи.

По умолчанию диагностика стиля — ошибка, и компиляция останавливается. Сборка
может понизить группу `StyleIssue` до предупреждений; смысл программы от этого
не меняется, потому что форма уже разобрана однозначно.

`S` означает `Style`. Ошибка синтаксиса (`Syntax`) ставится там, где смысл
записи неясен; диагностика стиля — там, где смысл ясен, но запись не
каноническая. Диагностика стиля содержит машинно применимое исправление, когда
переписывание не меняет семантику.

Например, параметры функции можно объявить в заголовке или через `param` в её
теле. Если параметров больше трёх, каноническая запись использует `param`:

```efen
fn combine -> Result {
    param first: Int
    param second: Int
    param third: Int
    param fourth: Int
}
```

Заголовок с четырьмя параметрами остаётся синтаксически допустимым, но получает:

```text
error[S.function-parameter-layout]: functions with more than three parameters use `param` declarations
  help: move the parameters to the beginning of the function body
```

Граница считается по runtime-параметрам функции. Variadic-параметр считается
одним; generic-параметры и неявный receiver в это число не входят.

Семейство `S` не ограничено параметрами функций. Отдельные стабильные правила
могут задавать канонический порядок модификаторов и секций объявления,
расположение переносов и отступов, форму блоков, пробелы, имена, допустимые
сокращения и выбор между несколькими семантически равными написаниями. Каждое
правило имеет собственный код и точное исправление; добавление или изменение
правила относится к версии языка и инструмента форматирования.

### Warnings of the syntax `W.syntax`

Предупреждение синтаксиса — запись, которую разбор читает однозначно, но
которую лучше написать иначе, а исправление решает автор: оно меняет не только
форму. Компиляция не останавливается. Пример — `W.syntax.doc-comment-expected`:
`//` прямо над объявлением; исправление `///` переносит текст в опубликованную
документацию ([комментарии](comments.md#проверка-компилятора)). Поэтому это не
диагностика стиля `S`, чьё исправление смысла не меняет.

### Warnings of the access rights `W.access`

Предупреждение прав — право в сигнатуре шире того, что делает тело. Пример —
`W.access.edit-suffices`: тело с параметром `mut` или метод `mut fn` не
перемещает и не уничтожает ни одного существующего слота и не делает перехода
состояния. Предупреждения нет у `open fn` и `override`, у реализации метода контракта или interface и у функции, которую кладут в тип функции с параметром `mut`. Исправление — право
`edit` или `edit fn` ([ownership](types/ownership.md#что-делает-ссылку-недействительной),
[доступ метода к self](contracts.md#доступ-метода-к-self)). Исправление решает
автор: оно меняет обещание вызывающим.

```text
warning[W.access.edit-suffices]: `list` keeps its existing slots; mark it `edit`
```

### Заметки и группа `Proof`

Заметка (notice) — уровень ниже предупреждения: компиляция не останавливается, а
сообщение говорит о том, что компилятор не смог установить. Группа `Proof` —
условия, которые сборка не доказала ([условия функций](conditions.md#обычная-сборка-и-диагностики)):

```text
notice: `ensures` of `span` is not proved [#Proof]
```

В группе и заметка `efen.unchecked`: строка `requires` или `ensures`, которую программа не может проверить при
выполнении, с причиной ([условия функций](conditions.md#обычная-сборка-и-диагностики)).

Заметку поднимают до предупреждения или ошибки флагом группы, как и любую
диагностику:

```bash
efen build -Wwarn Proof     # заметки Proof становятся предупреждениями
efen build -Werror Proof    # и ошибками
```

Арифметика самого условия подчиняется тому же правилу ([арифметика условий](conditions.md#арифметика-и-частичные-операции)):
переполнение, деление на ноль или индекс вне границ, которые видны точно, — ошибка; те, что FLOW не смог исключить, —
заметка `Proof`, и условие проверяется при выполнении вместе с этой операцией.

### Ошибки условий и объявлений

Правило одно ([условия значений и `invariants`](conditions.md#условия-значений-и-invariants)): условие на одно
значение — `{ }` в конце его строки-объявления, условие на несколько значений — строка `invariants`, у функции —
только `requires` и `ensures`. Каждое нарушение — ошибка с подсказкой, куда перенести строку. Исправление не
машинное: перенос меняет время проверки ([когда условие проверяется](conditions.md#когда-условие-проверяется)),
поэтому это не диагностика стиля `S`. Группы — `Declaration` и `Proof`.

| Код | Когда | Подсказка |
|---|---|---|
| `condition.reads-other-state` | `{ }` у строки читает что-то кроме собственной памяти `value` и констант | перенести строку в `invariants` |
| `condition.belongs-to-line` | строка `invariants` читает только собственную память одного имени, у которого в этом теле своя строка-объявление | перенести её к этой строке как `{ }` |
| `condition.second-invariants` | второй блок `invariants` в одном теле | соединить строки в один блок |
| `condition.function-block` | `{ }` прямо за типом параметра, результата или у строки `param` | строка `requires` или `ensures` |
| `generic.own-parameter-requires` | `requires T conforms C` про параметр `T`, которого объявила эта же функция | `<T: C>` или `generic T: C` ([ограничения параметров](generics.md#ограничения-параметров)) |
| `access.write-without-mark` | тело пишет параметр, `self` или окружение `in Env`, у которых нет пометки права, то есть `read` | нужное слово: `edit`, `mut`, `own`, `take` |

```text
error[condition.reads-other-state]: the condition of `head` reads `value.next`, which is written without writing `head`
  --> mm/list.efen:4:28
  help: move the line to `invariants { }` of `List`

error[condition.belongs-to-line]: line 2 of `invariants` reads only `capacity`
  --> std/ring.efen:9:9
  help: write it at the declaration: `let capacity: Int { value > 0 }`

error[access.write-without-mark]: `append` writes `self`, but the method has no access mark and is `read fn`
  --> std/queue.efen:12:5
  help: mark the method `edit fn` or `mut fn`
```

Строку `invariants` диагностика называет номером и текстом: имени у неё нет.

### Группа `Trust`

Заметка `efen.trust` — пакет рискованный: в нём есть места, которые сборка принимает на веру, а не доказывает
(`@asm`, `@platform`, `@abi(c)`, функция библиотеки C, `thread var x: own T`, приведение адреса к элементу набора;
[кому доступно доверие](memory/system.md#кому-доступно-доверие)). Одна заметка на пакет, у его первого такого места.
`-Wno-warn Trust` её убирает, `-Werror Trust` делает ошибкой.

### Module Groups (кто генерирует ошибку)
- `Package` - ошибки системы package
- `Module` - ошибки модульной системы
- `Parser` - ошибки парсера
- `Lexer` - ошибки лексера
- `SemanticAnalysis` - семантический анализ
- `TypeChecker` - проверка типов
- `CodeGen` - генерация кода
- `Linker` - линковка

### Feature Groups (категории проблем)
- `Syntax` - синтаксические ошибки
- `Declaration` - ошибки объявлений
- `TypeConformance` - несоответствие типов
- `AccessControl` - контроль доступа
- `Lifetime` - время жизни объектов
- `DeprecatedFeature` - устаревшие возможности
- `StyleIssue` - диагностики стиля семейства `S`, по умолчанию ошибки
- `Performance` - производительность
- `Layer` - нарушения границ слоёв: `uses`, `exposes`, `provides`
- `Proof` - недоказанные условия `requires`/`ensures`/`invariant`, по умолчанию заметки

## Примеры

### Package Declaration Error
```cpp
diagnosticEngine.error(loc, "duplicate package declaration")
    .withGroups({DiagnosticGroup::Package, DiagnosticGroup::Declaration})
    .withLabel(prevLoc, "previous declaration here");
```

Вывод:
```
error: duplicate package declaration [#Package] [#Declaration]
 --> src/main.efen:10:9
```

### Deprecated Feature Warning
```cpp
diagnosticEngine.warning(loc, "old syntax is deprecated")
    .withGroups({DiagnosticGroup::Parser, DiagnosticGroup::DeprecatedFeature})
    .withSuggestion("use new syntax instead");
```

Вывод:
```
warning: old syntax is deprecated [#Parser] [#DeprecatedFeature]
 --> src/old.efen:5:1
```
