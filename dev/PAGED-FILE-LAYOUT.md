# Layout и representation-aspect

Статус: проект модели для обсуждения. Здесь зафиксирована семантика, принятая в
разговоре, и приведён кандидат синтаксиса. Нормативные документы Efen пока не
изменены.

Документ проверен на двух разных задачах:

1. логическая база данных, реализованная в RAM или через файл с кешем;
2. реальный memory manager Limelight, который получает большие области памяти и
   динамически делит их на blocks, slots, arena allocations и отдельные runs.

## 1. Основная модель

`layout` и representation отвечают на разные вопросы.

```text
layout
    Что логически существует?
    Какие есть populations, values, pointers, predicates и операции?

representation-aspect
    Как конкретная generic-инстанциация реализована физически?
    Где лежат данные и каким кодом выполняются primitive operations?
```

Representation является aspect. Компилятор вызывает его во время компиляции и
передаёт definition конкретного типа или layout. Aspect регистрирует physical
state, implementations и handlers в обычном aspect definition plan. После
фиксации плана компилятор собирает logical methods через эти handlers и запускает
обычные type, CFG, effect, ownership и predicate checks.

Тип должен сам предусмотреть representation в своих generics:

```efen
layout Database {
    generic Physical: Representation = InMemory
    use Physical

    // logical definition
}
```

Внешний код не может заменить representation типа, который не объявил такую
точку. Эти generic-инстанциации являются разными concrete types:

```efen
Database<InMemory>
Database<BufferedFile>
```

Обычные правила generics определяют фиксированные aspect-параметры и packs. Тип
сам задаёт допустимое число, роли и порядок aspects.

## 2. Три разных области реализации

Aspect, применённый к layout, видит несколько возможных получателей. Поэтому
голый блок `implementation` и голый constructor неоднозначны.

### 2.1. Реализация конкретного типа

```efen
type implementation target {
    // physical members корневого realized type
    // constructors и methods корневого realized type
}
```

Для вложенного типа получатель называется отдельно:

```efen
type implementation target.User {
    // implementation именно User
}
```

`Self` внутри каждого блока означает явно названный type. Constructor корневого
блока создаёт `Database<BufferedFile>`. Constructor блока `target.User` создаёт
отдельный `User`.

### 2.2. Реализация population

Population не является типом и не имеет constructor. Она предоставляет
primitive operations логической памяти:

```efen
population implementation target.Users {
    reserve = owner.reserveUser
    access = owner.accessUser
    retire = owner.retireUser
    enumerate = owner.enumerateUsers
}
```

Здесь `owner` — runtime-экземпляр realized layout, а `population` — конкретное
население этого экземпляра. Точные имена handlers являются кандидатами.
`enumerate` может предоставить эффективный physical order, но core сверяет его с
`Live`; handler не создаёт membership и не может пропустить live identity в
операции, обещающей полный logical обход.

### 2.3. Физический источник

`source` — специальный physical member с явным ownership mode:

```efen
source file: own File
source ram: own Ram
source system: read write VirtualMemory
```

Source хранится в realized type и задаёт границу происхождения физических
grants. Он может быть файлом, RAM provider, `VirtualMemory`, другим layout или
адаптером FFI. Source не связывает один logical type с одним allocator.

## 3. Кто отвечает за identity и lifetime

Core layout владеет логическими identities и membership. Representation не
может самостоятельно опубликовать произвольную identity или удалить её из
`Live`.

Логическое создание выполняется так:

```text
core выбирает exact logical constructor
→ core резервирует fresh identity, ещё не входящую в Live
→ representation резервирует provisional physical grants
→ logical constructor инициализирует значение в этих grants
→ проверяются logical predicates
→ core одним no-throw commit публикует identity, Live и mappings
→ возвращается Population.Pointer
```

Ошибка до commit уничтожает только уже инициализированные части, возвращает
physical reservations и не создаёт member.

