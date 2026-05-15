# Prototype Chain & Inheritance in JavaScript

## Source
- codedamn "JavaScript prototype chain inheritance": https://codedamn.com/news/programming/javascript-prototype-chain-inheritance
- Canonical interview question — asked at literally every JS-flavored backend round (Razorpay, Atlassian, Microsoft, Booking).

## Why this question matters in interviews
This is the **single most fundamental conceptual question in JavaScript**. Everything else — `this`, `class`, polyfilling `bind`/`new`, why `instanceof` works, why `Array.prototype.last` exists at all — depends on you having a crisp mental model of `prototype`, `__proto__`, and `Object.getPrototypeOf`. Senior interviewers use it as a filter: if you can't draw the chain on a whiteboard in under 60 seconds, they will downgrade you. Backend engineers who came from Python or Java often have this fuzzy — drilling it is non-negotiable.

## Concepts involved

### The three names you must distinguish
| Name | Belongs to | Purpose |
|---|---|---|
| `Foo.prototype` | a **function** (constructor) | the object that *future instances will inherit from* |
| `instance.__proto__` | an **instance** (deprecated accessor) | the link back to `Foo.prototype` |
| `Object.getPrototypeOf(instance)` | modern API | same link, official way to read it |

Mantra: **constructors carry `.prototype`; instances point to it via `__proto__` / `getPrototypeOf`.** They are the *same* object, accessed two ways.

### Syntax to lock in
```js
// ES5-style constructor
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return this.name + ' makes a sound'; };

const a = new Animal('cat');
a.speak();                                    // 'cat makes a sound'
Object.getPrototypeOf(a) === Animal.prototype; // true
a.__proto__ === Animal.prototype;              // true (deprecated accessor)
a.constructor === Animal;                      // true (inherited via prototype)

// ES6 class — pure syntactic sugar over the above
class Dog extends Animal {
  bark() { return this.name + ' woofs'; }
}
const d = new Dog('rex');
Object.getPrototypeOf(d) === Dog.prototype;             // true
Object.getPrototypeOf(Dog.prototype) === Animal.prototype; // true (extends)
```

### The chain (memorize this picture)
```
d ──▶ Dog.prototype ──▶ Animal.prototype ──▶ Object.prototype ──▶ null
   instance       inherits           inherits             chain root
```
Property lookup walks left-to-right; the first match wins. `null` ends the chain — accessing any property of a value whose prototype is `null` (e.g. `Object.create(null)`) skips `Object.prototype` entirely.

### Runtime / engine behavior
- `new Foo()` does four things: (1) creates a new object `obj`, (2) sets `Object.getPrototypeOf(obj) = Foo.prototype`, (3) calls `Foo.apply(obj, arguments)`, (4) returns `obj` unless `Foo` itself returned an object.
- `instanceof Foo` walks the prototype chain of the LHS asking "is `Foo.prototype` anywhere on it?" — not a class check, a chain check.
- `extends Base` in `class` does **two** links: `Sub.prototype.__proto__ = Base.prototype` (instance methods chain), AND `Sub.__proto__ = Base` (static methods chain).
- `class` declarations are not hoisted in a usable way — they sit in the TDZ until evaluated, unlike `function` constructors.

### Edge cases (interview traps)
1. **`Array` literal's chain** — `[].__proto__ === Array.prototype`, then `Array.prototype.__proto__ === Object.prototype`. Two hops, not one.
2. **`Object.create(proto)`** — direct way to set a prototype without a constructor. `Object.create(null)` produces a "dictionary object" with no `__proto__`, `toString`, etc. — used by V8-friendly hash maps.
3. **Shadowing** — defining `a.speak = ...` on the instance does **not** mutate `Animal.prototype.speak`; it creates an own property that masks the prototype one.
4. **`hasOwnProperty`** — only checks own props, not inherited. Use to distinguish.
5. **`for...in` walks the chain** — includes enumerable inherited keys; that's why `Object.keys` is preferred.
6. **`constructor` is on the prototype** — `instance.constructor` is found via the chain at `Foo.prototype.constructor`. If you overwrite `Foo.prototype = {...}` you LOSE this link unless you re-set `.constructor = Foo`.
7. **Arrow functions have no `prototype`** — `(()=>{}).prototype === undefined`. Hence `new (()=>{})()` throws.
8. **`class` methods are non-enumerable** by default; methods you add as `Foo.prototype.x = ...` are enumerable. Explains `for...in` discrepancies.

