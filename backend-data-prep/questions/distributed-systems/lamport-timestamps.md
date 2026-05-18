# Lamport timestamps: a total order from a single counter

## Source / Origin
- Lamport (1978) "Time, Clocks, and the Ordering of Events in a Distributed System."
- Production: Cassandra LWW, Kafka offsets, many event sourcing systems.
- Concept reference: `backend-data-prep/distributed-systems/time.md`.

## Why this question matters in interviews
Lamport timestamps are the foundational concept of logical time. If you can explain the update rule, demonstrate that the resulting order respects happens-before, and articulate the limitation (cannot detect concurrency), you signal you understand the smallest-possible-clock for ordering distributed events.

## Concepts involved

### Syntax / mechanism to lock in

```
Each process maintains a single integer counter L.

Rules:
  Local event:      L = L + 1
  Send event:       L = L + 1; piggyback L on the message.
  Receive event:    L = max(L, L_msg) + 1

Total order:
  Compare (L, process_id) lexicographically:
     event A < event B iff L_A < L_B OR (L_A == L_B AND pid_A < pid_B)

Properties:
  If a → b (happens-before), then L(a) < L(b).
  Converse NOT true: L(a) < L(b) does NOT imply a → b.
  (Lamport gives total order but loses concurrency information.)
```

### Edge cases / interview traps

