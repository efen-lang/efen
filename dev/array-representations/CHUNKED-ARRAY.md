# `Array` из блоков фиксированного размера

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Синтаксис
дескрипторов памяти и их операции ещё не реализованы компилятором.

## Смысл представления

`Array<Target, Chunked>` хранит элементы в непрерывных блоках по 256 мест.
Сами блоки не перемещаются при росте каталога. Логический индекс раскладывается
на номер блока и смещение:

```text
chunk  = index / 256
offset = index % 256
```

`Target` — тип элемента. Конкретный массив неявно входит в аспект как `Self`,
а текущий экземпляр называется `self`.

## Два уровня памяти

```efen
aspect Chunked<Target> conforms Representation<Target> {
    const CHUNK_SIZE: Size = 256

    layout {
        set Items: Item

        set Chunks: Chunk {
            value in self.directory
        }

        struct Item {
            Target
        }

        struct Chunk {
            var block: own Items.Area {
                value.capacity == CHUNK_SIZE
            }
        }

        struct Self {
            var directory: own Chunks.Area

            var length: Size = 0 {
                value == Items.count
                value <= self.directory.count * CHUNK_SIZE
            }
        }
    }

    implementation {
        // Операции приведены ниже.
    }
}
```

`Items` описывает элементы массива. Каждый `Chunk.block` владеет отдельной
непрерывной `Items.Area`. `Chunks` описывает записи каталога, а
`self.directory` владеет непрерывной `Chunks.Area` с этими записями.

Так layout различает:

- логические элементы `Items.Item`;
- физические области элементов `Items.Area`;
- записи каталога `Chunks.Item`;
- непрерывную область каталога `Chunks.Area`.

В зарезервированных блоках могут оставаться неинициализированные места.
`Items.count` считает только живые `Item`, поэтому совпадает с
`self.length`, а не с общей вместимостью.

Одних типов полей для этого недостаточно. Условия layout должны также задавать
следующий точный закон. Для каждого индекса блока `i`:

```text
block[i].initializedCount =
    min(CHUNK_SIZE, max(0, self.length - i * CHUNK_SIZE))
```

Все `Items` являются ровно инициализированными местами этих блоков, а других
живых `Items` нет. `self.directory.count` означает число инициализированных
записей `Chunk`, а не capacity области каталога. Точный декларативный surface-
синтаксис квантора по блокам пока открыт; без этого закона приведённый layout
не считается законченным доказательным контрактом.

`Item` встраивает `Target`. Обычное поле `var value: Target` могло бы иметь
косвенную representation; голое `Target` требует разместить его внутри
`Item`. Доступ к значению выполняется через `.Target`.

## Доступ к позиции

```efen
implementation {
    const CHUNK_SIZE: Size = 256

    @constructor
    public fn init -> Self {
        self.directory = Chunks.allocateArea(capacity: 0)
        return self
    }

    struct Position {
        let chunk: Size
        let offset: Size
    }

    fn position(index: Size) -> Position {
        return Position(
            chunk: index / CHUNK_SIZE,
            offset: index % CHUNK_SIZE
        )
    }

    fn chunkAt(index: Size) -> Chunks.Item {
        return self.directory.itemAt(index)
    }

    fn itemAt(index: Size) -> Items.Item {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }

        let place = position(index)
        return chunkAt(place.chunk).block.itemAt(place.offset)
    }

    public fn count -> Size {
        return self.length
    }

    public fn read(index: Size) -> Target
        where Target: Copyable
    {
        return itemAt(index).Target
    }

    public fn replace(index: Size, value: own Target) -> Target {
        let item = itemAt(index)
        let previous = take item.Target
        item.Target = take value
        return take previous
    }

    public fn borrowRead(index: Size) -> &read[self] Target {
        return &read[self] itemAt(index).Target
    }
}
```

Ни логический код массива, ни вызывающий код не вычисляют байтовый адрес.
`Chunks.Area.itemAt` и `Items.Area.itemAt` проверяют соответствующие границы
и возвращают handles своих дескрипторов.

## Резервирование блоков

