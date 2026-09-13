# `Array` в виде односвязного списка

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Приведён эскиз
библиотеки на Efen, а не программа для уже существующего компилятора.

## Логический контракт

`Array<Element, List>` остаётся упорядоченной индексируемой
последовательностью. Представление меняет физическую форму и стоимость, но
сохраняет общий `IndexedSequence<Element>`:

```efen
contract IndexedSequence<Element> {
    fn count -> Size
    fn read(index: Size) -> Element where Element: Copyable
    fn replace(index: Size, value: own Element) -> Element
    fn slice(first: Size, last: Size) -> ArraySlice<Self>
}
```

Изменение длины и получение сохраняемой ссылки являются отдельными обычными
контрактами:

```efen
contract ResizableSequence<Element> {
    fn append(value: own Element)
    fn insert(index: Size, value: own Element)
    fn remove(index: Size) -> Element
}

contract BorrowedElements<Element> {
    fn borrowRead(index: Size) -> &read[self] Element
    fn borrowWrite(index: Size) -> &[self] Element
}
```

`List` выполняет оба дополнительных контракта. Другое представление массива
может их не выполнять.

Сам массив явно объявлен как обобщённый `layout`:

```efen
layout Array {
    generic Element: Type
    generic R<Target>: Representation<Target>

    conforms IndexedSequence<Element>
    use R<Self>
}
```

До применения `R` это определение намеренно неполно. Аспект достраивает конечный
тип через `implementation Target`, после чего компилятор проверяет контракт.

## Что становится частью `Target`

Объявление внутри `implementation Target` становится членом самого конечного
типа. Оно не хранится в отдельном экземпляре аспекта. Поэтому следующий блок:

```efen
implementation Target {
    set Nodes: Node
    var head: own Node.item? = null
    var tail: read Node.Pointer? = null
    var length: Size = 0
}
```

означает, что каждый экземпляр `Array<Element, List>` содержит своё логическое
множество `Nodes` и свои поля `head`, `tail` и `length`.

Все четыре члена имеют начальное состояние: `Nodes` пусто, ссылки равны `null`,
длина равна нулю. Поэтому Efen может синтезировать создание пустого значения по
умолчанию; пустой пользовательский конструктор не нужен.

Создание значения и выбор места для него — разные операции. Локальный `Target`
может находиться в стеке, быть полем другого значения или элементом внешнего
`layout`. Обязательный вызов `Target.allocate` навязал бы динамическую память
даже там, где она не нужна. Если программе требуется отдельно выделенный
`Target`, стандартное поведение его представления может предоставить такую
операцию автоматически.

## Какие средства используются

Внутренняя память узлов описывается обычным Efen `layout`:

```efen
set Nodes: Node
Nodes.Pointer
Node.allocate(...)
Node.allocateArea(count: ...)
Node.free(...)
```

Поэтому `implementation Target` может добавить в конечный тип член `set Nodes`.

`Nodes` задаёт только логическое множество узлов. Оно не является аллокатором и
не владеет физической памятью автоматически. `Nodes.Pointer` указывает на один
логический элемент этого множества.

Выделение выполняют две разные функции:

```efen
fn allocate(
    value: own Node,
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Node.item

fn allocateArea(
    count: Size,
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Node.Area

fn free(area: own Node.Area)
```

`Node.allocate` выделяет один элемент и возвращает `Node.item`.
`Node.allocateArea` выделяет блок для `count` элементов и возвращает
`Node.Area`. `Node.free` принимает `Node.Area`; ему можно передать `Node.item`,
но нельзя передать `Node.Range` или `Node.Pointer`.

Все четыре роли являются чистыми указателями без сохранённого размера:

- `Node.item` — владеющий указатель на выделение ровно одного элемента;
- `Node.Area` — владеющий указатель на начало выделенного блока;
- `Node.Range` — указатель на начало последовательности без права освободить
  блок;
- `Node.Pointer` — указатель ровно на один физический `Node`.

Размер области хранится отдельно. Из `Node.Area` можно получить `Node.Range`, а
из диапазона после проверки индекса — `Node.Pointer`.

`zeroed: true` зануляет физическую память до инициализации. Оно допустимо только
тогда, когда контракт типа разрешает нулевое представление. `alignment` не может
быть меньше естественного выравнивания `Node` и должен иметь допустимое для
источника памяти значение.

В этом представлении каждый логический элемент `Nodes` связан с отдельным
`Node.item`. `Node.Pointer` и `Nodes.Pointer` могут иметь одно машинное значение,
но выполняют разные роли. Физическая схема обязана описать их соответствие.

В эскизе остаются четыре явно кандидатных интерфейса:

- `Representation<Target>` и `implementation Target` — обсуждаемая модель
  аспекта представления;
- `compiler::DefinitionPlan` — обычный программный интерфейс компилятора для
  добавления соответствий и описания физической схемы;
