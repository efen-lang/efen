# Константы

`Efen` поддерживает объявление констант с помощью ключевого слова `const`.

Константы должны быть инициализированы при объявлении и не могут быть изменены впоследствии.

```efen
const pi = 3.14159
const appName = "MyApp"
const maxUsers: Int = 1000
```

## Основные характеристики констант

### Неизменяемость

Значение константы нельзя изменить после инициализации:

```efen
const version = "1.0.0"

// Ошибка компиляции!
version = "2.0.0"
```

### Инициализация при объявлении

Константы должны быть инициализированы сразу при объявлении:

```efen
// Правильно
const timeout = 5000

// Ошибка компиляции - константа не инициализирована
const maxRetries: Int
```

### Вывод типа

Тип константы может быть выведен автоматически или указан явно:

```efen
// Автоматический вывод типа
const port = 8080              // Int
const host = "localhost"       // String
const enabled = true           // Bool

// Явное указание типа
const maxConnections: Int = 100
const timeout: Float = 30.0
const mode: String = "production"
```

### Ширина числовых типов

`Int` и `UInt` имеют ширину указателя целевой платформы: 32 разряда на
32-разрядной цели и 64 разряда на 64-разрядной. Для данных с фиксированным
форматом используются `Int8`, `Int16`, `Int32`, `Int64` и соответствующие
беззнаковые типы. Размеры коллекций и разности адресов используют `UInt` и
`Int`, если API не требует конкретной фиксированной ширины.

`Float` является IEEE 754 binary64 на всех целях. `Float32` явно выбирает
binary32. Поэтому точность обычного вещественного литерала не зависит от
разрядности указателя.

## Область видимости констант

### Глобальные константы

Константы, объявленные на уровне модуля, доступны везде в модуле:

```efen
// В файле config.efen
const API_URL = "https://api.example.com"
const API_VERSION = "v1"
const MAX_RETRIES = 3

fn makeRequest {
    let url = API_URL + "/" + API_VERSION
    // Константы доступны
}
```

### Локальные константы

Константы могут быть объявлены внутри функций и блоков:

```efen
fn calculate {
    const PI = 3.14159
    const RADIUS = 10.0

    let area = PI * RADIUS * RADIUS
    return area
}

// Вне функции PI недоступна
```

### Константы в классах

Константы класса объявляются как статические члены:

```efen
class MathConstants {
    static const PI: Float = 3.14159265359
    static const E: Float = 2.71828182846
    static const GOLDEN_RATIO: Float = 1.61803398875
}

// Использование
let circumference = 2 * MathConstants.PI * radius
```

### Константы в контрактах и интерфейсах

Контракты и интерфейсы могут определять константы:

```efen
contract NetworkConfig {
    const DEFAULT_PORT: Int = 8080
    const TIMEOUT_MS: Int = 5000
}

interface HttpClient {
    const MAX_REDIRECTS: Int = 10
    const USER_AGENT: String = "EfenClient/1.0"

    fn get(url: String) -> Response
}
```

## Compile-time константы

Константы вычисляются во время компиляции, если их значение известно:

```efen
const SECONDS_PER_DAY = 60 * 60 * 24        // Вычислено в compile-time
const CONFIG_PATH = "/etc/" + "app.conf"    // Вычислено в compile-time
const IS_PRODUCTION = true && !false        // Вычислено в compile-time

// Компилятор встроит готовые значения в бинарник
```

### Compile-time выражения

В константах можно использовать compile-time выражения:

```efen
const BUFFER_SIZE = 1024 * 1024              // 1 МБ
const MAX_USERS = BUFFER_SIZE / 16           // Вычислено из другой константы
const VERSION_STRING = "v" + "1.0.0"         // Конкатенация строк

// Условные выражения
const LOG_LEVEL = if DEBUG_MODE { "debug" } else { "info" }
```

## Константные массивы и коллекции

Можно создавать неизменяемые коллекции:

```efen
const SUPPORTED_FORMATS = ["json", "xml", "yaml"]
const ERROR_CODES = [400, 401, 403, 404, 500]
const CONFIG_MAP = ["host": "localhost", "port": 8080]

// Элементы нельзя изменить
// ERROR_CODES[0] = 200  // Ошибка компиляции!
```

## Константы и ссылочные типы

При работе со ссылочными типами константа означает, что сама ссылка не может быть изменена, но объект может быть изменяемым:

```efen
class Config {
    var port: Int
    var host: String
}

const config = Config(port: 8080, host: "localhost")

// Можно изменить свойства объекта
config.port = 9000  // OK

// Но нельзя заменить саму ссылку
config = Config(port: 3000, host: "127.0.0.1")  // Ошибка!
```

Для полной неизменяемости используйте `let` с неизменяемыми свойствами:

```efen
class ImmutableConfig {
    let port: Int
    let host: String
}

const config = ImmutableConfig(port: 8080, host: "localhost")

// Нельзя изменить ни ссылку, ни свойства
config.port = 9000   // Ошибка!
config = ...         // Ошибка!
```

## Публичные и приватные константы

Константы могут иметь модификаторы доступа:

```efen
// Публичная константа - доступна из других модулей
public const API_VERSION = "v2"

// Приватная константа - только внутри модуля
private const INTERNAL_BUFFER_SIZE = 4096

// Защищённая константа - доступна в подклассах
protected const DEFAULT_TIMEOUT = 30000
```

## Именование констант

Рекомендации по именованию:

```efen
// Глобальные константы - UPPER_CASE
const MAX_CONNECTIONS = 100
const API_BASE_URL = "https://api.example.com"
const DEFAULT_TIMEOUT = 5000

// Математические константы - PascalCase или lowercase
const Pi = 3.14159
const pi = 3.14159
const GoldenRatio = 1.618

// Конфигурационные значения - UPPER_CASE
const DATABASE_HOST = "localhost"
const DATABASE_PORT = 5432
```

## Константы в модулях

Организация констант в отдельных модулях:

```efen
// constants/network.efen
module network {
    public const DEFAULT_PORT = 8080
    public const TIMEOUT_MS = 5000
    public const MAX_RETRIES = 3
}

// constants/limits.efen
module limits {
    public const MAX_FILE_SIZE = 10 * 1024 * 1024  // 10 МБ
    public const MAX_USERS = 1000
    public const MAX_CONCURRENT_REQUESTS = 100
}

// Использование
use network
use limits

fn startServer {
    listen(network::DEFAULT_PORT)
    setMaxUsers(limits::MAX_USERS)
}
```

## Перечисления как группы констант

Для связанных констант используйте перечисления:

```efen
enum HttpStatus {
    OK = 200,
    NOT_FOUND = 404,
    SERVER_ERROR = 500
}

enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3
}

// Использование
if status == HttpStatus::OK {
    // ...
}
```

## Константы vs let

Различия между `const` и `let`:

| Характеристика | const | let |
|----------------|-------|-----|
| Время вычисления | Compile-time (если возможно) | Runtime |
| Область видимости | Глобальная или локальная | Локальная |
| Использование | Значения, известные заранее | Вычисляемые значения |
| Оптимизация | Встраивается в код | Хранится в памяти |

```efen
// const - значение известно заранее
const MAX_SIZE = 1024

// let - значение вычисляется в runtime
let currentSize = calculateSize()

// let для неизменяемых локальных переменных
fn process {
    let input = readInput()  // Вычислено в runtime
    let result = input * 2   // Неизменяемая переменная
}
```

## Лучшие практики

1. **Используйте UPPER_CASE для глобальных констант**
   ```efen
   const MAX_RETRIES = 3
   const API_ENDPOINT = "https://api.example.com"
   ```

2. **Группируйте связанные константы**
   ```efen
   module DatabaseConfig {
       const HOST = "localhost"
       const PORT = 5432
       const MAX_CONNECTIONS = 10
   }
   ```

3. **Предпочитайте константы magic numbers**
   ```efen
   // Плохо
   if status == 200 { }

   // Хорошо
   const HTTP_OK = 200
   if status == HTTP_OK { }
   ```

4. **Используйте константы для конфигурации**
   ```efen
   const DEBUG_MODE = true
   const LOG_TO_FILE = false
   const CACHE_ENABLED = true
   ```

5. **Документируйте неочевидные константы**
   ```efen
   // Максимальное количество попыток переподключения
   // перед выбросом исключения
   const MAX_RECONNECT_ATTEMPTS = 5

   // Таймаут в миллисекундах для HTTP-запросов
   const HTTP_TIMEOUT_MS = 30000
   ```

## Ограничения

1. Константы должны быть инициализированы при объявлении
2. Значение константы нельзя изменить после инициализации
3. Константы не могут быть reassigned
4. Для compile-time констант значение должно быть вычислимо во время компиляции
