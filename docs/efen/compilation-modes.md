# Режимы компиляции

`Efen` поддерживает различные режимы компиляции, которые позволяют контролировать процесс компиляции,
оптимизации и выполнения кода в зависимости от требований безопасности и производительности.

## Песочница (Sandbox Mode)

`Efen` поддерживает специальный режим песочницы (sandbox mode),
который позволяет безопасно компилировать код, у которого будут ограничены возможности взаимодействия с внешним миром.

### Основные возможности

Режим песочницы позволяет полностью контролировать какие модули и функции доступны во время компиляции,
а также заменить стандартные модули и функции на свои собственные реализации
или специальные реализации для песочницы.

Режим песочницы также позволяет иначе генерировать финальный код (без изменений исходного кода),
добавляя специальные проверки безопасности и ограничения на выполнение некоторых операций.

### Ограничения в песочнице

```efen
// Конфигурация песочницы
sandbox {
    // Ограничение времени выполнения
    maxExecutionTime: 1000ms

    // Ограничение потребления памяти
    maxMemory: 10MB

    // Возможность прерывания выполнения для циклов
    interruptibleLoops: true

    // Возможность прерывания рекурсии
    interruptibleRecursion: true

    // Максимальная глубина рекурсии
    maxRecursionDepth: 100
}
```

### Ограничение доступных модулей

В режиме песочницы можно явно указать, какие модули доступны:

```efen
sandbox {
    allowedModules: ["std::math", "std::string", "std::collections"]
    deniedModules: ["std::fs", "std::net", "std::process"]
}
```

### Замена стандартных функций

```efen
sandbox {
    // Заменить функцию чтения файлов на безопасную версию
    replace std::fs::read => sandbox::fs::safeRead
    replace std::net::connect => sandbox::net::mockConnect
}
```

### Использование для compile-time кода

Режим песочницы используется для compile-time кода, который выполняется во время компиляции:

```efen
@compileTime
fn generateCode() {
    // Этот код выполняется в песочнице во время компиляции
    let data = readConfigFile("config.json")
    return generateStructs(data)
}
```

### Инъекция проверок безопасности

Песочница может автоматически добавлять проверки в код:

```efen
sandbox {
    injectBoundsChecks: true      // Проверка выхода за границы массива
    injectNullChecks: true         // Проверка на null
    injectOverflowChecks: true     // Проверка переполнения
}

// Исходный код
fn process(arr: [Int], index: Int) -> Int {
    return arr[index] * 2
}

// Компилятор автоматически добавит проверки:
fn process(arr: [Int], index: Int) -> Int {
    if index < 0 || index >= arr.count() {
        panic("Index out of bounds")
    }
    let value = arr[index]
    let result = value * 2
    if result < value {  // Проверка переполнения
        panic("Integer overflow")
    }
    return result
}
```

## Режимы оптимизации

### Debug режим

Режим отладки с минимальными оптимизациями и максимальной отладочной информацией:

```bash
efenc --mode=debug main.efen
```

**Характеристики:**
- Без оптимизаций или минимальные оптимизации
- Полная отладочная информация
- Проверки времени выполнения (bounds checking, null checking)
- Сохранение имён переменных
- Быстрая компиляция

### Release режим

Режим релиза с агрессивными оптимизациями:

```bash
efenc --mode=release main.efen
```

**Характеристики:**
- Максимальные оптимизации
- Минимальная или отсутствующая отладочная информация
- Удаление проверок времени выполнения (если безопасно)
- Инлайнинг функций
- Оптимизация размера бинарника
- Медленная компиляция

### Release with Debug Info

Оптимизированная сборка с отладочной информацией:

```bash
efenc --mode=release-debug main.efen
```

**Характеристики:**
- Агрессивные оптимизации
- Сохранение отладочной информации
- Полезно для профилирования production кода

## Режимы определённые программистом

Программисты могут определять собственные режимы компиляции:

```efen
// Определение пользовательского режима
@compilationMode("testing")
mode testing {
    optimizationLevel: 1
    debugInfo: true
    enableAssertions: true
    mockExternal: true

    // Замена модулей для тестирования
    replace std::net => mock::net
    replace std::fs => mock::fs
}
```

