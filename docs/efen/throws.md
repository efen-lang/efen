# Throws Contracts

> **Throws контракт** — система автоматического отслеживания исключений с точками ответственности,
> обеспечивающая статический контроль обработки ошибок без явного указания throws в каждой функции.

## Зачем?

В традиционных системах обработки исключений существует несколько проблем:

1. **Избыточная декларация**: Необходимость писать `throws` в каждой функции
2. **Сложность рефакторинга**: При добавлении нового исключения нужно менять все сигнатуры
3. **Неясная ответственность**: Непонятно, где именно должно обрабатываться исключение
4. **Дублирование информации**: Список исключений копируется по всей цепочке

Efen решает эти проблемы через **автоматическое распространение** и **точки ответственности**.

## Основная концепция

Функции автоматически наследуют все исключения от вызываемых функций:

```efen
class DatabaseError extends Exception { }
class ValidationError extends Exception { }

fn queryDatabase {
    throw DatabaseError("Connection failed")
}

fn validateData(data: String) {
    throw ValidationError("Empty data")
}

fn processData(data: String) {
    // Список throws выводится автоматически.
    validateData(data)
    queryDatabase()
    // processData автоматически может бросить: ValidationError, DatabaseError
}
```

## Синтаксис

### Без throws (автоматическое наследование)

```efen
fn process {
    operation()  // Наследует все исключения
}
```

### nothrows (точка ответственности)

```efen
fn handler nothrows {
    try {
        process()
    } catch (e: Error) {
        logError(e)
    }
}
```

### throws (добавление исключения)

```efen
fn processWithExtra throws CustomError {
    operation()          // Наследует исключения
    throw CustomError()  // Добавляет своё
}
```

Generic-функция может переносить точный pack исключений callback без сведения к
общему базовому типу:

```efen
fn map<T, U, ...Errors>(
    items: [T],
    transform: (T) -> U throws ...Errors
) -> [U] throws ...Errors
    where ...Errors: Exception
{
    // ...
}
```

`Errors` является compile-time массивом типов, совместимых с `Exception`. При
инстанциации pack связывается с опубликованным итоговым `throws` переданной
функции и раскрывается в `throws` функции `map`. Если callable прошёл через тип,
который не сохранил его точное итоговое множество исключений, вывести `Errors`
из такого значения нельзя: требуется явный аргумент либо более точная
сигнатура callable.

### throws only (ограничение исключений)

```efen
fn limitExceptions throws only NetworkError {
    try {
        operation()  // Все исключения должны быть обработаны
    } catch (e: Exception) {
        throw NetworkError(cause: e)
    }
}
```

## Точки ответственности

> **Точка ответственности** — функция, которая не может выбросить исключения (или ограничивает их).

Два вида точек ответственности:
1. **Полный запрет** (`nothrows`) — функция не может бросить исключения
2. **Ограничение** (`throws only`) — функция может бросить только указанные исключения

## Responsibility зоны

```efen
responsibility DatabaseLayer handles DatabaseError {
    
    fn query {
        throw QueryError()  // Свободно внутри зоны
    }
    
    // На границе зоны - точка ответственности
    fn publicAPI nothrows {
        try {
            query()
        } catch (e: DatabaseError) {
            logError(e)
        }
    }
}
```

`responsibility X handles E` и `region handles E` решают одну задачу на разных
масштабах: зона — это объявление, границей которого служат её функции с
`nothrows`, а регион — блок, который проверяется на каждом выходе из него.

## Сравнение режимов

| Режим               | Точка ответственности | Наследование | Добавление | Обработка требуется |
|---------------------|-----------------------|--------------|------------|---------------------|
| (без объявления)    | ❌                     | ✅ Все        | ❌          | ❌                   |
| `throws Error`      | ❌                     | ✅ Все        | ✅ Error    | ❌                   |
| `throws only Error` | ✅                     | ❌            | ✅ Error    | ✅ Все кроме Error   |
| `nothrows`          | ✅                     | ❌            | ❌          | ✅ Все               |

## Управление распространением

### isolated функция

```efen
isolated fn load throws IOError {
    readFile() // Допустимо: IOError объявлен явно.
}
```

`isolated` запрещает не сами исключения, а их неявное добавление к контракту.
Каждое исключение должно быть перечислено в `throws` либо обработано внутри
функции. Вызов, который потребовал бы расширить `throws`, является ошибкой.

### region nothrows

Блок `without throws` из языка убран; его место занял регион `nothrows`
([`code-regions.md`](code-regions.md)):

```efen
fn process {
    validate()  // ValidationError

    region nothrows {
        try {
            saveData()  // DatabaseError - обработан здесь
        } catch e: DatabaseError {
            logError(e)
        }
    }

    notify()  // NotificationError
}
// process может бросить: ValidationError, NotificationError (но НЕ DatabaseError)
```

Выход по `return` и `break` проверяется так же, как конец блока: до него не
должно быть непойманного выброса.

