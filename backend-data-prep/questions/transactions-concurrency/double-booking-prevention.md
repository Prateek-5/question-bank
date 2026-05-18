# Prevent double-booking of a single seat / room / SKU

## Source / Origin
- Universal system-design question across booking startups, ticketing, hotel platforms.
- Real-world: this is exactly the "two cashiers, one Switch" anomaly from Berenson's critique.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`, `08-locks-concurrency.md`.

## Why this question matters in interviews
You will be asked some flavour of "design a booking system" in 80% of senior backend rounds. The crucial sub-problem is: **two users click 'confirm' on the same seat at the same millisecond — how do you guarantee at most one wins?** It's a beautiful interview question because every isolation-level concept lands on it: phantom, write skew, lost update, lock granularity, optimistic vs pessimistic, idempotency. A senior candidate rattles through four solutions, ranks them by elegance, and picks one based on contention shape.

## Concepts involved

### Syntax to lock in

```sql
-- The cleanest: UNIQUE constraint expressing "no two confirms for the same seat"
CREATE TABLE reservations (
  id         SERIAL PRIMARY KEY,
  seat_id    INT NOT NULL,
  user_id    INT NOT NULL,
  show_id    INT NOT NULL,
  UNIQUE (show_id, seat_id)
);

-- Confirm path
INSERT INTO reservations (show_id, seat_id, user_id)
VALUES ($1, $2, $3)
ON CONFLICT (show_id, seat_id) DO NOTHING
RETURNING id;
-- If RETURNING is empty → someone else got the seat first → 409 Conflict.

-- Alternative: status column with pessimistic lock
BEGIN;
SELECT status FROM seats WHERE id = $1 AND show_id = $2 FOR UPDATE;
-- if status='available' then:
UPDATE seats SET status='reserved', user_id=$3 WHERE id=$1 AND show_id=$2;
COMMIT;
```

### Edge cases / interview traps

1. **`SELECT then INSERT` is a race.** Two concurrent transactions both see "no booking exists", both INSERT. This is phantom + write skew. UNIQUE constraint catches it; bare logic doesn't.
2. **`ON CONFLICT DO NOTHING` returns 0 rows.** Check `rowcount` or use `RETURNING id` and detect empty result. Forgetting this check ships the bug intact.
3. **"Soft-hold then confirm"** — most booking flows have a `held` intermediate state with TTL. The TTL is application-managed; you still need atomicity on the hold→confirm transition.
4. **Multi-seat orders.** Booking 4 seats for one party means 4 atomic inserts; partial success = inconsistent order. Wrap in a transaction so all 4 succeed or none.
5. **Idempotency on retry.** If the user clicks confirm twice (network blip), you don't want two charges. Include an idempotency key on the order, separate from the seat-uniqueness check.
6. **MySQL `INSERT IGNORE` vs `ON DUPLICATE KEY UPDATE`** — different semantics; `IGNORE` silently drops, `ON DUPLICATE` upserts. For booking you want IGNORE-shape (= Postgres `DO NOTHING`).
7. **Range overlap** (e.g., hotel room over date range) needs a GIST exclusion constraint, not a plain UNIQUE.

## Mental Model

The **"single chair at the auction"** model. One chair, ten bidders. Three strategies:

- **Auctioneer with a hammer** — first hand up gets it (UNIQUE constraint = DB hammer).
- **Lock the chair with a key** — bidder locks the chair, then takes their time deciding (FOR UPDATE).
- **Bidders write tickets, only the smallest number wins** — optimistic version (rarely best for seats).
- **One ticket per ticket-counter** — pre-allocate slots, just claim one (semaphore table).

```
   User A clicks confirm  ─┐
   User B clicks confirm  ─┼──► race to the DB
   User C clicks confirm  ─┘

   DB enforces: UNIQUE(show_id, seat_id)
   Winner: whichever INSERT lands first
   Losers: 0 rowcount → 409 Conflict
```

## Why interviewers care

- It's a **systems-design-meets-correctness** problem — they're checking both your DB and your API skills.
- They want you to **avoid the SELECT-then-INSERT trap** — the rookie mistake every junior makes.
- They want **idempotency awareness** — what happens on duplicate user clicks?
- They probe **multi-seat orders** — do you transactionally lock all seats or one at a time?

## Common beginner confusion