- `ArrayPlace<Element>` — логическое место с происхождением, правами и внутренней
  проекцией на `Node.value`;
- `PreparedReplacement` и `Mutation.commit` — общая подготовка замены значения
  и окно публикации, в котором нет отказов, приостановки и пользовательских
  обратных вызовов.

`ArraySlice`, `ArrayReadSlice`, `PhysicalSchema`, `HardConstraints` и
`CostHints` — общие кандидатные библиотечные типы, описанные в соседних
примерах. `PhysicalSchema` сообщает компилятору, какие объявления образуют
значение, прямой переход и начало обхода. Эти типы не являются скрытыми
специальными операциями списка.

## Полный эскиз

```efen
aspect List<Target> conforms Representation<Target> {
    struct Node {
        var value: Target.Element
        var next: own Node.item? = null
    }

    struct ReadCursor {
        let owner: &read Target
        var current: read Node.Pointer?
    }

    strategy ReadCursorIteration for ReadCursor {
        conforms Iterator<Item: &read[owner] Target.Element>

        fn next -> (&read[owner] Target.Element)? {
            if current == null {
                return null
            }

            let node = current!
            current = node.next
            return &read[owner] node.value
        }
    }

    meta fn define(plan: compiler::DefinitionPlan) {
        plan.addConformance(Target, ResizableSequence<Target.Element>)
        plan.addConformance(Target, BorrowedElements<Target.Element>)
        plan.registerSchema(Target, physicalSchema)
    }

    implementation Target {
        set Nodes: Node {
            invariant reachable(node) {
                node in head.next*
            }
        }

        var head: own Node.item? = null
        var tail: read Node.Pointer? = null {
            (head == null) == (tail == null) &&
            (tail == null || tail!.next == null)
        }

        var length: Size = 0

        public fn count -> Size {
            return length
        }

        fn checkIndex(index: Size) {
            if index >= length {
                throw BoundsError(index, length)
            }
        }

        fn checkInsertIndex(index: Size) {
            if index > length {
                throw BoundsError(index, length)
            }
        }

        fn nodeAt(index: Size) -> read Node.Pointer {
            checkIndex(index)

            var current = head!
            var position: Size = 0

            while position < index {
                current = current.next!
                position += 1
            }

            return current
        }

        fn place(index: Size) -> ArrayPlace<Target.Element> {
            let node = nodeAt(index)
            return ArrayPlace(
                owner: &read self,
                logicalIndex: index,
                projection: node.value
            )
        }

        public fn read(index: Size) -> Target.Element
            where Target.Element: Copyable
        {
            return place(index).copy()
        }

        public fn replace(
            index: Size,
            value: own Target.Element
        ) -> Target.Element {
            let replacement = PreparedReplacement(
                destination: place(index),
                value: take value
            )
            return Mutation.commit(take replacement)
        }

        public fn append(value: own Target.Element) {
            let nextLength = checkedAdd(length, 1)

            region suspend Nodes.reachable {
                region suspend tail {
                    let node = Node.allocate(
                        value: Node(value: take value, next: null),
                        alignment: Node.alignment
                    )

                    if tail == null {
                        head = take node
                        tail = head
                    } else {
                        tail!.next = take node
                        tail = tail!.next
                    }

                    length = nextLength
                }
            }
        }

        public fn insert(index: Size, value: own Target.Element) {
            checkInsertIndex(index)

            if index == length {
                append(take value)
                return
            }

            let nextLength = checkedAdd(length, 1)

            if index == 0 {
                region suspend Nodes.reachable {
                    region suspend tail {
                        let node = Node.allocate(
                            value: Node(value: take value, next: null),
                            alignment: Node.alignment
                        )
                        node.next = take head
                        head = take node
                        length = nextLength
                    }
                }
                return
            }

            let before = nodeAt(index - 1)

            region suspend Nodes.reachable {
                region suspend tail {
                    let node = Node.allocate(
                        value: Node(value: take value, next: null),
                        alignment: Node.alignment
                    )
                    node.next = take before.next
                    before.next = take node
                    length = nextLength
                }
            }
        }

        public fn remove(index: Size) -> Target.Element {
            checkIndex(index)
            var result: Target.Element

            if index == 0 {
                region suspend Nodes.reachable {
                    region suspend tail {
                        let victim = take head!
                        head = take victim.next

                        if head == null {
                            tail = null
                        }

                        length -= 1
                        result = take victim.value
                        Node.free(take victim)
                    }
                }
                return take result
            }

            let before = nodeAt(index - 1)

            region suspend Nodes.reachable {
                region suspend tail {
                    let victim = take before.next!
                    before.next = take victim.next

                    if before.next == null {
                        tail = before
                    }

                    length -= 1
                    result = take victim.value
                    Node.free(take victim)
                }
            }

            return take result
        }

        public fn slice(first: Size, last: Size) -> ArraySlice<Self> {
            if first > last || last > length {
                throw RangeError(first, last, length)
            }
            return ArraySlice(owner: &self, first: first, last: last)
        }

        public fn readSlice(first: Size, last: Size)
            -> ArrayReadSlice<Self>
        {
            if first > last || last > length {
                throw RangeError(first, last, length)
            }
            return ArrayReadSlice(
                owner: &read self,
                first: first,
                last: last
            )
        }

        public fn borrowRead(index: Size)
            -> &read[self] Target.Element
        {
            return &read[self] nodeAt(index).value
        }

        public fn borrowWrite(index: Size) -> &[self] Target.Element {
            return &[self] nodeAt(index).value
        }

        public fn iterator -> ReadCursor {
            return ReadCursor(owner: &read self, current: head)
        }

        meta fn physicalSchema -> PhysicalSchema {
            return PhysicalSchema.linkedSequence(
                members: Nodes,
                first: head,
                next: Node.next,
                element: Node.value,
                allocation: Node.item,
                logicalPointer: Nodes.Pointer,
                physicalPointer: Node.Pointer
            )
        }

        meta fn hardConstraints -> HardConstraints {
            return HardConstraints(
                forwardTraversal: true,
                backwardTraversal: false,
                structuralMutationWhileBorrowed: false
            )
        }

        meta fn costHints -> CostHints {
            return CostHints(
                index: linearFromFront,
                sequentialForward: linearTotal,
                append: constant,
                insertAfterLocatedNode: constant,
                removeAfterLocatedNode: constant,
                backwardTraversal: unavailable
            )
        }
    }
}
```

