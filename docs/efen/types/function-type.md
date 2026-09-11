# Тип функции

Тип функции описывает сигнатуру функции - типы параметров и тип возвращаемого значения, 
область видимости и другие характеристики.

## Синтаксис

```efen
(ParameterType1, ParameterType2, ...) -> ReturnType
```

Примеры:

```efen
// Функция без параметров, возвращающая Int
let getNumber: () -> Int

// Функция с двумя параметрами Int, возвращающая Int
let add: (Int, Int) -> Int

// Функция с одним параметром String, возвращающая Bool
let validate: (String) -> Bool

// Функция без возвращаемого значения
let print: (String) -> Void
```

## Использование в объявлениях переменных

Типы функций можно использовать для объявления переменных, которые будут хранить ссылки на функции:

```efen
// Объявление переменной с типом функции
let f: (Int, Int) -> Int

// Присваивание лямбда-выражения
f = (a: Int, b: Int) => { a + b }

// Использование
echo f(5, 3)  // Выведет: 8
```

## Опциональные типы функций

Тип функции может быть опциональным:

```efen
let optionalFunc: ((Int) -> Int)?
optionalFunc = null
```

## Функции высшего порядка

Типы функций позволяют создавать функции высшего порядка - функции, 
которые принимают другие функции в качестве параметров или возвращают функции:

```efen
fn apply(x: Int, operation: (Int) -> Int) -> Int {
    return operation(x)
}

fn double(n: Int) -> Int {
    return n * 2
}

echo apply(5, double)  // Выведет: 10
```

## Примеры с замыканиями

```efen
// Функция, возвращающая функцию
fn makeMultiplier(factor: Int) -> (Int) -> Int {
    return (n: Int) => { n * factor }
}

let multiplyBy3 = makeMultiplier(3)
echo multiplyBy3(4)  // Выведет: 12
```

## Алиасы для типов функций

Можно создавать алиасы для сложных типов функций:

```efen
alias BinaryOperation = (Int, Int) -> Int
alias UnaryPredicate = (Int) -> Bool

let operation: BinaryOperation = (a: Int, b: Int) => { a + b }
let isEven: UnaryPredicate = (n: Int) => { n % 2 == 0 }
```

## Грамматика

В грамматике Efen тип функции определяется как:

```antlr
functionType
    : '(' (type (',' type)*)? ')' '->' type
    ;
```

Это правило поддерживает:
- Функции без параметров: `() -> Int`
- Функции с одним параметром: `(Int) -> String`
- Функции с несколькими параметрами: `(Int, String, Bool) -> Void`
