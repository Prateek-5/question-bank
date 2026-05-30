# SQLAlchemy session scope — `scoped_session`, `async_session`, request scope

## Source / Origin
- SQLAlchemy 2.0 Unified API: <a href="https://docs.sqlalchemy.org/en/20/orm/session_basics.html" target="_blank" rel="noopener noreferrer">https://docs.sqlalchemy.org/en/20/orm/session_basics.html</a>
- Mike Bayer's docs on session scope are the canonical reference; every senior Python engineer should read them.
- The single most common Flask/FastAPI bug source: wrong session scope.

## Why this question matters in interviews
Session scope is where Python web apps go wrong. Symptoms include "DetachedInstanceError mid-request", "stale data after a write", "two threads sharing a connection", "session leaked between requests". The right question separates juniors who copy boilerplate from seniors who can explain:
- Why a global `Session()` is wrong.
- Why `scoped_session` works in threaded WSGI but breaks in async / threadpools.
- Why FastAPI uses `Depends(get_db)` instead of `scoped_session`.
- The async-specific traps (no implicit IO, `expire_on_commit=False` is almost mandatory).

## Concepts involved

### The three scopes you must know

```
┌────────────────────────────────────────────────────────────────────┐
│  GLOBAL Session (single, app-wide)                                 │
│   - Almost always wrong.                                           │
│   - Shared identity map across requests = stale data + race        │
│     conditions.                                                    │
│   - Not thread-safe.                                               │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  scoped_session (thread-local, classic Flask pattern)              │
│   - One Session per thread, lazily created.                        │
│   - Works for sync WSGI (Flask + gunicorn workers).                │
│   - Breaks under asyncio (one event loop, many coroutines, same    │
│     thread).                                                       │
│   - Must remove() at request end or you leak.                      │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  Request-scoped session (FastAPI / Starlette)                      │
│   - One Session per request via dependency injection.              │
│   - Safe for both sync and async.                                  │
│   - Closes deterministically (context manager).                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  AsyncSession + async_scoped_session                               │
│   - For async drivers (asyncpg, aiomysql).                         │
│   - Lazy loading raises sync-IO errors → use joinedload/select.    │
│   - expire_on_commit=False is the default-you-should-set.          │
└────────────────────────────────────────────────────────────────────┘
```

### Syntax to lock in

```python
# Classic Flask (sync) — scoped_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(URL, pool_size=10, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(bind=engine))

@app.teardown_appcontext
def remove_session(exc):
    SessionLocal.remove()         # CRITICAL — return to pool

@app.route('/users/<int:id>')
def get(id):
    u = SessionLocal().get(User, id)
    return {'email': u.email}
```

```python
# FastAPI (sync) — dependency-injected request scope
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/users/{id}')
def get(id: int, db: Session = Depends(get_db)):
    return db.get(User, id)
```

```python
# FastAPI (async) — AsyncSession + dependency injection
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

aengine = create_async_engine(ASYNC_URL, pool_size=10)
AsyncSessionLocal = async_sessionmaker(aengine, expire_on_commit=False)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as s:
        yield s

@app.get('/users/{id}')
async def get(id: int, db: AsyncSession = Depends(get_db)):
    u = await db.get(User, id)
    return {'email': u.email}
```

### Edge cases / interview traps

1. **`scoped_session` under async** — sync `scoped_session` uses `threading.local()`. Multiple coroutines on the same thread share the same Session → data races and double-flushes.
2. **`async_scoped_session` requires a scopefunc** like `asyncio.current_task` — without it, sessions still get shared.
3. **`expire_on_commit=True` in async** is painful: after commit, attribute access triggers a `SELECT`, but in async that becomes a sync-IO-in-async error. Use `expire_on_commit=False`.
4. **Lazy loading is forbidden in async**: `await db.get(User, 1); u.orders` will raise `MissingGreenlet` because the lazy-load is sync IO inside an async context. Use `selectinload`, `joinedload`, or refresh explicitly.
5. **`session.close()` returns the connection to the pool**; `session.remove()` (scoped) does both close + reset thread-local.
6. **`pool_pre_ping=True`** is the cheapest cure for "MySQL server has gone away" / stale connection issues.
7. **Background tasks / Celery** must NOT inherit the request session. Open a fresh session in the task.
8. **`autoflush=True`** (the default) can cause surprise flushes during queries — disable in apps that mix raw SQL and ORM operations.
9. **Identity map is per-session.** Two requests → two sessions → two distinct User#1 instances. `==` between them is False.
10. **Nested transactions** via `session.begin_nested()` use SAVEPOINTs — useful for "try this, rollback to checkpoint".

