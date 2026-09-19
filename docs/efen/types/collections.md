# Коллекции

Коллекцией называется любая перечисляемая структура данных, которая может содержать ноль или более элементов. 
В `Efen` есть несколько встроенных типов коллекций, каждый из которых имеет свои особенности и применения.

## Enum-массивы

Enum-массив — массив фиксированного размера, индексируемый значениями enum.
Он содержит ровно одно значение одного типа для каждого значения enum.

```efen
enum Stat {
    health
    mana
    stamina
}

var stats: EnumArray<Stat, Int>
stats[.health] = 100
stats[.mana] = 50

for stat in Stat {
    echo stats[stat]
}
```

Enum-массив отличается от словаря: набор ключей известен при компиляции,
каждый ключ всегда имеет позицию, а доступ не требует хеширования. Если значение
может отсутствовать, тип элемента должен быть optional:

```efen
var bonuses: EnumArray<Stat, Int?>
```

Физическое устройство enum-массива определяется его representation. Например,
плотная репрезентация может хранить значения последовательно, а sparse-
репрезентация — только присутствующие optional-значения. Синтаксис
`EnumArray<Key, Value>` является предварительным и намеренно отличается от
словаря `[Key: Value]`. См. [Репрезентации](../representations.md).

## Неизменяемая коллекция `Range`

`Range<T>` — библиотечная владеющая коллекция конечной упорядоченной
последовательности значений `T`. Количество и значения элементов могут
вычисляться во время выполнения. После успешного создания число логических
слотов, их порядок и записанные значения не изменяются; повторения разрешены.

```efen
let priorities = Range([calculatePriority(), 10, 10])

for priority in priorities {
    echo priority
}

let first = priorities[0]

// Запрещено:
// priorities[0] = 5
// priorities[] = 20
// priorities.remove(at: 0)
```

Это свойство типа, а не связывания. `var values: Range<Int>` позволяет
перепривязать целую переменную к другому `Range`, но не изменить слоты живого
экземпляра. `Range` не предоставляет append, insert, remove, clear, reorder,
mutable traversal или `take values[index]`.

### Создание snapshot

Одно написание `Range(...)` объединяет две перегрузки библиотечного constructor:

```efen
class Range<T> {
    @constructor
    fn init(source: own Array<T>) -> Self

    #if T conforms Copyable {
        @constructor
        fn init(source: read Array<T>) -> Self

        @constructor
        fn init<Source: Origin>(source: read Slice<T, Source>) -> Self {
            // Копирует выбранные элементы в собственное storage.
        }
    }
}
```

Именованный аргумент без `take` предоставляет constructor только
непотребляющий доступ. Перегрузка `own` для него не является кандидатом.
`take source`, owning temporary и литерал массива предоставляют владение; при
применимости перегрузка `own` имеет приоритет над временным заимствованием для
`read`. После выбора `own` ошибка владения не вызывает повторного выбора
копирующей перегрузки. Компилятор не вставляет `take` или неявную копию, чтобы
сменить режим.

```efen
var source = [1, 2, 3]

let snapshot = Range(source)       // source сохраняется; создаётся snapshot
source[0] = 9
echo snapshot[0]                   // 1

let moved = Range(take source)     // source потреблён
let loaded = Range(loadValues())   // принимается owning temporary
```

Именованный `source` без `take` никогда не потребляется неявно, даже если у
него есть `own`. Если для независимого snapshot требуется копирование
элементов, операция доступна при `T: Copyable`; `ImplicitlyCopyable` не нужен,
поскольку копирование запрошено явным constructor call. `Range(take source)` и
owning temporary передают стандартный `Array<T>` целиком. Стандартная
representation `Range<T>` обязана принять его backing storage как закрытое
storage без перемещения отдельных элементов и без сохранения изменяемого пути к
слотам. Поэтому эта перегрузка определена для любого допустимого `T` и не
требует `T: Copyable` или `T: Movable`. Альтернативная representation Range
может использовать другую физическую форму только при сохранении того же
безусловного owning constructor contract.

