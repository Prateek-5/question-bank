# Cache invalidation by tag

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [lru-cache-with-map.md](./lru-cache-with-map.md), [ttl-map.md](./ttl-map.md)
>
> **Source:** Next.js `revalidateTag`, Vercel Data Cache, Cloudflare `purgeByTag`, Varnish BAN.

---

## 1. Problem statement

Cache entries have one or more tags. Invalidate-by-tag should be O(|entries with that tag|), not O(total cache).

**Verification examples**

```js
const c = new TaggedCache();
c.set('user:42:profile', {...}, ['user:42', 'profile']);
c.set('user:42:settings', {...}, ['user:42', 'settings']);
c.set('post:7', {...}, ['post:7']);

c.invalidateTag('user:42');               // evicts 2 entries
c.get('user:42:profile');                 // undefined
c.get('post:7');                          // still there
```

**Constraints**
- O(1) get/set.
- O(matching entries) invalidate-by-tag.
- Reverse index needed for cleanup on `set`/`delete`.
- All references removed (no dangling).

---

## 2. Plain-English restatement

Two maps: primary `Map<key, value>` and secondary `Map<tag, Set<key>>`. On set: link tags both ways. On invalidateTag: walk tag→keys, delete each.

---

## 3. Why this matters in interviews

Two-Map data-modeling problem. Same skeleton as SQL secondary indexes, inverted indexes, event-bus topic routing. Signals you can design structures, not just use them.

---

## 4. Mental model

```
   Primary:    Map<key, value>
   Tag index:  Map<tag, Set<key>>
   Reverse:    Map<key, Set<tag>>    ← needed for cleanup on delete/overwrite
   
   set(key, value, tags):
     delete(key)                          ← clean old tag links
     primary.set(key, value)
     reverse.set(key, Set(tags))
     for t in tags:
       tagIndex.get(t) ?? .set(t, new Set())
       tagIndex.get(t).add(key)
   
   delete(key):
     primary.delete(key)
     for t in reverse.get(key) ?? []:
       tagIndex.get(t).delete(key)
       if tagIndex.get(t).size === 0: tagIndex.delete(t)
     reverse.delete(key)
   
   invalidateTag(tag):
     keys = tagIndex.get(tag) ?? Set()
     for k of [...keys]:    ← clone, since delete mutates
       delete(k)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why reverse index?
> 2. Why clone the Set before iterating in invalidateTag?
> 3. What happens on set with new tags for existing key?

---

## 6. Brute force — walked through

```js
class NaiveCache {
  data = new Map();           // {value, tags}
  invalidateTag(tag) {
    for (const [k, e] of this.data) {           // O(n) — scans ALL
      if (e.tags.includes(tag)) this.data.delete(k);
    }
  }
}
```

O(n) per invalidation. For 1M entries, slow.

---

## 7. The unlocking insight

> **Two-Map design: primary + secondary tag→keys index + reverse key→tags for cleanup. O(matches) invalidation.**

Three properties:

1. **Forward + reverse indexes.**
2. **Cleanup on delete/overwrite.**
3. **Clone keys before mutating iteration.**

---

## 8. Solution (annotated)

```js
class TaggedCache {
  #store = new Map();                                                     // step 1: primary
  #tagIndex = new Map();                                                  // step 2: tag → keys
  #keyTags = new Map();                                                   // step 3: key → tags (reverse)

