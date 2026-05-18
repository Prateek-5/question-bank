# MongoDB: Design the shopping cart — embed vs reference?

## Source / Origin
- Classic Mongo modeling question. Asked at Amazon (cart service), Flipkart, every Mongo-shop interview.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (embed-vs-reference section).
- Related: `backend-data-prep/nosql/01-nosql-fundamentals.md` (document model basics).

## Why this question matters in interviews
The shopping cart is the **canonical "small + bounded + co-accessed"** entity. If you say "embed everything" you fail the 16 MB / hot-product / write-amplification follow-ups. If you say "reference everything" you fail the "why use Mongo at all" follow-up. The senior signal is the *decision framework*: cardinality, access pattern, update frequency, document growth. Interviewers use this question to test your modeling instinct in 5 minutes — it predicts how you'll model the rest of the schema.

## Concepts involved

### Syntax to lock in

```javascript
// EMBED: cart-as-document. One read = whole cart.
{
  _id: ObjectId("..."),
  userId: "U-123",
  items: [
    { productId: "P-1", sku: "RED-M", name: "T-shirt", priceAtAdd: 499, qty: 2, addedAt: ISODate(...) },
    { productId: "P-2", sku: "BLU-L", name: "Mug",     priceAtAdd: 199, qty: 1, addedAt: ISODate(...) }
  ],
  updatedAt: ISODate(...),
  version: 4              // optimistic-concurrency token
}

// REFERENCE: cart holds pointers; product lives in its own collection.
{
  _id: ObjectId("..."),
  userId: "U-123",
  items: [
    { productId: ObjectId("P-1"), qty: 2, priceAtAdd: 499 },
    { productId: ObjectId("P-2"), qty: 1, priceAtAdd: 199 }
  ]
}
// rendering the cart now requires a $lookup into `products`.
```

### Edge cases / interview traps

1. **Embedding the full product** — duplicates name/image/description into every cart. When the product is renamed, 50K carts now show the old name. Embed only **immutable-at-add-time fields** (`priceAtAdd`, `nameSnapshot`) — these are correct to freeze.
2. **Unbounded array** — wishlists, infinite carts. 16 MB doc limit. Every $push rewrites the whole doc on disk if it outgrows its padding. Use a side collection once you expect >a few hundred items.
3. **Hot product** — a flash-sale item is referenced from 100K carts. If you embed the live product fields, you must touch 100K carts to change one price. References avoid this.
4. **Price at add vs price now** — interviewers love this. The cart shows `priceAtAdd`; checkout re-fetches live price; if they differ, you prompt "price changed, continue?". This is a *business rule* — be explicit.
5. **Stock check at checkout, not at add** — embedding `stockLevel` into the cart is wrong. Stock is live; cart is snapshot.
6. **Atomic single-doc writes** — `$inc qty`, `$push items`, `$pull items` are all atomic on one document. Two clients tapping "Add to cart" simultaneously won't corrupt data; both increments land.
7. **Optimistic concurrency** — add a `version` field; update with `findOneAndUpdate({ _id, version: 4 }, { $set: {...}, $inc: { version: 1 } })`. Retry on mismatch.

## Mental Model

> Cart is **session state with a long fuse**. It belongs to one user, has bounded size, is read and written together, and survives across devices. That's the embedding fingerprint.

```
   ┌────────────────────────────────────┐
   │  carts collection                  │
   │  ┌─────────────────────────────┐   │
   │  │ _id: ..., userId: U-123     │   │
   │  │ items: [                    │   │   ← bounded (≤ ~50 in practice)
   │  │   { productId, qty, snap },│   │   ← snapshot fields only
   │  │   { productId, qty, snap },│   │
   │  │ ]                           │   │
   │  └─────────────────────────────┘   │
   └────────────────────────────────────┘
                  │ productId points to
                  ▼
   ┌────────────────────────────────────┐
   │  products collection               │
   │  ┌─────────────────────────────┐   │
   │  │ _id: P-1, name, price, ...  │   │   ← source of truth; mutates often
   │  └─────────────────────────────┘   │
   └────────────────────────────────────┘
```

