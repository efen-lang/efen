# Ресурсная модель доказательств layout

[Управление памятью](index.md) · [Компоновка](addresses.md) ·
[План доказательств](viper-proof-plan.md) · [Ownership](../types/ownership.md) ·
[Примеры Array](layout-examples/)

Статус: проект формальной модели. Документ задаёт вход для будущего VIR и
Viper-emitter, но не является отчётом о машинном доказательстве. Ни один
приведённый ниже фрагмент Viper в этом репозитории пока не запускался. Операции
источника памяти считаются доверенными только там, где это явно указано; это
предположение должно исчезнуть после проверки их реализации или refinement.

Нормативная модель требует проверять origin, живость, инициализацию, границы и
права перед каждым разыменованием ([раздел «Владение, живость и доступ»](addresses.md#владение-живость-и-доступ)).
Она также отделяет `own` от прав чтения и записи
([раздел «Аспекты владения»](../types/ownership.md#аспекты-владения)). Настоящий
документ сохраняет это разделение на каждом уровне.

## 1. Область модели

Первая последовательная версия покрывает:

- отдельные стабильные allocations в `set`;
- одну или несколько однородных `area`;
- частичную инициализацию;
- линейное владение значениями и allocations;
- обычные read/write borrows без конкурентности;
- normal, exceptional и cleanup-рёбра;
- временно открытые декларативные условия;
- сохранение уже разрешённого compiler arithmetic CFG для `Size`;
- современные взаимные условия, записанные у обоих полей, без старого
  неявного `inverse`.

Columnar storage здесь задаёт только будущую границу refinement. Его logical
identity не совпадает с physical row ([формальная модель columnar storage](columnar-layouts.md#формальная-модель)), а
`create`, `remove`, `replace` и `compact` должны отдельно доказать сохранение
отображений ([операции columnar storage](columnar-layouts.md#операции)). Runtime-open kinds в эту модель не
входят.

## 2. Типизированное состояние

### 2.1. Имена разных уровней

```text
LayoutId       -- статическая декларация layout
LayoutInstance -- конкретная runtime-жизнь Self
DescriptorId   -- (LayoutInstance, декларация one/set/area/set area)
AllocationId   -- одна жизнь выделенного физического блока
ElementId      -- одна логическая жизнь опубликованного элемента
AreaId         -- AllocationId области
Epoch          -- поколение координат внутри AreaId
Index          -- беззнаковый индекс в пределах Size
FieldPath      -- типизированный путь поля
LocalId        -- локальный slot CFG
LoanId         -- конкретное заимствование
PropertyId     -- декларативное условие или взаимная группа условий
```

Ни одна пара этих типов не приводится неявно. В частности, одинаковый машинный
адрес из двух descriptor не создаёт одинаковый `ElementId`; это следует из
origin-правила `Items.Item` ([производные типы descriptor](addresses.md#производные-типы-дескриптора))
и [несовместимости разных множеств](addresses.md#происхождение-и-разные-множества).

### 2.2. Ссылки и места

```text
StableRef(d, e)
    d: DescriptorId
    e: ElementId

AreaRef(d, a, epoch, index)
    d: DescriptorId
    a: AreaId
    epoch: Epoch
    index: Index

Place =
    Local(LocalId)
  | SelfField(LayoutInstance, FieldPath)
  | StableField(StableRef, FieldPath)
  | AreaSlot(AreaRef)
  | AreaField(AreaRef, FieldPath)
```

`StableRef` называет логический элемент отдельного `allocate`. `AreaRef` — чистая
типизированная координата `(descriptor, area, epoch, index)`, но ещё не право
доступа. Surface-значение `Items.Item`, возвращённое `at`, состоит из этой
координаты и scoped-ресурса `LocationLease`; frontend не позволяет отделить
координату от lease. Для инициализированного area slot состояние хранит
`occupant[AreaRef] = ElementId`. `Items.move` может сохранить `ElementId`,
изменив его координату; старый `AreaRef` после этого указывает на пустой slot и
не проходит проверку инициализации. `reallocateArea` меняет epoch, поэтому все
ссылки со старым epoch непригодны независимо от совпадения машинного адреса.
Такое разделение требуется
потому, что текущая модель допускает invalidation старых `Items.Item` после
reallocation ([перевыделение area](addresses.md#перевыделение-области-и-корневой-указатель)),
а columnar compaction сохраняет logical identity
([формальная модель storage](columnar-layouts.md#формальная-модель)).

### 2.3. Чистая часть состояния

```text
layoutOf(d): LayoutInstance
kind(d): one | stableSet | area | areaSet
elementType(d): Type

liveAlloc: Set[AllocationId]
liveElem[d]: Set[ElementId]
everElem[d]: Set[ElementId]
memberLive[d] := liveElem[d]
externallyEscaped: Set[ElementId]

areaDescriptor[a]: DescriptorId
areaEpoch[a]: Epoch
areaCapacity[a]: Size
occupant[a, epoch, index]: ElementId?
location[e]: (AreaId, Epoch, Index)?

initialized: Set[Place]
phase[l]: constructing | closed | open | destroying | dead
openProperties[l]: Set[PropertyId]
loanPlace[loan]: Place
loanMode[loan]: read | write | out
loanEpoch[loan]: Epoch?
provisionalAlloc: Set[AllocationId]
provisionalElem: Set[ElementId]
```

Обязательные чистые законы:

```text
e in liveElem[d]                  ==> e in everElem[d]
occupant[a,k,i] == e              ==> a in liveAlloc
                                      && areaDescriptor[a] == d
                                      && areaEpoch[a] == k
                                      && 0 <= i < areaCapacity[a]
                                      && e in liveElem[d]
location[e] == (a,k,i)            <==> occupant[a,k,i] == e
AreaSlot(d,a,k,i) in initialized  <==> occupant[a,k,i] != null
externallyEscaped intersect elementsOf(d) subset memberLive[d]
provisionalElem disjoint liveElem[d]
provisionalElem disjoint externallyEscaped
```

`everElem` запрещает повторно признать старую identity свежей. Для политики с
recycling вместо монотонной identity требуется generation без wrap, способного
оживить старую ссылку ([формальная модель storage](columnar-layouts.md#формальная-модель)).

### 2.4. Ресурсная часть

Ресурсное утверждение не является `Bool`. Его композиция записывается `R1 ⊗ R2`;
нейтральный элемент — `emp`. Из `R1 ⊗ R2` нельзя получить вторую копию линейного
ресурса.

```text
LayoutWrite(l)                 -- исключительное изменение опубликованного layout
DescriptorWrite(d)             -- изменение membership descriptor
LayoutState(l, sigmaL)         -- phase, openProperties и layout ghost fields
DescriptorState(d, sigmaD)     -- memberLive/ever/externallyEscaped и associations
AreaState(d, a, sigmaA)        -- epoch, capacity, occupant/location/init slots
AllocationOwn(a)               -- обязанность освободить allocation
ElementOwn(e)                  -- обязанность уничтожить/передать логический элемент
StableOwner(d, a, e)           -- неразделимый owning handle allocation+element
Provisional(d, a, e, mask)     -- ещё не опубликованный initialized block
ValueOwn(v: T)                 -- обязанность уничтожить/передать значение
PreparedOwn(v: Item)           -- полностью построенный owning argument
PreparedReplace(rep,p,new,plan)-- fallible prepare при неизменном published place
ReplaceRefinement(rep,kind)    -- proof witness concrete representation
Uninit(p: Place, T)            -- slot существует и допускает construction
Init(p: Place, v: T)           -- в slot живёт полностью созданное значение
ReadCell(p, q)                 -- дробь q, 0 < q <= 1
WriteCell(p)                   -- полное исключительное право
LoanRead(loan, p, q)
LoanWrite(loan, p)
AreaStable(a, q)               -- доля запрета смены epoch
SlotStable(p, q)               -- доля запрета move/extract этого slot
LocationLease(loan, AreaRef, mode, q)
OpenAuthority(l, properties, openState)
ClosedInvariant(l, property)
Cleanup(value-or-allocation)
PayloadOwnTree(value, owners)   -- nested owning fields initialized payload
ConstructionCleanup(self, mask, owners)
SelfDrop(self, mask, owners)
LocalChunkCleanup(local, area)
TemporaryChunkCleanup(temp, area)
CalleeChunkCleanup(argument, area)
PublishedChunkDrop(chunkElement, area)
```

Основные законы:

```text
WriteCell(p)              == ReadCell(p, 1)
ReadCell(p, q1 + q2)      == ReadCell(p, q1) ⊗ ReadCell(p, q2)
                            only if q1 + q2 <= 1
ElementOwn(e)             != WriteCell(any field of e)
Init(p, v)                != ReadCell(p, q)
Live(e)                   != Init(placeOf(e), v)
AllocationOwn(a)          != ElementOwn(occupant of a)
StableOwner(d,a,e)         cannot be split into independently movable owners
```

`ElementOwn` переносится между owner-places, но не создаётся чтением. Это
ресурсная форма [правила `take`](../types/ownership.md#явное-извлечение). Диагностическая чистая
карта `ownerPlace[e]` допустима, но она не заменяет линейный ресурс.

Чистые maps не являются глобальными переменными, которые VIR может присваивать
без ресурса. `LayoutState`, `DescriptorState` и `AreaState` — линейные state
predicates, владеющие соответствующими ghost cells и физическими permissions.
`LayoutWrite`/`DescriptorWrite` также являются линейными authority tokens, а не
`Bool`: transition потребляет `State(old) ⊗ WriteAuthority` и возвращает
`State(new) ⊗ WriteAuthority`. Чтение получает дробный snapshot, который нельзя
использовать для mutation. `AreaState` изменяется только вместе с
`DescriptorWrite(d)` и полным доступом к затронутым slot resources; изменение
layout fields дополнительно требует `LayoutWrite(l)`. Поэтому присваивание
`liveElem`, `occupant`, `location`, `epoch`, `phase` или `externallyEscaped` без
соответствующего state predicate отвергает VIR validator.

Для стабильного set связь двух обязанностей задаёт bundle:

```text
StableOwner(d,a,e)
  == AllocationOwn(a) ⊗ ElementOwn(e) ⊗ Associated(d,a,e)

ElementStorage(d,a,e,mask,values)
  == Init(fields in mask) ⊗ Uninit(fields outside mask)
     ⊗ WriteCell(all physical fields) ⊗ PayloadOwnTree(values,nestedOwners)
```

`StableOwner` целиком находится в одном owner-place и переносится только целиком.
`ElementStorage` после публикации хранится внутри `DescriptorState`; borrows
временно выдают из него field resources. `free` требует одновременно owner
bundle и storage из того же association, поэтому нельзя потерять
`AllocationOwn`, сохранив `ElementOwn`, или наоборот.

`ElementStorage` для составного значения дополнительно содержит
`PayloadOwnTree`: все owner-resources его initialized owning fields. Например,
после публикации `Chunk.root: own Items.Area` вложенный `AllocationOwn(area)`
находится ровно в `PayloadOwnTree(Chunk, root)`, а не исчезает и не остаётся
второй копией у прежнего local.

`Uninit(p,T)` и `Init(p,v)` взаимоисключающи. Viper permission к физическому полю
сам по себе не доказывает `Init`: Viper heap всегда содержит математическое
значение, даже когда Efen-slot ещё нельзя читать.

### 2.5. Borrow

```text
BorrowRead(p, q):
    ReadCell(p, q)  --> LoanRead(freshLoan, p, q)

EndBorrowRead(loan):
    LoanRead(loan, p, q) --> ReadCell(p, q)

BorrowWrite(p):
    WriteCell(p) --> LoanWrite(freshLoan, p)

EndBorrowWrite(loan):
    LoanWrite(loan, p) --> WriteCell(p)
```

Для area surface `Items.at` одновременно создаёт lease:

```text
AcquireAreaLease(h = AreaRef(d,a,k,i), read, q):
    AreaStable(a,q) ⊗ SlotStable(slot(h),q) ⊗ ReadCell(slot(h),q)
      --> LocationLease(freshLoan,h,read,q)

AcquireAreaLease(h, write, 1):
    AreaStable(a,1) ⊗ SlotStable(slot(h),1) ⊗ WriteCell(slot(h))
      --> LocationLease(freshLoan,h,write,1)

EndLease(loan):
    LocationLease(loan,h,mode,q)
      --> AreaStable(a,q) ⊗ SlotStable(slot(h),q) ⊗ CellCapability(mode,q)
```

Полный `AreaStable(a,1)` требуется `reallocateArea` и `free`; полный
`SlotStable(p,1)` требуется `move` и `extract` для p. Следовательно, живой lease
делает нужный полный ресурс недоступным, и запрет relocation следует из
ресурсной алгебры. Чистая проверка epoch остаётся второй защитой stale coordinate,
но не заменяет возврат ресурса через `EndLease`.

Reborrow дробит ресурс родительского loan, а не создаёт новый доступ. В первой
версии frontend вычисляет lifetime и вставляет `EndBorrow` на каждом normal и
exceptional выходе. Живой loan area slot блокирует `move`, `extract`,
`reallocateArea` и `free`; это соответствует
[правилу живого заимствования](addresses.md#владение-живость-и-доступ). Для
заимствований projected columnar field остаются обязательны origin, live и
отсутствие конфликтующего перемещения, даже если backing slot `managed`
([ownership и `managed`](../types/ownership.md#аспекты-владения)).

## 3. Descriptor kinds

| Descriptor | Identity и allocation | Membership | Частичная инициализация | Relocation | Drop enumeration |
|---|---|---|---|---|---|
| `one` | один `AllocationId`, identity совпадает с жизнью `Self` | существует от публикации до destruction | только во время construction/destruction | по контракту representation; требует отсутствия leases либо сохранения их смысла | статический список полей |
| `set` | отдельные `AllocationId` и свежие `ElementId` | `liveElem[d]` | поля могут быть partial только до `Publish` и после `Retire` | стабильный блок не перемещается в первой версии | конечное `liveElem[d]` и схема полей |
| `area` | один `AreaId`, координаты `(epoch,index)`, отдельные `ElementId` occupants | множество инициализированных slots | произвольное конечное множество, API может требовать prefix | `reallocateArea` меняет epoch | `occupant` в объявленном порядке |
| `set area` | множество независимых `AreaId` одного descriptor | объединение occupants всех живых areas | отдельно для каждой area | независимо для каждой area | конечный каталог areas, затем slots каждой area |

`area` не хранит capacity или initialized count в runtime-pointer
([производные типы descriptor](addresses.md#производные-типы-дескриптора)). Proof state получает эти факты из полей владельца и
контрактов операций; emitter не вправе придумывать скрытую runtime-таблицу.

## 4. Контракты descriptor operations

Ниже `S` — входное состояние, `S'` — normal state, `S!` — exceptional state.
`sameObservable(S!,S)` означает равенство roots, `memberLive`, external escape,
значений и epochs. Переданный через `take` аргумент уже недоступен вызывающему;
если операция бросает после принятия аргумента, она обязана уничтожить принятые
части ровно один раз. Это согласуется с контрактом storage create
([обычный API](columnar-layouts.md#обычный-api-и-динамические-виды),
[операции](columnar-layouts.md#операции)).

Для всех transition-схем ниже действует правило линейной полноты: каждый
state/authority/owner/resource из `pre` обязан появиться на каждом выходе ровно
в одной из форм — возвращён неизменённым, возвращён с новым состоянием, передан
другому owner-place либо явно потреблён `drop`/`free`. Если сокращённая запись
post-state перечисляет только изменившиеся части, остальные ресурсы из `pre`
возвращаются в прежнем состоянии; VIR validator всё равно проверяет полный
баланс. Молчаливое исчезновение ресурса не означает его уничтожение.

### 4.1. Provisional allocation и `Publish` стабильного `set`

Базовой операцией является не публикация, а создание provisional block:

```text
allocateProvisional(D, value) pre:
    kind(D) == stableSet
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D) ⊗ ValueOwn(value)
    value полностью initialized
    арифметика size/alignment доказана

normal:
    fresh a notin S.liveAlloc
    fresh e notin S.everElem[D]
    a in provisionalAlloc; e in provisionalElem
    e notin memberLive[D]; e notin externallyEscaped
    result resource = Provisional(D,a,e,allFields)
    Provisional contains StableOwner(D,a,e)
      ⊗ ElementStorage(D,a,e,allFields,value)
      ⊗ Cleanup(a,e,allFields)
    DescriptorState records e in everElem[D], but not in membership
    ValueOwn(value) потреблён

exception:
    sameObservable(S!, S)
    no Provisional resource escapes
    точная initialized mask созданных полей использована cleanup
    каждое созданное поле уничтожено, a освобождён ровно один раз
    ValueOwn(value) потреблён и остаток value dropped ровно один раз
```

`Provisional` не является обычной `StableRef`: его нельзя копировать, вернуть из
layout operation, записать в опубликованное поле или разыменовать через обычный
API. Разрешены только typed construction, явные relation writes внутри открытой
group, `Publish` и `AbortProvisional`.

```text
Publish(D, provisional, ownerDestination) pre:
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D)
    ⊗ Provisional(D,a,e,allFields)
    все mandatory safety properties доказаны
    все затронутые layout conditions либо доказаны,
      либо caller держит OpenAuthority их полной group

normal, no-throw/no-suspend/no-reenter:
    provisionalAlloc -= {a}; provisionalElem -= {e}
    liveAlloc += {a}; memberLive[D] += {e}
    e notin externallyEscaped
    DescriptorState получает ElementStorage(D,a,e,allFields,value)
    ownerDestination получает StableOwner(D,a,e)
    provisional Cleanup consumed, но drop/free не выполнены

exception:
    отсутствует

AbortProvisional(D,a,e) pre:
    Provisional(D,a,e,mask)

normal, no-throw/no-suspend/no-reenter:
    drop ровно полей mask; free a ровно один раз
    provisional sets очищены; e никогда не входит в memberLive/externallyEscaped
    StableOwner, ElementStorage и Cleanup consumed
```

Surface `D.allocate(value)` является композицией `allocateProvisional` и
`Publish`. Его normal post явно содержит `e in memberLive[D]`,
`e notin externallyEscaped`,
`StableOwner(D,a,e)` у результата и `ElementStorage` внутри нового
`DescriptorState`. Его exceptional post совпадает с точным abort выше и не
возвращает caller уже переданный через `take` value.

Prepare может бросить. `Publish`, передача owner bundle результату и запись
membership образуют no-throw/no-suspend/no-reenter commit. До `Publish` ссылка не
может попасть в обычный Efen-код.

Для descriptor с условиями у `set` контракт имеет две формы. `allocateClosed`
может вернуть closed state только если поля нового элемента уже доказывают все
затронутые условия. `allocateOpen` принимает
`OpenAuthority(l,group,sigmaOpen)`, добавляет
membership внутри открытой group и возвращает тот же authority; caller обязан
безотказно присоединить элемент и выполнить `CloseProperty`. На exceptional
выходе `allocateClosed` возвращает прежние closed predicates, а `allocateOpen` —
прежний open authority и неизменённый member state. Третьего варианта, при
котором normal call публикует нарушающее condition состояние без authority, нет.
`allocateProvisional` является только внутренней VIR-операцией; новый surface API
для неё не требуется. Обычный surface `D.allocate(value)` под уже открытой group
lowerится в `allocateOpen`:

Потенциально бросающее построение аргумента выполняется раньше:

```text
PrepareItem(fields) при closed LayoutState:
    normal: ValueOwn(fields) --> PreparedOwn(item)
    exception: точная partial mask очищена; layout остаётся closed

OpenProperty(l,group)
allocateOpen(D, take prepared, group)
```

Исключение `PrepareItem` не является выходом `allocateOpen`: group ещё не
открыта, поэтому действует обычный construction cleanup текущего frame.

```text
allocateOpen(D,prepared,group) pre:
    layoutOf(D) == l
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D)
    ⊗ OpenAuthority(l,group,sigmaOpen) ⊗ PreparedOwn(prepared)

normal:
    DescriptorState(D,Sd') ⊗ DescriptorWrite(D)
    ⊗ OpenAuthority(l,group,sigmaOpen') ⊗ StableOwner(D,a,e)
    memberLive[D]' = memberLive[D] union {e}
    e notin externallyEscaped
    ElementStorage(D,a,e,allFields,prepared) находится внутри Sd'
    PreparedOwn(prepared) потреблён в ElementStorage
    formulas group не предполагаются

exception:
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D)
    ⊗ OpenAuthority(l,group,sigmaOpen)
    старый member state сохранён
    принятый prepared и точная provisional mask очищены ровно один раз
    наружу не выходит a, e, owner, storage или Cleanup
```

После exceptional return caller доказывает старые formulas из неизменённого
state, выполняет `CloseProperty` и только затем rethrow. После normal return
caller явно присоединяет новый element и закрывает group. `allocateOpen` обязан
не наблюдать layout, не добавлять e в `externallyEscaped`, не входить в тот же
layout повторно и не приостанавливаться; все state/authority resources явно
возвращаются на обоих выходах. Любой store, callback argument, return или другая
передача identity наружу запрещена до `CloseProperty`; membership внутри
descriptor уже существует и позволяет законно записать внутренний `next`.
Пока эти source/runtime effects не доказаны, lowering вызова получает статус
`unsupported`, а не доверенный `assume`.

Для стандартных Array compiler выбирает более сильное разложение, не требующее
fallible allocation под открытым invariant:

```text
prepared = PrepareItem(...)                 // layout closed
provisional = allocateProvisional(prepared) // layout closed; may fail
OpenProperty(fullGroup)
item = Publish(provisional)                  // no-fail commit
link item; update order/tail/length
CloseProperty(fullGroup)
```

Surface-вызов остаётся `Items.allocate(...)`; provisional является внутренним
ресурсом VIR. Compiler сам выносит allocation и другие fallible действия до
`OpenProperty`, а открытое окно содержит только проверенные transitions без
call/safepoint. Если concrete representation не позволяет построить такое
разложение, её соответствующая операция отклоняется. Новая source-аннотация не
нужна.

### 4.2. `D.free(item: own D.Item)` для стабильного `set`

```text
pre:
    item = StableRef(D,e)
    e in liveElem[D]
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D)
    StableOwner(D,a,e) ⊗ ElementStorage(D,a,e,mask,values)
    нет живых loans на e или его поля
    нет входящей strong-ссылки на e
    все оставшиеся initialized-компоненты перечислены

normal, no-throw/no-suspend/no-reenter:
    Retire e; e removed from liveElem[D], but remains in everElem[D]
    drop каждого оставшегося initialized-компонента ровно один раз
    физический allocation освобождён
    StableOwner(D,a,e), ElementStorage, Init/Uninit и field permissions потреблены
    association (D,a,e) удалена из DescriptorState

exception:
    отсутствует
```

Компонент, ранее извлечённый через `take item.Target`, отсутствует в initialized
set и не уничтожается повторно
([физическое встраивание](addresses.md#поле-и-физическое-встраивание)).

### 4.3. `D.allocateArea(capacity)`

```text
pre:
    kind(D) in {area, areaSet}
    DescriptorState(D,Sd) ⊗ DescriptorWrite(D)
    0 < capacity <= SIZE_MAX
    bytes(capacity, Item) и alignment representable

normal:
    fresh a; liveAlloc += {a}; areaEpoch[a] = fresh epoch k
    areaCapacity[a] = capacity
    forall 0 <= i < capacity: Uninit(AreaSlot(D,a,k,i), Item)
    no occupant and no live ElementId created
    result owns AllocationOwn(a) ⊗ AreaStable(a,1)
    DescriptorState records association D->a
    AreaState(D,a,k,capacity,empty) owns slot states and SlotStable shares

exception:
    sameObservable(S!, S); никакой allocation/resource не утёк
```

Нулевая capacity не вызывает эту операцию: текущая модель использует `null`
([нулевая area](addresses.md#производные-типы-дескриптора)). Первый Viper spike реализует получение физического
блока через `new`; будущий source ABI возвращает `AllocationOwn` по проверенному
контракту, а не через голый `inhale`.

### 4.4. `D.at(root, index)` и `EndLease`

```text
pre:
    root = (D,a,k), a in liveAlloc, areaEpoch[a] == k
    0 <= index < areaCapacity[a]
    occupant[a,k,index] = e
    AreaSlot(D,a,k,index) in initialized
    AreaState(D,a,Sa) и требуемая read/write capability доступны
    для read доступны AreaStable(a,q) и SlotStable(slot,q)
    для write доступны их полные доли

normal, no-throw:
    h = AreaRef(D,a,k,index), occupant(h) = e
    result = ScopedItem(h, loan)
    для read: AreaStable(a,q) ⊗ SlotStable(slot(h),q)
              ⊗ ReadCell(slot(h),q)
          --> LocationLease(loan,h,read,q)
    для write: соответствующие полные resources
          --> LocationLease(loan,h,write,1)
    AreaState возвращён с выданными долями, не с полным ресурсом

exception:
    отсутствует после явной bounds/null проверки frontend-а
```

Сам `Area` не доказывает bounds; вызывающий передаёт факты capacity и
инициализации ([операции descriptor](addresses.md#операции-дескриптора)).

`AreaRef` без `LocationLease` можно использовать только как внутреннюю координату
proof state или сравнить как значение; разыменование невозможно. Lifetime
surface `Items.Item` заканчивается явным VIR `EndLease`, который возвращает
`AreaStable`, `SlotStable` и cell capability в `AreaState`. `move`/`extract`
требуют полные `SlotStable`, а `reallocateArea`/`free` — полный
`AreaStable(a,1)`, поэтому конфликт блокируется отсутствующим ресурсом.

### 4.5. `D.initialize(root, index, value: own Item)`

```text
pre:
    valid live (D,a,k), 0 <= index < capacity
    Uninit(p, Item), p = AreaSlot(D,a,k,index)
    DescriptorState(D,Sd) ⊗ AreaState(D,a,Sa)
    ⊗ DescriptorWrite(D) ⊗ SlotStable(p,1) ⊗ ValueOwn(value)
    no conflicting loan

normal:
    fresh e notin everElem[D]
    occupant[p] = e; location[e] = p
    liveElem[D] += {e}; everElem[D] += {e}
    Uninit(p) --> Init(p,value)
    ValueOwn(value) --> ElementOwn(e), если Item является owning element

exception before commit:
    area, occupant, membership и epoch не изменены
    принятый value и provisional части уничтожены ровно один раз
```

Commit обязан быть no-throw/no-suspend/no-reenter. Алгоритм, который уже создал
дырку или открыл layout invariant, может вызывать `initialize` только после
успешного prepare либо при доказанном `nothrow` для выбранного `Target`.

### 4.6. `D.extract(root, index)`

```text
pre:
    valid initialized p with occupant e
    DescriptorState(D,Sd) ⊗ AreaState(D,a,Sa)
    ⊗ DescriptorWrite(D) ⊗ SlotStable(p,1)
    ⊗ ElementOwn(e) ⊗ Init(p,value)
    no conflicting loan

normal, no-throw:
    occupant[p] = null; location[e] = null
    e removed from liveElem[D], remains in everElem[D]
    Init(p,value) --> Uninit(p,Item) ⊗ ValueOwn(value)
    ElementOwn(e) consumed; payload ownership belongs to result

exception:
    absent
```

`extract` перемещает payload, а не уничтожает его. Если возвращается составной
`Item`, его initialized mask также переносится в результат.

### 4.7. `D.move(from, fromIndex, to, toIndex)`

```text
pre:
    source p and destination q belong to live areas of D
    p != q
    Init(p,value) with occupant e
    Uninit(q,Item)
    DescriptorState(D,Sd) ⊗ AreaState(sourceArea,Sa)
    ⊗ AreaState(destinationArea,Sb) if distinct
    ⊗ DescriptorWrite(D) ⊗ SlotStable(p,1) ⊗ SlotStable(q,1)
    ⊗ ElementOwn(e)
    no loans conflicting with p or q

normal, no-throw:
    occupant[p] = null; occupant[q] = e; location[e] = q
    Init(p,value) ⊗ Uninit(q) --> Uninit(p) ⊗ Init(q,value)
    liveElem[D], everElem[D] and ElementOwn(e) preserved

exception:
    absent
```

Совпадающие места — отдельная операция no-op либо frontend error; они не
подпадают молча под контракт выше. Перекрывающиеся последовательности реализуются
серией moves через доказуемую движущуюся дырку.

### 4.8. `D.reallocateArea`

```text
pre:
    DescriptorState(D,Sd) ⊗ AreaState(D,a,Sa) ⊗ DescriptorWrite(D)
    root place содержит единственный AllocationOwn(a)
    полный AreaStable(a,1) и все SlotStable(a,*,1) возвращены
    oldCapacity == areaCapacity[a]
    initializedIndices(a) == [0, initializedCount)
    0 <= initializedCount <= newCapacity <= SIZE_MAX
    bytes(newCapacity, Item) representable
    нет живых LocationLease/loans для a

normal:
    root указывает на live area с capacity newCapacity и fresh epoch k'
    ElementId и порядок первых initializedCount occupants сохранены
    initializedIndices(resultArea) == [0, initializedCount)
    old epoch непригоден

normal in-place branch:
    resultArea == a; AllocationId сохранён
    AllocationOwn(a,oldEpoch,oldCapacity)
      --> AllocationOwn(a,k',newCapacity)
    никакой area не freed

normal relocation branch:
    resultArea == fresh a' != a
    caller receives AllocationOwn(a',k',newCapacity)
    old AreaState/AllocationOwn(a) consumed; old a freed exactly once

exception:
    sameObservable(S!, S)
    root, old AreaState/AllocationOwn, capacity, epoch,
      initialized prefix и values сохранены
    provisional allocation/values очищены
```

Всегда новый proof epoch даёт консервативную семантику обещания, что старые
`Items.Item` *могут* стать недействительными
([перевыделение area](addresses.md#перевыделение-области-и-корневой-указатель)). Strong
exception post допустим только для одной из трёх доказанных стратегий:

1. **Provisional copy/clone.** Потенциально бросающие копии создаются в fresh
   area, не изменяя old slots. Ошибка уничтожает точную mask provisional copies.
   После полной готовности no-throw commit меняет root и затем освобождает old
   area. Эта стратегия требует разрешённой семантикой копии; `Copyable` может
   иметь эффекты, которые также входят в exceptional contract.
2. **Fallible work first, no-throw move later.** Fresh capacity и все способные
   бросить вычисления готовятся при неизменном old state. Затем начинается
   no-throw/no-suspend/no-reenter commit, который переносит occupants, меняет root
   и освобождает old area. Эта стратегия требует доказанного no-throw placement
   каждого `Target`.
3. **Доказанный rollback.** Destructive throwing move допустим лишь при явном CFG
   rollback, который для каждой точки отказа восстанавливает old values,
   initialized set, ownership и root без новых исключений. Существование rollback
   нельзя предполагать.

In-place source operation отдельно обязана гарантировать: до её success old
allocation и bytes наблюдаемо не изменены; после success дальнейших исключений
нет. Она обновляет capacity и proof epoch того же `AllocationId`, преобразуя
`AllocationOwn`, но не выполняет `free`. New-allocation relocation, напротив,
получает fresh `AllocationId` и освобождает старый ровно один раз. Фраза
«potentially throwing moves в prepare» без выбора одной из стратегий запрещена.

### 4.9. `D.free(root, capacity, initializedCount)` для area

```text
pre:
    DescriptorState(D,Sd) ⊗ AreaState(D,a,Sa) ⊗ DescriptorWrite(D)
    root owns AllocationOwn(a), capacity == areaCapacity[a]
    полный AreaStable(a,1) и все SlotStable возвращены
    initializedIndices(a) == [0, initializedCount)
    no loans or leases for a
    все ElementOwn occupants принадлежат уничтожаемому owner tree

normal, no-throw/no-suspend/no-reenter:
    drop slots в любом порядке, допустимом опубликованным contract descriptor
    каждый initialized logical field dropped exactly once
    все occupants retired; a removed from liveAlloc
    AllocationOwn(a), ElementOwn occupants, Init slots consumed

exception:
    absent
```

По умолчанию Efen не задаёт наблюдаемый порядок destructor-ов элементов.
Emitter может выбрать любой порядок, но обязан уничтожить каждый
инициализированный элемент ровно один раз. Программа не может зависеть от
выбранного порядка. Конкретная абстракция может опубликовать более сильный
contract; тогда representation и emitter обязаны его доказать и сохранить.
Первый Box spike с trivial-drop payload `Int` доказывает одно потребление owner
token, field/storage permissions и один `free` без дополнительного порядка.

## 5. Open/close и точки наблюдения

### 5.1. Три класса свойств

1. **Неоткрываемая safety:** origin, live allocation, bounds, initialization,
   отсутствие двух `Own`, отсутствие dangling strong target.
2. **Layout conditions:** `length == Items.count`, `tail.next == null`, порядок
   и coverage. Их можно временно открыть.
3. **Дополнительные свойства:** termination, отсутствие логической утечки,
   сортировка. Их отказ не становится memory-safety proof, пока safety от них не
   зависит.

### 5.2. Протокол

```text
OpenProperty(l, group):
    LayoutState(l, phase=closed, sigmaL)
    ⊗ LayoutWrite(l)
    ⊗ ClosedInvariant(l,p) for every p in dependencySCC(group)
  --> OpenAuthority(l, group, sigmaOpen) ⊗ exposed field resources

CloseProperty(l, group):
    OpenAuthority(l, group, sigmaOpen) ⊗ exposed field resources
    ⊗ Proof(all formulas in group)
  --> LayoutState(l, phase=closed, sigmaL')
      ⊗ LayoutWrite(l)
      ⊗ ClosedInvariant(l,p) for all p in group
```

`OpenAuthority(l,group,sigmaOpen)` инкапсулирует ровно один
`LayoutState(l,phase=open,...) ⊗ LayoutWrite(l)` и маску открытой полной SCC.
Эти ресурсы не существуют рядом вторыми независимыми tokens и возвращаются
только через `CloseProperty`. Поэтому helper или `allocateOpen` переносит один
authority целиком на обоих выходах, а потерять layout state невозможно.

Зависимые взаимные условия открываются одной strongly-connected group. Например,
`x.next == y` и `y.prev == x` открываются вместе, записи `next` и `prev`
выполняются явно, затем обе формулы доказываются. Никакой скрытой обратной записи
или старого `inverse` нет.

Закрытое состояние обязательно перед normal return, `throw`, suspension,
cancellation, публикацией ссылки, входом в destructor и вызовом кода, способного
получить доступ к layout
([декларативные условия](addresses.md#декларативные-условия)). Проверенный helper может
принимать и возвращать тот же `OpenAuthority`; внешний callback — нет.

### 5.3. Construction и destruction

Непубликованный `self` находится в фазе `constructing`. Полные layout conditions
ещё не обязаны быть истинны, но всегда действуют:

- initialized mask;
- линейность принятых owners;
- cleanup stack;
- запрет утечки ссылки на `self` или provisional element.

Callback допустим во время construction только если его контракт доказывает, что
он не может получить origin строящегося layout. Поэтому `make(index)` в
`Contiguous.init` (`contiguous-array.efen:41-48`) не требует закрыть финальное
`length == capacity`, но exceptional edge обязан выполнить cleanup точного
префикса. Перед `return self` выполняется `PublishSelf`, доказывающий все условия.

Cleanup constructor-а является линейным owning resource:

```text
ConstructionCleanup(self,mask,owners)
  encapsulates Init(mask) ⊗ PayloadOwnTree(self,owners)
             ⊗ все AllocationOwn construction

PublishSelf:
  LayoutState(self,constructing,sigma)
  ⊗ LayoutWrite(self)
  ⊗ ConstructionCleanup(self,mask,owners)
  ⊗ Proof(all closed layout conditions)
    --> LayoutState(self,closed,sigma')
        ⊗ LayoutWrite(self)
        ⊗ ValueOwn(self, SelfDrop(mask,owners))

ThrowFromConstruction:
  LayoutState(self,constructing,sigma) ⊗ LayoutWrite(self)
  ⊗ ConstructionCleanup(self,mask,owners)
    --> DropInitialized(mask) --> FreeOwnedAllocations(owners)
    --> phase(self)=dead; resources --> emp
```

`SelfDrop` не появляется рядом вторым token: он является destructor obligation
внутри owning результата `ValueOwn(self,...)`. `PublishSelf` не стирает и не
disarm-ит cleanup, а преобразует его владельца. На throw generated executable
CFG потребляет тот же `ConstructionCleanup`; ghost переход без runtime drop/free
не удовлетворяет контракту.

Destruction сначала переводит closed layout в `destroying`, запрещает новые
loans и публикации, затем уничтожает элементы в доказанном порядке. Полные
обычные layout conditions могут ослабляться по мере drop, но safety и cleanup
инвариант остаются до `dead`.

## 6. Own, move и drop

`take p` является не чтением, а переходом:

```text
Init(p,v) ⊗ ValueOwn(v) ⊗ WriteCell(p)
  --> UninitOrNull(p) ⊗ ValueOwn(v) ⊗ WriteCell(p)
```

Для optional place `UninitOrNull` означает initialized `null`; для локальной
`let` — moved-from typestate; для обычного dense array элемент извлекает только
descriptor operation ([явное извлечение](../types/ownership.md#явное-извлечение)).

`MoveOwn(source,destination)` требует пустое destination и отсутствие loans.
Он меняет `ownerPlace`, но сохраняет ровно один `ElementOwn` или `ValueOwn`.
Перезапись непустого owning destination должна сначала переместить или drop его
старого жильца. Самоприсваивание определяется отдельно до потребления ресурсов.

Compiler-known `replace(place, value)` является одним атомарным переходом layout.
Compiler сначала синтезирует и проверяет refinement конкретной representation:

```text
PrepareReplace(rep,p,new) pre:
    ReplaceRefinement(rep,kindOf(p)) ⊗ Init(p,old) ⊗ ValueOwn(new)

normal:
    Init(p,old) сохранён
    PreparedReplace(rep,p,new,plan)

exception before commit:
    Init(p,old) сохранён
    new уничтожен ровно один раз
    layout закрыт
```

Только prepared plan допускается в commit:

```text
ReplacePlace(plan, p, new) pre:
    ReplaceRefinement(rep,kindOf(p))
    ⊗ PreparedReplace(rep,p,new,plan)
    ⊗ Init(p, old) ⊗ WriteCell(p)
    no conflicting loan

normal:
    Init(p, new) ⊗ ValueOwn(old) ⊗ WriteCell(p)

exception:
    отсутствует внутри commit
```

Frontend проверяет тип place, `Movable` и отсутствие конфликтующего loan, а
emitter порождает один `ReplacePlace`, не создавая промежуточный `Uninit(p)`.
Потенциально бросающие representation-вычисления выполняются в prepare при
неизменном place. Compiler может построить этот plan сам, но не предполагает
без witness, что произвольный hook representation является безотказным.

Внешние exceptional outcomes различаются:

```text
prepare failure или доказанный rollback:
    place содержит old
    new уничтожен ровно один раз
    layout закрыт

событие, доставленное после успешного commit:
    place содержит new
    old уничтожен ровно один раз, поскольку result не возвращён
    layout закрыт
```

Причина события и контракт операции определяют конкретную ветку. Отложить
ошибку без завершения либо rollback и точного ownership post-state недостаточно.
Если compiler не может синтезировать `ReplaceRefinement`, условная операция этой
representation отклоняется; нового source syntax для этого не требуется.

То же обязательство может быть задано явной атомарной `region`, когда её
surface-свойство будет утверждено. Здесь «атомарный» означает отсутствие
наблюдаемого промежуточного CFG-state, а не одну CPU-инструкцию.

На каждом выходе CFG validator проверяет линейный баланс:

```text
owners_in + owners_created
    = owners_returned + owners_stored + owners_dropped
```

Отсутствующий owner не оправдывается тем, что element всё ещё находится в
`liveElem`. Если descriptor владеет потерянным, но живым элементом, это
представляется явным `ElementOwnAt(DescriptorRoot(d), e)`, а не отсутствием
ресурса.

## 7. Арифметика

Поведение каждой операции `Size`, необходимые range proofs и runtime paths
формирует общий compiler frontend до анализа Array. VIR получает уже явный CFG и
обязан сохранить его без изменений: target width, normal result и любой
failure/trap/modulo path конкретного compilation mode.

Это не отдельная проблема Array. Его исходники не обязаны вручную проверять
`length + 1`, `capacity * 2`, `cursor + 1` или `index - 1`. Array-proof использует
арифметический path, уже созданный компилятором, и проверяет, что изменение layout
начинается после завершения вычисления. Локальные bounds и guards могут позволить
frontend удалить недостижимый runtime path.

Viper-emitter не вправе заменить машинное значение безграничным `Int` так, чтобы
исчезло фактическое поведение CFG. Если compiler выбрал modulo-result, verifier
моделирует именно его и либо доказывает дальнейшую безопасность Array, либо
отвергает этот путь; он не исправляет программу другой overflow policy.

## 8. Стратегия Viper encoding

Это схема emitter-а, не проверенный `.vpr`.

### 8.1. Стабильный `set`

В первом vertical slice physical allocation и `ElementId` представлены одним
Viper `Ref`, но VIR сохраняет их разными типами. Это локальная оптимизация
encoding, не тождество языка.

```viper
field value: Int
field init: Bool
field ownToken: Bool
field members: Set[Ref]
field escaped: Set[Ref]
field descriptorWriteToken: Bool

predicate StableOwner(x: Ref) {
  acc(x.ownToken)
}

define Cells(xs)
  (forall x: Ref :: { x.value }{ x.init }
     x in xs ==> acc(x.value) && acc(x.init))

predicate DStateWrite(d: Ref) {
  acc(d.members) && acc(d.escaped) && acc(d.descriptorWriteToken) &&
  d.escaped subset d.members && Cells(d.members)
}
```

`d.members: Set[Ref]` является membership, но право знать и менять его упаковано
в `DStateWrite`; это Viper-encoding пары `DescriptorState ⊗ DescriptorWrite`, а
не свободная чистая переменная. Read-only methods получают отдельный snapshot и
дробные cell permissions, но не `acc(d.members)` для записи. `Cells(d.members)`
владеет heap permissions, `StableOwner(x)` — отдельным линейным token. Чтение
порождает сначала `assert x in d.members`, затем `assert x.init`, и лишь затем
`x.value`. Благодаря
этому source diagnostic определяется Efen obligation, а не случайным сообщением
об отсутствующем `acc`.

Создание использует Viper `new(value, init, ownToken)`, явно присваивает ghost
`init` и обычные fields и сначала формирует provisional resource. Лишь template
`Publish` раскрывает `DStateWrite`, добавляет ссылку в `d.members`, передаёт
field permissions в `Cells`, не добавляет её в `d.escaped` и сворачивает
отдельный `StableOwner`. Escape template доступен только после close. Сам `new`
выдаёт permissions и свежий `Ref`, но не считается
Efen-initialization полей. Окончательный source
ABI вместо `new` обязан вернуть те же ресурсы по проверенному контракту. `inhale
Fresh(x)` запрещён.

### 8.2. Area

```viper
domain AreaSlotDomain {
  function slot(area: Ref, epoch: Int, index: Int): Ref
  function slotArea(cell: Ref): Ref
  function slotEpoch(cell: Ref): Int
  function slotIndex(cell: Ref): Int

  axiom slot_left_inverse {
    forall a: Ref, k: Int, i: Int ::
      { slot(a,k,i) }
      slotArea(slot(a,k,i)) == a &&
      slotEpoch(slot(a,k,i)) == k &&
      slotIndex(slot(a,k,i)) == i
  }
}
```

Левая обратная функция доказывает injectivity receiver expression, необходимую
для quantified permissions. Аксиома описывает только кодирование координат; она
не утверждает live, bounds или initialization. Для живой area emitter выдаёт
permissions ко всем `slot(a,k,i)` при `0 <= i < capacity`, а `init` и occupant
определяют, какие slots можно читать и drop.

Prelude дополнительно имеет ghost guard fields area и slot. Полный permission к
area guard кодирует `AreaStable(a,1)`, permission к `slot(a,k,i).guard` —
`SlotStable(p,1)`. `at` не оставляет их без изменения: он передаёт дроби guard и
cell permission в predicate `LocationLease(loan,a,k,i,mode,q)`. `EndLease`
разворачивает predicate и возвращает те же дроби. Reallocation требует полные
permissions ко всем guards, а move/extract — полные permissions затронутых slots;
поэтому Viper exclusivity, а не чистый `assert noLoans`, блокирует конфликт.

Epoch хранится в proof state с полным permission владельца area. Lease содержит
снимок epoch; каждый access проверяет равенство. `reallocateArea` требует вернуть
все loan permissions, создаёт новый epoch и не переносит старые leases.

### 8.3. Инварианты и trusted contracts

Layout conditions могут кодироваться Viper predicate, который упаковывает
quantified permissions и чистые формулы. `OpenProperty` становится `unfold`,
`CloseProperty` — `fold`; emitter не использует `inhale` для восстановления
формулы. Quantified permissions подходят для неупорядоченного населения и
array slots, но triggers являются частью backend tests, не VIR.

Каждый `Assume` в VIR имеет один из источников:

```text
TypedFrontendLaw(id)
CheckedRuntimeContract(id, version, digest)
RepresentationRefinement(id, artifact)
```

Validator запрещает иной `Assume`. Отчёт запуска перечисляет все использованные
источники. Успешная проверка схемы выше ещё не подтверждает source runtime,
allocator или destructor.

## 9. Разбор `Contiguous`

### `init`

Код: `contiguous-array.efen:27-52`.

Pre-state и ресурсы:

```text
count: Size
Value callable make; self constructing and unpublished
self fields initialized as root=null, capacity=0, length=0
LayoutWrite(self) ⊗ ConstructionCleanup(self,empty,noAllocations)
```

После строк 33-39 normal state содержит либо `root=null, count=0`, либо
`AllocationOwn(area), capacity=count, initialized={}`. В цикле нужен инвариант:

```text
0 <= index <= count
self.capacity == count
self.length == index
initializedIndices(root) == [0,index)
Items.count == index
forall j < index: occupant(j) owns exactly one initialized Item
forall j >= index: Uninit(slot(j))
cleanup(root,index) is available
self is unpublished
```

Вызов `make(index)` — observation point, но не может наблюдать `self`, если origin
не передан и не опубликован. При исключении он сохраняет area и точный prefix;
cleanup drop-ит `[0,index)` и освобождает area. После успешного `initialize`
`length += 1` закрывает prefix-инвариант. На выходе доказываются строки 3-4,
14-20 и только затем `PublishSelf` преобразует `ConstructionCleanup` в
`ValueOwn(self,SelfDrop(...))`.

Отсутствие явного destructor/cleanup в исходнике не является дефектом порядка
этого конструктора. Lowering обязан создать реальный exceptional CFG/resource
artifact: после отказа `make(index)` он проходит только initialized prefix
`[0,index)`, выполняет drop каждого принятого `Target` ровно один раз и вызывает
`Items.free` с `initializedCount=index`. Этот CFG исполняется runtime; ghost
формула cleanup его не заменяет. Пока генерация и resource balance такого ребра
не реализованы, машинного proof конструктора ещё нет, но новый source contract
не требуется: compiler генерирует cleanup, а representation/runtime обязаны
пройти его no-reentry/no-throw refinement. Наблюдаемый порядок drop остаётся
отдельной семантикой.

Для `self.length += 1` в строке 48 compiler frontend уже предоставляет
арифметический path. Loop invariant `self.length == index < count` позволяет
доказать normal result; Array-proof не выбирает overflow policy.

### `itemAt`, `read`, `replace`

`itemAt` (`contiguous-array.efen:58-64`) требует closed layout, `index < length`,
ненулевой root, current epoch, initialized slot и read/write resource нужного
поля. BoundsError сохраняет все ресурсы.

`read` (`66-70`) возвращает копию только при `Copyable`; исходный `Init` и owners
сохраняются. `replace` (`72-79`) требует `ValueOwn(value)`, exclusive field loan,
отсутствие subobject borrow и `Target: Movable`. Исходная
`replace(item.Target, value)` lowerится в один `ReplacePlace`: normal post
заменяет последовательность в одной позиции и возвращает `ValueOwn(old)`, а
промежуточного exceptional state с пустым slot нет.

Доказательство обязано проверить типизированный контракт одной операции и
отсутствие внутри неё suspension, observation, reentry и отдельного throw-edge.
Если representation требует fallible prepare, оно выполняется до `ReplacePlace`;
ошибка выходит при неизменном массиве. Ошибка, доставка которой отложена,
выходит только после завершения или доказанного rollback перехода и закрытия
layout. `assume nothrows` для этого не используется.

Та же схема применяется к `dynamic-array.efen:148-155`,
`singly-linked-array.efen:65-72`, `doubly-linked-array.efen:92-99` и
`chunked-array.efen:219-226`. Поэтому пять `replace` больше не имеют отдельного
source-hole blocker. Для каждой concrete representation compiler ещё обязан
синтезировать либо проверить `ReplaceRefinement`; неудача отклоняет условную
операцию этой representation, а не требует новой конструкции в Array-коде.

Negative mutations: prepare изменяет old place; prepare теряет owner нового
значения; commit вызывает callback; post-commit exception забывает drop old;
opaque primitive не имеет `ReplaceRefinement`; также callback после утечки
`&self`, чтение slot до initialize, ранний `length += 1` и double-drop prefix.

## 10. Разбор `DynamicContiguous`

### `init`, access и `reserve`

`init` (`dynamic-array.efen:27-37`) публикует пустое membership и area заданной
capacity. При allocation failure partial `self` очищается, logical state наружу
не публикуется.

`itemAt`, `read`, `replace` имеют те же обязательства, что фиксированный вариант
(`dynamic-array.efen:47-53`, `142-155`).

`reserve` (`55-72`) требует closed layout, `minimum: Size`, `initialized ==
[0,length)`, `length <= areaCapacity`, `AllocationOwn(root)` при ненулевой
capacity и отсутствие живых area leases. Normal post:

```text
capacity' >= minimum
length' == length
values' == values
ElementId sequence' == old sequence
epoch' != epoch if reallocation happened
in-place: AllocationId preserved and no area freed
relocation: fresh AllocationId and old area freed exactly once
```

Exceptional post полностью сохраняет root, epoch, capacity, length, membership,
values и old `AllocationOwn`.

Compiler-resolved вычисление `areaCapacity * 2` в строке 62 завершается до
открытия условий. Array-proof рассматривает рост на полученном arithmetic path.
Строки 65-71 располагают потенциально бросающий prepare до no-throw записи новой
capacity при условии принятого контракта `reallocateArea`.

### `append`

Код: `dynamic-array.efen:74-86`. Pre: closed array, `ValueOwn(value)`, no
conflicting lease. Вычисление `length+1` разрешает compiler до изменения layout.
Неуспешный arithmetic path или `reserve` сохраняет array; до строки 83 `value` ещё должен быть либо доступен
cleanup текущего frame, либо уже принят операцией с точно заданным exceptional
drop. После reserve slot `length` пуст. `initialize` должен иметь no-throw commit;
только затем `length = nextLength` закрывает condition.

### `insert`

Код: `dynamic-array.efen:88-115`. После bounds, internal range check и reserve layout
открыт на no-throw участке. При входе в цикл:

```text
oldLength = old self.length
index <= cursor <= oldLength
initialized = [0,cursor) union (cursor,oldLength]
hole = cursor
sequence[0,cursor) == old[0,cursor)
sequence(cursor,oldLength] == old[cursor,oldLength)
ValueOwn(newValue)
```

После `move(cursor-1,cursor)` дырка становится `cursor-1`. Source всегда
initialized, destination empty. По выходе hole=`index`; initialize закрывает её,
а публикация `length=nextLength` происходит последней.

`cursor - 1` безопасен из guard `cursor > index >= 0`. В `remove` выражение
`cursor + 1` и следующий `cursor += 1` безопасны только потому, что loop
invariant усиливает guard до `cursor + 1 < oldLength <= SIZE_MAX`; emitter обязан
сохранить это proof obligation. `oldLength - 1` безопасен из входного
`index < oldLength`. Все arithmetic paths уже сформированы compiler frontend до
входа в доказательство изменения layout.

Текущий алгоритм корректен только если все moves и финальный initialize после
reserve не бросают и не входят повторно. Иначе exceptional edge видит дырку и
переставленный suffix без rollback. Это ограничение сейчас находится в общем
описании примеров, но не выражено в сигнатурах descriptor operations.

### `remove`

Код: `dynamic-array.efen:117-140`. `extract(index)` возвращает единственный
`ValueOwn(removed)` и создаёт hole. Loop invariant:

```text
index <= cursor < oldLength
initialized = [0,cursor) union (cursor,oldLength)
hole = cursor
newPrefix[0,index) == old[0,index)
newPrefix[index,cursor) == old[index+1,cursor+1)
ValueOwn(removed) == old[index]
```

После последнего move initialized=`[0,oldLength-1)`. Затем уменьшается length и
возвращается removed. Все moves и return-move должны быть no-throw. Ошибка
направления, условие `<= oldLength`, пропущенный move или ранняя запись length —
отдельные negative mutations.

## 11. Разбор `List`

Compiler-known condition `chained from self.head by Item.next` вместе с
`length == Items.count` (`singly-linked-array.efen:3-26`) порождает ghost
sequence `order: Seq[ElementId]`:

```text
length == |order|
set(order) == liveElem[Items]
all elements of order are distinct
head == null <==> |order| == 0
tail == null <==> |order| == 0
head == order[0] and tail == order[|order|-1] when nonempty
next(order[i]) == order[i+1] for i+1 < |order|
next(last) == null
ElementOwn(order[0]) is stored at self.head
ElementOwn(order[i+1]) is stored at order[i].next
```

Это конечный свидетель `chained`, а не аксиоматическая рекурсивная функция. Он
одновременно доказывает отсутствие раннего `null`, cycle, duplicate owner и lost
member node; отдельное tail-condition доказывает `tail == last(order)`.

`order` lowerится из compiler-known structural HIR contract `chained`, чья
семантика включает cardinality, termination и topology
(`amber/dev/DECISIONS.md:152-160`). Frontend создаёт proof-only state и обязан
доказать его обновление каждой операцией. Verifier не может existentially
«выбрать подходящий order» и получить его через `assume` после просмотра heap.
После замены set-level condition structural вход для List и DoubleLinkedList
определён. Compiler выносит fallible allocation до открытия и сам строит
effect-free publish window; concrete representation обязана доказать его
refinement.

`tail` объявлен как `var tail: read Items.Item?` в строке 15. `var` разрешает
переприсваивать сам слот; `read` относится к сохранённому невладеющему указателю.
При `self.tail!.next = ...` указатель предоставляет identity и origin, а
`LayoutWrite(self)` вместе с раскрытым `ElementStorage` предоставляет отдельный
`WriteCell(tail.next)`. Emitter не повышает `read` до `write`: он обязан показать
оба независимых ресурса. Поэтому запись корректна внутри изменяющей операции
layout и была бы отвергнута без её `write`-authority.

### `itemAt`, `read`, `replace`

`itemAt` (`singly-linked-array.efen:39-53`) после bounds использует invariant:

```text
0 <= position <= index < |order|
current == order[position]
current in liveElem[Items]
read resources for next fields remain available
```

Отсюда `current.next != null` на каждой итерации. Termination следует из
`index-position`, но это отдельный результат; безопасность разыменования не
должна зависеть от timeout. `read` и `replace` повторяют value-contracts выше.

### `append`

Код: `singly-linked-array.efen:74-91`. После compiler-resolved вычисления
`length+1` требуются `ValueOwn(value)`, `LayoutWrite`, closed order и отсутствие
conflicting loans.
Сначала при closed layout строится owning temporary `prepared = Item(take value,
next:null)` и выполняется fallible `allocateProvisional`. Только после его
успешного завершения компилятор открывает одну group
`{memberLive/Items.count,order,chained,head,tail,length,affected next,
ownerPlace(head/next)}`. Mandatory safety — origin, live targets, initialization,
unique own и отсутствие dangling strong target — в group не входит. Surface
`Items.allocate(take prepared)` внешне не меняется; provisional существует только
в VIR.

Normal path:

```text
prepared = PrepareItem(take value, next:null)  // layout ещё closed
provisional = allocateProvisional(take prepared) // may fail; layout closed
OpenProperty(group)
item = Publish(provisional)                    // no-fail membership commit
newId = inspect identity(item)
if empty:  MoveOwn(item, self.head)
else:      MoveOwn(item, oldTail.next)
tail = reference at new owner-place; order = old(order) ++ [newId]
length = nextLength
CloseProperty(group)
```

Exceptional path:

```text
PrepareItem throws
    -> layout остаётся closed; partial temporary очищен; rethrow

либо:

allocateProvisional(take prepared) throws
    -> layout остаётся closed
    -> old Items/order/head/tail/length
    -> принятый value dropped ровно один раз; rethrow
```

Открытый участок `Publish → links/order/length → CloseProperty` compiler сам
строит без call, safepoint, suspension или reentry. Concrete representation
обязана доказать refinement no-fail `Publish`; если это невозможно, её операция
отклоняется. Новая source-аннотация не требуется.

### `insert`

Код: `singly-linked-array.efen:93-120`. Bounds, arithmetic, построение Item и
fallible allocation выполняются до открытия group. Затем `Publish` и связывание
идут в одном generated critical window. После успешного allocation:

- index 0: owner старого head переносится в `item.next`, owner item — в head;
- middle: owner старого successor переносится `before.next -> item.next`, затем
  owner item — в `before.next`;
- index==length делегирует append до локального allocation.

Normal order равен `old[0,index) ++ [item] ++ old[index,...)`. После allocation
оставшийся участок обязан быть no-throw/no-suspend/no-reenter и закрывает group;
exception до normal return allocation восстанавливает старый closed список по
описанному пути.

### `remove`

Код: `singly-linked-array.efen:122-152`. `victim` получает owner из `head` либо
`before.next`; owner successor переносится из `victim.next` обратно в освободившийся
owner-place. Tail исправляется до закрытия group. Затем `Target` извлекается,
`Items.free` уничтожает только оставшиеся поля victim, а результат получает
`ValueOwn(Target)`. Normal order удаляет ровно `old[index]`.

`chained` теперь задаёт ghost order и точное соответствие owner chain membership.
Открытыми остаются representation refinement для atomic window и no-throw
placement после detach. Это proof-generator milestones, а не повод добавлять
`assume`.

Операции `length + 1`, `length -= 1` и `position += 1` поступают из общего
compiler arithmetic CFG и не являются отдельными решениями Array.

Negative mutations: tail не обновлён после удаления последнего; `before.next`
не получает `victim.next`; один `ElementOwn` потерян; один узел дважды входит в
order; ранний null; cycle; free до извлечения Target.

## 12. Разбор `DoubleLinkedList`

Ghost `order` и owning `next` chain остаются такими же. Дополнительная взаимная
группа задаёт:

```text
prev(order[0]) == null
prev(order[i]) == order[i-1] for 0 < i < |order|
next(order[i-1]) == order[i]
```

Это точная двусторонняя связь условий строк 10-20 и root-условия строк 24-27
`doubly-linked-array.efen`. `prev` — read edge, `next` — owning edge; равенство
ссылок не создаёт второй `ElementOwn`.

Как и в односвязном варианте, `read` у `tail`
(`doubly-linked-array.efen:30`) характеризует сохранённый невладеющий указатель,
а не запрещает переприсваивать `var tail`. Строка 117 использует его identity и
origin, но `WriteCell(oldTail.next)` получает отдельно из `LayoutWrite` и
раскрытого storage. Proof обязан проверить оба ресурса; получать write только из
`read Items.Item` запрещено.

### `itemAt`, `read`, `replace`

Для прямого прохода invariant совпадает с `List`. Для обратного прохода
(`doubly-linked-array.efen:63-83`):

```text
index <= position < |order|
current == order[position]
position decreases toward index
position > index ==> current.prev == order[position-1] != null
```

`self.length - 1` безопасен, потому что bounds `index < length` доказывает
`length > 0`. `read`/`replace` используют те же value resources.

### `append`

Код: `doubly-linked-array.efen:101-122`. Сначала при closed layout строится
`prepared = Item(take value, prev:oldTail, next:null)` и выполняется fallible
`allocateProvisional`. Затем перед no-fail `Publish` открывается полная SCC:

```text
memberLive / Items.count
order / chained
self.head / self.tail / self.length
все затронутые next / prev formulas
ownerPlace для self.head и owning next
двустороннее next <-> prev relation
```

Origin, live target, initialization, unique `Own` и отсутствие dangling strong
target остаются закрытой mandatory safety. Новый
item входит в membership через `Publish` с `prev=self.tail`, пока `tail.next` ещё
не обновлён; временно открытые formulas не предполагаются истинными.

Normal path совпадает с List, но до close явно доказывает обе стороны:

```text
prepared = PrepareItem(take value, prev: oldTail, next: null) // closed
provisional = allocateProvisional(take prepared)              // may fail, closed
OpenProperty(fullScc)
item = Publish(provisional)                                   // no-fail
newId = inspect identity(item)
oldTail.next = take item       // либо self.head для empty
tail = reference at new owner-place
order = old(order) ++ [newId]; length = nextLength
if old order empty:
    prove head == newId && prev(newId) == null
else:
    prove next(oldTail) == newId && prev(newId) == oldTail
CloseProperty(fullScc)
```

Если `PrepareItem` или `allocateProvisional` бросает, layout ещё закрыт, старые
membership/order/links сохранены, а temporary очищается ровно один раз. После
`OpenProperty` exceptional edge отсутствует до `CloseProperty`. Новый surface
provisional API не нужен.
Скрытой inverse-записи нет: обе стороны пишутся исходным кодом.

Compiler обеспечивает отсутствие call/safepoint/suspension/reentry между
`Publish` и close. Representation обязана доказать no-fail refinement `Publish`;
если это невозможно, соответствующая операция representation отклоняется.

### `insert`

Код: `doubly-linked-array.efen:124-154`. Fallible allocation завершается раньше;
group открывается перед `Publish` и закрывается после всех явных записей. В
head-case четыре факта должны закрыться
вместе: owner old head переходит в `item.next`, `oldHead.prev=item`, owner item —
в `self.head`, `item.prev=null`. В middle-case group включает `before.next`,
`item.prev`, `item.next` и `successor.prev`. Текущий порядок строк 146-150
временно нарушает обе стороны, что допустимо только под одним
`OpenAuthority` и без исключений/reentrancy.

### `remove`

Код: `doubly-linked-array.efen:156-190`. После `take self.head` либо `take
before.next` новый forward edge уже установлен, а back edge ещё указывает на
victim до строк 172 или 182. Весь участок detach обязан быть одной открытой
no-throw group. Перед `free` доказывается:

```text
victim notin order
no next/prev/root field targets victim
victim.next == null
Target may be the only remaining initialized payload
```

`chained` предоставляет конечный `order`, а mutual SCC открывается перед
`Publish`. Compiler обязан синтезировать effect-free commit и доказать его
для representation; no-throw field moves остаются частью этого refinement.

`length -= 1` в строке 186 безопасен из bounds. `position += 1` прямого обхода
доказуем из `position < index < length`; `length - 1` и `position -= 1`
обратного обхода — из `index < length` и `position > index` соответственно.

Negative mutations: не очистить `head.prev`; оставить `successor.prev=victim`;
записать `prev` не тому successor; закрыть group до парной записи; вызвать
callback между двумя сторонами; создать второй owning `next`; неверный backward
loop step.

## 13. Разбор `Chunked`

### 13.1. Generated cross-descriptor invariant

Compiler строит candidate ghost sequence `chunks` и flattening из трёх входов:
канонической семантики descriptor transitions, полного тела representation и
экспортируемого поведенческого контракта Array. Затем он отдельно доказывает
base case и preservation каждой операции:

```text
|chunks| == directoryLength
requiredChunks(n) = if n == 0 then 0 else 1 + (n - 1) / CHUNK_SIZE
requiredChunks(self.length) <= directoryLength
directory[i] owns chunks[i] for every i
all chunk AreaId are live and pairwise distinct
chunk.capacity == CHUNK_SIZE
initializedIndices(chunk[i]) == [0, chunk[i].length)
forall 0 <= i < directoryLength:
    chunk[i].length =
        min(CHUNK_SIZE, max(0, self.length - i * CHUNK_SIZE))
chunkItems[i]: Seq[ElementId]
|chunkItems[i]| == chunk[i].length
forall j in bounds(chunkItems[i]):
    location(chunkItems[i][j]) == AreaSlot(chunk[i].root,currentEpoch,j)
all locations above form a bijection with initialized slots
sum(chunk.length for chunk in chunks) == self.length
flatItems == concat(chunkItems in directory order)
allDistinct(flatItems)
set(flatItems) == memberLive[Items]
flatValues[j] == valueOf(flatItems[j])
```

Все операнды формул length и `requiredChunks` инъектированы в неограниченные
математические целые proof logic; это не runtime-умножение `Size`. Формула
допускает retained zero suffix: после уменьшения length
directory может содержать любое число прежних chunks с `length == 0`.
Неравенство `requiredChunks(self.length) <= directoryLength` не даёт формуле
стать vacuous при ненулевом `self.length` и пустом directory.

Descriptor semantics канонически даёт `occupant ↔ location`, initialization,
freshness и точное изменение membership: `initialize` добавляет один occupant,
`move` сохраняет identity, `extract` удаляет его, `free` удаляет остаток area.
`own Chunk.root` обеспечивает уникальность владельца area.

Остальные свойства доказываются по реализации. Compiler обязан проверить, что
все populated areas покрыты опубликованными `Chunk`, initialized slots образуют
нужные префиксы, записи `chunk.length`/`self.length` восстанавливают distribution
и sum, а направления moves сохраняют `flatItems`. Наконец, именно
экспортируемая семантика Array задаёт цель порядка: append добавляет в конец,
insert вставляет в позицию, remove удаляет её, read/replace обращаются к той же
логической последовательности. Одной корректности descriptor membership для
этого недостаточно.

Surface cross-descriptor квантор для этого не нужен. Generated invariant входит
в HIR/VIR как сгенерированная цель, а не как `assume`. Неучтённый producer/
consumer, populated hidden area вне owner tree, пропущенная запись длины или
неверный порядок moves разрушает preservation proof и отклоняет representation.
Новая пользовательская декларация для стандартного Chunked Array не нужна.

### 13.2. `itemAt`, `chunkForPosition`, `growDirectory`

`itemAt` (`chunked-array.efen:55-64`) требует `index < self.length` и flattening
contract. Тогда `chunkIndex < directoryLength`, `offset < chunk.length`, root
жив, epoch актуален и slot initialized. Деление и остаток требуют
`CHUNK_SIZE > 0`, что известно из константы 256.

`chunkForPosition` (`66-74`) проверяет только существование directory entry; он
не обещает initialized item по offset. Это достаточный helper для позиции дырки
`self.length`, но его имя/контракт не должны молча означать membership Items.

`growDirectory` (`76-91`) — обычный area reallocation для `Chunks`.
`directoryCapacity * 2` разрешается общим compiler arithmetic CFG до открытия
layout. Item block epochs не
меняются при directory relocation; leases на `Chunks.Item` инвалидируются.

### 13.3. `ensureChunks`

Код: `chunked-array.efen:93-113`. Loop invariant:

```text
oldMemberPrefix unchanged
oldDirectoryLength <= directoryLength
directoryLength <= max(oldDirectoryLength, required)
requiredChunks(self.length) <= directoryLength
|chunks| == directoryLength
all existing chunk roots pairwise distinct and owned once
all existing chunk init sets agree with chunk.length
no provisional block at loop head
```

После `growDirectory` выделяется новый item area. Если `Chunks.initialize`
бросает после принятия `Chunk(root: take block)`, cleanup token проходит точно
один owner-path:

```text
LocalChunkCleanup(block, AllocationOwn(itemArea))
  -- take block into prepared Chunk -->
TemporaryChunkCleanup(prepared, NestedOwn(root=itemArea))
  -- take prepared into Chunks.initialize -->
CalleeChunkCleanup(argument, NestedOwn(root=itemArea))

exception:
  CalleeChunkCleanup(argument, root, capacity=CHUNK_SIZE, initialized=0)
    --> Items.free(
          root: take cleanup.root,
          capacity: cleanup.capacity,
          initializedCount: 0
        )
    --> emp

normal publish:
  CalleeChunkCleanup(argument, root)
    --> PublishedChunkDrop(chunkElement, NestedOwn(root=itemArea))
    --> PayloadOwnTree(chunkElement, { root: AllocationOwn(itemArea) })
```

`ChunkCleanup` инкапсулирует `AllocationOwn`, а не существует рядом с ним. После
каждого `take` прежний cleanup owner-place пуст; поэтому exception callee не
может сочетаться со вторым cleanup local `block`. На normal path nested owner
удерживается `ElementStorage` member Chunk через `PayloadOwnTree` и
позже исполняется его `PublishedChunkDrop`. Это обязательный реальный executable
CFG/resource artifact, не ghost postcondition и не требование писать `defer`
вручную. Пока такой nested resource cleanup не сгенерирован и не проверен,
машинного proof `ensureChunks` ещё нет. Compiler сам создаёт critical cleanup
window; representation/runtime обязаны доказать его no-reentry/no-throw
refinement. После успешной инициализации запись `directoryLength` — no-throw
commit закрытия условий.

В guard цикла `directoryLength < required` локальный range-факт дополнительно
подтверждает normal arithmetic path `directoryLength + 1`; базовую семантику
предоставляет compiler frontend.

### 13.4. `append`

Код: `chunked-array.efen:129-150`. После compiler-resolved `length+1`
доказывается безопасное вычисление `1 + (nextLength-1)/CHUNK_SIZE`.
`ensureChunks` может оставить
дополнительные пустые chunks, но logical member sequence не меняет. Выбранный
`chunk.length` должен быть меньше capacity. `Items.initialize` затем
`chunk.length += 1`, затем `self.length=nextLength` образуют no-throw commit.

Здесь `self.length + 1` не имеет локального range proof. После успешного
internal narrowing выражение
`1 + (nextLength - 1) / CHUNK_SIZE` безопасно: `nextLength > 0`, частное меньше
или равно `nextLength - 1`, итог не превышает `nextLength <= SIZE_MAX`.
`chunk.length += 1` безопасен только из cross-descriptor факта
`chunk.length < CHUNK_SIZE`; локального условия `length <= capacity` для этого
недостаточно без доказательства, что выбранный slot пуст.

### 13.5. `insert`

Код: `chunked-array.efen:152-180`. После `ensureChunks` `chunkForPosition(old
length)` выбирает slot дырки, включая новую area на границе chunk. Loop invariant:

```text
index <= cursor <= oldLength
global initialized positions = [0,cursor) union (cursor,oldLength]
global hole = cursor
flat prefix/suffix preserve old order
all AreaId distinct
physical chunk.length fields still describe old member prefix
ValueOwn(newValue)
```

`movePosition` переносит occupant между areas без изменения global membership.
Локальные `chunk.length` временно не описывают init sets, особенно при переходе
через границу; поэтому связанные свойства всех затронутых chunks и Self должны
быть открыты одной group. После initialize увеличивается только `endChunk`
старого логического конца, затем общий length. Moves, initialize и эти записи обязаны быть
no-throw.

Формула requiredChunks имеет то же доказательство bounds. `cursor -= 1`
безопасен из `cursor > index`.
Увеличение `endChunk.length` требует доказать `< CHUNK_SIZE` по global prefix
contract, а не предположить это из существования chunk.

### 13.6. `remove`

Код: `chunked-array.efen:182-207`. После extract global hole движется вправо:

```text
index <= cursor < oldLength
global initialized = [0,cursor) union (cursor,oldLength)
removed owns old flatItems[index]
shifted prefix equals old[index+1..cursor]
all unaffected chunks retain exact resources
```

После цикла уменьшается `lastOccupiedChunk.length`, затем общий length. Пустые
chunks retained suffix остаются выделенными и могут быть повторно использованы;
это допустимо, но
должно быть частью representation contract и destructor enumeration. Удаление
самой пустой area алгоритм не выполняет и обещать не должно.

В loop `cursor + 1` и `cursor += 1` безопасны из
`cursor + 1 < oldLength <= SIZE_MAX`. Оба вычитания в строках 204-205 безопасны
только из `index < oldLength` и cross-descriptor следствия
`lastOccupiedChunk.length > 0`.

### 13.7. Итог по Chunked

Generated proof обязан установить cross-descriptor coverage, disjoint roots,
global order, prefix initialization и ownership каталога из всех descriptor
transitions. Открыта реальная генерация nested exceptional cleanup. При наличии
этих доказательств направление движения дырки и обновление chunk логического
конца выглядят корректными.

Negative mutations: два chunks с одним root; пропущенный chunk в union; неверный
`chunkIndex`; move с одинаковыми source/destination; неосвобождённый provisional
block; увеличение не `endChunk`; неправильный `lastOccupiedChunk` на границе 256;
ранняя запись общего length; directory freed раньше item areas.

## 14. Алгоритм или недостаточный contract

| Наблюдение | Класс | Следствие |
|---|---|---|
| Операции `Size` | вход от compiler frontend, не дефект Array | сохранить уже разрешённые arithmetic CFG paths; layout mutation начинается позже |
| `replace(place, value)` | compiler atomic transition | lowerить в один `ReplacePlace`; fallible prepare раньше, доставка ошибки только после commit/rollback и close |
| List allocation меняет membership до связывания | compiler-generated commit | fallible provisional allocation при closed layout, затем `Open → Publish → link → Close` |
| Нет явного cleanup конструктора/вложенного block | compiler lowering | сгенерировать реальный exceptional CFG с точным resource balance |
| `chained` требует proof witness порядка | compiler-known layout contract | вывести ghost `Seq` и доказать update каждой операцией |
| Связь `Items` с `Chunks` | generated compiler invariant | вывести coverage, disjointness, sum и flattening из полного набора descriptor transitions |
| Не задано, бросают ли `initialize`, `move`, field move, drop | descriptor/runtime contract | зафиксировать prepare/commit/cleanup effects |
| Не задан порядок drop area | принятое умолчание | порядок не определён; доказать exactly-once drop, а объявленную конкретной абстракцией гарантию проверять отдельно |
| Не задана identity area occupant при move/realloc | proof-model contract | использовать `ElementId + LocationLease + Epoch` |

`assume` не исправляет ни одну строку таблицы. Пока нужный contract не принят,
результат соответствующей операции — `unsupported lowering`, а не verified.

## 15. Минимальный one-block vertical slice

Исходный пример не использует Array:

```efen
layout BoxStore {
    set Boxes: Box

    struct Box {
        var value: Int
    }
}
```

Минимальный pipeline должен сохранить четыре артефакта: `.efen`, типизированный
CFG, `.vir`, `.vpr`. Срез выполняет:

1. `allocate` двух разных Box через Viper `new`;
2. формирование двух `Provisional`, затем публикацию двух свежих identity через
   `DescriptorState(Boxes) ⊗ DescriptorWrite(Boxes)`;
3. два read aliases первого Box;
4. завершение aliases и exclusive write;
5. `MoveOwn(localA, localB)` без изменения identity;
6. `free(take localB)` с exactly-once logical drop;
7. сравнение сохранённой identity после free;
8. отдельную попытку dereference, падающую на `Live`, а не на случайном backend
   permission message.

В этом срезе Viper-оптимизация `AllocationId == ElementId == Ref` разрешена
только потому, что каждый Box занимает отдельный стабильный allocation. Result
`allocate` всё равно содержит один `StableOwner`, а `DStateWrite` — связанные
`ElementStorage` и membership. `free` обязан получить оба ресурса, удалить
membership, consume все field permissions и owner token. Несохранённый owner или
field permission проверяется postcondition leak-check; успешный `new` сам по себе
не доказывает runtime allocator Efen и остаётся явно названной границей spike.

Обязательные negative mutations:

| Mutation | Ожидаемый obligation |
|---|---|
| заменить descriptor/layout instance у ссылки того же `Box` | `memory.foreign-origin` во frontend |
| скопировать `ElementOwn` вместо `MoveOwn` | `ownership.duplicate-own` в VIR validator |
| не завершить read loan перед write | `borrow.conflicting-write` |
| прочитать до `Initialize` | `memory.uninitialized-read` |
| прочитать после `free` | `memory.use-after-free` |
| дважды выполнить drop/free | `memory.double-drop` или отсутствие owner-resource |
| удалить `assert x in live` при намеренно сохранённом permission мёртвого блока | `memory.use-after-free`; fixture изолирует membership check от permission check |
| не потребить field permission при `free` | postcondition leak-check/ресурсный баланс не сходится |
| заменить `new` на `inhale acc(x.value)` без source contract | `vir.untrusted-assume`/template audit |
| потерять exceptional cleanup принятого value | `ownership.leaked-on-throw` |
| вернуть `Own` одновременно в двух postconditions | Viper permission/validator failure |

Каждый intentional failure обязан завершиться verification failure с ожидаемым
`obligationId` и `SourceSpan`; timeout, crash и unsupported не засчитываются.
Версия Silicon, solver settings, prelude digest и trusted assumptions сохраняются
рядом с результатом. До появления этих артефактов документ остаётся моделью, а
не доказательством.

## 16. Исправления после критики

- `AreaRef` теперь является только координатой, а surface `Items.Item` несёт
  scoped `LocationLease`; `EndLease` возвращает `AreaStable`, `SlotStable` и cell
  capability. Move и relocation блокируются отсутствием полного ресурса.
- `reallocateArea` разделён на in-place growth того же `AllocationId` и
  new-allocation relocation. Strong exception guarantee разрешена только для
  provisional copy, fallible-first/no-throw-move или явно доказанного rollback.
- Внутренние `allocateProvisional`, `Publish` и `AbortProvisional` имеют
  отдельные state и exact cleanup. Для стандартных Array surface `allocate`
  выносит fallible provisional allocation до `OpenProperty`, затем no-fail
  `Publish` обновляет `memberLive`, но не `externallyEscaped`.
- `AllocationOwn` и `ElementOwn` связаны неразделимым `StableOwner`; связанные
  `Init` и field permissions хранятся в `ElementStorage` и потребляются `free`.
- Чистые maps принадлежат `LayoutState`, `DescriptorState` и `AreaState`;
  transitions требуют линейные `LayoutWrite`/`DescriptorWrite`, а не boolean
  разрешение.
- Ghost `order` теперь lowerится из compiler-known `chained`; verifier доказывает
  update каждой операции и не подбирает witness через `assume`.
- Все пять `replace` получили требуемый `Movable`. Compiler-known
  `replace(place, value)` lowerится в один `ReplacePlace`, поэтому пустого
  промежуточного slot нет. Concrete representation обязана пройти
  `ReplaceRefinement`: fallible prepare сохраняет old place, commit не имеет
  observation edge, а оба exceptional post-state закрыты и сохраняют owners.
- Viper sketch и Box slice теперь используют state predicate, provisional
  publication, owner bundle, field-resource consumption и resource-backed area
  guards. Эти схемы по-прежнему не названы запущенным proof.
- После уточнения Edmond `read` у `var tail: read Items.Item?` относится к
  сохранённому указателю, а не к изменяемости слота. Запись через его identity
  использует отдельный `WriteCell`, полученный из `LayoutWrite`; прежняя
  классификация такой записи как ошибки прав удалена.
- `allocateOpen` теперь явно возвращает `DescriptorState ⊗ DescriptorWrite ⊗
  OpenAuthority` на обоих выходах; `OpenAuthority` инкапсулирует открытый
  `LayoutState ⊗ LayoutWrite`. Owning argument готовится до открытия group.
- Descriptor membership (`memberLive`) отделено от внешнего escape; новый member
  нельзя передать наружу до `CloseProperty`.
- `ConstructionCleanup` на `PublishSelf` преобразуется в owning `SelfDrop`, а
  `ChunkCleanup` линейно проходит local → temporary → callee →
  `PublishedChunkDrop`. Nested owners остаются в `PayloadOwnTree`.
- Chunked witness теперь связывает distinct identity с physical locations;
  одинаковые values допускаются отдельной проекцией `flatValues`.

## 17. Последовательность расширения

```text
stable Box set
  -> nullable strong field with finite holders
  -> quantified holders and mutual-condition group
  -> Area with prefix initialization
  -> Contiguous construction and cleanup
  -> DynamicContiguous relocation and moving holes
  -> List ghost order
  -> DoubleLinkedList mutual forward/back conditions
  -> Chunked cross-descriptor refinement
  -> closed-world columnar storage refinement
```

Клиентское доказательство всегда остаётся над logical population contract.
Physical representation отдельно доказывает bijection, unique writable location,
field-lens semantics, initialization и preservation transitions. Возможность
`Borrow`, `Address` или `Stable` подтверждается ресурсным witness, а не boolean
flag ([доступ и `managed`](columnar-layouts.md#доступ-ссылки-и-managed)).
