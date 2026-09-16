# Управляющие конструкции (Control Flow)

Управляющие конструкции в `Efen` позволяют контролировать порядок выполнения кода.
Язык заимствует лучшие идеи из Swift, предлагая мощные и выразительные инструменты.

## Основные концепции

`Efen` предоставляет следующие управляющие конструкции:

- **Условные операторы** — выполнение кода на основе условий
- **Циклы** — повторяющееся выполнение кода
- **Сопоставление с образцом** — `match` с образцами и проверкой полноты
- **Ранний выход** — guard для упрощения потока управления
- **Отложенное выполнение** — defer для гарантированной очистки ресурсов

## Содержание

### [1. Условные конструкции](if.md)

Условные операторы позволяют выполнять код в зависимости от результата проверки условий.

**Основные возможности:**
- `if` как выражение, возвращающее значение
- Optional binding для безопасной работы с optional типами
- Множественное optional binding
- `if-let` с дополнительными условиями
- Тернарный оператор

**Примеры:**
```efen
// if как выражение
let status = if age >= 18 { "Взрослый" } else { "Ребёнок" }

// Optional binding
if let name = optionalName {
    print("Привет, ${name}!")
}

// Множественное binding с условием
if let name = optionalName, let age = optionalAge, age >= 18 {
    print("${name} совершеннолетний")
}
```

### [2. Циклы](loops.md)

Циклы позволяют многократно выполнять блок кода.

**Типы циклов:**
- `for-in` — итерация по коллекциям
- `while` — выполнение пока условие истинно
- `repeat-while` — выполнение хотя бы раз

**Управление потоком:**
- `break` — выход из цикла
- `continue` — переход к следующей итерации
- Метки циклов для управления вложенными циклами

**Примеры:**
```efen
// for-in с диапазоном
for i in 1..5 {
    print(i)
}

// for-in с where
for number in numbers where number % 2 == 0 {
    print(number)
}

// while с optional binding
while let value = optionalValue, value > 0 {
    print(value)
    optionalValue = value - 1
}

// repeat-while
repeat {
    count += 1
} while count < 10
```

### [3. Match и сопоставление с образцом](match.md)

Мощная конструкция для сопоставления значений с образцами.

**Основные возможности:**
- `match` как оператор и как выражение
- Обязательная полнота покрытия (exhaustiveness)
- Отсутствие проваливания по умолчанию
- Pattern matching с where условиями
- Value binding
- Работа с диапазонами, кортежами, enum, variant и optional

**Примеры:**
```efen
// Базовый match
match number {
    1: "Один"
    2: "Два"
    _: "Другое"
}

// Match с диапазонами
match temperature {
    ..<0: "Мороз"
    0..<10: "Холодно"
    10..<20: "Прохладно"
    20..<30: "Тепло"
    _: "Жарко"
}

// Сопоставление с условием where
match point {
    let (x, y) where x == y: "На диагонали"
    let (x, y) where x == -y: "На обратной диагонали"
    let (x, y): "Точка (${x}, ${y})"
}
```

### [4. Guard и Defer](guard.md)

Конструкции для управления потоком выполнения и гарантированной очистки ресурсов.

**Guard:**
- Ранний выход из функции при невыполнении условий
- Optional binding с доступом к значениям в остальной части функции
- Избежание глубокой вложенности

**Defer:**
- Гарантированное выполнение кода перед выходом из области видимости
- Идеально для очистки ресурсов (файлы, соединения, блокировки)
- Выполнение в обратном порядке объявления (LIFO)

**Примеры:**
```efen
// Guard для раннего выхода
fn process(value: Int?) {
    guard let value = value else {
        print("Значение отсутствует")
        return
    }

    guard value > 0 else {
        print("Должно быть положительным")
        return
    }

    print("Обработка: ${value}")
}

// Defer для очистки
fn readFile(path: String) {
    let file = File.open(path)

    defer {
        file.close()  // Выполнится в любом случае
    }

    guard file.isOpen else {
        return
    }

    // Работа с файлом
}
```

### [5. Try-Catch](try-catch.md)

Обработка исключений с интеграцией в систему throws контрактов.

**Основные возможности:**
- `try-catch` для перехвата исключений
- `finally` для гарантированной очистки
- `catch` без `try` — обработка с начала scope
- Pattern matching в catch блоках
- Try как выражение
- Интеграция с nothrows и throws only

**Примеры:**
```efen
// Базовый try-catch
try {
    operation()
} catch e: ValidationError {
    print("Ошибка валидации")
} catch e: Exception {
    print("Другая ошибка")
}

// Catch без try — охватывает весь scope
fn process(data: String) {
    validateInput(data)
    saveToDatabase(data)
    
    catch e: ValidationError {
        print("Ошибка валидации")
        return
    }
    catch e: DatabaseError {
        print("Ошибка БД")
        rollback()
    }
    
    print("Успех")
}

// Try как выражение
let result = try {
    parseData(input)
} catch {
    defaultValue
}
```

## Ключевые особенности

### 1. Выражения вместо операторов

В `Efen` многие управляющие конструкции могут быть выражениями:

```efen
// if как выражение
let result = if condition { value1 } else { value2 }

// match как выражение
let description = match status {
    .success: "Успешно"
    .error: "Ошибка"
}
```

### 2. Безопасность типов

Все условия должны иметь тип `Bool`, неявное преобразование не поддерживается:

```efen
let count = 5

// ❌ Ошибка
// if count { ... }

// ✅ Правильно
if count > 0 { ... }
```

### 3. Pattern Matching

Мощная система сопоставления с образцами:

```efen
match value {
    let x where x < 0: "Отрицательное"
    let x where x % 2 == 0: "Чётное"
    let x: "Нечётное положительное"
}
```

### 4. Optional Binding

Безопасная работа с optional значениями:

```efen
if let value = optionalValue {
    // value доступен как non-optional
}

guard let value = optionalValue else {
    return
}
// value доступен во всей остальной функции
```

### 5. Гарантированная очистка

Defer обеспечивает выполнение кода при любом выходе:

```efen
func process {
    defer { cleanup() }

    guard condition else { return }  // cleanup выполнится
    // ...
    if error { return }  // cleanup выполнится
    // ...
}  // cleanup выполнится
```

## Рекомендации

1. **Используйте guard для early exit** вместо глубокой вложенности if
2. **Предпочитайте `match` длинным if-else цепочкам** когда проверяете одно значение
3. **Используйте pattern matching** для сложных условий
4. **Используйте defer для очистки ресурсов** сразу после их получения
5. **Используйте optional binding** вместо явной проверки на null
6. **Используйте where в циклах** для фильтрации элементов
7. **Используйте выражения** когда нужно вернуть значение

## Вдохновение от Swift

`Efen` заимствует следующие лучшие идеи из Swift:

- ✅ If и match как выражения
- ✅ Optional binding с if-let и guard-let
- ✅ Pattern matching с where условиями
- ✅ Отсутствие проваливания в ветку по умолчанию
- ✅ Обязательная полнота покрытия при сопоставлении
- ✅ Guard для раннего выхода
- ✅ Defer для гарантированной очистки
- ✅ Метки циклов
- ✅ for-in с where фильтрацией
- ✅ repeat-while вместо do-while

## См. также

- [../index.md](../index.md) — Общая документация Efen
- [../types/collections.md](../types/collections.md) — Коллекции
- [../memory.md](../memory.md) — Управление памятью
- [../classes.md](../classes.md) — Классы
- [../interfaces.md](../interfaces.md) — Интерфейсы
