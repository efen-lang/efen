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

Typestate указывается словом `state`. Одно состояние означает, что метод требует
это состояние и сохраняет его:

```efen
fn flush state Open
fn read -> String state Open
```

- `flush` ничего не возвращает, требует `Open` и оставляет объект в `Open`;
- `read` возвращает `String`, требует `Open` и оставляет объект в `Open`.

Отсутствие части `-> тип` означает, что метод не возвращает значения.

## Переход состояния

Оператор `>>` обозначает переход из исходного состояния в новое:

```efen
fn open state Closed >> Open
fn close state Open >> Closed
```

Метод с результатом записывается так:

```efen
fn connect -> Connection state Disconnected >> Connected
```

Общие формы сигнатуры:

```text
fn name(parameters) -> ReturnType state Before >> After
fn name(parameters) state Before >> After
fn name(parameters) -> ReturnType state State
fn name(parameters) state State
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

    fn open state Closed >> Open throws IOError {
        descriptor = os.open(path)
    }

    fn read(count: Int) -> [Byte] state Open {
        return os.read(descriptor, count)
    }

    fn close state Open >> Closed {
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
fn open state Closed >> Open throws IOError
```

- успешный возврат: `Closed` становится `Open`;
- `throw IOError`: объект остаётся в `Closed`.

Переходы при исключениях в первой версии не поддерживаются.

## Эффекты и контексты

Typestate отделён от контекстных эффектов `in` и исключений `throws`:

```efen
fn open state Closed >> Open in FileSystem, Logger throws IOError
```

Порядок частей сигнатуры:

```text
параметры -> результат state состояние in контексты throws исключения
```

Хвост сигнатуры идёт строго в этом порядке: `-> тип`, `state`, `in`,
`throws | throws only | nothrows`. Любая из частей может отсутствовать.

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

Состояние уточняется через `is` или `match`:

```efen
if file is Open {
    file.read(64)
}

match file {
    Open: file.read(64)
    Closed: file.open()
    Failed: echo file.error
}
```

Разбор публичных состояний должен быть исчерпывающим. Для совместимости с
будущими состояниями разрешена ветка `@unknown _`.

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

    fn connect state Disconnected >> Connected
    fn send(data: [Byte]) -> Int state Connected
    fn disconnect state Connected >> Disconnected
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
2. добавить необязательную часть `state` после возвращаемого типа;
3. разрешить форму `state State` без части `-> тип`;
4. разбирать `>>` как переход в сигнатуре, сохранив битовый сдвиг в выражениях;
5. добавить typestate в сигнатуры методов интерфейсов и контрактов;
6. реализовать flow-sensitive проверку совместно с ownership-анализом.

Слово `state` не конфликтует со structural union:

```efen
fn parse -> Bool | String state Ready
```

Здесь `Bool | String` — возвращаемый structural union, а `Ready` — состояние объекта.

## Области с гарантией состояния

Последовательность временных переходов может быть ограничена областью
`region preserve`, которая требует восстановить заданное состояние на каждом
пути выхода. Подробная спецификация приведена в документе
[«Области кода и гарантии состояния»](../code-regions.md).
