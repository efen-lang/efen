# Классы

> Классы являются абстракцией над структурами данных и поведением объектов.

Классы скрывают работу со структурами данных и предоставляют программисту удобный синтаксис для определения
состояния и поведения объектов. Классы могут иметь состояние (свойства) и поведение (методы).

## Определение класса

Базовый пример класса:

```efen
class Person {
    var name: String
    var age: Int

    fn greet {
        print("Hello, my name is ${name}")
    }

    fn haveBirthday {
        age += 1
        print("${name} is now ${age} years old")
    }
}
```

Использование класса:

```efen
let person = Person(name: "Alice", age: 30)
person.greet()  // Выведет: "Hello, my name is Alice"
person.haveBirthday()  // Выведет: "Alice is now 31 years old"
```

## Конструкторы

`Self` является алиасом текущего лексического класса, в объявлении которого он
написан. Он не меняется на тип наследника при позднем связывании.

Классы могут иметь пользовательские конструкторы:

```efen
class Rectangle {
    var width: Float
    var height: Float

    @constructor
    fn init(width: Float, height: Float) -> Self {
        self.width = width
        self.height = height
    }

    fn area -> Float {
        return width * height
    }
}

let rect = Rectangle(width: 10.0, height: 5.0)
```

До полной инициализации `self` не может escape: его нельзя вернуть, сохранить,
захватить или передать внешнему вызову. Compiler-proven `private final` helper
допустим, если он не выпускает `self` и не читает неинициализированные поля.
Обычная виртуальная диспетчеризация не отключается в constructor, включая
наиболее производный override; порядок и proof construction safety остаются
явной открытой границей.

## Наследование классов

Классы и методы являются final по умолчанию. `open class` разрешает
наследование, а `open fn` — переопределение метода:

```efen
final class Closed {}
```

Явный `final` закрепляет и документирует то же ограничение, которое действует
по умолчанию. Он также доступен для метода.

```efen
open class Animal {
    var name: String

    open fn makeSound {
        print("Some generic sound")
    }
}

class Dog: Animal {
    var breed: String

    override fn makeSound {
        print("Woof!")
    }

    fn fetch {
        print("${name} is fetching the ball")
    }
}

let dog = Dog(name: "Buddy", breed: "Golden Retriever")
dog.makeSound()  // Выведет: "Woof!"
dog.fetch()  // Выведет: "Buddy is fetching the ball"
```

`override fn` переопределяет открытый метод и снова делает его final. Если
следующий наследник тоже должен иметь право переопределения, текущий уровень
пишет `open fn`; наличие базового метода уже означает override:

```efen
open class Middle: Animal {
    open fn makeSound {
        print("Middle")
    }
}
```

`open fn` внутри final-класса является ошибкой, поскольку такой метод невозможно
унаследовать. Отдельного модификатора `abstract` в Efen нет.

## Реализация интерфейсов

Классы могут реализовывать один или несколько интерфейсов:

```efen
interface Drawable {
    fn draw
}

interface Resizable {
    fn resize(scale: Float)
}

class Circle {
    implements Drawable, Resizable

    var radius: Float
    var position: Point

    fn draw {
        print("Drawing circle at ${position} with radius ${radius}")
    }

    fn resize(scale: Float) {
        radius *= scale
    }
}
```

## Соответствие контрактам

Классы могут соответствовать контрактам времени компиляции:

```efen
contract Serializable {
    fn serialize -> String
    fn deserialize(data: String)
}

class User {
    conforms Serializable

    var name: String
    var email: String

    fn serialize -> String {
        return "${name};${email}"
    }

    fn deserialize(data: String) {
        let parts = data.split(separator: ";")
        self.name = parts[0]
        self.email = parts[1]
    }
}
```

## Комбинирование наследования, интерфейсов и контрактов

Класс может одновременно наследоваться от базового класса, реализовывать интерфейсы и соответствовать контрактам:

```efen
contract Validatable {
    fn validate -> Bool
}

interface Storable {
    fn save
    fn load
}

open class Entity {
    var id: Int
    var createdAt: DateTime
}

class Product: Entity {
    conforms Validatable
    implements Storable

    var name: String
    var price: Float

    fn validate -> Bool {
        return !name.isEmpty && price > 0
    }

    fn save {
        print("Saving product ${name}")
    }

    fn load {
        print("Loading product")
    }
}
```

