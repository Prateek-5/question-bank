# Consistent Hashing for Cache Keys — Ring, Virtual Nodes, Minimal Rehash

## Source / Origin
- Karger et al., "Consistent Hashing and Random Trees" (1997). The paper that fixed the web-cache hot-key problem at Akamai before Akamai existed.
- Productionised in Amazon Dynamo (2007), Memcached client libraries (ketama, 2007), Cassandra, Riak.
- Companion doc: `backend-data-prep/caching/02-cache-cluster-topology.md`.
- Interview prompt: "You have 10 Memcached nodes. One dies. Why does naive `hash(key) % N` melt the world, and what do you replace it with?"

## Why this question matters in interviews
This is the **canonical distributed-cache question** at senior backend rounds. Any candidate can describe `hash(key) % N`. The senior is the one who immediately says "wait — when N changes, every key remaps and the cache effectively dies." The interviewer wants you to (a) explain why modulo hashing is fatal during scale-up or node loss, (b) draw the hash ring, (c) describe how virtual nodes fix load imbalance, and (d) quantify what fraction of keys move when one node leaves. Miss this and you're flagged as someone who's only worked with a single Redis box.

## Concepts involved

### Syntax to lock in

The naive (broken) version:
```
node_for(key) = nodes[ hash(key) % len(nodes) ]
# If len(nodes) changes from 10 to 9, virtually every key remaps.
```

The consistent-hashing version:
```
ring = sorted list of (hash, node) tuples, one per virtual node
node_for(key):
    h = hash(key)
    idx = bisect_right(ring_hashes, h) % len(ring)
    return ring[idx].node
```

With `V` virtual nodes per physical node and `N` physical nodes, you get `N*V` points on a `2^32`-sized integer ring. A key picks the first point clockwise from its hash.

### Edge cases / interview traps

1. **Modulo hashing's failure mode.** With `hash(key) % N`, changing `N` from 10 to 11 remaps roughly `(N-1)/N = 90%` of keys. The cache hit rate collapses; the DB sees the full miss rate; cascade failure. **This is the entire reason consistent hashing exists.**
2. **Virtual nodes are mandatory, not optional.** With one point per node, load skew is severe — some nodes own 5x what others own. With ~150-200 virtual nodes per physical node, the standard deviation of load drops to a few percent.
3. **Hash function choice.** Use a non-cryptographic, well-distributed hash: MurmurHash3, xxHash, CityHash. `Math.random()`-style "looks random" is not good enough. Java's `String.hashCode` is genuinely bad here (poor distribution on short keys).
4. **Ketama vs jump hash.** Ketama (Memcached) uses the ring. Jump hash (Lamping & Veach, 2014) skips the ring entirely — `O(ln N)` math, two integers of memory, perfect balance — but only supports append-style scale-out (nodes 0..N-1), not arbitrary add/remove. Know both.
5. **Heterogeneous nodes.** If node A has 2x the RAM of node B, give A 2x the virtual nodes. Load follows vnode count.
6. **Bounded loads.** Vanilla consistent hashing still has tail skew. "Consistent hashing with bounded loads" (Mirrokni, Thorup, Zadimoghaddam 2017, used by Google Vimeo & Vimeo CDN) caps each node at `(1+ε) * avg_load` and walks the ring if full.
7. **Add vs remove.** Adding a node moves `K/N` keys (only from neighbours). Removing a node forces its neighbours to absorb its keys — the remaining nodes see a load spike. Plan headroom for this, not just average.
8. **Rebalancing during scale.** When you add a node, you're not migrating keys — the cache simply re-misses on those keys at the new node and refills from DB. Quantify the DB hit storm and pre-warm if needed.
9. **Replication interplay.** "Store on the next K nodes clockwise" is how Dynamo gets replicas for free. With vnodes you must be careful — the next vnode might belong to the *same physical node*. Skip until K distinct physical nodes.
10. **Client-side vs server-side ring.** Memcached: clients hold the ring, no coordination. Cassandra: gossip distributes the ring; nodes route. Trade-off: client-side is dead simple but every client needs the topology; server-side allows opaque add/remove.

