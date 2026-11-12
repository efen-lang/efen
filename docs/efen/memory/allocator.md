# Контракт аллокатора памяти

`Allocator<Type>` — стратегия, которая даёт память значениям одного типа: объекту класса, элементу множества
`layout`, области. Компилятор вызывает её сам, когда создаёт значение формой с полями (`Box(value: 10)`,
`Node<T>(value: take value)`), и когда значение кончается. Программа выделение и освобождение не пишет.

```efen 
contract Allocator<Type>
{
    for Type

    // Выделяет блок памяти заданного размера и выравнивания; без памяти бросает AllocationError.
    static fn allocate(bytes: Int, aligned: Int) -> own Pointer throws AllocationError
        ensures result.size == bytes && result.alignment == aligned

    // То же, но без памяти возвращает null.
    static fn tryAllocate(bytes: Int, aligned: Int) -> own Pointer?
        ensures result == null || (result.size == bytes && result.alignment == aligned)

    // Расширяет блок на месте; никогда не перемещает; если на месте нельзя, бросает AllocationError.
    static fn extend(pointer: mut Pointer, bytes: Int) throws AllocationError

    // То же, но если на месте нельзя, возвращает false.
    static fn tryExtend(pointer: mut Pointer, bytes: Int) -> Bool

    // Расширяет блок на месте или переносит в новый; без памяти бросает AllocationError, старый блок цел.
    static fn reallocate(pointer: mut Pointer, bytes: Int) throws AllocationError

    // То же, но без памяти возвращает false, старый блок цел.
    static fn tryReallocate(pointer: mut Pointer, bytes: Int) -> Bool

    // Освобождает ранее выделенный блок памяти по указанному указателю.
    static fn deallocate(pointer: own Pointer)
}
```

