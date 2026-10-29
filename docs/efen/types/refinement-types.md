# Refinement Types

## Введение

**Refinement types** (уточняющие типы) - это система типов, 
которая позволяет добавлять логические предикаты к базовым типам для более точной спецификации допустимых значений.

### Основная идея

Обычный тип описывает множество значений (например, `Int` = все целые числа), 
а `refinement type` сужает это множество через предикат:

```efen
// Обычный тип
var age: Int  // Любое целое число

// Direct predicate refinement
var age: Int { value >= 0 && value <= 150 }  // Только валидные возраста
var email: String { isValidEmail(value) }  // Только валидные email адреса

// Type definition style
type Nat: Int { value >= 0 }
type Email: String { isValidEmail(value) }

let age: Nat = 25  // age гарантированно >= 0
let email: Email = "email@dot.com" // email гарантированно валиден
```

### Зачем нужны Refinement Types?

1. **Статическая верификация** - проверка ограничений на этапе компиляции
2. **Отсутствие null checks** - `type NonNull<T>: T { value != null }`
3. **Безопасность индексации** - `type ValidIndex: Int { value >= 0 && value < len(array) }`
4. **Бизнес-логика в типах** - `type Email: String { isValidEmail(value) }`
5. **Контракты без runtime overhead** - проверки на compile-time когда возможно

## Синтаксис

### Определение Refinement Type

Для определения нового уточняющего типа используется ключевое слово `type`.
Прозрачные алиасы объявляются отдельным словом `alias`.

```efen
type Name: BaseType { predicate }
```

**Компоненты:**
- `type Name` - имя нового типа
- `: BaseType` - базовый тип, который уточняется
- `{ predicate }` - необязательный предикат с единственной явной переменной
  `value`, представляющей значение типа.

### Использование: метод `.refine()`

Compile-time метод с контекстной типизацией:

```efen
fn processAge(age: Int) {
    // Компилятор видит из контекста: source=Int, target=Nat
    let validated: Nat = age.refine()

    // Если статически не доказуемо - вставляется runtime проверка
    // При неудаче: RefinementException
}
```

**Ключевые особенности `.refine()`:**
- **Compile-time метод** - анализируется на этапе компиляции
- **Контекстная типизация** - не нужны параметры, компилятор знает source и target типы
- **Умная проверка**:
  - Если компилятор может статически доказать корректность - проверка убирается
  - Иначе - вставляется runtime проверка с `RefinementException`

### Примеры использования

#### Натуральные числа

```efen
type Nat: Int { value >= 0 }

fn factorial(n: Nat) -> Nat {
    // n гарантированно >= 0, не нужны проверки
    if n == 0 { return 1 }
    return n * factorial((n - 1).refine())
}

let x: Int = getUserInput()
let nat: Nat = x.refine()  // Runtime проверка
```

#### Email валидация

```efen
type Email: String { isValidEmail(value) }

class User {
    var email: Email  // Всегда валидный email

    @constructor
    fn init(email: String) -> Self {
        self.email = email.refine()  // Проверка при создании
    }
}
```

#### Индексация с compile-time границей

Тип индекса может получить границу обычным compile-time generic-параметром.
Конкретный `Index<10>` и `Index<20>` являются разными инстанциациями, а
predicate использует переданный предел. Если длина известна только runtime,
граница проверяется обычным `refine()` или proof compiler и не создаёт скрытой
generic identity. См. [типы с параметрами-значениями](value-parameterized-types.md).

#### Non-null значения

```efen
type NonNull<T>: T { value != null }

fn processUser(user: User?) {
    if user != null {
        // В этом scope компилятор знает что user != null
        let validated: NonNull<User> = user.refine()  // Статически доказуемо
        validated.getName()  // Без null checks
    }
}
```

## Семантика

### Совместимость

Новый `type` имеет собственную номинальную идентичность. Базовый и новый тип
требуют точного совпадения; отношение основы само по себе не создаёт widening:

```efen
fn printInt(x: Int) { ... }

let n: Nat = ...
printInt(n)  // Ошибка: ожидается Int, передан Nat
```

Переход выполняется явной операцией или одной прямой видимой стратегией
`Coerce<Source>`.

### Runtime проверка

При неудачной проверке бросается исключение:

```efen
try {
    let n: Nat = (-5).refine()
} catch e: RefinementViolationException {
    // Предикат не выполнен: -5 >= 0 == false
}
```

### Предикаты

Поддерживаемые предикаты (в порядке приоритета реализации):

1. **Простые сравнения**: `>`, `<`, `>=`, `<=`, `==`, `!=`
2. **Логические операции**: `&&`, `||`, `!`
3. **Функции-предикаты**: чистые функции типа `(T) -> bool`
4. **Compile-time параметры**: условия над явно объявленными generic-значениями

Предикаты должны быть **pure** (без побочных эффектов) для возможности статического анализа.

## Архитектура

### Структуры данных в efen-tu