## Mental Model

Picture a clock face numbered `0` to `2^32 - 1`. Place each node at multiple positions on the dial (its virtual nodes). To find which node owns a key, hash the key to a point on the dial and walk clockwise until you hit the first node marker. That's the owner.

```
                     0 / 2^32
                        │
              N3 ●──────┼──────● N1
              ╱         │         ╲
         N2 ●           │           ● N2
            │      key X─►          │
         N1 ●           │           ● N3
              ╲         │         ╱
              N2 ●──────┼──────● N1
                        │
                  Walk clockwise from key X →
                  First marker hit: N3
                  → key X belongs to node N3
```

When node N3 dies, only the arc *between N2's last point and N3's first point* needs to remap — and those keys go to whichever node is next clockwise. The arcs owned by N1 and N2 are untouched. That's the key insight: **a node removal only disturbs its successor arcs, not the whole space.**

### Why virtual nodes matter

```
Without vnodes (3 physical nodes, 3 points):
     N1 ●──────────────────● N2
        ╲                  ╱
         ╲     huge arc   ╱        ← N3 owns nearly half the ring
          ●─────────────●
                N3

Load: N1=20%, N2=25%, N3=55%.  Unacceptable skew.

With vnodes (3 physical × 150 = 450 points, distributed):
The arc sizes converge to roughly equal by the law of large numbers.
Std deviation of load drops from ~30% to ~3%.
```

The vnode count `V` is the knob: `V≈150` is the Memcached/Cassandra default. Higher `V` = smoother load but bigger ring (more memory, slower bisect). `V=1` (no vnodes) is the strawman that always loses.

## Why interviewers care

- Real systems use this: Memcached client libs (ketama), Cassandra, DynamoDB internals, Riak, Discord's chat backend.
- It separates "I've configured a Redis instance" from "I've reasoned about a cache cluster."
- The follow-ups are unbounded: replication, rebalancing storms, bounded loads, heterogeneous nodes, jump hash. Each is a senior-level depth probe.
- It's where caching meets distributed-systems math — interviewer can pivot to quorums, gossip, partitioning.

## Common beginner confusion

- **"Consistent hashing solves uneven load."** Only with virtual nodes. Vanilla ring is *worse* than modulo for load distribution.
- **"Modulo hashing is fine if I rarely add nodes."** It's also fatal when a node *dies* — which happens unprompted.
- **"More virtual nodes is always better."** More vnodes = better balance but bigger ring memory + slower lookups. 150-200 is the sweet spot.
- **"Consistent hashing keeps keys on the same node forever."** No — when the ring changes, some keys remap. The guarantee is *minimal* remap (`K/N`), not *zero*.
- **"Adding a node distributes load uniformly."** Adding one node `N+1` to `N` nodes shifts roughly `K/(N+1)` keys from the existing nodes to the new one. Not perfectly uniform across all, but bounded.
- **"I can use SHA-256."** You can; it's slower than necessary. Murmur/xxHash is 5-10x faster and good enough — these are hashes for distribution, not security.

## Brute force approach

`shard = hash(key) % N`. Works perfectly until `N` changes. Then:

```
N=10:  hash("user:42") % 10 = 2 → node[2]
N=11:  hash("user:42") % 11 = 9 → node[9]    (different!)
```

Probability any given key still maps to the same node when going from `N` to `N+1`: roughly `1/N`. So `(N-1)/N` of keys remap. With a 1B-key cache, that's ~900M cache misses arriving at the DB in a few seconds. **System-killing.**

## Optimal approach

### Consistent hashing (Karger 1997)

1. Pick a hash function with output space `[0, 2^32)`.
2. For each physical node, generate `V` deterministic virtual-node hashes (e.g., `hash("node3#0")`, `hash("node3#1")`, ...).
3. Insert all `N * V` points into a sorted list (`ring`).
4. To route key `k`: `h = hash(k)`; binary search the ring for the first point `≥ h`; that point's owner is the destination. If past the end, wrap to `ring[0]`.

Add node: insert its `V` points, rebalance the new arcs (move keys from successors to new node).
Remove node: delete its `V` points; its arcs collapse into the predecessor's territory.