## Mental Model

A Session is a **transactional bubble** with an identity map. The interview question is **how long does the bubble live, and who owns its end?**

- **Per-process global** = bubble lives forever → identity map grows unboundedly, threads collide.
- **Thread-local (`scoped_session`)** = bubble lives until you call `remove()` → fine for sync, broken for async.
- **Per-request (DI / context manager)** = bubble born at request entry, closed at request exit → deterministic, scales to async, no shared state.
- **Per-task (Celery, async job)** = each task opens and closes its own session → clean.

The constant rule: **never share a Session across boundaries** (threads, coroutines, requests, tasks).

## Why interviewers care

- It's where the rubber meets the road for "do you understand concurrency in Python".
- Async makes the old patterns wrong → reveals whether you've upgraded.
- DetachedInstanceError questions reduce to "what's your session scope?".

## Common beginner confusion

- "I'll make Session a global." Then concurrent requests share an identity map.
- "`scoped_session` is the right answer everywhere." Only for sync. In async, you'll get coroutine collisions.
- "I can lazy-load in async; the await will handle it." It won't — lazy-load is sync IO; async session refuses.
- "`expire_on_commit` doesn't matter." It does — especially in async; almost always set to False at the sessionmaker.

## Brute force approach

A module-level `session = Session(engine)` reused everywhere. Survives `hello-world.py`. Fails the first time two requests interleave: identity map confusion, intermixed transactions, deadlocks.

## Optimal approach

1. **Sync Flask / WSGI**: `scoped_session(sessionmaker(...))` + teardown `remove()`. Or context-manager `with Session(engine) as s` per request.
2. **FastAPI sync**: `Depends(get_db)` yielding `SessionLocal()`.
3. **FastAPI async**: `Depends(get_db)` yielding `AsyncSessionLocal()`, `expire_on_commit=False`, `autoflush=False` for predictability, eager-load via `selectinload`/`joinedload`.
4. **Background tasks**: open + close a fresh session inside the task body.
5. **Bulk jobs**: `Session` with `expire_on_commit=False` and explicit `flush()` per batch, or `connection.execute(insert(...))` core for max throughput.

## Solution

### Pattern A — Sync Flask, full setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
SessionLocal = scoped_session(SessionFactory)

# Inject as flask.g.db
@app.before_request
def open_session():
    g.db = SessionLocal()

@app.teardown_request
def close_session(exc):
    db = g.pop('db', None)
    if db is not None:
        if exc:
            db.rollback()
        else:
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
        db.close()
    SessionLocal.remove()
```

### Pattern B — FastAPI async, production shape

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

aengine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    aengine,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise

@app.get('/users/{id}')
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(User)
        .options(selectinload(User.orders))
        .where(User.id == id)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise HTTPException(404)
    return UserDto.from_orm(user)
```

### Pattern C — Background task / Celery

```python
@celery.task
def process_payment(payment_id: int):
    with SessionLocal() as db:
        p = db.get(Payment, payment_id)
        ...
        db.commit()
    # NOT: passing the session from the request. Always open fresh.
```

### Pattern D — Nested transaction via SAVEPOINT

```python
async with AsyncSessionLocal() as db:
    async with db.begin():
        db.add(parent)
        try:
            async with db.begin_nested():       # SAVEPOINT
                db.add(child)
                await db.flush()
        except IntegrityError:
            pass  # SAVEPOINT rolled back; outer txn intact
    # outer commit
```

## Step-by-step dry run

### Scenario: 2 concurrent FastAPI requests, async, correct setup

```
T=0   Request A enters → Depends(get_db) creates SessionA (conn from pool slot 1)
T=0   Request B enters → Depends(get_db) creates SessionB (conn from pool slot 2)

T=1   A: db.get(User, 1) → SessionA loads User#1 instance (instance_A)
T=1   B: db.get(User, 1) → SessionB loads User#1 instance (instance_B)
      instance_A is NOT instance_B  — separate identity maps; separate snapshots

T=2   A: user.email = 'new'; await db.commit()
        SessionA: UPDATE users SET email='new' WHERE id=1; COMMIT
        instance_A NOT expired (expire_on_commit=False)
T=2   B: still has stale instance_B with old email
        B: await db.commit() (no change to user) → fine
        B returns stale email in response

T=3   A finishes → SessionA closes → conn returned to pool slot 1
T=3   B finishes → SessionB closes → conn returned to pool slot 2

KEY: B's staleness is a snapshot artifact, not a bug. If B needs fresh data,
it must select again or db.refresh(instance_B).
```

