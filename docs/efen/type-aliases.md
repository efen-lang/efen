# Алиасы типов (Type Aliases)

Алиасы типов в Efen позволяют создавать альтернативные имена для существующих типов, улучшая читаемость и поддерживаемость кода.

## Содержание

- [Ключевое слово alias](#ключевое-слово-alias)
- [Отличие от нового type](#отличие-от-нового-type)
- [Дженерик-алиасы](#дженерик-алиасы)
- [Сложные типы](#сложные-типы)
- [Примеры использования](#примеры-использования)
- [Лучшие практики](#лучшие-практики)

## Ключевое слово alias

Ключевое слово `alias` используется для создания алиаса любого типа.

### Базовый синтаксис

```efen
alias MyInt = Int
alias UserID = String
alias Timestamp = Int
```

### Использование

```efen
alias UserID = String

fn getUser(id: UserID) -> User? {
    // ...
}

let userId: UserID = "user123"
let user = getUser(userId)
```

Объявление алиаса сохраняется в HIR вместе с именем, исходной позицией,
атрибутами и metadata. Употребление запоминает написанный алиас и
его каноническую цель. При проверке типов алиас раскрывается, а `typeof(UserID)`
возвращает основной семантический тип. Compile-time API может читать написанный
alias отдельно от результата `typeof`.

### Алиасы для примитивов

```efen
alias Byte = Int8
alias Word = Int16
alias DWord = Int32
alias QWord = Int64

alias Percentage = Float  // 0.0 - 100.0
alias Ratio = Float       // 0.0 - 1.0
```

### Алиасы для коллекций

```efen
alias IntList = [Int]
alias StringMap = [String: Any]
alias Matrix = [[Float]]
```

## Функциональные типы

Функциональный тип объявляется тем же `alias`, что и любой другой тип.

### Базовый синтаксис

```efen
alias Handler = (Int) -> Void
alias Predicate = (String) -> Bool
alias Mapper = (Int) -> String
```

### Использование

```efen
alias EventHandler = (Event) -> Void

class Button {
    var onClick: EventHandler?

    fn setClickHandler(handler: EventHandler) {
        onClick = handler
    }
}

let button = Button()
button.setClickHandler((event: Event) -> Void {
    echo "Button clicked!"
})
```

### Сложные функциональные типы

```efen
// Функция с несколькими параметрами
alias Comparator = (Int, Int) -> Int

// Функция, возвращающая функцию
alias HandlerFactory = (String) -> ((Event) -> Void)

// Функция с optional результатом
alias Parser = (String) -> Result?
```

## Дженерик-алиасы

Алиасы типов могут быть дженериками.

### alias с дженериками

```efen
alias Option<T> = T?
alias ValueOrError<T> = (T | Error)
alias Pair<T, U> = (T, U)
```

### alias функционального типа с дженериками

```efen
alias Handler<T> = (T) -> Void
alias Transformer<T, U> = (T) -> U
alias Predicate<T> = (T) -> Bool
alias Comparator<T> = (T, T) -> Int
```

### Использование дженерик-алиасов

```efen
alias Mapper<T, U> = (T) -> U

fn map<T, U>(items: [T], mapper: Mapper<T, U>) -> [U] {
    var result: [U] = []
    for item in items {
        result.append(mapper(item))
    }
    return result
}

// Использование
let numbers = [1, 2, 3]
let strings = map(numbers, (n) => String(n))
```

### Частичное применение дженериков

```efen
alias ValueOrError<T> = (T | Error)

// Можно создать специализированные алиасы
alias IntOrError = ValueOrError<Int>
alias StringOrError = ValueOrError<String>
```

## Сложные типы

### Union-типы

Запись `T | U` образует structural union существующих типов. Она не вводит
именованных constructors.

```efen
alias ID = (Int | String)
alias Response = (Success | Error | Pending)
```

Если альтернативам нужны собственные имена или payload одинакового типа должен
оставаться различимым по case, используется номинальный
[variant type](types/variant.md):

```efen
variant Side {
    left { value: Int }
    right { value: Int }
}
```

### Tuple типы

```efen
alias Point = (Int, Int)
alias RGB = (Int, Int, Int)
alias KeyValue = (String, Any)
```

### Вложенные структуры

```efen
alias UserData = [String: Any]
alias Config = [String: [String: Any]]
alias NestedList<T> = [T | [T]]
```

## Примеры использования

### Доменная модель

```efen
// Идентификаторы
alias UserID = String
alias PostID = Int
alias SessionToken = String

// Временные метки
alias Timestamp = Int
alias Duration = Int

// Результаты операций
alias UserResult = (User | Error)
alias ValidationResult = (Bool, [String])
```

### Callback и обработчики

```efen
alias SuccessCallback<T> = (T) -> Void
alias ErrorCallback = (Error) -> Void
alias CompletionHandler = (ValueOrError<Any>) -> Void

class HTTPClient {
    fn get(url: String, onSuccess: SuccessCallback<String>, onError: ErrorCallback) {
        // ...
    }
}
```

### Состояние приложения

```efen
alias AppState = [String: Any]
alias Action = (String, [String: Any])
alias Reducer = (AppState, Action) -> AppState
alias Middleware = (AppState, Action) -> Action

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
alias HostPort = (String, Int)
alias Headers = [String: String]
alias QueryParams = [String: String]

alias HTTPConfig = [String: Any]
alias DatabaseConfig = [String: Any]
```

### Математические типы

```efen
alias Vector2D = (Float, Float)
alias Vector3D = (Float, Float, Float)
alias Matrix2x2 = [[Float]]

alias BinaryOp = (Float, Float) -> Float
alias UnaryOp = (Float) -> Float
```

## Вложенные алиасы

Алиасы могут ссылаться на другие алиасы.

```efen
alias UserID = String
alias User = [String: Any]
alias UserMap = [UserID: User]

alias UserHandler = (User) -> Void
alias UserValidator = (User) -> Bool
alias UserTransformer = (User) -> User
```

## Декораторы

Алиасы типов поддерживают декораторы.

```efen
@deprecated("Use NewResult instead")
alias OldResult = (Int | Error)

@experimental
alias AsyncValueOrError<T> = Future<ValueOrError<T>>

@internal
alias InternalID = Int
```

## Алиасы в модулях

```efen
// types.efen
module MyApp::Types

alias UserID = String
alias PostID = Int

alias Handler<T> = (T) -> Void
```

```efen
// main.efen
use MyApp::Types

fn processUser(id: UserID) {
    // ...
}
```

## Отличие от нового type

`alias X = T` создаёт прозрачное имя существующего типа. `type X: T` создаёт
новый номинальный тип на основе `T`:

```efen
alias DatabaseId = Int
type UserId: Int
```

`DatabaseId` взаимозаменяем с `Int`. `UserId` требует точного совпадения типов
или отдельно объявленной прямой стратегии преобразования.

Новый тип не получает операций базового молча. Те, что нужны, он перечисляет
в своих скобках строкой `inherit` (Edmond, 2026-10-27); остальные строки скобок —
условия уточнения (агент):

```efen
type Meters: Float {
    inherit +, -, <, ==
}

@align(sizeOf(Int))
type AtomicInt: Int {
    inherit +, -, +=, ==, <
}
```

Унаследованная операция работает так же, как у базового типа; значения базового
типа в ней заменяются новым типом, а `==` и `<` по-прежнему возвращают `Bool`
(агент). Пример с атомарным числом — в
[Общей памяти](shared.md#атомики).

### Суффиксы и префиксы литералов

Новый тип объявляет в тех же скобках суффиксы и префиксы своих литералов: строка
`suffix` или `prefix`, имя, и по желанию после `=>` значение, которое тип делает
из числа или строки литерала, `value` (Edmond, 2026-10-29):

```efen
type Meters: Float {
    suffix m
    inherit +, -, <, ==
}

type Bytes: Int {
    suffix B
    suffix KB => value * 1024
    suffix MB => value * 1024 * 1024
    inherit +, <, ==
}

type Path: String {
    prefix path
}

let width = 2.5m             // Meters
let limit = 10MB             // Bytes, 10 485 760
let root = path"/usr/lib"    // Path
```

Правила:

- суффикс стоит вплотную за числом или строкой: `10MB`, `"text"utf16`; префикс —
  вплотную перед строкой: `path"/usr/lib"`. У чисел префиксов нет: `px5` не
  отличить от имени;
- `suffix m` без `=>` делает значение литерала значением типа как есть;
- значение после `=>` вычисляется при компиляции; переполнение и условия
  уточнения типа тоже проверяются при компиляции (агент);
- у шестнадцатеричного числа суффикса нет: буквы `A`–`F` — его цифры, и в
  `0x400B` суффикс `B` не отличить от цифры (агент);
- `r"…"` — встроенная сырая строка ([строки](types/strings.md#raw-строки)), тип не
  объявляет префикс `r`;
- суффикс и префикс объявляет только новый тип: `alias` прозрачен, и единица
  потерялась бы в базовом типе;
- суффикс виден там, где виден тип; два видимых типа с одним суффиксом — ошибка
  компиляции (агент).

Парсер хранит приставку как часть литерала; что тип сделает со строкой при
компиляции — проверит, разберёт шаблон или пересчитает число, — решает его
метакод ([метафункции](compile-time/metafunctions.md)). Префиксы и суффиксы
может объявить и библиотека для своих типов.

### Когда использовать alias

```efen
alias UserID = String
alias Point = (Int, Int)
alias ValueOrError<T> = (T | Error)
```

### Функциональные типы

```efen
alias Handler = (Event) -> Void
alias Validator<T> = (T) -> Bool
alias Mapper<T, U> = (T) -> U
```

## Ограничения

1. Алиасы не создают новые типы, только альтернативные имена
2. Нельзя добавить методы или свойства к алиасу
3. Алиасы не могут иметь ограничения (constraints) сами по себе
4. Рекурсивные алиасы не поддерживаются

```efen
// ❌ Ошибка: рекурсивный алиас
alias Tree = (Int, Tree?, Tree?)

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
   alias UserID = String  // ✅ Хорошо
   alias UID = String     // ⚠️ Непонятно
   ```

2. **Используйте alias для функциональных типов**
   ```efen
   alias Handler = (Event) -> Void
   ```

3. **Группируйте связанные алиасы**
   ```efen
   // Идентификаторы
   alias UserID = String
   alias PostID = Int
   alias CommentID = Int

   // Обработчики
   alias UserHandler = (User) -> Void
   alias PostHandler = (Post) -> Void
   ```

4. **Документируйте назначение**
   ```efen
   /// Уникальный идентификатор пользователя в системе
   alias UserID = String

   /// Обработчик события нажатия кнопки
   alias ClickHandler = (MouseEvent) -> Void
   ```

5. **Используйте для сложных типов**
   ```efen
   // ✅ Хорошо: упрощает сложный тип
   alias ValidationResult = (Bool, [String], [String: Any])

   // ❌ Плохо: слишком простой тип
   alias MyInt = Int
   ```

6. **Избегайте чрезмерного использования**
   - Не создавайте алиасы для очевидных типов
   - Используйте только когда это улучшает читаемость

## Смотрите также

- [Типы](types/type.md)
- [Функции](functions.md)
- [Дженерики](generics.md)
- [Модули и пакеты](packages.md)
