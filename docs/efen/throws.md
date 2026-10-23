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
class DatabaseError: Exception { }
class ValidationError: Exception { }

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
    } catch e: Error {
        logError(e)
    }
}
```

### nofail (системная точка ответственности)

Исключение, класс которого объявляет контракт `Fault`, — **сбой**: отказ машины
или проверяемой операции, который код бизнес-уровня не может предотвратить в
месте, где он случился. Сбои стандартной библиотеки: `AllocationError`,
`OverflowError`, `DivisionByZeroError`. Контракт наследуется подклассами.

```efen
class AllocationError: Exception {
    conforms Fault
}
```

`nothrows` запрещает все исключения, кроме сбоев: сбой проходит сквозь функцию
и остаётся в её сводке. `nofail` запрещает всё, сбои тоже. Коротко: из
`nothrows` не выходят ошибки, из `nofail` не выходит ничего.

```efen
fn handleRequest(req: Request) -> Response nothrows {
    try {
        return render(load(req.id))
    } catch e: NotFound {
        return Response.notFound()
    }
    // AllocationError и OverflowError могут выйти: это сбои
}

fn release(block: Pointer, size: Int) nofail {
    try {
        used = used - size
    } catch e: OverflowError {
        corrupted = true
    }
    // ничего не выходит
}
```

`nofail` пишут в системном коде: аллокатор, рантайм, деструкторы. `deinit` и
`dispose` являются `nofail` без объявления. Функция, которую вызывает код на C,
обязана быть `nofail`: иначе ошибка компиляции.

Правила:

1. `nofail` строже `nothrows`: реализация `nofail` может заменить объявление
   `nothrows`, обратное запрещено.
2. `throws only E` пропускает сбои, как `nothrows`. Если список называет сбой,
   он строг и для сбоев: `throws only AllocationError` не выпускает
   `OverflowError`.
3. Сбой не может быть `Expected` и не может быть `MustHandle`.
4. Исчерпание стека тоже сбой, но `nofail` от него не защищает: защитная
   страница срабатывает на любом вызове.
5. Сбой, брошенный в `defer`, пока функцию покидает обычное исключение, не
   уходит в `suppressed`: главным становится сбой, обычное исключение
   прикрепляется к нему.
6. Общий `catch` и `catch e: Exception` ловят и сбои.

Решение Edmond от 2026-10-23. Правило 6 и право любого модуля объявлять свои
сбои пока приняты по умолчанию и ждут его подтверждения.

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
fn map(items: [T], transform: (T) -> U throws ...Errors) -> [U] throws ...Errors {
    generic T: Type
    generic U: Type
    generic ...Errors: Type
    where ...Errors: Exception

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
    } catch e: Exception {
        throw NetworkError(cause: e)
    }
}
```

## Точки ответственности

> **Точка ответственности** — функция, которая не может выбросить исключения (или ограничивает их).