Срез является непотребляющим view исходного storage. Даже `take slice`
потребляет только объект view, но не передаёт владение его элементами, поэтому
создание `Range` из среза использует копирующую перегрузку при `T: Copyable`.

Конструктор не публикует частично готовый результат. В копирующей перегрузке
ошибка уничтожает созданные копии и временный читающий cursor; источник остаётся
у вызывающего. В передающей перегрузке источник уже потреблён, и constructor или
принадлежащий ему cursor уничтожает каждый оставшийся ресурс ровно один раз;
ошибка не восстанавливает потреблённую переменную. Внешние эффекты источника не
откатываются.

Чтение source storage защищается обычными правами или протоколом синхронизации
источника. Несинхронизированная одновременная запись недопустима; constructor не
обещает транзакционный snapshot произвольно изменяемого графа referents.

Неизменяемость поверхностная. Значение слота заменить нельзя, но ссылки внутри
`T` сохраняют собственные права, origin и время жизни; достижимые через них
объекты автоматически не замораживаются.

### Чтение и обход

Индексация и обычный обход конкретного `values` предоставляют
`&read[values] T`. Конкретный `RangeReadCursor<T, values>` соответствует
`Iterator<Item: &read[values] T>` и сохраняет origin storage. Эти операции не
копируют `T` и не требуют `Copyable`:

```efen
for item in priorities {
    // item читает слот priorities
}
```

Потребляющий обход `for item in take values` доступен при `T: Movable` и выдаёт
`T own` через `RangeTakeCursor<T>`. Cursor владеет storage и передаёт каждый
элемент ровно один раз; при досрочном выходе, `return` или исключении он
уничтожает оставшиеся элементы. Срез `values[a..<b]` является читающим невладеющим
`Slice` с origin исходного `Range`. Вызов `Range(slice)` создаёт отдельный
snapshot при наличии требуемого копирования.

Структурное равенство доступно условно при соответствующей операции `T` и
сравнивает длину и попарные значения с учётом порядка и повторений.
Неизменяемость сама по себе не предоставляет `Hashable`, `Copyable` или
`ImplicitlyCopyable`: эти соответствия объявляются отдельно при выполнении их
контрактов. `shared` является правом, а не contract; допустимость межпоточного
использования определяется правами элементов, representation и моделью
управления.

Пустой `Range<T>` разрешён. Создание из произвольного бесконечного источника не
завершится; первый API гарантирует только Array и Slice как источники.

`Range<T>` не является enum, не объявляет значения enum, не участвует в статической
проверке исчерпанности и не служит пространством ключей `EnumArray`. Два
экземпляра с одинаковым `T` имеют один тип независимо от runtime-содержимого.

## Оператор `[]`

Оператор `[]` используется для создания и доступа к элементам коллекций.
Он может применяться к массивам, словарям и другим типам коллекций.

В зависимости от контекста, оператор `[]` может означать:
- Создание коллекции: `let arr = [1, 2, 3]`
- Доступ к элементу по индексу или ключу: `let first = arr[0]`
- Добавление элемента в коллекцию: `arr[] = 4`
- Алиас для типа: `let dict: [String: Int] = ["one": 1, "two": 2]`

## Срезы массивов

Срезы создаются с помощью оператора индексирования `[]` и диапазонов внутри него.
Срезы могут применяться к массивам и другим типам коллекций, которые поддерживают индексацию.

Срез является невладеющим view исходного storage. Операция не выделяет новый
массив и не копирует элементы:

```efen
let values = [10, 20, 30, 40]
let middle = values[1..<3]
```

`middle` хранит диапазон и origin `values`. Его полный тип концептуально
соответствует `Slice<Int, values>`; origin может быть выведен и не обязан
писаться в исходнике. Права доступа к элементам выводятся из прав на источник.
Срез читающего источника не даёт запись, а срез изменяемого источника может
предоставлять изменяемые элементы при сохранении эксклюзивности.

Пока срез используется, операция, способная уничтожить или переместить его
storage либо изменить его representation, должна учитывать живой view. Явное
создание независимого массива выполняется отдельной операцией копирования.

Срез среза сохраняет origin исходного storage и сужает диапазон; он не образует
новую владеющую область памяти.

