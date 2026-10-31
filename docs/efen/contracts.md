# Контракты

[Документация](README.md) · [Словарь](glossary.md) · [Interfaces](interfaces.md) · [Стратегии](strategies.md)

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

Уточнение одного контракта другим пишется через `:`:

```efen
contract ImplicitlyCopyable : Copyable {
}
```

`ImplicitlyCopyable` уточняет `Copyable`: тип, соответствующий первому,
обязан соответствовать и второму.

`Movable` разрешает передать существующее значение через `take`. `Copyable`
разрешает создать независимое значение оператором `copy`. Ни один из этих
контрактов не подразумевает другой: перемещаемый ресурс может запрещать копию,
а закреплённое значение может разрешать построение копии, не разрешая перенос
существующего экземпляра.

### Оператор `copy`

Копия записывается префиксным оператором `copy x`, как перенос — `take x`. Оператор
вызывает метод `copy()` контракта `Copyable` типа `x`; сам метод объявляет и
реализует тип, а вызывается он только оператором (Edmond 2026-10-29).
Три способа отдать значение читаются одинаково, действие стоит первым словом:

```efen
send(take message)     // отдаёт владение
send(copy message)     // отдаёт независимую копию
send(message)          // одалживает
```

Копия стоит памяти и времени, поэтому она видна в начале выражения, а не в конце
цепочки. `copy x` для типа без `Copyable` — ошибка компиляции. Оператор связывает
слабее `.`: `copy a.b` копирует `a.b`.

`copy` — глубокая копия (Edmond 2026-10-31): у результата свои экземпляры всех данных в куче, которыми владеет
источник, поэтому `copy` строки, `indirect`-variant или класса с одним владельцем выделяет память и может бросить
`AllocationError`. Копия, которая провалилась на середине, разрушает уже построенное, как любой конструктор.

### Оператор `clone`

`clone x` копирует только верхний уровень значения: данные в куче остаются общими у источника и копии (Edmond
2026-10-31: «clone — это другое»). Без счётчика ссылок общий блок освободили бы дважды, поэтому `clone`
допустим только у типа со счётчиком ссылок, где он увеличивает счётчик, или там, где код layout доказывает, что
копия не переживёт источник. В остальных случаях `clone x` — ошибка компиляции.

```efen
let tree2 = copy tree      // своё дерево: каждый блок выделен заново
let shared = clone handle  // тот же объект, счётчик ссылок + 1
let wrong = clone tree     // ошибка: у `tree` нет счётчика ссылок
```

Не решено (агент): префиксная форма `clone x` взята по аналогии с `copy x`; каким контрактом тип разрешает `clone`,
не выбрано.

Префиксные операторы связывают сильнее `as`, поэтому `copy a as B` — это
`(copy a) as B`.

`copy` — контекстное слово, как `take` и `capture`. Оператором оно является, только
когда за ним через пробел идёт начало операнда: имя, литерал, `(`, `[`, `%`, `take`
или `copy`. Знаки `+ - ! ~ ++ --` операнд не начинают: `copy + 1`, `copy - n` и
`copy !flag` читаются как выражения над переменной `copy`. После `.` и перед `=`,
`:`, `.` или `(` это обычное имя, поэтому `let copy = twin`, `copy.second`, функция
`copy(from:to:)` и метод `fn copy -> Self` остаются допустимыми, как и метод
`numbers.take(3)`. Прямой вызов `x.copy()` метода `Copyable` получает диагностику
стиля с исправлением на `copy x`; другие члены с именем `copy` не затрагиваются. Как
значение функции копия пишется замыканием: `items.map((x) => copy x)`.

`ImplicitlyCopyable` говорит о передаче параметров: значение такого типа выгодно передавать в функцию копией, а
не по ссылке, как `Int` в регистре (Edmond 2026-10-31). Компилятор по нему решает, копировать ли аргумент. К
`let x = y` контракт отношения не имеет.

```efen
fn area(p: Point) -> Int { … }
area(point)          // Point — ImplicitlyCopyable: передаётся копией
evaluate(expression) // indirect variant: передаётся по ссылке
```

