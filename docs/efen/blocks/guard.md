# Guard и Defer

`Guard` и `defer` — это конструкции управления потоком выполнения, заимствованные из Swift.
Они помогают писать более чистый и безопасный код, следуя принципу "early exit" и гарантируя
выполнение очистки ресурсов.

## Guard — ранний выход

`Guard` используется для проверки условий и раннего выхода из функции, если условия не выполнены.
Это помогает избежать глубокой вложенности и делает код более линейным и читаемым.

### Базовый guard

```efen
fn greet(name: String?) {
    guard let name = name else {
        print("Имя не указано")
        return
    }

    print("Привет, ${name}!")
}

greet(name: "Иван")  // "Привет, Иван!"
greet(name: null)     // "Имя не указано"
```

### Guard требует выход

Блок `else` в `guard` **обязан** завершать выполнение функции одним из способов:
- `return` — выход из функции
- `throw` — выброс исключения
- `break` — выход из цикла
- `continue` — переход к следующей итерации
- Вызов функции, которая никогда не возвращается (например, `fatalError()`)

```efen
fn processAge(age: Int?) {
    guard let age = age else {
        print("Возраст не указан")
        return  // ✅ Обязательно
    }

    guard age >= 18 else {
        print("Слишком молод")
        return  // ✅ Обязательно
    }

    print("Возраст: ${age}")
}
```

### Guard vs If

Сравнение подходов:

```efen
// ❌ Глубокая вложенность с if
fn process(value: Int?) {
    if let value = value {
        if value > 0 {
            if value < 100 {
                print("Значение: ${value}")
            } else {
                print("Слишком большое")
            }
        } else {
            print("Должно быть положительным")
        }
    } else {
        print("Значение отсутствует")
    }
}
```

```efen
// ✅ Линейный код с guard
fn process(value: Int?) {
    guard let value = value else {
        print("Значение отсутствует")
        return
    }

    guard value > 0 else {
        print("Должно быть положительным")
        return
    }

    guard value < 100 else {
        print("Слишком большое")
        return
    }

    print("Значение: ${value}")
}
```

### Множественные условия

`Guard` может проверять несколько условий одновременно:

```efen
fn register(name: String?, email: String?, age: Int?) {
    guard let name = name,
          let email = email,
          let age = age else {
        print("Недостаточно данных для регистрации")
        return
    }

    print("Регистрация: ${name}, ${email}, ${age}")
}
```

### Guard с дополнительными условиями

```efen
fn validateUser(name: String?, age: Int?) {
    guard let name = name,
          let age = age,
          age >= 18,
          name.count >= 3 else {
        print("Неверные данные пользователя")
        return
    }

    print("Пользователь валиден: ${name}, ${age}")
}
```

### Guard в циклах

`Guard` можно использовать в циклах с `continue` или `break`:

```efen
let numbers = [1, 2, null, 4, null, 6]

for number in numbers {
    guard let value = number else {
        print("Пропускаем null")
        continue
    }

    print("Значение: ${value}")
}
```

### Guard с несколькими проверками

```efen
fn login(username: String?, password: String?) -> Bool {
    guard let username = username else {
        print("Имя пользователя не указано")
        return false
    }

    guard let password = password else {
        print("Пароль не указан")
        return false
    }

    guard username.count >= 3 else {
        print("Имя пользователя слишком короткое")
        return false
    }

    guard password.count >= 8 else {
        print("Пароль слишком короткий")
        return false
    }

    // Основная логика
    print("Вход выполнен успешно")
    return true
}
```

## Defer — отложенное выполнение

`Defer` используется для выполнения кода непосредственно перед выходом из текущей области видимости,
независимо от того, как произошёл выход (нормальное завершение, return, throw и т.д.).

Тело `defer` может бросить исключение. Если область уже покидает другое
исключение, оно остаётся главным, а ошибка `defer` добавляется к его
упорядоченному списку `suppressed`:

```efen
defer {
    resource.close() // может бросить CloseError
}
```

Если основного исключения нет, первая ошибка выполняемого cleanup становится
главной. Остальные `defer` всё равно выполняются в порядке LIFO, а их ошибки
добавляются к `suppressed` в фактическом порядке возникновения. Значение
`return`, незавершённый `break` или `continue` при этом уступает главной ошибке
cleanup. `try` вокруг инструкции `defer` обработчиком не является, поскольку
тело выполняется позже.

### Базовый defer

```efen
fn processFile {
    print("Открываем файл")

    defer {
        print("Закрываем файл")
    }

    print("Обрабатываем файл")
    // При выходе из функции автоматически выполнится defer
}

processFile()
// Открываем файл
// Обрабатываем файл
// Закрываем файл
```

### Гарантия выполнения

`Defer` гарантирует выполнение кода даже при раннем выходе:

```efen
fn process(value: Int?) {
    defer {
        print("Очистка ресурсов")
    }

    guard let value = value else {
        print("Значение отсутствует")
        return  // defer всё равно выполнится
    }

    print("Обработка: ${value}")
}

process(value: null)
// Значение отсутствует
// Очистка ресурсов

process(value: 42)
// Обработка: 42
// Очистка ресурсов
```

