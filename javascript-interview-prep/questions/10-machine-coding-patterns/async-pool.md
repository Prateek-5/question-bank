# Async Pool (limit N concurrent tasks)

## Source / Origin
- Asked at: Stripe (Promise pool), Razorpay, Atlassian, Cloudflare, Booking.
- Sometimes phrased as: "Implement `pLimit` from `p-limit`" or "Run M tasks with at most N in flight."
- Concept reference: `concepts/promises.md`; sibling `async-semaphore.md`.

## Why this question matters in interviews
This is *the* async-control-flow question. Everyone hits it: web scrapers, fan-out fetchers, image processors, batch ETL. It's the canonical "you have 10k URLs but the API only allows 5 concurrent calls — go." Interviewers grade you on three things: (1) you don't run all M in parallel (memory explosion); (2) you don't run sequentially (3 days to finish); (3) errors don't sink the whole pool. Solid execution maps to senior signal. Bombing it means you're going to overload someone's database in production.

## Concepts involved

### Syntax to lock in
```js
// pool(limit, items, worker)
async function pool(limit, items, worker) {
  const results = new Array(items.length);
  let cursor = 0;
  const runners = Array(Math.min(limit, items.length)).fill(0).map(async () => {
    while (cursor < items.length) {
      const i = cursor++;
      results[i] = await worker(items[i], i);
    }
  });
  await Promise.all(runners);
  return results;
}
```

### Edge cases / interview traps
1. **Output order must equal input order.** Beginner mistake: pushing into `results` in completion order — fails for "list of pages in order".
2. **One task throws → kill all?** Default: `Promise.all` rejects on first error, but tasks already running keep running. Decide explicitly: fail-fast vs allSettled-style.
3. **Empty input** → return `[]` without spawning runners.
4. **`limit > items.length`** → spawn only `items.length` runners (don't waste).
5. **`limit <= 0`** → throw TypeError; silently allowing it is a footgun.
6. **`worker` is sync** — still works; the `await` of a non-Promise is fine.
7. **Backpressure for streamed input** — when `items` is an async iterable, you can't precompute results array. Need a different shape.
8. **Cancellation** — interview follow-up: thread an AbortSignal so all in-flight work bails out.

## Mental Model

Imagine **N conveyor belts** and a stack of M packages. Each belt grabs the next package, processes it, drops the output into slot `i` of an output rack, and grabs the next. When the stack is empty, all belts stop. Output rack stays in input order because each belt knows its slot.

```
items:  [A][B][C][D][E][F][G][H]   (M=8)
                    ↓
        belt1: A → C → E → G
        belt2: B → D → F → H        (N=2, each belt drains the queue)
                    ↓
results:[A'][B'][C'][D'][E'][F'][G'][H']  (in original order)
```

## Why interviewers care

- **Resource-bounded async** — the hallmark of production-grade code.
- **Order preservation** — separates "I know `Promise.all`" from "I think about output contracts."
- **Error handling decisions** — fail-fast vs partial-success is a *design* discussion.

## Common beginner confusion

- **"Use `Promise.all(items.map(worker))`."** That doesn't bound concurrency; it fires M parallel.
- **"Chunk into groups of N and await each chunk."** Works, but stragglers stall everyone (whole chunk waits for slowest). Pool keeps belts busy.
- **"Use `for...of` with `await` inside."** Strictly sequential — concurrency = 1.
- **"Promises start when you call `.then()`."** No, promises start when *the function is called*. `map(worker)` starts all of them.

## Brute force approach

```js
// sequential — too slow
for (const item of items) results.push(await worker(item));

// parallel — too aggressive
const results = await Promise.all(items.map(worker));
```

## Optimal approach

N "runner" loops each pulling from a shared cursor. Constant memory (N concurrent, not M). Output order preserved by writing to `results[i]`.

## Solution (JavaScript)

```js
async function asyncPool(limit, items, worker, { stopOnError = true } = {}) {
  if (!Number.isInteger(limit) || limit < 1) throw new TypeError('limit must be >=1');
  const results = new Array(items.length);
  const errors  = new Array(items.length);
  let cursor = 0;
  let aborted = false;

  const runners = Array(Math.min(limit, items.length)).fill(0).map(async () => {
    while (!aborted && cursor < items.length) {
      const i = cursor++;
      try {
        results[i] = await worker(items[i], i);
      } catch (err) {
        errors[i] = err;
        if (stopOnError) { aborted = true; throw err; }
      }
    }
  });

  if (stopOnError) await Promise.all(runners);
  else            await Promise.allSettled(runners);

  return stopOnError ? results : { results, errors };
}
```

## Step-by-step dry run

`limit=2`, `items=[A,B,C,D,E]`, each worker takes random 50-150ms.

```
t=0      cursor=0  R1.pick A (cursor=1) ; R2.pick B (cursor=2)
t=80     A done → results[0]=A'; R1.pick C (cursor=3)
t=100    B done → results[1]=B'; R2.pick D (cursor=4)
t=180    C done → results[2]=C'; R1.pick E (cursor=5; loop exits next iter)
t=200    D done → results[3]=D'; R2 exits (cursor=5)
t=260    E done → results[4]=E'; R1 exits
         All runners done → return results=[A',B',C',D',E']
```

Concurrent count never exceeds 2; output is in input order.

## How to think aloud in the interview

> "I'll spawn N runner loops sharing a cursor. Each grabs `items[cursor++]`, awaits worker, writes to `results[i]`, repeats. That keeps memory at O(N) instead of O(M). Order is preserved because each runner writes to its slot. For errors I'd ask: fail-fast or partial-success? Default fail-fast — Promise.all on the runners. For partial-success I'd return `{results, errors}` and use Promise.allSettled."

## Important takeaways

- **N runners + shared cursor + indexed output**: the only pattern you need.
- **No chunking** — chunks waste time on stragglers.
- **Decide error policy upfront**, don't paper over it.
- **`Semaphore + Promise.all(items.map(sem.run))`** is an alternative implementation — same result, slightly more allocations.

## Variants

- **Async iterable input**: `for await (const item of source)` inside a single producer; N consumers race for `source.next()`. Used for streaming a paginated API.
- **AbortSignal**: thread signal into worker + check `signal.aborted` at top of loop; on abort, runners exit without writing results.
- **Per-item timeout**: wrap worker in `Promise.race([worker(...), timeout(ms)])`.
- **Backpressure on results**: if downstream is slow, gate `cursor++` on consumption (becomes a producer-consumer with bounded buffer).

## Revision notes

```
asyncPool(N, items, worker):
  cursor=0, results=[]
  spawn min(N, items.length) runners:
    while cursor < items.length:
      i = cursor++ ; results[i] = await worker(items[i], i)
  Promise.all(runners) → results
  Order preserved (write to results[i])
  Mem O(N), not O(M)
  Errors: fail-fast (Promise.all) or partial (Promise.allSettled + {results, errors})
  Variants: AbortSignal, per-item timeout, async-iterable input
```
