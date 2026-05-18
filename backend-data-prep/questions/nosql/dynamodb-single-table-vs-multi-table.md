# DynamoDB: Single-table vs multi-table design

## Source / Origin
- The defining DynamoDB design question. Asked at every AWS-shop interview. Popularized by Rick Houlihan.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Single-table design is the **most counter-intuitive idea in DynamoDB**. Coming from SQL, you instinctively want one table per entity. Senior signal: you can argue *both sides*, name the tradeoffs (debuggability vs performance, schema rigidity vs flexibility), and pick based on the team's experience and access patterns.

## Concepts involved

### Syntax to lock in

```javascript
// Single table with generic PK/SK and GSI overloading
{
  TableName: "App",
  KeySchema: [
    { AttributeName: "PK", KeyType: "HASH" },
    { AttributeName: "SK", KeyType: "RANGE" }
  ],
  AttributeDefinitions: [
    { AttributeName: "PK",      AttributeType: "S" },
    { AttributeName: "SK",      AttributeType: "S" },
    { AttributeName: "gsi1pk",  AttributeType: "S" },
    { AttributeName: "gsi1sk",  AttributeType: "S" }
  ],
  GlobalSecondaryIndexes: [
    {
      IndexName: "GSI1",
      KeySchema: [
        { AttributeName: "gsi1pk", KeyType: "HASH"  },
        { AttributeName: "gsi1sk", KeyType: "RANGE" }
      ],
      Projection: { ProjectionType: "ALL" }
    }
  ]
}
```

### Single-table vs multi-table

| Aspect | Single-table | Multi-table |
|---|---|---|
| Performance | One Query returns related entities in one trip | Multiple Queries, manual stitching |
| Cost | Fewer round trips, fewer GSI duplicates | Simpler isolation |
| Operability | Hard to read raw items; bespoke vocabulary | Familiar (one entity = one table) |
| Schema changes | Add a new access pattern = add a GSI overload or rewrite SK pattern | Add a new table |
| Debugging | "What does PK=ORG#1 SK=USER#5 even mean?" — needs a schema doc | Self-describing |
| Best for | Stable, well-understood access patterns | Exploratory phase, mixed teams |

### Edge cases / interview traps

1. **GSI overloading** — same `gsi1pk` attribute means different things on different entities (`userId` on one row, `orgId` on another). Powerful but easy to mess up.
2. **Heterogeneous items in one table** — Order rows, User rows, Item rows all coexist. ItemTypeAttribute (`type`) helps filter.
3. **Schema discipline is a code concern.** DynamoDB doesn't enforce it; your access layer must.
4. **Migration is brutal.** Moving an entity out of a single table = full backfill.
5. **Multi-table is fine if your access patterns are simple.** Don't single-table everything.
6. **Single-table doesn't mean one item with N nested entities.** It means N items sharing one table with structured keys.
7. **Streams / triggers** — single-table streams have heterogeneous events; consumers must dispatch by type.
8. **Backups** — same — but restore granularity is whole-table, not per-entity.

## Mental Model

> Single-table = a giant filing cabinet where the **labels on the folders encode the entity type and relationships**. You don't shuffle folders; you grab one drawer and pick out the labeled set in one motion.

```
   PK            SK                            type    attrs
   ───────────────────────────────────────────────────────────────
   ORG#1         METADATA                      org     {name, plan}
   ORG#1         USER#U-1                      user    {name, role}
   ORG#1         USER#U-2                      user    {name, role}
   ORG#1         PROJECT#P-1                   project {title}
   ORG#1         PROJECT#P-1#TASK#T-1          task    {title, owner}
   ORG#1         PROJECT#P-1#TASK#T-2          task    {title, owner}

   Query PK=ORG#1                              → entire org tree in 1 trip
   Query PK=ORG#1 begins_with(SK,"USER#")      → just users
   Query PK=ORG#1 begins_with(SK,"PROJECT#P-1")→ project + its tasks
```

## Why interviewers care

