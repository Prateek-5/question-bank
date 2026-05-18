# DynamoDB: Sort key patterns — composite, hierarchical, prefix queries

## Source / Origin
- Senior DynamoDB modeling question. Asked at AWS / Amazon / any team using single-table design.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Sort key is **the only place** Dynamo gives you a range scan. Designing the SK is what unlocks `BETWEEN`, `begins_with`, and hierarchical queries — all in one trip to one partition. Without a clever SK, you Scan. Senior signal: you compose SKs from multiple fields, use **prefix conventions** (`ORDER#`, `EVENT#`), and design SKs to support multiple access patterns.

## Concepts involved

### Syntax to lock in

```javascript
// Composite SK: zero-padded timestamp + ID
// SK = "2026-05-17T12:00:00Z#MSG-0042"
// → sorts naturally by time, with tiebreaker on ID

// Hierarchical SK: type#parent#child
// SK = "ORDER#2026-05-17#ITEM#1"
// → supports begins_with("ORDER#"), begins_with("ORDER#2026-05-17#"), etc.

// Query examples
{ TableName: "T", KeyConditionExpression: "PK = :p AND SK BETWEEN :a AND :b" }
{ TableName: "T", KeyConditionExpression: "PK = :p AND begins_with(SK, :pref)" }
{ TableName: "T", KeyConditionExpression: "PK = :p AND SK >= :since",
  ScanIndexForward: false, Limit: 50 }
```

### SK operators (memorize)

| Operator | Use |
|---|---|
| `=` | Exact SK match |
| `<`, `<=`, `>`, `>=` | Range |
| `BETWEEN x AND y` | Inclusive range |
| `begins_with(SK, prefix)` | Prefix scan within partition |
| `ScanIndexForward: false` | Reverse (newest first) |

### Edge cases / interview traps

1. **Zero-pad numeric SK components.** `"ORDER#9"` < `"ORDER#10"` is false lexically. Use `"ORDER#0000000010"`.
2. **ISO-8601 timestamps sort correctly as strings.** Use them — never epoch numbers as SK.
3. **`begins_with` requires a single prefix.** You can't OR multiple prefixes; use multiple Queries.
4. **No `contains` on SK.** Only prefix; no substring middle-match.
5. **SK type fixed at table creation.** Can't change S → N later.
6. **Composite SK with delimiter** — pick a delimiter that can't appear in any component (`#`, `|`).
7. **Empty SK** — not allowed for an SK attribute. Use a placeholder if you need a "no-sub-entity" row.
8. **Reverse pagination** — flip `ScanIndexForward` AND `ExclusiveStartKey`.

## Mental Model

> Think of a partition as a **sorted list inside a hash bucket**. SK is the within-bucket index. `begins_with` walks the prefix range; `BETWEEN` walks an arbitrary range; `=` is a binary-search hit.

```
   Partition PK="U-1":
     SK=ORDER#2026-05-15#ITEM#1   →  {sku, qty, price}
     SK=ORDER#2026-05-15#ITEM#2   →  {sku, qty, price}
     SK=ORDER#2026-05-15#META     →  {total, status}
     SK=ORDER#2026-05-17#ITEM#1   →  {sku, qty, price}
     SK=ORDER#2026-05-17#META     →  {total, status}
     SK=PROFILE                   →  {name, email}

   Query begins_with(SK, "ORDER#2026-05-15#")  →  3 items in O(matching)
   Query begins_with(SK, "ORDER#")             →  5 items
   Query SK = "PROFILE"                        →  1 item
```

## Why interviewers care

- Tests **single-trip query design** — composite SK eliminates round trips.
- Tests **hierarchical entity modeling** — order → items → metadata.
- Tests **string-sort awareness** — zero-padding, ISO-8601.

## Common beginner confusion