Embed the **snapshot**; reference the **source of truth**. That single rule resolves 80% of modeling debates.

## Why interviewers care

- It's the **first decision** in any Mongo schema — bad call here cascades.
- It tests **data-locality reasoning** (the entire point of document DBs).
- It surfaces **write-amplification awareness** — a senior trait.
- It tests **honesty about denormalization tax** — duplicates must be re-synced.

## Common beginner confusion

- "Mongo is fast because joins are bad → embed everything." Half right. Embedding wins when the embedded data is bounded and co-accessed. Past that, $lookup wins.
- "Embedding the product is fine, it's just JSON." Until a product is renamed and you have 50K stale carts.
- "Use references like SQL foreign keys." Then you've reimplemented SQL with worse joins. References belong on *high-cardinality, mutable, separately-accessed* entities.
- "Two-phase commit for cart + inventory." Overkill until checkout. Cart is local state; commit at checkout.
- "Atomicity needs transactions." No — single-doc updates are atomic. You only need transactions if the write spans cart + inventory + order docs.

## Brute force approach

Two collections: `carts` and `cart_items`, with `cart_items.cartId` as FK. Render-cart query = find cart + find items by cartId. You've rebuilt the SQL model in Mongo and now pay for both worlds. This is the **classic anti-pattern**: don't normalize 1-to-bounded-N relationships in a document store.

## Optimal approach

**Embed the line items inside the cart document. Snapshot price + name at add time. Reference the product by `productId` for live data at render/checkout. Cap the array at ~100 items.**

Why:
- A cart's lifetime read pattern = "load whole cart". Embedding gives 1 round trip.
- Items are bounded (no one has 10K cart lines).
- Snapshot fields freeze prices for the receipt; live fields fetched on demand.
- Atomic `$push` / `$pull` / `$inc` on one document = no transaction needed for normal cart ops.

## Solution (Mongo shell)

```javascript
// === Schema validator (recommended) ===
db.createCollection("carts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "items", "updatedAt", "version"],
      properties: {
        userId: { bsonType: "string" },
        items: {
          bsonType: "array",
          maxItems: 100,
          items: {
            bsonType: "object",
            required: ["productId", "qty", "priceAtAdd"],
            properties: {
              productId:  { bsonType: "objectId" },
              sku:        { bsonType: "string" },
              nameSnap:   { bsonType: "string" },
              priceAtAdd: { bsonType: "int" },
              qty:        { bsonType: "int", minimum: 1, maximum: 99 },
              addedAt:    { bsonType: "date" }
            }
          }
        },
        version:   { bsonType: "int" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
});

db.carts.createIndex({ userId: 1 }, { unique: true });

// === Add to cart (atomic, idempotent on productId+sku) ===
db.carts.updateOne(
  { userId: "U-123", "items.productId": { $ne: ObjectId("P-1") } },
  {
    $push: {
      items: {
        productId: ObjectId("P-1"),
        sku: "RED-M",
        nameSnap: "T-shirt",
        priceAtAdd: 499,
        qty: 1,
        addedAt: new Date()
      }
    },
    $inc: { version: 1 },
    $set: { updatedAt: new Date() }
  },
  { upsert: true }
);

// If item already exists, bump qty:
db.carts.updateOne(
  { userId: "U-123", "items.productId": ObjectId("P-1") },
  { $inc: { "items.$.qty": 1, version: 1 }, $set: { updatedAt: new Date() } }
);

// === Remove item ===
db.carts.updateOne(
  { userId: "U-123" },
  { $pull: { items: { productId: ObjectId("P-1") } }, $inc: { version: 1 } }
);

// === Render cart with live product data (join on demand) ===
db.carts.aggregate([
  { $match: { userId: "U-123" } },
  { $unwind: "$items" },
  { $lookup: {
      from: "products",
      localField: "items.productId",
      foreignField: "_id",
      as: "live"
  }},
  { $unwind: "$live" },
  { $project: {
      productId: "$items.productId",
      qty: "$items.qty",
      priceAtAdd: "$items.priceAtAdd",
      livePrice:  "$live.price",
      liveName:   "$live.name",
      priceChanged: { $ne: ["$items.priceAtAdd", "$live.price"] }
  }}
]);
```

