# Стратегии

[Документация](index.md) · [Словарь](glossary.md) · [Контракты](contracts.md) · [Member resolver](aspects/members-resolving.md)

> **Стратегия** — отдельная реализация поведения для типа. Она может участвовать
> в compile-time разрешении и не становится физическим членом целевого типа.

Стратегия может иметь целью любой тип: класс, структуру, enum, variant, новый номинальный
тип, interface и другую абстракцию. Внешнее применение требует согласия
целевого типа по правилу `allow strategies`, описанному ниже.

Метод стратегии участвует в разрешении вызова, но не добавляется в физический
список методов целевого `lang::Class`. Поэтому стратегия может предоставлять
публичное поведение без права аспекта непосредственно создать публичный член
класса. Правила физического изменения класса описаны в
[построении класса аспектами](aspects/compile-time/class.md).

## Определение стратегии

Стратегия описывает дополнительное поведение для существующих типов без изменения их определения:

```efen
interface Drawable {
    fn draw
}

// Стратегия для сериализации объектов Drawable
strategy Serialization for Drawable {
    fn serialize -> String {
        return "Serialized drawable object"
    }

    fn deserialize(data: String) -> Drawable {
        // Логика десериализации
    }
}
```

Имя стратегии необязательно. Стратегия может явно соответствовать compile-time
contract:

```efen
contract Coerce<Source> {
    static fn coerce(value: Source) -> Self
}

strategy for UserId {
    conforms Coerce<Int>
    static fn coerce(value: Int) -> UserId {
        return value.refine()
    }
}
```

Безымянная стратегия обязана иметь цель `for Type`. Именованная generic-
стратегия может получить конкретную цель через `provide`:

```efen
strategy MyAllocator<T> {
    conforms Allocator<T>
    // реализация контракта
}

provide MyAllocator for MyObject
```

Цель generic-стратегии может содержать её параметры. Такая стратегия
специализируется при разрешении, когда исходный и ожидаемый типы однозначно
связывают параметры; отдельный `provide` для каждой инстанциации не требуется.

`provide Strategy for Type` является явной инструкцией применить названную
стратегию к целевому типу при компиляции текущего пакета.

## Право применить стратегию

Пакет-владелец типа может применять к нему свои стратегии без дополнительного
разрешения. Чтобы внешний пакет мог применить стратегию к типу, тип явно
разрешает это специальной строкой `allow strategies`:

```efen
public class Document {
    allow strategies
}
```

Разрешение относится к точному типу. Оно не наследуется: `Child` может отдельно
написать `allow strategies` для себя, даже если `Parent` этого не разрешил.
Отсутствие строки означает запрет внешнего применения; отдельный `forbid` не
нужен, пока нет более широкого разрешения уровня модуля или пакета.

Разрешение не делает стратегию видимой, активной или экспортируемой и не выдаёт
права изменять HIR чужого типа. Для generic-цели владельцем считается пакет её
номинальной головы: например, владельцем `Array<User>` остаётся пакет `Array`, а
не пакет `User`.

При обычном разрешении одинаково применимых неявных кандидатов стратегия из
пакета целевого типа имеет приоритет над внешней. Явный `provide` выбирает
указанную именованную стратегию, а не запускает сравнение приоритетов. Несколько
одинаково приоритетных кандидатов остаются ошибкой; порядок объявлений ничего не
решает.

Объявление внешней библиотеки неизменяемо. `provide` выбирает стратегию, но не
выдаёт изменяемый builder чужого объявления. Если библиотека допускает внешнее
расширение, установленный ею аспект публикует функцию, которая сама выполняет
изменение либо принимает замыкание с ограниченным объектом изменения.
Потребитель вызывает этот API, а опубликованный исходный продукт зависимости не
переписывается.

## Применение стратегий

Стратегии применяются к объектам прозрачно, как если бы методы были частью интерфейса:

```efen
class Circle {
    implements Drawable

    var radius: Float

    fn draw {
        print("Drawing circle with radius ${radius}")
    }
}

let circle = Circle(radius: 5.0)
circle.draw()  // Метод из класса
let serialized = circle.serialize()  // Метод из стратегии Serialization
```

## Стратегии для классов

Стратегии могут применяться и к конкретным классам:

```efen
class User {
    var name: String
    var email: String
}

strategy Authentication for User {
    fn login(password: String) -> Bool {
        // Логика аутентификации
        return true
    }

    fn logout {
        // Логика выхода
    }
}

let user = User(name: "Alice", email: "alice@example.com")
user.login(password: "secret")  // Метод из стратегии
```

## Множественные стратегии

К одному типу может быть применено несколько стратегий:

```efen
strategy Validation for User {
    fn validate -> Bool {
        return !name.isEmpty && email.contains("@")
    }
}

strategy Logging for User {
    fn logActivity(action: String) {
        print("User ${name}: ${action}")
    }
}

let user = User(name: "Bob", email: "bob@example.com")
user.validate()  // Из стратегии Validation
user.logActivity(action: "logged in")  // Из стратегии Logging
user.login(password: "pass123")  // Из стратегии Authentication
```

