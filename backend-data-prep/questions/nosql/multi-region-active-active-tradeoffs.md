# Design multi-region active-active and articulate the tradeoffs you cannot escape

## Source / Origin
- Senior system design discriminator. Appears at FAANG/fintech rounds, distributed-systems heavy roles.
- DynamoDB Global Tables, Cassandra multi-DC, CosmosDB multi-region writes, Spanner external consistency.
- Concept reference: `backend-data-prep/nosql/multi-region.md`.

## Why this question matters in interviews
"Active-active" is a magnet phrase that candidates throw around without owning the tradeoffs. The interviewer's signal: do you know that **active-active means giving up linearizable writes** (or paying Spanner-class latency for them)? Can you name the four conflict-resolution strategies (LWW, CRDT, app-resolve, single-writer-per-key) and pick correctly? Can you explain why DynamoDB Global Tables advertise "eventual consistency only on cross-region replication" and what that means at 2 AM during a region failover? Owning this tells the panel you have built — or seriously thought about — geo-distributed systems.

## Concepts involved

### Syntax to lock in

```yaml
# DynamoDB Global Tables — provisioning
aws dynamodb create-global-table \
  --global-table-name Orders \
  --replication-group RegionName=us-east-1 RegionName=eu-west-1 RegionName=ap-south-1
# Conflict resolution: last-writer-wins by timestamp. No tunable.
# Read consistency: eventually consistent across regions; strong only within region.
```

```cql
-- Cassandra multi-DC keyspace
CREATE KEYSPACE orders WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'us_east': 3,
  'eu_west': 3
};
-- LOCAL_QUORUM for reads/writes; EACH_QUORUM if you need cross-DC durability.
```

```javascript
// MongoDB replica set across regions (NOT active-active — primary only writes)
// To get multi-region writes: sharded cluster with zone sharding.
sh.addShardTag("shard-us", "US");
sh.addShardTag("shard-eu", "EU");
sh.addTagRange("orders.orders",
  { region: "US", _id: MinKey }, { region: "US", _id: MaxKey }, "US");
// Each shard's writes stay in its region.
```

### Edge cases / interview traps

1. **"Active-active" is overloaded.** Three flavours: (a) sharded by key — each region owns a slice (no conflicts); (b) replicated with LWW (conflicts silently resolved); (c) replicated with CRDTs (conflicts merged). Be explicit about which one.
2. **CAP under partition is non-negotiable.** During a cross-region link failure you choose: keep accepting writes in both regions (AP — diverge, reconcile later) OR refuse writes on one side (CP — sacrifice availability). No engineering cleverness escapes this.
3. **LWW silently loses writes.** Two writes 5ms apart in different regions: the "newer" timestamp wins, the other vanishes. NTP skew makes "newer" meaningless at sub-second.
4. **Clock skew is the boogeyman.** Hybrid logical clocks (HLCs), TrueTime (Spanner), or vector clocks (Riak, DynamoDB old) exist *because* wall clocks lie across regions.
5. **Read-your-write across regions doesn't exist for free.** A user in EU writes, then their request gets routed to US replica — they see stale data. Sticky sessions or read-from-leader-region for the user's own writes.
6. **Failover ≠ active-active.** Active-passive with fast DNS failover is *much* simpler. Sell that first if requirements allow.
7. **Compliance kills truly global active-active.** GDPR data residency forces EU data to stay in EU. That's zone sharding, not full replication.

## Mental Model

The **"three offices, one ledger"** model.

```
   us-east   ←──── async replication ────→   eu-west
      ▲                                          ▲
      │ writes accepted locally                  │ writes accepted locally
      │ <10ms ack                                │ <10ms ack
      └─ replication lag: 100–500ms             ─┘

   If both regions write to the same row at "the same time":
     - LWW:    one wins by timestamp, other silently dropped
     - CRDT:   both merge deterministically (e.g., set union, counter add)
     - App:    surface both versions, ask user / business rule
     - Shard:  impossible by design — only one region owns this row
```

The single trick: **decide where the write conflict happens**. Either (a) prevent it (sharding) or (b) resolve it (LWW/CRDT/app).

## Why interviewers care

- Tests whether you've internalised that "global" + "strongly consistent" + "low write latency" is the **impossible triangle**. Pick two.
- Surfaces real operational experience: failover runbooks, split-brain handling, residency rules.
- Differentiates "I read the AWS blog" from "I've debugged divergence at 2 AM".

