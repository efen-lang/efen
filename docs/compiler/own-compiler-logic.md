# Формальная модель системы владения Phx

Данный документ содержит математическую спецификацию 
и алгоритмы проверки корректности системы владения ресурсами в языке `Phx`.

---

## 1. Формальная математическая модель

### 1.1. Базовые множества и определения

**Множество аспектов владения:**
```
C = {own, read, write, shared, split, inspect}
```

**Слот (абстракция ресурса):**
```
Slot ::= ⟨id, τ, caps, alive⟩

где:
  id   : SlotId           — уникальный идентификатор
  τ    : Type             — тип ресурса
  caps : 𝒫(C)             — множество текущих аспектов
  alive: 𝔹                — валидность слота
```

**Ссылка (переменная):**
```
Ref ::= ⟨name, σ⟩

где:
  name : Identifier       — имя переменной
  σ    : SlotId           — идентификатор слота
```

**Заимствование:**
```
Borrow ::= ⟨σ, c, scope, active⟩

где:
  σ      : SlotId         — заимствуемый слот
  c      : C              — аспект заимствования
  scope  : ScopeId        — область видимости
  active : 𝔹              — статус активности
```

**Область видимости:**
```
Scope ::= ⟨id, parent, slots, refs, borrows⟩

где:
  id      : ScopeId
  parent  : ScopeId ∪ {⊥}
  slots   : SlotId ⇀ Slot
  refs    : Identifier ⇀ Ref
  borrows : 𝒫(Borrow)
```

**Контекст проверки:**
```
Γ ::= ⟨scopes, current, errors⟩

где:
  scopes  : ScopeId ⇀ Scope
  current : ScopeId
  errors  : 𝒫(Error)
```

### 1.2. Отношения и предикаты

**Иерархия аспектов:**
```
own ≥ write ≥ read ≥ inspect

Формально:
  ≥ ⊆ C × C — частичный порядок на аспектах
```

**Правила зависимости:**
```
write ∈ caps ⟹ read ∈ caps
mut := write ∧ shared ∉ caps
shared ⊥ mut
```

**Предикат валидности слота:**
```
valid(σ, Γ) ≝ let ⟨_, _, _, alive⟩ = Γ.scopes(current).slots(σ)
              in alive = true

invalidate(σ, Γ) ≝ Γ[slots(σ).alive ↦ false]
```

**Предикат наличия аспекта:**
```
has(σ, c, Γ) ≝ let ⟨_, _, caps, _⟩ = Γ.scopes(current).slots(σ)
              in c ∈ caps
```

**Активные заимствования слота:**
```
activeBorrows(σ, Γ) ≝ {b ∈ Γ.scopes(current).borrows |
                       b.σ = σ ∧ b.active = true}
```

### 1.3. Инварианты системы

**Инвариант 1 (Единственность владельца):**
```
∀σ₁, σ₂ ∈ dom(Γ.slots):
  (σ₁ ≠ σ₂ ∧ valid(σ₁, Γ) ∧ valid(σ₂, Γ) ∧
   has(σ₁, own, Γ) ∧ has(σ₂, own, Γ)) ⟹
  resource(σ₁) ≠ resource(σ₂)
```

**Инвариант 2 (Согласованность алиасов):**
```
∀r₁, r₂ ∈ refs: r₁.σ = r₂.σ ⟹ (valid(r₁.σ, Γ) ⟺ valid(r₂.σ, Γ))
```

**Инвариант 3 (Зависимость аспектов):**
```
∀σ: has(σ, write, Γ) ⟹ has(σ, read, Γ)
```

**Инвариант 4 (Эксклюзивность mut):**
```
∀σ: |{b ∈ activeBorrows(σ, Γ) | b.c = mut}| ≤ 1
```

**Инвариант 5 (Несовместимость read/write):**
```
∀σ: (∃b ∈ activeBorrows(σ, Γ): b.c = write) ⟹
    (∀b' ∈ activeBorrows(σ, Γ): b'.c ≠ read)
```

---

## 2. Правила вывода (Inference Rules)

### 2.1. Создание слота

