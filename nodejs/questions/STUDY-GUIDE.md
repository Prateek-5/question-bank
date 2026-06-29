# Node.js & JavaScript Interview Prep — Mentor's Study Guide

> A concept-first companion to the 102 Codedamn Node.js labs in this folder.
> Instead of 102 isolated answers, the labs are grouped by the **fundamental being tested**. For each group you get: the core idea (explained as a mentor would), how it connects to the JS engine / Node runtime, a table mapping every lab to *what it's really testing once you strip the lab boilerplate*, common interview questions, and the gotchas that trip people up.

**How to use this guide**
- Each lab's wording is padded with "export using ESM syntax", "the tests will verify…", "create index.js" — that's **clutter**. The *Decluttered ask* column tells you the one concept the lab actually probes.
- Read a chapter, then open the matching lab files (e.g. `029-iteration-protocols-in-javascript.md`) and try to solve from the decluttered ask alone.
- The 🎯 **Interview-grade questions** are the version of each topic an interviewer actually asks.

---

## Table of contents

1. [The mental model: JS engine + Node runtime](#1-the-mental-model)
2. [Variables, types & coercion](#2-variables-types--coercion)
3. [Functions, scope & closures](#3-functions-scope--closures)
4. [Objects, prototypes & OOP](#4-objects-prototypes--oop)
5. [Meta-programming: Proxy, Reflect, Symbols, descriptors](#5-meta-programming)
6. [Iteration protocols & generators](#6-iteration-protocols--generators)
7. [Collections & memory: Map, Set, typed arrays](#7-collections--memory)
8. [Asynchronous JavaScript & the event loop](#8-asynchronous-javascript--the-event-loop)
9. [Modules: CommonJS vs ES Modules](#9-modules-commonjs-vs-es-modules)
10. [Node.js core modules (fs, os, path, http, crypto, process, child_process)](#10-nodejs-core-modules)
11. [Errors, debugging & robustness](#11-errors-debugging--robustness)
12. [Algorithms, complexity & functional array methods](#12-algorithms-complexity--functional-array-methods)
13. [Rapid-fire interview checklist](#13-rapid-fire-interview-checklist)

---

## 1. The mental model

Before any specific topic, internalize the layered picture — almost every Node interview circles back to it.

```
Your JS  ─▶  V8 engine (parses, JITs, runs JS; owns the heap + call stack)
              │
              ├─ no setTimeout, no fs, no http here — those are NOT JavaScript
              │
Node.js   ─▶  libuv (event loop + thread pool) + C++ bindings
              └─ provides: timers, fs, net/http, crypto, DNS, streams, process
```

- **JavaScript the language** (ECMAScript) gives you: types, functions, objects, prototypes, closures, Promises, iterators, `Symbol`, `Proxy`. This is what runs in a browser too.
- **Node.js the runtime** wraps V8 and adds the things a server needs: file system, OS access, networking, child processes, crypto — implemented in C/C++ and exposed as **core modules**.
- The **event loop** lives in libuv, not V8. It's what lets single-threaded JS handle thousands of concurrent I/O operations.

> 🎯 **Interview-grade:** "Is Node.js single-threaded?" — *The JavaScript you write runs on one thread (one call stack). But Node delegates I/O to libuv, which uses a thread pool and OS async primitives. So your code is single-threaded; the runtime around it is not.*

The 102 labs split cleanly into **language fundamentals** (chapters 2–9, 11–12) and **Node runtime APIs** (chapter 10). Interviewers test both, but weight the language fundamentals more heavily — a shaky grasp of closures or the prototype chain is a red flag; forgetting a `fs` method name is not.

---

## 2. Variables, types & coercion

**The fundamental.** JavaScript has 7 primitives (`number`, `string`, `boolean`, `null`, `undefined`, `symbol`, `bigint`) and everything else is an `object` (arrays, functions, dates included). Primitives are immutable and copied by value; objects are copied by reference. Coercion is JS converting a value from one type to another, either *implicitly* (`1 + "2"` → `"12"`) or *explicitly* (`Number("2")`).

**Why it matters in Node.** Config values from `process.env` are **always strings** — `process.env.PORT` is `"3000"`, not `3000`. Forgetting to coerce is a real-world bug, not a toy one.

| Lab | Decluttered ask |
|----|------------------|
| 42 Create Simple Variables | Declare values of each primitive type + an array; know `typeof` for each. |
| 90 Numbers Lab | Numeric variables + a runtime `add` function — `number` is always IEEE-754 double. |
| 86 Type Coercion Lab | Convert deliberately between number/string/boolean — `String()`, `Number()`, `Boolean()`. |
| 39 Custom Add Function | Branch on `typeof a === typeof b`; numbers add, strings concat, booleans → numbers. Throw on mismatch. |
| 8 / 31 Date | `new Date()`, `.getDay()` → 0–6, formatting. Dates are objects, not primitives. |
| 58 Math Object | `Math.PI`, `Math.pow` — `Math` is a namespace object, not a constructor (no `new Math()`). |
| 37 / 38 Strings | `toUpperCase`, `replace`, `slice` — strings are immutable; every method returns a *new* string. |
| 26 Regex | A pattern (`/.../`) + `.test()` for email validation. `RegExp` is an object. |
| 94 Query Parameters | Parse a URL query string into an object — use the `URL`/`URLSearchParams` Web API. |

**Gotchas interviewers love**
- `typeof null === "object"` (a historic bug, kept for compatibility).
- `typeof NaN === "number"`, and `NaN !== NaN` — test with `Number.isNaN()`.
- `0.1 + 0.2 !== 0.3` — floating point. Know *why* (binary can't represent 0.1 exactly).
- `[] == false` is `true`, `[] === false` is `false`. **Rule:** never use `==`; use `===` and coerce explicitly. Explain the abstract-equality algorithm if pushed.
- `"5" - 1 === 4` but `"5" + 1 === "51"` — `-` coerces to number, `+` prefers string concat.

> 🎯 **Interview-grade:** "What's the difference between `==` and `===`?" and "Walk me through what `[] + {}` evaluates to and why." (Answer: `"[object Object]"` — both operands coerce to primitives via `toString`.)

---

## 3. Functions, scope & closures

**The fundamental.** Functions are **first-class values** — you can store them in variables, pass them as arguments, and return them. A **closure** is a function bundled with the lexical environment it was defined in: it "remembers" variables from its birthplace even after that outer function has returned. **Scope** is resolved *lexically* (by where code is written), determined at author time, not call time.

| Lab | Decluttered ask |
|----|------------------|
| 25 Functions Lab | Named, arrow, and higher-order functions in one place. |
| 30 / 59 Arrow Functions | Concise syntax **and** lexical `this` (arrows have no own `this`/`arguments`). |
| 40 / 61 Function Expressions | Assign a function to a variable; named function expressions; default-export one. |
| 92 Function Methods | Two functions, one named + one default export. (Despite the title, it's about exports, not `call`/`apply`/`bind`.) |
| 20 Rest Parameters | `function sum(...nums)` — collects args into a *real array*. |
| 7 Spread Operator | `...` to expand: `Math.max(...arr)`, merge arrays/objects, clone. Same syntax as rest, opposite direction. |
| 91 Default Parameters | `function greet(name, greeting = "Hello")` — defaults fill in for `undefined`. |
| 80 Higher-order Functions | Functions that take/return functions — `map`/`filter`/`reduce` family. |
| 46 Lodash `_.over` | Build a function that runs N functions over the same args → array of results. Function composition. |
| 63 Dynamic Scope | Show a function reading a *global* + a parameter — contrast with lexical scope. |
| 55 Recursion | `factorial(n)` — a function calling itself with a base case. |
| 102 Memoization | A cache (closure over a `Map`/object) wrapping fib — the canonical closure interview question. |

**Rest vs spread (lab 20 vs 7) — the classic trap.** Same `...` token, mirror-image jobs:
```js
function sum(...nums) {}      // REST: many args  → one array  (in a definition)
sum(...[1, 2, 3]);            // SPREAD: one array → many args  (in a call)
```

**`this` is the #1 source of bugs.** It is set by **how a function is called**, not where it's defined — *except* arrow functions, which capture `this` lexically.
```js
const obj = {
  name: "A",
  regular() { return this.name; },        // `this` = obj  (called as obj.regular())
  arrow:  () => this.name,                 // `this` = enclosing scope, NOT obj
};
```

> 🎯 **Interview-grade**
> - "What is a closure? Give a real use." → memoization (lab 102), data privacy, event handlers, `once()`.
> - "Why does `setTimeout` in a `for (var i…)` loop print the same number? Fix it." → `var` is function-scoped; one shared binding. Fix with `let` (block-scoped, new binding per iteration) or an IIFE.
> - "Difference between arrow and regular functions?" → `this`, `arguments`, can't be `new`-ed, no `prototype`.
> - Implement `memoize(fn)` generically — they want a closure over a cache keyed by `JSON.stringify(args)`.

---

## 4. Objects, prototypes & OOP

**The fundamental.** Every JS object has a hidden link (`[[Prototype]]`, accessible via `Object.getPrototypeOf` / the legacy `__proto__`) to another object. Property lookups walk this **prototype chain** until found or `null`. `class` is **syntactic sugar** over this — under the hood it's still prototypes and constructor functions. `extends` sets up the chain; `super` calls the parent constructor/method.

| Lab | Decluttered ask |
|----|------------------|
| 5 Objects Lab | Object literal with mixed-type properties; export it. |
| 93 `Object.values()` | Returns an array of a plain object's own enumerable values. |
| 45 Class Creation | Minimal `class` with constructor + method + `new`. |
| 18 / 53 / 72 / 100 Inheritance (class) | `class Child extends Parent`, `super(...)`, override/extend methods. |
| 77 Inheritance | Override a parent method in the child (polymorphism). |
| 70 / 98 Prototypal Inheritance | The *pre-class* way: constructor functions + `Child.prototype = Object.create(Parent.prototype)`. Know this is what `class` compiles to. |
| 47 / 75 Mixins | Share behavior across classes **without** inheritance — copy methods in via `Object.assign`. Composition over inheritance. |
| 99 Singleton | One shared instance + global access point. `getInstance()` returns a cached instance. |
| 60 Property Descriptors | `get`/`set` accessors, `enumerable: false` via `Object.defineProperty`. |

**Class vs prototype — show you know they're the same thing:**
```js
// ES6 class
class Animal { speak() { return "…"; } }

// what it desugars to
function Animal() {}
Animal.prototype.speak = function () { return "…"; };
```

**Mixins vs inheritance (47, 75).** Inheritance is an *is-a* relationship and is single (one parent). Mixins compose *has-a-capability* — a `Person` can be a swimmer **and** a runner by mixing both in. The principle interviewers want named: **"composition over inheritance."**
```js
const swimmer = { swim() {} };
const runner  = { run() {} };
Object.assign(Person.prototype, swimmer, runner);
```

> 🎯 **Interview-grade**
> - "What is the prototype chain? How does property lookup work?"
> - "Difference between `__proto__` and `prototype`?" → `prototype` is a property on *constructor functions*; `__proto__` is the actual link on *instances*. `dog.__proto__ === Dog.prototype`.
> - "How does `class` work under the hood?" / "Implement inheritance without `class`."
> - "`Object.create(null)` — what and why?" → an object with no prototype, useful as a clean dictionary with no inherited `toString` etc.
> - "Composition vs inheritance — when each?"

---

## 5. Meta-programming

**The fundamental.** Meta-programming = code that inspects or alters the behavior of *other* code at runtime. JS gives you four tools: **`Proxy`** (intercept fundamental operations like get/set/delete), **`Reflect`** (a built-in object of those same operations as plain functions), **`Symbol`** (unique, collision-proof keys), and **property descriptors** (the metadata — writable/enumerable/configurable — behind every property).

| Lab | Decluttered ask |
|----|------------------|
| 9 Proxy Object | `new Proxy(target, { get(t, prop){…} })` — intercept reads, transform `msg` to uppercase. |
| 33 Revocable Proxy | `Proxy.revocable()` → `{ proxy, revoke }`; after `revoke()`, any use throws. |
| 19 `Reflect.deleteProperty` | Delete a key, get back a boolean success (vs `delete` operator). |
| 95 `Reflect.set` | Set a property programmatically; even works to tag a function object. |
| 81 Reflection | Dynamically change a property by name — `obj[key] = val` / `Reflect.set`. |
| 52 / 54 Symbols | Unique primitive keys; `Symbol("desc")`, `Symbol.for()` (global registry), `Object.getOwnPropertySymbols`. |
| 85 `Symbol.match` | A **well-known symbol** — define `[Symbol.match]` so an object customizes `str.match(obj)`. |
| 60 Property Descriptors | getters/setters + non-enumerable props via `Object.defineProperty`. |
| 23 `Object.seal` | Prevent add/delete of props (existing ones still writable); check with `Object.isSealed`. |
| 88 Side Effects | Functions that mutate external state — the *anti-pattern* meta-programming helps you observe/control. |

**Proxy mental model:** a Proxy wraps a target and a **handler** of *traps*. Each trap intercepts one operation.
```js
const p = new Proxy({}, {
  get:  (t, k) => k in t ? t[k] : `no ${String(k)}`,
  set:  (t, k, v) => { console.log(`set ${k}`); t[k] = v; return true; },
});
```
**`Reflect` pairs with `Proxy`:** inside a trap, call the matching `Reflect` method to get default behavior, e.g. `Reflect.get(t, k, receiver)`. `Reflect.deleteProperty` returns `true/false` instead of throwing — cleaner than the `delete` operator.

**Symbols — why they exist:** string keys collide. A `Symbol` is guaranteed unique, so library authors add metadata to your objects without clobbering your keys, and **well-known symbols** (`Symbol.iterator`, `Symbol.match`, `Symbol.asyncIterator`) let your objects hook into language syntax (chapter 6).

**Object integrity ladder** (know the three rungs): `Object.preventExtensions` (no new props) → `Object.seal` (no new/delete) → `Object.freeze` (no new/delete/change — fully immutable, shallowly).

> 🎯 **Interview-grade**
> - "What's a Proxy? Name two real uses." → validation, logging, reactive frameworks (Vue 3's reactivity is Proxy-based), default values, negative-index arrays.
> - "Why use a `Symbol` as a key instead of a string?"
> - "Difference between `seal`, `freeze`, `preventExtensions`?"
> - "What's a property descriptor? How do you make a property read-only / hidden from `for…in`?"

---

## 6. Iteration protocols & generators

**The fundamental.** This is the single most-repeated topic in the set (labs 22, 29, 32, 64, 65, 71) — so it's clearly a favorite. JS has **two protocols**:
- **Iterable**: an object with a `[Symbol.iterator]()` method that returns an iterator. `for…of`, spread, and destructuring all consume iterables.
- **Iterator**: an object with a `next()` method returning `{ value, done }`.

A **generator** (`function*` + `yield`) is the easy way to produce an iterator — it's a function that can pause and resume, automatically returning a `{value, done}`-shaped iterator that is *also* iterable.

| Lab | Decluttered ask |
|----|------------------|
| 22 Iterables | Add `[Symbol.iterator]` to an object so `for…of` works; sum the values. |
| 32 Iteration Protocols (Range class) | A `Range` class that is iterable — `[Symbol.iterator]` returns an iterator with `next()`/`done`. |
| 29 / 64 Iteration Protocols | Hand-roll an iterator that yields even numbers (with `hasNext()`/`done`), then do the same with a generator. |
| 65 Generators | `function*` that counts up to a limit; iterate it with `for…of`. |
| 71 Iterator Lab | `range(start,end)` → array, and `mapIterator(arr, fn)` → transformed array (manual `map`). |

**The canonical iterable (memorize this shape):**
```js
const range = {
  start: 1, end: 5,
  [Symbol.iterator]() {
    let cur = this.start, end = this.end;
    return { next: () => cur <= end ? { value: cur++, done: false }
                                     : { value: undefined, done: true } };
  },
};
[...range]; // [1,2,3,4,5]
```
**Same thing with a generator — note how much shorter:**
```js
function* range(start, end) { for (let i = start; i <= end; i++) yield i; }
[...range(1, 5)]; // [1,2,3,4,5]
```

**Why generators matter beyond toy ranges:** lazy/infinite sequences (you only compute values as pulled), and they were the conceptual basis for `async/await`. Mentioning that connection scores points.

> 🎯 **Interview-grade**
> - "Difference between an iterable and an iterator?"
> - "How does `for…of` work internally?" → calls `[Symbol.iterator]()`, then `next()` until `done`.
> - "What's a generator? Write one that yields an infinite sequence of even numbers." (Possible because it's lazy.)
> - "Why can you spread a `Set`/`Map`/string but not a plain object?" → those implement `[Symbol.iterator]`; plain objects don't (use `Object.entries`).

---

## 7. Collections & memory

**The fundamental.** Beyond arrays and objects, ES6 added **`Map`** (any-type keys, ordered, easy size) and **`Set`** (unique values). For low-level binary data, **`ArrayBuffer`** is a fixed chunk of raw memory and **typed arrays** (`Int32Array`, `Uint8Array`, …) are typed *views* into that buffer.

| Lab | Decluttered ask |
|----|------------------|
| 56 / 57 / 68 / 76 Maps | Create a `Map`, `set`/`get`/`size`/`delete`; iterate to find a max. |
| 79 Sets | `Set` + implement `union` and `intersection`. |
| 87 Sets | `Set` add/delete/size; sum unique elements. |
| 74 LinkedList | `Node {value, next}` + `LinkedList {add, length}` — pointer-based structure, no built-in. |
| 66 Queue | FIFO `enqueue`/`dequeue`/`getSize` (lab uses lodash; know array `push`/`shift`). |
| 83 Memory Management | `new ArrayBuffer(n)` → `new Int32Array(buf)`, fill, sum. Raw memory + typed view. |
| 96 Typed Arrays | Create/manipulate `Uint8Array` etc.; understand byte sizes and overflow wrap. |
| 44 `isTypedArray` | Detect a typed array — `ArrayBuffer.isView(x) && !(x instanceof DataView)`, or check `Object.prototype.toString`. |

**`Map` vs plain object — the interview staple:**

| | `Object` | `Map` |
|--|----------|-------|
| Keys | strings/symbols only | **any type** (objects, functions) |
| Order | mostly insertion (with quirks) | guaranteed insertion order |
| Size | `Object.keys(o).length` | `map.size` |
| Iteration | not directly iterable | iterable (`for…of`) |
| Prototype keys | inherits `toString` etc. (collision risk) | no default keys |

Use a `Map` when keys are dynamic/non-string or you mutate often; use an object for fixed, known-shape records.

**`Set` for dedupe** is the one-liner everyone should know: `[...new Set(arr)]`.

**Typed arrays (83, 96)** — the "what's actually tested": JS numbers are 64-bit floats, but sometimes you need raw bytes (file I/O, network buffers, WebGL). `ArrayBuffer` is the memory; a typed array is a lens over it. In Node, `Buffer` is a `Uint8Array` subclass. Overflow wraps: `Uint8Array` of `256` stores `0`.

> 🎯 **Interview-grade**
> - "`Map` vs object — when do you reach for each?"
> - "How do you remove duplicates from an array?" (Set.) "What about an array of objects?" (Set won't dedupe by value — need a key function.)
> - "`Map` vs `WeakMap`?" → WeakMap keys are objects held weakly (GC-able), not enumerable; good for private/metadata caches.
> - "What's an `ArrayBuffer`? How does it relate to Node's `Buffer`?"

---

## 8. Asynchronous JavaScript & the event loop

**The fundamental — the heart of Node.** JS is single-threaded, so it can't *block* on I/O. Instead, async work is registered with callbacks; the event loop runs them when the work completes and the call stack is empty. The evolution: **callbacks → Promises → async/await**. A Promise is an object representing a future value (`pending → fulfilled | rejected`). `async/await` is syntax sugar over Promises that lets you write async code that *reads* synchronously.

| Lab | Decluttered ask |
|----|------------------|
| 78 Callbacks | Pass a function to be invoked later — the original async pattern + "callback hell" motivation. |
| 6 `Promise.all` | Run independent promises concurrently; resolves to an array; rejects fast if **any** rejects. |
| 62 Promise Chaining | `.then()` returns a promise → chain `fetchData().then(processData)`; flatten async steps. |
| 28 Async/Await | `async` fn returns a promise; `await` pauses; wrap in `try/catch`. |
| 36 EventEmitter | Pub/sub: `on(event, cb)`, `emit(event, data)`, `off`/`once`. Node's core async pattern. |

**Promise combinators — know all four:**
- `Promise.all` — all succeed or it rejects on first failure (lab 6). Use for "I need everything."
- `Promise.allSettled` — waits for all, never rejects; returns status per promise. Use when partial failure is OK.
- `Promise.race` — settles as soon as the first settles (resolve *or* reject). Timeouts.
- `Promise.any` — first *fulfilled*; rejects only if all reject.

**The event loop phases (libuv).** One pass processes phases in order: **timers** (`setTimeout`/`setInterval`) → **pending callbacks** → **poll** (I/O) → **check** (`setImmediate`) → **close**. Between *every* callback, the **microtask queue** drains completely.

**Microtasks vs macrotasks — the question that separates juniors from mids:**
```js
console.log("1");
setTimeout(() => console.log("2"), 0);   // macrotask (timers phase)
Promise.resolve().then(() => console.log("3")); // microtask
console.log("4");
// Output: 1, 4, 3, 2
```
Microtasks (Promise callbacks, `queueMicrotask`, `process.nextTick`) run **before** the next macrotask. `process.nextTick` even jumps ahead of the Promise microtask queue.

**EventEmitter (36)** is Node's backbone — streams, HTTP servers, and `process` are all emitters. The pattern: register listeners with `on`, fire with `emit`. Implementing a mini one (a `Map` of event → listener array) is a very common live-coding task.

> 🎯 **Interview-grade**
> - "Explain the event loop." (Draw the layers; name microtask vs macrotask.)
> - "Predict the output" of a mixed `setTimeout` / `Promise.then` / `process.nextTick` snippet.
> - "`Promise.all` vs `allSettled` vs `race`?"
> - "What is callback hell and how do Promises/async-await solve it?"
> - "Implement a `sleep(ms)` / `promisify(fn)` / a basic `EventEmitter`."
> - "Where does `await` actually yield control?" (At the `await`, the rest of the function is scheduled as a microtask continuation.)

---

## 9. Modules: CommonJS vs ES Modules

**The fundamental.** Modules let you split code into files with explicit imports/exports. Node historically used **CommonJS** (`require` / `module.exports`) — synchronous, dynamic. The standard is now **ES Modules** (`import` / `export`) — static (analyzable at parse time), async-friendly, the same syntax browsers use. Almost every lab says "use ESM syntax."

| Lab | Decluttered ask |
|----|------------------|
| 24 ES6 Modules | `export` a function from one file, `import` it in another. |
| 48 Modules Lab | One file with **one default + named** exports; import both. |
| 50 Default Exports | `export default value`; import without braces. |
| 92 Function Methods | Named export one fn, default-export another (export mechanics). |
| 69 Namespaces | Group related fns/vars under one object to avoid global pollution (the pre-module pattern). |
| 27 Circular Dependencies | Two modules importing each other — understand partial/incomplete exports at load time. |
| 15 Standard I/O | (Note: the one lab that explicitly uses **CommonJS** — `module.exports`.) |

**ESM vs CommonJS — the comparison table:**

| | CommonJS | ES Modules |
|--|----------|-----------|
| Import | `const x = require('x')` | `import x from 'x'` |
| Export | `module.exports` / `exports.foo` | `export` / `export default` |
| Loading | synchronous, runtime | static, hoisted, async |
| `this` at top level | `module.exports` | `undefined` |
| Enable in Node | default `.cjs` | `"type":"module"` or `.mjs` |
| Tree-shaking | hard | easy (static) |
| `__dirname`/`__filename` | available | use `import.meta.url` |

**Named vs default:** a file can have **many** named exports but **one** default. Named imports use braces and must match the name (`import { foo }`); default imports don't and you can rename freely (`import whatever`).

**Circular dependencies (27)** — *what's really tested:* when A imports B and B imports A, whichever loads first gets a **partially-initialized** version of the other. In CommonJS you receive whatever `module.exports` held at that moment (possibly incomplete); ESM uses live bindings + hoisting which handles it more gracefully but can still throw on access-before-init. The fix is usually to restructure (extract the shared piece) or defer the access.

> 🎯 **Interview-grade**
> - "CommonJS vs ESM — list the differences."
> - "Can you use `require` and `import` in the same file?" (Not directly; ESM can `import` CJS, but not vice-versa without dynamic `import()`.)
> - "What happens with a circular dependency? How do you fix it?"
> - "Difference between default and named exports?"
> - "How do you get `__dirname` in an ES module?" (`path.dirname(fileURLToPath(import.meta.url))`.)

---

## 10. Node.js core modules

**The fundamental.** These are the batteries Node includes — implemented in C++/JS, imported by name (`import fs from 'node:fs'`). Interviewers care less about exact signatures and more about: sync vs async, callback vs promise API, and *when* you'd use each.

| Lab | Module | Decluttered ask |
|----|--------|------------------|
| 1 Routing | `http` | `http.createServer(handler)` + `.listen(port)`; branch on `req.url`; set status + `Content-Type`, `res.end(body)`. |
| 17 File System | `fs` | Read a file / write a file (default-export a `readFile`). |
| 34 / 97 Config Mgmt | `fs.promises` | Read & `JSON.parse` a `config.json`; export a config object. |
| 4 Change Permissions | `fs.chmod` | Async change file mode (octal); validate args; `try/catch`. |
| 14 FS Permissions | `fs` | `chmod`/`chown`/`lchmod` via `fs.promises`. |
| 3 / 16 OS Module | `os` | `os.platform()`/`type()`, `os.freemem()`, `totalmem()`, `uptime()`. |
| 12 Path Module | `path` | `join`, `basename`, `extname`, `dirname`, `resolve` — cross-platform paths. |
| 10 Crypto Hashing | `crypto` | `crypto.createHash('sha256').update(data).digest('hex')`; know md5/sha1 are weak. |
| 13 Encrypt/Decrypt | `crypto` | `createCipheriv`/`createDecipheriv` symmetric encryption. |
| 15 Standard I/O | `process` | `process.stdin`/`stdout`; `console.log` writes to stdout (CommonJS lab). |
| 2 Child Process | `child_process` | Wrap `exec`/`execFile` in promises; run shell commands/executables. |
| 66 Queue | (npm) | Install + import a third-party package (lodash) — dependency management. |

**The three things to actually remember about `fs`:**
1. **Three flavors:** sync (`fs.readFileSync` — blocks the event loop, avoid in servers), callback (`fs.readFile(path, cb)`), and promise (`fs.promises.readFile` / `import {readFile} from 'node:fs/promises'` — preferred with async/await).
2. **Never block the event loop** with `…Sync` in a request handler — one slow read stalls *all* concurrent requests.
3. File **mode** is octal (`0o644`); permissions = owner/group/others × read(4)/write(2)/execute(1).

**`http` (lab 1) — the minimal server everyone should be able to write blind:**
```js
import http from 'node:http';
http.createServer((req, res) => {
  if (req.url === '/hello') { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Hello, World!'); }
  else { res.writeHead(404, { 'Content-Type': 'text/plain' }); res.end('Not found'); }
}).listen(1337);
```

**`crypto` (10, 13):** a **hash** is one-way (integrity, password storage with salt) — you cannot reverse it. **Encryption** is two-way (you decrypt with a key). Knowing md5/sha1 are cryptographically broken (use sha256+, and bcrypt/argon2 for passwords) is a security-awareness signal.

**`child_process` (2):** `exec` runs a command *through a shell* (convenient, but shell-injection risk with untrusted input) and buffers output; `execFile` runs an executable directly (safer, no shell); `spawn` streams output (best for large/long output). Wrapping callback-style `exec` in a Promise (or `util.promisify`) is the lab's real lesson.

> 🎯 **Interview-grade**
> - "Sync vs async `fs` — why does it matter for a server?"
> - "How would you build an HTTP server without Express?" (lab 1)
> - "Hashing vs encryption — and how do you store passwords?"
> - "`exec` vs `spawn` vs `fork`?" → fork = spawn a new Node process with an IPC channel.
> - "What is `process`? Name things on it." → `argv`, `env`, `stdin/stdout`, `nextTick`, `exit`, `cwd()`, `pid`.

---

## 11. Errors, debugging & robustness

**The fundamental.** Robust code anticipates failure. Synchronous errors propagate up the call stack and are caught with `try/catch/finally`. Async errors are trickier: a rejected Promise is caught by `.catch()` or `try/catch` around `await`; an error thrown in a bare callback or unhandled rejection can crash the process.

| Lab | Decluttered ask |
|----|------------------|
| 73 Handling Errors | `throw new Error(msg)`, catch it, log it. Custom errors. |
| 89 Error Handling | Full `try / catch / finally` — `finally` always runs (cleanup). |
| 49 Debugging | Find & fix bugs in arithmetic functions — reading code critically. |
| 4 (revisited) | Real-world arg validation + `try/catch` around an async fs call. |

**The error-handling rules to recite:**
- Throw `Error` objects (or subclasses), never strings — you want a stack trace.
- `finally` runs whether or not an error was thrown — use for cleanup (close files/connections).
- `try/catch` does **not** catch errors inside an async callback or a non-awaited Promise. Around `await`, it does.
- A custom error: `class ValidationError extends Error { constructor(m){ super(m); this.name = "ValidationError"; } }`.
- In Node, listen for `process.on('unhandledRejection')` and `'uncaughtException')` as last-resort logging — then exit; don't try to "resume."

> 🎯 **Interview-grade**
> - "How do you handle errors in async/await vs Promises vs callbacks?"
> - "What does `finally` do? Does it run if the `try` returns?"
> - "What happens to an unhandled promise rejection in Node?"
> - "How do you create a custom error type?"

---

## 12. Algorithms, complexity & functional array methods

**The fundamental.** Even "framework" interviews probe basic algorithmic thinking and **Big-O** — how runtime/space grows with input size. Paired with this: the functional trio `map`/`filter`/`reduce`, which expresses transformations declaratively.

| Lab | Decluttered ask |
|----|------------------|
| 101 Computational Complexity | Implement + compare linear vs binary search; reason about O(n) vs O(log n). |
| 35 Searching Algorithms | `linearSearch` (O(n)) and `binarySearch` (O(log n), needs sorted input). |
| 11 DFS | Depth-First Search on an adjacency-list graph; return visited order. Recursion/stack + visited set. |
| 55 Recursion | `factorial` — base case + recursive case (also chapter 3). |
| 102 Memoization | Cache fib results → turn O(2ⁿ) into O(n). Trade space for time. |
| 82 Map/Filter/Reduce | Reimplement the three; know `reduce`'s accumulator. |
| 84 Loops | Same operations via different loop constructs. |
| 21 / 43 `every` | `Array.prototype.every` — true iff *all* elements pass; short-circuits on first false. |
| 41 `dropRight` | Return a copy without the last `n` elements (no mutation) — `slice`. |
| 51 Arrays Lab | create/sum/reverse/filter — array fundamentals. |

**Big-O cheat sheet (have these memorized):**
- O(1) constant — `map.get`, array index, object property.
- O(log n) — binary search, balanced tree ops.
- O(n) — linear scan, `map`/`filter`/`find`.
- O(n log n) — good sorts (`Array.sort`).
- O(n²) — nested loops, naive dedupe.
- O(2ⁿ) — naive recursive fib (why 102 exists).

**`reduce` is the one people fumble** — it folds an array into a single value:
```js
[1,2,3,4].reduce((acc, x) => acc + x, 0); // 10
// map and filter can both be written as reduce — be ready to show it.
```

**Memoization (102)** ties chapters together: it's a **closure** (ch.3) over a **cache** (ch.7) that improves **complexity** (ch.12).
```js
function memoize(fn) {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}
```

> 🎯 **Interview-grade**
> - "What's the time complexity of your solution? Can you do better?"
> - "Binary search — preconditions and complexity?"
> - "Implement `map`/`filter`/`reduce` from scratch." / "Implement `reduce` and then build `map` on top of it."
> - "DFS vs BFS — data structure each uses?" (stack/recursion vs queue.)
> - "Optimize recursive Fibonacci." (memoize or go iterative/bottom-up.)

---

## 13. Rapid-fire interview checklist

Tick these off — if you can answer each in two sentences, you're ready for most Node/JS screens.

**Language core**
- [ ] `var` vs `let` vs `const` (scope, hoisting, TDZ, reassignment)
- [ ] `==` vs `===` and the coercion rules
- [ ] What a closure is + one real use
- [ ] How `this` is determined (4 rules + arrow exception)
- [ ] Prototype chain & how `class` desugars
- [ ] `null` vs `undefined`; `typeof` quirks
- [ ] Pass-by-value (primitives) vs pass-by-reference (objects)
- [ ] Deep vs shallow copy (`structuredClone`, spread caveats)

**Async**
- [ ] Event loop: microtasks vs macrotasks; predict mixed output
- [ ] `Promise.all` / `allSettled` / `race` / `any`
- [ ] `async/await` error handling + where it yields
- [ ] `process.nextTick` vs `setImmediate` vs `setTimeout(…,0)`
- [ ] Callback hell → Promises → async/await

**Node runtime**
- [ ] Is Node single-threaded? (nuanced answer)
- [ ] libuv, thread pool, what's offloaded
- [ ] sync vs async `fs`; why blocking is bad
- [ ] CommonJS vs ESM
- [ ] `EventEmitter` / streams basics
- [ ] `process` object essentials; `process.env` returns strings
- [ ] Hashing vs encryption; password storage

**Data & algorithms**
- [ ] `Map`/`Set` vs object/array; `WeakMap`
- [ ] Iterables vs iterators vs generators
- [ ] Big-O of common operations
- [ ] `map`/`filter`/`reduce` (and implement them)
- [ ] Memoization (closure + cache)

**Meta & robustness**
- [ ] `Proxy` + `Reflect` (one real use)
- [ ] `Symbol` and well-known symbols
- [ ] `seal`/`freeze`/`preventExtensions`
- [ ] `try/catch/finally`; custom errors; unhandled rejections

---

### Suggested study order (by leverage, not by lab number)

1. **Async + event loop** (ch.8) — most-asked, highest signal.
2. **Closures, scope, `this`** (ch.3) — underpins everything.
3. **Prototypes & OOP** (ch.4) — classic deep-dive.
4. **Modules** (ch.9) and **core modules** (ch.10) — the Node-specific layer.
5. **Iteration/generators** (ch.6) and **collections** (ch.7).
6. **Coercion** (ch.2), **meta-programming** (ch.5), **errors** (ch.11), **algorithms** (ch.12) — round out the edges.

Work each chapter, then solve its mapped labs from the *decluttered ask* without peeking at the lab's step-by-step. If you can do that and answer the 🎯 questions out loud, the underlying concept is yours — which is what the interview is really testing.
