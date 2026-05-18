# Coverage Map — JS + Backend Interview Question Bank

> A senior-engineer-grade audit of which patterns/verticals are covered, which are gap-filling, and which are still pending.
> Goal: **No vertical or pattern is unexplored. No surprises in the interview.**

Status legend:
- `EXISTS` — file already present in the repo
- `ADD` — to be created (gap fill)
- `ENHANCE` — existing file that needs pedagogical-layer enhancement

---

## JavaScript — `javascript-interview-prep/questions/`

### 01-hoisting (target: ~18 files, existing 12)

EXISTS: hoisting-in-javascript, hoisting-and-scoping, var-hoisting-output, var-in-block, hoisting-in-try-catch, function-declaration-vs-expression-hoisting, class-hoisting, func-expr-in-conditional, tdz-let-const, let-vs-var-differences, let-in-for-loop-binding, es-module-live-bindings

ADD:
- tdz-with-default-parameter
- class-static-block-hoisting
- named-fn-expression-binding
- import-vs-require-hoisting
- typeof-on-tdz-variable
- circular-import-live-binding-quiz

### 02-closures (target: ~22 files, existing 15)

EXISTS: counter, counter-ii, create-incrementer, create-hello-world, to-be-or-not-to-be, allow-one-function-call, once-with-cached-return, memoize-with-ttl, partial-application, curry-via-closures, module-pattern-iife, private-data-counter, loop-closure-var-let, setinterval-stale-closure, closure-memory-leak-dom

ADD:
- closure-with-cancel-token
- memoize-with-deep-equality
- iife-async-bootstrap
- factory-with-injected-deps
- ring-buffer-via-closure
- closure-as-state-machine
- closure-vs-private-class-field-comparison

### 03-prototype (target: ~22 files, existing 14)

EXISTS: prototype-chain-inheritance, this-keyword-nodejs, hasownproperty-vs-in, instanceof-polyfill, polyfill-bind, polyfill-call-apply, polyfill-new, object-create-polyfill, extends-super-implementation, class-to-prototype-desugar, differences-between-two-objects, method-chaining-builder, array-prototype-last, tostring-symbol-tag-override

ADD:
- symbol-iterator-on-class
- mixin-composition-pattern
- decorator-basics-legacy
- private-static-fields
- getter-setter-via-prototype
- reflect-construct-vs-new
- object-setprototypeof-perf-trap
- defineproperty-vs-assignment

### 04-promises (target: ~28 files, existing 20)

EXISTS: build-promise-from-scratch, promise-all-polyfill, promise-allsettled-polyfill, promise-any-polyfill, promise-race-polyfill, promise-finally-polyfill, promise-pool, promise-time-limit, promisify-node-callback, retry-with-backoff, sequential-vs-parallel-async-map, sleep, fetch-with-abort, add-two-promises, async-filter, async-reduce, async-memoize, cache-with-time-limit, deferred-with-resolvers, priority-async-queue

ADD:
- abortcontroller-fanout
- async-generator-producer
- top-level-await-deadlock-quiz
- microtask-drainer
- async-mutex
- async-semaphore
- dataloader-batch-cache
- structured-concurrency-primitive

### 05-event-loop (target: ~22 files, existing 15)

EXISTS: predict-mixed-async-output, microtask-macrotask-order, nodejs-event-loop-phases, setimmediate-vs-settimeout-in-io, nexttick-vs-setimmediate, nexttick-starvation, queuemicrotask-deep-dive, messagechannel-microtask, top-level-await-modules, event-loop-concurrency, async-hooks-basics, worker-threads-vs-event-loop, cancellable-function, timeout-cancellation, interval-cancellation

ADD:
- broadcastchannel-fanout
- postmessage-roundtrip
- requestidlecallback-scheduling
- atomics-wait-notify-intuition
- worker-pool-implementation
- structured-clone-cost
- microtask-starvation-recipes

### 06-streams (target: ~20 files, existing 12)

EXISTS: readable-stream-push, writable-stream-implementation, transform-line-parser, stream-pipeline-error-handling, stream-pipeline-lab, pipeline-error-propagation, backpressure-demo, async-iterator-pagination, callback-api-to-async-iterator, custom-iterator, fibonacci-generator, generator-pipeline

ADD:
- web-streams-readable
- web-streams-transform
- fetch-response-async-iter
- csv-parser-via-transform
- ndjson-splitter
- throttled-stream
- stream-to-buffer-with-limits
- file-line-reader-with-backpressure

### 07-arrays (target: ~22 files, existing 15)

EXISTS: polyfill-map, polyfill-filter, polyfill-reduce, polyfill-some-every, polyfill-find-findindex, polyfill-flat, array-dedup, array-set-ops, chunk-array, zip-unzip, sort-by-multiple-keys, stable-sort-discussion, move-zeros-in-place, lodash-reduce, math-array-ops

