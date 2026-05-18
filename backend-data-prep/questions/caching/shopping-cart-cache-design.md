# Shopping cart cache design — TTL + write-through; user stickiness

## Source / Origin
- Industry pattern; every e-commerce backend has solved this.
- Amazon's Dynamo paper (2007) describes shopping cart as the canonical "always writable, eventually consistent" example.
- `backend-data-prep/caching/01-caching-strategies.md` — strategies overview.
- Classic prompt: *"Design the shopping cart for a high-traffic e-commerce site. Reads are 10× writes. Cart must survive 30 days of inactivity. What's in Redis, what's in Postgres, and how do they stay in sync?"*

## Why this question matters in interviews
Shopping cart is the **canonical "Redis is the source of truth" question**. Unlike a cache *of* a DB row, the cart often *lives* in Redis with periodic persistence — a pattern that flips the cache-aside default. The interviewer is testing:

1. You **don't reflexively use cache-aside** for everything — sometimes Redis is the system-of-record.
2. You can articulate **TTL, write-through, write-behind, eviction** tradeoffs in business terms ("30-day anonymous cart" vs "logged-in cart never expires").
3. You handle **identity stickiness** — cart starts anonymous (cookie), user logs in, cart must merge with their existing one.
4. You design for **abandonment / conversion analytics** — the cart isn't just data, it's a signal.

This is also a common Amazon / Flipkart / Shopify backend interview question, where the answer is calibrated to their actual production constraints.

## Concepts involved

### Syntax to lock in

```
Anonymous user:
  cookie cart_id = uuid (set on first add-to-cart)
  redis HSET   cart:<cart_id>  itemId quantity ...
  redis EXPIRE cart:<cart_id>  30*86400        (30-day TTL)

Logged-in user:
  cart_id = "user:" + user_id
  redis HSET   cart:user:42   itemId quantity ...
  redis PERSIST cart:user:42  (or much longer TTL)

On login (merge anonymous + user cart):
  redis HGETALL cart:<anon_id>
  redis HMSET   cart:user:42 ... merged ...
  redis DEL     cart:<anon_id>
  clear anon cookie

Persistent backing (write-through):
  every cart write: HSET in Redis, also INSERT/UPSERT into cart_items table
  on Redis miss: read from DB, populate Redis

Write-behind alternative:
  only Redis on writes; flush to DB every N seconds via background worker
```

### Edge cases / interview traps

1. **TTL refresh on every write.** Each cart update extends TTL — active carts live forever; truly abandoned carts expire. Use `EXPIRE` after every modification.
2. **Identity merge on login.** Conflict resolution: if both carts have item X, take max quantity? Sum quantities? Most products sum, capped at inventory.
3. **Inventory check** is a *separate* concern. Cart is intent; reservation is a separate step at checkout. Don't decrement stock when adding to cart.
4. **Logged-in cart eviction is dangerous.** TTL=30 days for anon is normal; for logged-in, either no TTL (cart persists indefinitely) or much longer TTL backed by DB.
5. **Write-through vs write-behind.** Write-through = synchronous DB write per cart mutation (durable, slower). Write-behind = async batch (fast, can lose recent updates).
6. **Cart abandonment events.** When TTL fires or user marks "abandon", emit an event for analytics / marketing email. Use Redis keyspace notifications or scheduled scan.
7. **Multi-device sync.** User on laptop and phone — same `user_id`, same cart key, last write wins. Or use CRDT-like sets if you need merge.
8. **Race conditions on quantity update.** "Add 1 of item X" must be atomic — use `HINCRBY`, not GET-then-SET.

## Mental Model

### Redis-as-source-of-truth picture

```
Cache-aside (typical for catalog data):
  read:   cache → on miss → DB → cache
  write:  DB → invalidate cache

Shopping cart (Redis-as-SoR, write-through to DB):
  read:   Redis only (DB is backup)
  write:  Redis + DB (atomic with retry)
  miss:   load from DB, rebuild Redis entry
  TTL:    Redis evicts after inactivity → DB still holds it for analytics
```

### Anonymous → logged-in flow

