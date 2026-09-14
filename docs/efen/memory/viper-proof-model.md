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
права перед каждым разыменованием ([`addresses.md:404-410`](addresses.md#владение-живость-и-доступ)).
Она также отделяет `own` от прав чтения и записи
([`ownership.md:5-20`](../types/ownership.md#аспекты-владения)). Настоящий
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
- checked-арифметику `Size`;
- современные взаимные условия, записанные у обоих полей, без старого
  неявного `inverse`.

Columnar storage здесь задаёт только будущую границу refinement. Его logical
identity не совпадает с physical row (`columnar-layouts.md:208-227`), а
`create`, `remove`, `replace` и `compact` должны отдельно доказать сохранение
отображений (`columnar-layouts.md:229-271`). Runtime-open kinds в эту модель не
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
origin-правила `Items.Item` (`addresses.md:133-137`) и несовместимости разных
множеств (`addresses.md:223-242`).

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
reallocation (`addresses.md:372-383`), а columnar compaction сохраняет logical
identity (`columnar-layouts.md:223-227`).

### 2.3. Чистая часть состояния

```text
layoutOf(d): LayoutInstance
kind(d): one | stableSet | area | areaSet
elementType(d): Type

liveAlloc: Set[AllocationId]
liveElem[d]: Set[ElementId]
everElem[d]: Set[ElementId]

areaDescriptor[a]: DescriptorId
areaEpoch[a]: Epoch
areaCapacity[a]: Size
occupant[a, epoch, index]: ElementId?
location[e]: (AreaId, Epoch, Index)?

initialized: Set[Place]
published: Set[ElementId]
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
published subset liveElem
provisionalElem disjoint liveElem[d]
provisionalElem disjoint published
```

`everElem` запрещает повторно признать старую identity свежей. Для политики с
recycling вместо монотонной identity требуется generation без wrap, способного
оживить старую ссылку (`columnar-layouts.md:223-227`).

### 2.4. Ресурсная часть

Ресурсное утверждение не является `Bool`. Его композиция записывается `R1 ⊗ R2`;
нейтральный элемент — `emp`. Из `R1 ⊗ R2` нельзя получить вторую копию линейного
ресурса.

```text
LayoutWrite(l)                 -- исключительное изменение опубликованного layout
DescriptorWrite(d)             -- изменение membership descriptor
LayoutState(l, sigmaL)         -- phase, openProperties и layout ghost fields
DescriptorState(d, sigmaD)     -- live/ever/published и association allocations
AreaState(d, a, sigmaA)        -- epoch, capacity, occupant/location/init slots
AllocationOwn(a)               -- обязанность освободить allocation
ElementOwn(e)                  -- обязанность уничтожить/передать логический элемент
StableOwner(d, a, e)           -- неразделимый owning handle allocation+element
Provisional(d, a, e, mask)     -- ещё не опубликованный initialized block
ValueOwn(v: T)                 -- обязанность уничтожить/передать значение
Uninit(p: Place, T)            -- slot существует и допускает construction
Init(p: Place, v: T)           -- в slot живёт полностью созданное значение
ReadCell(p, q)                 -- дробь q, 0 < q <= 1
WriteCell(p)                   -- полное исключительное право
LoanRead(loan, p, q)
LoanWrite(loan, p)
AreaStable(a, q)               -- доля запрета смены epoch
SlotStable(p, q)               -- доля запрета move/extract этого slot
LocationLease(loan, AreaRef, mode, q)
OpenAuthority(l, properties)
ClosedInvariant(l, property)
Cleanup(value-or-allocation)
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
ресурсная форма правила `take` из `ownership.md:233-260`. Диагностическая чистая
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
`liveElem`, `occupant`, `location`, `epoch`, `phase` или `published` без
соответствующего state predicate отвергает VIR validator.

Для стабильного set связь двух обязанностей задаёт bundle:

```text
StableOwner(d,a,e)
  == AllocationOwn(a) ⊗ ElementOwn(e) ⊗ Associated(d,a,e)

ElementStorage(d,a,e,mask,values)
  == Init(fields in mask) ⊗ Uninit(fields outside mask)
     ⊗ WriteCell(all physical fields)
```

`StableOwner` целиком находится в одном owner-place и переносится только целиком.
`ElementStorage` после публикации хранится внутри `DescriptorState`; borrows
временно выдают из него field resources. `free` требует одновременно owner
bundle и storage из того же association, поэтому нельзя потерять
`AllocationOwn`, сохранив `ElementOwn`, или наоборот.

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
`reallocateArea` и `free`; это соответствует `addresses.md:417-420`. Для
заимствований projected columnar field остаются обязательны origin, live и
отсутствие конфликтующего перемещения, даже если backing slot `managed`
(`ownership.md:25-44`).

## 3. Descriptor kinds

| Descriptor | Identity и allocation | Membership | Частичная инициализация | Relocation | Drop enumeration |
|---|---|---|---|---|---|
| `one` | один `AllocationId`, identity совпадает с жизнью `Self` | существует от публикации до destruction | только во время construction/destruction | по контракту representation; требует отсутствия leases либо сохранения их смысла | статический список полей |
| `set` | отдельные `AllocationId` и свежие `ElementId` | `liveElem[d]` | поля могут быть partial только до `Publish` и после `Retire` | стабильный блок не перемещается в первой версии | конечное `liveElem[d]` и схема полей |
| `area` | один `AreaId`, координаты `(epoch,index)`, отдельные `ElementId` occupants | множество инициализированных slots | произвольное конечное множество, API может требовать prefix | `reallocateArea` меняет epoch | `occupant` в объявленном порядке |
| `set area` | множество независимых `AreaId` одного descriptor | объединение occupants всех живых areas | отдельно для каждой area | независимо для каждой area | конечный каталог areas, затем slots каждой area |

`area` не хранит capacity или initialized count в runtime-pointer
(`addresses.md:139-171`). Proof state получает эти факты из полей владельца и
контрактов операций; emitter не вправе придумывать скрытую runtime-таблицу.

## 4. Контракты descriptor operations

Ниже `S` — входное состояние, `S'` — normal state, `S!` — exceptional state.
`samePublished(S!,S)` означает равенство всех опубликованных roots, membership,
значений и epochs. Переданный через `take` аргумент уже недоступен вызывающему;
если операция бросает после принятия аргумента, она обязана уничтожить принятые
части ровно один раз. Это согласуется с контрактом storage create
(`columnar-layouts.md:184-188`, `229-251`).

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
    e notin liveElem[D]; e notin published
    result resource = Provisional(D,a,e,allFields)
    Provisional contains StableOwner(D,a,e)
      ⊗ ElementStorage(D,a,e,allFields,value)
      ⊗ Cleanup(a,e,allFields)
    DescriptorState records e in everElem[D], but not in membership
    ValueOwn(value) потреблён

exception:
    samePublished(S!, S)
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
    liveAlloc += {a}; liveElem[D] += {e}; published += {e}
    DescriptorState получает ElementStorage(D,a,e,allFields,value)
    ownerDestination получает StableOwner(D,a,e)
    provisional Cleanup consumed, но drop/free не выполнены

exception:
    отсутствует

AbortProvisional(D,a,e) pre:
    Provisional(D,a,e,mask)

normal, no-throw/no-suspend/no-reenter:
    drop ровно полей mask; free a ровно один раз
    provisional sets очищены; e никогда не входит в liveElem/published
    StableOwner, ElementStorage и Cleanup consumed
```

Surface `D.allocate(value)` является композицией `allocateProvisional` и
`Publish`. Его normal post явно содержит `e in liveElem[D]`, `e in published`,
`StableOwner(D,a,e)` у результата и `ElementStorage` внутри нового
`DescriptorState`. Его exceptional post совпадает с точным abort выше и не
возвращает caller уже переданный через `take` value.

Prepare может бросить. `Publish`, передача owner bundle результату и запись
membership образуют no-throw/no-suspend/no-reenter commit. До `Publish` ссылка не
может попасть в обычный Efen-код.

Для descriptor с условиями у `set` контракт имеет две формы. `allocateClosed`
может вернуть closed state только если поля нового элемента уже доказывают все
затронутые условия. `allocateOpen` принимает `OpenAuthority(l,group)`, добавляет
membership внутри открытой group и возвращает тот же authority; caller обязан
безотказно присоединить элемент и выполнить `CloseProperty`. На exceptional
выходе `allocateClosed` возвращает прежние closed predicates, а `allocateOpen` —
прежний open authority и неизменённый published state. Третьего варианта, при
котором normal call публикует нарушающее condition состояние без authority, нет.
`allocateProvisional` вообще не меняет membership и потому предпочтителен для
построения нового узла перед присоединением. Если при открытой group последующая
операция всё же имеет exceptional edge, он обязан либо выполнить
`AbortProvisional` до восстановления старого state, либо доказанно завершить
новый state и закрыть group; оставить provisional resource на unwind нельзя.

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
set и не уничтожается повторно (`addresses.md:270-290`).

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
    samePublished(S!, S); никакой allocation/resource не утёк
```

Нулевая capacity не вызывает эту операцию: текущая модель использует `null`
(`addresses.md:166-171`). Первый Viper spike реализует получение физического
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
инициализации (`addresses.md:215-221`).

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
    samePublished(S!, S)
    root, old AreaState/AllocationOwn, capacity, epoch,
      initialized prefix и values сохранены
    provisional allocation/values очищены
```

Всегда новый proof epoch даёт консервативную семантику обещания, что старые
`Items.Item` *могут* стать недействительными (`addresses.md:372-383`). Strong
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
    drop slots в descriptor-declared DropOrder
    каждый initialized logical field dropped exactly once
    все occupants retired; a removed from liveAlloc
    AllocationOwn(a), ElementOwn occupants, Init slots consumed

exception:
    absent
```

Текущие документы не задают наблюдаемый порядок destructor-ов элементов.
Поэтому `DropOrder` является обязательным ещё не принятым контрактом descriptor,
а не скрытым выбором emitter-а. До решения прототип может фиксировать обратный
индексный порядок и указывать это в trusted assumptions.

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
    ClosedInvariant(l,p) for every p in dependencySCC(group)
    ⊗ LayoutWrite(l)
  --> OpenAuthority(l, group) ⊗ exposed field resources

CloseProperty(l, group):
    OpenAuthority(l, group) ⊗ exposed field resources
    ⊗ Proof(all formulas in group)
  --> ClosedInvariant(l,p) for all p in group ⊗ LayoutWrite(l)
```

Зависимые взаимные условия открываются одной strongly-connected group. Например,
`x.next == y` и `y.prev == x` открываются вместе, записи `next` и `prev`
выполняются явно, затем обе формулы доказываются. Никакой скрытой обратной записи
или старого `inverse` нет.

Закрытое состояние обязательно перед normal return, `throw`, suspension,
cancellation, публикацией ссылки, входом в destructor и вызовом кода, способного
получить доступ к layout (`addresses.md:329-341`). Проверенный helper может
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
`Contiguous.init` (`contiguous-array.efen:39-46`) не требует закрыть финальное
`length == capacity`, но exceptional edge обязан выполнить cleanup точного
префикса. Перед `return self` выполняется `PublishSelf`, доказывающий все условия.

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
descriptor operation (`ownership.md:262-266`).

`MoveOwn(source,destination)` требует пустое destination и отсутствие loans.
Он меняет `ownerPlace`, но сохраняет ровно один `ElementOwn` или `ValueOwn`.
Перезапись непустого owning destination должна сначала переместить или drop его
старого жильца. Самоприсваивание определяется отдельно до потребления ресурсов.

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

Каждое значение `Size` в VIR несёт `0 <= x <= SIZE_MAX`. Операции имеют явную
политику:

```text
CheckedAdd(x,y):
    normal if x + y <= SIZE_MAX: result = mathematical x + y
    exceptional Overflow: state and ownership arguments unchanged

CheckedMul(x,y):
    normal if x == 0 or y <= SIZE_MAX / x
    exceptional Overflow: state unchanged

CheckedSub(x,y):
    normal if y <= x
    exceptional Underflow: state unchanged

WrappingAdd(x,y): result = (x + y) mod (SIZE_MAX + 1)
```

Emitter использует Viper `Int` только вместе с этими range-фактами и ветвями.
`length + 1`, `capacity * 2`, `cursor + 1`, `index - 1` и вычисление числа chunks
не переводятся в безграничную арифметику молча.

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
field descriptorWriteToken: Bool

predicate StableOwner(x: Ref) {
  acc(x.ownToken)
}

define Cells(xs)
  (forall x: Ref :: { x.value }{ x.init }
     x in xs ==> acc(x.value) && acc(x.init))

predicate DStateWrite(d: Ref) {
  acc(d.members) && acc(d.descriptorWriteToken) && Cells(d.members)
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
field permissions в `Cells` и сворачивает отдельный `StableOwner`. Сам `new`
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

Код: `contiguous-array.efen:27-49`.

Pre-state и ресурсы:

```text
count: Size
Value callable make; self constructing and unpublished
self fields initialized as root=null, capacity=0, length=0
LayoutWrite(self) ⊗ construction Cleanup(self)
```

После строк 31-37 normal state содержит либо `root=null, count=0`, либо
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
14-20 и только затем публикуется `self`.

Текущий пробел контракта: в исходнике нет явного destructor/cleanup, хотя
`addresses.md:440-469` требует освобождение точного префикса. Это не ошибка
порядка строк конструктора, если compiler генерирует cleanup из descriptor, но
такой генератор и его контракт пока не определены.

Инкремент `self.length += 1` в строке 46 не требует отдельного overflow-ребра,
если loop invariant уже доказывает `self.length == index < count <= SIZE_MAX`.
Это именно доказанное отсутствие overflow, а не использование безграничного
Viper `Int`. Следующий индекс цикла проверяется тем же фактом.

### `itemAt`, `read`, `replace`

`itemAt` (`contiguous-array.efen:56-62`) требует closed layout, `index < length`,
ненулевой root, current epoch, initialized slot и read/write resource нужного
поля. BoundsError сохраняет все ресурсы.

`read` (`64-68`) возвращает копию только при `Copyable`; исходный `Init` и owners
сохраняются. `replace` (`70-75`) требует `ValueOwn(value)`, exclusive field loan и
отсутствие subobject borrow. Его normal post заменяет последовательность в одной
позиции и возвращает `ValueOwn(old)`.

Текущая развилка алгоритма: между `take item.Target` и присваиванием slot partial.
Если move/assignment нового `Target` может бросить, exceptional path оставляет
опубликованный массив с дырой. Нужен один из контрактов:

- перенос уже созданного `Target` в пустой slot является no-throw commit;
- либо `replace` сначала выполняет fallible prepare, затем атомарный no-throw
  обмен;
- либо exceptional cleanup восстанавливает старое значение.

Без одного из них текущий `replace` не доказуем. Добавление `assume nothrows` в
emitter недопустимо.

Это конкретный blocker текущей surface signature: `replace` не содержит ни
`Target: Movable`, ни гарантии no-throw placement. `Copyable` на `read` не
помогает: копия создаёт другой экземпляр, может иметь собственные эффекты, а код
`replace` использует именно `take`. Минимальное исправление — ввести принятый
контракт `NoThrowMovable` (либо нормативно включить no-throw placement в
`Movable`), потребовать его у прямой реализации `replace` и выполнять два
переноса в открытом no-throw commit. Для общего `Target` без такого ограничения
нужна descriptor-операция transactional `replaceSlot`: fallible prepare при
старом slot untouched, затем no-throw swap/commit. Просто дописать
`where Target: Copyable` недостаточно.

Тот же blocker повторяется в `dynamic-array.efen:140-145`,
`singly-linked-array.efen:65-70`, `doubly-linked-array.efen:92-97` и
`chunked-array.efen:211-216`; до изменения сигнатуры либо алгоритма ни один из
этих `replace` не получает статус verified.

Negative mutations: callback после утечки `&self`; чтение slot до initialize;
`length += 1` до initialize; cleanup `count` вместо `length`; double-drop prefix;
отсутствующая bounds-проверка; бросающий assignment после `take`.

## 10. Разбор `DynamicContiguous`

### `init`, access и `reserve`

`init` (`dynamic-array.efen:27-37`) публикует пустое membership и area заданной
capacity. При allocation failure partial `self` очищается, logical state наружу
не публикуется.

`itemAt`, `read`, `replace` имеют те же обязательства, что фиксированный вариант
(`dynamic-array.efen:47-53`, `134-145`).

`reserve` (`55-70`) требует closed layout, `minimum: Size`, `initialized ==
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

Алгоритмический дефект: `areaCapacity * 2` в строке 60 не защищён от overflow.
Нужен `CheckedMul` до открытия условий. Даже если allocator затем отвергнет
слишком маленькую capacity, wrapping уже изменил выбор алгоритма. Строки 63-69
корректно располагают потенциально бросающий prepare до no-throw записи новой
capacity при условии принятого контракта `reallocateArea`.

### `append`

Код: `dynamic-array.efen:72-82`. Pre: closed array, `ValueOwn(value)`, no
conflicting lease. Сначала нужен `CheckedAdd(length,1)`. Исключение arithmetic или
`reserve` сохраняет array; до строки 79 `value` ещё должен быть либо доступен
cleanup текущего frame, либо уже принят операцией с точно заданным exceptional
drop. После reserve slot `length` пуст. `initialize` должен иметь no-throw commit;
только затем `length = nextLength` закрывает condition.

### `insert`

Код: `dynamic-array.efen:84-109`. После bounds, checked add и reserve layout
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
`index < oldLength`. Единственные не выводимые из bounds увеличения здесь — оба
`length + 1` в строках 73 и 89; для них обязательны `CheckedAdd` до `reserve`.

Текущий алгоритм корректен только если все moves и финальный initialize после
reserve не бросают и не входят повторно. Иначе exceptional edge видит дырку и
переставленный suffix без rollback. Это ограничение сейчас находится в общем
описании примеров, но не выражено в сигнатурах descriptor operations.

### `remove`

Код: `dynamic-array.efen:111-132`. `extract(index)` возвращает единственный
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

Текущих условий reachability и `length == Items.count`
(`singly-linked-array.efen:3-26`) недостаточно как удобного Viper witness порядка.
Для proof вводится ghost sequence `order: Seq[ElementId]`:

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

Это конечный свидетель текущего `reachable`, а не аксиоматическая рекурсивная
функция. Он одновременно доказывает отсутствие раннего `null`, cycle, duplicate
owner и lost published node.

`order` имеет только два допустимых источника. Первый — compiler-known
structural HIR contract, например принятое в Amber `chained from head by next`,
чья семантика включает cardinality, termination и topology
(`amber/dev/DECISIONS.md:133-141`). Frontend обязан доказать refinement
`chained =>` опубликованные source-conditions и обновлять witness каждой
операцией. Второй — явное proof-only ghost state с объявленным representation
invariant и такими же проверяемыми updates. Verifier не может existentially
«выбрать подходящий order» и получить его через `assume` после просмотра heap.
Текущие `.efen`-примеры содержат только `reachable`, но не `chained` и не явный
ghost witness, поэтому lowering `List` и `DoubleLinkedList` пока обязан сообщать
`unsupported structural contract`, а не использовать последующие loop
invariants как уже доступные факты.

Есть отдельная ошибка прав: `tail` объявлен как `read Items.Item?` в строке 15,
но `append` записывает `self.tail!.next` в строке 82. Права являются частью типа
ссылки (`ownership.md:92-118`), поэтому наличие общего `LayoutWrite(self)` не
превращает read-only alias в write-ссылку. Алгоритм должен либо хранить у `tail`
невладеющую ссылку с правом записи и доказанным origin/lifetime, либо получать
write-доступ к последнему узлу через owning chain. До этого `append` должен быть
отвергнут frontend-ом, не Viper-emitter-ом.

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

Код: `singly-linked-array.efen:72-87`. Требуются `CheckedAdd(length,1)`,
`ValueOwn(value)`, `LayoutWrite`, closed order и no conflicting loans.
`allocate(Item(take value))` либо возвращает новый live element с
`ElementOwn(item)`, либо на исключении уничтожает принятый value и не меняет
список. Затем открывается group `{head,tail,order,next-ownership}`. Empty-case
переносит owner в `head`; nonempty-case — в старый `tail.next`. `tail` получает
read alias, order дополняется item, length обновляется, group закрывается.

Однако текущий `set Items` требует, чтобы *каждый* member был достижим от head
(`singly-linked-array.efen:3-5`). Если normal `Items.allocate` немедленно
публикует membership, новая identity между строками 74-76 и присоединением ещё
не достижима. Допустимы только два точных протокола:

1. `allocateProvisional` возвращает allocation, `ElementOwn` и initialized
   payload без membership; после явных записей `next/head/tail` операция
   `Publish` одновременно добавляет element в `Items`, обновляет `order/length`
   и закрывает conditions;
2. caller сначала получает `OpenAuthority` всей reachability-group, а контракт
   внутреннего `allocate` принимает и возвращает этот authority, меняет membership
   внутри открытого состояния и гарантированно не наблюдает layout. После normal
   return весь участок до присоединения no-throw/no-suspend/no-reenter; на throw
   до публикации прежний closed list сохранён, принятый value уничтожен ровно
   один раз.

Первый протокол проще и рекомендуется. Обычный внешний call boundary не может
вернуть published, но недостижимый item и затем надеяться закрыть condition позже.

### `insert`

Код: `singly-linked-array.efen:89-114`. Bounds и overflow выполняются до
allocation. После успешного allocation:

- index 0: owner старого head переносится в `item.next`, owner item — в head;
- middle: owner старого successor переносится `before.next -> item.next`, затем
  owner item — в `before.next`;
- index==length делегирует append до локального allocation.

Normal order равен `old[0,index) ++ [item] ++ old[index,...)`. После allocation
оставшийся участок обязан быть no-throw; иначе provisional item и временно
перенесённая chain требуют явного rollback.

### `remove`

Код: `singly-linked-array.efen:116-144`. `victim` получает owner из `head` либо
`before.next`; owner successor переносится из `victim.next` обратно в освободившийся
owner-place. Tail исправляется до закрытия group. Затем `Target` извлекается,
`Items.free` уничтожает только оставшиеся поля victim, а результат получает
`ValueOwn(Target)`. Normal order удаляет ровно `old[index]`.

Пробел layout-contract, не алгоритма: source не объявляет ghost order и точное
соответствие owner chain membership. Одного `reachable` недостаточно для
предсказуемого автоматического lowering. Алгоритмические риски: unchecked
`length+1`/`length-=1` и отсутствие явного no-throw контракта участка после
detach.

Точнее по арифметике: оба `length + 1` (`singly-linked-array.efen:73,99`)
требуют `CheckedAdd`; `length -= 1` в строке 140 доказуемо без underflow из
`index < length`; `position += 1` в строке 49 доказуемо из
`position < index < length <= SIZE_MAX`.

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

Как и в односвязном варианте, `tail` имеет только `read`
(`doubly-linked-array.efen:30`), но строка 113 пишет через `self.tail!.next`.
Это статически недостаточные права. Нужна write-capable невладеющая ссылка с
origin layout либо повторное получение write-доступа через owning chain.
Разрешение полного layout не повышает права самого значения ссылки.

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

Код: `doubly-linked-array.efen:99-118`. В nonempty-case новый item создаётся с
`prev=self.tail` до того, как `tail.next` указывает на него. Если `allocate`
публикует элемент и требует взаимные условия на своей normal boundary, строки
101-107 уже возвращают недопустимый published state: `item.prev.next != item`.

Это реальная несовместимость алгоритма с контрактом немедленной публикации, а не
недостаток SMT. Нужен один из вариантов:

- provisional allocation + явный `Publish` после обеих записей;
- `allocate` вызывается внутри открытой mutual-property group и его контракт
  принимает/возвращает `OpenAuthority` без observation;
- отдельная проверенная операция relation insertion.

Современная рекомендуемая форма — provisional item, затем открыть mutual group,
явно записать `oldTail.next=item` и `item.prev=oldTail`, обновить tail/order/length,
доказать обе стороны и опубликовать. Никакой скрытой inverse-записи нет.

Даже при `prev=null` та же публикационная проблема существует для любого нового
узла: condition `set Items { reachable ... }` из строк 3-5 ложно до включения в
head-chain. Поэтому provisional/Publish protocol обязателен для append и insert,
а не только для парного `prev`. Exceptional allocation до Publish сохраняет
старый closed list; после начала no-throw commit исключительных рёбер нет.

### `insert`

Код: `doubly-linked-array.efen:120-148`. В head-case четыре факта должны закрыться
вместе: owner old head переходит в `item.next`, `oldHead.prev=item`, owner item —
в `self.head`, `item.prev=null`. В middle-case group включает `before.next`,
`item.prev`, `item.next` и `successor.prev`. Текущий порядок строк 140-144
временно нарушает обе стороны, что допустимо только под одним
`OpenAuthority` и без исключений/reentrancy.

### `remove`

Код: `doubly-linked-array.efen:150-182`. После `take self.head` либо `take
before.next` новый forward edge уже установлен, а back edge ещё указывает на
victim до строк 164 или 174. Весь участок detach обязан быть одной открытой
no-throw group. Перед `free` доказывается:

```text
victim notin order
no next/prev/root field targets victim
victim.next == null
Target may be the only remaining initialized payload
```

Пробел layout-contract: нет явного конечного `order` и нет контракта открытия
mutual SCC. Алгоритмическая проблема append — ранняя публикация заведомо
несогласованного `prev`. Остальные перестановки доказуемы при явной open-group и
no-throw field moves. Также все изменения length требуют checked arithmetic.

Оба `length + 1` (`doubly-linked-array.efen:100,130`) требуют `CheckedAdd`.
`length -= 1` в строке 178 безопасен из bounds. `position += 1` прямого обхода
доказуем из `position < index < length`; `length - 1` и `position -= 1`
обратного обхода — из `index < length` и `position > index` соответственно.

Negative mutations: не очистить `head.prev`; оставить `successor.prev=victim`;
записать `prev` не тому successor; опубликовать item до парной записи; вызвать
callback между двумя сторонами; создать второй owning `next`; неверный backward
loop step.

## 13. Разбор `Chunked`

### 13.1. Необходимый cross-descriptor contract

Текущие условия `Chunks.count == directoryLength` и `Items.count == length`
(`chunked-array.efen:27-41`) не связывают конкретные item areas с directory.
Нужен ghost sequence `chunks` и flattening:

```text
|chunks| == directoryLength
directory[i] owns chunks[i] for every i
all chunk AreaId are live and pairwise distinct
chunk.capacity == CHUNK_SIZE
initializedIndices(chunk[i]) == [0, chunk[i].length)
0 <= chunk[i].length <= CHUNK_SIZE
all i + 1 < |chunks|: chunk[i].length == CHUNK_SIZE
sum(chunk.length for chunk in chunks) == self.length
flatItems == concat(chunkValues in directory order)
liveElem[Items] == set(flattened ElementIds)
```

Без pairwise distinct две записи directory могут владеть одним root, а quantified
permissions к slots дублируются. Без prefix/init и sum `itemAt` не доказывает,
что вычисленный slot инициализирован. Это недостаток layout-contract, а не
дефект `itemAt` сам по себе.

Поясняющий файл уже называет закон общего префикса нормативным
(`layout-examples/chunked-array.md:54-65`), но `.efen` содержит только локальные
условия строк 7-9, 34-40: квантор и cross-descriptor union там не выражены.
Backend не вправе извлекать нормативный закон из prose и молча `assume` его.
До появления внутреннего HIR-contract lowering этого примера должен завершаться
`unsupported layout contract`, даже если документационное объяснение верно.

### 13.2. `itemAt`, `chunkForPosition`, `growDirectory`

`itemAt` (`chunked-array.efen:55-64`) требует `index < self.length` и flattening
contract. Тогда `chunkIndex < directoryLength`, `offset < chunk.length`, root
жив, epoch актуален и slot initialized. Деление и остаток требуют
`CHUNK_SIZE > 0`, что известно из константы 256.

`chunkForPosition` (`66-74`) проверяет только существование directory entry; он
не обещает initialized item по offset. Это достаточный helper для позиции дырки
`self.length`, но его имя/контракт не должны молча означать membership Items.

`growDirectory` (`76-91`) — обычный area reallocation для `Chunks`. Его
алгоритмический дефект — unchecked `directoryCapacity * 2`. Item block epochs не
меняются при directory relocation; leases на `Chunks.Item` инвалидируются.

### 13.3. `ensureChunks`

Код: `chunked-array.efen:93-113`. Loop invariant:

```text
oldPublishedPrefix unchanged
directoryLength <= required
|chunks| == directoryLength
all existing chunk roots pairwise distinct and owned once
all existing chunk init sets agree with chunk.length
no provisional block at loop head
```

`nextDirectoryLength` использует `CheckedAdd`. После `growDirectory` выделяется
новый item area. Если `Chunks.initialize` бросает после принятия `Chunk(root:
take block)`, его exceptional cleanup обязан освободить вложенный item area. Если
этот nested-drop контракт отсутствует, строки 99-110 могут утечь. После успешной
инициализации запись `directoryLength` — no-throw commit закрытия условий.

В guard цикла `directoryLength < required`, где `required: Size`, поэтому
`directoryLength + 1 <= required <= SIZE_MAX`; overflow этого конкретного add
может быть доказан. Если frontend не сохраняет типовой range и guard-факт,
используется `CheckedAdd`, но не голый `Int + 1`.

### 13.4. `append`

Код: `chunked-array.efen:127-146`. Требуются checked `length+1` и безопасное
вычисление `1 + (nextLength-1)/CHUNK_SIZE`. `ensureChunks` может оставить
дополнительные пустые chunks, но published item sequence не меняет. Выбранный
`chunk.length` должен быть меньше capacity. `Items.initialize` затем
`chunk.length += 1`, затем `self.length=nextLength` образуют no-throw commit.

Здесь `self.length + 1` требует `CheckedAdd`. После его успеха выражение
`1 + (nextLength - 1) / CHUNK_SIZE` безопасно: `nextLength > 0`, частное меньше
или равно `nextLength - 1`, итог не превышает `nextLength <= SIZE_MAX`.
`chunk.length += 1` безопасен только из cross-descriptor факта
`chunk.length < CHUNK_SIZE`; локального условия `length <= capacity` для этого
недостаточно без доказательства, что выбранный slot пуст.

### 13.5. `insert`

Код: `chunked-array.efen:148-174`. После `ensureChunks` `chunkForPosition(old
length)` выбирает slot дырки, включая новую area на границе chunk. Loop invariant:

```text
index <= cursor <= oldLength
global initialized positions = [0,cursor) union (cursor,oldLength]
global hole = cursor
flat prefix/suffix preserve old order
all AreaId distinct
physical chunk.length fields still describe old published prefix
ValueOwn(newValue)
```

`movePosition` переносит occupant между areas без изменения global membership.
Локальные `chunk.length` временно не описывают init sets, особенно при переходе
через границу; поэтому связанные свойства всех затронутых chunks и Self должны
быть открыты одной group. После initialize увеличивается только old/new last
chunk length, затем общий length. Moves, initialize и эти записи обязаны быть
no-throw.

В insert снова требуется checked `self.length + 1`; формула requiredChunks имеет
то же доказательство bounds. `cursor -= 1` безопасен из `cursor > index`.
Увеличение `lastChunk.length` требует доказать `< CHUNK_SIZE` по global prefix
contract, а не предположить это из существования chunk.

### 13.6. `remove`

Код: `chunked-array.efen:176-199`. После extract global hole движется вправо:

```text
index <= cursor < oldLength
global initialized = [0,cursor) union (cursor,oldLength)
removed owns old flatItems[index]
shifted prefix equals old[index+1..cursor]
all unaffected chunks retain exact resources
```

После цикла уменьшается `lastChunk.length`, затем общий length. Пустой последний
chunk остаётся выделенным и может быть повторно использован; это допустимо, но
должно быть частью representation contract и destructor enumeration. Удаление
самой пустой area алгоритм не выполняет и обещать не должно.

В loop `cursor + 1` и `cursor += 1` безопасны из
`cursor + 1 < oldLength <= SIZE_MAX`. Оба вычитания в строках 196-197 безопасны
только из `index < oldLength` и cross-descriptor следствия
`lastChunk.length > 0`.

### 13.7. Итог по Chunked

Недостатки contracts: cross-descriptor coverage, disjoint roots, global order,
prefix initialization, ownership каталога и порядок nested destruction.
Алгоритмические проблемы: unchecked arithmetic и невыраженный cleanup
provisional block. При наличии названных contracts направление движения дырки и
обновление последнего chunk выглядят доказуемыми.

Negative mutations: два chunks с одним root; пропущенный chunk в union; неверный
`chunkIndex`; move с одинаковыми source/destination; неосвобождённый provisional
block; увеличение не последнего chunk; неправильный last chunk на границе 256;
ранняя запись общего length; directory freed раньше item areas.

## 14. Алгоритм или недостаточный contract

| Наблюдение | Класс | Следствие |
|---|---|---|
| `capacity * 2`, `length + 1`, `cursor + 1` без checked policy | алгоритм | добавить явные checked operations до открытия состояния |
| `Contiguous.replace` после `take` допускает бросающий assignment | алгоритм или ограничение generic | no-throw move либо transactional replace |
| `DoubleLinkedList.append` публикует item с несогласованным `prev` | алгоритм относительно immediate-publish `allocate` | provisional allocation или open-property contract операции |
| Нет явного cleanup конструктора/вложенного block | contract compiler-generated cleanup | определить generation и доказать exceptional edge |
| `reachable` не даёт удобного конечного порядка списка | layout contract | добавить ghost `Seq` witness/refinement |
| `Items.count` и `Chunks.count` не связывают две populations | layout contract | добавить coverage, disjointness, sum и flattening |
| Не задано, бросают ли `initialize`, `move`, field move, drop | descriptor/runtime contract | зафиксировать prepare/commit/cleanup effects |
| Не задан порядок drop area | descriptor contract | принять `DropOrder`, не выбирать его молча в emitter |
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
- `allocateProvisional`, `Publish` и `AbortProvisional` имеют отдельные state и
  exact cleanup; обычный `allocate` явно обновляет `liveElem` и `published`.
- `AllocationOwn` и `ElementOwn` связаны неразделимым `StableOwner`; связанные
  `Init` и field permissions хранятся в `ElementStorage` и потребляются `free`.
- Чистые maps принадлежат `LayoutState`, `DescriptorState` и `AreaState`;
  transitions требуют линейные `LayoutWrite`/`DescriptorWrite`, а не boolean
  разрешение.
- Ghost `order` допускается только из доказанного structural HIR contract
  (`chained`) либо явного proof state. При нынешнем одном `reachable` list
  lowering помечен unsupported.
- Все пять `replace` признаны заблокированными отсутствием
  `Movable`/no-throw-placement contract; `Copyable` не подменяет этот контракт.
- Viper sketch и Box slice теперь используют state predicate, provisional
  publication, owner bundle, field-resource consumption и resource-backed area
  guards. Эти схемы по-прежнему не названы запущенным proof.

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
flag (`columnar-layouts.md:273-291`).
