# Аспекты абстракций в Efen

В `Efen` аспекты абстракций позволяют определять логику работы абстракций.
Аспекты абстракций напрямую влияют на работу компилятора.

## Аспекты класса уровня компиляции

Аспекты класса уровня компиляции позволяют определять логику работы абстракций на уровне компиляции.

```efen
aspect RefCountClassCompiler {

    conforms lang::abstractions::ClassAspect
    conforms lang::abstractions::RefCountedAspect

    // Структура данных, которая будет использоваться для хранения данных класса
    @classStruct struct <T> {
        var refCount: Int
        T
    }

    /// Вызывается во время компиляции после определения класса
    @compileTime
    fn definition(class: lang::Class) {
        
    }

    // Вызывается при создании нового экземпляра класса
    @compileTime
    fn newInstance(ctx: pxh::compiler::context) -> lang::Reference {
        
    }
    
    fn allocate() -> Self {        
        let obj = Allocator::allocate(Self)
        return obj
    }
    
    fn deallocate(self: Self) {
        Allocator::deallocate(Self)
    }
    
    fn retain(self: Self) {
        Self.refCount     += 1  
    }
    
    fn release(self: Self) {
        if Self.refCount == 0 {
            throw lang::errors::RuntimeError("Release called on object with refCount 0")
        }
        
        Self.refCount     -= 1
                     
        if Self.refCount == 0 {
            Self.deinit()
            Allocator::deallocate(self)
        }
    }
}
```
    