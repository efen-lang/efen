# Постраничный файл через layout: проект модели

Статус: черновик для обсуждения. Предлагаемый синтаксис не является
нормативным, пока Edmond не утвердит соответствующий пронумерованный кейс.

## Цель

Документ проверяет одну идею на полном примере: `layout` описывает логическое
пространство памяти и алгоритмы, которые реализуют его через несколько областей
физической памяти.

В примере весь файл образует логическое население `Records`, но одновременно в
RAM помещаются только две страницы файла — население `Frames`. Обычное обращение
через `Records.Pointer` может прозрачно загрузить и закрепить frame, прочитать или
изменить его и затем отпустить. Логическая запись завершается, когда копия в RAM
становится authoritative. Долговечность отдельно запрашивается через `flush()`.

Пример должен покрыть полный цикл:

1. открыть и проверить существующий файл;
2. создать логические pointers только после проверки;
3. обработать попадание и промах кеша;
4. прочитать данные через кеш из двух frames;
5. изменить запись и передать authority копии в RAM;
6. вытеснить clean или dirty frame;
7. закрепить frame на время жизни borrow;
8. явно обеспечить долговечность через `flush()`;
9. сохранить согласованное состояние при каждой ошибке I/O;
10. закрыть layout согласно явно выбранной политике долговечности.

## Уже согласованные семантические основания

Это результаты обсуждения, а не предложения синтаксиса.

- Layout является логическим пространством памяти, а не одной физической
  аллокацией или одним физическим ресурсом.
- Один layout может одновременно использовать файл, RAM, DMA-буферы, device
  memory и другие физические области.
- `Records.Pointer` — логический указатель. Он не обещает машинный адрес или
  постоянное нахождение объекта в RAM.
- Одно логическое место может иметь несколько физических копий. В каждый момент
  не более одной копии является authoritative writable version. Остальные копии
  могут быть согласованными для чтения, устаревшими или ещё не опубликованными.
- Прозрачная реализация доступа может состоять из нескольких функций.
- После явного объявления такой реализации transparent исходный код использует
  обычный доступ `pointer.field`. Дополнительный знак в месте обращения не нужен.
- Все эффекты, исключения и возможная приостановка transparent access входят в
  контракт содержащей функции.
- Логическая запись завершается после публикации authoritative-копии в RAM.
  Файл может оставаться устаревшим до отдельного `flush()`.
- Логические условия выражаются предикатами свойств. Модель не требует
  встроенных в компилятор названий списков, деревьев, кешей или алгоритмов
  вытеснения.

## Логическая модель

Для типа записи фиксированного размера `R` файл содержит заголовок и страницы.
Каждая страница содержит `recordsPerPage` записей.

```text
Records.Pointer
    = origin этого экземпляра PagedFile
    + логическая identity записи

identity записи
    -> номер страницы и позиция внутри страницы
    -> resident frame, если страница сейчас находится в RAM
    -> байты записи внутри frame
```

`Records.Pointer` переживает вытеснение страницы и remap файла. Физический
borrow внутрь frame закрепляет этот frame до окончания borrow.

Минимальный пример разрешает не более одного resident frame для одной страницы
файла. Файл и frame всё равно являются двумя физическими копиями. Несколько
одновременных RAM-копий одной страницы остаются следующим проверочным сценарием.

Логическое значение страницы `p` определяется так:

```text
если у p есть Dirty или Flushing frame:
    Logical(p) = DirtyFrame(p)
иначе:
    Logical(p) = FilePage(p)
```

Для clean-копии:

```text
CleanFrame(p) = FilePage(p) = Logical(p)
```

Для dirty-копии:

```text
DirtyFrame(p) = Logical(p)
FilePage(p) содержит старую версию либо неизвестную torn-версию после
неудачного in-place flush
```

## Общий эскиз исходного кода

Каждая ещё не утверждённая форма ниже вынесена в отдельный синтаксический кейс.

