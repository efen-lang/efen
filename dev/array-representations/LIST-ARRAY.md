# `Array` в виде односвязного списка

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Приведён эскиз
библиотеки на `Efen`, а не программа для уже существующего компилятора. Имена
вспомогательных типов и методов являются кандидатами программного интерфейса.
Новых ключевых слов они не вводят.

## Что остаётся массивом

`Array<Element, List>` является конкретным типом массива. Представление меняет
физическое устройство и стоимость операций, но сохраняет логический контракт:

- элементы имеют порядок `0 ..< count`;
- чтение и запись по индексу обращаются к элементу в этой позиции;
- `append` добавляет элемент в конец;
- `insert` сдвигает старый суффикс вправо;
- `remove` удаляет позицию и сдвигает суффикс влево;
- прямой обход выдаёт элементы в порядке индексов;
- срез обозначает логический диапазон того же массива.

Различие с `Array<Element, Contiguous>` наблюдается в типе и стоимости:
индексация списка имеет `O(index + 1)`, а последовательный обход — `O(count)`.

## Кандидаты программного интерфейса

Следующие имена нужны для цельного эскиза, но ещё не являются существующим
программным интерфейсом `Efen`:

- `Representation<Target>` — известный компилятору контракт аспекта
  представления;
- `implementation Target` — блок, материализующий строящийся конечный тип;
- `NodePool<Node>` — приватный библиотечный владелец физических узлов;
- `ArrayPlace<Element>` — логическое место элемента с происхождением и правами;
- `IndexedSequence<Element>` и `ResizableSequence<Element>` — общий базовый
  контракт и отдельная возможность изменения длины;
- `ArrayReadSlice<Array>` и `ArraySlice<Array>` — общие представления диапазона
  позиций, пересылающие операции исходному массиву;
- `compiler::DefinitionPlan` — кандидат API, через который аспект добавляет
  соответствия обычным контрактам;
- `PreparedNode` и `PreparedReplacement` — владельцы подготовленного состояния;
- `Mutation.commit` — фиксация связанных изменений без возможности отказа;
- `CostHints` и `HardConstraints` — доступные во время компиляции описания
  стоимости и обязательных ограничений.

`NodePool` не является частью логического `Array`. Он выделяет узел, возвращает
устойчивую физическую ссылку, уничтожает подготовленный узел при отказе и
освобождает узел после логического удаления. Его `prepare` может бросить
исключение памяти; `commit` и `retire` после успешной подготовки не бросают и не
приостанавливаются.

`ArrayPlace` не обещает машинный адрес. Для этого представления он содержит
ссылку на найденный узел. Оператор `[]` выбирает обычные методы контракта
`Array`; сам оператор не знает о списке.

Базовый `Array` уже требует `IndexedSequence`. Изменение длины и получение
сохраняемой ссылки являются отдельными обычными контрактами:

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

## Полный эскиз аспекта

