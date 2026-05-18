# Read repair: fixing replica divergence on the read path

## Source / Origin
- Amazon Dynamo paper (2007); standard in Cassandra, Riak, ScyllaDB.
- Concept reference: `backend-data-prep/distributed-systems/eventual-consistency.md`.

## Why this question matters in interviews
Read repair is the answer to "your hint TTL expired and a replica missed updates — how do you fix divergence without a background job?" If you can explain blocking vs async read repair, when it fires, and how it interacts with consistency level, you signal mid-to-senior knowledge of eventual-consistency machinery.

## Concepts involved

### Syntax / mechanism to lock in

```
Client read with R replicas (e.g., R=QUORUM):
  Coordinator queries all RF replicas (or up to R+extra).
  Compares responses (digest first, full data if mismatch).

  If responses disagree:
     Blocking read repair (consistency mode):
       Pick latest version (LWW by timestamp, or merge siblings for vector clocks).
       Write the merged value back to stale replicas synchronously.
       Return latest version to client after repair acks.

     Async read repair (background mode):
       Return latest to client immediately.
       Schedule background write to stale replicas.
       Configurable probability (e.g., dclocal_read_repair_chance=0.1).
```

### Edge cases / interview traps

1. **Read repair only fixes keys that are read.** Cold keys stay diverged → still need anti-entropy.
2. **LWW timestamps must be monotonic.** Clock skew across nodes can resurrect old data.
3. **With CRDTs**, merge is convergent — read repair writes the merged sibling.
4. **Blocking read repair adds tail latency.** Async is the usual default in Cassandra 4+.
5. **Read repair + R=ONE = useless** — only one response, nothing to compare.
6. **Read repair is per-partition.** It cannot fix referential integrity across keys.
7. **Repair direction.** Always toward the *latest* version, never the majority.

## Mental Model

A book club where members occasionally miss meetings. Every time the group meets to discuss a chapter (read), they compare their notes (replica versions). If anyone is behind, the up-to-date members hand over the latest chapter notes (write-back to stale replicas). Over time, members converge on the same chapters — even ones who missed multiple meetings.

```
Client read K → Coordinator
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
      N1=v3      N2=v2       N3=v3       ← N2 is stale

   Coordinator picks latest = v3 (ts=highest)
   Writes v3 back to N2  (blocking or async)
   Returns v3 to client

   Now N2 caught up. Next read sees all v3.
```

## Why interviewers care
- Tests understanding of how eventual consistency repairs itself.
- Reveals knowledge of Cassandra read path and consistency tuning.
- Distinguishes read-repair from anti-entropy (Merkle trees) — both needed.

## Common beginner confusion
- "Read repair makes the system strongly consistent." It doesn't — gives eventual consistency only for keys that are actually read.
- "Read repair is the same as anti-entropy." Different: read repair is on the read path; anti-entropy is a background Merkle-tree comparison.
- "It always blocks the response." Configurable — async is common to avoid tail latency.
- "It uses majority vote." It uses *latest* by timestamp/version vector, not majority.

## Brute force approach

Run a nightly job that compares every replica's full state and writes the latest everywhere. Works but slow, expensive, doesn't help fresh reads see fresh data.

## Optimal approach

Coordinator queries R replicas on read. Use digest queries (hash of value) first; on mismatch fetch full data. Pick latest, write back to stale replicas in background (or blocking if consistency demands it). Combine with periodic Merkle-tree anti-entropy for cold keys and hinted handoff for short outages.

## Solution

