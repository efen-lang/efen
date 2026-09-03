# Стратегии

> **Стратегия** -- абстракция времени выполнения, которая определяет алгоритмы работы с данными,
> классами или интерфейсами, при этом не являясь частью этих абстракций.

Компилятор позволяет применять стратегии для классов и интерфейсов так, как если бы стратегии были частью этих абстракций.

## Определение стратегии

Стратегия описывает дополнительное поведение для существующих типов без изменения их определения:

```efen
interface Drawable {
    fn draw()
}

// Стратегия для сериализации объектов Drawable
strategy Serialization for Drawable {
    fn serialize() -> String {
        return "Serialized drawable object"
    }

    fn deserialize(data: String) -> Drawable {
        // Логика десериализации
    }
}
```

## Применение стратегий

Стратегии применяются к объектам прозрачно, как если бы методы были частью интерфейса:

```efen
class Circle : Drawable {
    var radius: Float

    fn draw() {
        print("Drawing circle with radius \(radius)")
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

    fn logout() {
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
    fn validate() -> Bool {
        return !name.isEmpty && email.contains("@")
    }
}

strategy Logging for User {
    fn logActivity(action: String) {
        print("User \(name): \(action)")
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
    fn save() {
        print("Saving data as JSON")
        // Логика сохранения в JSON
    }

    fn load() {
        print("Loading data from JSON")
        // Логика загрузки из JSON
    }
}

// Стратегия сохранения в XML
strategy XMLPersistence for DataStorage {
    fn save() {
        print("Saving data as XML")
        // Логика сохранения в XML
    }

    fn load() {
        print("Loading data from XML")
        // Логика загрузки из XML
    }
}
```

### Правила выбора стратегии

Компилятор использует следующие правила для разрешения конфликтов между конкурирующими стратегиями:

1. **Явное подключение в модуль**: Если стратегия была явно подключена в модуль с помощью директивы `use`,
   она имеет приоритет над другими стратегиями.

```efen
// Модуль ConfigModule
use JSONPersistence  // Явное подключение стратегии

let storage = DataStorage(data: ["item1", "item2"])
storage.save()  // Использует JSONPersistence.save()
```

2. **Запрет конфликтующих стратегий**: Две стратегии с одинаковыми методами не могут быть одновременно
   подключены в один модуль. Компилятор выдаст ошибку:

```efen
// Ошибка компиляции!
use JSONPersistence
use XMLPersistence  // Конфликт: обе стратегии определяют save() и load()

let storage = DataStorage(data: ["item1"])
storage.save()  // Неоднозначность: какую стратегию использовать?
```

3. **Явное указание стратегии**: Программист может явно указать, какую стратегию использовать:

```efen
use JSONPersistence
use XMLPersistence

let storage = DataStorage(data: ["item1"])

// Явное указание стратегии через синтаксис with
storage.save() with JSONPersistence  // Использует JSON
storage.save() with XMLPersistence   // Использует XML
```

4. **Область видимости стратегий**: Стратегии действуют в пределах модуля, где они подключены:

```efen
// Модуль A
use JSONPersistence

fn processInModuleA() {
    let storage = DataStorage(data: ["data"])
    storage.save()  // Использует JSONPersistence
}

// Модуль B
use XMLPersistence

fn processInModuleB() {
    let storage = DataStorage(data: ["data"])
    storage.save()  // Использует XMLPersistence
}
```

### Совместимость стратегий

Стратегии **совместимы**, если они не определяют методы с одинаковыми сигнатурами.
Совместимые стратегии могут быть подключены одновременно:

```efen
strategy Logging for DataStorage {
    fn log(message: String) {
        print("[LOG] \(message)")
    }
}

strategy Validation for DataStorage {
    fn validate() -> Bool {
        return !data.isEmpty
    }
}

// Эти стратегии совместимы и могут использоваться вместе
use JSONPersistence
use Logging
use Validation

let storage = DataStorage(data: ["item1"])
storage.validate()  // Из Validation
storage.log(message: "Starting save")  // Из Logging
storage.save()  // Из JSONPersistence
```

## Динамическая стратегия

Обычно стратегии применяются статически на этапе компиляции через директиву `use`.
Но иногда программисту нужно динамически выбирать стратегию во время выполнения.
Для этого используется **динамическая стратегия**.

> **Динамическая стратегия** -- это переменная типа интерфейс, которой присвоена конкретная стратегия.
> По сути это vtable (таблица виртуальных методов) без привязки к конкретному объекту.

