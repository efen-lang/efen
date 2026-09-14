# Variant types

`variant` объявляет номинальный закрытый tagged sum: каждое его значение создано
ровно одним именованным constructor. Constructor может не иметь payload либо
хранить собственный набор именованных полей.

```efen
variant ServerResponse {
    pending
    success { data: String }
    failure { code: Int, message: String }
}

let response = ServerResponse.failure(code: 404, message: "Not Found")
```

В нормативном тексте `variant` называется типом, а `pending`, `success` и
`failure` — его **constructors** или **cases**. Это устраняет двусмысленность
слова «вариант».

## Семантика sum of products

Variant type является алгебраическим типом данных: именованной дизъюнктной
суммой произведений. Выбирается ровно один constructor, а его поля образуют
произведение значений. Например:

```efen
variant Result<T, E> {
    ok { value: T }
    err { error: E }
}
```

соответствует сумме двух произведений: `ok × T + err × E`. Тег constructor
является частью семантики, поэтому одинаковый payload не объединяет cases:

```efen
variant Side {
    left { value: Int }
    right { value: Int }
}

let a = Side.left(value: 1)
let b = Side.right(value: 1) // b отличается от a
```

Компилятор выбирает физическую representation: fixed tagged union, косвенное
хранение или другую эквивалентную форму. Исходная программа не наблюдает этот
выбор.

## Constructors

Поля constructor всегда именованы и передаются с метками:

```efen
variant Barcode {
    upc { system: Int, manufacturer: Int, product: Int, check: Int }
    qrCode { code: String }
}

let product = Barcode.upc(
    system: 8,
    manufacturer: 85909,
    product: 51226,
    check: 3
)
let website = Barcode.qrCode(code: "https://example.com")
```

Один тип может смешивать constructors без payload и с payload. Если все cases
не несут данных, следует объявить [enum](enum.md), чтобы конечное перечисление
было видно из декларации.

## Pattern matching

Имя constructor в образце пишется с точкой. Его поля извлекаются
[оператором проекции `.{ }`](projection.md):

```efen
match response {
    .pending: print("Ожидание")
    .success.{ let data }: print("Получены данные: ${data}")
    .failure.{ let code, let message }:
        print("Ошибка ${code}: ${message}")
}
```

Ненужные поля можно опустить, а нужные — переименовать:

```efen
match product {
    .upc.{ let system }: print("Система: ${system}")
    .qrCode.{ code: let url }: print(url)
}
```

В образце `.{ }` копируемое поле связывается копией, uniquely-owned поле —
заимствованием. Передача владения требует явного `take`. Образец не создаёт
representation.

`match` без `_` обязан покрыть все constructors, доступные при компиляции.
Условия `where` могут уточнять один case:

```efen
match response {
    .success.{ let data } where data.length > 0: use(data)
    .success: reportEmpty()
    .failure.{ let code } where code >= 500: retry()
    .failure.{ let code, let message }: report(code, message)
    .pending: wait()
}
```

## Generic variant types

```efen
variant Result<T, E> {
    ok { value: T }
    err { error: E }
}

fn divide(a: Int, b: Int) -> Result<Float, String> {
    if b == 0 {
        return .err(error: "Division by zero")
    }
    return .ok(value: Float(a) / Float(b))
}
```

Optional остаётся встроенным типом `T?`; `Option<T>` — его стандартный alias, а
не отдельный runtime-container:

```efen
alias Option<T> = T?
```

## Рекурсивные variant types

Прямая рекурсия требует `indirect` у всего типа либо у конкретного constructor:

```efen
indirect variant Expression {
    number { value: Int }
    addition { left: Expression, right: Expression }
    multiplication { left: Expression, right: Expression }
}
```

```efen
variant Expression {
    number { value: Int }
    indirect addition { left: Expression, right: Expression }
    indirect multiplication { left: Expression, right: Expression }
}
```

Пример обхода:

```efen
fn evaluate(expr: Expression) -> Int {
    return match expr {
        .number.{ let value }: value
        .addition.{ let left, let right }: evaluate(left) + evaluate(right)
        .multiplication.{ let left, let right }: evaluate(left) * evaluate(right)
    }
}
```

## Методы, свойства и равенство

Variant type может объявлять методы и вычисляемые свойства. Равенство можно
синтезировать, когда его поддерживают поля всех constructors:

```efen
variant Message: Equatable {
    text { content: String }
    image { url: String, width: Int, height: Int }
}
```

## Вложенные типы

Как и другой номинальный тип, `variant` может содержать вложенные объявления:

```efen
variant Character {
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
```

## Закрытость и `@unknown _`

Набор constructors закрыт в пределах одной версии декларации. Библиотека может
добавить case в следующей версии; клиент использует `@unknown _`, если ему нужна
исходная совместимость с таким изменением:

```efen
match response {
    .success.{ let data }: use(data)
    .failure.{ let code, let message }: report(code, message)
    @unknown _: reportUnknown()
}
```

Эта ветка не превращает тип в открытую runtime-иерархию. Для открытого набора
проверенных exact-видов служит `Family<Base>`.

## Отличие от enum и structural union

```efen
enum Direction {
    north
    south
}

variant Side {
    left { value: Int }
    right { value: Int }
}

alias Scalar = Int | Float
```

- `enum` содержит только именованные значения без payload и может иметь raw
  values;
- `variant` вводит новые номинальные constructors и сохраняет их различие;
- `T | U` объединяет существующие типы структурно и не вводит constructors.

В частности, `Side.left(value: 1)` и `Side.right(value: 1)` различны благодаря
именам constructors; `T | U` таких имён не создаёт.

## Ограничения

- Raw values разрешены у `enum`, но не у `variant`.
- `CaseIterable` не синтезируется для `variant`.
- `variant` не наследуется и не расширяется из другого `variant`.
- Безымянных полей constructor нет.

## См. также

- [Enum](enum.md)
- [Structural union](../type-aliases.md#union-типы)
- [Match](../blocks/match.md)
- [Optional](optional.md)
