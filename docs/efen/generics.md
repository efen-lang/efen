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
- [Безымянный generic-параметр](#безымянный-generic-параметр)
- [Полиморфные функциональные типы](#полиморфные-функциональные-типы)
- [Variadic generic-параметры](#variadic-generic-параметры)
- [Pack значений](#pack-значений)
- [Сопоставление с типами](#сопоставление-с-типами)

## Дженерик-функции

Функции могут объявлять параметры типа в угловых скобках после имени функции.
Параметр типа является compile-time параметром со значением типа `Type`.
Угловые скобки — короткая запись; полная форма использует уже существующее
ключевое слово `param` в начале тела объявления:

```efen
fn identity -> T {
    param T: Type
    param value: T

    return value
}
```

Эта форма эквивалентна `fn identity<T>(value: T) -> T`. У функции без круглых
скобок объявления `param` идут подряд до остальных инструкций.

### Базовый синтаксис

```efen
fn identity<T>(value: T) -> T {
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
    var value: T

    @constructor
    fn init(value: T) -> Self {
        self.value = value
    }

    fn getValue() -> T {
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

Точный порядок работы `ClassGenericDefinition`, его связь с планом построения
обычного класса и различие поведения в режимах мономорфизации и стирания типов
пока не определены. В частности, документация не обещает отдельный физический
класс для каждого набора аргументов в режиме стирания.

### Наследование с дженериками

```efen
open class Container<T> {
    var items: [T] = []

    fn add(item: T) {
        items.append(item)
    }
}

class Stack<T>: Container<T> {
    fn push(item: T) {
        add(item)
    }

    fn pop() -> T? {
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

class Person implements Equatable<Person> {
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
fn process<T>(data: T)
    where T: Readable, T: Writable
{
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
alias Result<T> = (T | Error)
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
могут быть enum-константы, числа, строки, логические значения, origin,
атрибуты, contracts, interfaces, strategies, функции и другие декларации или
значения, доступные compile-time коду.

Категория параметра задаётся его типом:

```efen
param T: Type
param Requirement: Contract
param RuntimeAPI: Interface
param Annotation: Attribute
param Policy: Strategy
param Source: Origin
param Size: Int
```

Один символ interface может участвовать в двух разных ролях. При
`param T: Type` передаётся его runtime-тип; при `param I: Interface` передаётся
compile-time объект декларации interface, доступный reflection и генерации.
Contract не является runtime-типом, но является допустимым compile-time
значением для `param C: Contract`.

```efen
class Adapter {
    param Requirement: Contract
    param RuntimeAPI: Interface

    #if Self conforms Requirement {
        // compile-time формирование реализации RuntimeAPI
    }
}
```

Enum, объявленный владельцем generic-типа, позволяет выбрать одну из его
реализаций без отдельной глобальной конструкции:

```efen
type ParticleColumns: Array<Particle, SoA>
```

Здесь `Particle` — аргумент параметра типа `Element`, а `SoA` — enum-константа
внутри `Array`.
Конкретная инстанциация имеет одну определённую representation.
Запись `[T]` сокращает `Array<T, default>`.

Полная форма позволяет явно указать тип параметра и значение по умолчанию:

```efen
struct Array {
    param Element: Type
    param Form: Representation = default

    enum Representation {
        AoS
        SoA
    }
}
```

Атрибут можно передать отдельным параметром:

```efen
class AnnotatedStorage {
    param Element: Type
    param Annotation: Attribute
}

let values = AnnotatedStorage<Int, @myattr>()
```

Это отличается от атрибута внутри типового аргумента:

```efen
Array<@myattr Int>                 // T является аннотированным типом
AnnotatedStorage<Int, @myattr>    // @myattr является отдельным param
```

Параметры любого допустимого compile-time типа можно передавать позиционно и по
имени:

```efen
Array<Particle, SoA>
Array<Element: Particle, Form: SoA>
```

`SoA` может быть записан без квалификации, когда ожидаемый тип параметра
однозначно указывает на enum, объявленный `Array`. Вне такого контекста имя
квалифицируется владельцем. Две одноимённые константы, подходящие ожидаемому
типу, создают ошибку неоднозначности, а не выбираются по порядку импортов.

Любой `param` можно опустить в месте применения, если компилятор однозначно
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

Значением `param T: Type` является полное типовое выражение. Оно сохраняет
базовый тип, ссылочную форму, права и metadata употребления:

```efen
Array<User>
Array<&read User>
Array<ref read User>
Array<User shared read>
Array<@myattr Int>
Array<@cached &read User>
```

`ref` — полная словесная форма ссылки, а `&` — её сокращение, поэтому
`Array<&read User>` и `Array<ref read User>` обозначают одну инстанциацию.

Эти аргументы образуют разные инстанциации generic. Код может получить базовый
тип отдельно, но `T` по умолчанию не стирает его модификаторы и metadata.
Metadata является дополнительными опциями типа и сама по себе не меняет
совместимость значений: `@myattr Int` совместим с `Int`. Разные инстанциации
нужны потому, что generic-код может наблюдать опции и породить разный код.

Metadata проверяется оператором `has`. Оператор допустим и в обычном выражении,
и в compile-time директиве. `#if` выбирает код при построении инстанциации:

```efen
#if T has @myattr {
    // Код существует только для типового аргумента с @myattr.
}

if value has @myattr {
    // Runtime-проверка metadata значения там, где она сохраняется в runtime.
}
```

Поскольку compile-time код может наблюдать metadata, она входит в ключ
инстанциации и в зависимости её результата.

## Конструкторы типов

Обычный параметр `param T: Type` принимает законченный тип. Параметр с
собственным списком типовых параметров принимает конструктор типов:

```efen
interface Repository {
    param Entity: Type
    param Result<T>: Type

    fn load(id: Id) -> Result<Entity?>
}

alias Identity<T> = T
alias DirectUsers = Repository<User, Identity>
alias DeferredUsers = Repository<User, Future>
```

`Result` сам не является типом значения. `Result<T>` является типом после
применения конструктора к аргументу. Локальное имя `T` в `param Result<T>`
описывает сигнатуру конструктора и не добавляет параметр `Repository`.

Конструктор может иметь несколько параметров и ограничения на них:

```efen
param PairFamily<A, B>: Type
param Buffer<T: Movable>: Type
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
param F<T>: Type {
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
    param Rows: Int { Rows > 0 }
    param Columns: Int { Columns > 0 }
}
```

`where` выражает связь нескольких параметров или требование всего объявления:

```efen
class SquareMatrix {
    param Rows: Int { Rows > 0 }
    param Columns: Int { Columns > 0 }

    where Rows == Columns
}

fn processSameElements<A: Iterable, B: Iterable>(left: A, right: B)
    where A.Item == B.Item, A.Item: Equatable
{
    // left и right могут иметь разные типы, но один тип элемента.
}
```

Блок после `param` и `where` являются обязательными условиями: ложное условие
запрещает инстанциацию. Они отличаются от `#if`, который условно формирует
состав уже законной инстанциации.

Параметр выбранного соответствия contract доступен через проекцию, например
`A.Item`. Если один тип имеет несколько подходящих соответствий с разными
значениями `Item`, проекция неоднозначна и требует явно выбрать стратегию.

## Безымянный generic-параметр

Contract в позиции типа параметра функции является короткой записью отдельного
безымянного generic-параметра:

```efen
fn printAll(items: Iterable<Item: String>) {
    // ...
}
```

Эта форма эквивалентна:

```efen
fn printAll<T: Iterable<Item: String>>(items: T) {
    // ...
}
```

Она не превращает contract в runtime-тип и не выполняет стирание. Каждое
употребление contract в позиции отдельного параметра вводит независимый тип:

```efen
fn merge(
    left: Iterable<Item: String>,
    right: Iterable<Item: String>
) {
    // left и right могут иметь разные конкретные типы.
}
```

`left` и `right` могут иметь разные конкретные типы. Когда требуется один тип,
он объявляется явно:

```efen
fn merge<T: Iterable<Item: String>>(left: T, right: T) {
    // left и right имеют один конкретный тип T.
}
```

## Полиморфные функциональные типы

Generic-функцию можно передать как значение, не выбирая одну инстанциацию:

```efen
fn test(transform: fn<T>(T) -> T) {
    let number = transform(42)
    let text = transform("hello")
}
```

Тип `fn<T>(T) -> T` требует одну функцию, применимую для каждого допустимого
`T`. Он отличается от `fn test<T>(transform: (T) -> T)`, где `T` выбирается один
раз для всего вызова `test`.

## Variadic generic-параметры

Префикс `...` собирает оставшиеся generic-аргументы:

```efen
struct Tuple {
    param ...Elements: Type
}
```

При `Tuple<Int, String, Bool>` значение `Elements` равно compile-time массиву
`[Int, String, Bool]` типа `[Type]`. Пустой pack законен. В применении `...`
раскрывает массив обратно в последовательность аргументов:

```efen
Tuple<...Elements>
```

Variadic-параметр можно ограничить контрактом:

```efen
param ...Errors: Type
where ...Errors: Exception
```

Раскрытие `...Errors` в `where` создаёт ограничение для каждого аргумента:
каждый переданный тип должен быть совместим с `Exception`. Внутри `Errors`
остаётся массивом типов. Поэтому отдельное слово `each` не требуется. Справа от
`:` contract означает `conforms`, а класс или интерфейс — совместимость типа.

Pack раскрывается в кортеже, union и другом списке типов:

```efen
alias Result<Value, ...Errors> = Value | ...Errors
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
fn tuple<...Types>(...values: Types) -> Tuple<...Types> {
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

    #if T conforms Copyable {
        conforms Copyable

        fn copy() -> Box<T> {
            return Box(value.copy())
        }
    }
}
```

Ложное условие не запрещает саму инстанциацию. `Box<NonCopyable>` остаётся
законным типом, но не соответствует `Copyable` и не получает условные члены.
Это отличается от `class Box<T: Copyable>`, где ограничение запрещает создать
`Box<T>` для неподходящего `T`.

Условие может зависеть от нескольких параметров, compile-time значений и
metadata:

```efen
#if A conforms Copyable && B conforms Copyable {
    conforms Copyable
}

#if Size > 0 {
    conforms NonEmpty
}

#if T has @serializable {
    conforms Serializable
}
```

Результат условия, выбранные реализации и прочитанные compile-time факты входят
в ключ и зависимости инстанциации.

## Наблюдение параметра типа

Параметр типа доступен type-aware операциям:

```efen
fn printType<T>() {
    let descriptor = typeof(T)
    print T
}
```

`typeof(T)` возвращает дескриптор `Type`. `T` приводится к `String` для обычной
runtime-печати текущего конкретного типа.

## Генерация кода

Компилятор выбирает монотипизацию или стирание, если объявление не закрепило
режим:

```efen
@monomorphize
fn specialized<T>(value: T) {}

@erase
fn sharedBody<T>(value: T) {}
```

При монотипизации создаётся отдельное тело для необходимых инстанциаций. При
стирании одно общее тело получает скрытый runtime-дескриптор каждого параметра
типа; поэтому `typeof(T)` и преобразование `T` в строку остаются доступны.

## Варианс (Covariance/Contravariance)

Efen поддерживает вариантность для дженерик-типов:

```efen
// Ковариантность (out) - тип может быть только возвращаемым значением
interface Producer<out T> {
    fn produce() -> T
}

// Контравариантность (in) - тип может быть только входным параметром
interface Consumer<in T> {
    fn consume(item: T)
}

// Инвариантность (по умолчанию) - тип может быть и входным, и выходным
interface Storage<T> {
    fn get() -> T
    fn set(item: T)
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
fn transform<TInput, TOutput>(
    items: [TInput],
    mapper: (TInput) -> TOutput
) -> [TOutput] {
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