## Контракты на обработку исключений

`Efen` использует контракты для описания возможностей обработки исключений.
Контракт может требовать обработки определённых исключений. Например:

```efen
contract ErrorHandler extends CatchRules {
    required catch DatabaseError
}
```

Чтобы контракт работал правильно, он должен наследовать `CatchRules`, 
который позволяет использовать синтаксис `required catch`
или `catch`.

Применить контракт к функции можно с помощью атрибута `conforms`:

```efen
@conforms ErrorHandler
fn dataOperation {
    try {
        queryDatabase()
    } catch (e: DatabaseError) {
        // Обработка DatabaseError обязательна
        logError(e)
    }
}
```

### Ограничение обработки исключений

Обычно любая функция может обрабатывать исключения, которые она **не добавляет**.
Однако, иногда требуется создать исключение, 
которое может быть обработано только в определённых точках ответственности.

Например, таким исключением может быть CancellationException, которое может быть обработано 
только специальным кодом.

Для того чтобы ограничить обработку исключения,
следует использовать контракт `CatchRestriction`.
Он указывает компилятору, что это исключение может быть поймано 
только в функциях, которые поддерживают контракт, где указана возможность обработки этого исключения.

```efen
contract CancellationHandler extends CatchRules {
    required catch CancellationException
}

class CancellationException extends Exception {
    conforms CatchRestriction
    
}
```

Если исключение объявляет `MustHandle` вместе с `CatchRestriction`, оба
требования действуют сразу: поймать обязан непосредственный вызывающий, и он же
обязан быть помечен `@conforms` контракта-обработчика.

## Примеры

### Пример 1: Автоматическое распространение

```efen
fn funcC {
    throw ErrorC()
}

fn funcB {
    funcC()  // ErrorC автоматически наследуется
}

fn main nothrows {
    try {
        funcB()
    } catch (e: ErrorC) {
        print("Handled")
    }
}
```

### Пример 2: Многоуровневая архитектура

```efen
// Слой данных
responsibility DataLayer handles DataError {
    fn query {
        throw DatabaseError()
    }
    
    fn publicSave -> Bool nothrows {
        try {
            query()
            return true
        } catch {
            return false
        }
    }
}

// Бизнес-логика
responsibility BusinessLayer handles BusinessError {
    fn register {
        DataLayer.publicSave()  // nothrows
        throw RegistrationError()
    }
    
    fn publicRegister nothrows {
        try {
            register()
        } catch {
            logError()
        }
    }
}
```

## Интеграция с контекстами

```efen
context ErrorHandler {
    let logger: Logger
}

responsibility Service handles ServiceError in ErrorHandler {
    fn process {
        try {
            operation()
        } catch (e: ServiceError) {
            %logger.error(e)
            throw e
        }
    }
}
```

## Throws для интерфейсов

```efen
interface Repository {
    fn find(id: Int) nothrows
    fn save(entity: Entity) throws only PersistenceError
}

class UserRepository {
    conforms Repository
    
    fn find(id: Int) nothrows {
        // Обязаны обработать все исключения
    }
}
```

## Ковариантность

При переопределении можно только **сужать** исключения:

```efen
interface Service {
    fn process throws only ErrorA, ErrorB
}

class ConcreteService implements Service {
    fn process throws only ErrorA {  // ✅ Убрали ErrorB
    }
}

class BrokenService implements Service {
    fn process throws only ErrorA, ErrorB, ErrorC {  // ❌ Добавили ErrorC
    }
}
```

## Must-handle исключения

Обязанность поймать исключение объявляется у типа или у области. Отдельной
формы `throws!` у функции нет: она дублировала типовой `MustHandle`.

У типа она записывается контрактом `MustHandle` в объявлении класса исключения —
той же формой, что `CatchRestriction` выше. Обязанность действует везде, где это
исключение возникает, независимо от сигнатуры функции:

```efen
class CriticalError extends Exception {
    conforms MustHandle
}
```

Функция перечисляет исключение обычным `throws`; `MustHandle` типа заставляет
вызывающую сторону обработать его по описанному ниже правилу:

```efen
fn critical throws CriticalError {
    throw CriticalError()
}
```

У области обязанность задаёт свойство региона `handles`, а запрет исключений
целиком — свойство `nothrows`; оба описаны в разделе «Гарантии по исключениям»
документа [«Области кода»](code-regions.md):

```efen
region handles CriticalError {
    try {
        critical()
    } catch e: CriticalError {
        handleCritical(e)
    }
}
```

### Что значит «немедленно»

`MustHandle` требует явного перехвата в непосредственном вызывающем. Обработчик
может поглотить исключение либо явно бросить его снова. Повторный `throw` не
является молчаливым распространением: он создаёт новый выход того же типа и
сохраняет его `MustHandle` для следующего вызывающего:

```efen
fn rethrowing throws CriticalError {
    try {
        critical()
    } catch e: CriticalError {
        logError(e)
        throw e
    }
}
```

