# Структуры (Structs)

Структуры в Efen — это легковесные типы-значения (value types), предназначенные для хранения простых данных и поддержки композиции.

## Содержание

- [Базовый синтаксис](#базовый-синтаксис)
- [Поля структур](#поля-структур)
- [Композиция структур](#композиция-структур)
- [Дженерик-структуры](#дженерик-структуры)
- [Семантика значений](#семантика-значений)
- [Отличия от классов](#отличия-от-классов)
- [Декораторы](#декораторы)

## Базовый синтаксис

Структура объявляется с помощью ключевого слова `struct`:

```efen
struct Point {
    var x: Int
    var y: Int
}

// Создание экземпляра
let point = Point(x: 10, y: 20)
```

## Поля структур

Структуры могут содержать изменяемые (`var`) и неизменяемые (`let`) поля.

```efen
struct Rectangle {
    let width: Int
    let height: Int
    var color: String = "black"
}

// Использование
var rect = Rectangle(width: 100, height: 50)
// rect.width = 200  // Ошибка: width неизменяемое
rect.color = "red"   // OK: color изменяемое, переменная объявлена через var
```

`let` запрещает перепривязать саму переменную. Запись в поле `var` разрешена,
если тип допускает изменение и связывание располагает правом `write`.

```efen
let frozen = Rectangle(width: 100, height: 50)
frozen.color = "red"
```

### Поля с значениями по умолчанию

```efen
struct Configuration {
    var host: String = "localhost"
    var port: Int = 8080
    var timeout: Int = 30
}

// Можно создать с дефолтными значениями
let config1 = Configuration {}

// Или переопределить нужные
let config2 = Configuration(port: 3000)
```

## Композиция структур

Efen поддерживает встраивание одной структуры в другую через указание имени типа.

### Встроенные типы

```efen
struct Position {
    var x: Int
    var y: Int
}

struct Entity {
    var name: String
    Position  // Встраивание Position
}

// При использовании поля Position становятся доступны напрямую
let entity = Entity {
    name: "Player",
    x: 100,
    y: 200
}

echo entity.x      // 100
echo entity.name   // "Player"
```

### Множественная композиция

```efen
struct Velocity {
    var dx: Int
    var dy: Int
}

struct Sprite {
    var texture: String
}

struct MovingSprite {
    Velocity
    Sprite
    var rotation: Float = 0.0
}

let sprite = MovingSprite {
    dx: 5,
    dy: 3,
    texture: "hero.png",
    rotation: 45.0
}
```

### Паттерн Mixin через композицию

```efen
struct Timestamped {
    var createdAt: Int
    var updatedAt: Int
}

struct Identifiable {
    var id: String
}

struct User {
    Timestamped
    Identifiable
    var name: String
    var email: String
}

let user = User {
    id: "user123",
    name: "Alice",
    email: "alice@example.com",
    createdAt: 1234567890,
    updatedAt: 1234567890
}
```

## Дженерик-структуры

Структуры поддерживают параметры типа.

```efen
struct Box<T> {
    var value: T
}

let intBox = Box<Int>(value: 42)
let stringBox = Box<String>(value: "hello")
```

### Композиция с дженериками

```efen
struct RefCounted<T> {
    var refCount: Int = 0
    T  // Встраивание дженерик-типа
}

struct Data {
    var bytes: [Byte]
}

// RefCounted<Data> будет иметь поля: refCount и bytes
let data = RefCounted<Data> {
    refCount: 1,
    bytes: [0x01, 0x02, 0x03]
}
```

### Ограничения дженерик-типов

```efen
struct Wrapper<T: Comparable> {
    var value: T
}

strategy WrapperComparison<T> for Wrapper<T> {
    fn isGreaterThan(other: Wrapper<T>) -> Bool {
        return value > other.value
    }
}
```

Структуры содержат только данные. Методы и другое поведение предоставляются
стратегиями; их функции не становятся физическими полями структуры. Внешний
пакет может применить стратегию к структуре только при её `allow strategies`.

## Семантика значений

Структуры являются типами-значениями, но это само по себе не разрешает
копирование. Явную копию даёт соответствие `Copyable`, неявную —
`ImplicitlyCopyable`, а перенос существующего значения — независимый contract
`Movable`.

```efen
struct Point {
    conforms ImplicitlyCopyable

    var x: Int
    var y: Int
}

var p1 = Point(x: 10, y: 20)
var p2 = p1  // Создается копия

p2.x = 30

echo p1.x  // 10 - оригинал не изменился
echo p2.x  // 30
```

### Copy-on-write оптимизация

Тип может предоставить copy-on-write и соответствовать `ImplicitlyCopyable`,
если неявное копирование сохраняет значение и не меняет наблюдаемое состояние:

```efen
struct LargeData {
    conforms ImplicitlyCopyable

    var buffer: [Byte]  // Большой массив
}

let data1 = LargeData(buffer: [/* ... */])
let data2 = data1  // Копия не создается до модификации

// Копия создается только при первом изменении
data2.buffer[0] = 0xFF
```

## Отличия от классов

| Аспект | Структура | Класс |
|--------|-----------|-------|
| Семантика | Тип-значение | Ссылочный тип |
| Копирование | По `Copyable` / `ImplicitlyCopyable` | По тем же контрактам |
| Наследование | Нет | Да |
| Композиция | Через встраивание | Через наследование |
| Инициализация | Struct literal | Constructor (init) |
| Методы | Нет | Да |
| Размер | Статический | Динамический |

Отсутствие наследования не запрещает встраивание общей структуры:

```efen
struct Function {
    BaseNode
    var body: HirNodeId
}
```

`Function` не становится подтипом `BaseNode` и не получает vtable или
обязательный prefix layout. Встраивание предоставляет обычные логические поля.
Storage projection населения может физически разнести встроенный `BaseNode` и
остальные поля по разным columns, сохранив тот же API. См.
[колоночные layout](memory/columnar-layouts.md).

### Когда использовать структуры

✅ **Используйте структуры для:**
- Простых типов данных (Point, Size, Rectangle)
- Неизменяемых данных
- Небольших коллекций данных
- Типов, которые часто копируются
- Моделей данных без поведения

❌ **Не используйте структуры для:**
- Сложных объектов с поведением
- Когда нужна идентичность объектов
- Когда нужно наследование
- Больших данных, требующих ссылочной семантики

## Декораторы

Структуры поддерживают декораторы на уровне объявления и полей.

```efen
@serializable
@packed
struct NetworkPacket {
    @bigEndian
    var header: Int32

    @compressed
    var payload: [Byte]

    var checksum: Int32
}
```

### Декораторы для генерации кода

```efen
@equatable
@hashable
struct Person {
    var name: String
    var age: Int
}

// Декораторы автоматически генерируют:
// - fn equals(other: Person) -> Bool
// - fn hash() -> Int
```

## Вложенные структуры

```efen
struct Outer {
    struct Inner {
        var value: Int
    }

    var data: Inner
}

// Использование
let outer = Outer {
    data: Outer.Inner(value: 42)
}
```

## Работа с памятью

### Размер и выравнивание

```efen
struct Compact {
    var a: Byte   // 1 байт
    var b: Byte   // 1 байт
    var c: Int16  // 2 байта
}  // Размер: 4 байта с выравниванием

@packed
struct Packed {
    var a: Byte
    var b: Byte
    var c: Int16
}  // Размер: 4 байта без padding
```

## Примеры использования

### Структура для 2D графики

```efen
struct Vector2D {
    var x: Float
    var y: Float
}

struct Transform2D {
    Vector2D    // position
    var rotation: Float = 0.0
    var scale: Float = 1.0
}

let transform = Transform2D {
    x: 100.0,
    y: 200.0,
    rotation: 45.0
}
```

### Структура для конфигурации

```efen
struct DatabaseConfig {
    var host: String = "localhost"
    var port: Int = 5432
    var username: String
    var password: String
    var maxConnections: Int = 10
}

let config = DatabaseConfig {
    username: "admin",
    password: "secret"
}
```

### Структура с временными метками

```efen
struct Timestamped {
    var createdAt: Int
    var updatedAt: Int
}

struct Article {
    Timestamped
    var title: String
    var content: String
    var author: String
}
```

## Лучшие практики

1. **Держите структуры простыми**: Используйте для данных, а не для поведения
2. **Используйте композицию**: Встраивайте другие структуры вместо дублирования полей
3. **Значения по умолчанию**: Предоставляйте разумные дефолты для необязательных полей
4. **Неизменяемость**: Предпочитайте `let` вместо `var`, где возможно
5. **Документируйте**: Поясняйте назначение структуры и её полей

```efen
/// Представляет точку в 2D пространстве
struct Point {
    /// X координата
    var x: Int

    /// Y координата
    var y: Int
}
```

## Смотрите также

- [Классы](classes.md)
- [Дженерики](generics.md)
- [Декораторы](decorators.md)
- [Типы](types/type.md)
