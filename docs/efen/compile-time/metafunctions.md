# Метафункции (Metafunctions)

> Метафункции — это функции времени компиляции, которые возвращают **Inline Closure** для безопасной генерации и трансформации кода.

`InlineClosure` является compile-time типом и дескриптором типизированного
фрагмента HIR. Его можно передавать между метафункциями, преобразовывать и
вставлять. После вставки остаются обычные узлы HIR; значение `InlineClosure`
нельзя сохранить в runtime-объекте или вызвать во время выполнения программы.

Код строится только из типизированных `Statement`, `Expression` и
`InlineClosure`. Строка не преобразуется в код.

## Философия дизайна

### Проблема сырой генерации кода

В большинстве языков с метапрограммированием (C++, Rust macros, Lisp) используется **сырая вставка кода** (raw code injection):

```
// Псевдокод проблемного подхода
macro LOG(msg) {
    // Генерирует сырой код, который напрямую вставляется
    let __temp = msg;
    println("[LOG] " + __temp);
}

// Проблемы:
let __temp = "user data";
LOG("test");  // КОНФЛИКТ! Создаётся ещё один __temp
```

**Проблемы сырой генерации:**
- ❌ **Загрязнение окружения** — макрос создаёт скрытые переменные
- ❌ **Конфликты имён** — переменные макроса могут конфликтовать с кодом
- ❌ **Изменение существующих переменных** — макрос может случайно изменить переменные вызывающего кода
- ❌ **Непредсказуемость** — поведение зависит от контекста вызова
- ❌ **Сложность отладки** — ошибки в сгенерированном коде трудно найти

### Решение: Inline Closure

**Efen использует принципиально другой подход:**

Метафункции возвращают **Inline Closure** — специальное замыкание, которое:
- ✅ **Работает в своей области видимости** — не может создавать переменные в окружении вызова
- ✅ **Не имеет конфликтов имён** — внутренние переменные изолированы
- ✅ **Не может изменять окружение** — явный контракт через параметры и возвращаемое значение
- ✅ **Предсказуемо** — поведение не зависит от места вызова
- ✅ **Безопасно** — компилятор проверяет типы и корректность

```efen
// Efen подход с Inline Closure
meta fn log(message: String) -> InlineClosure {
    return inline {
        // Работает в своей области видимости
        let timestamp = Time.now()
        println("[LOG ${timestamp}] ${message}")
    }
}

// Использование - безопасно!
let timestamp = "user data"
log("test")  // Нет конфликта - timestamp внутри inline изолирован
```

## Концепция Inline Closure

### Что такое Inline Closure?

**Inline Closure** — это обычное замыкание с двумя особенностями:

1. **Автоматически встраивается (inlined)** компилятором на месте вызова
2. **Генерируется во время компиляции** метафункцией

```efen
meta fn double(x: Int) -> InlineClosure {
    return inline { x * 2 }
}

// Вызов
let result = double(5)

// Компилятор встраивает (inline) замыкание:
// let result = { 5 * 2 }()  // -> 10
```

### Синтаксис

```efen
inline {
    // тело замыкания
    // может содержать локальные переменные
    // возвращает значение последним выражением
}
```

Или с явными параметрами:

```efen
inline (param1: Type1, param2: Type2) -> ReturnType {
    // тело с параметрами
}
```

### Statement Placeholders

**Ключевая возможность:** Внутри `inline closure` можно использовать **statement placeholders** для динамической вставки кода.

**Синтаксис:** `${statement}`

```efen
meta fn withLogging(code: InlineClosure) -> InlineClosure {
    return inline {
        println("Starting...")
        ${code}  // Вставка InlineClosure
        println("Finished")
    }
}

// Использование - передача через =>
withLogging => {
    processData()
    saveResults()
}

// Компилируется в:
// println("Starting...")
// processData()
// saveResults()
// println("Finished")
```

Два правила разделяют вставку кода и интерполяцию строк:

1. Внутри строкового литерала `${...}` — всегда интерполяция во время выполнения.
   Вставка кода в строки не заходит.
2. Вставка кода пишется только со скобками — `${code}`. Голое `$name` —
   плейсхолдер замыкания, а не вставка.

**Важно:** Placeholders работают **только внутри inline closure**. Это безопасно, потому что:
- ✅ Код встраивается в изолированную область видимости closure
- ✅ Нет риска загрязнения окружения вызова
- ✅ Все переменные остаются локальными для closure
- ✅ Компилятор проверяет корректность сгенерированного кода

#### Типы placeholders

**1. Statement placeholder** - вставка одного или нескольких statements:

```efen
meta fn benchmark(name: String, body: Statement) -> InlineClosure {
    return inline {
        let start = Timer.now()
        ${body}  // Вставка statements
        let duration = Timer.now() - start
        println("${name}: ${duration}ms")
    }
}
```

**2. Expression placeholder** - вставка выражения:

```efen
meta fn square(expr: Expression) -> InlineClosure {
    return inline {
        let temp = ${expr}  // Вставка expression
        temp * temp
    }
}
```

**3. Multiple placeholders** - несколько вставок:

```efen
meta fn tryCatch(tryBody: Statement, catchBody: Statement) -> InlineClosure {
    return inline {
        try {
            ${tryBody}
        } catch e: Error {
            println("Error caught: ${e}")
            ${catchBody}
        }
    }
}

// Использование
tryCatch(
    tryBody: { riskyOperation() },
    catchBody: { rollback() }
)
```

#### Statement vs InlineClosure - Критическая разница

**ВАЖНО:** Это два разных типа с разным назначением!

**Statement** - это **блок кода для модификации**:
- ✅ Можно анализировать структуру кода
- ✅ Можно модифицировать и трансформировать
- ✅ Создаётся через `efen::code {}` или передаётся как `code: { }`
- ✅ Передаётся через **именованные параметры**

```efen
use efen::*

meta fn transform(code: Statement) -> InlineClosure {
    // Можем анализировать и модифицировать
    let wrapped = efen::code {
        println("Before")
        ${code}  // Вставка Statement
        println("After")
    }

    return inline { ${wrapped} }
}

// Передача через именованный параметр
transform(code: {
    processData()
    saveResults()
})
```

**InlineClosure** - это **дескриптор замыкания (неизменяемый)**:
- ❌ НЕ можем модифицировать код внутри
- ✅ Можем вставить через `${closure}`
- ✅ Можем вызвать с параметрами `${closure}(arg1, arg2)`
- ✅ Создаётся через `inline { }` или передаётся через `=>`
- ✅ Передаётся через **trailing closure syntax `=>`**

```efen
meta fn wrapper(closure: InlineClosure) -> InlineClosure {
    // НЕ можем модифицировать closure
    // Можем только вставить как есть
    return inline {
        println("Before")
        ${closure}  // Вставка InlineClosure
        println("After")
    }
}

// Передача через trailing closure =>
wrapper => {
    processData()
    saveResults()
}
```

**InlineClosure с параметрами:**

```efen
meta fn forEach(items: comptime Array, body: InlineClosure) -> InlineClosure {
    return inline {
        for i in 0..<items.count {
            ${body}(items[i], i)  // Вызов с параметрами!
        }
    }
}

// Использование - два параметра
forEach([1, 2, 3], (value, index) {
    println("Item ${index}: ${value}")
})
```

**Когда что использовать?**