## Brute force approach
"Copy parent properties into child via `Object.assign`." That gives you a flat snapshot, not live inheritance: a later change to the parent doesn't propagate, and `instanceof` lies. Drop it.

## Optimal approach
Use the **prototype chain** for shared behavior; use **own properties** for per-instance state. Two equivalent dialects:

- **ES5 dialect** — set `Child.prototype = Object.create(Parent.prototype)`, then `Child.prototype.constructor = Child`. Inside `Child`, call `Parent.call(this, ...)` to inherit instance state.
- **ES6 class dialect** — `class Child extends Parent { constructor(...){ super(...); } }`. Compiles to the above.

Both produce identical chains. Pick `class` in modern code, but **be able to write the ES5 form on demand** — interviewers ask precisely because it forces you to show you understand the mechanics.

## Solution (JavaScript)

```js
// ─── ES5 dialect: do it by hand, every wire visible ──────────────────────
function Animal(name) {
  this.name = name;          // own property — per-instance state
}
Animal.prototype.speak = function () {
  return `${this.name} makes a sound`;
};

function Dog(name, breed) {
  Animal.call(this, name);   // 1. inherit instance state (super(...))
  this.breed = breed;
}
// 2. inherit prototype methods. Object.create makes a new object whose
//    __proto__ is Animal.prototype WITHOUT calling Animal as a constructor.
Dog.prototype = Object.create(Animal.prototype);
// 3. restore .constructor (Object.create wiped it out)
Dog.prototype.constructor = Dog;
// 4. add Dog-specific methods AFTER the prototype reassignment
Dog.prototype.bark = function () {
  return `${this.name} woofs`;
};

const d = new Dog('rex', 'lab');
d.speak();                                   // 'rex makes a sound'   (inherited)
d.bark();                                    // 'rex woofs'           (own proto)
d instanceof Dog;                            // true
d instanceof Animal;                         // true   ← chain walk found Animal.prototype
d instanceof Object;                         // true   ← chain ultimately reaches Object.prototype
Object.getPrototypeOf(d) === Dog.prototype;            // true
Object.getPrototypeOf(Dog.prototype) === Animal.prototype; // true

// ─── ES6 class dialect: same machine, sugar syntax ───────────────────────
class Animal2 {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
}
class Dog2 extends Animal2 {
  constructor(name, breed) {
    super(name);              // === Animal2.call(this, name)
    this.breed = breed;
  }
  bark() { return `${this.name} woofs`; }
}
```

## Step-by-step dry run

Take `d.bark()` and trace the property lookup, then `d.speak()`:

```
d  =  { name: 'rex', breed: 'lab' }
        │
        ▼ Object.getPrototypeOf(d)
Dog.prototype  =  { bark, constructor: Dog }
        │
        ▼ Object.getPrototypeOf(Dog.prototype)
Animal.prototype  =  { speak, constructor: Animal }   ← actually .constructor was overwritten on Dog.prototype
        │
        ▼
Object.prototype  =  { toString, hasOwnProperty, ... }
        │
        ▼
null
```

1. `d.bark()` — engine asks `d` for own `bark`. **No.** Walk to `Dog.prototype`. **Found.** Call with `this = d`. Returns `'rex woofs'`.
2. `d.speak()` — engine asks `d` for own `speak`. **No.** Walk to `Dog.prototype`. **No.** Walk to `Animal.prototype`. **Found.** Call with `this = d`. Returns `'rex makes a sound'`.
3. `d.toString()` — walks all the way to `Object.prototype`. Found there. Returns `'[object Object]'`.
4. `d.zzz` — walks to `null`, returns `undefined` (does NOT throw).

