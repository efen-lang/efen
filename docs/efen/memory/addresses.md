# Layout и дескрипторы памяти

[Управление памятью](index.md) · [Примеры layout](layout-examples/) ·
[Ownership](../types/ownership.md) · [Representation](../representations.md) ·
[Efen → Viper](viper-verification-backend.md)

Статус: текущая нормативная модель дизайна. Показанный surface syntax ещё не
реализован компилятором; точные сигнатуры операций descriptor остаются
кандидатами API при зафиксированной ниже семантике.

Безопасность памяти обязательна независимо от пользовательских условий:
компилятор всегда проверяет происхождение, живость, инициализацию, границы и
права доступа. Достижимость, форма графа, соответствие счётчиков и завершение
обхода являются дополнительными доказательствами. Если от них зависит
безопасность операции, недоказанное свойство блокирует компиляцию.

## Три уровня

Логический тип задаёт наблюдаемый смысл. Для `Array<Element, R>` это порядок
элементов, `count`, чтение и замена позиции.

Representation является аспектом. Он выбирает layout памяти и реализует
операции конкретного типа.

Layout описывает:

- структуры, входящие в представление;
- количество и расположение их экземпляров;
- ссылки между ними;
- условия допустимого состояния;
- происхождение handles и области их жизни.

Источник памяти — RAM, файл, GPU или другой ресурс — может быть связан с
дескрипторами позднее. Точная модель `source` пока отложена.

## Target, Self и self

Логический тип передаёт representation исходный тип элемента:

```efen
struct Array {
    generic Element: Type
    generic R<Target>: Representation<Target>

    conforms IndexedSequence<Element>
    use R<Element>
}
```

Для `Array<User, List>`:

```text
Target = User
Self   = Array<User, List>
```

`Target` является явным generic-параметром аспекта. `Self` неявно приходит
из места применения `use R<Element>` и обозначает конкретный строящийся
`Array`. `self` — текущий runtime-экземпляр `Self`.

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        // Структуры и дескрипторы памяти Self.
    }

    implementation {
        // Конструкторы и операции над self.
    }
}
```

`implementation Target` не используется: `Target` является элементом, а не
строящимся массивом.

## Структуры и дескрипторы

`struct` задаёт форму одного значения. Он не сообщает, сколько таких значений
существует и где они размещены.

`set`, `one`, `area` и `set area` называются дескрипторами памяти:

- `one` — один экземпляр структуры;
- `set` — множество экземпляров без обещания непрерывности;
- `area` — одна непрерывная область элементов одной формы;
- `set area` — множество независимых непрерывных областей.

Heterogeneous area сможет перечислять допустимые типы, но её точный
surface-синтаксис ещё не утверждён.

```efen
layout {
    set Items: Item
    one Header

    struct Item {
        // Форма одного элемента.
    }

    struct Header {
        // Форма отдельного одиночного объекта.
    }
}
```

Дескрипторы принято группировать в начале layout. Порядок не влияет на
разрешение имён: один layout является общей декларативной областью.

Если корнем representation является сам применивший аспект тип, отдельный
`one` не нужен:

```efen
layout {
    set Items: Item

    struct Item {
        Target
        var next: own other Items.Item? = null
    }

    struct Self {
        var head: own Items.Item? = null
        var length: Size = 0
    }
}
```

`struct Self` определяет поля конкретного представляемого значения.
`implementation` обязана предоставить явный конструктор, который
инициализирует эти поля.

## Производные типы дескриптора

`Items.Item` — typed handle отдельного элемента, управляемого `Items`.
Он сохраняет происхождение из конкретного descriptor и конкретного экземпляра
layout.

`Items.Area` — typed pointer на начало одной непрерывной области `Item`.
Это чистый указатель. Он не хранит:

- capacity allocation;
- число инициализированных мест;
- длину логической коллекции;
- bitmap частичной инициализации.

Эти значения находятся в обычных полях `Self`, `Chunk` или локальных
переменных подготовки:

```efen
struct Self {
    var root: own Items.Area? = null

    var capacity: Size = 0 {
        (value == 0) == (self.root == null)
    }

    var length: Size = 0 {
        value == Items.count
        value <= self.capacity
    }
}
```

Нулевая capacity использует `root == null`; allocation нулевого размера не
создаётся.

Логический диапазон `root[0..<0]` пуст и не разыменовывает `root`, поэтому он
допустим при `root == null`. Любой непустой диапазон требует ненулевой root и
доказанной границы allocation.

## Операции дескриптора

Операции выделения принадлежат descriptor, а не `struct Item`:

```efen
Items.allocate(value: own Item) -> own Items.Item
Items.free(item: own Items.Item)

