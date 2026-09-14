# План построения доказательств Efen → Viper

[Управление памятью](index.md) · [Компоновка](addresses.md) ·
[Проект backend](viper-verification-backend.md) ·
[Ресурсная модель](viper-proof-model.md) ·
[Примеры Array](layout-examples/)

Статус: рабочий план. Он не является доказательством и не утверждает, что
описанные конструкции уже реализованы. Первый результат этого плана — маленький
воспроизводимый Viper-корпус; полные Array и columnar storage являются более
поздними этапами.

## Цель

Построить проверяемую цепочку:

```text
Efen source
    → типизированные origin, places, rights и descriptor operations
    → CFG с normal, throw и cleanup-рёбрами
    → независимый от Viper ресурсный VIR
    → Viper
    → Silicon
    → диагностика в координатах Efen
```

Результат считается доказательством безопасности Efen только при выполнении
двух дополнительных условий:

1. lowering Efen → VIR и VIR → Viper сохраняет семантику;
2. runtime/source/representation реализует те же контракты, которые использовало
   доказательство.

Если второй пункт пока принят как доверенное предположение, отчёт обязан назвать
его явно. Успешная проверка абстрактного `.vpr` сама по себе не доказывает
корректность allocator, relocation или field lens.

## Обязательная граница первой версии

Первая версия доказывает:

- origin из конкретного экземпляра `layout` и конкретного descriptor;
- живость allocation и logical identity;
- инициализацию каждого читаемого места;
- границы area slot;
- права чтения и записи;
- единственность и линейный перенос `own`;
- отсутствие сильных ссылок на удалённый элемент;
- выполнение cleanup на normal и exceptional путях.

В первую версию не входят:

- конкурентность и memory ordering;
- FFI и raw addresses;
- runtime-open kinds;
- автоматический вывод произвольной достижимости;
- полное доказательство завершения;
- доказательство отсутствия утечек не-владеющих графов, если оно не требуется
  для обязательной безопасности.

## Неподменяемые сущности proof state

Нельзя сводить следующие понятия к одному `Ref` или одному permission:

```text
LayoutInstanceId
DescriptorId
AllocationId
LogicalIdentity
LocationLease(AllocationId, Epoch, Index)
PlaceId
LiveIdentities
LiveAllocations
InitializedPlaces
Own(identity)
Read(place) / Write(place)
```

- `Live` не означает `Initialized`.
- Viper `acc` не означает Efen `own`.
- Logical identity не обязана совпадать с physical row или address.
- Location lease для area блокирует relocation либо становится непригодным при
  смене epoch.
- Потеря последнего `Own` без уничтожения или явной unsafe-операции запрещена.

## Артефакты

Работа должна породить:

1. нормативную таблицу семантики `one`, `set`, `area`, `set area`;
2. контракты всех descriptor operations;
3. ресурсную модель VIR и validator для неё;
4. Viper runtime prelude с закреплённой версией;
5. positive и negative `.efen`, `.vir` и `.vpr` fixtures;
6. таблицу `obligationId → SourceSpan → diagnostic code`;
7. список trusted assumptions для каждого запуска;
8. отдельные refinement proofs representations;
9. отчёт о проверке существующих Array-алгоритмов.

Generated `.vir` и `.vpr` сохраняются для воспроизведения, а не существуют
только как временные файлы теста.

## Этап 0. Зафиксировать семантический вход

До emitter требуется принять внутренние, а не обязательно surface, контракты.

### 0.1. Виды descriptor

Для каждого из `one`, `set`, `area`, `set area` определить:

- вид identity;
- кто владеет allocation;
- как задаются membership и liveness;
- можно ли перемещать physical storage;
- что именно инвалидирует reference, index и location lease;
- какие initialized states допустимы;
- как перечислить живые элементы для drop;
- какие операции меняют membership.

`Items.Item`, полученный отдельным `allocate`, и `Items.Item`, полученный через
`at(area, index)`, не должны неявно считаться одной стабильной identity.

### 0.2. Контракты операций

Для `allocate`, `allocateArea`, `at`, `initialize`, `extract`, `move`,
`reallocateArea` и `free` записать:

- входные ресурсы;
- normal post-state;
- exceptional post-state;
- изменение initialization set;
- изменение membership;
- изменение epoch и судьбу старых leases;
- порядок drop;
- `throws`, возможность suspension и reentrancy;
- требования размера, alignment и арифметики.

Голый `inhale` не является реализацией allocation. До проверяемого source ABI
первый spike использует Viper `new`; затем allocation выдаётся только контрактом
source с линейным allocation token.

### 0.3. Точки наблюдения

Однозначно определить, когда обязаны быть закрыты декларативные условия:

- завершение construction и публикация `self`;
- normal return;
- `throw`;
- suspension/cancellation;
- внешний или reentrant вызов;
- публикация ссылки;
- вход в destructor.

Внутри открытого состояния разрешены только проверенные no-throw, no-suspend и
no-reenter шаги, сохраняющие линейный authority экземпляра layout.

### 0.4. Числа

Каждое действие над `Size` получает одну из политик:

- доказанное отсутствие overflow;
- checked operation с exceptional ребром;
- явно выбранную wrapping-семантику.

Безграничный Viper `Int` нельзя использовать как молчаливую замену `Size`.

Критерий этапа: ни одна VIR-операция не ссылается на незафиксированное значение
слов `identity`, `live`, `own`, `initialized`, `free` или `relocate`.

## Этап 1. Воспроизводимая среда Viper

- закрепить версии Viper/Silicon и их checksums;
- добавить команду запуска с детерминированными timeout и solver settings;
- сохранить минимальные positive и intentionally failing `.vpr`;
- различать verification failure, timeout, crash и unsupported lowering;
- сохранять структурированный результат backend.

Критерий этапа: чистый checkout воспроизводит один успех и один ожидаемый отказ;
timeout не засчитывается как обнаруженная ошибка.

## Этап 2. Ресурсный VIR

VIR строится после всех aspect/metacode transformations и после раскрытия
порядка вычислений, `defer`, normal и exceptional CFG edges.

Минимальные операции:

```text
Allocate
AcquireOwn
MoveOwn
Borrow / EndBorrow
Initialize
Publish
Read / Write
Extract
MovePlace
Retire
Drop
Free
OpenProperty / CloseProperty
Invoke(normal, exceptional)
```

Ресурсные утверждения отделяются от boolean formulas. `Own`, `Read` и `Write`
нельзя дублировать обычным `And`. Каждый `Assume` содержит provenance доверенного
контракта; непомеченный `Assume` отвергает validator.

Frontend, а не SMT solver, окончательно разрешает `OriginId`, `DescriptorId`,
`PlaceId`, законность `take`, lifetime borrow и полный набор cleanup edges.

Критерий этапа: validator отвергает неизвестный origin/place, копирование `Own`,
чтение без initialization, непомеченный `Assume` и выход без обязательного drop.

## Этап 3. Первый вертикальный срез: отдельные стабильные блоки

Первый пример не использует Array:

```efen
layout BoxStore {
    set Boxes: Box

    struct Box {
        var value: Int
    }
}
```

Нужно доказать:

- создание двух разных блоков;
- несколько read aliases одного живого блока;
- запись только с эксклюзивным правом;
- перенос единственного `Own`;
- удаление и exactly-once drop;
- допустимое сравнение сохранённой logical identity после удаления;
- отказ при dereference после удаления;
- отказ при смешении одинаковых типов из двух layout instances;
- отказ при копировании `Own`.

Первый Viper slice использует `new`, отдельный линейный ресурс `Own(box)` и
physical field permission. Простого `box in Live` недостаточно.

Критерий этапа: каждая отрицательная мутация падает на ожидаемом
`obligationId`, а ошибка отображается на исходный Efen `SourceSpan`.

## Этап 4. Сильные отношения и удаление

Добавить nullable strong field и конечное число известных holders. Затем перейти
к произвольному множеству holders через quantified permissions.

Нужно доказать:

- strong target жив;
- overwrite сначала передаёт или уничтожает прежний `Own`;
- удаление невозможно при неочищенном входящем strong edge;
- очистка произвольных holders действительно покрывает всё множество;
- forward и reverse relation, если reverse существует, не расходятся.

