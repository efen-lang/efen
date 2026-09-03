# Классы не то, чем кажутся

Классы не просто так являются абстракциями более высокого уровня, 
чем структуры или типы данных. 

Мы попробуем рассмотреть классы с точки зрения компилятора, как 
на самом деле компилятор изнутри видит класс.

Рассмотрим простой класс.

```efen
class Point {
    var x: Float = 0
    var y: Float = 0
    
    @constructor
    fn init(x: Float, y: Float) {
        self.x = x
        self.y = y
    }
}
```

Как компилятор видит это?

```efen
struct Point {

    projection Raw as None
    projection NonInit as Nullable

    var x: Float = 0.0
    var y: Float = 0.0
}

fn init(x: Float, y: Float) -> Self in Self {
    %self.x = x
    %self.y = y
}
```

Компилятор воспринимает класс как структуру данных с двумя проекциями Raw и NonInit, 
которые используются в конструкторе и деструкторе