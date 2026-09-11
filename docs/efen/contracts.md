# Контракты

> Контакт -- высшая языковая абстракция времени компиляции, которая описывает правила формирования других абстракций.

Контракт устанавливает какие свойства и методы должны быть определены в абстракции.

Примеры контрактов:
```efen
contract MyContract {
    var myProperty: Int { get set }
    func myMethod()
}
```

## ⚠️ Contract vs Interface: Ключевое различие

**Это фундаментальная концепция Efen, которую необходимо понимать:**

### Contract — compile-time абстракция
- ✅ Существует **только** во время компиляции
- ✅ После компиляции **полностью исчезает** из бинарника
- ✅ Используется компилятором для проверки корректности кода
- ✅ Сам по себе не требует runtime-дескриптора или VTBL
- ✅ Позволяет статическую диспетчеризацию, когда конкретная реализация известна

Contract не является типом значения. Его нельзя использовать как тип свойства
или локальной переменной. В позиции параметра функции contract является короткой
записью безымянного generic-параметра, а в `opaque Contract` в позиции результата
— ограничением скрытого конкретного типа. Неизвестное конкретное значение с
runtime-полиморфизмом выражается интерфейсом; обе сокращённые формы contract
остаются статическими и не создают runtime-interface.

### Interface — runtime абстракция
- ✅ Существует в **runtime** как **VTBL** (виртуальная таблица)
- ✅ Присутствует в скомпилированном бинарнике
- ✅ Позволяет полиморфизм во время выполнения
- ✅ Имеет runtime overhead (косвенный вызов через VTBL)
- ✅ Динамическая диспетчеризация (dynamic dispatch)

### Практический пример

```efen
// CONTRACT: только compile-time
contract Drawable {
    fn draw()
}

// INTERFACE: runtime VTBL
interface Shape {
    fn area() -> Float
}

// Класс соответствует контракту и реализует интерфейс
class Circle {
    conforms Drawable      // Compile-time проверка
    implements Shape       // Runtime VTBL

    var radius: Float

    fn draw() {
        // Реализация требования контракта
        print("Рисую круг")
    }

    fn area() -> Float {
        // Реализация метода интерфейса
        return 3.14 * radius * radius
    }
}
```

### Что происходит после компиляции?

```efen
// Compile-time: компилятор проверяет что draw() есть
fn renderStatic<T: Drawable>(object: T) {
    object.draw()  // STATIC DISPATCH - прямой вызов
}

// Runtime: используется VTBL для полиморфизма
fn calculateArea(shape: Shape) -> Float {
    return shape.area()  // DYNAMIC DISPATCH - вызов через VTBL
}
```

**После компиляции:**
- `Drawable` контракт **исчез** — вызов `draw()` скомпилирован напрямую
- `Shape` интерфейс **присутствует** как VTBL в бинарнике
- `calculateArea` может принимать **любой** объект реализующий Shape

Исчезновение contract не означает, что любой использующий его код бесплатен.
Например, скрытый union нескольких реализаций выполняет switch по runtime-тегу.
Эта стоимость принадлежит выбранному представлению и dispatch, а не самому
contract; обычная известная реализация по-прежнему допускает прямой вызов.

### Когда использовать что?

**Используйте Contract когда:**
- ✅ Нужны generic constraints (ограничения на типы)
- ✅ Не нужен обязательный runtime-interface или VTBL
- ✅ Тип известен во время компиляции
- ✅ Хотите максимальную оптимизацию компилятора

**Используйте Interface когда:**
- ✅ Нужен runtime полиморфизм
- ✅ Тип неизвестен во время компиляции
- ✅ Хотите binary compatibility (совместимость бинарников)
- ✅ Реализуете plugin system или динамическую загрузку

### Комбинация Contract + Interface

Можно использовать оба одновременно для максимальной гибкости:

```efen
// Контракт для compile-time проверок
contract Serializable {
    fn serialize() -> String
}

// Интерфейс для runtime полиморфизма
interface Storable {
    fn save(path: String)
}

class Document {
    conforms Serializable  // Compile-time гарантия
    implements Storable    // Runtime возможность

    fn serialize() -> String {
        return "..."
    }

    fn save(path: String) {
        let data = serialize()  // Статический вызов
        writeToFile(path, data)
    }
}

// Generic с контрактом - нулевой overhead
fn sendOver<T: Serializable>(object: T) {
    let data = object.serialize()  // STATIC - оптимально
    network.send(data)
}

// Полиморфный с интерфейсом - runtime гибкость
fn saveAll(objects: [Storable]) {
    for obj in objects {
        obj.save("/tmp/file")  // DYNAMIC - через VTBL
    }
}
```

См. также: [interfaces.md](interfaces.md) для подробного описания интерфейсов.

## Контракты копирования и перемещения

`Movable`, `Copyable` и `ImplicitlyCopyable` являются независимыми
compile-time контрактами возможностей значения, кроме одной явной связи:
`ImplicitlyCopyable` наследует `Copyable`.

```efen
contract Movable {
}

contract Copyable {
    fn copy() -> Self
}

contract ImplicitlyCopyable : Copyable {
}
```