**Преимущества стратегий:**
- Разделение ответственности (separation of concerns)
- Расширение функциональности без изменения исходного кода
- Возможность подключения/отключения поведения на этапе компиляции
- Композиция поведения из независимых модулей

## Конкурирующие стратегии и выбор стратегии

Компилятор позволяет создавать несколько стратегий с одинаковыми методами для одного типа.
Такие стратегии называются **конкурирующими**.

```efen
class DataStorage {
    var data: [String]
}

// Стратегия сохранения в JSON
strategy JSONPersistence for DataStorage {
    fn save {
        print("Saving data as JSON")
        // Логика сохранения в JSON
    }

    fn load {
        print("Loading data from JSON")
        // Логика загрузки из JSON
    }
}

// Стратегия сохранения в XML
strategy XMLPersistence for DataStorage {
    fn save {
        print("Saving data as XML")
        // Логика сохранения в XML
    }

    fn load {
        print("Loading data from XML")
        // Логика загрузки из XML
    }
}

let storage = DataStorage(data: ["item1"])
storage.save() // Ошибка: JSONPersistence и XMLPersistence одинаково подходят
```

### Правила выбора стратегии

Стратегия является обычным символом модуля. Для неё действуют те же правила
видимости, экспорта и `use`, что и для других символов. Принадлежность пакету
целевого типа не делает стратегию глобально видимой.

Текущим называется каждый пакет, код которого сейчас компилируется, а не только
пакет исполняемой программы. Видимая стратегия, объявленная в текущем пакете,
может участвовать в обычном статическом разрешении. Стратегия, импортированная
из пакета-зависимости, от одного `use` активной не становится: текущий пакет
выбирает её явно через `provide Strategy for Type`.

`provide` действует только на код текущего пакета. Директива не экспортируется и
не передаётся транзитивно пакетам, которые используют текущий пакет. Уже
скомпилированная функция сохраняет выбранное для своего тела поведение, но её
потребитель не получает ту же стратегию для разрешения собственных операций.

```efen
// package JsonAdapter
use Documents
use JsonStrategies

provide JsonDocument for Documents::Document
```

Если `Application` затем делает `use JsonAdapter`, это не предоставляет
`JsonDocument` коду `Application`. Для собственных операций над `Document`
пакет `Application` должен сделать свой явный `provide`.

Во встроенном режиме две действительно пересекающиеся активные стратегии одного
приоритета дают конфликт при формировании области, не дожидаясь конкретного
вызова. Порядок объявлений не используется как правило выбора. Применимое
правило `Resolve<Contract>`, описанное ниже, получает набор кандидатов до этой
диагностики и заменяет встроенное правило. Отсутствие стратегии является ошибкой
только в точке, где соответствующее поведение действительно требуется.

Стратегия для класса применима и к его потомкам: потомок обязан сохранять
контракт поведения базового класса. Выбор остаётся статическим. Для выражения со
статическим типом `Parent` выбираются стратегии `Parent`; runtime-класс значения
не переключает выбранную стратегию. При точно выведенном `Child` собственная
стратегия `Child` может заменить унаследованную стратегию `Parent`.

Тело унаследованной стратегии проверяется через логическую поверхность её цели
и обычные лексические права места объявления. Применимость к `Child` не открывает
его private storage и не даёт стратегии право полагаться на физический layout
потомка. Виртуальный вызов метода `Parent` внутри стратегии сохраняет обычную
динамическую диспетчеризацию и может вызвать override `Child`.

Единица выбора — соответствие контракту целиком: компилятор запрашивает
стратегию один раз для типа в данной области и берёт из неё все методы
контракта. Выбора отдельно для каждого метода нет, поэтому `equals` и `hash`
одного `Hashable` всегда приходят из одной стратегии.

Алгоритм выбора расширяется тем же механизмом стратегий. `Resolve<Contract>` —
встроенная compile-time абстракция Efen; контракт в её имени называет род
выбираемых стратегий, а `where` задаёт, для каких целей правило применимо:

```efen
strategy for Resolve<Allocator<let T>>
where target is Box<T> {
    // какой Allocator взять для Box<T>
}
```

Когда условие подходит, компилятор вызывает эту стратегию вместо встроенного
алгоритма. Сам `Resolve` разрешается bootstrap-правилом компилятора, чтобы его
поиск не рекурсировал через себя. Если пользовательское правило не применимо,
действует встроенное; оно не сравнивает generic-кандидатов по необъявленной
«большей специализации».

Автоматическое приведение ищет одну прямую стратегию `Coerce<Source>` для
ожидаемого целевого типа. Цепочки `A -> B -> C` автоматически не строятся;
несколько шагов программист вызывает явно.

Ожидаемый тип приходит от связывания, параметра вызова, результата функции или
окружающего выражения. Стандартная generic-стратегия использует этот механизм
для проверяемого разворачивания optional:

```efen
strategy OptionalOrThrow<T> for T {
    conforms Coerce<T?>
    static fn coerce(value: T?) -> T throws MissingOptionalError {
        if let result = value {
            return result
        }

        throw MissingOptionalError()
    }
}
```

