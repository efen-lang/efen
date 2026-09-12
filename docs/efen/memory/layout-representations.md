# Варианты physical storage для layout

> Статус: исследование и план расширения. Нормативный MVP описан в
> [колоночных layout](columnar-layouts.md).

Разные layout-формы не требуют отдельных языковых сущностей. Их можно собрать
из небольшого набора общих механизмов:

1. независимая logical identity элемента;
2. обычные physical stores со своими representations;
3. отображение identity в physical coordinate;
4. field lens с объявленными возможностями чтения, записи и адреса;
5. поддерживаемые прямые и обратные отношения между stores;
6. транзакции `create`, `remove`, `replace`, `compact` и migration;
7. отдельные logical, kind-specific, physical и canonical enumerations.

`layout` связывает identities и stores. `representation` определяет физическую
форму каждого store. Поэтому `columnar`, `ecs`, `compressed` и `gpu` не являются
новыми видами логической структуры.

## Формы, выражаемые общей моделью

| Форма | Составляющие | Главный контракт |
|---|---|---|
| AoS | один row store | целый элемент может иметь адрес до relocation |
| SoA | field columns с общей координатой | единые membership, length и initialization |
| AoSoA / tiled / PAX | `(tile, lane)` и columns внутри tile | размер tile, alignment и tail mask |
| Hot/cold split | обязательный hot store и полный либо partial cold store | отсутствующий cold fragment должен быть optional/defaulted |
| Split-by-kind HIR | common store, kind, per-kind payload и reverse owner | kind соответствует payload, обе карты образуют биекцию |
| Sparse set | stable ID, sparse→dense и dense→ID | swap-remove обновляет обе стороны |
| ECS archetypes | ID→`(archetype, chunk, row)` и component columns | смена компонентов мигрирует entity целиком |
| Nullable column | validity bitmap и payload | validity публикуется после init и очищается до drop |
| Bit-packed | bit coordinate и codec | обычного `&field` нет; concurrent write требует atomic RMW или shard |
| Dictionary/RLE/delta | indices/runs и codec state | write может перестроить encoding и обязан публиковать новый согласованный state |
| Offset/index graph | base/origin и относительная coordinate | bounds, membership и liveness проверяются до dereference |
| Chunked/segmented/slab | directory и `(segment, offset)` | сегменты могут сохранять адреса только пока сами не перемещаются |
| Generational handles | `(slot, generation)` | generation не может wrap с повторным признанием старой identity |
| Stable ID + indirection | ID→location и packed values | compaction меняет location, а cached coordinate требует epoch |
| Inline/boxed | discriminator и inline bytes либо handle | spill конфликтует с живыми subobject borrows |
| Adaptive/hybrid | authoritative state, alternate stores и migration epoch | нельзя иметь две независимые writable копии |
| Matrix layouts | affine strides, row/column-major или tiled coordinates | transpose-view меняет mapping, physical transpose является mutation |
| Morton/vEB | shape-dependent rank mapping | locality покупается дорогой mutation и отсутствием stable address |
| GPU storage | address-space source и execution visibility | host/device/workgroup ссылки имеют разные scopes и coherence |

Практические модели подтверждают разложение на эти primitives:

- [Cabana AoSoA](https://kokkos.org/kokkos-core-wiki/usecases/SoA-and-AoSoA-with-Cabana.html)
  использует массив фиксированных SoA-блоков с vector length и field slices;
- [PAX](https://www.pdl.cmu.edu/ftp/Database/pax.pdf) группирует поля внутри
  страницы, сохраняя части строки в одном page-domain;
- [Apache Arrow](https://arrow.apache.org/docs/format/Columnar.html) представляет
  struct через child arrays, dense union через type IDs, offsets и отдельные
  child arrays, а nullability — validity bitmap;
- [Sparse sets](https://www.dcs.gla.ac.uk/~pat/ads2/papers/sparseSets.pdf)
  используют взаимные sparse/dense отображения;
- [FlatBuffers](https://flatbuffers.dev/internals/) показывает переносимые
  графы на offsets вместо process pointers;
- [LLVM BumpPtrAllocator](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Support/Allocator.h)
  использует последовательность slabs вместо одного растущего блока;
- [Parquet encodings](https://parquet.apache.org/docs/file-format/data-pages/encodings/)
  отделяют dictionary/RLE/bit-pack encoding от логического типа значения;
- [CUDA](https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html)
  и [SPIR-V](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html)
  требуют явно различать address spaces и области видимости памяти.

Ближайшая общая языковая работа —
[SHAPES](https://drops.dagstuhl.de/storage/00lipics/lipics-vol166-ecoop2020/LIPIcs.ECOOP.2020.31/LIPIcs.ECOOP.2020.31.pdf):
placement отделяется от обычной объектной программы при сохранении identity и
type safety. Efen распространяет эту границу на partial joins, variants,
compressed fields и программируемые transitions.

## Field lens и возможности

Логический доступ не всегда может вернуть машинный адрес. Representation или
storage предоставляет операции и capabilities:

```text
read(identity, field) -> T
write(identity, field, T)
borrow(identity, field) -> ref T    // логический origin-bound lens

Readable
Writable
Address
Stable
AtomicElementWrite
BatchReadable
ZeroCopySerializable
RequiresRebuildOnWrite
```

`Borrow` и `Address` — разные возможности. Bit-packed поле может быть
`Readable + Writable`, но не поддерживать передаваемый `Borrow`; логическая
ссылка при наличии `Borrow` всё равно не обязана быть машинным адресом.
Dictionary column может требовать rebuild при записи. `raw`, `offsetof` и C ABI
требуют отдельно `Address + Stable`.

## Несовместимые обещания

Без дополнительного механизма нельзя одновременно гарантировать:

- columnar/compressed row и обычный raw `&WholeStruct`;
- compaction и identity, равную physical index или address;
- bit-packed field и независимый writable `&field`;
- stable subobject address и inline→boxed spill;
- несколько independently mutable columns и инвариант структуры без общей
  transaction boundary;
- плотный per-kind обход без reverse payload→owner mapping;
- повторное использование slot и вечную freshness при generation wrap;
- две host/device replicas и запись без coherence protocol;
- immutable compressed main store и произвольный in-place update;
- runtime-адаптацию storage и исторический view без epoch/version.

## Порядок реализации

### MVP

- logical identity и origin;
- total/partial bidirectional mappings;
- row/column storage groups;
- field lenses и `Address`/`Stable` capabilities;
- транзакционные `create`, `remove`, `replace`, `compact`;
- logical, kind-specific, physical и canonical enumeration;
- HIR common columns и динамические per-kind payload stores;
- logical serializer и проверяемый physical snapshot.

Это покрывает AoS, SoA, basic hot/cold, split-by-kind, nullable columns,
offset references, chunked stores и базовый sparse set.

### После MVP

- AoSoA/PAX tiling;
- полноценные sparse/dense handles и exhaustion policy;
- ECS archetype migration;
- bit-packed, dictionary, RLE и delta representations;
- inline/boxed transitions;
- GPU sources и address-space references.

### Позже

- adaptive regrouping по workload;
- compressed main + mutable delta;
- concurrent background repack;
- replicated host/device layouts;
- Morton/vEB/cache-oblivious dynamic storage.

Эти формы остаются библиотечными representations и storage implementations.
Новые keywords нужны только тогда, когда существующие typed stores, mappings,
lenses и transitions не способны выразить необходимый контракт.