| Задача | Тип | Синтаксис передачи |
|--------|-----|-------------------|
| Нужно модифицировать код | `Statement` | `fun(code: { })` |
| Нужно только вставить код | `InlineClosure` | `fun => { }` |
| Closure с параметрами | `InlineClosure` | `fun => (a, b) { }` |

#### Передача Statement в метафункцию

**Statement передаётся ТОЛЬКО через именованные параметры** `code: { }`:

```efen
meta fn tryCatch(tryBody: Statement, catchBody: Statement) -> InlineClosure {
    return inline {
        try {
            ${tryBody}
        } catch e: Error {
            println("Error caught: ${e}")
            ${catchBody}
        }
    }
}

// Передача через именованные параметры
tryCatch(
    tryBody: {
        connectToDatabase()
        executeQuery()
    },
    catchBody: {
        logError()
        reconnect()
    }
)
```

**Несколько Statement параметров:**

```efen
meta fn ifElse(condition: Bool, thenBody: Statement, elseBody: Statement) -> InlineClosure {
    return inline {
        if condition {
            ${thenBody}
        } else {
            ${elseBody}
        }
    }
}

// Все параметры именованные
ifElse(x > 0,
    thenBody: { println("Positive") },
    elseBody: { println("Non-positive") }
)
```

#### Использование Trailing Closure Синтаксиса

Метафункции работают с обычным **trailing closure синтаксисом** языка Efen (с использованием `=>`):

> **ВАЖНО:** Синтаксис `fun => { }` работает **ТОЛЬКО** когда функция принимает **РОВНО ОДИН** параметр типа closure/InlineClosure. Для функций с несколькими параметрами используйте обычный синтаксис вызова.

```efen
meta fn withLogging(code: InlineClosure) -> InlineClosure {
    return inline {
        println("Starting...")
        ${code}
        println("Finished")
    }
}

// Передача через trailing closure syntax
withLogging => {
    processData()
    saveResults()
}
```

**Функции с несколькими параметрами:**

Когда метафункция принимает несколько параметров, используйте обычный синтаксис вызова:

```efen
meta fn retry(times: Int, code: InlineClosure) -> InlineClosure {
    // ...
}

// ❌ НЕПРАВИЛЬНО - функция имеет 2 параметра!
retry(3) => { connectToAPI() }

// ✅ ПРАВИЛЬНО - обычный вызов
retry(3, code {
    connectToAPI()
})

// ✅ ПРАВИЛЬНО - с параметрами closure
retry(3, (attempt) {
    connectToAPI()
    println("Attempt ${attempt}")
})
```

**Применение для метафункций с одним параметром:**

Trailing closure syntax делает метафункции похожими на встроенные конструкции:

**1. Создание языковых расширений:**
```efen
withTransaction => {
    db.insert(user)
    db.commit()
}

// Метафункция выглядит как встроенная конструкция
```

**2. DSL (Domain Specific Languages):**
```efen
meta fn measure(name: String, body: InlineClosure) -> InlineClosure {
    return inline {
        println("Running: ${name}")
        let start = Timer.now()
        try {
            ${body}
            let duration = Timer.now() - start
            println("✓ Success: ${duration}ms")
        } catch e: Error {
            let duration = Timer.now() - start
            println("✗ Failed: ${e} (${duration}ms)")
        }
    }
}

// DSL для измерения - два параметра
measure("User creation", body {
    let user = createUser("John")
    assert(user.name == "John")
})
```

3. **Несколько блоков с именованными параметрами:**
```efen
meta fn benchmark(
    setup: Statement,
    measure: Statement,
    teardown: Statement
) -> InlineClosure {
    return inline {
        ${setup}
        let start = Timer.now()
        ${measure}
        let duration = Timer.now() - start
        ${teardown}
        println("Time: ${duration}ms")
    }
}

// Использование с несколькими блоками
benchmark(
    setup: {
        let data = generateTestData()
    },
    measure: {
        sortAlgorithm(data)
    },
    teardown: {
        cleanup(data)
    }
)
```

4. **Комбинация обычных параметров и блока:**
```efen
meta fn retry(times: Int, code: InlineClosure) -> InlineClosure {
    return inline {
        var attempts = 0
        while attempts < times {
            try {
                ${code}
                break
            } catch {
                attempts++
            }
        }
    }
}

// Два параметра - обычный вызов
retry(3, code {
    connectToServer()
    sendRequest()
})
```

**Сравнение синтаксисов:**

```efen
// ✅ Один параметр - можно использовать =>
withLogging => { doSomething() }

// ✅ Несколько параметров - обычный вызов
retry(3, code { doSomething() })

// ❌ НЕПРАВИЛЬНО - нельзя использовать => с несколькими параметрами
retry(3) => { doSomething() }
```

#### Создание Statement программно: блок `efen::code {}`

Для создания объектов `Statement` программно в compile-time коде используется специальный блок `efen::code {}`.

**Важные правила:**

1. **Код внутри блока ВСЕГДА должен быть валидным синтаксически!**
   - Компилятор проверяет синтаксис внутри `efen::code {}`
   - Невалидный код приведёт к ошибке компиляции
   - Даже если код не будет выполнен, он должен парситься

2. **Внутри блока можно использовать placeholders**
   - Expression placeholders: `${expr}`
   - Statement placeholders: `${stmt}` (только в inline closures)

**Базовый пример:**

```efen
meta fn createLogger(level: String) -> InlineClosure {
    let logStatement = efen::code {
        println("[${level}] Log message")
    }

    return inline {
        ${logStatement}
    }
}
```

**Пример с условной генерацией:**

```efen
use project::*
use efen::*

meta fn conditionalCheck(enableCheck: Bool, varName: Identifier) -> InlineClosure {
    if enableCheck {
        let checkCode = efen::code {
            if ${varName} < 0 {
                throw Error("Value must be non-negative")
            }
        }
        return inline { ${checkCode} }
    } else {
        return inline { }
    }
}

// Использование
conditionalCheck(true, Identifier.create("value"))
```

**Пример с динамической генерацией кода:**

```efen
use efen::*

meta fn generateGetters(fields: comptime Identifier[]) -> InlineClosure {
    let statements = []

    for field in fields {
        let fieldName = field.toString()
        let getterName = Identifier.create("get" + fieldName.capitalize())
        let typeName = Identifier.create(fieldName + "Type")

        let getter = efen::code {
            fn ${getterName}() -> ${typeName} {
                return this.${field}
            }
        }
        statements.push(getter)
    }

    return inline {
        for stmt in statements {
            ${stmt}
        }
    }
}

// Использование
generateGetters([
    Identifier.create("name"),
    Identifier.create("age"),
    Identifier.create("email")
])
```

**Ошибки компиляции:**

```efen
// ❌ ОШИБКА: Невалидный синтаксис внутри блока
let bad = efen::code {
    this is not valid syntax!!!
}
// Компилятор сообщит об ошибке синтаксиса

// ❌ ОШИБКА: Незакрытая скобка
let bad2 = efen::code {
    if x > 0 {
        println("test")
    // Скобка не закрыта
}
// Компилятор сообщит об ошибке

// ✅ ПРАВИЛЬНО: Валидный синтаксис
let good = efen::code {
    if x > 0 {
        println("test")
    }
}
```

**Использование с placeholders:**

```efen
meta fn wrapWithCheck(varName: Expression, code: Statement) -> InlineClosure {
    let checkStatement = efen::code {
        if ${varName} == null {
            throw NullError("${varName} is null")
        }
    }

    return inline {
        ${checkStatement}
        ${code}
    }
}

// Использование
wrapWithCheck(user) {
    println("User: ${user.name}")
}
```

