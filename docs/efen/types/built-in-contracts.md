# Встроенные контракты

Типы обладают своими собственными встроенными контрактами.

## TypeContract

Базовый контракт для всех типов данных.

```efen
contract TypeContract {

    enum TypeKind {
        Primitive,
        Structure,
        Class,
        Interface,
        Service,
        Context,
        Aspect,
        TypeDef,
        Pointer,
        Generic
    }

    var name: String
    var kind: TypeKind
    var size: Size
}
```

## ArcClass

Контракт `lang::` без требований. Класс со счётчиком владельцев пишет `conforms ArcClass`. Реализацию даёт аспект
извне ([реализация извне](../contracts.md#реализация-извне)), по умолчанию `ArcCounter` из runtime: поле счётчика,
методы `retain` и `release` и соответствие `Cloneable`.
ARC здесь — Automatic Reference Counting: вызовы `retain` и `release` расставляет компилятор. Счётчик не атомарный;
счётчик, общий для нескольких потоков, — тема `shared class` ([общие классы](../shared.md)).

```efen
contract ArcClass {
    allow implementations from runtime, std
}
```

## Constructible

Пустой контракт `lang::`. Класс, у которого есть пользовательские конструкторы `@constructor`, пишет
`conforms Constructible`; без этой строки `@constructor` — ошибка компиляции. У такого класса нет создания из полей:
объект создаётся только конструктором. Класс без `Constructible` создаётся из полей (`Box(value: 10)`): это запись
данных, пользовательский код не выполняется ([классы](../classes.md#определение-класса)).

```efen
contract Constructible {
}
```

## Destructible

Пустой контракт `lang::`. Класс, у которого есть деструкторы `@destructor`, пишет `conforms Destructible`; без этой
строки `@destructor` — ошибка компиляции. Без деструктора уничтожение объекта — `dispose`, если класс
`implements Disposable`, затем уничтожение его полей и освобождение памяти ([Disposable](../disposable.md#запись)).
`Disposable` контракта `Destructible` не требует.

```efen
contract Destructible {
}
```

## OpenClass

Контракт `lang::` без требований. Корень иерархии с `open class` пишет `conforms OpenClass`; без этой строки `open`
у корня — ошибка компиляции, наследники соответствуют ему через корень. Описатель класса в объекте, по которому
работают переопределённые методы, интерфейсные таблицы наследников и `catch` по классу, даёт аспект извне
([реализация извне](../contracts.md#реализация-извне)), по умолчанию `ClassDescriptor` из runtime.

```efen
contract OpenClass {
    allow implementations from runtime, std
}
```

## ArcOperations

Контракт, который реализует аспект подсчёта ссылок (`ArcCounter`), а не класс. Вызовы `retain` и `release` расставляет компилятор;
программа их не пишет ([подсчёт ссылок](../memory.md#подсчет-ссылок)).

```efen
contract ArcOperations {
    mut fn retain
    mut fn release
}
```

## ImplicitlyDestroyable

Пустой контракт `lang::`: компилятор может уничтожить значение такого типа в точке, которую программа не называет.
Соответствие вычисляется, а не пишется ([Disposable](../disposable.md#implicitlydestroyable)).

```efen
contract ImplicitlyDestroyable {
}
```

## ThreadBound

Пустой контракт `lang::`: значение привязано к потоку. `conforms ThreadBound` пишет тип, который привязан к потоку
сам по себе; тип с полем, элементом, захватом или полем `layout` такого типа соответствует ему без строки. По
умолчанию тип свободен
([общая память](../shared.md#привязка-к-потоку-threadbound)).

```efen
contract ThreadBound {
}
```

## Freezable

Пустой контракт `lang::`: значение типа допускает заморозку в слот `immutable T`. Соответствие вычисляется по полям,
элементам, захватам и полям `layout`; строку не пишут. `conforms Freezable` пишет только класс над внешним значением:
компилятор её не проверяет, это точка доверия, и `efen proofs` показывает её как место без доказательства
([неизменяемость](../immutability.md#какие-типы-замораживаются)).

```efen
contract Freezable {
}
```

## IndirectExtensions

Контракт `lang::` без требований. Корень открытого `variant` пишет `conforms IndirectExtensions`, чтобы данные
constructors его расширений лежали в куче и размер корня не зависел от программы ([схемы
хранения](variant.md#схемы-хранения)).

```efen
open variant Shape {
    conforms IndirectExtensions
    dot
}
```