```efen
layout PagedFile<R> {
    // S1: несколько физических областей внутри одного layout.
    source file: FileMemory
    source cache: RamMemory

    // S2: логическое содержимое всего файла.
    set Records: R

    enum ReplicaState {
        Empty
        Clean
        Dirty
    }

    enum IoState {
        Idle
        Loading
        Flushing
    }

    set Frames: Frame from cache

    struct Frame {
        var page: Records.Page? {
            (replica == Empty) == (page == null) &&
            (page == null || Frames.count(where: it.page == page) == 1)
        }

        var bytes: [Byte] {
            bytes.count == pageSize &&
            (replica != Clean || decodesAsCurrentFilePage(bytes, page)) &&
            (replica != Dirty || decodesAsLogicalPage(bytes, page, version))
        }

        var replica: ReplicaState {
            replica == Empty || page != null
        }

        var io: IoState {
            io != Flushing || replica == Dirty
        }

        var version: Version {
            replica == Empty || version == logicalVersion(page)
        }

        // Вычисляется по живым access leases; пользователь не меняет это поле.
        var pins: UInt { get { return liveLoans(to: self).count } }
    }

    let pageSize: Size
    let recordsPerPage: Size
    let frameLimit: Size {
        frameLimit == 2
    }

    // S3: отображение проверенного внешнего storage в population.
    constructor(path: Path) throws IOError | InvalidFile {
        file = FileMemory.open(path, access: exclusiveReadWrite)
        Records.map(file)
    }

    // S4: группа операций, скрытая за чтением, записью и borrow через
    // Records.Pointer.
    transparent access Records {
        fn acquireRead(pointer: read Records.Pointer)
            -> ReadLease<R>
            throws IOError

        fn acquireWrite(pointer: read write Records.Pointer)
            -> WriteLease<R>
            throws IOError

        fn release(lease: AccessLease<R>)
    }

    fn findResident(page: Records.Page) -> read Frames.Pointer?

    fn acquireFrame(page: Records.Page)
        -> read write Frames.Pointer
        throws IOError

    fn load(page: Records.Page, into: read write Frames.Pointer)
        throws IOError

    fn evict(frame: read write Frames.Pointer)
        throws IOError

    fn flush(frame: read write Frames.Pointer)
        throws IOError

    fn flush() throws IOError
}
```

Это семантический эскиз. Он не утверждает окончательные написания `source`,
`Records.Page`, `ReadLease`, `WriteLease`, `transparent access` или
`Records.map`.

## Полный кандидат Efen-кода

Ниже намеренно дан один цельный вариант синтаксиса. Он нужен для оценки и ещё не
является спецификацией.

