# Layout и representation-aspect: файловая база данных

Статус: черновик для обсуждения. Семантические решения, уже принятые в
обсуждении, отделены от кандидатов синтаксиса. Синтаксис становится нормативным
только после последовательного утверждения Edmond.

## Задача

Сначала программист описывает базу данных как обычную логическую структуру
памяти. Она содержит пользователей, их identities, свойства, pointers,
предикаты и операции. Она ничего не знает о heap, файле, страницах или кеше.

Затем generic-параметр самой базы принимает representation-aspect. Разные
аспекты создают разные concrete types из одной логической структуры:

```text
Database<InMemory>
Database<BufferedFile>
```

`InMemory` размещает данные непосредственно в RAM. `BufferedFile` считает весь
файл логической памятью, но держит в RAM только две страницы. Оба аспекта
реализуют один logical contract `Database`, поэтому исходные операции базы не
меняются.

## Принятые основания

- `layout` описывает логическое понимание структур данных памяти, их
  взаимодействие, pointers и адресные операции высокого уровня.
- Representation является аспектом, вызываемым компилятором во время
  компиляции.
- Representation-aspect получает конкретную структуру данных или layout, к
  которому он применён.
- Аспект может менять внутренние handlers и тела методов, создавать private
  physical state и сообщать компилятору, как вычислять physical places.
- Тип сам предусматривает representation в своих generics. Внешний код не
  может заменить representation у типа, который не объявил такую точку.
- Разные generic-инстанциации с разными representations являются разными
  concrete types.
- Representation может состоять из списка аспектов, если generic-объявление
  целевого типа явно предусмотрело соответствующие параметры или aspect pack.
  Здесь действуют обычные правила generics и аспектов.
- Применимость к структуре или классу определяет сам representation-aspect.
  Компилятор не навязывает ему exact-type, closed-world или AoS ограничения.
- Opaque type использует ту же representation, что и скрытый за ним тип.
- Representation не может нарушить явно объявленный логический контракт. Код
  representation и сгенерированный им HIR проходят обычные проверки.
- Если функция не объявила закрытый набор исключений или эффектов, они
  наследуются и выводятся автоматически по графу вызовов.
- Suspension также наследуется автоматически.
- Representation-aspect может добавлять realized type собственные публичные
  операции, например `flush`, `prefetch` или `compact`.
- Transparent access является группой функций. После явного объявления группы
  пользователь пишет обычное `pointer.field`; отдельный знак в месте доступа не
  требуется.
- Один layout может использовать несколько физических областей одновременно.
- Population владеет lifetime своих members. Уничтожение локального
  `Users.Pointer` не удаляет member; удаление выполняется явной операцией
  population. Ownership pointer задаёт authority, а не скрытый persistent drop.
- Одно logical place может иметь несколько физических replicas. В каждый момент
  не более одной replica является authoritative для записи.
- Логическая запись в файловой representation завершается после публикации
  authoritative-копии в RAM. Durability отдельно запрашивается через `flush()`.
- Минимальный `BufferedFile` не является shared representation. Transparent
  access удерживает исключительный borrow private cache state через suspension,
  поэтому две загрузки или flush одной page не interleave. Concurrent
  representation обязана заменить эту сериализацию собственным directory и
  coherence protocol.

Контракт `Representation` связывает compile-time имя `target` со структурой
текущей generic-инстанциации на всё время исполнения аспекта. Member templates
аспекта могут использовать `target.User` и `target.Users.Pointer` в сигнатурах:
при применении эти имена заменяются конкретными типами. Runtime capture объекта
`lang::Layout` не возникает. Объявленные аспектом `source`, private fields,
populations и constructors материализуются как физическая часть нового realized
type через обычный aspect definition plan.

## Часть 1. Логическая база данных

Ниже нет файлового кода. `Database` описывает только структуру данных и
логические операции.

```efen
layout Database {
    // Кандидат синтаксиса G1: representation-aspect является generic-параметром
    // самого типа и применяется самим типом.
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

    fn createUser(
        id: UInt64,
        name: FixedString<48>,
        balance: Int64 = 0
    ) -> Users.Pointer {
        require balance >= 0

        return Users.create(
            id: id,
            name: name,
            balance: balance
        )
    }
}
```

Логическая модель обещает:

