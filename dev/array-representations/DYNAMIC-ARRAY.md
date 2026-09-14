# Динамический непрерывный `Array`

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Синтаксис
дескрипторов памяти и их операции ещё не реализованы компилятором.

## Смысл представления

`Array<Target, DynamicContiguous>` хранит существующие элементы подряд, но
различает длину и вместимость. Свободный хвост области не содержит
инициализированных `Target`. При росте представление выделяет новую область,
переносит элементы и освобождает старую.

`Target` — тип элемента. Конкретный массив неявно передаётся аспекту как
`Self`; его текущий экземпляр называется `self`.

## Layout

```efen
aspect DynamicContiguous<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value in self.items
        }

        struct Item {
            Target
        }

        struct Self {
            var items: own Items.Area {
                value.initializedCount == Items.count
            }
        }
    }

    implementation {
        @constructor
        public fn init(capacity: Size = 0) -> Self {
            self.items = Items.allocateArea(capacity: capacity)
            return self
        }

        // Операции приведены ниже.
    }
}
```

`Items.Area` является одной непрерывной областью из `Item`. Её
`capacity` сообщает число выделенных мест, а `initializedCount` — длину
инициализированного префикса. Всегда выполняется:

```text
0 <= initializedCount <= capacity
Items.count == initializedCount
```

`Item` встраивает `Target`. Поэтому место элемента обозначается
`Items.Item`, а встроенное значение — выражением `item.Target`. Обычное поле
`var value: Target` не гарантировало бы inline-размещение и могло бы иметь
косвенную representation.

## Кандидатный интерфейс области

| Операция | Смысл |
|---|---|
| `Items.allocateArea(capacity)` | Подготовить пустую непрерывную область |
| `area.initializeNext(Item(...))` | Инициализировать следующее место префикса |
| `area.initialize(index, Item(...))` | Инициализировать известное пустое место |
| `area.itemAt(index)` | Получить живой `Items.Item` с проверкой границы |
| `area.take(index)` | Перенести `Item` из живого места и оставить его пустым |
| `area.move(from, to)` | Перенести `Item` из инициализированного места в пустое |
| `area.relocateInto(destination)` | Перенести весь префикс в подготовленную область с сохранением identities |
| `area.finish(count)` | Доказать, что после изменения жив ровно префикс `0 ..< count` |
| `Items.free(area)` | Освободить область, не уничтожая уже перенесённые места повторно |

Эти операции принадлежат дескриптору `Items`, потому что именно он определяет,
какие элементы появляются, перемещаются и исчезают. API является кандидатом
общего memory-протокола, а не специальной веткой компилятора для `Array`.

## Основные операции

```efen
aspect DynamicContiguous<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value in self.items
        }

        struct Item {
            Target
        }

        struct Self {
            var items: own Items.Area {
                value.initializedCount == Items.count
            }
        }
    }

    implementation {
        @constructor
        public fn init(capacity: Size = 0) -> Self {
            self.items = Items.allocateArea(capacity: capacity)
            return self
        }

        public fn count -> Size {
            return self.items.initializedCount
        }

        public fn capacity -> Size {
            return self.items.capacity
        }

        fn itemAt(index: Size) -> Items.Item {
            return self.items.itemAt(index)
        }

        fn growthCapacity(minimum: Size) -> Size {
            if minimum <= self.capacity() {
                return self.capacity()
            }

            if self.capacity() == 0 {
                return max(8, minimum)
            }

            return max(
                checkedMultiply(self.capacity(), 2),
                minimum
            )
        }

        public fn reserve(minimum: Size) {
            if minimum <= self.capacity() {
                return
            }

            let nextCapacity = growthCapacity(minimum)
            var pending = Items.allocateArea(capacity: nextCapacity)

            self.items.relocateInto(pending)
            self.items.finish(0)

            let previous = take self.items
            self.items = take pending
            Items.free(take previous)
        }

        public fn read(index: Size) -> Target
            where Target: Copyable
        {
            return itemAt(index).Target
        }

        public fn replace(
            index: Size,
            value: own Target
        ) -> Target {
            let item = itemAt(index)
            let previous = take item.Target
            item.Target = take value
            return take previous
        }

        public fn append(value: own Target) {
            let nextCount = checkedAdd(self.count(), 1)
            reserve(nextCount)
            self.items.initializeNext(Item(take value))
        }

        public fn insert(index: Size, value: own Target) {
            if index > self.count() {
                throw BoundsError(index, self.count())
            }

            let nextCount = checkedAdd(self.count(), 1)
            reserve(nextCount)

            var cursor = self.count()
            while cursor > index {
                self.items.move(cursor - 1, cursor)
                cursor -= 1
            }

            self.items.initialize(index, Item(take value))
            self.items.finish(nextCount)
        }

        public fn remove(index: Size) -> Target {
            let oldCount = self.count()

            if index >= oldCount {
                throw BoundsError(index, oldCount)
            }

            let removed = self.items.take(index)
            var cursor = index

            while cursor + 1 < oldCount {
                self.items.move(cursor + 1, cursor)
                cursor += 1
            }

            self.items.finish(oldCount - 1)
            return take removed.Target
        }
    }
}
```

В `reserve` сначала проверяются размеры и выделяется `pending`. Затем
существующие `Item` переносятся без копирования `Target`. До публикации могут
существовать две `Items.Area` одного дескриптора; условие, связывающее все
`Items` с `self.items`, временно открыто. После присваивания `self.items`
старая область пуста и может быть освобождена.

Точная операция переноса всего префикса может быть оптимизирована memory-
протоколом. Для нетривиального `Target` это семантический move, а не
безусловный `memcpy`.

## Сдвиги

Вставка идёт справа налево, поэтому назначение каждого шага ещё пусто:

```text
[A B C _] -> [A B _ C] -> [A _ B C] -> [A X B C]
```

Удаление сначала изымает элемент, затем сдвигает суффикс слева направо:

```text
[A B C D] -> [A _ C D] -> [A C _ D] -> [A C D _]
```

Компилятор отслеживает инициализированность каждого затронутого места. Операция
обязана закончить с одним непрерывным префиксом; читать пустое место или
перезаписать живой `Target` нельзя.

## Исключения и заимствования

Проверка индекса, арифметика вместимости и выделение выполняются до необратимого
изменения. После начала переноса код не бросает исключений, не приостанавливается
и не вызывает пользовательский код. Это требует проверяемого контракта
перемещения и уничтожения `Target`.

Живая ссылка на `item.Target` блокирует `reserve`, вставку и удаление, потому
что они способны переместить элемент или заменить его место.

## Стоимость

- `count`, `capacity`, индексирование, чтение и замена: `O(1)`;
- `append`: амортизированно `O(1)`, при росте `O(count)`;
- `insert` и `remove`: `O(count - index)`;
- `reserve`: `O(count)`, если требуется новая область.

## Граница предложения

`Items.Area` и операции частичной инициализации являются кандидатным общим
memory API. Нужно отдельно закрепить их точные сигнатуры, exceptional contracts
и правила сохранения logical identity при relocation.
