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
Nodes.create(...)
Nodes.take(...)
```

Поэтому `implementation Target` может добавить в конечный тип член `set Nodes`.

Семантика `set`, указателей, `create` и `take` описана в
[адресах и структурах данных](../../docs/efen/memory/addresses.md). `Nodes`
задаёт логические идентификаторы и время жизни узлов. `Nodes.create` атомарно
создаёт члена множества, а `Nodes.take` исключает его и возвращает владеющее
значение `Node`. Выделение, освобождение и физическая форма указателя остаются
работой представления; отдельный пользовательский распределитель памяти в
алгоритме списка не появляется.

Физическое выделение показано двумя перегрузками `Nodes.allocate`:

```efen
fn allocate(
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Nodes.Reservation

fn allocate(
    count: Size,
    zeroed: Bool = false,
    alignment: Alignment = Node.alignment
) -> own Nodes.RangeReservation
```

Первая резервирует память для одного `Node`, вторая — для `count` узлов.
Результат ещё не является членом `Nodes` и не имеет `Nodes.Pointer`.
`Nodes.create` принимает одноэлементную резервацию, инициализирует в ней `Node`
и только затем включает его в логическое множество. Неиспользованная резервация
сама возвращает память своему представлению.

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

        @constructor
        public fn init -> Self {
            return self
        }

        public fn count -> Size {
            return Nodes.count
        }

        fn checkIndex(index: Size) {
            if index >= Nodes.count {
                throw BoundsError(index, Nodes.count)
            }
        }

        fn checkInsertIndex(index: Size) {
            if index > Nodes.count {
                throw BoundsError(index, Nodes.count)
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
            let memory = Nodes.allocate(alignment: Node.alignment)

            region suspend Nodes.reachable {
                region suspend tail {
                    let node = Nodes.create(
                        take memory,
                        value: take value,
                        next: null
                    )

                    if tail == null {
                        head = take node
                        tail = head
                    } else {
                        tail!.next = take node
                        tail = tail!.next
                    }
                }
            }
        }

        public fn insert(index: Size, value: own Target.Element) {
            checkInsertIndex(index)

            if index == Nodes.count {
                append(take value)
                return
            }

            if index == 0 {
                let memory = Nodes.allocate(alignment: Node.alignment)

                region suspend Nodes.reachable {
                    region suspend tail {
                        let node = Nodes.create(
                            take memory,
                            value: take value,
                            next: null
                        )
                        node.next = take head
                        head = take node
                    }
                }
                return
            }

            let before = nodeAt(index - 1)
            let memory = Nodes.allocate(alignment: Node.alignment)

            region suspend Nodes.reachable {
                region suspend tail {
                    let node = Nodes.create(
                        take memory,
                        value: take value,
                        next: null
                    )
                    node.next = take before.next
                    before.next = take node
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

                        var removed = Nodes.take(take victim)
                        result = take removed.value
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

                    var removed = Nodes.take(take victim)
                    result = take removed.value
                }
            }

            return take result
        }

        public fn slice(first: Size, last: Size) -> ArraySlice<Self> {
            if first > last || last > Nodes.count {
                throw RangeError(first, last, Nodes.count)
            }
            return ArraySlice(owner: &self, first: first, last: last)
        }

        public fn readSlice(first: Size, last: Size)
            -> ArrayReadSlice<Self>
        {
            if first > last || last > Nodes.count {
                throw RangeError(first, last, Nodes.count)
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
бросить исключение, но в этот момент список ещё не изменён. `Nodes.create`
принимает готовую резервацию; при ошибке он не публикует узел. После успешного
`create` остаются только безотказные переносы указателей.

Новый узел сначала создаётся с пустым `next`. Только после успешного `create`
алгоритм переносит в него `head` или `before.next`. Поэтому отказ создания не
может забрать и уничтожить уже опубликованный суффикс списка.

`region suspend` не отменяет проверку памяти, происхождения ссылки или прав. Он
временно разрешает нарушить два явно названных логических условия и требует
восстановить их на каждом выходе. Если `Nodes.create` бросает, старые `head`,
`tail` и множество `Nodes` остаются согласованными.

При удалении владеющий указатель сначала переносится из `head` или
`before.next`, продолжение цепочки занимает освободившееся место, затем
`Nodes.take` исключает узел из множества. Затем `take removed.value` переносит
`Element` из уже изъятого узла. Пользовательский деструктор результата работает
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
count() == Nodes.count
каждый узел Nodes достижим из head по next
count() == 0  <=>  head == null && tail == null
count() > 0   =>   tail — последний узел цепочки
nodeAt(i).value == логический elementAt(i)
append, insert и remove сохраняют порядок Array
iterator выдаёт позиции 0 ..< count
```

Индексирование стоит `O(index + 1)`, последовательный обход — `O(count)`, а
`append` после успешного `Nodes.create` — `O(1)`. Эти различия допустимы;
изменение логической последовательности недопустимо.

## Оставшиеся открытые формы

В коде нет дополнительной синтаксической формы для управления узлами: `set`,
`Nodes.Pointer`, `Nodes.create`, `Nodes.take`, `take removed.value` и предикат
достижимости уже показаны в нормативных примерах памяти.

Открыты точные сигнатуры предложенного `Nodes.allocate` и общих кандидатных
программных интерфейсов представления: `implementation Target`,
`DefinitionPlan`, `PhysicalSchema`, `ArrayPlace`, `PreparedReplacement`,
`HardConstraints` и `CostHints`.