`Population.Pointer` является logical pointer. Его identity не обязана быть
physical address. Relocation, cache eviction, remap и смена allocator authority
не меняют identity.

Population владеет lifetime members. Уничтожение локального pointer не удаляет
member. Удаление — явная логическая операция population. Representation
возвращает physical storage только после того, как core завершил logical
lifecycle и разрешил reclamation.

## 4. Граница власти representation

Representation может менять только compiler-defined realization seams:

- physical reservation и reclamation;
- logical identity → physical place;
- field и whole-value projection;
- create/remove preparation;
- iteration и enumeration;
- copy/move/drop lowering;
- transparent access;
- private physical state;
- representation-specific public API, если контракт `Representation` даёт это
  право.

Representation не заменяет произвольные logical methods. Иначе aspect мог бы
заменить:

```efen
balance += amount
```

на:

```efen
balance += amount * 2
```

и обычные type/ownership checks не доказали бы эквивалентность. Logical method
bodies сохраняются; representation реализует только зафиксированные seams, через
которые они обращаются к памяти.

Обычные aspects работают через checked compiler seams. Доступ к raw/native
physical primitives требует явной trusted boundary соответствующего backend или
source.

## 5. Стадии применения

Representation не создаёт параллельный compilation pipeline.

```text
generic substitution и immutable logical definition
→ non-mutating registration в общем aspect plan
→ фиксация type/population implementation recipients и порядка
→ materialization private physical state и public surface
→ binding primitive population/access handlers
→ compilation logical method bodies через зафиксированные handlers
→ effects, throws, suspension, ownership и predicates
→ publication realized type
```

Поздняя замена handler после анализа зависимого body является ошибкой.

Кандидат регистрационной формы:

```efen
aspect BufferedFile conforms Representation {
    meta fn register(
        target: lang::TypeDefinition,
        plan: lang::DefinitionPlan
    ) {
        requireDatabaseShape(target)

        plan.define {
            type implementation target {
                // runtime implementation root type
            }

            population implementation target.Users {
                // primitive population handlers
            }
        }
    }
}
```

`target` существует только во время compile time. `self` появляется только в
runtime body конкретного `type implementation`. Declarative blocks понижаются в
тот же definition plan, что и остальные aspect transformations.

## 6. Логическая база данных

В logical layout нет файла, RAM, страниц или кеша.

```efen
layout Database {
    generic Physical: Representation = InMemory
    use Physical

    set Users: User

    struct User {
        let id: UInt64

        var balance: Int64 {
            balance >= 0
        }

        var name: FixedString<48>
    }

    fn findUser(id: UInt64) -> read write Users.Pointer? {
        for user in Users {
            if user.id == id {
                return user
            }
        }

        return null
    }

    fn renameUser(id: UInt64, name: FixedString<48>) -> Bool {
        let user = findUser(id)

        if user == null {
            return false
        }

        user.name = name
        return true
    }

    fn deposit(id: UInt64, amount: Int64) -> Bool {
        require amount >= 0

        let user = findUser(id)

        if user == null {
            return false
        }

        user.balance += amount
        return true
    }
}
```

Минимальный пример deliberately read/update-only: membership `Users` фиксируется
при construction/import. Append/remove требуют отдельного persistent directory,
tombstones/generations и publication/recovery protocol; заглушки не выдаются за
реализацию.

Freeze membership является обязательством logical contract этого примера, а не
решением `BufferedFile`. Точный surface syntax такого обязательства будет
утверждаться отдельно.

## 7. InMemory representation

