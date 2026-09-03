# Словари (Dictionary)

> Словарь (Dictionary) — это коллекция пар ключ-значение, где каждый ключ уникален и связан с конкретным значением.

Словари позволяют эффективно хранить и извлекать данные по ключу.

## Синтаксис литералов словаря

Для создания словаря используется синтаксис `[key: value]` с парами ключ-значение, разделёнными запятыми.

### Базовый синтаксис

```efen
let ages = ["Alice": 25, "Bob": 30, "Charlie": 35]
let scores = ["Alice": 95, "Bob": 87, "Charlie": 92]
```

### Типы ключей

Словари могут использовать различные типы в качестве ключей:

```efen
// Строковые ключи
let names = ["first": "John", "last": "Doe"]

// Числовые ключи
let months = [1: "January", 2: "February", 3: "March"]

// Смешанные типы значений (требуется явное указание типа)
let mixed = [1: "one", 2: "two", 3: "three"]
```

### Пустой словарь

Для создания пустого словаря используется специальный синтаксис `[:]`:

```efen
let emptyDict = [:]
```

При создании пустого словаря обычно требуется указать тип:

```efen
let emptyNames: [String: String] = [:]
let emptyScores: [String: Int] = [:]
```

## Trailing Commas (Запятая после последнего элемента)

В Efen разрешено использовать запятую после последнего элемента словаря. 
Это современная практика, которая упрощает редактирование кода и делает git diffs чище.

```efen
let config = [
    "host": "localhost",
    "port": 8080,
    "timeout": 5000,  // ← trailing comma разрешена!
]

// Однострочный вариант (запятая необязательна)
let small = ["a": 1, "b": 2]
```

**Рекомендация:** Всегда используйте trailing comma в многострочных словарях.

## Вложенные словари

Словари могут содержать другие словари в качестве значений:

```efen
let users = [
    "alice": ["age": 25, "city": "Moscow"],
    "bob": ["age": 30, "city": "London"],
]
```

Более сложная структура с trailing commas:

```efen
let config = [
    "database": [
        "host": "localhost",
        "port": 5432,
        "name": "mydb",
    ],
    "cache": [
        "enabled": true,
        "ttl": 3600,
    ],
]
```

## Доступ к элементам

Для доступа к элементам словаря используется оператор индексирования `[]`:

```efen
let ages = ["Alice": 25, "Bob": 30]
let aliceAge = ages["Alice"]  // 25
```

### Безопасный доступ с optional chaining

Так как ключ может отсутствовать в словаре, рекомендуется использовать optional chaining:

```efen
let ages = ["Alice": 25, "Bob": 30]
let charlieAge = ages?["Charlie"]  // null, так как ключ не существует
```

## Изменение элементов

Для изменения существующих элементов или добавления новых используется оператор присваивания:

```efen
var ages = ["Alice": 25, "Bob": 30]

// Изменение существующего элемента
ages["Alice"] = 26

// Добавление нового элемента
ages["Charlie"] = 35
```

## Тип словаря

Тип словаря указывается в квадратных скобках с двоеточием между типом ключа и типом значения:

```efen
let names: [String: String] = ["first": "John", "last": "Doe"]
let scores: [String: Int] = ["Alice": 95, "Bob": 87]
let matrix: [Int: [Int: Float]] = [
    0: [0: 1.0, 1: 2.0],
    1: [0: 3.0, 1: 4.0]
]
```

## Примеры использования

### Конфигурация приложения

```efen
let config = [
    "app_name": "MyApp",
    "version": "1.0.0",
    "debug": true
]

echo "Application: ${config["app_name"]}"
echo "Version: ${config["version"]}"
```

### Перевод сообщений

```efen
let translations = [
    "hello": "Привет",
    "goodbye": "До свидания",
    "thanks": "Спасибо"
]

let greeting = translations["hello"]  // "Привет"
```

### Счётчик встречаемости

```efen
var wordCount = [:]
wordCount["hello"] = 3
wordCount["world"] = 5
wordCount["efen"] = 2
```

### HTTP заголовки