```cpp
// TypeKind расширен новым вариантом
enum class TypeKind : uint8_t {
    // ... existing kinds ...
    Refinement
};

// Predicate — номер функции-валидатора
struct Predicate {
    uint32_t validatorFunctionId;  // Index in Module::functions_
    SourceLocation location;
};

// Type с поддержкой refinement
struct Type {
    cista::offset::string name;
    TypeKind kind;
    // ... other fields ...

    // Refinement type data (only when kind == Refinement)
    TypeReference baseType;       // Base type being refined
    Predicate predicate;          // Validation predicate
};
```

### Валидаторные функции

Предикат хранится как индекс функции-валидатора в `Module::functions_`:

```cpp
// Синтетическая функция, генерируется компилятором
fn __validator_Nat(value: int): bool {
    return value >= 0;
}
```

**Характеристики валидатора:**
- Pure функция (без побочных эффектов)
- Сигнатура: `(baseType) -> bool`
- Compile-time вычисляется если возможно
- Runtime вызывается при необходимости

### Module API

```cpp
// Проверка типа
bool isTypeRefinement(const TypeHandle* handle) const;

// Получение ID валидатора
uint32_t getTypePredicateFunctionId(const TypeHandle* handle) const;

// Установка валидатора
void setTypePredicateFunctionId(TypeHandle* handle, uint32_t funcId);
```

## Примеры реальных use cases

### 1. Финансовые расчёты

```efen
type PositiveAmount: Float { value > 0.0 }
type Percentage: Float { value >= 0.0 && value <= 100.0 }

fn calculateDiscount(price: PositiveAmount, discount: Percentage) -> PositiveAmount {
    let result = price * (1.0 - discount / 100.0)
    return result.refine()
}
```

### 2. Безопасность веб-приложений

```efen
type SafeHtml: String { isSafeHtml(value) }
type ValidUrl: String { isValidUrl(value) }

fn renderLink(url: String, text: String) -> SafeHtml {
    let safeUrl: ValidUrl = url.refine()
    let safeText: SafeHtml = htmlspecialchars(text).refine()
    return "<a href=\"${safeUrl}\">${safeText}</a>".refine()
}
```

### 3. Конфигурация

```efen
type Port: Int { value >= 1 && value <= 65535 }
type NonEmptyString: String { strlen(value) > 0 }

class ServerConfig {
    var host: NonEmptyString
    var port: Port
}
```

### 4. Коллекции

```efen
type NonEmptyArray<T>: [T] { count(value) > 0 }

fn first<T>(arr: NonEmptyArray<T>) -> T {
    return arr[0]  // Безопасно, массив не пустой
}
```

## Типы с compile-time параметрами-значениями

Это действующая generic-возможность Efen. Compile-time значения входят в
identity конкретной инстанциации типа; runtime-значения проверяются через
`refine()` или proof compiler и не создают скрытой generic identity. Полные
правила находятся в
[типах с параметрами-значениями](value-parameterized-types.md).

## Будущие расширения

### 1. Compile-time SMT solver

Статическая верификация через SMT solver (Z3, CVC5):

```efen
fn abs(x: Int) -> Nat {
    if x >= 0 {
        return x.refine()  // SMT доказывает: x >= 0 => value >= 0
    } else {
        return (-x).refine()  // SMT доказывает: x < 0 => -x >= 0
    }
}
```

### 2. Сложные предикаты

```efen
type SortedArray<T>: [T] {
    forall i: 0 <= i && i < count(value) - 1 ==> value[i] <= value[i + 1]
}
```

### 3. Refinement inference

Автоматический вывод refinement types:

```efen
fn process(x: Int) {
    if x >= 0 {
        // Компилятор выводит: x : Int{value >= 0}
        let y = x + 1  // y : Int{value >= 1}
    }
}
```

## Сравнение с другими языками

### Liquid Haskell

```haskell
{-@ type Nat = {value:Int | value >= 0} @-}
{-@ type Pos = {value:Int | value > 0} @-}
```

### F* / Dafny

```fsharp
type nat = x:int{x >= 0}
type pos = x:int{x > 0}
```

### Ada

```ada
subtype Natural is Integer range 0 .. Integer'Last;
subtype Positive is Integer range 1 .. Integer'Last;
```

### Efen (наш синтаксис)

```efen
type Nat: Int { value >= 0 }
type Pos: Int { value > 0 }
```

## Заключение

Refinement types - мощный инструмент для повышения безопасности и надёжности кода через систему типов. Они позволяют выражать инварианты и предусловия как часть типов, делая невозможным создание невалидных состояний.

Ключевые преимущества:
- ✅ Статическая верификация когда возможно
- ✅ Автоматические runtime проверки когда необходимо
- ✅ Явное выражение инвариантов в типах
- ✅ Отсутствие boilerplate validation кода
- ✅ Интеграция с существующей системой типов

---

**Статус:** В разработке (структуры данных готовы, синтаксис финализируется)