Синтаксис среза: `array[range]`, где `range` — это любой диапазон (см. раздел "Операторы диапазона" ниже).

Примеры:
```efen
let arr = [10, 20, 30, 40, 50]

// Закрытые диапазоны
let slice1 = arr[1..3]     // [20, 30, 40]
let slice2 = arr[1..<3]    // [20, 30]
let slice3 = arr[1<..3]    // [30, 40]

// Открытые диапазоны
let slice4 = arr[2..]      // [30, 40, 50]
let slice5 = arr[..<3]     // [10, 20, 30]
```

## Оператор `[:]` для словарей

Оператор `[:]` зарезервирован для создания пустых словарей:
```efen
let emptyDict: [String: Int] = [:]
```

Словари с элементами создаются с парами ключ-значение:
```efen
let dict = ["one": 1, "two": 2, "three": 3]
```

## Операторы диапазона

В позиции выражения операторы диапазона создают библиотечный descriptor границ
`Interval`, а не материализованный `Range<T>`. В позиции образца та же запись
является interval-pattern: она проверяет принадлежность границам, не создаёт
runtime-объект и не требует возможности перечисления.

```efen
let bounds = 1..5

for i in 1..5 {
    echo i
}

match value {
    1..5: echo "inside"  // pattern, не constructor Interval
    _: echo "outside"
}
```

Форма границ входит в статический тип, а значения границ вычисляются runtime:

```efen
enum IntervalBound {
    unbounded
    inclusive
    exclusive
}

class Interval {
    generic Element: Type
    generic Lower: IntervalBound = .inclusive
    generic Upper: IntervalBound = .inclusive
}
```

`Interval<T>` благодаря defaults означает две включённые границы. Отсутствие и
включённость границ являются compile-time аргументами, определяемыми оператором;
сами runtime-значения границ в идентичность типа не входят.

### Перечисление интервала

Сравнимость сама по себе не задаёт следующий элемент. Для стандартного
возрастающего обхода используется библиотечный contract:

```efen
contract Steppable<T> {
    fn successor -> T?
}
```

Стандартная реализация обхода дополнительно требует сравнимость, неявное
копирование и перемещение значения. Contract уточняется через `:`, поэтому
составное требование может быть записано явно, например
`contract OrderedSteppable<T> : Comparable<T>, Steppable<T> {}`.

`successor()` возвращает строго следующее представимое значение либо `null` и
никогда не переполняется с переходом к меньшему значению. Стандартные целые
типы используют шаг один; для `Float` стандартный `Steppable` не объявляется.

При `Lower != .unbounded` и `T: Steppable<T>` интервал предоставляет
`Iterable<Item: own T>`. При отсутствующей нижней границе стандартного обхода
нет: `for i in ..5` является ошибкой, хотя `..5` остаётся законным descriptor
для среза и pattern.

Обход всегда возрастает. Если нижняя граница больше верхней, результат пуст.
При равных границах выдаётся один элемент только при включении обеих границ.
Интервал без верхней границы заканчивается, когда `successor()` возвращает
`null`; поэтому `5..` для целого типа завершается на его максимальном значении
без overflow. Реализация закрытой границы не вычисляет `upper + 1`.

### Интервалы с двумя границами

- **`a..b`** — включает `a` и `b` (closed range)
- **`a..<b`** — включает `a`, исключает `b` (half-open range, right-exclusive)
- **`a<..b`** — исключает `a`, включает `b` (half-open range, left-exclusive)
- **`a<..<b`** — исключает `a` и `b` (open range, both exclusive)

### Интервалы без одной границы

- **`a..`** — от `a` (включая) до конца
- **`a<..`** — от `a` (исключая) до конца
- **`..b`** — от начала до `b` (включая)
- **`..<b`** — от начала до `b` (исключая)

### Примеры использования

```efen
// Закрытые диапазоны
let r1 = 1..5      // обе границы включены
let r2 = 1..<5     // правая граница исключена
let r3 = 1<..5     // левая граница исключена
let r4 = 1<..<5    // обе границы исключены

// Открытые диапазоны
let r5 = 5..       // нижняя 5 включена; верхняя не задана
let r6 = 5<..      // нижняя 5 исключена; верхняя не задана
let r7 = ..5       // нижняя не задана; верхняя 5 включена
let r8 = ..<5      // нижняя не задана; верхняя 5 исключена
```

