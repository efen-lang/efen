# Layout, representation-aspect и физическая память

Статус: проект для обсуждения. Документ показывает цельную предлагаемую модель,
но не изменяет нормативную спецификацию Efen. Синтаксические формы в последнем
разделе предстоит утверждать последовательно.

Модель проверена на трёх задачах:

1. одна логическая база данных с реализациями в RAM и в файле;
2. колоночный массив структур;
3. реальный memory manager Limelight с regions, blocks, slots, arenas, buffers
   и large runs.

## 1. Два уровня

`layout` описывает логическую память:

- именованные `set`;
- значения и связи между ними;
- `Set.Pointer` и логическую адресную арифметику;
- свойства и предикаты;
- logical algorithms.

Representation является aspect, который описывает физическую реализацию
конкретного типа:

- physical fields и sources;
- placement и reclamation;
- mapping logical identity → physical place;
- field и whole-value access;
- create/remove preparation;
- copy, move и drop;
- iteration plans;
- transparent access;
- representation-specific API.

```text
layout                   что логически существует
representation-aspect    как это физически реализовано
```

Representation не является отдельным языковым механизмом. Это aspect,
удовлетворяющий compiler-known contract `Representation<T>`.

## 2. Target является generic-параметром

У aspect нет неявной переменной `target`. Целевой тип — обычный
generic-параметр:

```efen
aspect UserDatabaseInMemory<Target>
    conforms Representation<Target>
{
    // Target известен всему aspect.
}
```

Тип сам предусматривает representation в своих generics:

```efen
layout Database {
    generic Physical<T>: Representation<T> = UserDatabaseInMemory

    use Physical<Self>

    // logical definition
}
```

При инстанциации:

```efen
Database<UserDatabaseInMemory>
```

обычные generic rules строят:

```text
UserDatabaseInMemory<Database<UserDatabaseInMemory>>
```

Это не рекурсивное требование готового типа. Nominal identity
`Database<UserDatabaseInMemory>` уже известна, но `Target` предоставляет aspect
immutable logical C0 и текущий provisional definition до materialization самой
representation. `implementation Target` дополняет тот же definition plan; fully
realized `Target` публикуется только после завершения aspect stages.

Внешний код не может применить новую representation к типу, который сам не
объявил такой generic-параметр.

## 3. Required-описание

Representation-aspect обязан явно описать, к каким targets он применим.

RAM representation этого примера требует logical set `Users`:

```efen
aspect UserDatabaseInMemory<Target>
    conforms Representation<Target>
{
    required Target {
        set Users: let Item
    }
}
```

Конкретная файловая representation требует определённую logical shape:

```efen
aspect UserDatabaseFileV1<Target>
    conforms Representation<Target>
{
    required Target {
        set Users: let Item

        required Item {
            let id: UInt64
            var balance: Int64
            var name: FixedString<48>
        }
    }
}
```

`Item` связывается с типом из `set Users: Item`. Aspect не ищет магическое
вложенное имя `User`. В implementation используется `Target.Users.Item`.

Если required shape не выполнена, ошибка возникает при generic-instantiation до
изменения definition plan.

## 4. Общий блок implementation

`implementation` может использовать любой aspect. Блок всегда явно называет
абстракцию, которой добавляет declarations.

```efen
aspect Logging<T> {
    implementation T {
        fn logState() {
            // По умолчанию private.
        }
    }
}
```

В representation корневой блок реализует exact realized type:

```efen
implementation Target {
    source file: own File

    @constructor
    public fn init(file: own File) -> Self {
        self.file = take file
        return self
    }

    public fn flush() {
        // ...
    }
}
```

Здесь `Self` равен `Target`. Constructor принадлежит exact realized type, а не
aspect.

Logical set также может быть получателем общего implementation:

```efen
implementation Target.Users {
    type Witness = UserPlacement
    capabilities import, create, remove, read, write

    reserve = owner.reserveUser
    acquire = owner.acquireUser
    retire = owner.retireUser
}
```

Во втором блоке:

```text
Self          = Target.Users
Self.Item     = Target.Users.Item
Self.Pointer  = Target.Users.Pointer
owner         = runtime instance Target
```

Каждый implementation `set` выбирает associated `Witness`. Core хранит один
opaque witness возле каждой live identity и передаёт его handlers. Witness может
содержать owning RAM grant, file coordinate, несколько column coordinates или
другой mapping; witness не обязан быть allocation.

«Возле каждой identity» является логическим контрактом, а не обязательной
runtime record. Для `Buckets.Range` один owning range grant и ordinal identity
могут формулой вывести witness каждого bucket без per-bucket directory.

`capabilities` объявляет поддержанные logical operations. Если logical method
требует отсутствующую capability, representation-instantiation незаконна.
Read/update-only file может поддерживать `import, read, write` без
`create/remove`.

Отдельных синтаксических форм implementation для type и `set` не нужно.

## 5. Sources и смешанное placement

`source` является physical member implementation с явным ownership mode:

```efen
source file: own File
source ram: own Ram
source system: read write VirtualMemory
```

Source задаёт границу происхождения physical grants. Он не означает, что один
logical type всегда живёт в одном source.

Один implementation может:

- получить block из `VirtualMemory`;
- отделить header;
- разбить payload на slots;
- часть values отправить в arena;
- большие values разместить отдельными runs;
- out-of-line bodies хранить в другом source;
- при pressure изменить routing новых allocations.

Placement является runtime-алгоритмом implementation, а не таблицей
`type → allocator`.

## 6. Identity, create и remove

Core `set` владеет logical identities и `Live`. Для каждой identity core хранит
opaque associated `Witness` выбранного implementation. Representation не может
самостоятельно опубликовать или уничтожить membership.

`Users.create(...)` выполняется так:

```text
core выбирает logical constructor
→ резервирует fresh identity вне Live
→ implementation резервирует physical grants
→ constructor инициализирует logical value
→ проверяются predicates
→ core публикует identity, Live и Witness одним no-throw commit
→ возвращается Users.Pointer
```

Failure до commit уничтожает только инициализированные части и возвращает все
reservations. Member не появляется.

Если constructor realized type падает после принятия sources, компилятор
уничтожает уже инициализированные implementation members в обратном порядке.
Принятый owning source не теряется; неинициализированные fields не трогаются.

Удаление выполняется в обратном порядке:

```text
core проверяет authority и borrows
→ исключает identity из Live
→ выполняет logical lifecycle
→ выдаёт implementation retirement token
→ implementation возвращает либо откладывает physical grants
```

Локальный `Users.Pointer` сам не владеет lifetime persistent member. Drop pointer
не удаляет запись. `own` на pointer выражает authority, а удаление остаётся явной
операцией `set`.

## 7. Граница власти representation

