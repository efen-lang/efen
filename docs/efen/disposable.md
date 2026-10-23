# Disposable и lifecycle

Пользовательский destructor класса и низкоуровневый `Disposable` — разные
механизмы.

## Запись

Пользовательский destructor объявляется атрибутом, как конструктор:
`@destructor fn deinit()`, без параметров и результата, не больше одного в
классе. Низкоуровневый этап — контракт `Disposable` с методом `fn dispose()`
(Edmond, 2026-10-23).

```efen
class File {
    implements Disposable

    var handle: Int

    @constructor
    fn init(handle: Int) -> Self {
        self.handle = handle
    }

    @destructor
    fn deinit() {
        flush()
    }

    fn dispose() {
        closeHandle(handle)
    }
}
```

Ни `deinit`, ни `dispose` не вызываются как обычные методы: их вызывает только
уничтожение объекта.

## Automatic destruction

Когда исчезает последний владелец объекта, compiler запускает user destructor
только внутри неявной `clean`-области. После него выполняется низкоуровневый,
non-throwing `Disposable`. У наследника этапы идут от наиболее производного класса
к базе: `deinit` и `dispose` наследника, затем `deinit` и `dispose` базы. После
всей цепочки освобождаются поля, затем память объекта. Эта последовательность не является обычным `defer`:
правила `suppressed`-исключений для `defer` не переносятся на automatic
destruction без отдельного решения.

Обычный бросающий destructor не вызывается автоматически: это явная операция
автора с обычной семантикой исключений.

## Low-level `Disposable`

`Disposable` — внутренний non-throwing этап освобождения ресурсов после user
destructor. Он не выражает автоматический выход переменной из lexical scope:
момент automatic destruction определяется последним владельцем объекта.

## Граница модели

Этот документ описывает текущую lifecycle-семантику. Старые формы `let
disposable`, `forget`, автоматический бросающий `dispose()` и примеры, которые
приравнивали `Disposable` к `defer`, не являются частью текущего Efen.