Функции статические: значения типа до вызова ещё нет. `Type` — любой тип. Для множества `layout` компилятор
спрашивает стратегию `Allocator<X.Item>`, для области верхнего уровня `Allocator<X.Area>`, для класса
`Allocator<Класс>`. У множества ключом служит `X.Item`, а не структура: несколько видов описывают одни байты в
разное время ([смена вида](layout/operations.md#67-смена-вида-и-замена-области)), и память, взятая под одним видом,
возвращается под любым другим.

Для элемента компилятор вызывает `allocate(bytes: sizeOf(V(поля)), aligned: alignOf(V))` до вычисления
аргументов формы и приводит память к виду `V`; условие `ensures` доказывает, что память вмещает вид. Когда значение
`own` кончается, он вызывает `deallocate` той же стратегии
([создание элемента](layout/operations.md#62-создание-элемента)). `tryAllocate` и функции роста служат коду, который
работает с сырой памятью сам: менеджерам памяти и коллекциям. Формы создания, которая вместо исключения даёт
`null`, нет: такой код вызывает `tryAllocate` и приводит память сам.

Каждая операция есть в двух видах: с исключением и с `null` или `false`. При
неудаче ничего не меняется. Для правил областей доступа (`../types/access-regions.md`, «Рост без перемещения»)
у операций одно событие на все реализации: `allocate` и `extend` — создание (новая память, старая не двигается),
`reallocate` — создание, перенос и уничтожение (может переместить), `deallocate` — уничтожение. `Pointer` не
обобщённый ([сырая память](pointer.md)): аллокатор выдаёт байты, вид им даёт приведение `as`.
`extend` расширяет блок сырой памяти на месте. Области `layout` это не касается: формы роста области на месте нет.
Коллекция растёт заменой области, и после роста ссылки и указатели внутрь прежней области недействительны, каким бы
методом аллокатора рост ни был выполнен
([смена вида и замена области](layout/operations.md#67-смена-вида-и-замена-области)). На Linux с overcommit нехватку
физической памяти после успешного выделения видит ОС, а не программа.

Контракт один, реализации на платформах разные, и различаются они только тем, когда операция отказывает:

- Linux с overcommit: выделение почти всегда успешно, нехватку физической памяти видит ОС при первой
  записи и завершает процесс; программа об этом не узнаёт.
- Windows: выделение и `extend` внутри резерва (`MEM_COMMIT`) честно отказывают при нехватке памяти.
- wasm32 и платформы без MMU: независимого резерва адресов нет, `extend` удаётся только у последнего
  блока линейной памяти, поэтому `tryExtend` чаще возвращает `false`, а коллекции с резервом
  выделяют всю ёмкость сразу или объявляют предел.

## Менеджер памяти `mm`

`mm` — пакет, который управляет памятью программы: тот, который называет поле `allocator:` её конфигурации
([конфигурация сборки](../build-config.md)). Куча одна на исполняемый файл, и выбирает её программа, а не
библиотека. У функций `mm` те же сигнатуры и условия, что у функций контракта. Код пишет `mm.` только для сырой
памяти `own Pointer`; значения типов получают память через `Allocator<Type>`.

Стратегия по умолчанию передаёт каждую операцию в `mm`. Её даёт пакет `allocator:`; она действует для типа, для
которого не выбрана другая стратегия. При `allocator: none` форма, которой нужна память, вызывает ошибку сборки.

```efen
public strategy Heap<Type> {
    conforms Allocator<Type>

    static fn allocate(bytes: Int, aligned: Int) -> own Pointer throws AllocationError {
        return mm.allocate(bytes: bytes, aligned: aligned)
    }

    static fn tryAllocate(bytes: Int, aligned: Int) -> own Pointer? {
        return mm.tryAllocate(bytes: bytes, aligned: aligned)
    }

    static fn extend(pointer: mut Pointer, bytes: Int) throws AllocationError {
        mm.extend(pointer: pointer, bytes: bytes)
    }

    static fn tryExtend(pointer: mut Pointer, bytes: Int) -> Bool {
        return mm.tryExtend(pointer: pointer, bytes: bytes)
    }

    static fn reallocate(pointer: mut Pointer, bytes: Int) throws AllocationError {
        mm.reallocate(pointer: pointer, bytes: bytes)
    }

    static fn tryReallocate(pointer: mut Pointer, bytes: Int) -> Bool {
        return mm.tryReallocate(pointer: pointer, bytes: bytes)
    }

    static fn deallocate(pointer: own Pointer) {
        mm.deallocate(pointer: take pointer)
    }
}
```

## К каким типам прилипает стратегия

Ограничение параметра стратегии задаёт, к каким типам она применима. `ThreadHeap` ниже служит только типам,
привязанным к одному потоку, и берёт память из кучи потока без блокировки:

```efen
public strategy ThreadHeap<Type: ThreadBound> {
    conforms Allocator<Type>

    static fn allocate(bytes: Int, aligned: Int) -> own Pointer throws AllocationError {
        return threadheap::take(bytes: bytes, aligned: aligned)
    }

    static fn deallocate(pointer: own Pointer) {
        threadheap::give(pointer: take pointer)
    }

    // tryAllocate и четыре функции роста написаны так же
}
```

Стратегию для типа выбирают обычные правила ([выбор стратегии](../strategies.md#правила-выбора-стратегии)):
`provide` в пакете типа, запись программы, правило `Resolve<Allocator<let T>>`; стратегия по умолчанию — последний
шаг, а не кандидат наравне с другими. Внешний пакет и программа меняют аллокатор типа только там, где тип пишет
`allow strategies` ([право применить стратегию](../strategies.md#право-применить-стратегию)).

<a id="один-аллокатор-на-множество"></a>

## Один аллокатор на множество

Компилятор выбирает стратегию `Allocator<X.Item>` один раз на множество, а не на вызов: каждое создание и каждое
освобождение элемента `X` идёт через неё. Каждая строка `set`, `set area` и области верхнего уровня считается
ограничением своего `layout`, поэтому выбранная стратегия входит в тождество его типов
([идентичность](../strategies.md#тело-обобщённого-объявления)). Два пакета с разным выбором получают разные типы, и
передать значение из одного в другой — ошибка компиляции:

```text
error: expected List<Int> [Allocator = mm::Heap], found List<Int> [Allocator = pools::NodePool]
```

Так аллокатор подменяется в разных контекстах: по типу и при компиляции. Память элемента, которую выдала стратегия,
возвращается ей же: другой стратегии у множества нет. Память, которую множество получило извне, возвращает явный
код ([создание элемента](layout/operations.md#62-создание-элемента)).

Класс получает память так же: `MyObject(data: 1)` вызывает `allocate` стратегии, выбранной для `MyObject`.

```efen
class MyObject {
    conforms Constructible, ThreadBound
    var data: Int

    @constructor fn init(data: Int) -> Self {
        self.data = data
    }
}

provide ThreadHeap for MyObject                 // MyObject привязан к потоку: ThreadHeap к нему применим
```
