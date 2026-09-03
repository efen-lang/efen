# Switch, Match и Pattern Matching

В `Efen` есть две конструкции для сопоставления с образцами (pattern matching):
- **`switch`** — оператор (statement) с ключевым словом `case`
- **`match`** — выражение (expression) без ключевого слова `case` (Rust-style)

Обе конструкции поддерживают множество типов образцов, обязательную полноту покрытия
и отсутствие проваливания (no fallthrough по умолчанию).

## switch (statement)

`switch` — это оператор, который выполняет код в зависимости от значения. Использует ключевое слово `case`:

```efen
let number = 3

switch number {
    case 1:
        print("Один")
    case 2:
        print("Два")
    case 3:
        print("Три")
    default:
        print("Другое число")
}
// Три
```

## match (expression)

`match` — это выражение в стиле Rust, которое возвращает значение. **Не использует** ключевое слово `case`:

```efen
let number = 2
let description = match number {
    1: "Один"
    2: "Два"
    3: "Три"
    _: "Другое число"
}

print(description) // "Два"
```

### Различия switch и match

| Аспект | `switch` | `match` |
|--------|----------|---------|
| Тип | Statement (оператор) | Expression (выражение) |
| Ключевое слово `case` | Да | Нет |
| Default clause | `default:` | `_:` |
| Возвращает значение | Нет | Да |
| Тело case | Блок операторов | Выражение или блок |

## Полнота покрытия (Exhaustiveness)

`Switch` должен обрабатывать все возможные значения. Если все случаи не покрыты явно,
необходим блок `default`:

```efen
let number = 5

switch number {
case 1:
    print("Один")
case 2:
    print("Два")
// ❌ Ошибка: switch должен быть исчерпывающим
}
```

```efen
// ✅ Правильно
switch number {
case 1:
    print("Один")
case 2:
    print("Два")
default:
    print("Другое число")
}
```

## Множественные значения в case

Один `case` может проверять несколько значений:

```efen
let character = "a"

switch character {
case "a", "e", "i", "o", "u":
    print("Гласная")
case "b", "c", "d", "f", "g":
    print("Согласная")
default:
    print("Неизвестный символ")
}
```

## Диапазоны в case

Можно использовать диапазоны для проверки:

```efen
let count = 25

switch count {
case 0:
    print("Ноль")
case 1..<10:
    print("Несколько")
case 10..<100:
    print("Десятки")
case 100..<1000:
    print("Сотни")
default:
    print("Очень много")
}
// "Десятки"
```

## Кортежи (Tuples)

`Switch` отлично работает с кортежами:

```efen
let point = (1, 1)

switch point {
case (0, 0):
    print("Начало координат")
case (_, 0):
    print("На оси X")
case (0, _):
    print("На оси Y")
case (-2...2, -2...2):
    print("Внутри квадрата")
default:
    print("За пределами квадрата")
}
// "Внутри квадрата"
```

## Value Binding

Можно извлекать значения из проверяемого выражения:

```efen
let point = (2, 3)

switch point {
case (0, 0):
    print("Начало координат")
case (let x, 0):
    print("На оси X, координата x = ${x}")
case (0, let y):
    print("На оси Y, координата y = ${y}")
case (let x, let y):
    print("Точка (${x}, ${y})")
}
// "Точка (2, 3)"
```

Короткая форма для извлечения всех значений:

```efen
case let (x, y):
    print("Точка (${x}, ${y})")
```

## Условия where

К `case` можно добавить дополнительные условия:

```efen
let point = (1, -1)

switch point {
case let (x, y) where x == y:
    print("Точка на диагонали y = x")
case let (x, y) where x == -y:
    print("Точка на диагонали y = -x")
case let (x, y):
    print("Просто точка (${x}, ${y})")
}
// "Точка на диагонали y = -x"
```

Более сложный пример:

```efen
let number = 25

switch number {
case let n where n < 0:
    print("Отрицательное: ${n}")
case let n where n % 2 == 0:
    print("Чётное: ${n}")
case let n where n % 2 == 1:
    print("Нечётное: ${n}")
default:
    print("Неизвестное число")
}
// "Нечётное: 25"
```

## Switch с enum

`Switch` идеально подходит для работы с перечислениями:

```efen
enum Direction {
    north
    south
    east
    west
}

let direction = Direction.north

switch direction {
case north:
    print("На север")
case south:
    print("На юг")
case east:
    print("На восток")
case west:
    print("На запад")
}
// "На север"
```

### Enum с ассоциированными значениями