```efen
aspect List<Target> conforms Representation<Target> {
    meta fn define(plan: compiler::DefinitionPlan) {
        plan.addConformance(Target, ResizableSequence<Target.Element>)
        plan.addConformance(Target, BorrowedElements<Target.Element>)
    }

    implementation Target {
        struct Node {
            var value: Target.Element
            var next: own NodePool<Node>.Pointer? = null
        }

        struct ReadCursor {
            let owner: &read Target
            var current: read NodePool<Node>.Pointer?

            fn next -> (&read[owner] Target.Element)? {
                if current == null {
                    return null
                }

                let node = current!
                current = node.next
                return &read[owner] node.value
            }
        }

        let nodes: NodePool<Node>
        var head: own NodePool<Node>.Pointer? = null
        var tail: read write NodePool<Node>.Pointer? = null
        var length: Size = 0

        @constructor
        public fn init -> Self {
            self.nodes = NodePool<Node>()
            return self
        }

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

        fn nodeAt(index: Size) -> read write NodePool<Node>.Pointer {
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
                owner: self,
                logicalIndex: index,
                physical: node
            )
        }

        public fn read(index: Size) -> Target.Element
            where Target.Element: Copyable
        {
            return place(index).value.copy()
        }

        public fn replace(
            index: Size,
            value: own Target.Element
        ) -> Target.Element {
            let destination = place(index)
            let replacement = PreparedReplacement(
                destination: destination,
                value: take value
            )

            return Mutation.commit(take replacement)
        }

        public fn append(value: own Target.Element) {
            let nextCount = checkedAdd(length, 1)
            let prepared = nodes.prepare(
                Node(value: take value)
            )

            Mutation.commit {
                let node = nodes.publish(take prepared)

                if tail == null {
                    head = take node
                    tail = head
                } else {
                    tail!.next = take node
                    tail = tail!.next
                }

                length = nextCount
            }
        }

        public fn insert(
            index: Size,
            value: own Target.Element
        ) {
            checkInsertIndex(index)

            if index == length {
                append(take value)
                return
            }

            let nextCount = checkedAdd(length, 1)
            let prepared = nodes.prepare(
                Node(value: take value)
            )

            if index == 0 {
                Mutation.commit {
                    let node = nodes.publish(take prepared)
                    node.next = take head
                    head = take node
                    length = nextCount
                }
                return
            }

            let before = nodeAt(index - 1)

            Mutation.commit {
                let node = nodes.publish(take prepared)
                node.next = take before.next
                before.next = take node
                length = nextCount
            }
        }

        public fn remove(index: Size) -> Target.Element {
            checkIndex(index)

            if index == 0 {
                Mutation.commit {
                    let victim = take head!
                    head = take victim.next
                    length -= 1

                    if head == null {
                        tail = null
                    }

                    return nodes.takeValueAndRetire(take victim)
                }
            }

            let before = nodeAt(index - 1)

            Mutation.commit {
                let victim = take before.next!
                before.next = take victim.next
                length -= 1

                if before.next == null {
                    tail = before
                }

                return nodes.takeValueAndRetire(take victim)
            }
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
            return ReadCursor(
                owner: self,
                current: head
            )
        }

        meta fn hardConstraints -> HardConstraints {
            return HardConstraints(
                forwardTraversal: true,
                backwardTraversal: false,
                stableNodeWhileBorrowed: true,
                structuralMutationWhileBorrowed: false
            )
        }

        meta fn costHints -> CostHints {
            return CostHints(
                indexFromFront: linear,
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

Публичные методы принимают общий для `IndexedSequence` индекс `Size`.
Происхождение и права появляются у `ArrayPlace` и среза после проверки границ;
число индекса не становится байтовым смещением.

## Создание и откат

`nodes.prepare` выполняет выделение и конструирует `Node` до изменения `head`,
`tail` и `length`. Если выделение или конструктор `Element` бросает, подготовленный
объект уничтожается и массив остаётся прежним.

Внутри `Mutation.commit` разрешены только заранее подготовленные операции без
возможности отказа. Сначала публикуется узел, затем восстанавливаются связи и
`length`.
Выход из окна проверяет логические условия массива. `PreparedNode` владеет
неопубликованным узлом; если окно не началось, его уничтожение выполняет откат.

`replace` возвращает прежний элемент. Поэтому разрушение старого `Element` не
происходит внутри окна согласованности и может вызвать пользовательский
разрушитель только после публикации нового значения. Поверхностное присваивание

```efen
array[index] = take value
```

понижается в `replace`, после чего вызывающий код уничтожает проигнорированный
результат.

## Удаление и владение

Поле `next` владеет продолжением цепочки. `head` владеет первым узлом, `tail`
только читает последний. Перенос `head` и `next` всегда записан через `take`.

`remove` сначала исключает узел из цепочки и уменьшает `length`, затем
`takeValueAndRetire` переносит `Element` вызывающему и возвращает физический узел
в `NodePool`. Значение не копируется, поэтому операция допустима для
`Movable`, но не `Copyable`, элементов.

Если вызывающий код отбрасывает возвращённое значение, его разрушитель
выполняется уже после восстановления массива. Представление не удерживает
внутреннее изменяемое заимствование `NodePool` во время работы пользовательского
разрушителя.

## Индексация, место и заимствование

`place(index)` идёт от `head` и возвращает логическое место найденного элемента.
Базовые операции `read` и `replace` используют это место, но сами по себе не
обещают возможность сохранить ссылку.

`Array<Element, List>` отдельно предоставляет возможность `BorrowedElements`:

```efen
fn borrowRead(index: Size) -> &read[self] Target.Element {
    return &read[self] nodeAt(index).value
}
```

Живая ссылка удерживает структурное заимствование массива. Пока она существует,
`append`, `insert`, `remove` и операция, способная переместить или освободить
узлы, недоступны. Изменение самого элемента возможно только при соответствующих
правах ссылки. Более сильная возможность устойчивого дескриптора может быть
добавлена отдельно и не входит в базовый контракт `Array`.

`ArrayReadSlice` и `ArraySlice` являются заимствованными представлениями
диапазона позиций. Они хранят происхождение массива, начальный индекс и длину,
не копируют узлы и не превращают их в массив ссылок. Базовые `read` и `replace`
среза пересылаются исходному массиву и не требуют возможности получить
`&Element`. Методы заимствования появляются условно при соответствии владельца
`BorrowedElements`.

Структурное заимствование запрещает изменение порядка на время жизни среза.
Оптимизированный обход один раз находит первый узел, затем использует `next`,
поэтому не выполняет повторную индексацию для каждого элемента.

## Итератор и граф компилятора

`ReadCursor.next` является обычной операцией `Efen` и выдаёт читающую ссылку с
происхождением массива. Односвязное представление не предоставляет `prev`;
алгоритм, которому нужен двунаправленный курсор, отклоняется по контракту этой
возможности.

Для обычного цикла компилятор получает:

- граф зависимостей тела;
- физическую схему `head → next`;
- обязательное ограничение, запрещающее обратный переход;
- стоимость последовательного и индексного доступа.

Он может встроить `next` и устранить объект `ReadCursor`. Он не вправе заменить
последовательный обход повторными `nodeAt`, если оценки стоимости показывают
худший план, но неточная стоимость влияет только на скорость. Живость узла,
происхождение ссылки и запрет структурного изменения при заимствовании являются
обязательными ограничениями.

В обычном коде граф сохраняет порядок наблюдаемых действий. В `flow` независимые
операции имеют меньше рёбер, поэтому компилятор может сгруппировать чтения, но
представление не может переставить зависимые записи или пользовательские
эффекты.

## Проверка логического контракта

Для любой последовательности успешных операций должно выполняться:

```text
count == число узлов от head по next
count == 0  <=>  head == null && tail == null
count > 0   =>   tail — последний достижимый узел
elementAt(i) == значение логической позиции i
append(x)   == старая последовательность + [x]
insert(i,x) == prefix(i) + [x] + suffix(i)
remove(i)   == старый elementAt(i), оставшиеся позиции сохраняют порядок
iterator    == elementAt(0), ..., elementAt(count - 1)
```

Эти свойства являются обязательствами `List`. Линейная цена `nodeAt` является
допустимым отличием представления, но изменение порядка или значения элемента —
нарушением контракта `Array`.
