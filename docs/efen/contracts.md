# Контракты

[Документация](index.md) · [Словарь](glossary.md) · [Interfaces](interfaces.md) · [Стратегии](strategies.md)

> Контакт -- высшая языковая абстракция времени компиляции, которая описывает правила формирования других абстракций.

Контракт устанавливает какие свойства и методы должны быть определены в абстракции.

Примеры контрактов:
```efen
contract MyContract {
    var myProperty: Int { get set }
    fn myMethod
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
или локальной переменной. Generic-функция сначала объявляет конкретный тип через
`generic T: Contract`, а затем использует `T` как тип runtime-параметра.
`opaque Contract` в позиции результата ограничивает скрытый конкретный тип.
Неизвестное конкретное значение с runtime-полиморфизмом выражается интерфейсом.
`opaque Contract` остаётся статической формой и не создаёт runtime-interface.

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
    fn draw
}

// INTERFACE: runtime VTBL
interface Shape {
    fn area -> Float
}

// Класс соответствует контракту и реализует интерфейс
class Circle {
    conforms Drawable      // Compile-time проверка
    implements Shape       // Runtime VTBL

    var radius: Float

    fn draw {
        // Реализация требования контракта
        print("Рисую круг")
    }

    fn area -> Float {
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
Например, скрытый structural union нескольких реализаций выполняет switch по
runtime-тегу.
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
    fn serialize -> String
}

// Интерфейс для runtime полиморфизма
interface Storable {
    fn save(path: String)
}

class Document {
    conforms Serializable  // Compile-time гарантия
    implements Storable    // Runtime возможность

    fn serialize -> String {
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
    fn copy -> Self
}
```

Кандидат записи пока показывается только как текст:

```text
contract ImplicitlyCopyable : Copyable {
}
```

Отношение `ImplicitlyCopyable` уточняет `Copyable` семантически, но показанная
запись через `:` остаётся кандидатом Q46, а не принятой surface-формой.

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

Для `ImplicitlyCopyable` канонична неявная копия: `let second = first`. Явный
вызов `first.copy()` для такого типа получает диагностику стиля с исправлением
на присваивание. Для остальных `Copyable` копия записывается только `copy()`.

Копирование `ImplicitlyCopyable` не меняет исходное значение и не производит
наблюдаемых изменений состояния или ввода-вывода. Внутренняя аллокация, CoW и
изменение скрытого счётчика ссылок допустимы. Копирование может бросить
исключение; эффекты и `throws` неявно вставленного `copy()` входят в выведенный
контракт окружающей функции.

Стоимость копирования остаётся ответственностью автора типа. Generic-код,
который вызывает `copy()` явно, требует `Copyable`, а не
`ImplicitlyCopyable`.

## Параметры контракта

Контракт объявляет compile-time параметры через `generic`. Параметр со
значением типа записывается как `generic Name: Type`:

```efen
contract Iterator<Item> {
    fn next -> Item?
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
contract Iterable<Item, Cursor: Iterator<Item>> {
    fn iterator -> Cursor
}
```

`Cursor` здесь является конкретным типом результата. `Iterator<Item>` остаётся
compile-time ограничением и не используется как тип значения. Параметр может
иметь значение по умолчанию: `generic Name: Type = DefaultType`. Кроме типов,
`generic` принимает любое compile-time значение с указанным типом, включая
значение enum, число, строку, origin, экземпляр атрибута, contract, interface,
strategy, функцию или другую compile-time декларацию. Переданный contract
остаётся объектом compile-time и не становится типом runtime-значения.

Параметр contract можно не указывать при `conforms`, если его значение
однозначно выводится из реализованных требований:

```efen
class IntList {
    conforms Iterable<Item: Int>

    fn iterator -> IntListIterator
}
```

Здесь сопоставление с `fn iterator -> Cursor` выводит
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

`generic` является полной формой параметра объявления. Список в угловых скобках
остаётся допустимой короткой формой там, где она предусмотрена объявлением.

## Наследование контрактов

Q46 оставляет запись уточнения и наследования контрактов открытой. Следующие
фрагменты — только варианты для исследования, а не допустимый синтаксис Efen.

```text
contract BaseContract {
    var baseProperty: Int { get set }
    fn baseMethod
}

contract DerivedContract : BaseContract {
    var derivedProperty: String { get set }
    fn derivedMethod
}
```

Множественное наследование контрактов также является открытым вариантом:
```text
contract FirstContract {
    var firstProperty: Int { get set }
}

contract SecondContract {
    var secondProperty: String { get set }
}

contract CombinedContract : FirstContract, SecondContract {
    fn combinedMethod
}
```

Правила проверки и форма множественного наследования будут добавлены после
отдельного решения Q46.

## Связь контрактов с интерфейсами

Runtime-interface из contract создаётся только явной декларацией:

```efen
contract DrawableContract {
    fn draw
}

interface DrawableInterface from DrawableContract
```

`DrawableInterface` сохраняет compile-time identity исходного
`DrawableContract` и проверяется как соответствующий ему (`conforms`). В
runtime-поверхность переносятся только вызываемые методы. Associated types,
требования к representation и другие compile-time ограничения проверяются при
создании и реализации interface, но автоматически не материализуются в runtime
metadata. Каждая runtime-сигнатура должна быть полностью замкнута: несвязанный
associated type или `Self` и неудовлетворённое representation-требование
являются ошибкой, а не молча стираются. Нужную runtime metadata может отдельно
породить метакод.

Без `interface ... from ...` contract остаётся только compile-time абстракцией
и сам по себе не создаёт VTBL.

Интерфейс может **соответствовать** (`conforms`) одному или нескольким контрактам. Это означает, что
компилятор проверит на этапе компиляции, что интерфейс удовлетворяет всем требованиям контракта.

Базовый пример:
```efen
interface MyInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Наследование интерфейсов также остаётся открытым; ниже приведён
исследовательский вариант, а не нормативный синтаксис:
```text
interface ParentInterface {
    var parentProperty: Bool { get set }
    fn parentMethod
}

interface MyInterface : ParentInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Множественные контракты в conforms уже определены Q46; открытой остаётся
только форма наследования самих интерфейсов:
```text
contract SecondContract {
    fn additionalMethod
}

interface MyInterface : ParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

Множественное наследование интерфейсов с контрактами также является
исследовательским вариантом:
```text
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
