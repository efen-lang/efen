# Система комментариев в Efen

## Типы комментариев

### 1. Обычные комментарии

```php
// Однострочный комментарий

/*
 * Многострочный
 * комментарий
 */
```

**Канал:** `HIDDEN` (1)
**Назначение:** Пояснения в коде, временные заметки
**Доступ:** Через `TokenStream`, не попадают в AST

### 2. Doc-комментарии

```php
/// Однострочный doc-комментарий

/**
 * Многострочный
 * doc-комментарий
 */
```

**Канал:** `DOC` (2)
**Назначение:** Документация API, генерация docs
**Доступ:** Автоматически прикрепляются к AST узлам

## Использование с `param`

Наша уникальная фича - документирование параметров внутри функции:

```php
fn calculateDiscount(orderId: String) -> Float {
    /// Customer's order identifier
    /// Must be a valid UUID v4
    param orderId: String

    /// Discount percentage (0-100)
    /// Default: 10%
    param discountRate: Float = 10.0

    /**
     * Maximum discount amount in dollars
     *
     * Range: $0 - $1000
     * Default: $100
     */
    param maxDiscount: Float = 100.0

    let order = loadOrder(orderId)
    let discount = min(order.total * discountRate / 100, maxDiscount)
    return discount
}
```

## Архитектура

### Каналы токенов ANTLR4

```
Source Code: fn foo() { /// Doc comment
                         let x = 42; // regular comment

DEFAULT (0):  [fn] [foo] [(] [)] [{] [let] [x] [=] [42] [;]
DOC (2):      ..................[/// Doc comment]..............
HIDDEN (1):   ..........................................[// regular comment]
```

### Извлечение комментариев

```cpp
#include "Parser/CommentExtractor.h"

// В ASTBuilder::exitFunctionDeclaration
auto token = ctx->getStart();
auto docComments = CommentExtractor::extractDocComments(
    tokens,  // TokenStream
    token    // До какого токена искать
);

std::string documentation = CommentExtractor::joinDocComments(docComments);
functionNode->setDocumentation(documentation);
```

### Пример результата

```cpp
// AST Node после парсинга:
Function {
    name: "calculateDiscount",
    documentation: "Customer's order identifier\nMust be a valid UUID v4",
    parameters: [
        Parameter {
            name: "orderId",
            type: "String",
            documentation: "Customer's order identifier\nMust be a valid UUID v4"
        },
        Parameter {
            name: "discountRate",
            type: "Float",
            default: 10.0,
            documentation: "Discount percentage (0-100)\nDefault: 10%"
        }
    ]
}
```

## Генерация документации

```bash
# Будущая команда для генерации docs
efenc doc --output ./docs src/**/*.efen
```

Результат:
```markdown
## calculateDiscount

Customer's order identifier
Must be a valid UUID v4

**Parameters:**
- `orderId: String` - Customer's order identifier. Must be a valid UUID v4
- `discountRate: Float = 10.0` - Discount percentage (0-100). Default: 10%
- `maxDiscount: Float = 100.0` - Maximum discount amount in dollars. Range: $0 - $1000. Default: $100

**Returns:** `Float`
```

## IDE интеграция

### Hover information
```
┌─────────────────────────────────────┐
│ fn calculateDiscount(...)           │
│                                     │
│ Customer's order identifier         │
│ Must be a valid UUID v4             │
│                                     │
│ Parameters:                         │
│ • orderId: String                   │
│ • discountRate: Float = 10.0        │
│ • maxDiscount: Float = 100.0        │
└─────────────────────────────────────┘
```

### Auto-complete
```
calculateDiscount(
  orderId: String,        // Customer's order identifier. Must be UUID v4
  ▌
)
```

## Лучшие практики

### ✅ Хорошо

```php
/// Validates user email address
/// Returns true if email format is valid
fn validateEmail(email: String) -> Bool {
    /// Email address to validate
    /// Must follow RFC 5322 format
    param email: String

    return email.matches(emailRegex)
}
```

### ❌ Плохо

```php
// this function validates email  (обычный комментарий вместо doc)
fn validateEmail(email: String) -> Bool {
    param email: String  // missing documentation
    return email.matches(emailRegex)
}
```

## Совместимость

- **Rust:** Похоже на `///` и `//!`
- **Swift:** Аналог `///` markup
- **TypeScript:** Похоже на JSDoc `/** */`
- **Efen уникальность:** `param` с doc-комментариями внутри функции!