### Диапазоны в срезах массивов

Диапазоны часто используются в срезах массивов:
```efen
let arr = [10, 20, 30, 40, 50]

// Использование различных диапазонов
let slice1 = arr[1..3]     // [20, 30, 40] - включая оба конца
let slice2 = arr[1..<3]    // [20, 30] - исключая правый конец
let slice3 = arr[1<..3]    // [30, 40] - исключая левый конец
let slice4 = arr[1<..<3]   // [30] - исключая оба конца

// Открытые диапазоны
let slice5 = arr[2..]      // [30, 40, 50] - от индекса 2 до конца
let slice6 = arr[2<..]     // [40, 50] - от индекса 3 до конца
let slice7 = arr[..3]      // [10, 20, 30, 40] - от начала до индекса 3 включительно
let slice8 = arr[..<3]     // [10, 20, 30] - от начала до индекса 2
```

## Сравнительная таблица синтаксиса

| Синтаксис                 | Описание                      | Пример                          | Результат            |
|---------------------------|-------------------------------|---------------------------------|----------------------|
| **Литералы коллекций**    |                               |                                 |                      |
| `[]`                      | Пустой массив                 | `let arr = []`                  | `[]`                 |
| `[1, 2, 3]`               | Массив с элементами           | `let arr = [1, 2, 3]`           | `[1, 2, 3]`          |
| `[:]`                     | Пустой словарь                | `let dict: [String: Int] = [:]` | `[:]`                |
| `["a": 1]`                | Словарь с элементами          | `let dict = ["a": 1, "b": 2]`   | `["a": 1, "b": 2]`   |
| **Индексирование**        |
| `arr[i]`                  | Доступ к элементу массива     | `arr[0]`                        | `10`                 |
| `dict[key]`               | Доступ к элементу словаря     | `dict["key"]`                   | `value`              |
| **Диапазоны (выражения)** |
| `a..b`                    | Закрытый интервал             | `1..5`                          | `Interval<Int, .inclusive, .inclusive>` |
| `a..<b`                   | Полуоткрытый справа           | `1..<5`                         | `Interval<Int, .inclusive, .exclusive>` |
| `a<..b`                   | Полуоткрытый слева            | `1<..5`                         | `Interval<Int, .exclusive, .inclusive>` |
| `a<..<b`                  | Открытый с обоих концов       | `1<..<5`                        | `Interval<Int, .exclusive, .exclusive>` |
| `a..`                     | Без верхней границы           | `5..`                           | `Interval<Int, .inclusive, .unbounded>` |
| `a<..`                    | Без верхней границы           | `5<..`                          | `Interval<Int, .exclusive, .unbounded>` |
| `..b`                     | Без нижней границы            | `..5`                           | `Interval<Int, .unbounded, .inclusive>` |
| `..<b`                    | Без нижней границы            | `..<5`                          | `Interval<Int, .unbounded, .exclusive>` |
| **Срезы массивов**        |
| `arr[a..b]`               | Срез включая оба конца        | `arr[1..3]`                     | `[20, 30, 40]`       |
| `arr[a..<b]`              | Срез исключая правый конец    | `arr[1..<3]`                    | `[20, 30]`           |
| `arr[a<..b]`              | Срез исключая левый конец     | `arr[1<..3]`                    | `[30, 40]`           |
| `arr[a<..<b]`             | Срез исключая оба конца       | `arr[1<..<3]`                   | `[30]`               |
| `arr[a..]`                | Срез от `a` до конца          | `arr[2..]`                      | `[30, 40, 50]`       |
| `arr[a<..]`               | Срез от `a+1` до конца        | `arr[2<..]`                     | `[40, 50]`           |
| `arr[..b]`                | Срез от начала до `b`         | `arr[..3]`                      | `[10, 20, 30, 40]`   |
| `arr[..<b]`               | Срез от начала до `b-1`       | `arr[..<3]`                     | `[10, 20, 30]`       |
| **Типы**                  |
| `[Type]`                  | Тип массива                   | `let arr: [Int]`                | Массив целых чисел   |
| `[KeyType: ValueType]`    | Тип словаря                   | `let dict: [String: Int]`       | Словарь строка→число |

