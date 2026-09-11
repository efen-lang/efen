# Расширение generics Efen: решения и оставшиеся вопросы

Дата решения: 2026-09-11.

Нормативное описание находится в [generics](docs/efen/generics.md),
[типах](docs/efen/types/type.md), [функциях](docs/efen/functions.md) и
[`throws`](docs/efen/throws.md). Этот файл сохраняет мотивацию, границы решения
и вопросы реализации.

## Принятые решения

### Конструкторы типов

Generic-параметр может принимать семейство типов:

```efen
param Result<T>: Type
```

`Future` можно передать как аргумент и применить внутри generic как `Future<T>`.
Анонимное семейство записывается type-lambda:

```efen
type<T> => Future<Result<T, Error>>
```

### Требования через `required`

Новый вид «контракта конструктора» не вводится. Требования помещаются в блок
параметра:

```efen
param F<T>: Type {
    required method map<U>(transform: (T) -> U) -> F<U>
}
```

Требование удовлетворяет физический метод либо метод стратегии, участвующей в
обычном разрешении. Несколько подходящих стратегий — ошибка компиляции; автоматической
специализации по более узкому ограничению нет.

### Ограничения

Локальное условие пишется у параметра:

```efen
param Size: Int { Size > 0 }
```

Отношение нескольких параметров пишется через `where`:

```efen
where A.Item == B.Item
```

Обе формы запрещают неподходящую инстанциацию. `#if` условно формирует состав
уже законной инстанциации.

### Полиморфные функции

Generic-функция может быть значением:

```efen
fn<T>(T) -> T
```

Один объект такой функции обязан работать для каждого допустимого `T`.

### Безымянный generic-параметр

Contract в позиции параметра функции сокращает отдельный generic-параметр:

```efen
fn printAll(items: Iterable<Item: String>)
```

Несколько таких параметров вводят независимые конкретные типы; общий тип нужно
назвать явно.

### Variadic generics

```efen
param ...Elements: Type
Tuple<...Elements>
```

Внутри `Elements` имеет тип `[Type]`. Префикс `...` в объявлении собирает
аргументы, а в применении раскрывает их. Ограничение:

```efen
param ...Errors: Type
where ...Errors: Exception
```

проверяет каждый аргумент без дополнительного слова `each`.

Pack раскрывается в tuple, union и другом списке типов:

```efen
alias Result<Value, ...Errors> = Value | ...Errors
```

Compile-time `[Type]` можно преобразовать type-lambda:

```efen
Elements.map(type<T> => T?)
```

Runtime pack связывается с type pack:

```efen
fn tuple<...Types>(...values: Types) -> Tuple<...Types>
```

### Generic `throws`

```efen
fn map<T, U, ...Errors>(
    items: [T],
    transform: (T) -> U throws ...Errors
) -> [U] throws ...Errors
    where ...Errors: Exception
```

Generic сохраняет точный набор исключений callback.

### Match над типами

```efen
alias Element<T> = match T {
    Array<let item>: item
    _: T
}
```

Связанная переменная начинается со строчной буквы. Generic-образец
сопоставляется с самим применённым типом и с его наследником по номинальному
generic-head, без вариантности и coercion, если найдено ровно одно применение
базового generic. Несколько разных применений дают ошибку неоднозначности.

### Opaque-типы

Модификатор ставится перед `type`:

```efen
public opaque(private) type Buffer<T>:
    Iterable<Item: T>
= Array<T>
```

Видимость имени и область раскрытия независимы. `opaque(private)` раскрывает
внутренний тип объявившему модулю и является значением по умолчанию;
`opaque(internal)` раскрывает его всему пакету. За пределами пакета внутренний
тип не раскрывается.

Opaque-тип не обещает бинарной совместимости. Замена внутреннего типа требует
перекомпиляции зависимых продуктов; обязательной упаковки нет.

Функция может объявить безымянный opaque-результат:

```efen
fn tokens(text: String) -> opaque Iterator<Item: Token>
```

Несколько конкретных типов результата разрешены, если все соответствуют
контракту, их связанные параметры совпадают и все требуемые операции можно
синтезировать для union. Компилятор создаёт скрытый union и dispatch по его
runtime-тегу. Для общей идентичности нескольких сигнатур объявляется именованный
`opaque type`.

## Что уже было в Efen

Стратегии уже являются compile-time значениями и могут передаваться generic-
параметрами. Идея `SortedSet<String, CaseInsensitive>` не является новым
расширением. Существующие правила разрешения стратегий сохраняются:
неоднозначность является ошибкой.

Параметры contract уже связывают такие типы, как `Iterable.Item` и
`Iterable.Cursor`. Новое описание закрепляет проекцию выбранного параметра через
`T.Item` и её неоднозначность при нескольких соответствиях.

## Оставшиеся вопросы реализации

Языковая семантика выше принята. Для Amber и frontend остаются инженерные
решения:

1. Представление kind/арности конструктора типов и type-lambda в HIR.
2. Представление type pack, value pack и pack expansion без потери соответствия
   позиций.
3. Канонический ключ type-level `match`, включая найденный путь к generic-базе.
4. Представление полиморфного функционального типа и generic `throws` pack.
5. Идентичность анонимного opaque-результата и синтезированного union.
6. Инвалидация зависимых продуктов при изменении внутреннего opaque-типа.

Эти пункты не открывают заново поверхностный синтаксис и семантику языка. Они
должны быть закрыты при проектировании схемы HIR и алгоритма понижения.

## Отложенная проверка Expression Problem

Object Algebras остаются полезным тестом выразительности, а не отдельной
конструкцией языка. После реализации generics следует проверить четыре модуля:
базовые `literal`/`add`, независимую операцию печати, независимый `multiply` и
интеграционный модуль. Проверка должна доказать статическую полноту, композицию
расширений и фактическое повторное использование скомпилированного кода.

Источники идей:

- [Scala using clauses](https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html)
- [Scala type lambdas](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- [Rust associated types](https://doc.rust-lang.org/reference/items/associated-items.html#associated-types)
- [Swift opaque types](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/opaquetypes/)
- [Object Algebras](https://www.cs.utexas.edu/~wcook/Drafts/2012/ecoop2012.pdf)
