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

## ReferenceCounterContract

Контракт для типов с подсчётом ссылок.

```efen
contract ReferenceCounterContract {
    mut fn retain
    mut fn release
    var referenceCount: Int { get }
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
