# Классы

> Классы являются абстракцией над структурами данных и поведением объектов.

Классы скрывают работу со структурами данных и предоставляют программисту удобный синтаксис для определения
состояния и поведения объектов. Классы могут иметь состояние (свойства) и поведение (методы).

## Определение класса

Базовый пример класса:

```efen
class Person {
    var name: String
    var age: Int

    fn greet {
        print("Hello, my name is ${name}")
    }

    fn haveBirthday {
        age += 1
        print("${name} is now ${age} years old")
    }
}
```

Использование класса:

```efen
let person = Person(name: "Alice", age: 30)
person.greet()  // Выведет: "Hello, my name is Alice"
person.haveBirthday()  // Выведет: "Alice is now 31 years old"
```

## Конструкторы

`Self` является алиасом текущего лексического класса, в объявлении которого он
написан. Он не меняется на тип наследника при позднем связывании.

Классы могут иметь пользовательские конструкторы:

```efen
class Rectangle {
    var width: Float
    var height: Float

    @constructor
    fn init(width: Float, height: Float) -> Self {
        self.width = width
        self.height = height
    }

    fn area -> Float {
        return width * height
    }
}

let rect = Rectangle(width: 10.0, height: 5.0)
```

До полной инициализации `self` не может escape: его нельзя вернуть, сохранить,
захватить или передать внешнему вызову. Compiler-proven `private final` helper
допустим, если он не выпускает `self` и не читает неинициализированные поля.
Обычная виртуальная диспетчеризация не отключается в constructor, включая
наиболее производный override. Такой вызов допустим, только если compiler
докажет для каждого достижимого override и его вызовов, что до завершения
инициализации они не читают и не передают дальше неинициализированное состояние
`self`; иначе это ошибка в constructor.

## Наследование классов

Классы и методы являются final по умолчанию. `open class` разрешает
наследование, а `open fn` — переопределение метода:

```efen
final class Closed {}
```

Явный `final` закрепляет и документирует то же ограничение, которое действует
по умолчанию. Он также доступен для метода.

```efen
open class Animal {
    var name: String

    open fn makeSound {
        print("Some generic sound")
    }
}

class Dog: Animal {
    var breed: String

    override fn makeSound {
        print("Woof!")
    }

    fn fetch {
        print("${name} is fetching the ball")
    }
}

let dog = Dog(name: "Buddy", breed: "Golden Retriever")
dog.makeSound()  // Выведет: "Woof!"
dog.fetch()  // Выведет: "Buddy is fetching the ball"
```

`override fn` переопределяет открытый метод и снова делает его final. Если
следующий наследник тоже должен иметь право переопределения, текущий уровень
пишет `open fn`; наличие базового метода уже означает override:

```efen
open class Middle: Animal {
    open fn makeSound {
        print("Middle")
    }
}
```

`open fn` внутри final-класса является ошибкой, поскольку такой метод невозможно
унаследовать. Метод с именем открытого метода базы, написанный без `override` и
без `open`, — тоже ошибка: переопределение пишется явно, чтобы совпадение имён
не переопределило метод случайно. Отдельного модификатора `abstract` в Efen нет.

### Доступ метода к self