Items.allocateArea(capacity: Size) -> own Items.Area

Items.reallocateArea(
    root: &own Items.Area?,
    oldCapacity: Size,
    initializedCount: Size,
    newCapacity: Size
)

Items.free(
    root: own Items.Area,
    capacity: Size,
    initializedCount: Size
)

Items.at(root: Items.Area, index: Size) -> Items.Item
Items.initialize(
    root: Items.Area,
    index: Size,
    value: own Item
)
Items.extract(root: Items.Area, index: Size) -> Item
Items.move(
    from: Items.Area,
    fromIndex: Size,
    to: Items.Area,
    toIndex: Size
)
```

`Items.allocate` сообщает, в каком множестве появляется отдельный элемент.
`Item.allocate` было бы недостаточно: одна форма `Item` может использоваться
двумя разными descriptors.

`Items.at` требует доказанного существующего и инициализированного места.
Граница берётся из явных полей вызывающей структуры, а не из `Area`.

`Items.initialize` создаёт живой элемент в пустом месте. `Items.extract`
переносит `Item` наружу и оставляет место пустым. `Items.move` требует живой
источник и пустое назначение. Временные дырки отслеживаются проверочным IR и не
создают скрытого runtime-bitmap.

## Происхождение и разные множества

```efen
set Items: Item
set OtherItems: Item
```

`Items.Item` и `OtherItems.Item` несовместимы, даже если имеют одинаковое
машинное представление. Компилятор знает:

- descriptor;
- экземпляр layout;
- жив ли элемент;
- какие права доступны;
- можно ли передать handle менеджеру памяти.

Сырой адрес не приобретает membership приведением типа. Вход памяти от FFI или
системного allocator требует отдельно проверенной операции приёма. Бесплатно
забыть descriptor у живой ссылки и затем принять адрес в другое множество
нельзя.

## Поле и физическое встраивание

Обычное поле является логическим местом:

```efen
struct Item {
    var value: Target
}
```

Representation поля может хранить указатель, индекс или другую косвенную форму.
Эта запись не обещает, что байты `Target` входят в `Item`.

Голое имя типа физически встраивает его в объявленную позицию:

```efen
struct Item {
    var tag: UInt32
    Target
    var next: own other Items.Item? = null
}
```

`Target` здесь расположен после `tag`. Если он стоит первым, `Item`
начинается с `Target`.

Выражение `item.Target` обозначает embedded-место целиком:

```efen
let copy: Target = item.Target
let borrow = &item.Target
let moved: Target = take item.Target
item.Target = take replacement
```

Создание структуры с existing `Target` требует копирования при `Copyable`
или явного переноса:

```efen
Items.allocate(
    Item(take value, next: null)
)
```

После `take item.Target` manager получает состояние частичной инициализации.
`Items.free(take item)` освобождает память узла, не уничтожая перенесённый
`Target` повторно.

## Декларативные условия

Блок после `var` описывает допустимое значение свойства. `value` означает
значение именно этого свойства:

```efen
var length: Size = 0 {
    value == Items.count
}
```

Условие после `set` применяется к каждому элементу:

```efen
set Items: Item {
    value reachable from self.head by Item.next
}
```

`reachable` — логическое рефлексивное отношение пути. Оно не запускает
runtime-обход.

Обычный `if` внутри условия означает импликацию:

```efen
var tail: read Items.Item? = null {
    (self.head == null) == (value == null)

    if value != null {
        value reachable from self.head by Item.next
        value.next == null
    }
}
```

Несколько выражений одного блока соединяются логическим `&&`.

Компилятор выводит зависимости условия из прочитанных мест. Операция может
временно нарушить затронутое условие между соседними безотказными шагами, но
обязана восстановить его перед:

- `return`;
- `throw`;
- приостановкой;
- вызовом кода, способного наблюдать layout;
- публикацией ссылки на изменяемое состояние.

Отдельного surface-блока `proof` и изменяемой ghost-копии структуры не нужно.
Backend может использовать ghost-state внутри проверочного IR.

## Reallocation и root

Динамическая структура хранит root и metadata раздельно:

```efen
struct Self {
    var root: own Items.Area? = null
    var capacity: Size = 0
    var length: Size = 0
}
```

Рост вызывает:

```efen
Items.reallocateArea(
    root: &self.root,
    oldCapacity: self.capacity,
    initializedCount: self.length,
    newCapacity: nextCapacity
)
self.capacity = nextCapacity
```

Descriptor получает место root-поля и может изменить указатель. Он может
расширить allocation на месте либо выделить новый, перенести
`initializedCount` элементов, заменить root и освободить старый блок.

Контракт сильной ошибки:

- при ошибке root, metadata, membership и значения прежние;
- `newCapacity < initializedCount` отвергается до изменения;
- после успеха логический порядок значений сохранён;
- физические `Items.Item` старой области могут стать недействительными.

Поэтому живой handle, индекс или borrow перемещаемого места блокирует
reallocation. Единственный владеющий root, переданный через `&self.root`, не
является запрещающим alias.

Между успешной заменой root и записью новой capacity условие временно открыто.
Там запрещены исключения, приостановка и наблюдающие вызовы.

## Владение, живость и доступ

`own` означает обязанность уничтожить значение или передать эту обязанность.
`read` и `write` являются отдельными правами доступа.

Чтение владеющего места не переносит владение:

```efen
let borrowed = self.head
let owned = take self.head!
```

Первая строка получает невладеющий доступ. Вторая переносит владельца и
оставляет исходное место пустым.

Перед разыменованием compiler проверяет:

1. handle происходит из ожидаемого descriptor и layout-instance;
2. элемент ещё жив;
3. нужный компонент инициализирован;
4. индекс находится в доказанной границе allocation;
5. доступны требуемые права.

`Items.free` отдельного элемента требует `own Items.Item`.
`Items.free` области требует владеющий root, capacity и initializedCount.
Освобождение уничтожает каждый живой компонент ровно один раз.

Живой borrow блокирует удаление элемента, перемещение его physical place и
уничтожение layout-instance. Перемещение всего `Self` допустимо только тогда,
когда representation ссылок сохраняет их смысл либо живых зависимых ссылок нет.

## Обход и завершение

Переход по `next` безопасен, если handle жив, поле инициализировано и доступны
права чтения. Из этого не следует завершение обхода.

Доказательство:

```efen
value reachable from self.head by Item.next
```

говорит о существовании конечного пути к конкретному `value`. Для общего цикла
дополнительно требуется доказать, что повторов нет либо что число шагов
ограничено явным счётчиком.

Тестирование конечного числа списков и timeout proof-backend не являются
доказательством. Timeout означает «не доказано».

## Частичная инициализация и cleanup

Конструктор непрерывного массива хранит metadata до вызова пользовательской
функции:

```efen
self.root = null
self.capacity = count
self.length = 0

