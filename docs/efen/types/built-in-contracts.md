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
    fn retain
    fn release
    var referenceCount: Int { get }
}
```