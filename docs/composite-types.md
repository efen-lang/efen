# Composite Types (Типы-объединения)

## Обзор

EFEN поддерживает составные типы (Composite Types), которые позволяют комбинировать существующие типы для создания более сложных типовых конструкций. Эта возможность включает:

- **Union Types** (типы-объединения) - значение может быть одним из нескольких типов
- **Intersection Types** (типы-пересечения) - значение должно соответствовать всем указанным типам одновременно
- **Negation Types** (типы-отрицания) - значение не должно соответствовать указанному типу
- **DNF Types** (Disjunctive Normal Form) - комбинация union и intersection типов

## Мотивация

Составные типы решают несколько важных задач:

1. **Точное моделирование бизнес-логики**: Возможность выразить сложные типовые требования
2. **Безопасность типов**: Компилятор гарантирует корректность операций
3. **Выразительность**: Более точное описание контрактов API
4. **Совместимость с PHP**: PHP 8+ поддерживает union и intersection типы

## Union Types (Типы-объединения)

### Синтаксис

```efen
Type1 | Type2 | Type3
```

### Описание

Union type означает, что значение может быть **одним из** указанных типов. Это логическое **ИЛИ** для типов.

### Примеры

```efen
// Функция может принимать Int или String
fn processValue(value: Int | String) -> String {
    if value is Int {
        return "Number: ${value}"
    } else {
        return "String: ${value}"
    }
}

// Переменная может быть null или конкретным типом
let result: String | null = fetchData()

// Множественные типы
let mixedValue: Int | Float | String = getValue()

// С дженериками
let container: Array<Int | String> = [1, "two", 3, "four"]

// Nullable через union (альтернатива суффиксу ?)
fn getName(): String | null {
    return null
}

// Возвращаемое значение может быть Success или Error
fn divide(a: Float, b: Float): Float | Error {
    if b == 0.0 {
        return Error("Division by zero")
    }
    return a / b
}
```

### Особенности

- Union типы коммутативны: `A | B` == `B | A`
- Дублирующиеся типы схлопываются: `A | A | B` == `A | B`
- `never` является нейтральным элементом: `A | never` == `A`
- Приоритет: union имеет более низкий приоритет чем intersection

## Intersection Types (Типы-пересечения)

### Синтаксис

```efen
Type1 & Type2 & Type3
```

### Описание

Intersection type означает, что значение должно соответствовать **всем** указанным типам одновременно. Это логическое **И** для типов.

### Примеры

```efen
// Интерфейсы
interface Printable {
    fn print() -> Void
}

interface Serializable {
    fn serialize() -> String
}

// Объект должен реализовывать оба интерфейса
fn processObject(obj: Printable & Serializable) -> Void {
    obj.print()
    let data = obj.serialize()
}

// Миксин паттерн
interface Logger {
    fn log(message: String) -> Void
}

interface Validator {
    fn validate() -> Bool
}

class DataProcessor implements Logger & Validator {
    fn log(message: String) -> Void {
        echo message
    }

    fn validate() -> Bool {
        return true
    }
}

// С классами и интерфейсами
fn handle(obj: MyClass & Serializable) -> Void {
    // obj гарантированно является MyClass И реализует Serializable
}
```

### Особенности

- Intersection типы коммутативны: `A & B` == `B & A`
- `Any` является нейтральным элементом: `A & Any` == `A`
- Противоречивые типы дают `never`: `String & Int` == `never`
- Приоритет: intersection имеет более высокий приоритет чем union

## Negation Types (Типы-отрицания)

### Синтаксис

```efen
!Type
```

### Описание

Negation type означает, что значение **не должно** соответствовать указанному типу.

### Примеры

```efen
// Любой тип кроме null
fn processNonNull(value: !null) -> Void {
    // value гарантированно не null
}

// Любой тип кроме строки
fn processNotString(value: !String) -> Void {
    // value может быть Int, Float, Bool, и т.д., но не String
}

// Комбинация с union
fn acceptNumbersButNotFloat(value: (Int | Float) & !Float) -> Void {
    // Эквивалентно: fn acceptNumbersButNotFloat(value: Int)
}

// Исключение конкретного типа из union
type NonNullResult = Result & !null

// Generic constraints
fn process<T: !null>(value: T) -> T {
    // T не может быть null
    return value
}
```

### Особенности