`Movable` разрешает передать существующее значение через `take`. `Copyable`
разрешает создать независимое значение явным `copy()`. Ни один из этих
контрактов не подразумевает другой: перемещаемый ресурс может запрещать копию,
а закреплённое значение может разрешать построение копии, не разрешая перенос
существующего экземпляра.

`ImplicitlyCopyable` не добавляет новый способ копирования. Он разрешает
компилятору вставить имеющийся `copy()` там, где требуется новое значение:

```efen
let second = first
```

Копирование `ImplicitlyCopyable` не меняет исходное значение и не производит
наблюдаемых изменений состояния или ввода-вывода. Внутренняя аллокация, CoW и
изменение скрытого счётчика ссылок допустимы. Копирование может бросить
исключение; эффекты и `throws` неявно вставленного `copy()` входят в выведенный
контракт окружающей функции.

Стоимость копирования остаётся ответственностью автора типа. Generic-код,
который вызывает `copy()` явно, требует `Copyable`, а не
`ImplicitlyCopyable`.

## Параметры контракта

Контракт может объявлять compile-time параметры через `param`. Параметр со
значением типа записывается как `param Name: Type`:

```efen
contract Iterator {
    param Item: Type

    fn next() -> Item?
}
```

Параметры связываются при `conforms`. Позиционная и именованная формы
равноправны:

```efen
class StringIterator {
    conforms Iterator<String>
}

class AnotherStringIterator {
    conforms Iterator<Item: String>
}
```

Параметр может требовать, чтобы переданный тип соответствовал другому
контракту:

```efen
contract Iterable {
    param Item: Type
    param Cursor: Iterator<Item>

    fn iterator() -> Cursor
}
```

`Cursor` здесь является конкретным типом результата. `Iterator<Item>` остаётся
compile-time ограничением и не используется как тип значения. Параметр может
иметь значение по умолчанию: `param Name: Type = DefaultType`. Кроме типов,
`param` принимает любое compile-time значение с указанным типом, включая
enum-константу, число, строку, origin, экземпляр атрибута, contract, interface,
strategy, функцию или другую compile-time декларацию. Переданный contract
остаётся объектом compile-time и не становится типом runtime-значения.

Параметр contract можно не указывать при `conforms`, если его значение
однозначно выводится из реализованных требований:

```efen
class IntList {
    conforms Iterable<Item: Int>

    fn iterator() -> IntListIterator
}
```

Здесь сопоставление с `fn iterator() -> Cursor` выводит
`Cursor = IntListIterator`. Компилятор затем проверяет
`IntListIterator conforms Iterator<Item: Int>`. Неоднозначный вывод является
ошибкой и требует явного именованного аргумента.

Generic-тип может объявить соответствие условно внутри `#if`. Ложное условие
убирает соответствие и его условные члены из конкретной инстанциации, но не
запрещает создать сам тип:

```efen
class Box<T> {
    #if T conforms Copyable {
        conforms Copyable
    }
}
```

Для generic-объявлений угловые скобки служат короткой записью параметров.
Например, `class Box<T>` соответствует полной форме `param T: Type` в начале
тела `Box`.

## Наследование контрактов

Контракты могут наследоваться друг от друга. При наследовании правила контрактов не должны противоречить друг другу.

```efen
contract BaseContract {
    var baseProperty: Int { get set }
    func baseMethod()
}

contract DerivedContract : BaseContract {
    var derivedProperty: String { get set }
    func derivedMethod()
}
```

Множественное наследование контрактов:
```efen
contract FirstContract {
    var firstProperty: Int { get set }
}

contract SecondContract {
    var secondProperty: String { get set }
}

contract CombinedContract : FirstContract, SecondContract {
    func combinedMethod()
}
```

**Важно:** При множественном наследовании компилятор проверит, что требования базовых контрактов не противоречат друг другу.

## Связь контрактов с интерфейсами

Интерфейс может **соответствовать** (`conforms`) одному или нескольким контрактам. Это означает, что
компилятор проверит на этапе компиляции, что интерфейс удовлетворяет всем требованиям контракта.

Базовый пример:
```efen
interface MyInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Интерфейс с наследованием от родительского интерфейса:
```efen
interface ParentInterface {
    var parentProperty: Bool { get set }
    func parentMethod()
}

interface MyInterface : ParentInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Множественные контракты:
```efen
contract SecondContract {
    func additionalMethod()
}

interface MyInterface : ParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

Множественное наследование интерфейсов с контрактами:
```efen
interface AnotherParentInterface {
    var anotherParentProperty: Float { get set }
}

interface MyInterface : ParentInterface, AnotherParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

## Шаблоны структур в контрактах

Контракты во многом похожи на generic в том смысле, что некоторые структуры данных в них могут быть 
определены как шаблоны. При этом полезна возможность задать некие правила или ограничения на эти шаблоны.
Например, ARC-объект может быть представлен как структура данных, которая содержит счетчик ссылок и данные объекта.

```efen
contract RefCountedContract {

    requires struct: struct<T>

    @base struct <T> {
        var refCount: Int
        T
    }

    fn retain(self: Self)
    fn release(self: Self)
}
```