## Common beginner confusion

- "DynamoDB Global Tables give strong consistency globally." False — eventual cross-region; strong only within a region.
- "Cassandra `QUORUM` works across DCs." It does, but it costs the cross-region RTT on every write. `LOCAL_QUORUM` is the sane default.
- "CRDTs solve all conflicts." They handle the data types they're defined for (counters, sets, registers). Order-sensitive business logic (e.g., "first to redeem coupon wins") is not CRDT-friendly.
- "We'll just sync clocks." NTP gives ~10ms; that's an eternity for conflict resolution. You need HLC or causal tracking.
- "Active-active doubles availability." It can also double the failure surface — bad config replicates everywhere.

## Brute force approach

Two-phase commit across regions (XA). Works; cross-region RTT (~80–150ms) becomes the write latency floor; any region failure blocks all writes globally. Almost nobody runs this.

## Optimal approach

Four real patterns, ranked by how often they're the right answer:

1. **Zone-sharded (region-partitioned)** — each key belongs to one region; reads/writes for that key go there; other regions get async read replicas. No conflicts. Use when data has natural locality (users, tenants).
2. **Active-active with LWW + idempotent writes** — DynamoDB Global Tables, Cassandra. Acceptable when writes are idempotent and occasional silent loss is tolerable (analytics, telemetry, soft state).
3. **CRDT-based** — Riak, Redis CRDTs, AntidoteDB. Counters, sets, maps merge deterministically. Use for cart-merge, like-counts, presence.
4. **Spanner / CockroachDB / YugabyteDB** — synchronous Paxos/Raft across regions with TrueTime or HLC. Strong consistency globally; write latency = cross-region RTT (~100ms). Pay the cost when correctness > latency.

## Solution

```
┌──────────────────────────────────────────────────────────────────────┐
│  Pattern A: Zone Sharding (the boring, correct answer 70% of the    │
│             time)                                                    │
├──────────────────────────────────────────────────────────────────────┤
│   us-east        eu-west        ap-south                             │
│   ┌────────┐   ┌────────┐    ┌────────┐                              │
│   │user_id │   │user_id │    │user_id │                              │
│   │region= │   │region= │    │region= │                              │
│   │ "US"   │   │ "EU"   │    │ "IN"   │                              │
│   └────────┘   └────────┘    └────────┘                              │
│        ▲             ▲              ▲                                │
│        └─ async read-replicas to other regions for non-write paths ─┘│
│                                                                      │
│   Routing: edge (CloudFront/Route53 latency-based) → user's home    │
│   region. Failover: pick a secondary region, write goes there,      │
│   accept eventual reconcile.                                         │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Pattern B: Active-active with LWW (DynamoDB Global Tables)         │
├──────────────────────────────────────────────────────────────────────┤
│   Write in us-east at t=100ms:  {user=alice, name="Alice K"}        │
│   Write in eu-west  at t=102ms: {user=alice, name="Alice K-S"}      │
│                                                                      │
│   After replication: name="Alice K-S" everywhere (higher TS wins)   │
│   First write silently lost.                                         │
│                                                                      │
│   Mitigations:                                                       │
│   - Make writes additive (append-only events, not in-place edits)   │
│   - Use HLC, not wall clock                                          │
│   - Detect divergence via async reconciliation jobs                 │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Pattern C: CRDT (Riak / Redis CRDTs)                               │
├──────────────────────────────────────────────────────────────────────┤
│   shopping_cart: ORSet                                              │
│     us-east adds "sku-1"                                            │
│     eu-west adds "sku-2"                                            │
│     replicas converge to {sku-1, sku-2}  ← no loss                  │
│                                                                      │
│   counter: PNCounter                                                │
│     us-east +5, eu-west +3 → 8 everywhere                           │
│                                                                      │
│   Caveat: cannot express "deduct only if balance ≥ amount"          │
│   (a guarded operation). Needs single-writer or consensus.          │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Pattern D: Globally-consistent (Spanner / Cockroach / Yugabyte)    │
├──────────────────────────────────────────────────────────────────────┤
│   Raft groups span regions. Quorum write = majority across regions. │
│   Write latency floor ≈ cross-region RTT to second-nearest region   │
│   (~80ms US-east ↔ US-west, ~150ms US ↔ EU).                        │
│                                                                      │
│   You get: serializable, read-your-write, no conflicts.             │
│   You pay: latency, $$, operational complexity.                     │
└──────────────────────────────────────────────────────────────────────┘
```

