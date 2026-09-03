# Коллекции

Коллекцией называется любая перечисляемая структура данных, которая может содержать ноль или более элементов. 
В `Efen` есть несколько встроенных типов коллекций, каждый из которых имеет свои особенности и применения.

## Enum-массивы

Enum-массив — массив фиксированного размера, индексируемый вариантами enum.
Он содержит ровно одно значение одного типа для каждого варианта enum.

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

Операторы диапазона используются для создания диапазонов значений.
Они могут применяться к числовым типам и другим типам, которые поддерживают сравнение.

### Закрытые диапазоны (обе границы указаны)

- **`a..b`** — включает `a` и `b` (closed range)
- **`a..<b`** — включает `a`, исключает `b` (half-open range, right-exclusive)
- **`a<..b`** — исключает `a`, включает `b` (half-open range, left-exclusive)
- **`a<..<b`** — исключает `a` и `b` (open range, both exclusive)

### Открытые диапазоны (одна граница)

- **`a..`** — от `a` (включая) до конца
- **`a<..`** — от `a` (исключая) до конца
- **`..b`** — от начала до `b` (включая)
- **`..<b`** — от начала до `b` (исключая)

### Примеры использования

```efen
// Закрытые диапазоны
let r1 = 1..5      // [1, 2, 3, 4, 5]
let r2 = 1..<5     // [1, 2, 3, 4]
let r3 = 1<..5     // [2, 3, 4, 5]
let r4 = 1<..<5    // [2, 3, 4]

// Открытые диапазоны
let r5 = 5..       // [5, 6, 7, ...]
let r6 = 5<..      // [6, 7, 8, ...]
let r7 = ..5       // [..., 3, 4, 5]
let r8 = ..<5      // [..., 3, 4]
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
| `a..b`                    | Закрытый диапазон             | `1..5`                          | `[1, 2, 3, 4, 5]`    |
| `a..<b`                   | Полуоткрытый справа           | `1..<5`                         | `[1, 2, 3, 4]`       |
| `a<..b`                   | Полуоткрытый слева            | `1<..5`                         | `[2, 3, 4, 5]`       |
| `a<..<b`                  | Открытый с обоих концов       | `1<..<5`                        | `[2, 3, 4]`          |
| `a..`                     | От `a` до бесконечности       | `5..`                           | `[5, 6, 7, ...]`     |
| `a<..`                    | От `a+1` до бесконечности     | `5<..`                          | `[6, 7, 8, ...]`     |
| `..b`                     | От начала до `b` включительно | `..5`                           | `[..., 3, 4, 5]`     |
| `..<b`                    | От начала до `b` исключая     | `..<5`                          | `[..., 3, 4]`        |
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

- **Диапазоны** — самостоятельные выражения, создающие объект Range
- **Срезы** — результат применения диапазона к массиву через индексирование `[]`
- **Оператор `:`** используется только в словарях (литералы и типы)
- **Операторы `..`, `..<`, `<..`, `<..<`** используются только в диапазонах

## Массивы, Векторы, Множества, Словари

Массивы, векторы, множества, словари и другие коллекции реализуются в библиотеках,
которые можно подключить к проекту.

## Итераторы

Итератор — это объект, который предоставляет последовательный доступ к элементам коллекции.
В `Efen` итераторы используются для обхода коллекций в циклах и функциональных операциях.

### Два способа реализации итераторов

В `Efen` итераторы могут быть реализованы двумя способами:

1. **Через контракт (contract)** — compile-time, нулевой overhead, static dispatch
2. **Через интерфейс (interface)** — runtime VTBL, dynamic dispatch, полиморфизм

Выбор зависит от требований к производительности и необходимости runtime полиморфизма.

### Способ 1: Contract Iterator (compile-time)

Контракт определяет требования времени компиляции. После компиляции контракт полностью исчезает из бинарника.

```efen
// Контракт для итератора
contract Iterator<T> {
    fn next() -> Option<T>
}

// Контракт для итерируемых типов
contract Iterable<T> {
    fn iterator() -> Iterator<T>
}
```

**Преимущества contract:**
- ✅ Нулевой runtime overhead
- ✅ Static dispatch (прямой вызов методов)
- ✅ Максимальная оптимизация компилятором
- ✅ Используется в generic-функциях

**Пример использования:**

```efen
// Generic-функция с контрактом
fn sum<T, I>(iterable: I) -> Int
    where I: Iterable<Int> {

    var total = 0
    let iter = iterable.iterator()

    while let Some(value) = iter.next() {
        total += value
    }

    return total  // STATIC DISPATCH - оптимально
}

