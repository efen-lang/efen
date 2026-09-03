# Optional Types (Опциональные типы)

Optional типы в Efen позволяют явно выражать отсутствие значения, делая код более безопасным и предсказуемым.
Заимствуя идеи из Swift, Efen предоставляет мощный и выразительный синтаксис для работы с опциональными значениями.

## Что такое Optional?

Optional — это тип, который может содержать либо значение определенного типа, либо отсутствие значения (`null`).

```efen
var optionalInt: Int? = 42        // Содержит значение
var emptyOptional: Int? = null    // Отсутствие значения
```

### Синтаксис

Для объявления optional типа используется символ `?` после имени типа:

```efen
let name: String?           // Optional<String>
let age: Int?               // Optional<Int>
let values: [Int]?          // Optional<Array<Int>>
let callback: ((Int) -> Void)?  // Optional<Function>
```

## Зачем нужны Optional?

### Проблема null в других языках

В языках без optional типов (C, C++, Java до версии 8, старый PHP) `null` может появиться где угодно:

```php
// PHP: функция может вернуть null, но это не видно в сигнатуре
function findUser(int $id): User {
    // ...может вернуть null!
    return null;  // Runtime ошибка позже
}

$user = findUser(123);
echo $user->name;  // CRASH если null!
```

### Решение через Optional

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

## Создание Optional значений

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

## Работа с Optional значениями

### 1. Optional Binding (if let)

Самый безопасный способ извлечь значение:

```efen
let optionalName: String? = "Иван"

if let name = optionalName {
    print("Привет, \(name)!")  // name имеет тип String
} else {
    print("Имя не указано")
}
```

Множественное binding:

```efen
let optionalName: String? = "Иван"
let optionalAge: Int? = 25

if let name = optionalName, let age = optionalAge {
    print("\(name), возраст: \(age)")
} else {
    print("Недостаточно данных")
}
```

С дополнительными условиями:

```efen
if let age = optionalAge, age >= 18 {
    print("Совершеннолетний: \(age) лет")
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
    print("Привет, \(name)!")
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

### 4. Optional Chaining

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

Вызов методов через optional chaining:

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

⚠️ **Использовать осторожно!** Приводит к runtime ошибке если значение null.

```efen
let optionalNumber: Int? = 42
let number = optionalNumber!  // Int = 42

let empty: Int? = null
let crash = empty!  // ❌ RUNTIME CRASH!
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

## Optional в switch

Pattern matching с optional:

```efen
let optionalNumber: Int? = 42

switch optionalNumber {
case null:
    print("Значение отсутствует")
case let value?:
    print("Значение: \(value)")
}
```

С дополнительными условиями:

```efen
switch optionalNumber {
case null:
    print("Нет значения")
case let value? where value > 0:
    print("Положительное: \(value)")
case let value? where value < 0:
    print("Отрицательное: \(value)")
case 0?:
    print("Ноль")
default:
    print("Другое")
}
```

## Optional в коллекциях

### Массив optional значений

```efen
let numbers: [Int?] = [1, 2, null, 4, null, 6]

for number in numbers {
    if let value = number {
        print("Значение: \(value)")
    } else {
        print("Пропуск null")
    }
}
```

Фильтрация null значений:

```efen
let numbers: [Int?] = [1, 2, null, 4, null, 6]
let validNumbers = numbers.compactMap { $0 }  // [1, 2, 4, 6]
```

### Optional массив

```efen
let optionalArray: [Int]? = [1, 2, 3]

if let array = optionalArray {
    for item in array {
        print(item)
    }
}
```

### Dictionary с optional значениями

```efen
var userAges: [String: Int?] = [
    "Alice": 25,
    "Bob": null,  // Возраст неизвестен
    "Charlie": 30
]

if let age = userAges["Alice"] {
    if let value = age {
        print("Alice: \(value) лет")
    } else {
        print("Возраст Alice неизвестен")
    }
}
```

## Optional в функциях

### Optional параметры

```efen
fn greet(name: String?, title: String? = null) {
    let actualName = name ?? "Гость"
    if let title = title {
        print("Здравствуйте, \(title) \(actualName)")
    } else {
        print("Здравствуйте, \(actualName)")
    }
}

greet(name: "Иван")                    // "Здравствуйте, Иван"
greet(name: "Иван", title: "Доктор")   // "Здравствуйте, Доктор Иван"
greet(name: null)                      // "Здравствуйте, Гость"
```

### Optional возвращаемое значение

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
let firstEven = findFirst(array: numbers) { $0 % 2 == 0 }  // Int? = 2
let firstNegative = findFirst(array: numbers) { $0 < 0 }   // Int? = null
```

## Implicitly Unwrapped Optional (!)

Тип, который автоматически разворачивается, но может быть null:

```efen
var optionalValue: Int! = 42

// Автоматически разворачивается
let value: Int = optionalValue  // Не нужен !, но опасно если null!

// Можно присвоить null
optionalValue = null

// Теперь это вызовет runtime ошибку
let crash = optionalValue  // ❌ CRASH!
```

**Когда использовать:**
- Редко! Только для особых случаев
- Когда значение будет null только кратковременно
- Типичный пример: lazy свойства, dependency injection

```efen
class ViewController {
    var view: View!  // Будет инициализировано в viewDidLoad

    fn viewDidLoad() {
        self.view = View()  // Гарантированно установлено после загрузки
    }

    fn updateUI() {
        view.backgroundColor = .white  // Безопасно, view уже инициализирован
    }
}
```

## Optional Map и FlatMap

### Map

Преобразование значения внутри optional:

```efen
let optionalNumber: Int? = 42
let doubled = optionalNumber.map { $0 * 2 }  // Int? = 84

let empty: Int? = null
let result = empty.map { $0 * 2 }  // Int? = null
```

### FlatMap

Для функций, возвращающих optional:

```efen
let optionalString: String? = "42"
let number = optionalString.flatMap { parseInt($0) }  // Int?

// Без flatMap получили бы Int??
let nested = optionalString.map { parseInt($0) }  // Int?? (nested optional!)
```

## Лучшие практики

### 1. Предпочитайте Optional Binding

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

### 5. Используйте Optional Chaining

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

### 6. Не злоупотребляйте Optional

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

Optional — это enum с двумя вариантами:

```efen
enum Optional<T> {
    some: T
    none
}
```

Синтаксис `T?` — это синтаксический сахар для `Optional<T>`.

```efen
let value1: Int? = 42
let value2: Optional<Int> = .some(42)  // Эквивалентно

let empty1: Int? = null
let empty2: Optional<Int> = .none  // Эквивалентно
```

## Сравнение Optional

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

## Optional и Generics

Optional часто используется с generic функциями:

```efen
fn findFirst<T>(array: [T], where predicate: (T) -> Bool) -> T? {
    for item in array {
        if predicate(item) {
            return item
        }
    }
    return null
}

fn findLast<T>(array: [T], where predicate: (T) -> Bool) -> T? {
    for item in array.reversed() {
        if predicate(item) {
            return item
        }
    }
    return null
}
```

## Ошибки и Optional

Optional часто используется для простых случаев отсутствия значения.
Для ошибок используйте [Result<T, E>](enum.md) или [throws](../throws.md):

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
fn loadUser(id: Int) throws -> User {
    // ...
}
```

## См. также

- [enum.md](enum.md) — Optional реализован как enum
- [../blocks/if.md](../blocks/if.md) — Optional binding с if let
- [../blocks/guard.md](../blocks/guard.md) — Guard let для optional
- [../blocks/switch.md](../blocks/switch.md) — Pattern matching с optional
- [../throws.md](../throws.md) — Обработка ошибок