## Step-by-step dry run

Scenario: a user in EU updates their email; 200ms later they refresh the page; their request lands in US edge.

```
Pattern A (zone-sharded, user owns EU):
  Write   → EU primary → ACK ~10ms → async replicate to US (~200ms)
  Refresh → Edge sees user.region=EU → route to EU → reads own write ✓

Pattern B (LWW global tables):
  Write   → EU local write → ACK ~10ms → async replicate to US
  Refresh → routed to US (latency-based DNS) → reads US replica
            → if replication hasn't arrived: STALE EMAIL VISIBLE
  Fix: sticky session by user, or read-from-EU for this user

Pattern D (Spanner):
  Write   → Paxos quorum across regions → ACK ~120ms
  Refresh → routed to nearest replica → strong read → up-to-date ✓
  Cost: every write paid 120ms; UX may not love it
```

Failover scenario: us-east region down.

```
Pattern A: users in US lose writes until they're re-routed to a backup region.
           On reroute, their writes go to a region that doesn't own them →
           reconciliation queue on recovery.
Pattern B: writes redirected to eu-west. On us-east recovery, replication
           catches up; LWW resolves. Silent loss for concurrent writes.
Pattern D: if quorum is still achievable (majority alive), business as usual.
           If a whole region containing >50% replicas drops, writes pause.
```

## How to think aloud in the interview

> "Before I draw, I ask: do you actually need multi-region *writes*, or just multi-region *reads with fast failover*? Active-passive with DNS failover is dramatically simpler and is the right answer 80% of the time.
>
> If you genuinely need active-active, I'd next ask: can data be partitioned by region — users, tenants, hash zones? If yes, **zone sharding** — each region owns its keys, no conflicts. That's pattern A and it's almost always the answer.
>
> If keys are genuinely global and shared: I'd pick the conflict-resolution model. **LWW** (DynamoDB Global Tables) if writes are idempotent or last-write-wins matches the business rule. **CRDTs** for additive data — counters, sets, presence. **Spanner-class consensus** when correctness beats latency.
>
> The non-negotiables: clock skew makes wall-clock LWW dangerous → use HLC. Read-your-write across regions needs sticky routing. CAP is real — during a partition I pick AP (accept divergence) or CP (refuse writes); I name which and the rationale."

## Important takeaways

- Active-active means accepting one of: (a) sharded keys, (b) conflict resolution, (c) cross-region consensus cost.
- Default to zone sharding when data has locality. Default to active-passive when you can live with failover RTO.
- DynamoDB Global Tables / Cassandra multi-DC = LWW + async; silent conflict loss is real.
- CRDTs cover additive types; not guarded operations.
- Spanner/Cockroach/Yugabyte buy strong consistency with cross-region write latency.
- Wall clocks lie; use HLC or causal tracking.
- Compliance (GDPR data residency) often forces zone sharding regardless.

## Variants

1. **Cell-based architecture (AWS)** — region split into cells; failure blast radius bounded; orthogonal to active-active but often combined.
2. **DynamoDB Global Tables vs. self-managed Cassandra multi-DC** — DDB easier; less control over conflict resolution; LWW only.
3. **CosmosDB multi-master** — five consistency levels (strong / bounded staleness / session / consistent prefix / eventual); rare full menu.
4. **MongoDB zone sharding for residency** — not active-active in the conflict sense; each zone is the only writer for its keys.
5. **Geo-partitioned tables in Cockroach** — declare row-level region via `REGIONAL BY ROW`; engine handles routing.

## Revision notes

> **multi-region active-active — 60s recap**
> - Three flavours: zone-sharded, replicated-with-conflict-resolution, consensus-across-regions.
> - Default answer: zone sharding (no conflicts). Sell active-passive first if RTO allows.
> - LWW (DynamoDB GT, Cassandra) silently loses writes; needs HLC, idempotent writes.
> - CRDTs cover counters/sets; not guarded ops.
> - Spanner/Cockroach/Yugabyte = strong consistency, cross-region write latency.
> - CAP during partition: choose AP (diverge) or CP (refuse). Name it.
> - Clock skew, read-your-write routing, GDPR residency are the silent killers.
