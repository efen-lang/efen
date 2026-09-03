# Примеры декораторов Efen

Этот документ содержит практические примеры использования декораторов в Efen.

## Web-разработка

### REST API маршруты

```efen
@Route("/api/users", method: "GET")
@Authentication(required: true)
@RateLimit(requests: 100, period: 60)
fn getUsers(@Query page: Int = 1, @Query limit: Int = 10) -> [User] {
    return userService.getUsers(page, limit)
}

@Route("/api/users/:id", method: "PUT")
@Authorization(role: "admin")
fn updateUser(@Path id: Int, @Body userData: UserData) -> User {
    return userService.update(id, userData)
}
```

### ORM и база данных

```efen
@Entity
@Table(name: "users", indexes: ["email"])
class User {
    @Column(primary: true, autoIncrement: true)
    var id: Int

    @Column(type: "varchar", length: 255, unique: true)
    @NotNull
    @Email
    var email: String

    @Column(type: "varchar", length: 100)
    @NotNull
    var name: String

    @Column(type: "timestamp", default: "CURRENT_TIMESTAMP")
    var createdAt: DateTime

    @OneToMany(target: "Post", mappedBy: "author")
    var posts: [Post]
}

@Entity
class Post {
    @Column(primary: true)
    var id: Int

    @ManyToOne(target: "User")
    var author: User

    @Column(type: "text")
    var content: String
}
```

## Производительность

### Кэширование

```efen
@Cached(ttl: 3600, key: "user_config_{userId}")
fn getUserConfig(@Inject userId: Int) -> Config {
    return database.loadConfig(userId)
}

@Memoize
fn fibonacci(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fibonacci(n - 1) + fibonacci(n - 2)
}
```

### Профилирование и бенчмарки

```efen
@Benchmark
@Trace
fn complexCalculation(data: [Int]) -> Int {
    return data.reduce(0, (acc, x) => acc + x * x)
}

@Profile(detailed: true)
class DataProcessor {
    @Measure
    fn process(data: Data) -> Result {
        return transform(data)
    }
}
```

## Валидация и безопасность

### Валидация данных

```efen
fn createUser(
    @NotNull @Email email: String,
    @NotNull @Length(min: 3, max: 50) name: String,
    @Range(min: 18, max: 120) age: Int
) -> User {
    return User(email, name, age)
}

@ValidateInput
fn processPayment(
    @Positive amount: Float,
    @CreditCard cardNumber: String,
    @Future expiryDate: Date
) -> PaymentResult {
    return paymentGateway.charge(amount, cardNumber, expiryDate)
}
```

### Проверка прав доступа

```efen
@RequireAuthentication
@RequireRole("admin")
fn deleteUser(@Path userId: Int) -> Bool {
    return userService.delete(userId)
}

@CheckPermission("posts.edit")
fn editPost(@Inject currentUser: User, postId: Int, content: String) -> Post {
    return postService.update(postId, content)
}
```

## Dependency Injection

```efen
class UserController {
    @Inject
    var userService: UserService

    @Inject("database.primary")
    var database: Database

    @Inject
    var logger: Logger

    fn getUser(id: Int) -> User {
        logger.info("Fetching user: $id")
        return userService.find(id)
    }
}
```

## Транзакции и обработка ошибок

```efen
@Transaction
@Retry(maxAttempts: 3, backoff: "exponential")
fn transferMoney(from: Account, to: Account, amount: Float) -> Bool {
    from.withdraw(amount)
    to.deposit(amount)
    return true
}

@HandleErrors(strategy: "log_and_rethrow")
@Timeout(milliseconds: 5000)
fn fetchExternalData(url: String) -> Data {
    return httpClient.get(url)
}
```

## Сериализация

```efen
@Serializable
@JsonSerializable(camelCase: true)
class ApiResponse {
    @JsonProperty("user_id")
    var userId: Int

    @JsonIgnore
    var internalData: String

    var message: String
}
```

## Тестирование

```efen
@TestFixture
class UserServiceTests {
    @Mock
    var database: Database

    @BeforeEach
    fn setup() {
        database.clear()
    }

    @Test
    @Timeout(milliseconds: 1000)
    fn testCreateUser() {
        let user = userService.create("test@example.com")
        assert(user.id > 0)
    }

    @Test
    @ExpectedException("ValidationError")
    fn testInvalidEmail() {
        userService.create("invalid-email")
    }
}
```

## Логирование и мониторинг

```efen
@LogExecutionTime
@NotifyOnError(channel: "slack")
fn criticalOperation() -> Result {
    // выполнение критической операции
    return performOperation()
}

@Trace(level: "DEBUG", includeArguments: true)
fn debugFunction(param1: Int, param2: String) -> Result {
    return process(param1, param2)
}
```

## Оптимизация компиляции

```efen
@Inline
fn fastAdd(a: Int, b: Int) -> Int {
    return a + b
}

@NoInline
fn debugHelper() {
    // код для отладки
}

@CompileTimeEvaluate
fn constantCalculation() -> Int {
    return 42 * 1024 * 1024
}
```

## Deprecated и версионирование

```efen
@Deprecated("Use newFunction() instead", since: "2.0", removal: "3.0")
fn oldFunction() {
    // устаревший код
}

@Experimental
@Since("2.5")
fn experimentalFeature() {
    // экспериментальная функциональность
}
```

## Комбинирование декораторов

```efen
@Route("/api/admin/users", method: "POST")
@Authentication(required: true)
@Authorization(role: "admin")
@RateLimit(requests: 10, period: 60)
@ValidateInput
@Transaction
@Trace
@HandleErrors(strategy: "rollback_and_log")
fn createAdminUser(
    @NotNull @Email email: String,
    @NotNull @Strong password: String,
    @Inject logger: Logger
) -> User {
    logger.info("Creating admin user: $email")
    return userService.createAdmin(email, password)
}
```

## См. также

- [Основная документация по декораторам](decorators.md)
- [Compile-time функции](compile-time/index.md)
- [Метапрограммирование](meta/metadata.md)
