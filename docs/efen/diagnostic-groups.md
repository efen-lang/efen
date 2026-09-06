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
- `StyleIssue` - стиль кода
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
