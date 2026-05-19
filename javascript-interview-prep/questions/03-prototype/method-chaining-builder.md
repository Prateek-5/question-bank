# Method chaining — the `return this` builder pattern

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [this-keyword-nodejs.md](./this-keyword-nodejs.md)
>
> **Source:** Knex.js, mongoose, jQuery, lodash chain. Common machine-coding interview.

---

## 1. Problem statement

Build a fluent API (QueryBuilder) where methods return `this` to enable chaining.

**Verification examples**

```js
const sql = new QueryBuilder('users')
  .where('age', '>', 18)
  .where('status', '=', 'active')
  .orderBy('name')
  .limit(10)
  .build();

// "SELECT * FROM users WHERE age > 18 AND status = 'active' ORDER BY name ASC LIMIT 10"
```

**Constraints**
- Each mutator returns `this`.
- Terminal method (`.build()` / `.execute()`) returns materialized result.
- State accumulated on instance.

---

## 2. Plain-English restatement

Methods that mutate state return `this` so you can chain. Terminal method finalizes and returns the result.

---

## 3. Why this matters in interviews

Real backend pattern (query builders, ORMs, jQuery). Tests `this` flow + state separation.

---

## 4. Mental model

```
   class Builder {
     mutator() {
       this._state.something = value;
       return this;                  ← THE pattern
     }
     terminal() {
       return finalizeOf(this._state);
     }
   }
   
   builder.a().b().c().build()
            ▲   ▲   ▲    ▲
            this this this final result

   State stored on instance (this._field).
   Methods on prototype.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why return `this` from mutator methods?
> 2. Where does state live — prototype or instance?
> 3. What does the terminal method return?

---

## 6. Brute force — walked through

### Wrong attempt 1: return undefined
Chain breaks at first call.

### Wrong attempt 2: return new instance per call
Wastes allocations; harder to track state.

### Wrong attempt 3: state on prototype
Shared across instances — bug.

---

## 7. The unlocking insight

> **Mutator methods return `this`. State on instance via `this._field`. Terminal method materializes.**

Three properties:

1. **`return this`** — enable chaining.
2. **State on instance** — not prototype.
3. **Terminal method** materializes.

---

## 8. Solution (annotated)

```js
class QueryBuilder {
  constructor(table) {
    this.table = table;                                                  // step 1: instance state
    this._where = [];
    this._orderBy = null;
    this._limit = null;
  }

  where(field, op, value) {
    this._where.push({ field, op, value });
    return this;                                                          // step 2: chain
  }

  orderBy(field, dir = 'ASC') {
    this._orderBy = { field, dir };
    return this;
  }

  limit(n) {
    this._limit = n;
    return this;
  }

  build() {                                                                // step 3: terminal
    let sql = `SELECT * FROM ${this.table}`;
    if (this._where.length) {
      sql += ' WHERE ' + this._where.map((c) => `${c.field} ${c.op} ${typeof c.value === 'string' ? `'${c.value}'` : c.value}`).join(' AND ');
    }
    if (this._orderBy) sql += ` ORDER BY ${this._orderBy.field} ${this._orderBy.dir}`;
    if (this._limit != null) sql += ` LIMIT ${this._limit}`;
    return sql;
  }
}

// Chain
new QueryBuilder('users')
  .where('age', '>', 18)
  .where('status', '=', 'active')
  .orderBy('name')
  .limit(10)
  .build();
```

**Try it yourself**

```js
// Immutable variant (returns new instance per call — Redux-style)
class ImmutableBuilder {
  constructor(state = {}) { Object.assign(this, state); }
  where(field, op, value) {
    return new ImmutableBuilder({
      ...this,
      _where: [...(this._where || []), { field, op, value }],
    });
  }
  // ...
}
// Trade-off: allocations per call, but safer for reuse.
```

---

## 9. Step-by-step dry run

```
new QueryBuilder('users')         → builder { table:'users', _where:[], _orderBy:null, _limit:null }
  .where('age', '>', 18)           → builder._where pushed; return this → same builder
  .where('status', '=', 'active')  → push; return this
  .orderBy('name')                  → set; return this
  .limit(10)                        → set; return this
  .build()                          → assemble SQL from state, return string

Each chain step returns SAME builder instance; state accumulates.
Terminal .build() returns finalized result.
```

---

## 10. Common confusion + traps

1. **Return undefined** — breaks chain.
2. **State on prototype** — shared across instances.
3. **Mutator + terminal mixed** — separate concerns.
4. **Methods need `this`** — arrow functions on object literal break.
5. **Immutable variant** — heavier allocations but reuse-safe.
6. **`new` not required** — `QueryBuilder('users')` without `new` → `this` undefined.
7. **Reusing builder** — state persists; reset or use immutable.

---

## 11. Senior follow-ups & variants

### Variant 1 — Immutable variant
Each method returns new instance; safer reuse, more allocations.

### Variant 2 — Async terminal
`.execute()` returns Promise.

### Variant 3 — Validation in terminal
Throw if required fields missing.

### Variant 4 — Type-safe TypeScript
Generic state types narrow as you chain.

### Variant 5 — Lazy evaluation
Don't build SQL until `.execute()` runs.

---

## 12. How to think aloud

> "Method chaining: each mutator returns `this`, so calls can be chained. State lives on the INSTANCE (`this._field`), not prototype (shared). Terminal method materializes the result (`.build()` returns string, `.execute()` returns Promise). Used by knex, mongoose, jQuery, lodash chain. Trade-off: mutable (shared state — single instance) vs immutable (returns new instance per call — safer reuse, more allocations). Trap: forget `return this` (chain breaks); state on prototype (shared); arrow methods on object literal (no `this` from receiver)."

---

## 13. 60-second revision

> - **Mutator methods return `this`** — enable chain.
> - **State on instance** (`this._field`), NOT prototype.
> - **Terminal method** materializes.
> - **Used in:** knex, mongoose, jQuery, lodash.
> - **Immutable variant:** return new instance — safer reuse.
> - **Trap:** forget return this; state on prototype; arrow in object literal.

---

**Related:** [this-keyword-nodejs.md](./this-keyword-nodejs.md) · [mixin-composition-pattern.md](./mixin-composition-pattern.md) · [getter-setter-via-prototype.md](./getter-setter-via-prototype.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
