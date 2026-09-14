# Layout и representation

Статус: рабочий документ для последовательного утверждения модели. Синтаксис
показанных memory descriptors и их операций является проектом языка.

## Задача

`layout` описывает представление памяти структуры данных:

- какие структуры входят в представление;
- сколько их экземпляров существует;
- как они расположены;
- какие ссылки связывают их;
- какие условия правильности должны выполняться.

`representation` является аспектом, который предоставляет такой layout и
реализацию операций исходного типа.

Основной проверочный пример — `Array<Target, R>`. Один логический массив может
иметь разные конкретные представления:

```efen
Array<X, Contiguous>
Array<X, DynamicContiguous>
Array<X, List>
Array<X, DoubleLinkedList>
Array<X, Chunked>
```

Они сохраняют смысл упорядоченной последовательности, но используют разное
расположение памяти и имеют разную стоимость операций.

## Параметры representation

Исходный `Array` передаёт аспекту тип элемента:

```efen
struct Array {
    generic Element: Type
    generic R<Target>: Representation<Target>

    conforms IndexedSequence<Element>
    use R<Element>
}
```

При построении `Array<User, List>`:

```text
Target = User
Self   = Array<User, List>
```

`Target` является явным generic-параметром аспекта и означает исходный тип
элемента. `Self` не передаётся вторым generic-параметром: компилятор неявно
связывает его с конкретным типом, внутри которого написано `use R<Element>`.
`self` означает текущий runtime-экземпляр этого `Self`.

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        // Определение памяти Self.
    }

    implementation {
        // Операции над self.
    }
}
```

Блока `implementation Target` нет: он ошибочно трактовал тип элемента как
строящийся массив.

## Структуры и дескрипторы памяти

`struct` задаёт форму одного значения. `set`, `one`, `area` и
`set area` являются дескрипторами памяти: они описывают количество экземпляров
и их расположение.

```efen
layout {
    set Items: Item
    one Header

    struct Item {
        // Форма одного Item.
    }

    struct Header {
        // Форма единственного Header.
    }
}
```

Дескрипторы принято группировать в начале layout. Это канонический стиль, а не
ограничение разрешения имён: объявления одного layout видят друг друга
независимо от порядка.

`set Items: Item` и `set OtherItems: Item` являются разными множествами одной
формы. Их handles имеют разное происхождение:

```efen
Items.Item
OtherItems.Item
```

Поэтому выделение и освобождение принадлежат дескриптору:

```efen
Items.allocate(...)
Items.allocateArea(...)
Items.free(...)
```

`Item.allocate(...)` не сообщает, в каком множестве появляется память, и для
такой операции недостаточно одной формы `struct Item`.

`Items.Item` обозначает отдельный элемент, которым управляет `Items`.
`Items.Area` обозначает принадлежащую `Items` непрерывную область. Право
`own` остаётся отдельным от роли handle: только владеющий handle можно
потребить операцией освобождения.

В будущем дескриптор сможет назвать source: память процесса, файл, GPU или
другой ресурс. Точная модель source пока отложена.

## Self как корень layout

Когда representation определяет память самого применившего его типа, корнем
является `Self`:

```efen
aspect List<Target> conforms Representation<Target> {
    layout {
        set Items: Item

        struct Item {
            Target
            var next: own other Items.Item? = null
        }

        struct Self {
            var head: own Items.Item? = null
            var tail: read Items.Item? = null
            var length: Size = 0
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

        public fn count -> Size {
            return self.length
        }
    }
}
```

Создание нового `Array<Target, List>` вызывает конструктор representation,
который явно инициализирует поля `Self`. Отдельные `struct List`, `one List` и
присваивание `List = List()` для корня не нужны. `one` используется, когда
layout действительно содержит отдельный одиночный объект помимо `Self`.

## Поле и физическое встраивание

Обычное поле является логическим местом:

```efen
struct Item {
    var value: Target
}
```

Эта запись не обещает inline-размещение. Активная representation поля может
хранить указатель, индекс или другую косвенную форму.

Голое имя типа физически встраивает его в структуру:

```efen
struct Item {
    Target
    var next: own other Items.Item? = null
}
```

Здесь `Item` начинается с `Target`. Встраиваемый компонент может находиться и
не в начале:

```efen
struct Item {
    var tag: UInt32
    Target
    var next: own other Items.Item? = null
}
```

Выражение `item.Target` обозначает место встроенного значения независимо от
его смещения:

```efen
let copy: Target = item.Target
let borrow = &item.Target
let moved: Target = take item.Target
item.Target = take replacement
```

Создание структуры со встроенным значением требует поместить его данные внутрь
новой структуры. Обычная передача требует `Copyable`; `take` переносит
владение:

```efen
let item = Items.allocate(
    Item(take value, next: null)
)
```

Memory manager получает состояние инициализации компонентов. Если
`take item.Target` уже перенёс embedded-значение, последующий
`Items.free(take item)` освобождает память `Item`, не уничтожая `Target`
повторно.

## Декларативные условия

Блок после свойства описывает допустимое значение. Внутри него `value`
означает значение этого свойства:

```efen
var length: Size = 0 {
    value == Items.count
}
```

Условие при `set` применяется к каждому его элементу:

```efen
set Items: Item {
    value reachable from self.head by Item.next
}
```

`reachable` является логическим рефлексивным отношением пути. Оно не выполняет
runtime-обход.

Обычный синтаксис `if` внутри условия означает импликацию:

```efen
var tail: read Items.Item? = null {
    (self.head == null) == (value == null)

    if value != null {
        value reachable from self.head by Item.next
        value.next == null
    }
}
```

Выражения одного блока соединяются логическим `&&`. Компилятор может временно
открыть затронутые условия внутри операции, но обязан доказать их восстановление
перед `return`, `throw` и любым вызовом, способным наблюдать layout.
Отдельный изменяемый ghost-state для этого не требуется.

## Непрерывные и составные области

Одна непрерывная область однородных элементов представляется `Items.Area`.
Несколько областей того же дескриптора допустимы, например во время relocation
или в chunked-массиве.

Область из разнородных структур сможет перечислять допустимые типы. Точный
surface-синтаксис heterogeneous area пока не утверждён.

Динамический массив различает:

- capacity области;
- инициализированные места;
- логическое число живых элементов.

Chunked-массив использует каталог, чьи элементы владеют отдельными
`Items.Area`. Рост каталога переносит handles областей и не обязан перемещать
сами `Target`.

## Доступ и стоимость

`array[index]` является логическим местом. Representation предоставляет
обычные операции чтения, записи, заимствования и структурного изменения.
Логическое место может реализовываться:

- смещением внутри `Items.Area`;
- найденным `Items.Item` списка;
- парой «блок и смещение»;
- набором column projections;
- записью страницы файла.

Representation может менять стоимость, но не наблюдаемый порядок элементов.
Например, индексирование имеет `O(1)` у contiguous и chunked представлений,
`O(index)` у односвязного списка и
`O(min(index, count - index))` у двусвязного.

## Теоретические реализации

Модель развёрнута в пяти примерах:

1. [непрерывный массив постоянной длины](array-representations/CONTIGUOUS-ARRAY.md);
2. [динамический непрерывный массив](array-representations/DYNAMIC-ARRAY.md);
3. [массив на односвязном списке](array-representations/LIST-ARRAY.md);
4. [массив на двусвязном списке](array-representations/DOUBLE-LINKED-LIST-ARRAY.md);
5. [массив из блоков](array-representations/CHUNKED-ARRAY.md).

Во всех документах memory API остаётся кандидатным. Компилятор, runtime и
реальные программы Efen эти эскизы пока не проверяли.
