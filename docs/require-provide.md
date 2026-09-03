# Модульная система Efen
## Require и Provide

Модульная система Efen поддерживает декларативное управление зависимостями через механизм **require/provide**. Это позволяет модулям объявлять свои требования в виде контрактов, которые могут быть удовлетворены разными реализациями.

---

## Основные концепции

### Контракты

Контракт определяет интерфейс, который должен быть реализован:

```efen
contract FileSystem {
    fn open(path: String, mode: String) -> Result<FileHandle, Error>
    fn read(handle: FileHandle, size: Int) -> Result<[Byte], Error>
    fn write(handle: FileHandle, data: [Byte]) -> Result<Int, Error>
    fn close(handle: FileHandle) -> Result<Void, Error>
}
```

### Требования (require)

Модуль может объявить, что ему нужна реализация определенного контракта:

```efen
module DataProcessor {
    require FileSystem

    fn processFile(path: String) -> Result<Data, Error> {
        let handle = FileSystem::open(path, "r")?
        let data = FileSystem::read(handle, 1024)?
        FileSystem::close(handle)?
        return Ok(parseData(data))
    }
}
```

### Предоставление (provide)

Реализации контрактов можно предоставлять двумя способами:

**Глобально для всего проекта:**

```efen
module Main {
    // Везде, где требуется FileSystem, использовать PosixFileSystem
    implement FileSystem as std::fs::PosixFileSystem

    fn main() {
        DataProcessor::processFile("data.txt")
    }
}
```

**Локально при использовании модуля:**

```efen
module Main {
    // Для DataProcessor использовать PosixFileSystem
    use DataProcessor with {
        FileSystem: std::fs::PosixFileSystem
    }

    fn main() {
        DataProcessor::processFile("data.txt")
    }
}
```

---

## Синтаксис require

### Базовое требование

```efen
module MyModule {
    require ContractName
}
```

Модуль требует реализацию контракта. Если реализация не будет предоставлена, компилятор выдаст ошибку.

### Требование с реализацией по умолчанию

```efen
module MyModule {
    require FileSystem default std::fs::PosixFileSystem
}
```

Если никто не предоставит альтернативную реализацию, будет использована реализация по умолчанию.

### Опциональное требование

```efen
module Analytics {
    require Logger optional

    fn trackEvent(event: String) {
        Logger?.info("Event: ${event}")
        // Работает даже если Logger не предоставлен
    }
}
```

Если контракт не предоставлен, обращения к нему через `?` будут проигнорированы.

### Платформо-зависимые требования

```efen
module Worker {
    require Threading select {
        case Platform::Windows: std::thread::WindowsThreading
        case Platform::Linux: std::thread::PosixThreading
        case Platform::MacOS: std::thread::PosixThreading
    }
}
```

Реализация выбирается автоматически на основе целевой платформы.

---

## Синтаксис implement/provide

### Глобальное предоставление

**ВАЖНО:** Глобальные `implement` и `implements` объявляются только на уровне **package**, не внутри модулей.

```efen
package MyApp

// Глобально: везде использовать PostgresDB для контракта Database
implement Database as db::PostgresDB

module Config {
    // implement здесь будет ошибкой!
}
```

Предоставляет реализацию `PostgresDB` для контракта `Database` глобально во всём пакете.

### Предоставление с конфигурацией

```efen
package MyApp

implement Cache as cache::RedisCache {
    host: "localhost"
    port: 6379
    ttl: 3600
}
```

Конфигурация передается в конструктор реализации.

### Условное предоставление

Можно использовать условные выражения:

```efen
package MyApp

implement Storage as
    if isProduction() then S3Storage else LocalStorage
```

### Реализация по умолчанию

```efen
package MyApp

// Используется, если нет других implement для Logger
implement default Logger as ConsoleLogger

// Переопределяет default только в production
implement Logger as FileLogger where env == "production"
```

`implement default` используется только если нет других явных предоставлений.

### Блок глобальных предоставлений

```efen
package MyApp

implements {
    FileSystem: std::fs::PosixFileSystem
    Database: db::PostgresDB
    Logger: log::FileLogger
}
```

