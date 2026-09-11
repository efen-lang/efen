# Контракт аллокатора памяти

Аллокатор памяти в Efen определяет интерфейс для управления динамическим выделением и освобождением памяти. 
Контракт аллокатора включает следующие основные методы:

```efen 
contract Allocator<Type>
{
    for Type

    // Выделяет блок памяти заданного размера и возвращает указатель на него.
    fn allocate(size: Size<Type>) -> Pointer<Type>

    // Освобождает ранее выделенный блок памяти по указанному указателю.
    fn deallocate(pointer: Pointer<Type>)    
}
```

```efen
strategy MyAllocator<Type> conforms Allocator<Type> 
{
    fn allocate(size: Size<Type>) -> Pointer<Type> {
        return memory::Manager::allocate(size);
    }

    fn deallocate(pointer: Pointer<Type>) {
        memory::Manager::deallocate(pointer);
    }    
}

class MyObject 
{
    var data: Int;

    fn init() {
        self.data = data;
    }
}

provide MyAllocator for MyObject
```
