# Projection Types

## 1. Определение

**Projection** — это тип-представление поверх существующей структуры.

Projection:

- предоставляет доступ только к выбранным полям;
- может ослаблять nullability и доступ (read/write);
- **бинарно совместим** с базовой структурой;
- является **отдельным типом** для системы типов.
- может быть частью refinement types.

Projection — это *компиляторный view* на один и тот же участок памяти.

---

## 2. Цели

- Безопасные стадии **инициализации** (ctor) и **разрушения** (dtor).
- Ограничение видимости: передать только часть полей.
- Работа с полями, которые временно могут быть `null`.
- Низкоуровневые оптимизации без копирования памяти.

---

## 3. Синтаксис

### 3.1. Объявление

```efen
projection <Name> for <BaseType> {
    let name: <Type>
}
```

Проекция может быть определена прямо внутри структуры или класса:

```efen
struct MyStruct {
    private let id:    Int;
    private let name:  String cap read;
    private let flags: UInt32;

    projection Public {
        public let id;
        public let name;
        private let ptr;
    }

    projection Ctor {
        let id: Optional;
        let name: Optional;
    }
}
```

Использование:

```efen
let view = MyStruct::Public(...);
```

---

## 4. Примеры