Предоставляет реализации для всех модулей пакета.

### Условные выражения в блоке implements

Можно использовать условные выражения в блоке `implements`:

```efen
package MyApp

implements {
    Database: if isProduction()
              then db::PostgresDB
              else db::SQLiteDB

    Logger: if isProduction()
            then log::FileLogger
            else log::ConsoleLogger
}
```

### Локальное предоставление при использовании модуля

```efen
module TestConfig {
    // Для конкретного модуля
    use UserRepository with {
        Database: MockDatabase
        Logger: NullLogger
    }

    // Для группы модулей
    use app::* with {
        Logger: NullLogger
        Cache: MockCache
    }
}
```

---

## Примеры использования

### Пример 0: Полный цикл с package конфигурацией

**package.efen:**
```efen
package WebApp

// Глобальные реализации на уровне package
implements {
    Database: if isPostgres() then db::PostgresDB
              else if isMySQL() then db::MySQLDB
              else db::SQLiteDB

    Logger: if isProduction()
            then log::FileLogger { path: "/var/log/app.log" }
            else log::ConsoleLogger

    FileSystem: std::fs::PosixFileSystem
}

// Реализация по умолчанию для Cache (если не задано явно)
implement default Cache as cache::MemoryCache
```

**app/users.efen:**
```efen
module UserService {
    require Database
    require Logger
    require Cache optional

    fn createUser(name: String) -> Result<User, Error> {
        Logger.info("Creating user: ${name}")

        let user = User { name: name }
        Database::save(user)?

        Cache?.set("user:${user.id}", user)

        return Ok(user)
    }
}
```

**main.efen:**
```efen
module Main {
    // Для тестов можем переопределить локально
    use UserService with {
        Database: MockDatabase
        Logger: NullLogger
    } in tests

    fn main() {
        // В production используются глобальные implements из package
        UserService::createUser("Alice")
    }
}
```

### Пример 1: Файловая система

**Контракт:**

```efen
contract FileSystem {
    fn open(path: String, mode: String) -> Result<FileHandle, Error>
    fn read(handle: FileHandle, size: Int) -> Result<[Byte], Error>
    fn write(handle: FileHandle, data: [Byte]) -> Result<Int, Error>
    fn close(handle: FileHandle) -> Result<Void, Error>
}
```

**Реализация для POSIX:**

```efen
module PosixFileSystem implements FileSystem {
    fn open(path: String, mode: String) -> Result<FileHandle, Error> {
        let fd = ffi::fopen(path.cStr(), mode.cStr())
        if fd == null {
            return Error("Failed to open file")
        }
        return Ok(FileHandle(fd))
    }

    fn read(handle: FileHandle, size: Int) -> Result<[Byte], Error> {
        let buffer = [Byte](size)
        let bytesRead = ffi::fread(buffer.ptr(), 1, size, handle.fd)
        return Ok(buffer[0..<bytesRead])
    }

    fn write(handle: FileHandle, data: [Byte]) -> Result<Int, Error> {
        let written = ffi::fwrite(data.ptr(), 1, data.size(), handle.fd)
        return Ok(written)
    }

    fn close(handle: FileHandle) -> Result<Void, Error> {
        ffi::fclose(handle.fd)
        return Ok(void)
    }
}
```

**Использование:**

```efen
module FileProcessor {
    require FileSystem default PosixFileSystem

    fn readConfig(path: String) -> Result<Config, Error> {
        let handle = FileSystem::open(path, "r")?
        let data = FileSystem::read(handle, 4096)?
        FileSystem::close(handle)?

        return Config::parse(data)
    }
}
```

**Тестирование с моком:**