- `Users.Pointer` называет пользователя этого экземпляра `Database`;
- `findUser`, `renameUser`, `deposit` и `createUser` имеют один смысл при любой
  representation;
- значение `balance` никогда не становится отрицательным;
- representation может изменить физический алгоритм каждой операции, но не её
  логический результат.

`Database` сам предусмотрел параметр `Physical` и применил его через
`use Physical`. Поэтому representation имеет разрешение аспекта. Та же операция
была бы незаконна для типа без такого generic-параметра.

## Часть 2. Простая representation в RAM

`InMemory` является compile-time aspect, а не runtime wrapper.

```efen
aspect InMemory conforms Representation {
    source ram: Ram

    constructor(ram: own Ram) {
        self.ram = take ram
    }

    meta fn apply() {
        for population in target.populations {
            population.setCreateHandler(createInRam)
            population.setRemoveHandler(removeFromRam)
            population.setPointerHandler(directPointer)
            population.setAccessHandler(directAccess)
            population.setIterationHandler(iterateInRam)
        }
    }

    private fn createInRam(plan: CreatePlan) -> LogicalPointer {
        let place = ram.allocate(plan.size, alignment: plan.alignment)

        try {
            plan.construct(into: place)

            // Logical identity свежая и не равна physical address.
            return plan.publish(
                identity: plan.population.nextIdentity(),
                physical: place
            )
        } catch error {
            plan.destroyInitializedFields(place)
            ram.release(place)
            throw error
        }
    }

    private fn removeFromRam(pointer: LogicalPointer) {
        let place = directPointer(pointer)
        pointer.type.destroy(place)
        ram.release(place)
    }

    private fn directPointer(pointer: LogicalPointer) -> PhysicalPlace {
        return pointer.population.resolve(pointer.identity)
    }

    private fn directAccess(pointer: LogicalPointer) -> AccessLease {
        return AccessLease(
            logical: pointer,
            physical: directPointer(pointer)
        )
    }

    private fn iterateInRam(plan: IteratePlan) -> Iterator<LogicalPointer> {
        return plan.publishedPointers()
    }
}
```

После применения компилятор создаёт concrete type:

```efen
alias MemoryDatabase = Database<InMemory>
```

Его пользовательский код остаётся логическим:

```efen
var db = MemoryDatabase(ram: Ram.system)

let user = db.createUser(
    id: 42,
    name: "Ada"
)

user.balance += 100
echo user.name
```

`user.balance` понижается в прямой доступ к RAM, потому что handlers
`InMemory` вернули direct physical place.

## Часть 3. Файловая representation с кешем

`BufferedFile` применяется к тому же логическому `Database`. Весь файл хранит
логическое население `Users`, а два RAM frames являются его текущими физическими
replicas.

