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

interface ArenaAllocator {
    mut fn allocate(size: Size) -> Pointer
    mut fn reallocate(ptr: Pointer, size: Int) -> Pointer
    mut fn deallocate(ptr: Pointer)
    mut fn reset
    mut fn clear
}

interface PoolAllocator {
    mut fn allocate(size: Size) -> Pointer
    mut fn reallocate(ptr: Pointer, size: Int) -> Pointer
    mut fn deallocate(ptr: Pointer)
    mut fn acquire -> Pointer
    mut fn release(ptr: Pointer)
}
```

## Реализации

### HeapAllocator

Стандартный аллокатор, использующий системную heap память:

```efen
use runtime::memory

class HeapAllocator {
    conforms Constructible

    implements Allocator

    @constructor
    fn init(size: Size) -> Self {
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
use runtime::memory

class Arena {
    conforms Constructible

    implements ArenaAllocator, Disposable

    private var buffer: Pointer
    private var offset: Size
    private var capacity: Size

    @constructor
    fn init(size: Size) -> Self {
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

    fn dispose {
        if self.buffer != null {
            free(self.buffer)
        }
    }
}
```

**Пример использования:**

```efen
@allocator(Pool)
class Node {
    conforms Constructible

    var value: Int
    var next: Node?

    @constructor
    fn init(value: Int) -> Self {
        self.value = value
        self.next = null
    }
}

// Каждый Node выделяется из пула и возвращается в него при уничтожении
let head = Node(value: 1)
```

### Stack Allocator

Аллокатор на стеке — для очень короткоживущих данных:

```efen
use runtime::memory

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
use runtime::memory

@allocator(Arena)
class TemporaryData {
    conforms Constructible

    var value: Int

    @constructor
    fn init(value: Int) -> Self {
        self.value = value
    }
}

// Объекты TemporaryData будут выделяться через Arena
let data = TemporaryData(value: 42)
```

Кастомная стратегия памяти:

```efen
class MyClass {
    conforms Constructible

    // Указываем аллокатор для этого класса
    thread let allocator = Pool(
        objectSize: sizeOf(MyClass.self),
        poolSize: 100
    )

    var value: Int

    @constructor
    fn init(value: Int) -> Self {
        self.value = value
    }
}
```

## Composable Allocators

Аллокаторы можно комбинировать:

```efen
// Fallback allocator: сначала пробует pool, потом heap
class FallbackAllocator {
    conforms Constructible

    implements Allocator

    private var primary: Allocator
    private var fallback: Allocator

    @constructor
    fn init(primary: Allocator, fallback: Allocator) -> Self {
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
class TrackingAllocator {
    implements Allocator

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
// Игровой движок: entity выделяются из пула
@allocator(Pool)
class Entity {
    conforms Constructible

    var x: Float
    var y: Float

    @constructor
    fn init(x: Float, y: Float) -> Self {
        self.x = x
        self.y = y
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
