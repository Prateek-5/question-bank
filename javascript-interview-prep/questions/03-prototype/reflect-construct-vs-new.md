# `Reflect.construct` vs `new`

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [polyfill-new.md](./polyfill-new.md), [extends-super-implementation.md](./extends-super-implementation.md)
>
> **Source:** ES2015 Reflect API. Framework-internals interview.

---

## 1. Problem statement

`new C(...args)` is sugar; `Reflect.construct(C, args, newTarget?)` is the underlying primitive. The third arg lets you control which class's prototype is installed.

**Verification examples**

```js
class A { constructor() { this.fromA = true; } }
class B {}

// Same as new A()
Reflect.construct(A, []);                                                // A instance

// Run A's constructor, but install B.prototype
const b = Reflect.construct(A, [], B);
b.fromA;                                                                  // true (A's body ran)
b instanceof B;                                                           // true
b instanceof A;                                                           // false

// Required for built-in subclassing
class MyArr {
  constructor() { return Reflect.construct(Array, arguments, MyArr); }
}
```

**Constraints**
- Third arg `newTarget` (default = first arg).
- Inside constructor, `new.target === newTarget`.
- Required for `class extends Array/Error/Map` to work correctly.

---

## 2. Plain-English restatement

`Reflect.construct(C, args)` is just `new C(...args)`. The killer feature is the third argument — `newTarget` — which tells the engine "use THIS class's prototype, even though you're running THAT constructor." That's how `extends Array` actually works internally.

---

## 3. Why this matters in interviews

Built-in subclassing literacy + `new.target` understanding.

---

## 4. Mental model

```
   new C(...args)        = Reflect.construct(C, args, C)
   Reflect.construct(C, args, NT)  = run C body; obj.[[Prototype]] = NT.prototype
   
   new.target inside constructor:
     new C(...)                 → new.target = C
     Reflect.construct(C, [], NT) → new.target = NT
   
   Why needed:
   - Subclassing Array/Error/Map: parent.call(this) fails (they ignore this).
   - parent must construct obj; new.target tells parent which prototype to use.
   
   class MyArr extends Array {} desugars to:
     constructor() { super(); }
   super() under the hood = Reflect.construct(Array, args, new.target).
   new.target = MyArr → obj.[[Prototype]] = MyArr.prototype.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's `Reflect.construct(A, [], B)` — A's body or B's?
> 2. Why does `class MyArr extends Array {}` need `Reflect.construct`?
> 3. What's `new.target` inside a constructor?

---

## 6. Brute force — walked through

### Wrong attempt 1: `new C(...args)` always works
Fails for built-in subclassing (Array, Error, Map ignore `this`).

### Wrong attempt 2: ignore `newTarget` arg
Misses the headline feature.

### Wrong attempt 3: `Parent.call(this)` for built-ins
Returns Parent's own internals (not your subclass).

---

## 7. The unlocking insight

> **`Reflect.construct(C, args, NT)` runs C's body but installs NT.prototype. Required for built-in subclassing. `new C(...args) ≡ Reflect.construct(C, args, C)`. Inside constructor, `new.target = newTarget`.**

Three properties:

1. **`Reflect.construct` is the primitive** — `new` is sugar.
2. **`newTarget` controls prototype** — independent of which constructor runs.
3. **`new.target`** reflects newTarget inside body.

---

## 8. Solution (annotated)

```js
class A {
  constructor() { this.fromA = true; }
}
class B {}

const a1 = new A();
const a2 = Reflect.construct(A, []);                                    // step 1: same as new
a2 instanceof A;                                                         // true

// newTarget different from constructor
const b = Reflect.construct(A, [], B);                                   // step 2: A body + B prototype
b.fromA;                                                                 // true (A's constructor body ran)
b instanceof B;                                                          // true (B.prototype installed)
b instanceof A;                                                          // false (NOT A.prototype)

// Subclassing Array correctly
class MyArr extends Array {
  // class syntax handles Reflect.construct internally
  customMethod() { return 'hi'; }
}
const arr = new MyArr(1, 2, 3);
arr.length;                                                              // 3
arr instanceof MyArr;                                                    // true
arr instanceof Array;                                                    // true
arr.customMethod();                                                      // 'hi'