  set(key, value, tags = []) {
    this.delete(key);                                                      // step 4: clean old links
    this.#store.set(key, value);
    const tagSet = new Set(tags);
    this.#keyTags.set(key, tagSet);
    for (const t of tagSet) {
      if (!this.#tagIndex.has(t)) this.#tagIndex.set(t, new Set());
      this.#tagIndex.get(t).add(key);                                      // step 5: forward link
    }
  }

  get(key) {
    return this.#store.get(key);
  }

  delete(key) {
    if (!this.#store.has(key)) return false;
    this.#store.delete(key);
    const tags = this.#keyTags.get(key);
    if (tags) {
      for (const t of tags) {                                              // step 6: unlink
        const keys = this.#tagIndex.get(t);
        keys.delete(key);
        if (keys.size === 0) this.#tagIndex.delete(t);                     // step 7: clean empty
      }
      this.#keyTags.delete(key);
    }
    return true;
  }

  invalidateTag(tag) {
    const keys = this.#tagIndex.get(tag);
    if (!keys) return 0;
    let count = 0;
    for (const k of [...keys]) {                                            // step 8: clone (delete mutates)
      if (this.delete(k)) count++;
    }
    return count;
  }

  invalidateAllTags(tags) {
    let total = 0;
    for (const t of tags) total += this.invalidateTag(t);
    return total;
  }
}
```

**Try it yourself**

```js
const c = new TaggedCache();
c.set('user:42:profile', { name: 'A' }, ['user:42', 'profile']);
c.set('user:42:settings', { lang: 'en' }, ['user:42', 'settings']);
c.set('user:7:profile', { name: 'B' }, ['user:7', 'profile']);

c.get('user:42:profile');                                     // {name:'A'}

c.invalidateTag('user:42');                                   // 2 (evicts profile + settings)
c.get('user:42:profile');                                     // undefined
c.get('user:7:profile');                                      // {name:'B'} — still there

c.invalidateTag('profile');                                   // 1 (evicts user:7 profile only)

// Combine with TTL
class TaggedTTLCache extends TaggedCache {
  set(key, value, opts = {}) {
    const { tags = [], ttl = 60_000 } = opts;
    super.set(key, { value, exp: Date.now() + ttl }, tags);
  }
  get(key) {
    const entry = super.get(key);
    if (!entry) return undefined;
    if (entry.exp < Date.now()) { this.delete(key); return undefined; }
    return entry.value;
  }
}

// Stats
c.size;                                                        // ... add accessor
c.tagSize('user:42');                                          // number of entries tagged
```

---

## 9. Step-by-step dry run

```
c.set('user:42:profile', v1, ['user:42', 'profile']):
  delete('user:42:profile') → no-op.
  store: {'user:42:profile': v1}.
  keyTags: {'user:42:profile': Set{'user:42', 'profile'}}.
  tagIndex:
    'user:42' → Set{'user:42:profile'}.
    'profile' → Set{'user:42:profile'}.

c.set('user:42:settings', v2, ['user:42', 'settings']):
  store: {..., 'user:42:settings': v2}.
  tagIndex:
    'user:42' → Set{'user:42:profile', 'user:42:settings'}.
    'settings' → Set{'user:42:settings'}.

c.invalidateTag('user:42'):
  keys = Set{'user:42:profile', 'user:42:settings'}.
  Clone: ['user:42:profile', 'user:42:settings'].
  
  delete('user:42:profile'):
    store.delete. tags=Set{'user:42','profile'}.
    tagIndex['user:42'].delete(key) → Set{'user:42:settings'}.
    tagIndex['profile'].delete(key) → Set{} → delete 'profile' tag entirely.
    keyTags.delete.
  
  delete('user:42:settings'):
    store.delete. tags=Set{'user:42','settings'}.
    tagIndex['user:42'].delete → Set{} → delete 'user:42' tag.
    tagIndex['settings'].delete → Set{} → delete 'settings'.
    keyTags.delete.
  
  Return 2.

Why clone before iterate:
  invalidateTag iterates tagIndex.get(tag).
  Each delete(k) mutates that same set (removes k).
  Mutating Set during iteration → undefined behavior in JS spec.
  Clone via [...keys] is safe.
```

---

## 10. Common confusion + traps

1. **No reverse index** — can't clean tagIndex on delete; orphans.
2. **Iterate Set during mutation** — broken.
3. **Don't clean empty tag entries** — tagIndex grows.
4. **`set` over existing key** — must clean old tags first.
5. **Overlapping tags** — single invalidateTag removes from multiple tag indexes.
6. **TTL + tags** — combine; check expiry in get/set.
7. **Concurrent access** — JS single-threaded; safe per turn.

---

## 11. Senior follow-ups & variants

### Variant 1 — TTL + Tags
Combined eviction policies.

### Variant 2 — LRU + Tags
Track recency + tag invalidation.

### Variant 3 — Persistent (Redis)
SADD/SREM tag→keys; DEL on invalidate.

### Variant 4 — Hierarchical tags
`user:*` invalidates all `user:42`, `user:7`.

### Variant 5 — Eventbus integration
Publish event → invalidateTag on subscribers.

---

## 12. How to think aloud

> "Tag-based cache invalidation: naive scan-all is O(n) per call — for million-entry caches, dies. Senior answer: secondary index `Map<tag, Set<key>>` for O(matches) invalidation. Also need `Map<key, Set<tag>>` reverse index — when entry is deleted (or overwritten), we must clean it out of every tag's Set; without reverse index, we'd have to scan tagIndex looking for the key. Three structures: primary `Map<key, value>`, forward tag index `Map<tag, Set<key>>`, reverse `Map<key, Set<tag>>`. `set(key, value, tags)`: delete-first (cleans old tag links), then primary.set, reverse.set, and add to each forward tag Set. `delete(key)`: remove from primary, look up reverse tags, remove key from each forward Set (clean empty tag entries), remove reverse entry. `invalidateTag(tag)`: clone the tag's key-Set first (`[...keys]`) — iterating Set while mutating it is undefined; then delete each. Combine with TTL: check expiry on get. Production: Redis SADD/SREM for distributed; tag-prefix hierarchies (`user:*`). Trap: missing reverse index (orphan tag entries); iterating Set during delete (UB); not cleaning empty tag entries (tagIndex grows); forgetting to clean old tags on set-over."

---

## 13. 60-second revision

> - **Two indexes:** tag→keys forward, key→tags reverse.
> - **`set` deletes first** for clean tag links.
> - **`delete` removes from all tag sets** + cleans empty tags.
> - **`invalidateTag` clones key set** before iterate (delete mutates).
> - **O(matches)** invalidation, not O(n).
> - **Combine TTL/LRU** as needed.
> - **Hierarchical tags** for wildcards.
> - **Distributed:** Redis SADD/SREM equivalent.
> - **Trap:** no reverse; iterate-mutate; orphan tag entries.

---

**Related:** [lru-cache-with-map.md](./lru-cache-with-map.md) · [ttl-map.md](./ttl-map.md) · [`10-machine-coding-patterns/event-emitter.md`](../10-machine-coding-patterns/event-emitter.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
