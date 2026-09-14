# `Array` в виде односвязного списка

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Это эскиз языка и
библиотеки, а не программа для уже существующего компилятора.

## Контракт массива

`Array<Element, List>` остаётся упорядоченной индексируемой
последовательностью. Списочное представление меняет расположение памяти и
стоимость операций, но не смысл массива.

```efen
contract IndexedSequence<Element> {
    fn count -> Size
    fn read(index: Size) -> Element where Element: Copyable
    fn replace(index: Size, value: own Element) -> Element
}

contract ResizableSequence<Element> {
    fn append(value: own Element)
    fn insert(index: Size, value: own Element)
    fn remove(index: Size) -> Element
}
```

Исходный тип массива объявляет тип элемента и параметр представления:

```efen
struct Array {
    generic Element: Type
    generic R<Target>: Representation<Target>

    conforms IndexedSequence<Element>
    conforms ResizableSequence<Element>
    use R<Element>
}
```

При применении `List` параметр `Target` означает исходный тип элемента. Для
`Array<User, List>` внутри `List<Target>` именем `Target` называется `User`.
`Target` не является строящимся массивом, поэтому аспект содержит обычный блок
`implementation`, а не `implementation Target`.

## Layout списка

`layout` логически описывает представление памяти и связи между входящими в него
структурами. Он отделён от исполняющей операции реализации.

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        struct Item {
            var value: Target
            var next: own other Items.Item? = null
        }

        set Items: Item {
            value reachable from List.head by Item.next
        }

        struct List {
            var head: own Items.Item? = null

            var tail: read Items.Item? = null {
                (self.head == null) == (value == null)

                if value != null then {
                    value reachable from self.head by Item.next
                    value.next == null
                }
            }

            var count: Size = 0 {
                value == Items.count
            }
        }

        one List
    }

    implementation {
        // Операции приведены ниже.
    }
}
```

`struct Item` и `struct List` задают формы значений. Они сами не создают память.
`set Items: Item` и `one List` являются дескрипторами памяти:

- `set Items: Item` описывает множество отдельно размещённых `Item`;
- `one List` описывает ровно один размещённый корень списка;
- `Items.Item` является ссылкой на отдельный элемент, которым управляет
  дескриптор `Items`;
- `Items.allocate(...)`, `Items.allocateArea(...)` и `Items.free(...)`
  относятся именно к `Items`.

Это различие существенно, если в одном layout объявлены два множества одной
структуры:

```efen
set Items: Item
set OtherItems: Item
```

`Items.Item` и `OtherItems.Item` имеют разные origins. Вызов
`Items.allocate(...)` сообщает компилятору, в каком множестве появляется новый
элемент. Поэтому операции `Item.allocate(...)` и `Item.free(...)` здесь были бы
неопределёнными: структура задаёт форму элемента, но не его размещение.

В будущем layout сможет также указывать источник памяти — обычную память, файл,
GPU и другие источники. Этот пример источник не выбирает и использует поведение
дескрипторов по умолчанию.

## Декларативные условия

Блок после свойства задаёт условие его правильности. Внутри него `value`
означает значение объявляемого свойства:

```efen
var count: Size = 0 {
    value == Items.count
}
```

`Items.count` здесь является логической мощностью дескриптора. Хранимое runtime-
поле `List.count` обязано совпадать с ней.

Условие при `set` применяется к каждому его элементу. Поэтому:

```efen
set Items: Item {
    value reachable from List.head by Item.next
}
```

означает: каждый элемент `Items` достижим из `List.head` переходами по
`Item.next`.

`reachable` — логическое отношение, а не runtime-обход. Отношение рефлексивно:
корень достижим из самого себя за ноль переходов. Следующий элемент достижим,
если достижим предыдущий и его `next` указывает на следующий элемент.

`if condition then` внутри условия является логической импликацией. Тело не
исполняется во время работы программы:

```efen
if value != null then {
    value reachable from self.head by Item.next
    value.next == null
}
```

Два выражения внутри блока соединены логическим `&&`. Условие говорит, что
ненулевой `tail` достижим из `head` и заканчивает цепочку.

Все условия layout действуют вместе. На публичной границе они означают:

- `head` и `tail` либо оба пусты, либо оба непусты;
- каждый `Items.Item` входит в цепочку от `head`;
- `tail` входит в эту цепочку и его `next` равен `null`;
- `List.count` равен числу элементов `Items`.

Компилятор может временно открыть затронутые условия внутри операции. Он обязан
доказать их восстановление перед `return`, `throw` или вызовом кода, способного
наблюдать layout. Условия являются декларативными; отдельный блок `proof`,
изменяемые ghost-переменные и ручное дублирование списка не требуются.

## Реализация операций

Полный основной эскиз аспекта выглядит так:

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        struct Item {
            var value: Target
            var next: own other Items.Item? = null
        }

        set Items: Item {
            value reachable from List.head by Item.next
        }

        struct List {
            var head: own Items.Item? = null

            var tail: read Items.Item? = null {
                (self.head == null) == (value == null)

                if value != null then {
                    value reachable from self.head by Item.next
                    value.next == null
                }
            }

            var count: Size = 0 {
                value == Items.count
            }
        }

        one List
    }

    implementation {
        fn itemAt(index: Size) -> Items.Item {
            if index >= List.count {
                throw BoundsError(index, List.count)
            }

            var current = List.head!
            var position: Size = 0

            while position < index {
                current = current.next!
                position += 1
            }

            return current
        }

        public fn count -> Size {
            return List.count
        }

        public fn read(index: Size) -> Target
            where Target: Copyable
        {
            return itemAt(index).value
        }

        public fn replace(
            index: Size,
            value: own Target
        ) -> Target {
            let item = itemAt(index)
            let previous = take item.value
            item.value = take value
            return take previous
        }

        public fn append(value: own Target) {
            let nextCount = checkedAdd(List.count, 1)
            let item = Items.allocate(
                Item(value: take value, next: null)
            )

            if List.tail == null {
                List.head = take item
                List.tail = List.head
            } else {
                List.tail!.next = take item
                List.tail = List.tail!.next
            }

            List.count = nextCount
        }

        public fn insert(index: Size, value: own Target) {
            if index > List.count {
                throw BoundsError(index, List.count)
            }

            if index == List.count {
                append(take value)
                return
            }

            let nextCount = checkedAdd(List.count, 1)

            if index == 0 {
                let item = Items.allocate(
                    Item(value: take value, next: null)
                )

                item.next = take List.head
                List.head = take item
                List.count = nextCount
                return
            }

            let before = itemAt(index - 1)
            let item = Items.allocate(
                Item(value: take value, next: null)
            )

            item.next = take before.next
            before.next = take item
            List.count = nextCount
        }

        public fn remove(index: Size) -> Target {
            if index >= List.count {
                throw BoundsError(index, List.count)
            }

            if index == 0 {
                let victim = take List.head!
                List.head = take victim.next

                if List.head == null {
                    List.tail = null
                }

                List.count -= 1

                let result = take victim.value
                Items.free(take victim)
                return take result
            }

            let before = itemAt(index - 1)
            let victim = take before.next!
            before.next = take victim.next

            if before.next == null {
                List.tail = before
            }

            List.count -= 1

            let result = take victim.value
            Items.free(take victim)
            return take result
        }
    }
}
```