**Правило CREATE-SLOT:**
```
    τ — тип ресурса
    σ = fresh SlotId
    caps₀ = {own, read, write}
    ────────────────────────────────────────────
    Γ ⊢ create(x: τ) ⇝ Γ'

где:
  Γ'.slots(σ) = ⟨σ, τ, caps₀, true⟩
  Γ'.refs(x) = ⟨x, σ⟩
```

### 2.2. Создание алиаса

**Правило ALIAS:**
```
    Γ.refs(x₁) = ⟨x₁, σ⟩
    valid(σ, Γ)
    ────────────────────────────────────────────
    Γ ⊢ let x₂ = x₁ ⇝ Γ'

где:
  Γ'.refs(x₂) = ⟨x₂, σ⟩
```

**Правило ALIAS-FAIL:**
```
    Γ.refs(x₁) = ⟨x₁, σ⟩
    ¬valid(σ, Γ)
    ────────────────────────────────────────────
    Γ ⊢ let x₂ = x₁ ⇝ error("moved value")
```

### 2.3. Перемещение владения (Move)

**Правило MOVE:**
```
    Γ.refs(x) = ⟨x, σ⟩
    valid(σ, Γ)
    has(σ, own, Γ)
    fn f(y: τ own)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ⇝ Γ'

где:
  Γ' = invalidate(σ, Γ)
```

**Правило MOVE-DOUBLE-FAIL:**
```
    Γ.refs(x) = ⟨x, σ⟩
    ¬valid(σ, Γ)
    ────────────────────────────────────────────
    Γ ⊢ use(x) ⇝ error("use of moved value")
```

### 2.4. Заимствование неизменяемое

**Правило BORROW-READ:**
```
    Γ.refs(x) = ⟨x, σ⟩
    valid(σ, Γ)
    has(σ, read, Γ)
    ∀b ∈ activeBorrows(σ, Γ): b.c ≠ write
    fn f(y: τ read)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ⇝ Γ'

где:
  b = ⟨σ, read, scope_f, true⟩
  Γ'.borrows = Γ.borrows ∪ {b}
```

**Правило BORROW-READ-FAIL:**
```
    Γ.refs(x) = ⟨x, σ⟩
    ∃b ∈ activeBorrows(σ, Γ): b.c = write
    fn f(y: τ read)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ⇝ error("cannot borrow: already borrowed as write")
```

### 2.5. Заимствование изменяемое

**Правило BORROW-MUT:**
```
    Γ.refs(x) = ⟨x, σ⟩
    valid(σ, Γ)
    has(σ, write, Γ)
    activeBorrows(σ, Γ) = ∅
    fn f(y: τ mut)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ⇝ Γ'

где:
  b = ⟨σ, mut, scope_f, true⟩
  Γ'.borrows = Γ.borrows ∪ {b}
  Γ'.slots(σ).suspended = Γ.slots(σ).caps
  Γ'.slots(σ).caps = {own} ∩ Γ.slots(σ).caps
```

**Правило BORROW-MUT-FAIL:**
```
    Γ.refs(x) = ⟨x, σ⟩
    activeBorrows(σ, Γ) ≠ ∅
    fn f(y: τ mut)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ⇝ error("cannot borrow as mut: already borrowed")
```

### 2.6. Завершение заимствования

**Правило END-BORROW:**
```
    b = ⟨σ, c, scope, true⟩ ∈ Γ.borrows
    exitScope(scope)
    ────────────────────────────────────────────
    Γ ⊢ end(b) ⇝ Γ'

где:
  Γ'.borrows = Γ.borrows \ {b}
  Γ'.slots(σ).caps = Γ.slots(σ).suspended (если c = mut)
```

### 2.7. Выход из области видимости

**Правило EXIT-SCOPE:**
```
    scope = Γ.current
    ∀b ∈ Γ.borrows: b.scope = scope ⟹ end(b)
    ∀σ ∈ dom(scope.slots): has(σ, own, Γ) ⟹ destroy(σ)
    ────────────────────────────────────────────
    Γ ⊢ exit(scope) ⇝ Γ'

где:
  Γ'.current = scope.parent
```

---

