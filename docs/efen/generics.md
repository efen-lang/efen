# Дженерики (Generics)

Дженерики в Efen позволяют создавать универсальные компоненты, работающие с различными типами данных, сохраняя при этом типобезопасность.

## Содержание

- [Дженерик-функции](#дженерик-функции)
- [Дженерик-методы](#дженерик-методы)
- [Дженерик-классы](#дженерик-классы)
- [Дженерик-структуры](#дженерик-структуры)
- [Дженерик-интерфейсы](#дженерик-интерфейсы)
- [Ограничения типов](#ограничения-типов)
- [Множественные параметры типа](#множественные-параметры-типа)
- [Конструкторы типов](#конструкторы-типов)
- [Ограничения параметров](#ограничения-параметров)
- [Типы с параметрами-значениями](types/value-parameterized-types.md)
- [Generic-параметры с contract](#generic-параметры-с-contract)
- [Полиморфные функциональные типы](#полиморфные-функциональные-типы)
- [Variadic generic-параметры](#variadic-generic-параметры)
- [Pack значений](#pack-значений)
- [Право доступа как параметр](#право-доступа-как-параметр)
- [Сопоставление с типами](#сопоставление-с-типами)

## Дженерик-функции

Функции могут объявлять generic-параметры ключевым словом `generic` в начале
тела объявления. Параметр типа является compile-time параметром со значением
типа `Type`:

```efen
fn identity<T: Movable>(value: own T) -> T {
    return value
}
```

Тело проверяется один раз, и `T` в нём — самый строгий тип: у него есть только то, что дают его ограничения. Поэтому
`identity` берёт `value` во владение: вернуть читающий параметр без ограничения нельзя, это вернуло бы чужое значение.
`return value` переносит значение из слота параметра в слот результата, а перенос даёт `Movable`
([явное извлечение](types/ownership.md#явное-извлечение)): без
`T: Movable` тело отвергается. `T: ImplicitlyCopyable` тоже разрешил бы `return value`, но закрыл бы `identity` для
`String`.

Объявления `generic` предшествуют параметрам вызова, а объявления `param` идут
после них подряд до остальных инструкций. Имена из строк `generic` и `param` видны во всём объявлении, и в
заголовке тоже: в цели стратегии (`strategy ArrayTraversal for Array<T>`), в типах параметров и результата, в
строках `requires` и `ensures`. Список в угловых скобках остаётся
допустимой короткой формой generic-параметров объявления. Формы не смешиваются:
если объявление использует `generic` в теле, угловых скобок в его заголовке нет;
если использует `param`, нет круглых скобок параметров.

Полная форма обязательна, если выполняется хотя бы одно условие: параметров
больше трёх (generic и параметры вызова считаются порознь; образец `Item: Access T` — один параметр), есть значение
по умолчанию, есть pack `...`, у параметра есть условие `{ }` или несколько контрактов. Внутри `<…>` блока `{ }`
нет.
Иначе канонична короткая форма; простое ограничение `<T: Comparable>` остаётся в
заголовке. Отклонение в любую сторону получает диагностику стиля
`S.generic-parameter-layout`. У объявлений без тела, например `alias`, есть
только короткая форма.

### Базовый синтаксис

```efen
fn identity<T: Movable>(value: own T) -> T {
    return value
}

// Использование
let num = identity(42)       // T выводится как Int
let str = identity("hello")  // T выводится как String

// Тип можно указать явно
let explicit = identity<Int>(42)
```

### Множественные параметры типа

```efen
fn map<T, U>(items: [T], transform: (T) -> U) -> [U] {
    var result: [U] = []
    for item in items {
        result.append(transform(item))
    }
    return result
}

// Использование
let numbers = [1, 2, 3]
let strings = map(numbers, (n) => String(n))
```

### Вывод типов

Компилятор может автоматически выводить параметры типа из аргументов:

```efen
let result = identity(42)  // T выводится как Int
let doubled = map([1, 2, 3], (x) => x * 2)  // T=Int, U=Int
```

## Дженерик-методы

Методы классов и методы, предоставляемые стратегиями, также могут объявлять
собственные generic-параметры.

```efen
class Transformer {
    fn apply<T, U>(value: T, transform: (T) -> U) -> U {
        return transform(value)
    }
}

// Использование
let transformer = Transformer()
let text = transformer.apply(42, (number) => String(number))
```

`T` и `U` принадлежат методу `apply`, а не классу `Transformer`. Их значения
выводятся заново для каждого вызова метода.

## Дженерик-классы

Классы могут иметь параметры типа, которые применяются ко всему классу.

```efen
class Box<T> {
    conforms Constructible

    var value: T

    @constructor
    fn init(value: T) -> Self {
        self.value = value
    }

    fn getValue -> T {
        return value
    }

    fn setValue(newValue: T) {
        value = newValue
    }
}

// Использование
let intBox = Box<Int>(42)
let stringBox = Box<String>("hello")

echo intBox.getValue()  // 42
```

Построением обобщённого класса управляет отдельный compile-time контракт
`ClassGenericDefinition`. Он не является разновидностью обычного
`ClassDefinition` и не переносит на него ответственность за generic-
инстанциацию.

Сначала `ClassGenericDefinition` строит параметризованный generic. При раскрытии
он получает конкретные compile-time аргументы и решает, создавать ли новый
реальный класс или использовать уже существующую физическую реализацию. Затем
обычный `ClassDefinition` достраивает выбранный реальный класс.

При стирании может существовать несколько реальных классов для разных групп
аргументов. Эти группы выбирает `ClassGenericDefinition`; компилятор не выводит
их автоматически из ветвлений или наблюдений над `T`.

### Наследование с дженериками

```efen
open class Container<T> {
    conforms OpenClass

    var items: [T] = []

    fn add(item: T) {
        items.append(item)
    }
}

class Stack<T>: Container<T> {
    fn push(item: T) {
        add(item)
    }

    fn pop -> T? {
        if items.count > 0 {
            return items.removeLast()
        }
        return null
    }
}
```

## Дженерик-структуры

Структуры поддерживают дженерики с композицией типов.

```efen
struct Pair<T, U> {
    var first: T
    var second: U
}

// Использование
let pair = Pair<Int, String>(first: 42, second: "answer")
```

### Композиция с дженериками

```efen
struct RefCounted<T> {
    var refCount: Int = 0
    var value: T
}

let value = RefCounted<String>(refCount: 1, value: "hello")
```

## Дженерик-интерфейсы

Интерфейсы также могут быть дженерик-типами.

```efen
interface Equatable<T> {
    fn equals(other: T) -> Bool
}

class Person {
    implements Equatable<Person>

    var age: Int

    fn equals(other: Person) -> Bool {
        return age == other.age
    }
}
```

## Ограничения типов

Параметры типа могут иметь ограничения (constraints) для указания требований к типам.

```efen
contract Comparable<T> {
    fn compareTo(other: T) -> Int
}

// Базовое ограничение
fn compare<T: Comparable<T>>(left: T, right: T) -> Int {
    return left.compareTo(right)
}

// Множественные ограничения
fn process {
    generic T: Readable, Writable
    param data: T

    // T должен соответствовать обоим контрактам
}
```

## Множественные параметры типа

Функции, классы и другие конструкции могут иметь несколько параметров типа.

```efen
fn zip<T, U>(first: [T], second: [U]) -> [(T, U)] {

    var result: [(T, U)] = []
    let minCount = min(first.count, second.count)

    for i in 0..<minCount {
        result.append((first[i], second[i]))
    }

    return result
}

// Использование
let numbers = [1, 2, 3]
let letters = ["a", "b", "c"]
let zipped = zip(numbers, letters)  // [(1, "a"), (2, "b"), (3, "c")]
```

## Дженерики в алиасах типов

Алиасы типов также могут быть дженерик-типами:

```efen
alias ValueOrError<T> = (T | Error)
alias Handler<T> = (T) -> Void
alias Transformer<T, U> = (T) -> U

// Использование
fn processData<T>(handler: Handler<T>) {

    // ...
}
```

## Compile-time значения

Generic-параметр может быть любым compile-time значением. `Type` является одним
из допустимых типов параметра, а не отдельным видом generic. Параметрами также
могут быть значения enum, числа, строки, логические значения, origin,
атрибуты, contracts, interfaces, strategies, функции и другие декларации или
значения, доступные compile-time коду.

Категория параметра задаётся его типом:

```efen
generic T: Type
generic Requirement: Contract
generic RuntimeAPI: Interface
generic Annotation: Attribute
generic Policy: Strategy
generic Source: Origin
generic Size: Int
generic Access: Access
```

Один символ interface может участвовать в двух разных ролях. При
`generic T: Type` передаётся его runtime-тип; при `generic I: Interface` передаётся
compile-time объект декларации interface, доступный reflection и генерации.
Contract не является runtime-типом, но является допустимым compile-time
значением для `generic C: Contract`.

Когда compile-time значение является параметром объявления типа, оно входит в
identity concrete generic-инстанциации. Полная семантика, включая enum-категории,
runtime-классификацию и HIR-ключ, описана в
[типах с параметрами-значениями](types/value-parameterized-types.md).

```efen
class Adapter<Requirement: Contract, RuntimeAPI: Interface> {

    #if Self conforms Requirement
        // compile-time формирование реализации RuntimeAPI
    #endif
}
```

Enum, объявленный владельцем generic-типа, позволяет выбрать одну из его
реализаций без отдельной глобальной конструкции:

```efen
type ParticleColumns: Array<Particle, soa>
```

Здесь `Particle` — аргумент параметра типа `Element`, а `soa` — значение enum
внутри `Array`.
Конкретная инстанциация имеет одну определённую representation.
Запись `[T]` сокращает `Array<T, default>`.

Полная форма позволяет явно указать тип параметра и значение по умолчанию:

```efen
struct Array {
    generic Element: Type
    generic Form: Representation = default
    generic indirection: Indirection = default

    enum Representation {
        aos
        soa
    }

    enum Indirection {
        direct
        indirect
    }
}
```

`indirection` говорит, лежит ли в ячейке само значение (`direct`) или указатель на отдельно лежащее значение
(`indirect`). Умолчания: `aos`; `direct` у структуры, `indirect` у класса. Третий параметр
называют по имени: `Array<Row, indirection: indirect>`. Подробно — [библиотеки на C](foreign.md#массивы).

Атрибут можно передать отдельным параметром:

```efen
class AnnotatedStorage<Element: Type, Annotation: Attribute> {
}

let values = AnnotatedStorage<Int, @myattr>()
```

Это отличается от атрибута внутри типового аргумента:

```efen
Array<@myattr Int>                 // T является аннотированным типом
AnnotatedStorage<Int, @myattr>    // @myattr является отдельным generic-аргументом
```

Параметры любого допустимого compile-time типа можно передавать позиционно и по
имени:

```efen
Array<Particle, soa>
Array<Element: Particle, Form: soa>
```

`soa` может быть записан без квалификации, когда ожидаемый тип параметра
однозначно указывает на enum, объявленный `Array`. Вне такого контекста имя
квалифицируется владельцем. Две одноимённые константы, подходящие ожидаемому
типу, создают ошибку неоднозначности, а не выбираются по порядку импортов.

Любой `generic` можно опустить в месте применения, если компилятор однозначно
выводит его значение из остальных аргументов, ограничений и сигнатур. Вывод не
является отдельным видом параметра. Если решений нет или их несколько,
компилятор требует именованный аргумент:

```efen
fn consumeInts<T: Iterable<Item: Int>>(items: T) {
    // Cursor выводится из выбранного соответствия T контракту Iterable.
}

fn consume<T: Iterable>(items: T) {

    // Item и Cursor выводятся из T, если соответствие единственно.
}
```

Выведенные параметры являются частью полной инстанциации и сохраняются в её
ключе так же, как явно написанные.

Значением `generic T: Type` является полное типовое выражение. Оно сохраняет
базовый тип, права и metadata употребления:

```efen
Array<User>
Array<read Items.Item>
Array<@myattr Int>
Array<@cached User>
```

Ссылочной формы среди них нет: ссылка бывает только внутри тела функции и generic-аргументом не
бывает ([владение](types/ownership.md#ссылки-только-внутри-функции)); прежние `&read User`, `ref read User` и `shared read User` из языка убраны.

Эти аргументы образуют разные инстанциации generic. Код может получить базовый
тип отдельно, но `T` по умолчанию не стирает его модификаторы и metadata.
Metadata является дополнительными опциями типа и сама по себе не меняет
совместимость значений: `@myattr Int` совместим с `Int`. Разные инстанциации
нужны потому, что generic-код может наблюдать опции и породить разный код.

Metadata проверяется оператором `has`. Оператор допустим и в обычном выражении,
и в compile-time директиве. `#if` выбирает код при построении инстанциации:

```efen
#if T has @myattr
    // Код существует только для типового аргумента с @myattr.
#endif

if value has @myattr {
    // Runtime-проверка metadata значения там, где она сохраняется в runtime.
}
```

Поскольку compile-time код может наблюдать metadata, она входит в ключ
инстанциации и в зависимости её результата.

### Угловые скобки и выражения

Список generic-аргументов открывает `<`, прижатый слева к имени: `Box<Int>`,
`identity<Int>(42)`. Сравнение отделяет `<` пробелом слева, поэтому разбор не
зависит от того, что обозначает имя, и `f(a < b, c > (d))` передаёт два
сравнения, а `f(a<b, c>(d))` — один generic-вызов.

Запись `<...`, то есть `<` и сразу три точки, лексер делит на `<` и раскрытие
`...`: `Tuple<...Elements>`. Интервал `<..` получается, только если после двух
точек нет третьей: `a<..b`.

Внутри `<...>` знак, содержащий `<` или `>`, пишется только в скобках: сравнения,
сдвиги, `<=>` и диапазоны `..<`, `<..`. Первая `>` вне скобок закрывает список,
а `>>` — два вложенных списка:

```efen
Buffer<Size: (1 << 4)>
Choice<Flag: (a > b)>
Array<Array<Int>>

Buffer<Size: 1 << 4>     // ошибка синтаксиса: сдвиг без скобок
```

Угловые скобки всегда прижаты: `<` — к имени и к первому аргументу, `>` — к
последнему аргументу. Пробелы внутри списка допустимы только после запятой и
двоеточия. Пробел у скобки внутри списка смысл не меняет и получает
диагностику стиля `S`. Пробел между именем и `<` делает знак сравнением, и
такой код разбирается как сравнение:

```efen
Map<String, Int>         // каноническая запись
Array< Int >             // S: угловые скобки не прижаты
Array<Array<Int> >       // S: угловые скобки не прижаты
Box <Int>(42)            // сравнение Box < Int > (42): ошибка, цепочка сравнений
```

## Право доступа как параметр

Параметр типа `Access` принимает право доступа: `read`, `edit`, `mut` или
`own`. Он объявляется как остальные compile-time параметры и записывается там,
где обычно стоит слово права:

```efen
generic Access: Access
```

Аргумент без права значит `read`, как везде в языке: умолчания у параметра `Access` нет.

`Access` объявлен в `lang::` как обычный enum, но это особый встроенный вид,
как `Type` и `Origin`: компилятор знает его и читает значение как дескриптор
доступа.

```efen
enum Access { read, edit, mut, own }
```

Сравнение (`#if Access == own`), `match` и проверка полноты ветвей работают по
правилам для compile-time значений enum. `&` значением `Access` не бывает:
пишут слово `mut`.

Параметр обычно называют так же, как тип: `Access: Access`. Внутри объявления
имя `Access` означает параметр, а тип доступен как `lang::Access`.

Право из параметра пишется в поле, в типе и в результате. Все записи ниже
читаются одинаково: имя параметра стоит вместо `read` или `edit`. Структура
держит только данные, а `next` даёт стратегия ([структуры](structs.md)):

```efen
struct ArrayIterator<Item: Access T, Src: Origin> {
    let items: Access<Src> Array<T>     // поле: ссылка с правом Access на Src
    var index: Int = 0 { value >= 0 }

    invariants {
        index <= items.count
        Access == read || Access == edit
    }
}

strategy ArrayStep<Item: Access T, Src: Origin>
for ArrayIterator<Item, Src: Src> {
    conforms Iterator<Item, Src: Src>
    invariants { Access == read || Access == edit }

    mut fn next -> Access<Src> T? {     // ссылка на слот массива Src
        if index == items.count { return null }
        index += 1
        return items[index - 1]
    }
}
```

Результат `next` записан с правом и источником явно: `Access<Src> T` — ссылка на
слот массива `Src`. Без угловых скобок источником результата метода был бы `self`,
то есть сам итератор ([место в результате функции](types/ownership.md#место-в-результате-функции)),
а запись `-> Item?` без слова права дала бы копию. Поэтому следующий вызов `next`,
хотя это `mut fn`, прошлый элемент не убивает: оба живут, пока не меняется
структура `Src`.

Шаблон `Item: Access T` раскладывает переданный аргумент на две части: `T` —
тип без права, `Access` — право. Пишут при этом только `Item`, а `Access`
выводится:

```efen
ArrayIterator<Item: edit Int, Src: numbers>    // T = Int, Access = edit
ArrayIterator<Item: Int, Src: numbers>         // T = Int, Access = read: без пометки
```

Роль записи решает её позиция. В списке параметров сразу после имени объявления
(`struct`, `contract`, `strategy`, `fn`) `Item: Access T` вводит новые имена `T`
и `Access`. В любом другом месте — в `conforms`, в типе поля или результата —
та же запись берёт уже объявленные имена. Новое имя, совпадающее с внешним
generic-параметром, — ошибка.

Аргумент без права значит `read`: пометки нет — право `read`, как у параметра функции. Если `Access` передан явно
рядом (`Iterable<Item: T, Access: mut>`), право берётся оттуда. Шаблон сам вводит `Access`: строки
`Access: Access` рядом с ним не пишут, и умолчания у него нет. Ограничение права — строка `invariants`, она читает только параметры
generic и проверяется при сборке. Право ссылки (`&`) в обычный `generic T: Type` не
попадает; право указателя layout (`read Items.Item`) остаётся
частью типа.

Пометка метода тоже бывает параметром. Одно объявление покрывает все права,
которые допускает его параметр:

```efen
Access fn iterator -> ArrayIterator<Item: Access T, Src: self>
```

Такая пометка даёт семейство методов, по одному на каждое допустимое право:
`read fn iterator`, `edit fn iterator`. Методы с одним именем и разными
пометками различаются как перегрузки. Если получателю подходят несколько,
берётся самый узкий: у `v: edit Array<Int>` вызов `v.iterator()` берёт `read`.
Более широкое право просят явно, той же формой, что и `take`:
`(edit v).iterator()`, `(mut v).iterator()`, `(take v).iterator()`. Получатель
без `take` метод `own fn` не выбирает.

### Ограничение прав

Допустимые права задаёт обычное условие ([ограничения параметров](#ограничения-параметров)): у параметра со своей
строкой — `{ }` у неё, у права из образца — строка `invariants`:

```efen
strategy ArrayTraversal for Array<T> {
    generic T: Type
    generic Access: Access { value == read || value == edit }      // own и mut не подходят
    …
}
```

Условие обязательно там, где тело подходит не для всех прав: иначе один
параметр покрывает и `own`, и остальные права, и два объявления становятся
одинаково применимыми.

### Развилка по праву

Тип, который зависит от права, выбирается `match` по параметру
([сопоставление с типами](#сопоставление-с-типами)):

```efen
alias ArrayCursor<T, Access: Access, Src: Origin> = match Access {   // ветви mut нет: ArrayCursor<…, Access: mut> — ошибка
    own:  DrainIterator<T>
    read: ArrayIterator<Item: read T, Src: Src>
    edit: ArrayIterator<Item: edit T, Src: Src>
}
```

В теле право различает `#if`:

```efen
#if Access == own
    return DrainIterator(items: take self)
#elif Access == read || Access == edit
    return ArrayIterator(items: self)
#endif
```

Право входит в идентичность инстанциации: `ArrayIterator<Item: read Int, Src: numbers>`
и `ArrayIterator<Item: edit Int, Src: numbers>` — разные типы.

## Конструкторы типов

Обычный параметр `generic T: Type` принимает законченный тип. Параметр с
собственным списком типовых параметров принимает конструктор типов:

```efen
interface Repository<Entity: Type, Result<T>: Type> {

    fn load(id: Id) -> Result<Entity?>
}

alias Identity<T> = T
alias DirectUsers = Repository<User, Identity>
alias DeferredUsers = Repository<User, Future>
```

`Result` сам не является типом значения. `Result<T>` является типом после
применения конструктора к аргументу. Локальное имя `T` в `generic Result<T>`
описывает сигнатуру конструктора и не добавляет параметр `Repository`.

Конструктор может иметь несколько параметров и ограничения на них:

```efen
generic PairFamily<A, B>: Type
generic Buffer<T: Movable>: Type
```

Применение `Buffer<X>` законно только при доказанном `X conforms Movable`.
Сигнатура конструктора задаёт явно передаваемые параметры. Именованный generic
с дополнительными параметрами совместим с ней, если при каждом применении все
остальные параметры однозначно заполняются обычным правилом default/вывода.
Например, `Array<Element, Form = default>` можно передать как конструктор одного
аргумента. Полученные значения остальных параметров входят в полную
инстанциацию. Если их нельзя вывести однозначно, применение ошибочно.

Ограничения конструктора проверяются как область допустимых аргументов. Переданный
конструктор обязан принимать каждый аргумент, разрешённый сигнатурой параметра.
Поэтому конструктор, требующий `Copyable`, нельзя передать как неограниченный
`F<T>` или как `F<T: Movable>`: `Movable` не гарантирует `Copyable`. Обратное
усиление требования пользователя законно: неограниченный конструктор можно
передать как `F<T: Copyable>`.

Анонимный конструктор записывается как type-lambda:

```efen
type<T> => Future<Result<T, Error>>
```

Например:

```efen
Repository<User, type<T> => Future<Result<T, Error>>>
```

Параметры type-lambda являются compile-time типами, а её результат обязан быть
типом. Type-lambda не существует как runtime-значение.

### Требования к семейству типов

Блок параметра задаёт универсальные требования ко всем законным применениям
конструктора:

```efen
generic F<T>: Type {
    required method map<U>(transform: (T) -> U) -> F<U>
}
```

При связывании `F` компилятор должен доказать generic-реализацию `map`,
применимую для любого разрешённого `T` и `U`; удачный вызов только для нескольких
случайно использованных типов недостаточен. Требование может удовлетворить
физический метод либо метод стратегии, участвующей в обычном разрешении.
Несколько подходящих реализаций являются ошибкой компиляции.
Автоматического выбора «более специализированной» стратегии нет.

Выбранная реализация входит в зависимости и ключ инстанциации. Внутри одной
инстанциации разрешение не меняется от места следующего вызова этой
инстанциации.

## Ограничения параметров

Короткое ограничение `T: Contract` и полная форма с блоком параметра проверяются
при создании инстанциации:

```efen
class Matrix {
    generic Rows: Int { value > 0 }
    generic Columns: Int { value > 0 }
}
```

Условие одного параметра — `{ }` у его строки, предмет — `value`. Связь нескольких параметров у типа — строка
[`invariants`](conditions.md#условия-значений-и-invariants), у функции — строка `requires`. `T conforms C` — обычное
логическое выражение. Слова `where` нет.

```efen
class SquareMatrix {
    generic Rows: Int { value > 0 }
    generic Columns: Int { value > 0 }

    invariants { Rows == Columns }
}

fn processSameElements
    requires A.Item == B.Item
    requires A.Item conforms Equatable
{
    generic A: Iterable
    generic B: Iterable
    param left: A
    param right: B

    // left и right могут иметь разные типы, но один тип элемента.
}
```

Строка `requires` про один параметр, который объявила эта же функция, — ошибка с подсказкой перенести условие к его
строке (`generic T: C`). Про параметр типа у метода и про связанный тип (`A.Item`) — законно: своей строки у них в
этой функции нет.

`requires` у отдельного метода обобщённого типа требует только для этого метода. Так коллекции std требуют
[`ImplicitlyDestroyable`](disposable.md#implicitlydestroyable) только у методов, которые уничтожают элемент, не
возвращая его; сам тип принимает любой `T`:

```efen
mut fn removeAll
    requires T conforms ImplicitlyDestroyable
mut fn removeLast -> own T?
    ensures result == null ==> count == 0
```

Условие у строки `generic`, строки `invariants` и `requires`, которые читают только параметры generic, —
обязательные условия, их проверяют при сборке: ложное условие
запрещает инстанциацию. Они отличаются от `#if`, который условно формирует
состав уже законной инстанциации.

Параметр выбранного соответствия contract доступен через проекцию, например
`A.Item`. Если один тип имеет несколько подходящих соответствий с разными
значениями `Item`, проекция неоднозначна и требует явно выбрать стратегию.

## Generic-параметры с contract

Generic-функция всегда объявляет конкретный тип отдельно от runtime-параметра:

```efen
fn printAll<Items: Iterable<Item: String>>(items: Items) {

    // ...
}
```

То же имя используется во всех местах сигнатуры, которым нужна эта идентичность:

```efen
fn printAll<T: Iterable<Item: String>>(first: T, second: T) {

    // ...
}
```

Contract не становится runtime-типом и не выполняет стирание. Для двух
независимых конкретных типов объявляются два generic-параметра:

```efen
fn merge<Left: Iterable<Item: String>, Right: Iterable<Item: String>>(left: Left, right: Right) {

    // left и right могут иметь разные конкретные типы.
}
```

`left` и `right` могут иметь разные конкретные типы. Когда требуется один тип,
объявляется одна общая идентичность:

```efen
fn merge<T: Iterable<Item: String>>(left: T, right: T) {

    // left и right имеют один конкретный тип T.
}
```

## Полиморфные функциональные типы

Generic-функцию можно передать как значение, не выбирая одну инстанциацию:

```efen
fn test<transform: <T>(T) -> T> {
    let number = transform(42)
    let text = transform("hello")
}
```

Тип `<T>(T) -> T` требует одну функцию, применимую для каждого допустимого `T`.
`generic transform` связывает её как generic-параметр `test`. Это отличается от
именованного `generic T: Type` с `param transform: (T) -> T`, где `T` выбирается
один раз для всего вызова `test`.

## Variadic generic-параметры

Префикс `...` собирает оставшиеся generic-аргументы:

```efen
struct Tuple {
    generic ...Elements: Type
}
```

Тип кортежа `(Int, String, Bool)` и есть `Tuple<Int, String, Bool>`; имя `Tuple`
вручную пишется только с раскрытием pack. Для `(Int, String, Bool)` значение
`Elements` равно compile-time массиву `[Int, String, Bool]` типа `[Type]`. Пустой
pack законен. В применении `...` раскрывает массив обратно в последовательность
аргументов:

```efen
Tuple<...Elements>
```

Variadic-параметр можно ограничить контрактом:

```efen
generic ...Errors: Throwable
```

Контракт у pack — ограничение каждого аргумента: каждый переданный тип должен быть совместим с `Throwable`. Внутри `Errors`
остаётся массивом типов. Поэтому отдельное слово `each` не требуется. Справа от
`:` contract означает `conforms`, а класс или интерфейс — совместимость типа.

Pack раскрывается в кортеже, structural union и другом списке типов:

```efen
alias ValueOrErrors<Value, ...Errors> = Value | ...Errors
```

Compile-time коллекция типов поддерживает обычные допустимые операции над
коллекцией. В частности, `map` с type-lambda преобразует каждый тип:

```efen
alias OptionalTuple<...Elements> =
    Tuple<...Elements.map(type<T> => T?)>
```

## Pack значений

Runtime pack связывается с type pack той же длины:

```efen
fn tuple -> Tuple<...Types> {
    generic ...Types: Type
    param ...values: Types

    return Tuple(...values)
}
```

В вызове `tuple(42, "hello", true)` значение `Types` равно
`[Int, String, Bool]`, а тип каждого `values[i]` равен `Types[i]`. Запись
`...values` раскрывает pack с сохранением порядка и обычного порядка вычисления
аргументов Efen.

Обычный однородный variadic-параметр `values: ...Int` остаётся массивом значений
одного заранее известного типа. Форма `...values: Types` является
гетерогенным pack, типы элементов которого задаёт связанный type pack.

## Сопоставление с типами

`match` может выполняться над compile-time значением `Type`. Generic-образец
разбирает применённый тип и связывает его аргументы compile-time переменными:

```efen
alias Element<T> = match T {
    Array<let item>: item
    _: T
}
```

Имена, связанные через `let`, следуют обычному правилу переменных и начинаются
со строчной буквы. `Element<Array<String>>` равен `String`.

Образец `Array<let item>` сопоставляется также с наследником `Array<String>`,
если в его базовых типах существует ровно одно применение с номинально тем же
generic-head `Array`. Аргументы этого применения связываются напрямую, без
вариантности и coercion. Несколько применений с разными аргументами являются
ошибкой неоднозначности.
Прозрачные aliases раскрываются перед сопоставлением. `opaque type` раскрывается
только там, где видимо его внутреннее представление.

## Условное соответствие контрактам

Generic-тип может соответствовать contract только в тех инстанциациях, где
выполнено compile-time условие:

```efen
class Box<T> {
    var value: T

    #if T conforms Copyable
        conforms Copyable

        fn copy -> Box<T> {
            return Box(copy value)
        }
    #endif
}
```

Ложное условие не запрещает саму инстанциацию. `Box<NonCopyable>` остаётся
законным типом, но не соответствует `Copyable` и не получает условные члены.
Это отличается от `generic T: Copyable`, где ограничение запрещает создать
`Box<T>` для неподходящего `T`.

Условие может зависеть от нескольких параметров, compile-time значений и
metadata:

```efen
#if A conforms Copyable && B conforms Copyable
    conforms Copyable
#endif

#if Size > 0
    conforms NonEmpty
#endif

#if T has @serializable
    conforms Serializable
#endif
```

Результат условия, выбранные реализации и прочитанные compile-time факты входят
в ключ и зависимости инстанциации.

## Наблюдение параметра типа

Параметр типа доступен type-aware операциям:

```efen
fn printType<T> {
    let descriptor = typeof(T)
    print T
}
```

`typeof(T)` возвращает дескриптор `Type`. `T` приводится к `String` для обычной
runtime-печати текущего конкретного типа.

## Генерация кода

Компилятор выбирает монотипизацию, если объявление не закрепило режим. Явный
`@erase` является обязательством автора: если compiler не может построить одну
безопасную erased-реализацию, это ошибка, а не неявный fallback в
монотипизацию:

```efen
@monomorphize
fn specialized<T>(value: T) {
}

@erase
fn sharedBody<T>(value: T) {
}
```

При монотипизации создаётся отдельное тело для необходимых инстанциаций. При
стирании generic-функции одно общее тело использует допустимый erased carrier.
Операция тела, зависящая от выбранной стратегии, в `@erase` запрещена: compiler
не передаёт скрытый strategy witness. Он может упаковать значения в box, если
это нужно carrier-у, но контексты и исключения этой операции входят в итоговую
сводку callable; compiler никогда их не скрывает. Физическая форма carrier-а,
ownership, drop и unboxing — детали lowering compiler, а не дополнительная
surface-развилка языка.

Для generic-класса решение принимает `ClassGenericDefinition`: он может
направить несколько инстанциаций в одну реальную реализацию. Компилятор
передаёт конкретный тип аспекту как compile-time вход контролируемой операции.
Аспект может, например, вмешаться в построение `=` и материализовать
runtime-дескриптор в HIR. Такой дескриптор не обязан присутствовать, если
выбранная реализация класса его не использует.

## Варианс (Covariance/Contravariance)

Efen поддерживает вариантность для дженерик-типов:

```efen
// Ковариантность (out) - тип может быть только возвращаемым значением
interface Producer<out T> {
    fn produce -> T
}

// Контравариантность (in) - тип может быть только входным параметром
interface Consumer<in T> {
    fn consume(item: T)
}

// Инвариантность (по умолчанию) - тип может быть и входным, и выходным
interface Storage<T> {
    fn get -> T
    mut fn set(item: T)
}
```

## Лучшие практики

1. **Используйте осмысленные имена**: `T`, `U`, `V` для простых случаев, но `TElement`, `TKey`, `TValue` для сложных
2. **Избегайте избыточных дженериков**: Не делайте класс дженериком, если параметр типа используется только в одном методе
3. **Ограничивайте типы**: Используйте ограничения для явного указания требований к типам
4. **Документируйте**: Поясняйте назначение каждого параметра типа в doc-комментариях

```efen
/// Трансформирует элементы одного типа в другой
/// - TInput: Тип входных элементов
/// - TOutput: Тип выходных элементов
fn transform<TInput, TOutput>(items: [TInput], mapper: (TInput) -> TOutput) -> [TOutput] {

    var result: [TOutput] = []
    for item in items {
        result.append(mapper(item))
    }
    return result
}
```

## Ограничения

Параметры типа не могут использоваться для создания статических членов.
Наблюдение типа не предоставляет прав на произвольное изменение его объявления.

## Смотрите также

- [Функции](functions.md)
- [Классы](classes.md)
- [Структуры](structs.md)
- [Интерфейсы](interfaces.md)
- [Алиасы типов](type-aliases.md)
