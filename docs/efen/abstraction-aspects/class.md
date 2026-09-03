# Контракты для абстракции класс

Контракты (интерфейсы) определяют набор требований, которым должен соответствовать класс.
В `Efen` классы могут реализовывать один или несколько контрактов, обеспечивая полиморфизм и гибкую архитектуру.

## Основные понятия

**Контракт** — это абстрактное описание поведения, которое класс обязуется предоставить.
Контракты объявляются с помощью ключевого слова `interface`.

**Реализация контракта** — класс использует ключевое слово `implements` для указания,
что он предоставляет конкретную реализацию всех методов контракта.

## Объявление контракта

Простой пример контракта:

```efen
interface Drawable {
    fn draw() -> void;
    fn getColor() -> Color;
}
```

Контракт может содержать:
- Сигнатуры методов (без реализации)
- Свойства (геттеры/сеттеры)
- Вложенные типы
- Константы

## Реализация контракта

Класс реализует контракт, предоставляя конкретные реализации всех его методов:

```efen
class Circle implements Drawable {
    private let radius: Float
    private let color: Color

    fn new(radius: Float, color: Color) {
        this.radius = radius
        this.color = color
    }

    fn draw() -> void {
        // Конкретная реализация рисования круга
        drawCircle(this.radius, this.color)
    }

    fn getColor() -> Color {
        return this.color
    }
}
```

## Множественная реализация контрактов

Класс может реализовывать несколько контрактов одновременно:

```efen
interface Movable {
    fn move(x: Float, y: Float) -> void;
    fn getPosition() -> Point;
}

interface Resizable {
    fn resize(scale: Float) -> void;
    fn getSize() -> Size;
}

class Shape implements Drawable, Movable, Resizable {
    private var position: Point
    private var size: Size
    private var color: Color

    fn draw() -> void {
        // Реализация Drawable
    }

    fn getColor() -> Color {
        return this.color
    }

    fn move(x: Float, y: Float) -> void {
        // Реализация Movable
        this.position = Point::new(x, y)
    }

    fn getPosition() -> Point {
        return this.position
    }

    fn resize(scale: Float) -> void {
        // Реализация Resizable
        this.size = this.size.scale(scale)
    }

    fn getSize() -> Size {
        return this.size
    }
}
```

## Наследование контрактов

Контракты могут наследовать другие контракты, расширяя их требования:

```efen
interface Printable {
    fn print() -> void;
}

interface Serializable extends Printable {
    fn serialize() -> String;
    fn deserialize(data: String) -> void;
}

// Класс должен реализовать все методы обоих контрактов
class Document implements Serializable {
    fn print() -> void {
        // Из Printable
    }

    fn serialize() -> String {
        // Из Serializable
    }

    fn deserialize(data: String) -> void {
        // Из Serializable
    }
}
```

## Множественное наследование контрактов

Контракт может наследовать несколько других контрактов:

```efen
interface Persistable {
    fn save() -> void;
    fn load() -> void;
}

interface Validatable {
    fn validate() -> Bool;
}

interface Entity extends Persistable, Validatable {
    fn getId() -> Int;
}

// Класс должен реализовать методы всех трёх контрактов
class User implements Entity {
    private var id: Int
    private var name: String

    fn getId() -> Int {
        return this.id
    }

    fn save() -> void {
        // Сохранение в БД
    }

    fn load() -> void {
        // Загрузка из БД
    }

    fn validate() -> Bool {
        return this.name.length() > 0
    }
}
```

## Свойства в контрактах

Контракты могут определять требования к свойствам:

```efen
interface Named {
    fn getName() -> String;
    fn setName(name: String) -> void;
}

// Или с использованием синтаксиса свойств
interface Identifiable {
    property id: Int { get; }  // Только чтение
    property name: String { get; set; }  // Чтение и запись
}

class Product implements Identifiable {
    private var _id: Int
    private var _name: String

    property id: Int {
        get { return this._id }
    }

    property name: String {
        get { return this._name }
        set(value) { this._name = value }
    }
}
```

## Контракты с обобщениями

