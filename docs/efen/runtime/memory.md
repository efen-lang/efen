# Менеджер памяти

Контракты, структуры и функции, связанные с управлением памятью в `Efen`
доступны в пакете `memory`.

## Интерфейсы аллокаторов

```efen
interface Allocator {
    fn allocate(size: Size) -> Pointer
    fn reallocate(ptr: Pointer, size: Int) -> Pointer
    fn deallocate(ptr: Pointer)        
}

interface ArenaAllocator : Allocator {
    fn reset
    fn clear
}

interface PoolAllocator : Allocator {
    fn acquire -> Pointer
    fn release(ptr: Pointer)
}
```

## Реализации

### HeapAllocator

Стандартный аллокатор, использующий системную heap память:

```efen
import runtime.memory

class HeapAllocator implements Allocator {
    constructor(size: Size) {
        // Инициализация не требуется для heap
    }

    fn allocate(size: Size) -> Pointer {
        return malloc(size)
    }

    fn reallocate(ptr: Pointer, size: Int) -> Pointer {
        return realloc(ptr, size)
    }

    fn deallocate(ptr: Pointer) {
        free(ptr)
    }
}
```

### Arena Allocator

Arena (также известный как region/bump allocator) — быстрый аллокатор для временных данных.
Выделяет память последовательно из большого буфера, освобождение происходит одной операцией.

**Преимущества:**
- Очень быстрое выделение (просто инкремент указателя)
- Отличная кеш-локальность
- Нет фрагментации
- Идеален для временных данных с одинаковым lifetime

**Недостатки:**
- Невозможно освободить отдельные объекты
- Может тратить память впустую

```efen
import runtime.memory

class Arena implements ArenaAllocator {
    private var buffer: Pointer
    private var offset: Size
    private var capacity: Size

    constructor(size: Size) {
        self.buffer = malloc(size)
        self.offset = 0
        self.capacity = size
    }

    fn allocate(size: Size) -> Pointer {
        if self.offset + size > self.capacity {
            error("Arena out of memory")
        }

        let ptr = self.buffer + self.offset
        self.offset += size
        return ptr
    }

    fn reallocate(ptr: Pointer, size: Int) -> Pointer {
        // Arena не поддерживает realloc эффективно
        let newPtr = allocate(size)
        memcpy(newPtr, ptr, min(size, /* old size */))
        return newPtr
    }

    fn deallocate(ptr: Pointer) {
        // Arena не освобождает отдельные объекты
    }

    fn reset {
        // Сброс арены для повторного использования
        self.offset = 0
    }

    fn clear {
        // Полная очистка
        free(self.buffer)
        self.buffer = null
        self.offset = 0
        self.capacity = 0
    }

    destructor() {
        if self.buffer != null {
            free(self.buffer)
        }
    }
}
```

**Пример использования:**

```efen
fn processRequests(requests: [Request]) {
    // Создаем arena для обработки одного батча запросов
    let arena = Arena(size: 1024 * 1024)  // 1 MB

    for request in requests {
        // Все временные данные выделяются в arena
        let tempData = allocateInArena(arena, size: request.dataSize)
        processRequest(request, tempData)

        // Не нужно освобождать каждый tempData
    }

    // Вся память освобождается одним вызовом
    arena.clear()
}
```

### Pool Allocator

Pool allocator выделяет объекты фиксированного размера из предварительно выделенного пула.

**Преимущества:**
- O(1) выделение и освобождение
- Нет фрагментации
- Отличная кеш-локальность
- Идеален для объектов одного типа

**Недостатки:**
- Только фиксированный размер объектов
- Может тратить память если пул не полностью используется

```efen
import runtime.memory

class Pool implements PoolAllocator {
    private var objectSize: Size
    private var poolSize: Size
    private var buffer: Pointer
    private var freeList: Pointer

    constructor(objectSize: Size, poolSize: Size) {
        self.objectSize = objectSize
        self.poolSize = poolSize

        // Выделяем память для всего пула
        let totalSize = objectSize * poolSize
        self.buffer = malloc(totalSize)

        // Инициализируем free list
        initializeFreeList()
    }

    private fn initializeFreeList {
        self.freeList = self.buffer

        // Связываем все блоки в список
        var current = self.buffer
        for i in 0..<poolSize - 1 {
            let next = current + objectSize
            *(current as *Pointer) = next
            current = next
        }

        // Последний блок указывает на null
        *(current as *Pointer) = null
    }

    fn acquire -> Pointer {
        if self.freeList == null {
            error("Pool exhausted")
        }

        let ptr = self.freeList
        self.freeList = *(ptr as *Pointer)
        return ptr
    }

    fn release(ptr: Pointer) {
        // Возвращаем блок в начало free list
        *(ptr as *Pointer) = self.freeList
        self.freeList = ptr
    }

    fn allocate(size: Size) -> Pointer {
        if size != self.objectSize {
            error("Pool can only allocate objects of size ${objectSize}")
        }
        return acquire()
    }

    fn reallocate(ptr: Pointer, size: Int) -> Pointer {
        error("Pool does not support realloc")
    }

    fn deallocate(ptr: Pointer) {
        release(ptr)
    }

    destructor() {
        free(self.buffer)
    }
}
```

**Пример использования:**

