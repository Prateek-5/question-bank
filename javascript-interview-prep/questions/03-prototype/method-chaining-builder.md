# Method chaining — the `return this` builder pattern

## Source
- Common machine-coding interview problem ("build a chainable QueryBuilder" / "implement jQuery-style chaining" / "fluent API design").
- Reference: lodash `chain`, knex.js query builder, mongoose query API, jQuery — all use this pattern.

## Why this question matters in interviews
The builder pattern is a quick way to test three things at once: (1) do you know that prototype methods return `this` to enable chaining, (2) can you separate **mutation** of accumulator state from **terminal** materialization (`.build()` / `.execute()`), and (3) do you understand why `this` flows correctly through prototype methods. It's also the most realistic prototype question — every senior backend engineer has used or built a query builder (SQL, GraphQL, HTTP client). When you ship a fluent API, this is the skeleton.

## Concepts involved

### Syntax to lock in
```js
class QueryBuilder {
  constructor(table) {
    this.table = table;
    this._where = [];
    this._orderBy = null;
    this._limit = null;
  }
  where(field, op, value) {
    this._where.push({ field, op, value });
    return this;                         // <- the headline of the pattern
  }
  orderBy(field, dir = 'ASC') {
    this._orderBy = { field, dir };
    return this;
  }
  limit(n) {
    this._limit = n;
    return this;
  }
  build() {
    // Terminal — does NOT return `this`. Returns the materialized query.
    return {
      sql: this._compile(),
      params: this._params(),
    };
  }
}

const q = new QueryBuilder('users')
  .where('age', '>', 18)
  .where('country', '=', 'IN')
  .orderBy('created_at', 'DESC')
  .limit(10)
  .build();
```

### Runtime / engine behavior
- Every method on the prototype is shared across instances. `qb.where` is the same function for every `QueryBuilder` instance — only `this` changes.
- `return this` works because `qb.method()` invokes `method` with `this = qb`. Returning `this` lets the **dot-chain** continue on the same instance.
- Without `return this`, the second `.where(...)` would be called on `undefined` → `TypeError: Cannot read properties of undefined`.
- Chain mutation accumulates state on the instance; `build()` snapshots it. This is mutation-based; an immutable variant returns a *new* builder from each method (slower but composable — see Variants).

### Edge cases (these are the interview traps)
1. **Forgetting `return this`** — chain breaks on the second call with a cryptic error. Most common bug.
2. **`build()` returning `this`** — defeats the purpose. The terminal method should return the *result*, not the builder. Otherwise users can't tell when they're done.
3. **Reuse after `build()`** — if `build()` doesn't reset state, subsequent calls on the same builder reuse stale state. Decide: either (a) `build()` is single-shot (throw on second call), or (b) `build()` clones state before snapshotting.
4. **Arrow functions on the prototype** — never use `Foo.prototype.method = () => this._x`. Arrow `this` is lexical, points at the enclosing scope (likely `globalThis`). Methods must be regular functions.
5. **Method as callback** — `array.forEach(qb.where)` loses `this`. Pre-bind: `array.forEach(qb.where.bind(qb))`. Worth flagging because chain users assume `this` is automatic.
6. **Conditional chaining** — what if `.where(...)` should be a no-op when the value is null? Either return `this` unchanged (skip the push) or expose a `.when(cond, fn)` helper. Senior-friendly design choice.
7. **Subclassing the builder** — if `OrderQueryBuilder extends QueryBuilder` adds `.orderItems(...)`, `return this` correctly preserves the subclass type (because `this` is the subclass instance). Important for fluent APIs over class hierarchies.
8. **Immutable builders** — modern style: every method returns a new instance with copied state. Slower, but safer for shared/cached builders. Trade-off worth discussing.

## Brute force approach
"Pass all options to a single function call: `query('users', { where: [...], orderBy: ..., limit: ... })`." Works but loses the readability of fluent chains, conditional composition (`if (filter) qb.where(...)`), and the natural reuse of partial builders. The whole reason builders exist is to compose incrementally.

## Optimal approach
Mutation-based builder where every step returns `this` and a terminal `build()` (or `execute()` / `toSQL()`) returns the materialized output. State lives on the instance; methods live on the prototype. O(1) per chain step.

## Solution (JavaScript)

```js
class QueryBuilder {
  constructor(table) {
    this._table = table;
    this._where = [];
    this._orderBy = null;
    this._limit = null;
    this._built = false;
  }

  where(field, op, value) {
    if (value === undefined) return this;     // conditional skip
    this._where.push({ field, op, value });
    return this;
  }

  orderBy(field, dir = 'ASC') {
    this._orderBy = { field, dir: dir.toUpperCase() };
    return this;
  }

  limit(n) {
    if (!Number.isInteger(n) || n < 0) throw new RangeError('limit must be non-neg integer');
    this._limit = n;
    return this;
  }

  // Terminal — does NOT return `this`. Returns the materialized output.
  build() {
    if (this._built) throw new Error('build() can only be called once');
    this._built = true;

    const params = [];
    let sql = `SELECT * FROM ${this._table}`;

    if (this._where.length) {
      const clauses = this._where.map(({ field, op, value }) => {
        params.push(value);
        return `${field} ${op} ?`;
      });
      sql += ` WHERE ${clauses.join(' AND ')}`;
    }
    if (this._orderBy) sql += ` ORDER BY ${this._orderBy.field} ${this._orderBy.dir}`;
    if (this._limit !== null) sql += ` LIMIT ${this._limit}`;

    return { sql, params };
  }
}
```

