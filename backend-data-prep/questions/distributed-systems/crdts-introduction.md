# CRDTs: convergent data types that merge without coordination

## Source / Origin
- Shapiro et al., "Conflict-free Replicated Data Types" (INRIA, 2011).
- Production: Riak DT, Redis CRDTs (Enterprise), Automerge, Yjs, Figma, Akka Distributed Data.
- Concept reference: `backend-data-prep/distributed-systems/eventual-consistency.md`.

## Why this question matters in interviews
CRDTs are the answer to "how do you build a multi-master system where every replica accepts writes and they automatically reconcile?" If you can name G-Counter, PN-Counter, OR-Set, LWW-Register, and articulate the *commutativity-associativity-idempotence* requirement, you signal you've thought past eventual consistency into *strong* eventual consistency.

## Concepts involved

### Syntax / mechanism to lock in

Two flavours:

- **State-based (CvRDT)**: replicas exchange full state; merge is `join(s1, s2)` that is commutative, associative, idempotent.
- **Operation-based (CmRDT)**: replicas broadcast operations; delivery must be reliable and causally ordered; ops must commute.

```python
# G-Counter (grow-only): per-node counter, merge by elementwise max
state = {nodeA: 3, nodeB: 5, nodeC: 2}
value = sum(state.values())  # 10
merge(s1, s2) = {k: max(s1.get(k,0), s2.get(k,0)) for k in s1.keys()|s2.keys()}

# PN-Counter: two G-Counters (P for increments, N for decrements)
value = sum(P.values()) - sum(N.values())

# LWW-Register: (value, timestamp); merge picks higher timestamp
# OR-Set: each add tags element with unique id; remove only removes seen tags
```

### Edge cases / interview traps

1. **Merge must be CAI**: Commutative, Associative, Idempotent. Otherwise replicas diverge.
2. **LWW-Register loses data** on concurrent writes (one timestamp wins).
3. **2P-Set** allows remove-after-add but not re-add (tombstone forever).
4. **OR-Set** allows re-add because each add has a unique id.
5. **Causal delivery is required for op-based CRDTs** — otherwise an "add" might arrive after its "remove".
6. **State-based CRDTs gossip full state** — wasteful; delta-CRDTs send only the changed portion.
7. **CRDTs do not give linearizability** — they give *strong eventual consistency* (replicas converge when they have received the same set of updates).
8. **Counter underflow** in PN-Counter is allowed; if you need "non-negative", you need coordination.

## Mental Model

A CRDT is a data structure whose *shape* makes merge order irrelevant. Like adding to a set: `{a} ∪ {b} = {a,b}` regardless of order. Like elementwise-max on vectors: idempotent and associative.

```
    Replica A: state_A           Replica B: state_B
         \                          /
          \      gossip            /
           \                      /
            \                    /
             merge(state_A, state_B)
                      ↓
              same value at both replicas
              regardless of WHEN merge happened
              or how many times it happened
```

Compare to a normal counter: `a = a + 1` is not idempotent — replaying it doubles.

## Why interviewers care
- Tests whether you understand *strong eventual consistency*.
- Signals you can design for offline-first, multi-master, partition-tolerant systems.
- Bridges to real products: collaborative editors, shopping carts, distributed counters.

## Common beginner confusion
- "CRDTs solve the CAP theorem." No — they give AP with strong eventual consistency; you still cannot get linearizable writes without coordination.
- "Just use LWW." LWW silently loses concurrent writes. CRDTs let you choose data-structure-specific merge.
- "All operations are commutative if I retry enough." Not even close — counter increment is, but set-remove-then-add isn't unless you tag with unique ids.
- "CRDTs replace consensus." They sit alongside it; consensus for membership and config, CRDTs for data.

## Brute force approach

LWW everywhere with high-resolution timestamps. Works for write-rarely data. Silently corrupts on concurrent writes and reorders.

## Optimal approach

Pick the CRDT that matches your data semantics:

| Need | CRDT |
|------|------|
| Increment-only counter | G-Counter |
| Bidirectional counter | PN-Counter |
| Set with add only | G-Set |
| Set with add/remove (no re-add) | 2P-Set |
| Set with add/remove/re-add | OR-Set |
| Single value | LWW-Register or MV-Register |
| Map | OR-Map / Map of CRDTs |
| Text | RGA, Logoot, Yjs |

## Solution

