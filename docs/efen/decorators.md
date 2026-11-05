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
@deprecated
fn oldFunction {
    // код
}

// Декоратор с позиционными параметрами
@route("/api/users", method: "GET")
fn getUsers {
    // код
}

// Декоратор с именованными параметрами
@cache(ttl: 3600, strategy: "LRU")
fn expensiveOperation {
    // код
}

// Множественные декораторы
@trace
@benchmark
@transaction
fn criticalOperation {
    // код
}

// Декораторы с namespace
@orm::entity
@orm::table(name: "users")
class User {
    // код
}
```

### Применение декораторов

Декораторы могут быть применены к:

#### 1. Функциям

```efen
@route("/api/data")
@authorization("admin")
fn getData -> Data {
    return fetchData()
}
```

#### 2. Классам

```efen
@entity
@table(name: "users")
class User {
    var name: String
}
```

#### 3. Методам и свойствам классов

```efen
class Service {
    @inject
    var database: Database

    @cached
    @public
    fn fetchData -> Data {
        return database.query()
    }
}
```

#### 4. Параметрам функций

```efen
fn processUser(@notNull @validated userId: Int, @inject service: UserService) -> User {
    return service.getUser(userId)
}
```

#### 5. Переменным

```efen
@cached
let expensiveResult = computeHeavyCalculation()

@volatile
var sharedCounter: Int = 0

@deprecated("Use newConfig instead")
param oldConfig: Config = defaultConfig
```

#### 6. Интерфейсам, контрактам, стратегиям

```efen
@serializable
interface DataObject {
    fn toJSON -> String
}

@compileTimeValidated
contract Comparable {
    fn compare(other: Self) -> Int
}

@optimizedDispatch
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
let values = Array<@myattr Int>()
let readers: Array<@cached User>
```

Он не прикрепляется ко всем употреблениям базового `Int` или `User`.
Атрибут является дополнительной опцией типового употребления и сам по себе не
делает `@myattr Int` несовместимым с `Int`.
Оператор `has` проверяет наличие атрибута. Директива `#if` использует проверку
при построении кода, обычный `if` — во время выполнения, если атрибут сохранён
в runtime metadata:

```efen
#if T has @myattr
    // compile-time ветвь
#endif

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
@trace
fn calculateSum(a: Int, b: Int) -> Int {
    return a + b
}

// Декоратор @trace добавляет логирование входа/выхода:
// fn calculateSum(a: Int, b: Int) -> Int {
//     log("Entering calculateSum with a=${a}, b=${b}")
//     let result = a + b
//     log("Exiting calculateSum with result=${result}")
//     return result
// }
```

### Пример 2: Кэширование

```efen
@cached(ttl: 600)
let config: Config = loadConfig()

// Декоратор @cached генерирует код для кэширования:
// - Проверяет кэш перед вызовом
// - Сохраняет результат в кэш
// - Возвращает закэшированное значение при повторном обращении
```

### Пример 3: ORM

```efen
@entity
@table(name: "users")
class User {
    @column(type: "int", primary: true)
    var id: Int

    @column(type: "string", length: 255)
    @notNull
    var email: String
}

// Декораторы генерируют:
// - SQL схему таблицы
// - Методы save(), delete(), find()
// - Валидацию данных
```

## Ограничения

1. **Декоратор стоит перед определением или оператором, но не внутри выражения.**
   Перед оператором его смысл задаёт метакод, который такой
   декоратор обрабатывает; декоратор, который не обработал никакой метакод,
   — ошибка компиляции. Так метафункция подсказывает
   компилятору, как развернуть цикл ([метафункции](compile-time/metafunctions.md)).
   Декораторы `lang` обрабатывает сам компилятор, например
   [`@accumulators(N)`](blocks/loops.md#порядок-вещественной-свёртки-accumulatorsn).

```efen
// ✓ МОЖНО - перед определением
@cached
let x = computeValue()

// ✓ МОЖНО - перед оператором, если его обрабатывает расширение компилятора
fn sum(values: [Int]) -> Int {
    var total = 0

    @unroll(4)
    for value in values {
        total += value
    }

    return total
}

// ✗ НЕЛЬЗЯ - внутри выражения
let y = @value() + 5
```

2. **Порядок выполнения**: Декораторы выполняются сверху вниз

```efen
@first      // Выполняется первым
@second     // Выполняется вторым
@third      // Выполняется третьим
fn example { }
```

## Создание собственных декораторов

Декоратор — тип, реализация которого — `meta fn`. Он добавляет metadata и объявления рядом с
помеченным и может заменить тело помеченного объявления. Новое публичное объявление и изменённая
сигнатура объявляются при регистрации. Границы и песочница — в [плагинах и метакоде](compile-time/plugins.md#атрибуты).
Декоратор объявляется классом с `conforms Attribute` (контракт `lang::`); его имя разрешается так же, как
имя функции, а `@cache(ttl: 3600)` создаёт экземпляр класса, как вызов конструктора. Атрибут без `meta fn`
только несёт данные, их читает метакод или [плагин компилятора](compile-time/compiler-plugins.md#c0-осмотр).

## См. также

- [Compile-time функции](compile-time/index.md)
- [Метаданные](aspects/metadata.md)
- [Аспектно-ориентированное программирование](aspects/compile-time/index.md)