- Tests **modeling-by-access-pattern** at full depth.
- Tests **honesty about complexity** — single-table is hard to maintain.
- Tests **GSI overloading literacy** — the senior tooling skill.

## Common beginner confusion

- "Single-table = one item." It's many items sharing one table with overloaded keys.
- "Single-table is always better." No — small services with 1–2 access patterns shouldn't bother.
- "Multi-table can't do joins anyway, so just use single-table." Joins aren't the only reason; co-location for hot reads is.
- "I'll figure out the access patterns later." This is exactly when multi-table is right — you don't know yet.
- "GSI overloading is hard-coding." It's *structured* keys, like a routing prefix.

## Brute force approach

One table per entity, Lambdas/services do all the joins. Simple. Costs you 3–5× round trips for any non-trivial access pattern. Fine for low scale.

## Optimal approach

**Use single-table when:**
- Access patterns are well-understood and stable.
- A common access pattern needs related entities in one trip (e.g., load whole order + items + customer).
- Team is fluent in DynamoDB and has tooling.

**Use multi-table when:**
- Access patterns are evolving / exploratory.
- Entities are loosely related, accessed independently.
- Team prefers debuggability over peak performance.
- You're new to DynamoDB.

If single-table:
1. List all entities and their access patterns.
2. Map each to a `(PK, SK)` pattern with type prefixes.
3. Identify alternate access patterns; add GSI overloads (`gsi1pk`, `gsi1sk`).
4. Document the key schema as code (`KeySchemas.user(id)`, `KeySchemas.order(userId, orderId)`).
5. Provide a "decoder ring" doc.

## Solution (DynamoDB JSON + access layer)

```javascript
// === Key builder module ===
const Keys = {
  org:      (orgId)               => ({ PK: `ORG#${orgId}`, SK: "METADATA" }),
  user:     (orgId, userId)       => ({ PK: `ORG#${orgId}`, SK: `USER#${userId}` }),
  project:  (orgId, projId)       => ({ PK: `ORG#${orgId}`, SK: `PROJECT#${projId}` }),
  task:     (orgId, projId, taskId) =>
    ({ PK: `ORG#${orgId}`, SK: `PROJECT#${projId}#TASK#${taskId}` })
};

// === Access patterns ===

// 1. Load full org tree
await ddb.query({ TableName: "App", KeyConditionExpression: "PK = :p",
  ExpressionAttributeValues: { ":p": "ORG#1" } });

// 2. Just users in org
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :p AND begins_with(SK, :pref)",
  ExpressionAttributeValues: { ":p": "ORG#1", ":pref": "USER#" }
});

// 3. Project + its tasks
await ddb.query({
  TableName: "App",
  KeyConditionExpression: "PK = :p AND begins_with(SK, :pref)",
  ExpressionAttributeValues: { ":p": "ORG#1", ":pref": "PROJECT#P-1" }
});

// 4. Alternate access: find user by email (GSI overload)
// On a user row, set gsi1pk = `EMAIL#${email}`, gsi1sk = `USER#${userId}`
await ddb.query({
  TableName: "App",
  IndexName: "GSI1",
  KeyConditionExpression: "gsi1pk = :e",
  ExpressionAttributeValues: { ":e": "EMAIL#alice@example.com" }
});

// 5. Alternate access: tasks assigned to a user (GSI overload)
// On a task row, set gsi1pk = `ASSIGNEE#${userId}`, gsi1sk = `TASK#${createdAt}`
await ddb.query({
  TableName: "App",
  IndexName: "GSI1",
  KeyConditionExpression: "gsi1pk = :u AND begins_with(gsi1sk, :pref)",
  ExpressionAttributeValues: { ":u": "ASSIGNEE#U-1", ":pref": "TASK#" }
});
```

### Decoder ring (the doc your team needs)

```
PK pattern        SK pattern                          type     gsi1pk            gsi1sk
ORG#<orgId>       METADATA                            org      —                 —
ORG#<orgId>       USER#<userId>                       user     EMAIL#<email>     USER#<userId>
ORG#<orgId>       PROJECT#<projId>                    project  —                 —
ORG#<orgId>       PROJECT#<projId>#TASK#<taskId>      task     ASSIGNEE#<userId> TASK#<createdAt>
```

## Step-by-step dry run

```
Workload: B2B SaaS. Entities: Org, User, Project, Task.
Access patterns:
  A1. Load full org tree (settings page).
  A2. Load org users (admin page).
  A3. Load project + tasks (project page).
  A4. Find user by email (login).
  A5. List tasks assigned to user (my-tasks page).

