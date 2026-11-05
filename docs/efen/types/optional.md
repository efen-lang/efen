<a id="optional-types-опциональные-типы"></a>

# Опциональные типы: `T?`

Опциональный тип `T?` позволяет хранить значение типа `T` или обозначить
его отсутствие через `null`. Возможность отсутствия видна в типе, поэтому
код должен её учитывать при обращении к значению.

<a id="что-такое-optional"></a>

## Значение или его отсутствие

Например, `Int?` может содержать целое число или `null`.

`null` означает отсутствие значения. Это не число `0` и не нулевой указатель.
У него нет единого для всех типов представления в памяти: способ хранения
задаётся в типе. Например, отсутствие может храниться как специальное число,
как нулевой указатель или как отдельный признак. В коде Efen во всех этих
случаях пишется `null`; подробности хранения не меняют его смысла.

```efen
var optionalInt: Int? = 42        // Содержит значение
var emptyOptional: Int? = null    // Отсутствие значения
```

### Синтаксис

Для объявления опционального типа используется символ `?` после имени типа:

```efen
let name: String?           // строка или null
let age: Int?               // целое или null
let values: [Int]?          // массив целых или null
let callback: ((Int) -> Void)?  // функция или null
```

Каноническая запись опционального типа — `T?`. `Option<T>` — стандартный обобщённый псевдоним
`T?`, который пишется только для вложенного опционального типа; `Option<Int>` вместо `Int?`
и `T | null` получают диагностику стиля. Значения записываются только `null` и
самим значением:

```efen
alias Option<T> = T?

let number: Int? = 42
let absent: Int? = null
```

Вложенный опциональный тип сохраняет каждый уровень отсутствия значения:

```efen
Option<Option<String>>
Option<String?>
```

Обе записи различают отсутствие внешнего уровня и присутствующий внешний уровень
с `null` внутри. Повторение постфиксного оператора не является синтаксисом типа:
`String??` — ошибка; вложенность записывается через `Option<...>`. Значение
вложенного уровня задаётся через тип:

```efen
let inner: String? = null
let outer: Option<String?> = inner      // внешний уровень есть, внутри null
let empty: Option<String?> = null       // внешнего уровня нет
```

<a id="зачем-нужны-optional"></a>
<a id="проблема-null-в-других-языках"></a>

## Зачем явно указывать отсутствие значения

Если поиск может не дать результата, это должно быть видно в типе результата.
Например, `findUser(...) -> User?` сообщает вызывающему коду, что пользователь
может отсутствовать. До обращения к его полям нужно проверить результат.

<a id="решение-через-optional"></a>

### Проверка опционального значения

```efen
// Efen: тип явно показывает возможность отсутствия значения
fn findUser(id: Int) -> User? {
    // Явно возвращаем optional
    return null  // OK, соответствует типу User?
}

let user = findUser(id: 123)
// user имеет тип User?, компилятор заставит проверить
print(user.name)  // ❌ ОШИБКА КОМПИЛЯЦИИ!
```

<a id="создание-optional-значений"></a>

## Создание опциональных значений

### Из обычного значения

```efen
let number: Int? = 42
let text: String? = "Hello"
```

### Явное отсутствие значения

```efen
let empty: String? = null
```

### Автоматическое преобразование

```efen
let value: Int = 42
let optional: Int? = value  // Автоматически оборачивается в Optional
```

### Из функций

```efen
fn parseInt(string: String) -> Int? {
    // Возвращает Int? если парсинг успешен, иначе null
    if let result = tryParse(string) {
        return result
    }
    return null
}

let number = parseInt("42")    // Int?
let invalid = parseInt("abc")  // Int? = null
```

<a id="работа-с-optional-значениями"></a>

## Проверка и извлечение значений

<a id="1-optional-binding-if-let"></a>

### 1. Проверка и извлечение значения (if let)

Самый безопасный способ извлечь значение:

```efen
let optionalName: String? = "Иван"

if let name = optionalName {
    print("Привет, ${name}!")  // name имеет тип String
} else {
    print("Имя не указано")
}
```

Одновременная проверка нескольких значений:

```efen
let optionalName: String? = "Иван"
let optionalAge: Int? = 25

if let name = optionalName, let age = optionalAge {
    print("${name}, возраст: ${age}")
} else {
    print("Недостаточно данных")
}
```

С дополнительными условиями:

```efen
if let age = optionalAge, age >= 18 {
    print("Совершеннолетний: ${age} лет")
}
```

### 2. Guard Let (ранний выход)

Для функций с ранним выходом:

```efen
fn greet(name: String?) {
    guard let name = name else {
        print("Имя не указано")
        return
    }

    // name доступен во всей оставшейся функции
    print("Привет, ${name}!")
}
```

### 3. Nil-Coalescing Operator (??)

Предоставляет значение по умолчанию:

```efen
let optionalName: String? = null
let name = optionalName ?? "Гость"
print(name)  // "Гость"
```

С вычисляемым значением:

```efen
let name = optionalName ?? getDefaultName()
```

Цепочка операторов:

```efen
let result = option1 ?? option2 ?? option3 ?? "default"
```

<a id="4-optional-chaining"></a>

### 4. Цепочка обращений с проверкой `null`

Безопасный доступ к свойствам и методам:

```efen
class Person {
    var name: String
    var address: Address?
}

class Address {
    var street: String
    var city: String
}

let person: Person? = getPerson()

// Без optional chaining
if let person = person {
    if let address = person.address {
        print(address.city)
    }
}

// С optional chaining
print(person?.address?.city)  // Вернет String? или null
```

Вызов методов в цепочке с проверкой наличия значения:

```efen
class Calculator {
    fn add(a: Int, b: Int) -> Int {
        return a + b
    }
}

let calc: Calculator? = Calculator()
let result = calc?.add(a: 5, b: 3)  // Int?
```

### 5. Forced Unwrapping (!)

`x!` разворачивает `T?` в `T`. Если значение `null`, бросается
`NullUnwrapError`; исключение входит в выведенный `throws` функции, как и
у контекстного разворачивания. Остановки выполнения нет: `x!` — короткая запись
`x != null ? x : throw NullUnwrapError()`.

```efen
let optionalNumber: Int? = 42
let number = optionalNumber!  // Int = 42

let empty: Int? = null
let value = empty!            // бросает NullUnwrapError
```

**Когда использовать:**
- Только если вы **абсолютно уверены**, что значение не null
- После явной проверки на null

```efen
if optionalValue != null {
    let value = optionalValue!  // Безопасно после проверки
    // Но лучше использовать if let!
}
```

### 6. Проверка на null

Явная проверка:

```efen
if optionalValue != null {
    // Значение присутствует
} else {
    // Значение отсутствует
}
```

**Примечание:** Предпочитайте `if let` вместо явной проверки!

<a id="optional-в-match"></a>

## Опциональные значения в `match`

В `match` можно отдельно обработать значение и его отсутствие:

```efen
let optionalNumber: Int? = 42

match optionalNumber {
    null: print("Значение отсутствует")
    let value?: print("Значение: ${value}")
}
```

С дополнительными условиями:

```efen
match optionalNumber {
    null: print("Нет значения")
    let value? where value > 0: print("Положительное: ${value}")
    let value? where value < 0: print("Отрицательное: ${value}")
    0?: print("Ноль")
    _: print("Другое")
}
```

<a id="optional-в-коллекциях"></a>

## Опциональные значения и коллекции

<a id="массив-optional-значений"></a>

### Массив значений, каждое из которых может отсутствовать

```efen
let numbers: [Int?] = [1, 2, null, 4, null, 6]

for number in numbers {
    if let value = number {
        print("Значение: ${value}")
    } else {
        print("Пропуск null")
    }
}
```

Фильтрация null значений:

```efen
let numbers: [Int?] = [1, 2, null, 4, null, 6]
let validNumbers = numbers.compactMap => number  // [1, 2, 4, 6]
```

<a id="optional-массив"></a>

### Массив, который может отсутствовать

```efen
let optionalArray: [Int]? = [1, 2, 3]

if let array = optionalArray {
    for item in array {
        print(item)
    }
}
```

<a id="dictionary-с-optional-значениями"></a>