```efen
fn chunkCount(elementCount: Size) -> Size {
    if elementCount == 0 {
        return 0
    }

    return 1 + (elementCount - 1) / CHUNK_SIZE
}

fn reserve(minimum: Size) {
    let required = chunkCount(minimum)

    if required <= self.directory.count {
        return
    }

    var prepared = PreparedChunks()
    var count = self.directory.count

    while count < required {
        prepared.append(
            Items.allocateArea(capacity: CHUNK_SIZE)
        )
        count += 1
    }

    self.growDirectoryFor(prepared.count)

    for block in take prepared {
        self.directory.initializeNext(
            Chunk(block: take block)
        )
    }
}
```

`PreparedChunks` является обычным локальным владельцем ещё не опубликованных
`Items.Area`. Если одно из выделений завершается ошибкой, он освобождает только
новые блоки. Старый каталог и старые элементы не меняются.

Если самой `Chunks.Area` не хватает места, `growDirectoryFor` сначала
выделяет новую область каталога, затем переносит в неё структуры `Chunk`.
Переносятся только владельцы `Items.Area`; сами `Target` остаются в прежних
блоках.

Каталог растёт геометрически, иначе последовательность добавлений могла бы
переносить все записи каталога при каждом новом блоке:

```efen
fn growDirectoryFor(additional: Size) {
    let required = checkedAdd(self.directory.count, additional)

    if required <= self.directory.capacity {
        return
    }

    let doubled = checkedMultiply(self.directory.capacity, 2)
    let nextCapacity = max(required, max(4, doubled))
    var pending = Chunks.allocateArea(capacity: nextCapacity)

    self.directory.relocateInto(pending)
    self.directory.finish(0)

    let previous = take self.directory
    self.directory = take pending
    Chunks.free(take previous)
}
```

После успешной подготовки публикация не бросает исключений, не
приостанавливается и не вызывает пользовательский код.

## Добавление

```efen
public fn append(value: own Target) {
    let nextLength = checkedAdd(self.length, 1)
    reserve(nextLength)

    let destination = position(self.length)
    chunkAt(destination.chunk).block.initializeNext(
        Item(take value)
    )

    self.length = nextLength
}
```

Новый `Target` переносится непосредственно в свободное место последнего блока.
Если нужен новый блок или рост каталога, вся способная завершиться ошибкой
подготовка происходит до изменения `self.length`.

## Вставка и удаление

Вставка резервирует место, затем переносит элементы справа налево по логическим
позициям. Переход через границу блока использует те же `Items.Item`, что
переход внутри блока:

```text
[A B C D] [E _ _ _]
[A B C D] [_ E _ _]
[A B C _] [D E _ _]
[A B _ C] [D E _ _]
[A B X C] [D E _ _]
```

Удаление сначала изымает `itemAt(index).Target`, затем переносит суффикс слева
направо и уменьшает инициализированный префикс последнего блока. Пустой
зарезервированный блок может остаться в каталоге; явная операция уменьшения
capacity вправе освободить его позже.

Каждый move требует инициализированный источник и пустое назначение. Компилятор
проверяет это по состоянию мест `Items.Area`, включая переходы между двумя
областями.

Перенос `Target`, обновление служебных полей и освобождение уже опустошённой
area в таком окне не бросают исключений, не приостанавливаются и не вызывают
наблюдающий код. Иначе частично сдвинутый общий префикс мог бы стать видимым.

## Срезы и итераторы

Срез хранит ссылку на исходный `Self` и полуинтервал логических индексов. Он не
копирует блоки. Итератор может хранить следующий логический индекс и вызывать
`itemAt`; деление на 256 и остаток являются `O(1)`.

Живой borrow элемента удерживает соответствующую `Items.Area`. Рост каталога
его не нарушает, потому что Target-блок не перемещается. Удаление, сдвиг или
освобождение самого блока требуют окончания конфликтующего borrow.

## Стоимость

- индексирование, чтение и замена: `O(1)`;
- обход: `O(count)`;
- добавление: амортизированно `O(1)`;
- вставка и удаление: `O(count - index)`;
- рост каталога: `O(numberOfChunks)`, без переноса `Target`.

## Граница предложения

`Items.Area`, `Chunks.Area`, `PreparedChunks` и операции частично
инициализированных областей являются кандидатами общего memory API. Точные
контракты создания, переноса, освобождения и сохранения identity ещё необходимо
закрепить.