## Почему операции безопасны при ошибках

Проверка индекса выполняется до изменения структуры. `Node.allocate` может
бросить исключение, но при ошибке не оставляет частично созданный узел в
`Nodes`. После успешного `allocate` остаются только безотказные переносы
указателей.

Новый узел сначала создаётся с пустым `next`. Только после успешного `allocate`
алгоритм переносит в него `head` или `before.next`. Поэтому отказ создания не
может забрать и уничтожить уже опубликованный суффикс списка.

`region suspend` не отменяет проверку памяти, происхождения ссылки или прав. Он
временно разрешает нарушить два явно названных логических условия и требует
восстановить их на каждом выходе. Если `Node.allocate` бросает, старые `head`,
`tail` и множество `Nodes` остаются согласованными.

При удалении владеющий указатель сначала переносится из `head` или
`before.next`, продолжение цепочки занимает освободившееся место, затем
`take victim.value` переносит `Element` из отсоединённого узла. При уничтожении
опустевшего владеющего указателя узел исключается из `Nodes`, а его память
возвращается распределителю. Пользовательский деструктор результата работает
после выхода из окон и не видит промежуточную цепочку.

## Срезы, ссылки и обход

`ArraySlice` и `ArrayReadSlice` хранят ссылку на массив и полуинтервал. Их
`read` и `replace` пересылаются исходному массиву и не требуют возможности
получить `&Element`. Методы `borrowRead` и `borrowWrite` доступны условно через
`BorrowedElements`.

Срез или `ReadCursor` удерживает структурное заимствование массива. Поэтому
`append`, `insert` и `remove` недоступны, пока он жив. Прямой обход один раз
получает `head`, затем использует `next`; повторного индексного поиска нет.

Компилятор совмещает граф программы со схемой `head → next`, обязательными
ограничениями и оценками стоимости. Он может встроить `next`, но не может
синтезировать отсутствующий `prev` или изменить порядок наблюдаемых эффектов.

## Проверка контракта

На каждой публичной границе:

```text
length равно числу узлов, достижимых из head по next
каждый узел Nodes достижим из head по next
count() == 0  <=>  head == null && tail == null
count() > 0   =>   tail — последний узел цепочки
nodeAt(i).value == логический elementAt(i)
append, insert и remove сохраняют порядок Array
iterator выдаёт позиции 0 ..< count
```

Индексирование стоит `O(index + 1)`, последовательный обход — `O(count)`, а
`append` после успешного `Node.allocate` — `O(1)`. Эти различия допустимы;
изменение логической последовательности недопустимо.

## Оставшиеся открытые формы

В коде нет отдельного логического протокола `create/take`. `Node.allocate` и
`Node.allocateArea` образуют типизированный интерфейс выделения памяти.
`Node.free` освобождает только `Node.Area` или его более точную форму
`Node.item`.

Открыты точные сигнатуры `Node.allocate`, `Node.allocateArea`, `Node.free` и общих кандидатных
программных интерфейсов представления: `implementation Target`,
`DefinitionPlan`, `PhysicalSchema`, `ArrayPlace`, `PreparedReplacement`,
`HardConstraints` и `CostHints`.
