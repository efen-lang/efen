# Система типов компилятора

Данный документ описывает внутреннюю систему типов компилятора PHX, которая используется для управления типами и контрактами во время компиляции.

## Архитектура

Система типов компилятора состоит из четырёх основных компонентов:

1. **TypeDescriptor** - дескриптор типа данных
2. **ContractDescriptor** - дескриптор контракта
3. **TypeRegistry** - реестр всех типов и контрактов
4. **TypeResolver** - механизм разрешения типов

## TypeDescriptor

`TypeDescriptor` представляет собой дескриптор типа данных в системе компиляции.

### Виды типов

```cpp
enum class TypeKind {
    Primitive,    // Примитивные типы (Int, String, Bool и т.д.)
    Structure,    // Структуры данных
    Class,        // Классы
    Interface,    // Интерфейсы
    Service,      // Сервисы
    Context,      // Контексты
    Aspect,       // Аспекты
    TypeDef,      // Определения типов (алиасы, refinement types)
    Generic       // Обобщённые типы
};
```

### Статус разрешения типа

```cpp
enum class TypeResolutionStatus {
    FullyResolved,      // Тип полностью разрешён
    PartiallyResolved,  // Тип частично разрешён
    Unresolved          // Тип не разрешён
};
```

### Основные методы

- `getName()` - получить имя типа
- `getKind()` - получить вид типа
- `getResolutionStatus()` - получить статус разрешения
- `addContract(contract)` - добавить контракт к типу
- `getContracts()` - получить все контракты типа
- `isBuiltin()` - проверить, является ли тип встроенным
- `isResolved()` - проверить, разрешён ли тип

## ContractDescriptor

`ContractDescriptor` представляет собой дескриптор контракта - описания поведения типа.

### Структура контракта

Контракт содержит:
- **Имя контракта**
- **Базовые контракты** (наследование)
- **Свойства** (`ContractProperty`)
- **Методы** (`ContractMethod`)

### Свойства контракта

```cpp
struct ContractProperty {
    std::string name;           // Имя свойства
    std::string typeName;       // Тип свойства
    PropertyAccess access;      // Доступ (Get, Set, GetSet)
    bool isCompileTime;         // Доступно во время компиляции
    SourceLocation location;    // Расположение в коде
};
```

### Методы контракта

```cpp
struct ContractMethod {
    std::string name;                                      // Имя метода
    std::string returnType;                                // Тип возвращаемого значения
    std::vector<std::pair<std::string, std::string>> parameters;  // Параметры (имя, тип)
    bool isCompileTime;                                    // Доступно во время компиляции
    SourceLocation location;                               // Расположение в коде
};
```

### Валидация совместимости

Метод `validateCompatibility()` проверяет, совместимы ли два контракта при множественном наследовании.

## TypeRegistry

`TypeRegistry` - центральное хранилище всех типов и контрактов в системе компиляции.

### Регистрация типов

```cpp
auto type = registry.registerType("MyClass", TypeKind::Class, "MyModule", "MyPackage");
```

### Регистрация контрактов

```cpp
auto contract = registry.registerContract("MyContract", "MyModule", "MyPackage");
```

### Поиск типов и контрактов

```cpp
auto type = registry.lookupType("Int");
auto contract = registry.lookupContract("Equatable");
```

### Встроенные типы

При инициализации регистр автоматически создаёт встроенные типы:
- `Int`, `Int8`, `Int16`, `Int32`, `Int64`
- `UInt`, `UInt8`, `UInt16`, `UInt32`, `UInt64`
- `Float`, `Float32`, `Float64`
- `Bool`, `String`, `Void`

### Встроенные контракты

При инициализации регистр создаёт базовые контракты:
- **Equatable** - сравнение на равенство
- **Comparable** - сравнение (extends Equatable)
- **Hashable** - хеширование (extends Equatable)
- **StringConvertible** - преобразование в строку

## TypeResolver

`TypeResolver` обеспечивает механизм отложенного разрешения типов.

### Зачем нужен отложенный механизм

Когда компилятор встречает ссылку на тип, который ещё не был определён (например, тип находится в другом модуле), он создаёт запрос на отложенное разрешение.

### Использование

```cpp
TypeResolver resolver(registry);

// Попытка разрешить тип
auto type = resolver.resolveType("MyClass", "MyModule", "MyPackage");

if (!type) {
    // Если тип не найден, отложить разрешение
    resolver.deferTypeResolution(
        "MyClass",
        "MyModule",
        "MyPackage",
        location,
        [](auto resolvedType) {
            // Callback вызовется, когда тип будет разрешён
        }
    );
}

// Позже, после загрузки всех модулей
resolver.resolvePendingTypes();
```

### Статистика разрешения

```cpp
auto stats = resolver.getStats();
std::cout << "Unresolved: " << stats.unresolvedRequests << std::endl;
```

## Пример использования

### Создание типа с контрактами

```cpp
TypeRegistry registry;

// Создать контракт
auto printableContract = registry.registerContract("Printable");
ContractMethod printMethod("print", "Void");
printableContract->addMethod(printMethod);

// Создать тип
auto myClassType = registry.registerType("MyClass", TypeKind::Class);
myClassType->addContract(printableContract);
myClassType->setResolutionStatus(TypeResolutionStatus::FullyResolved);

// Найти тип
auto foundType = registry.lookupType("MyClass");
if (foundType) {
    auto contracts = foundType->getContracts();
    // Работа с контрактами...
}
```

### Отложенное разрешение

```cpp
TypeResolver resolver(registry);

// В модуле A ссылаемся на тип из модуля B
auto type = resolver.resolveType("TypeFromModuleB", "ModuleA");
if (!type) {
    // Тип не найден, отложить разрешение
    resolver.deferTypeResolution("TypeFromModuleB", "ModuleB", "", location);
}

// После загрузки модуля B
registry.registerType("TypeFromModuleB", TypeKind::Class, "ModuleB");

// Разрешить отложенные типы
if (!resolver.resolvePendingTypes()) {
    // Всё ещё есть неразрешённые типы
    auto unresolved = resolver.getUnresolvedRequests();
    for (const auto& req : unresolved) {
        std::cerr << "Unresolved type: " << req.typeName << std::endl;
    }
}
```

## Интеграция с AST

При обработке AST узлов типа `TypeRef`, компилятор должен:

1. Найти тип в `TypeRegistry`
2. Если тип не найден, создать запрос в `TypeResolver`
3. Сохранить ссылку на `TypeDescriptor` в структуре данных параметра/переменной
4. После обработки всех модулей, вызвать `resolvePendingTypes()`

## Файлы

- `include/TranslationUnit/TypeDescriptor.h` - дескриптор типа
- `include/TranslationUnit/ContractDescriptor.h` - дескриптор контракта
- `include/TranslationUnit/TypeRegistry.h` - реестр типов и контрактов
- `include/TranslationUnit/TypeResolver.h` - механизм разрешения типов
- `src/TranslationUnit/TypeDescriptor.cpp`
- `src/TranslationUnit/ContractDescriptor.cpp`
- `src/TranslationUnit/TypeRegistry.cpp`
- `src/TranslationUnit/TypeResolver.cpp`