- Двойное отрицание: `!!A` == `A`
- De Morgan's laws:
  - `!(A | B)` == `!A & !B`
  - `!(A & B)` == `!A | !B`
- `!Any` == `never`
- `!never` == `Any`

## DNF Types (Disjunctive Normal Form)

### Синтаксис

DNF - это стандартная форма записи булевых выражений в виде ИЛИ (дизъюнкций) последовательностей И (конъюнкций).

```efen
(Type1 & Type2) | (Type3 & Type4) | Type5
```

### Описание

DNF типы позволяют комбинировать union и intersection типы. Это наиболее общая форма составных типов.

### Правила синтаксиса

1. Intersection типы должны быть в скобках при комбинации с union
2. Форма: `(A & B & C) | D | (E & F) | G`

### Примеры

```efen
// Классический случай: пересечение с nullable
fn process(obj: (Printable & Serializable) | null) -> Void {
    if obj is null {
        return
    }
    obj.print()
    obj.serialize()
}

// Множественные варианты
type Handler =
    | (HttpHandler & Logging)
    | (WebSocketHandler & Logging)
    | FallbackHandler

// API response типы
type ApiResponse =
    | (SuccessResponse & Validated)
    | (ErrorResponse & Logged)
    | CachedResponse

// Сложный пример с дженериками
type Result<T, E> =
    | (Success & { value: T })
    | (Error & { error: E })

// Миксин композиция
type Component =
    | (BaseComponent & Renderable & EventEmitter)
    | (LazyComponent & Loadable)
    | StaticComponent
```

### Особенности

- DNF является канонической формой для составных типов
- Компилятор автоматически приводит сложные типы к DNF
- Упрощение происходит во время компиляции

## Приоритет операторов

От высшего к низшему:

1. **Скобки** `()`
2. **Отрицание** `!`
3. **Пересечение** `&`
4. **Объединение** `|`

### Примеры приоритета

```efen
// Без скобок
A | B & C           // Эквивалентно: A | (B & C)
!A & B              // Эквивалентно: (!A) & B
A | B | C & D       // Эквивалентно: A | B | (C & D)

// Со скобками
(A | B) & C         // Пересечение union типа с C
!(A & B)            // Отрицание intersection типа
(A | B) & (C | D)   // Пересечение двух union типов
```

## Type Narrowing (Сужение типов)

Компилятор автоматически сужает union типы в зависимости от контекста.

### Примеры

```efen
fn process(value: Int | String | null) -> String {
    // Проверка типа
    if value is String {
        // здесь value имеет тип String
        return value.toUpperCase()
    }

    if value is Int {
        // здесь value имеет тип Int
        return value.toString()
    }

    // здесь value имеет тип null
    return "null"
}

// Pattern matching
fn handle(result: Success | Error) -> Void {
    switch result {
        case Success:
            // result имеет тип Success
            echo "Success: ${result.value}"
        case Error:
            // result имеет тип Error
            echo "Error: ${result.message}"
    }
}

// Guard statements
fn safeDivide(a: Float, b: Float | null) -> Float {
    guard let divisor = b, divisor != 0.0 else {
        throw Error("Invalid divisor")
    }
    // здесь b гарантированно Float и != 0.0
    return a / divisor
}
```

## Ограничения и правила

### 1. Несовместимые типы

```efen
// ❌ Ошибка: String и Int несовместимы для intersection
type Invalid = String & Int  // Результат: never

// ✅ Правильно: использование union
type Valid = String | Int
```

### 2. Примитивные типы

```efen
// ❌ Ошибка: примитивные типы не могут образовывать intersection
type Invalid = Int & Float

// ✅ Правильно: union примитивов
type Number = Int | Float
```

### 3. DNF форма

```efen
// ❌ Ошибка: недопустимая форма (CNF вместо DNF)
type Invalid = (A | B) & (C | D)

// ✅ Правильно: раскрыть в DNF
type Valid = (A & C) | (A & D) | (B & C) | (B & D)
```

### 4. Nullable типы

```efen
// Два способа выразить nullable:
type NullableString1 = String?           // Короткая форма
type NullableString2 = String | null     // Явная union форма

// Оба эквивалентны
```

## Сравнение с другими языками

### TypeScript

```typescript
// TypeScript
type UnionType = string | number
type IntersectionType = Printable & Serializable
// Нет negation types
```