### Scenario: scoped_session under async (broken)

```
T=0   Request A enters; thread T1; scoped_session creates SessionA bound to T1
T=0   Request B enters; same thread T1 (single event loop!);
      scoped_session sees existing SessionA → returns SAME instance to B

T=1   A: db.add(user_a)
T=1   B: db.add(user_b)
      Both queued in the same session.

T=2   A: db.commit()  → both A's and B's writes commit together
      Now B thinks it's committed; A's transaction boundary is wrong.

T=3   B: db.commit() → no-op or error; B's domain logic violated.

FIX: use async_scoped_session(scopefunc=asyncio.current_task)
     or use request-scoped Depends(get_db) — preferred.
```

## How to think aloud in the interview

> "Three patterns, three contexts:
>
> 1. **Sync WSGI (Flask)**: `scoped_session(sessionmaker(...))` with thread-local scoping; teardown calls `remove()`. Each request thread gets its own Session.
>
> 2. **FastAPI sync**: dependency injection via `Depends(get_db)` that yields a Session from a `sessionmaker`. Closes in the finally block. Cleaner than `scoped_session` because no shared state.
>
> 3. **FastAPI async**: `AsyncSessionLocal` from `async_sessionmaker`, dependency-injected, **always** `expire_on_commit=False` and **never** lazy-load. Eager via `selectinload`/`joinedload`/`with_loader_criteria`.
>
> Rules I never break:
> - One session per request. Background tasks open their own.
> - `pool_pre_ping=True` to avoid the dreaded 'MySQL gone away'.
> - `expire_on_commit=False` for async.
> - Never close session before returning entities to the JSON layer (or DTO-map first).
> - `autoflush=False` when I want to avoid surprise SQL during queries.
>
> Trap I always raise: **`scoped_session` is wrong under async** unless you pass `scopefunc=asyncio.current_task`. The default `threading.local()` will collide coroutines."

## Important takeaways

- **Never share a Session** across threads, coroutines, requests, or tasks.
- **Sync WSGI**: `scoped_session` + teardown `remove()`.
- **Async**: `AsyncSession`, `expire_on_commit=False`, **no lazy loading**.
- **FastAPI**: `Depends(get_db)` is the cleanest pattern for both sync and async.
- **Pool sizing**: `pool_size + max_overflow` should not exceed DB's `max_connections`.
- **`pool_pre_ping=True`** for stale-connection safety.
- **Background tasks** open their own session — never pass the request's session.
- **`begin_nested()`** = SAVEPOINT, useful for "try sub-transaction" semantics.
- **Identity map is per-session** — same row in two sessions = two distinct objects.

## Variants

1. **"What's `autocommit` mode?"** Pre-2.0 legacy; 2.0 uses "future-style" transactions. Always `begin/commit/rollback` explicitly.
2. **"How do you share a connection (not session) across services?"** `with engine.connect() as conn:` for core-level operations; `Session(bind=conn)` to layer ORM on top.
3. **"Test pattern with rollback?"** Wrap each test in a transaction, use SAVEPOINTs, rollback at teardown — `pytest-flask-sqlalchemy` / `pytest-postgresql` patterns.
4. **"Why does `db.execute()` matter vs `db.query()`?"** 2.0 unified API uses `db.execute(select(...))`. Old 1.x `db.query(Model)` is legacy.
5. **"Connection pool exhaustion symptoms?"** Hanging requests → check `engine.pool.status()`. Usually a missing `db.close()` or a session held across awaits without yielding back.

## Revision notes

> **sqlalchemy-session-scope — 60 second recap**
> - One Session per request. Never share across threads/coroutines/tasks.
> - Sync: `scoped_session` + teardown `remove()`. Async: `AsyncSession` + DI.
> - Async **must** use `expire_on_commit=False` + eager-load. Lazy load = `MissingGreenlet`.
> - `pool_pre_ping=True` for stale connections; `pool_recycle` for periodic refresh.
> - FastAPI: `Depends(get_db)` yields a session; closes in finally.
> - Background tasks open their own session.
> - Identity map is per-session; same row in two sessions = two objects.
> - **Trap:** `scoped_session` under asyncio collides coroutines unless `scopefunc=asyncio.current_task`.