ADD:
- typed-array-basics
- holey-vs-packed-arrays
- structured-clone-vs-spread
- group-and-partition
- transpose-matrix
- rotate-array
- sliding-window-helper
- find-runs

### 08-maps-sets (target: ~20 files, existing 13)

EXISTS: lru-cache-with-map, two-sum-map, group-by, group-anagrams, first-non-repeating-char, weakmap-memoize, ttl-map, cache-invalidate-by-tag, set-operations-polyfill, object-vs-map-vs-set, object-deep-diff, is-object-empty, convert-object-to-json-string

ADD:
- weakref-finalization-registry
- json-with-map-replacer
- composite-key-strategies
- multiset-counter
- bloom-filter
- ordered-map-insertion-order-quiz
- map-vs-record-and-tuple

### 09-recursion (target: ~22 files, existing 13)

EXISTS: flatten-array-simple, flatten-deeply-nested-array, flatten-with-depth, nested-array-generator-codedamn, nested-array-generator-leetcode, deep-clone-with-cycles, tree-bfs-dfs, merge-sort, quick-sort, climbing-stairs-memoized, generate-parentheses, permutations, power-set

ADD:
- trampoline-pattern
- iterative-from-recursive
- mutual-recursion-even-odd
- recursive-descent-parser
- json-path-resolver
- deep-merge-with-cycles
- directory-walk-async
- tree-zipper-basics
- backtracking-template

### 10-machine-coding-patterns (target: ~38 files, existing 25)

EXISTS: debounce, throttle, memoize, memoize-ii, once, curry, function-composition, async-compose-pipe, bind-polyfill, deep-clone-with-cycles, event-emitter, pub-sub, observable-subject, lru-cache, rate-limiter-token-bucket, cancellable-promise-wrapper, dependency-injection-container, circular-buffer, min-heap-priority-queue, scheduler-idle-callback, trie, set-polyfill, json-parse-recursive-descent, json-stringify-polyfill, mini-state-machine

ADD:
- circuit-breaker
- async-semaphore
- async-pool
- dataloader-batch-cache
- batched-request-coalescer
- leader-election-toy
- saga-orchestration-toy
- request-deduplication
- idempotency-wrapper
- retry-with-jitter-and-budget
- cache-stampede-single-flight
- bfs-with-concurrency
- bloom-filter

---

## Backend — `backend-data-prep/questions/` (NEW)

### sql/ (target: ~28 files)

ADD:
- join-types-quiz, self-join, anti-join, semi-join, lateral-join
- group-by-with-rollup-cube
- having-vs-where
- null-three-valued-logic
- count-star-vs-count-col
- window-running-totals
- window-rank-dense-rank
- recursive-cte-org-chart
- pivot-unpivot-drill
- query-rewrite-for-index
- leftmost-prefix-puzzle
- function-on-indexed-column-trap
- explain-analyze-reading
- nested-loop-vs-hash-vs-merge-join-recognition
- partial-index-design
- covering-index-design
- index-only-scan-conditions
- exists-vs-in-vs-join
- top-n-per-group
- gaps-and-islands
- median-via-window
- pagination-with-keyset
- soft-delete-with-partial-index
- jsonb-query-design
- skewed-data-and-statistics
- materialized-view-vs-cte

### nosql/ (target: ~25 files)

ADD:
- mongo-embed-vs-reference-shopping-cart
- mongo-schema-for-chat
- mongo-schema-for-social-feed
- mongo-aggregation-pipeline-drill
- mongo-shard-key-design
- mongo-transactional-rollback
- mongo-change-streams-fanout
- mongo-time-series-collection-design
- dynamodb-partition-key-design
- dynamodb-sort-key-patterns
- dynamodb-gsi-vs-lsi
- dynamodb-hot-partition-fix
- dynamodb-single-table-vs-multi-table
- dynamodb-adjacency-list
- cassandra-partition-key-design
- cassandra-clustering-key-ordering
- cassandra-tombstone-trap
- cassandra-time-series-rotation
- cassandra-quorum-math-drill
- nosql-vs-sql-decision
- secondary-index-tradeoffs
- denormalization-budget
- multi-region-active-active-tradeoffs

### caching/ (target: ~22 files)

ADD:
- cache-aside-pattern
- write-through-vs-write-back
- read-through-cache
- refresh-ahead-cache
- cache-stampede-single-flight
- ttl-jitter-design
- cache-key-design-rules
- double-deletion-problem
- write-around-pattern
- cdn-vs-app-vs-redis-cache-layering
- redis-redlock-distributed-lock
- redis-fencing-token
- rate-limiter-fixed-window
- rate-limiter-sliding-window-log
- rate-limiter-sliding-window-counter
- rate-limiter-token-bucket
- rate-limiter-leaky-bucket
- session-store-design
- shopping-cart-cache-design
- hot-key-mitigation
- consistent-hashing-cache-keys
- cache-warm-up-strategies