Если источник имеет тип `T?`, а контекст требует `T`, компилятор может вставить
`OptionalOrThrow<T>.coerce`. Точное совпадение с ожидаемым `T?` всегда имеет
приоритет. При отсутствии ожидаемого типа значение сохраняет `T?`. Исключение
вставленной стратегии участвует в выводе `throws` вызывающей функции.

### Совместимость стратегий

Стратегии **совместимы**, если они не определяют методы с одинаковыми сигнатурами.
Совместимые стратегии могут быть подключены одновременно:

```efen
strategy Logging for DataStorage {
    fn log(message: String) {
        print("[LOG] ${message}")
    }
}

strategy Validation for DataStorage {
    fn validate -> Bool {
        return !data.isEmpty
    }
}

use Logging
use Validation

let storage = DataStorage(data: ["item1"])
storage.validate()  // Из Validation
storage.log(message: "Starting save")  // Из Logging
```

## Динамическая стратегия

Стратегия текущего пакета участвует в статическом разрешении по правилам выше;
для стратегии зависимости одного `use` недостаточно. Иногда программисту нужно
выбирать одну из реализаций во время выполнения. Сама стратегия не является
interface и не присваивается переменной произвольного interface-типа. Runtime-
граница создаётся только явной декларацией `interface ... from Strategy`.

### Создание динамической стратегии

Динамическая стратегия создается присваиванием стратегии переменной типа интерфейс:

```efen
contract DrawingContract {
    fn draw
    fn resize(scale: Float)
}

strategy CircleDrawing for Shape {
    conforms DrawingContract
    fn draw {
        print("Drawing circle")
    }

    fn resize(scale: Float) {
        print("Resizing circle by ${scale}")
    }
}

strategy SquareDrawing for Shape {
    conforms DrawingContract
    fn draw {
        print("Drawing square")
    }

    fn resize(scale: Float) {
        print("Resizing square by ${scale}")
    }
}

interface Drawing from CircleDrawing

let shape: Drawing = CircleDrawing
```

`Drawing` создаётся по образцу конкретной реализации `CircleDrawing`. Только эта
явная проекция разрешает материализовать стратегию как runtime-значение.
Совпадения имён методов недостаточно. Другая стратегия может использовать тот
же interface лишь при явном `conforms` общему contract и после проверки всей
runtime-поверхности `Drawing`. Поэтому `SquareDrawing` выше совместима, а
случайная стратегия с методами `draw` и `resize` — нет.

### Применение динамической стратегии к объекту

Чтобы применить динамическую стратегию к объекту, используется ключевое слово `using`:

#### Одна строка

```efen
let circle = Circle(radius: 5.0)

// Применяем стратегию к объекту для одного вызова
using shape circle.draw()  // Выведет: "Drawing circle"

// Можно присвоить результат
let result = using shape circle.resize(scale: 2.0)
```

#### Блок

Для нескольких вызовов удобнее использовать блочный синтаксис:

```efen
using shape {
    circle.draw()
    circle.resize(scale: 2.0)
    circle.move(x: 10, y: 20)  // Если метод есть в стратегии
}
```

### Динамический выбор стратегии

Главное преимущество динамических стратегий -- возможность выбирать поведение во время выполнения:

```efen
fn renderShape(shape: Shape, format: String) -> Drawing {
    if format == "circle" {
        return CircleDrawing
    }

    return SquareDrawing
}

let userFormat = getUserInput()  // Получаем формат от пользователя
let strategy = renderShape(shape: circle, format: userFormat)

// Применяем динамически выбранную стратегию
using strategy {
    circle.draw()
    circle.export()
}
```

### Пример: Система логирования

```efen
contract LoggerContract {
    fn log(message: String)
}

strategy ConsoleLogger for Request {
    conforms LoggerContract
    fn log(message: String) {
        print("[CONSOLE] ${message}")
    }
}

strategy FileLogger for Request {
    conforms LoggerContract
    fn log(message: String) {
        // Запись в файл
        writeToFile(message)
    }
}

strategy NetworkLogger for Request {
    conforms LoggerContract
    fn log(message: String) {
        // Отправка по сети
        sendToServer(message)
    }
}

// Выбор стратегии на основе конфигурации
interface Logger from ConsoleLogger

fn createLogger(config: Config) -> Logger {
    match config.logType {
        "console": return ConsoleLogger
        "file": return FileLogger
        "network": return NetworkLogger
        _: return ConsoleLogger
    }
}

let logger = createLogger(config: appConfig)

// Использование динамической стратегии
class Application {
    var logger: Logger

    fn processRequest(request: Request) {
        using logger request.log(message: "Processing request")
        // ... обработка запроса
        using logger request.log(message: "Request completed")
    }
}
```

### Граница runtime-проекции

Без `interface Name from Strategy` стратегия остаётся только compile-time
декларацией: её нельзя присвоить переменной, вернуть из runtime-функции или
положить в коллекцию. Отдельный модификатор `static strategy` для этого не
нужен. Проекция создаёт обычный runtime-interface и только тем самым разрешает
runtime-выбор совместимых явно подтверждённых реализаций.