```efen
// Пул для Node объектов в linked list
struct Node {
    value: Int
    next: Node?
}

let nodePool = Pool(
    objectSize: sizeOf(Node.self),
    poolSize: 1000
)

fn createLinkedList(values: [Int]) -> Node? {
    var head: Node? = null
    var tail: Node? = null

    for value in values {
        // Быстрое выделение из пула
        let nodePtr = nodePool.acquire()
        let node = Node(value: value, next: null)
        memcpy(nodePtr, &node, sizeOf(Node.self))

        if head == null {
            head = nodePtr as *Node
            tail = head
        } else {
            tail!.next = nodePtr as *Node
            tail = tail!.next
        }
    }

    return head
}

fn destroyLinkedList(head: Node?) {
    var current = head
    while current != null {
        let next = current!.next
        nodePool.release(current as Pointer)
        current = next
    }
}
```

### Stack Allocator

Аллокатор на стеке — для очень короткоживущих данных:

```efen
import runtime.memory

// Аллокатор использует alloca (выделение на стеке)
fn stackAllocate<T>(count: Int = 1) -> UnsafeMutablePointer<T> {
    let size = sizeOf(T.self) * count
    return alloca(size) as UnsafeMutablePointer<T>
}

fn processData(size: Int) {
    // Выделение на стеке, автоматически освобождается при выходе из функции
    let buffer = stackAllocate<UInt8>(count: size)

    // Использование buffer
    for i in 0..<size {
        buffer[i] = UInt8(i)
    }

    // Не нужно освобождать — стек автоматически очистится
}
```

## Использование с классами

Классы могут указывать собственные аллокаторы:

```efen
import runtime.memory

@allocator(Arena)
class TemporaryData {
    var value: Int

    constructor(value: Int) {
        self.value = value
    }
}

// Объекты TemporaryData будут выделяться через Arena
let data = TemporaryData(value: 42)
```

Кастомная стратегия памяти:

```efen
class MyClass {
    // Указываем аллокатор для этого класса
    static let allocator = Pool(
        objectSize: sizeOf(MyClass.self),
        poolSize: 100
    )

    var value: Int

    constructor(value: Int) {
        self.value = value
    }
}
```

## Composable Allocators

Аллокаторы можно комбинировать:

```efen
// Fallback allocator: сначала пробует pool, потом heap
class FallbackAllocator implements Allocator {
    private var primary: Allocator
    private var fallback: Allocator

    constructor(primary: Allocator, fallback: Allocator) {
        self.primary = primary
        self.fallback = fallback
    }

    fn allocate(size: Size) -> Pointer {
        let ptr = primary.allocate(size)
        if ptr == null {
            return fallback.allocate(size)
        }
        return ptr
    }

    // ... остальные методы
}

let allocator = FallbackAllocator(
    primary: nodePool,
    fallback: HeapAllocator(size: 0)
)
```

## Tracking Allocator

Для отладки утечек памяти:

```efen
class TrackingAllocator implements Allocator {
    private var inner: Allocator
    private var allocations: [Pointer: Size] = [:]

    fn allocate(size: Size) -> Pointer {
        let ptr = inner.allocate(size)
        allocations[ptr] = size
        print("Allocated ${size} bytes at ${ptr}")
        return ptr
    }

    fn deallocate(ptr: Pointer) {
        if let size = allocations[ptr] {
            print("Deallocated ${size} bytes at ${ptr}")
            allocations.removeValue(forKey: ptr)
        } else {
            error("Double free or invalid pointer: ${ptr}")
        }
        inner.deallocate(ptr)
    }

    fn reportLeaks {
        if allocations.isEmpty {
            print("No memory leaks detected")
        } else {
            print("Memory leaks detected:")
            for (ptr, size) in allocations {
                print("  ${size} bytes at ${ptr}")
            }
        }
    }
}
```

## Лучшие практики

### 1. Используйте Arena для временных данных

```efen
fn parseJSON(json: String) -> JSONValue {
    let arena = Arena(size: json.length * 2)

    // Парсинг создает много временных строк и объектов
    let tokens = tokenize(json, allocator: arena)
    let ast = buildAST(tokens, allocator: arena)

    // Финальный результат копируется в heap
    let result = ast.toValue()

    // Вся временная память освобождается
    arena.clear()

    return result
}
```

### 2. Используйте Pool для объектов одного типа

```efen
// Игровой движок: пул для entity объектов
class GameWorld {
    private let entityPool = Pool(
        objectSize: sizeOf(Entity.self),
        poolSize: 10000
    )

    fn spawnEntity -> Entity {
        let ptr = entityPool.acquire()
        return ptr as *Entity
    }

    fn despawnEntity(entity: Entity) {
        entityPool.release(entity as Pointer)
    }
}
```

### 3. Используйте Stack для микрооптимизаций

```efen
fn quickSort(array: [Int]) {
    // Малый временный буфер на стеке
    if array.count < 100 {
        let temp = stackAllocate<Int>(count: array.count)
        // ... sort logic
        // Автоматически освобождается
    } else {
        // Большой массив — используем heap
        let temp = HeapAllocator().allocate(array.count * sizeOf(Int.self))
        defer { deallocate(temp) }
        // ... sort logic
    }
}
```

## См. также

- [index.md](index.md) — Runtime API overview
- [../memory.md](../memory.md) — Концепция управления памятью в Efen
- [../types/ownership.md](../types/ownership.md) — Система владения