- "Number SK with epoch ms" — works numerically but loses readability and breaks if you want composite (number SK can't have `#TYPE#ID` suffix).
- "Use multiple SKs" — Dynamo allows only one SK per table/index.
- "Sort key is a foreign key." It's just a string that orders rows within a partition.
- "begins_with works on PK." It doesn't. PK is hashed.
- "I can sort by any attribute." Only by SK. Other attributes need a GSI.

## Brute force approach

Make SK a UUID. Now every query is `SK = exact` or `Scan`. Wasted opportunity.

## Optimal approach

Design the SK as **hierarchical composite** with type prefixes:
- `ORDER#<isoDate>#ITEM#<paddedSeq>` — group by order, within by item.
- `EVENT#<ts>` — pure time-ordered.
- `PROFILE` — sentinel SK for the singleton row.
- `META#<entityType>` — metadata partition for the entity.

Each `begins_with` prefix corresponds to a different access pattern.

## Solution (DynamoDB JSON + JS)

```javascript
// === Table schema (single-table style) ===
{
  TableName: "App",
  KeySchema: [
    { AttributeName: "PK", KeyType: "HASH" },
    { AttributeName: "SK", KeyType: "RANGE" }
  ],
  AttributeDefinitions: [
    { AttributeName: "PK", AttributeType: "S" },
    { AttributeName: "SK", AttributeType: "S" }
  ]
}

// === Items for one user ===
[
  { PK: "USER#U-1", SK: "PROFILE",                              name: "Alice" },
  { PK: "USER#U-1", SK: "ORDER#2026-05-15#META",                total: 1200, status: "PAID" },
  { PK: "USER#U-1", SK: "ORDER#2026-05-15#ITEM#0000000001",     sku: "SKU-A", qty: 2 },
  { PK: "USER#U-1", SK: "ORDER#2026-05-15#ITEM#0000000002",     sku: "SKU-B", qty: 1 },
  { PK: "USER#U-1", SK: "ORDER#2026-05-17#META",                total: 800,  status: "SHIPPED" },
  { PK: "USER#U-1", SK: "ORDER#2026-05-17#ITEM#0000000001",     sku: "SKU-C", qty: 3 }
]

// === Access patterns ===

// 1. Get user profile
await ddb.get({ TableName: "App", Key: { PK: "USER#U-1", SK: "PROFILE" } });

// 2. List all orders for user (meta only, paginated)
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :pk AND begins_with(SK, :pref)",
  ExpressionAttributeValues: { ":pk": "USER#U-1", ":pref": "ORDER#" },
  FilterExpression: "ends_with(SK, :meta)",   // not natively supported, see workaround
  Limit: 50
});

// 3. List items in a specific order
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :pk AND begins_with(SK, :pref)",
  ExpressionAttributeValues: {
    ":pk":   "USER#U-1",
    ":pref": "ORDER#2026-05-15#ITEM#"
  }
});

// 4. List user's orders in date range
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :pk AND SK BETWEEN :lo AND :hi",
  ExpressionAttributeValues: {
    ":pk": "USER#U-1",
    ":lo": "ORDER#2026-05-15",
    ":hi": "ORDER#2026-05-18~"   // ~ sorts after digits; cheap upper bound
  }
});

// 5. Most-recent N orders (reverse)
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :pk AND begins_with(SK, :pref)",
  ExpressionAttributeValues: { ":pk": "USER#U-1", ":pref": "ORDER#" },
  ScanIndexForward: false,
  Limit: 10
});
```

### Note on `ends_with`

DynamoDB **does not support `ends_with`** on the SK. Workaround: include the discriminator (`META`/`ITEM`) earlier in the SK so `begins_with` works. Example:
```
SK = "ORDERMETA#2026-05-15"          ← begins_with("ORDERMETA#") gives only metas
SK = "ORDERITEM#2026-05-15#1"        ← begins_with("ORDERITEM#") gives only items
```

### Padding helper

```javascript
const padN = (n, width = 10) => String(n).padStart(width, "0");
// SK = `ORDER#${isoDate}#ITEM#${padN(seq)}`
```

## Step-by-step dry run

```
Partition PK="USER#U-1":

  SK list (sorted):
    "ORDER#2026-05-15#ITEM#0000000001"
    "ORDER#2026-05-15#ITEM#0000000002"
    "ORDER#2026-05-15#META"
    "ORDER#2026-05-17#ITEM#0000000001"
    "ORDER#2026-05-17#META"
    "PROFILE"

  Query begins_with("ORDER#2026-05-15#") → first 3 items.
  Query begins_with("ORDER#")            → first 5 items.
  Query begins_with("PROFILE")           → 1 item.
  Query BETWEEN "ORDER#2026-05-15" AND "ORDER#2026-05-16~" → orders on 2026-05-15.

Time complexity: O(matching) — DynamoDB seeks into the sorted index and reads consecutively.
```

## How to think aloud in the interview

> "Sort key is the only place I get range scans. I design it as a hierarchical composite with type prefixes: `ORDER#<date>#ITEM#<padded-seq>`. That single SK supports multiple access patterns: 'all orders', 'orders in date range', 'items of one order', 'most recent N orders with `ScanIndexForward: false`'.
>
> Two non-obvious rules: zero-pad numeric components so lex sort matches numeric sort, and use ISO-8601 timestamps as strings because they sort correctly. Pick a delimiter that can't appear in any component — `#` or `|`.
>
> DynamoDB has `begins_with` and `BETWEEN` but not `contains` or `ends_with`. So the discriminator (META vs ITEM) goes at the *start* of the SK suffix, not the end.
>
> For multi-access-pattern designs, I add GSIs with different (PK, SK) combinations on the same items — that's the single-table-design move."

## Important takeaways

- **SK = sorted within partition.** Range/prefix queries land in O(matching) time.
- **Composite SK** with `#` delimiter unlocks multiple access patterns.
- **Zero-pad numerics. ISO-8601 timestamps.**
- **`begins_with` and `BETWEEN`; no `contains`/`ends_with`.**
- **Discriminator at SK prefix start**, not end.
- **`ScanIndexForward: false`** for newest-first.
- **GSI with different SK** for alternate access patterns.

## Variants

1. **Adjacency list** — `PK = entity, SK = "child#" + childId` for many-to-many.
2. **Versioned items** — `SK = "v#0000000003"` for revision history.
3. **TTL on SK** — TTL attribute separate from SK; doesn't need to be part of key.
4. **Sparse GSI sort** — only items with a particular SK pattern indexed.
5. **Date partition pivots** — `PK = entity#yyyy-mm`, `SK = day#hh#event`.
6. **Begin-and-end markers** — use `~` (tilde sorts after digits/letters) as a cheap upper bound for `BETWEEN`.

## Revision notes

> **dynamodb sort key — 60s recap**
> - SK = the only range/prefix scan inside a partition.
> - Composite: `TYPE#sub#TYPE#sub` with `#` delimiter.
> - Zero-pad numerics; use ISO-8601 timestamps as strings.
> - Operators: `=`, `<`, `>`, `BETWEEN`, `begins_with`. No `contains`/`ends_with`.
> - Discriminator (META/ITEM) at PREFIX, not suffix.
> - `ScanIndexForward: false` for newest-first.
> - Multiple access patterns → GSIs with different SK.
> - Hierarchical: ORDER#date#ITEM#seq supports 4 queries from 1 SK design.