```efen
module MockFileSystem implements FileSystem {
    var files: [String: [Byte]] = [:]

    fn open(path: String, mode: String) -> Result<FileHandle, Error> {
        if mode == "r" && !files.containsKey(path) {
            return Error("File not found")
        }
        return Ok(FileHandle(path))
    }

    fn read(handle: FileHandle, size: Int) -> Result<[Byte], Error> {
        return Ok(files[handle.path] ?? [])
    }

    fn write(handle: FileHandle, data: [Byte]) -> Result<Int, Error> {
        files[handle.path] = data
        return Ok(data.size())
    }

    fn close(handle: FileHandle) -> Result<Void, Error> {
        return Ok(void)
    }

    fn addMockFile(path: String, content: String) {
        files[path] = content.bytes()
    }
}

module FileProcessorTest {
    use FileProcessor with {
        FileSystem: MockFileSystem
    }

    test readConfig "should read config file" {
        MockFileSystem::addMockFile("config.json", """{"port": 8080}""")

        let result = FileProcessor::readConfig("config.json")

        assert(result.isOk())
        assert(result.unwrap().port == 8080)
    }
}
```

---

### Пример 2: Логирование

**Контракт:**

```efen
contract Logger {
    fn debug(message: String)
    fn info(message: String)
    fn warn(message: String)
    fn error(message: String)
}
```

**Использование опционального логирования:**

```efen
module OrderProcessor {
    require Logger optional

    fn processOrder(order: Order) -> Result<Void, Error> {
        Logger?.info("Processing order ${order.id}")

        if order.total < 0 {
            Logger?.error("Invalid order total: ${order.total}")
            return Error("Invalid order")
        }

        // Обработка заказа
        Logger?.info("Order ${order.id} processed successfully")
        return Ok(void)
    }
}
```

**Production конфигурация:**

```efen
module ProductionApp {
    use OrderProcessor with {
        Logger: logging::FileLogger {
            path: "/var/log/app.log"
            level: LogLevel::Info
        }
    }

    fn main() {
        let order = Order(id: "123", total: 100.0)
        OrderProcessor::processOrder(order)
    }
}
```

**Development без логирования:**

```efen
module DevelopmentApp {
    // Logger не предоставлен - вызовы Logger? игнорируются

    fn main() {
        let order = Order(id: "123", total: 100.0)
        OrderProcessor::processOrder(order)
    }
}
```

---

### Пример 3: База данных

**Контракт:**

```efen
contract Database {
    fn connect(url: String) -> Result<Connection, Error>
    fn query(conn: Connection, sql: String) -> Result<ResultSet, Error>
    fn execute(conn: Connection, sql: String) -> Result<Int, Error>
    fn close(conn: Connection)
}
```

**Использование:**

```efen
module UserRepository {
    require Database

    fn findById(id: Int) -> Result<User?, Error> {
        let conn = Database::connect(config::DB_URL)?
        let result = Database::query(conn, "SELECT * FROM users WHERE id = ${id}")?
        Database::close(conn)

        if result.isEmpty() {
            return Ok(null)
        }

        return Ok(User::fromRow(result[0]))
    }

    fn save(user: User) -> Result<Void, Error> {
        let conn = Database::connect(config::DB_URL)?
        let sql = """
            INSERT INTO users (name, email)
            VALUES ('${user.name}', '${user.email}')
        """
        Database::execute(conn, sql)?
        Database::close(conn)

        return Ok(void)
    }
}
```

**Production конфигурация:**

```efen
module Main {
    implements {
        Database: db::PostgresDB
    }

    fn main() {
        let user = UserRepository::findById(1)
        println(user)
    }
}
```

**Тестирование:**

```efen
module MockDatabase implements Database {
    var users: [Int: User] = [:]

    fn connect(url: String) -> Result<Connection, Error> {
        return Ok(Connection::mock())
    }

    fn query(conn: Connection, sql: String) -> Result<ResultSet, Error> {
        // Простой парсинг SQL для тестов
        if sql.contains("WHERE id =") {
            let id = extractId(sql)
            if let user = users[id] {
                return Ok(ResultSet([user.toRow()]))
            }
        }
        return Ok(ResultSet([]))
    }

    fn execute(conn: Connection, sql: String) -> Result<Int, Error> {
        // Эмуляция INSERT
        return Ok(1)
    }

    fn close(conn: Connection) {
        // Ничего не делаем
    }

    fn addUser(id: Int, user: User) {
        users[id] = user
    }
}

module UserRepositoryTest {
    use UserRepository with {
        Database: MockDatabase
    }

    test findById "should find user by id" {
        MockDatabase::addUser(1, User(name: "Alice", email: "alice@example.com"))

        let result = UserRepository::findById(1)

        assert(result.isOk())
        assert(result.unwrap()?.name == "Alice")
    }

    test findByIdNotFound "should return null for non-existent user" {
        let result = UserRepository::findById(999)

        assert(result.isOk())
        assert(result.unwrap() == null)
    }
}
```