Копирование `ImplicitlyCopyable` не меняет исходное значение, не производит
наблюдаемых изменений состояния или ввода-вывода и не выделяет память: тип, копия которого выделяет память, не
бывает `ImplicitlyCopyable`, передавать его копией невыгодно (Edmond 2026-10-31). Изменение скрытого счётчика
ссылок допустимо. Явная копия такого типа пишется, как у любого `Copyable`, `copy x`.

Стоимость копирования остаётся ответственностью автора типа. Generic-код,
который пишет `copy x` явно, требует `Copyable`, а не
`ImplicitlyCopyable`.

## Доступ метода к self

Метод контракта пишет, меняет ли он `self`, тем же правом, что и параметр.
`mut fn` может менять `self` целиком, включая структуру: добавить элемент,
убрать его, записать `self` заново. `edit fn` меняет только значения внутри
`self`, структура остаётся прежней. `read fn` только читает `self`. Метод без
пометки тоже только читает: пометка `read` записывает умолчание явно, как у
параметров.

```efen
contract Stack<T> {
    mut fn push(item: T)
    mut fn pop -> T?
    fn peek -> T?          // то же, что read fn peek -> T?
}

contract Cursors<T> {
    edit fn next(cursor: mut Cursor) -> edit T?
}
```

`edit fn` нужен методу, который отдаёт место `edit` в `self`
([место в результате функции](types/ownership.md#место-в-результате-функции)):
вызов `mut fn` может перестроить `self`, поэтому место из прошлого вызова
умирает, а после вызова `edit fn` оно живёт. Два курсора через контракт
работают только так:

```efen
fn pair(items: edit Cursors<Item>, a: mut Cursor, b: mut Cursor) {
    if let x = items.next(cursor: a) {
        if let y = items.next(cursor: b) {   // x жив: next не меняет структуру items
            x.count = y.count
        }
    }
}
```

Пометку `edit fn` ввёл Edmond 2026-10-29. Метод `edit fn` вызывается у
получателя `edit` и `mut`, но не у получателя без права записи (предложение
агента: так же, как параметр `edit` принимает только место с правом записи).
Так проверяется вызов через контракт или интерфейс, где видна одна пометка.
Прямой вызов метода класса проверяется по его телу, как вызов `mut fn`: `edit fn`,
который ничего не меняет, можно вызвать и у получателя без права записи. Вызов
`mut fn` через интерфейс может перестроить `self`, поэтому получатель `edit` его
не принимает (решения агента, S80.7).

Компилятор не смотрит в реализации, когда проверяет вызов через контракт:
вызывающий читает только пометку. Реализация проверяется по пометке там, где
она написана. Тело `peek`, которое меняет поле `self`, — ошибка в этом теле, а
не у вызывающего; так же ошибка — тело `edit fn`, которое меняет структуру
`self`. Реализация может быть уже пометки, но не шире: метод `mut fn`
реализуют `mut fn`, `edit fn` или `read fn`, метод `edit fn` — `edit fn` или
`read fn`.

Контракт остаётся такой границей и при сборке всей программы: его реализуют
типы, которые автор контракта не видит. Методы классов при сборке всей
программы пометки не требуют, см. [«Классы»](classes.md#доступ-метода-к-self).

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
    #if T conforms Copyable
        conforms Copyable
    #endif
}
```

`generic` является полной формой параметра объявления. Список в угловых скобках
остаётся допустимой короткой формой там, где она предусмотрена объявлением.

## Наследование контрактов

`:` у contract уточняет всех перечисленных parents. Соответствующий тип обязан
удовлетворять транзитивному объединению их требований:

```efen
contract Seekable : Readable, Writable {
    fn seek(position: Int)
}
```

Повтор одного ancestor с теми же resolved generic arguments дедуплицируется.
Members с одним именем допустимы лишь при идентичной нормализованной
requirement-signature: parameters, result, state, contexts, `throws` и rights.
Иначе declaration самого contract ошибочна. `use`/`as` не применяются: они
разрешают runtime member conflicts interface, а contract задаёт compile-time
requirements.

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

Интерфейс может наследовать один или несколько interface. Это расширяет
runtime-протокол, не добавляя storage:
```efen
interface ParentInterface {
    var parentProperty: Bool { get set }
    fn parentMethod
}

interface MyInterface : ParentInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Множественные контракты в conforms уже определены Q46:
```efen
contract SecondContract {
    fn additionalMethod
}

interface MyInterface : ParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

Множественное наследование интерфейсов с контрактами допустимо:
```efen
interface AnotherParentInterface {
    var anotherParentProperty: Float { get set }
}

interface MyInterface : ParentInterface, AnotherParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

## Классы в контракте

Контракт может потребовать класс, как требует функцию. Класс в контракте задаёт то, что видит код снаружи: имя, базовый
класс, `open` и `final`, `conforms`, конструкторы и подписи методов с эффектами. Тел у методов нет, полей нет. Поля и
тела даёт реализация контракта (Edmond, 2026-10-31):

```efen
// lang/exceptions.efen
contract Exceptions {
    open class Exception {
        conforms Throwable
        @constructor fn init() -> Self
        open fn reason() -> Reason nofail
    }
}

// рантайм
implementation Exceptions {
    class Exception {
        var message: String
        @constructor fn init() -> Self { … }
        fn reason() -> Reason nofail { return .program }
    }
}

// программа
class ParseError: Exception { }
try { parse(text) } catch e: Exception { log(e.message) }
```

- **Класс в контракте — всегда требование.** Контракт не определяет классы сам; класс с телами пишут рядом с
  контрактом, в том же файле. Поэтому отдельного слова для требования нет: класс без тел методов читается как `fn` без
  тела.
- **Только в контракте, который реализуют через `implementation`.** Класс в контракте, который соблюдают через
  `conforms` или называют в `generic T: Contract`, — ошибка компиляции: такой контракт не для классов. Тип, который
  выбирает соблюдающий, задают параметром контракта (`Iterable<Item>`).
- **Имя принадлежит модулю контракта.** Программа пишет `Exception` или `lang::Exception`, а не
  `Exceptions.Exception`: контракт не пространство имён. Объявление с тем же именем в том же модуле — ошибка. Класс
  внутри `implementation` не вводит нового имени: это тот же тип.
- **Реализация повторяет подписи и добавляет своё.** Она не меняет базовый класс, `open`, `conforms` и подписи из
  контракта, даёт тело каждому методу и может добавить поля и члены. Открытые члены, которые она добавила, программа
  видит (`e.message` выше), и тогда программа зависит от этой реализации.
- **Одна реализация в программе.** Реализацию выбирает конфигурация сборки, как для контракта `@unique`
  ([связывание](context-and-effects.md)). Раскладка класса зависит от реализации, поэтому другой выбор пересобирает
  пакеты, которые наследуют такой класс или читают его поля.
- **В любом пакете.** Первое применение — корни исключений в `lang::`, но объявлять классы в контракте может любой
  пакет.

Открыто (агент, 2026-10-31): как строка конфигурации называет блок `implementation`, у которого нет своего имени;
наследование контракта с классами.

## Поля, которые требует контракт

Контракт описывает функции, полей он не объявляет. Поле, которое нужно его
функциям, в тип добавляет аспект: интерфейс storage не владеет
([интерфейсы](interfaces.md)). Например, объект со счётчиком ссылок получает
устройство с полем `refCount` от аспекта, а контракт перечисляет функции над ним
(как в [аспектах компиляции](aspects/compile-time/index.md#управление-памятью)):

```efen
contract RefCounted {
    mut fn retain
    mut fn release
}

aspect RefCountClassCompiler {
    conforms ClassDefinition
    conforms RefCounted

    struct Header {
        var refCount: UInt
    }
}
```

Ранняя форма шаблона структуры внутри контракта (`requires struct: struct<T>`,
`@base struct <T> { … }`) в язык не входит (агент, 2026-10-29): поля даёт аспект.
