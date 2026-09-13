# `Array` в виде двусвязного списка

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Приведён эскиз
библиотеки на `Efen`, а не программа для уже существующего компилятора. Имена
вспомогательных типов и методов являются кандидатами программного интерфейса.
Новых ключевых слов они не вводят.

## Задача представления

`Array<Element, DoubleLinkedList>` сохраняет ту же логическую упорядоченную
последовательность, что `Array<Element, Contiguous>` и `Array<Element, List>`.
Физически каждый элемент лежит в отдельном узле с переходами `next` и `prev`.

Представление получает следующие свойства:

- последовательный обход вперёд и назад имеет `O(count)`;
- поиск позиции `i` имеет `O(min(i + 1, count - i))`;
- добавление и удаление уже найденного узла имеют `O(1)`;
- физический адрес узла не является логическим индексом;
- изменение связей не меняет смысл позиций массива.

## Кандидаты программного интерфейса

Следующие имена являются кандидатами библиотечных контрактов или контрактов,
известных компилятору:

- `Representation<Target>` и `implementation Target`;
- `NodePool<Node>` и его устойчивый `Pointer`;
- `ArrayPlace<Element>`;
- `IndexedSequence<Element>` и `ResizableSequence<Element>`;
- `ArrayReadSlice<Array>` и `ArraySlice<Array>`;
- `compiler::DefinitionPlan` — кандидат API добавления соответствий обычным
  контрактам;
- `PreparedNode`, `PreparedReplacement` и `PreparedLinks`;
- `Mutation.commit`;
- `CostHints` и `HardConstraints`.

`PreparedLinks` получает право записи во все затрагиваемые узлы и корни,
запоминает конечные значения `head`, `tail`, `next`, `prev` и `length`, а затем
публикует их одной фиксацией без возможности отказа. Это кандидат общего
механизма подготовленного изменения, а не специальная инструкция двусвязного
списка.

Базовый `Array` уже требует `IndexedSequence`. Этот аспект отдельно добавляет
`ResizableSequence<Element>` с `append`, `insert(Size, own Element)` и
`remove(Size) -> Element`, а также `BorrowedElements<Element>` с читающим и
изменяемым заимствованием элемента.

## Полный эскиз аспекта

```efen
aspect DoubleLinkedList<Target> conforms Representation<Target> {
    meta fn define(plan: compiler::DefinitionPlan) {
        plan.addConformance(Target, ResizableSequence<Target.Element>)
        plan.addConformance(Target, BorrowedElements<Target.Element>)
    }

    implementation Target {
        struct Node {
            var value: Target.Element

            var next: own NodePool<Node>.Pointer? = null {
                next == null || next!.prev == self
            }

            var prev: read NodePool<Node>.Pointer? = null {
                prev == null || prev!.next == self
            }
        }

        struct ReadCursor {
            let owner: &read Target
            var left: read NodePool<Node>.Pointer?
            var right: read NodePool<Node>.Pointer?

            fn next -> (&read[owner] Target.Element)? {
                if right == null {
                    return null
                }

                let node = right!
                left = node
                right = node.next
                return &read[owner] node.value
            }

            fn prev -> (&read[owner] Target.Element)? {
                if left == null {
                    return null
                }

                let node = left!
                right = node
                left = node.prev
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

            if index <= length / 2 {
                var current = head!
                var position: Size = 0

                while position < index {
                    current = current.next!
                    position += 1
                }

                return current
            }

            var current = tail!
            var position = length - 1

            while position > index {
                current = current.prev!
                position -= 1
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
            let replacement = PreparedReplacement(
                destination: place(index),
                value: take value
            )

            return Mutation.commit(take replacement)
        }

        public fn append(value: own Target.Element) {
            let nextCount = checkedAdd(length, 1)
            let prepared = nodes.prepare(
                Node(value: take value)
            )

            var links = PreparedLinks(
                owner: self,
                before: tail,
                inserted: prepared.pointer,
                after: null,
                nextCount: nextCount
            )

            Mutation.commit {
                let node = nodes.publish(take prepared)
                PreparedLinks.publish(
                    take links,
                    inserted: take node
                )
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

            let after = nodeAt(index)
            let before = after.prev
            let nextCount = checkedAdd(length, 1)
            let prepared = nodes.prepare(
                Node(value: take value)
            )
            var links = PreparedLinks(
                owner: self,
                before: before,
                inserted: prepared.pointer,
                after: after,
                nextCount: nextCount
            )

            Mutation.commit {
                let node = nodes.publish(take prepared)
                PreparedLinks.publish(
                    take links,
                    inserted: take node
                )
            }
        }

        public fn remove(index: Size) -> Target.Element {
            let victim = nodeAt(index)
            var links = PreparedLinks.removal(
                owner: self,
                before: victim.prev,
                removed: victim,
                after: victim.next,
                nextCount: length - 1
            )

            Mutation.commit {
                let removed = PreparedLinks.publishRemoval(take links)
                return nodes.takeValueAndRetire(take removed)
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
                left: null,
                right: head
            )
        }

        public fn reverseIterator -> ReadCursor {
            return ReadCursor(
                owner: self,
                left: tail,
                right: null
            )
        }

        meta fn hardConstraints -> HardConstraints {
            return HardConstraints(
                forwardTraversal: true,
                backwardTraversal: true,
                stableNodeWhileBorrowed: true,
                structuralMutationWhileBorrowed: false,
                reciprocalLinks: true
            )
        }

        meta fn costHints -> CostHints {
            return CostHints(
                index: linearFromNearestEnd,
                sequentialForward: linearTotal,
                sequentialBackward: linearTotal,
                append: constant,
                insertAfterLocatedNode: constant,
                removeLocatedNode: constant
            )
        }
    }
}
```

