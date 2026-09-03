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

fn queryDatabase() {
    throw DatabaseError("Connection failed")
}

fn validateData(data: String) {
    throw ValidationError("Empty data")
}

fn processData(data: String) {
    // НЕ НУЖНО писать throws!
    validateData(data)
    queryDatabase()
    // processData автоматически может бросить: ValidationError, DatabaseError
}
```

## Синтаксис

### Без throws (автоматическое наследование)

```efen
fn process() {
    operation()  // Наследует все исключения
}
```

### nothrows (точка ответственности)

```efen
fn handler() nothrows {
    try {
        process()
    } catch (e: Error) {
        logError(e)
    }
}
```

### throws (добавление исключения)

```efen
fn processWithExtra() throws CustomError {
    operation()          // Наследует исключения
    throw CustomError()  // Добавляет своё
}
```

### throws only (ограничение исключений)

```efen
fn limitExceptions() throws only NetworkError {
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
    
    fn query() {
        throw QueryError()  // Свободно внутри зоны
    }
    
    // На границе зоны - точка ответственности
    fn publicAPI() nothrows {
        try {
            query()
        } catch (e: DatabaseError) {
            logError(e)
        }
    }
}
```

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
isolated fn isolatedFunc() {
    // Нельзя вызывать функции с исключениями
}
```

### without throws блок

```efen
fn process() {
    validate()  // ValidationError
    
    without throws {
        try {
            saveData()  // DatabaseError - обработан здесь
        } catch (e: DatabaseError) {
            logError(e)
        }
    }
    
    notify()  // NotificationError
}
// process может бросить: ValidationError, NotificationError (но НЕ DatabaseError)
```

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
fn dataOperation() {
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

## Примеры

### Пример 1: Автоматическое распространение

```efen
fn funcC() {
    throw ErrorC()
}

fn funcB() {
    funcC()  // ErrorC автоматически наследуется
}

fn main() nothrows {
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
    fn query() {
        throw DatabaseError()
    }
    
    fn publicSave() -> Bool nothrows {
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
    fn register() {
        DataLayer.publicSave()  // nothrows
        throw RegistrationError()
    }
    
    fn publicRegister() nothrows {
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
    fn process() {
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
    fn process() throws only ErrorA, ErrorB
}

class ConcreteService implements Service {
    fn process() throws only ErrorA {  // ✅ Убрали ErrorB
    }
}

class BrokenService implements Service {
    fn process() throws only ErrorA, ErrorB, ErrorC {  // ❌ Добавили ErrorC
    }
}
```

## Must-handle исключения

```efen
fn critical() throws! CriticalError {
    throw CriticalError()
}

fn caller() {
    // ❌ Ошибка: CriticalError должен быть обработан немедленно
    critical()
}

fn correctCaller() {
    try {
        critical()
    } catch (e: CriticalError) {
        handleCritical(e)
    }
    // CriticalError НЕ распространяется дальше
}
```

## Диагностика

```efen
fn handler() nothrows {
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
- [Контракты](contracts.md)
- [Интерфейсы](interfaces.md)