---

### Пример 4: Кросс-платформенная разработка

**Контракт:**

```efen
contract Threading {
    fn createThread(fn: () -> Void) -> ThreadHandle
    fn joinThread(handle: ThreadHandle)
    fn sleep(milliseconds: Int)
}
```

**Модуль с платформо-зависимыми требованиями:**

```efen
module BackgroundWorker {
    require Threading select {
        case Platform::Windows: std::thread::WindowsThreading
        case Platform::Linux: std::thread::PosixThreading
        case Platform::MacOS: std::thread::PosixThreading
    }

    fn startJob(job: () -> Void) {
        let handle = Threading::createThread(job)
        Threading::joinThread(handle)
    }

    fn waitSeconds(seconds: Int) {
        Threading::sleep(seconds * 1000)
    }
}
```

**Реализация для Windows:**

```efen
module WindowsThreading implements Threading {
    fn createThread(fn: () -> Void) -> ThreadHandle {
        let handle = ffi::CreateThread(null, 0, fn, null, 0, null)
        return ThreadHandle(handle)
    }

    fn joinThread(handle: ThreadHandle) {
        ffi::WaitForSingleObject(handle.native, INFINITE)
    }

    fn sleep(milliseconds: Int) {
        ffi::Sleep(milliseconds)
    }
}
```

**Реализация для POSIX (Linux/macOS):**

```efen
module PosixThreading implements Threading {
    fn createThread(fn: () -> Void) -> ThreadHandle {
        var thread: pthread_t
        pthread_create(&thread, null, fn, null)
        return ThreadHandle(thread)
    }

    fn joinThread(handle: ThreadHandle) {
        pthread_join(handle.native, null)
    }

    fn sleep(milliseconds: Int) {
        let ts = timespec {
            tv_sec: milliseconds / 1000,
            tv_nsec: (milliseconds % 1000) * 1000000
        }
        nanosleep(&ts, null)
    }
}
```

---

## Разрешение зависимостей

### Порядок разрешения

Компилятор разрешает требования в следующем порядке:

1. **Локальное предоставление при `use`** (наивысший приоритет)
   ```efen
   use MyModule with { Logger: FileLogger }
   ```

2. **Глобальный `implements` блок на уровне package**
   ```efen
   implements { Logger: FileLogger }
   ```

3. **Глобальное `implement` на уровне package**
   ```efen
   implement Logger as FileLogger
   ```

4. **Реализация по умолчанию в `require`**
   ```efen
   require Logger default ConsoleLogger
   ```

5. **Глобальное `implement default` на уровне package**
   ```efen
   implement default Logger as ConsoleLogger
   ```

6. **Ошибка компиляции** (если требование обязательное)

### Приоритет предоставлений

Если несколько модулей предоставляют одну и ту же реализацию, используется последняя по порядку компиляции. Для явного управления используйте аннотацию `@priority`:

```efen
module ConfigA {
    @priority(1)
    implement Database as PostgresDB
}

module ConfigB {
    @priority(2)  // Более высокий приоритет
    implement Database as MySQLDB
}
```

### Проверка во время компиляции

Компилятор проверяет:

- ✅ Все обязательные требования удовлетворены
- ✅ Реализации соответствуют контрактам
- ✅ Нет циклических зависимостей
- ✅ Конфигурации имеют правильные типы

Пример ошибки:

```
Error: Unsatisfied requirement 'Database' for module 'UserRepository'

  --> user_repository.efen:2:5
   |
 2 |     require Database
   |     ^^^^^^^^^^^^^^^^
   |
   = help: Add a default: require Database default PostgresDB
   = help: Or implement globally: implement Database as PostgresDB
   = help: Or provide locally: use UserRepository with { Database: PostgresDB }
```

---

## Best Practices

### Используйте контракты для абстракций

