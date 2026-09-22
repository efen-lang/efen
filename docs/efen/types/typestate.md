# Типы-состояния (typestate)

> Статус: проект спецификации. Грамматика и проверка компилятором ещё не реализованы.

Типы-состояния описывают допустимые состояния объекта и переходы между ними.
Компилятор отслеживает текущее состояние значения и запрещает вызов метода,
если этот метод недоступен в данном состоянии.

Модель вдохновлена Plaid и Obsidian, но использует синтаксис и систему владения
Efen.

## Оси состояний

Состояния объявляются внутри класса или структуры как именованные оси. Каждая
ось имеет ровно одно начальное состояние:

```efen
class Connection {
    state Lifecycle {
        initial Disconnected
        Connected
        Closed
    }

    state Security {
        initial Plain
        Encrypted
    }
}
```

Внутри `Connection` состояние пишется как `Lifecycle.Connected`; снаружи — как
`Connection.Lifecycle.Connected`. Сокращение `Connection.Connected` допустимо,
только если это имя уникально среди осей `Connection`; в публичных сигнатурах,
контрактах и диагностических идентификаторах канонична полная форма.

Текущее состояние объекта — по одному значению каждой оси. Начальная
конфигурация — произведение всех `initial` состояний.

Состояние оси может определять собственные данные:

```efen
class File {
    let path: String

    state Lifecycle {
        initial Closed

        Open {
            let descriptor: Int
        }

        Failed {
            let error: IOError
        }
    }
}
```

`path` существует во всех конфигурациях. `descriptor` доступен только при
`Lifecycle.Open`, а `error` — только при `Lifecycle.Failed`.

## Инварианты конфигурации

`state invariant` задаёт допустимые сочетания осей. Он проверяется для начальной
конфигурации, на normal return каждого перехода и после восстановления на
exceptional path:

```efen
class Connection {
    state Lifecycle {
        initial Disconnected
        Connected
        Closed
    }

    state Security {
        initial Plain
        Encrypted
    }

    state invariant validStates {
        !(self is Security.Encrypted) || self is Lifecycle.Connected
    }
}
```

Это state-инвариант, а не общий инвариант представления класса: он ограничивает
только конфигурации осей. Во время временно нарушенной конфигурации тело не
может выполнять state-зависимый доступ, вызывать методы или выпускать зависящий
от состояния alias; до normal либо exceptional выхода инвариант должен быть
снова выполнен.

## Состояние в сигнатуре функции

Typestate указывается словом `state`. После него идёт непустой список правил
осей, разделённых запятой:

```efen
fn flush state Lifecycle.Open
fn read -> String state Lifecycle.Open
```

- `Lifecycle.Open` означает `Lifecycle.Open >> Lifecycle.Open`;
- запятая соединяет правила разных осей, а не порядок выполнения;
- одна ось не может встретиться в списке дважды;
- неупомянутая ось сохраняет своё входное состояние.

Поэтому `flush` требует и сохраняет `Lifecycle.Open`, а `read` возвращает
`String` при том же требовании. Отсутствие части `-> тип` означает, что метод
не возвращает значения.

Если доступ или результат перехода зависит от другой оси, она указывается
отдельной clause, даже если не меняется:

```efen
fn enableTls
    state Lifecycle.Connected,
          Security.Plain >> Security.Encrypted
```

## Переход состояния

Оператор `>>` обозначает переход одной оси из исходного состояния в новое:

```efen
fn open state Lifecycle.Closed >> Lifecycle.Open
fn close state Lifecycle.Open >> Lifecycle.Closed
```

Метод с результатом записывается так:

```efen
fn connect -> Connection state Lifecycle.Disconnected >> Lifecycle.Connected
```

Общие формы сигнатуры:

```text
AxisClause := Axis.State | Axis.State >> Axis.State

fn name(parameters) -> ReturnType state AxisClause (, AxisClause)*
fn name(parameters) state AxisClause (, AxisClause)*
```

- `ReturnType` — возвращаемый тип;
- `Before` — обязательное состояние оси до вызова;
- `After` — состояние оси после успешного завершения;
- одно `Axis.State` без `>>` эквивалентно identity-переходу этой оси.

`|` не входит в публичную transition-сигнатуру первой версии. После ветвления
компилятор может получить альтернативные состояния, но метод публикует точную
нормальную post-конфигурацию.

## Пример

```efen
class File {
    let path: String

    state Lifecycle {
        initial Closed

        Open {
            let descriptor: Int
        }
    }

    fn open state Lifecycle.Closed >> Lifecycle.Open throws IOError {
        descriptor = os.open(path)
    }

    fn read(count: Int) -> [Byte] state Lifecycle.Open {
        return os.read(descriptor, count)
    }

    fn close state Lifecycle.Open >> Lifecycle.Closed {
        os.close(descriptor)
    }
}

var file = File(path: "data.txt") // начальное состояние Lifecycle.Closed
file.open()                       // теперь Lifecycle.Open
let data = file.read(64)          // допустимо в Lifecycle.Open
file.close()                      // теперь Lifecycle.Closed
// file.read(64)                  // ошибка: требуется Lifecycle.Open
```