```efen
// EFEN
type UnionType = String | Int
type IntersectionType = Printable & Serializable
type NegationType = !null
```

### PHP 8+

```php
// PHP 8.0 - Union
function process(int|string $value): void {}

// PHP 8.1 - Intersection
function handle(Printable&Serializable $obj): void {}

// PHP 8.2 - DNF
function accept((Printable&Serializable)|null $obj): void {}
```

```efen
// EFEN - эквиваленты
fn process(value: Int | String) -> Void {}
fn handle(obj: Printable & Serializable) -> Void {}
fn accept(obj: (Printable & Serializable) | null) -> Void {}
```

### Scala 3

```scala
// Scala 3
type UnionType = String | Int
type IntersectionType = Printable & Serializable
// Negation через NotGiven
```

```efen
// EFEN
type UnionType = String | Int
type IntersectionType = Printable & Serializable
type NegationType = !SomeType
```

## Практические примеры

### 1. Result Type (Error Handling)

```efen
interface Success<T> {
    var value: T
    fn isSuccess() -> Bool { return true }
}

interface Failure<E> {
    var error: E
    fn isSuccess() -> Bool { return false }
}

type Result<T, E> = Success<T> | Failure<E>

fn divide(a: Int, b: Int) -> Result<Int, String> {
    if b == 0 {
        return Failure(error: "Division by zero")
    }
    return Success(value: a / b)
}

fn handleResult(result: Result<Int, String>) -> Void {
    if result.isSuccess() {
        echo "Success: ${result.value}"
    } else {
        echo "Error: ${result.error}"
    }
}
```

### 2. API Response Types

```efen
interface ApiSuccess {
    var data: Any
    var status: Int
}

interface ApiError {
    var message: String
    var code: Int
}

interface Cached {
    var cachedAt: Int
}

type ApiResponse =
    | (ApiSuccess & Cached)
    | ApiSuccess
    | ApiError

fn handleResponse(response: ApiResponse) -> Void {
    switch response {
        case ApiError:
            echo "Error: ${response.message}"
        case ApiSuccess & Cached:
            echo "Cached data: ${response.data}"
        case ApiSuccess:
            echo "Fresh data: ${response.data}"
    }
}
```

### 3. Event System

```efen
interface MouseEvent {
    var x: Int
    var y: Int
}

interface KeyboardEvent {
    var key: String
}

interface TouchEvent {
    var touches: [Touch]
}

type InputEvent = MouseEvent | KeyboardEvent | TouchEvent

fn handleInput(event: InputEvent) -> Void {
    if event is MouseEvent {
        echo "Mouse at: ${event.x}, ${event.y}"
    } else if event is KeyboardEvent {
        echo "Key pressed: ${event.key}"
    } else if event is TouchEvent {
        echo "Touches: ${event.touches.length}"
    }
}
```

### 4. Builder Pattern с ограничениями

```efen
interface HasName {
    var name: String
}

interface HasAge {
    var age: Int
}

interface HasEmail {
    var email: String
}

type CompleteProfile = HasName & HasAge & HasEmail
type PartialProfile = HasName | (HasName & HasAge) | CompleteProfile

fn saveProfile(profile: CompleteProfile) -> Void {
    // Требуется полный профиль
}

fn updateProfile(profile: PartialProfile) -> Void {
    // Можно обновить частичный профиль
}
```

## Семантика и проверка типов

### Subtyping Rules

1. **Union**: `A` является подтипом `A | B`
2. **Intersection**: `A & B` является подтипом `A`
3. **Negation**: `!A` и `A` не имеют общих значений

### Присваивание

```efen
let x: Int = 42
let y: Int | String = x        // ✅ OK: Int <: Int | String

let a: Int & Serializable = obj
let b: Int = a                  // ✅ OK: Int & Serializable <: Int

let c: !null = "hello"
let d: String = c               // ✅ OK: !null может содержать String
```

## Заключение

Составные типы в EFEN предоставляют мощный инструмент для точного моделирования типовых требований. Синтаксис вдохновлен TypeScript и PHP 8+, с дополнительной поддержкой типов-отрицаний для еще большей выразительности.

Основные преимущества:
- **Безопасность**: компилятор гарантирует корректность
- **Выразительность**: точное описание контрактов
- **Совместимость**: близость к PHP и TypeScript синтаксису
- **Гибкость**: DNF позволяет выражать сложные комбинации типов
