# Адресная арифметика

`Efen` предпочитает использовать декларативную адресную арифметику
вместо императивной адресной арифметики, которую можно доказать
с помощью формальной логики.

Для этого `Efen` использует несколько важных инструментов:
- Структуры как низкоуровневые контейнеры данных
- Композиция структур
- Формальные указатели

## Композиция структур и указатели

Структуры в `Efen` служат частью декларативной адресной арифметики:

```efen
struct Node {
    var value: Int
    var next: Node
}
```

Здесь, поле `next` является указателем на следующий узел в списке.

```efen
struct Book {
    var title: String
    var author: String    
}

struct Node {
    var inline item: Book
    var next: Node
}
```

А здесь `Book` является частью структуры `Node`, и все его поля
доступны напрямую через `Node`. Операция приведения `Node` к `Book` 
гарантируется правильной композицией структур.

Более сложный пример c объединением Union нескольких структур:
```efen
struct Header {
    var id: Int
    var timestamp: UInt64
}

struct Payload {
    var data: Byte[]
}

struct Footer {
    var checksum: UInt32
}

struct Packet {
    Header
    var unionSelector: UInt8 { unionSelector == data.typeOf }
    union data {
        payload: Payload
        footer: Footer
    }
}
```

Здесь `Payload` и `Footer` занимают одно и то же место в памяти,
и мы можем безопасно работать с ними, используя декларативную
адресную арифметику.

`Efen` так же поддерживает variadic unions:

```efen
struct Message {
    var type: UInt8 { type == data.indexOf }
    var size: Size { size == data.sizeOf }
    union data {
        text: String
        image: Image
        video: Video
    }
}
```

В этом случае структура `Message` имеет различный размер в памяти
в зависимости от значения поля `type`.

## Вычисляемые смещения

Обычно каждое поле структуры имеет фиксированное смещение,
но иногда требуется вычислять смещения динамически.

```efen
struct Buffer {
    var dataOffset: Offset<data>
    var footerOffset: Offset<footer>
    var header: Spawn<Byte>
    var data: Spawn<Byte>
    var footer: Spawn<Byte>
}
```

Специальный дженерик тип `Offset<Field>` обозначает смещение
поля `Field` внутри структуры. Он автоматически запрещает программисту
изменять это значение напрямую и обеспечивает методы для безопасного
использования смещения.

Атрибут `@offset` указывает, что функция вычисляет смещение
относительно начала структуры.


## Предикаты для динамических размеров

Пример выше можно решить другим способом с помощью предикатов.

```efen
struct Buffer {
    var dataOffset: Size { dataOffset == header.size }
    var footerOffset: Size { footerOffset == header.size + data.size }
    var header: Spawn<Byte>
    var data: Spawn<Byte>
    var footer: Spawn<Byte>
    
    @offset
    fn data() -> Size {
        return header.size
    }
    
    @offset
    fn footer() -> Size {
        return header.size + data.size
    }
    
    @setter
    fn setHeader(value: Spawn<Byte>) {
        self.header = value;
        self.dataOffset = header.size;
        self.footerOffset = header.size + data.size;
    }
    
    @setter
    fn setData(value: Spawn<Byte>) {
        self.data = value;
        self.footerOffset = header.size + data.size;
    }    
}
```

По сути этот код является более низкоуровневой версией предыдущего примера.
Здесь `dataOffset` и `footerOffset` вычисляются с помощью предикатов,
а функции с атрибутом `@offset` предоставляют безопасный доступ
к вычисленным смещениям.

Компилятор проверяет корректность предикатов
и гарантирует, что они всегда будут соответствовать фактическим размерам полей.

Предикаты type-refinement могут использоваться и для других случаев.

```efen
struct String {
    // Type refinement для массива байтов с динамическим размером    
    var size: Size { size == data.length }
    var data: Spawn<Byte>
}
```

Здесь элемент структуры `size` всегда обязан соответствовать длине массива data, 
что явно описано в предикате.
Компилятор обеспечивает корректность этого соответствия, проверяя все участки кода, 
где происходит изменение длины массива data. 
Если компилятор не может формально доказать это соответствие,
он выдаёт ошибку компиляции.

Вот более сложный пример:

```efen
string SmartObject {
    var payloadOffset: Size { payloadOffset == header.size }
    var footerOffset: Size { footerOffset == header.size + (payload != null ? payload.size : 0) }
    var header: Spawn<Byte>
    var payload: Spawn?<Byte>
    var footer: Spawn?<Byte>
}
```

## Приведение указателей

`Efen` агрессивно скрывает от программиста операции над указателями. 
Их нет ни в параметрах функций, ни в структурах данных. Однако под капотом
операции с указателями всё же происходят.

`Efen` отслеживает условия владения памятью и автоматически 
выбирает разные стратегии приведения указателей в зависимости от контекста.

Например, если переменная передаётся в функцию по значению и её можно 
передать по значению, то `Efen` выбирает стратегию копирования данных.
Если при этом передаётся владения, то `Efen` выбирает стратегию перемещения данных.

Если переменная имеет значительный размер, тогда она передаётся по ссылке,
и `Efen` выбирает стратегию приведения указателей без копирования данных.

### Захват конструктора

Рассмотрим следующую задачу. Пусть у нас есть структура связанный список, 
который хранит внутри себя объекты типа `Book`.

```efen
class Book {
    var title: String
    var author: String
    
    @constructor
    fn init(title: String, author: String) -> Self {
        self.title = title
        self.author = author
    }
}

struct Node {
    var inline item: Book
    var next: Node
}

class NodeList {
    var head: Node?
    
    constructor() {
        self.head = null
    }
    
    fn append() {}
}
```

Класс NodeList хотел бы на самом деле сам выделять память под Node, внутри которого содержится Book, 
но это невозможно, потому что Book не является структурой, 
у него свой конструктор, и его нельзя просто так встроить внутрь Node.
Конечно можно сперва создать Book, а потом перенести его внутрь Node,
но это будет неэффективно.

Решение этой задачи в `Efen` заключается в использовании захвата конструктора.

```efen
fn append(ctor: Constructor<Book>) {
    var newNode: Node = Node {
        next: self.head
    }
    self.head = newNode
    // Теперь передадим в конструктор указатель на место в памяти,
    // где должен быть создан объект Book
    ctor(newNode.item)
}
```

Как это работает?
1. Функция `append` принимает в качестве параметра `ctor` - замыкание на вызов конструктора Book.
2. Компилятор видит это, и если параметром функции является конструктор, 
   он образует замыкание с конструктором и передаёт его в функцию.
3. Внутри функции `append` создаётся новый узел Node,
   и выделяется память под него.
4. Затем вызывается переданный конструктор `ctor`,
   которому передаётся указатель на память внутри `newNode.item`.

Захват конструктора позволяет эффективно создавать объекты внутри структур,
избегая лишних копирований и перемещений данных, и при этом почти не изменяя сам код.