```efen
struct UserRecord {
    let id: UInt64

    var balance: Int64 {
        balance >= 0
    }

    var name: FixedString<48>
}

layout UserFile {
    source file: FileMemory
    source cache: RamMemory

    set Records: UserRecord
    set Frames: Frame from cache

    enum ReplicaState {
        Empty
        Clean
        Dirty
    }

    enum IoState {
        Idle
        Loading
        Flushing
    }

    struct Frame {
        var page: Records.Page? {
            (replica == Empty) == (page == null) &&
            (page == null || Frames.count(where: it.page == page) == 1)
        }

        var bytes: [Byte] {
            bytes.count == pageSize
        }

        var replica: ReplicaState
        var io: IoState {
            io != Flushing || replica == Dirty
        }

        var version: Version
        var lastUse: UInt64

        // Значение выводится из живых leases, присваивать ему нельзя.
        var pins: UInt {
            get { return liveLoans(to: self).count }
        }
    }

    let pageSize: Size = 4096
    let frameLimit: Size = 2
    let format: UserRecordFormatV1
    var clock: UInt64 = 0

    constructor(path: Path) throws IOError | InvalidFile {
        file = FileMemory.open(path, access: exclusiveReadWrite)

        format.validateHeader(file)
        format.validateAll(file, bufferSize: pageSize * frameLimit)

        Records.map(file)
    }

    fn findResident(page: Records.Page) -> read write Frames.Pointer? {
        for frame in Frames {
            if frame.page == page && frame.io == Idle {
                return frame
            }
        }

        return null
    }

    fn chooseVictim() -> read write Frames.Pointer throws CacheBusy {
        var result: read write Frames.Pointer? = null

        for frame in Frames {
            if frame.pins == 0 &&
               (result == null || frame.lastUse < result.lastUse) {
                result = frame
            }
        }

        if result == null {
            throw CacheBusy()
        }

        return result
    }

    fn emptyFrame() -> read write Frames.Pointer throws OutOfMemory {
        if Frames.count < frameLimit {
            return Frames.create(
                page: null,
                bytes: [Byte](count: pageSize),
                replica: Empty,
                io: Idle,
                version: Version.initial,
                lastUse: 0
            )
        }

        return chooseVictim()
    }

    fn flush(frame: read write Frames.Pointer) throws IOError {
        if frame.replica != Dirty {
            return
        }

        require frame.pins == 0

        let page = frame.page
        let version = frame.version
        let snapshot = frame.bytes.copy()

        frame.io = Flushing

        try {
            file.writePage(
                page: page,
                bytes: snapshot,
                version: version
            )
            file.sync(page)

            if frame.version == version {
                frame.replica = Clean
            }

            frame.io = Idle
        } catch error: IOError {
            frame.replica = Dirty
            frame.io = Idle
            throw error
        }
    }

    fn evict(frame: read write Frames.Pointer) throws IOError {
        require frame.pins == 0

        if frame.replica == Dirty {
            flush(frame)
        }

        frame.page = null
        frame.replica = Empty
        frame.io = Idle
    }

    fn load(
        page: Records.Page,
        into frame: read write Frames.Pointer
    ) throws IOError | InvalidFile {
        require frame.pins == 0

        if frame.replica != Empty {
            evict(frame)
        }

        frame.io = Loading

        try {
            let bytes = file.readPage(page, size: pageSize)
            format.validatePage(page, bytes)

            frame.bytes = take bytes
            frame.version = file.version(page)
            frame.page = page
            frame.replica = Clean
            frame.io = Idle
        } catch error: IOError | InvalidFile {
            frame.page = null
            frame.replica = Empty
            frame.io = Idle
            throw error
        }
    }

    fn acquireFrame(page: Records.Page)
        -> read write Frames.Pointer
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        let resident = findResident(page)

        if resident != null {
            clock += 1
            resident.lastUse = clock
            return resident
        }

        let frame = emptyFrame()
        load(page, into: frame)

        clock += 1
        frame.lastUse = clock

        return frame
    }

    transparent access Records {
        fn acquireRead(pointer: read Records.Pointer)
            -> ReadLease<UserRecord>
            throws IOError | InvalidFile | CacheBusy | OutOfMemory
        {
            let page = Records.page(of: pointer)
            let frame = acquireFrame(page)
            let offset = Records.offset(of: pointer, in: page)
            let place = format.project<UserRecord>(frame.bytes, offset)

            return ReadLease(
                logical: pointer,
                physical: place,
                pin: frame
            )
        }

        fn acquireWrite(pointer: read write Records.Pointer)
            -> WriteLease<UserRecord>
            throws IOError | InvalidFile | CacheBusy | OutOfMemory
        {
            let page = Records.page(of: pointer)
            let frame = acquireFrame(page)
            let offset = Records.offset(of: pointer, in: page)
            let place = format.project<UserRecord>(frame.bytes, offset)

            return WriteLease(
                logical: pointer,
                physical: place,
                pin: frame,
                originalVersion: frame.version
            )
        }

        fn prepareWrite<Field>(
            lease: read WriteLease<UserRecord>,
            field: Field,
            value: field.Type
        ) -> PreparedWrite throws InvalidValue | OutOfMemory {
            return format.prepare(
                place: lease.physical,
                field: field,
                value: value
            )
        }

        fn commitWrite(
            lease: read write WriteLease<UserRecord>,
            prepared: take PreparedWrite
        ) {
            format.commit(lease.physical, take prepared)

            lease.pin.version = lease.pin.version.next()
            lease.pin.replica = Dirty
        }

        fn release(lease: take AccessLease<UserRecord>) {
            // Drop lease завершает borrow и снимает pin.
        }
    }

    fn flush() throws IOError {
        for frame in Frames {
            if frame.replica == Dirty {
                flush(frame)
            }
        }
    }

    fn find(id: UInt64)
        -> read write Records.Pointer?
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        for record in Records {
            if record.id == id {
                return record
            }
        }

        return null
    }

    fn close() throws IOError {
        flush()
        file.close()
    }
}

fn renameUser(
    users: read write UserFile,
    user: read write users.Records.Pointer,
    name: FixedString<48>
) throws IOError | InvalidFile | CacheBusy | OutOfMemory | InvalidValue {
    // Эта строка может выполнить cache lookup, readPage и suspension.
    // Право скрыть их дано transparent access Records.
    user.name = name
}

fn updateAndSave(
    users: read write UserFile,
    user: read write users.Records.Pointer,
    name: FixedString<48>
) throws IOError | InvalidFile | CacheBusy | OutOfMemory | InvalidValue {
    renameUser(users, user, name)

    // До этой строки новое имя уже является логическим значением.
    // После успешного flush оно долговечно.
    users.flush()
}

var users = UserFile(path: "users.dat")
let user = users.find(id: 42)!

echo user.name
renameUser(users, user, "Alice")
echo user.name
users.flush()
users.close()
```

