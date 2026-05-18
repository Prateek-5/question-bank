# Causal consistency: the sweet spot between strong and eventual

## Source / Origin
- Lamport (1978) happens-before; Ahamad et al. (1995) Causal Memory.
- Production: COPS, Eiger, MongoDB causal sessions, AntidoteDB, Bayou.
- Concept reference: `backend-data-prep/distributed-systems/consistency.md`.

## Why this question matters in interviews
Causal consistency is the consistency model that gives you "no time travel inside a session" without paying for global coordination. If you can articulate when it's enough (social timelines, comments-on-posts) and when it's not (bank balances, inventory), and explain the implementation cost, you signal you understand the practical middle ground between linearizable and eventual.

## Concepts involved

### Syntax / mechanism to lock in

```
Causal consistency:
  If event A happens-before event B (a → b), then every replica must
  apply A before B.
  Concurrent events (a || b) can be applied in any order on each replica.

Happens-before:
  Same client/session: A before B in program order.
  Cross-client: B reads value written by A.
  Transitive closure of those.

Implementation:
  Each client tracks a "causal context" (vector clock or session token).
  Each write carries the context of all writes the client has seen.
  Each replica applies a write only when all causally prior writes are present.
  Reads from a replica include all writes that causally precede the read.

MongoDB causal sessions:
  startSession({ causalConsistency: true });
  // every read returns operationTime; client uses it to require
  // the next read sees that or later.
```

### Edge cases / interview traps

1. **Causal consistency is per-session.** Two different clients can see different orderings if no causal link between them.
2. **Convergent conflict resolution** still needed for concurrent writes — CRDT, LWW, or app merge.
3. **Causal+** consistency (COPS) adds convergent handling of concurrent writes.
4. **Reading from a stale replica** is allowed if it has all causally-prior writes.
5. **Cannot enforce invariants** that span concurrent updates (write skew possible).
6. **Metadata overhead.** Context vectors can grow per session; pruned by GC or sticky session.
7. **Comment-before-post problem**: classic example — if I post then comment, no replica should show the comment without the post.

## Mental Model

Causal consistency is like watching a TV show with friends across cities. You can have different friends pause at different scenes, but nobody sees scene 5 before scene 4. The order within a story arc is preserved; independent story arcs can be reordered.

```
Client C1:    write A (post)     ──→     write B (comment on A)
                  │                                │
                  └─────── causal edge ────────────┘

Client C2:                                          read B
                                            must also see A (B's causal parent)

Concurrent writes from C3 and C4 with no shared parent are unordered;
each replica is free to apply them in any order.

Diagram:
       A
       │
       ▼
       B          (X || Y are concurrent; either order ok)
                  X    Y
```

## Why interviewers care
- Tests nuanced understanding of consistency spectrum.
- Reveals knowledge of MongoDB causal sessions, COPS, Bayou.
- Senior signal: knows when full linearizability is overkill.

## Common beginner confusion
- "Causal = strong." It's weaker than linearizable but stronger than eventual.
- "Causal needs a global clock." No — vector clocks or session tokens suffice.
- "Causal handles concurrent writes." No — concurrent writes need additional merge logic (CRDT/LWW).
- "Causal prevents write skew." No — invariants across concurrent paths can still break.

## Brute force approach

Use eventual consistency and hope the client retries until it sees the write it just made. Bad UX, "I posted but my comment shows above my post".

## Optimal approach

Use a causal session token: every read returns the operation timestamp; every subsequent operation in the session attaches a "wait until you have applied >= this timestamp" hint. MongoDB calls this `operationTime` and `clusterTime`. Eiger uses dependency tracking on write metadata.

## Solution

### Quiz 1
> A user posts a tweet at 10:00, then comments on it at 10:01. Their friend opens their feed. What can/cannot happen under each consistency model?

- **Eventual**: friend may see the comment before the post arrives → bad UX.
- **Causal**: friend's session reads see post before (or with) comment. Good UX.
- **Linearizable**: same as causal here, plus real-time global order.

### Quiz 2
> Two clients write to a single key K:
> - Client A: K = "v1" at t=10
> - Client B: K = "v2" at t=11 (without reading K first)
>
> Are these concurrent? Does causal consistency order them?

