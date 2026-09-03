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

Enum может хранить дополнительные данные для каждого варианта:

```efen
enum Barcode {
    upc: Int, Int, Int, Int
    qrCode: String
}

let productBarcode = Barcode.upc(8, 85909, 51226, 3)
let websiteQR = Barcode.qrCode("https://example.com")
```

Именованные ассоциированные значения:

```efen
enum ServerResponse {
    success: data: String
    failure: code: Int, message: String
    redirect: url: String, permanent: Bool
}

let response = ServerResponse.failure(code: 404, message: "Not Found")
```

## Pattern Matching

Извлечение ассоциированных значений через switch:

```efen
let productCode = Barcode.upc(8, 85909, 51226, 3)

switch productCode {
case .upc(numberSystem, manufacturer, product, check):
    print("UPC: \(numberSystem), \(manufacturer), \(product), \(check)")
case .qrCode(code):
    print("QR код: \(code)")
}
```

С условиями where:

```efen
switch response {
case .success(data) where data.length > 0:
    print("Получены данные: \(data)")
case .success:
    print("Успешно, но данных нет")
case .failure(code, message) where code >= 500:
    print("Ошибка сервера: \(message)")
case .failure(code, message):
    print("Ошибка клиента (\(code)): \(message)")
case .redirect(url, permanent: true):
    print("Постоянный редирект на \(url)")
case .redirect(url, permanent: false):
    print("Временный редирект на \(url)")
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
    print("Метод: \(method)")  // "Метод: post"
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
        return switch self {
        case .north: .south
        case .south: .north
        case .east: .west
        case .west: .east
        }
    }

    var description: String {
        return switch self {
        case .north: "Север"
        case .south: "Юг"
        case .east: "Восток"
        case .west: "Запад"
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
    number: Int
    addition: Expression, Expression
    multiplication: Expression, Expression
}

// Или для конкретных вариантов
enum Expression {
    number: Int
    indirect addition: Expression, Expression
    indirect multiplication: Expression, Expression
}

// (5 + 4) * 2
let expr = Expression.multiplication(
    .addition(.number(5), .number(4)),
    .number(2)
)
```

Вычисление рекурсивного enum:

```efen
fn evaluate(expr: Expression) -> Int {
    return switch expr {
    case .number(value):
        value
    case .addition(left, right):
        evaluate(left) + evaluate(right)
    case .multiplication(left, right):
        evaluate(left) * evaluate(right)
    }
}

print(evaluate(expr))  // 18
```

## Result и Option типы

Типичные функциональные паттерны:

```efen
enum Result<T, E> {
    ok: T
    err: E
}

fn divide(a: Int, b: Int) -> Result<Float, String> {
    if b == 0 {
        return .err("Division by zero")
    }
    return .ok(Float(a) / Float(b))
}

let result = divide(a: 10, b: 2)
switch result {
case .ok(value):
    print("Результат: \(value)")
case .err(message):
    print("Ошибка: \(message)")
}
```

Option (альтернатива optional):

```efen
enum Option<T> {
    some: T
    none
}

fn find(array: [Int], target: Int) -> Option<Int> {
    for (index, value) in array.enumerated() {
        if value == target {
            return .some(index)
        }
    }
    return .none
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
    text: String
    image: url: String, width: Int, height: Int
}

let msg1 = Message.text("Hello")
let msg2 = Message.text("Hello")
let msg3 = Message.text("World")

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

    warrior: weapon: Weapon, armor: Armor
    mage: weapon: Weapon
    archer: weapon: Weapon
}

let hero = Character.warrior(
    weapon: .sword,
    armor: .heavy
)
```

## @unknown default

Для библиотек, которые могут добавить новые варианты:

```efen
enum NetworkStatus {
    connected
    disconnected
    connecting
}

func handleStatus(status: NetworkStatus) {
    switch status {
    case .connected:
        print("Подключено")
    case .disconnected:
        print("Отключено")
    @unknown default:
        // Компилятор предупредит, если появятся новые варианты
        print("Неизвестный статус")
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
    success: data: String
    error: message: String
}

let currentState = State.error(message: "Network failure")
```

### 3. Добавляйте методы для бизнес-логики

```efen
enum OrderStatus {
    pending
    confirmed
    shipped: trackingNumber: String
    delivered
    cancelled

    var canBeCancelled: Bool {
        return switch self {
        case .pending, .confirmed: true
        default: false
        }
    }

    fn nextStatus() -> OrderStatus? {
        return switch self {
        case .pending: .confirmed
        case .confirmed: null  // Нужен внешний триггер (отгрузка)
        case .shipped: .delivered
        case .delivered, .cancelled: null
        }
    }
}
```

### 4. Используйте indirect только при необходимости

```efen
// ✅ Рекурсивная структура - нужен indirect
indirect enum Tree<T> {
    leaf: T
    node: left: Tree<T>, right: Tree<T>
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
       case1 = 1
       case2: String  // Нельзя!
   }
   ```

2. **CaseIterable не работает с ассоциированными значениями**:
   ```efen
   // ❌ Ошибка
   enum Result<T>: CaseIterable {
       ok: T
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

- [switch.md](../blocks/switch.md) — Pattern matching с enum
- [generics.md](../generics.md) — Generic enum (Result, Option)
- [type.md](type.md) — Система типов
- [constants.md](constants.md) — Константы
