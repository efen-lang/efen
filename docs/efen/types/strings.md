# Строки

Строки в `Efen` представляют собой последовательности Unicode-символов и используются для работы с текстовыми данными.

## Строковые литералы

### Обычные строки

Строки заключаются в двойные кавычки `"`:

```efen
let message = "Hello, World!"
let name = "Alice"
let greeting = "Привет, мир!"
```

### Символьные литералы

Одиночные символы заключаются в одинарные кавычки:

```efen
let ch: Char = 'A'
let letter = 'Ж'
let digit = '5'
```

## Интерполяция строк

В `Efen` интерполяция строк осуществляется с помощью синтаксиса `${expression}` внутри строковых литералов.

```efen
var name: String = "Мир"
var greeting: String = "Привет, ${name}!"
print(greeting) // Выведет: Привет, Мир!
```

Интерполяция позволяет вставлять значения переменных, результаты выражений и вызовы функций прямо в строку.

```efen
var a: Int = 5
var b: Int = 10
var result = "Сумма ${a} и ${b} равна ${a + b}."
print(result) // Выведет: Сумма 5 и 10 равна 15.
```

### Сложные выражения в интерполяции

```efen
let user = User { name: "Alice", age: 30 }
let info = "Пользователь ${user.name}, возраст ${user.age} лет"

let numbers = [1, 2, 3, 4, 5]
let total = "Сумма: ${numbers.sum()}"

// Многострочные выражения
let description = "Результат: ${
    let x = calculateValue()
    let y = processValue(x)
    formatResult(y)
}"
```

## Многострочные строки

Многострочные строковые литералы в `Efen` заключаются в тройные кавычки `"""`.

```efen
var multiLineString: String = """
Это многострочная
строка в Efen.
Она может содержать несколько
строк текста.
"""

print(multiLineString)
```

### Отступы в многострочных строках

Компилятор автоматически удаляет общий отступ:

```efen
let code = """
    function hello() {
        console.log("Hello");
    }
    """
// Общий отступ (4 пробела) будет удалён
```

### Интерполяция в многострочных строках

```efen
let name = "Alice"
let age = 30

let profile = """
    Имя: ${name}
    Возраст: ${age}
    Статус: активен
    """
```

## Экранирование символов

### Стандартные escape-последовательности

```efen
let newline = "Первая строка\nВторая строка"
let tab = "Колонка1\tКолонка2"
let quote = "Он сказал: \"Привет!\""
let backslash = "Путь: C:\\Users\\Name"
let carriageReturn = "Текст\rНовый текст"
```

### Специальные символы

```efen
let bell = "\a"          // Звуковой сигнал
let backspace = "\b"     // Возврат на символ
let formfeed = "\f"      // Перевод страницы
let null = "\0"          // Нулевой символ
```

### Unicode-последовательности

```efen
let smile = "\u{1F600}"        // 😀 (emoji)
let copyright = "\u{00A9}"     // ©
let euro = "\u{20AC}"          // €
let heart = "\u{2764}"         // ❤
```

### Экранирование интерполяции

```efen
let literal = "Использовать \${variable} как литерал"
// Выведет: Использовать ${variable} как литерал
```

## Raw-строки

Raw-строки не обрабатывают escape-последовательности:

```efen
let raw = r"C:\Users\Name\Documents"
// Выведет: C:\Users\Name\Documents (без обработки \)

let regex = r"\d+\.\d+"
// Регулярное выражение без двойного экранирования

let path = r#"C:\Program Files\App"#
// Альтернативный синтаксис с # для избежания конфликтов с "
```

## Конкатенация строк

### Оператор +

```efen
let first = "Hello"
let second = "World"
let result = first + " " + second  // "Hello World"
```

### Метод concat

```efen
let parts = ["Hello", "World", "!"]
let result = String::concat(parts, " ")  // "Hello World !"
```

### StringBuilder для производительности

```efen
let builder = StringBuilder::new()
builder.append("Hello")
builder.append(" ")
builder.append("World")
let result = builder.toString()  // "Hello World"
```

## Строковые методы

### Длина и проверки

