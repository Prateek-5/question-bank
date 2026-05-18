# Bloom Filter

## Source / Origin
- Burton Howard Bloom, 1970.
- Used in: Cassandra (sstable bloom), Postgres pg_bloom, Bitcoin SPV, Chrome safe-browsing, Redis Bloom.
- Asked at: Razorpay, AWS, Atlassian, Google, Uber.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
A Bloom filter is a probabilistic membership data structure: O(1) `add` and `contains`, very low memory, with a tunable false-positive rate but *zero false negatives*. The asks are usually: "Implement it. Pick `m` and `k`. Walk through false-positive math." It tests three things at once: data-structure design, hashing intuition, and the candidate's ability to reason about *probabilistic* correctness (a senior signal — most engineers conflate "fast" with "exact").

## Concepts involved

### Syntax to lock in
```js
class BloomFilter {
  constructor({ size, hashCount }) {                 // size = bit array length m; hashCount = k
    this.size = size;
    this.k = hashCount;
    this.bits = new Uint8Array(Math.ceil(size / 8)); // 1 bit per cell, packed
  }
  add(item) {
    for (let i = 0; i < this.k; i++) {
      const idx = this._hash(item, i) % this.size;
      this.bits[idx >> 3] |= (1 << (idx & 7));
    }
  }
  contains(item) {
    for (let i = 0; i < this.k; i++) {
      const idx = this._hash(item, i) % this.size;
      if ((this.bits[idx >> 3] & (1 << (idx & 7))) === 0) return false;   // definitely NOT in set
    }
    return true;                                                            // PROBABLY in set
  }
  _hash(str, seed) {
    // simple double-hashing via FNV-1a + seed (in prod use murmurhash3)
    let h = 2166136261 ^ seed;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0);   // unsigned
  }
}
```

### Edge cases / interview traps
1. **No deletion.** Standard Bloom doesn't support remove — clearing bits would create false negatives. Use a *Counting Bloom* (k-bit counters per cell) for deletes.
2. **False positive rate (FPR)** depends on `m`, `k`, `n`. The formula: `FPR ≈ (1 − e^(−kn/m))^k`. Optimal `k = (m/n) · ln(2)`.
3. **Sizing.** For `n` items and target FPR `p`: `m = -n·ln(p) / (ln 2)^2`; `k = (m/n)·ln(2)`. Memorize: for `p=1%`, ~10 bits/item, k≈7.
4. **No false negatives.** This is the contract. If `contains` returns `false`, the item is *definitely* not there.
5. **Hash quality matters.** Bad hash → correlated bits → much higher FPR. Use murmur/xxhash; double-hashing trick: `h_i(x) = h1(x) + i·h2(x)`.
6. **Capacity is fixed at construction.** Adding beyond planned `n` blows up FPR. For unknown-size streams use **Scalable Bloom Filter** (chain of progressively larger filters).
7. **Concurrent writes** — the bit-OR is idempotent per-bit, but byte-level updates aren't atomic in plain JS; use `Atomics.or` on `SharedArrayBuffer` for multi-worker.

## Mental Model

Think of an **N-cell coatroom** where each customer gets `k` randomly assigned hooks. They tag *each* of their k hooks. To check "is this person here?", look at their k hooks: if any one is empty, definitely not here. If all are tagged, probably here — but maybe k unrelated customers tagged those hooks individually.

```
   m = 16 bits, k = 3 hash functions

   add('alice')  → hashes = [3, 7, 11]
                   bits:    0001 0001 0001 0000

   add('bob')    → hashes = [1, 7, 15]
                   bits:    0101 0001 0001 0001

   contains('alice') → check [3, 7, 11] → all set → PROBABLY YES
   contains('eve')   → hashes = [3, 9, 11]
                       check [3, 9, 11] → bit 9 is 0 → DEFINITELY NO
   contains('carol') → hashes = [1, 7, 15] (collision with bob!) → all set → FALSE POSITIVE
```

## Why interviewers care

- **Probabilistic reasoning.** A senior signal.
- **Big-system literacy.** Bloom filters underpin Cassandra, BigTable, RocksDB, Spark Bloom joins.
- **Math under the hood.** Knowing the FPR formula and how to size `m` and `k`.
- **Knowing the alternatives.** Cuckoo filter (supports delete), HyperLogLog (cardinality only), Quotient filter.

## Common beginner confusion

- **"Bloom filter stores items."** No — it stores bits *derived* from items. The items themselves are gone.
- **"k=1 is fine."** k=1 maximizes false-positive collisions. Optimal k > 1.
- **"Larger m always better."** Yes for FPR; but RAM cost grows linearly. Pick FPR target first, then size.
- **"It's like a Set."** It's like a *probabilistic* Set: `contains: true` means *maybe*, never *definitely*. `Set` is exact.
- **"I can delete by un-setting bits."** No — would create false negatives. Counting Bloom or rebuild.

## Brute force approach

