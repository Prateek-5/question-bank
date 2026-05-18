# Transactional scope design — where does `@Transactional` belong?

## Source / Origin
- Spring/Hibernate interview classic; equivalent variants in NestJS/TypeORM, Django, Flask/SQLAlchemy.
- Concept references: `backend-data-prep/orm/01-orm-internals.md` (transactions section), `transactions-concurrency/*.md` (isolation, retries).

## Why this question matters in interviews
The placement of transaction boundaries is the **most common architectural mistake** in backend codebases — and the one that surfaces as flaky tests, mysterious deadlocks, and "the row I just saved is gone" bugs. The interviewer asks: *which layer owns the transaction?* The right answer (service layer, not repository, not controller, not "wherever") and the *why* (atomicity of a use case, not a query) instantly signal senior.

## Concepts involved

### Syntax to lock in

```typescript
// ============================================================
// Spring / Java — the canonical example
// ============================================================
@Service
class TransferService {
  @Transactional        // ← begins TX on entry, commits on return, rolls back on RuntimeException
  public void transfer(long from, long to, BigDecimal amt) {
    Account a = accountRepo.findById(from).orElseThrow();
    Account b = accountRepo.findById(to).orElseThrow();
    a.debit(amt);
    b.credit(amt);
    accountRepo.save(a);
    accountRepo.save(b);
  }
}

// ============================================================
// NestJS + TypeORM — service-layer transaction
// ============================================================
@Injectable()
class TransferService {
  constructor(private dataSource: DataSource) {}

  async transfer(from: number, to: number, amt: number) {
    return this.dataSource.transaction(async (manager) => {   // ← service owns TX
      const a = await manager.findOneByOrFail(Account, { id: from });
      const b = await manager.findOneByOrFail(Account, { id: to });
      a.balance -= amt; b.balance += amt;
      await manager.save([a, b]);
    });
  }
}

// ============================================================
// Prisma — interactive transaction
// ============================================================
await prisma.$transaction(async (tx) => {
  await tx.account.update({ where: { id: from }, data: { balance: { decrement: amt } } });
  await tx.account.update({ where: { id: to   }, data: { balance: { increment: amt } } });
}, { isolationLevel: 'Serializable', timeout: 5000 });

// ============================================================
// SQLAlchemy — context-managed session
// ============================================================
def transfer(from_id, to_id, amt):
    with Session(engine) as session, session.begin():     # ← TX here
        a = session.get(Account, from_id)
        b = session.get(Account, to_id)
        a.balance -= amt; b.balance += amt
```

### Layered architecture — the canonical pattern

```
   ┌─────────────────────────────┐
   │  Controller / Handler       │   ← HTTP / RPC / Job
   │   - Parses request          │
   │   - Calls service           │
   │   - NO transactions here    │
   └──────────┬──────────────────┘
              │
              ▼
   ┌─────────────────────────────┐
   │  Service / Use-case         │   ← OWNS the transaction boundary
   │   - One method = one TX     │
   │   - Coordinates repos       │
   │   - Translates domain rules │
   └──────────┬──────────────────┘
              │
              ▼
   ┌─────────────────────────────┐
   │  Repository / DAO           │   ← Pure data access
   │   - Single-entity CRUD      │
   │   - NO transactions here    │
   │   - NO business logic       │
   └─────────────────────────────┘
```

### Edge cases / interview traps

1. **TX in the controller.** Bad: the controller's purpose is HTTP; transactions are about business consistency. Coupling them means every controller learns about Session/EntityManager.
2. **TX in the repository.** Worse: each repo method runs its own TX, so a service-level method that calls 3 repos has 3 separate TXs — no atomicity.
3. **Nested `@Transactional`** — usually becomes a **savepoint**, not a new TX. If the inner method's `REQUIRES_NEW` is set, you get a separate TX with its own connection. Most teams ban this because it's confusing.
4. **External API call inside TX** — locks held while waiting on the network. Connection pool exhaustion + lock-wait deadlocks. Move I/O outside, or use the **transactional outbox** pattern.
5. **`@Transactional` and self-invocation in Spring** — a method calling another `@Transactional` method on the same bean via `this.foo()` skips the proxy → no new TX starts. Classic gotcha.
6. **Checked exceptions in Spring** don't roll back by default — only `RuntimeException` and `Error`. Add `rollbackFor = Exception.class` or use `runtime` exceptions.
7. **Read-only transactions** are real — `@Transactional(readOnly = true)` lets Hibernate skip dirty tracking and route to read replicas.
8. **Long-running TX kills throughput.** Lock contention, replication lag, idle-in-transaction. Keep TXs short — fetch + decide + write, then commit.
9. **TX timeout** — set one explicitly. Default is "forever" in many ORMs, which means a hung connection holds locks indefinitely.

## Mental Model

A **transaction = one business decision**. The unit isn't a query or a row — it's "the user transferred $100" or "the order was placed and inventory reserved." That unit lives in the service layer.

