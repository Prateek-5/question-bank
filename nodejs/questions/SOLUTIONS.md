# Worked Solutions — Medium & Hard Labs

> Reference solutions for all **47** Medium/Hard problems (44 Medium + 3 Hard) in this set.
> Every solution is **idiomatic ES Modules** (the format the labs expect), with the *decluttered ask* up top and notes on the concept being tested. Where a lab's exact test signature isn't fully specified in the prompt, the most conventional signature is used and flagged.
>
> Pair this with the **[Study Guide](./STUDY-GUIDE.md)** — it explains the *why*; this file shows the *how*.

## Contents

- [Async & the event loop](#async--the-event-loop) — 6, 36, 62, 78
- [Functions & functional programming](#functions--functional-programming) — 25, 39, 40, 46, 80, 102
- [Objects, prototypes & OOP](#objects-prototypes--oop) — 18, 47, 70, 75, 77, 98, 99, 100
- [Meta-programming](#meta-programming) — 9, 19 (H), 60, 81 (H), 85, 88, 95 (H)
- [Iteration protocols & generators](#iteration-protocols--generators) — 22, 29, 64, 65, 71
- [Collections & memory](#collections--memory) — 44, 66, 74, 79, 83, 96
- [Arrays](#arrays) — 21, 82
- [Algorithms & complexity](#algorithms--complexity) — 11, 35, 101
- [Modules & Node core](#modules--node-core) — 2, 10, 13, 14, 27, 97

---

## Async & the event loop

### 6 — Using `Promise.all()` (Medium)
**Tests:** running independent promises concurrently and collecting results.
```js
// index.js
export function getUsers() {
  return new Promise((resolve) => {
    setTimeout(() => resolve([{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]), 100);
  });
}

export function getPosts() {
  return new Promise((resolve) => {
    setTimeout(() => resolve([{ id: 1, title: 'Hello' }, { id: 2, title: 'World' }]), 100);
  });
}

// Run both concurrently — total wait ≈ 100ms, not 200ms.
export async function getAll() {
  const [users, posts] = await Promise.all([getUsers(), getPosts()]);
  return { users, posts };
}
```
> `Promise.all` rejects as soon as *any* input rejects. If you need every result regardless, use `Promise.allSettled`.

### 36 — EventEmitter (Medium)
**Tests:** the pub/sub pattern — implement `on` / `emit` / `off` / `once` from scratch.
```js
// EventEmitter.js
export default class EventEmitter {
  #listeners = new Map(); // event -> Set<fn>

  on(event, listener) {
    if (!this.#listeners.has(event)) this.#listeners.set(event, new Set());
    this.#listeners.get(event).add(listener);
    return this; // chainable, like Node's
  }

  off(event, listener) {
    this.#listeners.get(event)?.delete(listener);
    return this;
  }

  once(event, listener) {
    const wrapper = (...args) => { this.off(event, wrapper); listener(...args); };
    return this.on(event, wrapper);
  }

  emit(event, ...args) {
    const set = this.#listeners.get(event);
    if (!set) return false;
    for (const fn of [...set]) fn(...args); // copy so once() removal mid-emit is safe
    return true;
  }
}
```

### 62 — Promise Chaining (Medium)
**Tests:** `.then()` returns a promise, so steps chain and flatten.
```js
// index.js
export function fetchData() {
  return new Promise((resolve) => setTimeout(() => resolve('raw data'), 1000));
}

export function processData(data) {
  return new Promise((resolve) => setTimeout(() => resolve(`processed: ${data}`), 1000));
}

// Chain: each .then returns a promise the next .then awaits.
export function run() {
  return fetchData()
    .then((data) => processData(data))
    .then((result) => result);
}
```

### 78 — Callbacks (Medium)
**Tests:** functions as arguments invoked later — the foundation async was built on.
```js
// index.js
// A callback is just a function passed in to be called when work is done.
export function add(a, b, callback) {
  callback(a + b);
}

// Node-style "error-first" callback convention: (err, result).
export function divide(a, b, callback) {
  if (b === 0) return callback(new Error('Division by zero'));
  callback(null, a / b);
}

// Simulated async work that calls back later.
export function fetchUser(id, callback) {
  setTimeout(() => callback(null, { id, name: `User ${id}` }), 100);
}

// Higher-order: take a callback, run it over each item.
export function forEach(array, callback) {
  for (let i = 0; i < array.length; i++) callback(array[i], i);
}
```

---

## Functions & functional programming

### 25 — Functions Lab (Medium)
**Tests:** named functions, arrow functions, and higher-order functions together.
```js
// index.js
export function square(n) { return n * n; }          // named function declaration
export const cube = (n) => n ** 3;                   // arrow function expression

// Higher-order: returns a function (a closure over `factor`).
export const multiplier = (factor) => (n) => n * factor;

// Higher-order: takes a function as an argument.
export const applyTwice = (fn, value) => fn(fn(value));
```

### 39 — Custom Add Function (Medium)
**Tests:** `typeof` branching, type coercion, throwing on mismatch.
```js
// index.js
export function customAdd(a, b) {
  if (typeof a !== typeof b) {
    throw new Error('Arguments should be of the same type');
  }
  if (typeof a === 'boolean') return Number(a) + Number(b); // true+true -> 2
  return a + b; // numbers add, strings concatenate
}
```

### 40 — Function Expressions (Medium)
**Tests:** named function expressions and exporting them (individually and grouped).
```js
// index.js
// Named function expression — the name `addFn` is internal/for stack traces.
export const add = function addFn(a, b) { return a + b; };
export const subtract = function subFn(a, b) { return a - b; };

// An object of named function expressions, default-exported.
const mathOps = {
  multiply: function mul(a, b) { return a * b; },
  divide: function div(a, b) { return a / b; },
};
export default mathOps;
```

### 46 — Lodash `_.over()` (Medium)
**Tests:** functional composition — one input, many functions, array of results.
```js
// index.js
// Returns a function that invokes every fn with the same args.
export function over(...fns) {
  return (...args) => fns.map((fn) => fn(...args));
}

// Example:
// const minMax = over(Math.min, Math.max);
// minMax(3, 1, 4, 1, 5); // [1, 5]
```

### 80 — Higher-order Functions (Medium)
**Tests:** writing/consuming functions that take or return functions.
```js
// index.js
export const mapArray = (arr, fn) => arr.map(fn);
export const filterArray = (arr, fn) => arr.filter(fn);
export const reduceArray = (arr, fn, init) => arr.reduce(fn, init);

// Returns a function — composition of two functions.
export const compose = (f, g) => (x) => f(g(x));

// Curried adder demonstrates closures returning functions.
export const adder = (x) => (y) => x + y;
```

### 102 — Memoization (Medium)
**Tests:** a closure over a cache to turn O(2ⁿ) fib into O(n).
```js
// index.js
// Generic memoizer: closure over a Map keyed by stringified args.
export function memoize(fn) {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

// Memoized fibonacci. Internal recursion also hits the cache.
export const fib = memoize(function f(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
});
```

---

## Objects, prototypes & OOP

### 18 — Inheritance with classes (Medium)
**Tests:** `class`, `constructor`, `extends`, `super`, methods.
```js
// index.js
export class Person {
  constructor(name) { this.name = name; }
  greeting() { return `Hello, my name is ${this.name}`; }
}

export class Student extends Person {
  constructor(name, course) {
    super(name);          // must call before using `this`
    this.course = course;
  }
  courseDetails() { return `${this.name} is enrolled in ${this.course}`; }
}
```

### 47 — Mixins & Composition (Medium)
**Tests:** sharing behavior without inheritance (composition over inheritance).
```js
// index.js
export const swimmer = { swim() { return `${this.name} is swimming`; } };
export const runner  = { run()  { return `${this.name} is running`; } };

export class Person {
  constructor(name) { this.name = name; }
}

// `extend` copies mixin methods onto the target's prototype.
export function extend(target, ...mixins) {
  Object.assign(target.prototype, ...mixins);
  return target;
}

extend(Person, swimmer, runner);
// new Person('Sam').swim(); // "Sam is swimming"
```

### 70 — Prototypal Inheritance (Medium)
**Tests:** the pre-`class` mechanism that `class` desugars to.
```js
// index.js
export function Person(name, age) {
  this.name = name;
  this.age = age;
}
Person.prototype.describe = function () { return `${this.name}, ${this.age}`; };

export function Employee(name, age, company) {
  Person.call(this, name, age);     // borrow parent constructor
  this.company = company;
}
// Link the prototype chain, then fix the constructor pointer.
Employee.prototype = Object.create(Person.prototype);
Employee.prototype.constructor = Employee;

export const emp = new Employee('Alice', 30, 'Codedamn');
```

### 75 — Composition with Mixins (Medium)
**Tests:** combining multiple capabilities into classes via function mixins.
```js
// index.js
// Function-style mixins: take a base class, return an extended subclass.
export const Serializable = (Base) => class extends Base {
  serialize() { return JSON.stringify(this); }
};
export const Loggable = (Base) => class extends Base {
  log() { return `[LOG] ${this.serialize?.() ?? JSON.stringify(this)}`; }
};

export class Model {
  constructor(data) { Object.assign(this, data); }
}

// Compose both onto Model.
export class User extends Loggable(Serializable(Model)) {}
// new User({ id: 1 }).log();
```

### 77 — Inheritance with method override (Medium)
**Tests:** polymorphism — child overrides a parent method.
```js
// index.js
export class Animal {
  saySomething() { return 'Some generic sound'; }
}

export class Dog extends Animal {
  saySomething() { return 'Woof! Woof!'; } // overrides Animal's version
}

export const dog = new Dog();
// dog.saySomething(); // "Woof! Woof!"
```

### 98 — Prototypes Lab (Medium)
**Tests:** constructor functions + prototype methods + inheritance.
```js
// index.js
export function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return `${this.name} makes a sound`; };

export function Dog(name) { Animal.call(this, name); }
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;
Dog.prototype.speak = function () { return `${this.name} barks`; }; // override
```

### 99 — Singleton Pattern (Medium)
**Tests:** one instance + a global access point.
```js
// index.js
export class Singleton {
  static #instance = null;

  static getInstance() {
    if (!Singleton.#instance) Singleton.#instance = new Singleton();
    return Singleton.#instance;
  }

  message() { return 'Hello Singleton!'; }
}
// Singleton.getInstance() === Singleton.getInstance(); // true
```

### 100 — Inheritance (Person → Employee) (Medium)
**Tests:** inherited methods + `toString` override.
```js
// index.js
export class Person {
  constructor(firstName, lastName) {
    this.firstName = firstName;
    this.lastName = lastName;
  }
  fullName() { return `${this.firstName} ${this.lastName}`; }
}

export class Employee extends Person {
  constructor(firstName, lastName, position, salary) {
    super(firstName, lastName);
    this.position = position;
    this.salary = salary;
  }
  toString() {
    return `${this.fullName()} — ${this.position} ($${this.salary})`;
  }
}
```

---

## Meta-programming

### 9 — Proxy Object (Medium)
**Tests:** a `get` trap that transforms one property.
```js
// proxy.js
const target = { msg: 'hello world', other: 'unchanged' };

const handler = {
  get(obj, prop) {
    const value = Reflect.get(obj, prop);
    return prop === 'msg' && typeof value === 'string' ? value.toUpperCase() : value;
  },
};

export const proxy = new Proxy(target, handler);
// proxy.msg   -> "HELLO WORLD"
// proxy.other -> "unchanged"
```

### 19 — `Reflect.deleteProperty()` (Hard)
**Tests:** deleting a key and getting a boolean result (vs the `delete` operator).
```js
// index.js
export const target = { a: 1, b: 2, c: 3 };

// Returns true on success, false if the property is non-configurable.
export function deleteProp(obj, prop) {
  return Reflect.deleteProperty(obj, prop);
}

deleteProp(target, 'b'); // true; target is now { a: 1, c: 3 }
```

### 60 — Property Descriptors (Medium)
**Tests:** getter/setter accessors + a non-enumerable property.
```js
// index.js
export function defineProperties(obj) {
  Object.defineProperty(obj, 'fullName', {
    get() { return `${this.firstName} ${this.lastName}`; },
    enumerable: true,
    configurable: true,
  });

  Object.defineProperty(obj, 'age', {
    set(value) { this._age = value; },
    get() { return this._age; },
    enumerable: false, // hidden from for..in / Object.keys
    configurable: true,
  });

  return obj;
}
```

### 81 — Reflection: Property Manipulation (Hard)
**Tests:** dynamically changing a property by name at runtime.
```js
// index.js
export const person = { name: 'Alice', age: 30, city: 'NYC' };

// Reflect.set returns a boolean indicating success.
export function changeProperty(obj, key, value) {
  return Reflect.set(obj, key, value);
}

changeProperty(person, 'age', 31); // person.age === 31
```

### 85 — `Symbol.match` (Medium)
**Tests:** a well-known symbol that customizes `String.prototype.match`.
```js
// index.js
export const dogChecker = {
  [Symbol.match](str) {
    const found = str.includes('dog');
    return found ? ['dog'] : null; // mimic a match-result shape
  },
};
// 'I love my dog'.match(dogChecker); // ['dog']
// 'I love my cat'.match(dogChecker); // null
```

### 88 — Side Effects (Medium)
**Tests:** distinguishing pure functions from ones that mutate external state.
```js
// index.js
let counter = 0;
export let globalValue = null;

// Side effect: mutates module-level `counter`.
export function increment() { counter += 1; return counter; }
export function getCounter() { return counter; }

// Side effect: mutates the array passed in (does NOT return a new one).
export function addItem(arr, item) { arr.push(item); return arr; }

// Side effect: writes a module-level variable.
export function setGlobal(value) { globalValue = value; }

// For contrast — the PURE version of addItem (no mutation):
export const addItemPure = (arr, item) => [...arr, item];
```

### 95 — `Reflect.set()` (Hard)
**Tests:** setting a property programmatically — even on a function object.
```js
// reflect.js
export function calculateArea(length, width) {
  return length * width;
}

// Functions are objects, so you can attach metadata to them.
Reflect.set(calculateArea, 'type', 'rectangle');
// calculateArea.type === 'rectangle'
// calculateArea(4, 5) === 20
```

---

## Iteration protocols & generators

### 22 — Iterables (Medium)
**Tests:** make an object work with `for...of` via `[Symbol.iterator]`.
```js
// index.js
export const customIterable = {
  start: 1,
  end: 5,
  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next: () => current <= end
        ? { value: current++, done: false }
        : { value: undefined, done: true },
    };
  },
};

export let sum = 0;
for (const n of customIterable) sum += n; // 1+2+3+4+5 = 15
```

### 29 — Iteration Protocols (iterator + generator) (Medium)
**Tests:** a hand-rolled even-number iterator with `hasNext()`, then the same as a generator.
```js
// index.js
export function createEvenIterator(start, end) {
  let current = start % 2 === 0 ? start : start + 1;
  return {
    hasNext: () => current <= end,
    next() {
      if (current > end) return { value: undefined, done: true };
      const value = current;
      current += 2;
      return { value, done: false };
    },
  };
}

// Same behavior, far less code — generators auto-build the iterator.
export function* evenGenerator(start, end) {
  for (let i = start % 2 === 0 ? start : start + 1; i <= end; i += 2) yield i;
}
```

### 64 — Iteration Protocols (iterable + iterator) (Medium)
**Tests:** an object that is both iterable and exposes the iterator protocol.
```js
// index.js
export function createEvenNumbers(limit) {
  return {
    [Symbol.iterator]() {
      let current = 0;
      return {
        next() {
          if (current > limit) return { value: undefined, done: true };
          const value = current;
          current += 2;
          return { value, done: false };
        },
      };
    },
  };
}
// [...createEvenNumbers(8)]; // [0, 2, 4, 6, 8]
```

### 65 — Generators (Medium)
**Tests:** `function*` + `yield`; a pausable counter.
```js
// index.js
export function* countUpTo(limit) {
  for (let i = 1; i <= limit; i++) yield i;
}
// [...countUpTo(5)]; // [1, 2, 3, 4, 5]
```

### 71 — Iterator Lab (range + mapIterator) (Medium)
**Tests:** building `range` and a manual `map`, then composing them.
```js
// range.js
export default function range(start, end) {
  const result = [];
  for (let i = start; i <= end; i++) result.push(i);
  return result;
}

// mapIterator.js
export default function mapIterator(array, callback) {
  const result = [];
  for (let i = 0; i < array.length; i++) result.push(callback(array[i], i));
  return result;
}

// index.js
import range from './range.js';
import mapIterator from './mapIterator.js';

export const myRange = range(1, 10);
export const timesTwo = (n) => 2 * n;
export const doubledRange = mapIterator(myRange, timesTwo);
```

---

## Collections & memory

### 44 — Custom `isTypedArray()` (Medium)
**Tests:** detecting typed arrays without lodash + writing assert tests.
```js
// index.js
export function isTypedArray(value) {
  // Every typed array is a view over an ArrayBuffer; DataView is the exception.
  return ArrayBuffer.isView(value) && !(value instanceof DataView);
  // Equivalent tag-based check:
  // return /^\[object (Int|Uint|Float|BigInt|BigUint).*Array\]$/
  //   .test(Object.prototype.toString.call(value));
}

// tests.js (Node's built-in assert)
import assert from 'node:assert';
import { isTypedArray } from './index.js';

assert.strictEqual(isTypedArray(new Int8Array(2)), true);
assert.strictEqual(isTypedArray(new Uint8Array(2)), true);
assert.strictEqual(isTypedArray([1, 2, 3]), false);       // normal array
assert.strictEqual(isTypedArray(new DataView(new ArrayBuffer(2))), false);
console.log('All tests passed');
```

### 66 — Queue with a third-party library (Medium)
**Tests:** FIFO queue + using/importing an npm dependency.
```js
// queue.js — vanilla (works without any dependency)
export default class Queue {
  #items = [];
  enqueue(item) { this.#items.push(item); }       // add to back
  dequeue() { return this.#items.shift(); }        // remove from front
  getSize() { return this.#items.length; }
}

// queue.js — lodash variant (the lab's stated approach)
// import _ from 'lodash';
// export default class Queue {
//   constructor() { this.items = []; }
//   enqueue(item) { this.items.push(item); }
//   dequeue() { return _.pullAt(this.items, 0)[0]; }
//   getSize() { return this.items.length; }
// }
```

### 74 — LinkedList (Medium)
**Tests:** pointer-based structure — `Node {value, next}` + `LinkedList`.
```js
// index.js
export class Node {
  constructor(value) {
    this.value = value;
    this.next = null;
  }
}

export class LinkedList {
  constructor() {
    this.head = null;
    this.size = 0;
  }

  add(value) {
    const node = new Node(value);
    if (!this.head) {
      this.head = node;
    } else {
      let current = this.head;
      while (current.next) current = current.next; // walk to the tail
      current.next = node;
    }
    this.size++;
    return this;
  }

  length() { return this.size; }
}
```

### 79 — Sets: union & intersection (Medium)
**Tests:** `Set` for uniqueness + set algebra.
```js
// index.js
export function union(setA, setB) {
  return new Set([...setA, ...setB]);
}

export function intersection(setA, setB) {
  return new Set([...setA].filter((x) => setB.has(x)));
}
// Bonus: difference = [...setA].filter(x => !setB.has(x))
```

### 83 — Memory Management (ArrayBuffer + typed array) (Medium)
**Tests:** raw memory allocation and a typed view over it.
```js
// index.js
export function createBuffer(byteLength) {
  return new ArrayBuffer(byteLength);     // raw bytes
}

export function createInt32View(buffer) {
  return new Int32Array(buffer);          // typed lens over the bytes
}

export function fillAndSum(byteLength) {
  const buffer = new ArrayBuffer(byteLength);
  const view = new Int32Array(buffer);    // length = byteLength / 4
  for (let i = 0; i < view.length; i++) view[i] = i + 1; // fill 1..N
  return view.reduce((sum, n) => sum + n, 0);
}
```

### 96 — Typed Arrays (Medium)
**Tests:** creating/manipulating typed arrays; byte sizes; overflow wrap.
```js
// index.js
export function createTypedArray(length) {
  return new Uint8Array(length); // zero-filled, 1 byte per element
}

export function setValues(arr, values) {
  arr.set(values);   // bulk copy; values beyond 0–255 wrap (mod 256)
  return arr;
}

export function sumTypedArray(arr) {
  return arr.reduce((sum, n) => sum + n, 0);
}

export function byteInfo(arr) {
  return { length: arr.length, bytesPerElement: arr.BYTES_PER_ELEMENT, byteLength: arr.byteLength };
}
// new Uint8Array([256, 257]) -> Uint8Array(2) [0, 1]  (overflow wraps)
```

---

## Arrays

### 21 — `Array.prototype.every()` (Medium)
**Tests:** the `every` predicate (all elements must pass; short-circuits).
```js
// index.js
export const allPositive = (arr) => arr.every((n) => n > 0);

export const startsWithCapital = (arr) =>
  arr.every((s) => s.length > 0 && s[0] === s[0].toUpperCase());
// every() returns true for an empty array (vacuous truth) — worth knowing.
```

### 82 — Map, Filter, Reduce (Medium)
**Tests:** reimplementing the functional trio (shows you understand callbacks + accumulators).
```js
// index.js
export function map(array, fn) {
  const result = [];
  for (let i = 0; i < array.length; i++) result.push(fn(array[i], i, array));
  return result;
}

export function filter(array, fn) {
  const result = [];
  for (let i = 0; i < array.length; i++) if (fn(array[i], i, array)) result.push(array[i]);
  return result;
}

export function reduce(array, fn, initial) {
  let acc = initial;
  let start = 0;
  if (acc === undefined) { acc = array[0]; start = 1; } // no seed -> use first element
  for (let i = start; i < array.length; i++) acc = fn(acc, array[i], i, array);
  return acc;
}
```

---

## Algorithms & complexity

### 11 — Depth-First Search (Medium)
**Tests:** graph traversal with an adjacency list, recursion + visited set.
```js
// index.js
export class Graph {
  constructor() { this.adjacencyList = new Map(); }

  addVertex(v) { if (!this.adjacencyList.has(v)) this.adjacencyList.set(v, []); }

  addEdge(v1, v2) {
    this.addVertex(v1); this.addVertex(v2);
    this.adjacencyList.get(v1).push(v2);
    this.adjacencyList.get(v2).push(v1); // undirected
  }

  dfs(start) {
    const visited = new Set();
    const result = [];
    const traverse = (vertex) => {
      if (visited.has(vertex)) return;
      visited.add(vertex);
      result.push(vertex);
      for (const neighbor of this.adjacencyList.get(vertex) ?? []) traverse(neighbor);
    };
    traverse(start);
    return result;
  }
}
```

### 35 — Searching Algorithms (Medium)
**Tests:** linear O(n) vs binary O(log n) search.
```js
// index.js
export function linearSearch(arr, key) {
  for (let i = 0; i < arr.length; i++) if (arr[i] === key) return i;
  return -1;
}

// Requires a SORTED array.
export function binarySearch(arr, key) {
  let lo = 0, hi = arr.length - 1;
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (arr[mid] === key) return mid;
    if (arr[mid] < key) lo = mid + 1;
    else hi = mid - 1;
  }
  return -1;
}
```

### 101 — Computational Complexity (Medium)
**Tests:** implement both searches and reason about their growth.
```js
// index.js  (same algorithms as #35 — the lab's focus is the Big-O comparison)
export function linearSearch(arr, key) {        // O(n) time, O(1) space
  for (let i = 0; i < arr.length; i++) if (arr[i] === key) return i;
  return -1;
}

export function binarySearch(arr, key) {        // O(log n) time, O(1) space; needs sorted input
  let lo = 0, hi = arr.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] === key) return mid;
    arr[mid] < key ? (lo = mid + 1) : (hi = mid - 1);
  }
  return -1;
}
// For n = 1,000,000: linear ≈ up to 1,000,000 checks; binary ≈ 20 checks (log2 n).
```

---

## Modules & Node core

### 2 — Child Process (Medium)
**Tests:** wrapping callback-based `exec`/`execFile` in promises.
```js
// index.js
import { exec, execFile } from 'node:child_process';

export function execCommand(command) {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) return reject(error);
      resolve(stdout);
    });
  });
}

export function execFileCommand(file, args) {
  return new Promise((resolve, reject) => {
    execFile(file, args, (error, stdout, stderr) => {
      if (error) return reject(error);
      resolve(stdout);
    });
  });
}
// Tip: util.promisify(exec) does this for you in real code.
```

### 10 — Crypto Hashing (Medium)
**Tests:** `crypto.createHash` with different algorithms.
```js
// index.js
import crypto from 'node:crypto';

const hashWith = (algorithm) => (data) =>
  crypto.createHash(algorithm).update(data).digest('hex');

export const sha256Hash = hashWith('sha256');
export const md5Hash = hashWith('md5');   // fast but cryptographically broken
export const sha1Hash = hashWith('sha1'); // also broken — avoid for security
// Hashing is one-way. For passwords use bcrypt/scrypt/argon2, not these.
```

### 13 — File Encryption & Decryption (Medium)
**Tests:** symmetric encryption with `createCipheriv` / `createDecipheriv`.
```js
// src/encrypt.js
import crypto from 'node:crypto';
import fs from 'node:fs/promises';

const ALGO = 'aes-256-cbc';

export async function encryptFile(inputPath, outputPath, key, iv) {
  const data = await fs.readFile(inputPath);
  const cipher = crypto.createCipheriv(ALGO, key, iv);
  const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
  await fs.writeFile(outputPath, encrypted);
}

// src/decrypt.js
import crypto from 'node:crypto';
import fs from 'node:fs/promises';

export async function decryptFile(inputPath, outputPath, key, iv) {
  const data = await fs.readFile(inputPath);
  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
  const decrypted = Buffer.concat([decipher.update(data), decipher.final()]);
  await fs.writeFile(outputPath, decrypted);
}
// key must be 32 bytes for aes-256, iv must be 16 bytes:
// const key = crypto.randomBytes(32); const iv = crypto.randomBytes(16);
```

### 14 — File System Permissions & Access (Medium)
**Tests:** `chmod` / `chown` / `lchmod` via the promise API.
```js
// index.js
import fs from 'node:fs/promises';

export async function changeMode(path, mode) {
  await fs.chmod(path, mode);          // e.g. 0o644
}

export async function changeOwner(path, uid, gid) {
  await fs.chown(path, uid, gid);
}

export async function changeSymlinkMode(path, mode) {
  // lchmod affects the symlink itself, not its target (macOS-only in Node).
  await fs.lchmod(path, mode);
}
```

### 27 — Circular Dependencies (Medium)
**Tests:** understanding partial exports when two modules import each other.
```js
// a.js
import { bValue } from './b.js';
export const aValue = 'A';
export function showB() { return bValue; }

// b.js
import { aValue } from './a.js';
export const bValue = 'B';
export function showA() {
  // By the time showA() is *called*, a.js has finished loading,
  // so aValue is defined. ESM live bindings make this work.
  return aValue;
}

// index.js
import { showA } from './b.js';
import { showB } from './a.js';
console.log(showB(), showA()); // "B A"
```
> The trap: reading an imported value at module-*evaluation* time (top level) instead of inside a function can give `undefined`, because the other module may be only partially initialized. Defer access into functions, or extract the shared value into a third module.

### 97 — Configuration Management (Medium)
**Tests:** an exported config object + reading JSON with `fs.promises`.
```js
// config.json
// { "host": "localhost", "port": 8080 }

// index.js
import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const config = { host: 'localhost', port: 8080 };

const __dirname = path.dirname(fileURLToPath(import.meta.url)); // ESM has no __dirname

export async function readConfig() {
  const raw = await fs.readFile(path.join(__dirname, 'config.json'), 'utf8');
  const parsed = JSON.parse(raw);
  console.log(parsed);
  return parsed;
}
```

---

### Notes & caveats
- Solutions target **Node 18+ / ESM**. For labs that specify CommonJS (none of the Medium/Hard set do), swap `export` for `module.exports`.
- A few labs (25, 78, 80, 88) describe behavior loosely without exact test signatures; the conventional signature is used and the intent matches the lab description. Adjust names if a lab's test file expects different ones.
- The Easy labs are deliberately omitted — they're one-liners best solved straight from the [Study Guide](./STUDY-GUIDE.md) decluttered asks.
