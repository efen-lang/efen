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
    use R<Element>
}
```

При применении `List` параметр `Target` означает исходный тип элемента. Для
`Array<User, List>` внутри `List<Target>` именем `Target` называется `User`.
`Target` не является строящимся массивом. Конкретный
`Array<Element, R>`, внутри которого выполнен `use R<Element>`, неявно входит в
аспект как `Self`, а его текущий экземпляр внутри условий и операций называется
`self`.

## Layout списка

`layout` логически описывает представление памяти и связи между входящими в него
структурами. Он отделён от исполняющей операции реализации.

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value reachable from self.head by Item.next
        }

        struct Item {
            Target
            var next: own other Items.Item? = null
        }

        struct Self {
            var head: own Items.Item? = null

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

`struct Item` задаёт форму одного узла и встраивает `Target` первым компонентом.
`struct Self` определяет поля самого конкретного `Array<Element, List>`.
Отдельного корневого `struct List` и дескриптора `one List` здесь нет: корнем
layout уже является `Self`.

`set Items: Item` является дескриптором памяти:

- `set Items: Item` описывает множество отдельно размещённых `Item`;
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

При создании нового `Array<Element, List>` конструктор representation явно
инициализирует поля `Self`. Дескриптор `Items` начинается пустым; после записи
`head`, `tail` и `length` условия layout выполняются для пустого списка.

## Поле и встраивание

Обычное поле не обещает, что байты `Target` находятся внутри содержащей его
структуры:

```efen
struct Item {
    var value: Target
}
```

Это логическое поле. Его representation может оказаться указателем на `Target`
или другой косвенной формой.

Голое имя типа в теле структуры означает физическое встраивание:

```efen
struct Item {
    Target
    var next: own other Items.Item? = null
}
```

В этом примере `Item` начинается со встроенной структуры `Target`. В общем
случае встроенный тип может находиться и не в начале: его положение задаётся
порядком компонентов структуры.

Создание `Item` должно поместить данные `Target` внутрь памяти нового узла.
Обычное значение потребовало бы `Target: Copyable`; список принимает `own
Target` и явно переносит его:

```efen
let item = Items.allocate(
    Item(
        take value,
        next: null
    )
)
```

Выражение `item.Target` обозначает место встроенного значения целиком:

```efen
let copy: Target = item.Target
let borrow = &item.Target
let moved: Target = take item.Target
item.Target = take replacement
```

Само выражение не выбирает копирование или перенос. Обычное чтение копирует при
`Target: Copyable`, `&` заимствует, а `take` переносит встроенное значение.

## Декларативные условия

Блок после свойства задаёт условие его правильности. Внутри него `value`
означает значение объявляемого свойства:

```efen
var length: Size = 0 {
    value == Items.count
}
```

`Items.count` здесь является логической мощностью дескриптора. Хранимое runtime-
поле `self.length` обязано совпадать с ней.

Условие при `set` применяется к каждому его элементу. Поэтому:

```efen
set Items: Item {
    value reachable from self.head by Item.next
}
```

означает: каждый элемент `Items` достижим из `self.head` переходами по
`Item.next`.

`reachable` — логическое отношение, а не runtime-обход. Отношение рефлексивно:
корень достижим из самого себя за ноль переходов. Следующий элемент достижим,
если достижим предыдущий и его `next` указывает на следующий элемент.

`if condition { ... }` внутри условия является логической импликацией. Тело не
исполняется во время работы программы:

```efen
if value != null {
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
- `self.length` равен числу элементов `Items`.

Компилятор может временно открыть затронутые условия внутри операции. Он обязан
доказать их восстановление перед `return`, `throw` или вызовом кода, способного
наблюдать layout. Условия являются декларативными; отдельный блок `proof`,
изменяемые ghost-переменные и ручное дублирование списка не требуются.

## Реализация операций

Полный основной эскиз аспекта выглядит так:

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value reachable from self.head by Item.next
        }

        struct Item {
            Target
            var next: own other Items.Item? = null
        }

        struct Self {
            var head: own Items.Item? = null

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

            var current = self.head!
            var position: Size = 0

            while position < index {
                current = current.next!
                position += 1
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
            let nextCount = checkedAdd(self.length, 1)
            let item = Items.allocate(
                Item(take value, next: null)
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
                    Item(take value, next: null)
                )

                item.next = take self.head
                self.head = take item
                self.length = nextCount
                return
            }

            let before = itemAt(index - 1)
            let item = Items.allocate(
                Item(take value, next: null)
            )

            item.next = take before.next
            before.next = take item
            self.length = nextCount
        }

        public fn remove(index: Size) -> Target {
            if index >= self.length {
                throw BoundsError(index, self.length)
            }

            if index == 0 {
                let victim = take self.head!
                self.head = take victim.next

                if self.head == null {
                    self.tail = null
                }

                self.length -= 1

                let result = take victim.Target
                Items.free(take victim)
                return take result
            }

            let before = itemAt(index - 1)
            let victim = take before.next!
            before.next = take victim.next

            if before.next == null {
                self.tail = before
            }

            self.length -= 1

            let result = take victim.Target
            Items.free(take victim)
            return take result
        }
    }
}
```

`itemAt` возвращает `Items.Item`. Результат сохраняет знание о том, что адрес
обозначает отдельный элемент, управляемый `Items`. Владение остаётся отдельным
правом: обычный результат `itemAt` не получает `own`, а `take self.head!` или
`take before.next!` переносит владеющий `Items.Item`, который затем можно
передать `Items.free`.

## Сохранение условий

Проверка индекса и `checkedAdd` выполняются до изменения списка.
`Items.allocate` может завершиться ошибкой, но при ошибке не добавляет частично
созданный элемент в `Items`. После успешного выделения `append` и `insert`
выполняют только переносы ссылок и запись счётчика.

Между успешным `Items.allocate` и присоединением нового элемента условие
достижимости временно открыто: новый `Items.Item` уже входит в `Items`, но ещё не
достижим из `self.head`. До восстановления условия код не возвращается, не
бросает исключение и не вызывает наблюдающий пользовательский код.

При удалении владеющая ссылка сначала переносится из `self.head` или
`before.next`. Продолжение цепочки занимает освободившееся место, после чего
значение извлекается из отсоединённого элемента. `Items.free(take victim)`
потребляет владеющий `Items.Item` и удаляет его из дескриптора. На границе
операции оставшиеся элементы снова достижимы, `tail` заканчивает цепочку, а
`self.length == Items.count`.

Этот прямой алгоритм применим, когда перенос `Target`, запись служебных полей и
освобождение уже опустошённого `Items.Item` не бросают исключений, не
приостанавливаются и не вызывают наблюдающий код. `take victim.Target` передаёт
менеджеру памяти состояние частичной инициализации: последующий `Items.free` не
уничтожает перенесённый `Target` повторно.

## Стоимость

`count` выполняется за `O(1)`. `itemAt`, `read`, `replace`, `insert` и `remove`
требуют `O(index + 1)` переходов от `head`. `append` выполняется за `O(1)`, потому
что `Self` хранит `tail`.

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