## Step-by-step dry run

```
t=0  User adds P-1 (qty 1) → upsert cart, items=[P-1×1], version=1
t=5  User adds P-2 (qty 1) → $push, items=[P-1×1, P-2×1],   version=2
t=9  User taps "+" on P-1 → match on items.productId, $inc items.$.qty
                                                   items=[P-1×2, P-2×1], version=3
t=20 Admin renames P-1 in products collection. Cart is unaffected.
t=30 Render cart → $lookup pulls live name; nameSnap differs; UI shows
       "product renamed since you added it" (optional UX).
t=60 Checkout → re-fetch live prices; if priceAtAdd ≠ live price,
       prompt user to confirm new total; then create order doc inside
       a multi-document transaction (cart → order → inventory).
```

## How to think aloud in the interview

> "A cart is bounded, owned by one user, read and written together. That's the embedding fingerprint, so I embed line items in the cart document. But the product itself is mutable, high-cardinality, accessed by many carts — that's the *reference* fingerprint, so `productId` is a pointer, and live fields come from a `$lookup` at render time.
>
> I snapshot only the fields the business wants frozen at add time: `priceAtAdd`, `nameSnap`. Live fields like stock and current price are fetched on demand. This is the same pattern as an invoice line item — the receipt freezes the price; the catalog moves on.
>
> Concurrency: single-doc updates are atomic, so `$push`, `$inc qty`, `$pull` need no transaction. I add a `version` for optimistic concurrency on render-then-edit flows. Multi-doc atomicity is only needed at checkout — cart + order + inventory — and that's a multi-document transaction.
>
> Hard cap items at ~100 in the validator. If the use case is a wishlist with thousands of items, I'd switch to a side collection keyed by `userId`."

## Important takeaways

- **Embed when bounded + co-accessed + snapshot semantics.** Cart line items fit perfectly.
- **Reference when high-cardinality + mutable + independently accessed.** Products fit perfectly.
- **Snapshot vs live** is the modeling axis, not embed vs reference per se.
- **Single-doc atomicity** removes 80% of the need for transactions.
- **Cap the array** in the validator — catches schema drift early.
- **Two indexes you must have**: `{ userId: 1 }` unique on carts, `{ _id: 1 }` (auto) on products.

## Variants

1. **Wishlist with 10K items** — flip to side collection: `wishlist_items(userId, productId, addedAt)`.
2. **Cart sharing across devices** — userId is the partition; embedding still wins; add `lastDeviceId` for diagnostics.
3. **Guest carts** — `userId` becomes a session token; merge on login (set-union of items).
4. **Cart abandonment analytics** — TTL index on `updatedAt` to expire idle carts after 30 days; emit `cart.expired` event for re-engagement.
5. **B2B carts with 1000 SKUs** — embedding breaks; switch to `cart_lines` collection keyed by `cartId`.
6. **Multi-currency** — `priceAtAdd` becomes `{ amount, currency }`; lock currency for the cart's lifetime.

## Revision notes

> **cart embed-vs-reference — 60s recap**
> - Cart = bounded + co-accessed + per-user → **embed line items**.
> - Product = mutable + shared + high-cardinality → **reference by productId**.
> - Embed *snapshot* fields (priceAtAdd, nameSnap). Reference *live* fields.
> - Single-doc updates are atomic → `$push`/`$pull`/`$inc` need no transaction.
> - `version` field for optimistic concurrency.
> - Cap items at ~100 via validator. If unbounded → side collection.
> - Multi-doc transaction only at checkout (cart → order → inventory).
> - Hot-product mutation? Don't embed live product fields; that's write amplification.