```efen
let text = "Hello, World!"

text.length()         // 13
text.isEmpty()        // false
text.isBlank()        // false (есть не-пробельные символы)

let empty = ""
empty.isEmpty()       // true

let spaces = "   "
spaces.isBlank()      // true
```

### Поиск и проверка содержимого

```efen
let text = "Hello, World!"

text.contains("World")        // true
text.startsWith("Hello")      // true
text.endsWith("!")            // true

text.indexOf("o")             // 4 (первое вхождение)
text.lastIndexOf("o")         // 8 (последнее вхождение)

text.indexOf("xyz")           // -1 (не найдено)
```

### Извлечение подстрок

```efen
let text = "Hello, World!"

text.substring(0, 5)          // "Hello"
text.substring(7)             // "World!"

text[0..5]                    // "Hello" (срез)
text[7..]                     // "World!"

text.slice(0, 5)              // "Hello"
```

### Преобразование регистра

```efen
let text = "Hello, World!"

text.toLowerCase()            // "hello, world!"
text.toUpperCase()            // "HELLO, WORLD!"

text.capitalize()             // "Hello, world!"
text.toTitleCase()            // "Hello, World!"
```

### Удаление пробелов

```efen
let text = "  Hello  "

text.trim()                   // "Hello"
text.trimStart()              // "Hello  "
text.trimEnd()                // "  Hello"

let multispace = "Hello    World"
multispace.trimAll()          // "Hello World" (все множественные пробелы в один)
```

### Замена

```efen
let text = "Hello, World!"

text.replace("World", "Efen")           // "Hello, Efen!"
text.replaceAll("l", "L")               // "HeLLo, WorLd!"
text.replaceFirst("o", "0")             // "Hell0, World!"
```

### Разделение строк

```efen
let csv = "apple,banana,orange"
let fruits = csv.split(",")             // ["apple", "banana", "orange"]

let text = "one  two   three"
let words = text.split()                // ["one", "two", "three"] (по пробелам)

let data = "a:b:c:d"
let parts = data.split(":", 2)          // ["a", "b:c:d"] (максимум 2 части)
```

### Объединение

```efen
let words = ["Hello", "World"]
let result = words.join(" ")            // "Hello World"

let numbers = [1, 2, 3]
let csv = numbers.join(", ")            // "1, 2, 3"
```

### Повторение

```efen
let dash = "-"
let line = dash.repeat(10)              // "----------"

let pattern = "ab"
let result = pattern.repeat(3)          // "ababab"
```

### Padding (дополнение)

```efen
let num = "42"

num.padStart(5, "0")                    // "00042"
num.padEnd(5, "0")                      // "42000"

let word = "Hi"
word.padStart(10)                       // "        Hi" (пробелами)
```

## Форматирование строк

### Метод format

```efen
let name = "Alice"
let age = 30

// Позиционные аргументы
let msg1 = String::format("Name: {}, Age: {}", name, age)

// Именованные аргументы
let msg2 = String::format("Name: {name}, Age: {age}", name=name, age=age)

// Форматирование чисел
let pi = 3.14159
String::format("Pi: {:.2}", pi)         // "Pi: 3.14"
String::format("Pi: {:.4}", pi)         // "Pi: 3.1416"

// Выравнивание
String::format("{:>10}", "right")       // "     right"
String::format("{:<10}", "left")        // "left      "
String::format("{:^10}", "center")      // "  center  "
```

## Сравнение строк

### Операторы сравнения

```efen
let a = "apple"
let b = "banana"

a == b                                   // false
a != b                                   // true
a < b                                    // true (лексикографически)
a > b                                    // false
```

### Методы сравнения

```efen
let a = "Apple"
let b = "apple"

a.equals(b)                              // false
a.equalsIgnoreCase(b)                    // true

a.compareTo(b)                           // < 0 (a меньше b)
b.compareTo(a)                           // > 0 (b больше a)
```

## Работа с Unicode

### Графемные кластеры

```efen
let emoji = "👨‍👩‍👧‍👦"
emoji.length()                           // 7 (code units)
emoji.graphemeLength()                   // 1 (visual characters)

let text = "café"
text.length()                            // 4
text.graphemeLength()                    // 4
```

### Итерация по символам