- "I'll lock the seats table." Locks the whole table, kills concurrency, blocks unrelated bookings.
- "Wrapping in a transaction is enough." A transaction guarantees atomicity of the steps, not uniqueness of the outcome. You still need a constraint or lock.
- "`SELECT FOR UPDATE` on the seat row" — works *only if the row already exists*. For "create reservation if not exists", there's no row yet. UNIQUE INDEX is the actual fix.
- "Distributed locks via Redis." Useful, but in-DB UNIQUE is simpler and stronger when both confirms hit the same DB.

## Brute force approach

`SELECT COUNT(*) FROM reservations WHERE ...; IF count = 0 THEN INSERT`. Classic race. Ship this, get paged at 3 AM.

## Optimal approach

Recipe by booking shape:

- **Single seat, no overlap** → `UNIQUE(show_id, seat_id)` + `INSERT ... ON CONFLICT DO NOTHING`. Check rowcount.
- **Pre-existing seat row with status** → `SELECT ... FOR UPDATE` then conditional UPDATE.
- **Range overlap (date intervals)** → `EXCLUDE USING gist` exclusion constraint.
- **Multi-seat order** → wrap in a transaction; UNIQUE catches each seat; if any fails, ROLLBACK whole order.
- **Idempotent retries** → idempotency key on `orders` table, separate from seat uniqueness.

## Solution

```sql
-- ============================================================
-- Recipe #1: UNIQUE constraint (the canonical answer)
-- ============================================================

CREATE TABLE reservations (
  id         BIGSERIAL PRIMARY KEY,
  show_id    INT NOT NULL,
  seat_id    INT NOT NULL,
  user_id    INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  idempotency_key UUID,
  UNIQUE (show_id, seat_id),
  UNIQUE (idempotency_key)
);

-- Confirm endpoint (single seat)
INSERT INTO reservations (show_id, seat_id, user_id, idempotency_key)
VALUES ($1, $2, $3, $4)
ON CONFLICT (show_id, seat_id) DO NOTHING
RETURNING id;
-- rowcount = 1 → confirmed
-- rowcount = 0 → seat taken; check if idempotency_key matches an existing row
--                (your row), else 409 Conflict

-- ============================================================
-- Recipe #2: FOR UPDATE on a status column
-- ============================================================

CREATE TABLE seats (
  show_id INT,
  seat_id INT,
  status  TEXT CHECK (status IN ('available', 'held', 'reserved')),
  held_by INT,
  held_until TIMESTAMPTZ,
  PRIMARY KEY (show_id, seat_id)
);

BEGIN;
SELECT status, held_until FROM seats
WHERE show_id = $1 AND seat_id = $2
FOR UPDATE;
-- If status = 'available' OR (status='held' AND held_until < NOW() AND held_by != me):
UPDATE seats
SET status='reserved', held_by=$3, held_until=NULL
WHERE show_id=$1 AND seat_id=$2;
COMMIT;

-- ============================================================
-- Recipe #3: range-overlap (hotel room over dates)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE bookings (
  id      BIGSERIAL PRIMARY KEY,
  room_id INT NOT NULL,
  during  TSTZRANGE NOT NULL,
  EXCLUDE USING gist (room_id WITH =, during WITH &&)
);
-- Concurrent overlapping inserts: one succeeds, other raises 23P01 exclusion_violation

-- ============================================================
-- Recipe #4: multi-seat order
-- ============================================================
BEGIN;
INSERT INTO orders (id, user_id, idempotency_key, status)
VALUES ($1, $2, $3, 'PENDING')
ON CONFLICT (idempotency_key) DO NOTHING;
-- Insert each seat, all in the same transaction
INSERT INTO reservations (show_id, seat_id, user_id, order_id)
VALUES
  ($show, $seat1, $user, $1),
  ($show, $seat2, $user, $1),
  ($show, $seat3, $user, $1),
  ($show, $seat4, $user, $1);
-- If any UNIQUE violation: whole tx rolls back; user gets "one of your seats was taken"
UPDATE orders SET status='CONFIRMED' WHERE id=$1;
COMMIT;
```

Node confirm handler:

```javascript
async function confirmSeat(showId, seatId, userId, idempotencyKey) {
  const { rows } = await db.query(
    `INSERT INTO reservations (show_id, seat_id, user_id, idempotency_key)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (show_id, seat_id) DO NOTHING
     RETURNING id`,
    [showId, seatId, userId, idempotencyKey]
  );
  if (rows.length === 1) return { ok: true, id: rows[0].id };

  // Check if it's the user's own prior reservation (idempotent retry)
  const existing = await db.query(
    `SELECT id FROM reservations
     WHERE show_id=$1 AND seat_id=$2 AND idempotency_key=$3`,
    [showId, seatId, idempotencyKey]
  );
  if (existing.rows.length === 1) return { ok: true, id: existing.rows[0].id, retry: true };
  return { ok: false, error: 'SEAT_TAKEN' };
}
```

