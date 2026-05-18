# Hinted handoff: keeping writes alive when a replica is down

## Source / Origin
- Amazon Dynamo paper (2007), Cassandra and Riak adopted it.
- Concept reference: `backend-data-prep/distributed-systems/availability-techniques.md`.

## Why this question matters in interviews
Hinted handoff is the canonical answer to "what does Cassandra do when one of the W replicas is down — does the write fail?" If you can explain that a coordinator stores a *hint* on a healthy node and replays it when the target recovers, you signal you understand availability under partial failure.

## Concepts involved

### Syntax / mechanism to lock in

```
Client writes key K with replication factor RF=3, consistency W=QUORUM=2.
Preference list for K: [N1, N2, N3].

Normal:    coordinator writes K to N1, N2, N3 in parallel; acks when ≥W ack.

Failure:   N3 is down. Coordinator writes to N1, N2 (W=2 satisfied, ack client).
           Coordinator (or a peer) stores a HINT on, say, N4:
              hint = {target: N3, key: K, value: V, timestamp: T, ttl}
           When N3 comes back, N4 streams hints to N3, then deletes them.

Tunable:   write_consistency = ONE / QUORUM / ALL
           hint TTL (e.g., 3 hours in Cassandra default)
           max hint size per node
```

### Edge cases / interview traps

1. **Hints are not durable across coordinator failure** unless persisted (Cassandra writes them to a hint table on disk).
2. **Hint TTL is critical.** If N3 stays down longer than TTL, hints are discarded → divergence — anti-entropy/read-repair must catch up.
3. **Hint storms.** If many nodes go down, the surviving nodes can be overwhelmed by hint backlogs. Cassandra has back-pressure and per-target throttling.
4. **Hints + consistency ALL.** If you write with W=ALL, hinted handoff doesn't help — you need all replicas reachable.
5. **Hinted handoff is not enough for full consistency.** Always pair with read-repair and anti-entropy (Merkle trees).
6. **The coordinator may itself be on the preference list.** When the coordinator stores a hint for itself (rare), it's just a local write.
7. **Hints are per-target, not per-key.** They batch up; replay is in target-grouped streams.

## Mental Model

A package courier analogy. The courier (coordinator) has a package for house N3. N3's gate is locked (down). The courier leaves the package with the neighbour N4 along with a note "deliver this to N3 when they're home". When N3 returns, N4 hands it over. If N3 stays away too long, N4 throws the package out (TTL expired) — anti-entropy later reconciles.

```
Client → Coordinator (N1)
            ├──► N1 (self)        ✓ ack
            ├──► N2               ✓ ack       ⇒ W=2 satisfied, ack client
            └──► N3 DOWN          ✗
                 │
                 └─ HINT created at N4:
                    {target=N3, key, value, ts, ttl=3h}

Later: N3 boots up.
N4 streams hints → N3 → success → N4 deletes hint.

If TTL expires before N3 is back:
   Hint is dropped.
   Read-repair (on next read) or anti-entropy (Merkle compare)
   eventually brings N3 back to consistency.
```

## Why interviewers care
- Shows you understand availability under partial failure.
- Tests knowledge of Cassandra/Dynamo write path.
- Bridges to read-repair and anti-entropy: hints alone aren't sufficient.

## Common beginner confusion
- "Hints make the system strongly consistent." No — hints + read-repair + anti-entropy give eventual consistency.
- "Hints are stored at the target node." No, they're stored at a *peer* until target recovers.
- "Hinted handoff means write to W-1 replicas is OK." Only if you configured W < RF; otherwise write fails.
- "Hints replace anti-entropy." Hints handle short outages; anti-entropy handles long-term divergence.

## Brute force approach

Fail the write if any preference-list replica is down. Available only when every replica is up — single failure kills availability. Don't.

## Optimal approach

Coordinator writes to reachable replicas, satisfies W, acks client. For each unreachable replica, store a hint on a healthy peer (often the coordinator itself). On recovery, replay hints. Combine with read-repair (on every read, check replicas and fix mismatches) and periodic Merkle-tree anti-entropy.

## Solution

