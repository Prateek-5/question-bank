# Vector clocks: detecting concurrent updates across replicas

## Source / Origin
- Fidge (1988) and Mattern (1989) — generalisation of Lamport timestamps.
- Production reference: Amazon Dynamo paper (2007), Riak, Voldemort.
- Concept reference: `backend-data-prep/distributed-systems/causality.md`.

## Why this question matters in interviews
Vector clocks are the canonical answer to "how do you detect concurrent writes without a global clock?" in any senior backend round touching replication, eventual consistency, or merge conflicts. If you can draw a 3-node clock progression, explain why `[1,0,0]` and `[0,1,0]` are *concurrent*, and recognise that Dynamo uses them for sibling detection, you signal you actually understand causality vs wall time.

## Concepts involved

### Syntax / mechanism to lock in

```
Each node N maintains VC[N] = [c1, c2, ..., cN] of counters per node.

On local event at node i:
  VC[i] += 1 at position i

On send from i to j:
  VC[i] += 1 at i; piggyback VC on the message

On receive at j from i with vc_in:
  VC[j] = elementwise_max(VC[j], vc_in)
  VC[j] += 1 at position j

Comparison of two vectors A, B:
  A < B    iff A[k] <= B[k] for all k AND A != B    (A happened-before B)
  A || B   iff neither A < B nor B < A              (concurrent)
```

### Edge cases / interview traps

1. **Concurrent != equal.** `[1,0,0]` and `[0,1,0]` are concurrent, not equal.
2. **Vector grows with cluster size.** Naive vector clocks are O(N) per write — Dynamo's "version vector pruning" trims old entries.
3. **Client IDs vs server IDs.** Dynamo originally used coordinator (server) IDs; Riak switched to *client* IDs to avoid sibling explosion when many coordinators write.
4. **Not the same as Lamport.** Lamport gives total order but loses concurrency info. Vector clocks preserve it.
5. **Vector clocks don't resolve conflicts** — they only *detect* them. App or LWW must merge siblings.
6. **Dotted version vectors** (Riak 2.0+) fix the false-concurrent bug where a client reads an old version and writes back, creating a false sibling.

## Mental Model

Think of each node keeping a **gossip-style scorecard** of "how many events I have seen from every other node, including myself". When two nodes' scorecards aren't comparable (neither dominates the other), the writes happened independently — that's concurrency.

```
Node A: [Ka, Kb, Kc]   ← A's count, A's view of B, A's view of C

A writes:   [1, 0, 0]
B writes:   [0, 1, 0]
            ↑ neither dominates — CONCURRENT (siblings)

A → B msg:  B updates to [1, 2, 0]   (max + own++)
            ↑ now dominates the original [0,1,0] — happened-after
```

## Why interviewers care
- Tests whether you can reason about causality without a global clock.
- Bridge to Dynamo, Riak, version vectors, CRDTs, "last-write-wins is wrong".
- Reveals whether you understand *partial order* vs total order.

## Common beginner confusion
- "Vector clocks order events." They define a *partial* order. Many pairs are unordered (concurrent).
- "Bigger vector wins." No — that's LWW, which loses data. Concurrent vectors mean both writes survive as siblings.
- "Wall clocks are good enough." Not across machines with skew; NTP drifts by tens of ms.
- "Lamport timestamps are enough." Lamport gives total order but you cannot tell if A `→` B or A `||` B.

## Brute force approach

Use wall-clock timestamps; resolve conflicts with last-write-wins. Cheap, simple, silently corrupts on clock skew or concurrent updates from different clients. Don't.

## Optimal approach

Maintain a vector clock per replica. Piggyback the vector on every replicated write. On read, compare client-supplied context vector with stored vector; if incomparable, return siblings to the client.

## Solution

```python
class VectorClock:
    def __init__(self, node_id, n_nodes):
        self.node_id = node_id
        self.vc = [0] * n_nodes

    def local_event(self):
        self.vc[self.node_id] += 1

    def send_event(self):
        self.vc[self.node_id] += 1
        return list(self.vc)  # piggyback

    def receive_event(self, incoming_vc):
        self.vc = [max(a, b) for a, b in zip(self.vc, incoming_vc)]
        self.vc[self.node_id] += 1

    @staticmethod
    def compare(a, b):
        less = any(x < y for x, y in zip(a, b)) and all(x <= y for x, y in zip(a, b))
        greater = any(x > y for x, y in zip(a, b)) and all(x >= y for x, y in zip(a, b))
        if less:    return "a_before_b"
        if greater: return "a_after_b"
        if a == b:  return "equal"
        return "concurrent"
```

