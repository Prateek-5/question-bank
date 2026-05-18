# Two-phase commit (2PC): coordinator + participants protocol

## Source / Origin
- Classic distributed-systems protocol from Jim Gray (1978).
- X/Open XA standard codifies it for heterogeneous resource managers.
- Concept reference: `backend-data-prep/sql/06-transactions.md`.

## Why this question matters in interviews
2PC is the *textbook* answer to "how do you make N distributed databases agree on a commit?". Interviewers test whether you can (a) walk through prepare + commit phases, (b) name the failure modes (especially coordinator-failure-after-prepare), and (c) explain why microservices avoid 2PC in favor of sagas + outbox. If you can sketch the message flow and articulate the blocking problem, you signal real distributed-systems literacy.

## Concepts involved

### Syntax to lock in

```sql
-- Postgres prepared transactions (the local primitive 2PC builds on)
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
PREPARE TRANSACTION 'tx-2024-001';   -- writes WAL, releases nothing until COMMIT PREPARED
-- ... coordinator now decides ...
COMMIT PREPARED 'tx-2024-001';       -- final commit
-- OR
ROLLBACK PREPARED 'tx-2024-001';     -- abort

-- Inspect prepared transactions
SELECT * FROM pg_prepared_xacts;

-- Enable in postgresql.conf
-- max_prepared_transactions = 10  (0 by default = disabled)
```

### Edge cases / interview traps

