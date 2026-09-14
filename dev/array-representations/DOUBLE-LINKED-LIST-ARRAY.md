# `Array` в виде двусвязного списка

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Это эскиз языка и
memory API, а не программа для существующего компилятора.

## Смысл представления

`Array<Target, DoubleLinkedList>` хранит каждый элемент в отдельном узле.
`next` задаёт логический порядок массива, а `prev` позволяет начинать поиск с
ближайшего конца.

- прямой и обратный обход: `O(count)`;
- поиск позиции: `O(min(index + 1, count - index))`;
- добавление после найденного узла: `O(1)`;
- адрес узла не является логическим индексом.

`Target` — тип элемента. Конкретный массив неявно входит в аспект как `Self`,
а его текущий экземпляр называется `self`.

## Layout

```efen
aspect DoubleLinkedList<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value reachable from self.head by Item.next
        }

        struct Item {
            Target

            var prev: read other Items.Item? = null {
                if value != null {
                    value.next == self
                }
            }

            var next: own other Items.Item? = null {
                if value != null {
                    value.prev == self
                }
            }
        }

        struct Self {
            var head: own Items.Item? = null {
                if value != null {
                    value.prev == null
                }
            }

            var tail: read Items.Item? = null {
                (self.head == null) == (value == null)

                if value != null {
                    value reachable from self.head by Item.next
                    value.next == null
                }
            }

            var length: Size = 0 {
                value == Items.count
            }
        }
    }

    implementation {
        @constructor
        public fn init -> Self {
            self.head = null
            self.tail = null
            self.length = 0
            return self
        }

        // Операции приведены ниже.
    }
}
```

`set Items: Item` — дескриптор памяти узлов. `Items.allocate` создаёт
`own Items.Item`, а `Items.free` принимает владеющий handle отсоединённого
узла.

`Target` встроен в начало `Item`. Выражение `item.Target` обозначает всё
встроенное место. Обычное поле `var value: Target` могло бы иметь косвенную
representation и не давало бы обещания inline-размещения.

В условиях полей `Item` имя `self` означает текущий узел. В условиях
`struct Self` оно означает текущий массив. Условия `prev` и `next`
декларативно задают взаимную согласованность обеих связей.

## Основные операции

```efen
aspect DoubleLinkedList<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value reachable from self.head by Item.next
        }

        struct Item {
            Target

            var prev: read other Items.Item? = null {
                if value != null {
                    value.next == self
                }
            }

            var next: own other Items.Item? = null {
                if value != null {
                    value.prev == self
                }
            }
        }

        struct Self {
            var head: own Items.Item? = null {
                if value != null {
                    value.prev == null
                }
            }

            var tail: read Items.Item? = null {
                (self.head == null) == (value == null)

                if value != null {
                    value reachable from self.head by Item.next
                    value.next == null
                }
            }

            var length: Size = 0 {
                value == Items.count
            }
        }
    }

    implementation {
        @constructor
        public fn init -> Self {
            self.head = null
            self.tail = null
            self.length = 0
            return self
        }

        fn itemAt(index: Size) -> Items.Item {
            if index >= self.length {
                throw BoundsError(index, self.length)
            }

            if index <= self.length / 2 {
                var current = self.head!
                var position: Size = 0

                while position < index {
                    current = current.next!
                    position += 1
                }

                return current
            }

            var current = self.tail!
            var position = self.length - 1

            while position > index {
                current = current.prev!
                position -= 1
            }

            return current
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

        public fn append(value: own Target) {
            let nextCount = checkedAdd(self.length, 1)
            let item = Items.allocate(
                Item(
                    take value,
                    prev: self.tail,
                    next: null
                )
            )

            if self.tail == null {
                self.head = take item
                self.tail = self.head
            } else {
                self.tail!.next = take item
                self.tail = self.tail!.next
            }

            self.length = nextCount
        }

        public fn insert(index: Size, value: own Target) {
            if index > self.length {
                throw BoundsError(index, self.length)
            }

            if index == self.length {
                append(take value)
                return
            }

            let nextCount = checkedAdd(self.length, 1)

            if index == 0 {
                let item = Items.allocate(
                    Item(
                        take value,
                        prev: null,
                        next: null
                    )
                )

                item.next = take self.head
                item.next!.prev = item
                self.head = take item
                self.length = nextCount
                return
            }

            let before = itemAt(index - 1)
            let item = Items.allocate(
                Item(
                    take value,
                    prev: before,
                    next: null
                )
            )

            item.next = take before.next
            item.next!.prev = item
            before.next = take item
            self.length = nextCount
        }

        public fn remove(index: Size) -> Target {
            if index >= self.length {
                throw BoundsError(index, self.length)
            }

            var victim: own Items.Item

            if index == 0 {
                victim = take self.head!
                self.head = take victim.next

                if self.head == null {
                    self.tail = null
                } else {
                    self.head!.prev = null
                }
            } else {
                let before = itemAt(index - 1)
                victim = take before.next!
                before.next = take victim.next

                if before.next == null {
                    self.tail = before
                } else {
                    before.next!.prev = before
                }
            }

            self.length -= 1

            let result = take victim.Target
            Items.free(take victim)
            return take result
        }
    }
}
```

Все проверки и потенциально падающее выделение выполняются до изменения
опубликованных связей. После успешного `Items.allocate` остаются переносы
владеющих ссылок, обновление невладеющего `prev` и счётчика. Условия могут быть
временно открыты внутри операции, но должны быть восстановлены до любой
наблюдаемой границы.

`take victim.Target` оставляет embedded-компонент изъятым. Последующий
`Items.free(take victim)` освобождает память узла и не уничтожает перенесённый
`Target` повторно; memory manager получает от компилятора состояние
инициализации компонентов.

Прямые `replace` и `remove` требуют, чтобы перенос `Target`, запись служебных
полей и освобождение опустошённого узла не бросали исключений, не
приостанавливались и не вызывали наблюдающий код.

## Итератор

Курсор должен хранить ссылку на массив, а не на `Target`. Чтобы вложенный
`Self` не стал двусмысленным, тип владельца передаётся явно:

```efen
struct ReadCursor<Owner> {
    let owner: &read Owner
    var left: read Items.Item?
    var right: read Items.Item?
}

public fn iterator -> ReadCursor<Self> {
    return ReadCursor(
        owner: &read self,
        left: null,
        right: self.head
    )
}
```

Живой курсор удерживает structural borrow массива и запрещает удаление или
перестройку связей.

## Проверяемые свойства

На публичной границе компилятор должен доказать:

- каждый `Items.Item` достижим из `self.head` по `next`;
- соседние `next` и `prev` взаимно согласованы;
- `head.prev == null` и `tail.next == null`;
- пустота `head` и `tail` совпадает;
- `self.length == Items.count`;
- `itemAt(i).Target` является элементом логической позиции `i`.

## Граница предложения

Точные contracts `Items.allocate`, `Items.free` и автоматического открытия
условий остаются кандидатами memory API. Отдельные `NodePool`,
`PreparedLinks` и `Mutation.commit` для выражения этой структуры не нужны.