Три вида точек ответственности:
1. **Полный запрет** (`nofail`) — функция не может бросить ничего, сбои тоже
2. **Запрет ошибок** (`nothrows`) — функция не может бросить исключения, кроме сбоев
3. **Ограничение** (`throws only`) — функция может бросить только указанные исключения и сбои

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
        } catch e: DatabaseError {
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
| `throws only Error` | ✅                     | ❌            | ✅ Error    | ✅ Все кроме Error и сбоев |
| `nothrows`          | ✅                     | ❌            | ❌          | ✅ Все кроме сбоев   |
| `nofail`            | ✅                     | ❌            | ❌          | ✅ Все               |

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

`isolated` закрывает только эффекты. Состояния параметров, изменение структуры
памяти и источники ссылок компилятор выводит из тела `isolated` функции так же,
как из любой другой, и вызывающий их видит:

```efen
isolated fn prepare(file: mut File) { file.open() }   // выведено: file Closed >> Open

fn use(file: mut File) {
    prepare(file)
    file.read(4)   // допустимо: после prepare file в состоянии Open
}
```

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

Contract может уточнять другой contract через `:`:

```efen
contract ErrorHandler : CatchRules {
    required catch DatabaseError
}
```

`CatchRules` разрешает требования `required catch`.

Функция соответствует контракту через объявление `conforms` в теле:

```efen
fn dataOperation {
    conforms ErrorHandler

    try {
        queryDatabase()
    } catch e: DatabaseError {
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
contract CancellationHandler : CatchRules {
    required catch CancellationException
}

class CancellationException: Exception {
    conforms CatchRestriction
    
}
```

Если исключение объявляет `MustHandle` вместе с `CatchRestriction`, оба
требования действуют сразу: поймать обязан непосредственный вызывающий, и он же
обязан объявлять `conforms` контракта-обработчика.

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
    } catch e: ErrorC {
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
        } catch e: ServiceError {
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

class ConcreteService {
    implements Service

    fn process throws only ErrorA {  // ✅ Убрали ErrorB
    }
}

class BrokenService {
    implements Service

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
class CriticalError: Exception {
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
        items.forEach => critical(item)
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
функцией — так же, как сохранённое для последующего вызова замыкание.

Сохранённое замыкание переживает вызов регистрации и выполняется отдельно,
поэтому `try` вокруг регистрации ничего не ловит. Получатель выражает это право
модификатором `@escaping` в функциональном типе:

```efen
fn wrongForStoredCallback(register: (@escaping () -> Void) -> Void) {
    try {
        // ❌ Ошибка: вызов уйдёт за пределы try
        register => critical()
    } catch e: CriticalError {
        handleCritical(e)
    }
}

fn correctForStoredCallback(register: (() -> Void) -> Void) {
    register => {
        try {
            critical()
        } catch e: CriticalError {
            handleCritical(e)
        }
    }
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

## Как исключение передаётся: раскрутка стека и `Expected`

Для программы все исключения одинаковы: `throw`, `catch`, `finally` и
сводки `throws` работают одинаково. Различается только цена. По умолчанию
исключение передаётся раскруткой стека, как в C++: вызов, который ничего не
бросил, не выполняет ни одной лишней инструкции, а сам бросок дорогой —
обработчик ищется по таблицам, кадр за кадром. Так передаются редкие сбои:
нехватка памяти, переполнение, отмена.

Класс исключения, который объявляет контракт `Expected`, передаётся вторым
значением возврата, как `Result` в Rust: бросок почти бесплатный, но после
каждого вызова функции, которая может его бросить, стоит проверка. Так
передаются ожидаемые сбои обычной работы: нет ключа, неверный ввод, файл не
найден.

```efen
class NotFound: Exception {
    conforms Expected
}

fn lookup(key: String) -> Int {
    throw NotFound()        // возвращается вызывающему вторым значением
}

fn load() -> Pointer<Byte> {
    return allocate(4096)   // AllocationError раскручивает стек
}
```

Правила:

1. Без `Expected` исключение раскручивает стек. `AllocationError`, в том
   числе при создании экземпляра класса, раскручивает стек. Это обычное
   исключение: функция, которая создаёт экземпляр класса, может бросить
   `AllocationError` по своей сводке. Это сбой: функция `nofail`, которая
   неявно выделяет память, обязана поймать его явно, а `nothrows` его
   пропускает. Где компилятор доказал, что
   память уже есть (рост коллекции после `reserve`), бросок снимается.
2. `Expected` наследуется: подкласс класса с `Expected` тоже передаётся
   возвратом.
3. Функция может бросать исключения обоих видов сразу: `Expected` уходят
   возвратом, остальные раскруткой. Функция, которая не бросает `Expected`,
   сохраняет обычную сигнатуру.
4. Там, где раскрутки нет (песочница WebAssembly без обработки исключений),
   компилятор передаёт возвратом все исключения; поведение программы то же.

Решение Edmond от 2026-10-23. Реализация — amber dev/plans/S57.md.

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
2. **Точки ответственности**: `nofail` обязан обработать всё, `nothrows` и `throws only` — всё, кроме сбоев
3. **Два режима throws**:
   - `throws Error` — **добавляет** Error
   - `throws only Error` — **ограничивает** до Error
4. **Ковариантность**: Можно только сужать исключения при переопределении
5. **Responsibility**: Зоны ответственности с автоматической проверкой на границах
6. **Канал передачи**: по умолчанию раскрутка стека, `Expected` — вторым значением возврата

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
