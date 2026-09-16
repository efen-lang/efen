# Try-Catch — обработка исключений

Конструкция `try-catch` используется для перехвата и обработки исключений в `Efen`.
В сочетании с [throws контрактами](../throws.md) она обеспечивает мощную и типобезопасную
систему обработки ошибок.

## Базовый try-catch

Стандартная форма обработки исключений:

```efen
fn processData(data: String) {
    try {
        validateData(data)
        saveToDatabase(data)
        notifyUsers(data)
    } catch e: ValidationError {
        print("Ошибка валидации: ${e.message}")
    } catch e: DatabaseError {
        print("Ошибка БД: ${e.message}")
        rollback()
    } catch e: Exception {
        print("Неизвестная ошибка: ${e}")
    }
}
```

## Try как выражение

`Try-catch` может возвращать значение:

```efen
let result = try {
    parseData(input)
} catch e: ParseError {
    defaultValue
}

let status = try {
    validateAndSave(data)
    "success"
} catch {
    "error"
}
```

## Множественный catch

Несколько `catch` блоков проверяются по порядку:

```efen
try {
    operation()
} catch e: NetworkError {
    handleNetworkError(e)
} catch e: TimeoutError {
    handleTimeout(e)
} catch e: IOException {
    handleIO(e)
} catch e: Exception {
    handleGeneric(e)
}
```

## Catch без типа

Если тип исключения не важен:

```efen
try {
    riskyOperation()
} catch {
    print("Произошла ошибка")
}

// С именем переменной
try {
    riskyOperation()
} catch e {
    print("Ошибка: ${e}")
}
```

## Finally блок

`Finally` выполняется всегда, независимо от наличия исключения:

```efen
try {
    openConnection()
    performOperation()
} catch e: Exception {
    logError(e)
} finally {
    closeConnection()  // Выполнится в любом случае
}
```

`finally` — часть конструкции `try … catch … finally` и выполняется после
обработчиков. `try { … } finally { … }` без единого `catch` получает диагностику
стиля с исправлением на [`defer`](guard.md#defer--отложенное-выполнение): очистка
ресурса объявляется рядом с его открытием.

## On exception блок

`On exception` позволяет выполнить код при возникновении исключения, не перехватывая его:

```efen
try {
    readFile
} on IOException {
    log("Ошибка ввода-вывода при чтении файла")
}
```

## Catch без Try

`catch` можно писать без `try`. `catch e: T` ловит исключения типа `T` из кода
выше себя от начала блока. Если выше уже стоит `catch`, который ловит это
исключение (тот же тип или базовый), зона начинается сразу после него. Код ниже
`catch` он не ловит. Переменные, объявленные между `catch`, видны дальше по блоку.

```efen
fn process(data: String) {
    validateInput(data)

    catch e: ValidationError {          // ValidationError из validateInput
        print("Ошибка валидации: ${e.message}")
        return
    }

    let parsed = parseData(data)

    catch e: ParseError {               // ParseError из validateInput и parseData
        print("Ошибка парсинга: ${e.message}")
        return
    }

    saveToDatabase(parsed)              // parsed виден

    catch e: DatabaseError {
        print("Ошибка БД: ${e.message}")
        rollback()
        return
    }

    print("Успешно обработано")
}
```

Такой подход позволяет группировать обработку ошибок линейно, рядом с кодом.

Краткая форма `catch` — одна инструкция на той же строке. Тип пишется с
заглавной буквы, обработчик — со строчной, поэтому граница между ними видна без
разрешения имён:

```efen
fn process(data: String) {
    someOperation()
    catch Error log("Ошибка")
    anotherOperation()
    catch log("Другая ошибка")
}
```

Если в блоке `catch` или `on` одна инструкция и вся запись помещается в одну
строку, блок получает диагностику стиля с исправлением на краткую форму:
`catch Error { log("Ошибка") }` → `catch Error log("Ошибка")`.

### on Exception

Конструкция `on Exception` позволяет обработать исключение перед выходом из функции:

```efen
fn readFile(path: String) throws only FileError {
    let file = openFile(path)
    
    on e: IOException print("Ошибка при чтении файла: ${e}")
    
    let content = readContent(file)
    return content
}
```

В отличие от `catch`, `on` не подавляет исключение, а лишь позволяет выполнить дополнительную логику
перед его пробросом.

### Вложенные scope

В вложенных блоках catch/finally без try работают только для своего scope:

```efen
fn complex {
    operation1()

    if condition {
        operation2()
        operation3()

        catch e: Error {
            // Перехватывает только operation2 и operation3
        }
    }

    operation4()

    catch e: Exception {
        // Перехватывает operation1, operation4 и весь if блок
    }
}
```

## Pattern matching в catch

```efen
try {
    operation()
} catch e: HttpError where e.code == 404 {
    print("Не найдено")
} catch e: HttpError where e.code >= 500 {
    print("Ошибка сервера")
} catch e: HttpError {
    print("Другая HTTP ошибка")
}
```

## Rethrow

Повторный выброс исключения:

```efen
try {
    operation()
} catch e: TemporaryError {
    retry()
} catch e: CriticalError {
    logCritical(e)
    throw e  // Пробрасываем дальше
}
```

Обёртывание исключения:

```efen
try {
    operation()
} catch e: Exception {
    throw ApplicationError("Не удалось выполнить операцию", cause: e)
}
```

## Try с throws only

Для точек ответственности с `throws only`:

```efen
fn limited throws only NetworkError {
    try {
        operation()  // Может бросить разные исключения
    } catch e: DatabaseError {
        throw NetworkError(cause: e)
    } catch e: ValidationError {
        throw NetworkError(cause: e)
    } catch e: Exception {
        throw NetworkError(cause: e)
    }
}
```

## Try с nothrows

Для точек ответственности с `nothrows`:

```efen
fn handler nothrows {
    try {
        riskyOperation()
    } catch e: Exception {
        logError(e)
        // НЕ пробрасываем исключение
    }
}
```

## Nested try-catch

Вложенные блоки обработки:

```efen
try {
    prepareData()

    try {
        saveToDatabase()
    } catch e: DatabaseError {
        // Обрабатываем только ошибки БД
        useCache()
    }

    notifyUsers()
} catch e: Exception {
    // Обрабатываем остальные ошибки
    logError(e)
}
```

## См. также

- [../throws.md](../throws.md) — Throws контракты и автоматическое распространение
- [guard.md](guard.md) — Guard для раннего выхода
- [if.md](if.md) — Условные конструкции
- [index.md](index.md) — Управляющие конструкции
