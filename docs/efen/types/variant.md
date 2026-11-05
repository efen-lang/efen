# Вариантные типы: `variant`

`variant` объявляет размеченное объединение: значение принадлежит ровно одному
из перечисленных случаев. Каждый случай имеет имя и может хранить собственный
набор именованных полей.

Тип является **номинальным**: его определяет объявление, поэтому два типа
с одинаковыми случаями и полями остаются разными типами. Набор случаев
**закрыт**: все они перечислены в объявлении, добавить случай извне нельзя.

```efen
variant ServerResponse {
    pending
    success { let data: String }
    failure { let code: Int, let message: String }
}

let response = ServerResponse.failure(code: 404, message: "Not Found")
```

В этом примере `ServerResponse` — тип с тремя случаями: `pending`, `success`
и `failure`. Запись `ServerResponse.failure(code: 404, message: "Not Found")`
создаёт значение случая `failure` и задаёт его поля.

## Семантика sum of products

Variant type является алгебраическим типом данных: именованной дизъюнктной
суммой произведений. Выбирается ровно один constructor, а его поля образуют
произведение значений. Например:

```efen
variant Result<T, E> {
    ok { let value: T }
    err { let error: E }
}
```

соответствует сумме двух произведений: `ok × T + err × E`. Тег constructor
является частью семантики, поэтому одинаковый payload не объединяет cases:

```efen
variant Side {
    left { let value: Int }
    right { let value: Int }
}

let a = Side.left(value: 1)
let b = Side.right(value: 1) // b отличается от a
```

Компилятор выбирает физическую representation: fixed tagged union, косвенное
хранение или другую эквивалентную форму. Исходная программа не наблюдает этот
выбор. Исключение — открытый variant: его схему хранения выбирает корень
(«Расширение»).

## Constructors

Поля constructor всегда именованы и передаются с метками:

```efen
variant Barcode {
    upc { let system: Int, let manufacturer: Int, let product: Int, let check: Int }
    qrCode { let code: String }
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

В образце `.{ }` поле типа `ImplicitlyCopyable` (`Int`, `Float`) связывается копией, любое
другое — вторым именем того же значения, а не копией: копию
даёт только `copy`, передачу владения — `take` ([связывание существующего значения](../types/ownership.md#связывание-существующего-значения)). Образец не создаёт
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
    ok { let value: T }
    err { let error: E }
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
    number { let value: Int }
    addition { let left: Expression, let right: Expression }
    multiplication { let left: Expression, let right: Expression }
}
```

```efen
variant Expression {
    number { let value: Int }
    indirect addition { left: Expression, right: Expression }
    indirect multiplication { left: Expression, right: Expression }
}
```

Данные constructor с `indirect` лежат в куче, в значении остаются тег и указатель на них:

- Создание такого значения выделяет память и может бросить `AllocationError`, как любой конструктор, который
  выделяет память. При провале конструктор ставит в указатель NULL: он видит не само значение, а его проекцию со
  своими правилами. Затем недостроенное значение разрушается.
