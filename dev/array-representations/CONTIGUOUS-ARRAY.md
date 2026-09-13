# Непрерывный массив постоянной длины

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Приведён эскиз
библиотеки на `Efen`, а не программа для уже существующего компилятора. Имена
вспомогательных типов и методов являются кандидатами программного интерфейса.
Новых ключевых слов они не вводят.

## Цель и границы

`Array<X, Contiguous>` хранит элементы последовательно в одном принадлежащем ему
выделении памяти. Длина устанавливается конструктором и затем не меняется.
Значения элементов можно заменять. Пустой массив допустим.

Это представление проверяет самый простой случай: логический индекс переводится
в положение элемента одного выделения. Сам `Array` остаётся библиотечным типом,
а `Contiguous` — аспектом, достраивающим конкретный тип.

Общий базовый контракт `IndexedSequence` описывает длину, чтение, замену
элементов и срезы. Изменение длины задаёт отдельный обычный контракт
`ResizableSequence`: `append`, `insert` и `remove`. Поэтому
`Array<X, Contiguous>` является полноценным `Array`, но не соответствует
`ResizableSequence`. Он не подменяет отсутствующие операции методами, которые
всегда бросают исключение.

[Динамический непрерывный массив](DYNAMIC-ARRAY.md) отдельно показывает изменение
длины и перевыделение памяти.

## Контракты и используемые операции

Следующий контракт задаёт операции над последовательностью. Квадратные скобки
компилятор связывает с обычными методами конкретного типа; они не вызывают
отдельную встроенную реализацию массива.

```efen
contract IndexedSequence<Element> {
    fn count -> Size
    fn read(index: Size) -> Element where Element: Copyable
    fn replace(index: Size, value: own Element) -> Element
    fn slice(first: Size, last: Size) -> ArraySlice<Self>
}

contract BorrowedElements<Element> {
    fn borrowRead(index: Size) -> &read[self] Element
    fn borrowWrite(index: Size) -> &[self] Element
}

struct Array {
    generic Element: Type
    generic R<T>: Representation<T>

    conforms IndexedSequence<Element>
    use R<Self>
}
```

`replace` возвращает прежнее значение с передачей владения. Это позволяет
отделить замену места от последующего уничтожения вытесненного значения.
Обычное присваивание может уничтожить этот результат по общим правилам языка.

В сигнатуре `slice` показана форма для изменяемого получателя. В эскизе также
есть `readSlice` — только читающая форма той же операции над диапазоном.
Обычное разрешение диапазона выбирает форму по правам получателя и не
усиливает эти права. Срез заимствует объект массива, но не требует возможности
длительно заимствовать отдельный элемент.

`BorrowedElements` — кандидат имени обычного контракта возможности `Borrow`.
Он не входит в обязательные требования к любому представлению массива.
`Contiguous` его выполняет: ссылка на элемент может удерживать существующее
место в памяти. Сам тип ссылки остаётся логическим и сохраняет происхождение.

Нижняя библиотека памяти в этом эскизе предоставляет следующие типы. Их
реализация является отдельной задачей; отсутствие отдельной ветки для массива
в компиляторе не устраняет необходимость в системном выделении памяти.

| Кандидат интерфейса | Обязательный смысл |
|---|---|
| `Allocator` | Обычный сохраняемый дескриптор службы выделения памяти |
| `allocateSlots<T>(count)` | Выделить достаточно правильно выровненных мест для `count` значений, пока не инициализированных |
| `OwnedSlots<T>` | Владеть выделением и учитывать инициализированный префикс |
| `initializeNext(value)` | Перенести значение в следующее свободное место и увеличить инициализированный префикс |
| `copyAt(index)` | Скопировать инициализированное значение; требует `Copyable` |
| `exchangeAt(index, value)` | Без отказа обменять подготовленное значение с инициализированным местом и вернуть прежнее |
| `borrowReadAt`, `borrowWriteAt` | Выдать ссылку с происхождением и необходимыми правами |
| `initializedCount` | Количество существующих значений, не количество зарезервированных мест |

`OwnedSlots` хранит собственные сведения для освобождения памяти и удерживает
необходимую связь со службой выделения. Он не хранит ссылку на поле
перемещаемого объекта `Array`. Его уничтожение обрабатывает только
инициализированные значения и затем освобождает выделение ровно один раз.
Для этого примера освобождение выделения не бросает исключений, не
приостанавливается и не вызывает пользовательский код. Эти свойства обязан
обеспечивать выбранный `Allocator`, а не только тип элемента.

