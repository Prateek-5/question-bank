# Cache invalidation by tag (Redis-style)

## Source
- Inspired by Next.js `revalidateTag()`, Vercel's Data Cache, Cloudflare Cache API `purgeByTag`, and Varnish's BAN-by-tag pattern.
- Reference: Next.js cache invalidation docs (https://nextjs.org/docs/app/api-reference/functions/revalidateTag), Redis Cache Tags pattern.

## Why this question matters in interviews
"Cache invalidation by tag" is the **two-Map data-modeling problem** that separates engineers who reach for the right structure from those who try to brute-force it with linear scans. Every senior backend engineer hits this: when product data changes, invalidate every cache entry tagged `product:123`. When a user logs out, invalidate every cache entry tagged `user:42`. The naïve answer (scan all entries, check tags array, delete matches) is O(n) per invalidation. The interview-worthy answer maintains a **secondary index** — `Map<tag, Set<key>>` — that makes invalidation O(|entries-with-that-tag|), independent of total cache size. It's the same skeleton as SQL secondary indexes, full-text inverted indexes, and event-bus topic subscriptions. Nailing this question signals you can design data structures, not just use them.

## Concepts involved

### Syntax to lock in
```js
class TaggedCache {
  #store = new Map();                          // key -> value
  #tagIndex = new Map();                       // tag -> Set<key>
  #keyTags = new Map();                        // key -> Set<tag> (reverse index)

  set(key, value, tags = []) {
    this.delete(key);                          // clean old tag links
    this.#store.set(key, value);
    const tagSet = new Set(tags);
    this.#keyTags.set(key, tagSet);
    for (const t of tagSet) {
      if (!this.#tagIndex.has(t)) this.#tagIndex.set(t, new Set());
      this.#tagIndex.get(t).add(key);
    }
  }

  invalidateTag(tag) {
    const keys = this.#tagIndex.get(tag);
    if (!keys) return 0;
    for (const k of keys) this.delete(k);
    return keys.size;
  }
}
```

### Runtime / engine behavior
- **Primary store** (`Map<key, value>`): standard cache. O(1) get/set/delete.
- **Tag index** (`Map<tag, Set<key>>`): inverted index. Maps every tag to the set of keys carrying it. `invalidateTag(t)` walks `#tagIndex.get(t)` (O(|entries with that tag|)) and deletes each from the primary store.
- **Reverse index** (`Map<key, Set<tag>>`): needed to clean up the tag index when a single key is deleted. Without it, `delete(k)` would have to walk every tag's Set looking for `k` — O(#tags) per delete.
- Total space overhead: O(total tag-key pairs) — same as the count of "(key, tag)" edges. If each key has ~3 tags, the indexes weigh ~3x the primary store.
- `Set.add` / `Set.delete` are O(1). Iteration order is insertion order.

### Edge cases (these are the interview traps)
1. **Overwriting a key with different tags** — `set('a', v1, ['t1'])` then `set('a', v2, ['t2'])` must remove `'a'` from `t1`'s Set. Naive implementations leak tag→key references forever. The reverse index `#keyTags` solves this: read old tags, remove from tag index, write new.
2. **Invalidating an empty tag** — `invalidateTag('nonexistent')` should return 0, not throw.
3. **A key with no tags** — should still be cacheable; just skip the tag-index work.
4. **Tag with one remaining key, then delete** — after `delete(k)`, if `tagIndex.get(t)` is now empty, you can either leave the empty Set in place (wasteful) or delete the tag entry. Production caches usually clean up.
5. **Concurrent modification during invalidation** — iterating `#tagIndex.get(tag)` while `delete()` removes from it: in JS, V8 allows removing the current key during `for...of` on a Set. But `delete()` also mutates `#tagIndex` itself — same Set being iterated. Snapshot with `Array.from(...)` to be safe.
6. **Invalidation cascade** — should invalidating `tag:product` also invalidate `tag:product:123`? No, by default tags are strings, not hierarchies. If you want prefix invalidation, that's a different data structure (Trie or a third index).
7. **Tag explosion** — keys with hundreds of tags inflate memory. Cap tags per key, or use compact bitset-based tags for known small tag-universe.
8. **TTL interaction** — when a TTL expires a key, the tag index must also be cleaned. Easy to forget. Make `delete` the single source of cleanup, and have the TTL handler call it.

## Brute force approach
Single `Map<key, { value, tags }>`. `invalidateTag(tag)` scans every entry, checks if `entry.tags.includes(tag)`, deletes if so. **O(n) per invalidation** where n = total entries — independent of how many entries actually have the tag. For a 10⁶-entry cache invalidating a tag that hits 5 entries, you still scan all 10⁶. Fine on a toy cache; terrible at scale.

## Optimal approach
**Maintain three Maps:**

1. `#store: Map<key, value>` — primary cache.
2. `#tagIndex: Map<tag, Set<key>>` — for each tag, the set of keys carrying it. Lets `invalidateTag(t)` directly enumerate affected keys in O(|hits|).
3. `#keyTags: Map<key, Set<tag>>` — reverse index. Lets `delete(k)` remove `k` from every tag's Set in O(|tags-of-k|), no scan.

Cost model:
- `set(k, v, tags)`: O(|tags|).
- `delete(k)`: O(|tags-of-k|).
- `invalidateTag(t)`: O(|keys-with-t|).
- Storage: O(total (key, tag) edges).

The trade is **memory for time**. Pay 2-3x storage to make tagged invalidation proportional to the work done, not the cache size.

## Solution (JavaScript)

```js
/**
 * Cache with O(1) tagged invalidation via inverted index.
 */
class TaggedCache {
  #store = new Map();                          // key -> value
  #tagIndex = new Map();                       // tag -> Set<key>
  #keyTags = new Map();                        // key -> Set<tag>

  /** @param {string} key  @param {*} value  @param {string[]} tags */
  set(key, value, tags = []) {
    if (this.#store.has(key)) this.#unlinkKey(key);       // clear old tags

    this.#store.set(key, value);

    if (tags.length === 0) return;
    const tagSet = new Set(tags);                          // dedupe
    this.#keyTags.set(key, tagSet);
    for (const t of tagSet) {
      let keys = this.#tagIndex.get(t);
      if (!keys) { keys = new Set(); this.#tagIndex.set(t, keys); }
      keys.add(key);
    }
  }

  get(key) { return this.#store.get(key); }
  has(key) { return this.#store.has(key); }

  /** Delete a single key and clean up its tag links. */
  delete(key) {
    if (!this.#store.has(key)) return false;
    this.#unlinkKey(key);
    return this.#store.delete(key);
  }

  /** Invalidate all entries carrying `tag`. Returns count deleted. */
  invalidateTag(tag) {
    const keys = this.#tagIndex.get(tag);
    if (!keys) return 0;

    // Snapshot — we're about to mutate `keys` via `delete()` -> `#unlinkKey`.
    const snapshot = [...keys];
    for (const k of snapshot) this.delete(k);
    this.#tagIndex.delete(tag);                            // tag is now empty
    return snapshot.length;
  }

  clear() {
    this.#store.clear();
    this.#tagIndex.clear();
    this.#keyTags.clear();
  }

  get size() { return this.#store.size; }

  /** Internal: remove `key` from every tag's Set without touching #store. */
  #unlinkKey(key) {
    const tags = this.#keyTags.get(key);
    if (!tags) return;
    for (const t of tags) {
      const keys = this.#tagIndex.get(t);
      if (!keys) continue;
      keys.delete(key);
      if (keys.size === 0) this.#tagIndex.delete(t);       // cleanup empty tag
    }
    this.#keyTags.delete(key);
  }
}
```

## Step-by-step dry run

```js
const cache = new TaggedCache();

