# DynamoDB: Adjacency list — many-to-many in a single table

## Source / Origin
- Rick Houlihan's hallmark pattern. Asked at AWS re:Invent-style interviews.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Many-to-many relationships look impossible in DynamoDB without joins. The adjacency-list pattern solves them with **two rows per edge** and **GSI for reverse lookup**. Senior signal: you walk through the user-follows-user or student-enrolls-in-course example, draw both directions, and discuss the consistency tradeoffs.

## Concepts involved

### Syntax to lock in

```javascript
// Edge: U-1 follows U-2
// Forward edge row:
{ PK: "USER#U-1", SK: "FOLLOWS#U-2", createdAt: "...", gsi1pk: "USER#U-2", gsi1sk: "FOLLOWED_BY#U-1" }
// (Optional) reverse edge row for tighter consistency:
{ PK: "USER#U-2", SK: "FOLLOWED_BY#U-1", createdAt: "..." }

// Query: who does U-1 follow?
{ KeyConditionExpression: "PK = :pk AND begins_with(SK, :pref)",
  ExpressionAttributeValues: { ":pk": "USER#U-1", ":pref": "FOLLOWS#" } }

// Query: who follows U-2? (via GSI)
{ IndexName: "GSI1",
  KeyConditionExpression: "gsi1pk = :pk AND begins_with(gsi1sk, :pref)",
  ExpressionAttributeValues: { ":pk": "USER#U-2", ":pref": "FOLLOWED_BY#" } }
```

### Adjacency list shapes

| Shape | Forward query | Reverse query |
|---|---|---|
| **One row + GSI** | PK=A SK=REL#B | GSI1 PK=B sk=INVREL#A |
| **Two rows** | PK=A SK=REL#B | PK=B SK=INVREL#A |
| **Three rows** | Edge metadata in a third PK=EDGE#A-B row |

### Edge cases / interview traps

1. **Single-row + GSI is cheapest** for read-heavy graphs. Reverse reads go via GSI.
2. **Two-row pattern** for write-heavy or when GSI eventual consistency is unacceptable.
3. **Transactional edge writes** — TransactWriteItems guarantees both rows succeed or neither.
4. **Edge metadata** (timestamp, role, weight) — store on the forward row; duplicate to reverse only if needed.
5. **Deletion** — both rows must be removed; use TransactWriteItems.
6. **Cardinality bombs** — celebrity with 100M followers blows up Query latency; paginate or use GSI on follower side with bucket-sharding.
7. **Recursive relationships** (org chart, comments) — use prefix SK to walk descendants.
8. **GSI throttling** — heavy edge writes hit GSI partition limits separately.

## Mental Model

> An edge is **two pieces of evidence**: "A says they follow B" and "B says A follows them." You can store one piece and infer the other via a GSI, or store both pieces explicitly.

```
   Forward + GSI (one row per edge)
     Base table:
       PK=U-1 SK=FOLLOWS#U-2        gsi1pk=U-2  gsi1sk=FOLLOWED_BY#U-1
       PK=U-1 SK=FOLLOWS#U-3        gsi1pk=U-3  gsi1sk=FOLLOWED_BY#U-1
       PK=U-7 SK=FOLLOWS#U-2        gsi1pk=U-2  gsi1sk=FOLLOWED_BY#U-7

     GSI1:
       gsi1pk=U-2  → gsi1sk=FOLLOWED_BY#U-1, FOLLOWED_BY#U-7
       gsi1pk=U-3  → gsi1sk=FOLLOWED_BY#U-1

   Two rows per edge (both bases of truth)
     PK=U-1 SK=FOLLOWS#U-2          (forward)
     PK=U-2 SK=FOLLOWED_BY#U-1      (reverse)
```

## Why interviewers care

- Tests **graph-modeling in a non-graph DB** — the senior trick.
- Tests **GSI literacy** — reverse lookup via overloaded attributes.
- Tests **transaction reasoning** — atomicity of edge writes.

## Common beginner confusion