1. **Lamport ≠ wall clock.** It's a logical counter; comparing across nodes only meaningful via the protocol.
2. **Tie-breaking by pid** is required for a *total* order; without it you only get partial.
3. **Cannot detect concurrency.** If L(a) < L(b), you cannot tell if a → b or a || b.
4. **Vector clocks fix this** but cost O(N) space.
5. **Cassandra timestamps** are wall-clock based, not Lamport — but the principle of "monotonic per-key ordering" is the same.
6. **Used in version control** for some local-first apps (Git's commit graph is partial-order).
7. **Useful for total-order broadcast** (TOB) and many consensus protocols at the abstract level.

## Mental Model

Lamport timestamps are like everybody in a meeting writing the agenda-item number on every sticky note they post and adopting the highest number they've seen +1. The numbers don't have to match wall time, but if you wait long enough, every sticky note's number reflects "at least as new as everything that happened before me".

```
P1 events:  A(1)             D(3)        F(5)
                \                 \           \
                 \  send           \  send     \
                  \                 \           \
P2 events:        B(2)              E(4)        G(6)
                                  ^
                                  on receive: L = max(self=2, msg=3) + 1 = 4

Total order: A(1) < B(2) < D(3) < E(4) < F(5) < G(6).
But L(B)=2 and L(D)=3 — could it be that B || D rather than B → D?
With Lamport alone, you can't tell. (In the diagram B → D via the message send.)
```

## Why interviewers care
- Foundational for understanding logical time.
- Bridge to vector clocks, HLC, total-order broadcast.
- Tests grasp of partial vs total order.

## Common beginner confusion
- "Lamport gives wall time." No — purely logical counter.
- "Lamport detects concurrency." No — gives total order but loses concurrency info.
- "Used in production for LWW." Wall clocks are typical for LWW; Lamport is more often in event sourcing or distributed algorithm building blocks.
- "Smaller L means earlier in real time." Not necessarily — only with respect to happens-before.

## Brute force approach

Use wall clocks. Fast, simple, fragile under skew. Don't use for distributed event ordering.

## Optimal approach

Lamport for ordering when concurrency detection isn't needed (broadcast ordering, consensus log indices). Vector clocks when you need to detect concurrency. HLC when you want both monotonic logical and approximate wall-clock semantics.

## Solution

```python
class LamportClock:
    def __init__(self, pid):
        self.pid = pid
        self.l = 0

    def tick(self):
        self.l += 1
        return self.l

    def send_event(self):
        return self.tick()

    def receive_event(self, l_msg):
        self.l = max(self.l, l_msg) + 1
        return self.l

    def total_order_key(self):
        return (self.l, self.pid)
```

Total-order broadcast via Lamport timestamps:

```python
class TOBNode:
    def __init__(self, id, peers):
        self.id = id
        self.peers = peers
        self.clock = LamportClock(id)
        self.pending = []     # heap of (lamport, pid, msg)

    def broadcast(self, msg):
        ts = self.clock.send_event()
        for p in self.peers + [self.id]:
            rpc_call(p, "deliver", ts, self.id, msg)

    def deliver(self, ts, sender, msg):
        self.clock.receive_event(ts)
        heappush(self.pending, ((ts, sender), msg))
        self.try_deliver()

    def try_deliver(self):
        # deliver in (ts, pid) order when all peers have "acked" timestamps lower
        while self.pending and self.safe_to_deliver(self.pending[0][0]):
            (_, msg) = heappop(self.pending)
            self.application_layer.handle(msg)
```

## Step-by-step dry run

3 processes P1, P2, P3.

```
                Lamport values progress:

t=0   P1=0     P2=0     P3=0

t=1   P1 local event A:   P1=1
t=2   P2 local event B:   P2=1
t=3   P3 local event C:   P3=1

t=4   P1 sends m1 to P2 (L=2). P2 receives at t=5: P2 = max(1, 2)+1 = 3.
t=6   P2 local event D:   P2=4
t=7   P3 sends m2 to P1 (L=2). P1 receives at t=8: P1 = max(2, 2)+1 = 3.

Events and timestamps:
  (P1, A, 1)
  (P2, B, 1)
  (P3, C, 1)
  (P1, send m1, 2)
  (P2, recv m1, 3)
  (P2, D, 4)
  (P3, send m2, 2)
  (P1, recv m2, 3)

Total order (Lamport,pid):
  (1, P1) A   (1, P2) B   (1, P3) C   (2, P1) send m1   (2, P3) send m2   (3, P1) recv m2
  (3, P2) recv m1   (4, P2) D

Happens-before edges:
  P1 send m1 → P2 recv m1  ✓ (L(send)=2 < L(recv)=3)
  P3 send m2 → P1 recv m2  ✓
  Concurrent: A || B || C — but Lamport ordered them by pid arbitrarily.
  You CANNOT tell from timestamps which were truly concurrent.
```

## How to think aloud in the interview

> "Lamport timestamps are a single integer counter per process. Rule: every local event bumps the counter; every send carries the counter; every receive takes the max of self and the message's counter, then bumps.
>
> This produces a total order — comparing `(L, pid)` lexicographically — that respects happens-before: if A causally precedes B, then L(A) < L(B). The converse doesn't hold: L(A) < L(B) does not mean A precedes B; they might be concurrent.
>
> Use Lamport when you need a total order on events but don't care about concurrency detection — total-order broadcast, log indices, consensus message ordering. Use vector clocks when concurrency must be detected. Use HLC when you want both logical monotonicity and wall-clock approximation.
>
> Cassandra's LWW uses wall clocks not Lamport, but the same principle of monotonic-per-key applies; clock skew is its known weakness."

## Important takeaways
- Single integer counter per process; max+1 rule on receive.
- Gives a total order that respects happens-before.
- Cannot distinguish concurrent vs causally-ordered events.
- Tie-break by pid for strict total order.
- Used in TOB, consensus log indices, event sourcing.
- Vector clocks are the natural upgrade for concurrency detection.

## Variants
1. **Vector clocks** — per-process counter array; detects concurrency.
2. **Hybrid logical clocks (HLC)** — Lamport + wall time.
3. **Interval Tree Clocks** — fork/join Lamport for dynamic membership.
4. **Bloom clocks** — probabilistic, smaller than vector clocks.
5. **Dotted version vectors** — Riak's variant; avoid false-concurrency on RMW.

## Revision notes

> **lamport-timestamps — 60 second recap**
> - One counter per process. Local event: ++; receive: max(self, msg)+1.
> - Total order via (L, pid); respects happens-before.
> - DOES NOT detect concurrency — that's vector clocks.
> - Use cases: total-order broadcast, log indices, consensus.
> - Cassandra LWW uses wall clocks, not Lamport — vulnerable to skew.
> - HLC is the practical hybrid.