Ожидаемый физический trace для первого `echo user.name`, если нужной страницы
нет в RAM:

```text
Records.page(user)
-> findResident: miss
-> Frames.create либо chooseVictim
-> evict dirty victim при необходимости
-> file.readPage
-> format.validatePage
-> publish Clean frame
-> create ReadLease and pin frame
-> format.project(UserRecord.name)
-> read
-> release lease and unpin frame
```

Для `user.name = "Alice"`:

```text
acquireWrite and pin frame
-> format.prepare new field encoding
-> no-throw format.commit
-> increment frame.version
-> publish Dirty authority
-> release lease
```

Именно этот цельный пример является материалом для утверждения кейсов S1–S13.
Пояснения ниже фиксируют смысл каждой части и найденные failure boundaries.

## Состояние кеша из двух frames

Пусть в RAM находятся страницы `4` и `9`:

```text
Frames
    F0 = { page: 4, replica: Clean, io: Idle, version: 12, pins: 0 }
    F1 = { page: 9, replica: Dirty, io: Idle, version: 8, pins: 1 }

Page 4
    версия файла 12
    версия frame 12
    обе копии допустимы для чтения

Page 9
    версия файла 7
    версия frame 8
    F1 является authoritative
    F1 нельзя вытеснить: он dirty и pinned
```

Реализация может хранить версии только как proof/debug metadata, если более
дешёвое представление доказывает те же свойства. Модель не требует отдельного
runtime-счётчика возле каждого production frame.

## Операция A: открытие существующего файла

Открытие не создаёт логические записи: их байты уже существуют.

```text
открыть файл с exclusive ownership или как стабильный snapshot
-> проверить magic, версию формата и codec witness
-> проверить размер файла, число записей и арифметические переполнения
-> последовательно проверить каждое encoded R через ограниченный frame buffer
-> установить множество допустимых identities
-> опубликовать Records и его origin
```

До проверки bounds, структуры и encoding нельзя создать `Records.Pointer`.
Минимальный пример использует eager validation, но удерживает только два frames.
Lazy-вариант рассматривается отдельно: непроверенные slots нельзя заранее
объявить населением `R`.

Внешний вызов:

```efen
var records = PagedFile<User>(path: "users.dat")
```

Решающая внутренняя операция пока записана так:

```efen
Records.map(file)
```

Её место среди остальных операций population:

```efen
Records.create(...)       // создать один логический элемент
Records.create(count: n)  // создать несколько логических элементов
Records.reserve(capacity: n)
Records.map(bytes)        // признать существующие bytes элементами после проверки
```

`map` заимствует file source, принадлежащий layout, и не потребляет binding
`file`. Перенос уже типизированного населения меняет origin и не входит в этот
пример.

## Операция B: transparent read при попадании в кеш

Пользовательский код остаётся обычным:

```efen
let name = user.name
```

Transparent implementation выполняет:

```text
page = pageOf(user)
frame = findResident(page)
проверить, что replica равна Clean или Dirty, а io равен Idle
увеличить frame.pins
спроецировать user.name через frame.bytes
прочитать logical place
уменьшить frame.pins после окончания logical borrow
```

Метаданные кеша могут измениться, но логическое значение не меняется.

## Операция C: transparent read при промахе кеша

Та же строка:

```efen
let name = user.name
```

может выполнить:

```text
page = pageOf(user)
frame = acquireFrame(page)
load(page, into: frame)
опубликовать frame как Clean
закрепить frame
спроецировать и прочитать user.name
освободить pin
```

`acquireFrame` переиспользует незакреплённый frame либо, пока
`Frames.count < frameLimit`, создаёт новый через `Frames.create(...)`.
`reserve` сам по себе frame не создаёт.

Вся fallible-работа завершается до публикации frame как current replica. Ошибка
чтения не меняет прежние отображения кеша и логическое состояние файла.

## Операция D: логическая запись

```efen
user.name = "Alice"
```

понижается в следующую последовательность:

```text
получить либо загрузить страницу для записи
получить исключительное logical write authority
закрепить frame
спроецировать выбранное поле
подготовить encoding нового значения и выполнить все fallible allocations
выполнить no-throw physical commit подготовленного значения
без wrap увеличить логическую версию
тем же commit опубликовать frame как Dirty и authoritative
освободить pin после окончания borrow
```

In-place update допустим, только если реализация доказывает, что физическая
запись и публикация `Dirty` не бросают и не приостанавливаются. Fallible encoding
не может изменить bytes, всё ещё помеченные `Clean`.

После завершения assignment все дальнейшие reads через этот layout видят
`Alice`. Долговечный файл всё ещё может содержать прежнее значение.

## Операция E: borrow и pin

```efen
let name = &read user.name
consume(name)
```

Origin borrow включает логическую запись и access lease. Frame остаётся pinned
до последнего использования `name`. В это время layout отклоняет или задерживает
операции, которые потребовали бы вытеснить, переместить или разрушительно
перезаписать frame.

Lease не обязан быть виден пользователю. При lowering его доказательство несёт
обычный Efen borrow.

## Операция F: выбор жертвы для вытеснения

Политика вытеснения является обычным кодом layout. Например, LRU выбирает любой
незакреплённый frame.

```text
candidate.pins обязан быть равен 0

candidate.replica == Clean и candidate.io == Idle:
    удалить page-to-frame mapping
    переиспользовать frame

candidate.replica == Dirty и candidate.io == Idle:
    выполнить flush(candidate)
    удалить mapping только после успешного flush
    переиспользовать frame
```

Если все frames закреплены, transparent access может ждать, приостановиться или
вернуть ошибку согласно своему публичному effect contract. Storage не может
молча инвалидировать живой borrow.

## Операция G: flush одного dirty frame

```text
потребовать frame.replica == Dirty
зафиксировать версию v и неизменяемые bytes этой версии
поставить frame.io = Flushing, сохранив authority за frame
записать v в новый page image либо через выбранный recovery protocol
дождаться заявленной границы durability

успех и frame.version == v:
    опубликовать replica = Clean, io = Idle

успех, но появилась версия v + 1:
    сохранить replica = Dirty, опубликовать io = Idle

ошибка:
    сохранить replica = Dirty, опубликовать io = Idle
    поставить durable state = Unknown, если протокол не доказал сохранность
    прежнего file image
```

File page не становится current только потому, что ОС приняла часть записи.
Публикация следует заявленной границе durability. Обычная in-place page write
может порваться при ошибке. Layout, обещающий корректное повторное открытие,
должен реализовать journal, copy-on-write либо другой recovery protocol.

## Операция H: flush всего layout

Пользователь явно запрашивает долговечность:

```efen
records.flush()
```

При исключительном write authority успешная операция устанавливает:

```text
для каждой логической страницы p:
    FilePage(p) == Logical(p)
```

Concurrent-вариант должен повторять работу до отсутствия более новых dirty
versions либо обещать более слабую snapshot durability. Один `flush()` не
гарантирует crash-atomic замену нескольких страниц. Для неё нужен journal,
copy-on-write root или другой транзакционный алгоритм внутри layout.

## Операция I: close и destruction

Здесь остаётся самостоятельное семантическое решение:

- `close()` может выполнить flush и вернуть `IOError`;
- destruction может требовать отсутствия dirty frames;
- отдельная операция discard может отказаться от недолговечных изменений,
  только если публичный контракт типа это разрешает;
- journaled layout может commit или rollback согласно своему протоколу.

Обычный destructor не может молча отбросить подтверждённые логические записи и
не может сообщить ошибку асинхронного flush. Вероятная безопасная модель — явный
fallible `close()`, переводящий значение в clean closed typestate, после чего
no-throw destructor освобождает ресурсы. Точная политика пока не выбрана.

## Дополнительный кейс J: append

Append не входит в минимальный цикл read/write/flush: он открывает отдельную
задачу persistent publication.

```efen
var user = Records.create(
    id: id,
    name: name
)
```

Bulk creation:

```efen
var users = Records.create(
    count: input.count,
    initializer: (i) => User(
        id: input[i].id,
        name: input[i].name
    )
)
```

Результат содержит новые identities `Records.Pointer`. Пока не решено, дают ли
эти pointers право удаления либо только доступ к persistent members, которыми
владеет population.