## Step-by-step dry run

Two concurrent confirms with UNIQUE constraint:

```
time →

T1 (User A):  |--INSERT (show=1, seat=5, user=A) ON CONFLICT DO NOTHING--|--rowcount=1--|--HTTP 200--|
T2 (User B):    |--INSERT (show=1, seat=5, user=B) ON CONFLICT DO NOTHING--|--rowcount=0--|--HTTP 409--|

DB state: one row {show=1, seat=5, user=A}.
T2's INSERT internally hit the unique index, saw a key collision, the ON CONFLICT clause
turned the error into "0 rows inserted". No retry needed; client gets a clean 409.
```

Multi-seat order with two concurrent overlapping orders:

```
T1 wants {seat=5, seat=6, seat=7}:
  |--BEGIN--|--INSERT seat=5 OK--|--INSERT seat=6 OK--|--INSERT seat=7 OK--|--COMMIT--|
T2 wants {seat=6, seat=8}:
  |--BEGIN--|--INSERT seat=8 OK--|--INSERT seat=6 FAILS unique_violation--|--ROLLBACK--|

T1 confirmed 3 seats. T2 rolled back entirely (including seat=8) — atomicity preserved.
User B gets "seat 6 was just taken; please reselect".
```

Allowed at: any isolation level if no constraint and no FOR UPDATE. Prevented by: UNIQUE INDEX (any level), FOR UPDATE on status row, exclusion constraint for ranges.

## How to think aloud in the interview

> "Double-booking is a phantom + write skew on the seat. Two concurrent confirms both see 'no booking exists', both insert, double-book. The cleanest fix is a UNIQUE constraint on (show_id, seat_id) plus `INSERT ... ON CONFLICT DO NOTHING RETURNING id`. The winner gets 1 rowcount, the loser gets 0 and we return 409. No isolation upgrade needed; the DB enforces the invariant physically.
>
> For range overlap (hotel rooms over dates) I'd use a GIST exclusion constraint with `&&` on the range.
>
> For multi-seat orders, wrap all inserts in one transaction so partial failure rolls back atomically.
>
> Idempotency on user-double-click is a separate concern — I'd add an idempotency_key UNIQUE column on the reservation/order so a retried POST returns the same outcome instead of failing as 'seat taken by yourself'."

## Important takeaways

- **UNIQUE constraint is the canonical answer.** Cheapest, engine-agnostic, works at any isolation level.
- `INSERT ... ON CONFLICT DO NOTHING` + `RETURNING id` + rowcount check is the pattern.
- Range overlap needs `EXCLUDE USING gist`.
- Multi-seat orders wrap in transaction so partial failure rolls back.
- Idempotency key is separate from uniqueness — handles user-double-click distinctly from real conflict.
- Never use SELECT-then-INSERT for "create if not exists".

## Variants

1. **High-contention seat (e.g., front row at a concert)** — UNIQUE handles correctness but losers retry. Mitigate with a lottery / virtual queue.
2. **Soft holds with TTL** — `held_until` column; expired holds become available. Cleanup job or check at confirm time.
3. **Distributed booking across cells/shards** — UNIQUE is local. Cross-shard booking needs a single source of truth (often a dedicated reservation service).
4. **MySQL difference** — same pattern using `INSERT IGNORE` or `INSERT ... ON DUPLICATE KEY UPDATE`. Watch out for auto-increment burn (gaps in the PK from failed inserts).
5. **Eventual consistency on cache** — if you cache seat availability, the cache may show "available" briefly after a confirm. UI must treat it as best-effort; the DB is the source of truth.

## Revision notes

> **double-booking-prevention — 60 second recap**
> - Two concurrent confirms = phantom + write skew on the seat.
> - **Canonical fix**: `UNIQUE(show_id, seat_id)` + `INSERT ... ON CONFLICT DO NOTHING RETURNING id`. Check rowcount.
> - Range overlap → `EXCLUDE USING gist (room WITH =, during WITH &&)`.
> - Multi-seat orders → wrap in transaction; partial failure rolls back atomically.
> - Idempotency key → separate column, handles user-double-click distinctly.
> - MySQL: `INSERT IGNORE` or `ON DUPLICATE KEY UPDATE`.
> - Never SELECT-then-INSERT. Always express the invariant as a DB constraint.