**Важно:** `efen::code {}` возвращает объект типа `Statement`, который можно хранить в переменных, передавать в функции и использовать с placeholders внутри `inline closure`.

#### Специальные типы для метапрограммирования

**КРИТИЧЕСКИ ВАЖНО:** Компилятор **ЗАПРЕЩАЕТ** вставлять сырые строки (`String`) в код через placeholders. Вместо этого используются специальные типы:

**1. `efen::Identifier` - идентификаторы**

Представляет имя переменной, функции, свойства и т.д.

```efen
use efen::*

meta fn createGetter(fieldName: Identifier) -> InlineClosure {
    let getterName = Identifier.create("get" + fieldName.toString().capitalize())

    return inline {
        fn ${getterName}() -> Auto {
            return this.${fieldName}
        }
    }
}

// Использование
createGetter(Identifier.create("userName"))
```

**2. `efen::Expression` - выражения**

Представляет compile-time выражение.

```efen
use efen::*

meta fn doubleValue(expr: Expression) -> InlineClosure {
    return inline {
        let temp = ${expr}
        temp * 2
    }
}

// Expression создается из AST узлов, а не из строк!
```

**3. `efen::Type` - типы**

Представляет тип данных (уже используется в примерах).

```efen
use efen::*

meta fn createValidator(type: Type) -> InlineClosure {
    return inline (value: ${type}) -> ${type} {
        if !value.isValid() {
            throw ValidationError("Invalid ${type.name()}")
        }
        return value
    }
}
```

**4. `efen::Statement` - statements**

Представляет блок кода (уже используется в примерах).

#### API для работы с идентификаторами

```efen
// Создание идентификатора
Identifier.create(name: comptime String) -> Identifier

// Получение имени
identifier.toString() -> String

// Проверка валидности
identifier.isValid() -> Bool

// Конкатенация
identifier.concat(suffix: String) -> Identifier
```

#### Безопасность типов

**❌ ОШИБКА - сырая строка:**
```efen
// ЗАПРЕЩЕНО компилятором!
meta fn bad(varName: String) -> InlineClosure {
    return inline {
        if ${varName} < 0 {  // ❌ ОШИБКА КОМПИЛЯЦИИ
            throw Error("negative")
        }
    }
}
```

**✅ ПРАВИЛЬНО - специальный тип:**
```efen
use efen::*

meta fn good(varName: Identifier) -> InlineClosure {
    return inline {
        if ${varName} < 0 {  // ✅ OK - проверено компилятором
            throw Error("negative")
        }
    }
}

// Вызов
good(Identifier.create("counter"))
```

#### Преимущества специальных типов

**1. Защита от инъекций кода:**
```efen
// ❌ Если бы разрешались строки - инъекция!
let malicious = "x; deleteAllData(); y"
badFunction(malicious)  // Катастрофа!

// ✅ С Identifier - безопасно
let safe = Identifier.create("x; deleteAllData(); y")
// ❌ ОШИБКА: невалидный идентификатор
```

**2. Проверка синтаксиса на этапе компиляции:**
```efen
// Компилятор проверяет что идентификатор валиден
let id1 = Identifier.create("myVar")     // ✅ OK
let id2 = Identifier.create("123abc")    // ❌ ОШИБКА: начинается с цифры
let id3 = Identifier.create("my-var")    // ❌ ОШИБКА: содержит дефис
let id4 = Identifier.create("for")       // ❌ ОШИБКА: ключевое слово
```

**3. Типобезопасность:**
```efen
meta fn createProperty(name: Identifier, type: Type) -> InlineClosure {
    return inline {
        var ${name}: ${type}  // ✅ Компилятор проверяет типы
    }
}

// ✅ Правильно
createProperty(
    Identifier.create("age"),
    Type.int()
)

// ❌ ОШИБКА КОМПИЛЯЦИИ - неправильные типы аргументов
createProperty("age", "Int")
```

**4. Рефлексия и анализ:**
```efen
meta fn validateIdentifier(id: Identifier) -> InlineClosure {
    // Можем анализировать идентификатор на этапе компиляции
    if id.toString().length() > 50 {
        compileWarning("Identifier too long: ${id}")
    }

    if id.toString().startsWith("_") {
        compileWarning("Private identifier: ${id}")
    }

    return inline {
        // ...
    }
}
```

#### Композиция placeholders

Placeholders можно комбинировать с обычным кодом:

```efen
meta fn withTransaction(setup: Statement, body: Statement, cleanup: Statement) -> InlineClosure {
    return inline {
        // Код метафункции
        let transaction = beginTransaction()

        // Вставка setup
        ${setup}

        try {
            // Вставка основного тела
            ${body}

            transaction.commit()
        } catch e: Error {
            transaction.rollback()
            throw e
        } finally {
            // Вставка cleanup
            ${cleanup}
        }
    }
}

// Использование
withTransaction(
    setup: { validateConnection() },
    body: {
        insertData()
        updateRecords()
    },
    cleanup: { closeConnection() }
)
```

#### Ограничения и безопасность

**✅ Что МОЖНО:**
- Вставлять statements внутри inline closure
- Комбинировать placeholders с обычным кодом
- Использовать множественные placeholders
- Вставлять как statements, так и expressions

**❌ Что НЕЛЬЗЯ:**
- Использовать placeholders ВНЕ inline closure
- Создавать переменные в окружении вызова через placeholders
- Модифицировать область видимости вызывающего кода

```efen
// ❌ ОШИБКА - placeholder вне inline closure
meta fn bad(code: Statement) -> InlineClosure {
    ${code}  // ОШИБКА КОМПИЛЯЦИИ - вне inline closure
    return inline { ... }
}

// ✅ ПРАВИЛЬНО - placeholder внутри inline closure
meta fn good(code: Statement) -> InlineClosure {
    return inline {
        ${code}  // ✅ OK - внутри inline closure
    }
}
```

#### Примеры использования

**Пример 1: Retry wrapper**

```efen
meta fn retry(maxAttempts: Int, body: InlineClosure) -> InlineClosure {
    return inline {
        var attempts = 0
        var success = false

        while attempts < maxAttempts && !success {
            try {
                ${body}
                success = true
            } catch e: Error {
                attempts++
                if attempts >= maxAttempts {
                    throw e
                }
                println("Retry ${attempts}/${maxAttempts}")
            }
        }
    }
}

// Использование - два параметра
retry(3, body {
    connectToAPI()
    fetchData()
})
```

**Пример 2: Measure memory**

```efen
meta fn measureMemory(name: String, body: InlineClosure) -> InlineClosure {
    return inline {
        let memBefore = Runtime.getMemoryUsage()
        ${body}
        let memAfter = Runtime.getMemoryUsage()
        println("${name} used ${memAfter - memBefore} bytes")
    }
}

// Использование - два параметра
measureMemory("Data processing", body {
    let data = loadLargeFile()
    processData(data)
})
```

**Пример 3: Conditional execution**

```efen
use project::*

meta fn onlyIf(condition: comptime Bool, body: InlineClosure) -> InlineClosure {
    if condition {
        return inline {
            ${body}
        }
    } else {
        return inline { }  // Пустое - код не выполняется
    }
}

// Использование - два параметра
onlyIf(project.isDebug(), body {
    validateInvariants()
    printDebugInfo()
})
```

**Пример 4: Scope guard**

