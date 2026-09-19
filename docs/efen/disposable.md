# Disposable и lifecycle

Пользовательский destructor класса и низкоуровневый `Disposable` — разные
механизмы.

## Automatic destruction

Когда исчезает последний владелец объекта, compiler запускает user destructor
только внутри неявной `clean`-области. После него выполняется низкоуровневый,
non-throwing `Disposable`. Эта последовательность не является обычным `defer`:
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