Batch больше двух страниц нельзя целиком удержать только как dirty authority в
двух RAM frames. Реализация должна последовательно записать provisional pages в
неавторитетную область файла, затем атомарно опубликовать новый header/root либо
использовать journal. До выбора этого протокола документ не обещает all-or-none
persistent bulk `create`.

## Схема lowering

Выражение:

```efen
user.name = "Alice"
```

семантически эквивалентно:

```text
lease = PagedFile.Records.access.acquireWrite(user)
place = lease.project(field: User.name)
replacement = prepareWrite(place, "Alice")
commitWriteAndPublishDirty(lease, place, replacement)
lease.release()
```

`release()` ставится на каждый обычный и исключительный выход. Реальный код
может встроить быстрый путь и вынести cache miss в cold helper:

```text
if directory[page].resident:
    fast projected access
else:
    loadPageSlow(page)
```

Семантический контракт обеих форм одинаков.

## Обязательства безопасности

### Логическая безопасность

- Каждый `Records.Pointer` принадлежит этому экземпляру layout.
- Его identity обозначает живую запись.
- Identity сохраняется при движении кеша и remap файла.
- Read наблюдает текущую логическую версию.
- Write требует исключительного logical authority.

### Физическая безопасность

- Frame одновременно содержит не более одной страницы.
- Одна logical page имеет не более одной resident writable authority.
- `Clean` idle frame совпадает с соответствующей долговечной страницей.
- `Dirty` или `Flushing` frame является authority своей logical page.
- В минимальном примере на одну page опубликован не более чем один RAM frame.
- Неопубликованный loading frame не может обслужить read.
- Pinned frame нельзя вытеснить или несовместимо переместить.
- Failed load не публикует неинициализированные bytes.
- Failed flush не теряет dirty authority.

### Создание и уничтожение

- Проверка файла предшествует публикации addressable identities.
- Encoded value проверяется до публикации как значение `R`.
- Частично инициализированная запись не является живым member.
- Каждое опубликованное поле инициализировано ровно один раз.
- Каждое logical value уничтожается ровно один раз при удалении.
- Физические копии не вызывают повторный logical destruction.
- Close ждёт завершения leases либо отклоняется согласно своему контракту.

## Семантические вопросы до окончательного синтаксиса

### P1. Ownership persistent members

Уничтожение локального pointer, возвращённого `Records.create(...)`, не должно
молча удалять долговечную запись. Population contract должен различать authority
доступа/удаления и lifetime persistent member. Точный result type `create` пока
не выбран.

### P2. Eager и lazy validation

Минимальный пример выбирает eager validation: open последовательно читает файл
ограниченным буфером и публикует `Records` только после проверки всех encoded
values. Lazy-варианту нужно отдельное население encoded slots; успешный decode
может создать `R`, но непроверенное население нельзя назвать `set Records: R`.

### P3. Внешнее изменение файла

Минимальный пример открывает файл эксклюзивно либо использует immutable snapshot.
При внешних writers нужны epochs, invalidation и повторная validation. Иначе
предикат равенства clean frame и file page становится ложным.

### P4. Ошибка persistent write

После failed flush dirty RAM остаётся logical authority. Но in-place запись могла
оставить torn file image. Повторное открытие требует journal, copy-on-write или
другой recovery algorithm.

### P5. Закрытие

Явный fallible close может выполнить flush и перейти в clean closed typestate.
После этого no-throw destructor освобождает ресурсы. Explicit discard, retry
после failed flush и recovery после process crash являются разными политиками.

## Синтаксические кейсы для последовательного утверждения

### S1. Несколько физических областей

Кандидат:

```efen
source file: FileMemory
source cache: RamMemory
```

Обе области участвуют в одном логическом layout. Layout не отождествляется ни с
одной из них.

### S2. Логические и физические populations

Кандидат:

```efen
set Records: R
set Frames: Frame
```

Оба являются высокоуровневыми populations со своими pointer types. Роль
логического содержимого или физической реализации следует из алгоритмов и
отношений, а не из двух разных видов `set`.

### S3. Принятие существующих физических данных

Кандидат:

```efen
Records.map(file)
```

`map` проверяет и интерпретирует физическое содержимое через source, которым
продолжает владеть layout. Перенос typed population с изменением origin —
отдельный будущий кейс.

### S4. Объявление transparent access implementation