Multi-table approach:
  4 tables. A1 = 4 Queries. A3 = 2 Queries. Each adds latency.

Single-table approach:
  All 5 patterns from 1 table + 1 GSI.
  A1 = Query PK="ORG#1"           → 1 trip
  A2 = Query PK="ORG#1" begins_with("USER#")  → 1 trip
  A3 = Query PK="ORG#1" begins_with("PROJECT#P-1")  → 1 trip
  A4 = Query GSI1 gsi1pk="EMAIL#x"  → 1 trip
  A5 = Query GSI1 gsi1pk="ASSIGNEE#U-1"  → 1 trip

  Cost: 1 table, 1 GSI, 5 access patterns. Tooling: a decoder ring doc.
```

## How to think aloud in the interview

> "Two camps. Single-table maxes performance and minimizes round trips; multi-table maximizes debuggability and lets the team iterate on access patterns. I pick based on team fluency and stability of access patterns.
>
> For single-table I list every entity and every access pattern *first*, then map to `(PK, SK)` with type prefixes — `ORG#<id>`, `USER#<id>`, `PROJECT#<id>#TASK#<id>`. Hierarchical SKs let me load an org's whole tree in one Query.
>
> Alternate access patterns I encode with GSI overloading: `gsi1pk = "EMAIL#"+email` on user rows, `gsi1pk = "ASSIGNEE#"+userId` on task rows. Same GSI, multiple entity types, dispatched by a `type` attribute.
>
> The cost is operability: raw items are unreadable without a decoder ring. I write that doc upfront and check it in next to the table schema. Tests and the access-layer module enforce the conventions.
>
> If the access patterns are still being explored, I prefer multi-table — easier to throw away. Single-table earns its keep when patterns are stable."

## Important takeaways

- **Single-table = one table, many entity types, overloaded keys.**
- **Co-locate related entities** for one-trip queries.
- **GSI overloading**: generic `gsi1pk`/`gsi1sk` attributes, type prefixes encode access.
- **Decoder ring** doc is mandatory — items are unreadable without it.
- **Multi-table is fine** for exploratory / loosely related entities.
- **Migration is hard.** Pre-commit to one approach early.
- **Access layer** = key builders + dispatcher by `type`.

## Variants

1. **Adjacency list** — many-to-many via two rows per relationship (covered in separate file).
2. **Tree structures** — `SK = parent#child#grandchild#...` for unbounded depth.
3. **Type discriminator** — every item carries `type` attribute; filters and stream consumers dispatch on it.
4. **Multi-tenant single-table** — `PK = TENANT#<id>#...` prefixes everything.
5. **Mixed approach** — single-table for hot core entities, multi-table for adjuncts (logs, analytics).
6. **Two GSIs** for orthogonal alternate accesses (`GSI1` for email, `GSI2` for assignee).

## Revision notes

> **single-table vs multi-table — 60s recap**
> - Single-table: co-locate entities, one-trip queries, hard to debug.
> - Multi-table: simple, debuggable, more round trips.
> - List access patterns FIRST, then map to (PK, SK) with type prefixes.
> - GSI overloading: generic gsi1pk/gsi1sk, different meanings per entity type.
> - Decoder ring doc is mandatory.
> - Migration off single-table is brutal — commit early.
> - Default to multi-table for exploratory work; single-table when patterns are stable.