```
Step 1: Visitor arrives. No cart yet.
  Server sets cookie:  cart_id = uuid-abc

Step 2: Visitor adds 2 items.
  redis HSET cart:uuid-abc  prod_42 2  prod_99 1
  redis EXPIRE cart:uuid-abc 30*86400

Step 3: Visitor logs in as user_id=7.
  redis HGETALL cart:uuid-abc      → { prod_42: 2, prod_99: 1 }
  redis HGETALL cart:user:7        → { prod_42: 1 }    (had it before)
  merge → { prod_42: 3, prod_99: 1 }
  redis HMSET cart:user:7 ...
  redis DEL cart:uuid-abc
  clear cookie

Step 4: Visitor adds more items.
  cart_id is now "user:7" — uses the logged-in cart.

Step 5: Logged-in user logs out.
  Server keeps cart:user:7 untouched (will be picked up next login).
  Optionally create a new anon cart for the now-anonymous browser.
```

### TTL refresh on every modification

```
t=0      add to cart: HSET cart:abc ..., EXPIRE 30d
t=2d     add another: HSET cart:abc ..., EXPIRE 30d   (TTL reset)
t=4d     add another: HSET cart:abc ..., EXPIRE 30d
... user goes silent ...
t=34d    no activity since t=4d → Redis evicts at t=34d.

Effective TTL is "30 days of inactivity", not "30 days since first add".
```

## Why interviewers care

- Real e-commerce backends use Redis as the cart's primary store. Anyone who has shipped this knows the pattern; anyone who hasn't will reach for cache-aside.
- Identity merge on login is a **subtle product flow** that requires explicit design — no library does it for you.
- Inventory vs cart separation is a **classic concerns-mixing trap** — naïve candidates decrement stock at "add to cart" which destroys conversion.
- TTL strategy choices map to **business decisions** — abandonment window, conversion analytics, GDPR retention.

## Common beginner confusion

- *"Cart should be in Postgres."* It can be, but Redis dominates for read-heavy access patterns. The data is small (max ~20 items × few bytes); Redis fits.
- *"Cache the cart from the DB."* That treats DB as source of truth; works but doubles write latency and adds invalidation surface. Redis-as-SoR is cleaner for this access pattern.
- *"Use the user_id as the cart key."* Only works for logged-in. Anonymous users need a cookie-driven id.
- *"Decrement inventory when adding to cart."* Bad — abandoned carts lock inventory. Reserve at checkout, not at add.
- *"Use `SET` on quantity update."* Race: two tabs increment, one read-modify-write overwrites the other. Use `HINCRBY` atomic increment.

## Brute force approach

Every cart op = write to Postgres. Cart reads = SELECT from Postgres. Works but every page load hits the DB; high concurrency means many SELECTs on the cart_items table. With 1M active users adding items, you're at thousands of DB writes per second on a low-margin path. Hence Redis.

## Optimal approach

1. **Redis as primary store** for cart data.
2. **`HSET` + `HINCRBY`** for atomic quantity ops.
3. **TTL refresh on every modification** — 30 days inactivity for anon, much longer (or none) for logged-in.
4. **Write-through to Postgres** for durability + analytics — on each write, also UPSERT to the cart_items table.
5. **Identity merge on login** — explicit endpoint that combines anonymous + user carts and clears the anon one.
6. **Don't reserve inventory** — separate concern at checkout.
7. **Background reconciliation** — nightly job verifies Redis ↔ DB consistency; corrects drift if any.

## Solution (Node + Redis + Postgres)