### Порядок выполнения defer

Если в функции несколько `defer`, они выполняются в **обратном** порядке объявления (LIFO):

```efen
fn example {
    defer { print("1") }
    defer { print("2") }
    defer { print("3") }

    print("Тело функции")
}

example()
// Тело функции
// 3
// 2
// 1
```

Это позволяет освобождать ресурсы в правильном порядке:

```efen
fn processData {
    print("Открываем соединение с БД")
    defer { print("Закрываем соединение с БД") }

    print("Начинаем транзакцию")
    defer { print("Завершаем транзакцию") }

    print("Выполняем запросы")
}

processData()
// Открываем соединение с БД
// Начинаем транзакцию
// Выполняем запросы
// Завершаем транзакцию
// Закрываем соединение с БД
```

### Defer и область видимости

`Defer` выполняется при выходе из своей области видимости, не обязательно функции:

```efen
fn example {
    print("Начало функции")

    if true {
        defer { print("Выход из if блока") }
        print("Внутри if")
    }

    print("После if")
}

example()
// Начало функции
// Внутри if
// Выход из if блока
// После if
```

### Defer с циклами

```efen
for i in 1..3 {
    defer { print("Завершение итерации ${i}") }
    print("Итерация ${i}")
}
// Итерация 1
// Завершение итерации 1
// Итерация 2
// Завершение итерации 2
// Итерация 3
// Завершение итерации 3
```

### Практические примеры

#### Работа с файлами

```efen
fn readFile(path: String) -> String? {
    let file = File.open(path)

    defer {
        file.close()
    }

    guard file.isOpen else {
        return null
    }

    return file.readAll()
}
```

#### Блокировки

```efen
fn updateSharedResource {
    lock.acquire()

    defer {
        lock.release()
    }

    // Работа с защищённым ресурсом
    // Блокировка будет освобождена в любом случае
}
```

#### Логирование

```efen
fn performOperation(name: String) {
    print("Начало операции: ${name}")

    defer {
        print("Завершение операции: ${name}")
    }

    // Логика операции
}
```

#### Изменение состояния

```efen
fn process {
    var isProcessing = true

    defer {
        isProcessing = false
    }

    // Выполнение обработки
    // isProcessing автоматически станет false при выходе
}
```

## Комбинирование Guard и Defer

`Guard` и `defer` отлично работают вместе:

```efen
fn processData(data: Data?, cache: Cache) {
    defer {
        cache.cleanup()
    }

    guard let data = data else {
        print("Данные отсутствуют")
        return  // cleanup всё равно выполнится
    }

    guard data.isValid else {
        print("Данные невалидны")
        return  // cleanup всё равно выполнится
    }

    // Обработка данных
    cache.store(data)
}
```

Более сложный пример:

```efen
fn transaction(connection: Connection?, query: String?) {
    defer {
        print("Закрытие соединения")
        connection?.close()
    }

    guard let connection = connection else {
        print("Соединение отсутствует")
        return
    }

    defer {
        print("Завершение транзакции")
        connection.commit()
    }

    guard let query = query else {
        print("Запрос отсутствует")
        return
    }

    print("Выполнение запроса: ${query}")
    connection.execute(query)
}
```

## Рекомендации

### Guard
1. **Используйте guard для early exit** вместо глубокой вложенности if
2. **Проверяйте предусловия в начале функции** с помощью guard
3. **Группируйте связанные проверки** в один guard
4. **Используйте guard для optional binding** когда значение нужно в остальной части функции
5. **Пишите понятные сообщения об ошибках** в блоке else

### Defer
1. **Используйте defer для очистки ресурсов** (файлы, соединения, блокировки)
2. **Размещайте defer сразу после получения ресурса** для наглядности
3. **Помните о порядке выполнения** (LIFO — последний объявленный выполнится первым)
4. **Не используйте defer для сложной логики** — только для очистки
5. **Избегайте изменения возвращаемых значений** в defer

### Анти-паттерны

```efen
// ❌ Плохо: сложная логика в defer
defer {
    if condition {
        performComplexOperation()
    }
}

// ✅ Хорошо: простая очистка
defer {
    resource.cleanup()
}
```

```efen
// ❌ Плохо: guard без early exit
guard let value = optionalValue else {
    print("Ошибка")
    // ❌ Нет return/throw/break/continue
}

// ✅ Хорошо: guard с early exit
guard let value = optionalValue else {
    print("Ошибка")
    return
}
```

## Сравнение с другими языками

### Go
```go
// Go использует defer похожим образом
defer file.Close()
```

### Python
```python
# Python использует контекстные менеджеры
with open("file.txt") as file:
    # defer не нужен, очистка автоматическая
```

### C++
```cpp
// C++ использует RAII
{
    std::unique_ptr<File> file = openFile();
    // Автоматическая очистка при выходе из области видимости
}
```

## См. также

- [if.md](if.md) — Условные конструкции
- [match.md](match.md) — Match и сопоставление с образцом
- [loops.md](loops.md) — Циклы
- [../memory.md](../memory.md) — Управление памятью