```efen
meta fn scopeGuard(onEnter: Statement, body: Statement, onExit: Statement) -> InlineClosure {
    return inline {
        ${onEnter}

        defer {
            ${onExit}
        }

        ${body}
    }
}

// Использование
scopeGuard(
    onEnter: { acquireLock() },
    body: {
        criticalSection()
    },
    onExit: { releaseLock() }
)
```

#### Преимущества statement placeholders

**1. Безопасность**
```efen
// Placeholder в inline closure - безопасно
meta fn safe(code: InlineClosure) -> InlineClosure {
    return inline {
        let temp = 42  // Локальная переменная closure
        ${code}
    }
}

let temp = "user data"
safe => { println(temp) }  // temp из closure не конфликтует
// temp всё ещё "user data"
```

**2. Гибкость**
```efen
// Можно строить сложную логику вокруг вставляемого кода
meta fn smartRetry(body: Statement) -> InlineClosure {
    return inline {
        var delay = 100
        for attempt in 0..<5 {
            try {
                ${body}
                break
            } catch e: NetworkError {
                sleep(delay)
                delay *= 2  // Exponential backoff
            }
        }
    }
}
```

**3. Композируемость**
```efen
// Placeholders можно вкладывать
meta fn logAndMeasure(name: String, body: InlineClosure) -> InlineClosure {
    return inline {
        log("INFO", "Starting ${name}")
        measureMemory(name, body {
            ${body}
        })
        log("INFO", "Finished ${name}")
    }
}
```

## Объявление метафункций

### Базовый синтаксис

```efen
meta fn functionName(params...) -> InlineClosure {
    // Compile-time код для генерации замыкания
    return inline {
        // Runtime код, который будет встроен
    }
}
```

### Ключевое слово `meta fn`

Определяет функцию, выполняющуюся во время компиляции:

```efen
meta fn assert(condition: Bool, message: String) -> InlineClosure {
    return inline {
        if !condition {
            throw AssertionError(message)
        }
    }
}

// Вызов во время runtime (но генерируется во время компиляции)
assert(x > 0, "x must be positive")
```

### Возвращаемый тип `InlineClosure`

Метафункции **всегда** возвращают `InlineClosure` — специальный тип, обозначающий Inline Closure:

```efen
meta fn log(level: String, msg: String) -> InlineClosure {
    return inline {
        if Logger.isEnabled(level) {
            Logger.log(level, location.file, location.line, msg)
        }
    }
}
```

### Параметры метафункций

Метафункции могут принимать два типа параметров:

#### 1. Compile-time константы

Вычисляются во время компиляции:

```efen
meta fn repeatString(text: comptime String, count: comptime Int) -> InlineClosure {
    let repeated = text.repeat(count)  // Вычисляется во время компиляции
    return inline {
        repeated  // Константа встроена в замыкание
    }
}

// Использование
let greeting = repeatString("Hello! ", 3)  // "Hello! Hello! Hello! "
```

#### 2. Runtime параметры

Передаются в inline closure как есть:

```efen
meta fn max(a: Int, b: Int) -> InlineClosure {
    return inline {
        if a > b { a } else { b }
    }
}

// Использование
let maximum = max(x * 2, y + 3)  // Выражения вычисляются во время runtime
```

**Правило**: Если параметр не помечен `comptime`, он передаётся в inline closure как runtime значение.

## Inline Closure в деталях

### Область видимости

Inline closure имеет **собственную область видимости**:

```efen
meta fn swap(a: var Int, b: var Int) -> InlineClosure {
    return inline {
        let temp = a  // temp - локальная переменная inline closure
        a = b
        b = temp
    }
}

// Использование
let temp = "user data"  // Не конфликтует!
swap(x, y)
```

### Захват переменных

Inline closure может захватывать переменные из окружения **только явно**:

```efen
meta fn incrementBy(value: Int) -> InlineClosure {
    return inline {
        // value захвачен из параметра метафункции
        counter += value
    }
}

let counter = 10
incrementBy(5)  // counter = 15
```

### Возвращаемое значение

Inline closure возвращает значение последним выражением или через `return`:

```efen
meta fn square(x: Int) -> InlineClosure {
    return inline {
        x * x  // Возвращаемое значение
    }
}

let result = square(5)  // 25
```

### Типизация

Inline closure **полностью типизирован** компилятором:

```efen
meta fn safeDivide(a: Int, b: Int) -> InlineClosure {
    return inline {
        if b == 0 {
            throw DivisionByZeroError()
        }
        a / b
    }
}

// Компилятор знает:
// - Тип результата: Int
// - Может выбросить исключение: DivisionByZeroError
let result: Int = safeDivide(10, 2)
```

### Соответствие сигнатур

**Критически важно:** Inline closure **должен иметь ту же сигнатуру**, что ожидается в месте вызова.

Компилятор проверяет:
- ✅ **Типы параметров** должны совпадать
- ✅ **Возвращаемый тип** должен совпадать
- ✅ **Количество параметров** должно совпадать

#### Пример: функция без параметров

```efen
meta fn getTimestamp -> InlineClosure {
    let file = location.file
    let line = location.line

    return inline {
        // Inline closure НЕ принимает параметров
        "${file}:${line} at ${Time.now()}"
    }
}

// Вызов как функция без параметров
let timestamp = getTimestamp()  // ✅ OK - тип String
```

#### Пример: функция с параметрами

```efen
meta fn validateRange(min: Int, max: Int) -> InlineClosure {
    return inline (value: Int) -> Int {
        // Inline closure ПРИНИМАЕТ Int и ВОЗВРАЩАЕТ Int
        if value < min || value > max {
            throw RangeError("Value out of range")
        }
        return value
    }
}

// Вызов с параметром - inline closure должно принять Int
let age: Int = validateRange(0, 150)(42)  // ✅ OK
let age: Int = validateRange(0, 150)      // ❌ ОШИБКА - возвращает функцию (Int) -> Int
```

#### Пример: проверка типов компилятором

```efen
meta fn logger(level: String) -> InlineClosure {
    return inline (message: String) -> Void {
        // Inline closure принимает String, возвращает Void
        if Logger.isEnabled(level) {
            Logger.log(level, message)
        }
    }
}

// Использование
let info = logger("INFO")
info("User logged in")  // ✅ OK - передан String

info(123)  // ❌ ОШИБКА КОМПИЛЯЦИИ - ожидается String, получен Int
```

#### Пример: generic с проверкой типов

```efen
meta fn identity<T> -> InlineClosure {
    return inline (value: T) -> T {
        // Inline closure принимает T и возвращает T
        value
    }
}

let intIdentity = identity<Int>()
let x: Int = intIdentity(42)      // ✅ OK
let y: Int = intIdentity("text")  // ❌ ОШИБКА - String не совместим с Int
```

#### Важное правило

```efen
// Если вызов выглядит так:
someFunction(param1, param2) -> Result

// То inline closure ДОЛЖНО иметь сигнатуру:
inline (param1Type, param2Type) -> Result

// Компилятор проверяет это во время компиляции!
```

#### Пример с несовпадением типов (ошибка)

```efen
meta fn badexample -> InlineClosure {
    return inline (x: String) -> Int {  // Принимает String, возвращает Int
        x.length()
    }
}

// Попытка вызвать как функцию без параметров
let result = badexample()
// ❌ ОШИБКА КОМПИЛЯЦИИ:
// Expected: () -> T
// Got: (String) -> Int
```

#### Корректный вариант