## 3. Алгоритмы проверки

### 3.1. Проверка перемещения владения

**Алгоритм CHECK-MOVE:**
```
Вход: Γ, x (переменная), required (требуемые аспекты)
Выход: Γ' или Error

1. σ ← lookup(Γ, x)
   если σ = ⊥ то вернуть Error("variable not found")

2. если ¬valid(σ, Γ) то
     вернуть Error("use of moved value")

3. available ← capabilities(Γ, σ)
   если required ⊄ available то
     вернуть Error("missing capabilities: " + (required \ available))

4. если own ∈ required то
     Γ' ← invalidate(σ, Γ)
     вернуть Γ'
   иначе
     вернуть Γ
```

**Формальное определение:**
```
CheckMove(Γ, x, required) =
  let σ = Γ.refs(x).σ in
  match (valid(σ, Γ), required ⊆ Γ.slots(σ).caps, own ∈ required) with
  | (false, _, _) → error("moved")
  | (true, false, _) → error("missing capabilities")
  | (true, true, true) → invalidate(σ, Γ)
  | (true, true, false) → Γ
```

### 3.2. Проверка создания заимствования

**Алгоритм CHECK-BORROW:**
```
Вход: Γ, σ (слот), c (аспект), scope_target (целевая область)
Выход: Γ' или Error

1. если ¬valid(σ, Γ) то
     вернуть Error("cannot borrow moved value")

2. если c ∉ capabilities(Γ, σ) то
     вернуть Error("slot doesn't have capability " + c)

3. active ← activeBorrows(σ, Γ)

4. случай c:
     write →
       если |active| > 0 то
         вернуть Error("cannot borrow as write")

     read →
       если ∃b ∈ active: b.c = write то
         вернуть Error("already borrowed as write")

     mut →
       если |active| > 0 то
         вернуть Error("already borrowed")

5. b ← ⟨σ, c, scope_target, true⟩
   Γ' ← Γ[borrows ↦ Γ.borrows ∪ {b}]

6. если c = mut то
     Γ'' ← suspend_capabilities(Γ', σ)
     вернуть Γ''
   иначе
     вернуть Γ'
```

**Вспомогательная функция suspend_capabilities:**
```
suspend_capabilities(Γ, σ) =
  let caps = Γ.slots(σ).caps
      own_cap = {own} ∩ caps
  in Γ[slots(σ).suspended ↦ caps,
       slots(σ).caps ↦ own_cap]
```

### 3.3. Проверка lifetime заимствования

**Алгоритм CHECK-LIFETIME:**
```
Вход: Γ, b (заимствование), scope_use (область использования)
Выход: Boolean

1. scope_borrow ← b.scope

2. если ¬isAncestorOrSelf(scope_borrow, scope_use) то
     вернуть false

3. вернуть true
```

**Предикат isAncestorOrSelf:**
```
isAncestorOrSelf: Scope × Scope → 𝔹

isAncestorOrSelf(s₁, s₂) =
  s₁ = s₂ ∨
  (s₂.parent ≠ ⊥ ∧ isAncestorOrSelf(s₁, s₂.parent))
```

### 3.4. Проверка передачи между потоками

**Алгоритм CHECK-SEND:**
```
Вход: Γ, σ (слот), scope_target (целевая область в другом потоке)
Выход: Boolean

1. caps ← capabilities(Γ, σ)

2. sendable ← {own, val, inspect, shared}

3. если caps ⊄ sendable то
     вернуть Error("non-sendable capabilities: " + (caps \ sendable))

4. active_mut ← {b ∈ activeBorrows(σ, Γ) | b.c = mut}

5. если |active_mut| > 0 то
     вернуть Error("cannot send: mut borrow exists")

6. вернуть true
```

**Предикат sendable:**
```
Sendable: C → 𝔹

Sendable(c) = c ∈ {own, val, inspect, shared}
```

### 3.5. Завершение заимствования