```efen
let headers = [
    "Content-Type": "application/json",
    "Authorization": "Bearer token123",
    "User-Agent": "Efen/1.0"
]
```

## Итерация по словарю

Для перебора элементов словаря используется цикл `for`:

```efen
let ages = ["Alice": 25, "Bob": 30, "Charlie": 35]

for (name, age) in ages {
    echo "${name} is ${age} years old"
}
```

Или только по ключам:

```efen
for name in ages.keys() {
    echo "Name: ${name}"
}
```

Или только по значениям:

```efen
for age in ages.values() {
    echo "Age: ${age}"
}
```

## Особенности

### Требования к ключам

Ключи словаря должны быть уникальными в рамках одного словаря. 
При попытке добавить дубликат ключа, предыдущее значение будет заменено:

```efen
let dict = ["key": 1, "key": 2]  // Результат: ["key": 2]
```

### Порядок элементов

В стандартной реализации словари не гарантируют порядок элементов. 
Если требуется сохранить порядок вставки, используется специальный тип `OrderedDictionary` из библиотеки.

### Производительность

Доступ к элементам по ключу имеет в среднем сложность O(1), что делает словари эффективными для поиска данных.

## Связь с массивами

Словарь можно рассматривать как обобщение массива, где вместо числовых индексов используются произвольные ключи:

```efen
// Массив - индексы от 0
let array = [10, 20, 30]
let first = array[0]  // 10

// Словарь - произвольные ключи
let dict = ["a": 10, "b": 20, "c": 30]
let value = dict["a"]  // 10
```

## Spread Operator

Оператор `...` позволяет распаковать содержимое одного словаря в другой. 
Это удобно для слияния словарей и создания копий с изменениями.

```efen
// Слияние словарей
let defaults = ["timeout": 30, "retries": 3]
let custom = ["timeout": 60, "verbose": true]
let config = [...defaults, ...custom]
// Результат: ["timeout": 60, "retries": 3, "verbose": true]

// Добавление новых ключей
let extended = [...config, "debug": true, "port": 8080]

// Порядок важен - правые значения перезаписывают левые
let merged = [...["a": 1], ...["a": 2, "b": 3]]
// Результат: ["a": 2, "b": 3]
```

### Null-aware Spread

Оператор `...?` безопасно распаковывает nullable словари:

```efen
let baseConfig = ["host": "localhost"]
let optionalConfig: [String: Any]? = null

// Без ошибки - null игнорируется
let config = [...baseConfig, ...?optionalConfig, "port": 8080]
// Результат: ["host": "localhost", "port": 8080]
```

## Merge Operator (Оператор слияния)

Оператор `+` предоставляет короткий синтаксис для слияния словарей:

```efen
// Слияние нескольких словарей
let merged = dict1 + dict2 + dict3

// Правый операнд перезаписывает левый при конфликте ключей
let result = ["a": 1, "b": 2] + ["b": 3, "c": 4]
// Результат: ["a": 1, "b": 3, "c": 4]

// Update operator (мутирующий)
var config = ["host": "localhost", "port": 8080]
config += ["port": 9000, "debug": true]
// config теперь: ["host": "localhost", "port": 9000, "debug": true]
```

**Выбор между `...` и `+`:**
- Используйте `...` для создания новых словарей с дополнительными литеральными ключами
- Используйте `+` для простого слияния существующих словарей

## Collection If/For (Условия и циклы в литералах)

Efen поддерживает уникальную возможность использовать условия и циклы прямо в литералах словарей. Это делает код более декларативным и читаемым.

### Collection If (Условные ключи)

```efen
let isDev = true
let hasAuth = true

let config = [
    "host": "localhost",
    "port": 8080,
    if (isDev) "debug": true,           // ← добавляется только если isDev == true
    if (hasAuth) "token": authToken,    // ← добавляется только если hasAuth == true
    if (isProd) "optimize": true,       // ← не добавится, если isProd == false
]
```

### Collection For (Генерация из циклов)