```efen
meta fn goodexample -> InlineClosure {
    return inline (x: String) -> Int {
        x.length()
    }
}

// Правильный вызов - с параметром
let length = goodexample()("hello")  // ✅ OK - 5

// Или сохранить функцию
let stringLength = goodexample()  // Тип: (String) -> Int
let len = stringLength("world")   // ✅ OK - 5
```

## Два способа использования метафункций

Метафункции могут работать в двух режимах в зависимости от сигнатуры inline closure:

### Режим 1: Statement/Expression (inline closure без параметров)

Метафункция принимает все параметры и возвращает inline closure без параметров, которое встраивается как statement или expression:

```efen
meta fn log(level: String, message: String) -> InlineClosure {
    return inline {  // () -> Void - БЕЗ параметров
        Logger.log(level, location.file, location.line, message)
    }
}

// Вызов
log("INFO", "test")

// Компилируется в:
// {  // inline closure встраивается
//     Logger.log("INFO", "main.efen", 42, "test")
// }()  // и сразу выполняется
```

**Применение:** логирование, assertions, benchmark обёртки, условная компиляция - всё, что выполняется как statement.

### Режим 2: Higher-Order Function (inline closure с параметрами)

Метафункция возвращает inline closure С параметрами, которое используется как функция:

```efen
meta fn validateRange(min: Int, max: Int) -> InlineClosure {
    return inline (value: Int) -> Int {  // (Int) -> Int - С параметрами
        if value < min || value > max {
            throw RangeError("Out of range")
        }
        return value
    }
}

// Получаем функцию-валидатор
let ageValidator = validateRange(0, 150)  // Тип: (Int) -> Int

// Используем её
let age = ageValidator(42)  // ✅ OK
```

**Применение:** валидаторы, трансформеры, фабрики функций - всё, что возвращает переиспользуемую функцию.

### Сравнение режимов

| Режим | Inline closure | Использование | Пример |
|-------|----------------|---------------|--------|
| Statement/Expression | `() -> T` или `() -> Void` | Выполняется сразу | `log("INFO", "msg")` |
| Higher-Order Function | `(P1, P2, ...) -> R` | Возвращает функцию | `validateRange(0, 100)(value)` |

## Практические примеры

### 1. Логирование с контекстом

```efen
meta fn log(level: comptime String, message: String) -> InlineClosure {
    return inline {
        if Logger.isEnabled(level) {
            Logger.log(
                level,
                location.file,   // Встроено во время компиляции
                location.line,   // Встроено во время компиляции
                message
            )
        }
    }
}

// Использование
log("INFO", "User logged in: " + username)

// Компилируется в:
// if Logger.isEnabled("INFO") {
//     Logger.log("INFO", "main.efen", 42, "User logged in: " + username)
// }
```

### 2. Assert с автоматическим сообщением

```efen
meta fn assert(condition: Bool, message: String? = null) -> InlineClosure {
    let conditionStr = condition.toString()  // Compile-time
    let file = location.file
    let line = location.line
    let msg = message ?? "Assertion failed: ${conditionStr}"

    return inline {
        if !condition {
            throw AssertionError("${file}:${line} - ${msg}")
        }
    }
}

// Использование
assert(x > 0)
assert(y < 100, "y out of range")
```

### 3. Benchmark

```efen
meta fn benchmark(name: comptime String, code: InlineClosure) -> InlineClosure {
    return inline {
        let startTime = Timer.now()
        let result = code()  // Выполняем переданное замыкание
        let endTime = Timer.now()
        let duration = endTime - startTime
        println("Benchmark '${name}': ${duration}ms")
        result  // Возвращаем результат кода
    }
}

// Использование
let result = benchmark("data processing") => {
    processData()
    optimizeResults()
}
```

### 4. Ленивое вычисление

```efen
meta fn lazy<T>(computation: inline -> T) -> InlineClosure {
    return inline {
        var cached: T? = null
        var isComputed = false

        fn get -> T {
            if !isComputed {
                cached = computation()
                isComputed = true
            }
            return cached!
        }

        get  // Возвращаем функцию-геттер
    }
}

// Использование
let lazyValue = lazy => expensiveComputation()
// ...
let value = lazyValue()  // Вычисляется только здесь
```

### 5. Условная компиляция

```efen
use project::*

meta fn debugOnly(code: InlineClosure) -> InlineClosure {
    if project.isDebug() {
        return code
    } else {
        return inline { }  // Пустое замыкание
    }
}

// Использование
debugOnly => {
    println("Debug info: ${debugData}")
    validateInvariants()
}

// В release сборке полностью исключается!
```

### 6. Проверка диапазона

```efen
meta fn inRange<T>(value: T, min: T, max: T, name: comptime String) -> InlineClosure {
    return inline {
        if value < min || value > max {
            throw RangeError("${name} must be in range [${min}, ${max}], got ${value}")
        }
        value
    }
}

// Использование
let age = inRange(userInput, 0, 150, "age")
```

### 7. Memoization

```efen
meta fn memoize<K, V>(keyFn: inline -> K, valueFn: inline -> V) -> InlineClosure {
    return inline {
        static var cache: [K: V] = [:]

        let key = keyFn()
        if let cached = cache[key] {
            return cached
        }

        let value = valueFn()
        cache[key] = value
        return value
    }
}

// Использование
fn fibonacci(n: Int) -> Int {
    if n <= 1 { return n }

    return memoize(
        keyFn: => n,
        valueFn: => fibonacci(n-1) + fibonacci(n-2)
    )
}
```

### 8. Try-with-resources

```efen
meta fn using<T: Disposable, R>(
    resource: inline -> T,
    body: inline (T) -> R
) -> InlineClosure {
    return inline {
        let res = resource()
        defer { res.dispose() }
        body(res)
    }
}

// Использование
using(
    resource: => File.open("data.txt"),
    body: (file: File) -> String {
        file.readAll()
    }
)
```

## Передача кода в метафункции

### Inline closure как параметр

Метафункции могут принимать inline closure:

```efen
meta fn repeat(count: comptime Int, code: InlineClosure) -> InlineClosure {
    return inline {
        for i in 0..<count {
            code()
        }
    }
}

// Использование с trailing closure
repeat(3) => {
    println("Hello!")
}

// Результат:
// Hello!
// Hello!
// Hello!
```

### Inline closure с параметрами

```efen
meta fn forEach<T>(
    collection: [T],
    body: inline (T, Int) -> Void
) -> InlineClosure {
    return inline {
        for (index, item) in collection.enumerated() {
            body(item, index)
        }
    }
}

// Использование - два параметра
forEach([1, 2, 3], (value, index) {
    println("Item ${index}: ${value}")
})
```

### Inline closure с возвращаемым значением

```efen
meta fn transform<T, R>(
    value: T,
    transformer: inline (T) -> R
) -> InlineClosure {
    return inline {
        transformer(value)
    }
}

// Использование
let doubled = transform(5) => (x) { x * 2 }  // 10
```

## Compile-time вычисления

### Константное вычисление

Параметры с `comptime` вычисляются во время компиляции:

```efen
meta fn powerOfTwo(exponent: comptime Int) -> InlineClosure {
    let result = 1 << exponent  // Вычисляется во время компиляции
    return inline {
        result  // Константа
    }
}

let value = powerOfTwo(10)  // Встроенная константа 1024
```

### Генерация на основе compile-time условий

