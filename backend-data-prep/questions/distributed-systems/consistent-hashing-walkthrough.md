# Consistent Hashing — Ring, Virtual Nodes, and Key Mapping

## Source / Origin
- Karger et al., "Consistent Hashing and Random Trees" (STOC 1997) — original paper from Akamai's founding work.
- DeCandia et al., "Dynamo: Amazon's Highly Available Key-value Store" (SOSP 2007) — popularised vnodes.
- Cassandra, Riak, DynamoDB, ScyllaDB, memcached (Ketama), Envoy load-balancer — all use this directly.
- Interview prompt: "How do you partition a billion keys across 100 servers and handle elastic scale?" — staple at any infrastructure round.

## Why this question matters in interviews
Consistent hashing is the *most-asked* distributed-systems mechanism after CAP. Every senior backend interview has a sharding question, and "rehashing modulo N" vs "consistent hashing" is the canonical trade-off. Interviewers want (a) the ring picture drawn correctly, (b) the math on key movement when a node is added or removed, (c) the *virtual node* refinement and why naive consistent hashing is insufficient, and (d) a follow-up on replica placement. Candidates who fumble vnodes typically get caught at the load-imbalance question.

## Concepts involved

### Syntax / mechanism to lock in

```
1. Hash space: [0, 2^32) (typical: MurmurHash3 or MD5 truncated).
2. Each node N gets a position pos(N) = hash(node_id) on the ring.
3. Each key K maps to position pos(K) = hash(K).
4. Key K is owned by the first node clockwise from pos(K).

Operations:
   add_node(N):     hash N → insert into ring → keys in (predecessor, N] move from successor to N.
   remove_node(N):  remove N → keys (predecessor, N] now belong to successor.
   lookup(K):       hash K → find ceil(K) on the ring → return that node.
```

Virtual nodes (vnodes):
```
For each physical node, generate V virtual replicas: hash("nodeA#0"), hash("nodeA#1"), ..., hash("nodeA#V-1").
Each goes on the ring at its own position.
A key's owner is the physical node behind the next vnode clockwise.
Typical V = 128 or 256 per physical node.
```

### Edge cases / interview traps
1. **Without vnodes, load imbalance is severe.** Just 3 nodes randomly placed on a ring will not split the space into 3 equal arcs; one node may own 60% of the keyspace by luck.
2. **Adding a node only affects keys between predecessor and the new node.** Movement is O(K/N) keys, not O(K) — this is the whole point.
3. **Replication = next R nodes clockwise.** Skip the same physical node when walking vnodes — otherwise two replicas live on the same physical box.
4. **Hash function choice matters.** Use MurmurHash3 or MD5; not Java's default `hashCode()`. Bad hash = clustered positions = imbalance.
5. **Ring is logical; lookups are local.** A correctly-implemented client maintains its own copy of the ring; no network call to find owner.
6. **Membership-change consistency.** When a node joins, *who* updates the ring? Typically gossip (Dynamo, Cassandra) or external coordination (etcd-driven).
7. **Hot key bypasses the design.** A single key receiving 10× the traffic still lands on one node; consistent hashing doesn't help. Need request-level fan-out or hot-key sharding.
8. **Anti-affinity / rack-awareness.** Replica selection must skip same-rack vnodes for the *physical* disaster-tolerance constraint.
9. **Bounded-load consistent hashing** (Google, 2016) — augment with a load constraint so heavily-loaded nodes overflow to next.
10. **Removal of a vnode does not necessarily move all its keys to the same successor** if successor differs per vnode; this is the load-spreading benefit.

## Mental Model

A clock face from 0 to 2^32. Each server gets pinned at some angle. Each key gets pinned at some angle. Each key belongs to whichever server is *just clockwise* from it.

```
                       0/2^32
                          │
                ┌─────────┼─────────┐
                │   ★Key1 │         │
            ★KeyA       ●NodeA      │
                │                   │
                │                   │
       NodeC●   │       Ring        │   ●NodeB
                │                   │
                │                   │
                │   ★Key3 ★Key2    │
                │                   │
                └─────────┼─────────┘
                          │
                       2^31

Key1 → NodeA  (clockwise next)
KeyA → NodeA
Key2 → NodeC  (clockwise next from lower-left)
Key3 → NodeC
```

With virtual nodes, instead of one mark per server you have hundreds — spreading the ownership statistically uniformly.

## Why interviewers care
- Tests understanding of *elastic sharding* — the foundation of modern cloud databases.
- The "movement on rebalance" math is exactly what determines downtime / migration cost in real systems.
- Replication-strategy questions (R replicas on the next R nodes) probe whether you've actually implemented a quorum store.
- Distinguishes from naive `hash(key) % N` modular sharding, which is the *negative example* every senior should reject without prompting.