- "Use a join table." There are no joins.
- "Use one big array on the user row." Caps at 400KB item size and 100s of elements.
- "GSI is strong-consistent like LSI." It isn't; reverse reads are eventual.
- "Just denormalize follower lists on both ends." Same as adjacency list, but unmanaged.
- "Edge is symmetric, store once." Follow is directed; co-author might be symmetric but you still need both views in queries.

## Brute force approach

Store followers as a JSON array on each user. Works until lists get >100 entries; then writes become full-doc rewrites; then they exceed 400KB. Don't.

## Optimal approach

**Read-heavy graph** → one edge row + GSI for reverse.
**Write-heavy graph** → two edge rows + TransactWriteItems for atomicity.
**Edge metadata** (timestamp, role) → forward row carries it; copy to reverse if reverse-side reads need it.
**Cardinality limit** → paginate; for extreme cardinality, bucket the GSI side.

## Solution (DynamoDB JSON + Node)

```javascript
// === Create follow edge (one-row + GSI) ===
async function follow(followerId, followeeId) {
  await ddb.put({
    TableName: "App",
    Item: {
      PK: `USER#${followerId}`,
      SK: `FOLLOWS#${followeeId}`,
      gsi1pk: `USER#${followeeId}`,
      gsi1sk: `FOLLOWED_BY#${followerId}`,
      createdAt: new Date().toISOString(),
      type: "edge"
    },
    ConditionExpression: "attribute_not_exists(PK)"   // idempotent
  });
}

// === Unfollow ===
async function unfollow(followerId, followeeId) {
  await ddb.delete({
    TableName: "App",
    Key: { PK: `USER#${followerId}`, SK: `FOLLOWS#${followeeId}` }
  });
}

// === Who does U-1 follow? ===
async function listFollowees(userId, limit = 50, cursor) {
  return ddb.query({
    TableName: "App",
    KeyConditionExpression: "PK = :pk AND begins_with(SK, :pref)",
    ExpressionAttributeValues: { ":pk": `USER#${userId}`, ":pref": "FOLLOWS#" },
    Limit: limit,
    ExclusiveStartKey: cursor
  });
}

// === Who follows U-2? (reverse via GSI) ===
async function listFollowers(userId, limit = 50, cursor) {
  return ddb.query({
    TableName: "App",
    IndexName: "GSI1",
    KeyConditionExpression: "gsi1pk = :pk AND begins_with(gsi1sk, :pref)",
    ExpressionAttributeValues: { ":pk": `USER#${userId}`, ":pref": "FOLLOWED_BY#" },
    Limit: limit,
    ExclusiveStartKey: cursor
  });
}

// === Two-row pattern with transaction ===
async function followTwoRow(followerId, followeeId) {
  const now = new Date().toISOString();
  await ddb.transactWrite({
    TransactItems: [
      { Put: {
          TableName: "App",
          Item: { PK: `USER#${followerId}`, SK: `FOLLOWS#${followeeId}`, createdAt: now },
          ConditionExpression: "attribute_not_exists(PK)"
      }},
      { Put: {
          TableName: "App",
          Item: { PK: `USER#${followeeId}`, SK: `FOLLOWED_BY#${followerId}`, createdAt: now },
          ConditionExpression: "attribute_not_exists(PK)"
      }}
    ]
  });
}

// === Counter denormalization (for "follower count" UI) ===
await ddb.update({
  TableName: "App",
  Key: { PK: `USER#${followeeId}`, SK: "METADATA" },
  UpdateExpression: "ADD followerCount :one",
  ExpressionAttributeValues: { ":one": 1 }
});
// Wrap in TransactWriteItems with the edge Put for atomicity.
```

### Example: student ↔ course (M:N with edge metadata)

```javascript
// Forward edge: student enrolled in course
{ PK: "STUDENT#S-1", SK: "ENROLLED#C-101", grade: null, enrolledAt: "...", gsi1pk: "COURSE#C-101", gsi1sk: "STUDENT#S-1" }

