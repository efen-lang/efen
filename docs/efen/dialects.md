# Диалекты

`Efen` является мультидиалектным языком программирования, что позволяет использовать различные синтаксисы
и семантики в рамках одного проекта для решения специфических задач.

Границы встроенного блока вида `sql { ... }`/`query { ... }` относятся к
открытому вопросу B1. Также ещё не решено, как `$имя` внутри такого блока
отличается от placeholder-параметра окружающего Efen-замыкания. Примеры ниже
показывают требуемую интеграцию, но не закрывают эти две лексические развилки.

## Типы диалектов

Различаются диалекты трёх видов:
- **Полноценные диалекты** (Full Dialects)
- **Inline диалекты** (Inline Dialects)
- **Extension диалекты** (Extension Dialects)

## Полноценные диалекты (Full Dialects)

Полноценные диалекты представляют собой отдельные языки программирования с собственным синтаксисом,
семантикой и правилами компиляции, которые не противоречат основному языку `Efen`,
могут работать совместно с его типами и абстракциями.
Полноценные диалекты поставляются в виде плагинов компилятора.

### Характеристики

- Собственный парсер и AST
- Интеграция с системой типов Efen
- Возможность использования типов и функций Efen
- Полная изоляция синтаксиса от основного языка
- Compile-time и runtime проверки

### Пример полноценного диалекта

```efen
// Файл с расширением .efql (Efen + SQL dialect)
dialect efql

use efen::database::Connection

fn getUserByEmail(conn: Connection, email: String) -> User? {
    // SQL диалект с полной интеграцией типов
    let result = query {
        SELECT id, name, email
        FROM users
        WHERE email = $email
        LIMIT 1
    }

    return result.first()
}
```

### Регистрация полноценного диалекта

```efen
// Плагин компилятора для нового диалекта
@dialectPlugin
class MyDialect {
    implements DialectCompiler

    fn name -> String {
        return "mydialect"
    }

    fn fileExtensions -> [String] {
        return [".emd", ".mydialect"]
    }

    fn parse(source: String) -> AST {
        // Парсинг исходного кода диалекта
    }

    fn typeCheck(ast: AST, context: TypeContext) -> TypedAST {
        // Проверка типов
    }

    fn compile(ast: TypedAST) -> IR {
        // Компиляция в промежуточное представление
    }
}
```

## Inline диалекты (Inline Dialects)

Inline диалекты — это встроенный синтаксис, который ограничен областью выражений и может быть использован
внутри кода `Efen`. Примером такого диалекта является строка "with ${name}" с возможностью интерполяции.

### Встроенные inline диалекты

`Efen` поддерживает inline-диалекты с помощью специального синтаксиса:

```efen
// TOML inline
let config = toml {
    [server]
    host = "localhost"
    port = 8080

    [database]
    url = "postgresql://localhost/mydb"
    max_connections = 10
}

// JSON inline
let data = json {
    "name": "John",
    "age": 30,
    "active": true,
    "tags": ["developer", "efen"]
}

// SQL inline
let users = sql {
    SELECT id, name, email
    FROM users
    WHERE active = true
    ORDER BY created_at DESC
    LIMIT 10
}

// YAML inline
let manifest = yaml {
    version: "1.0"
    services:
      - name: web
        port: 8080
      - name: api
        port: 3000
}

// XML inline
let document = xml {
    <root>
        <user id="1">
            <name>Alice</name>
            <email>alice@example.com</email>
        </user>
    </root>
}
```

### Интерполяция переменных

Inline диалекты поддерживают интерполяцию переменных Efen:

```efen
let tableName = "users"
let minAge = 18

let query = sql {
    SELECT * FROM ${tableName}
    WHERE age >= ${minAge}
}

let userId = 42
let config = json {
    "userId": ${userId},
    "timestamp": ${getCurrentTime()},
    "active": ${isUserActive(userId)}
}
```

### Типизация inline диалектов

Компилятор может выводить типы для inline диалектов:

```efen
// Тип выводится автоматически
let config: TomlConfig = toml {
    host = "localhost"
    port = 8080
}

// Явное указание типа
let data: JsonObject = json {
    "name": "test"
}

// SQL запрос с типизированным результатом
let users: ResultSet<User> = sql {
    SELECT * FROM users
}
```

### Compile-time валидация

Inline диалекты могут валидироваться во время компиляции:

```efen
// Ошибка компиляции - невалидный JSON
let invalid = json {
    "key": value,  // Пропущены кавычки
}

// Ошибка компиляции - невалидный SQL
let badQuery = sql {
    SELECT * FORM users  // Опечатка в FROM
}
```

## Extension диалекты (Extension Dialects)

Extension диалекты позволяют расширять существующий синтаксис `Efen` в пределах указанного контекста,
добавляя новые ключевые слова, операторы или синтаксические конструкции.

### Объявление extension диалекта

```efen
// Определение extension диалекта
@extensionDialect("async-await")
dialect AsyncExtension {
    // Добавляем новые ключевые слова
    keywords: ["async", "await", "spawn"]

    // Добавляем новый синтаксис для функций
    syntax function {
        async fn name(params) { body }
    }

    // Трансформация в базовый Efen
    transform async_fn(name, params, body) -> fn {
        return fn ${name}(${params}) -> Future<T> {
            return Future.spawn(|| { ${body} })
        }
    }
}
```

### Использование extension диалекта

```efen
// Подключение extension диалекта
use dialect AsyncExtension

// Использование расширенного синтаксиса
async fn fetchData(url: String) -> String {
    let response = await httpGet(url)
    let data = await response.json()
    return data
}

async fn processUsers {
    let users = await fetchUsers()
    for user in users {
        await processUser(user)
    }
}
```

### Контекстные расширения

Extension диалекты могут быть активны только в определённом контексте:

```efen
// Расширение активно только внутри блока
with dialect ReactiveExtension {
    // Специальный синтаксис для реактивности
    let signal count = 0

    effect {
        println("Count changed: ${count}")
    }

    count += 1  // Автоматически триггерит effect
}

// За пределами блока расширение не активно
```

## DSL диалекты (Domain-Specific Languages)

Специализированные диалекты для конкретных предметных областей:

### HTML/JSX диалект

```efen
use dialect JSX

fn renderUserCard(user: User) -> Element {
    return jsx {
        <div class="user-card">
            <h2>{user.name}</h2>
            <p>{user.email}</p>
            <button onClick={handleClick}>
                Contact
            </button>
        </div>
    }
}
```

### CSS диалект

```efen
use dialect CSS

let styles = css {
    .container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: ${spacing}px;
    }

    .button {
        background: ${primaryColor};
        border: none;
        border-radius: 4px;
    }
}
```

### GraphQL диалект

```efen
use dialect GraphQL

let userQuery = graphql {
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
            posts {
                title
                createdAt
            }
        }
    }
}
```

### Regex диалект

```efen
use dialect Regex

let emailPattern = regex {
    ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
}

let phonePattern = regex {
    ^\+?[\d\s-()]{10,}$
}

if emailPattern.matches(input) {
    println("Valid email")
}
```

## Создание пользовательских inline диалектов

### Простой пользовательский диалект

```efen
@inlineDialect("matrix")
dialect MatrixDialect {
    fn parse(source: String) -> Matrix {
        // Парсинг матричного синтаксиса
        let rows = source.lines()
        let values = rows.map => $row.split().map(parseFloat)
        return Matrix(values)
    }
}

// Использование
let matrix = matrix {
    1.0  0.0  0.0
    0.0  1.0  0.0
    0.0  0.0  1.0
}
```

### Диалект с валидацией

```efen
@inlineDialect("cron")
dialect CronDialect {
    fn parse(source: String) -> CronExpression {
        // Парсинг cron выражения
    }

    fn validate(expr: CronExpression) -> Result<(), Error> {
        // Валидация во время компиляции
        if !expr.isValid() {
            return .err(error: "Invalid cron expression")
        }
        return .ok(value: ())
    }
}

// Использование
let schedule = cron {
    0 0 * * *  // Каждый день в полночь
}
```

