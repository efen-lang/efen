# Architecture Overview

## Compilation Pipeline

```
PHP Source Code
      ↓
  ANTLR4 Lexer/Parser
      ↓
    AST Builder
      ↓
   PHP MLIR Dialect
      ↓
  Lowering Passes
      ↓
  Standard/LLVM Dialect
      ↓
   LLVM CodeGen
      ↓
  Machine Code
```

## Components

- **Frontend**: Parsing PHP to AST using ANTLR4
- **PHP Dialect**: MLIR operations for PHP constructs
- **Lowering**: Transform PHP dialect to standard dialects
- **CodeGen**: Final compilation to machine code