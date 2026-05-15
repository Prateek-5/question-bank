# 15-Day JavaScript Interview Prep Plan
**Audience:** Senior backend engineer (3–4 yrs), rusty on JS, strong on theory.
**Goal:** Walk into a machine-coding round and produce correct, idiomatic JS under time pressure.

---

## How to use this plan with 154 questions

The repo has **154 question files** — far more than you can solve carefully in 15 days. Treat it as a deep bench, not a checklist.

For each concept folder, your daily target is **the first 6–8 files (the canonical ones)**. The rest are there as:
- Variants to pull from when you want extra reps on a weak area
- "Day 12 weak-spot day" material
- Practice problems for after the interview is booked but before it lands

If you complete all 154, you're way past the bar. If you complete the canonical 6–8 per bucket × 10 buckets ≈ **70 questions** + the daily code-reps, you're interview-ready.

**Priority signal** (look for these — they're the canonical ones in each folder):
- Anything with `polyfill-` in the name (universal interview material)
- The simplest-named files (`counter.md`, `debounce.md`, `lru-cache.md`)
- Files matching the "9 patterns" list in the README

---

## Ground rules (read once, follow every day)

1. **No tutorials, no videos.** You don't need theory — you need reps. Every day must end with code typed without copy-paste.
2. **Type, don't read.** Even when reading a concept primer, retype the syntax cheat sheet in a scratch file. Muscle memory is the whole game.
3. **Speak the trace out loud.** When dry-running, narrate the call stack and microtask queue. Interviewers want to hear your reasoning, not see your final answer.
4. **One concept folder = one focused block.** Don't jump between concepts in a single session — it kills syntax recall.
5. **Track timing.** Every problem from Day 4 onward gets a stopwatch. Senior bar: easy ≤ 10 min, medium ≤ 25 min, machine-coding ≤ 45 min including tests.
6. **Day-before mode (Day 14–15):** only re-read the "60-second revision" blocks + your own notes file. No new content.

---

## Daily structure (every day)

| Block | Duration | Activity |
|---|---|---|
| Warm-up | 15 min | Type out 1 syntax cheat sheet from yesterday's concept primer without looking. |
| Core | 90–120 min | Today's primary work (concept / questions / mock). |
| Code reps | 45 min | Solve 1 machine-coding pattern from scratch (no peeking). |
| Wrap-up | 15 min | Update your personal `notes.md` with mistakes made today + the one thing you'd say differently to an interviewer. |

---

## Day-by-day

### Day 1 — Foundations: hoisting, closures, scope
**Read primers:** `concepts/hoisting.md`, `concepts/closures.md` (focus on the new "Interview worked examples" section in each)
**Solve:** top 6 from `questions/01-hoisting/` (the canonical output-prediction problems) + top 8 from `questions/02-closures/` (counter, once, loop-var-let, module-pattern, curry-via-closures, setinterval-stale-closure, memoize-with-ttl, allow-one-function-call)
**Code reps:** Implement `once(fn)`, `memoize(fn)`, `counter factory` from scratch — each 3 times.
**Goal by EOD:** You can explain TDZ, function vs var hoisting, and write a closure-based private counter in <60 seconds.

---

### Day 2 — Objects, prototype chain, `this`
**Read primer:** `concepts/prototype.md`
**Solve:** all questions in `questions/03-prototype/`
**Code reps:** Implement `Function.prototype.bind` polyfill, `new` keyword polyfill, `Object.create` polyfill.
**Goal by EOD:** You can trace `this` through any of the 5 binding rules at sight, and explain why arrow functions have no `this`.

---

### Day 3 — Async core: promises, async/await, event loop
**Read primers:** `concepts/promises.md`, `concepts/event-loop.md`
**Solve:** first 2/3 of `questions/04-promises/` + first 2/3 of `questions/05-event-loop/`
**Code reps:** Implement a Promise from scratch (just `.then` + `resolve`/`reject`), and `Promise.all` polyfill.
**Goal by EOD:** You can predict the output of any mixed `setTimeout` / `Promise.resolve().then` / `process.nextTick` / `queueMicrotask` puzzle.

---

### Day 4 — Async deep dive: queues, microtasks, libuv phases
**Re-read:** `concepts/event-loop.md` (focus on Node-specific phases)
**Solve:** remaining questions in `questions/04-promises/` and `questions/05-event-loop/`
**Code reps:** `promisePool(tasks, concurrency)`, `retry(fn, { attempts, backoff })`, `withTimeout(promise, ms)`.
**Goal by EOD:** Write a concurrency-limited async map without referencing anything.

---

### Day 5 — Streams + iterators + generators (backend-critical)
**Read primer:** `concepts/streams.md`
**Solve:** all questions in `questions/06-streams/`
**Code reps:** Build a Transform stream that uppercases lines. Convert a paginated API into an async iterator. Generator-based range function.
**Goal by EOD:** You can explain backpressure mechanically and pipe a readable through a transform without looking up the API.

---

### Day 6 — Arrays + collections (Map, Set, WeakMap)
**Read primers:** `concepts/arrays.md`, `concepts/maps-sets.md`
**Solve:** all questions in `questions/07-arrays/` and `questions/08-maps-sets/`
**Code reps:** Polyfills for `map`, `filter`, `reduce`, `flat(depth)`. Build an LRU using Map.
**Goal by EOD:** Reduce-based one-liners are instinct, and you know when to reach for `Map` vs `Object` vs `WeakMap`.

---

### Day 7 — Recursion + tree/graph traversal
**Read primer:** `concepts/recursion.md`
**Solve:** all questions in `questions/09-recursion/`
**Code reps:** Iterative DFS/BFS on a JSON tree. Flatten nested object. Recursive deep clone with cycle detection.
**Goal by EOD:** You stop blanking on recursive structure — base case + recursive case is automatic.

---

### Day 8 — Machine-coding patterns (rapid-fire)
**Read primer:** `concepts/machine-coding-patterns.md` (this is your bible)
**Solve:** first half of `questions/10-machine-coding-patterns/`
**Code reps (timed, 20 min each, no peeking):**
- `debounce(fn, wait, { leading, trailing })`
- `throttle(fn, wait)`
- `EventEmitter` (on / off / once / emit)
- `curry(fn)`
- `deepClone(obj)` with cycles
**Goal by EOD:** Five patterns above are muscle memory. You write them while talking.

---

### Day 9 — Machine-coding: scheduling + rate control
**Solve:** second half of `questions/10-machine-coding-patterns/`
**Code reps:**
- `rateLimiter(maxCalls, perMs)` (token bucket)
- `asyncQueue` (FIFO, configurable concurrency)
- `batchProcessor(fn, { maxSize, maxWait })` (groups calls, flushes on size or timeout)
**Goal by EOD:** Token bucket + batch processor are interview-ready in ≤ 25 min each.

---

### Day 10 — Machine-coding: data + cache
**Code reps (full machine-coding session — 60 min each):**
- LRU cache (Map-based, O(1) get/set)
- TTL cache with lazy expiry
- Observable / Pub-Sub system with topic patterns
- In-memory key-value store with `expire(key, sec)` like Redis
**Goal by EOD:** You can design + implement + test a small system in one sitting.

---

### Day 11 — Machine-coding: full mini-systems
Pick **two** of:
- URL shortener (in-memory) with collision handling
- File-watcher / debouncer system (callback-driven)
- Simple ORM-style query builder
- HTTP rate-limited fetch wrapper with retry + circuit breaker
- Job scheduler with cron-like syntax

Build with tests (use `node --test` — no jest setup needed in interviews).
**Goal by EOD:** Comfortable producing a small system from a blank file with proper module structure.

---

### Day 12 — Weak-spot day (self-assessed)
Look at your `notes.md`. Re-do the 5 problems that hurt the most. Then revisit the 2 concept primers that feel shakiest.
**Goal by EOD:** No remaining "ugh" topics.

---

### Day 13 — Mock round #1 (timed)
- 15 min: 3 output-prediction puzzles (hoisting / closures / event-loop questions you haven't seen)
- 25 min: 1 medium algorithmic JS problem (pick from `questions/07-arrays/` or `09-recursion/`)
- 45 min: 1 machine-coding (pick a pattern you didn't drill — e.g. `compose/pipe` or `async filter`)
- 15 min: post-mortem in `notes.md`

**Rule:** simulate the room. Talk out loud. No googling.

---

### Day 14 — Mock round #2 (timed) + revision pass
Morning: another mock (different problem set, harder).
Afternoon: **revision-only mode.** Read every concept primer's "60-second revision" block. Type out 10 patterns from `machine-coding-patterns.md` from memory.

---

### Day 15 — Day-before mode
- 60 min only: re-read your own `notes.md` and the "Revision notes" sections of every question file.
- Sleep early. Don't learn anything new today — confidence > novelty.
- 10 min of warm-up the morning of: implement `debounce` + a Promise.all polyfill on a blank page.

---

## How to measure progress (honest checklist)

By end of Day 8 you should be able to:
- [ ] Predict output of any closure / hoisting puzzle on first read.
- [ ] Explain microtask vs macrotask in 30 seconds with an example.
- [ ] Write a debounce, throttle, and EventEmitter from a blank file in ≤ 15 min each.

By end of Day 12 you should be able to:
- [ ] Implement Promise.all + Promise.allSettled + retry-with-backoff in one sitting.
- [ ] Build a token-bucket rate limiter or LRU cache in ≤ 25 min with tests.
- [ ] Stream-transform a file without consulting docs.

By end of Day 15 you should be able to:
- [ ] Sit through a 45-min machine-coding round without panicking when given an unfamiliar spec.
- [ ] Speak the event loop trace of any async snippet.

---

## What to skip (intentionally)

You're a senior backend engineer. Do **not** spend time on:
- DOM manipulation puzzles
- React component questions
- CSS / framework-specific trivia
- TypeScript syntax (unless the role mandates it — and even then, just the structural type system, not advanced generics)
- ES proposal trivia (decorators, pipeline operator, records & tuples)
- Pure algorithmic LeetCode hards in JS (your time is better spent on machine-coding patterns)

If an interviewer asks DOM / framework questions in a backend role, you can honestly say "I work primarily on the server side" — that's a credible answer.

---

## When you fall behind

If life happens and you lose 2–3 days, cut in this order:
1. **First cut:** Day 11 mini-systems (one is enough).
2. **Next cut:** Day 10 (do only the LRU).
3. **Next cut:** Day 5 streams (keep, but skip the generator/iterator deep dives).
4. **Never cut:** Days 1–4 (foundations), Day 8 (machine-coding patterns), Day 13–15 (mocks + revision). These are non-negotiable.