### Словарь со значениями, которые могут отсутствовать

```efen
var userAges: [String: Int?] = [
    "Alice": 25,
    "Bob": null,  // Возраст неизвестен
    "Charlie": 30
]

if let age = userAges["Alice"] {
    if let value = age {
        print("Alice: ${value} лет")
    } else {
        print("Возраст Alice неизвестен")
    }
}
```

<a id="optional-в-функциях"></a>

## Опциональные параметры и результаты функций

<a id="optional-параметры"></a>

### Параметры, допускающие отсутствие значения

```efen
fn greet(name: String?, title: String? = null) {
    let actualName = name ?? "Гость"
    if let title = title {
        print("Здравствуйте, ${title} ${actualName}")
    } else {
        print("Здравствуйте, ${actualName}")
    }
}

greet(name: "Иван")                    // "Здравствуйте, Иван"
greet(name: "Иван", title: "Доктор")   // "Здравствуйте, Доктор Иван"
greet(name: null)                      // "Здравствуйте, Гость"
```

<a id="optional-возвращаемое-значение"></a>

### Результат, который может отсутствовать

```efen
fn findFirst<T>(array: [T], predicate: (T) -> Bool) -> T? {
    for item in array {
        if predicate(item) {
            return item
        }
    }
    return null
}

let numbers = [1, 2, 3, 4, 5]
let firstEven = findFirst(array: numbers, predicate: (x) => x % 2 == 0)  // Int? = 2
let firstNegative = findFirst(array: numbers, predicate: (x) => x < 0)   // Int? = null
```

## Контекстное разворачивание через Coerce

Обычный `T?` сохраняет опциональный тип, когда контекст не требует другого:

```efen
let value = dictionary["key"]       // T?
let optional: T? = dictionary["key"]
```

Если связывание, параметр вызова или результат функции явно требует `T`,
компилятор ищет одну прямую стратегию `Coerce<T?>` для целевого `T`.
Стандартная стратегия называется `OptionalOrThrow<T>`:

```efen
let required: T = dictionary["key"]
// OptionalOrThrow<T>.coerce(dictionary["key"])
```

Отсутствующее значение бросает `NullUnwrapError`. Этот эффект участвует в
обычном выводе `throws`. Точное совпадение `T?` имеет приоритет, цепочки преобразований
не строятся, а без ожидаемого типа разворачивание не выполняется.

## Поле, заполняемое после конструктора

Отдельного типа с неявным извлечением значения `T!` в Efen нет. Поле, которое появляется
позже конструктора, объявляется данными состояния
[состояния типов](typestate.md): до перехода обращение к нему — ошибка компиляции.

```efen
class OrderService {
    state Setup {
        initial Unconfigured
        Configured
    }

    let repository: Repository {
        state Setup.Configured
    }

    fn setup(repo: Repository) state Setup.Unconfigured >> Setup.Configured {
        repository = repo
    }

    fn load(id: Int) -> Order state Setup.Configured {
        return repository.find(id)
    }
}
```

<a id="optional-map-и-flatmap"></a>

## Преобразования через `map` и `flatMap`

### Map

Метод `map` преобразует присутствующее значение, сохраняя возможность его отсутствия:

```efen
let optionalNumber: Int? = 42
let doubled = optionalNumber.map => value * 2  // Int? = 84

let empty: Int? = null
let result = empty.map => value * 2  // Int? = null
```

### FlatMap

Если функция сама возвращает опциональный тип, `flatMap` не добавляет
ещё один уровень вложенности:

```efen
let optionalString: String? = "42"
let number = optionalString.flatMap => parseInt(value)  // Int?

// Без flatMap получили бы Option<Int?>
let nested = optionalString.map => parseInt(value)  // Option<Int?>: вложенный опциональный тип
```

## Лучшие практики

<a id="1-предпочитайте-optional-binding"></a>

### 1. Предпочитайте Проверка и извлечение значения

❌ **Плохо:**
```efen
if user != null {
    print(user!.name)  // Forced unwrap опасен
}
```

✅ **Хорошо:**
```efen
if let user = user {
    print(user.name)  // Безопасно
}
```

### 2. Используйте Guard для ранних выходов