Функция, которая пробрасывает такое исключение, объявляет обычный `throws E`.
Отдельный `!` не нужен: `MustHandle` сохраняется свойством типа `E`, поэтому
следующий непосредственный вызывающий также обязан поставить обработчик.

Немедленно — значит в той же функции, где лексически написан вызов. Пропустить
такое исключение дальше по стеку молча нельзя:

```efen
fn caller {
    // ❌ Ошибка: CriticalError должен быть обработан немедленно
    critical()
}

fn correctCaller {
    try {
        critical()
    } catch e: CriticalError {
        handleCritical(e)
    }
    // CriticalError НЕ распространяется дальше
}
```

Замыкание, которое не покидает функцию, для этого правила прозрачно: оно
выполняется внутри вызова, поэтому `try` вокруг вызова требование выполняет.

```efen
fn correctInClosure(items: [Item]) {
    try {
        items.forEach => critical($0)
    } catch e: CriticalError {
        handleCritical(e)
    }
}
```

Тело `defer` выполняется на выходе из функции, а не на месте инструкции, поэтому
`try` вокруг самой инструкции его не покрывает. `catch` пишется внутри тела
`defer`:

```efen
fn withDefer(path: String) {
    defer {
        try {
            critical()
        } catch e: CriticalError {
            handleCritical(e)
        }
    }

    process(path)
}
```

Обычное исключение из `defer` может выйти наружу. Если другое исключение уже
покидает область, оно остаётся главным, а новая ошибка добавляется в его
упорядоченный список `suppressed`. Если активного исключения нет, первая ошибка
cleanup становится главной; последующие ошибки остальных `defer` добавляются к
ней. Все тела продолжают выполняться в порядке LIFO.

`cause` и `suppressed` имеют разный смысл. `cause` задаётся явно, когда одна
ошибка объясняет другую. `suppressed` хранит независимые ошибки cleanup,
которым не разрешено заменить уже выбранный основной выход. Обычный `catch`
сопоставляется с главным исключением; прикреплённые ошибки доступны через
`error.suppressed` и показываются диагностикой вместе с ним.

Для `MustHandle` сохраняется более сильное правило выше: такое исключение
нельзя только прикрепить к цепочке, его нужно явно поймать внутри `defer`.

Блок `flow { }` для этого правила считается отдельной функцией, а его оператор
`catch Err` — обработчиком. Выбор по типу в `catch Err` определяет раздел
«Оператор catch» в [`flow.md`](flow.md).

Тело `flow generator` выполняется на вызове `next()`, то есть после того, как
вызов генератора вернул управление. Поэтому оно тоже считается отдельной
функцией — так же, как `@escaping`-замыкание.

`@escaping`-замыкание переживает вызов и выполняется отдельно, поэтому `try`
вокруг его регистрации ничего не ловит. Обработчик пишется внутри самого
замыкания:

```efen
fn wrongInEscaping(register: (@escaping () -> Void) -> Void) {
    try {
        // ❌ Ошибка: вызов уйдёт за пределы try
        register(() => critical())
    } catch e: CriticalError {
        handleCritical(e)
    }
}

fn correctInEscaping(register: (@escaping () -> Void) -> Void) {
    register(() => {
        try {
            critical()
        } catch e: CriticalError {
            handleCritical(e)
        }
    })
}
```

### Сложение требований

Требования складываются. `MustHandle`, `required catch` контракта и `region
handles` должны быть выполнены все; старшинства между ними нет, и выполнение
одного не снимает остальные.

`throws only E`, объявленный или выведенный `throws E` сохраняют `MustHandle`
типа `E` через сигнатуру. На каждой непосредственной границе вызова исключение
должно быть обработано; обычный `throws` не снимает эту обязанность и не требует
дублирующего знака `!`.

## Диагностика

```efen
fn handler nothrows {
    processData()
}

// Ошибка компиляции:
// error: function 'handler' is nothrows but may throw:
//   - DatabaseError (from processData -> queryDB)
//   - ValidationError (from processData -> validate)
```

## Правила

1. **Автоматическое распространение**: Исключения автоматически наследуются
2. **Точки ответственности**: `nothrows` и `throws only` обязаны обработать исключения
3. **Два режима throws**:
   - `throws Error` — **добавляет** Error
   - `throws only Error` — **ограничивает** до Error
4. **Ковариантность**: Можно только сужать исключения при переопределении
5. **Responsibility**: Зоны ответственности с автоматической проверкой на границах

## Преимущества

- ✅ Нет декларативного мусора
- ✅ Автоматическое отслеживание
- ✅ Явные границы ответственности
- ✅ Гибкость: `throws` vs `throws only`
- ✅ Простой рефакторинг
- ✅ Статическая проверка

## См. также

- [Контексты](context-and-effects.md) — похожая модель распространения
- [Области кода](code-regions.md) — `region handles` и `region nothrows`
- [Контракты](contracts.md)
- [Интерфейсы](interfaces.md)
