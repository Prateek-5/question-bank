# JavaScript Interview Prep — Senior Backend Edition

A curated, concept-classified, machine-coding-focused prep repo for a senior backend engineer (3–4 yrs) who is rusty on day-to-day JavaScript but solid on theory. Built for a 10–15 day sprint into senior backend interviews where JS shows up in machine-coding rounds and screens.

---

## What's in here

```
javascript-interview-prep/
├── README.md                     ← you are here
├── learning-plan.md              ← 15-day daily schedule
├── concepts/                     ← 10 deep-dive primers (one per concept, each with worked interview examples)
└── questions/                    ← 154 question files, concept-classified
    ├── 01-hoisting/              12 files
    ├── 02-closures/              15 files
    ├── 03-prototype/             14 files
    ├── 04-promises/              20 files
    ├── 05-event-loop/            15 files
    ├── 06-streams/               12 files
    ├── 07-arrays/                15 files
    ├── 08-maps-sets/             13 files
    ├── 09-recursion/             13 files
    └── 10-machine-coding-patterns/ 25 files
```

**Totals:** 10 concept primers + 154 question files + 1 plan + 1 README = 166 markdown files (~2.1 MB).

### Concepts covered

| # | Concept | Primer | Question Folder |
|---|---|---|---|
| 1 | Hoisting & scoping (var/let/const, TDZ, function/class hoisting, ES modules) | [concepts/hoisting.md](concepts/hoisting.md) | [questions/01-hoisting/](questions/01-hoisting/) |
| 2 | Closures (lexical env, private state, loop-closures, memory leaks) | [concepts/closures.md](concepts/closures.md) | [questions/02-closures/](questions/02-closures/) |
| 3 | Prototype, `this`, classes, polyfills of `bind`/`call`/`apply`/`new` | [concepts/prototype.md](concepts/prototype.md) | [questions/03-prototype/](questions/03-prototype/) |
| 4 | Promises, async/await, polyfills (`all`/`race`/`allSettled`), pools, retries | [concepts/promises.md](concepts/promises.md) | [questions/04-promises/](questions/04-promises/) |
| 5 | Event loop (libuv phases, microtasks vs macrotasks, `nextTick` vs `setImmediate`) | [concepts/event-loop.md](concepts/event-loop.md) | [questions/05-event-loop/](questions/05-event-loop/) |
| 6 | Streams, iterators, generators (backpressure, `pipeline`, async iterators) | [concepts/streams.md](concepts/streams.md) | [questions/06-streams/](questions/06-streams/) |
| 7 | Arrays (polyfills, sparse arrays, sort traps, big-O of common ops) | [concepts/arrays.md](concepts/arrays.md) | [questions/07-arrays/](questions/07-arrays/) |
| 8 | Map / Set / WeakMap (vs Object, JSON, LRU patterns, GC-aware caching) | [concepts/maps-sets.md](concepts/maps-sets.md) | [questions/08-maps-sets/](questions/08-maps-sets/) |
| 9 | Recursion (tree/graph traversal, deep clone, V8 no-TCO trap) | [concepts/recursion.md](concepts/recursion.md) | [questions/09-recursion/](questions/09-recursion/) |
| 10 | Machine-coding patterns (debounce, throttle, EventEmitter, LRU, rate-limiter, etc.) | [concepts/machine-coding-patterns.md](concepts/machine-coding-patterns.md) | [questions/10-machine-coding-patterns/](questions/10-machine-coding-patterns/) |

### Per-question file structure (every file follows this 11-section format)

