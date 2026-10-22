# Контракт аллокатора памяти

Аллокатор памяти в Efen определяет интерфейс для управления динамическим выделением и освобождением памяти. 
Контракт аллокатора включает следующие основные методы:

```efen 
contract Allocator<Type>
{
    for Type

    // Выделяет блок памяти заданного размера; без памяти бросает AllocationError.
    fn allocate(size: Size<Type>) -> Pointer<Type> throws AllocationError

    // То же, но без памяти возвращает null.
    fn tryAllocate(size: Size<Type>) -> Pointer<Type>?

    // Расширяет блок на месте; никогда не перемещает; если на месте нельзя, бросает AllocationError.
    fn extend(pointer: Pointer<Type>, size: Size<Type>) throws AllocationError

    // То же, но если на месте нельзя, возвращает false.
    fn tryExtend(pointer: Pointer<Type>, size: Size<Type>) -> Bool

    // Расширяет блок на месте или переносит в новый; без памяти бросает AllocationError, старый блок цел.
    fn reallocate(pointer: Pointer<Type>, size: Size<Type>) -> Pointer<Type> throws AllocationError

    // То же, но без памяти возвращает null, старый блок цел.
    fn tryReallocate(pointer: Pointer<Type>, size: Size<Type>) -> Pointer<Type>?

    // Освобождает ранее выделенный блок памяти по указанному указателю.
    fn deallocate(pointer: Pointer<Type>)    
}
```

Каждая операция есть в двух видах (Edmond, 2026-10-22): с исключением и с `null` или `false`. При
неудаче ничего не меняется. Для правил ссылок (`../types/access-regions.md`, «Рост без перемещения»)
у операций одно действие на все реализации: `allocate` и `extend` — `allocate` (новые места, старые
не двигаются), `reallocate` — `allocate`, `move` и `free` (может переместить), `deallocate` — `free`.
Поэтому коллекция, которая растёт только через `extend`, сохраняет ссылки на свои элементы, а
`reallocate` в её коде делает сводку «может переместить». На Linux с overcommit нехватку физической
памяти после успешного выделения видит ОС, а не программа.

```efen
strategy MyAllocator<Type> {
    conforms Allocator<Type>

    fn allocate(size: Size<Type>) -> Pointer<Type> {
        return memory::Manager.allocate(size);
    }

    fn deallocate(pointer: Pointer<Type>) {
        memory::Manager.deallocate(pointer);
    }    
}

class MyObject 
{
    var data: Int;

    fn init {
        self.data = data;
    }
}

provide MyAllocator for MyObject
```