cache.set('product:1', { name: 'Shoe' },  ['products', 'category:footwear']);
cache.set('product:2', { name: 'Sock' },  ['products', 'category:footwear']);
cache.set('product:3', { name: 'Lamp' },  ['products', 'category:home']);
cache.set('user:42',   { name: 'Alice' }, ['users']);
```

State after writes:
- `#store`: 4 entries.
- `#tagIndex`:
  - `'products'` → `{'product:1', 'product:2', 'product:3'}`
  - `'category:footwear'` → `{'product:1', 'product:2'}`
  - `'category:home'` → `{'product:3'}`
  - `'users'` → `{'user:42'}`
- `#keyTags`: 4 entries, each mapping the key to its tag Set.

Now invalidate `'category:footwear'`:

```js
cache.invalidateTag('category:footwear');    // returns 2
```

Trace:
- `#tagIndex.get('category:footwear')` → Set `{'product:1', 'product:2'}`.
- Snapshot: `['product:1', 'product:2']`.
- `delete('product:1')`:
  - `#unlinkKey('product:1')`: tags are `['products', 'category:footwear']`. Remove `'product:1'` from `#tagIndex.get('products')` → leaves `{'product:2', 'product:3'}`. Remove from `'category:footwear'` Set → leaves `{'product:2'}` (we'll clear it below).
  - `#store.delete('product:1')`.
- `delete('product:2')`: similar. After unlink, `'category:footwear'` Set is now empty → deleted from `#tagIndex`. `'products'` Set is now `{'product:3'}`.
- `#tagIndex.delete('category:footwear')` (already gone, no-op).
- Returns 2.

Final state: `#store` has `'product:3'` and `'user:42'`. `#tagIndex` has `'products' → {'product:3'}`, `'category:home' → {'product:3'}`, `'users' → {'user:42'}`. **Indexes are consistent — no dangling pointers.**

## Important takeaways

**Syntax to memorize**
- Three Maps: primary, tag-to-keys, key-to-tags.
- `Map<tag, Set<key>>` is the inverted index — the heart of tagged invalidation.
- `Map<key, Set<tag>>` is the reverse index — the unsung hero that makes single-key deletes cheap.
- Snapshot before iterating + mutating: `for (const k of [...keys])` — `Array.from(keys)`.

**Patterns to reuse**
- **Inverted index** — same data shape powers full-text search (`Map<term, Set<docId>>`), event bus subscriptions (`Map<topic, Set<handler>>`), permission checks (`Map<role, Set<userId>>`), feature flags by segment.
- **Two-way index for cheap removal** — any time you have a many-to-many relation in memory, maintain both directions. The cost is memory + write complexity; the reward is constant-time deletion from either side.
- **Snapshot-before-mutate** — when you're iterating a collection that the loop body mutates, materialize the iteration target first.

**Common mistakes**
- Single Map with tags-as-array on each entry → O(n) invalidation. The trap question.
- Forgetting the reverse `#keyTags` index → `delete(k)` becomes O(#tags-globally).
- Forgetting to unlink old tags when overwriting a key → tag index accumulates dead pointers; `invalidateTag` returns count > actual deletes.
- Iterating `#tagIndex.get(tag)` while calling `delete()` inside the loop — `delete` mutates the same Set. Snapshot first.
- Not cleaning up empty tag Sets → memory leak over time as tags churn.
- Forgetting that TTL-driven expiry must also call `delete()` so the indexes stay consistent.

**Complexity table**
| Op                   | Time                       | Space (delta)              |
|----------------------|----------------------------|----------------------------|
| `set(k, v, tags)`    | O(\|tags\|)                | O(\|tags\|)                |
| `get(k)` / `has(k)`  | O(1)                       | 0                          |
| `delete(k)`          | O(\|tags-of-k\|)           | -O(\|tags-of-k\|)          |
| `invalidateTag(t)`   | O(\|keys-with-t\|)         | -O(\|edges-of-t\|)         |

**Related questions**
- LRU Cache (combine with this for production cache)
- Event bus with topic subscriptions
- Full-text inverted index (Lucene-style)
- LeetCode #146 LRU Cache, #460 LFU Cache

## Variants

1. **Hierarchical tags** — `product`, `product:123`, `product:123:price`. Invalidating `product` should invalidate everything beneath. Use a **Trie of tags** instead of a flat Map. Or normalize to a list of prefixes when tagging and store each prefix in the flat index.

2. **Wildcard tags** — `invalidateTagPattern('user:*')`. Either iterate all tag keys (O(#tags)) or pre-build a Trie. The flat Map doesn't naturally support patterns.

3. **TTL + tagged invalidation combo** — extend `set` to take a `ttl` and combine with the LazyTTLMap pattern. Expiry must go through `delete()` so the indexes stay consistent.

4. **Distributed version (Redis)** — use Redis Sets keyed by tag (`SADD tag:products key1`), with `SMEMBERS` and pipelined `DEL`. Same algorithm, different substrate. Mention this for "scale" questions.

5. **Reference counting per (key, tag)** — if the same tag can be attached multiple times (e.g. by different writers), use `Map<tag, Map<key, count>>` instead of `Map<tag, Set<key>>`. Decrement on delete; remove when count hits 0.

6. **Memory-bounded LRU + tags** — when size exceeds limit, evict LRU. Eviction goes through `delete()` so indexes stay consistent. This is essentially Next.js's data cache.

## Revision notes

> **cache-invalidate-by-tag — 60 second recap**
> - **Three Maps**: `store: Map<k,v>`, `tagIndex: Map<tag, Set<k>>`, `keyTags: Map<k, Set<tag>>`.
> - `set(k, v, tags)`: O(|tags|). On overwrite, **unlink old tags first**.
> - `delete(k)`: O(|tags-of-k|) — uses reverse index.
> - `invalidateTag(t)`: O(|keys-with-t|), **snapshot** the key Set before mutating.
> - Clean up empty tag Sets to avoid leaks.
> - Pattern: **inverted index + reverse index** = constant-time many-to-many removal.
> - Same skeleton as event-bus topics, full-text search, permission lookups.
> - Naïve single-Map answer is O(n) per invalidation — the trap.
