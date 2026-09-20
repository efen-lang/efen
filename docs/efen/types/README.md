# Типы и данные

[Документация](../README.md) · [Словарь](../glossary.md) · [Владение и память](../memory/README.md)

Этот раздел описывает типы Efen: от объявления имени и формы значения до
владения, состояний и generic-параметров. Сначала прочитайте основы, затем —
только нужную форму данных или ограничение.

## Начать здесь

1. [Алиасы и новые типы](type.md) — номинальные и opaque-типы.
2. [Контракты](../contracts.md) — ограничения, которым может соответствовать
   тип.
3. [Generics](../generics.md) — параметры типов и вывод.
4. [Владение, borrow, origin и `take`](ownership.md) — права на значение и
   время его жизни.

## Формы данных

| Нужна форма | Документ |
|---|---|
| Фиксированное составное значение | [Tuple](tuples.md) |
| Набор именованных вариантов | [enum](enum.md) |
| Дизъюнкция форм значения | [variant](variant.md) |
| Значение, которое может отсутствовать | [optional](optional.md) |
| Значение с дополнительным предикатом | [refinement types](refinement-types.md) |
| Вид части или зависимого свойства | [проекции](projection.md) |
| Функция как значение | [function type](function-type.md) |

## Библиотечные и generic-типы

| Тема | Документ |
|---|---|
| Коллекции | [collections](collections.md) |
| Словари | [dictionaries](dictionaries.md) |
| Строки | [strings](strings.md) |
| Константы времени компиляции | [constants](constants.md) |
| Типы с параметрами-значениями | [value-parameterized types](value-parameterized-types.md) |
| Встроенные контракты | [built-in contracts](built-in-contracts.md) |

## Состояние и ресурсы

- [Typestate](typestate.md) описывает допустимые состояния значения.
- [Ownership](ownership.md) определяет владение, заимствования, `origin` и
  передачу через `take`.
- [Disposable](../disposable.md) описывает освобождаемые ресурсы.
- [Memory guide](../memory/README.md) продолжает маршрут, когда важны
  представление и физическая компоновка.
