# Синтаксис вызова функций

В `Efen` существует несколько способов вызова функций, каждый из которых подходит для разных сценариев использования.

## Обычный вызов (со скобками)

Стандартный способ вызова функций - с использованием круглых скобок:

```efen
// Без аргументов
doSomething()

// С одним аргументом
println("Hello")

// С несколькими аргументами
add(5, 3)
greet("John", "Doe")

// Вложенные вызовы
calculate(multiply(2, 3), add(4, 5))
```

**Использование:** Универсальный способ, работает везде - в выражениях, присваиваниях, условиях и т.д.

## Application Operator `<|`

Специальный унарный оператор для применения функции к одному аргументу:

```efen
// Простые вызовы
println <| "Hello, World!"
log <| "Debug message"
debug <| 42

// С выражениями в качестве аргумента
println <| "Result: " + result
log <| x + y * 2
assert <| count > 0

// Вложенные применения (право-ассоциативен)
save <| transform <| validate <| data
// Эквивалентно: save(transform(validate(data)))

// В выражениях
let result = process <| validate <| input
array[calculate <| index]
```

### Особенности `<|` оператора

**Унарный оператор:**
- ✅ Принимает только ОДНО выражение справа
- ✅ Работает везде - в statements и в expressions
- ✅ Право-ассоциативный: `f <| g <| x` = `f(g(x))`
- ✅ Самый низкий приоритет (ниже всех операторов)

**Ограничения:**
- ❌ НЕ поддерживает несколько аргументов
- ❌ Запятая после `<|` - синтаксическая ошибка

```efen
// ❌ ОШИБКА - несколько аргументов
printf <| "format", arg1, arg2  // Синтаксическая ошибка!

// ✅ ПРАВИЛЬНО - используйте скобки для множественных аргументов
printf("format", arg1, arg2)
```

### Приоритет операций

`<|` имеет самый низкий приоритет, поэтому захватывает всё выражение справа:

```efen
// Арифметика вычисляется первой
print <| 2 + 3           // = print(2 + 3) = print(5)
save <| x * 2 + y        // = save((x * 2) + y)

// Вызовы функций тоже вычисляются первой
log <| getValue()        // = log(getValue())
process <| data.map(fn)  // = process(data.map(fn))
```

### Избежание вложенных скобок

Главное преимущество `<|` - избежание глубокой вложенности скобок:

```efen
// Без <| - множество скобок
print(json_encode(array_filter(transform(data))))

// С <| - читается линейно
print <| json_encode <| array_filter <| transform <| data
```

### Сравнение: `<|` vs скобки

| Критерий | `func <| arg` | `func(arg)` |
|----------|---------------|-------------|
| Количество аргументов | Только один | Любое количество |
| Где работает | Везде | Везде |
| Вложенность | Легко читается | Нужны скобки |
| Типичное использование | Цепочки трансформаций | Обычные вызовы |

## Вызов с именованными параметрами

Явное указание имён параметров при вызове:

```efen
fn greet(firstName: String, lastName: String) {
    println("Hello, $firstName $lastName!")
}

// Вызов с именованными параметрами
greet(firstName: "John", lastName: "Doe")

// Можно менять порядок
greet(lastName: "Smith", firstName: "Jane")
```

**Преимущества:**
- Улучшает читаемость кода
- Делает вызов самодокументируемым
- Позволяет изменять порядок аргументов

## Вызов с дженериками

Для дженерик-функций можно явно указывать типы:

```efen
fn identity<T>(value: T) -> T {
    return value
}

// Явное указание типа
let num = identity<Int>(42)
let str = identity<String>("hello")

// Вывод типа компилятором
let num = identity(42)      // T = Int
let str = identity("hello") // T = String
```

## Вызов с замыканиями

Функции высшего порядка могут принимать замыкания:

```efen
// Замыкание как аргумент
numbers.map((x) => x * 2)

// Многострочное замыкание
numbers.filter((x) => {
    return x > 10 && x < 100
})

// С application operator
numbers.map <| (x) => x * 2
transform <| (data) => {
    return process(data)
}
```

## Вызов методов

Вызов методов объектов через точечную нотацию:

```efen
// Обычный вызов метода
user.getName()
list.add(item)

// Цепочка вызовов
user.getProfile().getSettings().update()

// Опциональный вызов
user?.getName()
user?.profile?.getEmail()

// С application operator
process <| user.getName()
save <| list.first()
```

## Сравнение синтаксисов

| Синтаксис | Где использовать | Пример |
|-----------|------------------|--------|
| `func()` | Везде (универсальный) | `getValue()` |
| `func <| arg` | Унарные функции, цепочки | `print <| "Hello"` |
| `func(a: val)` | Именованные параметры | `greet(name: "John")` |
| `func<T>()` | Дженерики | `identity<Int>(42)` |
| `obj.method()` | Методы объектов | `user.getName()` |
| `obj?.method()` | Опциональные методы | `user?.getEmail()` |

## Рекомендации

### Используйте `<|` для:

1. **Цепочек унарных функций**
   ```efen
   result <| validate <| parse <| input
   save <| encode <| compress <| data
   ```

2. **Избежания скобочного ада**
   ```efen
   // Плохо
   print(format(prepare(getData())))

   // Хорошо
   print <| format <| prepare <| getData()
   ```

3. **Функциональных пайплайнов**
   ```efen
   data
       |> parse
       |> validate
       |> transform
       |> save <| compress  // можно комбинировать с |>
   ```

### Используйте обычный вызов для:

1. **Функций с несколькими аргументами**
   ```efen
   add(5, 3)
   greet("John", "Doe")
   printf("User: %s", name)
   ```

2. **Простых вызовов**
   ```efen
   getValue()
   process(data)
   ```

3. **Когда не нужна цепочка**
   ```efen
   if isValid(input) { }
   let x = calculate(a, b)
   ```

## Примеры из реальной практики

### Функциональные трансформации

```efen
fn processUsers(users: [User]) {
    return users
        .filter((u) => u.isActive)
        .map((u) => u.getName())
        .map <| capitalize
        .sort()
}
```

### Работа с данными

```efen
fn saveData(data: Data) {
    validate <| data

    let compressed = compress <| serialize <| data
    let encrypted = encrypt <| compressed

    write <| encrypted
    log <| "Data saved successfully"
}
```

### Обработка ошибок

```efen
fn processRequest(request: Request) -> Result {
    let data = parse <| request.body
    let validated = validate <| data

    if !validated {
        return error <| "Validation failed"
    }

    return process <| validated
}
```

### Логирование и отладка

```efen
fn debugPipeline(input: String) {
    log <| "Input: " + input

    let result = input
        |> parse
        |> validate
        |> transform

    debug <| result
    return result
}
```

## Приоритет и ассоциативность

### Application operator `<|`

- **Приоритет:** Самый низкий (ниже присваивания)
- **Ассоциативность:** Право-ассоциативный

```efen
// Право-ассоциативность
f <| g <| h <| x
// Парсится как: f <| (g <| (h <| x))
// Эквивалентно: f(g(h(x)))

// Низкий приоритет
print <| x + y * 2
// Парсится как: print <| ((x + (y * 2)))
// Эквивалентно: print((x + (y * 2)))
```

### Комбинирование с другими операторами

```efen
// С присваиванием
let result = transform <| data
let value = f <| g <| x

// С условиями
if isValid <| input {
    process <| input
}

// С return
return format <| calculate <| value

// В коллекциях
[1, 2, 3].map <| double
array[process <| index]
```
