# Efen

Efen — компилируемый язык, в котором классы, стратегии,
представления данных и другие высокоуровневые механизмы могут определяться и
преобразовываться кодом времени компиляции.

Репозиторий сейчас содержит проект языка и примеры. Наличие конструкции в
документации не означает, что она уже реализована компилятором.

## Начать чтение

| Цель | Маршрут |
|---|---|
| Быстро понять язык | [Карта документации](docs/efen/README.md) → [абстракции](docs/efen/abstractions.md) → [классы](docs/efen/classes.md) |
| Разобраться в типах и памяти | [Типы и данные](docs/efen/types/README.md) → [ownership](docs/efen/types/ownership.md) → [управление памятью](docs/efen/memory/README.md) |
| Понять расширяемость | [Контракты](docs/efen/contracts.md) → [расширяемость](docs/efen/aspects/README.md) → [Compile-time API](docs/efen/compile-time/README.md) |
| Писать compile-time код | [Compile-time и toolchain](docs/efen/compile-time/README.md) → [метафункции](docs/efen/compile-time/metafunctions.md) → [metadata](docs/efen/aspects/metadata.md) |
| Найти определение термина | [Словарь Efen](docs/efen/glossary.md) |
| Понять принципы синтаксиса | [Философия языка](docs/efen/philosophy.md) |
| Читать внешние исследования | [Исследования](docs/research/README.md) |

Полный тематический каталог и дополнительные маршруты находятся в
[карте документации](docs/efen/README.md).

## Место Efen в toolchain

```text
Efen source
    ↓ frontend
Amber HIR
    ↓ analysis and transformations
backend profile
    ├─ MLIR / LLVM
    ├─ Cranelift
    └─ other compatible backends
```

Efen определяет исходную семантику. [Amber](https://github.com/efen-lang/amber)
задаёт общий HIR, стадии готовности, анализ и границы frontend/backend. Начальная
точка для сопоставления языка с HIR — [путеводитель Amber](https://github.com/efen-lang/amber/blob/main/design/README.md).

## Источники истины

- Текущая модель языка: [`docs/efen/`](docs/efen/README.md).
- Термины языка: [`docs/efen/glossary.md`](docs/efen/glossary.md).
- Принятые межрепозиторные решения и план реализации ведутся в Amber:
  [decision log](https://github.com/efen-lang/amber/blob/main/dev/DECISIONS.md) и
  [plan](https://github.com/efen-lang/amber/blob/main/dev/PLAN.md).
- Актуальная очередь ещё не решённых вопросов поверхности Efen ведётся в
  [`dev/language-design-questions.md`](dev/language-design-questions.md); пометка
  «решено» у Q01–Q55 закрывает сформулированные решения; следующая очередь
  содержит ещё не оформленные темы аудита.

Историческое обсуждение и review не переопределяют текущие языковые документы.