```efen
aspect InMemory conforms Representation {
    meta fn register(
        target: lang::TypeDefinition,
        plan: lang::DefinitionPlan
    ) {
        requireDatabaseShape(target)

        plan.define {
            type implementation target {
                source ram: own Ram

                let locations: IdentityMap<PhysicalPlace>

                @constructor
                public fn init(
                    ram: own Ram,
                    users: [target.User]
                ) -> Self {
                    self.ram = take ram
                    self.locations = IdentityMap()
                    self.Users.import(take users)
                    return self
                }

                fn reserveUser(request: PlacementRequest)
                    -> PhysicalReservation
                {
                    let place = self.ram.reserve(
                        bytes: request.size,
                        alignment: request.alignment
                    )

                    return PhysicalReservation(
                        place: place,
                        rollback: () => self.ram.release(place)
                    )
                }

                fn accessUser(pointer: read self.Users.Pointer)
                    -> AccessLease<self.User>
                {
                    return AccessLease(
                        logical: pointer,
                        physical: self.locations[pointer.identity]
                    )
                }

                fn enumerateUsers() -> Iterator<self.Users.Pointer> {
                    return self.Users.liveIdentities()
                }
            }

            population implementation target.Users {
                reserve = owner.reserveUser
                access = owner.accessUser
                enumerate = owner.enumerateUsers
            }
        }
    }
}
```

`Users.import` остаётся core logical transaction. Aspect предоставляет
physical reservations; core выполняет constructors, публикует `Live` и
заполняет `locations`. Удаление identity также сначала проходит core lifecycle,
после чего representation получает право вернуть RAM grant.

## 8. BufferedFile representation

Формат фиксирован для минимального примера:

```text
page size:       4096 bytes
encoded User:      64 bytes
records per page:  64
cache:              2 resident pages
```

Одна запись не пересекает page boundary. `UserFileV1` задаёт offsets и encoding
полей, а не использует native ABI структуры `User`.