Синтаксис:
- `: BaseClass` в заголовке — одиночное наследование класса. После `:` стоит
  только базовый класс, интерфейсы там не перечисляются
- `conforms Contract1, Contract2` в теле — соответствие контрактам (множественное)
- `implements Interface1, Interface2` в теле — реализация интерфейсов

Каждое из объявлений `conforms` и `implements` пишется одной строкой через запятую.
В теле первой идёт строка `conforms`, за ней `implements`, затем члены класса.

## Свойства класса

### Вычисляемые свойства

Классы могут иметь вычисляемые свойства:

```efen
class Rectangle {
    var width: Float
    var height: Float

    var area: Float {
        get {
            return width * height
        }
    }

    var perimeter: Float {
        get {
            return 2 * (width + height)
        }
    }
}

let rect = Rectangle(width: 10.0, height: 5.0)
print(rect.area)  // Выведет: 50.0
print(rect.perimeter)  // Выведет: 30.0
```

### Свойства с наблюдателями

Свойства могут иметь наблюдатели изменений:

```efen
class Temperature {
    var celsius: Float {
        didSet {
            print("Temperature changed from ${oldValue} to ${celsius}")
        }
        willSet {
            print("Temperature will change to ${newValue}")
        }
    }
}
```

## Методы класса

### Статические методы

Классы могут иметь статические методы и свойства:

```efen
class Math {
    const PI: Float = 3.14159

    static fn max(a: Float, b: Float) -> Float {
        return a > b ? a : b
    }

    static fn min(a: Float, b: Float) -> Float {
        return a < b ? a : b
    }
}

let maxValue = Math.max(a: 10.0, b: 20.0)
let pi = Math.PI
```

`const` в классе уже является static compile-time значением. `static let` —
другая конструкция: один runtime-слот класса, который инициализируется eagerly.
Его initializer может бросить; такая ошибка завершает startup приложения, а не
откладывается до первого чтения поля. Зависимость инициализируется полностью до
использующего её класса. Порядок независимых модулей и инстанциаций generic
классов остаётся отдельной темой.

### Методы экземпляра

Обычные методы работают с конкретным экземпляром класса:

```efen
class Counter {
    var count: Int = 0

    fn increment {
        count += 1
    }

    fn decrement {
        count -= 1
    }

    fn reset {
        count = 0
    }
}
```

## Проекции класса

Проекции это мощный механизм объявить разные представления одной и той же структуры данных
с целью манипуляций.

Проекция может временно изменить доступ к свойствам класса, а после 
преобразовать проекцию в сам класс или другую проекцию.

Так как проекции гарантируют совершенное бинарное равенство 
между исходной структурой и проекцией, проекции позволяют временно раскрыть данные класса
без опасности нарушить внутреннее состояние или логику внутреннего состояния. При этом операции
будут происходить физически на одной и той же структуре данных без копирования.

Механизм проекций так же позволяет выделять память для класса в разных аллокаторах, 
а после инициализировать класс с помощью конструктора без копирования данных, переноса и так далее.

При этом проекции гарантируют безопасность доступа к данным, сохранения сокрытия данных, 
так как они описывают манипуляции над разными типами данных, и с точки зрения
компилятора программист не может без явного преобразования превратить один тип в другой.

## Управление памятью

Классы являются ссылочными типами. Несколько переменных могут ссылаться на один и тот же объект:

```efen
class Box {
    var value: Int
}

let box1 = Box(value: 10)
let box2 = box1  // box2 ссылается на тот же объект

box2.value = 20
print(box1.value)  // Выведет: 20 (оба ссылаются на один объект)
```

## Ключевые особенности классов

- **Ссылочный тип**: Классы передаются по ссылке, в отличие от структур
- **Одиночное наследование**: Класс может наследоваться только от одного базового класса
- **Множественная реализация интерфейсов**: Класс может реализовывать несколько интерфейсов
- **Соответствие контрактам**: Класс может соответствовать нескольким контрактам через `conforms`
- **Расширение через стратегии**: К классам могут применяться стратегии для добавления функциональности
- **Инкапсуляция**: Классы скрывают внутреннюю реализацию и предоставляют публичный API
