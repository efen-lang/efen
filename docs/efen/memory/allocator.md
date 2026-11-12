# Контракт аллокатора памяти

Аллокатор памяти в Efen определяет интерфейс для управления динамическим выделением и освобождением памяти. 
Контракт аллокатора включает следующие основные методы:

```efen 
contract Allocator<Type>
{
    for Type

    // Выделяет блок памяти заданного размера; без памяти бросает AllocationError.
    fn allocate(bytes: Int) -> own Pointer throws AllocationError
        ensures result.size == bytes

    // То же, но без памяти возвращает null.
    fn tryAllocate(bytes: Int) -> own Pointer?
        ensures result == null || result.size == bytes

    // Расширяет блок на месте; никогда не перемещает; если на месте нельзя, бросает AllocationError.
    fn extend(pointer: mut Pointer, bytes: Int) throws AllocationError

    // То же, но если на месте нельзя, возвращает false.
    fn tryExtend(pointer: mut Pointer, bytes: Int) -> Bool

    // Расширяет блок на месте или переносит в новый; без памяти бросает AllocationError, старый блок цел.
    fn reallocate(pointer: mut Pointer, bytes: Int) throws AllocationError

    // То же, но без памяти возвращает false, старый блок цел.
    fn tryReallocate(pointer: mut Pointer, bytes: Int) -> Bool

    // Освобождает ранее выделенный блок памяти по указанному указателю.
    fn deallocate(pointer: own Pointer)    
}
```

Каждая операция есть в двух видах: с исключением и с `null` или `false`. При
неудаче ничего не меняется. Для правил областей доступа (`../types/access-regions.md`, «Рост без перемещения»)
у операций одно событие на все реализации: `allocate` и `extend` — создание (новая память, старая не двигается),
`reallocate` — создание, перенос и уничтожение (может переместить), `deallocate` — уничтожение. `Pointer` не
обобщённый ([сырая память](pointer.md)): аллокатор выдаёт байты, вид им даёт приведение `as`.
Условие `ensures result.size == bytes` у `allocate` и `tryAllocate` сообщает вызывающему размер выданной памяти: по
нему компилятор доказывает, что память вмещает вид в приведении
`mm.allocate(bytes: sizeOf(Node<T>)) as Node<T>(value: take value)`.
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

Пример реализует все семь методов контракта: каждый передаёт операцию менеджеру памяти `memory::Manager`, у функций
которого те же сигнатуры и условия.

```efen
strategy MyAllocator<Type> {
    conforms Allocator<Type>

    fn allocate(bytes: Int) -> own Pointer throws AllocationError {
        return memory::Manager.allocate(bytes: bytes)
    }

    fn tryAllocate(bytes: Int) -> own Pointer? {
        return memory::Manager.tryAllocate(bytes: bytes)
    }

    fn extend(pointer: mut Pointer, bytes: Int) throws AllocationError {
        memory::Manager.extend(pointer: pointer, bytes: bytes)
    }

    fn tryExtend(pointer: mut Pointer, bytes: Int) -> Bool {
        return memory::Manager.tryExtend(pointer: pointer, bytes: bytes)
    }

    fn reallocate(pointer: mut Pointer, bytes: Int) throws AllocationError {
        memory::Manager.reallocate(pointer: pointer, bytes: bytes)
    }

    fn tryReallocate(pointer: mut Pointer, bytes: Int) -> Bool {
        return memory::Manager.tryReallocate(pointer: pointer, bytes: bytes)
    }

    fn deallocate(pointer: own Pointer) {
        memory::Manager.deallocate(pointer: take pointer)
    }
}

class MyObject {
    conforms Constructible
    var data: Int

    @constructor fn init(data: Int) -> Self {
        self.data = data
    }
}

provide MyAllocator for MyObject
```
