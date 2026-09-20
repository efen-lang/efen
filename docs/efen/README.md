# Документация Efen

[Корень репозитория](../../README.md) · [Словарь](glossary.md) · [Amber HIR](https://github.com/efen-lang/amber/blob/main/design/README.md)

Efen — компилируемый язык с программируемыми compile-time абстракциями. Эта
документация описывает проект языка: наличие конструкции в ней не означает, что
компилятор уже её реализует.

## Начните с маршрута

| Цель | Читайте по порядку |
|---|---|
| Понять модель языка | [Абстракции](abstractions.md) → [типы и данные](types/README.md) → [функции](functions.md) → [классы](classes.md) |
| Написать обычный код | [Философия и синтаксис](philosophy.md) → [вызовы](function-call-syntax.md) → [управляющие конструкции](blocks/README.md) → [ошибки](throws.md) |
| Работать с данными и ресурсами | [Типы и данные](types/README.md) → [ownership](types/ownership.md) → [memory guide](memory/README.md) |
| Расширить поведение типа | [Контракты](contracts.md) → [interfaces](interfaces.md) → [стратегии](strategies.md) |
| Писать метапрограммирование | [Аспекты](aspects/README.md) → [Compile-time API](compile-time/README.md) → [метафункции](compile-time/metafunctions.md) |
| Понять toolchain | [Режимы компиляции](compilation-modes.md) → [диалекты](dialects.md) → [Amber](https://github.com/efen-lang/amber/blob/main/design/README.md) |
| Понять модули и архитектурные границы | [Пакеты](packages.md) → [видимость](visibility.md) → [слои](layers.md) |
| Работать с ambient-зависимостями и ошибками | [Контексты и эффекты](context-and-effects.md) → [`throws`](throws.md) → [code regions](code-regions.md) |

## Карта разделов

| Раздел | Что внутри |
|---|---|
| [Выражения и поток](blocks/README.md) | [функции](functions.md), [вызовы](function-call-syntax.md), [замыкания](closure.md), [генераторы](generators.md), [flow](flow.md), [`is`](is.md), [деструктуризация](destructuring.md), [операторы](operators.md), [комментарии](comments.md), [условная компиляция](сonditional_compilation.md) |
| [Типы и данные](types/README.md) | Формы данных, коллекции, generics, ownership и typestate |
| [Абстракции](abstractions.md) | [классы](classes.md), [структуры](structs.md), [контракты](contracts.md), [interfaces](interfaces.md), [superpolymorphism](superpolymorphism.md) |
| [Расширение поведения](contracts.md) | Контракты, interfaces, superpolymorphism и стратегии |
| [Метапрограммирование](aspects/README.md) | Аспекты, построение класса, member resolver, metadata, декораторы и Compile-time API |
| [Модули и архитектура](packages.md) | Пакеты, модули, пространства имён, видимость и слои |
| [Контексты, эффекты и ошибки](context-and-effects.md) | Ambient-зависимости, `throws`, `try/catch`, `guard` и code regions |
| [Память и представление](memory/README.md) | Владение, representation, layout, примеры и proof boundary |
| [Toolchain и интеграция](compile-time/README.md) | Режимы компиляции, диалекты, runtime API и Amber |

## Ориентиры и границы

- [Словарь](glossary.md) определяет термины; его стоит предпочесть совпадению
  слов в старом примере.
- [Философия языка](philosophy.md) объясняет канонический синтаксис. Первую
  букву имени регулирует грамматика: типы, состояния, populations `set` и
  контексты начинаются с заглавной; значения, функции, поля, значения `enum`
  и cases `variant` — со строчной. Неявный receiver называется `self`, а его
  лексический тип — `Self`.
- [Исследования](../research/README.md) — сравнительные и внешние материалы;
  они ненормативны.
- Принятые межрепозиторные решения и план реализации ведутся в Amber:
  [decision log](https://github.com/efen-lang/amber/blob/main/dev/DECISIONS.md)
  и [plan](https://github.com/efen-lang/amber/blob/main/dev/PLAN.md).
- Актуальная очередь ещё не решённых тем поверхности Efen находится в
  [`dev/language-design-questions.md`](../../dev/language-design-questions.md).
  Историческое обсуждение и review не переопределяют текущие языковые документы.

## Как проверить утверждение

| Вопрос | Источник |
|---|---|
| Как конструкция должна вести себя? | Тематический документ в `docs/efen/` |
| Что означает термин? | [Словарь](glossary.md) |
| Почему решение принято или отменено? | [Amber decision log](https://github.com/efen-lang/amber/blob/main/dev/DECISIONS.md) |
| Что ещё нужно спроектировать или реализовать? | [Очередь вопросов Efen](../../dev/language-design-questions.md) и [Amber plan](https://github.com/efen-lang/amber/blob/main/dev/PLAN.md) |
| Как семантика хранится в HIR? | [Amber HIR guide](https://github.com/efen-lang/amber/blob/main/design/hir/README.md) |
| Реализовано ли это? | Нужны код и runtime/compiler tests; одной документации недостаточно |
