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

## Дженерик-функции

Функции могут объявлять параметры типа в угловых скобках после имени функции.
Параметр типа является compile-time параметром со значением типа `Type`.
Угловые скобки — короткая запись; полная форма использует уже существующее
ключевое слово `param` в начале тела объявления:

```efen
class Box {
    param T: Type

    var value: T
}
```

Эта форма эквивалентна `class Box<T>`. Как и у функции без круглых скобок,
объявления `param` идут подряд до остальных членов.

### Базовый синтаксис

```efen
fn identity<T>(value: T) -> T {
    return value
}

// Использование
let num = identity<Int>(42)
let str = identity<String>("hello")
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
let strings = map<Int, String>(numbers, fn(n) { return String(n) })
```

### Вывод типов

Компилятор может автоматически выводить параметры типа из аргументов:

```efen
let result = identity(42)  // T выводится как Int
let doubled = map([1, 2, 3], fn(x) { return x * 2 })  // T=Int, U=Int
```

## Дженерик-методы

Методы классов и функций стратегий также могут быть дженерик-методами.

```efen
class Container {
    var items: [Any] = []

    fn add<T>(item: T) {
        items.append(item)
    }

    fn get<T>(index: Int) -> T? {
        if index < items.count {
            return items[index] as? T
        }
        return null
    }
}

// Использование
let container = Container()
container.add<Int>(42)
container.add<String>("hello")

let num: Int? = container.get<Int>(0)
let str: String? = container.get<String>(1)
```

## Дженерик-классы

Классы могут иметь параметры типа, которые применяются ко всему классу.

```efen
class Box<T> {
    var value: T

    init(value: T) {
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
    T  // Встроенная структура типа T
}

// При использовании все поля T становятся частью RefCounted
```

## Дженерик-интерфейсы

Интерфейсы также могут быть дженерик-типами.

```efen
interface Comparable<T> {
    fn compareTo(other: T) -> Int
}

class Person implements Comparable<Person> {
    var age: Int

    fn compareTo(other: Person) -> Int {
        return age - other.age
    }
}
```

## Ограничения типов

Параметры типа могут иметь ограничения (constraints) для указания требований к типам.

```efen
// Базовое ограничение
fn sort<T: Comparable>(items: [T]) -> [T] {
    // T должен реализовывать Comparable
}

// Множественные ограничения
fn process<T: Readable & Writable>(data: T) {
    // T должен реализовывать оба интерфейса
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

Здесь `Particle` — параметр типа, а `SoA` — enum-константа внутри `Array`.
Конкретная инстанциация имеет одну определённую representation.
Запись `[T]` сокращает `Array<T, default>`.

Полная форма позволяет явно указать тип параметра и значение по умолчанию:

```efen
class Array {
    param Element: Type
    param Form: Representation = default
}
```

Атрибут можно передать отдельным параметром:

```efen
class AnnotatedStorage {
    param Element: Type
    param Annotation: Attribute
}

let values = new AnnotatedStorage<Int, @myattr>
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

Любой `param` можно опустить в месте применения, если компилятор однозначно
выводит его значение из остальных аргументов, ограничений и сигнатур. Вывод не
является отдельным видом параметра. Если решений нет или их несколько,
компилятор требует именованный аргумент:

```efen
Iterable<Item: Int> // Cursor выводится из iterator()
Iterable            // Item и Cursor выводятся, если решение однозначно
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
    // ...
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