// Manual subclassing without class syntax
function MyError(msg) {
  const instance = Reflect.construct(Error, [msg], MyError);             // step 3: built-in
  Object.setPrototypeOf(instance, MyError.prototype);
  return instance;
}
Object.setPrototypeOf(MyError.prototype, Error.prototype);
Object.setPrototypeOf(MyError, Error);

const e = new MyError('boom');
e instanceof MyError;                                                    // true
e instanceof Error;                                                      // true
e.message;                                                                // 'boom'
e.stack;                                                                  // includes stack trace
```

---

## 9. Step-by-step dry run

```
new A():
  Internally: Reflect.construct(A, [], A).
  Create obj. obj.[[Prototype]] = A.prototype.
  Run A body with this=obj, new.target=A.
  Return obj.

Reflect.construct(A, [], B):
  Create obj. obj.[[Prototype]] = B.prototype.   ← KEY DIFFERENCE
  Run A body with this=obj, new.target=B.        ← new.target = B
  obj.fromA = true (A's body did this).
  Return obj.
  
  Result: object with B.prototype chain that had A's constructor body run on it.

class MyArr extends Array {}:
  Desugars to:
    constructor() {
      // super() → Reflect.construct(Array, arguments, new.target)
      // new.target = MyArr (because we did `new MyArr()`)
      // obj.[[Prototype]] = MyArr.prototype.
    }
  
  new MyArr(1,2,3) works because Array constructor sees new.target = MyArr
    and installs MyArr.prototype on the new array.
```

---

## 10. Common confusion + traps

1. **`new C ≡ Reflect.construct(C, args)`** — same.
2. **`newTarget` defaults to constructor** — provide explicitly to override.
3. **Built-in subclassing without Reflect** — fails.
4. **`Parent.call(this)`** vs `Reflect.construct(Parent, args, new.target)` — first fails for built-ins.
5. **`new.target` is constructor** — actually is `newTarget` passed in.
6. **Inside arrow function** — no `new.target`.
7. **`Reflect.construct(null)`** — TypeError; first arg must be constructor.

---

## 11. Senior follow-ups & variants

### Variant 1 — Abstract class enforcement
`if (new.target === AbstractClass) throw new Error('Abstract');`.

### Variant 2 — Factory returns different prototype
`Reflect.construct(C, args, OtherClass)` for unusual factory patterns.

### Variant 3 — Polyfill `new`
`Reflect.construct` is the spec-complete primitive.

### Variant 4 — `super()` desugar
Uses `Reflect.construct(Parent, args, new.target)` internally.

### Variant 5 — `Date` returns string without `new`
`Date()` returns string; `new Date()` returns Date. Checks `new.target`.

---

## 12. How to think aloud

> "`new C(...args)` is syntactic sugar for `Reflect.construct(C, args, C)`. The killer feature of Reflect.construct is the THIRD argument — `newTarget` — which lets you run one constructor's body but install a DIFFERENT class's prototype on the resulting object. Inside the constructor, `new.target` reflects the newTarget. Required for: subclassing built-ins (Array, Error, Map — they ignore `this` in normal calls; you need `Reflect.construct(Array, args, new.target)` to get a new array with the SUBCLASS's prototype). `class extends Array {}` works because the engine implicitly uses Reflect.construct under the hood. For manual built-in subclassing without class syntax, do `Reflect.construct(Error, [msg], MyError)` then `setPrototypeOf` to wire chains. Trap: built-in subclassing without Reflect (fails); confusing `new.target` with `this`."

---

## 13. 60-second revision

> - **`new C(args) ≡ Reflect.construct(C, args, C)`**.
> - **3rd arg `newTarget`** controls which prototype is installed.
> - **`new.target` inside** body = newTarget.
> - **Required for built-in subclassing** (Array, Error, Map).
> - **`class extends Array {}`** uses Reflect.construct internally.
> - **Abstract enforcement:** `if (new.target === Abstract) throw`.
> - **Without `new`** (`Date()`) → no new.target.
> - **Trap:** built-in subclass via `Parent.call(this)`; ignoring newTarget.

---

**Related:** [polyfill-new.md](./polyfill-new.md) · [extends-super-implementation.md](./extends-super-implementation.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