```efen
aspect BufferedFile conforms Representation {
    meta fn register(
        target: lang::TypeDefinition,
        plan: lang::DefinitionPlan
    ) {
        requireDatabaseShape(target)

        plan.define {
            type implementation target {
                source file: own File
                source ram: own Ram

                type Page: UInt64

                enum FrameState {
                    Empty
                    Clean
                    Dirty
                    Loading
                    Flushing
                }

                struct Frame {
                    var page: Page? {
                        (page == null) ==
                            (state == Empty || state == Loading)
                    }
                    var bytes: PageBytes<4096>
                    var state: FrameState
                    var version: Version
                    var lastUse: UInt64

                    var pins: UInt {
                        get { return liveLoans(to: self).count }
                    }
                }

                let format: UserFileV1 = UserFileV1()
                let cache: PhysicalGrant
                var frames: [Frame] {
                    .count == 2 && unique(
                        .filter((frame) => frame.page != null)
                            .map((frame) => frame.page)
                    )
                }
                var clock: UInt64 = 0

                @constructor
                public fn init(file: own File, ram: own Ram) -> Self {
                    self.file = take file
                    self.ram = take ram

                    self.cache = self.ram.reserve(
                        bytes: 8192,
                        alignment: 4096
                    )

                    // Один grant разбит на две непересекающиеся page areas.
                    let pages = self.cache.split<PageBytes<4096>>(
                        count: 2,
                        stride: 4096
                    )

                    // Frame metadata лежит отдельно; bytes являются view grant.
                    self.frames = pages.map((bytes) =>
                        Frame(
                            page: null,
                            bytes: bytes,
                            state: Empty,
                            version: Version.initial,
                            lastUse: 0
                        )
                    )

                    self.format.validateHeader(self.file)
                    self.format.validateAll(
                        self.file,
                        through: self.frames
                    )

                    // Core публикует проверенные logical identities Users.
                    self.Users.import(
                        count: self.file.header.userCount
                    )

                    return self
                }

                fn findResident(page: Page) -> read write Frame? {
                    for frame in self.frames {
                        if frame.page == page &&
                           (frame.state == Clean || frame.state == Dirty) {
                            return frame
                        }
                    }

                    return null
                }

                fn chooseVictim() -> read write Frame throws CacheBusy {
                    var result: read write Frame? = null

                    for frame in self.frames {
                        if frame.pins == 0 &&
                           (frame.state == Empty ||
                            frame.state == Clean ||
                            frame.state == Dirty) &&
                           (result == null || frame.lastUse < result.lastUse) {
                            result = frame
                        }
                    }

                    if result == null {
                        throw CacheBusy()
                    }

                    return result
                }

                fn flushFrame(frame: read write Frame) throws IOError {
                    if frame.state != Dirty {
                        return
                    }

                    require frame.pins == 0

                    let page = frame.page
                    let version = frame.version
                    frame.state = Flushing

                    try {
                        // Exclusive access сериализует эту минимальную
                        // representation, поэтому snapshot-copy не нужен.
                        self.file.writePage(
                            page: page,
                            from: frame.bytes
                        )
                        self.file.sync(page)
                        frame.state = Clean
                    } catch error: IOError {
                        // RAM остаётся logical authority. Файл мог стать torn;
                        // повторное открытие требует recovery representation.
                        frame.state = Dirty
                        throw error
                    }

                    assert frame.version == version
                }

                fn evict(frame: read write Frame) throws IOError {
                    require frame.pins == 0

                    if frame.state == Dirty {
                        flushFrame(frame)
                    }

                    frame.commitState(
                        page: null,
                        state: Empty
                    )
                }

                fn load(page: Page, into frame: read write Frame)
                    throws IOError | InvalidFile
                {
                    if frame.state != Empty {
                        evict(frame)
                    }

                    frame.state = Loading

                    try {
                        // File читает прямо в заранее выбранный cache frame.
                        self.file.readPage(
                            page: page,
                            into: frame.bytes
                        )
                        self.format.validatePage(page, frame.bytes)

                        frame.commitState(
                            page: page,
                            state: Clean,
                            version: self.file.version(page)
                        )
                    } catch error: IOError | InvalidFile {
                        frame.commitState(
                            page: null,
                            state: Empty
                        )
                        throw error
                    }
                }

                fn acquireFrame(page: Page)
                    -> read write Frame
                    throws IOError | InvalidFile | CacheBusy
                {
                    let resident = findResident(page)

                    if resident != null {
                        self.clock += 1
                        resident.lastUse = self.clock
                        return resident
                    }

                    let frame = chooseVictim()
                    load(page, into: frame)
                    self.clock += 1
                    frame.lastUse = self.clock
                    return frame
                }

                fn accessUser(pointer: read self.Users.Pointer)
                    -> AccessLease<self.User>
                    throws IOError | InvalidFile | CacheBusy
                {
                    let record = self.format.location(pointer.identity)
                    let frame = acquireFrame(record.page)

                    return AccessLease(
                        logical: pointer,
                        physical: self.format.project(
                            frame.bytes,
                            record.offset
                        ),
                        pin: frame
                    )
                }

                fn prepareUserWrite<Field>(
                    lease: read AccessLease<self.User>,
                    field: Field,
                    value: field.Type
                ) -> PreparedFieldWrite {
                    return self.format.prepareWrite(
                        place: lease.physical,
                        field: field,
                        value: value
                    )
                }

                fn commitUserWrite(
                    lease: read write AccessLease<self.User>,
                    prepared: own PreparedFieldWrite
                ) {
                    // Encoding, version и Dirty authority меняются одним
                    // no-throw commit после всех fallible preparations.
                    lease.pin.commitWrite(
                        place: lease.physical,
                        encoding: take prepared,
                        version: lease.pin.version.next(),
                        state: Dirty
                    )
                }

                fn releaseUserAccess(
                    lease: own AccessLease<self.User>
                ) {
                    // Drop lease завершает borrow и снимает pin.
                }

                fn enumerateUsers() -> Iterator<self.Users.Pointer> {
                    return self.Users.liveIdentities()
                }

                public fn prefetch(pointer: read self.Users.Pointer)
                    throws IOError | InvalidFile | CacheBusy
                {
                    acquireFrame(
                        self.format.location(pointer.identity).page
                    )
                }

                public fn flush() throws IOError {
                    // Exclusive receiver authority запрещает живые leases.
                    assert self.frames.all(where: it.pins == 0)

                    for frame in self.frames {
                        flushFrame(frame)
                    }
                }

                public fn close() throws IOError {
                    flush()
                    self.file.close()
                }
            }

            population implementation target.Users {
                access = owner.accessUser
                prepareWrite = owner.prepareUserWrite
                commitWrite = owner.commitUserWrite
                release = owner.releaseUserAccess
                enumerate = owner.enumerateUsers
            }
        }
    }
}
```

