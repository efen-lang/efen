# Кортежи (Tuples)

Кортеж — это неизменяемая упорядоченная коллекция фиксированного размера, которая может содержать значения разных типов. Кортежи используются для группировки связанных значений без создания отдельного типа.

Tuple задаёт логическую форму данных, но не обязан фиксировать их физическое
представление. Элемент optional-типа всегда является частью схемы tuple, хотя
его значение может быть `null`:

```efen
alias EntityData = (
    position: Position?,
    velocity: Velocity?,
    health: Health?
)

let empty: EntityData = (
    position: null,
    velocity: null,
    health: null
)
```

Именованная representation может хранить такой tuple целиком, колонками либо
не выделять физическое место под отсутствующие optional-значения. При этом
логическая схема tuple остаётся фиксированной. См. [Репрезентации](../representations.md).

## Содержание

- [Основы](#основы)
- [Создание кортежей](#создание-кортежей)
- [Доступ к элементам](#доступ-к-элементам)
- [Именованные элементы](#именованные-элементы)
- [Деструктуризация](#деструктуризация)
- [Кортежи в функциях](#кортежи-в-функциях)
- [Pattern Matching](#pattern-matching)
- [Tuple vs Struct](#tuple-vs-struct)
- [Особые случаи](#особые-случаи)

## Основы

Кортеж объявляется с помощью круглых скобок `()` и может содержать значения любых типов:

```efen
// Кортеж из двух чисел
let point = (10, 20)

// Кортеж из разных типов
let person = ("Alice", 30, true)

// Пустой кортеж (unit type)
let empty = ()
```

### Типы кортежей

Тип кортежа определяется типами его элементов:

```efen
// Тип: (Int, Int)
let point: (Int, Int) = (10, 20)

// Тип: (String, Int, Bool)
let person: (String, Int, Bool) = ("Alice", 30, true)

// Алиас для типа кортежа
alias Point = (Int, Int)
alias Person = (String, Int, Bool)

let p: Point = (5, 15)
```

## Создание кортежей

### Безымянные элементы

Простейший способ создания кортежа — перечислить значения через запятую в скобках:

```efen
let coordinates = (100, 200)
let rgb = (255, 128, 0)
let mixed = (42, "hello", true, 3.14)
```

### Именованные элементы

Элементам кортежа можно давать имена для улучшения читаемости:

```efen
let point = (x: 10, y: 20)
let person = (name: "Alice", age: 30)
let response = (status: 200, body: "OK", headers: ["Content-Type": "text/plain"])
```

### Смешанные кортежи

Кортеж может содержать как именованные, так и безымянные элементы:

```efen
let mixed = (x: 10, 20, z: 30)
// Доступ: mixed.x, mixed.1, mixed.z
```

### Вложенные кортежи

Кортежи могут быть вложенными:

```efen
let nested = ((1, 2), (3, 4))
let complex = (point: (x: 10, y: 20), name: "Origin")
```

## Доступ к элементам

### Доступ по индексу

К элементам кортежа можно обращаться по индексу с помощью синтаксиса `.0`, `.1`, и т.д.:

```efen
let point = (10, 20)
let x = point.0  // 10
let y = point.1  // 20

let triple = (1, 2, 3)
echo triple.0    // 1
echo triple.1    // 2
echo triple.2    // 3
```

### Доступ по имени

Для именованных элементов можно использовать имена:

```efen
let person = (name: "Alice", age: 30)
echo person.name  // "Alice"
echo person.age   // 30

// Именованные элементы доступны и по индексу
echo person.0     // "Alice"
echo person.1     // 30
```

### Вложенный доступ

Для вложенных кортежей доступ осуществляется цепочкой:

```efen
let nested = ((1, 2), (3, 4))
echo nested.0.0   // 1
echo nested.0.1   // 2
echo nested.1.0   // 3

let complex = (point: (x: 10, y: 20), name: "Origin")
echo complex.point.x    // 10
echo complex.name       // "Origin"
```

## Именованные элементы

Именованные элементы делают код более читаемым и самодокументирующимся:

```efen
// Без имен — неочевидно что означают числа
let config1 = ("localhost", 8080, 30)

// С именами — ясно и понятно
let config2 = (host: "localhost", port: 8080, timeout: 30)

echo config2.host     // "localhost"
echo config2.port     // 8080
echo config2.timeout  // 30
```

### Именованные типы кортежей

Можно создавать алиасы для именованных кортежей:

```efen
alias Config = (host: String, port: Int, timeout: Int)
alias Point = (x: Int, y: Int)
alias RGB = (r: Int, g: Int, b: Int)

fn createConfig() -> Config {
    return (host: "localhost", port: 8080, timeout: 30)
}

let cfg = createConfig()
echo cfg.host  // "localhost"
```

## Деструктуризация

Кортежи можно распаковывать в отдельные переменные:

### Базовая деструктуризация

```efen
let point = (10, 20)
let (x, y) = point
echo x  // 10
echo y  // 20

let person = (name: "Alice", age: 30)
let (name, age) = person
echo name  // "Alice"
echo age   // 30
```

### Деструктуризация по именам элементов

Именованный кортеж можно разобрать не по позиции, а по именам элементов —
[оператором проекции `.{ }`](projection.md):

```efen
alias Point = (x: Int, y: Int)

let point = getPoint()
let .{ x, y } = point

// Элемент можно связать с другим именем
let .{ x: px, y: py } = point
```

Имена внутри `.{ }` совпадают с именами элементов кортежа. Позиционный
разбор круглыми скобками остаётся доступным:

```efen
let (x, y) = getCoordinates()
let (name, age) = getPerson()
```

### Игнорирование элементов

Используйте `_` для игнорирования ненужных элементов:

```efen
let triple = (1, 2, 3)
let (first, _, third) = triple
// Второй элемент игнорируется

let person = (name: "Alice", age: 30, active: true)
let (name, _, _) = person
// Берем только имя
```

### Вложенная деструктуризация

```efen
let nested = ((1, 2), (3, 4))
let ((a, b), (c, d)) = nested
echo a  // 1
echo b  // 2
echo c  // 3
echo d  // 4
```

## Кортежи в функциях

### Возврат нескольких значений

Кортежи позволяют возвращать несколько значений из функции:

```efen
fn divmod(a: Int, b: Int) -> (quotient: Int, remainder: Int) {
    return (quotient: a / b, remainder: a % b)
}

let result = divmod(17, 5)
echo result.quotient   // 3
echo result.remainder  // 2

// Или с деструктуризацией
let (q, r) = divmod(17, 5)
echo "${q}, ${r}"  // "3, 2"
```

### Кортежи как параметры

```efen
fn distance(point1: (Int, Int), point2: (Int, Int)) -> Float {
    let dx = point2.0 - point1.0
    let dy = point2.1 - point1.1
    return sqrt(dx * dx + dy * dy)
}

let p1 = (0, 0)
let p2 = (3, 4)
echo distance(p1, p2)  // 5.0
```

### Именованные параметры-кортежи

```efen
alias Point = (x: Int, y: Int)

fn distance(p1: Point, p2: Point) -> Float {
    let dx = p2.x - p1.x
    let dy = p2.y - p1.y
    return sqrt(dx * dx + dy * dy)
}

let origin = (x: 0, y: 0)
let point = (x: 3, y: 4)
echo distance(origin, point)  // 5.0
```

## Pattern Matching

Кортежи можно использовать в pattern matching:

### Match с кортежами

```efen
let point = (10, 20)

match point {
    (0, 0): echo "Origin"
    (let x, 0): echo "On X-axis at ${x}"
    (0, let y): echo "On Y-axis at ${y}"
    let (x, y): echo "Point at (${x}, ${y})"
}
```

### Match с именованными элементами

```efen
let response = (status: 200, body: "OK")

match response {
    (status: 200, body: let body): echo "Success: ${body}"
    (status: 404, body: _): echo "Not found"
    (status: let status, body: _) where status >= 500: echo "Server error: ${status}"
    (status: let status, body: let body): echo "Response ${status}: ${body}"
}
```

### Вложенное сопоставление

```efen
let data = (result: (x: 10, y: 20), status: "ok")

match data {
    (result: (x: 0, y: 0), status: _): echo "Origin"
    (result: (x: let x, y: let y), status: "ok"): echo "Valid point: (${x}, ${y})"
    (result: _, status: "error"): echo "Error occurred"
}
```

## Tuple vs Struct

В EFEN есть как кортежи, так и структуры. Важно понимать разницу и знать, когда что использовать.

### Структуры в EFEN

Структуры создаются с помощью синтаксиса `Name { field: value }`:

```efen
struct Point {
    var x: Int
    var y: Int
}

let point = Point { x: 10, y: 20 }
```

### Ключевые отличия

| Аспект | Tuple | Struct |
|--------|-------|--------|
| Синтаксис создания | `(10, 20)` | `Point { x: 10, y: 20 }` |
| Определение типа | Не требуется | Требуется `struct` объявление |
| Изменяемость | Неизменяемы | Поля могут быть `var` или `let` |
| Доступ к элементам | `.0`, `.1` или `.name` | `.field` |
| Методы | Не поддерживают | Поддерживают |
| Композиция | Только вложенность | Встраивание типов |
| Декораторы | Нет | Поддерживают |

### Когда использовать Tuple

Используйте кортежи для:

```efen
// 1. Возврата нескольких значений из функции
fn getMinMax(numbers: [Int]) -> (min: Int, max: Int) {
    // ...
}

// 2. Временной группировки данных
let coords = (10, 20)
let rgb = (255, 0, 0)

// 3. Простых пар и триплетов
let pairs = [(1, "one"), (2, "two"), (3, "three")]

// 4. Локальных данных без методов
fn processData() {
    let temp = (value: 42, valid: true)
    if temp.valid {
        echo temp.value
    }
}
```

### Когда использовать Struct

Используйте структуры для:

```efen
// 1. Типов данных с поведением, предоставленным стратегией
struct Point {
    var x: Int
    var y: Int
}

strategy PointGeometry for Point {
    fn distance(other: Point) -> Float {
        let dx = other.x - x
        let dy = other.y - y
        return sqrt(dx * dx + dy * dy)
    }
}

// 2. Публичного API
struct User {
    let id: String
    var name: String
    var email: String
}

// 3. Сложных данных (4+ поля)
struct Configuration {
    var host: String
    var port: Int
    var timeout: Int
    var retries: Int
    var debug: Bool
}

// 4. Когда нужна композиция через встраивание
struct Entity {
    var name: String
    Position  // Встроенный тип
    Velocity  // Встроенный тип
}
```

### Примеры сравнения

```efen
// ❌ Плохо: кортеж для сложной структуры
alias User = (id: String, name: String, email: String, age: Int, active: Bool)

// ✅ Хорошо: struct для сложной структуры
struct User {
    let id: String
    var name: String
    var email: String
    var age: Int
    var active: Bool
}

// ✅ Хорошо: кортеж для простого возврата
fn getUserName(id: String) -> (name: String, found: Bool) {
    // ...
}

// ❌ Плохо: struct для одноразовой группировки
struct TempResult {
    var value: Int
    var valid: Bool
}
fn process() {
    let temp = TempResult { value: 42, valid: true }
    // Используется только здесь
}

// ✅ Лучше: кортеж
fn process() {
    let temp = (value: 42, valid: true)
    if temp.valid {
        echo temp.value
    }
}
```

## Особые случаи

### Пустой кортеж (Unit Type)

Пустой кортеж `()` представляет отсутствие значения:

```efen
let unit = ()

fn doSomething() -> () {
    echo "Done"
    return ()
}

// Эквивалентно Void
fn doSomething() -> Void {
    echo "Done"
}
```

### Одноэлементный кортеж

Для создания кортежа с одним элементом требуется завершающая запятая:

```efen
let single = (42,)    // Кортеж с одним элементом
let notTuple = (42)   // Просто число в скобках

let expr = (2 + 3)    // 5 (выражение)
let tuple = (2 + 3,)  // (5,) (кортеж)
```

### Swap переменных

Кортежи позволяют обмениваться значениями переменных без временной переменной:

```efen
var a = 10
var b = 20

(a, b) = (b, a)

echo a  // 20
echo b  // 10
```

### Кортежи в коллекциях

Кортежи можно использовать как элементы массивов и словарей:

```efen
// Массив кортежей
let points: [(Int, Int)] = [
    (0, 0),
    (10, 20),
    (30, 40)
]

// Итерация
for (x, y) in points {
    echo "Point: (${x}, ${y})"
}

// Словарь с кортежами как значениями
let users: [String: (name: String, age: Int)] = [
    "alice": (name: "Alice", age: 30),
    "bob": (name: "Bob", age: 25)
]
```

### Именованные элементы в деструктуризации

При деструктуризации можно использовать произвольные имена:

```efen
let person = (name: "Alice", age: 30)

// Имена в деструктуризации не обязаны совпадать
let (username, userAge) = person
echo username  // "Alice"
echo userAge   // 30

// Разбор по именам требует совпадения с именами элементов кортежа
let .{ name, age } = person
```

## Иммутабельность

Кортежи в EFEN неизменяемы — нельзя изменить отдельный элемент:

```efen
let point = (10, 20)
// point.0 = 30  // ❌ Ошибка: кортежи неизменяемы

// Можно только переприсвоить весь кортеж
var mutablePoint = (10, 20)
mutablePoint = (30, 40)  // ✅ OK
```

Если нужна изменяемость отдельных полей, используйте struct:

```efen
struct Point {
    var x: Int
    var y: Int
}

var point = Point { x: 10, y: 20 }
point.x = 30  // ✅ OK
```

## Примеры использования

### Возврат результата с ошибкой

```efen
fn divide(a: Float, b: Float) -> (result: Float?, error: String?) {
    if b == 0.0 {
        return (result: null, error: "Division by zero")
    }
    return (result: a / b, error: null)
}

let (result, error) = divide(10.0, 2.0)
if error != null {
    echo "Error: ${error}"
} else {
    echo "Result: ${result}"
}
```

### Парсинг данных

```efen
fn parseCoordinate(input: String) -> (x: Int, y: Int, valid: Bool) {
    let parts = input.split(",")
    if parts.count != 2 {
        return (x: 0, y: 0, valid: false)
    }

    let x = Int(parts[0])
    let y = Int(parts[1])

    if x == null || y == null {
        return (x: 0, y: 0, valid: false)
    }

    return (x: x!, y: y!, valid: true)
}

let (x, y, valid) = parseCoordinate("10,20")
if valid {
    echo "Coordinates: (${x}, ${y})"
}
```

### Итерация с индексами

```efen
let items = ["apple", "banana", "cherry"]
let indexed = items.enumerated()  // Возвращает [(Int, String)]

for (index, item) in indexed {
    echo "${index}: ${item}"
}
// 0: apple
// 1: banana
// 2: cherry
```

### Группировка связанных значений

```efen
fn analyzeArray(arr: [Int]) -> (sum: Int, avg: Float, min: Int, max: Int) {
    let sum = arr.reduce(0) => $0 + $1
    let avg = Float(sum) / Float(arr.count)
    let min = arr.min()!
    let max = arr.max()!

    return (sum: sum, avg: avg, min: min, max: max)
}

let stats = analyzeArray([1, 2, 3, 4, 5])
echo "Sum: ${stats.sum}"      // 15
echo "Average: ${stats.avg}"  // 3.0
echo "Min: ${stats.min}"      // 1
echo "Max: ${stats.max}"      // 5
```

## Смотрите также

- [Структуры](../structs.md) — Struct типы в EFEN
- [Деструктуризация](../destructuring.md) — Паттерны деструктуризации
- [Коллекции](collections.md) — Массивы и словари
- [Type Aliases](../type-aliases.md) — Алиасы типов