```efen
meta fn optimizedSort<T>(
    array: [T],
    algorithm: comptime String
) -> InlineClosure {
    if algorithm == "quick" {
        return inline { quickSort(array) }
    } else if algorithm == "merge" {
        return inline { mergeSort(array) }
    } else {
        compileError("Unknown sorting algorithm: ${algorithm}")
    }
}

// Использование - алгоритм выбирается во время компиляции!
let sorted = optimizedSort(data, "quick")
```

### Статическая генерация кода

```efen
use efen::*

meta fn generateAccessors(propertyName: comptime Identifier, type: Type) -> InlineClosure {
    let propStr = propertyName.toString()
    let getterName = Identifier.create("get" + propStr.capitalize())
    let setterName = Identifier.create("set" + propStr.capitalize())

    return inline {
        fn ${getterName}() -> type {
            return this.${propertyName}
        }

        fn ${setterName}(value: type) {
            this.${propertyName} = value
        }
    }
}

// Использование
generateAccessors(Identifier.create("userName"), Type.string())
```

## Контекст компиляции

### Объект `location`

Внутри метафункций доступен встроенный объект `location`, который содержит информацию о **месте вызова** метафункции:

```efen
meta fn debugInfo -> InlineClosure {
    return inline {
        println("Debug: ${location.file}:${location.line} in ${location.function}")
    }
}

// Использование
fn processData {
    debugInfo()  // Debug: main.efen:42 in processData
}
```

#### API объекта `location`

**Поля:**
- `location.file: String` - путь к файлу (относительно корня проекта)
- `location.line: Int` - номер строки
- `location.column: Int` - номер колонки
- `location.function: String?` - имя функции (или `null` если вне функции)
- `location.module: String` - имя модуля

**Методы:**
- `location.toString() -> String` - форматированная строка `"file.efen:42:15"`

**Пример использования:**

```efen
use efen::*

meta fn assert(condition: Expression, message: String) -> InlineClosure {
    // location указывает на место ВЫЗОВА assert(), не на его определение
    let callSite = location.toString()

    return inline {
        if !${condition} {
            throw AssertionError(
                "${message}\n" +
                "  at ${callSite}\n" +
                "  in ${location.function ?? 'global scope'}"
            )
        }
    }
}

// Вызов
fn validateUser(user: User) {
    assert(user.age >= 18, "User must be adult")
    // При ошибке: "User must be adult
    //              at validators.efen:42:5
    //              in validateUser"
}
```

**Важно:** `location` всегда указывает на **место вызова метафункции**, а не на место её определения. Это позволяет создавать точные сообщения об ошибках и отладочную информацию.

#### Продвинутое использование `location`

**1. Условная компиляция по файлу:**
```efen
use project::*

meta fn testOnly(code: InlineClosure) -> InlineClosure {
    // Компилируем только если вызвано из тестового файла
    if location.file.endsWith("_test.efen") {
        return inline { ${code} }
    } else {
        return inline { }
    }
}
```

**2. Профилирование с точной локацией:**
```efen
meta fn profile(code: InlineClosure) -> InlineClosure {
    let loc = location.toString()

    return inline {
        let start = Timer.now()
        ${code}
        let duration = Timer.now() - start
        Profiler.record(loc, duration)
    }
}
```

**3. Логирование с контекстом:**
```efen
meta fn log(level: String, message: String) -> InlineClosure {
    return inline {
        Logger.log(
            level,
            message,
            file: location.file,
            line: location.line,
            function: location.function
        )
    }
}
```

### Модуль `project`

Для структурированного доступа к информации о проекте и сборке используйте модуль `project`:

```efen
use project::*

meta fn debugOnly(code: InlineClosure) -> InlineClosure {
    if project.isDebug() {
        return inline {
            ${code}
        }
    } else {
        return inline { }
    }
}

// Использование
debugOnly => {
    println("Debug information")
    validateInvariants()
}
```

#### Доступные функции модуля `project`

**Режим сборки:**
```efen
use project::*

// Проверка режима сборки
project.isDebug() -> Bool       // true если debug сборка
project.isRelease() -> Bool     // true если release сборка
project.buildMode() -> String   // "debug" или "release"

// Профиль оптимизации
project.optimizationLevel() -> Int  // 0-3
```

**Информация о проекте:**
```efen
use project::*

project.name() -> String        // Имя проекта
project.version() -> String     // Версия проекта
project.target() -> String      // Целевая платформа (linux, windows, macos)
project.architecture() -> String // Архитектура (x86_64, arm64)
```

**Флаги компиляции:**
```efen
use project::*

project.hasFeature(name: String) -> Bool    // Включена ли feature
project.getConfig(key: String) -> String?   // Значение config параметра
```

#### Примеры использования

**Пример 1: Условная компиляция по режиму**

```efen
use project::*

meta fn smartAssert(condition: Bool, message: String) -> InlineClosure {
    if project.isDebug() {
        // В debug - полная проверка с детальной информацией
        return inline {
            if !condition {
                println("Assertion failed: ${message}")
                println("Location: ${location.file}:${location.line}")
                debugBreak()
            }
        }
    } else if project.isRelease() {
        // В release - только логирование
        return inline {
            if !condition {
                logError("Assertion failed: ${message}")
            }
        }
    }
}
```

**Пример 2: Профилирование только в debug**

```efen
use project::*

meta fn profile(name: String, code: InlineClosure) -> InlineClosure {
    if project.isDebug() {
        return inline {
            let startTime = Timer.now()
            let startMem = Runtime.getMemoryUsage()

            ${code}

            let duration = Timer.now() - startTime
            let memUsed = Runtime.getMemoryUsage() - startMem
            println("Profile '${name}': ${duration}ms, ${memUsed} bytes")
        }
    } else {
        // В release - просто выполняем код без профилирования
        return inline {
            ${code}
        }
    }
}

// Использование - два параметра
profile("data processing", code {
    processLargeDataset()
})
```

**Пример 3: Feature-based compilation**

```efen
use project::*

meta fn withFeature(featureName: comptime String, code: InlineClosure) -> InlineClosure {
    if project.hasFeature(featureName) {
        return inline {
            ${code}
        }
    } else {
        return inline { }
    }
}

// Использование - два параметра
withFeature("experimental_api", code {
    useExperimentalFeature()
})
```

**Пример 4: Platform-specific code**

```efen
use project::*

meta fn platformSpecific -> InlineClosure {
    let target = project.target()

    if target == "windows" {
        return inline {
            useWindowsAPI()
        }
    } else if target == "linux" {
        return inline {
            useLinuxAPI()
        }
    } else if target == "macos" {
        return inline {
            useMacOSAPI()
        }
    } else {
        compileError("Unsupported platform: ${target}")
    }
}
```

**Пример 5: Версионирование**

```efen
use project::*

meta fn requireVersion(minVersion: comptime String) -> InlineClosure {
    let currentVersion = project.version()

    if !versionIsAtLeast(currentVersion, minVersion) {
        compileError("Project version ${currentVersion} is below required ${minVersion}")
    }

    return inline { }
}

// Использование
requireVersion("1.5.0")
```

**Пример 6: Оптимизация по уровню**

```efen
use project::*

meta fn optimizedLoop(body: Statement) -> InlineClosure {
    let optLevel = project.optimizationLevel()

    if optLevel >= 2 {
        // Агрессивная оптимизация
        return inline {
            @vectorize
            @unroll(4)
            ${body}
        }
    } else {
        // Обычное выполнение
        return inline {
            ${body}
        }
    }
}
```

#### Преимущества использования `project`

