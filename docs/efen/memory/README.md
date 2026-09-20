# Память, представление и layout

[Документация](../README.md) · [Типы и данные](../types/README.md) · [Словарь](../glossary.md)

Этот раздел начинается с прав на значение, затем отделяет логическую форму от
физического хранения. Документы о proof-модели и внешних системах фиксируют
границы проекта, а не выполненный machine proof.

## Маршрут

1. [Ownership, borrow, origin и `take`](../types/ownership.md).
2. [Representations](../representations.md) — логический тип и физическая
   форма.
3. [Компоновка и дескрипторы](addresses.md) — адреса, `Target`, `Self` и
   безопасные операции.
4. [Примеры компоновки](layout-examples/README.md) — цельные реализации
   структур данных.

## Карта материалов

| Назначение | Документ |
|---|---|
| Общая модель управления памятью | [Обзор](../memory.md), [тематическая модель](index.md) |
| Дескрипторы, адреса и layout | [addresses](addresses.md), [разбор прежних дефектов](addresses-defects.md) |
| Физическое хранение | [колоночные layout](columnar-layouts.md), [варианты representation](layout-representations.md) |
| Доказательная граница | [Efen → Viper](viper-verification-backend.md), [план](viper-proof-plan.md), [proof model](viper-proof-model.md) |
| Сравнение и исторический контекст | [prior art](prior-art.md), [allocator](allocator.md), [class internals](classes-internal.md) |
| Самостоятельные примеры | [примеры](examples/README.md), [layout examples](layout-examples/README.md) |

`allocator.md` и `classes-internal.md` — исторические низкоуровневые наброски;
они не заменяют правила ownership и layout выше.