В minimal slice `BufferedFile` не shared. Exclusive borrow его cache state живёт
через suspension, поэтому два load/flush одной page не interleave. Concurrent
aspect должен добавить directory и coherence protocol.

Transparent access не требует отдельного marker:

```efen
alias FileDatabase = Database<BufferedFile>

var database = FileDatabase(
    file: File.open("users.db", access: readWrite),
    ram: Ram(size: 8192)
)

let user = database.findUser(42)!

echo user.name       // может загрузить page и приостановить функцию
user.name = "Alice" // RAM frame становится Dirty authority

database.flush()    // отдельная durability boundary
database.close()
```

Effects, exceptions и suspension наследуются автоматически. Explicitly closed
contract, несовместимый с handlers выбранной representation, даёт compile error.

## 9. Columnar как representation-aspect

`Columnar` получает конкретный контейнер и logical structure его element type.
Он сам решает applicability.

```efen
struct X {
    var a: Int
    var b: Float
}

struct Array {
    generic Element: Type
    generic Physical: Representation = Contiguous
    use Physical

    fn append(value: Element)
    fn get(index: Index) -> read write Element
}
```

```efen
aspect Columnar conforms Representation {
    meta fn register(
        target: lang::TypeDefinition,
        plan: lang::DefinitionPlan
    ) {
        let element = target.genericArgument("Element")

        if !supportsColumnProjection(element) {
            compileError("Columnar cannot represent ${element}")
        }

        plan.define {
            type implementation target {
                // По одному physical storage на logical field Element.
                let columns: Columns<element> = Columns<element>()

                fn prepareAppend(value: element)
                    -> PreparedColumns<element>
                {
                    // Резервирует все columns и сохраняет ownership уже
                    // подготовленных частей для no-throw rollback.
                    return self.columns.prepare(value)
                }

                fn commitAppend(prepared: own PreparedColumns<element>) {
                    // No-throw commit всех columns и общего count.
                    self.columns.commit(take prepared)
                }

                fn acquireElement(index: self.Index)
                    -> CompositeLease<element>
                {
                    return self.columns.lease(index)
                }
            }

            plan.bind(
                target.elementOperations,
                prepareAppend: target.prepareAppend,
                commitAppend: target.commitAppend,
                access: target.acquireElement
            )
        }
    }
}
```

`CompositeLease<X>` является logical place над несколькими columns:

```efen
alias XColumns = Array<X, Columnar>

var values = XColumns()
values.append(X(a: 1, b: 2.0))
values.append(X(a: 3, b: 4.0))

values[1].a = 10
echo values[0].b
```

Whole-element operations имеют определённую семантику:

```efen
let copy: X = values[0]       // gather logical fields
values[1] = copy              // prepare all fields, then scatter commit
mutate(&values[0])            // composite borrow, не fabricated contiguous &X
swap(values[0], values[1])    // transaction over all columns
```

Код, требующий native-contiguous `&X`, неприменим к composite place. Компилятор
не создаёт скрытый pointer на несуществующий цельный объект.

Opaque type наследует exact physical representation underlying type. Это не
раскрывает его public API и не создаёт отдельный encoding.

## 10. Limelight memory manager как решающий пример

Фактическая архитектура `/home/edmond/limelight/model`:

```text
OS / VirtualMemory
    2 MiB regions
        BlockPool: 64 KiB blocks
            256-byte tagged header
            65 280-byte payload

Physical routing одного entity:
    small counted, <= 8192 B     → size-class slot
    medium, <= 65 280 B          → один pooled block
    huge                         → OS-direct aligned run
    request-scoped small         → arena bump
    request-scoped huge          → logged direct run

Out-of-line body:
    request category             → request arena
    counted/long-lived           → buffer arena
    huge                         → direct run
```

Один type не соответствует одному source. Один entity может иметь inline header
в entity slot и отдельно размещённый body в buffer arena. Один 64 KiB block в
разное время становится heap, entity, arena, buffer, retained или free block.

Логический owner должен быть долгоживущим runtime layout. Thread heaps и request
arenas являются его components. Иначе thread-exit adoption ложно уничтожило бы
entities, а arena promotion потребовала бы перетипизировать все pointers.

```efen
layout RuntimeMemory {
    generic Physical: Representation = LimelightNative
    use Physical

    set Entities: Entity

    // Logical lifetime, reset, escape и collection algorithms.
}
```

```efen
aspect LimelightNative conforms Representation {
    meta fn register(
        target: lang::TypeDefinition,
        plan: lang::DefinitionPlan
    ) {
        requireRuntimeMemoryShape(target)

        plan.define {
            type implementation target {
                source system: own VirtualMemory

                let pool: BlockPoolState
                let entityHeaps: EntityHeapStates
                let requestArenas: RequestArenaStates
                let bodyArenas: BufferArenaStates
                let runs: RunRegistry

                @constructor
                public fn init(system: own VirtualMemory) -> Self {
                    self.system = take system
                    self.pool = BlockPoolState()
                    self.entityHeaps = EntityHeapStates()
                    self.requestArenas = RequestArenaStates()
                    self.bodyArenas = BufferArenaStates()
                    self.runs = RunRegistry()
                    return self
                }

                fn reserveEntity(request: EntityPlacementRequest)
                    -> EntityReservation
                {
                    match request.category {
                        RequestArena => {
                            return self.requestArenas.reserveEntity(
                                request,
                                pool: self.pool,
                                backing: self.system
                            )
                        }

                        GcHeap | LongLived => {
                            if request.bytes <= 8192 {
                                return self.entityHeaps.reserveSlot(
                                    request,
                                    pool: self.pool,
                                    backing: self.system
                                )
                            }

                            if request.bytes <= 65280 {
                                return self.pool.reserveWholeBlock(
                                    request,
                                    backing: self.system
                                )
                            }

                            return self.runs.reserve(
                                request,
                                backing: self.system,
                                alignment: 65536
                            )
                        }

                        Immortal => {
                            return self.reserveImmortal(request)
                        }
                    }
                }

                fn reserveBody(request: BodyPlacementRequest)
                    -> BodyReservation
                {
                    match request.category {
                        RequestArena => {
                            return self.requestArenas.reserveBody(
                                request,
                                pool: self.pool,
                                backing: self.system
                            )
                        }

                        GcHeap | LongLived => {
                            return self.bodyArenas.reserveBody(
                                request,
                                pool: self.pool,
                                backing: self.system
                            )
                        }

                        Immortal => {
                            return self.reserveImmortalBody(request)
                        }
                    }
                }

                fn accessEntity(pointer: read self.Entities.Pointer)
                    -> AccessLease<self.Entity>
                {
                    let grant = self.Entities.physicalGrant(pointer.identity)
                    let block = grant.place.mask(alignment: 65536)
                    return block.kind.access(pointer, grant)
                }

                fn retireEntity(retirement: EntityRetirement) {
                    // Logical death уже завершена core. Физический возврат
                    // может быть отложен remote-free, trace window или hold.
                    retirement.grant.owner.retire(retirement.grant)
                }

                fn scanCountedEntityGrants()
                    -> Iterator<PhysicalGrant>
                {
                    let pooled = self.pool.regions()
                        .blocks()
                        .flatMap((block) => match block.kind {
                            Entity => block.occupiedSizeClassSlots()
                            EntityLarge => [block.soleOccupant()]
                            Retained => block.retainedOccupantInventory()
                            _ => []
                        })

                    return pooled + self.runs.registeredEntityLargeRuns()
                }
            }

            population implementation target.Entities {
                reserve = owner.reserveEntity
                access = owner.accessEntity
                retire = owner.retireEntity
            }
        }
    }
}
```

