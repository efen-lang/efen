# Замыкания

`Efen` поддерживает замыкания (closures) — анонимные функции,
которые могут захватывать переменные из окружающей области видимости.
Замыкания являются функциями первого класса и могут быть присвоены переменным,
переданы как аргументы или возвращены из других функций.

## Синтаксис замыканий

Полная форма замыкания с указанием типов параметров и возвращаемого значения:

```efen
var closure = (param1: Int, param2: Int) -> Int { return param1 + param2 }
```

Литерал замыкания с блоком пишется без `=>`; `->` здесь задаёт тип результата.
Знак `=>` обязателен в двух случаях: когда телом замыкания служит голое выражение
и когда замыкание передаётся хвостовым аргументом после вызова.

Замыкание как возвращаемый тип функции:

```efen
fn getClosure -> (Int, Int) -> Int {
    return => return param1 + param2
}
```

Альтернативный синтаксис с параметрами в теле замыкания:

```efen
var closure => {
    param1: Int, param2: Int
    return param1 + param2
}
```

Сокращённая форма замыкания без указания типов (типы выводятся компилятором):

```efen
var closure = (param1, param2) => param1 + param2
```

Сокращённая формат без параметров (замыкание без аргументов):

```efen
var closure => x + 1
```

## Короткий синтаксис замыканий (Closure Short Syntax)

Efen поддерживает несколько форм сокращённого синтаксиса для замыканий,
что делает код более лаконичным и читаемым.

### Оператор `=>` для trailing closures

Использование оператора `=>` для определения замыкания как параметра метода:

```efen
var y = array.map => $0 + 1
var natural = [-100..100].filter => $0 >= 0
```

**ВАЖНО**: Синтаксис `method { body }` ЗАПРЕЩЁН из-за неоднозначности.
Всегда используйте `=>` для однозначности:

```efen
// ❌ ЗАПРЕЩЕНО - неоднозначный синтаксис
numbers.map { $0 * 2 }

// ✅ ПРАВИЛЬНО - однозначный синтаксис
numbers.map => $0 * 2
numbers.map => { $0 * 2 }
```

Вызов с цепочкой методов с замыканиями:
```efen
var result = data.filter => $0 > 0
            .map => $0 * 2
            .reduce(0) => $0 + $1
```

### Перенос строк