```python
class Coordinator:
    def __init__(self, ring):
        self.ring = ring

    def read(self, key, consistency=2):
        replicas = self.ring.preference_list(key, rf=3)
        # Step 1: digest query to all, fetch full from one
        responses = []
        for r in replicas:
            try:
                responses.append((r, rpc_call(r, "get_with_digest", key, timeout=100)))
            except Exception:
                pass
        if len(responses) < consistency:
            raise ReadFailure()

        # Step 2: detect mismatch
        digests = {resp.digest for _, resp in responses}
        if len(digests) == 1:
            return responses[0][1].value      # all agreed

        # Step 3: full read from all (mismatch path)
        full = [(r, rpc_call(r, "get", key)) for r, _ in responses]
        latest = max(full, key=lambda rv: rv[1].timestamp)

        # Step 4: repair
        stale = [(r, v) for r, v in full if v.timestamp < latest[1].timestamp]
        for r, _ in stale:
            self.async_write_back(r, key, latest[1])     # async or blocking

        return latest[1].value
```

## Step-by-step dry run

3-replica cluster, R=QUORUM=2, key K. N1=v3 (ts=10), N2=v2 (ts=5), N3=v3 (ts=10).

```
t=0   Client GET K with R=2.

t=1   Coordinator sends digest queries to N1, N2, N3.
        N1: digest=hash(v3)
        N2: digest=hash(v2)
        N3: digest=hash(v3)

t=2   Coordinator sees 2 distinct digests. Mismatch.

t=3   Full reads:
        N1: (v3, ts=10)
        N2: (v2, ts=5)
        N3: (v3, ts=10)
      Latest = (v3, ts=10).

t=4   Blocking repair: PUT to N2 (v3, ts=10). N2 acks.
      Async repair: schedule background write to N2.

t=5   Return v3 to client.

t=6   Next read of K: all three replicas have (v3, ts=10). Converged.

----------------------------------------------------------------------
Scenario: clock skew trap.

  N2 has v2 with ts=10 (clock 5s ahead) and N1 has v3 with ts=8.
  Latest by ts = v2 (incorrect causally).
  Read repair would overwrite v3 with v2 → DATA RESURRECTION.

  Fix: use HLC / monotonic logical clocks, or version vectors, or
  use Cassandra's "USING TIMESTAMP" application-supplied ts.
```

## How to think aloud in the interview

> "Read repair fixes replica divergence on the read path. The coordinator queries R replicas, often using digest queries first (hash of value, small). If digests mismatch, it fetches full data, picks the latest by timestamp or merges siblings via vector clocks, and writes the latest back to stale replicas. Blocking repair pays repair latency on the read; async repair schedules it after returning to the client.
>
> Read repair only fixes keys that are read. Cold keys can stay diverged for days, so you also need Merkle-tree anti-entropy as a background pass. And it relies on monotonic timestamps — clock skew or non-monotonic clients can resurrect old data, which is why production systems use HLC or app-provided timestamps.
>
> Read repair plus hinted handoff plus anti-entropy is the Dynamo triple: short outages caught by hints, fresh reads caught by repair, cold divergence caught by anti-entropy."

## Important takeaways
- Coordinator compares R responses; writes latest back to stale replicas.
- Digest query first (cheap), full read on mismatch.
- Blocking vs async; blocking adds tail latency.
- Only fixes keys that are actually read → pair with anti-entropy.
- Clock skew can resurrect old data — use HLC or app timestamps.
- Together with CRDT or vector clocks for sibling merge.

## Variants
1. **Blocking read repair** — coordinator waits for repair acks before responding.
2. **Async / probabilistic** — repair in background, configurable chance.
3. **Cross-DC read repair** — repair across data centres on consistency level EACH_QUORUM.
4. **Per-key TTL** — old tombstones complicate read repair; need GC grace period.
5. **Digest-only repair** — for very large values, compare digests but don't transmit full data unless necessary.

## Revision notes

> **read-repair — 60 second recap**
> - On read, coordinator compares R replica responses; writes latest to stale.
> - Digest first, full read on mismatch.
> - Blocking (tail latency) vs async (background).
> - Only fixes keys that are read → still need Merkle anti-entropy.
> - Clock skew can resurrect old data → use HLC / app timestamps.
> - Dynamo triple: hints + read repair + anti-entropy.
