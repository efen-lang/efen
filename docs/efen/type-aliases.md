<a id="алиасы-типов-type-aliases"></a>

# Псевдонимы типов: `alias`

Псевдоним даёт существующему типу другое имя. Он удобен для длинных типов
функций, вложенных коллекций и имён, которые поясняют назначение значения.
Сам тип при этом не меняется: ограничения и новые операции псевдоним
не добавляет.

## Содержание

- [Ключевое слово alias](#ключевое-слово-alias)
- [Отличие от нового type](#отличие-от-нового-type)
- [Дженерик-псевдонимы](#псевдонимы-с-параметрами-типов)
- [Сложные типы](#сложные-типы)
- [Примеры использования](#примеры-использования)
- [Лучшие практики](#лучшие-практики)

## Ключевое слово alias

Ключевое слово `alias` используется для создания псевдонима любого типа.

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

В HIR сохраняется само объявление псевдонима: имя, место в исходном коде,
атрибуты и метаданные. Употребление хранит и написанное имя, и исходный тип.
При проверке совместимости псевдоним раскрывается; `typeof(UserID)` возвращает
основной семантический тип. API времени компиляции позволяет отдельно
прочитать написанный псевдоним.

<a id="алиасы-для-примитивов"></a>

### Псевдонимы для примитивов

```efen
alias Byte = Int8
alias Word = Int16
alias DWord = Int32
alias QWord = Int64

alias Percentage = Float  // только имя: диапазон 0.0–100.0 не проверяется
alias Ratio = Float       // только имя: диапазон 0.0–1.0 не проверяется
```

Диапазон значений проверяет [уточняющий тип](types/refinement-types.md),
объявленный через `type`, а не прозрачный псевдоним.

<a id="алиасы-для-коллекций"></a>

### Псевдонимы для коллекций

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

    mut fn setClickHandler(handler: own EventHandler) {
        onClick = take handler
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

// Функция с результатом, который может отсутствовать
alias Parser = (String) -> Result?
```

<a id="дженерик-алиасы"></a>

## Псевдонимы с параметрами типов

Псевдоним может зависеть от одного или нескольких параметров типов.

<a id="alias-с-дженериками"></a>

### Объявление параметров

```efen
alias Option<T> = T?
alias ValueOrError<T> = (T | Error)
alias Pair<T, U> = (T, U)
```

<a id="alias-функционального-типа-с-дженериками"></a>

### Параметризованный тип функции

```efen
alias Handler<T> = (T) -> Void
alias Transformer<T, U> = (T) -> U
alias Predicate<T> = (T) -> Bool
alias Comparator<T> = (T, T) -> Int
```

<a id="использование-дженерик-алиасов"></a>

### Использование параметризованного псевдонима

```efen
alias Mapper<T, U> = (T) -> U

fn map<T, U>(items: [T], mapper: Mapper<T, U>) -> [U] {
    return items.map(mapper).toArray()
}

// Использование
let numbers = [1, 2, 3]
let strings = map(numbers, (n) => String(n))
```

<a id="частичное-применение-дженериков"></a>

### Фиксация аргументов обобщённого типа

```efen
alias ValueOrError<T> = (T | Error)

// Можно создать специализированные псевдонимы
alias IntOrError = ValueOrError<Int>
alias StringOrError = ValueOrError<String>
```

## Сложные типы

<a id="union-типы"></a>

### Структурные объединения

Запись `T | U` образует структурное объединение: значение может иметь
любой из перечисленных типов. Новые именованные случаи не объявляются.

```efen
alias ID = (Int | String)
alias Response = (Success | Error | Pending)
```

Если двум случаям нужны разные имена даже при одинаковых типах данных,
объявите [размеченное объединение `variant`](types/variant.md):

```efen
variant Side {
    left { let value: Int }
    right { let value: Int }
}
```

<a id="tuple-типы"></a>

### Типы кортежей

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

<a id="callback-и-обработчики"></a>

### Функции обратного вызова и обработчики

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

<a id="вложенные-алиасы"></a>

## Вложенные псевдонимы

Псевдонимы могут ссылаться на другие псевдонимы.

```efen
alias UserID = String
alias User = [String: Any]
alias UserMap = [UserID: User]

alias UserHandler = (User) -> Void
alias UserValidator = (User) -> Bool
alias UserTransformer = (User) -> User
```

## Декораторы

Псевдонимы типов поддерживают декораторы.

```efen
@deprecated("Use NewResult instead")
alias OldResult = (Int | Error)

@experimental
alias AsyncValueOrError<T> = Future<ValueOrError<T>>

@internal
alias InternalID = Int
```

<a id="алиасы-в-модулях"></a>

## Псевдонимы в модулях

```efen
// types.efen
alias UserID = String
alias PostID = Int

alias Handler<T> = (T) -> Void
```

```efen
// main.efen
use types

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

Новый тип не получает автоматически все операции базового типа. Нужные
операции перечисляются в теле через `inherit`; там же можно записать
условия уточнения:

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
типа в ней заменяются новым типом, а `==` и `<` по-прежнему возвращают `Bool`. Пример с атомарным числом — в
[Общей памяти](shared.md#атомики).

### Суффиксы и префиксы литералов

Новый тип объявляет в тех же скобках суффиксы и префиксы своих литералов: строка
`suffix` или `prefix`, имя, и по желанию после `=>` значение, которое тип делает
из числа или строки литерала, `value`:

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
  уточнения типа тоже проверяются при компиляции;
- у шестнадцатеричного числа суффикса нет: буквы `A`–`F` — его цифры, и в
  `0x400B` суффикс `B` не отличить от цифры;
- суффикс числа не начинается с `e` или `E` и цифры или знака: `2e5` — число с
  порядком ([числовые литералы](types/constants.md#числовые-литералы));
- `r"C:\path"` — встроенная сырая строка ([строки](types/strings.md#raw-строки)), тип не
  объявляет префикс `r`;
- суффикс и префикс объявляет только новый тип: `alias` прозрачен, и единица
  потерялась бы в базовом типе;
- суффикс виден там, где виден тип; два видимых типа с одним суффиксом — ошибка
  компиляции.

Парсер хранит приставку как часть литерала; что тип сделает со строкой при
компиляции — проверит, разберёт шаблон или пересчитает число, — решает его
метакод ([метафункции](compile-time/metafunctions.md)). Префиксы и суффиксы
может объявить и библиотека для своих типов.

### Когда использовать `alias`

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

1. Псевдонимы не создают новые типы, только альтернативные имена
2. Нельзя добавить методы или свойства к псевдониму
3. Псевдоним не добавляет отдельное условие на значения исходного типа; для этого нужен `type`
4. Рекурсивные псевдонимы не поддерживаются

```efen
// ❌ Ошибка: рекурсивный псевдоним
alias Tree = (Int, Tree?, Tree?)

// ✅ Используйте класс или структуру
class Tree {
    var value: Int
    var left: Tree?
    var right: Tree?
}
```

## Лучшие практики

1. **Используйте осмысленные имена**: Имя псевдонима должно отражать его назначение
   ```efen
   alias UserID = String  // ✅ Хорошо
   alias UID = String     // ⚠️ Непонятно
   ```

2. **Используйте alias для функциональных типов**
   ```efen
   alias Handler = (Event) -> Void
   ```

3. **Группируйте связанные псевдонимы**
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
   - Не создавайте псевдонимы для очевидных типов
   - Используйте только когда это улучшает читаемость

## Смотрите также

- [Типы](types/type.md)
- [Функции](functions.md)
- [Дженерики](generics.md)
- [Модули и пакеты](packages.md)