### Создание динамической стратегии

Динамическая стратегия создается присваиванием стратегии переменной типа интерфейс:

```efen
interface Drawable {
    fn draw()
    fn resize(scale: Float)
}

strategy CircleDrawing for Drawable {
    fn draw() {
        print("Drawing circle")
    }

    fn resize(scale: Float) {
        print("Resizing circle by \(scale)")
    }
}

strategy SquareDrawing for Drawable {
    fn draw() {
        print("Drawing square")
    }

    fn resize(scale: Float) {
        print("Resizing square by \(scale)")
    }
}

// Создание динамической стратегии
let drawable: Drawable = CircleDrawing  // Присваиваем стратегию переменной
```

В памяти `drawable` -- это vtable со ссылками на методы стратегии `CircleDrawing`, но без привязки к объекту.

### Применение динамической стратегии к объекту

Чтобы применить динамическую стратегию к объекту, используется ключевое слово `using`:

#### Одна строка

```efen
let circle = Circle(radius: 5.0)

// Применяем стратегию к объекту для одного вызова
using drawable circle.draw()  // Выведет: "Drawing circle"

// Можно присвоить результат
let result = using drawable circle.resize(scale: 2.0)
```

#### Блок

Для нескольких вызовов удобнее использовать блочный синтаксис:

```efen
using drawable {
    circle.draw()
    circle.resize(scale: 2.0)
    circle.move(x: 10, y: 20)  // Если метод есть в стратегии
}
```

### Динамический выбор стратегии

Главное преимущество динамических стратегий -- возможность выбирать поведение во время выполнения:

```efen
fn renderShape(shape: Shape, format: String) -> Drawable {
    if format == "svg" {
        return SVGDrawing  // Возвращаем одну стратегию
    } else if format == "canvas" {
        return CanvasDrawing  // Возвращаем другую стратегию
    } else {
        return DefaultDrawing  // Возвращаем дефолтную
    }
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
interface Logger {
    fn log(message: String)
}

strategy ConsoleLogger for Logger {
    fn log(message: String) {
        print("[CONSOLE] \(message)")
    }
}

strategy FileLogger for Logger {
    fn log(message: String) {
        // Запись в файл
        writeToFile(message)
    }
}

strategy NetworkLogger for Logger {
    fn log(message: String) {
        // Отправка по сети
        sendToServer(message)
    }
}

// Выбор стратегии на основе конфигурации
fn createLogger(config: Config) -> Logger {
    switch config.logType {
        case "console": return ConsoleLogger
        case "file": return FileLogger
        case "network": return NetworkLogger
        default: return ConsoleLogger
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

### Статические стратегии

Стратегию можно объявить как `static`, тогда её **нельзя** будет использовать динамически:

```efen
static strategy DefaultDrawing for Drawable {
    fn draw() {
        print("Default drawing")
    }
}

// Ошибка компиляции!
let drawable: Drawable = DefaultDrawing  // Нельзя! Стратегия статическая

// Можно использовать только через use
use DefaultDrawing
circle.draw()  // Использует DefaultDrawing статически
```

**Когда использовать `static`:**
- Когда стратегия никогда не должна выбираться динамически
- Для оптимизации производительности (статическая диспетчеризация)
- Чтобы явно запретить присваивание переменной

### Отличия статических и динамических стратегий

| **Статическая стратегия**                  | **Динамическая стратегия**                |
|--------------------------------------------|-------------------------------------------|
| Объявляется с `static strategy`            | Объявляется с `strategy`                  |
| Выбирается на этапе компиляции через `use` | Выбирается во время выполнения            |
| Нельзя присвоить переменной                | Можно присвоить переменной типа интерфейс |
| Статическая диспетчеризация                | Виртуальная диспетчеризация (vtable)      |
| Быстрее (inline-оптимизации)               | Медленнее (косвенный вызов)               |
| Используется для архитектурных решений     | Используется для runtime-поведения        |

### Когда использовать динамические стратегии

**Используйте динамические стратегии, когда:**
- Выбор стратегии зависит от пользовательского ввода
- Стратегия определяется конфигурацией или настройками
- Нужно передавать стратегию как параметр функции
- Требуется plugin-архитектура с загрузкой стратегий во время выполнения

**Используйте статические стратегии, когда:**
- Стратегия известна на этапе компиляции
- Важна производительность
- Стратегия является частью архитектуры и не должна меняться
- Нужна compile-time проверка использования стратегии

