# Типы-состояния (typestate)

> Статус: проект спецификации. Грамматика и проверка компилятором ещё не реализованы.

Типы-состояния описывают допустимые состояния объекта и переходы между ними.
Компилятор отслеживает текущее состояние значения и запрещает вызов метода,
если этот метод недоступен в данном состоянии.

Модель вдохновлена Plaid и Obsidian, но использует синтаксис и систему владения
Efen.

## Объявление состояний

Состояния объявляются внутри класса или структуры:

```efen
class File {
    initial state Closed
    state Open
    state Failed
}
```

`initial` отмечает состояние нового объекта. У типа должно быть ровно одно
начальное состояние.

Состояния могут определять собственные данные:

```efen
class File {
    let path: String

    initial state Closed

    state Open {
        let descriptor: Int
    }

    state Failed {
        let error: IOError
    }
}
```

`path` существует во всех состояниях. `descriptor` доступен только в `Open`, а
`error` — только в `Failed`.

## Состояние в сигнатуре функции

Typestate указывается после двоеточия. Одно состояние означает, что метод требует
это состояние и сохраняет его:

```efen
fn flush() -> :Open
fn read() -> String: Open
```

- `flush` ничего не возвращает, требует `Open` и оставляет объект в `Open`;
- `read` возвращает `String`, требует `Open` и оставляет объект в `Open`.

Пустое место между `->` и `:` означает отсутствие возвращаемого значения.

## Переход состояния

Оператор `>>` обозначает переход из исходного состояния в новое:

```efen
fn open() -> :Closed >> Open
fn close() -> :Open >> Closed
```

Метод с результатом записывается так:

```efen
fn connect() -> Connection: Disconnected >> Connected
```

Общие формы сигнатуры:

```text
fn name(parameters) -> ReturnType: Before >> After
fn name(parameters) -> :Before >> After
fn name(parameters) -> ReturnType: State
fn name(parameters) -> :State
```

- `ReturnType` — возвращаемый тип;
- `Before` — обязательное состояние до вызова;
- `After` — состояние после успешного завершения;
- одно `State` без `>>` эквивалентно `State >> State`.

## Пример

```efen
class File {
    let path: String

    initial state Closed

    state Open {
        let descriptor: Int
    }

    fn open() -> :Closed >> Open throws IOError {
        descriptor = os.open(path)
    }

    fn read(count: Int) -> [Byte]: Open {
        return os.read(descriptor, count)
    }

    fn close() -> :Open >> Closed {
        os.close(descriptor)
    }
}

var file = File(path: "data.txt") // начальное состояние Closed
file.open()                       // теперь Open
let data = file.read(64)          // допустимо в Open
file.close()                      // теперь Closed
// file.read(64)                  // ошибка: требуется Open
```

## Нормальное и аварийное завершение

Переход применяется только после нормального завершения функции. Если функция
выбрасывает исключение, объект сохраняет исходное состояние:

```efen
fn open() -> :Closed >> Open throws IOError
```

- успешный возврат: `Closed` становится `Open`;
- `throw IOError`: объект остаётся в `Closed`.

Переходы при исключениях в первой версии не поддерживаются.

## Эффекты и контексты

Typestate отделён от контекстных эффектов `in` и исключений `throws`:

```efen
fn open() -> :Closed >> Open in FileSystem, Logger throws IOError
```

Порядок частей сигнатуры:

```text
параметры -> результат: typestate in контексты throws исключения
```

Typestate описывает изменение самого объекта. `in` описывает внешние зависимости,
а `throws` — возможные исключения.

## Ветвление и слияние

Компилятор отслеживает состояние отдельно в каждой ветке. После ветвления
состояние известно точно только тогда, когда все пути приводят к одному состоянию:

```efen
if shouldClose {
    file.close()
} else {
    file.flush()
}

// Возможные состояния: Open | Closed
```

До уточнения состояния доступны только операции, допустимые одновременно для
`Open` и `Closed`.

Состояние уточняется через `is` или `switch`:

```efen
if file is Open {
    file.read(64)
}

switch file {
    case Open:
        file.read(64)
    case Closed:
        file.open()
    case Failed:
        echo file.error
}
```

Разбор публичных состояний должен быть исчерпывающим. Для совместимости с
будущими состояниями разрешена ветка `@unknown default`.

## Владение и псевдонимы

Переход состояния требует эксклюзивного права изменить объект. Это связывает
typestate с существующей системой ownership Efen:

- `own` разрешает переход;
- эксклюзивный `write` разрешает переход;
- `read` и `inspect` разрешают только методы без перехода;
- `shared read` запрещает переход;
- переход через `shared write` требует синхронизированной атомарной операции.

Компилятор должен гарантировать, что после перехода не существует изменяемой
ссылки, которая продолжает считать объект находящимся в старом состоянии.

## Интерфейсы

Интерфейс может описать протокол без определения данных состояний:

```efen
interface Connection {
    initial state Disconnected
    state Connected

    fn connect() -> :Disconnected >> Connected
    fn send(data: [Byte]) -> Int: Connected
    fn disconnect() -> :Connected >> Disconnected
}
```

Реализующий тип обязан предоставить совместимые состояния и переходы. Он может
иметь дополнительные приватные состояния, не нарушающие публичный протокол.

## Диагностика

Ошибка должна показывать найденное и требуемое состояния:

```text
error[typestate.invalid-call]: `read` requires state `Open`
  found state: `Closed`
  note: `file` changed to `Closed` after calling `close`
```

## Изменения грамматики

Для реализации потребуется:

1. добавить объявления `state` и `initial state` в классы, структуры и интерфейсы;
2. добавить необязательную typestate-часть после возвращаемого типа;
3. разрешить форму `-> :State`, где возвращаемый тип отсутствует;
4. разбирать `>>` как переход в сигнатуре, сохранив битовый сдвиг в выражениях;
5. добавить typestate в сигнатуры методов интерфейсов и контрактов;
6. реализовать flow-sensitive проверку совместно с ownership-анализом.

Двоеточие не конфликтует с union-типами:

```efen
fn parse() -> Bool | String: Ready
```

Здесь `Bool | String` — возвращаемый union-тип, а `Ready` — состояние объекта.

## Области с гарантией состояния

Последовательность временных переходов может быть ограничена областью
`region preserve`, которая требует восстановить заданное состояние на каждом
пути выхода. Подробная спецификация приведена в документе
[«Области кода и гарантии состояния»](../code-regions.md).