Representation реализует только объявленные memory seams. Она не переписывает
произвольные logical method bodies.

Иначе aspect мог бы заменить:

```efen
balance += amount
```

на:

```efen
balance += amount * 2
```

и обычная проверка HIR не доказала бы semantic equivalence.

Logical algorithms сохраняются. Representation получает право реализовать:

- reserve/commit/retire physical storage;
- logical pointer access;
- logical field projection;
- whole-value gather/scatter;
- iteration/traversal plan;
- lifecycle lowering;
- private physical state.

`Representation<T>` также явно разрешает aspect добавлять realized type
representation-specific public API: `flush`, `prefetch`, `compact` и другие
methods. Collisions и ordering проходят обычный aspect definition plan.

## 8. Стадии compilation

Representation использует существующий aspect plan:

```text
generic substitution и immutable logical definition
→ non-mutating registration aspect applications
→ фиксация implementation recipients и ordering
→ materialization physical members и public surface
→ binding memory/access/traversal handlers
→ compilation logical bodies
→ effects, throws, suspension, ownership и predicates
→ publication realized type
```

Поздняя замена handler после анализа зависимого body запрещена.

`implementation` blocks декларативно регистрируются в plan. Для динамической
генерации aspect использует обычную metafunction:

```efen
meta fn register(plan: lang::DefinitionPlan) {
    // Target уже является generic-параметром aspect.
}
```

## 9. Логическая база данных

