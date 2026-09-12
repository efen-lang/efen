# Efen

Efen — PHP-совместимый компилируемый язык, в котором классы, стратегии,
представления данных и другие высокоуровневые механизмы могут определяться и
преобразовываться кодом времени компиляции.

Репозиторий сейчас содержит проект языка и примеры. Наличие конструкции в
документации не означает, что она уже реализована компилятором.

## Начать чтение

| Цель | Маршрут |
|---|---|
| Быстро понять язык | [Обзор документации](docs/efen/index.md) → [абстракции](docs/efen/abstractions.md) → [классы](docs/efen/classes.md) |
| Разобраться в типах и памяти | [Типы](docs/efen/types/type.md) → [ownership](docs/efen/types/ownership.md) → [управление памятью](docs/efen/memory/index.md) |
| Понять расширяемость | [Контракты](docs/efen/contracts.md) → [стратегии](docs/efen/strategies.md) → [аспекты](docs/efen/aspects/aspect.md) |
| Писать compile-time код | [Compile-time API](docs/efen/compile-time/index.md) → [метафункции](docs/efen/compile-time/metafunctions.md) → [metadata](docs/efen/aspects/metadata.md) |
| Найти определение термина | [Словарь Efen](docs/efen/glossary.md) |

Полный тематический каталог и дополнительные маршруты находятся в
[индексе документации](docs/efen/index.md).

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

Efen определяет исходную семантику. [Amber](https://github.com/limelight-lang/amber)
задаёт общий HIR, стадии готовности, анализ и границы frontend/backend. Начальная
точка для сопоставления языка с HIR — [путеводитель Amber](https://github.com/limelight-lang/amber/blob/main/design/README.md).

## Источники истины

- Текущая модель языка: [`docs/efen/`](docs/efen/index.md).
- Термины языка: [`docs/efen/glossary.md`](docs/efen/glossary.md).
- Незавершённый аудит документации: [`docs/DOCUMENTATION-AUDIT.md`](docs/DOCUMENTATION-AUDIT.md).
- Мотивация принятых generic-решений и оставшиеся вопросы реализации:
  [`GENERIC-EXTENSIONS-IDEAS.md`](GENERIC-EXTENSIONS-IDEAS.md). Нормативные
  формулировки находятся в связанных из него языковых документах.
- Принятые межрепозиторные решения и план реализации ведутся в Amber:
  [decision log](https://github.com/limelight-lang/amber/blob/main/dev/DECISIONS.md) и
  [plan](https://github.com/limelight-lang/amber/blob/main/dev/PLAN.md).

Историческое обсуждение и review не переопределяют текущие языковые документы.