Текущий `inverse` из старого Viper-документа не используется как неявная
атомарная операция. Современные взаимные условия открываются на ограниченном
участке, все записи выполняются явно, затем отношение доказывается заново.

Критерий этапа: пропуск одного holder и перестановка одной парной записи дают
отдельные ожидаемые negative failures.

## Этап 5. `area` и фиксированный Contiguous Array

Для area ввести:

```text
AreaId
AreaEpoch
Capacity
Slot(AreaId, AreaEpoch, Index)
InitializedSlots: Set[Index]
AreaOwn
```

`Slot` доказывается инъективным по живым `(AreaId, Epoch, Index)`. Права на
uninitialized slot позволяют запись-конструирование, но не чтение и не drop как
готового значения.

Проверка `contiguous-array.efen` обязана отдельно покрыть:

- состояние `root == null` при нулевой capacity;
- construction boundary до первого пользовательского callback;
- callback `make(index)`, его исключение и cleanup точного initialized prefix;
- публикацию элемента только после полной инициализации;
- равенство `length`, `Items.count` и capacity на выходе;
- `replace` с move-only и потенциально бросающим generic `Target`.

Критерий этапа: constructor доказывается для произвольной точки исключения
callback, а injected double-drop и read-before-init отвергаются.

## Этап 6. DynamicContiguous Array

Сначала доказать `reserve`, затем `append`, затем `insert`, затем `remove`.

### `reserve`

- overflow в `capacity * 2` проверяется до вычисления;
- `newCapacity >= initializedCount`;
- prepare не меняет опубликованный state;
- commit сохраняет порядок значений и membership;
- старые location leases отсутствуют;
- old area освобождается ровно один раз;
- исключение сохраняет прежние root, capacity, length и значения.

### `insert`

Loop invariant содержит точный initialized set с одной движущейся дырой:

```text
initialized = prefix(0, cursor) ∪ suffix(cursor + 1, oldLength + 1)
```

Каждый `move` требует initialized source и empty destination. После цикла
`initialize(index)` закрывает дыру; только затем публикуется новый `length`.

### `remove`

После `extract(index)` дырка движется вправо. Loop invariant доказывает, что
каждый source initialized, destination empty, а извлечённое значение имеет ровно
один `Own`. После последнего move initialized set становится новым префиксом.

Критерий этапа: алгоритмы проходят для `index == 0`, middle, last, empty/full
capacity boundaries; off-by-one, wrong move direction, missing move и overflow
являются negative tests.

## Этап 7. List и DoubleLinkedList

Сначала выбрать доказуемое структурное представление порядка: ghost `Seq` живых
identity либо другой конечный witness. Не кодировать `reachable` рекурсивной
Viper-функцией без доказательства её well-foundedness.

Для односвязного списка доказать:

- `head`, `tail`, `length` соответствуют одной последовательности;
- `next` задаёт её соседние элементы и последний `next == null`;
- owning chain выдаёт ровно один `Own` каждому узлу;
- `itemAt(index)` не разыменовывает `null` для `index < length`;
- append/insert/remove сохраняют sequence и ownership.

Для двусвязного списка дополнительно:

- `prev` является точной обратной связью `next`;
- временное нарушение пары не пересекает observation point;
- direct update `prev` не оставляет старую обратную связь;
- удалённый узел не остаётся целью `prev` или `next`.

Критерий этапа: cycle, lost node, wrong tail, stale `prev`, duplicate owner и
ранний `null` имеют отдельные отрицательные fixtures. Завершение обхода является
отдельным результатом и не подменяет safety.

## Этап 8. Chunked Array

Перед proof алгоритмов добавить отсутствующий cross-descriptor invariant:

```text
Chunks == directory[0..<directoryLength]
Items == union(chunk.root[0..<chunk.length] for chunk in Chunks)
all chunk areas are pairwise disjoint
all non-last used chunks are full
sum(chunk.length) == self.length
```

Нынешних отдельных `Chunks.count` и `Items.count` недостаточно, чтобы доказать,
что `itemAt` выбрал инициализированный slot нужного chunk.

Проверить:

- cleanup блока, выделенного до публикации `Chunk`;
- directory relocation отдельно от relocation item blocks;
- переходы через границу `CHUNK_SIZE`;
- moving hole между соседними chunks;
- нулевой последний chunk после remove и его повторное использование;
- освобождение каждого item block до directory block.