Keys moved per node change: `K / N`. **That's the headline guarantee.**

### Jump consistent hash (Lamping–Veach 2014)

When your node set is a contiguous integer range and you only ever add at the high end, this is strictly better:

```
int JumpHash(uint64_t key, int num_buckets):
    int b = -1, j = 0
    while j < num_buckets:
        b = j
        key = key * 2862933555777941757ULL + 1
        j = (b + 1) * (1 << 31) / ((key >> 33) + 1)
    return b
```

`O(ln N)` time, two ints of memory, statistically perfect balance, zero ring data structure. Used in Google Vimeo, RocksDB sharding. Limitation: cannot remove an arbitrary bucket; only the highest.

### Consistent hashing with bounded loads

Cap each node at `(1+ε) * average_load`. When a key would route to a full node, walk the ring until you find a non-full one. Guarantees worst-case load skew of `(1+ε)` with `ε` typically 0.1.

## Solution (Python-flavoured pseudo-code)

```python
import bisect
import hashlib

class ConsistentHashRing:
    def __init__(self, nodes=None, vnodes_per_node=150):
        self.vnodes_per_node = vnodes_per_node
        self.ring = []                 # sorted list of (hash, node)
        self.hashes = []               # parallel list of hashes for bisect
        for n in (nodes or []):
            self.add_node(n)

    @staticmethod
    def _hash(s):
        # MurmurHash3 in prod; SHA1 here for portability
        return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)

    def add_node(self, node):
        for i in range(self.vnodes_per_node):
            h = self._hash(f"{node}#{i}")
            bisect.insort(self.ring, (h, node))
        self.hashes = [h for h, _ in self.ring]

    def remove_node(self, node):
        self.ring = [(h, n) for h, n in self.ring if n != node]
        self.hashes = [h for h, _ in self.ring]

    def node_for(self, key):
        if not self.ring:
            raise RuntimeError("empty ring")
        h = self._hash(key)
        idx = bisect.bisect_right(self.hashes, h) % len(self.ring)
        return self.ring[idx][1]

    def replicas_for(self, key, k):
        """First k *distinct* physical nodes clockwise."""
        seen, out = set(), []
        h = self._hash(key)
        start = bisect.bisect_right(self.hashes, h) % len(self.ring)
        for offset in range(len(self.ring)):
            node = self.ring[(start + offset) % len(self.ring)][1]
            if node not in seen:
                seen.add(node)
                out.append(node)
                if len(out) == k:
                    break
        return out
```

## Step-by-step dry run

Setup: 4 nodes (`A, B, C, D`), 2 virtual nodes each, 16-bit ring for illustration.

Hash assignments (made up for clarity):
```
A#0 → 100        A#1 → 40000
B#0 → 8000       B#1 → 50000
C#0 → 20000      C#1 → 55000
D#0 → 30000      D#1 → 60000

Sorted ring:
  100   (A)   ─┐
  8000  (B)    │
  20000 (C)    │
  30000 (D)    │   key X hashes to 25000
  40000 (A)    │   walk clockwise → first ≥ 25000 is D@30000
  50000 (B)    │   → owner = D
  55000 (C)    │
  60000 (D)   ─┘
                wrap: > 60000 → A@100
```

Now: **node D dies.** Points at 30000 and 60000 vanish.

```
New ring:
  100   (A)
  8000  (B)
  20000 (C)
  40000 (A)         ← was D@30000 → keys 20001..40000 now go here
  50000 (B)
  55000 (C)
   (wrap)           ← was D@60000 → keys 55001..100 now go to A

Keys that moved:
  - key X (hash 25000): was D, now A (next clockwise after C@20000 is A@40000)
  - all keys in arcs 20001-30000 and 40001-60000 remap

Keys that did NOT move:
  - hash 5000 → still B
  - hash 45000 → still B
  - hash 15000 → still C

Fraction moved: roughly 1/4 of keys (D's arc share). Other 3/4 untouched.
```

Compare with `hash % 4 → hash % 3`: nearly every key remaps. **The 1/N vs (N-1)/N difference is the entire point.**

