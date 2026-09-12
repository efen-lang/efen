# Колоночные layout

`layout` может представлять обычные логические структуры несколькими
физическими хранилищами. Код работает с полями структуры, а layout отображает
логическую идентичность и путь поля в column, строку или другой storage.

Эта возможность не создаёт новый вид структуры и не меняет единственную
representation самостоятельного значения. Она задаёт storage projection для
населения конкретного экземпляра layout.

## Однородная колоночная структура

```efen
struct Particle {
    var position: Vec3
    var velocity: Vec3
    var mass: Float
}

layout World {
    source memory: Arena
    set Particles: Particle from memory

    storage columns for Particles {
        representation Columnar<Particle>
    }
}
```

`storage` — член layout, связывающий одно население с его физическим
хранилищем. `Columnar` — обычная compile-time representation этого storage, а
не keyword и не вторая representation `Particle`.

```text
storage Name for Population [from Source] {
    representation RepresentationExpression
}
```

`storage` является контекстным словом только в позиции члена layout. Имя
населения разрешается среди `set` того же layout; допустима ровно одна активная
storage binding. Явный `from Source` переопределяет источник населения, иначе
используется источник его `set`. Тело содержит одну representation-директиву.

`Columnar<Common>` — обычная generic-реализация compile-time контракта storage
representation. Она получает `PopulationSchema` и строит типизированный
`StoragePlan`: physical stores, отображения, field lenses, lifecycle,
enumerations и snapshot decoder. Другая библиотечная реализация того же
контракта может группировать несколько полей в AoS-store, отделять hot/cold
части или применять иной план без новой грамматики.

Логически программа видит:

```text
Particle { position, velocity, mass }
```

Физически `columns` может хранить:

```text
identities[]
positions[]
velocities[]
masses[]
```

Доступ `particle.position` является доступом к логическому месту. Он не требует,
чтобы целый `Particle` существовал одним непрерывным блоком памяти.

## Общая часть и отдельные виды

Структуры используют обычное встраивание Efen:

```efen
struct BaseNode {
    var type: Type
    var source: SourceRange
}

struct Function {
    BaseNode

    var parameters: [Parameter]
    var result: Type
    var body: HirNodeId
}

struct Call {
    BaseNode

    var callee: HirNodeId
    var arguments: [HirNodeId]
}
```

Layout HIR может связать общее население с открытым семейством storage:

```efen
layout HirStorage {
    source memory: Arena
    set Nodes: Family<BaseNode> from memory

    storage columns for Nodes {
        representation Columnar<BaseNode>
    }
}
```

`Family<BaseNode>` — обычный библиотечный открытый tagged carrier, а не
наследование структур. Вид допускается, если он является точным `BaseNode` либо
непосредственно содержит ровно одно встраивание точного `BaseNode` и предоставляет
проверенный storage witness. Structural matching, coercion и транзитивный поиск
embedding не выполняются. Конкретная generic-инстанциация является отдельным
видом; opaque-владелец создаёт witness внутри разрешённой reveal-области.
Точный `BaseNode` использует само значение как common fragment и не создаёт
payload. Для остальных видов требуется ровно одно непосредственное embedding.

`Columnar<BaseNode>` хранит поля единственного встроенного `BaseNode` в общих
columns, а остальные поля каждого зарегистрированного логического вида — в его
собственном payload storage:

```text
directory
    identity -> live, kind, commonRow, payloadRow

common columns
    types[]
    sources[]
    commonOwners[]

Function payload
    parameters[]
    results[]
    bodies[]
    functionOwners[]

Call payload
    callees[]
    arguments[]
    callOwners[]
```

Прямое и обратное отображения обязательны. По `HirNodeId` находится payload, а при
плотном обходе `Function` по payload-строке восстанавливается исходный `HirNodeId`
и общая часть. `swap-remove` согласованно обновляет обе стороны.

## Обычный API и динамические виды

Новый вид HIR остаётся обычной структурой Efen:

```efen
use amber

struct SqlQuery {
    BaseNode

    var sql: String
    var arguments: [HirNodeId]
    var result: Type
}
```

Обычный API создаёт значение и возвращает новую логическую идентичность:

```efen
let query: HirNodeId = hir.nodes.create(
    SqlQuery(
        type: queryType,
        source: querySource,
        sql: text,
        arguments: arguments,
        result: resultType
    )
)
```