Для простоты этот конкретный аспект принимает элементы, у которых перенос
владения и освобождение не бросают исключений, не приостанавливаются и не
вызывают пользовательский код. Назовём этот проверяемый обычный контракт
`PlainLifetime`. Это ограничение примера, а не свойство всех типов `Efen` и не
новое ограничение общего `Array`. Копирование и построение элемента могут
бросать исключения.

## Аспект и физические поля

Единственное поле представления — `slots`. Оно содержит дескриптор выделения
и длину инициализированного префикса. Отдельная копия длины в массиве не нужна.

```efen
aspect Contiguous<Target> conforms Representation<Target> {
    meta fn define(plan: compiler::DefinitionPlan) {
        plan.expectGenericType(Target, "Element")
        plan.expectConformance(Target.Element, PlainLifetime)
        plan.addConformance(Target, BorrowedElements<Target.Element>)
        plan.registerResolver(Target, contiguousIndexing)
        plan.registerSchema(Target, contiguousSequenceSchema)
    }

    implementation Target {
        var slots: OwnedSlots<Target.Element>

        @constructor
        public fn init(
            allocator: Allocator,
            count: Size,
            make: (Size) -> Target.Element
        ) -> Self {
            var pending = allocator.allocateSlots<Target.Element>(count)

            for index in 0..<count {
                let value = make(index)
                pending.initializeNext(take value)
            }

            self.slots = take pending
            return self
        }

        public fn count -> Size {
            return self.slots.initializedCount
        }

        fn checkIndex(index: Size) {
            if index >= self.count() {
                throw BoundsError(index, self.count())
            }
        }

        public fn read(index: Size) -> Target.Element
            where Target.Element: Copyable
        {
            self.checkIndex(index)
            return self.slots.copyAt(index)
        }

        public fn replace(
            index: Size,
            value: own Target.Element
        ) -> Target.Element {
            self.checkIndex(index)
            return self.slots.exchangeAt(index, take value)
        }

        public fn borrowRead(index: Size) -> &read[self] Target.Element {
            self.checkIndex(index)
            return self.slots.borrowReadAt(index)
        }

        public fn borrowWrite(index: Size) -> &[self] Target.Element {
            self.checkIndex(index)
            return self.slots.borrowWriteAt(index)
        }

        public fn slice(first: Size, last: Size) -> ArraySlice<Self> {
            return ArraySlice(owner: &self, first: first, last: last)
        }

        public fn readSlice(first: Size, last: Size) -> ArrayReadSlice<Self> {
            return ArrayReadSlice(owner: &read self, first: first, last: last)
        }

        public fn iterator -> ArrayIterator<Self> {
            return ArrayIterator(owner: &read self, cursor: 0)
        }

        public fn reverseIterator -> ArrayIterator<Self> {
            return ArrayIterator(owner: &read self, cursor: self.count())
        }
    }
}
```

`define`, `DefinitionPlan` и его методы — обозначения кандидатов обычного
программного интерфейса компилятора. Первый шаг проверяет параметры и
ограничения, затем регистрирует разрешение выражений и описание хранения.
Объявления из `implementation Target` входят в строящийся конечный тип.
Законченные методы проверяются до завершения типа и анализа зависимых тел.

`contiguousIndexing` обозначает реализацию уже общего разрешения операторов и
членов; `contiguousSequenceSchema` — описание из раздела об оптимизации ниже.
Это не новые встроенные точки компилятора, предназначенные только для `Array`.
Точная запись регистрации требует отдельного определения программного
интерфейса; здесь задано её содержание.

Конструктор вызывает `make(index)` ровно один раз для каждого индекса в
возрастающем порядке. Если выделение или очередной вызов падает, `pending`
уничтожает только уже полученные значения. Незаконченный `Self` наружу не
возвращается. Побочные действия уже выполненных вызовов `make` не откатываются.

## Индексирование и места полей

Разрешение сохраняет контекст всего обращения:

| Выражение | Смысл после разрешения |
|---|---|
| `let x = array[i]` | Проверить индекс и прочитать значение; копирование требует `Copyable` |
| `array[i] = take x` | Проверить индекс, перенести новое значение в место, обработать прежнее значение |
| `array[i].a` | Проверить индекс, получить логическое место элемента и проекцию поля `a` |
| `array[i].a = value` | Записать только поле `a` по общим правилам доступа к этому полю |
| `&array[i]` | Вызвать доступ для заимствования с необходимыми правами |
| `array[first..<last]` | Создать обычную структуру среза |

