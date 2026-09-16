# Enum (перечисления)

`enum` объявляет конечное перечисление именованных значений. Ни одно значение
`enum` не несёт собственного payload: если хотя бы один случай должен хранить
поля, объявляется [variant type](variant.md).

```efen
enum Direction {
    north
    south
    east
    west
}

let heading = Direction.north
let destination: Direction = .east
```

Имена типов начинаются с заглавной буквы, имена значений `enum` — со строчной.
При известном ожидаемом типе квалификатор можно опустить.

## Семантика

Значение `enum` является ровно одним элементом объявленного конечного множества.
Оно не содержит скрытого пользовательского значения и не является числом или
строкой только потому, что компилятор может представить его целочисленным тегом.

Поля у значения `enum` запрещены:

```efen
// Ошибка: error хранит payload, поэтому это должен быть variant.
enum Status {
    ready
    error { message: String }
}
```

Правильная декларация такого типа:

```efen
variant Status {
    ready
    error { message: String }
}
```

## Сопоставление с образцом

Значение `enum` в образце пишется с точкой:

```efen
match heading {
    .north: print("Север")
    .south: print("Юг")
    .east: print("Восток")
    .west: print("Запад")
}
```

`match` без `_` обязан покрыть все объявленные значения. Подробнее см.
[сопоставление с образцом](../blocks/match.md).

## Raw values

`enum` может задавать внешнее значение каждого элемента. Raw value является
отображением для преобразования, сериализации или ABI, а не payload отдельного
случая.

```efen
enum StatusCode: Int {
    ok = 200
    created = 201
    badRequest = 400
    notFound = 404
}

let code = StatusCode.notFound
print(code.rawValue) // 404
```

Для `Int` разрешён автоинкремент:

```efen
enum Priority: Int {
    low = 1
    medium
    high
    critical
}
```

Для `String` значением по умолчанию служит имя:

```efen
enum HttpMethod: String {
    get = "GET"
    post = "POST"
    put = "PUT"
    delete = "DELETE"
}
```

Преобразование из raw value возвращает optional:

```efen
let method = HttpMethod(rawValue: "POST") // HttpMethod?
let invalid = HttpMethod(rawValue: "INVALID") // null
```

Raw values принадлежат только `enum`. У `variant` разные constructors могут
нести значения разных типов, поэтому единого raw-типа у него нет.

## Методы и свойства

`enum` может объявлять поведение так же, как другой номинальный тип:

```efen
enum Direction {
    north
    south
    east
    west

    fn opposite -> Direction {
        return match self {
            .north: .south
            .south: .north
            .east: .west
            .west: .east
        }
    }
}
```

## Перечисление всех значений

Поскольку множество значений конечно и ни одно из них не требует payload,
`CaseIterable` может сгенерировать их полный список:

```efen
enum Direction {
    conforms CaseIterable

    north
    south
    east
    west
}

for direction in Direction.allCases {
    print(direction)
}
```

`CaseIterable` не применяется к `variant`: для constructor с полем `Int` или
`String` нельзя сгенерировать конечный список всех значений.

## Равенство и порядок

Значения одного `enum` автоматически поддерживают равенство. `enum` с raw values
упорядочиваемого типа может явно запросить `Comparable`:

```efen
enum Priority: Int {
    conforms Comparable

    low = 1
    medium = 2
    high = 3
}

print(Priority.low < Priority.high)
```

## Вложенные enum

`enum` может принадлежать другому типу:

```efen
struct Character {
    enum Weapon {
        sword
        bow
        staff
    }

    var weapon: Weapon
}
```

## Совместимость библиотек

Декларация `enum` закрыта в каждой версии программы. Библиотека может добавить
значение в следующей версии; `@unknown _` позволяет клиенту сохранить исходную
совместимость и получить предупреждение о новом случае:

```efen
match status {
    .connected: print("Подключено")
    .disconnected: print("Отключено")
    @unknown _: print("Неизвестный статус")
}
```

`@unknown _` не делает `enum` открытым во время выполнения.

## Enum, variant и structural union

Это три разные конструкции:

```efen
enum Direction {
    north
    south
}

variant Result<T, E> {
    ok { value: T }
    err { error: E }
}

alias ID = Int | String
```

- `enum` — конечное перечисление значений без payload;
- `variant` — номинальный закрытый tagged sum с именованными constructors;
- `T | U` — structural union существующих типов без новых constructors.

Обычное перечисление теоретически является частным случаем sum type, но Efen
разделяет декларации намеренно: наличие payload видно уже по ключевому слову.

`enum` и `variant` не поддерживают наследование. Расширяемая во время компиляции
иерархия отдельных exact-типов выражается не ими, а `Family<Base>`.

## См. также

- [Variant types](variant.md) — constructors с payload
- [Structural union](../type-aliases.md#union-типы)
- [Match](../blocks/match.md)
- [Константы](constants.md)