```python
class GCounter:
    def __init__(self, node_id):
        self.node_id = node_id
        self.counts = {node_id: 0}

    def increment(self, n=1):
        self.counts[self.node_id] = self.counts.get(self.node_id, 0) + n

    def value(self):
        return sum(self.counts.values())

    def merge(self, other):
        all_keys = set(self.counts) | set(other.counts)
        self.counts = {k: max(self.counts.get(k, 0), other.counts.get(k, 0))
                       for k in all_keys}


class ORSet:
    """Observed-Remove Set: add tags with unique id; remove only removes seen ids."""
    def __init__(self):
        self.added = set()    # {(element, unique_id)}
        self.removed = set()  # {(element, unique_id)}

    def add(self, e):
        self.added.add((e, uuid4()))

    def remove(self, e):
        for tag in [t for t in self.added if t[0] == e]:
            self.removed.add(tag)

    def value(self):
        return {e for (e, _) in self.added - self.removed}

    def merge(self, other):
        self.added |= other.added
        self.removed |= other.removed
```

## Step-by-step dry run

Two-replica G-Counter, three increments:

```
Replica A counts={A:0}         Replica B counts={B:0}

A.increment(3) → {A:3}         B.increment(2) → {B:2}
A.increment(1) → {A:4}

         ── gossip A→B ──
B.merge(A): max per key:
  {A: max(0,4)=4, B: max(2,0)=2} = {A:4, B:2}
  value() = 6

         ── gossip B→A ──
A.merge(B): {A: max(4,4)=4, B: max(0,2)=2} = {A:4, B:2}
  value() = 6

         ── replay merge (idempotence test) ──
A.merge(B) again: same result. Replicas converged.
```

OR-Set "remove then concurrent add" case:

```
Replica A: add("x") with tag t1   → added={(x,t1)}
            sync → B
Replica A: remove("x")            → removed={(x,t1)}
Replica B: add("x") with tag t2 (concurrent) → added={(x,t1),(x,t2)}
            sync both ways
After merge:
  added    = {(x,t1), (x,t2)}
  removed  = {(x,t1)}
  value    = {(x,t2)} → "x" is in the set.
```

LWW-Register would have lost one of the operations; OR-Set preserves the intent "x was re-added".

## How to think aloud in the interview

> "CRDTs are data structures with a merge function that is commutative, associative, and idempotent. Because of those three properties, replicas converge to the same state regardless of message order, duplication, or replay — that's strong eventual consistency.
>
> Two flavours: state-based gossips full state and merges by join; op-based broadcasts operations that commute, requires causal delivery.
>
> The catalog covers most needs: G-Counter and PN-Counter for numeric, G/2P/OR-Set for sets, LWW or MV-Register for single values, OR-Map for maps, RGA/Yjs for text. Pick by semantics: do you need re-add? Then OR-Set. Decrement? PN-Counter.
>
> CRDTs do not replace consensus — they sit alongside it for data that doesn't need linearizability. Figma, Automerge, Yjs, Riak DT, Redis Enterprise are real production examples."

## Important takeaways
- CRDT merge must be commutative, associative, idempotent.
- State-based vs op-based; delta-CRDTs reduce bandwidth.
- G-Counter, PN-Counter, OR-Set, LWW-Register are the canonical building blocks.
- Gives strong eventual consistency, not linearizability.
- Real use: collaborative editors, distributed counters, offline-first apps.
- Cannot enforce invariants like "balance ≥ 0" without coordination.

## Variants
1. **Delta-CRDTs** — propagate only state changes, not full state.
2. **Pure op-based CRDTs** — embed metadata in ops to avoid causal broadcast cost.
3. **Computational CRDTs** — Bloom, Anna; allow arbitrary functions if monotonic.
4. **Hybrid systems** — Riak combines CRDTs with vector clocks and quorum.
5. **Text CRDTs**: RGA, Logoot, Treedoc, Yjs (Y-CRDT) — used in Yjs, Automerge, Figma.

## Revision notes

> **crdts — 60 second recap**
> - Merge is commutative, associative, idempotent → replicas converge.
> - State-based (full state, join) vs op-based (broadcast ops, must commute + causal).
> - Catalog: G-Counter, PN-Counter, G/2P/OR-Set, LWW/MV-Register, OR-Map, RGA.
> - Gives strong eventual consistency, not linearizability — no invariant enforcement.
> - Production: Riak DT, Redis Enterprise, Automerge, Yjs, Figma, Akka.
> - Delta-CRDTs cut gossip bandwidth.
