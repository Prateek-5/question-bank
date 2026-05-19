# 06 — Streams

Generators, async iterators, Node streams, Web Streams. Files follow the v2 13-section template.

---

## How to study this folder

1. **Foundation:** fibonacci-generator, custom-iterator, generator-pipeline.
2. **Async iteration:** async-iterator-pagination, callback-api-to-async-iterator, fetch-response-async-iter.
3. **Node streams:** readable-stream-push, writable-stream-implementation, backpressure-demo.
4. **Transforms:** transform-line-parser, csv-parser-via-transform, ndjson-splitter.
5. **Pipelines:** stream-pipeline-lab, stream-pipeline-error-handling, pipeline-error-propagation.
6. **Web Streams:** web-streams-readable, web-streams-transform.
7. **Specialty:** file-line-reader-with-backpressure, stream-to-buffer-with-limits, throttled-stream.

---

## Files (20)

### Foundation
- [fibonacci-generator.md](./fibonacci-generator.md) — Lazy `function*` + yield.
- [custom-iterator.md](./custom-iterator.md) — `Symbol.iterator` + lazy chains.
- [generator-pipeline.md](./generator-pipeline.md) — Unix pipes in JS.

### Async iteration
- [async-iterator-pagination.md](./async-iterator-pagination.md) — `async function*` + paginated API.
- [callback-api-to-async-iterator.md](./callback-api-to-async-iterator.md) — Wrap callback into `for await`.
- [fetch-response-async-iter.md](./fetch-response-async-iter.md) — Stream HTTP body via `res.body`.

### Node streams
- [readable-stream-push.md](./readable-stream-push.md) — `_read`, `push`, `push(null)`.
- [writable-stream-implementation.md](./writable-stream-implementation.md) — `_write`, `_writev`, `_final`.
- [backpressure-demo.md](./backpressure-demo.md) — `write()` returns false, `.once('drain')`.

### Transforms
- [transform-line-parser.md](./transform-line-parser.md) — Buffer partial line.
- [csv-parser-via-transform.md](./csv-parser-via-transform.md) — Quote-aware state machine.
- [ndjson-splitter.md](./ndjson-splitter.md) — Simpler than CSV; JSON per line.

### Pipelines
- [stream-pipeline-lab.md](./stream-pipeline-lab.md) — gzip file via `pipeline`.
- [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md) — Three layered scopes.
- [pipeline-error-propagation.md](./pipeline-error-propagation.md) — Replaces `.pipe()` chains.

### Web Streams
- [web-streams-readable.md](./web-streams-readable.md) — Cross-platform Readable.
- [web-streams-transform.md](./web-streams-transform.md) — `transform` + `flush`.

### Specialty
- [file-line-reader-with-backpressure.md](./file-line-reader-with-backpressure.md) — `readline` + `for await`.
- [stream-to-buffer-with-limits.md](./stream-to-buffer-with-limits.md) — Bounded body parsing.
- [throttled-stream.md](./throttled-stream.md) — Rate-limited via async transform.

---

## Concept primers

- [`concepts/streams.md`](../../concepts/streams.md) — Stream mechanics.
- [`concepts/promises.md`](../../concepts/promises.md) — Async iteration.

---

## Companion sections

- `04-promises/` — Async generators, promise chains.
- `05-event-loop/` — Microtask vs macrotask scheduling.
- `10-machine-coding-patterns/` — Rate limiter, throttle.
