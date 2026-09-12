# Match и сопоставление с образцом

В `Efen` одна конструкция сопоставления с образцом (pattern matching) — `match`.
Она одновременно оператор и выражение: её можно поставить отдельной инструкцией
и можно присвоить её результат переменной.

Ветка записывается как `образец: выражение` либо `образец: { блок }`.
Умолчание обозначается `_`. Проваливания в следующую ветку нет, покрытие
обязательно.

## Базовый синтаксис

```efen
let number = 3

match number {
    1: print("Один")
    2: print("Два")
    3: print("Три")
    _: print("Другое число")
}
// Три
```

## match как выражение

Результат выбранной ветки — значение всего `match`:

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

## Блок в ветке

Если ветка содержит несколько инструкций, тело заключается в фигурные скобки.
Значением ветки становится последнее выражение блока:

```efen
match number {
    1: {
        log("Обрабатываем единицу")
        print("Один")
    }
    _: print("Другое число")
}
```

## Полнота покрытия (Exhaustiveness)

`match` обрабатывает все возможные значения. Если случаи не покрыты явно,
нужна ветка `_`:

```efen
let number = 5

match number {
    1: print("Один")
    2: print("Два")
// ❌ Ошибка: match должен быть исчерпывающим
}
```

```efen
// ✅ Правильно
match number {
    1: print("Один")
    2: print("Два")
    _: print("Другое число")
}
```

## Несколько образцов в одной ветке

Альтернативы разделяются знаком `|`:

```efen
let character = "a"

match character {
    "a" | "e" | "i" | "o" | "u": print("Гласная")
    "b" | "c" | "d" | "f" | "g": print("Согласная")
    _: print("Неизвестный символ")
}
```

## Диапазоны

Образцом может быть интервал. Операторы границ в этой позиции создают
interval-pattern, а не runtime-значение `Interval`; constructor не вызывается и
возможность последовательного шага не требуется:

```efen
let count = 25

match count {
    0: print("Ноль")
    1..<10: print("Несколько")
    10..<100: print("Десятки")
    100..<1000: print("Сотни")
    _: print("Очень много")
}
// "Десятки"
```

## Кортежи (Tuples)

```efen
let point = (1, 1)

match point {
    (0, 0): print("Начало координат")
    (_, 0): print("На оси X")
    (0, _): print("На оси Y")
    (-2..2, -2..2): print("Внутри квадрата")
    _: print("За пределами квадрата")
}
// "Внутри квадрата"
```

## Value Binding

Связывает только `let`. Голое имя в образце ничего не объявляет — оно
сравнивается со значением, которое это имя уже имеет. `let` стоит либо перед
одним именем (`(let x, 0)`), либо перед составным образцом (`let (x, y)`) — тогда
связываются все голые имена внутри него.

Голое имя с заглавной буквы сравнением не является: по правилу регистра это
образец типа или состояния — `Open:` в разборе typestate, `obj is MyInterface`.

```efen
let expected = 404

match code {
    expected: print("Ожидаемый код")   // сравнение с переменной expected
    let other: print("Другой: ${other}")  // связывание
}
```

Из проверяемого выражения можно извлекать значения:

```efen
let point = (2, 3)

match point {
    (0, 0): print("Начало координат")
    (let x, 0): print("На оси X, координата x = ${x}")
    (0, let y): print("На оси Y, координата y = ${y}")
    (let x, let y): print("Точка (${x}, ${y})")
}
// "Точка (2, 3)"
```

Короткая форма для извлечения всех значений — `let` перед всем образцом:

```efen
match point {
    let (x, y): print("Точка (${x}, ${y})")
}
```

## Условия where

К образцу можно добавить дополнительное условие:

```efen
let point = (1, -1)

match point {
    let (x, y) where x == y: print("Точка на диагонали y = x")
    let (x, y) where x == -y: print("Точка на диагонали y = -x")
    let (x, y): print("Просто точка (${x}, ${y})")
}
// "Точка на диагонали y = -x"
```

Более сложный пример:

```efen
let number = 25

match number {
    let n where n < 0: print("Отрицательное: ${n}")
    let n where n % 2 == 0: print("Чётное: ${n}")
    let n where n % 2 == 1: print("Нечётное: ${n}")
    _: print("Неизвестное число")
}
// "Нечётное: 25"
```

## match с enum

Вариант enum в образце пишется с точкой:

```efen
enum Direction {
    north
    south
    east
    west
}

let direction = Direction.north

match direction {
    .north: print("На север")
    .south: print("На юг")
    .east: print("На восток")
    .west: print("На запад")
}
// "На север"
```

### Enum с ассоциированными значениями

Поля варианта именованные, поэтому образец перечисляет их
[оператором проекции `.{ }`](../types/projection.md) после имени варианта.
В образце `.{ }` связывает копии значений полей и представления не создаёт:

```efen
enum Barcode {
    upc { system: Int, manufacturer: Int, product: Int, check: Int }
    qrCode { code: String }
}

let productCode = Barcode.upc(system: 8, manufacturer: 85909, product: 51226, check: 3)

match productCode {
    .upc.{ let system, let manufacturer, let product, let check }:
        print("UPC: ${system}, ${manufacturer}, ${product}, ${check}")
    .qrCode.{ let code }:
        print("QR код: ${code}")
}
// "UPC: 8, 85909, 51226, 3"
```

Ненужные поля можно опустить, а нужные — переименовать:

```efen
match productCode {
    .upc.{ let system }: print("Система нумерации: ${system}")
    .qrCode.{ code: let url }: print("QR код: ${url}")
}
```

## match с optional

```efen
let optionalNumber: Int? = 42

match optionalNumber {
    null: print("Значение отсутствует")
    let value?: print("Значение: ${value}")
}
// "Значение: 42"
```

## Составные образцы с привязкой

Альтернативы могут привязывать одно и то же имя:

```efen
let point = (1, 0)

match point {
    (let distance, 0) | (0, let distance):
        print("Расстояние от начала координат: ${distance}")
    _: print("Не на оси")
}
```

## Pattern Matching с типами

Можно проверять типы значений:

```efen
let value: Any = "Hello"

match value {
    let str as String: print("Строка: ${str}")
    let num as Int: print("Число: ${num}")
    let arr as [Int]: print("Массив целых чисел")
    _: print("Неизвестный тип")
}
// "Строка: Hello"
```

## Сложные образцы

Образцы разных видов комбинируются:

```efen
let result = (status: 200, data: "OK")

match result {
    (200, let data): print("Успех: ${data}")
    (400..499, let data): print("Ошибка клиента: ${data}")
    (500..599, let data): print("Ошибка сервера: ${data}")
    _: print("Неизвестный статус")
}
```

## match в функциях

```efen
fn describe(point: (Int, Int)) -> String {
    return match point {
        (0, 0): "Начало координат"
        (_, 0): "На оси X"
        (0, _): "На оси Y"
        let (x, y) where x == y: "На диагонали y = x"
        let (x, y): "Точка (${x}, ${y})"
    }
}

print(describe(point: (0, 0)))  // "Начало координат"
print(describe(point: (3, 3)))  // "На диагонали y = x"
```

## Вложенный match

```efen
let point = (1, 2)

match point {
    (0, 0): print("Начало координат")
    (let x, let y): match (x > 0, y > 0) {
        (true, true): print("Первая четверть")
        (false, true): print("Вторая четверть")
        (false, false): print("Третья четверть")
        (true, false): print("Четвёртая четверть")
    }
}
```

## @unknown _

Для enum, которые могут быть расширены в будущем:

```efen
enum Status {
    success
    pending
    error
}

let status = Status.success

match status {
    .success: print("Успешно")
    .pending: print("В процессе")
    @unknown _: {
        // Компилятор выдаст предупреждение, если появятся новые варианты
        print("Неизвестный статус")
    }
}
```

## Рекомендации

1. **Используйте `match` вместо длинных if-else цепочек** когда проверяете одно значение
2. **Предпочитайте сопоставление с образцом** явным проверкам типов
3. **Используйте where** для дополнительных условий
4. **Используйте value binding** для извлечения значений
5. **Покрывайте все случаи** — добавляйте ветку `_`, когда покрытие неполное
6. **Объединяйте похожие образцы через `|`** для уменьшения дублирования

## Сравнение с другими языками

### Отличия от C/C++/PHP:
- Ветка не проваливается в следующую
- Полнота покрытия проверяется компилятором
- `match` возвращает значение
- Образцом может быть кортеж, диапазон, тип или вариант enum

### Общее со Swift:
- Образцы с условием `where`
- Привязка значений
- Работа с enum и optional

## См. также

- [if.md](if.md) — Условные конструкции
- [guard.md](guard.md) — Early exit с guard
- [loops.md](loops.md) — Циклы
