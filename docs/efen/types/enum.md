# Enum (Перечисления)

Перечисления (enum) в Efen — это мощный тип данных для определения набора связанных значений.
Заимствуя лучшие идеи из Swift и Rust, enum в Efen поддерживают:
- Простые перечисления
- Ассоциированные значения (associated values)
- Raw values
- Методы и вычисляемые свойства
- Pattern matching

## Базовый enum

Простейшая форма — список именованных констант:

```efen
enum Direction {
    north
    south
    east
    west
}

let heading = Direction.north
```

При известном типе можно опускать имя enum:

```efen
let heading: Direction = .north

fn turn(to: Direction) {
    // ...
}

turn(to: .east)  // Тип известен из сигнатуры
```

## Ассоциированные значения

Enum может хранить дополнительные данные для каждого варианта. Поля варианта
перечисляются в фигурных скобках и всегда именованы:

```efen
enum Barcode {
    upc { system: Int, manufacturer: Int, product: Int, check: Int }
    qrCode { code: String }
}

let productBarcode = Barcode.upc(system: 8, manufacturer: 85909, product: 51226, check: 3)
let websiteQR = Barcode.qrCode(code: "https://example.com")
```

Вариант создаётся вызовом с метками полей:

```efen
enum ServerResponse {
    success { data: String }
    failure { code: Int, message: String }
    redirect { url: String, permanent: Bool }
}

let response = ServerResponse.failure(code: 404, message: "Not Found")
```

## Pattern Matching

Извлечение ассоциированных значений через `match`. Образец перечисляет поля
[оператором проекции `.{ }`](projection.md) после имени варианта; связывает
только `let`, а ненужные поля можно опустить:

```efen
let productCode = Barcode.upc(system: 8, manufacturer: 85909, product: 51226, check: 3)

match productCode {
    .upc.{ let system, let manufacturer, let product, let check }:
        print("UPC: ${system}, ${manufacturer}, ${product}, ${check}")
    .qrCode.{ let code }:
        print("QR код: ${code}")
}
```

С условиями where:

```efen
match response {
    .success.{ let data } where data.length > 0: print("Получены данные: ${data}")
    .success: print("Успешно, но данных нет")
    .failure.{ let code, let message } where code >= 500: print("Ошибка сервера: ${message}")
    .failure.{ let code, let message }: print("Ошибка клиента (${code}): ${message}")
    .redirect.{ let url, permanent: true }: print("Постоянный редирект на ${url}")
    .redirect.{ let url, permanent: false }: print("Временный редирект на ${url}")
}
```

## Raw Values

Enum может иметь базовый тип (raw value):

```efen
enum StatusCode: Int {
    ok = 200
    created = 201
    badRequest = 400
    unauthorized = 401
    notFound = 404
    serverError = 500
}

let code = StatusCode.notFound
print(code.rawValue)  // 404
```

Автоинкремент для Int:

```efen
enum Priority: Int {
    low = 1
    medium     // 2
    high       // 3
    critical   // 4
}
```

String raw values (равны имени по умолчанию):

```efen
enum Direction: String {
    north      // "north"
    south      // "south"
    east       // "east"
    west       // "west"
}

print(Direction.north.rawValue)  // "north"
```

Кастомные String values:

```efen
enum HttpMethod: String {
    get = "GET"
    post = "POST"
    put = "PUT"
    delete = "DELETE"
}
```

Инициализация из raw value:

```efen
let method = HttpMethod(rawValue: "POST")  // Optional<HttpMethod>

if let method = HttpMethod(rawValue: "POST") {
    print("Метод: ${method}")  // "Метод: post"
}

let invalid = HttpMethod(rawValue: "INVALID")  // null
```

## Вычисляемые свойства и методы

Enum может иметь методы и свойства:

```efen
enum Direction {
    north
    south
    east
    west

    fn opposite() -> Direction {
        return match self {
            .north: .south
            .south: .north
            .east: .west
            .west: .east
        }
    }

    var description: String {
        return match self {
            .north: "Север"
            .south: "Юг"
            .east: "Восток"
            .west: "Запад"
        }
    }
}

let heading = Direction.north
print(heading.description)      // "Север"
print(heading.opposite())       // Direction.south
```

## Рекурсивные enum

Для рекурсивных структур используйте indirect:

```efen
indirect enum Expression {
    number { value: Int }
    addition { left: Expression, right: Expression }
    multiplication { left: Expression, right: Expression }
}

// Или для конкретных вариантов
enum Expression {
    number { value: Int }
    indirect addition { left: Expression, right: Expression }
    indirect multiplication { left: Expression, right: Expression }
}

// (5 + 4) * 2
let expr = Expression.multiplication(
    left: .addition(left: .number(value: 5), right: .number(value: 4)),
    right: .number(value: 2)
)
```

Вычисление рекурсивного enum:

```efen
fn evaluate(expr: Expression) -> Int {
    return match expr {
        .number.{ let value }: value
        .addition.{ let left, let right }: evaluate(left) + evaluate(right)
        .multiplication.{ let left, let right }: evaluate(left) * evaluate(right)
    }
}

print(evaluate(expr))  // 18
```

## Result и Option типы

Типичные функциональные паттерны:

```efen
enum Result<T, E> {
    ok { value: T }
    err { error: E }
}

fn divide(a: Int, b: Int) -> Result<Float, String> {
    if b == 0 {
        return .err(error: "Division by zero")
    }
    return .ok(value: Float(a) / Float(b))
}

let result = divide(a: 10, b: 2)
match result {
    .ok.{ let value }: print("Результат: ${value}")
    .err.{ let error }: print("Ошибка: ${error}")
}
```

Optional использует обычный optional-тип и его стандартный alias:

```efen
alias Option<T> = T?

fn find(array: [Int], target: Int) -> Option<Int> {
    for (index, value) in array.enumerated() {
        if value == target {
            return Some(index)
        }
    }
    return None
}
```

## CaseIterable

Enum может генерировать список всех вариантов:

```efen
enum Direction: CaseIterable {
    north
    south
    east
    west
}

for direction in Direction.allCases {
    print(direction.description)
}
// Север
// Юг
// Восток
// Запад

print(Direction.allCases.count)  // 4
```

**Примечание**: CaseIterable работает только с enum без ассоциированных значений.

## Сравнение enum

Enum автоматически поддерживают равенство:

```efen
let d1 = Direction.north
let d2 = Direction.north
let d3 = Direction.south

print(d1 == d2)  // true
print(d1 == d3)  // false
```

Для enum с ассоциированными значениями:

```efen
enum Message: Equatable {
    text { content: String }
    image { url: String, width: Int, height: Int }
}

let msg1 = Message.text(content: "Hello")
let msg2 = Message.text(content: "Hello")
let msg3 = Message.text(content: "World")

print(msg1 == msg2)  // true
print(msg1 == msg3)  // false
```

## Comparable enum

С raw values типа Int/String enum автоматически Comparable:

```efen
enum Priority: Int, Comparable {
    low = 1
    medium = 2
    high = 3
    critical = 4
}

print(Priority.low < Priority.high)      // true
print(Priority.critical > Priority.medium) // true
```

## Вложенные enum

Enum может содержать другие enum:

```efen
enum Character {
    enum Weapon {
        sword
        bow
        staff
    }

    enum Armor {
        light
        medium
        heavy
    }

    warrior { weapon: Weapon, armor: Armor }
    mage { weapon: Weapon }
    archer { weapon: Weapon }
}

let hero = Character.warrior(
    weapon: .sword,
    armor: .heavy
)
```

## @unknown _

Для библиотек, которые могут добавить новые варианты:

```efen
enum NetworkStatus {
    connected
    disconnected
    connecting
}

func handleStatus(status: NetworkStatus) {
    match status {
        .connected: print("Подключено")
        .disconnected: print("Отключено")
        @unknown _: {
            // Компилятор предупредит, если появятся новые варианты
            print("Неизвестный статус")
        }
    }
}
```

## Лучшие практики

### 1. Используйте enum вместо констант

❌ **Плохо:**
```efen
const STATUS_PENDING = 0
const STATUS_ACTIVE = 1
const STATUS_COMPLETED = 2

fn updateStatus(status: Int) { ... }
updateStatus(3)  // Ошибка не будет поймана
```

✅ **Хорошо:**
```efen
enum Status {
    pending
    active
    completed
}

fn updateStatus(status: Status) { ... }
updateStatus(.active)  // Типобезопасно
```

### 2. Используйте ассоциированные значения для контекста

❌ **Плохо:**
```efen
enum State {
    loading
    success
    error
}

var currentState = State.loading
var errorMessage: String? = null  // Отдельная переменная
```

✅ **Хорошо:**
```efen
enum State {
    loading
    success { data: String }
    error { message: String }
}

let currentState = State.error(message: "Network failure")
```

### 3. Добавляйте методы для бизнес-логики

```efen
enum OrderStatus {
    pending
    confirmed
    shipped { trackingNumber: String }
    delivered
    cancelled

    var canBeCancelled: Bool {
        return match self {
            .pending | .confirmed: true
            _: false
        }
    }

    fn nextStatus() -> OrderStatus? {
        return match self {
            .pending: .confirmed
            .confirmed: null  // Нужен внешний триггер (отгрузка)
            .shipped: .delivered
            .delivered | .cancelled: null
        }
    }
}
```

### 4. Используйте indirect только при необходимости

```efen
// ✅ Рекурсивная структура - нужен indirect
indirect enum Tree<T> {
    leaf { value: T }
    node { left: Tree<T>, right: Tree<T> }
}

// ❌ Не нужен indirect
enum Direction {
    north
    south
}
```

### 5. Raw values для сериализации

```efen
enum Environment: String {
    development = "dev"
    staging = "staging"
    production = "prod"

    static fn fromConfig(value: String) -> Environment? {
        return Environment(rawValue: value)
    }
}

let env = Environment.fromConfig(value: config.env) ?? .development
```

## Ограничения

1. **Нельзя комбинировать raw values и ассоциированные значения**:
   ```efen
   // ❌ Ошибка
   enum Mixed: Int {
       first = 1
       second { value: String }  // Нельзя!
   }
   ```

2. **CaseIterable не работает с ассоциированными значениями**:
   ```efen
   // ❌ Ошибка
   enum Result<T>: CaseIterable {
       ok { value: T }
       error
   }
   ```

3. **Нельзя наследоваться от enum**:
   ```efen
   // ❌ Enum не поддерживают наследование
   enum Base { ... }
   enum Derived: Base { ... }  // Ошибка
   ```

## Сравнение с другими языками

### vs C/C++ enum
- ✅ Типобезопасны (нельзя присвоить Int)
- ✅ Поддерживают методы
- ✅ Ассоциированные значения
- ✅ Pattern matching

### vs Swift enum
- ✅ Аналогичный синтаксис
- ✅ Те же возможности
- ⚠️ Проверьте поддержку всех фич (@unknown, indirect)

### vs Rust enum
- ✅ Похожие ассоциированные значения
- ⚠️ Rust имеет более строгую систему типов
- ⚠️ В Rust нет raw values (используют derive)

## См. также

- [match.md](../blocks/match.md) — Сопоставление с образцом и enum
- [generics.md](../generics.md) — Generic enum (Result, Option)
- [type.md](type.md) — Система типов
- [constants.md](constants.md) — Константы