Использование:

```bash
efenc --mode=testing main.efen
```

### Условная компиляция по режиму

```efen
fn connectToDatabase() {
    #if MODE == "production"
        return Database::connect("production.db")
    #elif MODE == "testing"
        return MockDatabase::new()
    #else
        return Database::connect("dev.db")
    #endif
}
```

## Режим проверки типов

### Строгий режим (Strict Mode)

Включение максимально строгой проверки типов:

```efen
@strict
module myModule {
    // Запрещены неявные приведения типов
    // Обязательна обработка всех ошибок
    // Запрещены небезопасные операции
}
```

### Разрешительный режим (Permissive Mode)

Более мягкая проверка типов:

```efen
@permissive
module legacy {
    // Разрешены некоторые неявные приведения
    // Предупреждения вместо ошибок
}
```

## Режим безопасной памяти

### Safe режим

Режим с проверками безопасности памяти:

```bash
efenc --memory-safety=safe main.efen
```

**Характеристики:**
- Проверка выхода за границы массива
- Проверка null pointer
- Проверка use-after-free
- Проверка double-free
- Runtime overhead

### Unsafe режим

Режим без проверок безопасности для максимальной производительности:

```bash
efenc --memory-safety=unsafe main.efen
```

**Характеристики:**
- Без runtime проверок
- Максимальная производительность
- Ответственность на программисте

### Гибридный подход

```efen
fn processData(data: [Int]) {
    // Safe код с проверками
    for item in data {
        validate(item)
    }

    // Unsafe блок для критичных по производительности операций
    unsafe {
        // Без проверок - максимальная скорость
        let ptr = data.rawPointer()
        // Прямая работа с памятью
    }
}
```

## Режимы целевой платформы

### Нативная компиляция

```bash
efenc --target=native main.efen
```

Компиляция для текущей платформы с оптимизациями под конкретный процессор.

### Кросс-компиляция

```bash
efenc --target=x86_64-linux-gnu main.efen
efenc --target=aarch64-apple-darwin main.efen
efenc --target=wasm32-unknown-unknown main.efen
```

### JIT компиляция

Режим динамической компиляции во время выполнения:

```bash
efenc --mode=jit main.efen
```

## Режимы линковки

### Статическая линковка

```bash
efenc --link=static main.efen
```

Всё включается в один исполняемый файл.

### Динамическая линковка

```bash
efenc --link=dynamic main.efen
```

Использование динамических библиотек.

## Профилирующие режимы

### Профилирование производительности

```bash
efenc --profile=perf main.efen
```

Добавляет инструментацию для профилирования.

### Профилирование памяти

```bash
efenc --profile=memory main.efen
```

Отслеживание аллокаций и утечек памяти.

### Coverage режим

```bash
efenc --profile=coverage main.efen
```

Измерение покрытия кода тестами.

## Комбинирование режимов

Режимы можно комбинировать:

```bash
efenc \
    --mode=release \
    --target=x86_64-linux-gnu \
    --memory-safety=safe \
    --link=static \
    --lto=full \
    main.efen
```

## Конфигурация через файл

Создание конфигурационного файла `.efenrc`:

```toml
[mode.production]
optimization = "aggressive"
debug-info = false
memory-safety = "safe"
target = "native"
lto = true

[mode.development]
optimization = "none"
debug-info = true
memory-safety = "safe"
fast-compile = true

[mode.testing]
optimization = "basic"
debug-info = true
assertions = true
mock-external = true
```

Использование:

```bash
efenc --config=.efenrc --mode=production main.efen
```

## Лучшие практики

1. **Используйте debug для разработки**
   ```bash
   efenc --mode=debug main.efen
   ```

2. **Release для production**
   ```bash
   efenc --mode=release --memory-safety=safe main.efen
   ```

3. **Песочница для ненадёжного кода**
   ```efen
   @sandbox
   fn executeUserCode(code: String) {
       // Выполнение в изолированной среде
   }
   ```

4. **Профилирование перед оптимизацией**
   ```bash
   efenc --profile=perf --mode=release main.efen
   ```

5. **Тестирование в режиме близком к production**
   ```bash
   efenc --mode=release-debug main.efen
   ```