## Common beginner confusion
- **"`hash(key) % N` is consistent hashing."** It is not. That's *modular* hashing. Adding a node changes N, which moves ~N-1/N fraction of keys. Consistent hashing moves ~1/N.
- **"More vnodes = always better."** Diminishing returns past V=128 or 256. More vnodes = larger ring data structure, slightly more lookup cost.
- **"Vnodes solve hot keys."** They don't. Hot keys are an orthogonal problem; vnodes solve cold-server imbalance.
- **"Each replica is on the next physical node."** Replication walks *vnodes* but must dedupe by physical node, or two replicas can live on one box.
- **"The ring is stored centrally."** No — every client/node maintains a copy; the ring is gossipped or distributed via membership protocol.
- **"Adding a node moves no data on neighbours."** It moves keys *to* the new node from the successor. That successor sees its load drop, but data moves.

## Brute force approach

**Modular sharding:** `node = hash(key) % N`. Trivial, fast. But when N changes from 4 to 5, every key gets a different node. Every cache value evicts; every database needs full rebalance. Catastrophic at elastic scale.

**Range sharding:** assign explicit key ranges. Manual, brittle, prone to hot-range. Used by HBase historically; not ideal for unbounded growth.

## Optimal approach

Consistent hashing with virtual nodes:
1. Hash both nodes (with V virtual copies each) and keys to the same hash space.
2. Maintain a sorted ring (e.g., `TreeMap<Long, NodeID>`).
3. Lookup: `ring.ceilingEntry(hash(key))` — O(log V·N).
4. On node join/leave: O(V log V·N) work per node; O(K/N) keys move.

For replication: walk clockwise from the primary's vnode, collecting R *distinct physical* nodes.

For elasticity: gossip the ring; let each node learn membership independently.

For hot keys: layer on top with explicit hot-key replication (see Variants).

## Solution (algorithm + pseudocode + diagram)

### Pseudocode (Java-style)

```java
class ConsistentHashRing {
    TreeMap<Long, String> ring = new TreeMap<>();
    int virtualNodes = 128;

    void addNode(String nodeId) {
        for (int i = 0; i < virtualNodes; i++) {
            long pos = murmur3(nodeId + "#" + i);
            ring.put(pos, nodeId);
        }
    }

    void removeNode(String nodeId) {
        for (int i = 0; i < virtualNodes; i++) {
            long pos = murmur3(nodeId + "#" + i);
            ring.remove(pos);
        }
    }

    String getNode(String key) {
        if (ring.isEmpty()) return null;
        long h = murmur3(key);
        Map.Entry<Long, String> e = ring.ceilingEntry(h);
        if (e == null) e = ring.firstEntry();   // wrap-around
        return e.getValue();
    }

    List<String> getReplicas(String key, int R) {
        if (ring.isEmpty()) return List.of();
        long h = murmur3(key);
        Set<String> distinct = new LinkedHashSet<>();
        Long pos = ring.ceilingKey(h);
        if (pos == null) pos = ring.firstKey();
        while (distinct.size() < R) {
            distinct.add(ring.get(pos));
            pos = nextKey(pos);
        }
        return new ArrayList<>(distinct);
    }
}
```

### Ring diagram with vnodes

```
   Hash space [0, 2^32), shown as a clock

                       12 (0 / 2^32)
                          │
            B3●       A2● │     ●C2
                 ●A1      │
       C1●                │            ●B1
                          │
       9 ────────●A3──────┼──────●B2──── 3
                          │
                          │            ●A0
                ●C3       │     ●B0
                          │
                       6

   Physical nodes: A, B, C (each with vnodes A0..A3, etc.)
   Keys land in arcs.

   Key K:  hash → arc (B2 → B0) → owned by physical node B
   Replicas R=3: walk clockwise from K, collect 3 distinct physical nodes
                  e.g., B, then A, then C  → replicas [B, A, C]
```

### Diagram: adding node D

```
Before:                       After D joins with 4 vnodes:

  A0 ───── B0                   A0 ───── B0
    \     /                       \  D0 /
     C0                             C0
                                    D1
                                    D2
                                    D3 inserted

Keys whose hash sits in arcs immediately preceding any D vnode
move from their old owner (the successor) to D.
Each arc is ~1/(N·V) of the keyspace.
Total moved: ~1/N of the data — not all data.
```

## Step-by-step dry run

3 physical nodes A, B, C, with **2 vnodes each** (small for illustration; production uses ~128). Hash space simplified to 0..99.

Vnode positions (after hashing):
```
A0=10, A1=70
B0=30, B1=85
C0=50, C1=95
```

Sorted ring: `10(A) 30(B) 50(C) 70(A) 85(B) 95(C)`

Five keys with hashes:
```
K1 hash=15  → ceiling(15) = 30(B) → owner B
K2 hash=42  → ceiling(42) = 50(C) → owner C
K3 hash=72  → ceiling(72) = 85(B) → owner B
K4 hash=88  → ceiling(88) = 95(C) → owner C
K5 hash=99  → ceiling(99) = wrap → 10(A) → owner A
```

Replicas R=2 for K2 (hash=42):
```
ceiling(42) = 50(C) → replica 1 = C
next       = 70(A) → replica 2 = A (distinct from C)
Final: [C, A]
```

