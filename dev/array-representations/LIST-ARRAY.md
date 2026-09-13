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

## Какие средства используются

Внутренняя память узлов описывается обычным Efen `layout`:

```efen
set Nodes: Node
Nodes.Pointer
Nodes.allocate(...)
Nodes.allocateMany(count: ...)
```

Поэтому `implementation Target` может добавить в конечный тип член `set Nodes`.

Семантика `set` и указателей описана в
[адресах и структурах данных](../../docs/efen/memory/addresses.md). `Nodes`
задаёт логические идентификаторы и время жизни узлов. Его две функции выделения
создают элементы этого множества. Владеющий `Nodes.Pointer` отвечает за время
жизни выделения; когда последний владелец уничтожается, представление возвращает
память тому же физическому распределителю.

Выделение выполняют две разные функции:

```efen
fn allocate(
    value: own Node,
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Nodes.Pointer

fn allocateMany(
    count: Size,
    make: (Size) -> Node,
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Nodes.Range
```

`Nodes.allocate` создаёт один `Node` и возвращает `Nodes.Pointer`.
`Nodes.allocateMany` создаёт `count` узлов и возвращает `Nodes.Range`. Обе
функции выделяют память, инициализируют значения и включают их в логическое
множество. При ошибке ни один частично созданный элемент не остаётся в `Nodes`.

`zeroed: true` зануляет физическую память до инициализации. Оно допустимо только
тогда, когда контракт типа разрешает нулевое представление. `alignment` не может
быть меньше естественного выравнивания `Node` и должен иметь допустимое для
источника памяти значение.

В этом примере физическое представление `Nodes` выбирается по умолчанию. Позже
`List` сможет открыть его как ещё один обобщённый параметр. Это позволит тем же
логическим узлам жить в непрерывном пуле, блоках, файле или другой памяти без
изменения алгоритма списка.

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

        struct Node {
            var value: Target.Element
            var next: own other Nodes.Pointer? = null
        }

        struct ReadCursor {
            let owner: &read Target
            var current: read Nodes.Pointer?

            fn next -> (&read[owner] Target.Element)? {
                if current == null {
                    return null
                }

                let node = current!
                current = node.next
                return &read[owner] node.value
            }
        }

        var head: own Nodes.Pointer? = null
        var tail: read Nodes.Pointer? = null {
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

        fn nodeAt(index: Size) -> read Nodes.Pointer {
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
                    let node = Nodes.allocate(
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
                        let node = Nodes.allocate(
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
                    let node = Nodes.allocate(
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
                element: Node.value
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

Проверка индекса выполняется до изменения структуры. `Nodes.allocate` может
бросить исключение, но при ошибке не оставляет частично созданный узел в
`Nodes`. После успешного `allocate` остаются только безотказные переносы
указателей.

Новый узел сначала создаётся с пустым `next`. Только после успешного `allocate`
алгоритм переносит в него `head` или `before.next`. Поэтому отказ создания не
может забрать и уничтожить уже опубликованный суффикс списка.

`region suspend` не отменяет проверку памяти, происхождения ссылки или прав. Он
временно разрешает нарушить два явно названных логических условия и требует
восстановить их на каждом выходе. Если `Nodes.allocate` бросает, старые `head`,
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
`append` после успешного `Nodes.allocate` — `O(1)`. Эти различия допустимы;
изменение логической последовательности недопустимо.

## Оставшиеся открытые формы

В коде нет отдельного логического протокола `create/take`. `Nodes.allocate` и
`Nodes.allocateMany` образуют типизированный интерфейс выделения памяти, а
время жизни полученного места следует из владения `Nodes.Pointer`.

Открыты точные сигнатуры `Nodes.allocate`, `Nodes.allocateMany` и общих кандидатных
программных интерфейсов представления: `implementation Target`,
`DefinitionPlan`, `PhysicalSchema`, `ArrayPlace`, `PreparedReplacement`,
`HardConstraints` и `CostHints`.