```efen
aspect BufferedFile conforms Representation {
    // Кандидат F1: несколько физических областей принадлежат одному
    // representation-aspect.
    source file: File
    source ram: Ram

    // Representation contract связывает compile-time `target` со структурой
    // Database текущей generic-инстанциации. В runtime его объекта нет.

    private type Page: UInt64

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

    // Private population добавляется аспектом только в realized type.
    private set Frames: Frame from ram

    private struct Frame {
        var page: Page? {
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

        // Вычисляется из живых access leases и недоступно для присваивания.
        var pins: UInt {
            get { return liveLoans(to: self).count }
        }
    }

    let pageSize: Size = 4096
    let frameLimit: Size = 2
    let format: DatabaseFileV1 = DatabaseFileV1()
    var clock: UInt64 = 0

    // Кандидат F2: representation-aspect может добавить constructor своему
    // realized type.
    constructor(file: own File, ram: own Ram) throws IOError | InvalidFile {
        self.file = take file
        self.ram = take ram

        format.validateHeader(self.file)
        format.validateAllRecords(
            self.file,
            bufferSize: pageSize * frameLimit
        )

        // Кандидат F3: связать уже существующие bytes с logical population,
        // не создавая заново каждого User.
        self.Users.map(self.file)
    }

    meta fn apply() {
        if !target.hasPopulation("Users") ||
           target.Users.elementType != target.User {
            compileError("BufferedFile requires Database.Users: Database.User")
        }

        target.Users.setCreateHandler(createUser)
        target.Users.setRemoveHandler(removeUser)
        target.Users.setIterationHandler(iterateUsers)

        target.Users.setTransparentAccess(
            acquireRead: acquireRead,
            acquireWrite: acquireWrite,
            prepareWrite: prepareWrite,
            commitWrite: commitWrite,
            release: release
        )

        target.addMethod(flush)
        target.addMethod(close)
        target.addMethod(prefetch)
    }

    private fn findResident(page: Page)
        -> read write Frames.Pointer?
    {
        for frame in Frames {
            if frame.page == page && frame.io == Idle {
                return frame
            }
        }

        return null
    }

    private fn chooseVictim()
        -> read write Frames.Pointer
        throws CacheBusy
    {
        var result: read write Frames.Pointer? = null

        for frame in Frames {
            if frame.pins == 0 && frame.io == Idle &&
               (result == null || frame.lastUse < result.lastUse) {
                result = frame
            }
        }

        if result == null {
            throw CacheBusy()
        }

        return result
    }

    private fn acquireEmptyFrame()
        -> read write Frames.Pointer
        throws CacheBusy | OutOfMemory
    {
        if Frames.count < frameLimit {
            return Frames.create(
                page: null,
                bytes: ram.bytes(count: pageSize),
                replica: Empty,
                io: Idle,
                version: Version.initial,
                lastUse: 0
            )
        }

        return chooseVictim()
    }

    private fn flushFrame(frame: read write Frames.Pointer) throws IOError {
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
                frame.commitState(replica: Clean, io: Idle)
            } else {
                frame.commitState(replica: Dirty, io: Idle)
            }
        } catch error: IOError {
            frame.commitState(replica: Dirty, io: Idle)
            throw error
        }
    }

    private fn evict(frame: read write Frames.Pointer) throws IOError {
        require frame.pins == 0

        if frame.replica == Dirty {
            flushFrame(frame)
        }

        publishEmpty(frame)
    }

    private fn load(
        page: Page,
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

            publishClean(
                frame: frame,
                page: page,
                bytes: take bytes,
                version: file.version(page)
            )
        } catch error: IOError | InvalidFile {
            publishEmpty(frame)
            throw error
        }
    }

    private fn publishEmpty(frame: read write Frames.Pointer) {
        // Один no-throw commit меняет связанные свойства Frame.
        frame.commitState(
            page: null,
            replica: Empty,
            io: Idle
        )
    }

    private fn publishClean(
        frame: read write Frames.Pointer,
        page: Page,
        bytes: own [Byte],
        version: Version
    ) {
        // Validation и allocation завершены до этого no-throw commit.
        frame.commitState(
            page: page,
            bytes: take bytes,
            replica: Clean,
            io: Idle,
            version: version
        )
    }

    private fn acquireFrame(page: Page)
        -> read write Frames.Pointer
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        let resident = findResident(page)

        if resident != null {
            clock += 1
            resident.lastUse = clock
            return resident
        }

        let frame = acquireEmptyFrame()
        load(page, into: frame)

        clock += 1
        frame.lastUse = clock
        return frame
    }

    private fn acquireRead(pointer: read target.Users.Pointer)
        -> ReadLease<target.User>
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        let page = pageOf(pointer)
        let frame = acquireFrame(page)
        let offset = offsetOf(pointer, in: page)
        let place = format.project<target.User>(frame.bytes, offset)

        return ReadLease(
            logical: pointer,
            physical: place,
            pin: frame
        )
    }

    private fn acquireWrite(pointer: read write target.Users.Pointer)
        -> WriteLease<target.User>
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        let page = pageOf(pointer)
        let frame = acquireFrame(page)
        let offset = offsetOf(pointer, in: page)
        let place = format.project<target.User>(frame.bytes, offset)

        return WriteLease(
            logical: pointer,
            physical: place,
            pin: frame,
            originalVersion: frame.version
        )
    }

    private fn prepareWrite<Field>(
        lease: read WriteLease<target.User>,
        field: Field,
        value: field.Type
    ) -> PreparedWrite throws InvalidValue | OutOfMemory {
        return format.prepareEncoding(
            place: lease.physical,
            field: field,
            value: value
        )
    }

    private fn commitWrite(
        lease: read write WriteLease<target.User>,
        prepared: take PreparedWrite
    ) {
        // Encoding и authority metadata публикуются одним no-throw commit.
        lease.pin.commitWrite(
            place: lease.physical,
            encoding: take prepared,
            version: lease.pin.version.next(),
            replica: Dirty
        )
    }

    private fn release(lease: take AccessLease<target.User>) {
        // Drop lease завершает borrow и снимает pin.
    }

    private fn iterateUsers() -> Iterator<target.Users.Pointer> {
        // Header содержит число проверенных logical identities. Iterator
        // создаёт pointers по этим identities; доступ к полям идёт через
        // transparent handlers и загружает страницы по требованию.
        return logicalPointers(
            population: self.Users,
            count: file.header.userCount
        )
    }

    private fn createUser(plan: CreatePlan) -> target.Users.Pointer {
        // Append требует отдельного persistent publication protocol.
        // До его утверждения этот handler намеренно неполон.
        return appendAndPublish(plan)
    }

    private fn removeUser(pointer: target.Users.Pointer) {
        removeAndPublish(pointer)
    }

    fn prefetch(pointer: read target.Users.Pointer)
        throws IOError | InvalidFile | CacheBusy | OutOfMemory
    {
        acquireFrame(pageOf(pointer))
    }

    fn flush() throws IOError {
        // Write authority на realized instance исключает живые access leases
        // минимальной non-shared representation.
        assert Frames.all(where: it.pins == 0)

        for frame in Frames {
            if frame.replica == Dirty {
                flushFrame(frame)
            }
        }
    }

    fn close() throws IOError {
        flush()
        file.close()
    }
}
```