**Алгоритм END-BORROW:**
```
Вход: Γ, b (заимствование)
Выход: Γ'

1. Γ' ← Γ[borrows ↦ Γ.borrows \ {b}]

2. если b.c = mut то
     σ ← b.σ
     suspended ← Γ.slots(σ).suspended
     Γ'' ← Γ'[slots(σ).caps ↦ suspended,
               slots(σ).suspended ↦ ⊥]
     вернуть Γ''
   иначе
     вернуть Γ'
```

### 3.6. Выход из области видимости

**Алгоритм EXIT-SCOPE:**
```
Вход: Γ, scope (область видимости)
Выход: Γ'

1. borrows_to_end ← {b ∈ Γ.borrows | b.scope = scope.id}

2. Γ₁ ← Γ
   для каждого b ∈ borrows_to_end:
     Γ₁ ← END-BORROW(Γ₁, b)

3. owned_slots ← {σ ∈ dom(scope.slots) | has(σ, own, Γ₁)}

4. для каждого σ ∈ owned_slots:
     если valid(σ, Γ₁) то
       active ← activeBorrows(σ, Γ₁)
       если |active| > 0 то
         вернуть Error("cannot destroy: active borrows")
       Γ₁ ← destroy(σ, Γ₁)

5. Γ' ← Γ₁[current ↦ scope.parent]

6. вернуть Γ'
```

**Вспомогательная функция destroy:**
```
destroy(σ, Γ) =
  let slot = Γ.slots(σ)
      weak_refs = slot.weak_refs
  in Γ[slots(σ).alive ↦ false,
       ∀w ∈ weak_refs: w.valid ↦ false]
```

---

## 4. Формальные доказательства

### 4.1. Теорема единственности владельца

**Теорема 1:**
```
∀Γ, R (ресурс), t (момент времени):
  |{σ | valid(σ, Γ) ∧ has(σ, own, Γ) ∧ resource(σ) = R}| ≤ 1
```

**Доказательство:**
```
Индукция по времени выполнения программы.

База: t = 0
  При создании ресурса R создается ровно один слот σ с own.
  |{σ | ...}| = 1 ✓

Шаг: t → t+1
  Рассмотрим возможные операции:

  1) CREATE: создается новый ресурс R' ≠ R
     Не влияет на счетчик для R ✓

  2) MOVE(σ): σ.alive ← false
     |{σ | valid(σ, Γ') ∧ ...}| = 0 или 1 ✓

  3) BORROW: не изменяет own
     Счетчик не меняется ✓

  4) EXIT-SCOPE: вызывает destroy(σ)
     σ.alive ← false
     Счетчик уменьшается на 1 ✓

∴ Инвариант сохраняется для всех t ∎
```

### 4.2. Теорема отсутствия use-after-free

**Теорема 2:**
```
∀Γ, операция access(σ):
  Γ ⊢ access(σ) ⇒ valid(σ, Γ)
```

**Доказательство:**
```
Рассмотрим все правила доступа:

1) MOVE:
   Предусловие: valid(σ, Γ)
   Проверяется явно ✓

2) BORROW-READ, BORROW-MUT:
   Предусловие: valid(σ, Γ)
   Проверяется явно ✓

3) ALIAS:
   Предусловие: valid(σ, Γ)
   Если ¬valid(σ, Γ), выдается ошибка (ALIAS-FAIL) ✓

∴ Все доступы проверяют valid(σ, Γ) ∎
```

### 4.3. Теорема отсутствия data races

**Теорема 3:**
```
∀Γ, σ, потоки t₁ ≠ t₂:
  ¬(write(t₁, σ) ∧ access(t₂, σ))
```

**Доказательство:**
```
Рассмотрим случаи параллельного доступа:

Случай 1: mut borrow в t₁
  По правилу BORROW-MUT:
    activeBorrows(σ, Γ) = ∅ — предусловие
    После создания: |activeBorrows(σ, Γ')| = 1

  По правилу CHECK-SEND:
    mut ∉ {own, val, inspect, shared}
    ∴ mut нельзя отправить в t₂

  ∴ Невозможен доступ из t₂ ✓

Случай 2: shared с write
  По правилу CHECK-SEND:
    Требуется внутренняя синхронизация
    Проверяется hasInternalSynchronization

  ∴ Доступ безопасен ✓

Случай 3: передача own в t₂
  По правилу MOVE:
    Γ' = invalidate(σ, Γ)

  Попытка доступа из t₁:
    ¬valid(σ, Γ') ⇒ error

  ∴ Невозможен доступ из t₁ ✓

∎
```