```efen
// Создание словаря из массива
let items = [1, 2, 3, 4, 5]
let squares = [
    for (i in items) i: i * i
]
// Результат: [1: 1, 2: 4, 3: 9, 4: 16, 5: 25]

// Преобразование массива объектов
let users = [
    ["id": 1, "name": "Alice"],
    ["id": 2, "name": "Bob"],
]
let userMap = [
    for (user in users) user["id"]: user["name"]
]
// Результат: [1: "Alice", 2: "Bob"]
```

### Комбинация If и For

```efen
// Фильтрация и преобразование за один проход
let data = [
    ["key": "a", "value": 10, "valid": true],
    ["key": "b", "value": 20, "valid": false],
    ["key": "c", "value": 30, "valid": true],
]

let filtered = [
    for (entry in data)
        if (entry["valid"])
            entry["key"]: entry["value"]
]
// Результат: ["a": 10, "c": 30]
```

**Примечание:** Вложенные collection if/for не поддерживаются для упрощения синтаксиса. Для сложных преобразований используйте обычные циклы и условия.

## Destructuring (Распаковка словарей)

Destructuring позволяет извлекать значения из словарей в отдельные переменные одним выражением.

### Базовый destructuring

```efen
let user = ["name": "John", "age": 30, "city": "NYC"]

// Извлечение значений
["name": name, "age": age] = user
echo "${name} is ${age} years old"
```

### С default значениями

```efen
let user = ["name": "John"]

// Если ключ отсутствует, используется default
["name": name, "age": age = 0, "city": city = "Unknown"] = user
// name = "John", age = 0, city = "Unknown"
```

### Rest operator (остальные элементы)

```efen
let user = ["id": 1, "name": "John", "age": 30, "city": "NYC"]

// Извлечь id, остальное в rest
["id": id, ...rest] = user
// id = 1, rest = ["name": "John", "age": 30, "city": "NYC"]
```

### Вложенный destructuring

```efen
let data = [
    "user": [
        "profile": [
            "email": "john@example.com",
            "phone": "+1234567890",
        ],
    ],
]

// Извлечение вложенных значений
["user": ["profile": ["email": email]]] = data
echo "Email: ${email}"
```

### В параметрах функций

```efen
// Destructuring в параметрах
function greet(["name": name, "age": age]) {
    echo "Hello ${name}, you are ${age} years old"
}

greet(["name": "Alice", "age": 25])
```

## Сравнительная таблица операторов

| Оператор             | Описание             | Пример                     | Результат               |
|----------------------|----------------------|----------------------------|-------------------------|
| `[:]`                | Пустой словарь       | `let d = [:]`              | `[:]`                   |
| `["k": v]`           | Литерал с элементами | `["a": 1, "b": 2]`         | `["a": 1, "b": 2]`      |
| `...dict`            | Spread operator      | `[...d1, ...d2]`           | Слияние словарей        |
| `...?dict`           | Null-aware spread    | `[...d1, ...?d2]`          | Слияние, игнорируя null |
| `d1 + d2`            | Merge operator       | `d1 + d2`                  | Слияние словарей        |
| `d1 += d2`           | Update operator      | `d1 += d2`                 | Обновление d1           |
| `if (cond) k: v`     | Условный ключ        | `if (isDev) "debug": true` | Добавить если true      |
| `for (x in xs) k: v` | Генерация            | `for (i in [1,2]) i: i*i`  | `[1: 1, 2: 4]`          |
| `["k": var]`         | Destructuring        | `["name": n] = user`       | Извлечь в переменную    |
| `...rest`            | Rest operator        | `["id": id, ...rest] = u`  | Остальные элементы      |

## Различия между `[]` и `[:]`

- `[]` — создаёт пустой массив
- `[:]` — создаёт пустой словарь
- `[1, 2, 3]` — массив с элементами
- `["a": 1, "b": 2]` — словарь с парами ключ-значение

```efen
let emptyArray = []           // Пустой массив
let emptyDict = [:]           // Пустой словарь
let array = [1, 2, 3]         // Массив
let dict = ["a": 1, "b": 2]   // Словарь
```
