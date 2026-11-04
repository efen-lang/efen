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

## RefCount

Пустой контракт `lang::`. Класс со счётчиком владельцев пишет `conforms RefCount`; строка выбирает определение
класса `RefCountClassCompiler` из std, и этот аспект даёт объекту заголовок со счётчиком, методы `retain` и `release`
и соответствие `Cloneable` ([поля, которые требует контракт](../contracts.md#поля-которые-требует-контракт)).

```efen
contract RefCount {
}
```

## RefCountOperations

Контракт, который реализует аспект подсчёта ссылок, а не класс. Вызовы `retain` и `release` расставляет компилятор;
программа их не пишет ([подсчёт ссылок](../memory.md#подсчет-ссылок)).

```efen
contract RefCountOperations {
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

Пустой контракт `lang::`: значение привязано к потоку. Тип-лист пишет `conforms ThreadBound`; тип, который
содержит такое значение, соответствует ему без строки. По умолчанию тип свободен
([общая память](../shared.md#привязка-к-потоку-threadbound)).

```efen
contract ThreadBound {
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