Now add node D with vnodes D0=20, D1=60.

New sorted ring: `10(A) 20(D) 30(B) 50(C) 60(D) 70(A) 85(B) 95(C)`

Re-evaluate:
```
K1 hash=15 → ceiling(15) = 20(D)  ← MOVED from B to D
K2 hash=42 → ceiling(42) = 50(C)  ← unchanged
K3 hash=72 → ceiling(72) = 85(B)  ← unchanged
K4 hash=88 → ceiling(88) = 95(C)  ← unchanged
K5 hash=99 → ceiling(99) = 10(A)  ← unchanged
```

**Only K1 moved.** 1 of 5 keys = 20% relocation. With modular hashing on N=3 → N=4, ~75% of keys would move.

Now remove node B (B0=30, B1=85).

Sorted ring: `10(A) 20(D) 50(C) 60(D) 70(A) 95(C)`

K3 hash=72 was at 85(B); now ceiling(72) = 95(C). **K3 moves B → C.** Other keys unchanged. Total movement: only keys whose vnode owner disappeared.

## How to think aloud in the interview

"Right, sharding. The naive approach is `node = hash(key) % N`. Works until you scale — adding the Nth+1 node changes the modulus and shuffles roughly `N/(N+1)` of all keys. For a cache that's a complete eviction; for a database that's a full rebalance. Unacceptable.

Consistent hashing fixes this. You map both nodes and keys onto the same hash space — conventionally a 2^32 ring — using something like MurmurHash3. Each key is owned by the first node clockwise from it. The crucial property: adding a node only steals the arc between itself and its predecessor. About 1/N of the keys move, not N/(N+1). Removing a node moves only that node's arcs to the successor.

But raw consistent hashing has a load-balance problem. Three randomly-placed nodes on a circle won't split the circle into three equal thirds — by luck one might own half the keyspace. The fix is *virtual nodes*: instead of placing one mark per physical node, you hash 128 or 256 'virtual' positions per node. Now the law of large numbers gives you near-uniform load, and removing a node spreads its arcs across many successors rather than dumping them all on one.

For replication, you place a key on the next R *distinct* physical nodes clockwise — must dedupe by physical, not vnode, or you get two replicas on one box. Rack-awareness layers on top: skip same-rack vnodes.

In production, Cassandra, Dynamo, and Riak use this directly. Ketama, the memcached client variant, uses a slightly different distribution. The membership of the ring is gossipped — every node knows the full ring locally; lookups are O(log VN) tree lookups, no network hop.

The one anti-pattern: consistent hashing doesn't help with hot keys — a single overpopular key still lands on one node. For that you need request-level mirroring or explicit hot-key replication on top."

## Important takeaways
- **Modular hashing moves ~N/(N+1) of keys on scale; consistent hashing moves ~1/N.**
- **Vnodes are essential** for load balance; V=128 or 256 typical.
- **Replication walks vnodes but dedupes by physical node.**
- **Hash function quality matters:** MurmurHash3, MD5, FNV. Avoid Java `hashCode()`.
- **Hot keys are orthogonal** — consistent hashing solves cold imbalance, not hot keys.
- **Membership is gossipped or coordinated externally** (Dynamo: gossip; Riak: gossip; some systems: etcd).
- **Bounded-load consistent hashing** (Google) caps per-node load.
- **Rack-awareness / anti-affinity** for replica placement under physical failure.

## Variants
1. **Jump Consistent Hash (Lamping & Veach, 2014)** — O(1) memory, no ring stored; `jump_consistent_hash(key, N)`. Used by some sharded databases.
2. **Rendezvous Hashing (HRW)** — for each key, hash with every node, pick highest score. Same movement guarantees as consistent hashing; no ring. Cleaner code, slightly more compute per lookup.
3. **Maglev Hashing** (Google) — used by Maglev load balancer; lookup-table based, near-uniform, very fast.
4. **Bounded-load consistent hashing** — add a load constraint; overflow to next on full nodes.
5. **CRUSH (Ceph)** — hierarchical placement; takes datacentre/rack/host topology into account.
6. **Anchor Hashing** — newer, supports node-weighted distribution and minimal disruption on removal.
7. **Sharded hot-key** — duplicate a hot key as `key:0..key:N-1`, route by client-side hash. See `hot-key-mitigation.md`.

## Revision notes

> **Consistent hashing — 60 second recap**
> - Map nodes and keys onto a ring (hash space).
> - Key owned by first node clockwise.
> - Add/remove a node moves ~1/N of keys (not N/(N+1) as in modular).
> - **Vnodes** (V=128–256 per physical node) balance load.
> - **Replication** = next R *distinct physical* nodes clockwise.
> - Hot keys unsolved by consistent hashing.
> - Alternatives: Rendezvous hashing, Jump consistent hash, Maglev.
> - **Trap:** confusing consistent hashing with modular hashing; forgetting vnodes; not deduping replicas by physical node.