### orm/ (target: ~20 files)

ADD:
- detect-n-plus-1
- eager-load-vs-join-vs-batch
- transactional-scope-design
- optimistic-locking-version-column
- pessimistic-locking-select-for-update
- dirty-tracking-edge-cases
- migration-without-downtime
- expand-then-contract-pattern
- backwards-compatible-schema-change
- soft-delete-with-orm-quirk
- bulk-insert-orm-trap
- raw-sql-escape-hatch
- repository-vs-active-record
- unit-of-work-design
- session-lifecycle-pitfalls
- prisma-vs-typeorm-decision
- hibernate-l1-l2-cache-quiz
- sqlalchemy-session-scope-quiz
- multi-tenant-orm-strategy
- audit-log-via-orm-hook

### transactions-concurrency/ (target: ~22 files)

ADD:
- identify-isolation-level
- dirty-read-scenario
- non-repeatable-read-scenario
- phantom-read-scenario
- lost-update-scenario
- write-skew-scenario
- double-booking-prevention
- idempotency-key-design
- optimistic-vs-pessimistic-decision
- mvcc-version-chain-walkthrough
- deadlock-construction
- deadlock-resolution-strategies
- 2pl-vs-mvcc-comparison
- advisory-lock-use-cases
- transactional-outbox
- two-phase-commit-walkthrough
- saga-vs-2pc
- savepoint-usage
- read-uncommitted-trap
- skip-locked-job-queue
- gap-lock-vs-next-key-lock
- transaction-retry-loop

### system-design/ (target: ~25 files)

ADD:
- url-shortener
- chat-system
- news-feed
- ride-sharing
- distributed-rate-limiter
- notification-system
- search-autocomplete
- payments-ledger
- multi-tenancy-architecture
- file-storage-s3-like
- video-streaming
- ads-counter
- realtime-leaderboard
- distributed-cron
- live-comments
- email-service
- url-crawler
- twitter-tweet-fanout
- instagram-explore
- e-commerce-inventory
- ticket-booking-concurrency
- recommendation-feed
- pastebin-clone
- typeahead-suggestions
- analytics-pipeline

### messaging/ (target: ~18 files)

ADD:
- at-least-once-vs-exactly-once
- transactional-outbox
- inbox-pattern-idempotent-consumer
- kafka-partition-design
- kafka-consumer-group-rebalance
- kafka-ordering-guarantees
- dlq-design
- retry-topic-pattern
- fan-out-pattern
- saga-orchestration-vs-choreography
- backpressure-in-messaging
- message-ordering-strategies
- delivery-semantics-comparison
- poison-message-handling
- compaction-vs-retention
- broker-vs-broker-less-decision
- pub-sub-vs-queue
- schema-evolution-with-registry

### distributed-systems/ (target: ~20 files)

ADD:
- leader-election-bully-algorithm
- leader-election-raft-intuition
- raft-vs-paxos-intuition
- consistent-hashing-walkthrough
- vector-clocks
- crdts-introduction
- gossip-protocol-intuition
- hinted-handoff
- read-repair
- anti-entropy
- 2pc-vs-3pc
- quorum-math-drills
- linearizability-vs-serializability
- causal-consistency-quiz
- split-brain-prevention
- clock-skew-and-truetime
- lamport-timestamps
- consensus-on-membership
- failure-detector-design
- byzantine-vs-crash-fault-models

### observability/ (target: ~16 files)

ADD:
- distributed-tracing-primitives
- correlation-ids-and-baggage
- structured-logging-patterns
- log-levels-and-sampling
- metrics-types-counter-gauge-histogram
- red-method-vs-use-method
- slo-sli-error-budget
- alert-design-fatigue-prevention
- on-call-debug-drill-cpu-spike
- on-call-debug-drill-latency-tail
- on-call-debug-drill-disk-fill
- on-call-debug-drill-deadlock
- on-call-debug-drill-broken-replica
- opentelemetry-concepts
- prometheus-scrape-design
- log-tracing-metric-correlation

---

## Conventions for new question files (same as JS existing format)

Every new file follows this 11-section structure plus the new pedagogical layers:

```
# <Problem Name>

## Source / Origin

## Why this question matters in interviews

## Concepts involved  (syntax / runtime / edge cases / traps)

## Mental Model           ← NEW pedagogical layer
## Why interviewers care  ← NEW pedagogical layer
## Common beginner confusion  ← NEW pedagogical layer

## Brute force approach

## Optimal approach

## Solution (language)

## Step-by-step dry run

## How to think aloud in the interview  ← NEW pedagogical layer

## Important takeaways

## Variants

## Revision notes
```

ASCII diagrams used wherever they help intuition.