Вычисления получателя и индекса не дублируются. Обращение к полю не обязано
сначала копировать целый элемент. Если поле имеет пользовательский способ
чтения или записи, разрешение сохраняет этот способ, а не обходит его прямым
доступом к байтам.

```efen
struct X {
    var a: Int
    var b: Float
}

var array = Array<X, Contiguous>(
    allocator: allocator,
    count: 4,
    make: (index) => X(a: index.toInt(), b: 0.0)
)

array[2].a = 10
let item = array[2]
var part = array[1..<3]
part[0].b = 2.0
```

`index.toInt()` в примере является проверяемым преобразованием. Переполнение,
как и любое исключение из `make`, прерывает конструирование.

Отдельное `take array[i]`, оставляющее навсегда неинициализированное место,
не выполняет контракт этого фиксированного массива. Для передачи прежнего
значения существует `replace`. Временное извлечение возможно только при
доказанном восстановлении места до любой точки наблюдения; удаление элемента
со сдвигом принадлежит контракту изменения длины.

## Срезы как обычные структуры

Срез хранит ссылку на конкретный массив и полуинтервал. Он не копирует элементы
и не владеет отдельным выделением. Для обеих структур достаточно
`A: IndexedSequence<A.Element>`: чтение вызывает `owner.read`, а замена при
наличии прав — `owner.replace`. Ни одна из этих операций не выдаёт ссылку
на элемент.

Только методы `borrowRead` и `borrowWrite` дополнительно требуют
`BorrowedElements`. У представления без этой возможности остаются срезы,
чтение и запись через них. Ссылка на сам объект массива и ссылка на его
элемент — разные требования.

```efen
struct ArrayReadSlice<A>
    where A: IndexedSequence<A.Element>
{
    let owner: &read A
    let first: Size
    let length: Size

    @constructor
    fn init(owner: &read A, first: Size, last: Size) -> Self {
        if first > last || last > owner.count() {
            throw RangeError(first, last, owner.count())
        }

        self.owner = owner
        self.first = first
        self.length = last - first
        return self
    }

    fn count -> Size {
        return self.length
    }

    fn read(index: Size) -> A.Element where A.Element: Copyable {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.read(self.first + index)
    }

    fn borrowRead(index: Size) -> &read[owner] A.Element
        where A: BorrowedElements<A.Element>
    {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.borrowRead(self.first + index)
    }
}

struct ArraySlice<A>
    where A: IndexedSequence<A.Element>
{
    let owner: &A
    let first: Size
    let length: Size

    @constructor
    fn init(owner: &A, first: Size, last: Size) -> Self {
        if first > last || last > owner.count() {
            throw RangeError(first, last, owner.count())
        }

        self.owner = owner
        self.first = first
        self.length = last - first
        return self
    }

    fn count -> Size {
        return self.length
    }

    fn borrowRead(index: Size) -> &read[owner] A.Element
        where A: BorrowedElements<A.Element>
    {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.borrowRead(self.first + index)
    }

    fn borrowWrite(index: Size) -> &[owner] A.Element
        where A: BorrowedElements<A.Element>
    {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.borrowWrite(self.first + index)
    }

    fn read(index: Size) -> A.Element where A.Element: Copyable {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.read(self.first + index)
    }

    fn replace(index: Size, value: own A.Element) -> A.Element {
        if index >= self.length {
            throw BoundsError(index, self.length)
        }
        return self.owner.replace(self.first + index, take value)
    }
}
```

Ссылки, сохранённые в полях среза, удерживают заимствование исходного объекта по
обычным правилам `Efen`. Сам срез и полученные из него ссылки не переживают
исходный массив. Из проверок конструктора и индекса следует, что
`first + index` не переполняется и остаётся в границах исходного массива.

`ArrayReadSlice` разрешает только чтение; `ArraySlice` сохраняет права
изменяемого получателя и разрешает `replace`. Даже когда отдельный элемент
нельзя заимствовать, оба вида могут сохранять ссылку на обычный объект
владельца и обращаться к его методам.

Для срезов используется то же общее разрешение индексирования по их методам.
Наличие подходящих методов не означает новой специальной конструкции языка.

## Двунаправленный итератор

Состояние итератора — читающее заимствование массива и позиция между
элементами. `next` возвращает следующий элемент и увеличивает позицию;
`prev` сначала уменьшает позицию и возвращает предыдущий элемент.