`itemAt` возвращает `Items.Item`. Результат сохраняет знание о том, что адрес
обозначает отдельный элемент, управляемый `Items`. Владение остаётся отдельным
правом: обычный результат `itemAt` не получает `own`, а `take List.head!` или
`take before.next!` переносит владеющий `Items.Item`, который затем можно
передать `Items.free`.

## Сохранение условий

Проверка индекса и `checkedAdd` выполняются до изменения списка.
`Items.allocate` может завершиться ошибкой, но при ошибке не добавляет частично
созданный элемент в `Items`. После успешного выделения `append` и `insert`
выполняют только переносы ссылок и запись счётчика.

Между успешным `Items.allocate` и присоединением нового элемента условие
достижимости временно открыто: новый `Items.Item` уже входит в `Items`, но ещё не
достижим из `List.head`. До восстановления условия код не возвращается, не
бросает исключение и не вызывает наблюдающий пользовательский код.

При удалении владеющая ссылка сначала переносится из `List.head` или
`before.next`. Продолжение цепочки занимает освободившееся место, после чего
значение извлекается из отсоединённого элемента. `Items.free(take victim)`
потребляет владеющий `Items.Item` и удаляет его из дескриптора. На границе
операции оставшиеся элементы снова достижимы, `tail` заканчивает цепочку, а
`List.count == Items.count`.

## Стоимость

`count` выполняется за `O(1)`. `itemAt`, `read`, `replace`, `insert` и `remove`
требуют `O(index + 1)` переходов от `head`. `append` выполняется за `O(1)`, потому
что `one List` хранит `tail`.

Эти различия являются свойствами списочного представления. Они не меняют
логический порядок элементов и контракт `Array`.

## Открытые границы

Точный proof-backend, правила автоматического открытия условий и диагностики
недоказанных формул ещё предстоит определить. Возможное понижение в VIR/Viper не
является частью surface syntax этого примера.

`source` памяти, `area` и `set area` намеренно не используются. Они могут
расширить layout для файлов, GPU и нескольких непрерывных областей, не меняя
основного различия между формой `struct` и размещением, заданным дескриптором
памяти.