## Нормальное и аварийное завершение

Переход применяется только после нормального завершения функции. Если функция
выбрасывает исключение, объект сохраняет валидное исходное состояние:

```efen
fn open state Lifecycle.Closed >> Lifecycle.Open throws IOError
```

- успешный возврат: `Lifecycle.Closed` становится `Lifecycle.Open`;
- `throw IOError`: объект остаётся в полной валидной исходной конфигурации.

Это проверяемое обязательство тела, а не автоматический rollback. На каждом
exceptional edge должны быть сохранены данные, state-инварианты и все clauses
`Before`; после необратимого commit допустим только доказанно non-throwing
путь. Отдельные exceptional poststates в первой версии не поддерживаются.

## Эффекты и контексты

Typestate отделён от контекстных эффектов `in` и исключений `throws`:

```efen
fn open state Lifecycle.Closed >> Lifecycle.Open in FileSystem, Logger throws IOError
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

// Возможные состояния Lifecycle: Open | Closed
```

До уточнения состояния доступны только операции, допустимые одновременно для
`Lifecycle.Open` и `Lifecycle.Closed`.

Состояние уточняется через `is` или `match`:

```efen
if file is Lifecycle.Open {
    file.read(64)
}

match file {
    Lifecycle.Open: file.read(64)
    Lifecycle.Closed: file.open()
    Lifecycle.Failed: echo file.error
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

Существующая ссылка сама по себе не запрещает переход и не становится
недействительной только из-за нового typestate. Она сохраняет обычные origin,
rights, liveness и initialization obligations; representation не вправе
уничтожить или переиспользовать адресуемое ею место так, чтобы получить
use-after-free.

## Интерфейсы

Интерфейс с одной осью может описать протокол без определения данных состояний:

```efen
interface Connection {
    state Lifecycle {
        initial Disconnected
        Connected
    }

    fn connect state Lifecycle.Disconnected >> Lifecycle.Connected
    fn send(data: [Byte]) -> Int state Lifecycle.Connected
    fn disconnect state Lifecycle.Connected >> Lifecycle.Disconnected
}
```

Реализующий тип обязан предоставить совместимые состояния и переходы. Он может
иметь дополнительные приватные состояния, не нарушающие публичный протокол.

Concrete type сопоставляет свои состояния публичному протоколу явно, после
`implements` и до members:

```efen
class TcpConnection {
    implements Connection

    state Lifecycle {
        initial Resolving
        Handshaking
        Ready
    }

    state Connection.Lifecycle.Disconnected = Lifecycle.Resolving | Lifecycle.Handshaking
    state Connection.Lifecycle.Connected = Lifecycle.Ready
}
```

Правая часть mapping непуста; один concrete state не может соответствовать двум
states одного interface. Для каждого interface transition `P >> Q` реализация
обязана покрыть каждый concrete state из mapping `P` совместимым переходом в
state из mapping `Q`. Exceptional path сохраняет concrete `Before` и тем самым
остаётся в public `P`. Interface value создаётся только в состоянии из mapping;
compiler не добавляет скрытый runtime dispatch для непокрытого состояния.

Отображение нескольких осей interface на несколько concrete-осей пока не
определено. Нельзя независимо отображать каждую ось: это способно создать
декартово произведение недопустимых публичных конфигураций. До отдельного
решения многомерные оси в интерфейсном протоколе не публикуются.

## Диагностика

Ошибка должна показывать найденное и требуемое состояния:

```text
error[typestate.invalid-call]: `read` requires state `Lifecycle.Open`
  found state: `Lifecycle.Closed`
  note: `file` changed to `Lifecycle.Closed` after calling `close`
```

## Изменения грамматики

Для реализации потребуется:

1. добавить блоки осей `state Axis { initial State ... }` в классы и структуры;
2. добавить `state invariant Name { Expr }` и проверку полной конфигурации;
3. добавить список `AxisClause`, разделённый запятой, после результата метода;
4. разбирать `>>` внутри clause, сохранив битовый сдвиг в выражениях;
5. нормализовать clauses осей в сигнатурах методов, контрактов и HIR;
6. реализовать flow-sensitive проверку конфигураций совместно с ownership-анализом;
7. добавить точную диагностику дублированной оси, нарушения state-инварианта и
   недопустимого перехода;
8. отдельно определить mapping нескольких осей interface на concrete type;
9. отдельно определить данные, принадлежащие комбинации нескольких осей, и их
   инициализацию, очистку и доступ. В первой версии данные принадлежат только
   одному конкретному состоянию одной оси.

Слово `state` не конфликтует со structural union:

```efen
fn parse -> Bool | String state Lifecycle.Ready
```

Здесь `Bool | String` — возвращаемый structural union, а `Lifecycle.Ready` —
состояние объекта.

## Области с гарантией состояния

Последовательность временных переходов может быть ограничена областью
`region preserve`, которая требует восстановить заданное состояние на каждом
пути выхода. Подробная спецификация приведена в документе
[«Области кода и гарантии состояния»](../code-regions.md).