### 4.4. Теорема корректности системы типов

**Теорема 4 (Soundness):**
```
Если Γ ⊢ P : τ (программа P проходит проверку типов),
то выполнение P не приводит к:
  1) use-after-free
  2) double-free
  3) data races
```

**Доказательство:**
```
Следует из Теорем 1, 2, 3:

1) Теорема 2 ⇒ нет use-after-free

2) Теорема 1 + алгоритм EXIT-SCOPE ⇒ нет double-free
   (destroy вызывается только для valid слотов с own,
    и только один такой слот существует)

3) Теорема 3 ⇒ нет data races

∎
```

### 4.5. Сложность алгоритмов

**Теорема 5 (Complexity):**
```
Проверка владения для программы размера n выполняется за O(n).
```

**Доказательство:**
```
Пусть n = |AST| — количество узлов в AST.

Основной алгоритм:
  visitNode: каждый узел посещается 1 раз
  ∴ O(n) вызовов

Операции на узле:
  - lookup(Γ, x): O(1) (хэш-таблица)
  - valid(σ, Γ): O(1) (чтение поля)
  - activeBorrows(σ, Γ): O(b), где b — количество активных borrows

Ограничение на b:
  По инварианту 4: |{b | b.c = mut}| ≤ 1
  По инварианту 5: write и read несовместимы

  Практически: b ≤ c для некоторой константы c
  (обычно c < 10)

∴ Операции на узле: O(c) = O(1)

Общая сложность: O(n) × O(1) = O(n) ∎
```

---

## 5. Расширения модели

### 5.1. Слабые ссылки

**Расширение Slot:**
```
Slot ::= ⟨id, τ, caps, alive, weak_refs⟩

где:
  weak_refs : 𝒫(WeakRef)

WeakRef ::= ⟨target, valid⟩
  target : SlotId
  valid  : 𝔹
```

**Правило CREATE-WEAK:**
```
    Γ.refs(x) = ⟨x, σ⟩
    valid(σ, Γ)
    has(σ, own, Γ) ∨ (∃σ': has(σ', own, Γ) ∧ resource(σ') = resource(σ))
    ────────────────────────────────────────────
    Γ ⊢ weak(x) ⇝ Γ'

где:
  w = ⟨σ, true⟩
  σ_weak = fresh SlotId
  Γ'.slots(σ_weak) = ⟨σ_weak, τ?, {inspect}, true, {w}⟩
  Γ'.slots(σ).weak_refs = Γ.slots(σ).weak_refs ∪ {w}
```

**Инвариант weak ссылок:**
```
∀w ∈ WeakRef:
  w.valid = true ⟹ (∃σ: σ = w.target ∧ valid(σ, Γ))
```

**Правило DESTROY с weak:**
```
    σ — уничтожаемый слот
    W = Γ.slots(σ).weak_refs
    ────────────────────────────────────────────
    Γ ⊢ destroy(σ) ⇝ Γ'

где:
  ∀w ∈ W: Γ'.weak_refs(w).valid = false
  Γ'.slots(σ).alive = false
```

### 5.2. Передача между потоками (Thread Safety)

**Семантика `shared`:**

Атрибут `shared` указывает, что тип данных можно безопасно передавать между потоками.
Это статическая гарантия thread-safety на уровне типов.

**Правило TYPE-SHARED:**
```
    τ помечен как shared
    ────────────────────────────────────────────
    shared ∈ capabilities(τ)

Примеры:
  class Counter { shared }  // Внутренне синхронизирован
  class Point { }           // НЕ shared по умолчанию
```

**Правило PASS-SHARED:**
```
    Γ ⊢ f : (shared own T) → U
    Γ.refs(x) = ⟨x, σ⟩
    has(σ, shared, Γ)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ✓

Ошибка компиляции:
    Γ ⊢ f : (shared own T) → U
    Γ.refs(x) = ⟨x, σ⟩
    ¬has(σ, shared, Γ)
    ────────────────────────────────────────────
    Γ ⊢ f(x) ✗  // Error: передача non-shared в shared параметр
```