Контракты могут быть обобщёнными (generic):

```efen
interface Container<T> {
    fn add(item: T) -> void;
    fn get(index: Int) -> Option<T>;
    fn size() -> Int;
}

class ArrayList<T> implements Container<T> {
    private var items: [T] = []

    fn add(item: T) -> void {
        this.items[] = item
    }

    fn get(index: Int) -> Option<T> {
        if index >= 0 && index < this.items.count() {
            return Some(this.items[index])
        }
        return None
    }

    fn size() -> Int {
        return this.items.count()
    }
}
```

## Ассоциированные типы в контрактах

Контракты могут определять ассоциированные типы:

```efen
interface Collection {
    type Element;
    type Iterator: Iterator<Element>;

    fn iterator() -> Iterator;
    fn add(item: Element) -> void;
}

class StringList implements Collection {
    type Element = String;
    type Iterator = StringListIterator;

    private var items: [String] = []

    fn iterator() -> StringListIterator {
        return StringListIterator::new(this.items)
    }

    fn add(item: String) -> void {
        this.items[] = item
    }
}
```

## Методы с реализацией по умолчанию

Контракты могут предоставлять реализации по умолчанию для некоторых методов:

```efen
interface Logger {
    fn log(message: String) -> void;

    // Метод с реализацией по умолчанию
    fn logError(message: String) -> void {
        this.log("[ERROR] " + message)
    }

    fn logWarning(message: String) -> void {
        this.log("[WARNING] " + message)
    }
}

class ConsoleLogger implements Logger {
    // Обязательно реализовать только log
    fn log(message: String) -> void {
        println(message)
    }

    // logError и logWarning можно не реализовывать,
    // будут использоваться реализации по умолчанию
}

class CustomLogger implements Logger {
    fn log(message: String) -> void {
        println(message)
    }

    // Можно переопределить метод по умолчанию
    fn logError(message: String) -> void {
        println("!!! " + message + " !!!")
    }
}
```

## Статические методы в контрактах

Контракты могут определять требования к статическим методам:

```efen
interface Factory<T> {
    static fn create() -> T;
    static fn createDefault() -> T {
        return Self::create()
    }
}

class UserFactory implements Factory<User> {
    static fn create() -> User {
        return User::new("Anonymous")
    }
}
```

## Константы в контрактах

Контракты могут определять константы:

```efen
interface MathConstants {
    const PI: Float = 3.14159;
    const E: Float = 2.71828;
}

class Calculator implements MathConstants {
    fn circleArea(radius: Float) -> Float {
        return PI * radius * radius
    }
}
```

## Проверка соответствия контракту

Можно проверить, реализует ли объект определённый контракт:

```efen
fn processDrawable(obj: any) {
    if obj is Drawable {
        let drawable = obj as Drawable
        drawable.draw()
    }
}

// Или с использованием pattern matching
fn process(obj: any) {
    match obj {
        drawable as Drawable => drawable.draw(),
        movable as Movable => movable.move(0, 0),
        _ => println("Unknown type")
    }
}
```

## Контракты как типы

Контракты могут использоваться как типы для полиморфизма:

```efen
fn drawAll(items: [Drawable]) {
    for item in items {
        item.draw()
    }
}

let shapes: [Drawable] = [
    Circle::new(10.0, Color::Red),
    Rectangle::new(20.0, 15.0, Color::Blue),
    Triangle::new(5.0, 8.0, Color::Green)
]

drawAll(shapes)
```

## Запечатанные контракты

Запечатанные контракты (sealed interfaces) могут реализовываться только в том же модуле:

```efen
sealed interface InternalAPI {
    fn process() -> void;
}

// Можно реализовать только в том же модуле
class InternalProcessor implements InternalAPI {
    fn process() -> void {
        // Реализация
    }
}
```

## Маркерные контракты

Маркерные контракты не содержат методов и используются для пометки классов:

```efen
interface Serializable {
    // Пустой контракт - только маркер
}

class Data implements Serializable {
    // Класс помечен как Serializable
}

fn canSerialize(obj: any) -> Bool {
    return obj is Serializable
}
```