Метод класса может написать `mut fn`, `edit fn` или `read fn`, как метод
контракта, но не обязан. Без пометки компилятор выводит доступ к `self` из тела. `own fn`
компилятор не выводит: он меняет форму вызова на `(take x).m()`, поэтому
пометку `own` пишут всегда ([«Контракты»](contracts.md#доступ-метода-к-self)). Вызов
`open fn` при сборке всей программы делает всё, что делает любой достижимый
override, поэтому выведенного доступа достаточно ([«Режимы
компиляции»](compilation-modes.md#сборка-всей-программы)).

Пометка у `open fn` — обещание для наследников. Override метода `read fn` не
может менять `self`, и вызывающий читает такой метод по пометке, не
перебирая override:

```efen
open class Shape {
    open read fn area -> Float { return 0.0 }
}

class Square: Shape {
    var side: Float
    var calls: Int = 0

    override read fn area -> Float {
        calls += 1           // ошибка: area объявлен как read fn
        return side * side
    }
}
```

## Реализация интерфейсов

Классы могут реализовывать один или несколько интерфейсов:

```efen
interface Drawable {
    fn draw
}

interface Resizable {
    mut fn resize(scale: Float)
}

class Circle {
    implements Drawable, Resizable

    var radius: Float
    var position: Point

    fn draw {
        print("Drawing circle at ${position} with radius ${radius}")
    }

    fn resize(scale: Float) {
        radius *= scale
    }
}
```

## Соответствие контрактам

Классы могут соответствовать контрактам времени компиляции:

```efen
contract Serializable {
    fn serialize -> String
    mut fn deserialize(data: String)
}

class User {
    conforms Serializable

    var name: String
    var email: String

    fn serialize -> String {
        return "${name};${email}"
    }

    fn deserialize(data: String) {
        let parts = data.split(separator: ";")
        self.name = parts[0]
        self.email = parts[1]
    }
}
```

## Комбинирование наследования, интерфейсов и контрактов

Класс может одновременно наследоваться от базового класса, реализовывать интерфейсы и соответствовать контрактам:

```efen
contract Validatable {
    fn validate -> Bool
}

interface Storable {
    fn save
    mut fn load
}

open class Entity {
    var id: Int
    var createdAt: DateTime
}

class Product: Entity {
    conforms Validatable
    implements Storable

    var name: String
    var price: Float

    fn validate -> Bool {
        return !name.isEmpty && price > 0
    }

    fn save {
        print("Saving product ${name}")
    }

    fn load {
        print("Loading product")
    }
}
```

Синтаксис:
- `: BaseClass` в заголовке — одиночное наследование класса. После `:` стоит
  только базовый класс, интерфейсы там не перечисляются
- `conforms Contract1, Contract2` в теле — соответствие контрактам (множественное)
- `implements Interface1, Interface2` в теле — реализация интерфейсов

Каждое из объявлений `conforms` и `implements` пишется одной строкой через запятую.
В теле первой идёт строка `conforms`, за ней `implements`, затем члены класса.

## Свойства класса

### Вычисляемые свойства

Классы могут иметь вычисляемые свойства:

```efen
class Rectangle {
    var width: Float
    var height: Float

    var area: Float {
        get {
            return width * height
        }
    }

    var perimeter: Float {
        get {
            return 2.0 * (width + height)
        }
    }
}

let rect = Rectangle(width: 10.0, height: 5.0)
print(rect.area)  // Выведет: 50.0
print(rect.perimeter)  // Выведет: 30.0
```

### Свойства с наблюдателями

Свойства могут иметь наблюдатели изменений:

```efen
class Temperature {
    var celsius: Float {
        didSet {
            print("Temperature changed from ${oldValue} to ${celsius}")
        }
        willSet {
            print("Temperature will change to ${newValue}")
        }
    }
}
```

## Методы класса

### Статические методы

Классы могут иметь статические методы и свойства:

```efen
class Math {
    const PI: Float = 3.14159

    static fn max(a: Float, b: Float) -> Float {
        return a > b ? a : b
    }

    static fn min(a: Float, b: Float) -> Float {
        return a < b ? a : b
    }
}

let maxValue = Math.max(a: 10.0, b: 20.0)
let pi = Math.PI
```

`const` в классе — значение, вычисленное при сборке, одно на программу.

**`static let` и `static var` в классе — переменные потока (thread-local).** У каждого потока своё значение;
между потоками оно не делится, поэтому гонки на нём нет. Одного значения на всю программу класс объявить не
может: для этого есть [контекст процесса](context-and-effects.md#контексты-процесса-и-потока).

```efen
class Parser {
    static var depth: Int = 0                           // своя у каждого потока
    static let keywords: Map<String, Token> = makeKeywords()
}
```

Правила те же, что у поля [контекста потока](context-and-effects.md#контексты-процесса-и-потока):

- значение создаётся при первом обращении в потоке и уничтожается, когда поток завершается. Общего порядка
  создания нет: если начальное значение читает другое, то другое создаётся тут же, внутри. К чему поток не
  обратился, то в нём не создаётся;
- значение, которое вычисляется при сборке (`static var depth: Int = 0`), лежит в сегменте потока (TLS) сразу:
  каждый новый поток получает готовую копию, и создавать нечего;
- начальное значение не бросает и не ждает. Исключение, вылетевшее из него, останавливает программу с именем
  поля. Круг (`A` при создании читает `B`, а `B` читает `A`) — ошибка сборки; круг, видимый только во время
  работы, останавливает программу;
- ссылка на `static`-поле или внутрь него умирает в каждой точке ожидания: корутина может проснуться на другом
  потоке, где своё значение. Обращение через имя класса после пробуждения находит значение нового потока.

```efen
class Config {
    static let port: Int = defaultPort()
}
class Server {
    static let address: String = "0.0.0.0:${Config.port}"
}

fn main {
    print("start")             // ещё ничего не создано
    print(Server.address)      // создаётся address; ему нужен Config.port, он создаётся первым
    print(Config.port)         // уже создан
}
```

У каждой конкретной инстанциации generic-класса своё поле: `Cache<Int>.table` и `Cache<String>.table` — разные
значения, даже если реализация общая.

### Методы экземпляра

Обычные методы работают с конкретным экземпляром класса:

```efen
class Counter {
    var count: Int = 0

    fn increment {
        count += 1
    }

    fn decrement {
        count -= 1
    }

    fn reset {
        count = 0
    }
}
```

## Проекции класса

Проекции это мощный механизм объявить разные представления одной и той же структуры данных
с целью манипуляций.

Проекция может временно изменить доступ к свойствам класса, а после 
преобразовать проекцию в сам класс или другую проекцию.

Так как проекции гарантируют совершенное бинарное равенство 
между исходной структурой и проекцией, проекции позволяют временно раскрыть данные класса
без опасности нарушить внутреннее состояние или логику внутреннего состояния. При этом операции
будут происходить физически на одной и той же структуре данных без копирования.

Механизм проекций так же позволяет выделять память для класса в разных аллокаторах, 
а после инициализировать класс с помощью конструктора без копирования данных, переноса и так далее.

При этом проекции гарантируют безопасность доступа к данным, сохранения сокрытия данных, 
так как они описывают манипуляции над разными типами данных, и с точки зрения
компилятора программист не может без явного преобразования превратить один тип в другой.

## Управление памятью

Класс по умолчанию без счётчика ссылок: у объекта один владелец, и FLOW проверяет его, как любое значение.
Объект тонкий: заголовка со счётчиком у него нет. `let b = a` даёт второе имя того же объекта, а не второго
владельца ([связывание существующего значения](types/ownership.md#связывание-существующего-значения)); `take`
передаёт владение; `copy` есть только у класса с `Copyable`; `clone` — ошибка.

```efen
class Box {
    var value: Int
}

let box1 = Box(value: 10)
let box2 = box1             // второе имя того же объекта
box2.value = 20
print(box1.value)           // Выведет: 20
let box3 = take box1        // владелец теперь box3
```

Класс, объекты которого делят несколько владельцев, пишет `conforms RefCount`. У такого объекта есть счётчик
владельцев, его слоты — `managed` ([владение](types/ownership.md#аспекты-владения)), `let b = a` даёт второго
владельца, `clone` увеличивает счётчик ([`clone`](contracts.md#оператор-clone)). Счётчик и операции над ним даёт
пакет std ([подсчёт ссылок](memory.md#подсчет-ссылок)).

```efen
class Config {
    conforms RefCount

    var timeout: Int
}

let config = Config(timeout: 30)
let other = clone config    // тот же объект, счётчик + 1
```

Третий вид — [класс над внешним значением](#класс-над-внешним-значением): объект — это значение, которое
создал внешний код (C, `@asm`, бинарный пакет).

## Класс над внешним значением

Класс над внешним значением — класс, объект которого создаёт внешний код: функция C, вставка `@asm`, бинарный
пакет. Объект — само это значение (сырое значение): тот же размер, выравнивание и регистр, без заголовка,
счётчика, выделения памяти и таблицы методов на объект. Своей памяти Efen у объекта нет, поэтому хранимое поле в
таком классе — ошибка компиляции. Счётчика у него тоже нет: один владелец и проверка FLOW, как у
[класса по умолчанию](#управление-памятью).

Сырое значение задаёт одна из двух форм:

- `representation Raw<R>`, где `R` — целый тип или его [уточнение](types/refinement-types.md);
- `@abi(c)` у класса без строки `representation`: сырое значение — тип C класса. `@c("имя")` у класса называет
  этот тип (typedef или struct); без `@c` имя класса — непрозрачная структура C, и сырое значение — указатель
  `Имя*`.

От формы зависит пустое значение `T?`: у указателя это `NULL` без доплаты, у целого и typedef — только то, что
объявил модуль ([внутреннее представление optional](types/optional.md#внутреннее-представление)).

```efen
type Descriptor: Int32 { value >= 0 }

public class File {
    representation Raw<Descriptor>               // объект — дескриптор
    …
}

@abi(c) class sqlite3 { … }                      // сырое значение — sqlite3*
@c("pthread_t") @abi(c) class Thread { … }       // сырое значение — pthread_t, пустого значения нет
```

В одном классе можно смешивать методы с телом и внешние методы. Наследования и `open fn` у такого класса нет,
`conforms` есть. Сырое значение читается только в модуле класса, через representation; форма такого чтения не
решена.

### Внешние методы

Внешний метод — метод без тела с `@abi(c)` (взятым у класса или написанным у метода) или метод с телом `@asm`.
`self` пишется в списке параметров на позиции C, если хендлер в C стоит не первым:
`mut fn fputs(text: read CString, self)`; без записи `self` первый. У `@asm` `self` получает регистр, как параметр:
`@in(rdi) self`. На первой позиции `self` пишут явно, только когда у него есть `?`, `{}` или регистр. Право
`self` даёт пометка метода: `read fn`, `mut fn`, `own fn`.

Внешнему методу без тела нужен `nocontext` или `in`. Вокруг таких методов в теле класса может стоять
[блок объявлений](foreign.md#блок-объявлений-c) с этими словами, по правилам блока верхнего уровня: `private` и
атрибуты пишутся у метода, `model` после сигнатуры внутри блока допустим, метод с телом — ошибка.

`mut fn` класса над внешним значением меняет внешний объект, а не сырое значение. Поэтому его вызывают и через
`mut`, и через ссылку `edit`. Заменить сырое значение в слоте (присваиванием или `take` из слота) можно только
через `mut` на слоте, как любое владеющее значение; запись владеющего значения через ссылку `edit` меняет
структуру и запрещена:

```efen
mut fn statement(sql: read String) -> edit<self.cache> sqlite3_stmt?

conn.statement(sql)!.sqlite3_step()              // можно: mut fn внешнего объекта через edit
conn.statement(sql)! = take other                // ошибка: запись владеющего значения через edit
```

### Конструкторы внешнего объекта

`@constructor` у внешней функции бывает трёх видов:

1. Результат несёт объект: `-> Self`, `-> Self?` (`own` подразумевается) или вариант
   [`Packed`](types/variant.md#представление-packed), случай которого держит `own Self`. Вызов —
   `File.openX86(…)`; сокращение `Тип(аргументы)` остаётся для `-> Self` и `-> Self?`. `-> Self?` у внешней
   функции допустим, только если при отказе она возвращает ровно объявленное пустое значение. Функция, у которой
   отказ — диапазон в том же слове (`-errno`), возвращает вариант `Packed`.
2. `self` на выходной позиции, результат — код внешней стороны. Вызов идёт через имя типа, метка `self:` называет
   слот вызывающего: `sqlite3_stmt.sqlite3_prepare_v2(db: db, …, self: s)`.
3. Объекты, записанные в массив вызывающего: `fds: mut [File?]` (элементы пусты перед вызовом и проверяются после)
   или `fds: out [File] { посылка ==> out }` (записаны ровно на путях посылки), с `requires fds.count == n`.
   Каждый элемент проверочная сборка записывает в таблицу хендлеров как выданный.

Кортеж в результате конструктором не бывает.

Выходной слот, который пишет внешняя функция, объявляется одной из двух форм; голый `self` на выходной позиции —
ошибка, которая называет обе:

- `self?` (у другого параметра — `p: mut T?`): слот типа `mut T?`, пуст перед вызовом, функция пишет его на
  каждом возврате — объект или объявленное пустое значение. Вызывающий проверяет слот, а не код возврата. Нужно
  пустое значение сырого типа.
- `self { посылка ==> out }` (у другого параметра — `p: out T { посылка ==> out }`): слот типа `T` записан ровно на
  путях посылки (`result` или `throws E`, как у условного `take`), на остальных путях не записан и не читается.
  Пустое значение не нужно, и проверки по нему FLOW не добавляет: читается только посылка.

```efen
@constructor fn sqlite3_open(filename: read CString, self?) -> Int32
@constructor fn pthread_create(self { result == 0 ==> out }, attr: read pthread_attr_t?, …) -> Int32
@constructor fn posix_spawn(pid: out Pid { result == 0 ==> out }, …) -> Int32
@constructor fn open_thing(self) -> Int32        // ошибка: нужен self? или self { посылка ==> out }
```

В модели конструктора `self` после вызова имеет тип `Self?` при `self?`, и модель пишет в него под
`if let s = self { … }`; при посылке `self` есть ровно под её проверкой (`if result == 0 { … }`). `!` у
возможно пустого `self` в модели — ошибка.

Получатель с посылкой — `own fn m(self { посылка ==> take })`: метод забирает объект только на путях посылки.
Его вызывают на владеющем optional-слоте без `take` (`db.sqlite3_close()`), и после вызова слот пуст ровно на путях
посылки, как у параметра `own T? { … ==> take }`. Безусловный `own fn` вызывается как `(take x).m()`.

Конструктор с телом на Efen кончается `return Self(raw: r)`. `Self(raw:)` пишется только в модуле класса, видимость
функции выбирает модуль. Функция, в которой он есть, — операция приёма
([происхождение](memory/addresses.md#происхождение-и-разные-множества)): каждый её вызов — место доверия пакета
вызывающего ([кому доступно доверие](memory/system.md#кому-доступно-доверие)), а проверочная сборка записывает
значение в таблицу хендлеров и останавливается, если оно уже выдано.

```efen
@constructor
public fn adopt(raw: Descriptor) -> own Self { return Self(raw: raw) }

let inherited = File.adopt(raw: 3)               // место доверия этого пакета
let twice = File.adopt(raw: 3)                   // проверочная сборка: дескриптор 3 уже выдан
```

### Поля `layout` и модель

`layout { … }` в теле класса описывает, что держит внешняя сторона: поля, которых нет в байтах объекта
([`layout` в теле класса](memory/addresses.md#layout-в-теле-класса)). Пишет их модель — абстрактный код после
сигнатуры функции ([модель](conditions.md#модель-model)). По ним FLOW проверяет, что внешняя сторона не держит
слот дольше, чем он живёт.

```efen
@abi(c) class sqlite3_stmt {                     // сырое значение — sqlite3_stmt*
    layout {
        var db: mut sqlite3                      // запрос держит соединение
        var bound: [Int32: read CString]         // строки, которые sqlite хранит после SQLITE_STATIC
    }
    nocontext {
        @constructor fn sqlite3_prepare_v2(db: mut sqlite3, sql: read CString, length: Int32, self?,
                                           tail: out read<sql> CString? = null) -> Int32
        model { if let s = self { s.db = db } }

        mut fn sqlite3_bind_text(index: Int32, text: read CString, length: Int32,
                                 destructor: sqlite3_destructor_type) -> Int32
        model { if destructor == SQLITE_STATIC { self.bound[index] = text } else { self.bound.remove(index) } }

        mut fn sqlite3_step -> Int32
        @destructor own fn sqlite3_finalize -> Int32
    }
}

fn countUsers(db: mut sqlite3) -> Int throws SqliteError {
    var name = "Alice"
    var s: sqlite3_stmt? = null                  // пуст перед вызовом
    let rc = sqlite3_stmt.sqlite3_prepare_v2(db: db, sql: query.cString, length: -1, self: s)
    guard let st = s, rc == SQLITE_OK else { throw SqliteError() }
    st.sqlite3_bind_text(index: 1, text: name.cString, length: -1, destructor: SQLITE_STATIC)
    print(name)                                  // можно: удержание read
    // name.append("x")                          // ошибка: st.bound[1] держит name
    var total = 0
    while st.sqlite3_step() == SQLITE_ROW { total += 1 }
    (take st).sqlite3_finalize()                 // удержания кончились
    name.append("x")                             // можно
    return total
}
```

Поля `layout` бывают у класса без счётчика, у интерфейса и у контракта; у класса со счётчиком — ошибка. Класс с
обычными полями пишет в `layout` отношение между своими полями и полями `layout` элементов
([отношения в `layout`](conditions.md#отношения-в-layout-класса)):

```efen
class Connection {
    var db: own sqlite3
    var cache: Dictionary<String, own sqlite3_stmt>
    layout { forall s in cache.values: s.db == db }   // cache уничтожается раньше db; db не заменить, пока cache не пуст
}
```

Деструкторы класса над внешним значением описаны в [Disposable](disposable.md#внешние-деструкторы). Объект, который
внешняя сторона трогает из другого потока, объявляет `shared layout` ([общая память](shared.md#пометка-shared)).

## Ключевые особенности классов

- **Один владелец по умолчанию**: объект класса без `conforms RefCount` принадлежит одному владельцу; общий
  объект — класс со счётчиком
- **Одиночное наследование**: Класс может наследоваться только от одного базового класса
- **Множественная реализация интерфейсов**: Класс может реализовывать несколько интерфейсов
- **Соответствие контрактам**: Класс может соответствовать нескольким контрактам через `conforms`
- **Расширение через стратегии**: К классам могут применяться стратегии для добавления функциональности
- **Инкапсуляция**: Классы скрывают внутреннюю реализацию и предоставляют публичный API
