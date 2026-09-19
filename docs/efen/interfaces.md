# Интерфейсы

[Документация](index.md) · [Словарь](glossary.md) · [Контракты](contracts.md)

`Efen` разделяет две группы абстракций: абстракции времени компиляции и абстракции времени выполнения.
Интерфейсы и классы относятся к абстракциям времени выполнения.

> **Интерфейс** -- это бинарная структура данных, которая позволяет обращаться к методам
> и свойствам объекта без знания его конкретного типа.

## ⚠️ Interface vs Contract: Фундаментальное различие

**Интерфейс — это НЕ контракт!** Это ключевая концепция Efen:

### Interface — runtime полиморфизм (VTBL)
- ✅ Существует в **скомпилированном бинарнике** как виртуальная таблица
- ✅ Обеспечивает **runtime полиморфизм** — тип может быть неизвестен во время компиляции
- ✅ Использует **dynamic dispatch** (косвенный вызов через VTBL)
- ✅ Имеет **runtime overhead** — каждый вызов через указатель
- ✅ Позволяет **binary compatibility** — можно менять реализацию без перекомпиляции

### Contract — compile-time проверка
- ✅ Существует **только** во время компиляции
- ✅ **Полностью исчезает** из бинарника после компиляции
- ✅ Использует **static dispatch** (прямой вызов)
- ✅ Сам contract не требует runtime-дескриптора или VTBL
- ✅ Для generic constraints и compile-time проверок

Interface не возникает из contract автоматически. Явная декларация
`interface Name from Contract` создаёт runtime-interface и сохраняет
compile-time связь с исходным contract. В interface переносятся только runtime-
вызываемые методы; associated types, representation и прочие статические
требования остаются проверками времени компиляции.

Стратегия также не является interface и не преобразуется в произвольный
interface по совпадению методов. Явная декларация создаёт отдельную runtime-
проекцию по образцу конкретной стратегии:

```efen
interface Drawing from CircleDrawing

let shape: Drawing = CircleDrawing
```

Без `interface Drawing from CircleDrawing` последнее присваивание запрещено.
Другая стратегия допускается как реализация `Drawing` только при явном
`conforms` общему contract исходной стратегии и после проверки всей runtime-
поверхности interface. Подробнее см. [«Стратегии»](strategies.md#динамическая-стратегия).

### Практический пример

```efen
// INTERFACE: присутствует в runtime как VTBL
interface Logger {
    fn log(message: String)
    fn level -> Int
}

class FileLogger {
    implements Logger  // Создается VTBL в бинарнике

    fn log(message: String) {
        writeToFile("/var/log/app.log", message)
    }

    fn level -> Int {
        return 3
    }
}

class ConsoleLogger {
    implements Logger  // Другая VTBL

    fn log(message: String) {
        print(message)
    }

    fn level -> Int {
        return 5
    }
}

// Runtime полиморфизм - тип определяется во время выполнения!
fn processLogs(logger: Logger, messages: [String]) {
    for msg in messages {
        logger.log(msg)  // DYNAMIC DISPATCH через VTBL
    }
}

// Работает с любым Logger
let fileLogger = FileLogger()
let consoleLogger = ConsoleLogger()

processLogs(logger: fileLogger, messages: ["Error 1", "Error 2"])
processLogs(logger: consoleLogger, messages: ["Debug info"])
```

**Что в бинарнике:**
- **VTBL для Logger** с указателями на методы `log()` и `level()`
- **FileLogger VTBL** — указатели на реализацию FileLogger
- **ConsoleLogger VTBL** — указатели на реализацию ConsoleLogger
- `processLogs` вызывает методы через VTBL (indirect call)

### Сравнение: Interface vs Contract

| Характеристика | Interface (VTBL) | Contract |
|---------------|------------------|----------|
| Время жизни | Runtime | Compile-time only |
| В бинарнике | ✅ Присутствует | ❌ Исчезает |
| Dispatch | Dynamic (VTBL) | Static (direct) |
| Overhead | Есть (indirect call) | Нет |
| Полиморфизм | Runtime | Compile-time (generics) |
| Тип известен | Может быть неизвестен | Должен быть известен |
| Binary compatibility | ✅ Да | ❌ Нет |
| Plugin system | ✅ Подходит | ❌ Не подходит |
| Performance critical | ⚠️ Overhead | ✅ Оптимально |

### Когда использовать Interface?

**✅ Используйте Interface когда:**

1. **Runtime полиморфизм**
   ```efen
   // Тип определяется во время выполнения
   fn createLogger(type: String) -> Logger {
       return match type {
           "file": FileLogger()
           "console": ConsoleLogger()
           _: NullLogger()
       }
   }
   ```

2. **Plugin architecture**
   ```efen
   // Плагины загружаются динамически
   interface Plugin {
       fn name -> String
       fn execute
   }

   let plugins = loadPlugins("/plugins/*.dll")
   for plugin in plugins {
       plugin.execute()  // Runtime dispatch
   }
   ```

3. **Dependency injection**
   ```efen
   class App {
       var logger: Logger  // Может быть любая реализация
       var database: Database

       @constructor
       fn init(logger: Logger, db: Database) -> Self {
           self.logger = logger
           self.database = db
       }
   }
   ```

4. **Binary compatibility**
   ```efen
   // Библиотека может обновиться без перекомпиляции клиента
   interface ApiClient {
       fn fetch(url: String) -> Response
   }
   ```

**❌ НЕ используйте Interface когда:**

1. Критична производительность (используйте Contract)
2. Тип известен во время компиляции (используйте generics с Contract)
3. Нужна оптимизация компилятора (inline, etc)

См. также: [contracts.md](contracts.md) для подробного сравнения.

Пример интерфейса:
```efen
interface MyInterface {
    var myProperty: Int { get set }
    fn myMethod
}
```

Пример использования интерфейса:
```efen
fn useInterface(interface: MyInterface) {
    interface.myProperty = 42
    interface.myMethod()
}
```

Интерфейсы позволяют реализовать обобщённое программирование прямо в runtime без участия компилятора.
Компилятор гарантирует, что объекты разных классов, реализующие один и тот же интерфейс,
могут быть использованы взаимозаменяемо без необходимости **перекомпиляции кода**.

Интерфейсы имеют множественное наследование, но не могут иметь состояния. Свойства класса могут быть частью интерфейса.