## Step-by-step dry run

Input:
```js
const q = new QueryBuilder('users')
  .where('age', '>', 18)
  .where('country', '=', 'IN')
  .where('deleted_at', 'IS', undefined)   // skipped via conditional
  .orderBy('created_at', 'DESC')
  .limit(10)
  .build();
```

Trace:
- `new QueryBuilder('users')` → instance with `_where=[]`, `_orderBy=null`, `_limit=null`, `_built=false`.
- `.where('age', '>', 18)` → push `{age,>,18}` → returns `this` (the same instance).
- `.where('country', '=', 'IN')` → push `{country,=,'IN'}` → returns `this`. Chain has 2 where clauses.
- `.where('deleted_at', 'IS', undefined)` → `value === undefined` → skip push, return `this`. Chain unchanged.
- `.orderBy('created_at', 'DESC')` → `_orderBy = {field:'created_at', dir:'DESC'}` → return `this`.
- `.limit(10)` → integer check passes → `_limit = 10` → return `this`.
- `.build()` → snapshots state. `_built = true`. Compiles:
  - `sql = 'SELECT * FROM users WHERE age > ? AND country = ? ORDER BY created_at DESC LIMIT 10'`
  - `params = [18, 'IN']`
- Returns `{ sql, params }`. The variable `q` is now the **materialized output**, not the builder.

Second `q.where(...)` call — `q` is the result object, not the builder, so `.where` is `undefined` → `TypeError`. This is desirable: the chain has a clear terminator.

## Important takeaways

**Syntax to memorize**
- Every chainable method: `return this;` (last line, no exceptions).
- Terminal method: returns the result, NOT `this`. Common names: `build()`, `execute()`, `toSQL()`, `compile()`.
- Methods on the prototype (auto via `class` body); state on the instance (via `this._x = ...` in constructor).

**Patterns to reuse**
- "Return `this` to chain" — same pattern in lodash `chain`, jQuery, Express middleware (`app.use().get().listen()`), mocha test setup (`describe.skip.only`), knex/mongoose query builders.
- "Mutate state, then materialize via terminal" — separation of accumulation and execution. Same shape as Stream pipelines, RxJS observables, reducers.

**Common mistakes**
- Forgetting `return this` on one method — chain breaks mid-stream with a confusing error.
- Using arrow functions in the class body — wait, ES2022 class fields with `=` *do* bind `this` lexically, but arrow methods would still need `this` from the instance. Just don't use arrows on the prototype.
- Returning `this` from the terminal — users can't tell when they're done; chains never resolve.
- Sharing one builder across requests without cloning — accumulator state leaks between requests. In backend code, prefer fresh builders per call or an immutable variant.

**Related questions**
- "Implement `_.chain(arr).filter(...).map(...).value()`" — same pattern, terminal is `.value()`.
- Express-style middleware chains (`return next()`).
- "What's the difference between this builder and a Promise chain?" (Builder is sync, accumulates state; Promise chains are async, pass values through.)

## Variants

1. **Immutable builder** — "Make each method return a new builder instead of mutating." Inside each method: `const next = new QueryBuilder(this._table); Object.assign(next, this); next._where = [...this._where, newClause]; return next;`. Safer for shared/cached builders.

2. **Async terminal** — "What if `build()` should actually execute the SQL?" Make it `async execute() { return this._db.query(this._compile()); }`. Terminal returns a Promise; chain remains synchronous until then.

3. **Type-safe builder (TS)** — "How would you type this so that `.where(...)` after `.build()` is a compile error?" Phantom types / branded builders: `Builder<{ table: true; where: true; built: false }>` and `.build()` flips `built` to `true`, removing the chainable methods from the union.

## Revision notes

> **method-chaining builder — 60 second recap**
> - Every chainable method ends with `return this;`. Methods live on the prototype.
> - Terminal method (`build` / `execute` / `toSQL`) returns the **materialized output**, NOT `this`.
> - Chain works because `qb.method()` sets `this = qb`; returning `this` lets the next `.x(...)` resolve.
> - Conditional chaining: return `this` unchanged when a no-op condition is met.
> - **Trap:** forgetting `return this` on one method → cryptic `Cannot read properties of undefined`.
> - **Trap:** arrow functions on the prototype — `this` is lexical, breaks chaining.
> - **Trap:** reusing a builder after `build()` without reset → stale state. Either single-shot or clone-on-build.
> - Subclasses naturally preserve type because `this` is the actual subclass instance.