Весь кеш, I/O и physical mapping находятся в `BufferedFile`, а не в
`Database`. Representation-aspect добавляет private `Frames`, заменяет handlers
`Users` и добавляет realized type методы `prefetch`, `flush` и `close`.

## Часть 4. Использование двух concrete types

```efen
alias MemoryDatabase = Database<InMemory>
alias FileDatabase = Database<BufferedFile>

var temporary = MemoryDatabase(
    ram: Ram.system
)

var persistent = FileDatabase(
    file: File.open("users.db", access: readWrite),
    ram: Ram(size: 8192)
)

temporary.createUser(
    id: 1,
    name: "Temporary"
)

let user = persistent.findUser(42)!

// Обычный logical access. BufferedFile может выполнить cache lookup,
// file.readPage и suspension. Эффекты выводятся автоматически.
echo user.name

// Assignment завершается после публикации Dirty RAM frame как authority.
user.name = "Alice"

// Representation-specific API виден на точном типе FileDatabase.
persistent.prefetch(user)
persistent.flush()
persistent.close()
```

`MemoryDatabase` и `FileDatabase` являются разными типами. Общий алгоритм явно
параметризуется representation:

```efen
fn depositBonus(
    generic Physical: Representation,
    database: read write Database<Physical>,
    userId: UInt64,
    amount: Int64
) -> Bool {
    return database.deposit(userId, amount)
}
```

Для `Database<InMemory>` функция не получает I/O effects. Для
`Database<BufferedFile>` effects, `throws` и suspension наследуются из handlers
аспекта. Если внешний контракт функции закрыт и не допускает их, компилятор
выдаёт ошибку.

## Как компилятор применяет representation-aspect

Для `Database<BufferedFile>`:

```text
1. Подставить generic Physical = BufferedFile.
2. Построить логический Database: Users, User, predicates и methods.
3. Вызвать compile-time аспект BufferedFile с target = этот Database.
4. Аспект добавляет private physical state и регистрирует handlers.
5. Скомпилировать logical methods через новые handlers.
6. Проверить generated HIR обычными type, CFG, effect, ownership и predicate
   passes.
7. Опубликовать новый concrete type Database<BufferedFile>.
```

Например:

```efen
user.name = "Alice"
```

понижается через handlers аспекта:

```text
lease = BufferedFile.acquireWrite(user)
place = lease.project(field: User.name)
replacement = BufferedFile.prepareWrite(place, "Alice")
BufferedFile.commitWrite(lease, replacement)
BufferedFile.release(lease)
```

На каждом normal и exceptional exit borrow завершается, а pin освобождается.

## Пример representation-aspect для Columnar

Та же модель применяется к обычному контейнеру.

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

