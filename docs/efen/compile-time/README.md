# Метапрограммирование и Compile-time API

[Документация](../README.md) · [Метапрограммирование](../aspects/README.md) · [Amber HIR](https://github.com/efen-lang/amber/blob/main/design/README.md)

Compile-time API — часть метапрограммирования Efen: он позволяет читать и
преобразовывать разрешённый HIR. Модель самого HIR и его стадий ведётся в Amber.

## Метапрограммирование

| Тема | Документ |
|---|---|
| API компилятора и generated HIR | [Compile-time API](index.md) |
| Вычисления времени компиляции | [Метафункции](metafunctions.md) |
| Преобразование деклараций | [Аспекты](../aspects/README.md) |
| Декларативные данные | [Metadata и декораторы](../aspects/metadata.md) |

## Toolchain и интеграция

| Тема | Документ |
|---|---|
| Режимы сборки и диагностики | [Режимы компиляции](../compilation-modes.md), [группы диагностик](../diagnostic-groups.md) |
| Другие frontend-языки | [Диалекты](../dialects.md) |
| Runtime-facing API | [Runtime](../runtime/README.md) |

Свойства HIR, scheduler и backend-граничницы не дублируются здесь: для них
используйте [Amber design](https://github.com/efen-lang/amber/blob/main/design/README.md).
