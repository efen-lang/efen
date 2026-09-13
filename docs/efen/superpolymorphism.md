# Суперполиморфизм

В большинстве случаев класс реализует интерфейс статически —
во время создания объекта все методы интерфейса уже известны.

Однако иногда возникает необходимость в динамическом определении методов интерфейса на этапе выполнения программы.
Это называется **суперполиморфизмом**.

> **Суперполиморфизм** — возможность класса делегировать реализацию интерфейса динамически изменяемому свойству.

## Синтаксис

Класс объявляет интерфейс как свойство с помощью ключевого слова `interface`:

```efen
interface Drawable {
    func draw
    func resize(scale: Float)
}

class Shape implements Drawable {
    // Динамическая реализация интерфейса
    interface drawable: Drawable

    var x: Float
    var y: Float
}
```

Когда у класса есть свойство `interface drawable: Drawable`, это означает:
1. Класс реализует интерфейс `Drawable`
2. Все вызовы методов `Drawable` автоматически делегируются свойству `drawable`
3. Свойство `drawable` можно изменять в runtime

## Использование

```efen
strategy SVGDrawing for Drawable {
    func draw {
        print("Drawing as SVG")
    }

    func resize(scale: Float) {
        print("Resizing SVG by ${scale}")
    }
}

strategy CanvasDrawing for Drawable {
    func draw {
        print("Drawing on Canvas")
    }

    func resize(scale: Float) {
        print("Resizing Canvas by ${scale}")
    }
}

let shape = Shape(x: 10.0, y: 20.0)

// Устанавливаем реализацию через SVG
shape.drawable = SVGDrawing
shape.draw()  // Выведет: "Drawing as SVG"

// Меняем реализацию на Canvas
shape.drawable = CanvasDrawing
shape.draw()  // Выведет: "Drawing on Canvas"
```

## Пример: Система рендеринга

```efen
interface Renderer {
    func render(scene: Scene)
    func clear
}

strategy OpenGLRenderer for Renderer {
    func render(scene: Scene) {
        // Рендеринг через OpenGL
    }

    func clear {
        // Очистка OpenGL буфера
    }
}

strategy VulkanRenderer for Renderer {
    func render(scene: Scene) {
        // Рендеринг через Vulkan
    }

    func clear {
        // Очистка Vulkan буфера
    }
}

class GraphicsEngine implements Renderer {
    interface renderer: Renderer

    var scenes: [Scene]

    func renderAll {
        for scene in scenes {
            render(scene: scene)  // Делегируется renderer.render()
        }
    }
}

let engine = GraphicsEngine()

// Пользователь выбирает API
if userPreference == "opengl" {
    engine.renderer = OpenGLRenderer
} else {
    engine.renderer = VulkanRenderer
}

engine.renderAll()  // Использует выбранный рендерер
```

## Множественные интерфейсы

Класс может иметь несколько динамических интерфейсов:

```efen
interface Drawable {
    func draw
}

interface Serializable {
    func serialize -> String
    func deserialize(data: String)
}

class Document implements Drawable, Serializable {
    interface drawable: Drawable
    interface serializer: Serializable

    var content: String
}

let doc = Document(content: "Hello")

// Устанавливаем разные стратегии
doc.drawable = PDFDrawing
doc.serializer = JSONSerializer

doc.draw()  // Использует PDFDrawing
let data = doc.serialize()  // Использует JSONSerializer
```

## Комбинация со статическими методами

Класс может комбинировать статические и динамические реализации:

```efen
interface Drawable {
    func draw
    func clear
}

class Shape implements Drawable {
    interface drawable: Drawable  // Динамическая реализация draw()

    // Статическая реализация clear()
    func clear {
        print("Clearing shape")
    }
}

let shape = Shape()
shape.drawable = SVGDrawing

shape.draw()   // Делегируется drawable.draw()
shape.clear()  // Вызывает статический метод Shape.clear()
```

## Отличие от агрегации

**Агрегация (обычное свойство):**
```efen
class Shape {
    var renderer: Renderer  // Просто свойство
}

let shape = Shape()
shape.renderer.draw()  // Явный вызов через свойство
```

**Суперполиморфизм:**
```efen
class Shape implements Drawable {
    interface drawable: Drawable  // Динамический интерфейс
}

let shape = Shape()
shape.draw()  // Автоматическая делегация к drawable.draw()
```

Разница:
- **Агрегация**: нужно явно обращаться к свойству `shape.renderer.draw()`
- **Суперполиморфизм**: вызов напрямую `shape.draw()`, делегация автоматическая

## Когда использовать суперполиморфизм

**Используйте суперполиморфизм, когда:**
- Реализация интерфейса должна выбираться или меняться во время выполнения
- Нужна стратегия, но объект сам должен выглядеть как реализация интерфейса
- Требуется прозрачная замена поведения без изменения API
- Plugin-архитектура с динамической загрузкой реализаций

**Используйте обычную реализацию интерфейса, когда:**
- Реализация известна на этапе компиляции
- Поведение не меняется во время жизни объекта
- Важна производительность (статическая диспетчеризация)

**Используйте агрегацию, когда:**
- Нужен явный доступ к вложенному объекту
- Отношение "имеет" важнее отношения "является"
- Не нужна автоматическая делегация

## Производительность

Суперполиморфизм добавляет один уровень косвенности:

```
shape.draw() → shape.drawable.draw() → vtable[draw](shape.drawable)
```

Это медленнее статической реализации, но дает максимальную гибкость во время выполнения.