## How to think aloud in the interview

> "OK, the question is how to route keys across a cache cluster such that adding or removing a node doesn't invalidate the entire cache. The naive approach is `hash(key) % N`. The problem: when `N` changes — even from 10 to 11 — about `(N-1)/N` of keys remap to a new node. For a 10-node cluster, that's 90% cache miss storm. The DB melts.
>
> Consistent hashing fixes this. Hash all nodes onto a fixed-size ring (say `2^32`). Hash each key onto the same ring. The owner is the first node clockwise from the key. When a node leaves, only its arc remaps; the rest is untouched. The fraction of keys that move is `1/N`, not `(N-1)/N`. That's the headline win.
>
> Naive consistent hashing has uneven load — some nodes own much larger arcs than others. The fix is virtual nodes: each physical node owns ~150 random points on the ring. Law of large numbers smooths the arc-size distribution; load std-dev drops from ~30% to a few percent.
>
> A few production refinements:
> - **Bounded loads**: cap each node at `(1+ε)` average; walk the ring if a node is full.
> - **Heterogeneous nodes**: give a 2x-larger node 2x the vnodes.
> - **Replication**: for K replicas, take the next K *distinct physical* nodes clockwise — important because two adjacent vnodes might be the same physical node.
> - **Jump hash**: if your topology is append-only (`nodes 0..N-1`), Lamping–Veach is strictly better — O(ln N) lookup, no ring data structure.
>
> Big trap to mention: removing a node *increases* load on its neighbours; plan headroom. And re-warming the cache during scale events is a real concern — pre-warm hot keys."

## Important takeaways

- **Modulo hashing dies when N changes.** Consistent hashing is the correction.
- **Ring + first-clockwise-node** is the core algorithm.
- **Virtual nodes (~150 per physical node) are mandatory** for even load distribution.
- **Keys moved when topology changes: `K/N`** — the headline guarantee.
- **Replicas = next K distinct physical nodes clockwise** (skip same-physical-node duplicates).
- **Bounded-load variant** caps the worst-case skew at `(1+ε)`.
- **Jump hash** is the better option if topology is append-only.
- **Heterogeneous nodes** scaled by vnode count, not by hashing magic.
- **Adding a node** does *not* trigger key migration; it triggers cache misses + refills. Pre-warm hot keys before scale-up.

## Variants

1. **Memcached + ketama** — canonical consistent-hashing client. Each app process holds the ring; nodes are oblivious. Used at Facebook for >15 years.
2. **DynamoDB / Cassandra style** — server-side ring with gossip propagation; clients don't need topology. Tradeoff: extra hop.
3. **Jump hash** — append-only topologies; no ring; mathematically optimal. Used in some Google internal systems.
4. **Maglev hash (Google 2016)** — fixed-size lookup table built from preferences; constant lookup, even better balance than ketama, slightly more memory.
5. **Rendezvous hashing (HRW)** — for each key, compute `hash(key, node)` for every node; pick max. No ring; perfect balance; O(N) per lookup — fine for small N.
6. **Consistent hashing with bounded loads** — caps worst-case skew at `(1+ε)`. Recommended for production load balancers (e.g., Envoy supports it).
7. **MySQL/Redis sharding** — sometimes people use consistent hashing for *DB* shards too. Caution: rebalancing a DB shard is much more expensive than rebalancing a cache (you move data, not just cause cache misses).

## Revision notes

> **consistent hashing — 60 second recap**
> - **Problem:** `hash % N` remaps `(N-1)/N` of keys when N changes; cache dies.
> - **Fix:** ring of `2^32`; each node placed at multiple points; key goes to first node clockwise.
> - **Vnodes (~150/node)** smooth load distribution.
> - **Topology change moves `K/N` keys.** That's the guarantee.
> - **Replicas:** next K *distinct physical* nodes clockwise.
> - **Bounded loads** caps worst-case skew at `(1+ε)`.
> - **Jump hash** if topology is append-only.
> - **Trap:** vanilla ring without vnodes — terrible load skew.
> - **Trap:** thinking "add node" migrates data; it doesn't, it causes misses. Pre-warm.