**1. Читаемость**
```efen
// ❌ Магические константы
if __BUILD_MODE__ == "debug" { ... }

// ✅ Ясный API
if project.isDebug() { ... }
```

**2. Типобезопасность**
```efen
// ❌ Строковое сравнение - можно ошибиться
if __BUILD_MODE__ == "debuf" { ... }  // Опечатка!

// ✅ Функция - проверка компилятором
if project.isDebug() { ... }  // Типобезопасно
```

**3. Расширяемость**
```efen
// Легко добавить новые проверки
if project.isDebug() && project.hasFeature("profiling") {
    // ...
}
```

**4. Консистентность**
```efen
// Единый способ доступа к информации о проекте
project.name()
project.version()
project.target()
project.isDebug()
```

### Доступ к Compile-time API

```efen
meta fn validateInterface(type: Type) -> InlineClosure {
    use compiler::*

    if !type.isInterface() {
        compileError("Expected interface type, got ${type.getName()}")
    }

    let methods = type.getMethods()
    return inline {
        println("Interface ${type.getName()} has ${methods.count} methods")
    }
}
```

## Безопасность и ограничения

### Что МОЖНО делать

✅ **Создавать локальные переменные** внутри inline closure
```efen
meta fn example -> InlineClosure {
    return inline {
        let temp = 42  // OK - локальная переменная
        temp * 2
    }
}
```

✅ **Принимать параметры** и возвращать значения
```efen
meta fn calculate(x: Int, y: Int) -> InlineClosure {
    return inline {
        x + y  // OK - работает с параметрами
    }
}
```

✅ **Захватывать переменные явно** через параметры
```efen
meta fn increment(value: var Int) -> InlineClosure {
    return inline {
        value += 1  // OK - явный параметр
    }
}
```

### Что НЕЛЬЗЯ делать

❌ **Создавать переменные в окружении вызова**
```efen
// НЕВОЗМОЖНО в Efen!
// Inline closure не может создать переменную в вызывающем коде
```

❌ **Изменять переменные окружения неявно**
```efen
let x = 10
SomeMeta()  // НЕ может изменить x без явной передачи
```

❌ **Генерировать сырой код**
```efen
// В Efen нет механизма сырой вставки кода
// Весь код проходит через inline closure
```

### Преимущества ограничений

**Предсказуемость**
```efen
let temp = "important data"

// Всегда безопасно - temp не может быть затёрт
SomeMetafunction()

// temp всё ещё содержит "important data"
```

**Явные контракты**
```efen
meta fn modify(x: var Int) -> InlineClosure {  // Явно: модифицирует x
    return inline { x += 1 }
}

meta fn read(x: Int) -> InlineClosure {  // Явно: только читает x
    return inline { x * 2 }
}
```

**Простота отладки**
```efen
// Ошибка в inline closure имеет чёткий стек вызовов
// Нет "магических" переменных
// Всё прозрачно и отлаживается как обычный код
```

## Сравнение подходов

### Проблемный подход (как в других языках)

```cpp
// C++ макрос
#define SWAP(a, b) \
    do { \
        auto temp = a; \
        a = b; \
        b = temp; \
    } while(0)

// Проблема:
auto temp = getUserData();
SWAP(x, y);  // ОШИБКА! Конфликт temp
```

### Подход Efen

```efen
meta fn swap(a: var Int, b: var Int) -> InlineClosure {
    return inline {
        let temp = a  // Изолированная область видимости
        a = b
        b = temp
    }
}

// Безопасно:
let temp = getUserData()
swap(x, y)  // OK! Нет конфликта
```

### Сравнение с генерацией кода

**Другие языки - сырая вставка кода:**
```cpp
// C++ - код вставляется напрямую в окружение
#define WITH_LOGGING(code) \
    printf("Start\n"); \
    code; \
    printf("End\n");

// Проблема:
WITH_LOGGING(doWork());  // Вставляется сырой код
```

**Efen - placeholders в inline closure:**
```efen
// Efen - код встраивается В closure
meta fn withLogging(code: InlineClosure) -> InlineClosure {
    return inline {
        println("Start")
        ${code}  // Вставка ВНУТРИ closure
        println("End")
    }
}

// Безопасно - closure изолирует код
withLogging => { doWork() }
```

**Ключевое отличие:**
- ❌ C++ макрос вставляет код **в место вызова** (загрязняет окружение)
- ✅ Efen placeholder вставляет код **внутрь closure** (изолированная область)

### Табличное сравнение

| Аспект | Сырая генерация кода | Inline Closure (Efen) |
|--------|---------------------|----------------------|
| **Область видимости** | Разрушает окружение | Изолирована |
| **Конфликты имён** | Возможны | Невозможны |
| **Изменение окружения** | Неявное | Только через параметры |
| **Генерация кода** | Прямая вставка | Placeholders в closure |
| **Отладка** | Сложная | Простая |
| **Безопасность типов** | Ограниченная | Полная |
| **Предсказуемость** | Низкая | Высокая |
| **Производительность** | Высокая | Высокая (inline) |

## Продвинутые паттерны

### 1. Композиция метафункций

```efen
meta fn logAndBenchmark(name: comptime String, code: InlineClosure) -> InlineClosure {
    return inline {
        log("INFO", "Starting ${name}")
        benchmark(name, code)
        log("INFO", "Finished ${name}")
    }
}

// Использование
logAndBenchmark("data processing") => {
    processLargeDataset()
}
```

### 2. Условная генерация

```efen
meta fn smartAssert(condition: Bool, level: comptime String) -> InlineClosure {
    if level == "debug" {
        return inline {
            if !condition {
                println("Assertion failed at ${location.file}:${location.line}")
                debugBreak()
            }
        }
    } else if level == "production" {
        return inline {
            if !condition {
                logError("Assertion failed")
            }
        }
    } else {
        return inline { }  // Отключено
    }
}
```

### 3. Генерация типизированных функций

```efen
meta fn createValidator<T>(
    validationFn: inline (T) -> Bool,
    errorMsg: comptime String
) -> InlineClosure {
    return inline (value: T) -> T {
        if !validationFn(value) {
            throw ValidationError(errorMsg)
        }
        return value
    }
}

// Использование
let validateAge = CreateValidator<Int>(
    validationFn: => (age) { age >= 0 && age <= 150 },
    errorMsg: "Age must be between 0 and 150"
)

let age = validateAge(userInput)
```

### 4. Автоматическое управление ресурсами

```efen
meta fn withResource<R: Disposable, T>(
    acquire: inline -> R,
    use: inline (R) -> T
) -> InlineClosure {
    return inline {
        var resource: R? = null
        var result: T? = null
        var error: Error? = null

        try {
            resource = acquire()
            result = use(resource!)
        } catch e: Error {
            error = e
        } finally {
            resource?.dispose()
        }

        if let err = error {
            throw err
        }

        return result!
    }
}
```

### 5. Генерация state machine

```efen
meta fn stateMachine(
    states: comptime [String],
    initialState: comptime String
) -> InlineClosure {
    if !states.contains(initialState) {
        compileError("Initial state must be in states list")
    }

    return inline {
        var currentState = initialState
        var handlers: [String: () -> Void] = [:]

        fn on(state: String, handler: () -> Void) {
            handlers[state] = handler
        }

        fn transition(newState: String) {
            if !states.contains(newState) {
                throw InvalidStateError("Unknown state: ${newState}")
            }
            currentState = newState
            handlers[currentState]?()
        }

        fn getState -> String {
            return currentState
        }

        (on, transition, getState)
    }
}
```