Dynamo-style write with siblings:

```python
def put(key, value, context_vc):
    stored = store.get(key)  # list of (vc, value) siblings
    new_vc = merge_increment(context_vc, my_node_id)
    survivors = [(vc, val) for (vc, val) in stored
                 if compare(vc, new_vc) != "a_before_b"]
    survivors.append((new_vc, value))
    store.put(key, survivors)
```

## Step-by-step dry run

Three-node cluster {A, B, C}. Client writes "cart=[milk]" via A, then "cart=[milk,eggs]" via A again, then concurrently a different client writes "cart=[bread]" via B.

```
Time   Node A             Node B             Node C
       VC=[0,0,0]         VC=[0,0,0]         VC=[0,0,0]

t1     write milk
       VC=[1,0,0]
       value: {milk}

t2     replicate → B,C    receive [1,0,0]    receive [1,0,0]
                          VC=[1,1,0]         VC=[1,0,1]
                          value: {milk}      value: {milk}

t3     write milk,eggs
       VC=[2,0,0] (no — actually [2,1,0] if A merged B's prior; let's keep clean)
       VC=[2,0,0]         (concurrent client at B writes bread)
       value: {milk,eggs}  VC=[1,2,0]
                          value: {bread}

t4     A and B gossip; both see incoming vectors.
       A receives [1,2,0]; compare to [2,0,0]:
         pos0: 2 vs 1   (A greater)
         pos1: 0 vs 2   (A lesser)
         → CONCURRENT.   A stores both as siblings.

       Sibling set at A:
         ([2,0,0], {milk,eggs})
         ([1,2,0], {bread})

t5     read from A returns BOTH siblings + context vector.
       Client merges semantically: {milk, eggs, bread}.
       Client writes back with merged context → VC becomes
       elementwise_max([2,0,0],[1,2,0]) + A++ = [3,2,0].
       This new write dominates both previous; siblings collapse.
```

## How to think aloud in the interview

> "Vector clocks track, per replica, a counter for every node. On local event, increment own slot. On message receive, elementwise-max the incoming vector and bump own slot. Comparison gives a *partial* order: A < B if every slot ≤ and at least one strict; otherwise concurrent.
>
> The key insight: concurrent isn't a bug, it's information. The system detects 'these two writes were independent' and returns siblings instead of silently dropping one via LWW.
>
> Dynamo and Riak use this. The drawback is the vector grows with cluster size; you prune oldest entries or switch to dotted version vectors to avoid the read-modify-write false-sibling bug.
>
> The choice point is whether your app can merge siblings (carts: union; counters: sum). If not, you fall back to LWW with the trade-off that concurrent writes lose data."

## Important takeaways
- Vector clock = per-node counter array; compares as partial order.
- Concurrent = neither dominates; that's a real signal, not a flaw.
- Used by Dynamo and Riak for sibling detection on writes.
- App or convergent data type (CRDT) must merge siblings.
- Size grows with cluster; prune or use dotted version vectors.
- Wall clocks and Lamport timestamps cannot detect concurrency.

## Variants
1. **Lamport timestamp** — single integer, total order, no concurrency info.
2. **Dotted version vectors** — fix false siblings from client read-modify-write.
3. **Hybrid logical clocks** (HLC) — combine wall time with logical counter; CockroachDB uses these.
4. **Interval Tree Clocks** — fork/join clocks for dynamic membership.
5. **CRDTs** — convergent data types that make sibling merge automatic.
6. **Bloom-clocks** — probabilistic, smaller, used in Cassandra-like systems.

## Revision notes

> **vector-clocks — 60 second recap**
> - Per-node counter array; piggyback on messages; elementwise-max on receive.
> - Comparison is partial: `<`, `>`, equal, or **concurrent**.
> - Concurrent = neither dominates → real independent writes → keep as siblings.
> - Dynamo/Riak use these for sibling detection; app merges semantically.
> - Lamport timestamps lose concurrency info; HLC and DVV are practical evolutions.
> - Pruning needed because vector grows with cluster size.