Для именованного `value` без `take` применима копирующая перегрузка и требуется
`Copyable`; `create(take value)` и owning temporary потребляют значение. Hidden
field-by-field copy или move не меняет порядок init/drop и не скрывает эффекты и
`throws`. После принятого `take` ошибка не восстанавливает исходную переменную,
а уничтожает ещё не перенесённые ресурсы ровно один раз.

При первом `create(SqlQuery)` implementation `Columnar` получает declaration и
retained `StorageWitness`, регистрирует kind и лениво создаёт его payload
storage. Существующие `HirNodeId` и физические stores других видов не
перестраиваются.
Пользователь не распределяет kind ID, не создаёт payload table и не работает с
runtime `StoreFamily` напрямую.

Witness содержит nominal identity, common embedding, descriptors полей,
physical storage plan, прямые и обратные mappings, field capabilities,
initialize/move/drop operations и декларативный decoder. Он принадлежит storage
и живёт до уничтожения последнего payload своего вида. Semantic analysis или
lowering handler можно отключить отдельно; lifecycle hooks и decoder живого
storage выгружать нельзя.

Это обычное поведение generic API storage. Оно не является специальным
синтаксисом HIR: другая библиотека может использовать тот же подход для AST,
ECS или базы данных.

## Формальная модель

Для каждого опубликованного состояния существуют:

```text
Live: Set<Identity>
Kind: Live -> kind_catalog
Common: Live <-> CommonRows
Payload[K]: { id in Live | Kind(id) == K } <-> PayloadRows[K]
```

Прямые и обратные отображения являются взаимно обратными. Каждая опубликованная
физическая строка имеет ровно одного логического владельца, каждая живая
идентичность — ровно одну общую строку и необходимый payload своего вида.

Физическая строка не является identity. `compact` и `swap-remove` могут менять
координаты, не меняя логическую идентичность и origin. Для HIR `HirNodeId`
выдаётся монотонно и не переиспользуется в пределах storage; исчерпание его
пространства завершает создание ошибкой. Другой layout может выбрать recycling
identity с поколением, но не вправе допустить wrap, оживляющий старую ссылку.

## Операции

`create`, `remove`, `replace` и `compact` являются транзакциями на наблюдаемых
границах операций, а не обещанием lock-free машинной атомарности.

Каждая операция разделена на fallible prepare, no-throw commit и no-throw
cleanup. Prepare может выделять память, проверять witness и создавать
provisional fragments, не меняя опубликованные roots, `Live` и mappings. Commit
не бросает, не приостанавливается, не вызывает reentrant пользовательский код и
не выполняет allocation. Cancellation применяется только на согласованной
границе. Drop после commit также не бросает и не входит повторно в тот же layout.

`create`:

1. резервирует capacity всех необходимых stores;
2. получает ещё не опубликованную identity;
3. инициализирует common и payload fragments;
4. устанавливает прямые и обратные отображения;
5. публикует identity в `Live`.

Ошибка до публикации уничтожает только уже созданные поля и оставляет
опубликованное состояние прежним. Внешние побочные эффекты произвольного кода
автоматически не откатываются.

`remove` требует write authority населения и предусмотренное его контрактом
владение и допускается только при отсутствии конфликтующих заимствований. Для
обычного owning population это может быть потребляемый owner; `HirNodeId` сам по
себе является identity, а не владельцем, поэтому HIR API использует отдельное
право преобразования storage. Все fallible действия завершаются до commit;
затем операция исключает identity из `Live`, исправляет отображения и уничтожает
каждое логическое поле ровно один раз. Операция не может принудительно закончить
чужой loan.

`replace(identity, value)` может изменить конкретный вид с сохранением logical
ID. Для owning population она потребляет прежнего типизированного владельца; для
HIR выполняется под write authority текущего `HirViewId`. Операция заранее
строит новые common и payload fragments, затем no-throw commit меняет kind и обе
карты. Ошибка prepare сохраняет старое значение и authority; старая полная
версия уничтожается после commit. Публичной записи в `kind` нет.

`compact` сохраняет значения, membership и identity. Он либо готовит private
replacement stores и публикует их no-throw заменой, либо выполняет доказанные
перемещения с восстановлением обеих сторон отображений после каждого commit.

## Доступ, ссылки и `managed`

Скрытые backing columns могут находиться в `managed`-слотах. Этот режим не
переходит на публичные projected places.

Логическая ссылка на элемент содержит origin экземпляра layout, identity,
права и при необходимости доказанный вид. Ссылка на поле дополнительно хранит
логический field path. Она не обязана быть машинным адресом.

