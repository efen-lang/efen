# Циклы

Циклы позволяют многократно выполнять блок кода. `Efen` предоставляет несколько типов циклов,
заимствуя лучшие идеи из Swift: `for-in`, `while`, и `repeat-while`.

## Цикл for-in

Цикл `for-in` используется для итерации по последовательностям: массивам, диапазонам,
строкам и другим коллекциям, которые соответствуют контракту `Iterable`.

### Базовое использование

```efen
let numbers = [1, 2, 3, 4, 5]

for number in numbers {
    print(number)
}
```

### Итерация по диапазону

```efen
// Диапазон от 1 до 5 включительно
for i in 1...5 {
    print(i) // 1, 2, 3, 4, 5
}

// Диапазон от 1 до 5 (5 не включается)
for i in 1..<5 {
    print(i) // 1, 2, 3, 4
}
```

### Итерация по строке

```efen
let text = "Hello"

for char in text {
    print(char) // H, e, l, l, o
}
```

### Итерация по словарю

```efen
let dict = ["name": "Иван", "age": "25", "city": "Москва"]

for (key, value) in dict {
    print("${key}: ${value}")
}
```

### Игнорирование значения с underscore

Если значение итерации не нужно, используйте `_`:

```efen
// Повторить действие 5 раз
for _ in 1...5 {
    print("Привет!")
}
```

### Итерация с индексом

```efen
let fruits = ["Яблоко", "Банан", "Апельсин"]

for (index, fruit) in fruits.enumerated() {
    print("${index}: ${fruit}")
}
// 0: Яблоко
// 1: Банан
// 2: Апельсин
```

### Шаг итерации (stride)

```efen
// От 0 до 10 с шагом 2
for i in stride(from: 0, to: 10, by: 2) {
    print(i) // 0, 2, 4, 6, 8
}

// От 10 до 0 с шагом -2
for i in stride(from: 10, through: 0, by: -2) {
    print(i) // 10, 8, 6, 4, 2, 0
}
```

### Фильтрация с where

Можно добавить условие `where` для фильтрации элементов:

```efen
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

for number in numbers where number % 2 == 0 {
    print(number) // 2, 4, 6, 8, 10
}
```

## Цикл while

Цикл `while` выполняется, пока условие истинно. Проверка условия происходит
перед каждой итерацией.

### Базовое использование

```efen
var count = 0

while count < 5 {
    print(count)
    count += 1
}
// 0, 1, 2, 3, 4
```

### Бесконечный цикл с break

```efen
var count = 0

while true {
    print(count)
    count += 1

    if count >= 5 {
        break
    }
}
```

### Обработка optional значений

```efen
var optionalValue: Int? = 5

while let value = optionalValue, value > 0 {
    print(value)
    optionalValue = value > 1 ? value - 1 : null
}
// 5, 4, 3, 2, 1
```

## Цикл repeat-while

Цикл `repeat-while` выполняет блок кода хотя бы один раз, затем повторяет его,
пока условие истинно. Проверка условия происходит после каждой итерации.

### Базовое использование

```efen
var count = 0

repeat {
    print(count)
    count += 1
} while count < 5
// 0, 1, 2, 3, 4
```

### Гарантированное выполнение

```efen
var value = 10

repeat {
    print("Выполнится хотя бы раз")
    value -= 1
} while value < 5
// Выведет "Выполнится хотя бы раз" один раз, даже если условие ложно
```

## Управление потоком выполнения

### break — выход из цикла

Оператор `break` прерывает выполнение цикла:

```efen
for i in 1...10 {
    if i == 5 {
        break
    }
    print(i)
}
// 1, 2, 3, 4
```

### continue — переход к следующей итерации

Оператор `continue` пропускает текущую итерацию и переходит к следующей:

```efen
for i in 1...5 {
    if i == 3 {
        continue
    }
    print(i)
}
// 1, 2, 4, 5
```

### Метки циклов

Для управления вложенными циклами можно использовать метки:

```efen
outerLoop: for i in 1...3 {
    for j in 1...3 {
        if i == 2 && j == 2 {
            break outerLoop
        }
        print("i: ${i}, j: ${j}")
    }
}
// i: 1, j: 1
// i: 1, j: 2
// i: 1, j: 3
// i: 2, j: 1
```

