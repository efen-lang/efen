# Disposable Resources

Рассмотрим типичную задачу работы с файлом:

```efen
fn handleFile(path: str) {

    try {
        let file = gs::File.open(path);

        while let line = file.readLine() {
            println(line);
        }

    } finally {
        file.close();
    }
}
```

В этом примере блок try finally используется для гарантированного закрытия файла после его использования.
Он достаточно громоздкий и зависит от внимания программиста, чтобы не забыть закрыть ресурс.

`Efen` предлагает решать эту проблему с помощью явно обозначенных "disposable" ресурсов:

```efen
fn handleFile(path: str) {
    let disposable file = gs::File.open(path);

    while let line = file.readLine() {
        println(line);
    }
}
```

Ключевое слово `disposable` указывает компилятору,
что ресурс должен быть автоматически освобожден (в данном случае файл будет закрыт)
при условии, что тип ресурса реализует интерфейс `Disposable`.

## Интерфейс Disposable

Для автоматического управления ресурсами тип должен реализовать интерфейс `Disposable`:

```efen
interface Disposable {
    fn dispose -> Void
}
```

Метод `dispose()` вызывается автоматически компилятором, когда переменная
выходит из области видимости. Автоматическая очистка имеет ту же семантику, что
`defer`, и может иметь собственный выведенный `throws`.

### Пример реализации

```efen
class Database {
    implements Disposable

    private var connection: Connection

    @constructor
    fn init(connectionString: String) -> Self {
        this.connection = Connection.open(connectionString)
    }

    fn query(sql: String) -> ResultSet {
        return this.connection.execute(sql)
    }

    fn dispose {
        println("Закрываем соединение с БД")
        this.connection.close()
    }
}

// Использование
fn fetchData {
    let disposable db = Database("localhost:5432")

    let results = db.query("SELECT * FROM users")
    processResults(results)

    // dispose() будет вызван автоматически здесь
}
```

## Гарантии освобождения

Компилятор гарантирует, что `dispose()` будет вызван:

1. **При нормальном выходе из области видимости**
   ```efen
   fn process {
       let disposable file = File.open("data.txt")
       let content = file.read()
       // dispose() вызывается здесь
   }
   ```

2. **При раннем возврате (return)**
   ```efen
   fn process -> Bool {
       let disposable file = File.open("data.txt")

       if file.isEmpty() {
           return false  // dispose() вызывается здесь
       }

       processFile(file)
       return true  // dispose() вызывается здесь
   }
   ```

3. **При выбросе исключения**
   ```efen
   fn process throws {
       let disposable file = File.open("data.txt")

       if corruptedData(file) {
           throw Error("Corrupted file")  // dispose() вызывается перед выбросом
       }

       processFile(file)
   }
   ```

4. **При panic**
   ```efen
   fn process {
       let disposable file = File.open("data.txt")

       if invalidData(file) {
           panic("Invalid data!")  // dispose() вызывается перед panic
       }
   }
   ```

## Множественные disposable ресурсы

Можно объявить несколько disposable ресурсов - они будут освобождены в обратном порядке объявления:

```efen
fn transfer(sourcePath: String, destPath: String) {
    let disposable source = File.open(sourcePath)
    let disposable dest = File.create(destPath)
    let disposable buffer = Buffer.allocate(4096)

    while let chunk = source.read(buffer) {
        dest.write(chunk)
    }

    // Порядок освобождения:
    // 1. buffer.dispose()
    // 2. dest.dispose()
    // 3. source.dispose()
}
```

## Вложенные области видимости

Disposable работает с любыми блоками кода:

```efen
fn process(files: [String]) {
    for path in files {
        let disposable file = File.open(path)
        processFile(file)
        // file.dispose() вызывается в конце каждой итерации
    }
}

fn conditionalProcessing(condition: Bool) {
    if condition {
        let disposable resource = Resource.acquire()
        useResource(resource)
        // resource.dispose() вызывается здесь
    }
}
```

## Передача ownership

Disposable ресурсы можно передавать, передавая ownership:

```efen
fn openFile(path: String) -> File {
    let disposable file = File.open(path)
    return file  // Ownership передается, dispose() НЕ вызывается здесь
}

fn useFile {
    let disposable file = openFile("data.txt")
    processFile(file)
    // dispose() вызывается здесь
}
```

## Ручной вызов dispose

Можно вызвать `dispose()` вручную, но после этого использовать ресурс нельзя:

```efen
fn manualDispose {
    let disposable file = File.open("data.txt")

    processFile(file)

    file.dispose()  // Ручной вызов

    // file больше недоступен для использования
    // file.read()  // Ошибка компиляции!
}
```

## Отмена автоматического dispose

Чтобы предотвратить автоматический dispose, используйте `forget`:

```efen
fn keepAlive -> File {
    let disposable file = File.open("data.txt")

    // Отменяем автоматический dispose
    forget(file)

    return file  // Ответственность за закрытие на вызывающем коде
}

fn caller {
    let file = keepAlive()
    // Теперь нужно вручную закрыть файл
    defer {
        file.close()
    }
}
```

## Composable Disposables

Класс может содержать disposable поля:

```efen
class FileProcessor {
    implements Disposable

    private let disposable input: File
    private let disposable output: File
    private let disposable logger: Logger

    @constructor
    fn init(inputPath: String, outputPath: String) -> Self {
        this.input = File.open(inputPath)
        this.output = File.create(outputPath)
        this.logger = Logger("processor.log")
    }

    fn process {
        // Обработка
    }

    fn dispose {
        // Автоматически вызовет dispose() для всех disposable полей
        // в обратном порядке объявления:
        // 1. logger.dispose()
        // 2. output.dispose()
        // 3. input.dispose()
    }
}
```