Now check `instanceof`:
- `d instanceof Animal` ⇒ walk `Object.getPrototypeOf(d)`, `Object.getPrototypeOf(Dog.prototype)`, ... — does any equal `Animal.prototype`? **Yes**, at hop 2. Return `true`.

## Important takeaways

**Syntax to memorize**
- `Object.create(proto)` — make a new object with `proto` as its prototype, *without* running a constructor.
- `Child.prototype = Object.create(Parent.prototype); Child.prototype.constructor = Child;` — the two-line ES5 inheritance setup. The second line is the one everyone forgets.
- `super(...)` ≡ `Parent.call(this, ...)` inside an ES6 class constructor.

**Patterns to reuse**
- Sharing methods → put on `prototype`. Per-instance data → assign in constructor.
- For library code, prefer `Object.create(null)` for hash-maps to avoid `__proto__` / `toString` collisions with user keys.
- `class` is the right default; ES5 form is the right *exam answer*.

**Common mistakes**
- Setting `Child.prototype = Parent.prototype` directly. Now mutating `Child.prototype` mutates `Parent.prototype` — shared instance. Use `Object.create` to break the link.
- Forgetting `Child.prototype.constructor = Child` after `Object.create`. `new instance.constructor()` will now construct a `Parent`.
- Trying to use `new` with arrow functions or methods defined with `{ foo() {} }` shorthand on a plain object (those have no `[[Construct]]`).
- Confusing `Foo.prototype` (the parent-to-be) with `Foo.__proto__` (Foo's *own* prototype, which is `Function.prototype`).

**Why interviewers ask this**
- One question reveals whether you understand JS object model, `this`, `new`, `instanceof`, `class` desugar, and Node's module objects — all of which rest on this single chain idea.

## Variants

1. **Implement `instanceof`** — write `myInstanceof(obj, Ctor)`: walk `Object.getPrototypeOf(obj)` until you hit `Ctor.prototype` or `null`. ~6 lines.
2. **Implement `Object.create(proto)`** — `function fakeCreate(p){ function F(){}; F.prototype=p; return new F(); }` (the classic "Crockford pattern" before `Object.create` was standard).
3. **Mixin pattern** — combine multiple objects' methods onto one prototype without single-parent chains (`Object.assign(Target.prototype, Mixin1, Mixin2)`).
4. **Static methods** — `class Foo { static bar(){} }` puts `bar` on `Foo` itself, not on `Foo.prototype`. `Foo.bar()` works; `new Foo().bar()` does not. Be ready to draw both chains (instance chain + constructor chain).
5. **`Object.create(null)`** — explain when you'd use it (safe maps, V8-friendly dictionaries).

## Revision notes

> **Prototype chain — 60 second recap**
> - Three names: `Foo.prototype` (on the constructor), `instance.__proto__` (deprecated), `Object.getPrototypeOf(instance)` (modern). Last two point to the first.
> - Lookup walks instance → its proto → its proto's proto → … → `null`. First match wins.
> - `new Foo()` = create obj, set proto to `Foo.prototype`, run `Foo.apply(obj, args)`, return obj (unless constructor returned object).
> - ES5 inherit: `Child.prototype = Object.create(Parent.prototype); Child.prototype.constructor = Child;` + `Parent.call(this, ...)` inside `Child`.
> - `class Child extends Parent` is sugar over the above; also wires static-method chain `Sub.__proto__ = Base`.
> - `instanceof` = "is `Ctor.prototype` anywhere on LHS's chain?"
> - `Object.create(null)` makes a prototype-less object — safe map / dict.
> - Arrow functions have no `.prototype`, can't be `new`-ed.
> - **Trap:** `Child.prototype = Parent.prototype` (aliases, not inherits). Use `Object.create`.
> - **Trap:** forgetting to re-set `constructor` after reassigning prototype.