// Компилятор генерирует специализированный код для каждого типа
let arr = [1, 2, 3, 4, 5]
let result = sum(arr)  // Прямые вызовы без VTBL
```

### Способ 2: Interface Iterator (runtime)

Интерфейс существует в runtime как виртуальная таблица (VTBL) и обеспечивает полиморфизм.

```efen
// Интерфейс для итератора
interface Iterator<T> {
    fn next() -> Option<T>
}

// Интерфейс для итерируемых типов
interface Iterable<T> {
    fn iterator() -> Iterator<T>
}
```

**Преимущества interface:**
- ✅ Runtime полиморфизм
- ✅ Тип может быть неизвестен во время компиляции
- ✅ Binary compatibility
- ✅ Plugin systems

**Пример использования:**

```efen
// Функция принимает любой Iterable через VTBL
fn printAll(iterable: Iterable<String>) {
    let iter = iterable.iterator()

    while let Some(value) = iter.next() {
        println(value)  // DYNAMIC DISPATCH через VTBL
    }
}

// Можно передать любую реализацию
let list = StringList::new()
let array = ["a", "b", "c"]

printAll(list)   // Runtime dispatch
printAll(array)  // Runtime dispatch
```

### Комбинированный подход

Класс может одновременно соответствовать контракту (`conforms`) и реализовывать интерфейс (`implements`):

```efen
class MyCollection<T> {
    conforms Iterable<T>    // Compile-time проверка
    implements Iterable<T>  // Runtime VTBL

    private var items: [T] = []

    fn iterator() -> MyIterator<T> {
        return MyIterator::new(this.items)
    }
}

class MyIterator<T> {
    conforms Iterator<T>
    implements Iterator<T>

    private var items: [T]
    private var index: Int = 0

    fn next() -> Option<T> {
        if this.index >= this.items.count() {
            return None
        }
        let value = this.items[this.index]
        this.index += 1
        return Some(value)
    }
}

// Compile-time использование (оптимально)
fn processStatic<C: Iterable<Int>>(collection: C) {
    let iter = collection.iterator()
    // Static dispatch - прямые вызовы
}

// Runtime использование (гибко)
fn processDynamic(collection: Iterable<Int>) {
    let iter = collection.iterator()
    // Dynamic dispatch через VTBL
}
```

### Когда использовать какой подход?

**Используйте Contract когда:**
- Критична производительность
- Тип известен во время компиляции
- Используете generics
- Не нужен runtime полиморфизм

**Используйте Interface когда:**
- Нужен runtime полиморфизм
- Тип определяется во время выполнения
- Реализуете plugin system
- Нужна binary compatibility

### Цикл for-in с итераторами

Цикл `for-in` работает с любым типом, реализующим `Iterable`:

```efen
let numbers = [1, 2, 3, 4, 5]

for number in numbers {
    println(number)
}

// Эквивалентно:
let iter = numbers.iterator()
while let Some(number) = iter.next() {
    println(number)
}
```

### Методы итераторов

`Efen` предоставляет богатую библиотеку методов для работы с итераторами:

#### Трансформация

```efen
let numbers = [1, 2, 3, 4, 5]

// map - преобразование каждого элемента
let doubled = numbers.map(|x| x * 2)  // [2, 4, 6, 8, 10]

// filter - фильтрация элементов
let evens = numbers.filter(|x| x % 2 == 0)  // [2, 4]

// flatMap - преобразование с развёртыванием
let nested = [[1, 2], [3, 4], [5]]
let flattened = nested.flatMap(|x| x)  // [1, 2, 3, 4, 5]
```

#### Агрегация

```efen
let numbers = [1, 2, 3, 4, 5]

// reduce - свёртка коллекции
let sum = numbers.reduce(0, |acc, x| acc + x)  // 15

// fold - алиас для reduce
let product = numbers.fold(1, |acc, x| acc * x)  // 120

// count - подсчёт элементов
let count = numbers.count()  // 5

// sum - сумма элементов (для числовых типов)
let total = numbers.sum()  // 15
```

#### Поиск и проверка

```efen
let numbers = [1, 2, 3, 4, 5]

// find - поиск первого подходящего элемента
let found = numbers.find(|x| x > 3)  // Some(4)

// any - проверка существования элемента
let hasEven = numbers.any(|x| x % 2 == 0)  // true

// all - проверка всех элементов
let allPositive = numbers.all(|x| x > 0)  // true

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
let taken = numbers.takeWhile(|x| x < 4)  // [1, 2, 3]

