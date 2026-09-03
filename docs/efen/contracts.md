# Контракты

> Контакт -- высшая языковая абстракция времени компиляции, которая описывает правила формирования других абстракций.

Контракт устанавливает какие свойства и методы должны быть определены в абстракции.

Примеры контрактов:
```efen
contract MyContract {
    var myProperty: Int { get set }
    func myMethod()
}
```

## ⚠️ Contract vs Interface: Ключевое различие

**Это фундаментальная концепция Efen, которую необходимо понимать:**

### Contract — compile-time абстракция
- ✅ Существует **только** во время компиляции
- ✅ После компиляции **полностью исчезает** из бинарника
- ✅ Используется компилятором для проверки корректности кода
- ✅ **Нулевой runtime overhead** — не влияет на производительность
- ✅ Статическая диспетчеризация (static dispatch)

### Interface — runtime абстракция
- ✅ Существует в **runtime** как **VTBL** (виртуальная таблица)
- ✅ Присутствует в скомпилированном бинарнике
- ✅ Позволяет полиморфизм во время выполнения
- ✅ Имеет runtime overhead (косвенный вызов через VTBL)
- ✅ Динамическая диспетчеризация (dynamic dispatch)

### Практический пример

```efen
// CONTRACT: только compile-time
contract Drawable {
    fn draw()
}

// INTERFACE: runtime VTBL
interface Shape {
    fn area() -> Float
}

// Класс соответствует контракту и реализует интерфейс
class Circle {
    conforms Drawable      // Compile-time проверка
    implements Shape       // Runtime VTBL

    var radius: Float

    fn draw() {
        // Реализация требования контракта
        print("Рисую круг")
    }

    fn area() -> Float {
        // Реализация метода интерфейса
        return 3.14 * radius * radius
    }
}
```

### Что происходит после компиляции?

```efen
// Compile-time: компилятор проверяет что draw() есть
fn renderStatic<T: Drawable>(object: T) {
    object.draw()  // STATIC DISPATCH - прямой вызов
}

// Runtime: используется VTBL для полиморфизма
fn calculateArea(shape: Shape) -> Float {
    return shape.area()  // DYNAMIC DISPATCH - вызов через VTBL
}
```

**После компиляции:**
- `Drawable` контракт **исчез** — вызов `draw()` скомпилирован напрямую
- `Shape` интерфейс **присутствует** как VTBL в бинарнике
- `calculateArea` может принимать **любой** объект реализующий Shape

### Когда использовать что?

**Используйте Contract когда:**
- ✅ Нужны generic constraints (ограничения на типы)
- ✅ Критична производительность (нет runtime overhead)
- ✅ Тип известен во время компиляции
- ✅ Хотите максимальную оптимизацию компилятора

**Используйте Interface когда:**
- ✅ Нужен runtime полиморфизм
- ✅ Тип неизвестен во время компиляции
- ✅ Хотите binary compatibility (совместимость бинарников)
- ✅ Реализуете plugin system или динамическую загрузку

### Комбинация Contract + Interface

Можно использовать оба одновременно для максимальной гибкости:

```efen
// Контракт для compile-time проверок
contract Serializable {
    fn serialize() -> String
}

// Интерфейс для runtime полиморфизма
interface Storable {
    fn save(path: String)
}

class Document {
    conforms Serializable  // Compile-time гарантия
    implements Storable    // Runtime возможность

    fn serialize() -> String {
        return "..."
    }

    fn save(path: String) {
        let data = serialize()  // Статический вызов
        writeToFile(path, data)
    }
}

// Generic с контрактом - нулевой overhead
fn sendOver<T: Serializable>(object: T) {
    let data = object.serialize()  // STATIC - оптимально
    network.send(data)
}

// Полиморфный с интерфейсом - runtime гибкость
fn saveAll(objects: [Storable]) {
    for obj in objects {
        obj.save("/tmp/file")  // DYNAMIC - через VTBL
    }
}
```

См. также: [interfaces.md](interfaces.md) для подробного описания интерфейсов.

## Наследование контрактов

Контракты могут наследоваться друг от друга. При наследовании правила контрактов не должны противоречить друг другу.

```efen
contract BaseContract {
    var baseProperty: Int { get set }
    func baseMethod()
}

contract DerivedContract : BaseContract {
    var derivedProperty: String { get set }
    func derivedMethod()
}
```

Множественное наследование контрактов:
```efen
contract FirstContract {
    var firstProperty: Int { get set }
}

contract SecondContract {
    var secondProperty: String { get set }
}

contract CombinedContract : FirstContract, SecondContract {
    func combinedMethod()
}
```

**Важно:** При множественном наследовании компилятор проверит, что требования базовых контрактов не противоречат друг другу.

## Связь контрактов с интерфейсами

Интерфейс может **соответствовать** (`conforms`) одному или нескольким контрактам. Это означает, что
компилятор проверит на этапе компиляции, что интерфейс удовлетворяет всем требованиям контракта.

Базовый пример:
```efen
interface MyInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Интерфейс с наследованием от родительского интерфейса:
```efen
interface ParentInterface {
    var parentProperty: Bool { get set }
    func parentMethod()
}

interface MyInterface : ParentInterface {
    conforms MyContract

    var anotherProperty: String { get set }
}
```

Множественные контракты:
```efen
contract SecondContract {
    func additionalMethod()
}

interface MyInterface : ParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```

Множественное наследование интерфейсов с контрактами:
```efen
interface AnotherParentInterface {
    var anotherParentProperty: Float { get set }
}

interface MyInterface : ParentInterface, AnotherParentInterface {
    conforms MyContract, SecondContract

    var anotherProperty: String { get set }
}
```
