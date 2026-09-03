# Тестирование

`Efen` предлагает встроенную поддержку для написания и выполнения тестов.

Различается несколько типов тестов:
- **Модульные тесты**: Тестируют отдельные функции и модули, изолированные от остальной системы.
- **Интеграционные тесты**: Проверяют взаимодействие между несколькими модулями.
- **Функциональные тесты**: Тестируют полные сценарии использования приложения.
- **Fuzzy-тесты**: Автоматически генерируют случайные входные данные для проверки устойчивости кода.
- **Failure-тесты**: Проверяют, что код корректно обрабатывает ошибки и исключения.

## Расположение тестов

Модульные тесты могут быть размещены прямо в коде модуля
или в отдельном файле непосредственно рядом с тестируемым модулем.
Расширение у такого файла должно быть `.test.efn`.

Если модульные тесты занимают большой объём, 
их следует расположить в папке `tests` внутри директории модуля.
Имена файлов в этой папке также должны оканчиваться на `.test.efn`.

## Определение модульных тестов

Для определения модульного теста используется синтаксис:

```efen
    fn add(a: Int, b: Int) -> Int {
        return a + b
    }

    test add "should correctly add two numbers" {
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
    }
    
    test add "should handle zero correctly" {
        assert add(0, 0) == 0
        assert add(5, 0) == 5
    }
```

## Запуск тестов

Для запуска всех тестов в проекте используйте команду:

```bash
efen test .
```

Эта команда найдет и выполнит все тесты, определенные в файлах с расширением `.test.efn`.

## Fuzzy-тесты

Fuzzy-тесты позволяют автоматически генерировать случайные входные данные для функций,
что помогает выявить неожиданные ошибки и уязвимости.

Для определения fuzzy-теста используется декоратор `@fuzzy`:

```efen
    fn reverse_list(lst: [Int]) -> [Int] {
        return lst.reverse()
    }

    @fuzzy
    test reverse_list "should correctly reverse a list" {
        let list = [Int] where value in 0..x
        assert reverse_list(list) == list.reverse()
    }
```

## Failure-тесты

Failure-тесты проверяют, что функции корректно обрабатывают ошибки и исключения.
Для определения failure-теста используется декоратор `@failure`:

```efen
    fn getUserProfile(userId: Int) -> UserProfile in DataBase {
        let profile = DataBase.run sql {
            SELECT * FROM user_profiles WHERE id = userId
        }

        let userSettings = DataBase.run sql {
            SELECT * FROM user_settings WHERE user_id = userId
        }

        profile.settings = userSettings

        return profile
    }

    @failure
    test getUserProfile "should handle missing user profile" {
        let userId: Int in value > 0
        raise DataBaseError when DataBase.run sql {
            SELECT * FROM user_profiles WHERE id = userId
        }
        expect getUserProfile(userId) to throw DataBaseError
    }
```