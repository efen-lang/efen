# Алиасы типов (Type Aliases)

Алиасы типов в Efen позволяют создавать альтернативные имена для существующих типов, улучшая читаемость и поддерживаемость кода.

## Содержание

- [Ключевое слово type](#ключевое-слово-type)
- [Ключевое слово function](#ключевое-слово-function)
- [Дженерик-алиасы](#дженерик-алиасы)
- [Сложные типы](#сложные-типы)
- [Примеры использования](#примеры-использования)
- [Лучшие практики](#лучшие-практики)

## Ключевое слово type

Ключевое слово `type` используется для создания алиаса любого типа.

### Базовый синтаксис

```efen
type MyInt = Int
type UserID = String
type Timestamp = Int
```

### Использование

```efen
type UserID = String

fn getUser(id: UserID) -> User? {
    // ...
}

let userId: UserID = "user123"
let user = getUser(userId)
```

### Алиасы для примитивов

```efen
type Byte = Int8
type Word = Int16
type DWord = Int32
type QWord = Int64

type Percentage = Float  // 0.0 - 100.0
type Ratio = Float       // 0.0 - 1.0
```

### Алиасы для коллекций

```efen
type IntList = [Int]
type StringMap = [String: Any]
type Matrix = [[Float]]
```

## Ключевое слово function

Ключевое слово `function` специально предназначено для создания алиасов функциональных типов.

### Базовый синтаксис

```efen
function Handler = (Int) -> Void
function Predicate = (String) -> Bool
function Mapper = (Int) -> String
```

### Использование

```efen
function EventHandler = (Event) -> Void

class Button {
    var onClick: EventHandler?

    fn setClickHandler(handler: EventHandler) {
        onClick = handler
    }
}

let button = Button()
button.setClickHandler(fn(event) {
    echo "Button clicked!"
})
```

### Сложные функциональные типы

```efen
// Функция с несколькими параметрами
function Comparator = (Int, Int) -> Int

// Функция, возвращающая функцию
function HandlerFactory = (String) -> ((Event) -> Void)

// Функция с optional результатом
function Parser = (String) -> Result?
```

## Дженерик-алиасы

Алиасы типов могут быть дженериками.

### type с дженериками

```efen
type Optional<T> = T?
type Result<T> = (T | Error)
type Pair<T, U> = (T, U)
```

### function с дженериками

```efen
function Handler<T> = (T) -> Void
function Transformer<T, U> = (T) -> U
function Predicate<T> = (T) -> Bool
function Comparator<T> = (T, T) -> Int
```

### Использование дженерик-алиасов

```efen
function Mapper<T, U> = (T) -> U

fn map<T, U>(items: [T], mapper: Mapper<T, U>) -> [U] {
    var result: [U] = []
    for item in items {
        result.append(mapper(item))
    }
    return result
}

// Использование
let numbers = [1, 2, 3]
let strings = map(numbers, fn(n) { return String(n) })
```

### Частичное применение дженериков

```efen
type Result<T> = (T | Error)

// Можно создать специализированные алиасы
type IntResult = Result<Int>
type StringResult = Result<String>
```

## Сложные типы

### Union типы

```efen
type ID = (Int | String)
type Response = (Success | Error | Pending)
type Nullable<T> = (T | null)
```

### Tuple типы

```efen
type Point = (Int, Int)
type RGB = (Int, Int, Int)
type KeyValue = (String, Any)
```

### Вложенные структуры

```efen
type UserData = [String: Any]
type Config = [String: [String: Any]]
type NestedList<T> = [T | [T]]
```

## Примеры использования

### Доменная модель

```efen
// Идентификаторы
type UserID = String
type PostID = Int
type SessionToken = String

// Временные метки
type Timestamp = Int
type Duration = Int

// Результаты операций
type UserResult = (User | Error)
type ValidationResult = (Bool, [String])
```

### Callback и обработчики

```efen
function SuccessCallback<T> = (T) -> Void
function ErrorCallback = (Error) -> Void
function CompletionHandler = (Result<Any>) -> Void

class HTTPClient {
    fn get(
        url: String,
        onSuccess: SuccessCallback<String>,
        onError: ErrorCallback
    ) {
        // ...
    }
}
```

### Состояние приложения

```efen
type AppState = [String: Any]
type Action = (String, [String: Any])
function Reducer = (AppState, Action) -> AppState
function Middleware = (AppState, Action) -> Action

class Store {
    var state: AppState
    var reducer: Reducer
    var middleware: [Middleware]

    fn dispatch(action: Action) {
        // ...
    }
}
```

### Конфигурация

```efen
type HostPort = (String, Int)
type Headers = [String: String]
type QueryParams = [String: String]

type HTTPConfig = [String: Any]
type DatabaseConfig = [String: Any]
```

### Математические типы

```efen
type Vector2D = (Float, Float)
type Vector3D = (Float, Float, Float)
type Matrix2x2 = [[Float]]

function BinaryOp = (Float, Float) -> Float
function UnaryOp = (Float) -> Float
```

## Вложенные алиасы

Алиасы могут ссылаться на другие алиасы.

```efen
type UserID = String
type User = [String: Any]
type UserMap = [UserID: User]

function UserHandler = (User) -> Void
function UserValidator = (User) -> Bool
function UserTransformer = (User) -> User
```

## Декораторы

Алиасы типов поддерживают декораторы.

```efen
@deprecated("Use NewResult instead")
type OldResult = (Int | Error)

@experimental
type AsyncResult<T> = Future<Result<T>>

@internal
type InternalID = Int
```

## Алиасы в модулях

```efen
// types.efen
module MyApp.Types

type UserID = String
type PostID = Int

function Handler<T> = (T) -> Void
```

```efen
// main.efen
use MyApp.Types

fn processUser(id: UserID) {
    // ...
}
```

## Отличия type от function

| Аспект | type | function |
|--------|------|----------|
| Назначение | Любые типы | Только функциональные типы |
| Читаемость | Универсальное | Явно указывает на функцию |
| Семантика | Общий алиас | Специфичный для функций |

### Когда использовать type

```efen
type UserID = String
type Point = (Int, Int)
type Result<T> = (T | Error)
```

### Когда использовать function

```efen
function Handler = (Event) -> Void
function Validator<T> = (T) -> Bool
function Mapper<T, U> = (T) -> U
```

## Ограничения

1. Алиасы не создают новые типы, только альтернативные имена
2. Нельзя добавить методы или свойства к алиасу
3. Алиасы не могут иметь ограничения (constraints) сами по себе
4. Рекурсивные алиасы не поддерживаются

```efen
// ❌ Ошибка: рекурсивный алиас
type Tree = (Int, Tree?, Tree?)

// ✅ Используйте класс или структуру
class Tree {
    var value: Int
    var left: Tree?
    var right: Tree?
}
```

## Лучшие практики

1. **Используйте осмысленные имена**: Имя алиаса должно отражать его назначение
   ```efen
   type UserID = String  // ✅ Хорошо
   type UID = String     // ⚠️ Непонятно
   ```

2. **Предпочитайте function для функциональных типов**
   ```efen
   function Handler = (Event) -> Void  // ✅ Явно
   type Handler = (Event) -> Void      // ⚠️ Менее явно
   ```

3. **Группируйте связанные алиасы**
   ```efen
   // Идентификаторы
   type UserID = String
   type PostID = Int
   type CommentID = Int

   // Обработчики
   function UserHandler = (User) -> Void
   function PostHandler = (Post) -> Void
   ```

4. **Документируйте назначение**
   ```efen
   /// Уникальный идентификатор пользователя в системе
   type UserID = String

   /// Обработчик события нажатия кнопки
   function ClickHandler = (MouseEvent) -> Void
   ```

5. **Используйте для сложных типов**
   ```efen
   // ✅ Хорошо: упрощает сложный тип
   type ValidationResult = (Bool, [String], [String: Any])

   // ❌ Плохо: слишком простой тип
   type MyInt = Int
   ```

6. **Избегайте чрезмерного использования**
   - Не создавайте алиасы для очевидных типов
   - Используйте только когда это улучшает читаемость

## Смотрите также

- [Типы](types.md)
- [Функции](functions.md)
- [Дженерики](generics.md)
- [Модули](modules.md)