```js
// Set works but uses O(n) memory of the *full* items (strings, objects)
const seen = new Set();
seen.add('user-42-event-3-2024-01-15-...');  // tens of bytes per entry
seen.has(...);
```

For 100M URLs in Chrome SafeBrowsing this would be ~10GB. Bloom: ~120MB at 1% FPR. 100× memory savings.

## Optimal approach

`k` hash functions, bit array of `m` bits. `add` sets the k bits; `contains` checks all k. Tune `(m, k)` from `(n, target_fpr)`.

## Solution (JavaScript)

```js
class BloomFilter {
  constructor({ n, fpr }) {
    const m = Math.ceil(-n * Math.log(fpr) / (Math.LN2 ** 2));
    const k = Math.max(1, Math.round((m / n) * Math.LN2));
    this.size = m;
    this.k = k;
    this.bits = new Uint8Array(Math.ceil(m / 8));
  }

  add(item) {
    const [h1, h2] = this._two(item);
    for (let i = 0; i < this.k; i++) {
      const idx = ((h1 + i * h2) >>> 0) % this.size;
      this.bits[idx >> 3] |= (1 << (idx & 7));
    }
  }

  contains(item) {
    const [h1, h2] = this._two(item);
    for (let i = 0; i < this.k; i++) {
      const idx = ((h1 + i * h2) >>> 0) % this.size;
      if ((this.bits[idx >> 3] & (1 << (idx & 7))) === 0) return false;
    }
    return true;
  }

  _two(str) {                                       // double-hashing trick
    let h1 = 2166136261;
    let h2 = 1099511628211 >>> 0;
    for (let i = 0; i < str.length; i++) {
      const c = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ c, 16777619);
      h2 = Math.imul(h2 ^ c, 2246822519);
    }
    return [h1 >>> 0, h2 >>> 0];
  }

  static estimateBits(n, fpr) { return Math.ceil(-n * Math.log(fpr) / (Math.LN2 ** 2)); }
}

const bf = new BloomFilter({ n: 1_000_000, fpr: 0.01 });
bf.add('alice@x.com');
bf.contains('alice@x.com');  // true
bf.contains('eve@x.com');    // probably false (~1% chance of false-true)
```

## Step-by-step dry run

`n=10, fpr=0.05` → `m = ceil(-10·ln(0.05)/(ln 2)²) = 63`; `k = round(63/10 · ln 2) ≈ 4`.

```
add('A')      → h1=83, h2=11 → indices = [83%63, (83+11)%63, (83+22)%63, (83+33)%63]
                                = [20, 31, 42, 53]   → set bits 20,31,42,53

contains('A') → same 4 indices → all 4 set → PROBABLY IN

contains('B') → h1=141, h2=7 → indices = [15, 22, 29, 36] → bit 15 = 0 → DEFINITELY NOT

(after adding 9 more items, ~36 of the 63 bits set)
contains('Z') → 4 indices may all happen to land on tagged bits → FALSE POSITIVE
                expected rate ≈ 5%
```

## How to think aloud in the interview

> "Bloom filter — probabilistic Set with O(1) add/contains, big memory win at the cost of tunable false positives. I'll size m and k from the FPR formula. For 1M items at 1% FPR: m≈10·n ≈ 10M bits ≈ 1.25 MB, k≈7. I'll use double-hashing — two real hashes, k synthetic via `h1 + i·h2`. Standard caveats: no false negatives, no deletes (counting bloom if needed), capacity fixed (scalable bloom for unknown size)."

## Important takeaways

- **No false negatives, tunable false positives.**
- **Size formula**: `m = -n·ln(p)/(ln 2)²`, `k = (m/n)·ln 2`.
- **Double-hashing**: two real hashes; `h_i = h1 + i·h2`.
- **No deletes** in standard Bloom; use Counting Bloom or rebuild.
- **Use cases**: cache prefilter (avoid DB hit on definite misses), set membership for huge keyspaces, dedup in streams, joinable filter in distributed queries.

## Variants

- **Counting Bloom Filter** — k-bit counter per cell (4 bits typical); supports delete; ~4× memory.
- **Scalable Bloom Filter** — chain of bloom filters, each larger than the last, when capacity is unknown.
- **Cuckoo Filter** — supports delete, smaller for low FPR (<1%), slightly more complex.
- **Quotient Filter** — better cache locality, supports merge.
- **Distributed Bloom** — share bit-array via Redis Bitmap; multi-process add via Lua atomic OR.

## Revision notes

```
BloomFilter:
  m bits + k hash functions
  add(x): set bit h_i(x) % m for i=1..k
  contains(x): all k bits set? PROBABLY YES; any 0? DEFINITELY NO
  
  sizing: m = -n·ln(p)/(ln 2)²   ; k = (m/n)·ln 2
         1% FPR ≈ 10 bits/item, k≈7
  
  no false negatives; no deletes
  double-hashing: h_i = h1 + i·h2
  variants: Counting (delete), Scalable (unbounded), Cuckoo (delete + smaller), HLL (cardinality only)
```