## Интеграция с другими возможностями Efen

### С декораторами

```efen
meta fn createLogDecorator -> Decorator {
    return Decorator => (method: Method) {
        let methodName = method.getName()

        return inline {
            log("INFO", "Entering ${methodName}")
            let result = method()
            log("INFO", "Exiting ${methodName}")
            result
        }
    }
}

@createLogDecorator()
fn processData {
    // ...
}
```

### С контрактами

```efen
contract Validated {
    meta fn validate(value: Self) -> InlineClosure {
        return inline {
            if !value.isValid() {
                throw ValidationError("Invalid value")
            }
            value
        }
    }
}
```

### С generics

```efen
meta fn createOption<T>(hasValue: Bool, value: T) -> InlineClosure {
    return inline {
        if hasValue {
            Some(value)
        } else {
            None
        }
    }
}
```

## Best Practices

### 1. Используйте `comptime` для константных параметров

```efen
// ✅ Хорошо - константа вычисляется во время компиляции
meta fn repeatMessage(count: comptime Int, msg: String) -> InlineClosure

// ❌ Плохо - теряется оптимизация
meta fn repeatMessage(count: Int, msg: String) -> InlineClosure
```

### 2. Явно указывайте типы для сложных inline closure

```efen
// ✅ Хорошо - типы понятны
meta fn transform<T, R>(
    value: T,
    fn: inline (T) -> R
) -> InlineClosure

// ❌ Плохо - типы неясны
meta fn transform(value: Any, fn: inline) -> InlineClosure
```

### 3. Следите за соответствием сигнатур inline closure

**Компилятор строго проверяет типы!** Inline closure должно иметь правильную сигнатуру:

```efen
// ✅ Правильно - inline closure принимает String, возвращает Int
meta fn stringLength -> InlineClosure {
    return inline (s: String) -> Int {
        s.length()
    }
}

let lengthFn = stringLength()  // Тип: (String) -> Int
let len = lengthFn("hello")    // ✅ OK - 5

// ❌ Ошибка - несоответствие типов
meta fn badLength -> InlineClosure {
    return inline (s: String) -> Int {
        s.length()
    }
}

let result = badLength()  // ❌ ОШИБКА КОМПИЛЯЦИИ
// Expected: () -> T (вызов без параметров)
// Got: (String) -> Int
```

**Правильные варианты в зависимости от использования:**

```efen
// Вариант A: Statement - inline closure без параметров
meta fn logMessage(msg: String) -> InlineClosure {
    return inline {  // () -> Void
        println(msg)
    }
}
logMessage("test")  // ✅ OK - вызов как statement

// Вариант B: Higher-order function - inline closure с параметрами
meta fn createLogger -> InlineClosure {
    return inline (msg: String) -> Void {  // (String) -> Void
        println(msg)
    }
}
let logger = createLogger()  // ✅ OK - получаем функцию
logger("test")               // ✅ OK - вызываем функцию
```

### 4. Документируйте метафункции

```efen
/// Генерирует код логирования с информацией о месте вызова
///
/// # Параметры
/// - level: уровень логирования (compile-time константа)
/// - message: сообщение для логирования (runtime значение)
///
/// # Пример
/// ```efen
/// log("INFO", "User logged in: " + username)
/// ```
///
/// # Компилируется в
/// ```efen
/// if Logger.isEnabled("INFO") {
///     Logger.log("INFO", "main.efen", 42, "User logged in: " + username)
/// }
/// ```
meta fn log(level: comptime String, message: String) -> InlineClosure {
    // ...
}
```

### 4. Проверяйте параметры во время компиляции

```efen
meta fn validatedRange(min: comptime Int, max: comptime Int) -> InlineClosure {
    if min >= max {
        compileError("min must be less than max")
    }

    return inline (value: Int) -> Int {
        if value < min || value > max {
            throw RangeError("Value ${value} out of range [${min}, ${max}]")
        }
        return value
    }
}
```

### 5. Избегайте сложной логики в inline closure

```efen
// ✅ Хорошо - сложная логика во время компиляции
meta fn optimizedCase(value: comptime String) -> InlineClosure {
    let result = complexCompileTimeLogic(value)  // Во время компиляции
    return inline {
        result  // Простая константа во время runtime
    }
}

// ❌ Плохо - вся сложность во время runtime
meta fn optimizedCase(value: String) -> InlineClosure {
    return inline {
        complexRuntimeLogic(value)  // Не оптимально
    }
}
```

## Встроенные метафункции

Efen предоставляет набор встроенных метафункций:

### Информация о типах

```efen
meta fn sizeOf(type: Type) -> InlineClosure  // Размер типа в байтах
meta fn alignOf(type: Type) -> InlineClosure  // Выравнивание типа
meta fn typeName(type: Type) -> InlineClosure  // Имя типа как строка
```

### Compile-time утилиты

```efen
meta fn static(expr: comptime Expr) -> InlineClosure  // Вычисляет выражение во время компиляции
meta fn compileLog(message: comptime String) -> InlineClosure  // Выводит сообщение во время компиляции
meta fn compileError(message: comptime String) -> Never  // Ошибка компиляции
meta fn compileWarning(message: comptime String) -> InlineClosure  // Предупреждение компиляции
```

### Отладка

```efen
meta fn unreachable -> InlineClosure  // Помечает недостижимый код
meta fn todo(message: comptime String = "not implemented") -> InlineClosure  // Временная заглушка
```

## Производительность

### Inline-оптимизация

Компилятор **всегда** встраивает inline closure:

```efen
let result = max(a, b)

// Компилируется в:
let result = if a > b { a } else { b }

// Нет накладных расходов на вызов функции!
```

### Zero-cost abstraction

Метафункции — это **zero-cost abstraction**:

```efen
// Код с метафункцией
let x = assert(value > 0, "positive value required")
let y = square(x)

// Компилируется в код без накладных расходов:
if !(value > 0) {
    throw AssertionError("positive value required")
}
let x = value
let y = x * x
```

### Оптимизация на основе compile-time информации

```efen
meta fn divideByPowerOfTwo(value: Int, exponent: comptime Int) -> InlineClosure {
    // Оптимизация: деление на степень двойки = побитовый сдвиг
    return inline {
        value >> exponent  // Быстрее, чем value / (1 << exponent)
    }
}
```

## Заключение

**Метафункции с Inline Closure** в Efen предоставляют:

- **Безопасность** — нет сырой вставки кода, нет конфликтов имён
- **Гибкость** — statement placeholders позволяют генерировать код, оставаясь в безопасных рамках closure
- **Предсказуемость** — явные контракты через типы и параметры
- **Производительность** — zero-cost abstraction с автоматическим inline
- **Простоту** — работают как обычные функции и замыкания
- **Мощность** — полный доступ к compile-time API и контексту

**Ключевая инновация:** Statement placeholders (`${code}`) работают **только внутри inline closure**, что даёт:
- ✅ Возможность динамической генерации кода
- ✅ Полную изоляцию от окружения вызова
- ✅ Безопасность на уровне компиляции

Это принципиально отличает Efen от других языков с метапрограммированием, обеспечивая уникальный баланс между выразительностью и безопасностью.

## См. также

- [Замыкания (Closures)](../closure.md) — Подробно о замыканиях в Efen
- [Compile-time API](index.md) — API времени компиляции
- [Декораторы](../decorators.md) — Метапрограммирование на уровне определений
- [Контракты](../contracts.md) — Статические проверки во время компиляции
