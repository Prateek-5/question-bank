# Bloom Filter — probabilistic set membership

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [set-polyfill.md](./set-polyfill.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** Burton Howard Bloom (1970). Cassandra sstable, Postgres pg_bloom, Chrome safe-browsing, Redis Bloom. Razorpay, AWS, Atlassian, Google, Uber.

---

## 1. Problem statement

**Signature**
```ts
class BloomFilter {
  constructor(opts: { n: number; fpr: number });   // sizes m and k automatically
  add(item: string): void;
  contains(item: string): boolean;
}
```

**Input / Output examples**

| Setup                                  | Behaviour                                              |
|----------------------------------------|---------------------------------------------------------|
| `add('alice'); contains('alice')`       | `true` (definitely)                                     |
| `add('alice'); contains('bob')`         | `false` (definitely) OR `true` (false positive)         |
| `contains` after no `add`                | `false`                                                  |
| FPR target 1%, n=1M                      | ~10 bits/item ≈ 1.25 MB; k≈7                            |
| `n=10, fpr=0.05`                         | `m≈63, k≈4`                                              |

**Constraints**
- **No false negatives** — if `contains` returns `false`, item definitely NOT added.
- **Tunable false positive rate.**
- Sizing: `m = -n·ln(p)/(ln 2)²`; `k = (m/n)·ln 2`.
- No deletes in standard Bloom (use Counting Bloom for delete).
- Capacity fixed at construction (use Scalable Bloom for unknown n).

---

## 2. Plain-English restatement

A space-efficient probabilistic Set. Stores N items in ~10 bits/item (vs ~30+ bytes/item for `Set<string>`). Hashes each item into `k` bit positions; sets those bits on `add`; checks all `k` on `contains`. **`contains` true means PROBABLY in; false means DEFINITELY not in.** Used as cache pre-filter: "is this URL malicious? Bloom check first; only consult expensive DB if maybe."

---

## 3. Why this matters in interviews

Probabilistic data-structure literacy — a senior signal. Probes: data-structure design, hashing intuition, ability to reason about probabilistic correctness, knowing alternatives (Cuckoo, HyperLogLog).

---

## 4. Mental model

```
   m = 16 bits; k = 3 hash functions

   add('alice'): hashes = [3, 7, 11]
                 bits: 0001 0001 0001 0000
                       └─3──┘└─7──┘└─11─┘

   add('bob'):   hashes = [1, 7, 15]
                 bits: 0101 0001 0001 0001
                       (bit 7 shared with alice — that's fine)

   contains('alice'): check [3, 7, 11] → all 1 → PROBABLY YES
   contains('eve'):   hashes = [3, 9, 11]
                       check [3, 9, 11] → bit 9 is 0 → DEFINITELY NO
   contains('carol'): hashes = [1, 7, 15] (same as bob by chance!)
                       all 1 → FALSE POSITIVE

   "No false negatives" → if any one bit is 0, item DEFINITELY not added.
   "Tunable false positives" → false-yes possible due to collisions.
```

**Sizing math:**
- For `n` items, target FPR `p`:
  - `m = ⌈-n·ln(p) / (ln 2)²⌉`
  - `k = ⌈(m/n) · ln 2⌉`
- Memorize: **1% FPR ≈ 10 bits/item, k≈7**.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why no false negatives?
> 2. Why does Bloom not support deletion?
> 3. For 1M items at 1% FPR, how many MB?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Set<string>`
Works, but ~30 bytes/item. For 100M URLs → ~3GB. Bloom: ~120MB at 1% FPR. 25× savings.

### Wrong attempt 2: k=1
Maximizes false-positive rate. Optimal `k > 1`.

### Wrong attempt 3: deletion by unsetting bits
Two items share bit 7. Unset alice's bit 7 → bob's `contains` returns false → FALSE NEGATIVE. Use Counting Bloom or rebuild.

---

## 7. The unlocking insight

> **`k` hash functions, bit array of `m` bits. `add` sets `k` bits; `contains` checks ALL `k`. Any 0 → definitely not. All 1 → probably yes. Double-hashing trick: `h_i(x) = h1(x) + i·h2(x)` — two real hashes, k synthetic.**

Three properties:

1. **No false negatives** — Bloom invariant; never break by allowing delete.
2. **Sizing formula** — `m = -n·ln(p)/(ln 2)²`, `k = (m/n)·ln 2`.
3. **Double-hashing** — two real hashes generate `k` synthetic positions.

---

## 8. Solution (annotated)

```js
class BloomFilter {
  constructor({ n, fpr }) {
    const m = Math.ceil(-n * Math.log(fpr) / (Math.LN2 ** 2));        // step 1: size m
    const k = Math.max(1, Math.round((m / n) * Math.LN2));             // step 2: size k
    this.size = m;
    this.k = k;
    this.bits = new Uint8Array(Math.ceil(m / 8));                       // step 3: packed bits
  }

  add(item) {
    const [h1, h2] = this._two(item);
    for (let i = 0; i < this.k; i++) {
      const idx = ((h1 + i * h2) >>> 0) % this.size;                    // step 4: double-hash
      this.bits[idx >> 3] |= (1 << (idx & 7));                          // set bit
    }
  }

  contains(item) {
    const [h1, h2] = this._two(item);
    for (let i = 0; i < this.k; i++) {
      const idx = ((h1 + i * h2) >>> 0) % this.size;
      if ((this.bits[idx >> 3] & (1 << (idx & 7))) === 0) return false; // step 5: any 0 → not in
    }
    return true;                                                         // all 1 → probably in
  }

  _two(str) {                                                            // step 6: FNV-1a-like
    let h1 = 2166136261;
    let h2 = 1099511628211 >>> 0;
    for (let i = 0; i < str.length; i++) {
      const c = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ c, 16777619);
      h2 = Math.imul(h2 ^ c, 2246822519);
    }
    return [h1 >>> 0, h2 >>> 0];
  }
}
```

**Try it yourself**

```js
const bf = new BloomFilter({ n: 1_000_000, fpr: 0.01 });
bf.add('alice@example.com');
bf.add('bob@example.com');

