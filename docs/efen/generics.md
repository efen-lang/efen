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

Методы классов и структур также могут быть дженерик-методами.

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
class Container<T> {
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

class Person: Comparable<Person> {
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
type Result<T> = (T | Error)
type Handler<T> = (T) -> Void
function Transformer<T, U> = (T) -> U

// Использование
fn processData<T>(handler: Handler<T>) {
    // ...
}
```

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

1. Параметры типа не могут использоваться для создания статических членов
2. Дженерик-типы не могут быть использованы в `typeof` выражениях напрямую
3. Рефлексия над дженерик-типами ограничена из-за type erasure

## Смотрите также

- [Функции](functions.md)
- [Классы](classes.md)
- [Структуры](structs.md)
- [Интерфейсы](interfaces.md)
- [Алиасы типов](type-aliases.md)
