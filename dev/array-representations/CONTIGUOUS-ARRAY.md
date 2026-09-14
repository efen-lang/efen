# Непрерывный `Array` фиксированной длины

Статус: теоретический пример для
[модели компоновки и представления](../PAGED-FILE-LAYOUT.md). Синтаксис
дескрипторов памяти и их операции ещё не реализованы компилятором.

## Смысл представления

`Array<Target, Contiguous>` хранит элементы в одной непрерывной области.
Логические позиции `0 ..< count` соответствуют соседним `Item` внутри этой
области. Длина задаётся при создании и больше не меняется.

`Target` — тип элемента. Конкретный `Array<Target, Contiguous>` неявно входит
в аспект как `Self`, а текущий массив внутри операций называется `self`.

## Layout

```efen
aspect Contiguous<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value in self.items
        }

        struct Item {
            Target
        }

        struct Self {
            var items: own Items.Area {
                value.initializedCount == Items.count
                value.initializedCount == value.capacity
            }
        }
    }

    implementation {
        // Операции приведены ниже.
    }
}
```

`set Items: Item` объявляет элементы массива. `Items.Area` — принадлежащий
этому дескриптору handle одной непрерывной области из `Item`. Условие
`value in self.items` означает, что каждый живой `Items.Item` находится в
области текущего массива.

`Item` физически встраивает `Target`:

```efen
struct Item {
    Target
}
```

Запись `var value: Target` не подошла бы: обычное поле может получить косвенную
representation. Голое `Target` требует разместить данные элемента внутри
`Item`. Выражение `item.Target` проецирует встроенное место целиком.

Фиксированный массив полностью инициализирует выделенную область, поэтому
`initializedCount == capacity`. Логическая мощность `Items.count` совпадает с
числом инициализированных мест.

## Операции области

Эскиз использует следующий интерфейс дескриптора памяти:

| Операция | Смысл |
|---|---|
| `Items.allocateArea(capacity)` | Подготовить непрерывную область для `capacity` элементов `Item` |
| `area.initializeNext(item)` | Перенести следующий `Item` в свободное место |
| `area.itemAt(index)` | Получить `Items.Item` и проверить границу инициализированного префикса |
| `Items.free(area)` | Освободить принадлежащую `Items` область |

`Items.allocateArea` может завершиться ошибкой. До публикации `self.items`
подготовленная область принадлежит локальной переменной и очищает только уже
инициализированные элементы.

## Полный эскиз

```efen
aspect Contiguous<Target> conforms Representation<Target> {
    layout {
        set Items: Item {
            value in self.items
        }

        struct Item {
            Target
        }

        struct Self {
            var items: own Items.Area {
                value.initializedCount == Items.count
                value.initializedCount == value.capacity
            }
        }
    }

    implementation {
        @constructor
        public fn init(
            count: Size,
            make: (Size) -> Target
        ) -> Self {
            var pending = Items.allocateArea(capacity: count)

            for index in 0..<count {
                let value = make(index)
                pending.initializeNext(Item(take value))
            }

            self.items = take pending
            return self
        }

        public fn count -> Size {
            return self.items.initializedCount
        }

        fn itemAt(index: Size) -> Items.Item {
            return self.items.itemAt(index)
        }

        public fn read(index: Size) -> Target
            where Target: Copyable
        {
            return itemAt(index).Target
        }

        public fn replace(
            index: Size,
            value: own Target
        ) -> Target {
            let item = itemAt(index)
            let previous = take item.Target
            item.Target = take value
            return take previous
        }

        public fn borrowRead(index: Size) -> &read[self] Target {
            return &read[self] itemAt(index).Target
        }

        public fn borrowWrite(index: Size) -> &[self] Target {
            return &[self] itemAt(index).Target
        }
    }
}
```

При создании компилятор сначала знает незавершённый `Self`. После успешной
инициализации всех мест `pending` переносится в поле `self.items`, и условия
layout закрываются. Если `make(index)` бросает исключение, незавершённый
`Self` наружу не выходит.

При уничтожении `Self` владеющий `Items.Area` уничтожает каждый
инициализированный `Target`, а затем передаётся `Items.free`. Точный lowering
этого автоматического уничтожения относится к протоколу дескриптора.

Прямой `replace` требует, чтобы перенос `Target` в уже подготовленное место не
бросал исключений, не приостанавливался и не вызывал наблюдающий код. Иначе
между `take item.Target` и присваиванием нового значения мог бы появиться
наблюдаемый неинициализированный элемент.

## Стоимость

`count`, индексирование, чтение, замена и получение ссылки выполняются за
`O(1)`. Обход всех элементов выполняется за `O(count)`. Представление не
поддерживает изменение длины; для этого предназначен
[динамический непрерывный массив](DYNAMIC-ARRAY.md).

## Граница предложения

`Items.Area`, `initializedCount`, `capacity`, `initializeNext` и `itemAt`
являются кандидатами общего интерфейса дескрипторов памяти. Они не являются
специальными операциями `Array` и не доказывают корректность сами по себе.