## Асинхронное освобождение

Для асинхронных ресурсов используйте `AsyncDisposable`:

```efen
interface AsyncDisposable {
    async fn disposeAsync -> Void
}

class AsyncDatabase {
    implements AsyncDisposable

    private var connection: AsyncConnection

    async fn disposeAsync {
        await this.connection.closeAsync()
        println("Соединение закрыто")
    }
}

async fn useDatabase {
    let disposable db = AsyncDatabase()
    await db.query("SELECT * FROM users")
    // await db.disposeAsync() вызывается автоматически
}
```

## Обработка ошибок в dispose

`dispose()` может бросить исключение и по-прежнему использоваться для
автоматической очистки. Его итоговый `throws` участвует в сводке окружающей
функции:

```efen
class FallibleResource {
    implements Disposable

    fn dispose -> Void throws DisposeError {
        this.connection.close()
    }
}

fn useResource {
    let disposable resource = FallibleResource()

    processResource(resource)
}
```

Если `processResource` завершилась нормально, `DisposeError` становится главным
исключением выхода. Если она уже бросила другое исключение, оно остаётся
главным, а `DisposeError` добавляется в его список `suppressed`. При нескольких
ресурсах все операции очистки продолжают выполняться в порядке LIFO; первая
активная ошибка остаётся главной, остальные добавляются к ней в порядке
возникновения. Это соответствует поведению Java `try-with-resources`.

Обычный `catch` сопоставляется только с главным исключением. Если ошибка
cleanup требует самостоятельной обработки, `dispose()` вызывается внутри
явного `defer` с локальным `try`/`catch`. Исключение с контрактом `MustHandle`
обязано быть обработано именно так и не может остаться только в `suppressed`.

## Disposable в структурах данных

Disposable можно использовать в коллекциях:

```efen
fn processMultipleFiles(paths: [String]) {
    let disposable files = paths.map => File.open($path)

    for file in files {
        processFile(file)
    }

    // Все файлы будут автоматически закрыты
    // files.dispose() вызовет dispose() для каждого элемента
}
```

## Лучшие практики

1. **Всегда используйте disposable для ресурсов**
   ```efen
   // Хорошо
   let disposable file = File.open(path)

   // Плохо - можно забыть закрыть
   let file = File.open(path)
   ```

2. **Не забывайте про ownership**
   ```efen
   fn getData -> File {
       let disposable file = File.open("data.txt")
       return file  // Ownership передается
   }
   ```

3. **Используйте defer для сложных сценариев**
   ```efen
   fn complex {
       let resource = acquireResource()
       defer {
           resource.release()  // Гарантированно выполнится
       }

       // Сложная логика
   }
   ```

4. **Обрабатывайте ошибки в dispose**
   ```efen
   class SafeResource {
       implements Disposable

       fn dispose {
           try {
               this.connection.close()
           } catch e: Error {
               logError("Failed to dispose: ${e}")
           }
       }
   }
   ```

5. **Документируйте disposable классы**
   ```efen
   /// Represents a database connection that must be disposed.
   /// Use with `let disposable` to ensure proper cleanup.
   class Database {
       implements Disposable

       // ...
   }
   ```

## Сравнение с другими подходами

### try-finally

```efen
// Старый подход
fn oldWay {
    let file = File.open("data.txt")
    try {
        processFile(file)
    } finally {
        file.close()
    }
}

// С disposable
fn newWay {
    let disposable file = File.open("data.txt")
    processFile(file)
}
```

### defer

```efen
// С defer
fn withDefer {
    let file = File.open("data.txt")
    defer {
        file.close()
    }
    processFile(file)
}

// С disposable - проще
fn withDisposable {
    let disposable file = File.open("data.txt")
    processFile(file)
}
```

### RAII (C++)

```cpp
// C++ RAII
void processFile() {
    std::ifstream file("data.txt");  // Автоматически закроется
    // ...
}  // Деструктор вызывается здесь
```

```efen
// Efen disposable - явная семантика
fn processFile {
    let disposable file = File.open("data.txt")
    // ...
}  // dispose() вызывается здесь
```

## Частые ошибки

1. **Забыть ключевое слово disposable**
   ```efen
   // Ошибка - файл не закроется автоматически
   let file = File.open("data.txt")

   // Правильно
   let disposable file = File.open("data.txt")
   ```

2. **Использование после dispose**
   ```efen
   let disposable file = File.open("data.txt")
   file.dispose()
   file.read()  // Ошибка компиляции!
   ```

3. **Двойной dispose**
   ```efen
   let disposable file = File.open("data.txt")
   file.dispose()  // Ручной вызов
   // Автоматический dispose() не вызывается повторно
   ```

## Интеграция с другими языковыми возможностями

### С pattern matching

`Result<T, E>` здесь является [variant type](types/variant.md):

```efen
fn processFile(result: Result<File, Error>) {
    match result {
        .ok.{ value: let file }: {
            let disposable f = file
            processData(f)
            // f.dispose() вызывается здесь
        }
        .err.{ let error }: println("Error: ${error}")
    }
}
```

### С замыканиями

```efen
fn withFile<T>(path: String, action: (File) -> T) -> T {
    let disposable file = File.open(path)
    return action(file)
    // file.dispose() вызывается после action
}

let content = withFile("data.txt", (file) => file.read())
```

### С generics

```efen
fn useResource<T: Disposable>(resource: T) {
    let disposable r = resource
    processResource(r)
    // r.dispose() вызывается автоматически
}
```
