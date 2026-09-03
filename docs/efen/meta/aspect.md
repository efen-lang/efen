# Аспекты

> Аспекты - это инструмент метапрограммирования, 
> который позволяет программисту описывать свойства абстракций на этапе компиляции.

Возможности аспектов:

 * Аспекты могут быть применены к классам, интерфейсам, стратегиям и другим аспектам.
 * Аспекты могут требовать от кода реализации определённых методов и свойств.
 * Аспекты могут требовать от кода реализации контрактов или интерфейсов.
 * Аспекты могут добавлять к целевому коду новые методы и свойства.
 * Аспекты могут добавлять к целевому коду новые контракты и интерфейсы.
 * Аспекты могут изменять поведение компилятора при разрешении компонентов абстракции.
 * Аспекты могут работать как шаблоны для генерации кода.
 * Аспекты имеют полный доступ к этапу компиляции целевого кода.
 * Аспекты могут взаимодействовать с другими аспектам на этапе компиляции, производя вычисления.
 * Аспекты могут управлять метаданными целевого кода. Добавлять или изменять атрибуты.
 * Аспекты могут подмешивать поведение в целевой код.

## Синтаксис

```efen
aspect AspectName
{
    meta {
        // Метаданные аспекта
        // Например, атрибуты, описание и т.д.
        // А так же код времени компиляции
        strategy for Class {
            fn addMethod() {
                // Алгоритм добавление нового метода к классу
            }
        }
    }

    // Aspect can be
    applied for classes, interfaces, strategies, aspects;

    // Requirements
    
    required aspect AnotherAspect
    required contract ContractName
    required interface InterfaceName
    required property PropertyName: PropertyType
    optional method MethodName(Param1: Type1, Param2: Type2) -> ReturnType
    
    // Mixins
    property NewProperty: PropertyType = InitialValue
    
    method NewMethod(Param: Type) -> ReturnType {
        // Implementation
    }    
}
```

Применение аспекта:

```efen
class MyClass {
    use AspectName;
    // Class implementation
}

Пример generic аспекта:

```efen
aspect Queue<Item> {
    array items: Item[] = [];
    required method enqueue(item: Item);
    required method dequeue() -> Item;
}

class IntQueue {
    use Queue<Int>;
    
    method enqueue(item: Int) {
        items.push(item);
    }
    
    method dequeue() -> Int {
        return items.pop();
    }
}
```

Это генерик с мономорфизацией.
Аспект `Queue` определяет обобщённую очередь для элементов типа `Item`, а 
класс `IntQueue` реализует очередь для целых чисел, используя аспект `Queue<Int>`.
