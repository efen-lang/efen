# Layout: формы типов

Справочник правил `layout`: таблица из раздела 2.1 и абзац из раздела 1. Все статьи: [Layout](README.md).

Назад: [2. Объявление](declaration.md) · Дальше: [3. Владение](owners.md)

## Содержание

- [Таблица форм](#таблица-форм)
- [Права с источником](#права-с-источником)
- [Где определена каждая форма](#где-определена-каждая-форма)

## Таблица форм

<a id="формы-типов"></a>

Формы типов. Множество и область дают имена типам. Таблица перечисляет все формы; `Nodes` в ней множество
(`set Nodes: Node`), `Items` область (`area Items: T`), `Block.data` область, объявленная полем `data` структуры
`Block`.

| Запись | Что называет | Пример |
|---|---|---|
| `Nodes.Item` | невладеющий указатель на элемент множества `Nodes`; читает (раздел 4.1) | `var to: Nodes.Item` |
| `Nodes.Item?` | такой указатель или `null` | `var prev: Nodes.Item? = null` |
| `own Nodes.Item` | исключительное владение элементом (раздел 3.1) | `fn newNode(value: Int) -> own Nodes.Item` |
| `anchor Nodes.Item` | якорь: владение элементом, на который указывают хранимые указатели (раздел 3.1) | `var head: anchor Nodes.Item? = null` |
| `edit Nodes.Item`, `mut Nodes.Item` | указатель-параметр с правом записи, которое на время вызова выдаёт вызывающий (раздел 8.2) | `fn setPrev(a: Nodes.Item, b: edit Nodes.Item)` |
| `read<list> Nodes.Item` | указатель на элемент структуры `list`; так же пишутся `edit<list>` и `mut<list>` (раздел 4.1, правило 4) | `fn first(list: read List) -> read<list> Nodes.Item?` |
| `Items.Item` | слот области `Items`; у `area Items: T` слот хранит значение `T` | `var key: Items.Item` |
| `Items.Area` | область `Items` целиком; хранится под `own` (раздел 3.4) | `var items: own Items.Area? = null` |
| `Block.data.Item` | слот области-поля `data`, названный через структуру; под `own` это выданный слот или диапазон (раздел 3.5) | `fn acquire(pool: mut Pool) -> own Block.data.Item?` |
| `block.data.Item` | тот же слот, названный через значение-родителя `block` | `fn releaseSlot(block: mut Block, slot: own block.data.Item)` |
| `slots.Item` | слот области-поля в инвариантах самой структуры | `sizeOf(slots.Item) == SIZES[sizeClass]` |
| `Nodes<Int>.Item` | элемент множества `layout` с параметрами, названный вне этого `layout` (раздел 2.4) | `fn newNode<T>(value: own T) -> anchor Nodes<T>.Item` |
| `Lists<Entry>.Nodes.Item` | элемент множества `open layout` с именем `Lists` (раздел 10.1) | `var node: Lists<Entry>.Nodes.Item? = null` |
| `Vector<own Nodes.Item>`, `Vector<read<g> Nodes.Item>` | форма в аргументе типа: контейнер владеет элементами (раздел 3.4) или хранит заимствование (раздел 4.5) | `var pending: Vector<own Nodes.Item>` |

## Права с источником

Права в сигнатурах функций `layout` пишутся с источником: `from: read<g> Nodes.Item` (указатель на элемент структуры
`g`), `-> edit<list> Items.Item?` (результат с правом `edit` на элемент из `list`), `mut<self.cache, edit self.items> fn`
(метод меняет `cache` и правит поле `items`). Все одиннадцать мест, где пишется запись `право<путь>`, с примером к
каждому, перечисляет таблица в статье [об областях доступа](../../types/access-regions.md#источник-право-и-время-действия).

## Где определена каждая форма

| Форма | Статья |
|---|---|
| `Nodes.Item`, `Items.Item`, `Items.Area`, `slots.Item`: имена, которые дают множество и область | [Объявление](declaration.md), раздел 2.1 |
| `Nodes<Int>.Item`: множество `layout` с параметрами | [Объявление](declaration.md), раздел 2.4 |
| `own Nodes.Item`, `anchor Nodes.Item` | [Владение](owners.md), раздел 3.1 |
| `own Items.Area`, `Vector<own Nodes.Item>` | [Владение](owners.md), раздел 3.4 |
| `own Block.data.Item`, `own block.data.Item`: выданный слот | [Владение](owners.md), раздел 3.5 |
| `Nodes.Item`, `Nodes.Item?`, `read<list> Nodes.Item` | [Невладеющие указатели](pointers.md), раздел 4.1 |
| `Vector<read<g> Nodes.Item>` | [Невладеющие указатели](pointers.md), раздел 4.5 |
| `edit Nodes.Item`, `mut Nodes.Item` | [Функции](functions.md), раздел 8.2 |
| `Lists<Entry>.Nodes.Item` | [Расширение](extension.md), раздел 10.1 |

---

[Документация](../../README.md) · [Контракты](../../contracts.md) · [Runtime языка Efen](../../runtime/README.md) · [Память](../README.md) · [Layout](README.md)