// Reverse query: who is in course C-101?
// IndexName=GSI1, gsi1pk="COURSE#C-101", begins_with(gsi1sk, "STUDENT#")
```

## Step-by-step dry run

```
Initial: U-1, U-2, U-3 exist as PK=USER#... SK=METADATA rows.

t=0   follow("U-1", "U-2") → put { PK:USER#U-1, SK:FOLLOWS#U-2, gsi1pk:USER#U-2, gsi1sk:FOLLOWED_BY#U-1 }
t=1   follow("U-3", "U-2") → put { PK:USER#U-3, SK:FOLLOWS#U-2, gsi1pk:USER#U-2, gsi1sk:FOLLOWED_BY#U-3 }

Query "who does U-1 follow":
  base: PK=USER#U-1, begins_with(SK, "FOLLOWS#") → 1 row → U-2

Query "who follows U-2":
  GSI1: gsi1pk=USER#U-2, begins_with(gsi1sk, "FOLLOWED_BY#") → 2 rows → U-1, U-3
  (eventual consistency; new follows may take ms to appear)

t=10  unfollow("U-1", "U-2") → delete one row; GSI auto-updates.

Failure: TransactWriteItems on two-row pattern
  If forward row exists but reverse insert fails (rare; quota/throttle):
  TransactWriteItems aborts; both Puts roll back. Atomicity guaranteed.
```

## How to think aloud in the interview

> "Adjacency list is how Dynamo does many-to-many. Each edge is at minimum one row in the base table with a *forward* `(PK, SK)` like `(USER#A, FOLLOWS#B)`. For reverse queries — 'who follows B' — I add a GSI by setting `gsi1pk = USER#B` and `gsi1sk = FOLLOWED_BY#A` on the same row. The GSI is a denormalized reverse view.
>
> If reverse reads must be strong-consistent (rare for follow graphs but real for permissions), I switch to a two-row pattern and write both rows in a TransactWriteItems. Atomicity guaranteed, double the write cost.
>
> Edge metadata — timestamp, role, weight — lives on the forward row. If the reverse view needs it, I copy. For counts I keep a denormalized `followerCount` on the user metadata row, updated atomically with the edge write inside the transaction.
>
> Cardinality bombs: a celebrity with 100M followers. Pagination is required (no full-load API), and for write-side hotspots I bucket-shard the GSI partition: `gsi1pk = USER#celeb#bucket(0..N)`."

## Important takeaways

- **Adjacency list = (PK=A, SK=REL#B) + GSI for reverse.** Or two rows for atomic both-sides.
- **TransactWriteItems** for atomic dual-row writes.
- **Edge metadata on forward row.** Copy if reverse needs it.
- **GSI reads are eventual.** Plan for stale reverse views.
- **Counters denormalized** with the edge write in same txn.
- **Celebrity reverse partition** → bucket-shard GSI side.
- **Pagination is mandatory** for unbounded relationships.

## Variants

1. **Symmetric relationships** (friends, co-authors) — store both directions as the canonical pattern.
2. **Hierarchical (tree)** — `SK = PARENT#P-1#CHILD#C-1#GRANDCHILD#G-1`.
3. **Weighted edges** — store weight on the edge row; sort by weight via additional SK component.
4. **Time-ordered relationships** — `SK = FOLLOWS#<timestamp>#B` for "follows in chrono order".
5. **RBAC** — `(USER#U, ROLE#R)` + `(ROLE#R, PERM#P)`; query via GSI to find users with a permission.
6. **Graph traversal** — recursive function: query out-edges, recurse on each target. Limit depth.

## Revision notes

> **adjacency list — 60s recap**
> - Edge = one row PK=A SK=REL#B + GSI overload for reverse.
> - Or two rows for strong-consistent both-sides; TransactWriteItems for atomicity.
> - Edge metadata (ts, role, weight) on forward row.
> - GSI reads = eventual; reverse view may lag.
> - Counters denormalized on metadata row, atomic with edge write.
> - Pagination mandatory for unbounded relations.
> - Celebrity reverse → bucket-shard the GSI partition.
> - Hierarchies → prefix SK with full path.
