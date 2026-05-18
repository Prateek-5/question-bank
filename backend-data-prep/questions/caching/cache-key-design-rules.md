# Cache Key Design Rules

## Source / Origin
- Codified across Memcached / Redis production docs at Etsy, Shopify, GitHub.
- Discussed extensively in Brad Fitzpatrick's memcached design notes ("the key is the API").
- Companion concept doc: `backend-data-prep/caching/02-redis-patterns.md` — naming + cluster slot discussion.
- Interview prompt: "Walk me through your key naming convention. Why?"

## Why this question matters in interviews
Key design is the *first* thing senior engineers get right and juniors get wrong. Bad keys cause: silent collisions (two features write to the same key), un-invalidatable caches (can't enumerate by prefix), hash hotspots in clustered Redis (all keys land on one node), security leaks (PII in keys), and unfixable migrations (no versioning). The interviewer wants to see whether you have a *system* for keys, not just ad hoc strings.

## Concepts involved

### Syntax to lock in

A production-grade key:
```
{app}:{entity}:{id}:{aspect}:v{schema_version}

# examples
acme:user:42:profile:v3
acme:user:42:settings:v1
acme:order:{user:42}:cart:v2     # hashtag for co-location in Cluster
acme:feed:{user:42}:home:v5
acme:rate-limit:ip:198.51.100.4:60s
```

Anti-patterns:
```
user_42                           # no app prefix, no versioning, ambiguous
User42                            # case-inconsistent, easily mistyped
session-abc123-userinfo           # which app? which version?
get_user_by_id_42_with_settings   # function name as key — leaks impl
user:42:0a8f9b2c                  # opaque hash; can't enumerate
```

### The five rules of key design
1. **Namespace by app/service.** Prevents collision when multiple services share a Redis. `payments:user:42` vs `auth:user:42`.
2. **Entity:ID:aspect.** Predictable structure makes invalidation and observability mechanical.
3. **Version the schema.** When the value's shape changes, bump `:v2` — old and new versions coexist during rollout. No migrations needed.
4. **Use hashtags for co-location.** In Redis Cluster, keys hash to slots. To run multi-key ops (MGET, transactions, Lua) across related keys, embed `{...}` so they hash identically: `user:{42}:profile` and `user:{42}:settings`.
5. **Never put PII or secrets in keys.** Keys are logged, exported, and visible in metrics. Hash them if you must include user IDs: `user:sha256(email):prefs`.

### Edge cases / interview traps
1. **Key length** — Redis allows up to 512MB per key, but long keys waste RAM and CPU on every lookup. Aim for <200 bytes. `user:{long-uuid-here}:long-aspect-description` is fine; encoding entire JSON queries into keys is not.
2. **Hash collisions on truncated keys** — if you hash long inputs to fixed-length keys (e.g., MD5 of a query), collisions are rare but possible. Use the full hash; never truncate without thinking about birthday-bound math.
3. **Cluster-mode cross-slot ops** — `MGET user:1 user:2 user:3` fails in Cluster unless all keys map to the same slot. Either single-slot with hashtag or use pipeline with one round-trip per slot.
4. **Wildcard scans (`SCAN MATCH "user:*"`)** are O(N) over the entire keyspace. Don't design invalidation around `SCAN`. Use versioned keys or maintain a secondary index (set of all `user:*` keys).
5. **`KEYS pattern` blocks Redis** for the duration of the scan. Forbidden in production. `SCAN` is cursor-based and safe, but still costly for large keyspaces.
6. **Unicode / control chars in keys** — technically legal, but a nightmare for ops tools. Stick to ASCII alphanumerics, `:`, `-`, `_`.
7. **Composite keys with dynamic ordering** — `cache(a, b)` and `cache(b, a)` should produce the same key if the operation is symmetric (e.g., friendship). Sort the components before composing.
8. **Tenant isolation** — `tenant:{tenantId}:user:{userId}` is mandatory for multi-tenant systems. Forgetting this is a data-leak bug waiting to happen.
9. **Time-bucket keys** — `metrics:pv:home:2024-01-15:14` (per-hour bucket) is great for windowed aggregates; bad for high-cardinality (per-second buckets explode memory).

## Mental Model

```
Anatomy of a key

   acme : user : 42 : profile : v3
   ────   ────   ──   ───────   ──
    │      │     │      │       │
    │      │     │      │       └── schema version (rolling-deploy friendly)
    │      │     │      └────────── aspect (which slice of the entity)
    │      │     └───────────────── entity ID
    │      └─────────────────────── entity type
    └────────────────────────────── app / service namespace

Mental model: the key encodes *what data is this* + *which version of its shape*.
```

### Cluster hashtag mechanics

```
Without hashtag:
  user:42:profile  → CRC16("user:42:profile") % 16384 = slot 4271
  user:42:settings → CRC16("user:42:settings") % 16384 = slot 1093
  → different slots → cannot use MGET, MULTI, Lua across both

With hashtag:
  user:{42}:profile  → CRC16("42") % 16384 = slot 3672
  user:{42}:settings → CRC16("42") % 16384 = slot 3672
  → same slot → MGET, MULTI, Lua all work
```

## Why interviewers care
- Reveals **system thinking** — do you design for ops, migration, multi-tenancy, and clustering, or just for "first write works"?
- The follow-up "how would you invalidate every cached user?" forces you to confront the consequence of your naming.
- Versioning is the unambiguous senior-level cue. Most candidates don't think about it.

## Common beginner confusion
- **"It's just a string."** Yes, but it's the primary key of your cache. Treat it like a DB primary key.
- **"I'll use UUIDs."** Then you can't enumerate them, can't read keys at a glance in monitoring, and can't do `SCAN user:tenant:42:*` to find a tenant's data.
- **"I'll add a timestamp to the key for freshness."** Now you have an infinite-cardinality key space and can never re-read old values. TTL is what you want.
- **"Hashtags make Cluster work."** They make *related* keys co-located. They also create a hotspot if every key for `{user:42}` ends up on one node. Trade-off.
- **"Versioning is overengineering."** Until you deploy a new value schema in a rolling deploy and old pods crash on JSON.parse of new shape.

## Brute force approach
"Use whatever string is convenient at the call site." Works for a prototype. Falls apart the moment two engineers cache to the same key with different shapes, or a Cluster migration scatters your related keys across nodes.

"Hash the function name and arguments." Works mechanically. Loses introspectability — you can't read keys in Redis CLI to debug. And changes to the function signature silently invalidate caches.

## Optimal approach

### Template
```
{app}:{entity}:{id}:{aspect}:v{version}[:{sub_aspect}]
```

### Conventions
- **Lowercase, ASCII alnum + `:` + `-`.** No spaces, no Unicode.
- **`:` separates components.** Never embed `:` inside a component.
- **Hashtag `{...}` around the co-location dimension** (usually the entity ID).
- **`v{N}` version segment** for any value with a non-trivial shape.
- **Length < 200 bytes** unless you have a reason.

### Versioning strategy
- **Bump on shape change.** Old version naturally ages out via TTL.
- **Global invalidate via a "current version" key.** Store `acme:user:current_version = 4`; read it first, append to key. Bumping it invalidates every cached user without scanning.

### Composite keys (multi-dimensional)
- Sort components for symmetric ops: `friend:{min(a,b)}:{max(a,b)}`.
- For lookup-by-multiple-fields, hash deterministically: `search:hash(query+filters):v1`.

### Tenant isolation
- Always include `tenant:{tid}` prefix, even for single-tenant prototypes — easier to bolt on multi-tenancy later than refactor.

## Solution

### Key builder helper (Node.js)

```javascript
const APP = 'acme';
const VERSIONS = { user: 3, order: 2, feed: 5 };   // central registry

function key(entity, id, aspect, opts = {}) {
  const v = VERSIONS[entity] ?? 1;
  const co = opts.coLocate ? `{${id}}` : id;
  return `${APP}:${entity}:${co}:${aspect}:v${v}`;
}

// Usage
key('user', 42, 'profile');              // acme:user:42:profile:v3
key('user', 42, 'settings', { coLocate: true });
                                          // acme:user:{42}:settings:v3
key('order', 'abc-123', 'cart', { coLocate: true });
                                          // acme:order:{abc-123}:cart:v2
```

### Global version-bump invalidation

```javascript
async function bumpUserVersion() {
  await redis.incr('acme:_version:user');
}

async function userKey(id, aspect) {
  const v = await redis.get('acme:_version:user');
  return `acme:user:${id}:${aspect}:v${v}`;
}
```

A single `INCR` invalidates every cached user — old reads fall through and repopulate under the new version. Old entries age out via TTL.

### Composite key for symmetric op (mutual-friend check)

```javascript
function friendKey(a, b) {
  const [x, y] = [a, b].sort();
  return `acme:friend:${x}:${y}:v1`;
}
friendKey(42, 17);   // acme:friend:17:42:v1
friendKey(17, 42);   // acme:friend:17:42:v1  ← same
```

### Hash-based key for high-dimensional query cache

```javascript
const crypto = require('crypto');

function searchKey(query, filters) {
  const canonical = JSON.stringify({ q: query, f: filters }, Object.keys({ q: '', f: '' }).sort());
  const hash = crypto.createHash('sha256').update(canonical).digest('hex').slice(0, 16);
  return `acme:search:${hash}:v1`;
}
```

## Step-by-step dry run

Scenario: design keys for a multi-tenant e-commerce app. Need to cache: user profiles, order details, shopping carts (user-scoped), product catalog.

```
acme:tenant:nike:user:42:profile:v3
acme:tenant:nike:user:42:settings:v2
acme:tenant:nike:order:{user:42}:list:v1    ← hashtag co-locates with cart
acme:tenant:nike:order:{user:42}:cart:v1
acme:tenant:nike:product:sku-123:detail:v4
acme:tenant:nike:product:sku-123:price:v1
```

**Why these choices:**
- `tenant:nike:` prefix isolates Nike's keys from Adidas's. A misconfigured client cannot read across tenants.
- `user:42:profile:v3` and `user:42:settings:v2` versioned independently — profile schema change doesn't invalidate settings.
- `order:{user:42}:list:v1` and `order:{user:42}:cart:v1` share hashtag `{user:42}` → same Cluster slot → can do `MGET` or atomic Lua across them when checking out.
- `product:sku-123:detail:v4` — no hashtag because we never need atomic multi-product ops on the cache. Even distribution across Cluster nodes.

**Invalidation scenarios:**
- Profile schema v3 → v4: update central version registry, deploy. Old `v3` keys expire via TTL; new reads write `v4`.
- One user's profile updated: `DEL acme:tenant:nike:user:42:profile:v3`.
- All users in tenant Nike — no easy enumeration; either bump tenant-scoped version `acme:tenant:nike:_v` and append to keys, or maintain a `SET` of all user IDs and iterate via `SCAN`.

## How to think aloud in the interview

"I treat cache keys like primary keys — they're an API. The shape I default to is `{app}:{entity}:{id}:{aspect}:v{version}`. The pieces matter: the app prefix prevents collisions across services on shared Redis; the entity:ID:aspect lets me cache slices of an object instead of the whole blob; and the version segment is the unsung hero — when the value shape changes, I bump the version and old keys age out naturally via TTL. No migration script needed.

For Cluster mode, I use the hashtag syntax. If I have two keys for the same user — say their profile and their cart — and I want to do an atomic operation across both, I wrap the shared dimension in braces: `user:{42}:profile`, `user:{42}:cart`. Both hash to the same slot. Without that, they're on different nodes and any multi-key operation fails.

Things I avoid: PII in keys (they're logged), opaque hashes when I need to introspect (use hashes only for high-dimensional things like search queries), and overly long keys (memory cost adds up). Also `KEYS pattern` is banned in production — it blocks Redis. If I need enumeration, I maintain a secondary index in a set, or use `SCAN` carefully, or use versioned keys to invalidate without enumerating.

For multi-tenant systems, I always prefix with `tenant:{tid}` even on day one. It's trivial to add and almost impossible to bolt on later without a full refactor.

If they push on versioning: the cheap version is putting `v3` literally in the key string and bumping it in code on schema changes. The fancier version is a centralized `current_version` key that the app reads to construct the key — bumping that one key invalidates everything dependent on it."

## Important takeaways

- **`{app}:{entity}:{id}:{aspect}:v{version}` is the default template.**
- **Always include a version segment** for non-trivial values.
- **Hashtag `{...}` for co-location** in Cluster mode.
- **Never put PII or secrets in keys.**
- **`KEYS pattern` is banned in prod**; use `SCAN` or maintain secondary indices.
- **Multi-tenant: always prefix with `tenant:{tid}`.**
- **Sort components of symmetric composite keys.**
- **Hash high-dimensional inputs** to fixed-size keys (full hash, no truncation without math).
- **Bump a central version key** for "invalidate everything of type X" without scanning.

## Variants

1. **Tag-based invalidation** — store a set of "tags" per key (`tag:user:42 → SET{key1, key2}`); invalidate a tag iterates the set. Adds write cost but enables fast bulk invalidation.
2. **Versioned values inline** — store `{value, schema_version}` inside the value; old readers detect and ignore. Avoids the version-in-key complexity.
3. **Time-bucket keys** — `metrics:pv:2024-01-15T14` for hourly aggregates. Natural TTL via cron deletion.
4. **Per-tenant key prefix** — for strict multi-tenant isolation.
5. **Sharded hot key** — `trending:home:shard:{0..15}` to spread one logical hot key across Cluster nodes.
6. **Content-addressed keys** — `blob:{sha256}` for immutable cached blobs. Natural deduplication.

## Revision notes

> **cache key design — 60 second recap**
> - **Template:** `{app}:{entity}:{id}:{aspect}:v{version}`
> - **Namespace by service** (avoids collisions on shared Redis).
> - **Version every non-trivial value's schema** — bump on shape change, old keys die via TTL.
> - **Hashtag `{...}`** in Cluster mode for co-locating related keys.
> - **No PII, no secrets, no Unicode, no spaces.**
> - **`KEYS pattern` banned** — use `SCAN` or secondary index.
> - **Multi-tenant: prefix with tenant ID** from day one.
> - **Composite keys: sort components** for symmetric operations.
> - **Trap:** ad hoc strings, opaque hashes, no version, hashtags creating hotspots.