### Примечания к таблице

- **Диапазоны в позиции выражения** создают descriptor границ `Interval`; в
  позиции образца та же запись создаёт interval-pattern, а не runtime-значение
- **Срезы** — результат применения диапазона к массиву через индексирование `[]`
- **Оператор `:`** используется только в словарях (литералы и типы)
- **Операторы `..`, `..<`, `<..`, `<..<`** используются только в диапазонах

## Массивы, Векторы, Множества, Словари

Массивы, векторы, множества, словари и другие коллекции реализуются в библиотеках,
которые можно подключить к проекту.

## Итераторы

Итератор — это объект, который предоставляет последовательный доступ к элементам коллекции.
В `Efen` итераторы используются для обхода коллекций в циклах и функциональных операциях.

### Контракты обхода

`Iterator` описывает уже созданный курсор, а `Iterable` — значение, которое
может создать такой курсор. Оба являются compile-time contract и не служат
типами runtime-значений:

```efen
contract Iterator<Item> {
    fn next -> Item?
}

contract Iterable<Item, Cursor: Iterator<Item>> {
    fn iterator -> Cursor
}
```

`Cursor` обязан быть конкретным типом, соответствующим `Iterator<Item>`.
Аргументы contract можно передавать позиционно и по имени:
`Iterator<String>` и `Iterator<Item: String>` равнозначны.

```efen
class ArrayIterator<T> {
    conforms Iterator<Item: T>

    private let items: [T]
    private var index: Int = 0

    fn next -> T? {
        if index >= items.count() {
            return null
        }

        let value = items[index]
        index += 1
        return value
    }
}

class MyCollection<T> {
    conforms Iterable<Item: T>

    private var items: [T] = []

    fn iterator -> ArrayIterator<T> {
        return ArrayIterator<T>(items)
    }
}
```

`Cursor` в этом соответствии выводится из результата `iterator()` и после
вывода равен `ArrayIterator<T>`. Его можно указать явно по имени, если вывод
неоднозначен.

Тип элемента является полным типовым выражением. Один `Iterator` поэтому может
выдавать значения, читающие ссылки, изменяемые ссылки и другие типы с правами:

```efen
Iterator<Item: T>
Iterator<Item: &read T>
Iterator<Item: &T>
```

`for` выбирает операцию обхода по полному типу и правам исходного выражения.
Тип `Item` задаёт найденная реализация `Iterable`; язык не требует, чтобы любой
итератор возвращал ссылку. `Interval` или генератор может вычислять `T`, а
стандартный изменяемый `Array` предоставляет три режима. Другие коллекции
предоставляют только поддерживаемые ими режимы:

```efen
for item in collection {
    // Для Array<T>: item имеет тип &read T.
}

for item in &collection {
    // Для Array<T>: item имеет тип &T.
}

for item in take collection {
    // Для Array<T>: item имеет тип own T; collection потреблена.
}
```

Все три формы синтаксически допустимы. Компилятор отвергает конкретное
употребление, если тип источника не предоставляет подходящую операцию обхода.
При досрочном выходе потребляющий курсор уничтожает оставшиеся принадлежащие ему
элементы вместе с собой.

### Цикл for-in с итераторами

Цикл `for-in` работает с любым типом, реализующим `Iterable`:

```efen
let numbers = [1, 2, 3, 4, 5]

for number in numbers {
    println(number)
}

// Эквивалентно:
let iter = numbers.iterator()
while let number = iter.next() {
    println(number)
}
```

### Методы итераторов

`Efen` предоставляет богатую библиотеку методов для работы с итераторами:

#### Трансформация

```efen
let numbers = [1, 2, 3, 4, 5]

// map - преобразование каждого элемента
let doubled = numbers.map => item * 2  // [2, 4, 6, 8, 10]

// filter - фильтрация элементов
let evens = numbers.filter => item % 2 == 0  // [2, 4]

// flatMap - преобразование с развёртыванием
let nested = [[1, 2], [3, 4], [5]]
let flattened = nested.flatMap => items  // [1, 2, 3, 4, 5]
```

