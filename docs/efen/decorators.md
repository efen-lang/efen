# Декораторы

Декораторы -- мощный инструмент для добавления дополнительного поведения к функциям, классам,
модулям без изменения их исходного кода.
Они позволяют модифицировать код, добавлять функциональность, такую как логирование, проверка прав доступа,
кэширование, генерацию кода и многое другое.

Декораторы в `Efen` являются **функциями времени компиляции** с доступом к API компилятора, которые:
- Могут изменять AST (абстрактное синтаксическое дерево)
- Инжектировать код в функции, классы
- Модифицировать метаданные и атрибуты
- Влиять на runtime поведение через compile-time трансформации

## Синтаксис

### Базовый синтаксис

```efen
// Декоратор без параметров
@Deprecated
fn oldFunction {
    // код
}

// Декоратор с позиционными параметрами
@Route("/api/users", method: "GET")
fn getUsers {
    // код
}

// Декоратор с именованными параметрами
@Cache(ttl: 3600, strategy: "LRU")
fn expensiveOperation {
    // код
}

// Множественные декораторы
@Trace
@Benchmark
@Transaction
fn criticalOperation {
    // код
}

// Декораторы с namespace
@ORM::Entity
@ORM::Table(name: "users")
class User {
    // код
}
```

### Применение декораторов

Декораторы могут быть применены к:

#### 1. Функциям

```efen
@Route("/api/data")
@Authorization("admin")
fn getData -> Data {
    return fetchData()
}
```

#### 2. Классам

```efen
@Entity
@Table(name: "users")
class User {
    var name: String
}
```

#### 3. Методам и свойствам классов

```efen
class Service {
    @Inject
    var database: Database

    @Cached
    @Public
    fn fetchData -> Data {
        return database.query()
    }
}
```

#### 4. Параметрам функций

```efen
fn processUser(
    @NotNull @Validated userId: Int,
    @Inject service: UserService
) -> User {
    return service.getUser(userId)
}
```

#### 5. Переменным

```efen
@Cached
let expensiveResult = computeHeavyCalculation()

@Volatile
var sharedCounter: Int = 0

@Deprecated("Use newConfig instead")
param oldConfig: Config = defaultConfig
```

#### 6. Интерфейсам, контрактам, стратегиям

```efen
@Serializable
interface DataObject {
    fn toJSON -> String
}

@CompileTimeValidated
contract Comparable {
    fn compare(other: Self) -> Int
}

@OptimizedDispatch
strategy FastMath for Int {
    fn square -> Int {
        return this * this
    }
}
```

#### 7. Употреблениям типов

Атрибут перед типом относится к этому конкретному типовому употреблению и
передаётся вместе с ним в generic-код:

```efen
let values = new Array<@myattr Int>
let readers: Array<@cached &read User>
```

Он не прикрепляется ко всем употреблениям базового `Int` или `User`.
Атрибут является дополнительной опцией типового употребления и сам по себе не
делает `@myattr Int` несовместимым с `Int`.
Оператор `has` проверяет наличие атрибута. Директива `#if` использует проверку
при построении кода, обычный `if` — во время выполнения, если атрибут сохранён
в runtime metadata:

```efen
#if T has @myattr {
    // compile-time ветвь
}

if value has @myattr {
    // runtime ветвь
}
```

## Как работают декораторы

Декораторы выполняются во время компиляции в следующем порядке:

1. **Парсинг** - декораторы распознаются парсером и добавляются в AST
2. **Разрешение** - компилятор находит определения декораторов
3. **Выполнение** - декораторы вызываются с доступом к:
   - AST узлу, к которому они применены
   - Контексту компиляции
   - API компилятора для модификации кода
4. **Трансформация** - декораторы могут изменить AST, добавить код, метаданные
5. **Кодогенерация** - измененный AST используется для генерации финального кода

## Примеры использования

### Пример 1: Логирование

```efen
@Trace
fn calculateSum(a: Int, b: Int) -> Int {
    return a + b
}

// Декоратор @Trace добавляет логирование входа/выхода:
// fn calculateSum(a: Int, b: Int) -> Int {
//     log("Entering calculateSum with a=${a}, b=${b}")
//     let result = a + b
//     log("Exiting calculateSum with result=${result}")
//     return result
// }
```

### Пример 2: Кэширование

```efen
@Cached(ttl: 600)
let config: Config = loadConfig()

// Декоратор @Cached генерирует код для кэширования:
// - Проверяет кэш перед вызовом
// - Сохраняет результат в кэш
// - Возвращает закэшированное значение при повторном обращении
```

### Пример 3: ORM

```efen
@Entity
@Table(name: "users")
class User {
    @Column(type: "int", primary: true)
    var id: Int

    @Column(type: "string", length: 255)
    @NotNull
    var email: String
}

// Декораторы генерируют:
// - SQL схему таблицы
// - Методы save(), delete(), find()
// - Валидацию данных
```

## Ограничения

1. **Декораторы только для определений**: Декораторы не могут использоваться как отдельные операторы или внутри выражений

```efen
// ✗ НЕЛЬЗЯ - как отдельный оператор
fn test {
    @something
    echo "test"
}

// ✗ НЕЛЬЗЯ - внутри выражения
let x = @value() + 5

// ✓ МОЖНО - привязан к определению
@cached
let x = computeValue()
```

2. **Порядок выполнения**: Декораторы выполняются сверху вниз

```efen
@First      // Выполняется первым
@Second     // Выполняется вторым
@Third      // Выполняется третьим
fn example { }
```

## Создание собственных декораторов

Декораторы определяются как compile-time функции с доступом к API компилятора:

```efen
// Пример структуры декоратора (детали реализации в документации метапрограммирования)
@CompilerAPI
fn MyDecorator(target: ASTNode, args: DecoratorArgs) {
    // Модификация AST узла
    // Инжектирование кода
    // Изменение метаданных
}
```

## См. также

- [Compile-time функции](compile-time/index.md)
- [Метаданные](aspects/metadata.md)
- [Аспектно-ориентированное программирование](aspects/compile-time/index.md)