```efen
outerLoop: for i in 1...3 {
    for j in 1...3 {
        if j == 2 {
            continue outerLoop
        }
        print("i: ${i}, j: ${j}")
    }
}
// i: 1, j: 1
// i: 2, j: 1
// i: 3, j: 1
```

## Вложенные циклы

Циклы могут быть вложенными для обработки многомерных структур:

```efen
let matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

for row in matrix {
    for element in row {
        print(element, terminator: " ")
    }
    print() // Новая строка после каждой строки матрицы
}
// 1 2 3
// 4 5 6
// 7 8 9
```

## Функциональные альтернативы

`Efen` также поддерживает функциональные методы работы с коллекциями:

### map — преобразование элементов

```efen
let numbers = [1, 2, 3, 4, 5]
let doubled = numbers.map { $0 * 2 }
print(doubled) // [2, 4, 6, 8, 10]
```

### filter — фильтрация элементов

```efen
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let evenNumbers = numbers.filter { $0 % 2 == 0 }
print(evenNumbers) // [2, 4, 6, 8, 10]
```

### reduce — свёртка

```efen
let numbers = [1, 2, 3, 4, 5]
let sum = numbers.reduce(0, +)
print(sum) // 15
```

### forEach — выполнение действия для каждого элемента

```efen
let numbers = [1, 2, 3, 4, 5]

numbers.forEach { number in
    print(number)
}
```

**Примечание**: `forEach` не поддерживает `break` и `continue`, используйте обычный `for-in` если нужен контроль потока.

## Ленивые коллекции

Для эффективной работы с большими коллекциями используйте ленивые вычисления:

```efen
let numbers = 1...1000000

// Без ленивых вычислений создаются промежуточные массивы
let result1 = numbers.map { $0 * 2 }.filter { $0 % 3 == 0 }.prefix(5)

// С ленивыми вычислениями вычисляются только нужные элементы
let result2 = numbers.lazy.map { $0 * 2 }.filter { $0 % 3 == 0 }.prefix(5)
```

## Производительность

### Выбор правильного цикла

- **for-in**: для итерации по коллекциям (наиболее читаемый)
- **while**: когда количество итераций заранее неизвестно
- **repeat-while**: когда нужно выполнить код хотя бы один раз

### Оптимизация циклов

```efen
// ❌ Медленно — вызов count на каждой итерации
var i = 0
while i < array.count {
    print(array[i])
    i += 1
}

// ✅ Быстрее — for-in
for element in array {
    print(element)
}

// ✅ Быстрее — кешируем count
let count = array.count
var i = 0
while i < count {
    print(array[i])
    i += 1
}
```

## Безопасность

### Итерация с модификацией

Будьте осторожны при модификации коллекции во время итерации:

```efen
var numbers = [1, 2, 3, 4, 5]

// ❌ Опасно — модификация во время итерации может привести к ошибкам
// for number in numbers {
//     if number % 2 == 0 {
//         numbers.remove(number)
//     }
// }

// ✅ Правильно — создаём новую коллекцию
numbers = numbers.filter { $0 % 2 != 0 }

// ✅ Правильно — итерация в обратном порядке для удаления
for i in (0..<numbers.count).reversed() {
    if numbers[i] % 2 == 0 {
        numbers.remove(at: i)
    }
}
```

## Рекомендации

1. **Используйте for-in** как основной цикл для коллекций
2. **Используйте where** для фильтрации в циклах
3. **Используйте `_`** когда значение итератора не нужно
4. **Предпочитайте функциональные методы** когда они делают код понятнее
5. **Используйте метки** для управления вложенными циклами
6. **Избегайте модификации коллекции** во время итерации
7. **Используйте lazy** для работы с большими коллекциями
8. **Используйте repeat-while** когда код должен выполниться хотя бы раз

## См. также

- [if.md](if.md) — Условные конструкции
- [switch.md](switch.md) — Switch и pattern matching
- [../types/collections.md](../types/collections.md) — Коллекции в Efen