```
   Request:  POST /transfer { from, to, amt }

   Controller     ─►  parse JSON, authorize
                                                 ◄── NO TX
   Service.transfer(from, to, amt)
       ├─ BEGIN TX  ─────────────────────────────────┐
       │   accountRepo.findById(from)                │
       │   accountRepo.findById(to)                  │  ◄── one logical unit
       │   debit; credit                             │      one TX scope
       │   accountRepo.save([from, to])              │
       │   auditRepo.recordTransfer(...)             │
       └─ COMMIT (or ROLLBACK on exception) ─────────┘

   Controller     ─►  shape response
```

The rule:
- **Service method begins, commits, rolls back.** One method = one TX.
- **Repos take a tx-aware manager/session.** They don't open or commit.
- **Controllers and middleware never touch TX.**

## Why interviewers care

- Tests **layered architecture vocabulary** — service, repository, use-case, unit-of-work.
- Tests **failure thinking**: what rolls back? what doesn't? when is the lock held?
- Tests **operational maturity** — long TX = bad, I/O in TX = bad, retry strategy = required.
- Distinguishes "I copy-pasted `@Transactional`" from "I know how proxying, propagation, and rollback rules work."

## Common beginner confusion

- **"Slap `@Transactional` on the controller and call it a day."** Couples HTTP to DB; every retry now retries the whole request including external side effects.
- **"Every repository method should be `@Transactional`."** Then you can't compose two repos atomically; the service has 3 independent TXs.
- **"Nested `@Transactional` starts a new TX."** Usually it joins the outer one (propagation REQUIRED). Only `REQUIRES_NEW` opens a new TX (and a new connection).
- **"My exception didn't roll back — is the TX broken?"** No, Spring's default rolls back on `RuntimeException` and `Error` only. Add `rollbackFor`.
- **"I'll call `transactionManager.commit()` myself."** Almost always a code smell. Let the framework handle it via try/catch.
- **"Read-only is just a hint."** Some ORMs (Hibernate) skip dirty checking and Spring routes to read replicas — measurable speedup.

## Brute force approach

Wrap *every* service method in a TX with default settings. Works for most cases. Misses: read-only optimization, isolation tuning, retry on conflicts, propagation choices for cross-service composition.

## Optimal approach

1. **Service layer owns TX.** One service method = one TX boundary.
2. **Repos accept a tx-scoped session / manager.** They never open their own TX.
3. **Read-only methods declared `readOnly = true`** — gives the ORM permission to skip dirty tracking and the framework to use a replica.
4. **External I/O outside the TX.** Use the transactional outbox or saga pattern if cross-system writes are needed.
5. **Explicit isolation** when correctness demands it: `SERIALIZABLE` for write-skew-prone flows, `REPEATABLE READ` for "consistent snapshot" reads.
6. **Retry wrapper** for serialization failures (`40001`) and deadlocks (`40P01`).
7. **Timeouts** — set a TX timeout (e.g., 5s) so a hung query can't hold locks indefinitely.

## Solution

```typescript
// ============================================================
// NestJS + TypeORM — production-grade transactional service
// ============================================================
import { Injectable } from '@nestjs/common';
import { DataSource, EntityManager } from 'typeorm';

@Injectable()
class TransferService {
  constructor(private ds: DataSource) {}

  async transfer(fromId: number, toId: number, amt: number) {
    return this.withRetry(() =>
      this.ds.transaction('SERIALIZABLE', async (mgr) => {
        const from = await mgr.findOneByOrFail(Account, { id: fromId });
        const to   = await mgr.findOneByOrFail(Account, { id: toId });

        if (from.balance < amt) throw new InsufficientFundsError();

        from.balance -= amt;
        to.balance   += amt;
        await mgr.save([from, to]);

        await mgr.insert(Ledger, {
          fromId, toId, amt, ts: new Date(),
        });

        // NOTE: do NOT publish to Kafka here — outbox pattern instead
        await mgr.insert(Outbox, {
          topic: 'transfer.completed',
          payload: { fromId, toId, amt },
          status: 'PENDING',
        });
      })
    );
  }

  private async withRetry<T>(fn: () => Promise<T>, max = 3): Promise<T> {
    for (let i = 0; i < max; i++) {
      try { return await fn(); }
      catch (e: any) {
        const code = e?.driverError?.code ?? e?.code;
        if (code === '40001' || code === '40P01') {       // serialization fail / deadlock
          await new Promise(r => setTimeout(r, 50 * (1 << i) + Math.random() * 20));
          continue;
        }
        throw e;
      }
    }
    throw new Error('TX_RETRY_EXHAUSTED');
  }
}

// ============================================================
// Repository — NO transactions, accepts manager
// ============================================================
class AccountRepository {
  findById(mgr: EntityManager, id: number) {
    return mgr.findOneByOrFail(Account, { id });
  }
  save(mgr: EntityManager, accounts: Account[]) {
    return mgr.save(accounts);
  }
}

// ============================================================
// Read-only path — Hibernate / Spring style
// ============================================================
@Service
class AccountQueryService {
  @Transactional(readOnly = true)        // ← signals replica routing + no dirty checking
  public AccountDto findOne(long id) {
    Account a = accountRepo.findById(id).orElseThrow();
    return AccountDto.from(a);
  }
}
```