#### Агрегация

```efen
let numbers = [1, 2, 3, 4, 5]

// reduce - свёртка коллекции
let sum = numbers.reduce(0, (acc, x) => acc + x)  // 15

// fold - алиас для reduce
let product = numbers.fold(1, (acc, x) => acc * x)  // 120

// count - подсчёт элементов
let count = numbers.count()  // 5

// sum - сумма элементов (для числовых типов)
let total = numbers.sum()  // 15
```

#### Поиск и проверка

```efen
let numbers = [1, 2, 3, 4, 5]

// find - поиск первого подходящего элемента
let found = numbers.find => number > 3  // 4

// any - проверка существования элемента
let hasEven = numbers.any => number % 2 == 0  // true

// all - проверка всех элементов
let allPositive = numbers.all => number > 0  // true

// contains - проверка наличия элемента
let hasThree = numbers.contains(3)  // true
```

#### Выбор элементов

```efen
let numbers = [1, 2, 3, 4, 5]

// take - взять первые n элементов
let first3 = numbers.take(3)  // [1, 2, 3]

// skip - пропустить первые n элементов
let last2 = numbers.skip(3)  // [4, 5]

// takeWhile - брать элементы пока условие истинно
let taken = numbers.takeWhile => number < 4  // [1, 2, 3]

// skipWhile - пропускать элементы пока условие истинно
let skipped = numbers.skipWhile => number < 4  // [4, 5]

// first - первый элемент
let first = numbers.first()  // 1

// last - последний элемент
let last = numbers.last()  // 5
```

#### Комбинирование

```efen
let numbers1 = [1, 2, 3]
let numbers2 = [4, 5, 6]

// zip - объединение двух итераторов
let zipped = numbers1.zip(numbers2)  // [(1, 4), (2, 5), (3, 6)]

// chain - последовательное соединение
let chained = numbers1.chain(numbers2)  // [1, 2, 3, 4, 5, 6]

// enumerate - добавление индексов
let indexed = numbers1.enumerate()  // [(0, 1), (1, 2), (2, 3)]
```

### Ленивые вычисления

Большинство операций над итераторами являются **ленивыми** (lazy) — они не выполняются немедленно,
а откладываются до момента, когда результат действительно нужен:

```efen
let numbers = [1, 2, 3, 4, 5]

// Цепочка операций не выполняется сразу
let lazyResult = numbers
    .map => {
        println("Mapping: ${item}")
        item * 2
    }
    .filter => {
        println("Filtering: ${item}")
        item > 5
    }

// Вычисление начнётся только здесь
for value in lazyResult {
    println("Result: ${value}")
}

// Вывод:
// Mapping: 1
// Filtering: 2
// Mapping: 2
// Filtering: 4
// Mapping: 3
// Filtering: 6
// Result: 6
// ...
```

Для немедленного вычисления используйте терминальные операции:

```efen
// collect - собрать результат в коллекцию
let result = numbers.map => { item * 2 }.collect()  // [2, 4, 6, 8, 10]

// toArray - преобразовать в массив
let arr = numbers.filter => { item > 2 }.toArray()  // [3, 4, 5]

// toSet - преобразовать в множество
let set = numbers.toSet()
```

### Создание собственных итераторов

Пример реализации пользовательского итератора:

```efen
class CountingIterator {
    conforms Iterator<Item: Int>

    private let start: Int
    private let end: Int
    private var current: Int

    @constructor
    fn init(start: Int, end: Int) -> Self {

        this.start = start
        this.end = end
        this.current = start
    }

    fn next -> Int? {
        if this.current >= this.end {
            return null
        }

        let value = this.current
        this.current += 1
        return value
    }
}

// Использование
let iter = CountingIterator(1, 5)

while let value = iter.next() {
    println(value)  // 1, 2, 3, 4
}
```

### Реализация Iterable для коллекции

Пример создания пользовательской коллекции с поддержкой итераций:

```efen
class IntList {
    conforms Iterable<Item: Int>

    private var items: [Int] = []

    fn add(item: Int) {

        this.items[] = item
    }

    fn iterator -> IntListIterator {
        return IntListIterator(this.items)
    }
}

class IntListIterator {
    conforms Iterator<Item: Int>

    private let items: [Int]
    private var index: Int = 0

    @constructor
    fn init(items: [Int]) -> Self {

        this.items = items
    }

    fn next -> Int? {
        if this.index >= this.items.count() {
            return null
        }

        let value = this.items[this.index]
        this.index += 1
        return value
    }
}

// Использование
let list = IntList()
list.add(10)
list.add(20)
list.add(30)

for value in list {
    println(value)  // 10, 20, 30
}
```

### Бесконечные итераторы

Итераторы могут быть бесконечными — возвращать значения без конца:

```efen
class InfiniteCounter {
    conforms Iterator<Item: Int>

    private var current: Int = 0

    fn next -> Int? {
        let value = this.current
        this.current += 1
        return value
    }
}

// Использование с ограничением
let counter = InfiniteCounter()
let first10 = counter.take(10).collect()  // [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### Итераторы для словарей

Словари могут итерироваться по ключам, значениям или парам:

```efen
let dict = ["one": 1, "two": 2, "three": 3]

// Итерация по парам ключ-значение
for (key, value) in dict {
    println("${key}: ${value}")
}

// Итерация только по ключам
for key in dict.keys() {
    println(key)
}

// Итерация только по значениям
for value in dict.values() {
    println(value)
}
```

### Производительность итераторов

Итераторы в `Efen` оптимизированы компилятором:

```efen
// Ленивые операции не создают промежуточных коллекций
let result = numbers
    .map => item * 2       // Не создаёт массив
    .filter => item > 5    // Не создаёт массив
    .take(3)             // Не создаёт массив
    .collect()           // Создаёт финальный массив

// Эквивалентно оптимизированному циклу:
let result = []
let taken = 0
for x in numbers {
    if taken >= 3 {
        break
    }
    let mapped = x * 2
    if mapped > 5 {
        result[] = mapped
        taken += 1
    }
}
```

### Лучшие практики

1. **Используйте ленивые вычисления** для больших коллекций:
   ```efen
   // Хорошо: обрабатывает только нужные элементы
   let found = largeList.find => item > 100

   // Плохо: фильтрует всю коллекцию
   let found = largeList.filter => { item > 100 }.first()
   ```

2. **Предпочитайте методы итераторов императивным циклам**:
   ```efen
   // Хорошо
   let sum = numbers.filter => { item > 0 }.sum()

   // Хуже
   let sum = 0
   for x in numbers {
       if x > 0 {
           sum += x
       }
   }
   ```

3. **Комбинируйте операции в цепочки**:
   ```efen
   let result = users
       .filter => user.active
       .map => user.email
       .sorted()
       .collect()
   ```

4. **Используйте бесконечные итераторы с осторожностью**:
   ```efen
   // Всегда ограничивайте бесконечные итераторы
   let infinite = InfiniteCounter()
   let limited = infinite.take(100).collect()
   ```

### Дополнительные методы

```efen
let numbers = [1, 2, 3, 4, 5]

// partition - разделение на две коллекции
let (evens, odds) = numbers.partition => number % 2 == 0
// evens: [2, 4], odds: [1, 3, 5]

// groupBy - группировка по ключу
let items = ["apple", "banana", "apricot", "blueberry"]
let grouped = items.groupBy => item[0]
// { 'a': ["apple", "apricot"], 'b': ["banana", "blueberry"] }

// sorted - сортировка
let sorted = numbers.sorted()  // [1, 2, 3, 4, 5]

// sortedBy - сортировка по ключу
let words = ["zebra", "apple", "banana"]
let sorted = words.sortedBy => word.length()  // ["apple", "zebra", "banana"]

// reversed - переворот
let reversed = numbers.reversed()  // [5, 4, 3, 2, 1]

// distinct - уникальные элементы
let duplicates = [1, 2, 2, 3, 1, 4]
let unique = duplicates.distinct()  // [1, 2, 3, 4]
```