❌ **Плохо:**
```efen
fn process(data: Data?) {
    if data != null {
        // Вся логика вложена
        let d = data!
        // ... много кода
    }
}
```

✅ **Хорошо:**
```efen
fn process(data: Data?) {
    guard let data = data else {
        return
    }

    // Логика на верхнем уровне
    // ... много кода
}
```

### 3. Используйте ?? для значений по умолчанию

❌ **Плохо:**
```efen
let name: String
if let optionalName = optionalName {
    name = optionalName
} else {
    name = "Unknown"
}
```

✅ **Хорошо:**
```efen
let name = optionalName ?? "Unknown"
```

### 4. Избегайте Forced Unwrapping (!)

❌ **Опасно:**
```efen
let value = optionalValue!  // Может упасть!
```

✅ **Безопасно:**
```efen
if let value = optionalValue {
    // Используем value
}
```

<a id="5-используйте-optional-chaining"></a>

### 5. Используйте Цепочка обращений с проверкой `null`

❌ **Плохо:**
```efen
if let person = optionalPerson {
    if let address = person.address {
        if let city = address.city {
            print(city)
        }
    }
}
```

✅ **Хорошо:**
```efen
if let city = optionalPerson?.address?.city {
    print(city)
}
```

<a id="6-не-злоупотребляйте-optional"></a>

### 6. Указывайте возможность отсутствия только там, где она нужна

❌ **Плохо:**
```efen
fn calculateArea(width: Int?, height: Int?) -> Int? {
    // Слишком много optional!
}
```

✅ **Лучше:**
```efen
fn calculateArea(width: Int, height: Int) -> Int {
    return width * height
}

// Optional только если действительно может отсутствовать
fn findArea(shape: Shape?) -> Int? {
    guard let shape = shape else { return null }
    return shape.width * shape.height
}
```

## Внутреннее представление

Тип `T?` описывает значение типа `T`, которое может отсутствовать.
`Option<T>` — стандартный псевдоним этого же типа.

Способ хранения `T?` в памяти задаётся в типе и может зависеть от целевой платформы.
Отдельный признак наличия значения нужен не всегда: иногда отсутствие можно
обозначить неиспользуемым значением в представлении `T`. Генератор кода
соблюдает заданные типом правила хранения. При любом способе хранения значение и его
отсутствие должны оставаться различимыми.

```efen
let value: Int? = 42
let empty: Int? = null
```

Для вложенного типа `Option<Option<T>>` представление в памяти должно
различать три случая: внешнее значение отсутствует; внешнее значение есть,
но внутреннее равно `null`; оба уровня присутствуют и содержат значение `T`.

### Если внешнее значение — указатель