```efen
enum Barcode {
    upc: Int, Int, Int, Int
    qrCode: String
}

let productCode = Barcode.upc(8, 85909, 51226, 3)

switch productCode {
case upc numberSystem, manufacturer, product, check:
    print("UPC: ${numberSystem}, ${manufacturer}, ${product}, ${check}")
case qrCode code:
    print("QR код: ${code}")
}
// "UPC: 8, 85909, 51226, 3"
```

Короткая форма:

```efen
switch productCode {
case .upc(numberSystem, manufacturer, product, check):
    print("UPC: ${numberSystem}, ${manufacturer}, ${product}, ${check}")
case .qrCode(code):
    print("QR код: ${code}")
}
```

## Switch с optional

Можно проверять optional значения:

```efen
let optionalNumber: Int? = 42

switch optionalNumber {
case null:
    print("Значение отсутствует")
case let value?:
    print("Значение: ${value}")
}
// "Значение: 42"
```

## Составные case

Несколько case с одинаковым телом можно объединить:

```efen
let character = "e"

switch character {
case "a", "e", "i", "o", "u":
    print("Гласная буква")
default:
    print("Не гласная")
}
```

С value binding:

```efen
let point = (1, 0)

switch point {
case (let distance, 0), (0, let distance):
    print("Расстояние от начала координат: ${distance}")
default:
    print("Не на оси")
}
```

## Проваливание (Fallthrough)

По умолчанию проваливания нет. Для явного проваливания используйте `fallthrough`:

```efen
let number = 5

switch number {
case 5:
    print("Пять")
    fallthrough
case 4:
    print("Четыре или меньше")
default:
    print("Другое")
}
// Выведет:
// Пять
// Четыре или меньше
```

**Примечание**: Использование `fallthrough` не рекомендуется без крайней необходимости.

## Pattern Matching с типами

Можно проверять типы значений:

```efen
let value: Any = "Hello"

switch value {
case let str as String:
    print("Строка: ${str}")
case let num as Int:
    print("Число: ${num}")
case let arr as [Int]:
    print("Массив целых чисел")
default:
    print("Неизвестный тип")
}
// "Строка: Hello"
```

## Сложные паттерны

Можно комбинировать различные паттерны:

```efen
let result = (status: 200, data: "OK")

switch result {
case (200, let data):
    print("Успех: ${data}")
case (400...499, let data):
    print("Ошибка клиента: ${data}")
case (500...599, let data):
    print("Ошибка сервера: ${data}")
default:
    print("Неизвестный статус")
}
```

## match в функциях

`match` как выражение удобно использовать в функциях:

```efen
fn describe(point: (Int, Int)) -> String {
    return match point {
        (0, 0): "Начало координат"
        (_, 0): "На оси X"
        (0, _): "На оси Y"
        (x, y) where x == y: "На диагонали y = x"
        (x, y): "Точка (${x}, ${y})"
    }
}

print(describe(point: (0, 0)))  // "Начало координат"
print(describe(point: (3, 3)))  // "На диагонали y = x"
```

## Вложенные switch

Switch может быть вложенным:

```efen
let point = (1, 2)

switch point {
case (0, 0):
    print("Начало координат")
case (let x, let y):
    switch (x > 0, y > 0) {
    case (true, true):
        print("Первая четверть")
    case (false, true):
        print("Вторая четверть")
    case (false, false):
        print("Третья четверть")
    case (true, false):
        print("Четвёртая четверть")
    }
}
```

## @unknown default

Для работы с enum, которые могут быть расширены в будущем:

```efen
enum Status {
    case success
    case pending
    case error
}

let status = Status.success

switch status {
case .success:
    print("Успешно")
case .pending:
    print("В процессе")
@unknown default:
    // Компилятор выдаст предупреждение, если добавятся новые case
    print("Неизвестный статус")
}
```

## Рекомендации

1. **Используйте switch/match вместо длинных if-else цепочек** когда проверяете одно значение
2. **Используйте match для выражений**, switch для операторов
3. **Предпочитайте pattern matching** вместо явных проверок типов
4. **Используйте where** для дополнительных условий
5. **Избегайте fallthrough** если он не критически необходим
6. **Используйте value binding** для извлечения значений
7. **Покрывайте все случаи** — используйте `default:` или `_:` когда необходимо
8. **Группируйте похожие case** для уменьшения дублирования

## Сравнение с другими языками

### Отличия от C/C++/PHP:
- Нет проваливания по умолчанию (no implicit fallthrough)
- Обязательная полнота покрытия
- Switch как выражение
- Мощный pattern matching

### Общее со Swift:
- Pattern matching с where
- Value binding
- Работа с enum и optional
- Switch как выражение

## См. также

- [if.md](if.md) — Условные конструкции
- [guard.md](guard.md) — Early exit с guard
- [loops.md](loops.md) — Циклы