```javascript
const Redis = require('ioredis');
const { Pool } = require('pg');
const redis = new Redis();
const pg = new Pool();

const ANON_TTL = 30 * 86400;       // 30 days
const USER_TTL = 365 * 86400;      // 1 year (effectively persistent)

function cartKey(cartId) { return `cart:${cartId}`; }

// Add item to cart (write-through)
async function addToCart(cartId, isUser, productId, quantityDelta = 1) {
  const key = cartKey(cartId);
  const ttl = isUser ? USER_TTL : ANON_TTL;

  // Atomic increment in Redis
  const tx = redis.multi();
  tx.hincrby(key, productId, quantityDelta);
  tx.expire(key, ttl);
  const [newQty] = await tx.exec().then(r => r.map(([_, v]) => v));

  // Write-through to Postgres (UPSERT)
  await pg.query(
    `INSERT INTO cart_items (cart_id, product_id, quantity, updated_at)
     VALUES ($1, $2, $3, NOW())
     ON CONFLICT (cart_id, product_id)
     DO UPDATE SET quantity = $3, updated_at = NOW()`,
    [cartId, productId, newQty],
  );
  return newQty;
}

// Get cart
async function getCart(cartId, isUser) {
  const key = cartKey(cartId);
  let items = await redis.hgetall(key);
  if (Object.keys(items).length === 0) {
    // Redis miss — read from DB
    const { rows } = await pg.query(
      `SELECT product_id, quantity FROM cart_items WHERE cart_id = $1`,
      [cartId],
    );
    if (rows.length === 0) return {};
    items = Object.fromEntries(rows.map(r => [r.product_id, r.quantity]));
    // Populate Redis
    const tx = redis.multi();
    tx.hmset(key, items);
    tx.expire(key, isUser ? USER_TTL : ANON_TTL);
    await tx.exec();
  }
  return items;
}

// Remove item
async function removeItem(cartId, productId) {
  await redis.hdel(cartKey(cartId), productId);
  await pg.query(
    `DELETE FROM cart_items WHERE cart_id = $1 AND product_id = $2`,
    [cartId, productId],
  );
}

// Merge anonymous cart into user cart on login
async function mergeOnLogin(anonCartId, userId) {
  const userKey  = cartKey(`user:${userId}`);
  const anonKey  = cartKey(anonCartId);

  const lua = `
    local anon = redis.call('HGETALL', KEYS[1])
    if #anon == 0 then return 0 end
    for i = 1, #anon, 2 do
      local pid = anon[i]
      local qty = tonumber(anon[i + 1])
      redis.call('HINCRBY', KEYS[2], pid, qty)
    end
    redis.call('DEL', KEYS[1])
    redis.call('EXPIRE', KEYS[2], ARGV[1])
    return 1
  `;
  await redis.eval(lua, 2, anonKey, userKey, USER_TTL);

  // Reconcile to DB
  const merged = await redis.hgetall(userKey);
  const client = await pg.connect();
  try {
    await client.query('BEGIN');
    await client.query(`DELETE FROM cart_items WHERE cart_id = $1`, [anonCartId]);
    for (const [pid, qty] of Object.entries(merged)) {
      await client.query(
        `INSERT INTO cart_items (cart_id, product_id, quantity, updated_at)
         VALUES ($1, $2, $3, NOW())
         ON CONFLICT (cart_id, product_id)
         DO UPDATE SET quantity = $3, updated_at = NOW()`,
        [`user:${userId}`, pid, qty],
      );
    }
    await client.query('COMMIT');
  } catch (e) {
    await client.query('ROLLBACK'); throw e;
  } finally {
    client.release();
  }
}

// Listen for Redis expiry (abandonment event)
const subscriber = new Redis();
await subscriber.config('SET', 'notify-keyspace-events', 'Ex');
await subscriber.subscribe('__keyevent@0__:expired');
subscriber.on('message', (chan, key) => {
  if (key.startsWith('cart:')) {
    const cartId = key.slice(5);
    emitAbandonmentEvent(cartId);
  }
});
```

### Postgres schema

```sql
CREATE TABLE cart_items (
  cart_id     TEXT NOT NULL,
  product_id  TEXT NOT NULL,
  quantity    INT  NOT NULL CHECK (quantity > 0),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (cart_id, product_id)
);
CREATE INDEX idx_cart_items_updated ON cart_items(updated_at);
```

## Step-by-step dry run

**Scenario A: anonymous user adds 2 items, then logs in.**

```
t=0:     no cart. cookie cart_id = "abc-uuid".
t=10s:   addToCart("abc-uuid", false, prod_42, 2)
         redis HSET cart:abc-uuid prod_42 2, EXPIRE 30d
         pg INSERT cart_items (abc-uuid, prod_42, 2)
t=20s:   addToCart("abc-uuid", false, prod_99, 1)
         redis state: cart:abc-uuid = { prod_42: 2, prod_99: 1 }, TTL 30d
t=60s:   login as user_id=7.
         existing redis state: cart:user:7 = { prod_42: 1 }   (old session)
         mergeOnLogin("abc-uuid", 7):
            HINCRBY cart:user:7 prod_42 2   → 3
            HINCRBY cart:user:7 prod_99 1   → 1
            DEL cart:abc-uuid
            EXPIRE cart:user:7 365d
         pg: DELETE cart_items WHERE cart_id='abc-uuid'
             UPSERT (user:7, prod_42, 3), (user:7, prod_99, 1)
         clear cookie cart_id, set cookie user_id=7.

Final: cart:user:7 = { prod_42: 3, prod_99: 1 } in both Redis and Postgres.
```

**Scenario B: cart abandonment.**

