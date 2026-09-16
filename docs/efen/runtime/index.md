# Runtime API

Runtime API в Efen предоставляет низкоуровневые возможности для работы с памятью,
рефлексией, интроспекцией и системными вызовами.

## Обзор

Runtime API организован в следующие модули:

### 1. Управление памятью (`memory`)

Предоставляет контракты и функции для работы с аллокаторами памяти:

- **AllocatorContract** — базовый интерфейс аллокатора
- **ArenaContract** — arena allocator для быстрого выделения временной памяти
- **PoolContract** — pool allocator для объектов фиксированного размера
- **StackAllocator** — аллокатор на стеке
- **HeapAllocator** — стандартный heap allocator

См. [memory.md](memory.md) для детального описания.

### 2. Рефлексия (`reflection`)

Механизмы для интроспекции типов и объектов во время выполнения:

```efen
import runtime.reflection

let typeInfo = TypeInfo.of(MyClass.self)
print(typeInfo.name)           // "MyClass"
print(typeInfo.size)           // Размер в байтах
print(typeInfo.alignment)      // Выравнивание

for property in typeInfo.properties {
    print("${property.name}: ${property.type}")
}

for method in typeInfo.methods {
    print("${method.signature}")
}
```

**Возможности:**
- Получение информации о типах
- Динамический вызов методов
- Доступ к свойствам по имени
- Получение атрибутов и декораторов

### 3. Интроспекция (`introspection`)

Низкоуровневая информация об объектах:

```efen
import runtime.introspection

let obj = MyClass()

// Адрес объекта в памяти
let address = addressOf(obj)

// Размер объекта
let size = sizeOf(obj)

// Выравнивание
let alignment = alignOf(MyClass.self)

// Информация о владении
let ownershipInfo = ownershipOf(obj)
print(ownershipInfo.refCount)
print(ownershipInfo.isWeak)
```

### 4. Intrinsics

Встроенные функции компилятора для оптимизации:

```efen
import runtime.intrinsics

// Атомарные операции
let value = Atomic<Int>(0)
value.fetchAdd(1, ordering: .sequentiallyConsistent)

// Prefetch для оптимизации кеша
prefetch(address, locality: .high, intent: .read)

// Вероятность ветвления
if likely(condition) {
    // Часто выполняется
}

if unlikely(error) {
    // Редко выполняется
}

// SIMD операции
let vec1 = SIMD4<Float>(1, 2, 3, 4)
let vec2 = SIMD4<Float>(5, 6, 7, 8)
let result = vec1 + vec2
```

### 5. Системные вызовы (`syscall`)

Прямой доступ к системным вызовам (platform-specific):

```efen
import runtime.syscall

// Linux/Unix
let fd = syscall.open("/path/to/file", O_RDONLY)
let bytesRead = syscall.read(fd, buffer, count)
syscall.close(fd)

// Windows
let handle = syscall.CreateFileW(path, GENERIC_READ, ...)
syscall.ReadFile(handle, buffer, count, ...)
syscall.CloseHandle(handle)
```

### 6. Thread Local Storage (TLS)

Поточно-локальное хранилище:

```efen
import runtime.tls

@threadLocal var counter: Int = 0

fn incrementCounter {
    counter += 1  // Каждый поток имеет свою копию
}
```

### 7. Fiber/Coroutine Support

Легковесные потоки выполнения:

```efen
import runtime.fiber

let fiber = Fiber {
    print("Fiber started")
    yield()
    print("Fiber resumed")
}

fiber.resume()  // "Fiber started"
fiber.resume()  // "Fiber resumed"
```

### 8. Stack Management

Управление стеком:

```efen
import runtime.stack

// Получить текущий размер стека
let stackSize = getCurrentStackSize()

// Проверить доступное место на стеке
if getStackSpaceAvailable() < 1024 {
    error("Stack overflow imminent")
}

// Установить guard page
setStackGuard(size: 4096)
```

### 9. Exception Handling (Low-level)

Низкоуровневая работа с исключениями:

```efen
import runtime.exceptions

// Получить текущее исключение
if let exception = getCurrentException() {
    print("Exception: ${exception.message}")
    print("Stack trace: ${exception.stackTrace}")
}

// Пробросить исключение дальше
rethrow(exception)

// Установить обработчик необработанных исключений
setUnhandledExceptionHandler => {
    logError($exception)
    terminate()
}
```

### 10. Debug Support

Поддержка отладки:

```efen
import runtime.debug

// Breakpoint (только в debug режиме)
debugBreak()

// Вывод stack trace
printStackTrace()

// Проверка ассертов
assert(condition, "Assertion failed")
debugAssert(condition)  // Только в debug

// Memory sanitizer
if isAddressSanitizerEnabled() {
    // Дополнительные проверки
}
```

## Режимы компиляции и Runtime

Runtime API может вести себя по-разному в зависимости от режима компиляции:

### Debug режим
- Все проверки включены
- Доступна полная рефлексия
- Stack traces детализированы
- Дополнительные assertion'ы

### Release режим
- Минимальные проверки
- Рефлексия может быть ограничена
- Оптимизации включены
- Debug символы удалены

### Profile режим
- Включены счетчики производительности
- Трейсинг выделения памяти
- CPU profiling hooks

## Платформо-зависимые API

Некоторые runtime API доступны только на определенных платформах:

```efen
#if os(Linux)
    import runtime.linux
    let tid = gettid()
#elseif os(Windows)
    import runtime.windows
    let tid = GetCurrentThreadId()
#elseif os(macOS)
    import runtime.darwin
    let tid = pthread_self()
#endif
```

## Интеграция с C/C++

Runtime API обеспечивает интероперабельность с C/C++ кодом:

```efen
import runtime.ffi

// Загрузка динамической библиотеки
let lib = DynamicLibrary.load("libexample.so")

// Получение символа
let symbol = lib.symbol("my_function")

// Вызов C функции
typealias MyCFunction = @convention(c) (Int32) -> Int32
let cFunction = unsafeBitCast(symbol, to: MyCFunction.self)
let result = cFunction(42)
```

## Управление жизненным циклом приложения

Runtime предоставляет hooks для управления жизненным циклом:

```efen
import runtime.lifecycle

// Регистрация обработчика запуска
registerStartupHandler {
    print("Application starting...")
}

// Регистрация обработчика завершения
registerShutdownHandler {
    print("Application shutting down...")
    cleanup()
}

// Регистрация обработчика сигналов
registerSignalHandler(.SIGTERM) {
    print("Received SIGTERM")
    gracefulShutdown()
}
```

## Performance Monitoring

Встроенные счетчики производительности:

```efen
import runtime.perf

let counter = PerfCounter()
counter.start()

// Код для измерения
performHeavyComputation()

counter.stop()
print("Elapsed: ${counter.elapsedNanoseconds} ns")
print("CPU cycles: ${counter.cpuCycles}")
```

## Memory Barriers

Барьеры памяти для многопоточности:

```efen
import runtime.sync

// Полный барьер памяти
memoryBarrier()

// Барьер только для чтения
loadBarrier()

// Барьер только для записи
storeBarrier()

// Acquire/Release семантика
acquireBarrier()
releaseBarrier()
```

## Лучшие практики

1. **Используйте высокоуровневые API когда возможно**
   - Runtime API предназначен для специальных случаев
   - Предпочитайте стандартную библиотеку

2. **Проверяйте платформу**
   - Используйте условную компиляцию для платформо-зависимого кода
   - Предоставляйте fallback реализации

3. **Тестируйте в разных режимах**
   - Код может вести себя по-разному в debug/release
   - Используйте sanitizers

## Ограничения

- Рефлексия может быть недоступна для некоторых типов в release режиме
- Некоторые функции доступны только на определенных платформах
- Runtime overhead зависит от используемых возможностей

## См. также

- [memory.md](memory.md) — Управление памятью
- [../types/ownership.md](../types/ownership.md) — Система владения
- [../compile-time/index.md](../compile-time/index.md) — Compile-time API
- [../meta/metadata.md](../aspects/metadata.md) — Метаданные
