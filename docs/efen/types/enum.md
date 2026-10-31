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

## Расширение

`enum` закрыт по умолчанию, как класс. `open enum` разрешает другим enum добавлять к нему значения; расширение
пишет базу после двоеточия, как подкласс (Edmond 2026-10-31):

```efen
// lang::
open enum Reason {
    program
    environment
    user
    cancellation
}

// программа
enum StorageReason: Reason {
    quota
    diskFull
}
```

Расширение объявляет только новые значения. Значения базы ему не принадлежат: `StorageReason.program` — ошибка.
Поэтому каждое значение `StorageReason` — значение `Reason`, и `StorageReason` годится там, где ждут `Reason`, как
подкласс там, где ждут базу:

```efen
fn reason() -> Reason nofail {
    return StorageReason.quota
}
```

Расширение закрыто, пока не написано `open enum StorageReason: Reason`. База у расширения одна. Расширить можно
только `open enum`; `final enum` пишет умолчание явно.

### Короткая запись

`.x` ищет значение только среди значений самого ожидаемого типа. Значение расширения там, где ждут базу, пишется с
именем типа:

```efen
let r: Reason = .quota                  // ошибка: у Reason нет значения quota
let r: Reason = StorageReason.quota     // верно
let s: StorageReason = .quota           // верно
```

Так же ищутся значения в образцах `match`. Поэтому чужое расширение не меняет смысл `.x` в коде, который его не
видит.

### Имена

Значение расширения не повторяет имя значения предка: `enum NetReason: Reason { user }` — ошибка. Иначе
`NetReason.user` попадало бы в чужую ветку там, где читатель видит `.user`. Это правило классов: метод с именем
метода базы не пишется без `override`. Два расширения одной базы могут объявить одно имя: `StorageReason.quota` и
`BillingReason.quota` различаются полными именами. Интерполяция значения расширения печатает полное имя:
`"StorageReason.quota"`.

### `match` по открытому enum

Множество значений открытого enum знает только сборка программы, поэтому `match` по нему требует ветку `_` или
`@extended _`:

```efen
fn describe(r: Reason) -> String {
    return match r {
        .program: "баг"
        .environment: "среда"
        .user: "ввод"
        .cancellation: "отмена"
        @extended _: "прочее"
    }
}
```

- `_` ловит всё неперечисленное.
- `@extended _` ловит значения расширений, а значения самого типа требует перечислить все. Если в `Reason` появится
  новое значение, каждый такой `match` перестанет собираться с ошибкой «не покрыто»: `@extended _` не прячет новые
  значения базы.
- `@extended _` — только ветка верхнего уровня `match`, только по открытому типу и не вместе с `_`.
- `match` по закрытому расширению (`StorageReason`) исчерпывающий без `_`.

Значение расширения в образце пишется `StorageReason.quota`; образец типа — `let s as StorageReason`; вне `match` —
`if r is let s as StorageReason`. Тип значения открытого enum определяет его тег, контракт `matchable` для такой
проверки не нужен.

### Перезапись места

Значение enum можно перезаписать целиком, поэтому места не следуют за подтипом. Параметр `mut`, `out` или `edit`
типа `Reason` принимает только место ровно типа `Reason`:

```efen
fn reset(r: out Reason) {
    r = .user
}

var s: StorageReason = .quota
reset(s)            // ошибка: в s оказалось бы значение, которого нет в StorageReason
```

По той же причине метод базы, который пишет `self` (`mut fn`), на значении расширения вызвать нельзя, если
расширение его не переопределило. `[StorageReason]` превращается в `[Reason]` только копией.

### Методы и контракты

`open fn` в базе, `override fn` в расширении, `final` — по правилам [классов](../classes.md#наследование-классов).
Метод базы с `match self` по открытому типу содержит `_` или `@extended _`, как любой такой `match`.

`conforms` базы наследуется. Синтезированные члены (`allCases`, `rawValue`, `==`, `Comparable`) компилятор строит
заново для расширения. Требование контракта, которое база реализовала сама и в котором `Self` стоит в результате (в
том числе `Self?` и `[Self]`) или в параметре `mut`, `out`, `edit`, а также каждое требование `mut fn`, расширение
обязано переопределить. Иначе ошибка в расширении с именем требования: метод базы вернул бы или записал значение
базы под видом значения расширения.

Значения одной иерархии сравниваются через общую базу: `r == StorageReason.quota`.

### Raw values

Raw-тип пишет только корень. Расширение наследует его и после двоеточия пишет только базу:

```efen
open enum StatusCode: Int {
    ok = 200
    notFound = 404
}

enum MyStatus: StatusCode {
    teapot = 418
}

StatusCode(rawValue: 418)   // MyStatus.teapot
```

- Для `Int` первое значение расширения задаётся явно, дальше действует автоинкремент внутри объявления.
- Для `String` значением по умолчанию служит имя.
- Повтор raw value во всей иерархии программы — ошибка сборки с местами обоих объявлений (Edmond 2026-10-31).
- `T(rawValue:)` ищет среди значений `T` и всех его расширений.

### `CaseIterable`

`T.allCases` у открытого enum перечисляет значения `T` и его расширений в порядке тегов (ниже).

### Сборка программы

Полное множество значений знает только сборка программы. Тест библиотеки собирается без программы, поэтому
`Reason.allCases`, `Reason(rawValue:)` и проверка повторов raw values в тесте библиотеки и в программе дают разный
результат. Проверка считается по тем же исходникам, что и сборка: `efen test` программы включает её тестовые файлы.

### Generic

Расширение generic-корня повторяет его параметры с теми же ограничениями: у `open enum Base<T: Hashable>` расширение
пишется `enum E<T: Hashable>: Base<T>`. Лишние или конкретные параметры — ошибка. Расширение, вложенное в generic-тип,
не упоминает его параметры; `Cache<Int>.Miss` и `Cache<String>.Miss` — один тип.

### Представление

- Все типы одной открытой иерархии, включая закрытые расширения, используют общий тег шириной 16 бит и общую
  нумерацию. Ширина не зависит от программы: раскладка `var source: Reason` одна и в рантайме, и в программе.
  Больше 65 536 значений в иерархии — ошибка сборки.
- Нумерация идёт обходом в глубину: значения типа в порядке объявления, затем его расширения. Расширения одной базы
  упорядочены по полному пути объявления (модуль, затем охватывающие типы) тем же сравнением, что `static let` в
  [классах](../classes.md); внутри модуля — по порядку объявления.
- Значения поддерева идут подряд, поэтому `is StorageReason` — проверка диапазона тегов.
- Значение открытого enum не пересекает границу динамической библиотеки: наружу из неё идут только функции
  `@abi(c)` ([сборка](../build-config.md)).

## Совместимость библиотек

Закрытая декларация `enum` закрыта в каждой версии программы. Библиотека может добавить
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

`@unknown _` относится к закрытым enum. У открытого enum ветку «остальное» дают `_` и `@extended _`
(«Расширение»). Добавить значение в открытый enum — ломающее изменение для каждого `match` с `@extended _` по нему,
для расширения с тем же именем значения и, если у enum есть raw-тип, для расширения с тем же raw value.

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

`open enum` и `open variant` расширяются по правилам классов (раздел «Расширение» и
[variant](variant.md#расширение)). `Family<Base>` — другое: открытый носитель видов хранения для layout, а не тип
значения.

## См. также

- [Variant types](variant.md) — constructors с payload
- [Structural union](../type-aliases.md#union-типы)
- [Match](../blocks/match.md)
- [Константы](constants.md)