[Класс над внешним значением](../classes.md#класс-над-внешним-значением)
может хранить указатель из библиотеки C. Для такого типа представление
отсутствующего значения — нулевой указатель C (`NULL`). Это правило хранения
для конкретной группы типов: само значение `null` в Efen от этого не становится
указателем или числом `0`. Отдельный признак наличия значения не нужен:
`T?` занимает столько же памяти, сколько сам указатель.

Это правило действует для класса с `@abi(c)`, если у него нет `@c` либо
`@c` задаёт указательный тип C. Оно уже определено языком; объявлять для
такого класса `type Option<T> { … }` нельзя.

Если параметр `mut T?` позволяет функции C записать указатель в переменную
вызывающего, в C передаётся адрес этой переменной. Для указательного типа
`T*` соответствующий параметр C имеет тип `T**`.

### Если внешнее значение — целое число

Некоторые библиотеки C обозначают отсутствие ресурса специальным числом.
Например, допустимые дескрипторы файлов неотрицательны, а `-1` означает,
что дескриптора нет.

Модуль типа `T` может описать такое правило для `T?`:

```efen
type Option<T> {
    representation Raw<I>
    null: c
}
```

Здесь `I` — целый тип, в котором хранится внешнее значение, а `c` — число,
обозначающее его отсутствие. Это может быть базовый целый тип, на который
наложено ограничение, или целый тип, названный через `typedef` в C.

Компилятор проверяет, что `c` не является допустимым значением `T`:
подставляет его в условие типа и требует результат `false`. Поэтому обычное
значение нельзя спутать с отсутствующим. Допустимые условия описаны
в разделе [«Фрагмент сравнений»](refinement-types.md#фрагмент-сравнений).

Например, если класс `File` хранит дескриптор типа `Descriptor`, модуль
может выбрать такое представление:

```efen
type Descriptor: Int32 { value >= 0 }

@platform(os: "linux")
public type Option<File> {
    representation Raw<Int32>
    null: -1
}

var fds: [File?] = [null, null]
```

Здесь каждый элемент `fds` хранится как одно число `Int32`. Оба элемента
содержат `-1`, то есть ни один из них пока не содержит файл.

Пометка `@platform` позволяет задать разные правила для разных платформ.
Если такое представление не объявлено, используется обычное хранение
с отдельным признаком наличия значения. Этот признак также называют тегом.

Объявление `type Option<T> { … }` задаёт только способ хранения уже
существующего типа. Новый самостоятельный тип при этом не создаётся:
`T?` и `Option<T>` остаются одним типом.

<a id="как-хранится-вложенный-optional"></a>

### Как хранится вложенный опциональный тип

У `Option<T?>` два уровня, поэтому одного обозначения `null` недостаточно.
Нужно различать три случая:

| Состояние | Как оно хранится |
|---|---|
| Внешнее значение отсутствует | Отдельный признак внешнего уровня указывает на отсутствие |
| Внешнее значение есть, внутреннее отсутствует | Внешний уровень отмечен как присутствующий; внутри хранится `NULL` или специальное число |
| Оба значения присутствуют | Внешний уровень отмечен как присутствующий; внутри хранится обычное значение `T` |

Таким образом, если внутренний `T?` использует `NULL` или специальное число,
это обозначение относится только к внутреннему уровню. Для внешнего уровня
добавляется отдельный признак.

<a id="сравнение-optional"></a>

## Сравнение опциональных значений

```efen
let a: Int? = 42
let b: Int? = 42
let c: Int? = null

print(a == b)  // true
print(a == c)  // false
print(c == null)  // true
```

Сравнение с обычными значениями:

```efen
let optional: Int? = 42
print(optional == 42)  // true (автоматическое преобразование)
```

<a id="optional-и-generics"></a>

## Опциональные типы в обобщённом коде

Опциональный результат может зависеть от параметра типа:

```efen
fn findFirst<T>(array: [T], predicate: (T) -> Bool) -> T? {
    for item in array {
        if predicate(item) {
            return item
        }
    }
    return null
}

fn findLast<T>(array: [T], predicate: (T) -> Bool) -> T? {
    for item in array.reversed() {
        if predicate(item) {
            return item
        }
    }
    return null
}
```

<a id="ошибки-и-optional"></a>

## Отсутствие значения и ошибки

Опциональный тип используется для простых случаев отсутствия значения.
Для ошибок используйте [Result<T, E>](variant.md) или [throws](../throws.md):

```efen
// ✅ Optional - для простого отсутствия значения
fn findUser(id: Int) -> User? {
    return database.find(id)  // Может не найти
}

// ✅ Result - для операций с возможными ошибками
fn loadUser(id: Int) -> Result<User, DatabaseError> {
    // ...
}

// ✅ Throws - для исключительных ситуаций
fn loadUser(id: Int) -> User throws DatabaseError {
    // ...
}
```

## См. также

| Продолжить чтение | Что описано |
|---|---|
| [Проверка через `if let`](../blocks/if.md) | Как выполнить код, если значение присутствует |
| [Ранний выход через `guard let`](../blocks/guard.md) | Как завершить обработку, если значения нет |
| [Сопоставление с образцом](../blocks/match.md) | Как разобрать случаи наличия и отсутствия значения |
| [Вариантные типы: `variant`](variant.md) | `Result<T, E>` и другие типы с именованными вариантами, каждый из которых может хранить свои данные |
| [Перечисления: `enum`](enum.md) | Конечный набор именованных значений без дополнительных данных у каждого значения |
| [Обработка исключений](../throws.md) | Как сообщать об ошибках через `throws` и обрабатывать их |