```efen
layout Database {
    generic Physical<T>: Representation<T> = UserDatabaseInMemory

    use Physical<Self>

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

Logical `Database` не содержит File, Ram, pages или cache.

Минимальный файловый пример read/update-only: membership `Users` фиксируется при
construction/import. Append/remove требуют persistent directory,
tombstones/generations и recovery protocol и не маскируются заглушками.

## 10. InMemory representation базы

```efen
aspect UserDatabaseInMemory<Target>
    conforms Representation<Target>
{
    required Target {
        set Users: let Item
    }

    implementation Target {
        source ram: own Ram

        @constructor
        public fn init(
            ram: own Ram,
            initial: [Target.Users.Item]
        ) -> Self {
            self.ram = take ram

            // Core import создаёт Live и сохраняет opaque RamWitness
            // каждой identity через set implementation.
            self.Users.import(take initial)
            return self
        }

        fn reserveValue(request: PlacementRequest)
            -> PhysicalReservation<RamWitness>
        {
            let place = self.ram.reserve(
                bytes: request.size,
                alignment: request.alignment
            )

            return PhysicalReservation(
                witness: RamWitness(place: place),
                rollback: () => self.ram.release(place)
            )
        }

        fn accessValue(
            pointer: read Target.Users.Pointer,
            witness: read RamWitness
        ) -> AccessLease<Target.Users.Item> {
            return AccessLease(
                logical: pointer,
                physical: witness.place
            )
        }

        fn retireValue(retirement: own RetirementToken<RamWitness>) {
            self.ram.release(take retirement.witness.place)
        }
    }

    implementation Target.Users {
        type Witness = RamWitness
        capabilities import, read, write

        reserve = owner.reserveValue
        acquire = owner.accessValue
        retire = owner.retireValue
    }
}
```

Это concrete пример для `Database.Users`. Полностью generic `InMemory` может
metafunction-ой создать такой implementation для каждого `set` из
`Target.sets`, используя `set.Item` и не зная имён `Users` или `User`.

Logical identity не равна RAM address. Core хранит для неё opaque
`PhysicalGrant`, передаёт его access/retire handlers и invalidates identity до
physical reuse.

## 11. Файловая representation с двумя frames

Минимальный формат:

```text
encoded User:       64 bytes
page:             4096 bytes
users per page:     64
resident pages:      2
```

Одна запись не пересекает page boundary. `UserFileV1` задаёт encoding и offsets
полей, а не использует native ABI `User`.

```efen
aspect UserDatabaseFileV1<Target>
    conforms Representation<Target>
{
    required Target {
        set Users: let Item

        required Item {
            let id: UInt64
            var balance: Int64
            var name: FixedString<48>
        }
    }

    implementation Target {
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
            let slot: UInt {
                slot < 2
            }

            var page: Page? {
                (page == null) ==
                    (state == Empty || state == Loading)
            }

            var state: FrameState {
                (state == Clean || state == Dirty || state == Flushing) ==
                    (page != null)
            }
            var version: Version
            var lastUse: UInt64

            var pins: UInt {
                get { return liveLoans(to: self).count }
            }
        }

        let format: UserFileV1 = UserFileV1()
        let cacheGrant: own PhysicalGrant

        var frames: [Frame] {
            .count == 2 && unique(
                .filter((frame) => frame.page != null)
                    .map((frame) => frame.page)
            )
        }

        var clock: UInt64 = 0
        var uncertainPages: Set<Page> = Set<Page>()

        @constructor
        public fn init(file: own File, ram: own Ram) -> Self {
            self.file = take file
            self.ram = take ram

            self.cacheGrant = self.ram.reserve(
                bytes: 8192,
                alignment: 4096
            )

            // Frame хранит только metadata. cacheGrant остаётся единственным
            // owner bytes; slot выбирает непересекающуюся page projection.
            self.frames = [
                Frame(
                    slot: 0,
                    page: null,
                    state: Empty,
                    version: Version.initial,
                    lastUse: 0
                ),
                Frame(
                    slot: 1,
                    page: null,
                    state: Empty,
                    version: Version.initial,
                    lastUse: 0
                )
            ]

            self.format.validateHeader(self.file)
            self.format.validateAll(
                self.file,
                through: self.frames
            )

            // Core публикует проверенные identities.
            self.Users.import(
                count: self.file.header.userCount,
                witness: (identity) =>
                    self.format.location(identity)
            )

            return self
        }

        fn frameBytes(frame: read Frame)
            -> read write PageBytes<4096>
        {
            return self.cacheGrant.project<PageBytes<4096>>(
                offset: frame.slot * 4096
            )
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

            frame.state = Flushing

            try {
                // Пишем прямо из pinned frame: скрытой третьей page copy нет.
                self.file.writePage(
                    page: frame.page,
                    from: frameBytes(frame)
                )
                self.file.sync(frame.page)
                self.uncertainPages.remove(frame.page)
                frame.state = Clean
            } catch error: IOError {
                // RAM остаётся logical authority. File page могла стать torn.
                self.uncertainPages.add(frame.page)
                frame.state = Dirty
                throw error
            }
        }

        fn load(page: Page, into frame: read write Frame)
            throws IOError | InvalidFile
        {
            if frame.state == Dirty {
                flushFrame(frame)
            }

            frame.commitState(page: null, state: Loading)

            try {
                // Чтение идёт прямо в заранее выделенный frame.
                self.file.readPage(page: page, into: frameBytes(frame))
                self.format.validatePage(page, frameBytes(frame))

                frame.commitState(
                    page: page,
                    state: Clean,
                    version: self.file.version(page)
                )
            } catch error: IOError | InvalidFile {
                frame.commitState(page: null, state: Empty)
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

        fn acquireUser(
            pointer: read Target.Users.Pointer,
            location: read FileLocation
        ) -> RecordLease state Open
            throws IOError | InvalidFile | CacheBusy
        {
            let frame = acquireFrame(location.page)

            return RecordLease(
                logical: pointer,
                pin: frame,
                offset: location.offset
            )
        }

        fn readUserField<Field>(
            lease: read RecordLease,
            field: Field
        ) -> field.Type {
            return self.format.decodeField(
                frameBytes(lease.pin),
                lease.offset,
                field
            )
        }

        fn gatherUser(lease: read RecordLease)
            -> Target.Users.Item
        {
            return self.format.decodeRecord(
                frameBytes(lease.pin),
                lease.offset
            )
        }

        fn borrowReadUserField<Field>(
            lease: read RecordLease,
            field: Field
        ) -> ReadFieldLease<field.Type> {
            // Совместимое поле заимствуется прямо; иначе lease владеет
            // materialized scratch value до конца read borrow.
            return self.format.borrowReadOrMaterialize(
                frameBytes(lease.pin),
                lease.offset,
                field,
                pin: lease.pin
            )
        }

        fn borrowWriteUserField<Field>(
            lease: read write RecordLease,
            field: Field
        ) -> WriteFieldLease<field.Type> {
            if !self.format.directWritable(field) {
                compileError(
                    "encoded field ${field} has no direct write borrow"
                )
            }

            return self.format.borrowWriteDirect(
                frameBytes(lease.pin),
                lease.offset,
                field,
                pin: lease.pin
            )
        }

        fn prepareUserWrite<Field>(
            lease: read RecordLease,
            field: Field,
            value: field.Type
        ) -> PreparedFieldWrite {
            return self.format.prepareWrite(
                bytes: frameBytes(lease.pin),
                offset: lease.offset,
                field: field,
                value: value
            )
        }

        fn commitUserWrite(
            lease: read write RecordLease,
            prepared: own PreparedFieldWrite
        ) {
            lease.pin.commitWrite(
                offset: lease.offset,
                encoding: take prepared,
                version: lease.pin.version.next(),
                state: Dirty
            )
        }

        fn releaseUserAccess(
            lease: own RecordLease
        ) {
            // Drop lease завершает borrow и снимает pin.
        }

        public fn prefetch(pointer: read Target.Users.Pointer)
            throws IOError | InvalidFile | CacheBusy
        {
            acquireFrame(
                self.format.location(pointer.identity).page
            )
        }

        public fn flush() state Open throws IOError {
            // Изменение frames выводит exclusive borrow cache state.
            // Живой RecordLease делает этот вызов недопустимым типово.
            for frame in self.frames {
                flushFrame(frame)
            }
        }

        public fn close() state Open >> Closed throws IOError {
            flush()
            self.file.close()
        }
    }

    implementation Target.Users {
        type Witness = FileLocation
        capabilities import, read, write

        acquire = owner.acquireUser
        readField = owner.readUserField
        gather = owner.gatherUser
        borrowReadField = owner.borrowReadUserField
        borrowWriteField = owner.borrowWriteUserField
        prepareWrite = owner.prepareUserWrite
        commitWrite = owner.commitUserWrite
        release = owner.releaseUserAccess
    }
}
```

Минимальная representation не shared. Exclusive borrow cache state живёт через
suspension, поэтому две загрузки одной page не interleave. Concurrent-вариант
обязан добавить directory и coherence protocol.

`state Open` и `state Open >> Closed` в signatures являются кандидатами
typestate-написания. Требуемая семантика: после успешного `close` access и
повторный `close` недоступны; при исключении instance остаётся `Open` с dirty
authority в RAM.

Пользовательский код:

```efen
alias FileDatabase = Database<UserDatabaseFileV1>

var database = FileDatabase(
    file: File.open("users.db", access: readWrite),
    ram: Ram(size: 8192)
)

let user = database.findUser(42)!

echo user.name       // Может загрузить page и приостановить функцию.
user.name = "Alice" // RAM frame становится Dirty authority.

database.flush()
database.close()
```

Effects, exceptions и suspension наследуются автоматически. Если внешний
contract явно закрыт и несовместим с handlers, компилятор выдаёт ошибку.

## 12. Columnar representation массива

```efen
struct X {
    var a: Int
    var b: Float
}

struct Array {
    generic Element: Type
    generic Physical<T>: Representation<T> = Contiguous

    use Physical<Self>

    fn append(value: own Element)
    fn reserve(capacity: Size)
    fn get(index: Index) -> Element where Element: Copyable
    fn take(index: Index) -> Element
}
```

`get` является runtime-функцией и возвращает copied materialized `Element`,
поэтому доступен только для `Copyable`. `take` перемещает whole value. Ни один из
них не возвращает proxy с addresses или indices.

```efen
aspect Columnar<Target>
    conforms Representation<Target>
{
    required Target {
        generic Element: Type
        fn append(value: own Element)
        fn reserve(capacity: Size)
        fn get(index: Index) -> Element where Element: Copyable
        fn take(index: Index) -> Element
    }

    meta fn register(plan: lang::DefinitionPlan) {
        if !supportsColumnProjection(Target.Element) {
            compileError("Columnar cannot represent ${Target.Element}")
        }

        let implementation = plan.implementation(Target)

        for field in Target.Element.fields {
            implementation.addField(
                name: "column_${field.name}",
                type: Array<field.Type, Contiguous>
            )
        }

        plan.bind(
            Target.elementAccess,
            acquire: Target.accessElement,
            projectField: Target.projectElementField,
            release: Target.releaseElement
        )
    }

    implementation Target {
        @constructor
        public fn init(capacity: Size = 0) -> Self {
            for field in Target.Element.fields {
                self.column(field) = Array<field.Type, Contiguous>(
                    capacity: capacity
                )
            }

            return self
        }

        fn reserve(capacity: Size) {
            var prepared = PreparedColumns()

            for field in Target.Element.fields {
                prepared.add(
                    self.column(field).prepareReserve(capacity)
                )
            }

            self.commitReserve(take prepared)
        }

        fn append(value: own Target.Element) {
            // PreparedColumns владеет input и всеми уже извлечёнными fields.
            // Drop выполняет no-throw rollback ровно один раз.
            var prepared = PreparedColumns(input: take value)

            for field in Target.Element.fields {
                prepared.prepareField(
                    field,
                    into: self.column(field)
                )
            }

            // Commit всех columns и общего count не бросает.
            self.commitAppend(take prepared)
        }

        fn get(index: Target.Index) -> Target.Element
            where Target.Element: Copyable
        {
            return Target.Element(
                for field in Target.Element.fields {
                    field: self.column(field)[index].copy()
                }
            )
        }

        fn take(index: Target.Index) -> Target.Element {
            var prepared = PreparedColumns.take(
                from: self,
                index: index
            )
            return PreparedColumns.commitTake(take prepared)
        }

        fn accessElement(index: Target.Index) -> ElementLease {
            return ElementLease(
                owner: self,
                index: index
            )
        }

        fn projectElementField<Field>(
            lease: read ElementLease,
            field: Field
        ) -> FieldPlace<field.Type> {
            return self.column(field).place(lease.index)
        }

        fn releaseElement(lease: own ElementLease) {
            // Завершает logical borrow всех затронутых columns.
        }
    }

}
```

Применение:

```efen
alias XRows = Array<X, Contiguous>
alias XColumns = Array<X, Columnar>

var values = XColumns()

values.append(X(a: 1, b: 2.0))
values.append(X(a: 3, b: 4.0))

values[1].a = 10
echo values[0].b
```

Physical state:

```text
column_a = [1, 10]
column_b = [2.0, 4.0]
```

Логические операции:

```efen
let x: X = values.get(0)      // Собирает materialized X.
let slice = values[10..<20]   // Borrowed logical view, без массива pointers.
slice[2].a                    // Читает column_a[12].
```

`values[index].field` использует compile-time element-access handler и сразу
обращается к нужной column. `get(index)` отдельно собирает value.

Whole-element borrow является logical reference, а не fabricated contiguous
`&X`. Representation может реализовать его как `(array, index)` с field
handlers. Операция, требующая native-contiguous address целого `X`, для
Columnar недоступна.

Точный reference type сохраняет origin и access witness массива. При вызове:

```efen
fn mutate(value: &X) {
    value.a += 1
    value.b += 1
}

mutate(&values[0])
```

компилятор специализирует доступы `value.a`/`value.b` по representation ссылки
из `values`. Erased callable, ABI которого требует native `Address + Stable`, не
может принять такой composite borrow. Это проверяется при binding callable, а не
созданием временного contiguous `X` с неявным writeback.

## 13. Representation-directed flow

`flow {}` задаёт логический dataflow, в котором source order сам по себе не
обязан быть execution order.

Этот раздел является отдельным исследовательским расширением уже существующего
`flow`, а не доказанной частью representation contract. Он проверяет, какой
compiler seam потребуется для representation-directed traversal.

```efen
flow {
    let positive <- values.y > 0
    let nextX <- values.x + 1

    values.x <- nextX if positive
    let total <- sum(nextX)

    return total
}
```

Компилятор строит dependency graph:

```text
read y → positive ─┐
                   ├→ conditional write x
read x → nextX ────┤
                   └→ aggregation
```

Representation получает `TraversalRequest`:

```text
source
read/write/consume mode
field projections
dependency edges
logical order requirements
early exit
aliasing
effects и suspension
aggregation operation
```

И может предложить:

- scalar traversal;
- direct column traversal;
- fused field operations;
- SIMD masked update;
- parallel reduction;
- page streaming;
- aggregation compressed runs без полного decode.

Например наивный код:

```efen
var total = 0

for value in values {
    total += value.a
}
```

для `Columnar` понижается в прямой scan `column_a`, а для `BufferedFile` — в
последовательное чтение pages через ограниченный buffer.

Операции можно переставлять только согласно flow laws:

- data dependency задаёт обязательный порядок;
- conflicting writes без dependency являются ошибкой;
- external effects сохраняют порядок, если contract не разрешает иное;
- aggregation перегруппируется только при подходящих algebraic laws;
- `Float` и trapping overflow не reassociate без явного разрешения;
- при недоказанной оптимизации сохраняется обычный logical traversal.

Representation не переписывает произвольный код: compiler сначала распознаёт
standard traversal/reduction seam, а aspect выбирает его physical plan.

## 14. Limelight memory manager

Фактическая модель `/home/edmond/limelight/model`:

```text
VirtualMemory
    2 MiB regions
        BlockPool: 64 KiB blocks
            header:   256 bytes
            payload: 65 280 bytes

Entity routing:
    counted <= 8192 bytes       → size-class slot
    counted <= 65 280 bytes     → один pooled block
    counted larger              → OS-direct aligned run
    request small               → arena bump
    request large               → logged direct run

Out-of-line body routing:
    request                     → request arena
    counted/long-lived          → buffer arena
    large                       → direct run
```

Один type не соответствует одному source. Один entity может иметь inline header
в entity slot и out-of-line body в buffer arena. Один 64 KiB block в разное
время становится free, heap, entity, arena, buffer или retained block.

Logical owner должен быть долгоживущим runtime layout. Thread heaps и request
arenas — его physical components. Тогда promotion и thread adoption не меняют
logical pointer identity.

```efen
layout RuntimeMemory {
    generic Physical<T>: Representation<T> = LimelightNative

    use Physical<Self>

    set Entities: Entity

    // Logical lifetime, reset, escape и collection algorithms.
}
```

```efen
aspect LimelightNative<Target>
    conforms Representation<Target>
{
    required Target {
        set Entities: let EntityType
    }

    implementation Target {
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
                    return self.reserveImmortalEntity(request)
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

        fn accessEntity(
            pointer: read Target.Entities.Pointer,
            grant: read EntityGrant
        ) -> AccessLease<Target.Entities.Item> {
            let block = grant.place.mask(alignment: 65536)
            return block.kind.access(pointer, grant)
        }

        fn retireEntity(retirement: EntityRetirement) {
            // Logical death уже завершена core. Physical reuse может ждать
            // remote-free owner, trace window или retained-block holds.
            let grant = retirement.grant

            if grant.kind == EntityLargeRun {
                self.runs.retireCurrent(grant)
                return
            }

            let block = grant.place.mask(alignment: 65536)
            let kind = block.loadCurrentKind()
            let owner = block.loadCurrentOwner()
            owner.retireOrPostRemote(kind, grant)
        }

        fn growBody(request: BodyGrowthRequest) -> BodyReservation {
            return request.currentOwner.growThrough(
                request,
                pool: self.pool,
                backing: self.system
            )
        }

        fn retireBody(retirement: BodyRetirement) {
            // Category определяет domain; current block kind/owner — точный
            // механизм возврата внутри этого domain.
            retirement.category.retireThroughCurrentOwner(retirement)
        }

        fn scanCountedEntityGrants() -> Iterator<PhysicalGrant> {
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

    implementation Target.Entities {
        type Witness = EntityGrant
        capabilities create, remove, read, write, physicalCensus

        reserve = owner.reserveEntity
        access = owner.accessEntity
        retire = owner.retireEntity
        reserveBody = owner.reserveBody
        growBody = owner.growBody
        retireBody = owner.retireBody
        physicalCensus = owner.scanCountedEntityGrants
    }
}
```

Body operations являются physical seams representation `Entities`, а не
отдельным logical `set`. Representation конкретного entity type вызывает их для
out-of-line payload; body остаётся частью одного entity lifecycle.

Core перечисляет logical `Live`. `scanCountedEntityGrants` — отдельный physical
census collector-а: entity size-class blocks, pooled large entities, retained
inventories и OS-direct entity runs. Active request-arena entities не становятся
counted heap rows.

### Разбиение одного block

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

Компилятор проверяет bounds, alignment, непересечение частей и полный перенос
ownership исходного block. Intrusive free-list может использовать bytes
свободного slot: в Limelight link лежит в `8..16`, а `0..8` сохраняет финальный
нулевой refcount/flags, читаемый collector-ом.

### Promotion и adoption

```text
arena survivor promotion:
    та же logical identity
    адрес может сохраниться
    новая lifetime category и reclamation state

thread exit adoption:
    те же logical entities и physical blocks
    новый owner allocator-private state
```

Representation не меняет `Live` самостоятельно. Logical algorithms
`RuntimeMemory` решают survival, escape, reset и destruction; aspect реализует
physical transition.

## 15. Robin Hood HashMap и адресная арифметика

Этот пример использует open addressing, Robin Hood insertion и backward-shift
deletion. Он отделяет logical position от physical address.

### Логическая структура

```efen
layout HashMap {
    generic Key: Type
    generic Value: Type
    generic Physical<T>: Representation<T> = ContiguousHash

    where Key: Hashable
    where Key: Equatable<Key>
    where Key: Movable
    where Value: Movable

    use Physical<Self>

    set Entries: Entry
    set Buckets: Bucket

    struct Entry {
        let key: Key
        var value: Value

        @constructor
        fn init(key: own Key, value: own Value) -> Self {
            self.key = take key
            self.value = take value
            return self
        }
    }

    struct Bucket {
        var hash: UInt64 = 0
        var entry: Entries.Pointer? = null
    }

    var buckets: Buckets.Range {
        buckets.count >= 8 &&
        buckets.count.isPowerOfTwo() &&
        Entries.count <= buckets.count - buckets.count / 8 &&
        validRobinHoodIndex(buckets, Entries)
    }
}
```

Все функции следующих подразделов являются members того же `layout HashMap`;
они вынесены в отдельные code blocks только для последовательного объяснения.

`set Buckets` сам по себе не упорядочен. `Buckets.Range` является отдельным
logical positional contract конкретного диапазона корзин:

```text
range.count
range.Index
range.indices
range.wrap(integer)
range.nextWrapped(index)
range.distance(from, to)
range[start..<end]
range.ringSlice(start, length)
```

`Range.Index` несёт origin и bounds своего диапазона. Он не является byte offset
или pointer. `ringSlice` может состоять из двух обычных slices и не создаёт
массив pointers.

Для capacity, равной степени двойки:

```text
wrap(hash)       = hash & (capacity - 1)
nextWrapped(i)   = (i + 1) & (capacity - 1)
distance(a, b)   = (b - a) modulo capacity
```

Это арифметика логических номеров. Она не знает размер `Bucket`, base address или
physical contiguous storage.

### Инварианты

- capacity является степенью двойки и не меньше 8;
- `Entries.count <= capacity - capacity / 8`;
- каждый live `Entry` указан ровно одной занятой корзиной;
- каждая занятая корзина указывает на live `Entry` этого map;
- эквивалентных keys не больше одного;
- cached hash соответствует key и не меняется, пока entry находится в map;
- поиск от home position достигает entry до условия ранней остановки.

Stored key нельзя изменить через внешнюю mutable alias так, чтобы изменились его
hash или equality semantics.

### Поиск

```efen
fn locate(
    key: read Key,
    hash: UInt64
) -> buckets.Index? {
    var index = buckets.wrap(hash)
    var distance: Size = 0

    for step in 0..<buckets.count {
        let resident = buckets[index]

        if resident.entry == null {
            return null
        }

        let residentDistance = buckets.distance(
            from: buckets.wrap(resident.hash),
            to: index
        )

        if residentDistance < distance {
            return null
        }

        if resident.hash == hash &&
           resident.entry!.key.equals(key) {
            return index
        }

        index = buckets.nextWrapped(index)
        distance += 1
    }

    unreachable
}

public fn find(key: read Key) -> Entries.Pointer? {
    let hash = key.hash()
    let index = locate(key, hash)

    if index == null {
        return null
    }

    return buckets[index].entry
}
```

Физический access происходит только в:

```efen
buckets[index]
resident.entry!.key
```

Первое выражение вызывает positional/access handlers `Buckets.Range`, второе —
handlers `Entries`. `nextWrapped` не двигает physical pointer.

### PreparedWrite

Robin Hood insertion может изменить несколько корзин. Если каждое присваивание
само способно allocate, suspend или throw, partial displacement разрушит map.

```text
slice.prepareWrite()
    выполняет все fallible work;
    получает witnesses, pins и authority всего диапазона;
    возвращает PreparedWrite.

PreparedWrite
    меняет только заранее подготовленные indices;
    read/write/swap не allocate, не suspend и не throw;
    release не вызывает user code.
```

Поиск диапазона до первой пустой корзины:

```efen
fn insertionSpan<R>(
    table: read R,
    hash: UInt64
) -> table.Slice
    where R: IndexedRange<Bucket>
{
    let start = table.wrap(hash)
    var index = start
    var length: Size = 0

    for step in 0..<table.count {
        length += 1

        if table[index].entry == null {
            return table.ringSlice(start, length)
        }

        index = table.nextWrapped(index)
    }

    unreachable
}
```

`IndexedRange<Bucket>` является общим contract опубликованного `Range` и
закрытого construction view `DraftRange`.

Подготовленный Robin Hood placement:

```efen
fn placeReady(
    write: read write PreparedWrite<Bucket>,
    hash: UInt64,
    entry: Entries.Pointer
) {
    var incoming = Bucket(hash: hash, entry: entry)
    var distance: Size = 0

    for index in write.sourceIndices {
        let resident = write[index]

        if resident.entry == null {
            write[index] = incoming
            return
        }

        let residentDistance = write.origin.distance(
            from: write.origin.wrap(resident.hash),
            to: index
        )

        if residentDistance < distance {
            write[index] = incoming
            incoming = resident
            distance = residentDistance
        }

        distance += 1
    }

    unreachable
}
```

### Insert

`Entries.prepareCreate` готовит logical value и physical reservations, но ещё не
публикует identity. `commitCreate` выполняет core no-throw publication.

```efen
fn insertWithoutGrowth(
    key: own Key,
    value: own Value,
    hash: UInt64
) -> Entries.Pointer {
    let prepared = Entries.prepareCreate(
        key: take key,
        value: take value
    )

    let span = insertionSpan(buckets, hash)
    let write = span.prepareWrite()

    var pointer: Entries.Pointer

    region suspend buckets {
        pointer = Entries.commitCreate(take prepared)
        placeReady(write, hash, pointer)
    }

    return pointer
}
```

Invariant window содержит только заранее подготовленные no-throw operations и
не допускает suspension или user callbacks.

Обычный scope exit освобождает `PreparedWrite`. Явный `write.finish()` нужен
только перед публикацией нового range, когда draft остаётся в той же лексической
области, но его construction borrow уже должен закончиться.

Публичный insert сначала выполняет hash/equality, пока map согласован:

```efen
public fn insert(
    key: own Key,
    value: own Value
) -> InsertResult<Entries.Pointer, Key, Value> {
    let hash = key.hash()
    let existing = locate(key, hash)

    if existing != null {
        return Existing(
            pointer: buckets[existing].entry!,
            key: take key,
            value: take value
        )
    }

    let nextCount = checkedAdd(Entries.count, 1)
    let limit = buckets.count - buckets.count / 8

    let pointer = if nextCount <= limit {
        insertWithoutGrowth(take key, take value, hash)
    } else {
        insertWithGrowth(take key, take value, hash)
    }

    return Inserted(pointer)
}
```

Existing возвращает переданные owning values вызывающему коду. Неожиданного
destruction rejected key/value внутри map нет.

### Resize

Новый bucket range строится закрыто. Rehash использует cached hashes и не
трогает `Key`/`Value`:

```efen
fn buildIndex(capacity: Size) -> Buckets.DraftRange {
    let draft = Buckets.prepareRange(
        count: capacity,
        initial: Bucket()
    )

    for oldIndex in buckets.indices {
        let old = buckets[oldIndex]

        if old.entry != null {
            let span = insertionSpan(draft, old.hash)
            let write = span.prepareWrite()
            placeReady(write, old.hash, old.entry!)
        }
    }

    return draft
}

public fn resize(capacity: Size) {
    require capacity >= 8
    require capacity.isPowerOfTwo()
    require Entries.count <= capacity - capacity / 8

    let draft = buildIndex(capacity)
    let retirement = Buckets.prepareRetireRange(buckets)

    region suspend buckets {
        let next = Buckets.commitRange(take draft)
        buckets = take next
        Buckets.commitRetireRange(take retirement)
    }
}
```

Если build падает, старый range не меняется. Bucket indices старого range после
publication нового теряют применимость; identities `Entries` сохраняются.

Insert с growth готовит draft, entry и все writes до одного commit window:

```efen
fn insertWithGrowth(
    key: own Key,
    value: own Value,
    hash: UInt64
) -> Entries.Pointer {
    let capacity = checkedDouble(buckets.count)
    let draft = buildIndex(capacity)

    let prepared = Entries.prepareCreate(
        key: take key,
        value: take value
    )

    let span = insertionSpan(draft, hash)
    let write = span.prepareWrite()
    let retirement = Buckets.prepareRetireRange(buckets)

    var pointer: Entries.Pointer

    region suspend buckets {
        pointer = Entries.commitCreate(take prepared)
        placeReady(write, hash, pointer)
        write.finish()

        let next = Buckets.commitRange(take draft)
        buckets = take next
        Buckets.commitRetireRange(take retirement)
    }

    return pointer
}
```

### Remove без tombstones

Backward-shift deletion закрывает hole, пока следующая корзина не пуста и её
entry не находится на home position.

```efen
fn deletionSpan(start: buckets.Index) -> buckets.Slice {
    var length: Size = 1
    var index = buckets.nextWrapped(start)

    for step in 1..<buckets.count {
        let resident = buckets[index]

        if resident.entry == null {
            break
        }

        let distance = buckets.distance(
            from: buckets.wrap(resident.hash),
            to: index
        )

        if distance == 0 {
            break
        }

        length += 1
        index = buckets.nextWrapped(index)
    }

    return buckets.ringSlice(start, length)
}

fn closeHoleReady(write: read write PreparedWrite<Bucket>) {
    var hole = write.firstSourceIndex

    for index in write.sourceIndices.dropFirst() {
        write[hole] = write[index]
        hole = index
    }

    write[hole] = Bucket()
}

public fn remove(key: read Key) -> Entry? {
    let hash = key.hash()
    let index = locate(key, hash)

    if index == null {
        return null
    }

    let pointer = buckets[index].entry!
    let extraction = Entries.prepareTake(pointer)
    let write = deletionSpan(index).prepareWrite()

    var result: Entry

    region suspend buckets {
        closeHoleReady(write)
        result = Entries.commitTake(take extraction)
    }

    return result
}
```

`remove` возвращает owning `Entry`; user destructors не запускаются внутри
invariant window.

### Representations

Обе representations требуют одну logical shape:

```efen
required Target {
    generic Key: Type
    generic Value: Type
    set Entries: let Entry
    set Buckets: let Bucket
    var buckets: Buckets.Range
}
```

`ContiguousHash<Target>` размещает bucket range одним compact grant, а Entries —
в stable slots. `SegmentedHash<Target>` размещает buckets chunks по 256 и может
разнести key/value по columns. Logical HashMap code одинаков.

Contiguous positional handler:

```text
Bucket.Index
→ ordinal
→ checked element projection одного grant
```

Segmented handler:

```text
Bucket.Index
→ ordinal
→ chunk = ordinal / 256
→ offset = ordinal % 256
→ checked projection chunk grant
```

`Entries.Pointer` сначала проверяется core по identity/generation, затем witness
выбирает physical entry storage и field projection.

#### ContiguousHash

```efen
aspect ContiguousHash<Target>
    conforms Representation<Target>
{
    required Target {
        generic Key: Type
        generic Value: Type
        set Entries: let Entry
        set Buckets: let Bucket
        var buckets: Buckets.Range
    }

    implementation Target {
        source ram: own Ram

        let entries: StableSlots<Target.Entries.Item>

        @constructor
        public fn init(ram: own Ram, capacity: Size = 8) -> Self {
            require capacity >= 8
            require capacity.isPowerOfTwo()

            self.ram = take ram
            // StableSlots хранит metadata, а Ram получает коротким borrow
            // на каждой reserve/retire operation.
            self.entries = StableSlots()
            self.buckets = self.Buckets.createRange(
                count: capacity,
                initial: Target.Buckets.Item()
            )
            return self
        }

        fn reserveEntry(request: PlacementRequest)
            -> PhysicalReservation<StableEntryWitness>
        {
            return self.entries.reserve(
                request,
                source: self.ram
            )
        }

        fn acquireEntry(
            pointer: read Target.Entries.Pointer,
            witness: read StableEntryWitness
        ) -> AccessLease<Target.Entries.Item> {
            return self.entries.acquire(pointer, witness)
        }

        fn retireEntry(
            retirement: own RetirementToken<StableEntryWitness>
        ) {
            self.entries.retire(
                take retirement,
                source: self.ram
            )
        }

        fn prepareBucketRange(count: Size)
            -> RangeReservation<ContiguousBucketWitness>
        {
            let cells = self.ram.reserveElements<Target.Buckets.Item>(
                count: count
            )

            return RangeReservation(
                count: count,
                witness: ContiguousBucketWitness(cells: take cells)
            )
        }

        fn acquireBucket(
            position: read IndexedPosition<Target.Buckets.Item>,
            witness: read ContiguousBucketWitness
        ) -> AccessLease<Target.Buckets.Item> {
            return AccessLease(
                logical: position,
                physical: witness.cells.project(position.ordinal)
            )
        }

        fn prepareBucketWrite(
            slice: read IndexedSlice<Target.Buckets.Item>,
            witness: read write ContiguousBucketWitness
        ) -> PreparedWrite<Target.Buckets.Item> {
            return PreparedWrite(
                logical: slice,
                physical: witness.cells.prepareWrite(slice.ordinals)
            )
        }

        fn retireBucketRange(
            retirement: own RangeRetirement<ContiguousBucketWitness>
        ) {
            self.ram.release(take retirement.witness.cells)
        }
    }

    implementation Target.Entries {
        type Witness = StableEntryWitness
        capabilities create, remove, read, write,
                     prepareCreate, prepareTake

        reserve = owner.reserveEntry
        acquire = owner.acquireEntry
        retire = owner.retireEntry
    }

    implementation Target.Buckets {
        type Witness = ContiguousBucketWitness
        capabilities createRange, retireRange, read, preparedWrite

        prepareRange = owner.prepareBucketRange
        acquire = owner.acquireBucket
        prepareWrite = owner.prepareBucketWrite
        retireRange = owner.retireBucketRange
    }
}
```

Один `ContiguousBucketWitness` принадлежит целому range. Witness отдельного
bucket выводится как `(range witness, ordinal)` и не требует per-bucket map.

#### SegmentedHash

```efen
aspect SegmentedHash<Target>
    conforms Representation<Target>
{
    required Target {
        set Entries: let Entry
        set Buckets: let Bucket
        var buckets: Buckets.Range
    }

    implementation Target {
        source ram: own Ram

        let entries: StableSlots<Target.Entries.Item>

        @constructor
        public fn init(ram: own Ram, capacity: Size = 256) -> Self {
            require capacity >= 8
            require capacity.isPowerOfTwo()

            self.ram = take ram
            self.entries = StableSlots()
            self.buckets = self.Buckets.createRange(
                count: capacity,
                initial: Target.Buckets.Item()
            )
            return self
        }

        fn prepareBucketRange(count: Size)
            -> RangeReservation<SegmentedBucketWitness>
        {
            let chunkCount = ceilDiv(count, 256)
            var chunks = PreparedChunks<Target.Buckets.Item>()

            for chunk in 0..<chunkCount {
                let remaining = count - chunk * 256
                let length = min(remaining, 256)

                chunks.add(
                    self.ram.reserveElements<Target.Buckets.Item>(
                        count: length
                    )
                )
            }

            return RangeReservation(
                count: count,
                witness: SegmentedBucketWitness(
                    chunks: PreparedChunks.commit(take chunks)
                )
            )
        }

        fn acquireBucket(
            position: read IndexedPosition<Target.Buckets.Item>,
            witness: read SegmentedBucketWitness
        ) -> AccessLease<Target.Buckets.Item> {
            let chunk = position.ordinal / 256
            let offset = position.ordinal % 256

            return AccessLease(
                logical: position,
                physical: witness.chunks[chunk].project(offset)
            )
        }

        fn prepareBucketWrite(
            slice: read IndexedSlice<Target.Buckets.Item>,
            witness: read write SegmentedBucketWitness
        ) -> PreparedWrite<Target.Buckets.Item> {
            // ringSlice может затронуть несколько chunks. Подготовка получает
            // leases всех затронутых chunks до первого write.
            return PreparedWrite(
                logical: slice,
                physical: witness.chunks.prepareWrite(slice.ordinals)
            )
        }

        fn retireBucketRange(
            retirement: own RangeRetirement<SegmentedBucketWitness>
        ) {
            for chunk in take retirement.witness.chunks {
                self.ram.release(take chunk)
            }
        }

        fn reserveEntry(request: PlacementRequest)
            -> PhysicalReservation<StableEntryWitness>
        {
            return self.entries.reserve(
                request,
                source: self.ram
            )
        }

        fn acquireEntry(
            pointer: read Target.Entries.Pointer,
            witness: read StableEntryWitness
        ) -> AccessLease<Target.Entries.Item> {
            return self.entries.acquire(pointer, witness)
        }

        fn retireEntry(
            retirement: own RetirementToken<StableEntryWitness>
        ) {
            self.entries.retire(
                take retirement,
                source: self.ram
            )
        }
    }

    implementation Target.Entries {
        type Witness = StableEntryWitness
        capabilities create, remove, read, write,
                     prepareCreate, prepareTake

        reserve = owner.reserveEntry
        acquire = owner.acquireEntry
        retire = owner.retireEntry
    }

    implementation Target.Buckets {
        type Witness = SegmentedBucketWitness
        capabilities createRange, retireRange, read, preparedWrite

        prepareRange = owner.prepareBucketRange
        acquire = owner.acquireBucket
        prepareWrite = owner.prepareBucketWrite
        retireRange = owner.retireBucketRange
    }
}
```

Обе representations исполняют один Robin Hood code. Различается только
projection logical `Range.Index` в physical bucket place.

`IndexedPosition` и `IndexedSlice` являются core adapter requests для
опубликованного `Range` и закрытого `DraftRange`. Они несут logical origin,
полную capacity, circular source order и соответствующую live либо construction
authority. `PreparedWrite` сохраняет этот logical request рядом с подготовленным
physical view; одни `ordinals` не заменяют origin.

### Нужна ли адресная арифметика

Logical HashMap использует:

```text
hash arithmetic
origin-bound Range.Index
wrap / nextWrapped / distance
logical slices
Entries.Pointer
prepared logical writes
```

Byte pointer arithmetic ему не нужна.

Representation может пользоваться checked operations:

```efen
let cells = ram.reserveElements<Bucket>(count: count)
let place = cells.project(index)
```

или:

```efen
let chunks = grant.split(
    count: chunkCount,
    elementsPerChunk: 256,
    element: Bucket
)

let place = chunks[chunk].project(offset)
```

Компилятор проверяет bounds, multiplication, alignment и origin. Backend в итоге
вычисляет:

```text
base + ordinal * stride + fieldOffset
```

В этом HashMap raw byte arithmetic остаётся только внутри trusted native
source/backend. Она не нужна ни logical layout, ни показанным обычным
representation-aspects.

### Проверка алгоритма

Reference implementation перебрал 32 768 последовательностей из пяти hashes при
capacity 8. Для каждой последовательности проверялись insert, удаление каждого
key, grow `8 → 16`, shrink `16 → 8`, absent lookup и reachability invariant.
Отдельно проверялось вычисление distance из logical position и cached hash.

Это алгоритмическая проверка Robin Hood example. Она не доказывает compiler
protocols, ownership или crash recovery.

## 16. Transparent access и lifecycle

```text
получить logical access authority
→ получить representation lease
→ построить field либо whole-value projection
→ выполнить fallible prepare
→ проверить predicates
→ выполнить no-throw commit
→ освободить lease на каждом exit
```

`&pointer.field` удерживает lease и необходимые pins до конца borrow. Eviction,
relocation и reclamation не могут его нарушить.

Representation не удерживает exclusive borrow allocator state через вызов
пользовательского destructor, collector callback или другой reentrant code. Она
завершает structural mutation, отпускает borrow, вызывает user code, затем снова
получает state и перечитывает прежние предположения.

Порядок destruction:

```text
logical lifetimes
→ physical grants и holds
→ allocator/cache metadata
→ sources
```

Owning source уничтожается последним. Borrowed source только освобождает borrow.

## 17. Что уже следует из общих правил языка

- `Array<X>` означает exact default generic-instantiation.
- `Array<X, Columnar>` является другим concrete type.
- Общая функция явно параметризуется representation aspect-constructor.
- Aspect composition использует обычные fixed generic parameters и packs.
- Applicability задаётся `required`-описанием representation-aspect.
- Representation сама решает поддержку структуры, класса или layout.
- Opaque type имеет exact representation underlying type.
- Default visibility private; `private` в примерах не дублируется.
- Constructor записывается `@constructor fn init(...) -> Self`.
- Effects, exceptions и suspension выводятся автоматически.
- Mixed placement является runtime-алгоритмом implementation.

## 18. Кандидаты синтаксиса для утверждения

### S1. Generic aspect-constructor

```efen
generic Physical<T>: Representation<T> = UserDatabaseInMemory
use Physical<Self>
```

### S2. Required shape

```efen
required Target {
    set Users: let Item
    required Item { /* fields */ }
}
```

### S3. Общий implementation block

```efen
implementation Target {
    // fields, sources, constructors, methods
}
```

### S4. Implementation logical set

```efen
implementation Target.Users {
    type Witness = UserPlacement
    capabilities import, create, remove, read, write

    reserve = owner.reserveUser
    acquire = owner.acquireUser
    retire = owner.retireUser
}
```

### S5. Source member

```efen
source file: own File
source ram: own Ram
```

### S6. Constructor realized type

```efen
@constructor
public fn init(file: own File, ram: own Ram) -> Self
```

### S7. Transparent access

```efen
echo user.name
user.name = "Alice"
```

### S8. Traversal planning

```efen
meta fn planTraversal(
    request: TraversalRequest
) -> TraversalPlan
```

### S9. Упорядоченный диапазон logical set

```efen
var buckets: Buckets.Range
```

`Range` добавляет origin-bound `Index`, wrap/distance и slices, не превращая
произвольный `set` в упорядоченную память.

### S10. Подготовленная запись диапазона

```efen
let write = slice.prepareWrite()
```

После успешной подготовки операции `write[index]`, swap и finish не allocate,
не suspend, не throw и не вызывают user code.

## 19. Проверочные сценарии

1. `Database<UserDatabaseInMemory>` и `Database<UserDatabaseFileV1>` проходят
   одинаковые logical read/update tests.
2. Required shape отклоняет неподходящий target до plan mutation.
3. Handler нельзя заменить после анализа logical body.
4. Failed prepare не публикует identity.
5. Remove инвалидирует identity до physical reuse.
6. Cache hit не читает file повторно.
7. Cache miss читает прямо в выбранный frame.
8. Три pages через два frames корректно вытесняют victim.
9. Field borrow удерживает frame pinned.
10. Logical write виден до `flush()`.
11. Failed flush сохраняет RAM authority и отмечает неопределённость file image.
12. Columnar field access обращается прямо к соответствующей column.
13. Columnar `get` возвращает materialized value.
14. Slice не создаёт массив element pointers.
15. Whole-element borrow не выдаётся за native-contiguous address.
16. Failed column prepare уничтожает уже подготовленные fields ровно один раз.
17. `flow` сохраняет dependencies и использует representation traversal plan.
18. Limelight small entity идёт в size-class slot.
19. Limelight medium entity получает целый pooled block.
20. Limelight large entity получает OS-direct run.
21. Entity body использует отдельный routing и granted capacity.
22. Arena promotion сохраняет logical identity.
23. Thread adoption меняет physical authority без изменения `Live`.
24. Robin Hood insert сохраняет lookup invariant при collision displacement.
25. Backward-shift removal не разрывает дальнейший probe chain.
26. Failed grow оставляет прежний bucket range опубликованным.
27. Rehash сохраняет `Entries.Pointer` identities.
28. Contiguous и segmented hash representations проходят одинаковые logical
    tests.
29. Ни один logical hash method не использует byte address arithmetic.

## 20. Граница текущего документа

Имена `DefinitionPlan`, `PhysicalReservation`, `RetirementToken`, `AccessLease`,
`TraversalRequest`, `ElementLease` и методы вроде `commitState` являются
candidate library/compiler contracts. Они не выдаются за уже существующий API.

После утверждения синтаксиса новая модель должна синхронно заменить старые
описания в:

- `docs/efen/representations.md`;
- `docs/efen/generics.md`;
- `docs/efen/memory/addresses.md`;
- `docs/efen/memory/columnar-layouts.md`;
- `docs/efen/memory/layout-representations.md`;
- документах aspects и compile-time API;
- Amber `dev/DECISIONS.md`, `dev/PLAN.md`, HIR declarations/generics и
  compilation plan.