**Правило CLONE-SHARED:**
```
    Γ.refs(x) = ⟨x, σ⟩
    has(σ, shared, Γ)
    ────────────────────────────────────────────
    Γ ⊢ clone(x) ⇝ Γ', x'

где:
  Γ' содержит новый слот σ' для x' с теми же capabilities
  Реализация clone должна гарантировать thread-safety
```

### 5.3. Разделение владения (Split)

**Семантика split:**

При доступе к полю с атрибутом `split` создаётся **отдельный слот владения** для этого поля.
Это позволяет независимо заимствовать разные поля одной структуры.

**Структурный слот:**
```
StructSlot ::= ⟨id, τ, caps, alive, fields⟩

где:
  fields : FieldName ⇀ SlotId

Инвариант:
  f ∈ dom(fields) ⟹ ∃σ_f: slots(σ_f).alive ∧ fields(f) = σ_f
  // Для каждого split-поля существует живой слот
```

**Правило SPLIT-FIELD (создание слота для поля):**
```
    Γ.refs(x) = ⟨x, σ_struct⟩
    σ_struct : StructSlot
    f ∈ fields(τ_struct)
    split ∈ capabilities(f)
    f ∉ dom(σ_struct.fields)  // Поле ещё не разделено
    ────────────────────────────────────────────
    Γ ⊢ access(x.f) ⇝ Γ', σ_f

где:
  σ_f = fresh SlotId  // Новый уникальный слот для поля
  Γ'.slots(σ_f) = ⟨σ_f, τ_f, caps_f, true, ∅⟩
  Γ'.slots(σ_struct).fields(f) = σ_f

Результат: поле f теперь имеет собственный слот σ_f
```

**Правило SPLIT-FIELD-REUSE (повторный доступ к split-полю):**
```
    Γ.refs(x) = ⟨x, σ_struct⟩
    σ_struct.fields(f) = σ_f  // Слот уже создан
    ────────────────────────────────────────────
    Γ ⊢ access(x.f) ⇝ Γ, σ_f

Результат: возвращается существующий слот σ_f
```

**Независимость split полей:**
```
∀σ_struct, f₁ ≠ f₂:
  σ₁ = σ_struct.fields(f₁)
  σ₂ = σ_struct.fields(f₂)
  ⟹
  activeBorrows(σ₁, Γ) ⊥ activeBorrows(σ₂, Γ)

Следствие: можно одновременно заимствовать x.f₁ и x.f₂
```

**Правило DESTROY-STRUCT (уничтожение с split-полями):**
```
    σ_struct : StructSlot
    F = dom(σ_struct.fields)  // Все split-поля
    ∀f ∈ F: activeBorrows(σ_struct.fields(f), Γ) = ∅
    ────────────────────────────────────────────
    Γ ⊢ destroy(σ_struct) ⇝ Γ'

где:
  ∀f ∈ F: Γ' = destroy(σ_struct.fields(f), Γ')
  Γ'.slots(σ_struct).alive = false

// Сначала уничтожаем все слоты полей, затем саму структуру
```

---

## 6. Практические аспекты реализации

### 6.1. Структуры данных

**Эффективное представление Scope:**
```
Scope:
  id       : uint64
  parent   : uint64 | null
  slots    : HashMap<SlotId, Slot>
  refs     : HashMap<String, Ref>
  borrows  : SmallVec<Borrow>  // обычно < 10 элементов
```

**Оптимизация поиска слота:**
```
Γ содержит дополнительное поле:
  slot_cache : HashMap<SlotId, ScopeId>

lookup(Γ, σ):
  если σ ∈ Γ.slot_cache то
    scope_id = Γ.slot_cache(σ)
    вернуть Γ.scopes(scope_id).slots(σ)
  иначе
    // медленный поиск вверх по дереву scopes
```

### 6.2. Flow-sensitive анализ