`reserveBody` не регистрируется как implementation отдельного logical
population. Это physical seam, который вызывает representation конкретного
entity type, когда его logical value требует out-of-line payload. Body остаётся
частью одного entity lifecycle.

Обычный обход `Entities` перечисляет core `Live`.
`scanCountedEntityGrants` является отдельной physical operation collector-а:
она обходит entity size-class blocks, pooled large entities, retained occupant
inventories и registry OS-direct entity runs. Активные request-arena entities не
становятся counted heap rows. Physical census не получает права изобретать
logical membership.

`EntityReservation` и `BodyReservation` обязаны хранить или доказывать:

- granted size и alignment;
- physical provenance;
- единственное право rollback;
- ownership всех provisional fragments;
- no-throw commit в опубликованный object;
- возврат каждой части ровно один раз при failure.

Для body free используется granted capacity, а не requested size. Category
определяет, освобождается ли body отдельно вообще; block kind затем выбирает
механизм внутри разрешённого domain.

### Разбиение одного block

Representation может получить один physical grant и разбить его как угодно при
проверяемой arithmetic:

```efen
fn commissionBlock(
    block: own Block<65536>,
    stride: Size
) -> SlotBlock {
    let header = block.take(range: 0..<256)
    let payload = block.take(range: 256..<65536)

    let slots = payload.split(
        stride: stride,
        alignment: 16
    )

    return SlotBlock(
        header: take header,
        slots: take slots,
        bump: 0,
        free: null
    )
}
```

Compiler проверяет bounds, alignment, непересечение частей и то, что ownership
исходного block полностью распределён между результатами. Intrusive free-list
может хранить link в bytes свободного slot: после logical death эти bytes больше
не принадлежат прежнему entity value и становятся allocator metadata. В
Limelight link entity free-list лежит в bytes `8..16`; bytes `0..8` сохраняют
финальный нулевой refcount/flags, который collector использует как occupancy
stamp.

### Promotion и adoption

```text
arena survivor promotion:
    logical identity сохраняется
    native address может сохраниться
    меняются lifetime category и reclamation state

thread exit adoption:
    logical entities сохраняются
    physical blocks сохраняются
    меняется authority над allocator-private state
```

Representation не имеет права тайно изменить `Live`. Решение о survival,
escape, reset и logical destruction принимает `RuntimeMemory`; aspect реализует
требуемые physical transitions.

## 11. Transparent access и effects

Transparent access реализует logical place, а не обязательно native `&T`:

```text
acquire logical authority
→ representation lease
→ field либо composite projection
→ fallible prepare
→ predicate check
→ no-throw publication
→ release lease на всех exits
```

`&pointer.field` удерживает lease и необходимые pins до конца borrow. Eviction,
relocation и reclamation не могут нарушить этот borrow. Effects, exceptions и
suspension handlers должны быть известны до анализа caller и автоматически
распространяются по графу вызовов.

Representation не может удерживать exclusive borrow allocator state через вызов
пользовательского destructor, collector callback или другой reentrant code. Она
завершает structural mutation, отпускает borrow, вызывает user code, затем снова
получает state и перечитывает предположения.

При destruction порядок один:

```text
завершить logical lifetimes
→ закончить либо передать physical grants и holds
→ уничтожить allocator/cache metadata
→ отпустить sources
```

Owning source уничтожается последним. Borrowed source только освобождает свой
borrow/reference.