```
t=0:        user adds items as cart:abc.
t=30d:      no further activity. Redis TTL fires.
            keyspace notification → __keyevent@0__:expired with key cart:abc.
            subscriber emits abandonment event with cart_id=abc.
            marketing service reads cart_items from Postgres (still there for analytics).
            sends "did you forget something?" email.
            optionally archives cart_items to a cold table.
```

**Scenario C: race on quantity increment.**

```
Two tabs of the same user, both click "add to cart" for prod_42 simultaneously.

Without HINCRBY (broken):
  Tab A: GET prod_42 → 5. SET prod_42 6.
  Tab B: GET prod_42 → 5. SET prod_42 6.
  Result: 6, expected 7. Lost update.

With HINCRBY (correct):
  Tab A: HINCRBY prod_42 1 → 6.
  Tab B: HINCRBY prod_42 1 → 7.
  Both updates land. Atomic.
```

## How to think aloud in the interview

> "Cart is one of the rare cases where Redis is the source of truth, not a cache of the DB. Reads dominate writes 10:1, payload is small (few KB), and instant updates from any device matter more than strict durability. So my default: Redis primary store, write-through to Postgres for durability and abandonment analytics.
>
> Key naming: `cart:<id>` where `<id>` is either a cookie-set UUID (anonymous) or `user:<id>` (logged-in). Hash type: field per product, value is quantity. `HINCRBY` for atomic increments — never read-modify-write on quantities, races are real.
>
> TTL: 30 days for anonymous, with refresh on every modification — gives '30 days of inactivity', not 30 from cart creation. For logged-in, much longer or none; the cart effectively persists until checkout.
>
> Login merge: explicit endpoint. Take both carts, sum quantities (with inventory cap if needed), write to user cart, delete anon. I'd do this in a Lua script for atomicity in Redis and a single transaction in Postgres.
>
> What I'd *not* do: reserve inventory at add-to-cart. That kills conversion — abandoned carts hold stock. Reservation happens at checkout, in a short-lived hold (5-10 min) with explicit release.
>
> Abandonment events via Redis keyspace notifications — when a TTL fires on a `cart:*` key, emit an event for marketing. The cart data still in Postgres for the email content.
>
> Cross-region: cart in regional Redis with async replication to other regions. Eventually consistent — Amazon's Dynamo paper makes this exact case: cart should be 'always writable, eventually consistent.'"

## Important takeaways

- **Redis is the source of truth for shopping carts**, not a cache of the DB.
- **Write-through to Postgres** for durability and analytics.
- **`HSET` + `HINCRBY`** for atomic quantity updates — never read-modify-write.
- **TTL refresh on each write** = "N days of inactivity" semantics.
- **Anonymous → user merge on login** — Lua + transaction for atomicity.
- **Don't reserve inventory at add-to-cart** — reserve at checkout in a short-lived hold.
- **Keyspace notifications** for abandonment events.
- **Different TTL policies** for anon (30d) vs user (1y or none).
- **Multi-device sync** is automatic — same key, latest write visible to all.

## Variants

1. **Write-behind** — flush Redis to Postgres every 60s in batch. Faster writes, slightly less durable.
2. **Inventory hold at checkout** — separate `reservation:<sku>:<cart>` key with 10-minute TTL.
3. **Cart sharing via link** — generate a shareable cart_id; permission model.
4. **Saved-for-later** — second hash `saved:<id>` alongside `cart:<id>`; "move to cart" is a `HGET`+`HSET`+`HDEL`.
5. **B2B carts with quotes / approvals** — escalates from key-value to actual relational schema; Redis becomes a cache.
6. **Cross-region replication** — async; cart updates from one region propagate to others.
7. **CRDT cart** for true multi-master — useful for Shopify-style multi-channel (web + POS) editing the same cart concurrently.
8. **GDPR purge** — when user requests deletion, `DEL` Redis + `DELETE FROM cart_items` for all their cart_ids.

## Revision notes

> **shopping cart cache — 60 second recap**
> - **Redis as source of truth**, not as cache.
> - **Hash per cart**: `cart:<id>` → field=product_id, value=quantity.
> - **`HINCRBY` for atomic** quantity updates.
> - **TTL refresh on each write** → "N days of inactivity".
> - **Anon TTL ~30d, user TTL ~1y / none.**
> - **Write-through to Postgres** for durability + analytics.
> - **Login merges** anon cart into user cart (sum, then DEL anon).
> - **Don't reserve inventory** at add-to-cart; reserve at checkout.
> - **Keyspace notifications** for abandonment events.
> - Multi-device sync: same key, automatic.