1. **The blocking problem**: if the coordinator crashes after participants prepared but before sending commit/abort, participants hold their locks indefinitely waiting for instructions. Cannot self-resolve.
2. **Prepare phase is durable**: a participant who voted YES *must* honor it. Crashes recover by replaying WAL and looking up the prepared tx on restart.
3. **`max_prepared_transactions = 0` by default in Postgres.** Must enable explicitly; consumes shared memory.
4. **2PC is not the same as Postgres' commit phase**. A single Postgres commit is implicitly 2PC between WAL fsync and visibility. The interview is about cross-system 2PC.
5. **XA transactions** are the standard API: Java JTA, .NET DTC. Most modern microservice stacks avoid XA.
6. **Performance**: 2PC requires 2× round-trips + 2× fsyncs. Throughput hits hard.
7. **Modern alternatives**: sagas (compensating actions), outbox + idempotency, Paxos-based distributed SQL (Spanner, CockroachDB) — all designed to escape 2PC's blocking problem.
8. **3PC** adds a "pre-commit" phase to make non-blocking under coordinator failure; rarely used in practice (network assumptions don't hold).

## Mental Model

The **"contract signing with notarization"** model. Three parties sign a contract. A notary (coordinator) asks each: "Are you ready to sign?" Each replies yes/no. If all yes, the notary tells each "sign now". If any no, "rip up the draft". The danger: if the notary disappears between the last "yes" reply and the "sign now" instruction, the parties sit holding their pens, not knowing whether to sign or tear up.

```
   Phase 1: PREPARE                    Phase 2: COMMIT
   ────────────────                    ───────────────

   Coordinator                         Coordinator
      │                                   │
      ├──"prepare"──► P1                  ├──"commit"──► P1
      ├──"prepare"──► P2                  ├──"commit"──► P2
      ├──"prepare"──► P3                  └──"commit"──► P3
      │                                                  │
      ◄──"YES"────── P1                  ◄──"ACK"─────── P1
      ◄──"YES"────── P2                  ◄──"ACK"─────── P2
      ◄──"YES"────── P3                  ◄──"ACK"─────── P3
      │                                   │
   Decision: all YES → COMMIT          Done. Locks released.
   Decision: any NO  → ABORT
   Persist decision before phase 2.
```

The **blocking failure mode**:

```
   Coordinator
      │
      ├──"prepare"──► P1
      ├──"prepare"──► P2
      │
      ◄──"YES"────── P1                  P1 holds locks; voted yes; cannot abort.
      ◄──"YES"────── P2                  P2 holds locks; voted yes; cannot abort.
      │
      💀 (coordinator crashes here)      P1, P2 wait forever.
                                          Manual operator intervention required.
```

## Why interviewers care

- It's the **textbook distributed transaction protocol** — they want to know if you know the canonical answer.
- They probe **failure modes** — especially the coordinator-crash blocking problem.
- They want you to **identify why modern microservices avoid it** — and propose sagas + outbox as alternatives.
- They probe **2PC's role inside distributed SQL** (Spanner uses Paxos-based commit; CockroachDB uses a Raft-replicated transaction record).

## Common beginner confusion

- "2PC is just two phases." Yes, but the durable persistence of the prepare *vote* by each participant is the key insight.
- "If the coordinator crashes, the participants vote again." They can't — they've already prepared and are bound by their YES vote.
- "2PC guarantees consistency." It guarantees atomicity across participants. Consistency (constraint enforcement) is local.
- "Modern microservices use 2PC." They mostly don't. Sagas + outbox + idempotency keys are the modern pattern.

## Brute force approach

"Just call all the services in a loop and hope they all succeed." Naive distributed write; partial failure leaves the system in an inconsistent state. This is exactly what 2PC was invented to solve.

## Optimal approach

For homogeneous SQL databases (single vendor across nodes): use distributed SQL (Spanner, CRDB) that internally does Paxos-based commit. Looks like a single transaction from the app's POV.

For heterogeneous microservices: **don't use 2PC**. Use:
- **Outbox + sagas** for cross-service workflows.
- **Idempotency keys** for retry safety.
- **Eventual consistency** with compensating actions for failure cases.

For legacy systems that already use XA: keep 2PC but monitor the prepared-but-not-committed backlog; have runbooks for coordinator failure.

## Solution

```sql
-- ============================================================
-- Local 2PC primitive in Postgres
-- ============================================================

-- Participant A
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
PREPARE TRANSACTION 'transfer-2024-001-A';   -- vote: YES (durable)

-- Participant B
BEGIN;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
PREPARE TRANSACTION 'transfer-2024-001-B';   -- vote: YES (durable)

-- Coordinator (some external process):
--   1. Both voted YES; persist decision = COMMIT in coordinator log
--   2. Send commit to both
COMMIT PREPARED 'transfer-2024-001-A';
COMMIT PREPARED 'transfer-2024-001-B';

-- ============================================================
-- If a participant votes NO during prepare:
-- ============================================================
-- Participant A
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1 AND balance >= 100;
-- If 0 rows: insufficient funds
ROLLBACK;
-- Coordinator records NO; tells everyone to abort
ROLLBACK PREPARED 'transfer-2024-001-B';
```

Coordinator pseudo-code:

```python
class Coordinator:
    def commit_distributed(self, tx_id, participants):
        # Phase 1: prepare
        votes = []
        for p in participants:
            try:
                p.send('PREPARE', tx_id)
                votes.append(p.recv())
            except Timeout:
                votes.append('NO')

        decision = 'COMMIT' if all(v == 'YES' for v in votes) else 'ABORT'

        # **CRITICAL**: persist decision to durable log BEFORE phase 2
        self.log.write(tx_id, decision)
        self.log.fsync()

        # Phase 2: send decision; retry indefinitely on failure
        for p in participants:
            while True:
                try:
                    p.send(decision, tx_id)
                    p.recv_ack()
                    break
                except (Timeout, NetworkError):
                    time.sleep(retry_backoff())

    def recover_on_startup(self):
        # Replay any in-flight decisions
        for tx_id, decision in self.log.unfinished():
            for p in self.participants_of(tx_id):
                p.send(decision, tx_id)
```

## Step-by-step dry run

Happy path with two participants:

```
time →

Coord:   |--prepare tx P1--|--prepare tx P2--|--collect votes (YES, YES)--|--persist decision=COMMIT--|--commit P1--|--commit P2--|--done--|
P1:      |--prepare WAL fsynced, vote YES--|----------------------------------------(locks held)----|--commit, release locks--|
P2:                       |--prepare WAL fsynced, vote YES--|----------------------(locks held)------|--commit, release locks--|

Both rows updated atomically across two databases. No partial state visible to external observers (assuming RR or higher reads).
```

Coordinator crash after prepare (the famous failure):

```
time →

Coord:   |--prepare P1--|--prepare P2--|--collect (YES, YES)--|--💀 crash before persisting decision--|
P1:      |--prepared, locks held--------------------------------- (stuck forever) ------------------|
P2:      |--prepared, locks held--------------------------------- (stuck forever) ------------------|

Recovery:
  Coordinator restarts, reads its log:
    No decision persisted → coordinator wasn't sure → must contact participants
    Participants: "we voted YES; what's the decision?"
    Coordinator: "I don't know either; I'll abort." → ROLLBACK PREPARED on both.

But if coordinator log says "decision=COMMIT" (persisted before crash):
    Coordinator on restart: sends commit to both.

Worst case: coordinator log lost (disk failure). Operator must manually decide and run COMMIT/ROLLBACK PREPARED on each participant. This is why 2PC has the "blocking" reputation.
```

## How to think aloud in the interview

> "2PC: coordinator + N participants. Phase 1 prepare: coordinator asks each participant to durably write their changes to WAL and vote yes/no. Each participant that votes yes is now *bound* — it holds locks and cannot unilaterally abort. Phase 2 commit: if all voted yes, coordinator persists the decision and sends commit to all; otherwise abort.
>
> The blocking failure mode: coordinator crashes after participants voted yes but before sending the decision. Participants hold their locks indefinitely; cannot resolve without coordinator. Manual intervention required.
>
> 2PC's costs: 2× round trips, 2× fsyncs, locks held longer (across the prepare-to-commit window). Plus the blocking problem.
>
> Modern microservices avoid 2PC. Instead they use:
> 1. **Outbox** for atomic DB-write-plus-event-emit.
> 2. **Sagas** with compensating transactions for cross-service workflows.
> 3. **Idempotency keys** for retry safety.
> 4. Within a single distributed SQL database (Spanner, CockroachDB), Paxos/Raft replaces classical 2PC with non-blocking consensus.
>
> 2PC is still used inside JDBC XA transactions for legacy enterprise systems and inside distributed SQL engines as a primitive. Application-level 2PC is a red flag for senior reviewers."

## Important takeaways

- 2PC = prepare phase (collect votes) + commit phase (send decision).
- Prepare is *durable*: a YES vote cannot be retracted.
- **Blocking failure**: coordinator crashes after prepare → participants stuck.
- 2× round trips, 2× fsyncs, locks held longer — performance cost.
- Postgres `PREPARE TRANSACTION` / `COMMIT PREPARED` is the local primitive.
- `max_prepared_transactions = 0` by default; must enable.
- Modern microservices avoid app-level 2PC; use outbox + sagas + idempotency.
- Spanner/CockroachDB use Paxos/Raft inside; look like 2PC to apps but non-blocking under failure.

## Variants

1. **3PC**: adds pre-commit phase to make non-blocking. Assumes synchronous network; doesn't hold in real internets. Rarely used.
2. **Paxos-based commit**: replicate the transaction record itself via Paxos so coordinator failure is non-blocking. Spanner, CockroachDB.
3. **Saga**: replace cross-service atomicity with sequence of local transactions + compensating actions.
4. **Outbox + idempotent consumer**: at-least-once messaging with dedupe; eventual consistency.
5. **XA (X/Open distributed transactions)**: standard API for 2PC across resources (DB + JMS + ...). Used in J2EE.
6. **Two-phase locking ≠ two-phase commit**. 2PL is a concurrency control protocol within one DB. 2PC is a commit protocol across multiple DBs.

## Revision notes

> **two-phase-commit — 60 second recap**
> - Phase 1: coordinator asks N participants to prepare; each fsyncs and votes YES/NO.
> - Phase 2: coordinator persists decision; sends commit/abort to all.
> - **Blocking**: coordinator crash after prepare → participants stuck holding locks.
> - 2× RTT, 2× fsync, locks held longer.
> - Postgres: `PREPARE TRANSACTION` + `COMMIT PREPARED`; `max_prepared_transactions ≥ 1`.
> - **Modern microservices avoid app-level 2PC**; use outbox + sagas + idempotency.
> - Spanner/CockroachDB use Paxos/Raft inside — non-blocking under coordinator failure.
> - 2PL ≠ 2PC. 2PL = concurrency control; 2PC = commit protocol.
