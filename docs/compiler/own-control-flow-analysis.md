# Анализ ветвлений в системе контроля владения

Рассмотрим случай
```swift
let resource: ResourceType own = acquireResource()
var value = resource

if someCondition {
    value = acquireResourceB()
    
    if anotherCondition {
        value = acquireResourceB1()
    }
    
} else {
    value = acquireResourceC()
}

myFunction(value)
```

Переменная `value` владеет разными слотами памяти в зависимости от пути выполнения программы.
Как компилятор может убедиться, что в конце функции `myFunction` переменная `value` действительно владеет ресурсом?

Для этого компилятор запоминает, какими слотами владеет каждая переменная.
В точке вызова функции `myFunction`, компилятор проверяет
условия владения для каждого слота, которым может владеть `value`.

## Слоты vs конкретная память

Важно понимать: **слот ≠ конкретная ячейка памяти**.

Слот - это абстрактное место хранения с правами владения.
При присваивании в цикле переменная указывает на один слот, но содержимое слота меняется:

```swift
var value = initial

while condition {
    value = newResource()  // слот value меняет содержимое
}

// value указывает на один слот, но содержимое менялось N раз
```

Множество слотов для переменной возникает только при ветвлениях:

```swift
var value = slot_initial

if cond {
    value = resourceA  // создаёт slot_A
} else {
    value = resourceB  // создаёт slot_B
}

// value → {slot_initial, slot_A, slot_B}
```

## Уничтожение одного из слотов переменной

Критичная ситуация возникает, когда один из возможных слотов переменной уничтожается:

```swift
var file = slot1

if cond {
    file = slot2
}

// file → {slot1, slot2}

if otherCond {
    consume(file)  // Уничтожает один из слотов
}

// Состояние слотов:
// Path A (cond=true, otherCond=true): slot2 consumed
// Path B (cond=false, otherCond=true): slot1 consumed
// Path C (otherCond=false): оба alive

file.close()  // ❌ ОШИБКА: хотя бы один слот может быть consumed
```

**Правило:** Если хотя бы ОДИН возможный слот переменной имеет состояние `consumed`,
переменная становится недоступной для использования.

Компилятор отслеживает состояние каждого слота:

```
slot1: {consumed, alive} → помечается consumed
slot2: {consumed, alive} → помечается consumed

file → {slot1: consumed, slot2: consumed}
```

После этого любое использование `file` вызывает ошибку компиляции.

## Слоты с разными правами

Переменной могут присваиваться слоты с разными правами владения:

```swift
var resource = slot_own  // own

if cond {
    let temp = acquireResource() own
    resource = temp read  // понижаем до read
}

// resource → {slot_own: own, slot_temp: read}

consume(resource)  // Требует own для ВСЕХ слотов
```

**Правило:** При проверке прав для переменной компилятор проверяет,
что ВСЕ возможные слоты имеют требуемые права.

```
consume() требует own
slot_own: own ✓
slot_temp: read ❌

ОШИБКА: не все слоты имеют право own
```

Для безопасного использования нужно, чтобы все пути присваивали слоты с одинаковыми правами:

```swift
var resource: Resource own

if cond {
    resource = acquireA() own
} else {
    resource = acquireB() own
}

// resource → {slot_A: own, slot_B: own}

consume(resource)  // ✓ OK: все слоты имеют own
```

При merge прав компилятор вычисляет **минимальное общее право**:

```
merge(own, own) = own
merge(own, read) = read
merge(read, write) = read
merge(own, consumed) = consumed
```

Это гарантирует безопасность: переменная может использоваться только с правами,
которые точно есть у всех возможных слотов.