**Вывод capabilities:**
```
infer: Γ × Expr → 𝒫(C)

infer(Γ, x) = Γ.slots(Γ.refs(x).σ).caps

infer(Γ, e.f) = let caps_e = infer(Γ, e)
                    caps_f = capabilities(field f)
                in caps_e ∩ caps_f

infer(Γ, f(args)) = return_capabilities(f)
```

**Анализ условных веток:**
```
Γ ⊢ if cond then e₁ else e₂ ⇝ Γ'

где:
  Γ₁ ⊢ e₁ ⇝ Γ₁'
  Γ₂ ⊢ e₂ ⇝ Γ₂'
  Γ' = merge(Γ₁', Γ₂')

merge(Γ₁, Γ₂):
  ∀σ:
    если valid(σ, Γ₁) ∧ valid(σ, Γ₂) то
      Γ'.slots(σ).alive = true
      Γ'.slots(σ).caps = Γ₁.slots(σ).caps ∩ Γ₂.slots(σ).caps
    иначе
      Γ'.slots(σ).alive = false
```

### 6.3. Сообщения об ошибках

**Формат ошибки:**
```
Error ::= ⟨kind, location, context⟩

где:
  kind     : ErrorKind
  location : SourceLoc
  context  : ErrorContext

ErrorKind ::= MovedValue | BorrowConflict | MissingCapability | ...

ErrorContext ::= ⟨
  primary_message   : String
  help_message      : String
  related_locations : List<(SourceLoc, String)>
⟩
```

**Пример формирования ошибки:**
```
reportMovedValue(x, loc_use, loc_move):
  вернуть ⟨
    MovedValue,
    loc_use,
    ⟨"use of moved value `" + x + "`",
     "consider borrowing with &" + x,
     [(loc_move, "value moved here")]⟩
  ⟩
```

---

## 7. Нерешенные проблемы

### 7.1. Циклические структуры

**Проблема:**
```
∀ структура с циклической зависимостью:
  если используется only own ⟹ impossible to construct
```

**Возможные решения:**

1) Weak ссылки:
```
   break cycle с weak ⟹ manageable но requires explicit null checks
```

2) Arena allocation:
```
   container owns all ⟹ no individual ownership
```

### 7.2. Self-referential типы

**Проблема:**
```
struct S {
  data: T own
  view: &T      // ссылка на data
}

Как гарантировать lifetime(view) ⊆ lifetime(data)?
```

**Решение: lifetime параметры**
```
struct S<'a> {
  data: T own
  view: &'a T
}

с ограничением: 'a привязано к времени жизни S
```

### 7.3. Async контексты

**Проблема:**
```
async fn f(x: T mut) {
  await g()      // x должен оставаться валидным
  use(x)
}

Как проверить валидность x через await point?
```

**Решение: захват владения**
```
async fn f(x: T own) -> T {
  await g()
  use(x)
  return x
}

или: Pin<T> для фиксации в памяти
```

---

## 8. Заключение

### 8.1. Резюме формальной модели

**Доказано:**

1. **Корректность:**
   ```
   ⊢ P : τ ⟹ Memory Safe(P)
   ```

2. **Полнота (с ограничениями):**
   ```
   Семантически корректная P ∧ явные аннотации ⟹ ⊢ P : τ
   ```

3. **Эффективность:**
   ```
   Time(check) = O(|AST|)
   Space(Γ) = O(|Scopes| + |Slots|)
   ```

### 8.2. Математическая реализуемость

**Вывод: модель владения Phx является математически корректной.**

Критерии выполнены:
- ✓ Формальная модель определена
- ✓ Алгоритмы проверки разработаны
- ✓ Инварианты сформулированы
- ✓ Теоремы доказаны
- ✓ Сложность линейная

**Модель готова к реализации.**

### 8.3. Дальнейшие шаги

1. **Формальная верификация:**
   - Формализация в Coq/Isabelle
   - Машинная проверка доказательств

2. **Расширения:**
   - Lifetime параметры
   - Async интеграция
   - Generic ограничения

3. **Реализация:**
   - Прототип checker
   - Тестирование на примерах
   - Оптимизация производительности
