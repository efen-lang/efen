# Compile-time и toolchain

[Документация](../README.md) · [Расширяемость](../aspects/README.md) · [Amber HIR](https://github.com/efen-lang/amber/blob/main/design/README.md)

Этот раздел отделяет пользовательскую семантику Efen от работы компилятора.
Compile-time API позволяет читать и преобразовывать разрешённый HIR; модель
самого HIR и его стадий ведётся в Amber.

| Тема | Документ |
|---|---|
| API компилятора и generated HIR | [Compile-time API](index.md) |
| Вычисления времени компиляции | [Метафункции](metafunctions.md) |
| Преобразование деклараций | [Расширяемость и аспекты](../aspects/README.md) |
| Режимы сборки и диагностики | [Режимы компиляции](../compilation-modes.md), [группы диагностик](../diagnostic-groups.md) |
| Другие frontend-языки | [Диалекты](../dialects.md) |
| Runtime-facing API | [Runtime](../runtime/README.md) |

Свойства HIR, scheduler и backend-граничницы не дублируются здесь: для них
используйте [Amber design](https://github.com/efen-lang/amber/blob/main/design/README.md).
