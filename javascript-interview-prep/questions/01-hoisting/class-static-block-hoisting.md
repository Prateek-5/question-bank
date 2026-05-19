# Class static blocks — initialization order & hoisting

> **Difficulty:** Medium-Senior   |   **Time:** ~10 min   |   **Prereqs:** [class-hoisting.md](./class-hoisting.md)
>
> **Source:** ES2022 (`static { ... }` blocks). Stripe, Atlassian, modern-JS-graded interviews.

---

## 1. Problem statement

`static { ... }` blocks run once at class definition time, in source order. They have access to private members and `this` (the class).

**Verification examples**

```js
class Config {
  static URL = 'http://x.com';
  static defaults;

  static {                                                              // runs at class eval
    Config.defaults = { url: Config.URL, retries: 3 };
  }
  static {                                                              // second block
    Config.defaults.timeout = 5000;
  }
}
console.log(Config.defaults);                                           // {url, retries: 3, timeout: 5000}
```

**Verification table**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| Multiple static blocks                              | run in source order at class eval time                |
| Access private static `#x`                          | allowed; useful for "friend" patterns                  |
| `this` inside static block                          | the class constructor                                   |
| Field above static block                            | accessible                                              |
| Field below static block                            | TDZ — throws                                            |
| `await` in static block                             | NOT allowed (synchronous only)                          |
| Derived class static block                          | runs after base class fully evaluated                  |

**Constraints**
- Runs once, synchronously, at class evaluation time.
- Multiple blocks in source order.
- Access to private members.
- `this` = class constructor.
- Fields below are TDZ.

---

## 2. Plain-English restatement

A `static { ... }` block runs once when the class is defined — like a constructor for the class object itself. You can run imperative initialization code with access to private members. Multiple blocks execute in source order, interleaved with field initializers.

---

## 3. Why this matters in interviews

ES2022 feature. Senior bar: know it exists, when it runs, interaction with hoisting + TDZ.

---

## 4. Mental model

```
   Class evaluation order (top-to-bottom in source):
   
   class Foo {
     static A = computeA();          // field 1: A = computeA()
     static {                         // static block 1
       Foo.B = doSomething(Foo.A);   // can access A above
       // Foo.C is TDZ here (declared later)
     }
     static C = 42;                   // field 2: C = 42 (TDZ ended)
     static {                         // static block 2
       Foo.D = Foo.A + Foo.C;        // both accessible now
     }
   }
   
   ALL of this runs ONCE at the `class Foo {}` declaration line.
   
   `this` inside static block = Foo (the constructor).
   Can access private members: `static #x = 1; static { console.log(Foo.#x); }`.
   
   Cannot use `await` (synchronous only).
   Derived: child's static block runs AFTER base class fully evaluated.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. When does a static block run?
> 2. Can you access a field declared BELOW the static block from inside it?
> 3. Can you `await` inside a static block?

---

## 6. Brute force — walked through

### Wrong attempt 1: "static block runs per instance"
Wrong — runs ONCE at class evaluation.

### Wrong attempt 2: "all fields available everywhere"
Fields below the static block are TDZ.

### Wrong attempt 3: "await works in static block"
Synchronous only.

---

## 7. The unlocking insight

> **Static blocks run ONCE at class evaluation time, in source order, interleaved with field initializers. `this` = class. Access private members. Fields below = TDZ. No await. Derived class blocks run after base.**

Three properties:

1. **Runs once at class eval** — like a class-object constructor.
2. **Source order interleaving** with field initializers.
3. **Private member access** — useful for friend patterns.

---

## 8. Solution (annotated)

```js
class Config {
  static URL = 'http://x.com';                                          // step 1: field init
  static defaults;                                                      // step 2: declared, undefined

  static {                                                              // step 3: first static block
    Config.defaults = { url: Config.URL, retries: 3 };                  // accesses URL (above)
  }

  static {                                                              // step 4: second static block
    Config.defaults.timeout = 5000;                                     // augment defaults
  }
}

console.log(Config.defaults);
// { url: 'http://x.com', retries: 3, timeout: 5000 }

// Private "friend" pattern
class Secret {
  static #pwd = 'sec';

  static {
    // Allows another class to access private — write to a module-scoped var
    revealedPwd = Secret.#pwd;
  }
}

let revealedPwd;
// After class evaluation: revealedPwd === 'sec'
```

