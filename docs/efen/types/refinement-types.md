# Refinement Types

## Введение

**Refinement types** (уточняющие типы) - это система типов, 
которая позволяет добавлять логические предикаты к базовым типам для более точной спецификации допустимых значений.

### Основная идея

Обычный тип описывает множество значений (например, `int` = все целые числа), 
а `refinement type` сужает это множество через предикат:

```efen
// Обычный тип
var age: int  // Любое целое число

// Direct predicate refinement
var age: int { $v >= 0 && $v <= 150 }  // Только валидные возраста
var email: string { is_valid_email($v) }  // Только валидные email адреса

// Type definition style
type Nat extends int { $v >= 0 }
type Email extends string { is_valid_email($v) }

let age: Nat = 25  // age гарантированно >= 0
let email: Email = "email@dot.com" // email гарантированно валиден
```

### Зачем нужны Refinement Types?

1. **Статическая верификация** - проверка ограничений на этапе компиляции
2. **Отсутствие null checks** - `type NonNull<T> extends T where { v != null }`
3. **Безопасность индексации** - `type ValidIndex extends int where { v >= 0 && v < len(array) }`
4. **Бизнес-логика в типах** - `type Email extends string where { is_valid_email(v) }`
5. **Контракты без runtime overhead** - проверки на compile-time когда возможно

## Синтаксис

### Определение Refinement Type

Для определения нового уточняющего типа используется ключевое слово `type`, 
которое участвует так же в создании алиасов типов или материализации generic типов.

```php
type Name extends BaseType { predicate }
```

**Компоненты:**
- `type Name` - имя нового типа
- `extends BaseType` - базовый тип, который уточняется
- `{ predicate }` - предикат с явной переменной `$v` или `$value`, представляющей значение типа.

### Использование: метод `.refine()`

Compile-time метод с контекстной типизацией:

```efen
fn processAge(age: int) {
    // Компилятор видит из контекста: source=int, target=Nat
    let validated: Nat = age.refine();

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

```php
type Nat extends int { v >= 0 }

fn factorial(n: Nat): Nat {
    // n гарантированно >= 0, не нужны проверки
    if (n == 0) return 1;
    return n * factorial((n - 1).refine());
}

let x: int = getUserInput();
let nat: Nat = x.refine();  // Runtime проверка
```

#### Email валидация

```php
type Email extends string { is_valid_email(v) }

class User {
    email: Email;  // Всегда валидный email

    fn construct(email: string) {
        self.email = email.refine();  // Проверка при создании
    }
}
```

#### Безопасная индексация

```php
type Index<T> extends int { v >= 0 && v < count($array) }

fn safeGet<T>(array: array<T>, index: int): T {
    let safe: Index<T> = index.refine();  // Проверка границ
    return array[safe];  // Гарантированно безопасно
}
```

#### Non-null значения

```php
type NonNull<T> extends T where { v != null }

fn processUser(user: User?) {
    if (user != null) {
        // В этом scope компилятор знает что user != null
        let validated: NonNull<User> = user.refine();  // Статически доказуемо
        validated.getName();  // Без null checks
    }
}
```

## Семантика

### Subtyping

Refinement type является подтипом базового типа:

```php
Nat <: int  // Nat можно использовать везде где ожидается int
```

Автоматическое приведение вверх (widening):

```php
fn printInt(x: int) { ... }

let n: Nat = ...;
printInt(n);  // OK, автоматическое приведение Nat -> int
```

### Runtime проверка

При неудачной проверке бросается исключение:

```php
try {
    let n: Nat = (-5).refine();
} catch (RefinementViolationException $e) {
    // Предикат не выполнен: -5 >= 0 == false
}
```

### Предикаты

Поддерживаемые предикаты (в порядке приоритета реализации):

1. **Простые сравнения**: `>`, `<`, `>=`, `<=`, `==`, `!=`
2. **Логические операции**: `&&`, `||`, `!`
3. **Функции-предикаты**: чистые функции типа `(T) -> bool`
4. **Зависимости от других переменных**: dependent types (будущее расширение)

Предикаты должны быть **pure** (без побочных эффектов) для возможности статического анализа.

## Архитектура

### Структуры данных в efen-tu

```cpp
// TypeKind расширен новым вариантом
enum class TypeKind : uint8_t {
    // ... existing kinds ...
    Refinement
};

// Predicate - ссылка на функцию-валидатор
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
fn __validator_Nat(v: int): bool {
    return v >= 0;
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

```php
type PositiveAmount extends float where { v > 0.0 }
type Percentage extends float where { v >= 0.0 && v <= 100.0 }

fn calculateDiscount(price: PositiveAmount, discount: Percentage): PositiveAmount {
    let result = price * (1.0 - discount / 100.0);
    return result.refine();
}
```

### 2. Безопасность веб-приложений

```php
type SafeHtml extends string where { is_safe_html(v) }
type ValidUrl extends string where { is_valid_url(v) }

fn renderLink(url: string, text: string): SafeHtml {
    let safeUrl: ValidUrl = url.refine();
    let safeText: SafeHtml = htmlspecialchars(text).refine();
    return "<a href=\"{$safeUrl}\">{$safeText}</a>".refine();
}
```

### 3. Конфигурация

```php
type Port extends int where { v >= 1 && v <= 65535 }
type NonEmptyString extends string where { strlen(v) > 0 }

class ServerConfig {
    host: NonEmptyString;
    port: Port;
}
```

### 4. Коллекции

```php
type NonEmptyArray<T> extends array<T> where { count(v) > 0 }

fn first<T>(arr: NonEmptyArray<T>): T {
    return arr[0];  // Безопасно, массив не пустой
}
```

## Будущие расширения

### 1. Compile-time SMT solver

Статическая верификация через SMT solver (Z3, CVC5):

```php
fn abs(x: int): Nat {
    if (x >= 0) {
        return x.refine();  // SMT доказывает: x >= 0 => v >= 0
    } else {
        return (-x).refine();  // SMT доказывает: x < 0 => -x >= 0
    }
}
```

### 2. Dependent types

Зависимость от значений других параметров:

```php
type BoundedInt<min, max> extends int where { v >= min && v <= max }
type Array<T, n> extends array<T> where { count(v) == n }

fn createFixedArray<T, n>(value: T): Array<T, n> {
    return array_fill(0, n, value).refine();
}
```

### 3. Сложные предикаты

```php
type SortedArray<T> extends array<T> where {
    for (i = 0; i < count(v) - 1; i++) {
        v[i] <= v[i + 1]
    }
}
```

### 4. Refinement inference

Автоматический вывод refinement types:

```php
fn process(x: int) {
    if (x >= 0) {
        // Компилятор выводит: x : int{v >= 0}
        let y = x + 1;  // y : int{v >= 1}
    }
}
```

## Сравнение с другими языками

### Liquid Haskell

```haskell
{-@ type Nat = {v:Int | v >= 0} @-}
{-@ type Pos = {v:Int | v > 0} @-}
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

```php
type Nat extends int where { v >= 0 }
type Pos extends int where { v > 0 }
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