Критерий этапа: доказаны операции на границах `0`, `CHUNK_SIZE - 1`,
`CHUNK_SIZE`, `CHUNK_SIZE + 1`; aliasing двух chunk roots отвергается.

## Этап 9. Refinement representations и columnar storage

Клиентские методы доказываются над абстрактным Population contract. Отдельный
proof конкретного storage связывает его с physical state:

```text
Live
Kind
Common: Identity ↔ CommonRow
Payload[K]: IdentityOfKind(K) ↔ PayloadRow[K]
FieldLocation(Identity, FieldPath)
```

Обязательны bijection, unique physical owner, initialization каждого logical
field, доказанная semantics field lens и preservation при
`create/remove/replace/compact`.

Первый этап columnar verification является closed-world: набор kinds фиксирован
в verification unit. `Borrow`, `Address` и `Stable` являются проверенными
контрактами witness, а не доверенными boolean flags.

Критерий этапа: ложный reverse map, две identity на одну writable row, неверный
kind payload, compaction при живом borrow и lens на чужое поле отвергаются.

## Этап 10. Runtime-open kinds

Этот этап начинается только после closed-world columnar proof. Нужно выбрать и
реализовать одно:

- proof-carrying registration над фиксированным erased descriptor calculus;
- offline verification каждого plugin с совместимым certificate;
- явное включение plugin witness и lifecycle code в TCB.

`CatalogEpoch` является механизмом invalidation, но не доказательством нового
kind. Нельзя объявлять ранее скомпилированный код перепроверенным только потому,
что epoch изменился.

Критерий этапа: plugin с owning field, отсутствующим в drop descriptor, и plugin
с aliasing writable lenses не проходят admission.

## Проверка существующих Array-алгоритмов

Для каждого файла в `layout-examples/` итоговый отчёт содержит:

| Пример | Обязательные proof themes |
|---|---|
| `contiguous-array.efen` | partial construction, callback failure, prefix init, exact drop |
| `dynamic-array.efen` | overflow, relocation, lease invalidation, moving hole, strong exception guarantee |
| `singly-linked-array.efen` | finite order witness, safe traversal, owning chain, tail |
| `doubly-linked-array.efen` | paired relation, temporary invariant opening, stale back edge |
| `chunked-array.efen` | cross-descriptor coverage, disjoint areas, cross-chunk hole, nested cleanup |

Для каждой операции фиксируются:

1. pre-state;
2. требуемые ресурсы;
3. normal post-state;
4. exceptional post-state;
5. loop invariant;
6. observation points;
7. concrete counterexample при ослаблении каждого существенного условия.

Если алгоритм нельзя доказать из текущего layout, это дефект спецификации или
алгоритма, а не повод добавить `assume`.

## Общие критерии приёмки

Этап считается завершённым только если:

- существует реально запущенный `.vpr`, а не схема с `...`;
- positive fixtures проходят Silicon;
- negative fixtures завершаются ожидаемым отказом, а не timeout;
- каждый lowering template имеет mutation test;
- unresolved origin/place и непомеченный `Assume` запрещены validator;
- arithmetic соответствует target width;
- normal, throw и cleanup paths проверены раздельно;
- список trusted assumptions сохранён рядом с результатом;
- proof cache зависит от frontend, transformations, VIR, emitter, prelude,
  representation witness, target и solver versions;
- документация не называет proof дополнительного свойства доказательством
  memory safety и наоборот.

Carbon подключается только как независимая проверка после стабильного Silicon
корпуса. Расхождение backend сохраняется как VIR/Viper reproduction и не
маскируется общим `pass`.

## Порядок выполнения

```text
семантика descriptors
    → Viper toolchain
    → resource VIR
    → stable one-block set
    → strong relations
    → area
    → fixed contiguous Array
    → dynamic contiguous Array
    → singly/doubly linked Array
    → chunked Array
    → closed-world columnar refinement
    → runtime-open registration
```

Переход к следующему этапу запрещён, пока отрицательный корпус текущего этапа
может быть принят из-за `assume`, aliasing location, потерянного `Own`, неверной
инициализации или непроверенного exceptional path.
