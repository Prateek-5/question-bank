# 2PC vs 3PC: blocking, non-blocking, and why both lose to Raft

## Source / Origin
- Gray (1978) Two-Phase Commit; Skeen and Stonebraker (1983) Three-Phase Commit.
- Production: XA transactions, distributed RDBMS, Saga is the modern alternative.
- Concept reference: `backend-data-prep/distributed-systems/atomic-commit.md`.

## Why this question matters in interviews
2PC is the textbook distributed commit protocol — and the textbook example of "why distributed transactions don't scale". If you can describe both phases, name the blocking problem, contrast 3PC's pre-commit phase, and articulate why modern systems prefer sagas or Raft-replicated state machines, you signal you understand atomicity across machines.

## Concepts involved

### Syntax / mechanism to lock in

**2PC** (two-phase commit):
```
Coordinator                       Participants
   |                                  |
   |---- PREPARE ------------>        |
   |   each participant writes        |
   |   PREPARE log, holds locks       |
   |<--- VOTE YES / NO ---------      |
   |                                  |
   |  if all YES: write COMMIT log    |
   |---- COMMIT ------------->        |
   |   each participant commits       |
   |<--- ACK -------------------      |
   |                                  |
   |  if any NO: write ABORT log      |
   |---- ABORT -------------->        |
```

**3PC** adds a PRE-COMMIT phase to bound the blocking window:
```
Phase 1: CAN-COMMIT (vote)
Phase 2: PRE-COMMIT (acknowledge intent, but don't commit yet)
Phase 3: DO-COMMIT
If coordinator dies after Phase 2, participants can elect new coordinator
and complete commit because all of them voted YES already.
```

### Edge cases / interview traps

1. **2PC blocks indefinitely** if coordinator crashes after PREPARE — participants hold locks until coordinator returns.
2. **3PC assumes synchronous network with bounded latency.** In an async network (real internet), it can still violate atomicity under network partitions.
3. **2PC participants must write PREPARE to durable log** before voting YES.
4. **Heuristic decisions** — DBA manually resolves stuck participants (XA `xa_recover`).
5. **3PC is rarely used in practice.** Most systems either accept 2PC's blocking risk or switch to sagas/Paxos.
6. **2PC is not "consensus"** — it's atomic commit. Different problem; can be solved by consensus (Paxos commit).
7. **Locks held during PREPARE → reduce throughput** dramatically; you serialise on the slowest participant.

## Mental Model

2PC is the wedding officiant analogy: "Do you take...? Do you take...? Then I pronounce you married." If anyone says "no" — abort. The problem: if the officiant has a heart attack between asking and pronouncing, the couple is stuck — they each privately said yes but the marriage isn't recorded. That's the 2PC blocking state.

```
2PC timeline (blocking failure mode):

Coordinator      Participant A         Participant B
    |                |                       |
    |--PREPARE---->  PREPARE log; lock        |
    |<--YES------                              |
    |--PREPARE---->                  PREPARE log; lock
    |<--YES----------------------------------
    |
    |  [COMMIT log written? Maybe.]
    |  CRASH at coordinator.
    |
    |                |                       |
    A and B hold locks. Don't know if they should commit or abort.
    Cannot decide unilaterally. BLOCKED until coordinator recovers
    (and its log says COMMIT or ABORT).
```

## Why interviewers care
- Tests understanding of atomic commit across machines.
- Reveals knowledge of XA, distributed transactions, and their limits.
- Bridges to why modern systems prefer sagas and event-driven compensation.

## Common beginner confusion
- "2PC is consensus." It's atomic commit; weaker problem, solvable by consensus.
- "3PC fixes everything." Only under synchronous assumptions; partitions still break it.
- "2PC is fine at scale." Tail latency and lock contention make it impractical above a few participants.
- "Use 2PC for microservices." Modern advice: use sagas with compensation.

## Brute force approach

Run 2PC for every cross-service write. Works correctness-wise; tail latency, lock contention, and blocking under coordinator failure kill it in production at scale.

## Optimal approach

For two-database transactions where you must have atomicity (rare): use XA 2PC, accept blocking risk, monitor with alerts. For everything else (microservices, async workflows): use sagas with idempotent compensating actions and the outbox pattern.

## Solution