```efen
struct ArrayIterator<A>
    where A: IndexedSequence<A.Element>, A: BorrowedElements<A.Element>
{
    let owner: &read A
    var cursor: Size

    @constructor
    fn init(owner: &read A, cursor: Size) -> Self {
        if cursor > owner.count() {
            throw BoundsError(cursor, owner.count())
        }
        self.owner = owner
        self.cursor = cursor
        return self
    }

    fn next -> (&read[owner] A.Element)? {
        if self.cursor == self.owner.count() {
            return null
        }

        let index = self.cursor
        let result = self.owner.borrowRead(index)
        self.cursor += 1
        return result
    }

    fn prev -> (&read[owner] A.Element)? {
        if self.cursor == 0 {
            return null
        }

        let index = self.cursor - 1
        let result = self.owner.borrowRead(index)
        self.cursor = index
        return result
    }
}
```

Скобки в типе результата существенны: необязательной является ссылка, а не
значение по ссылке. Возвращённая ссылка происходит из `owner`, а не из
изменяемого поля `cursor`. При ошибке получения элемента позиция не меняется.

Контракты `Iterable` и `Iterator` связывают эти обычные методы с обходом.
Наличие `prev` означает выполнение дополнительного двунаправленного контракта.
Для явно сохраняемого итератора структура существует как значение; при
непосредственном обходе компилятор может устранить её.

## Исключения, владение и инварианты

На каждой доступной внешнему коду границе:

1. существует ровно `count()` инициализированных элементов;
2. каждый элемент занимает своё логическое место;
3. длина равна длине, заданной конструктором;
4. выделение имеет достаточный размер и правильное выравнивание;
5. каждое владеющее значение уничтожается ровно один раз;
6. действующие ссылки имеют нужные права и живое происхождение.

Проверки размера и выравнивания принадлежат `allocateSlots`, включая
переполнение произведения количества на размер элемента. Количество элементов
не выводится из количества байтов: элементы нулевого размера сохраняют
логические позиции и собственные события времени жизни.

`read` может бросить исключение при проверке границ или копировании. Сохранённый
массив при этом не меняется. `replace` проверяет границы до изменения, затем
выполняет допустимый для `PlainLifetime` перенос. Если индекс неверен, владение
переданным аргументом обрабатывается по обычным правилам вызова с `own`; это не
обещание вернуть аргумент вызывающему.

Длина постоянна, но уничтожение самого массива или замена его владельца всё
равно конфликтует с живым заимствованием. Непрерывное хранение не отменяет
проверку владения и не превращает любую ссылку в разрешённый внешний адрес.

## Стоимость

Пусть `n` — длина, а `s` — размер физического элемента с учётом шага размещения.
Стоимость пользовательского построения и копирования учитывается отдельно.

| Операция | Стоимость |
|---|---|
| Создание | `O(n)` и одно выделение под элементы |
| Получение длины | `O(1)` |
| Вычисление места элемента | `O(1)` |
| Чтение значения | `O(1)` адресации плюс стоимость копирования |
| Замена | `O(1)` адресации плюс стоимость переноса значения |
| Создание среза | `O(1)`, без копирования элементов |
| `next`, `prev` | `O(1)` на переход |
| Полный обход | `O(n)` |
| Память | `n * s` плюс постоянный дескриптор |
| Увеличение длины | Не входит в контракт этого конкретного типа |

## Схема и работа компилятора

Аспект сообщает через обычный программный интерфейс компилятора:

- элементы представлены строками одного выделения;
- строке с логическим номером `i` соответствует место `i`;
- поля строки имеют известные проекции;
- переходы вперёд и назад изменяют логический номер на единицу;
- длина и владелец неизменны в течение заимствованного обхода;
- произвольный и последовательный доступ имеют указанные оценки стоимости.

Обязательные сведения о границах, происхождении и допустимых заимствованиях
отделяются от оценок. Компилятор совмещает их с графом вычислений программы.
Он может убрать повторные проверки индекса, встроить переходы итератора и
читать только используемые поля. Векторизация допустима лишь при подходящих
зависимостях, выравнивании и эффектах операций.

В обычном коде сохраняется порядок наблюдаемых действий. `flow` может разрешить
больше перестановок, но не отменяет зависимости или правила владения.

Логический алгоритм не вычисляет байтовый адрес. Нижняя реализация
`OwnedSlots` может свести место к `base + index * stride`, а проекцию поля —
к добавлению его смещения. Эти действия локализованы в проверяемой библиотеке
памяти и её системной границе.