- `copy e` — глубокая копия: каждый блок выделяется заново, копия может бросить `AllocationError`. `clone e` у
  `indirect`-variant без счётчика ссылок — ошибка ([`clone`](../contracts.md#оператор-clone)).
- `indirect`-variant не бывает `ImplicitlyCopyable`: его копия выделяет память, поэтому в функцию он передаётся по
  ссылке.

```efen
let e = Expression.addition(left: a, right: b)   // выделяет; может бросить AllocationError
let f = copy e                                    // глубокая копия дерева
evaluate(e)                                       // по ссылке, без копии
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
variant Message {
    conforms Equatable

    text { let content: String }
    image { let url: String, let width: Int, let height: Int }
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

    warrior { let weapon: Weapon, let armor: Armor }
    mage { let weapon: Weapon }
    archer { let weapon: Weapon }
}
```

## Расширение

`open variant` расширяется так же, как [`open enum`](enum.md#расширение): расширение добавляет новые constructors,
его значения годятся там, где ждут базу. Правила enum действуют и здесь: короткая запись,
имена, `match` с `_` или `@extended _`, перезапись места, методы и контракты, generic, представление тега, сборка
программы. Raw values и `CaseIterable` у variant нет и при расширении.

```efen
open indirect variant Expression {
    number { let value: Int }
    addition { let left: Expression, let right: Expression }
}

variant ExtraExpression: Expression {
    negation { let operand: Expression }
}

fn evaluate(expr: Expression) -> Int {
    return match expr {
        .number.{ let value }: value
        .addition.{ let left, let right }: evaluate(left) + evaluate(right)
        ExtraExpression.negation.{ let operand }: -evaluate(operand)
        @extended _: 0
    }
}
```

Расширение не меняет поля constructors базы и расширяет только `variant`, не `enum`.

### Схемы хранения

Размер значения variant — тег плюс наибольший constructor. У открытого variant наибольший constructor может прийти
из расширения в другом пакете. Корень выбирает одну из двух схем:

- **В значении** (по умолчанию). Размер открытого variant считает сборка программы по всей иерархии. Кучи нет.
- **В куче** — `conforms IndirectExtensions` у корня. Данные каждого constructor, объявленного не в корне, лежат в
  куче, как у `indirect`; размер корня известен в его пакете.

```efen
open variant Shape {
    conforms IndirectExtensions
    dot
}
```

Правила схем:

- Все типы иерархии, включая закрытые расширения, имеют раскладку корня. Поэтому значение расширения копируется
  в место базы без перевода.
- `IndirectExtensions` пишет только корень, безусловно и прямо в своём теле: не под `#if`, не через уточняющий
  контракт; ограничением generic-параметра контракт не служит. Это контракт `lang::` без требований.
- В схеме «в куче» создание значения расширения выделяет память и может бросить `AllocationError`. Копия тоже
  выделяет, поэтому `IndirectExtensions` вместе с `ImplicitlyCopyable` — ошибка: копия пишется `copy s`, и
  `AllocationError` стоит в сводке каждого `copy` этого типа. `let s as B` в `match` заимствует значение, а не
  копирует. В программе без кучи создание значения расширения с данными — ошибка сборки с именем constructor.
- В схеме «в значении» размер корня известен в его пакете, только если его constructors не содержат по значению
  другой открытый variant в той же схеме.
- Сборка программы предупреждает, когда constructor расширения больше наибольшего constructor корня, и называет
  его: каждое значение корня в программе выросло (группа диагностик `VariantSize`). Ответ — `indirect` у этого
  constructor.
- Цикл размеров между расширениями (`A` содержит `B` через расширение, `B` содержит `A`) — ошибка сборки программы.
  Ошибка перечисляет все constructors цикла; основное место — constructor с наибольшим полным путём, по сравнению из
  раздела представления enum. Ответ — `indirect` у любого из них.
- `indirect` у корня покрывает и constructors расширений; `indirect` у объявления расширения покрывает его
  constructors.
- Перевод корня на `IndirectExtensions` или обратно — ломающее изменение: меняются сводки исключений.
- Файлы `lang::` не объявляют открытый variant: раскладка `lang` — часть версии рантайма, а куча в `lang` запрещена.

### Соответствия полей

Поле constructor расширения обязано удовлетворять соответствиям корня, которые зависят от полей: `Equatable`,
`Copyable`, `ImplicitlyCopyable`, `Movable`. Иначе ошибка в расширении:

```efen
open variant Shape {
    conforms ImplicitlyCopyable
    dot
}

variant FileShape: Shape {
    file { let handle: File }      // ошибка: File не Copyable, а Shape копируется неявно
}
```

`@abi(c)` у открытого variant и у его расширения — ошибка: раскладка C фиксирована объявлением.

## Закрытость и `@unknown _`

Набор constructors закрытого variant закрыт в пределах одной версии декларации. Библиотека может
добавить case в следующей версии; клиент использует `@unknown _`, если ему нужна
исходная совместимость с таким изменением:

```efen
match response {
    .success.{ let data }: use(data)
    .failure.{ let code, let message }: report(code, message)
    @unknown _: reportUnknown()
}
```

`@unknown _` относится к закрытому variant. Открытый variant («Расширение») требует `_` или `@extended _`.
`Family<Base>` — открытый носитель видов хранения для layout, а не тип значения.

## Отличие от enum и structural union

```efen
enum Direction {
    north
    south
}

variant Side {
    left { let value: Int }
    right { let value: Int }
}

alias Scalar = Int | Float
```

- `enum` содержит только именованные значения без payload и может иметь raw
  values;
- `variant` вводит новые номинальные constructors и сохраняет их различие;
- `T | U` объединяет существующие типы структурно и не вводит constructors.

В частности, `Side.left(value: 1)` и `Side.right(value: 1)` различны благодаря
именам constructors; `T | U` таких имён не создаёт.

## Раскладка C: `@abi(c) variant`

`@abi(c)` на `variant` раскладывает его как `union` C: все случаи лежат с нулевого смещения, байтов метки нет. Метка такого значения не хранится, поэтому `match` и `==` по нему без доказательства живого
случая — ошибка. Живой случай доказывают условие на внешней структуре, typestate или контракт функций C; без
доказательства читаются только случаи из целых и дробных чисел. Подробно — [библиотеки на C](../foreign.md#union).

## Представление `Packed`

`representation Packed<I>` укладывает вариант в одно значение `I`. Так возвращает результат системный вызов Linux и
внешняя функция, у которой отказ — диапазон в том же слове (`-errno`).

- У каждого случая не больше одного поля. Его тип — `I`, уточнение `I`, класс над внешним значением над `I` или его
  уточнением, или `T?` из таких типов с объявленным пустым значением `c`: диапазон этого поля — диапазон `T` вместе
  с `c`.
- Случай без поля называет своё сырое значение: `name = c`. Это есть только у `Packed`.
- Диапазон каждого случая записан во [фрагменте сравнений](refinement-types.md#фрагмент-сравнений); другое — ошибка.
  Диапазоны попарно не пересекаются, это проверяется при объявлении. `match` проверяет диапазоны.
- `Result<T, E>` раскладку выбирает компилятор, и результатом функции `@asm` или `@abi(c)` он не бывает: у
  инстанциации generic-типа нет строки `representation`. Пишут номинальный вариант `Packed`.

```efen
type Descriptor: Int32 { value >= 0 }
type Errno: Int32 { value >= -4095 && value <= -1 }

public variant OpenResult {
    representation Packed<Int32>              // одно слово, диапазоны не пересекаются
    opened { let file: own File }                 // диапазон Descriptor
    failed { let code: Errno }
}

match File.openX86(dir: AT_FDCWD, path: "log".cString, flags: O_RDONLY, mode: 0) {
    .failed.{ let code }: throw IoError(code: code)
    .opened.{ let file }: return file.readAll()   // closeX86 вызывается в конце области file
}
```

`MapResult` ([вариант в одно слово](../memory/system.md#вариант-в-одно-слово)) — выведенная форма той же раскладки;
`Packed` делает её явной и проверенной. Значение вне всех диапазонов, которое вернула внешняя функция, ловит
проверочная сборка.

## Ограничения

- Raw values разрешены у `enum`, но не у `variant`, кроме случая без поля у варианта [`Packed`](#представление-packed).
- `CaseIterable` не синтезируется для `variant`.
- Расширяется только `open variant` и только другим `variant` («Расширение»).
- Безымянных полей constructor нет.

## См. также

- [Enum](enum.md)
- [Structural union](../type-aliases.md#union-типы)
- [Match](../blocks/match.md)
- [Optional](optional.md)