```python
# 2PC coordinator (simplified)
class Coordinator:
    def __init__(self, participants):
        self.participants = participants

    def commit_txn(self, tx_id, ops_per_participant):
        # Phase 1: PREPARE
        votes = []
        for p, ops in ops_per_participant.items():
            try:
                vote = rpc_call(p, "prepare", tx_id, ops, timeout=10)
                votes.append(vote)
            except Timeout:
                votes.append("NO")

        decision = "COMMIT" if all(v == "YES" for v in votes) else "ABORT"
        durable_log.write(tx_id, decision)        # critical durability point

        # Phase 2: COMMIT / ABORT
        for p in ops_per_participant:
            try:
                rpc_call(p, decision.lower(), tx_id, timeout=10)
            except Timeout:
                async_retry_queue.add((p, tx_id, decision))  # eventually
        return decision


class Participant:
    def prepare(self, tx_id, ops):
        try:
            apply(ops, lock=True)
            durable_log.write(tx_id, "PREPARED", ops)
            return "YES"
        except Exception:
            return "NO"

    def commit(self, tx_id):
        ops = durable_log.read(tx_id).ops
        finalize(ops)
        release_locks(tx_id)
        durable_log.write(tx_id, "COMMITTED")
```

## Step-by-step dry run

3 participants, all vote YES, coordinator crashes after writing COMMIT log:

```
t=0   Coordinator → A,B,C: PREPARE(tx_42, ops)
t=1   A,B,C each: write PREPARE log; lock affected rows; reply YES.
t=2   Coordinator receives all YES votes.
t=3   Coordinator writes COMMIT(tx_42) to its durable log.
t=4   Coordinator CRASHES before sending COMMIT to participants.

Meanwhile A,B,C are blocked, holding locks, waiting for the decision.

t=5   Coordinator restarts. Reads its log → finds COMMIT(tx_42).
t=6   Resends COMMIT to A,B,C. They finalize and release locks. Done.

----------------------------------------------------------------------
Worse case: coordinator crashes BEFORE writing COMMIT log.

t=3   Coordinator decides COMMIT mentally but hasn't written log.
t=4   Coordinator CRASHES.
t=5   Coordinator restarts. No COMMIT log entry → decision = ABORT (presumed abort rule).
t=6   Send ABORT. Participants undo their PREPARE state.

But what if the coordinator NEVER comes back? Participants are stuck.
In 3PC, after PRE-COMMIT phase, participants can elect a new coordinator
and recover — but only under synchronous network. Real network → partitions
mean 3PC can also lose atomicity.
```

## How to think aloud in the interview

> "2PC has two phases: PREPARE (coordinator asks all participants if they can commit; each writes a PREPARE log and votes YES/NO) and COMMIT/ABORT (if all YES, coordinator writes COMMIT to its log and tells everyone to finalise; else ABORT).
>
> The blocking problem: if the coordinator crashes after some participants have prepared but before all have heard the decision, those participants hold locks indefinitely. They can't decide unilaterally because they don't know if the others voted YES too.
>
> 3PC adds a PRE-COMMIT phase. Once everyone PRE-COMMITS, even if the coordinator dies, participants know all voted YES and can elect a new coordinator to drive the commit. But 3PC assumes synchronous bounded-latency network — under real partitions, atomicity can still fail.
>
> In practice, 2PC's blocking risk plus lock-holding latency makes it unsuitable for most modern systems. We use sagas with compensating actions instead. The exception is XA 2PC across two databases when business correctness genuinely demands atomicity — we accept the operational pain."

## Important takeaways
- 2PC = PREPARE + COMMIT/ABORT; blocks indefinitely if coordinator dies mid-protocol.
- 3PC adds PRE-COMMIT to bound blocking; assumes synchronous network.
- Both are atomic commit protocols, not consensus (but Paxos can implement commit).
- Locks held across PREPARE — kills throughput.
- Modern alternative: sagas with idempotent compensating actions + outbox.
- XA 2PC still used for two-DB transactions in legacy enterprise.

## Variants
1. **Paxos Commit** — replace coordinator with a Paxos group; no blocking.
2. **Saga** — sequence of local transactions with compensating actions.
3. **Try-Confirm-Cancel (TCC)** — saga variant with explicit reserve phase.
4. **Outbox pattern** — atomic local write + event for downstream; eventual consistency.
5. **2PC with presumed abort** — if no COMMIT log entry, assume abort on recovery (saves a fsync).

## Revision notes

> **2pc-vs-3pc — 60 second recap**
> - 2PC: PREPARE (vote, lock) + COMMIT/ABORT.
> - Coordinator crash after PREPARE → participants blocked, locks held.
> - 3PC: + PRE-COMMIT; bounds blocking under sync network, fails under partitions.
> - Both kill tail latency; locks held across cross-network round trips.
> - Modern: sagas + compensating actions + outbox + idempotency.
> - XA 2PC niche: two-DB atomic transactions in legacy systems.