if count > 0 {
    self.root = Items.allocateArea(capacity: count)
}
```

После каждого успешного `Items.initialize` увеличивается `length`. Если
следующая операция бросает, cleanup получает точные значения:

```efen
if self.root != null {
    Items.free(
        root: take self.root!,
        capacity: self.capacity,
        initializedCount: self.length
    )
}
```

Area ничего не знает о префиксе; правильность уничтожения зависит от явно
сохранённого `length`.

Для chunked layout каждая структура `Chunk` хранит собственные root, capacity
и length. Уничтожение каталога сначала освобождает блок каждого живого Chunk,
затем сам каталог. Общий `Target` не уничтожается второй раз.

## Примеры

Полные варианты и построчные объяснения:

- [общие контракты Array](layout-examples/array-contracts.md);
- [непрерывный фиксированный Array](layout-examples/contiguous-array.md);
- [динамический непрерывный Array](layout-examples/dynamic-array.md);
- [односвязный Array](layout-examples/singly-linked-array.md);
- [двусвязный Array](layout-examples/doubly-linked-array.md);
- [chunked Array](layout-examples/chunked-array.md).

## Граница модели

Пока не определены окончательно:

- surface-синтаксис `source`;
- heterogeneous area;
- квантор для закона общего префикса chunked layout;
- конкурентный доступ к одному layout-instance;
- точная representation weak handles и поколений;
- массовый перенос между descriptors;
- полный контракт proof-backend и диагностики.

[Аудит старой модели](addresses-defects.md) и
[сравнение с другими системами](prior-art.md) относятся к предыдущей редакции и
сохраняются как исторические материалы. Текущие обязательства backend описаны в
[Efen → Viper](viper-verification-backend.md); его старые surface-примеры не
являются нормативным синтаксисом.
