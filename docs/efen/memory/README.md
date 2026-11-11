# Память, представление и layout

[Документация](../README.md) · [Типы и данные](../types/README.md) · [Словарь](../glossary.md)

Этот раздел начинается с прав на значение, затем отделяет логическую форму от
физического хранения. Документы о proof-модели и внешних системах фиксируют
границы проекта, а не выполненный machine proof.

## Маршрут

Все правила доступа к памяти сведены в одну таблицу: [правила доступа к памяти](memory-rules.md). Статьи ниже их
вводят и объясняют.

1. [Ownership, borrow, origin и `take`](../types/ownership.md).
2. [Representations](../representations.md) — логический тип и физическая
   форма.
3. [Layout и описание памяти](layout.md), [модели поведения](../models.md).
4. [Компоновка и дескрипторы](addresses.md) — адреса, `Target`, `Self` и
   безопасные операции.
5. [Примеры компоновки](layout-examples/README.md) — цельные реализации
   структур данных.

## Карта материалов

| Назначение | Документ |
|---|---|
| Общая модель управления памятью | [Обзор](../memory.md), [тематическая модель](index.md) |
| Layout и удержания | [Layout](layout.md), [модели поведения](../models.md) |
| Дескрипторы, адреса и layout | [addresses](addresses.md), [разбор прежних дефектов](addresses-defects.md) |
| Физическое хранение | [колоночные layout](columnar-layouts.md), [варианты representation](layout-representations.md) |
| Доказательная граница | [условия и доказательства](../conditions.md) |
| Проверка при выполнении | [проверочная сборка](checking-build.md) |
| Сравнение и исторический контекст | [prior art](prior-art.md), [allocator](allocator.md), [class internals](classes-internal.md) |
| Самостоятельные примеры | [примеры](examples/README.md), [layout examples](layout-examples/README.md) |

`allocator.md` и `classes-internal.md` — исторические низкоуровневые наброски;
они не заменяют правила ownership и layout выше.

---

[Документация](../README.md) · [Контракты](../contracts.md) · [Runtime языка Efen](../runtime/README.md) · [Память](README.md)
