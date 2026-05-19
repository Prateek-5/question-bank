# `Set.prototype.intersection` / `union` / `difference` polyfills

> **Difficulty:** Medium-Senior   |   **Time:** ~10 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md), [`07-arrays/array-set-ops.md`](../07-arrays/array-set-ops.md)
>
> **Source:** TC39 Set Methods (Stage 4, ES2025).

---

## 1. Problem statement

Polyfill ES2025 Set methods: `intersection`, `union`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`. Accept "set-like" inputs.

**Verification examples**

```js
const a = new Set([1, 2, 3]);
const b = new Set([2, 3, 4]);

a.intersection(b);                       // Set {2, 3}
a.union(b);                              // Set {1, 2, 3, 4}
a.difference(b);                         // Set {1}
a.symmetricDifference(b);                // Set {1, 4}
a.isSubsetOf(b);                         // false
a.isDisjointFrom(b);                     // false
```

**Constraints**
- Accept "set-like": `{size: number, has(v), keys()}` — not just Set.
- Smaller-set-first optimization for intersection.
- SameValueZero (handles NaN).
- Return new Set; don't mutate.
- Order: result preserves first-iterated set's order.

---

## 2. Plain-English restatement

Standard set theory ops with three twists: (1) other operand can be any set-like duck-typed value; (2) iterate the smaller set for intersection (O(min) not O(this)); (3) return new Set, immutable.

---

## 3. Why this matters in interviews

Recency signal (ES2025) + algorithmic (smaller-first) + spec literacy (set-like protocol). Real backend uses: feature flags, permission sets, tag matching, segment overlap.

---

## 4. Mental model

```
   Set-like protocol:
     other.size: number
     other.has(v): boolean
     other.keys(): Iterator
   
   Map qualifies (size, has on keys, keys() yields keys).
   Custom collections qualify if they implement this.
   
   Operations:
     intersection(other):
       iterate SMALLER of (this, other)
       if smaller is this: filter this by other.has(v)
       if smaller is other: filter other.keys() by this.has(v)
       result preserves smaller's iteration order
     
     union(other):
       new Set([...this, ...other.keys()])
       preserves this then other
     
     difference(other):
       new Set([v of this | !other.has(v)])
     
     symmetricDifference(other):
       (this \ other) ∪ (other \ this)
     
     isSubsetOf(other):
       this.size > other.size → false
       all v of this in other → true
     
     isSupersetOf(other): inverse
     
     isDisjointFrom(other):
       smaller of (this, other) — no element of smaller in larger
   
   All return new Set (or boolean for predicates).
   Don't mutate this or other.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why iterate smaller set for intersection?
> 2. What's "set-like" — does Map qualify?
> 3. Are results new Sets or same Set?

---

## 6. Brute force — walked through

```js
function intersection(a, b) {
  return new Set([...a].filter(v => b.has(v)));    // iterates `a` always
}
```

Works but always O(|a|). Spec mandates smaller-first optimization.

---

## 7. The unlocking insight

> **Set-like duck-type (size, has, keys). Smaller-first iteration. Return new Set; preserve order.**

Three properties:

1. **Duck-typed set-like input.**
2. **Smaller-first** for intersection.
3. **Non-mutating** new Set.

---

## 8. Solution (annotated)

```js
// Set-like check
function isSetLike(o) {
  return o != null &&
    typeof o.size === 'number' &&
    typeof o.has === 'function' &&
    typeof o.keys === 'function';
}

function intersection(self, other) {
  if (!isSetLike(other)) throw new TypeError('other is not set-like');
  const out = new Set();
  if (self.size <= other.size) {                                          // step 1: smaller first
    for (const v of self) {
      if (other.has(v)) out.add(v);
    }
  } else {
    for (const v of other.keys()) {
      if (self.has(v)) out.add(v);
    }
  }
  return out;
}

function union(self, other) {
  if (!isSetLike(other)) throw new TypeError('other is not set-like');
  const out = new Set(self);
  for (const v of other.keys()) out.add(v);                               // step 2: preserve order
  return out;
}

function difference(self, other) {
  if (!isSetLike(other)) throw new TypeError();
  const out = new Set();
  for (const v of self) {
    if (!other.has(v)) out.add(v);                                        // step 3: in self, not other
  }
  return out;
}

function symmetricDifference(self, other) {
  if (!isSetLike(other)) throw new TypeError();
  const out = new Set();
  for (const v of self) if (!other.has(v)) out.add(v);
  for (const v of other.keys()) if (!self.has(v)) out.add(v);
  return out;
}

function isSubsetOf(self, other) {
  if (!isSetLike(other)) throw new TypeError();
  if (self.size > other.size) return false;                                // step 4: short-circuit
  for (const v of self) if (!other.has(v)) return false;
  return true;
}

function isSupersetOf(self, other) {
  if (!isSetLike(other)) throw new TypeError();
  if (other.size > self.size) return false;
  for (const v of other.keys()) if (!self.has(v)) return false;
  return true;
}

function isDisjointFrom(self, other) {
  if (!isSetLike(other)) throw new TypeError();
  const [small, big] = self.size <= other.size ? [self, other] : [other, self];
  const iter = small === self ? self : other.keys();
  for (const v of iter) {
    if (big.has(v)) return false;
  }
  return true;
}

// Install on Set.prototype if not native
if (!Set.prototype.intersection) {
  Object.defineProperty(Set.prototype, 'intersection', {
    enumerable: false, value(other) { return intersection(this, other); },
  });
  // ... same for others
}
```

