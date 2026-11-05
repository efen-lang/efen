# Примеры декораторов Efen

Этот документ содержит практические примеры использования декораторов в Efen.

## Web-разработка

### REST API маршруты

```efen
@route("/api/users", method: "GET")
@authentication(required: true)
@rateLimit(requests: 100, period: 60)
fn getUsers(@query page: Int = 1, @query limit: Int = 10) -> [User] {
    return userService.getUsers(page, limit)
}

@route("/api/users/:id", method: "PUT")
@authorization(role: "admin")
fn updateUser(@path id: Int, @body userData: UserData) -> User {
    return userService.update(id, userData)
}
```

### ORM и база данных

```efen
@entity
@table(name: "users", indexes: ["email"])
class User {
    @column(primary: true, autoIncrement: true)
    var id: Int

    @column(type: "varchar", length: 255, unique: true)
    @notNull
    @email
    var email: String

    @column(type: "varchar", length: 100)
    @notNull
    var name: String

    @column(type: "timestamp", default: "CURRENT_TIMESTAMP")
    var createdAt: DateTime

    @oneToMany(target: "Post", mappedBy: "author")
    var posts: [Post]
}

@entity
class Post {
    @column(primary: true)
    var id: Int

    @manyToOne(target: "User")
    var author: User

    @column(type: "text")
    var content: String
}
```

## Производительность

### Кэширование

```efen
@cached(ttl: 3600, key: "user_config_${userId}")
fn getUserConfig(@inject userId: Int) -> Config {
    return database.loadConfig(userId)
}

@memoize
fn fibonacci(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fibonacci(n - 1) + fibonacci(n - 2)
}
```

### Профилирование и бенчмарки

```efen
@benchmark
@trace
fn complexCalculation(data: [Int]) -> Int {
    return data.reduce(0, (acc, x) => acc + x * x)
}

@profile(detailed: true)
class DataProcessor {
    @measure
    fn process(data: Data) -> Result {
        return transform(data)
    }
}
```

## Валидация и безопасность

### Валидация данных

```efen
fn createUser(
    @notNull @email email: String,
    @notNull @length(min: 3, max: 50) name: String,
    @withinRange(min: 18, max: 120) age: Int
) -> User {
    return User(email, name, age)
}

@validateInput
fn processPayment(@positive amount: Float, @creditCard cardNumber: String, @future expiryDate: Date) -> PaymentResult {
    return paymentGateway.charge(amount, cardNumber, expiryDate)
}
```

### Проверка прав доступа

```efen
@requireAuthentication
@requireRole("admin")
fn deleteUser(@path userId: Int) -> Bool {
    return userService.delete(userId)
}

@checkPermission("posts.edit")
fn editPost(@inject currentUser: User, postId: Int, content: String) -> Post {
    return postService.update(postId, content)
}
```

## Dependency Injection

```efen
class UserController {
    @inject
    var userService: UserService

    @inject("database.primary")
    var database: Database

    @inject
    var logger: Logger

    fn getUser(id: Int) -> User {
        logger.info("Fetching user: ${id}")
        return userService.find(id)
    }
}
```

## Транзакции и обработка ошибок

```efen
@transaction
@retry(maxAttempts: 3, backoff: "exponential")
fn transferMoney(from: Account, to: Account, amount: Float) -> Bool {
    from.withdraw(amount)
    to.deposit(amount)
    return true
}

@handleErrors(strategy: "log_and_rethrow")
@timeout(milliseconds: 5000)
fn fetchExternalData(url: String) -> Data {
    return httpClient.get(url)
}
```

## Сериализация

```efen
@serializable
@jsonSerializable(camelCase: true)
class ApiResponse {
    @jsonProperty("user_id")
    var userId: Int

    @jsonIgnore
    var internalData: String

    var message: String
}
```

## Тестирование

Тест — объявление языка, а не функция с декоратором ([тесты](tests/tests.md)). Декоратор на `test` — атрибут теста,
его определение даёт фреймворк тестов; ожидаемое исключение проверяет `assert throws`.

```efen
@group("users")
test UserService.create "выдаёт пользователю номер" {
    let user = userService.create("test@example.com")

    assert user.id > 0
}

@group("users")
test UserService.create "отклоняет неверный адрес" {
    assert throws ValidationError {
        userService.create("invalid-email")
    }
}
```

## Логирование и мониторинг

```efen
@logExecutionTime
@notifyOnError(channel: "slack")
fn criticalOperation -> Result {
    // выполнение критической операции
    return performOperation()
}

@trace(level: "DEBUG", includeArguments: true)
fn debugFunction(param1: Int, param2: String) -> Result {
    return process(param1, param2)
}
```

## Оптимизация компиляции

```efen
@inline
fn fastAdd(a: Int, b: Int) -> Int {
    return a + b
}

@noInline
fn debugHelper {
    // код для отладки
}

@compileTimeEvaluate
fn constantCalculation -> Int {
    return 42 * 1024 * 1024
}
```

## Deprecated и версионирование

```efen
@deprecated("Use newFunction() instead", since: "2.0", removal: "3.0")
fn oldFunction {
    // устаревший код
}

@experimental
@since("2.5")
fn experimentalFeature {
    // экспериментальная функциональность
}
```

## Комбинирование декораторов

```efen
@route("/api/admin/users", method: "POST")
@authentication(required: true)
@authorization(role: "admin")
@rateLimit(requests: 10, period: 60)
@validateInput
@transaction
@trace
@handleErrors(strategy: "rollback_and_log")
fn createAdminUser(@notNull @email email: String, @notNull @strong password: String, @inject logger: Logger) -> User {
    logger.info("Creating admin user: ${email}")
    return userService.createAdmin(email, password)
}
```

## См. также

- [Основная документация по декораторам](decorators.md)
- [Compile-time функции](compile-time/index.md)
- [Метапрограммирование](aspects/metadata.md)