```
# <Problem Name>

## Source
## Why this question matters in interviews
## Concepts involved          (syntax / runtime / edge cases / traps)
## Brute force approach
## Optimal approach
## Solution (JavaScript)      (interview-ready code in a ```js block)
## Step-by-step dry run       (tick-by-tick trace with sample input)
## Important takeaways        (syntax + patterns + mistakes + related)
## Variants                   (2-3 interviewer twists)
## Revision notes             (boxed 8-15 line cram block)
```

The **gold-standard exemplar** is [`questions/10-machine-coding-patterns/debounce.md`](questions/10-machine-coding-patterns/debounce.md) — every other file was written to match its depth and voice.

---

## Best order to study

You have two practical entry points. Pick based on time available:

### A. Full 15-day plan (recommended)
Follow [`learning-plan.md`](learning-plan.md) day-by-day. Foundations first → async core → streams + collections → recursion → machine-coding patterns → mocks → revision.

### B. 7-day crunch (if you're tight on time)
Skip primer reads on the concepts you already know cold. Concentrate on:
1. **Day 1** — `04-promises` + `05-event-loop` (these dominate backend interviews).
2. **Day 2** — `10-machine-coding-patterns` (debounce, throttle, EventEmitter, retry, promise-pool, LRU, rate-limiter — minimum).
3. **Day 3** — `02-closures` + `03-prototype` (output-prediction puzzles + polyfills).
4. **Day 4** — `06-streams` + `09-recursion` (deep-clone, tree traversal, async iterators).
5. **Day 5** — `07-arrays` + `08-maps-sets` (reduce-fluency + LRU-with-Map).
6. **Day 6** — `01-hoisting` (1 hr, output-prediction is muscle memory by now) + weak-spot revisions.
7. **Day 7** — Full 60-min mock + cram revision blocks.

### Why this ordering
Backend JS interviews load *heavily* on async + machine-coding + closures. Hoisting and prototype questions show up as quick warm-ups; they're worth knowing cold but not worth grinding for a week. Streams and recursion show up when interviewer wants to test depth (you should be able to discuss backpressure and cycle-safe clones credibly, but you won't see them every round).

---

## Last-minute revision strategy (day before)

**Read only this. Do not learn anything new.**

1. **The 60-second revision blocks** at the bottom of every concept primer (10 files × 60 sec = 10 min).
2. **The "Revision notes" boxed block** at the bottom of every question file you've solved — speed-skim only your strongest 40–50. (~45 min)
3. **Re-type these 5 patterns from a blank file** (no peeking — 30 min total):
   - `debounce(fn, wait)`
   - `Promise.all` polyfill
   - `EventEmitter` (on/off/once/emit)
   - `retry(fn, { attempts, backoff })`
   - LRU cache with `Map`
4. **The microtask vs macrotask trace.** Predict the output of one mixed setTimeout / Promise.then / queueMicrotask / process.nextTick example out loud. (10 min)
5. **Your own `notes.md`** — the mistakes file you've been building since Day 1. (15 min)

Total day-before time: **≈ 1.5 hours.** Anything more and you'll panic. Sleep beats cramming.

**Morning of the interview:**
- Open a blank file. Type `debounce` + `Promise.all` polyfill from memory in 10 min.
- That's it. Walk in.

---

## Machine-coding strategy for backend engineers

Machine-coding rounds are pattern-recognition rounds. The interviewer wants to see: structure, naming, tests, edge cases, then performance discussion. Speed comes from having the patterns burned in — not from typing fast.

### The 9 patterns that cover ~80% of senior backend JS machine-coding rounds

These are the implementations you should be able to produce **from a blank file in ≤ 25 minutes each**, with tests, while talking out loud:

1. **`debounce`** + **`throttle`** — the universal warm-up.
2. **`EventEmitter`** — comes up whenever they want to test prototype/Map/closure all at once.
3. **`retry(fn, { attempts, backoff, jitter, signal })`** — backend bread and butter; expect AbortSignal follow-up.
4. **`promisePool(tasks, concurrency)`** — "Implement Promise.all but cap concurrency to N." If you can write the running-pool version (not chunked) cleanly, you're already above the bar.
5. **`Promise.all` polyfill** (and a strong opinion on `allSettled` / `race` differences).
6. **`LRU cache`** with `Map` — O(1) get/put, eviction on size, optional TTL.
7. **`rateLimiter`** (token bucket) — refill rate, capacity, `tryConsume`. Bonus: per-key (e.g. per API-key) bucket.
8. **`batchProcessor(fn, { maxSize, maxWait })`** — groups calls, flushes on size or timeout. Common in real systems (DB writes, log shipping).
9. **`deepClone`** with cycles — WeakMap-tracked, handles Date/RegExp/Map/Set/cycles. Mention `structuredClone` exists.

If you walk in with all 9 of those memorized, you're ready.

### The interview script (do this every machine-coding round)

1. **Restate the spec in your words.** "So you want `X(args)` that returns `Y`, with the following constraints: A, B, C. Anything I'm missing?" — buys you 30 seconds + catches misunderstandings.
2. **Write the function signature and example calls FIRST.** Before any implementation. This anchors you.
3. **Stub the function with a comment block of the algorithm.** 3–5 lines of pseudocode. Talk through it.
4. **Implement.** Talk while typing. Narrate why each line exists ("closure over `timerId` so it persists across calls").
5. **Hand-run with a sample input** out loud. Catch bugs before the interviewer does.
6. **Edge cases the interviewer hasn't mentioned.** Bring them up yourself: "What if `wait` is 0? What about leading-edge?" Even if you don't implement the variant, *naming* them earns points.
7. **Tests** — write 3–5 sanity checks with `node --test` (no jest setup needed in interviews). Most candidates skip this. Don't.
8. **Performance discussion** — Big-O of your solution. Where it'd fail (memory, contention, lost updates).
9. **What you'd add for production** — observability, error semantics, cancellation, instrumentation, retries-on-retries. This is the "senior" signal.

### Backend framings to inject (always score well)

- "In production, I'd wire this through our logging / metrics — emit a counter on each rate-limit deny."
- "If `fn` returns a promise, we should think about whether we want to *queue* or *drop*."
- "For multi-instance deployments, this is in-memory state — we'd back it with Redis."
- "The `AbortSignal` pattern is what I'd use to make this cancellable end-to-end."

These cost nothing to say and put you visibly above the candidates who only know the academic algorithm.

### What NOT to do

- Don't open with theory. Start writing. Backend interviewers care about output, not lecturing.
- Don't optimize prematurely. Get a working version, *then* discuss the production version.
- Don't argue with the interviewer about API design. Implement what they asked, then ask about alternatives.
- Don't `console.log` debug in the final solution. Show that you can reason about correctness without running.

---

## How this repo was built

This repo was curated from a live crawl of:
- codedamn Node.js problem list (pages 1–20)
- LeetCode JavaScript problemset + 30 Days of JavaScript study plan
- Canonical senior-JS interview problems (where source coverage was sparse)

Questions were classified into 10 concept buckets (NOT by source) — so all closures questions sit together, all promise questions sit together, etc. This is deliberately optimized for **concept-by-concept revision**, not source-by-source completion.

The set is intentionally weighted toward async + machine-coding (45 of the 154 files) and closures + prototype (29 files) since those dominate senior backend JS interviews. Hoisting, streams, and recursion are kept tighter (~12–13 files each) because they show up as warm-ups or depth-checks, not as the main event.

Every file passed a 4-axis quality bar (Concept Completeness, Interview Relevance, Explanation Clarity, Revision Utility — all ≥ 8/10) before being saved.

---

## A note on attitude

You're a senior backend engineer. You aren't here to learn JavaScript — you're here to **prove fluency under pressure**. The whole point of this repo is to **rebuild the muscle memory** that long-term server work eroded.

Every problem in here can be done two ways: the academic way (which gets a passing grade) and the senior way (which makes the interviewer write a "yes" on the rubric). The "Variants", "Important takeaways", and "Revision notes" sections of every file are where the senior signal lives.

Type the patterns. Don't read them. Good luck.