// skipWhile - пропускать элементы пока условие истинно
let skipped = numbers.skipWhile(|x| x < 4)  // [4, 5]

// first - первый элемент
let first = numbers.first()  // Some(1)

// last - последний элемент
let last = numbers.last()  // Some(5)
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
    .map(|x| {
        println("Mapping: {x}")
        x * 2
    })
    .filter(|x| {
        println("Filtering: {x}")
        x > 5
    })

// Вычисление начнётся только здесь
for value in lazyResult {
    println("Result: {value}")
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
let result = numbers.map(|x| x * 2).collect()  // [2, 4, 6, 8, 10]

// toArray - преобразовать в массив
let arr = numbers.filter(|x| x > 2).toArray()  // [3, 4, 5]

// toSet - преобразовать в множество
let set = numbers.toSet()
```

### Создание собственных итераторов

Пример реализации пользовательского итератора:

```efen
class RangeIterator implements Iterator<Int> {
    private let start: Int
    private let end: Int
    private var current: Int

    fn new(start: Int, end: Int) {
        this.start = start
        this.end = end
        this.current = start
    }

    fn next() -> Option<Int> {
        if this.current >= this.end {
            return None
        }

        let value = this.current
        this.current += 1
        return Some(value)
    }
}

// Использование
let iter = RangeIterator::new(1, 5)

while let Some(value) = iter.next() {
    println(value)  // 1, 2, 3, 4
}
```

### Реализация Iterable для коллекции

Пример создания пользовательской коллекции с поддержкой итераций:

```efen
class IntList implements Iterable<Int> {
    private var items: [Int] = []

    fn add(item: Int) {
        this.items[] = item
    }

    fn iterator() -> Iterator<Int> {
        return IntListIterator::new(this.items)
    }
}

class IntListIterator implements Iterator<Int> {
    private let items: [Int]
    private var index: Int = 0

    fn new(items: [Int]) {
        this.items = items
    }

    fn next() -> Option<Int> {
        if this.index >= this.items.count() {
            return None
        }

        let value = this.items[this.index]
        this.index += 1
        return Some(value)
    }
}

// Использование
let list = IntList::new()
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
class InfiniteCounter implements Iterator<Int> {
    private var current: Int = 0

    fn next() -> Option<Int> {
        let value = this.current
        this.current += 1
        return Some(value)
    }
}

// Использование с ограничением
let counter = InfiniteCounter::new()
let first10 = counter.take(10).collect()  // [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### Итераторы для словарей

Словари могут итерироваться по ключам, значениям или парам:

```efen
let dict = ["one": 1, "two": 2, "three": 3]

// Итерация по парам ключ-значение
for (key, value) in dict {
    println("{key}: {value}")
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
    .map(|x| x * 2)      // Не создаёт массив
    .filter(|x| x > 5)   // Не создаёт массив
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
   let found = largeList.find(|x| x > 100)

   // Плохо: фильтрует всю коллекцию
   let found = largeList.filter(|x| x > 100).first()
   ```

2. **Предпочитайте методы итераторов императивным циклам**:
   ```efen
   // Хорошо
   let sum = numbers.filter(|x| x > 0).sum()

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
       .filter(|u| u.active)
       .map(|u| u.email)
       .sorted()
       .collect()
   ```

4. **Используйте бесконечные итераторы с осторожностью**:
   ```efen
   // Всегда ограничивайте бесконечные итераторы
   let infinite = InfiniteCounter::new()
   let limited = infinite.take(100).collect()
   ```

### Дополнительные методы

```efen
let numbers = [1, 2, 3, 4, 5]

// partition - разделение на две коллекции
let (evens, odds) = numbers.partition(|x| x % 2 == 0)
// evens: [2, 4], odds: [1, 3, 5]

// groupBy - группировка по ключу
let items = ["apple", "banana", "apricot", "blueberry"]
let grouped = items.groupBy(|s| s[0])
// { 'a': ["apple", "apricot"], 'b': ["banana", "blueberry"] }

// sorted - сортировка
let sorted = numbers.sorted()  // [1, 2, 3, 4, 5]

// sortedBy - сортировка по ключу
let words = ["zebra", "apple", "banana"]
let sorted = words.sortedBy(|s| s.length())  // ["apple", "zebra", "banana"]

// reversed - переворот
let reversed = numbers.reversed()  // [5, 4, 3, 2, 1]

// distinct - уникальные элементы
let duplicates = [1, 2, 2, 3, 1, 4]
let unique = duplicates.distinct()  // [1, 2, 3, 4]
```