**Try it yourself**

```js
const a = new Set([1, 2, 3]);
const b = new Set([2, 3, 4]);

intersection(a, b);                                           // Set {2, 3}
union(a, b);                                                  // Set {1, 2, 3, 4}
difference(a, b);                                             // Set {1}
symmetricDifference(a, b);                                    // Set {1, 4}
isSubsetOf(new Set([1, 2]), new Set([1, 2, 3]));             // true

// NaN
new Set([NaN]).intersection(new Set([NaN]));                  // Set {NaN}  (SameValueZero)

// Set-like Map (Map qualifies)
const m = new Map([[1, 'a'], [2, 'b']]);
m.size; m.has(1); m.keys();
intersection(new Set([1, 2, 3]), m);                          // Set {1, 2}

// Native ES2025 (Node 22+)
a.intersection(b);                                            // Set {2, 3}
a.isDisjointFrom(new Set([5, 6]));                           // true

// Performance: smaller-first
const big = new Set(Array.from({length: 1_000_000}, (_, i) => i));
const small = new Set([42, 999_999, 1_000_000]);
big.intersection(small);                                      // iterates small (3 ops), not big (1M).
```

---

## 9. Step-by-step dry run

```
intersection(Set{1,2,3}, Set{2,3,4}):
  isSetLike(other) → true.
  self.size 3 ≤ other.size 3 → iterate self.
  
  v=1: other.has(1)? no.
  v=2: yes → out.add(2). out: {2}.
  v=3: yes → out.add(3). out: {2, 3}.
  
  Return {2, 3}.

intersection(big1M, small3):
  big.size 1M > small.size 3 → iterate small.
  v=42: big.has(42)? yes → add.
  v=999_999: yes → add.
  v=1_000_000: no.
  Return {42, 999_999}.
  
  Saves 999_997 iterations.

union(Set{1,2,3}, Set{2,3,4}):
  out = Set{1,2,3} (clone).
  add 2 (no-op), add 3 (no-op), add 4 → {1,2,3,4}.

NaN:
  Set.has uses SameValueZero. NaN === NaN per SVZ.
  Set{NaN}.has(NaN) → true.

Set-like Map:
  intersection(new Set([1,2,3]), new Map([[1,'a'],[2,'b']])):
    isSetLike(Map)? Map has size, has (checks keys), keys() (returns keys iterator).
    Smaller? self.size 3 > other.size 2 → iterate other.keys().
    v=1: self.has(1) yes → add.
    v=2: self.has(2) yes → add.
    Return {1, 2}.
```

---

## 10. Common confusion + traps

1. **Always iterate `this`** — should iterate smaller.
2. **`instanceof Set` check** — too strict; Map/custom break.
3. **Mutate `this`** — spec says new Set.
4. **`new Set(a).intersection(b)`** then mutate — fine; new Set.
5. **`other.keys()` for Map** — yields keys (correct); for plain Object — there's no `.keys()` (not set-like).
6. **NaN matching** — SVZ handles via `Set.has`.
7. **Result order** — first-iterated set's order.

---

## 11. Senior follow-ups & variants

### Variant 1 — Set-like Map
Map's set methods compatible.

### Variant 2 — Bitmask for finite domain
Integer bitmask; O(1) ops.

### Variant 3 — Bloom filter
Probabilistic; trade accuracy for memory.

### Variant 4 — Native methods
ES2025 native; skip polyfill on modern.

### Variant 5 — Lodash equivalents
`_.intersection`, `_.union`, `_.difference` — array versions.

---

## 12. How to think aloud

> "ES2025 set methods: `intersection`, `union`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`. Three key spec details: (1) accept any 'set-like' object — duck-typed by `size: number, has: function, keys: function`. This means Map qualifies (Map's `.size`, `.has(key)` checks keys, `.keys()` returns key iterator). Custom collections too. Don't use `instanceof Set` — too strict. (2) Smaller-set-first optimization for intersection: iterate the smaller of (this, other), check `has` on the larger. O(min(|this|, |other|)) instead of always O(|this|). Critical when comparing a 3-element filter against a million-element index. (3) All return new Set (never mutate); predicates return boolean. NaN matching: Sets use SameValueZero so `Set{NaN}.has(NaN) === true`. Order: result preserves first-iterated set's insertion order. `isSubsetOf` can short-circuit if `this.size > other.size`. `isDisjointFrom` iterates smaller. Polyfill installs only if missing (`if (!Set.prototype.intersection)`). Trap: `instanceof Set` check (breaks Map); always iterate `this` (slow); mutating; assuming order from `other`."

---

## 13. 60-second revision

> - **7 methods:** intersection, union, difference, symmetricDifference, isSubsetOf, isSupersetOf, isDisjointFrom.
> - **Set-like:** `{size, has, keys}` — Map qualifies.
> - **Smaller-first** for intersection.
> - **Non-mutating** new Set / boolean.
> - **SameValueZero** equality.
> - **`isSubsetOf` short-circuits** on size.
> - **ES2025 native** (Node 22+).
> - **Trap:** instanceof Set (too strict); always iterate this; mutate.

---

**Related:** [`07-arrays/array-set-ops.md`](../07-arrays/array-set-ops.md) · [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [cache-invalidate-by-tag.md](./cache-invalidate-by-tag.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