Answer: They are concurrent (no causal edge: B didn't read v1 before writing v2). Causal consistency does not order them; replicas may converge to either v1 or v2 via LWW/CRDT/app merge.

### Quiz 3
> MongoDB session-based causal consistency: client reads from secondary at t=20. The secondary lags by 5 seconds. What does the client see?

Answer: With causal session enabled, MongoDB attaches the client's `operationTime` (latest known timestamp from this session). The secondary waits until its replication state >= that timestamp before responding. If the wait exceeds the timeout, the read fails — preserving causal consistency.

### Quiz 4
> Why doesn't causal consistency prevent write skew?

Answer: Write skew involves two concurrent transactions reading overlapping data and writing disjoint rows. Neither transaction has a causal edge to the other; both write in "parallel" causal branches. The combined invariant violation isn't caught.

### Quiz 5
> Cross-session causal: client A writes X=1; client B (no shared session) writes Y=2 after reading X. Are X and Y causally ordered?

Answer: Yes. B's read of X creates a causal edge A's-write-of-X → B's-read-of-X → B's-write-of-Y. Any replica observing Y must also observe X.

## Step-by-step dry run

Two-replica system, MongoDB-style causal session:

```
t=0   Client C1 connects to replica R1, starts causal session.

t=1   C1 writes Post P at R1. R1 returns operationTime=T1.
      C1 remembers context = {T1}.

t=2   R1 replicates P to R2 (async).

t=3   C1 writes Comment C (causally depends on P) at R1.
      R1 returns operationTime=T2 (T2 > T1).
      C1 context = {T2}.

t=4   C1 switches to R2 (or another client C2 attaches with shared
      session token). C2 reads with context={T2}.

      R2 has not yet received C from R1.
      R2 checks: do I have all writes <= T2? No (missing C).
      R2 waits or proxies to R1 until it has C.

      If R2 has both P and C → returns them.
      If R2 has P but not C → wait until C arrives.

t=5   Eventually R2 has both → returns post + comment in causal order.

Scenario without causal session (eventual):
      C2 reads from R2 at t=4 before C replicated.
      R2 returns "comment seen, post not seen". Bad UX.
```

## How to think aloud in the interview

> "Causal consistency guarantees that if A happens-before B, every replica applies A before B. Happens-before is the transitive closure of (same-session program order) and (one operation reads a value written by another).
>
> Concurrent operations — no shared causal edge — can be applied in any order on each replica. So causal consistency *alone* doesn't resolve concurrent writes; you need LWW or a CRDT on top. COPS calls this combination 'causal+'.
>
> Implementation: each session/client tracks a causal context (vector clock or operation timestamp). Reads carry this context; replicas wait or proxy until they have all causally-prior writes. MongoDB exposes this as `causalConsistency: true` on a session.
>
> Causal is the sweet spot for social feeds, collaborative apps, comments-on-posts. It's NOT enough for bank balances, inventory, or any cross-object invariant — those need stronger isolation."

## Important takeaways
- Causal = preserves happens-before across replicas; concurrent ops unordered.
- Stronger than eventual, weaker than sequential/linearizable.
- Needs causal context (vector clock or op timestamp) per session.
- Doesn't resolve concurrent writes; pair with CRDT or LWW.
- MongoDB causal sessions, COPS, Eiger, Bayou are production implementations.
- Doesn't prevent write skew.

## Variants
1. **Causal+** consistency — adds convergent conflict handling.
2. **Sequential consistency** — same total order seen by all; stronger.
3. **PRAM consistency** — per-process ordering only, weaker.
4. **Eventual** — no ordering guarantee.
5. **Bolt-on causal** — middleware adds causal layer over eventually consistent store.

## Revision notes

> **causal-consistency — 60 second recap**
> - happens-before preserved on every replica; concurrent ops unordered.
> - Carry per-session context (vector clock / op-time).
> - Doesn't resolve concurrent writes — pair with CRDT/LWW.
> - Sweet spot for social, collaborative, comment-on-post UX.
> - MongoDB `causalConsistency: true`; COPS, Eiger, Bayou.
> - Doesn't prevent write skew or enforce cross-object invariants.