Имена `DefinitionPlan`, `PhysicalReservation`, `AccessLease`,
`IdentityMap`, `CompositeLease`, `EntityRetirement` и методы `plan.define` в
примерах обозначают ещё не выписанные library/compiler contracts. Код является
архитектурным Efen sketch. В частности, core commit `Users.import` заполняет
`IdentityMap` через зарегистрированный mapping seam; aspect не мутирует `Live`
самостоятельно.

## 12. Что уже решено без отдельного вопроса

- `Array<X>` означает exact default generic-instantiation.
- `Array<X, Columnar>` является другим concrete type.
- Общая функция явно параметризуется representation generic.
- Aspect composition следует обычным fixed generic parameters или packs.
- Applicability определяет representation-aspect.
- Representation может работать со структурами и классами.
- Opaque type наследует exact representation underlying type.
- Representation-specific public API разрешается контрактом `Representation`.
- Default visibility остаётся private; `private` в примерах не дублируется.
- Constructor записывается `@constructor fn init(...) -> Self`.
- Suspension, effects и exceptions могут выводиться автоматически.
- Mixed placement является внутренним алгоритмом population implementation.

## 13. Кандидаты синтаксиса для утверждения

### S1. Generic representation-aspect

```efen
generic Physical: Representation = InMemory
use Physical
```

### S2. Регистрация в общем definition plan

```efen
meta fn register(
    target: lang::TypeDefinition,
    plan: lang::DefinitionPlan
)
```

### S3. Реализация конкретного type

```efen
type implementation target {
    // members, constructors, methods
}
```

### S4. Реализация конкретного population

```efen
population implementation target.Users {
    reserve = owner.reserveUser
    access = owner.accessUser
    enumerate = owner.enumerateUsers
}
```

### S5. Physical source member

```efen
source file: own File
source ram: own Ram
```

### S6. Constructor точного realized type

```efen
type implementation target {
    @constructor
    public fn init(file: own File, ram: own Ram) -> Self {
        self.file = take file
        self.ram = take ram
        return self
    }
}
```

### S7. Обычный transparent access

```efen
echo user.name
user.name = "Alice"
```

Дополнительный marker на месте доступа не нужен.

## 14. Проверочные сценарии

1. `Database<InMemory>` и `Database<BufferedFile>` проходят одинаковые logical
   read/update tests.
2. Representation не может зарегистрировать handler после анализа logical body.
3. Failed physical prepare не публикует logical identity.
4. Remove инвалидирует identity до физического reuse.
5. Cache hit не читает файл повторно.
6. Cache miss читает прямо в выбранный frame.
7. Три pages через два frames вызывают корректное eviction.
8. Field borrow удерживает frame pinned.
9. Logical write виден до `flush()`.
10. Failed flush сохраняет RAM authority и честно отмечает неопределённость
    durable image.
11. `Array<X, Columnar>` поддерживает field и whole-element operations через
    composite place.
12. Failed column prepare откатывает уже подготовленные fields ровно один раз.
13. Limelight small entity идёт в size-class slot.
14. Limelight medium entity занимает один pooled block.
15. Limelight huge entity получает OS-direct run.
16. Entity body использует отдельный routing и granted capacity.
17. Arena promotion сохраняет logical identity.
18. Thread adoption меняет physical authority без изменения logical membership.

## 15. Документы, которые новая модель заменит после утверждения

Текущие нормативные документы всё ещё описывают прежнюю модель representation
как enum/value, принадлежащую типу, а physical `storage` — внутри logical layout.
После утверждения синтаксиса нужно синхронно обновить:

- `docs/efen/representations.md`;
- `docs/efen/generics.md`;
- `docs/efen/memory/addresses.md`;
- `docs/efen/memory/columnar-layouts.md`;
- `docs/efen/memory/layout-representations.md`;
- документы аспектов и compile-time API;
- Amber `dev/DECISIONS.md`, `dev/PLAN.md`, HIR generics/declarations и
  compilation plan.