Методы без параметров записаны без `()`: `init`, `next`, `prev`, `iterator`,
`reverseIterator`, `hardConstraints` и `costHints`.

Публичные методы принимают общий для `IndexedSequence` индекс `Size`.
Происхождение и права появляются у `ArrayPlace` и среза после проверки границ;
число индекса не является физическим адресом или номером узла `NodePool`.

## Согласованность `next` и `prev`

Физический закон узлов имеет две стороны:

```text
a.next == b  =>  b.prev == a
b.prev == a  =>  a.next == b
head != null => head.prev == null
tail != null => tail.next == null
```

Обычная последовательность присваиваний временно нарушила бы этот закон.
`PreparedLinks` сначала вычисляет конечную конфигурацию и получает все нужные
права. `publish` меняет обе стороны и корни в окне без возможности отказа,
после которого компилятор повторно проверяет предикаты.

Для вставки между `before` и `after` конечное состояние равно:

```text
before.next = inserted   или head = inserted
inserted.prev = before
inserted.next = after
after.prev = inserted    или tail = inserted
length = old length + 1
```

Для удаления выполняется обратная операция. `PreparedLinks` не владеет
`Element`; он управляет только физическими ссылками и правами на их места.

## Создание, исключения и владение

`nodes.prepare` выделяет память и конструирует значение до изменения списка. При
ошибке он уничтожает уже инициализированные части. После подготовки
`nodes.publish`, `links.publish` и изменение `length` не бросают, не
приостанавливаются и не вызывают пользовательский код.

`next` является владеющей связью цепочки. `prev` — невладеющая обратная ссылка.
`head` владеет первым узлом, `tail` только читает последний. Такое распределение
не создаёт цикла владения.

`remove` переносит `Element` из исключённого узла и возвращает его вызывающему.
Копирование не требуется. Разрушитель отброшенного результата запускается после
восстановления связей и освобождения внутренних изменяемых заимствований.

`replace` также возвращает вытесненное значение. Поверхностное присваивание
уничтожает его после публикации нового элемента. Это сохраняет корректность при
повторном входе из разрушителя.

## Индексация и логическое место

`nodeAt` выбирает путь во время выполнения:

```text
index <= length / 2 → head, затем next
иначе               → tail, затем prev
```

Результатом `place` остаётся логическое место позиции массива. Оно не раскрывает
`NodePool.Pointer` пользователю. `read`, `replace`, доступ к полю и `take`
используют это место по контракту `Array`.

Базовый контракт чтения и записи не обещает сохранить `&Element`.
Представление отдельно предоставляет `BorrowedElements` и логическую ссылку на
поле `value` узла. Живое заимствование запрещает структурное изменение массива;
поэтому удаление узла не может обесценить ссылку. Возможность устойчивого
дескриптора потребовала бы отдельного контракта и не выводится из
двусвязности.

`ArrayReadSlice` и `ArraySlice` являются представлениями диапазона позиций с
происхождением массива и границами. Их `read` и `replace` не требуют
`BorrowedElements`; методы выдачи ссылок доступны условно. Пока срез жив,
изменение порядка запрещено. Представление может использовать первый и
последний узлы для быстрого двунаправленного обхода, но это физическая
оптимизация: логический смысл среза остаётся диапазоном позиций.

## Итераторы `next` и `prev`

`ReadCursor` соответствует обычному `Iterator` через `next` и дополнительному
контракту двунаправленного курсора через `prev`. `iterator` начинает перед
прямым обходом с `head`, `reverseIterator` — перед обратным обходом с `tail`.

Сохранённый курсор является обычным значением `Efen`. При непосредственном цикле
компилятор может встроить переход и убрать объект курсора. Он не синтезирует
`prev`: наличие обратного перехода является обязательной возможностью
представления.

Для операции над диапазоном компилятор получает граф требуемых чтений и записей.
Оценки стоимости позволяют выбрать начало, ближайшее к диапазону, и направление
обхода. Если программа требует установленный порядок эффектов, граф запрещает
его обратить. В `flow` независимые вычисления могут иметь меньше рёбер, но
предикаты связей, происхождение и заимствование остаются обязательными
ограничениями.

## Сравнение с другими представлениями

| Операция | `Contiguous` | `List` | `DoubleLinkedList` | `Columnar` | файл |
|---|---:|---:|---:|---:|---:|
| индекс | `O(1)` | `O(i)` | `O(min(i, n-i))` | `O(1)` по колонке | зависит от кеша/I/O |
| прямой обход | `O(n)` | `O(n)` | `O(n)` | `O(n)` по нужным колонкам | поток страниц |
| обратный обход | `O(n)` | нет возможности | `O(n)` | зависит от аспекта | зависит от схемы |
| добавление после подготовки | недоступно | `O(1)` | `O(1)` | фиксация нескольких колонок | зависит от файла |
| устойчивый физический узел | нет | да | да | нет общего узла | закреплённая страница |

Таблица описывает стоимость и физические возможности. Все пять типов обязаны
возвращать одинаковые логические значения и сохранять порядок `Array`.

## Проверка логического контракта

Для каждого опубликованного состояния:

```text
count == число узлов, достижимых от head по next
count == число узлов, достижимых от tail по prev
прямой и обратный порядки взаимно обратны
head.prev == null, если head существует
tail.next == null, если tail существует
каждая пара соседей удовлетворяет reciprocal links
nodeAt(i).value == логический elementAt(i)
append, insert и remove имеют семантику последовательности Array
```

Контракт следует проверять одинаковыми модельными тестами для `Contiguous`,
`List`, `DoubleLinkedList`, `Columnar` и файлового представления. Дополнительные
тесты двусвязного варианта проверяют обход назад, выбор ближайшего конца и
согласованное восстановление обеих ссылок после каждой операции.