Обычные операции чтения и записи реализуются field lens. Логическое
`&read[origin] T`, `&[origin] T` или `&out[origin] T` требует capability
`Borrow` соответствующего режима, но не обязано быть машинным адресом. Живое
заимствование блокирует конфликтующие `remove`, `replace` и `compact`.
Временная AoS-копия скрыто не материализуется.

Bit-packed, dictionary и другие addressless columns могут поддерживать чтение и
запись через lens, не поддерживая `Borrow`. Переход к `raw T` для FFI отдельно
требует `Address + Stable`: физический слот нужного типа и сохранение его адреса
до конца loan.

## Обход

Storage предоставляет разные логические обходы без создания промежуточного
массива:

```efen
for node in Nodes { ... }
for function in Nodes.of<Function>() { ... }
for base in Nodes.fields<BaseNode>() { ... }
```

`Nodes.of<T>()` возвращает `KindView<T, Nodes>`; его читающий cursor выдаёт
`&read[Nodes] T`. `Nodes.fields<BaseNode>()` возвращает
`FieldView<BaseNode, Nodes>` с элементами `&read[Nodes] BaseNode` и использует
общие columns. Оба view сохраняют identity и origin исходного населения, не
копируют значения и не создают нового населения.

`of<Function>()` использует плотный payload storage и обратных владельцев;
`fields<BaseNode>()` использует общие columns. Изменяемый cursor возможен только
при write-доступе и соответствующем `Borrow` capability.
Порядок не является свойством неупорядоченного `set`; канонический порядок для
сериализации задаётся отдельно.

## Версии и сериализация

HIR history и `HirViewId` разрешают значения по logical ID и revision, а не по
текущей физической строке. Изменение текущего payload не изменяет старый view;
история сохраняет согласованные прежние fragments и отображения. Сама compaction
не создаёт семантическую revision.

Логический snapshot записывает значения и identities и при загрузке может
выбрать другую физическую storage projection. Физический snapshot для mmap
дополнительно содержит:

- kind и store catalogs;
- common и payload tables;
- прямые и обратные отображения;
- identity policy и необходимое generation state;
- field-to-store plan;
- representation и codec parameters.

Writer канонически упорядочивает descriptors и logical identities и remap-ит в
выходном потоке kind/store codes, logical IDs, все ссылки на них, координаты,
исторические версии и обратных владельцев. Порядок загрузки расширений и
расположение строк рабочего storage не меняют байты одного логического snapshot.

Bootstrap row snapshot, columnar physical mmap snapshot и logical serialization
являются разными versioned profiles. Columnar-файл нельзя отображать как массив
24-байтовых bootstrap `HirNode`. Header выбирает profile и revision; перед
добавлением в доверенный cache reader проверяет catalogs, decoder, bounds,
coverage и обе стороны всех mappings.

## Проверяемые ошибки

Компилятор отвергает:

- производный вид без единственного совместимого непосредственного embedding
  общей структуры;
- kind без действительного retained `StorageWitness`;
- две physical storage bindings одного населения;
- потерянную или дважды покрытую строку/колонку;
- несогласованные forward и reverse mappings;
- чтение поля через payload другого вида;
- физическое перемещение при живом конфликтующем заимствовании;
- логическое заимствование без `Borrow` и raw-адрес без `Address + Stable`;
- generation wrap, способный оживить старую identity;
- анализ или lowering вида без требуемой активной capability.

## Дальнейшие формы

Тот же контракт identity, mappings, lenses и transitions позволяет библиотечным
representations реализовать:

- AoSoA и tiled/PAX storage;
- hot/cold splitting и nullable columns;
- sparse sets и ECS archetypes;
- chunked, segmented и slab storage;
- bit-packed, dictionary, RLE и delta columns;
- inline/boxed и adaptive layouts;
- row-major, column-major и Morton mappings;
- host/device и GPU address spaces.

AoSoA требует размера tile и tail-mask; compressed columns — addressless lenses
и явных эффектов rebuild; ECS — миграции между archetypes; GPU — отдельной
модели address spaces и coherence; adaptive storage — versioned migration.
Поэтому они являются расширениями общего API, а не отдельными keywords языка.

Обзор этих форм, общих primitives и порядка реализации находится в
[исследовании physical storage](layout-representations.md).

## Границы реализации

Документ задаёт семантику языка и layout API. Parser, generated accessors,
runtime storage, verifier, lowering и physical snapshot ещё должны быть
реализованы и проверены вертикальными тестами.