aspect Columnar conforms Representation {
    meta fn apply() {
        if !target.hasGenericArgument("Element") {
            compileError("Columnar requires a container with Element")
        }

        let element = target.genericArgument("Element")

        if !supportsColumnProjection(element) {
            compileError(
                "Columnar cannot realize the fields and lifecycle of ${element}"
            )
        }

        for field in element.fields {
            target.addPrivateStorage(
                name: field.name,
                type: Array<field.type>
            )
        }

        target.replaceHandler("append", appendFields)
        target.setElementAccessHandler(
            acquire: acquireElement,
            project: projectField,
            release: releaseElement
        )
        target.replaceHandler("copy", copyColumns)
        target.replaceHandler("move", moveColumns)
        target.replaceHandler("drop", dropColumns)
    }

    private fn appendFields(value: target.Element) throws OutOfMemory {
        // Сначала каждая column резервирует место и готовит своё значение.
        // Ни одна логическая строка ещё не опубликована.
        var prepared = PreparedColumns()

        for field in target.Element.fields {
            prepared.add(
                target.storage(field).prepareAppend(value[field])
            )
        }

        // Все последующие append и увеличение общего count не бросают.
        target.commitRow(take prepared)
    }

    private fn acquireElement(index: target.Index) -> ElementLease {
        return ElementLease(
            owner: target,
            index: index
        )
    }

    private fn projectField(
        lease: read ElementLease,
        field: target.Element.Field
    ) -> PhysicalPlace {
        return target.storage(field)[lease.index]
    }

    private fn releaseElement(lease: take ElementLease) {
        // Завершает logical borrow всех затронутых columns.
    }

    private fn copyColumns() -> Self {
        return target.copyEachStorage()
    }

    private fn moveColumns() -> Self {
        return target.moveEachStorage()
    }

    private fn dropColumns() {
        target.dropEachLogicalValueOnce()
        target.releaseAllStorages()
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

Логически:

```text
[X(a: 1, b: 2.0), X(a: 10, b: 4.0)]
```

Физически:

```text
a = [1, 10]
b = [2.0, 4.0]
```

`Columnar` сам решает, применим ли он к переданному element type, структуре,
классу или открытому набору runtime-видов. Это compile-time решение самого
аспекта.

## Непрозрачные типы

Opaque меняет nominal identity и visibility, но не representation:

```efen
opaque type UserId = UInt64
```

```text
Representation<UserId> == Representation<UInt64>
```

Если representation-aspect работает с physical form `UserId`, компилятор
проверяет совпадение с типом за opaque-границей. Opaque не требует отдельного
boxing или нового encoding.

## Несколько representation-aspects

Representation использует обычные возможности generic-параметров. Тип сам
задаёт число, роли и порядок aspects.

Фиксированный набор:

```efen
struct StoredArray {
    generic Element: Type
    generic Storage: Representation
    generic Codec: Aspect = Plain
    generic Protection: Aspect = None

    use Storage
    use Codec
    use Protection
}
```

Aspect pack, когда он нужен самому generic:

```efen
struct ExtensibleStore {
    generic Element: Type
    generic ...Physical: Aspect

    use ...Physical
}
```

Произвольная внешняя запись вида
`Encrypted<Compressed<Columnar>>` не создаёт pipeline сама по себе. Композиция
допустима только через generic-параметры и применение аспектов, предусмотренные
автором типа.

## Обязательства representation

### Логическая семантика

- Каждый logical pointer принадлежит правильному экземпляру realized type.
- Logical identity сохраняется при physical relocation, cache eviction и remap.
- Read возвращает текущее logical value.
- Write меняет ровно разрешённое logical place.
- Predicates исходной структуры сохраняются.
- Representation-specific API не отменяет исходный logical contract.

### Порожденный код

- Constructors не публикуют частично инициализированные values.
- Copy, move и drop выполняют lifecycle каждого logical value ровно один раз.
- Код аспекта и generated HIR проходят обычные проверки.
- Explicitly closed effects нельзя расширить.
- Inferred effects, exceptions и suspension распространяются автоматически.

### Файловая representation

- Минимальный вариант не shared: exclusive borrow private cache state живёт
  через suspension и сериализует load/flush одной page.
- На одну page опубликован не более чем один RAM frame в минимальном примере.
- Clean frame совпадает с file page.
- Dirty или Flushing frame является logical authority.
- Loading frame не обслуживает read до publication.
- Pinned frame нельзя вытеснить или несовместимо переместить.
- Failed load не публикует invalid bytes.
- Fallible encoding не оставляет изменённые bytes помеченными Clean.
- Failed flush не теряет dirty authority.
- Успешный flush версии `v` не может объявить clean более новую версию.

## Открытые семантические вопросы

Эти вопросы нельзя закрыть только выбором другого имени.

### P1. Предварительная и отложенная проверка

Минимальный `BufferedFile` использует eager validation с ограниченным RAM
buffer. Lazy-варианту требуется отдельное население encoded slots: до успешного
decode их нельзя объявить значениями `User`.

### P2. Ошибка долговечной записи

После failed flush RAM остаётся logical authority, но in-place file page может
быть torn. Повторное открытие требует journal, copy-on-write либо другого
recovery aspect.

### P3. Закрытие

Вероятная модель — explicit fallible `close`, переходящий в clean closed
typestate, и следующий за ним no-throw destructor. Retry, explicit discard и
process-crash recovery являются разными политиками.

### P4. Внешняя запись

Минимальная модель открывает файл эксклюзивно. Shared mutable file требует
epochs, coherence, invalidation и повторной validation.

## Кандидаты синтаксиса для последовательного утверждения

### G1. Representation как generic aspect

```efen
generic Physical: Representation = InMemory
use Physical
```

Требуемый смысл: generic type сам объявляет и применяет representation-aspect.

### G2. Конкретные реализованные типы

```efen
alias MemoryDatabase = Database<InMemory>
alias FileDatabase = Database<BufferedFile>
```

Это разные concrete types. `alias` только даёт им короткие имена.

### A1. Объявление representation-aspect

```efen
aspect BufferedFile conforms Representation {
    // compile-time and generated runtime code
}
```

### A2. Точка входа времени компиляции

```efen
meta fn apply()
```

`Representation` связывает compile-time имя `target` с определением текущей
generic-инстанциации. Ссылки вида `target.User` в типах специализируются и не
создают runtime capture. Entry point нужно сопоставить с уже принятым
aspect/ClassDefinition plan вместо параллельного механизма вызова.

### F1. Несколько физических областей

```efen
source file: File
source ram: Ram
```

Обе области принадлежат одной representation одного logical layout.

### F2. Конструктор representation

```efen
constructor(file: take File, ram: take Ram)
```

### F3. Принятие существующих байтов

```efen
target.Users.map(file)
```

`map` использует file source, но не создаёт заново каждый logical User.

### F4. Регистрация прозрачных обработчиков

```efen
target.Users.setTransparentAccess(
    acquireRead: acquireRead,
    acquireWrite: acquireWrite,
    prepareWrite: prepareWrite,
    commitWrite: commitWrite,
    release: release
)
```

### F5. Обычный пользовательский доступ

```efen
echo user.name
user.name = "Alice"
```

Дополнительный marker в месте доступа не нужен.

### F6. API конкретной representation

```efen
persistent.prefetch(user)
persistent.flush()
persistent.close()
```

### C1. Колоночный контейнер

```efen
alias XColumns = Array<X, Columnar>
```

`Columnar` получает конкретный `Array<X>` и структуру element type `X`, затем
заменяет physical handlers контейнера.

## Проверочные сценарии

1. `Database<InMemory>` выполняет logical tests базы без I/O.
2. `Database<BufferedFile>` проходит те же logical tests.
3. Cache hit не читает файл повторно.
4. Cache miss загружает страницу до publication.
5. Чтение трёх pages через два frames корректно вытесняет victim.
6. Dirty victim сбрасывается перед reuse.
7. Field borrow удерживает frame pinned.
8. Failed load не меняет logical state.
9. Logical write виден до flush.
10. Successful flush делает соответствующую version durable.
11. Failed flush сохраняет RAM authority.
12. `Array<X, Columnar>` и `Array<X, Contiguous>` проходят одинаковые logical
    tests массива.
13. Columnar access `values[i].field` обращается к соответствующей field column.
14. Неприменимая representation отклоняется при проверке generic-instantiation.

## Граница обобщения

После файлового примера ту же модель нужно проверить без новых языковых
primitives на:

- register allocation: logical values через registers и spill slots;
- DMA: logical buffers через host, in-flight и device replicas;
- GPU: host/device copies с authority transfer;
- NUMA: node-local read replicas;
- compressed storage: logical fields через decoded cache blocks;
- journaled database: RAM pages поверх WAL или copy-on-write file pages.