Тело замыкания после `=>` без фигурных скобок кончается на конце строки;
многострочное тело записывается только в `{ }`. Перенос сразу после `=>` смысл
не меняет, но получает диагностику стиля `S`: тело начинается на строке
стрелки. Общие правила — [перенос строк](operators.md#перенос-строк).

Тело в `{ }` кончается на своей закрывающей скобке, поэтому постфикс после `}`
относится к вызову, а не к телу: в `numbers.map => { $0 * 2 }.collect()` метод `collect` вызывается у результата
`map`.

Строка, начинающаяся с `.` или с бинарного оператора, продолжает выражение
предыдущей строки — и присоединяется к нему целиком, а не к последнему операнду:

```efen
let x = a + b
    .foo()
// разбирается как (a + b).foo()
```

Поэтому цепочка выше разбирается как одно выражение, а каждое `=>` захватывает
ровно свою строку:

```efen
var result = data.filter => $0 > 0   // тело замыкания кончается здесь
            .map => $0 * 2           // строка начинается с `.` — продолжение
            .reduce(0) => $0 + $1

// Многострочное тело требует скобок
var filtered = data.filter => {
    let normalized = normalize($0)
    normalized > 0
}
```

### Placeholder-параметры

Efen поддерживает placeholder-параметры для сокращённой записи замыканий:
- `$` — безымянный placeholder (для одного параметра)
- `$0`, `$1`, `$2`, ... — нумерованные placeholders
- `$name` — именованные placeholders

**Правила использования placeholder-параметров**:

1. **Один параметр**: placeholder может называться как угодно
   ```efen
   numbers.map => $ * 2         // $ - первый параметр
   numbers.map => $0 * 2        // $0 - первый параметр
   numbers.map => $item * 2     // $item - первый параметр
   ```

2. **Несколько параметров**: placeholder ОБЯЗАН совпадать с именем параметра
   ```efen
   // Если функция принимает (accumulator, current)
   numbers.reduce(0) => $accumulator + $current

   // Или используйте нумерованные placeholders
   numbers.reduce(0) => $0 + $1
   ```

Примеры использования:
```efen
// Простое преобразование
let doubled = [1, 2, 3].map => $0 * 2       // [2, 4, 6]

// Фильтрация
let positive = [-1, 2, -3, 4].filter => $0 > 0  // [2, 4]

// Reduce с двумя параметрами
let sum = [1, 2, 3, 4].reduce(0) => $0 + $1     // 10
```

Замыкание в качестве аргумента метода:
```efen
object.method({
    тело_функции
}, другие_аргументы)

// или с параметрами
object.method((param1, param2) -> Type {
    тело_функции
}, другие_аргументы)
```

## Примеры использования

Простое замыкание с одним выражением:
```efen
let add = (a: Int, b: Int) => a + b
let result = add(5, 3)  // 8
```

Замыкание с блоком кода:
```efen
let greet = (name: String) -> String {
    let greeting = "Hello, ${name}!"
    print(greeting)
    return greeting
}
```

Замыкание без параметров:
```efen
let getRandomNumber => {
    return 42
}
```

Использование замыканий как аргументов функций:
```efen
fn processArray(arr: Array<Int>, transform: (Int) -> Int) -> Array<Int> {
    let result = []
    for item in arr {
        result[] = transform(item)
    }
    return result
}

let numbers = [1, 2, 3, 4, 5]
let doubled = processArray(numbers, (x) => x * 2)  // [2, 4, 6, 8, 10]
```

## Захват переменных

Замыкание видит переменные окружающей области. Имя внешней переменной в теле
захватывает её заимствованием; право `read` или `write` выводится из того, что
тело с ней делает, как у параметра:

```efen
let total = items.map => $0 * factor     // read-заимствование factor
items.forEach => sum += $0               // write-заимствование sum
```

Заимствование не продлевает жизнь переменной. Замыкание, которое переживает её
область, с заимствованием не компилируется:

```efen
fn makeCounter -> () -> Int {
    var count = 0
    return => {
        count += 1                       // ошибка: заимствование count выходит за его origin
        return count
    }
}
```

### Объявление `capture`

Чтобы замыкание владело значением, оно объявляет захват в начале тела, после
`generic` и `param`:

```efen
fn makeCounter -> () -> Int {
    var count = 0
    return => {
        capture var count = take count
        count += 1
        return count
    }
}
```

`capture имя = выражение` создаёт поле окружения замыкания. Справа стоит любое
выражение, результат которого принадлежит замыканию:

```efen
let report => {
    capture connection = take connection   // перенос
    capture factor = factor.copy()         // копия
    capture total = a + b                  // новое значение
    connection.send(factor * total)
}
```

Правила объявления:

- поле неизменяемо; изменяемое поле объявляется `capture var`. Форма
  `capture let` получает диагностику стиля `S`;
- выражение вычисляется один раз, при создании замыкания, а не при вызове;
- имена в выражении разрешаются в области, окружающей литерал замыкания:
  `param`, `generic`, `$0` и предыдущие `capture` в нём не видны; совпадение
  имени `capture` с именем `param` — ошибка;
- результат обязан быть владением: `capture items = items` для типа без
  `ImplicitlyCopyable` даёт заимствование и является ошибкой с подсказкой
  `take items` или `items.copy()`;
- захваты инициализируются в порядке объявления. Если выражение бросает
  исключение, уже созданные поля освобождаются в обратном порядке, а
  перенесённые значения остаются перенесёнными. Исключение принадлежит функции,
  создающей замыкание, а не типу замыкания.

Генератор и `spawn` вычисляют `capture` при создании, синхронно; `await` и `<-`
в выражении захвата запрещены.

### Захват контекста

Контекст — скрытый параметр функции, поэтому `%name` в теле замыкания
заимствует активный контекст. Чтобы замыкание владело контекстом, объявление
`capture in` делает значение активным контекстом своего тела:

```efen
fn process in Environment {
    spawn {
        capture connection = take connection
        capture in Environment = Environment.copy()
        %logger.log("sent")                // поле захваченной копии
        connection.send(message)
    }
}
```

Задача `spawn` может пережить область создания, поэтому все её захваты —
владения; заимствование в теле `spawn` является ошибкой компиляции.

## Права вызова замыкания

Замыкание является значением анонимного конкретного типа. Его окружение хранит
захваченные значения и ссылки так же, как поля обычной структуры. Требуемое
право на вызов компилятор выводит из операций тела над этим окружением:

- тело, которое только читает захваты, можно вызывать через `read`;
- тело, которое изменяет захваты, но не извлекает их, требует `write`;
- тело, которое через `take` извлекает хотя бы один захват, требует `own` и
  потребляет всё значение замыкания.

Режим определяется тем, что тело делает с захватами, а не самим фактом захвата
по значению. Замыкание может владеть значением и оставаться повторно вызываемым,
если тело это значение только читает.

Потребляющий вызов явно передаёт замыкание через `take`:

```efen
fn send {
    param connection: Connection own
}

fn makeTask -> () -> Void {
    let connection: Connection = connect()

    return => {
        capture connection = take connection
        send(take connection)
    }
}

let task = makeTask()
(take task)()
// task() // ошибка: значение task уже передано
```

`capture connection = take connection` передаёт локальное значение в окружение
создаваемого замыкания. Внутренний `take connection` определяет семантику тела:
при вызове это поле покидает окружение. Внешний `(take task)()` передаёт вызову
само окружение целиком. Даже если тело извлекает только одно его поле, повторно
вызывать частично опустошённое замыкание нельзя. Для `let` имя после вызова
остаётся недействительным; `var` можно снова использовать после присваивания
нового замыкания подходящего типа.

Эта модель соответствует логике `Fn`/`FnMut`/`FnOnce` в Rust, но не вводит в
Efen три отдельных встроенных contract: различие выражается существующими
правами `read`, `write` и `own`.

## Escaping и Non-Escaping замыкания

### Non-Escaping замыкания

По умолчанию замыкания являются non-escaping — они не могут пережить вызов функции:

```efen
fn processData(data: [Int], transform: (Int) -> Int) -> [Int] {
    return data.map(transform)  // transform используется только внутри функции
}

let numbers = [1, 2, 3]
let doubled = processData(data: numbers, transform: (x) => x * 2)
```

### Escaping замыкания

Если замыкание сохраняется для последующего использования, оно должно быть помечено как `@escaping`:

```efen
var callbacks: [(Int) -> Void] = []

fn registerCallback(callback: @escaping (Int) -> Void) {
    callbacks.append(callback)  // callback сохраняется за пределами функции
}

fn executeCallbacks(value: Int) {
    for callback in callbacks {
        callback(value)
    }
}

registerCallback => {
    print("Callback 1: ${$0}")
}

registerCallback => {
    print("Callback 2: ${$0}")
}

executeCallbacks(value: 42)
// Callback 1: 42
// Callback 2: 42
```

## Автозамыкания (Autoclosure)

Автозамыкание автоматически оборачивает выражение в замыкание без параметров:

```efen
fn assert(_ condition: @autoclosure () -> Bool, message: String) {
    if !condition() {
        print("Assertion failed: ${message}")
    }
}

// Использование
let x = 5
assert(x > 0, message: "x must be positive")  // x > 0 автоматически завёрнут в замыкание
```

Без `@autoclosure` пришлось бы писать:

```efen
assert({ x > 0 }, message: "x must be positive")
```

## Замыкания в коллекциях

### map — преобразование элементов

```efen
let numbers = [1, 2, 3, 4, 5]
let squared = numbers.map => $0 * $0
print(squared)  // [1, 4, 9, 16, 25]
```

### filter — фильтрация элементов

```efen
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let evenNumbers = numbers.filter => $0 % 2 == 0
print(evenNumbers)  // [2, 4, 6, 8, 10]
```

### reduce — свёртка коллекции

```efen
let numbers = [1, 2, 3, 4, 5]
let sum = numbers.reduce(0) => $0 + $1
print(sum)  // 15

let product = numbers.reduce(1) => $0 * $1
print(product)  // 120
```

### sorted — сортировка

```efen
let names = ["Иван", "Алексей", "Мария", "Анна"]
let sorted = names.sorted => $0 < $1
print(sorted)  // ["Алексей", "Анна", "Иван", "Мария"]
```

### forEach — выполнение действия

```efen
let numbers = [1, 2, 3, 4, 5]
numbers.forEach => {
    print("Number: ${$0}")
}
```

## Замыкания с несколькими параметрами

```efen
let combine = (a: Int, b: Int, operation: String) -> Int {
    return match operation {
        "+": a + b
        "-": a - b
        "*": a * b
        "/": a / b
        _: 0
    }
}

print(combine(10, 5, "+"))  // 15
print(combine(10, 5, "*"))  // 50
```

## Замыкания, возвращающие замыкания

```efen
fn makeAdder(increment: Int) -> (Int) -> Int {
    return (value: Int) => value + increment
}

let addFive = makeAdder(increment: 5)
let addTen = makeAdder(increment: 10)

print(addFive(3))   // 8
print(addTen(3))    // 13
```

## Trailing Closure Syntax

Trailing closure позволяет передать замыкание как последний аргумент функции
с использованием оператора `=>`:

```efen
// Обычный синтаксис
numbers.map((x: Int) => x * 2)

// Trailing closure с выражением
numbers.map => $0 * 2

// Trailing closure с блоком
numbers.map => {
    return $0 * 2
}

// Trailing closure после других аргументов
numbers.reduce(0) => $0 + $1
```

**Важные замечания**:
- Оператор `=>` ОБЯЗАТЕЛЕН для trailing closures
- Синтаксис без `=>` (например `method { body }`) ЗАПРЕЩЁН из-за неоднозначности
- Можно использовать как с выражениями, так и с блоками кода

Для функций с несколькими замыканиями:

```efen
func loadData(onSuccess: (Data) -> Void, onError: (Error) -> Void) {
    // ...
}

// Trailing closure для последнего параметра
loadData(onSuccess: (data) => {
    print("Success: ${data}")
}) => {
    print("Error: ${$0}")
}
```

## Рекурсивные замыкания

Для создания рекурсивных замыканий используйте явное объявление типа:

```efen
var factorial: (Int) -> Int
factorial = (n: Int) -> Int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

print(factorial(5))  // 120
```

## Лучшие практики

### 1. Используйте сокращённый синтаксис когда уместно

```efen
// ❌ Излишне многословно
numbers.map => {
    return $0 * 2
}

// ✅ Лаконично
numbers.map => $0 * 2
```

### 2. Используйте правильный синтаксис trailing closures

```efen
// ❌ ЗАПРЕЩЕНО - неоднозначный синтаксис
numbers.map { $0 * 2 }

// ✅ ПРАВИЛЬНО - используйте оператор =>
numbers.map => $0 * 2
```

### 3. Именуйте параметры для сложной логики

```efen
// ❌ Неясно с placeholders
users.filter => $0.age > 18 && $0.isActive && !$0.isBanned

// ✅ Понятно с явными параметрами
users.filter((user) => user.age > 18 && user.isActive && !user.isBanned)
```

### 4. Избегайте retain cycles

```efen
class ViewController {
    var onComplete: (() -> Void)?

    func setup {
        // ❌ Retain cycle
        onComplete = {
            self.dismiss()
        }

        // ✅ Слабая ссылка
        onComplete = { [weak self] in
            self?.dismiss()
        }
    }
}
```

### 5. Используйте @autoclosure для ленивого вычисления

```efen
fn log(_ message: @autoclosure () -> String, level: LogLevel) {
    if level >= currentLogLevel {
        print(message())  // Вычисляется только при необходимости
    }
}

// Дорогое вычисление message() выполнится только если уровень логирования подходит
log("User data: ${fetchExpensiveUserData()}", level: .debug)
```

### 6. Предпочитайте non-escaping когда возможно

```efen
// ✅ Non-escaping по умолчанию — быстрее
fn process(data: [Int], transform: (Int) -> Int) -> [Int] {
    return data.map(transform)
}

// ⚠️ Escaping только когда необходимо
fn asyncProcess(completion: @escaping () -> Void) {
    DispatchQueue.main.async {
        completion()
    }
}
```

## Замыкания и память

### Захват self

```efen
class NetworkManager {
    var requests: [() -> Void] = []

    func addRequest(_ request: @escaping () -> Void) {
        requests.append(request)
    }

    func processData {
        addRequest { [weak self] in
            guard let self = self else { return }
            self.performTask()
        }
    }

    func performTask {
        print("Task performed")
    }
}
```

### Unowned vs Weak

```efen
class Parent {
    var child: Child?
}

class Child {
    // Используйте unowned если объект всегда существует
    unowned let parent: Parent

    // Используйте weak если объект может быть nil
    weak var optionalParent: Parent?

    init(parent: Parent) {
        self.parent = parent
    }

    func doSomething {
        parent.someMethod()  // Безопасно с unowned
        optionalParent?.someMethod()  // Безопасно с weak
    }
}
```

## Производительность

### Inline-оптимизация

Компилятор может встраивать (inline) простые замыкания:

```efen
// ✅ Часто инлайнится
let doubled = numbers.map => $0 * 2

// ⚠️ Сложнее инлайнить
let processed = numbers.map((value) => {
    if value > 10 {
        return value * 2
    } else {
        return value / 2
    }
})
```

### Избегайте захвата больших объектов

```efen
// ❌ Захватывает весь массив
var largeArray = [1..1000000]
let closure = () => largeArray.count

// ✅ Захватывает только нужное значение
let count = largeArray.count
let closure = () => count
```

## См. также

- [functions.md](functions.md) — Функции в Efen
- [types/function-type.md](types/function-type.md) — Функциональные типы
- [classes.md](classes.md) — Классы и методы