Кандидат:

```efen
transparent access Records {
    fn acquireRead(...)
    fn acquireWrite(...)
    fn release(...)
}
```

Вся группа операций, а не одна функция, может реализовать обычный field access
через pointer.

### S5. Использование transparent access

Направление уже согласовано:

```efen
let value = pointer.field
pointer.field = value
```

В месте использования нет дополнительного marker. Effects и suspension входят
в inferred или declared contract содержащей функции.

### S6. Внутренний результат access

Кандидаты:

```efen
ReadLease<R>
WriteLease<R>
AccessLease<R, Mode>
```

Результат удерживает physical storage pinned на время logical borrow и даёт
field projection. Обычный пользовательский код не обязан уметь назвать его тип.

### S7. Logical creation и capacity

Направление уже согласовано:

```efen
Records.create(...)
Records.create(count: n, initializer: ...)
Records.reserve(capacity: n)
```

`create` меняет logical membership. `reserve` меняет только доступную physical
capacity.

### S8. Durability

Направление уже согласовано:

```efen
pointer.field = value
records.flush()
```

Assignment завершается после публикации authoritative RAM replica. `flush()`
отдельно запрашивает durability.

### S9. Политика close

Кандидаты:

```efen
records.close() throws IOError
records.close(discard: true)
```

Нужно определить, выполняет ли обычный close flush, отклоняет dirty state либо
может явно отказаться от него.

### S10. Ожидание свободного frame

Если все frames pinned, transparent access может приостановиться, вернуть
resource error либо применить policy своей реализации. Выбранное поведение
обязательно входит в публичный effect contract.

### S11. Witness файлового представления

Одного `R` недостаточно для интерпретации bytes. Нужен retained witness, который
задаёт encoded size, alignment, endian, допустимые bit patterns, field
projections и lifecycle rules.

Кандидат:

```efen
generic Format: RecordFormat<R>
let format: Format
```

Точное размещение generic-параметра и имя контракта пока не выбраны.

### S12. Предикаты отношений физических свойств

Эскиз frame использует property predicate:

```efen
var page: Records.Page? {
    page == null || Frames.count(where: it.page == page) == 1
}
```

Он требует уникальности page среди живых `Frames` и прикреплён к свойству,
изменение которого способно нарушить условие. Точный синтаксис квантификации по
другому population остаётся открытым.

### S13. Стабильная identity страницы

Эскиз использует `Records.Page` как стабильную страницу логической записи. Это
не array index, инвалидируемый append или ростом файла. Точный derived-type
syntax открыт; обязательная семантика — стабильная identity, origin данного
layout и проверяемый переход к текущему file range.

## Проверочные сценарии

Будущая реализация должна пройти как минимум следующие behaviour tests:

1. Повторные reads одной записи загружают её страницу один раз.
2. Чтение трёх страниц через два frames корректно вытесняет одну страницу.
3. Dirty unpinned victim сбрасывается перед переиспользованием.
4. Failed flush сохраняет dirty page как logical authority.
5. Живой field borrow запрещает вытеснить его frame.
6. Failed load не публикует mapping или неинициализированные records.
7. Logical write немедленно виден дальнейшим reads до `flush()`.
8. Успешный exclusive `flush()` делает подтверждённые writes долговечными.
9. Remap сохраняет identities `Records.Pointer`.
10. Raw или address-dependent borrow запрещает несовместимый remap.
11. Fallible field encoding не оставляет изменённые bytes в состоянии `Clean`.
12. Flush версии `v` не может объявить clean появившуюся версию `v + 1`.
13. Внешний writer не может разрушить предикат живого clean frame.
14. Close с dirty frames следует выбранной и документированной policy.

Bulk `create` получает собственные проверки после выбора протокола публикации
header/root.

## Граница обобщения

Следующие применения являются гипотезами, которыми нужно проверить общий
механизм до добавления новых языковых primitives:

- register allocation: logical values реализуются registers и spill slots;
- DMA: logical buffers реализуются host-, in-flight- и device-копиями;
- GPU memory: host/device replicas с явной передачей authority;
- NUMA: один logical object с node-local read replicas;
- compressed storage: logical fields через decoded cache blocks;
- database pages: RAM frames поверх journaled или copy-on-write file pages.

Меняются physical populations, access functions и predicates. Logical pointers,
ownership, borrows, effects и publication rules остаются общими.