## Функциональные контракты

Контракты могут описывать функциональное поведение:

```efen
interface Comparable<T> {
    fn compareTo(other: T) -> Int;
}

class Person implements Comparable<Person> {
    private let name: String
    private let age: Int

    fn compareTo(other: Person) -> Int {
        return this.age - other.age
    }
}

// Теперь можно сортировать
let people: [Person] = [...]
people.sort()  // Использует compareTo
```

## Композиция контрактов

Контракты позволяют реализовать композицию вместо наследования:

```efen
interface Flyable {
    fn fly() -> void;
}

interface Swimmable {
    fn swim() -> void;
}

class Duck implements Flyable, Swimmable {
    fn fly() -> void {
        println("Duck is flying")
    }

    fn swim() -> void {
        println("Duck is swimming")
    }
}

class Airplane implements Flyable {
    fn fly() -> void {
        println("Airplane is flying")
    }
}
```

## Лучшие практики

1. **Минимальные контракты**: Определяйте только необходимые методы
   ```efen
   // Хорошо
   interface Reader {
       fn read() -> String;
   }

   // Плохо - слишком много методов
   interface SuperReader {
       fn read() -> String;
       fn readLine() -> String;
       fn readBytes() -> [Byte];
       fn readAsync() -> Future<String>;
       // ... ещё 20 методов
   }
   ```

2. **Разделение контрактов**: Один контракт — одна ответственность
   ```efen
   // Хорошо
   interface Readable {
       fn read() -> String;
   }

   interface Writable {
       fn write(data: String) -> void;
   }

   // Плохо
   interface ReadWritable {
       fn read() -> String;
       fn write(data: String) -> void;
   }
   ```

3. **Именование контрактов**: Используйте прилагательные или существительные с -able/-ible
   ```efen
   interface Drawable { }
   interface Comparable<T> { }
   interface Iterator<T> { }
   interface Container<T> { }
   ```

4. **Используйте контракты для тестирования**:
   ```efen
   interface UserRepository {
       fn findById(id: Int) -> Option<User>;
       fn save(user: User) -> void;
   }

   // Реальная реализация
   class DatabaseUserRepository implements UserRepository { }

   // Мок для тестов
   class MockUserRepository implements UserRepository { }
   ```

5. **Предпочитайте контракты конкретным типам в параметрах**:
   ```efen
   // Хорошо
   fn processItems(items: Iterable<Item>) { }

   // Хуже
   fn processItems(items: ArrayList<Item>) { }
   ```

## Ограничения

1. Контракты не могут содержать состояние (поля экземпляра)
2. Контракты не могут иметь конструкторов
3. Все методы контракта должны быть реализованы классом (кроме методов с реализацией по умолчанию)
4. Контракты не поддерживают множественное наследование реализаций (только сигнатур)

## Пример комплексного использования

```efen
interface Identifiable {
    fn getId() -> String;
}

interface Timestamped {
    fn getCreatedAt() -> DateTime;
    fn getUpdatedAt() -> DateTime;
}

interface Auditable extends Identifiable, Timestamped {
    fn getCreatedBy() -> String;
    fn getModifiedBy() -> String;
}

interface Persistable {
    fn save() -> Future<void>;
    fn delete() -> Future<void>;
}

class Article implements Auditable, Persistable {
    private let id: String
    private let title: String
    private let createdAt: DateTime
    private var updatedAt: DateTime
    private let createdBy: String
    private var modifiedBy: String

    // Реализация всех методов контрактов
    fn getId() -> String { return this.id }
    fn getCreatedAt() -> DateTime { return this.createdAt }
    fn getUpdatedAt() -> DateTime { return this.updatedAt }
    fn getCreatedBy() -> String { return this.createdBy }
    fn getModifiedBy() -> String { return this.modifiedBy }

    fn save() -> Future<void> {
        this.updatedAt = DateTime::now()
        return database.save(this)
    }

    fn delete() -> Future<void> {
        return database.delete(this.id)
    }
}
```