✅ **Правильно:**
```efen
contract Database {
    fn query(sql: String) -> Result<ResultSet, Error>
}

module UserRepo {
    require Database
}
```

❌ **Неправильно:**
```efen
module UserRepo {
    require PostgresDB  // Конкретная реализация!
}
```

### Предоставляйте реализации по умолчанию

Для библиотечного кода предоставляйте разумные реализации по умолчанию:

```efen
module DataProcessor {
    require FileSystem default std::fs::PosixFileSystem
}
```

Для application кода можно требовать явную конфигурацию:

```efen
module WebServer {
    require Database  // Обязательно явное предоставление
}
```

### Используйте package-level конфигурацию

**ВАЖНО:** Всегда определяйте `implement` и `implements` на уровне **package**, а не в модулях.

✅ **Правильно:**
```efen
package MyApp

implements {
    Database: PostgresDB
    Cache: RedisCache
    Logger: FileLogger
}
```

❌ **Неправильно:**
```efen
module Config {
    implements {  // ОШИБКА! Только на уровне package!
        Database: PostgresDB
    }
}
```

### Используйте условные выражения для гибкости

```efen
package MyApp

implement Database as if isPostgres() then PostgresDB else SQLiteDB
implement Cache as RedisCache {
    ttl: 3600
}
```

### Используйте опциональные требования для не-критичных зависимостей

```efen
module Analytics {
    require Logger optional
    require Metrics optional

    fn trackEvent(event: String) {
        Logger?.info("Event: ${event}")
        Metrics?.increment("events.${event.type}")
        // Основная логика работает без Logger и Metrics
    }
}
```

---

## Сравнение с use

`use` и `require/provide` решают разные задачи:

### use - импорт модулей

```efen
use std::collections::HashMap
use math::complex as Complex

fn example() {
    let map = HashMap::new()
    let c = Complex::new(1.0, 2.0)
}
```

`use` импортирует конкретный модуль и его API становится доступным.

### require - декларация зависимостей

```efen
require FileSystem default PosixFileSystem

fn example() {
    let handle = FileSystem::open("file.txt", "r")
    // FileSystem - это контракт, реализация может быть разной
}
```

`require` объявляет зависимость от контракта, конкретная реализация может меняться.

### Когда что использовать

- **use** - когда нужна конкретная реализация
- **require** - когда зависите от абстракции

Пример комбинированного использования:

```efen
module App {
    use std::collections::HashMap  // Конкретная структура данных
    require Database               // Абстракция для БД

    fn cacheUsers() {
        let cache = HashMap::new()
        let users = Database::query("SELECT * FROM users")
        // ...
    }
}
```

---

## Грамматика

### require

```efen
requireDeclaration
    : 'require' IDENTIFIER requireModifier*
    ;

requireModifier
    : 'default' type
    | 'optional'
    | 'where' whereClause
    | 'select' '{' selectCase+ '}'
    ;

selectCase
    : 'case' expression ':' type
    ;
```

### implement (глобальное, только на уровне package)

```efen
implementDeclaration
    : 'implement' 'default'? IDENTIFIER 'as' implementationExpr whereClause?
    ;

implementationExpr
    : type                                      // SimpleImpl
    | type '{' implementConfig '}'             // ConfiguredImpl { key: value }
    | 'if' expression 'then' type 'else' type  // условная
    ;

implementConfig
    : (IDENTIFIER ':' expression ','?)*
    ;

whereClause
    : 'where' expression
    ;
```

### implements (блок, только на уровне package)

```efen
implementsBlock
    : 'implements' '{' implementEntry+ '}'
    ;

implementEntry
    : IDENTIFIER ':' implementationExpr
    ;
```

### use with (локальное)

```efen
useDeclaration
    : 'use' modulePath ('with' '{' contractBindings '}')?
    ;

contractBindings
    : contractBinding (',' contractBinding)*
    ;

contractBinding
    : IDENTIFIER ':' implementationExpr
    ;
```

---

## См. также

- [Контракты](contracts.md)
- [Модули](modules.md)
- [Стратегии](strategies.md)
- [Импорты (use)](imports.md)