## Step-by-step dry run

Request: `POST /transfer { from: 1, to: 2, amt: 100 }`

```
1. Controller receives request, parses JSON, authorizes user.
   (No TX.)
        │
        ▼
2. Service.transfer() entered → AOP proxy intercepts → BEGIN TX (SERIALIZABLE).
        │
        ▼
3. mgr.findOneByOrFail(Account, {id:1})
   - SELECT * FROM accounts WHERE id = 1 FOR UPDATE  (depending on lock mode)
   - hydrate into Account#1; row locked
        │
        ▼
4. mgr.findOneByOrFail(Account, {id:2})  → SELECT, hydrate, lock.
        │
        ▼
5. balance check, debit/credit on in-memory objects.
        │
        ▼
6. mgr.save([from, to])
   - UPDATE accounts SET balance = $1 WHERE id = 1;
   - UPDATE accounts SET balance = $1 WHERE id = 2;
        │
        ▼
7. mgr.insert(Ledger, {...})
   - INSERT INTO ledger (...) VALUES (...);
        │
        ▼
8. mgr.insert(Outbox, {...})
   - INSERT INTO outbox (...) VALUES (...);
        │
        ▼
9. Service method returns normally.
   - AOP proxy calls COMMIT.
   - All UPDATEs/INSERTs durable.
        │
        ▼
10. Outbox worker (separate process) reads outbox row → publishes to Kafka.
    (No external I/O inside the TX; system stays loosely coupled.)
```

If a `RuntimeException` is thrown at any point inside step 3-8:
- AOP proxy catches it → ROLLBACK → all locks released, no rows changed.
- If it's `40001` / `40P01`, the retry wrapper re-runs the whole service method (with fresh state).

If step 3 hung (TX timeout 5s exceeded):
- DB or framework kills the transaction; rollback fires; retry kicks in.

## How to think aloud in the interview

> "Transaction boundaries live in the **service layer**. One service method = one transaction = one business decision (transfer $100, place an order, register a user). The controller is HTTP, the repository is data access — neither owns transactions.
>
> The repo accepts a tx-scoped manager or session. That way the service can compose multiple repo calls inside one transaction.
>
> Four discipline rules:
> 1. **No external I/O inside a TX** — use the outbox pattern for downstream events.
> 2. **Set an explicit timeout** so a hung query doesn't hold locks forever.
> 3. **Retry on `40001` / `40P01`** with exponential backoff.
> 4. **Read-only methods marked `readOnly = true`** — gives the ORM permission to skip dirty checks and route to replicas.
>
> Watch-outs:
> - Spring self-invocation: `this.foo()` skips the proxy, so the inner `@Transactional` doesn't fire.
> - Spring rollback rules: only `RuntimeException` by default; checked exceptions don't roll back unless declared in `rollbackFor`.
> - Nested `@Transactional` joins the outer TX (REQUIRED), unless `REQUIRES_NEW` — most teams avoid this for clarity."

## Important takeaways

- TX boundary lives in the **service layer**, not controller or repository.
- One service method = one logical TX = one business decision.
- Repos take a tx-scoped session/manager; they don't open or commit.
- External I/O goes **outside** the TX (outbox pattern, sagas).
- Set explicit isolation and timeout; retry on `40001` / `40P01`.
- Spring `@Transactional` defaults roll back only on `RuntimeException`; checked exceptions need `rollbackFor`.
- Self-invocation skips the proxy — class methods called via `this.foo()` won't start a new TX.

## Variants

1. **Saga across services** — instead of one TX, model the flow as compensating actions (book hotel → book flight → if flight fails, cancel hotel). Discussed in the messaging set.
2. **`REQUIRES_NEW` for audit logs** — audit entry must commit even if the parent rolls back. Open a sibling TX with its own connection.
3. **`SUPPORTS` / `NOT_SUPPORTED`** — propagation modes for methods that work with or without an outer TX (rare; explicit is better).
4. **Two-phase commit (XA)** — distributed TX across DB + queue. Avoid unless required; the outbox pattern is simpler.
5. **Read-only TX on replica** — Spring `@Transactional(readOnly = true)` + `AbstractRoutingDataSource` routes to the replica.

## Revision notes

> **transactional-scope-design — 60 second recap**
> - Service layer owns the TX; one method = one TX = one business decision.
> - Repos accept a session/manager; never open their own TX.
> - Controllers never touch TX.
> - External I/O outside TX (outbox pattern for events).
> - Set timeouts; retry on `40001` (serialization) / `40P01` (deadlock).
> - Read-only TX is real — replica routing + skipped dirty check.
> - Spring traps: self-invocation skips proxy; checked exceptions don't roll back by default; nested usually joins outer.
