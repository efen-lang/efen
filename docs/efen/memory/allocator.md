# Контракт аллокатора памяти

Аллокатор памяти в Efen определяет интерфейс для управления динамическим выделением и освобождением памяти. 
Контракт аллокатора включает следующие основные методы:

```efen 
contract Allocator<Type>
{
    for Type

    // Выделяет блок памяти заданного размера; без памяти бросает AllocationError.
    fn allocate(bytes: Int) -> own Pointer throws AllocationError

    // То же, но без памяти возвращает null.
    fn tryAllocate(bytes: Int) -> own Pointer?

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
Поэтому коллекция, которая растёт только через `extend`, не перемещает свои элементы, и указатели на них остаются верными, а
`reallocate` в её коде делает сводку «может переместить». На Linux с overcommit нехватку физической
памяти после успешного выделения видит ОС, а не программа.

Контракт один, реализации на платформах разные, и различаются они только тем, когда операция отказывает:

- Linux с overcommit: выделение почти всегда успешно, нехватку физической памяти видит ОС при первой
  записи и завершает процесс; программа об этом не узнаёт.
- Windows: выделение и `extend` внутри резерва (`MEM_COMMIT`) честно отказывают при нехватке памяти.
- wasm32 и платформы без MMU: независимого резерва адресов нет, `extend` удаётся только у последнего
  блока линейной памяти, поэтому `tryExtend` чаще возвращает `false`, а коллекции с резервом
  выделяют всю ёмкость сразу или объявляют предел.

```efen
strategy MyAllocator<Type> {
    conforms Allocator<Type>

    fn allocate(bytes: Int) -> own Pointer {
        return memory::Manager.allocate(bytes)
    }

    fn deallocate(pointer: own Pointer) {
        memory::Manager.deallocate(take pointer)
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