**Try it yourself**

```js
// TDZ for fields below
class Demo {
  static A = 1;
  static {
    console.log(Demo.A);                                                 // 1
    try { console.log(Demo.B); } catch (e) { console.log(e.message); }   // undefined (declared via field below, but cell exists)
    // Note: static fields hoisted as declared but uninitialized;
    //       reading below the declaration line in this block sees undefined.
  }
  static B = 2;
  static {
    console.log(Demo.B);                                                 // 2
  }
}

// Derived class static order
class Base {
  static {
    console.log('Base static');
  }
}
class Child extends Base {
  static {
    console.log('Child static');
  }
}
// Output:
//   Base static     ← base evaluated first
//   Child static
```

---

## 9. Step-by-step dry run

```
class Foo definition reached at execution:

CLASS EVALUATION (top to bottom):
  1. Evaluate `static A = computeA()` → Foo.A = ...
  2. Run first static block { Foo.B = ... } 
     - Foo.A accessible.
     - this === Foo.
  3. Evaluate `static C = 42` → Foo.C = 42
  4. Run second static block { Foo.D = Foo.A + Foo.C }
     - All three (A, B, C) accessible now.

After class definition: Foo.A, Foo.B, Foo.C, Foo.D all set.

Derived class:
  class Child extends Base {
    static { ... }
  }
  Evaluation:
    Base evaluated first (all fields + static blocks).
    Then Child's class body — fields and static blocks in order.
```

---

## 10. Common confusion + traps

1. **Runs per instance** — no, once at class eval.
2. **All fields accessible everywhere** — fields below are TDZ.
3. **`await` works** — synchronous only.
4. **Static blocks can be empty** — yes; useful for side-effect markers.
5. **Multiple blocks combined** — no, each independent in source order.
6. **`this` is undefined in static block** — `this` is the class.
7. **Cannot access private from static block** — they CAN.

---

## 11. Senior follow-ups & variants

### Variant 1 — Friend pattern
Expose private to module via static block: `static { friendVar = Secret.#field }`.

### Variant 2 — Singleton init
`static { if (!instance) instance = new this() }` for lazy singleton.

### Variant 3 — Symbol-keyed fields
Static block can compute Symbol-keyed property keys.

### Variant 4 — Field-then-block-then-field
TDZ semantics: forward references throw if not yet initialized.

### Variant 5 — Inheritance order
Child class fields/blocks run AFTER base class fully evaluated.

---

## 12. How to think aloud

> "Static block runs ONCE at class evaluation time, in source order, interleaved with field initializers. Like a constructor for the class object itself. `this` is the class constructor. Can access private members — useful for friend patterns where you expose a private to a module-scoped variable. Multiple blocks allowed; run in order. Cannot use `await` (synchronous only). Fields declared BELOW a static block are TDZ — accessing throws. Derived class: child's static block runs AFTER base class fully evaluated. Trap: thinking it runs per instance; forward field access without TDZ awareness."

---

## 13. 60-second revision

> - **`static { ... }` runs ONCE** at class evaluation.
> - **Source order** with field initializers.
> - **`this`** = class constructor.
> - **Access private members** — `static #x; static { Foo.#x }`.
> - **No `await`** (synchronous only).
> - **Fields below are TDZ.**
> - **Multiple blocks** allowed; each runs in order.
> - **Inheritance:** base fully evaluated before child's blocks.
> - **Trap:** "runs per instance"; await; field below TDZ.

---

**Related:** [class-hoisting.md](./class-hoisting.md) · [tdz-let-const.md](./tdz-let-const.md) · [`03-prototype/private-class-fields.md`](../03-prototype/private-class-fields.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