bf.contains('alice@example.com');     // true (definitely)
bf.contains('eve@example.com');       // probably false (~1% chance of FP)

// Cache pre-filter use case
async function lookupUser(email) {
  if (!bloomOfActiveEmails.contains(email)) return null;   // fast no
  return db.query('SELECT * FROM users WHERE email = $1', [email]);
}
```

---

## 9. Step-by-step dry run

```
n=10, fpr=0.05.
m = ⌈-10 · ln(0.05) / (ln 2)²⌉ = ⌈-10 · -2.996 / 0.480⌉ = ⌈62.4⌉ = 63.
k = round(63/10 · ln 2) = round(4.37) ≈ 4.

add('A'):
  h1=83, h2=11
  indices = [(83+0·11)%63, (83+11)%63, (83+22)%63, (83+33)%63]
          = [20, 31, 42, 53]
  set bits 20, 31, 42, 53.

contains('A'):
  same indices → all 4 set → PROBABLY YES.

contains('B'):
  h1=141, h2=7
  indices = [15, 22, 29, 36]
  bit 15 is 0 → DEFINITELY NOT.

(After adding 9 more items, ~36 of 63 bits set.)
contains('Z'):
  4 indices may all happen to land on tagged bits → FALSE POSITIVE.
  Expected rate ≈ 5% (matches target).
```

---

## 10. Common confusion + traps

1. **"Stores items"** — no, stores bits derived from items.
2. **k=1** — maximizes false positives.
3. **Larger m always better** — but linear RAM cost. Pick FPR target first.
4. **Same as `Set`** — Set is exact; Bloom is probabilistic.
5. **Delete by unsetting bits** — creates false negatives. Use Counting Bloom.
6. **Add beyond planned n** — FPR balloons. Use Scalable Bloom for unknown size.
7. **Bad hash quality** — correlated bits → much higher FPR. Use murmur/xxhash.

---

## 11. Senior follow-ups & variants

### Variant 1 — Counting Bloom Filter
k-bit counter per cell (4 bits typical); supports delete; ~4× memory.

### Variant 2 — Scalable Bloom Filter
Chain of progressively larger filters; capacity unbounded.

### Variant 3 — Cuckoo Filter
Supports delete; smaller for low FPR (<1%); slightly more complex.

### Variant 4 — HyperLogLog
Estimates **cardinality** (count of unique items), not membership. Different problem.

### Variant 5 — Distributed Bloom
Share bit-array via Redis Bitmap; multi-process `add` via atomic Lua OR.

### Variant 6 — Quotient Filter
Better cache locality, supports merge.

---

## 12. How to think aloud

> "Bloom filter — probabilistic Set. `m` bits + `k` hash functions. `add` sets k bits; `contains` checks all k — any 0 means definitely not, all 1 means probably yes. No false negatives by design; tunable false positives. Sizing: `m = -n·ln(p)/(ln 2)²`, `k = (m/n)·ln 2`. For 1M items at 1% FPR: ~1.25 MB, k≈7. Double-hashing trick: two real hashes, `h_i = h1 + i·h2`. No deletes in standard (use Counting Bloom). Capacity fixed; for unknown n use Scalable Bloom. Use case: cache pre-filter — Bloom says 'definitely not' fast, expensive DB lookup only for 'maybe'. Trap: deleting by unsetting bits (false negatives); too few hash functions; bad hash quality."

---

## 13. 60-second revision

> - **`m` bits + `k` hashes; add sets all k, contains checks all k.**
> - **No false negatives;** tunable false positives.
> - **Sizing:** `m = -n·ln(p)/(ln 2)²`, `k = (m/n)·ln 2`.
> - **1% FPR ≈ 10 bits/item, k≈7.**
> - **Double-hashing** `h_i = h1 + i·h2`.
> - **No deletes** (Counting Bloom); fixed capacity (Scalable Bloom).
> - **Use:** cache pre-filter, dedup in streams, SSTable filter, SafeBrowsing.
> - **Family:** Counting Bloom (delete), Scalable Bloom (unbounded), Cuckoo (delete + smaller), HLL (cardinality).
> - **Trap:** delete-by-unset; k=1; treating as Set.

---

**Related:** [set-polyfill.md](./set-polyfill.md) · [lru-cache.md](./lru-cache.md) · [memoize.md](./memoize.md) · [bfs-with-concurrency.md](./bfs-with-concurrency.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
