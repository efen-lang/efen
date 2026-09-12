# API времени компиляции (Compile-Time API)

[Документация](../index.md) · [Словарь](../glossary.md) · [Метафункции](metafunctions.md) · [Amber HIR](https://github.com/limelight-lang/amber/blob/main/design/hir/README.md)

API времени компиляции предоставляет программисту полный доступ к структуре компилируемого кода во время компиляции.
`API` может быть подключен как модуль `compiler`.

## Обход HIR и расширения компилятора

До понижения Amber предоставляет расширениям schema-driven обход выбранного
согласованного HIR-view. Обход охватывает объявления, выражения, типы,
операнды и достижимые боковые таблицы, а не только иерархию классов и других
объявлений. Расширение может читать происхождение порождённых узлов и, в рамках
прав текущей стадии, строить или заменять HIR.

Порождённый код хранится в неизменяемых виртуальных исходных фрагментах с
точными spans. При вложенной генерации сохраняется полная цепочка от реального
места применения через каждый виртуальный фрагмент. Поэтому диагностика может
показать точное место внутри сгенерированного HIR и все аспекты, обработчики и
входные узлы, которые его породили.

Amber можно запускать без codegen. Запрос может завершиться после построения,
преобразования, анализа или проверки HIR. Каноническое текстовое изображение
выбранного HIR-view является запланированным самостоятельным выходом и не
требует lowering или backend.

Конфигурация Amber может отключать необязательные оптимизационные проходы и
подключаемые модули компилятора. Модуль объявляет свои capabilities, зависимости
и точки подключения. Если программе или выбранному output нужна возможность,
для которой не осталось активного производителя, запуск завершается ошибкой
конфигурации. Активный набор и параметры входят в идентичность сборки.

Новый вид HIR является обычной структурой Efen со встроенной базовой
HIR-структурой. Специального синтаксиса `hir node` и функции
`compiler.hir.defineNode()` нет. Декларация структуры задаёт устойчивую
идентичность и поля, а типы полей задают роли ссылок. При первом употреблении
builder интернирует декларацию в append-only каталог конкретного HIR storage.
Универсальные walker и текстовый printer используют это описание. Для анализа
или codegen метакод либо подключённый модуль также предоставляет требуемую
проверку, преобразование или lowering.

Core HIR описывается теми же структурами Efen. C++ records и accessors Amber
генерируются из них для bootstrap и не образуют отдельную нормативную схему.

Схематический модуль расширения выглядит как обычный Efen-код:

```efen
use amber

struct SqlQuery {
    BaseNode

    var connection: Symbol
    var queryText: String
    var parameters: [HirNodeId]
    var resultType: Type
}
```

`use amber` подключает базовые HIR-структуры и их compile-time API. Загрузка
`SqlQuery` автоматически делает её декларацию доступной builder-у как новый
вид; отдельного ручного числового ID или вызова регистрации в исходнике нет.
Поля используют обычные типы Efen. Representation базовых HIR-структур решает,
как `String`, `[HirNodeId]`, `Type` и другие значения кодируются индексами,
диапазонами и side tables.

## Базовые типы

### compiler::CompileContext

Контекст времени компиляции - корневой объект для доступа к API компилятора.

```efen
interface CompileContext {
    // Получение модуля
    fn getModule() -> Module;

    // Поиск типа по имени
    fn findType(name: String) -> Type?;

    // Поиск класса по имени
    fn findClass(name: String) -> Class?;

    // Поиск интерфейса по имени
    fn findInterface(name: String) -> Interface?;

    // Поиск аспекта по имени
    fn findAspect(name: String) -> Aspect?;
}
```

### Module

Модуль - корневой элемент иерархии компилируемого кода.

```efen
interface Module {
    // Имя модуля
    fn getName() -> String;

    // Получение всех классов модуля
    fn getClasses() -> [String: Class];

    // Получение всех интерфейсов модуля
    fn getInterfaces() -> [String: Interface];

    // Получение всех структур модуля
    fn getStructs() -> [String: Struct];

    // Получение всех аспектов модуля
    fn getAspects() -> [String: Aspect];

    // Получение всех стратегий модуля
    fn getStrategies() -> [String: Strategy];
}
```

## API для работы с классами

### Class

Объект, представляющий информацию о классе во время компиляции.

```efen
contract Class {
    // ===== Базовая информация =====

    // Получение имени класса
    fn getName() -> String;

    // Получение полного имени класса (с namespace)
    fn getFullName() -> String;

    // Получение модуля, в котором определён класс
    fn getModule() -> Module;

    // Получение исходного расположения определения класса
    fn getSourceLocation() -> SourceLocation;

    // ===== Иерархия наследования =====

    // Получение базового класса (если есть)
    fn getBaseClass() -> Class?;

    // Проверка наследования от другого класса
    fn inheritsFrom(other: Class) -> Bool;

    // Получение всех базовых классов в иерархии
    fn getAllBaseClasses() -> Class[];

    // ===== Интерфейсы и контракты =====

    // Получение списка реализуемых интерфейсов
    fn getInterfaces() -> Interface[];

    // Получение списка контрактов
    fn getContracts() -> Contract[];

    // Проверка реализации интерфейса
    fn implements(interface: Interface) -> Bool;

    // Проверка соблюдения контракта
    fn satisfies(contract: Contract) -> Bool;

    // ===== Аспекты =====

    // Получение списка применённых аспектов
    fn getAspects() -> Aspect[];

    // Проверка применения аспекта
    fn hasAspect(aspect: Aspect) -> Bool;

    // Получение аспекта по имени
    fn getAspect(name: String) -> Aspect?;

    // ===== Методы =====

    // Получение всех методов класса (включая унаследованные)
    fn getMethods(inherited: Bool = true) -> Method[];

    // Получение собственных методов класса
    fn getOwnMethods() -> Method[];

    // Поиск метода по имени
    fn findMethod(name: String) -> Method?;

    // Поиск метода по сигнатуре
    fn findMethod(name: String, params: Type[]) -> Method?;

    // Проверка наличия метода
    fn hasMethod(name: String) -> Bool;

    // ===== Свойства =====

    // Получение всех свойств класса (включая унаследованные)
    fn getProperties(inherited: Bool = true) -> Property[];

    // Получение собственных свойств класса
    fn getOwnProperties() -> Property[];

    // Поиск свойства по имени
    fn findProperty(name: String) -> Property?;

    // Проверка наличия свойства
    fn hasProperty(name: String) -> Bool;

    // ===== Модификаторы =====

    // Проверка модификаторов
    fn isFinal() -> Bool;
    fn isOpen() -> Bool;
    fn isPublic() -> Bool;
    fn isPrivate() -> Bool;
    fn isProtected() -> Bool;
    fn isFamily() -> Bool;

    // ===== Метаданные и атрибуты =====

    // Получение метаданных класса
    fn getMetadata() -> Metadata;

    // Получение атрибутов класса
    fn getAttributes() -> Attribute[];

    // Поиск атрибута по типу
    fn findAttribute<T>(type: Type<T>) -> T?;

    // Проверка наличия атрибута
    fn hasAttribute(type: Type) -> Bool;

    // ===== Модификация (Builder Pattern) =====

    // Получение builder'а для модификации класса
    fn toBuilder() -> ClassBuilder;
}
```

`Class` по умолчанию представляет текущий рабочий вид объявления. После чтения
исходника компилятор отдельно сохраняет исходный вид С0; он запрашивается явно,
остаётся неизменяемым и не включает последующие преобразования аспектов.
Конкретное имя операции чтения С0 ещё не закреплено API.

Чтение С0 не обещает окончательного разрешения типов и членов. Компилятор не
подменяет требуемый завершённый вид исходным автоматически: допустимость
явного чтения С0 для разрыва compile-time зависимости остаётся частью контракта
конкретной операции.

`toBuilder()` не предоставляет общего права менять импортированный класс.
Объявления зависимости доступны только для чтения, пока их владелец явно не
разрешил внешнее преобразование и текущая сборка не применила его через
`provide`. Такое изменение создаёт рабочий вид текущей сборки и не переписывает
продукт зависимости. Точная форма разрешения ещё проектируется.

### ClassBuilder

Builder для модификации класса во время компиляции.

Методы builder описывают доступные операции, а не выдают разрешение на них.
Аспект без отдельного контракта может физически создать только приватный метод.
Создание неприватного метода и другие изменения существующей поверхности класса
требуют явного разрешающего контракта. Дополнительное публичное поведение
стратегии не становится физическим методом класса.

Каждая мутация проходит через режимы доступа и ограничения соответствующих
HIR-узлов. Компилятор сохраняет происхождение операции; запрет нельзя обойти
заменой родителя защищённого узла.

```efen
contract ClassBuilder {
    // ===== Добавление методов =====

    // Добавить метод к классу
    fn addMethod(method: MethodBuilder) -> ClassBuilder;

    // Добавить метод с кодом
    fn addMethod(name: String,
                 params: Parameter[],
                 returnType: Type,
                 body: CodeBlock) -> ClassBuilder;

    // ===== Добавление свойств =====

    // Добавить свойство к классу
    fn addProperty(property: PropertyBuilder) -> ClassBuilder;

    // Добавить простое свойство
    fn addProperty(name: String,
                   type: Type,
                   defaultValue: Expression? = null) -> ClassBuilder;

    // ===== Добавление интерфейсов =====

    // Добавить реализацию интерфейса
    fn addInterface(interface: Interface) -> ClassBuilder;

    // ===== Добавление аспектов =====

    // Применить аспект к классу
    fn addAspect(aspect: Aspect) -> ClassBuilder;

    // Применить аспект с параметрами
    fn addAspect(aspect: Aspect, params: Map<String, Value>) -> ClassBuilder;

    // ===== Модификация существующих элементов =====

    // Модифицировать метод
    fn modifyMethod(name: String,
                    modifier: (MethodBuilder) -> MethodBuilder) -> ClassBuilder;

    // Модифицировать свойство
    fn modifyProperty(name: String,
                      modifier: (PropertyBuilder) -> PropertyBuilder) -> ClassBuilder;

    // ===== Изменение модификаторов =====

    fn setFinal(value: Bool) -> ClassBuilder;
    fn setOpen(value: Bool) -> ClassBuilder;
    fn setVisibility(visibility: Visibility) -> ClassBuilder;

    // ===== Метаданные и атрибуты =====

    // Добавить атрибут к классу
    fn addAttribute(attribute: Attribute) -> ClassBuilder;

    // Добавить метаданные
    fn addMetadata(key: String, value: MetadataValue) -> ClassBuilder;

    // ===== Применение изменений =====

    // Применить все изменения
    fn build() -> Class;

    // Проверить корректность перед применением
    fn validate() -> ValidationResult;
}
```

При построении класса `addAspect` может расширить исполняемый состав текущего
`ClassDefinitionPlan` только во время регистрационной части, до
`primaryClassDefinition`. Правило первой версии отклоняет позднее подключение
аспекта, которому нужны новые шаги или обработчики плана; откат и повторное
исполнение уже пройденных шагов не выполняются.

Полная модель приведена в
[построении класса аспектами](../aspects/compile-time/class.md).

## Дополнительные типы для API классов

### Method

```efen
interface Method {
    fn getName() -> String;
    fn getParameters() -> Parameter[];
    fn getReturnType() -> Type;
    fn isPublic() -> Bool;
    fn isPrivate() -> Bool;
    fn isProtected() -> Bool;
    fn isStatic() -> Bool;
    fn isFinal() -> Bool;
    fn isOpen() -> Bool;
    fn isFamily() -> Bool;
    fn getAttributes() -> Attribute[];
    fn getMetadata() -> Metadata;
    fn getSourceLocation() -> SourceLocation;
    fn toBuilder() -> MethodBuilder;
}
```

### Property

```efen
interface Property {
    fn getName() -> String;
    fn getType() -> Type;
    fn hasDefaultValue() -> Bool;
    fn getDefaultValue() -> Expression?;
    fn isPublic() -> Bool;
    fn isPrivate() -> Bool;
    fn isProtected() -> Bool;
    fn isStatic() -> Bool;
    fn isReadonly() -> Bool;
    fn hasGetter() -> Bool;
    fn hasSetter() -> Bool;
    fn getGetter() -> Method?;
    fn getSetter() -> Method?;
    fn getAttributes() -> Attribute[];
    fn getMetadata() -> Metadata;
    fn getSourceLocation() -> SourceLocation;
    fn toBuilder() -> PropertyBuilder;
}
```

### Type

```efen
interface Type {
    fn getName() -> String;
    fn getFullName() -> String;
    fn isClass() -> Bool;
    fn isInterface() -> Bool;
    fn isStruct() -> Bool;
    fn isPrimitive() -> Bool;
    fn isArray() -> Bool;
    fn isGeneric() -> Bool;
    fn getGenericParameters() -> Type[];
    fn isAssignableFrom(other: Type) -> Bool;
    fn isAssignableTo(other: Type) -> Bool;

    // Статические методы для создания базовых типов
    static fn void() -> Type;
    static fn bool() -> Type;
    static fn int() -> Type;
    static fn float() -> Type;
    static fn string() -> Type;
    static fn array(elementType: Type) -> Type;
}
```

### Parameter

```efen
struct Parameter {
    name: String;
    type: Type;
    defaultValue: Expression?;
    isVariadic: Bool;
}
```

### SourceLocation

```efen
interface SourceLocation {
    fn getFile() -> String;
    fn getLine() -> Int;
    fn getColumn() -> Int;
    fn toString() -> String;
}
```

### Metadata

`MetadataValue` может быть значением расширения с произвольной бинарной схемой.
Перед публикацией HIR производитель сериализует его в непрозрачный payload и
сам отвечает за типовой ключ и версию схемы. Amber не вызывает методы значения
и не интерпретирует его байты.

```efen
interface Metadata {
    fn get(key: String) -> MetadataValue?;
    fn set(key: String, value: MetadataValue);
    fn has(key: String) -> Bool;
    fn remove(key: String);
    fn keys() -> String[];

    // Маркировка метаданных для включения в runtime
    fn markForRuntime(key: String);
    fn isMarkedForRuntime(key: String) -> Bool;
}
```

### Attribute

```efen
interface Attribute {
    fn getType() -> Type;
    fn getArguments() -> Map<String, Value>;
    fn getArgument(name: String) -> Value?;
}
```

### Visibility

```efen
enum Visibility {
    Public,
    Private,
    Protected,
    Internal
}
```

### CodeBlock

```efen
interface CodeBlock {
    // Создание пустого блока кода
    static fn empty() -> CodeBlock;

    // Добавление выражений
    fn addExpression(expr: Expression) -> CodeBlock;

    // Преобразование в строку
    fn toString() -> String;
}
```

### Expression

```efen
interface Expression {
    fn getType() -> Type;
    fn toString() -> String;

    // Статические методы для создания выражений
    static fn literal(value: Value) -> Expression;
    static fn variable(name: String) -> Expression;
    static fn call(target: Expression, method: String, args: Expression[]) -> Expression;
}
```