## Композиция диалектов

Диалекты могут комбинироваться:

```efen
use dialect JSX
use dialect CSS

fn renderApp -> Element {
    let styles = css {
        .app { padding: 20px; }
    }

    return jsx {
        <div class="app" style={styles}>
            <h1>My App</h1>
        </div>
    }
}
```

## Система плагинов для диалектов

### Установка диалекта из пакета

```bash
efen install dialect @efen/sql-dialect
efen install dialect @community/react-jsx
```

### Конфигурация диалектов

```toml
# efen.toml
[dialects]
enabled = ["json", "sql", "jsx"]

[dialects.sql]
validate_at_compile_time = true
database_schema = "schema.sql"

[dialects.jsx]
jsx_factory = "createElement"
jsx_fragment = "Fragment"
```

## Производительность диалектов

### Compile-time обработка

Большинство inline диалектов обрабатываются во время компиляции:

```efen
// Компилируется в константу
const config = json {
    "version": "1.0",
    "features": ["auth", "api"]
}

// Эквивалентно:
const config = JsonObject(
    version: "1.0",
    features: ["auth", "api"]
)
```

### Runtime обработка

Некоторые диалекты требуют runtime обработки:

```efen
// SQL с параметрами - runtime
let userId = getUserInput()
let query = sql {
    SELECT * FROM users WHERE id = ${userId}
}
// Генерирует подготовленный запрос с параметрами
```

## Безопасность диалектов

### SQL Injection защита

```efen
let userInput = "'; DROP TABLE users; --"

// Безопасно - параметры экранируются
let query = sql {
    SELECT * FROM users WHERE name = ${userInput}
}

// Компилируется в параметризованный запрос:
// SELECT * FROM users WHERE name = $1
```

### XSS защита в HTML

```efen
let userInput = "<script>alert('xss')</script>"

// Безопасно - автоматическое экранирование
let html = jsx {
    <div>{userInput}</div>
}

// Результат: <div>&lt;script&gt;alert('xss')&lt;/script&gt;</div>
```

## Отладка диалектов

### Source maps

Диалекты генерируют source maps для отладки:

```efen
// Исходный код с JSX
let element = jsx {
    <div>
        <h1>{title}</h1>
    </div>
}

// При ошибке показывается исходная позиция в JSX,
// а не в скомпилированном коде
```

### Режим отладки

```bash
efen compile --dialect-debug main.efen
```

Показывает промежуточное представление диалектов.

## Лучшие практики

1. **Используйте inline диалекты для DSL**
   ```efen
   // Хорошо - читаемо и безопасно
   let query = sql { SELECT * FROM users }

   // Плохо - строки подвержены ошибкам
   let query = "SELECT * FROM users"
   ```

2. **Валидируйте диалекты во время компиляции**
   ```efen
   @validateAtCompileTime
   let config = json { ... }
   ```

3. **Используйте типизацию**
   ```efen
   let data: JsonObject = json { ... }
   let users: ResultSet<User> = sql { ... }
   ```

4. **Избегайте переусложнения**
   ```efen
   // Хорошо - простой случай
   let data = json { "key": "value" }

   // Плохо - лучше использовать обычный код
   let complex = customDialect {
       // Очень сложная логика
   }
   ```

5. **Документируйте пользовательские диалекты**
   ```efen
   /// Matrix dialect для линейной алгебры
   /// Пример: matrix { 1 0; 0 1 }
   @inlineDialect("matrix")
   dialect MatrixDialect { ... }
   ```

## Ограничения

1. Inline диалекты не могут содержать определения типов
2. Extension диалекты не могут конфликтовать с базовым синтаксисом
3. Полноценные диалекты требуют отдельного компилятора-плагина
4. Максимальная вложенность диалектов ограничена
5. Некоторые диалекты требуют runtime библиотек