```efen
let text = "Hello"

// Итерация по code points
for ch in text.chars() {
    println(ch)
}

// Итерация по графемным кластерам
for grapheme in text.graphemes() {
    println(grapheme)
}
```

### Нормализация Unicode

```efen
let text1 = "café"                       // é как один символ
let text2 = "café"                       // é как e + ́

text1 == text2                           // false

text1.normalize() == text2.normalize()   // true
```

## Регулярные выражения

### Создание regex

```efen
let pattern = Regex::new(r"\d+")
let email = Regex::new(r"^[a-z0-9]+@[a-z]+\.[a-z]{2,}$")
```

### Поиск совпадений

```efen
let text = "The year is 2024"
let pattern = Regex::new(r"\d+")

if pattern.isMatch(text) {
    println("Found numbers!")
}

let matches = pattern.findAll(text)      // ["2024"]
```

### Замена с помощью regex

```efen
let text = "Phone: 123-456-7890"
let pattern = Regex::new(r"\d")

text.replaceRegex(pattern, "X")          // "Phone: XXX-XXX-XXXX"
```

### Группы захвата

```efen
let pattern = Regex::new(r"(\d{4})-(\d{2})-(\d{2})")
let date = "2024-03-15"

if let captures = pattern.captures(date) {
    let year = captures[1]               // "2024"
    let month = captures[2]              // "03"
    let day = captures[3]                // "15"
}
```

## Кодировки

### UTF-8 (по умолчанию)

```efen
let text = "Привет"
let bytes = text.toBytes()               // UTF-8 bytes
let restored = String::fromBytes(bytes)  // "Привет"
```

### Другие кодировки

```efen
let text = "Hello"

text.encode("UTF-16")                    // Конвертация в UTF-16
text.encode("ASCII")                     // Конвертация в ASCII
text.encode("Windows-1251")              // Конвертация в Windows-1251

String::decode(bytes, "UTF-16")          // Декодирование из UTF-16
```

## Неизменяемость строк

Строки в Efen неизменяемы (immutable):

```efen
let text = "Hello"

// Это создаёт НОВУЮ строку
let upper = text.toUpperCase()

// text остаётся неизменным
println(text)                             // "Hello"
println(upper)                            // "HELLO"
```

Для изменяемых операций используйте StringBuilder:

```efen
let mut builder = StringBuilder::from("Hello")
builder.append(" World")
builder.insert(5, ",")
let result = builder.toString()           // "Hello, World"
```

## Производительность

### Избегайте конкатенации в циклах

```efen
// Плохо - создаёт много промежуточных строк
var result = ""
for i in 1..1000 {
    result = result + i.toString()
}

// Хорошо - использует StringBuilder
let builder = StringBuilder::new()
for i in 1..1000 {
    builder.append(i.toString())
}
let result = builder.toString()
```

### Используйте срезы вместо substring

```efen
// Хорошо - срез не копирует данные
let slice = text[0..5]

// Может быть менее эффективно
let sub = text.substring(0, 5)
```

## Лучшие практики

1. **Используйте интерполяцию вместо конкатенации**
   ```efen
   // Хорошо
   let msg = "Hello, ${name}!"

   // Хуже
   let msg = "Hello, " + name + "!"
   ```

2. **Используйте raw-строки для путей и regex**
   ```efen
   let path = r"C:\Users\Name"
   let pattern = r"\d+\.\d+"
   ```

3. **Проверяйте пустоту правильно**
   ```efen
   // Проверка на пустую строку
   if text.isEmpty() { }

   // Проверка на пустую строку или только пробелы
   if text.isBlank() { }
   ```

4. **Используйте многострочные строки для читаемости**
   ```efen
   let query = """
       SELECT name, email
       FROM users
       WHERE active = true
       """
   ```

5. **StringBuilder для множественных операций**
   ```efen
   let builder = StringBuilder::new()
   builder.append("Line 1\n")
   builder.append("Line 2\n")
   builder.append("Line 3\n")
   ```

## Особенности

1. Строки в Efen используют UTF-8 по умолчанию
2. Строки неизменяемы (immutable)
3. Интерполяция вычисляется во время выполнения
4. Срезы строк не копируют данные
5. Поддержка полного набора Unicode, включая emoji и сложные графемы