```python
class Coordinator:
    def __init__(self, ring, hint_store):
        self.ring = ring
        self.hint_store = hint_store

    def write(self, key, value, consistency=2):
        replicas = self.ring.preference_list(key, rf=3)
        acks = 0
        hints = []
        for r in replicas:
            try:
                rpc_call(r, "put", key, value, ts=time.time(), timeout=200)
                acks += 1
            except (Timeout, NodeDown):
                hints.append(r)
        if acks < consistency:
            raise WriteFailure(f"only {acks} acks, need {consistency}")
        for target in hints:
            self.hint_store.add(target, key, value, ttl=10800)
        return "OK"


class HintStore:
    """Persistent local store of pending hints for offline peers."""
    def add(self, target, key, value, ttl):
        self.db.insert(target, key, value, time.time(), ttl)

    def replay_when_up(self, target):
        for hint in self.db.iter(target):
            try:
                rpc_call(target, "put", hint.key, hint.value, ts=hint.ts)
                self.db.delete(hint.id)
            except Exception:
                return  # try again next cycle

    def expire(self):
        self.db.delete_where("now - ts > ttl")
```

## Step-by-step dry run

Cluster {N1, N2, N3, N4}; RF=3, W=QUORUM=2. Key K maps to preference list [N1, N2, N3].

```
t=0   Client → N1 (coordinator) PUT K=v1
        N1 fans out:
          local write: ✓
          → N2: ✓
          → N3: TIMEOUT (down)
        acks = 2 ≥ W. Return OK to client.
        N1 stores hint: {target=N3, key=K, value=v1, ts=0, ttl=3h}
        (stored locally on N1's hint table)

t=1   Client → N1 PUT K=v2
        N1: ✓; N2: ✓; N3: still down → hint #2 created.

t=2   Client → N2 reads K with R=QUORUM=2
        N2 → N1: returns v2 (ts=1)
        N2 → N3: down
        N2 has v2 already → returns v2 to client.

t=3   N3 recovers.
        N1 detects N3 is back (gossip).
        N1 streams hints in timestamp order:
          PUT K=v1 (ts=0)   → N3 applies   (LWW skipped if already newer)
          PUT K=v2 (ts=1)   → N3 applies, K=v2.
        N1 deletes both hints.

t=4   If N3 had been down for >3h, hints would have been dropped.
        Next read of K with R=2 from N3 finds N3 has stale data → read-repair
        triggers, fixes N3 in-flight. Anti-entropy with Merkle trees would catch
        any keys never read.
```

## How to think aloud in the interview

> "Hinted handoff is Dynamo's trick to preserve availability when some replicas are down. Coordinator writes to the reachable replicas in the preference list, satisfies the W requirement, acks the client. For each unreachable replica, it parks a hint on a healthy peer — usually itself — recording target node, key, value, timestamp, TTL.
>
> When the target recovers, the hint store streams pending writes to it, then deletes them. If the target stays down past TTL — Cassandra defaults 3h — hints are dropped and we rely on read-repair and Merkle-tree anti-entropy.
>
> Hints are not a consistency primitive on their own. They're a *latency* primitive for short outages. Pair with read-repair (catch divergence on read) and anti-entropy (catch divergence in background). All three together give us eventual consistency with high availability under partial failures."

## Important takeaways
- Hint = "deliver this later" packet held on a peer when target is down.
- Coordinator-managed; persistent across coordinator restart (Cassandra).
- TTL bounds memory/disk; after TTL, rely on read-repair + anti-entropy.
- Combines with W < RF to keep writes available during failures.
- Watch for hint storms; throttle replay.

## Variants
1. **Sloppy quorum** — write to *any* W nodes, not necessarily preference list; then handoff to correct replicas.
2. **Strict quorum** — require W from the actual preference list; less available, simpler reasoning.
3. **DynamoDB-style** — managed service hides hints, exposes only "eventually consistent" semantics.
4. **Cross-DC handoff** — hints can be held in another DC's coordinator for geo-redundancy.
5. **Hint indexing** — by target node for efficient replay; by key for read-repair lookup.

## Revision notes

> **hinted-handoff — 60 second recap**
> - Replica down → coordinator parks a HINT on a peer.
> - On recovery → peer streams hints to target → deletes them.
> - TTL bounds memory; past TTL rely on read-repair + Merkle anti-entropy.
> - Pairs with sloppy quorum to keep writes available during partial failures.
> - Hints do NOT replace anti-entropy; they speed up the common short-outage case.
> - Cassandra, Dynamo, Riak: same primitive, slight variants.
