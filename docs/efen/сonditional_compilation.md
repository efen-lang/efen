# Условная компиляция

Условная компиляция позволяет включать или исключать части кода в зависимости от определённых условий. 

Синтаксис:

```efen
#if <condition>
    code1
#else
    code2
#endif
```

Короткий синтаксис:

```efen
#when <condition>
code
```

Примеры:

```efen
#if os() == "windows"
    use WinAPI
#else
    use Posix
#endif

fn platformSpecificFunction {
    #if os() == "windows"
        // Код для Windows
        WinAPI.doSomethingWindowsSpecific()
    #else
        // Код для других платформ
        Posix.doSomethingPosixSpecific()   
    #endif
}
```

Условная компиляция не может нарушать целостность других блоков if, else if, else.
Не может пересекать обычные scope-блоки `{}`, функции, классы, интерфейсы и т.д.

```efen
#if condition1
    if true {
        // Код
    
#else // Ошибка: Нарушение целостности блока if
        // Код
    }
```
