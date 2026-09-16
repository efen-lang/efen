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
diagnosticEngine.error(loc, "package already declared")
    .withGroup(DiagnosticGroup::Package);
```

### Несколько групп (как теги)
```cpp
diagnosticEngine.error(loc, "package already declared")
    .withGroups({DiagnosticGroup::Package, DiagnosticGroup::Declaration});
```

## Вывод компилятора

```
error: package 'MyPackage' is already declared in namespace 'App' [#Package] [#Declaration]
 --> src/main.efen:5:9
  |
5 | package MyPackage;
  |         ^^^^^^^^^
```

## Управление через флаги

```bash
# Сделать все ошибки Package критическими
efenc -Werror Package main.efen

# Подавить предупреждения о deprecated
efenc -Wno-warn DeprecatedFeature main.efen

# Показать группы в выводе (по умолчанию включено)
efenc -print-diagnostic-groups main.efen
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
