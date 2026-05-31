# LeetLens — LLD Questions (Categorized)

> **146 questions** from `processed.extracted_questions` (snapshot 2026-05-31).
> Buckets are listed in **pedagogical study order** — go top-down for a structured path.
> Within each bucket, questions are sorted Easy → Medium → Hard.
> Companion file: [`STUDY-GUIDE.md`](./STUDY-GUIDE.md) for the cross-category sequence.

## Bucket index (in study order)

| # | Bucket | Count | Difficulty mix | Layer |
|---|---|---:|---|---|
| 1 | [`Object-Oriented Design (general)`](#object_oriented_design) | 26 | Medium:12 · Hard:14 | Foundation — start here |
| 2 | [`SOLID Principles`](#solid_principles) | 1 | Medium:1 | Foundation — design philosophy |
| 3 | [`Data-Structure Implementations`](#lld_datastructures) | 60 | Medium:50 · Hard:10 | Foundation — implement core DS as classes |
| 5 | [`Factory Pattern`](#factory_pattern) | 1 | Medium:1 | Creational |
| 6 | [`Builder Pattern`](#builder_pattern) | 1 | Medium:1 | Creational |
| 7 | [`Strategy Pattern`](#strategy_pattern) | 17 | Medium:10 · Hard:7 | Behavioral — most common |
| 8 | [`Observer Pattern`](#observer_pattern) | 12 | Medium:9 · Hard:3 | Behavioral — high-impact |
| 9 | [`State Pattern`](#state_pattern) | 10 | Medium:3 · Hard:7 | Behavioral |
| 10 | [`Command Pattern`](#command_pattern) | 3 | Medium:1 · Hard:2 | Behavioral |
| 11 | [`Chain of Responsibility`](#chain_of_responsibility) | 1 | Medium:1 | Behavioral |
| 12 | [`Template Method`](#template_method) | 1 | Medium:1 | Behavioral |
| 13 | [`Iterator Pattern`](#iterator_pattern) | 1 | Medium:1 | Behavioral |
| 15 | [`Decorator Pattern`](#decorator_pattern) | 1 | Hard:1 | Structural |
| 16 | [`Composite Pattern`](#composite_pattern) | 2 | Hard:2 | Structural |
| 18 | [`Interceptor Pattern`](#interceptor_pattern) | 1 | Medium:1 | Architectural |
| 19 | [`Plugin Architecture`](#plugin_architecture) | 2 | Hard:2 | Architectural |
| 20 | [`Dependency Injection`](#dependency_injection) | 1 | Hard:1 | Architectural |
| 22 | [`Rule Engine / RBAC`](#rule_engine) | 2 | Medium:1 · Hard:1 | Architectural |
| 23 | [`Retry / Circuit Breaker`](#retry_pattern) | 3 | Medium:3 | Resilience |
| **Total** | | **146** | | |

---

## <a id="object_oriented_design"></a>1. Object-Oriented Design (general) — 26 questions

_Layer: **Foundation — start here**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Airbnb | Object-Oriented Design, Strategy Pattern, State Pattern, Date Range Handling | Design a hotel booking system supporting room types (single, double, suite), date-range availability checks, booking confirmation, cancellation with refund policy, and loyalty points tracking. ⚠️ also fits: `State_Pattern` · `Strategy_Pattern` |
| 2 | Medium | Amazon | Object-Oriented Design, Game Loop, Queue Data Structure, Collision Detection | Design the Snake game with a grid-based board, growing snake on food consumption, collision detection with walls and self, score tracking, and increasing speed levels. |
| 3 | Medium | Amazon | Object-Oriented Design, State Pattern, Strategy Pattern, Finite State Machine | Design a vending machine that supports multiple product types, coin/bill payment, change dispensing, inventory management, and an admin restocking interface. Handle edge cases like insufficient funds and out-of-stock ite ⚠️ also fits: `State_Pattern` · `Strategy_Pattern` |
| 4 | Medium | Amazon | Object-Oriented Design, Observer Pattern, Strategy Pattern, Memento Pattern | Design an e-book reader application: book library management, pagination/scrolling modes, bookmarks, highlights with notes, font/theme customization, reading progress sync across devices, and dictionary lookup. ⚠️ also fits: `Memento_Pattern` · `Observer_Pattern` · `Strategy_Pattern` |
| 5 | Medium | Google | Object-Oriented Design, Observer Pattern, Repository Pattern, SOLID Principles | Design a library management system supporting book cataloging, member registration, book checkout/return, fine calculation, reservation queues, and search by title/author/ISBN. ⚠️ also fits: `Observer_Pattern` · `Repository_Pattern` · `SOLID_Principles` |
| 6 | Medium | Google | Graph, Dynamic Programming | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 7 | Medium | Google | Graph, Dijkstra's algorithm | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 8 | Medium | Google | Object-Oriented Design, Hash Table, Collision Resolution, Generics | Design a hash map from scratch with support for generic key-value types, dynamic resizing, collision handling via chaining and open addressing, and custom hash function injection. |
| 9 | Medium | Google | Object-Oriented Design, SOLID Principles, Design Patterns, State Pattern | Design a parking lot system with multiple floors, different vehicle types (motorcycle, car, bus), and payment processing. Include entry/exit gates, ticket generation, and hourly rate calculation. ⚠️ also fits: `SOLID_Principles` · `State_Pattern` |
| 10 | Medium | Meta | Object-Oriented Design, Validation, Strategy Pattern, Composite Pattern | Design a form validation library supporting field-level and form-level validation, async validators (e.g., checking username availability), dependent field validation, custom error messages, and validation groups. ⚠️ also fits: `Composite_Pattern` · `Strategy_Pattern` |
| 11 | Medium | Microsoft | Object-Oriented Design, Scheduling, Observer Pattern, State Pattern | Design a healthcare appointment scheduling system with doctor availability management, patient booking, appointment types (in-person, telehealth), waiting room queue, automated reminders, and cancellation with rebooking. ⚠️ also fits: `Observer_Pattern` · `State_Pattern` |
| 12 | Medium | — | Graph | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 13 | Hard | Amazon | Object-Oriented Design, Concurrency, Thread Pool, Strategy Pattern | Design a thread pool executor with configurable core and max pool size, task queue with bounded capacity, rejection policies (abort, discard, caller-runs), and graceful shutdown. ⚠️ also fits: `Strategy_Pattern` |
| 14 | Hard | Amazon | Object-Oriented Design, LSM Tree, Append-Only Log, Compaction | Design a key-value store with support for get, put, delete, TTL-based expiration, persistence to disk (append-only log), and compaction. Model the storage engine classes. |
| 15 | Hard | Google | Object-Oriented Design, Backtracking, Constraint Propagation, Puzzle Generation | Design a Sudoku solver and validator. Model the board, implement constraint propagation, backtracking search, and provide efficient validation for rows, columns, and 3x3 boxes. Support puzzle generation with unique solut |
| 16 | Hard | Google | Cache, Data Structures | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 17 | Hard | Google | Object-Oriented Design, Inverted Index, TF-IDF, Boolean Query | Design a search engine at the class level with inverted index construction, TF-IDF scoring, boolean query support (AND, OR, NOT), phrase queries, and result pagination. Support incremental index updates. |
| 18 | Hard | Google | Object-Oriented Design, Recursive Descent Parser, Tokenizer, Visitor Pattern | Design a JSON parser from scratch that handles objects, arrays, strings, numbers, booleans, and null values. Support nested structures and provide meaningful error messages for malformed input. |
| 19 | Hard | Google | Graph, Dynamic Programming | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 20 | Hard | Google | Object-Oriented Design, Garbage Collection, Mark and Sweep, Generational GC | Design a garbage collector for a managed language runtime. Support mark-and-sweep, reference counting, generational collection, and support for finalizers. Handle root set identification and object graph traversal. |
| 21 | Hard | LinkedIn | Object-Oriented Design, Message Broker, Consumer Groups, Partitioning | Design a message broker at the class level supporting topics, queues, message persistence, consumer groups, message acknowledgment, and dead letter queue. Include message ordering guarantees within a partition. |
| 22 | Hard | Meta | Parking Lot, Distributed Systems | Design a parking lot system for a city with a large number of cars and trucks ⚠️ also fits: `LLD_DataStructures` |
| 23 | Hard | Meta | Graph, Distributed Systems | Design a parking lot system ⚠️ also fits: `LLD_DataStructures` |
| 24 | Hard | Microsoft | Object-Oriented Design, Strategy Pattern, State Machine, Scheduling Algorithms | Design an elevator system for a 40-floor building with multiple elevators, handling peak traffic, priority requests, and maintenance mode. Define the scheduling algorithm for optimal wait times. ⚠️ also fits: `State_Pattern` · `Strategy_Pattern` |
| 25 | Hard | Netflix | Object-Oriented Design, Object Pool Pattern, Concurrency, Resource Management | Design a connection pool manager supporting configurable min/max connections, connection health checking, idle timeout eviction, fair queuing for waiting clients, and graceful shutdown. |
| 26 | Hard | — | Graph Data Structure, Parking Lot | Design a parking lot system |

## <a id="solid_principles"></a>2. SOLID Principles — 1 questions

_Layer: **Foundation — design philosophy**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Microsoft | SOLID Principles, Single Responsibility, Open-Closed, Liskov Substitution | Explain the SOLID principles with real-world code examples. For each principle, provide a violation example and a corrected version. When would you intentionally deviate from these principles? |

## <a id="lld_datastructures"></a>3. Data-Structure Implementations — 60 questions

_Layer: **Foundation — implement core DS as classes**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | Object-Oriented Design, Hash Map, Doubly Linked List, Cache Eviction | Design an LRU Cache with O(1) get and put operations, configurable capacity, and eviction callback support. Implement it using a doubly linked list and hash map. ⚠️ also fits: `Object_Oriented_Design` |
| 2 | Medium | Google | Cache, LRU | Design a cache with least recently used (LRU) eviction policy |
| 3 | Medium | Google | Cache, LRU | Design LRU Cache |
| 4 | Medium | Google | Stack, Min Heap | Design a Min Deque with Synchronization (Java) |
| 5 | Medium | Google | Stack, Data Structure | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(1)) |
| 6 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(1)) |
| 7 | Medium | Google | Stack, Min Heap | Design a Min Priority Queue |
| 8 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(1)) |
| 9 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 10 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 11 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 12 | Medium | Google | Stack, Min Heap | Design a Min Queue with Synchronization (Python) |
| 13 | Medium | Google | Stack, Min Heap | Design a Min Deque with Synchronization (Python) |
| 14 | Medium | Google | Cache, Data Structures | Design LRU Cache |
| 15 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 16 | Medium | Google | Deque, Data Structure | Design a Min Deque |
| 17 | Medium | Google | Cache, Data Structure | Design LRU Cache |
| 18 | Medium | Google | Stack, Min Heap | Design a Min Queue with Synchronization (C#) |
| 19 | Medium | Google | Heap, Data Structure | Design a Min Heap |
| 20 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(1)) |
| 21 | Medium | Google | Heap, Data Structure | Design a Min Heap with Support for Push and Pop Operations (with time complexity O(log n)) |
| 22 | Medium | Google | Heap, Data Structure | Design a Min Heap with Support for Push and Pop Operations |
| 23 | Medium | Google | Stack, Min Heap | Design a Min Deque |
| 24 | Medium | Google | Stack, Min Heap | Design a Min Deque with Synchronization (C++) |
| 25 | Medium | Google | Heap, Data Structure | Design a Min Heap with Support for Push and Pop Operations (with time complexity O(log n)) |
| 26 | Medium | Google | Stack, Min Heap | Design a Min Queue with Synchronization (C++) |
| 27 | Medium | Google | Stack, Min Heap | Design a Min Stack with Synchronization |
| 28 | Medium | Google | Stack, Min Heap | Design a Min Queue |
| 29 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations |
| 30 | Medium | Google | Stack, Min Heap | Design a Min Queue with Synchronization |
| 31 | Medium | Google | Stack, Data Structure | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(log n)) |
| 32 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations |
| 33 | Medium | Google | Stack, Min Heap | Design a Min Deque with Synchronization (C#) |
| 34 | Medium | Google | Stack, Data Structure | Design a Min Stack with Support for Push and Pop Operations |
| 35 | Medium | Google | Queue, Data Structure | Design a Min Queue |
| 36 | Medium | Google | Stack, Min Heap | Design a Min Deque with Synchronization |
| 37 | Medium | Google | Stack, Data Structure | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(log n)) |
| 38 | Medium | Google | Stack, Min Heap | Design a Min Priority Queue with Synchronization (C++) |
| 39 | Medium | Google | Stack, Min Heap | Design a Min Stack |
| 40 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(1)) |
| 41 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 42 | Medium | Google | Stack, Min Heap | Design a Min Priority Queue with Synchronization (Java) |
| 43 | Medium | Google | Stack, Min Heap | Design a Min Queue with Synchronization (Java) |
| 44 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 45 | Medium | Google | Stack, Min Heap | Design a Min Priority Queue with Synchronization (Python) |
| 46 | Medium | Google | Stack, Min Heap | Design a Min Priority Queue with Synchronization (C#) |
| 47 | Medium | Google | Queue, Data Structure | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 48 | Medium | Google | Deque, Data Structure | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) |
| 49 | Medium | Google | Stack, Data Structure | Design a Min Stack |
| 50 | Medium | Microsoft | Object-Oriented Design, Hashing, Base62 Encoding, Repository Pattern | Design a URL shortener service at the class level: URL encoding/decoding, custom alias support, expiration handling, click analytics tracking, and collision resolution. ⚠️ also fits: `Object_Oriented_Design` · `Repository_Pattern` |
| 51 | Hard | Amazon | Object-Oriented Design, Priority Queue, DAG, Observer Pattern | Design a task scheduler that supports one-time and recurring tasks, priority-based execution, task dependencies (DAG), cancellation, and retry with exponential backoff. ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` · `Retry_Pattern` |
| 52 | Hard | Cloudflare | Object-Oriented Design, Sliding Window, Middleware Pattern, Decorator Pattern | Design an API rate limiter middleware that supports per-user, per-endpoint, and global rate limits using sliding window counters. Include rate limit headers in responses and support distributed deployment. ⚠️ also fits: `Decorator_Pattern` · `Object_Oriented_Design` |
| 53 | Hard | Google | Graph, Dijkstra's Algorithm | Design a distributed queue for a microservices architecture |
| 54 | Hard | Google | Graph, Dijkstra's Algorithm | Design a distributed queue for a microservices architecture |
| 55 | Hard | Google | Object-Oriented Design, Trie, Compressed Trie, Fuzzy Matching | Design a type-ahead suggestion system at the class level: trie-based prefix matching, suggestion ranking by frequency/recency/personalization, fuzzy matching for typos, and memory-efficient trie representations (compress ⚠️ also fits: `Object_Oriented_Design` |
| 56 | Hard | Google | Graph, Hash Map | Design a system for handling duplicate keys in a database |
| 57 | Hard | Google | Graph, Dijkstra's Algorithm | Design a distributed queue for a microservices architecture |
| 58 | Hard | Google | Graph, Dijkstra's Algorithm | Design a load balancing system for a web application |
| 59 | Hard | LinkedIn | Object-Oriented Design, Cron Parser, Priority Queue, DAG | Design a cron job scheduler that parses cron expressions, schedules jobs at specified intervals, handles missed executions, supports job dependencies, and provides execution history and alerting. ⚠️ also fits: `Object_Oriented_Design` |
| 60 | Hard | Microsoft | Object-Oriented Design, Tree Data Structure, DAG, Content-Addressable Storage | Design a version control system (simplified Git) supporting init, add, commit, branch, checkout, merge, diff, and log operations. Model the object store (blobs, trees, commits) and reference management. ⚠️ also fits: `Object_Oriented_Design` |

## <a id="factory_pattern"></a>5. Factory Pattern — 1 questions

_Layer: **Creational**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Microsoft | Design Patterns, Factory Pattern, Abstract Factory, Builder Pattern | Compare and contrast the Factory, Abstract Factory, and Builder design patterns. When would you use each? Implement a real-world example where using the wrong pattern leads to maintenance issues. ⚠️ also fits: `Builder_Pattern` · `Object_Oriented_Design` |

## <a id="builder_pattern"></a>6. Builder Pattern — 1 questions

_Layer: **Creational**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Microsoft | Object-Oriented Design, Builder Pattern, Fluent Interface, SQL Generation | Design a database query builder that supports SELECT, WHERE, JOIN, ORDER BY, GROUP BY, HAVING, LIMIT, and subqueries. Use the Builder pattern to provide a fluent API and generate valid SQL strings with parameterized quer ⚠️ also fits: `Object_Oriented_Design` |

## <a id="strategy_pattern"></a>7. Strategy Pattern — 17 questions

_Layer: **Behavioral — most common**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, Template Method Pattern, Enum Design | Design a deck of cards system that supports multiple card games (Poker, Blackjack, Rummy). Include deck shuffling, dealing, hand evaluation, and game-specific rule engines. ⚠️ also fits: `Object_Oriented_Design` · `Template_Method` |
| 2 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, Observer Pattern, Template Method | Design a notification service at the class level supporting multiple channels (email, SMS, push notification, in-app), template management, user preference handling, batching, and retry logic. ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` · `Retry_Pattern` · `Template_Method` |
| 3 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, Decorator Pattern, State Pattern | Design an online shopping cart with product catalog browsing, cart management (add/remove/update quantity), coupon/discount application, tax calculation, and checkout flow with order creation. ⚠️ also fits: `Decorator_Pattern` · `Object_Oriented_Design` · `State_Pattern` |
| 4 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, Grid Data Structure, Game Design | Design a Battleship game supporting grid setup, ship placement with rotation, turn-based attack system, hit/miss tracking, ship sinking detection, and game end condition. Support both human and AI players. ⚠️ also fits: `Object_Oriented_Design` |
| 5 | Medium | Amazon | Object-Oriented Design, Load Testing, Strategy Pattern, Statistics | Design a load testing framework at the class level supporting configurable user scenarios, ramp-up patterns, request rate control, response time measurement, percentile calculation (P50/P95/P99), and result reporting. ⚠️ also fits: `Object_Oriented_Design` |
| 6 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, Chain of Responsibility, Decorator Pattern | Design a coupon/discount engine supporting percentage off, flat amount off, buy-one-get-one, tiered discounts, combinable vs exclusive coupons, and usage limits per user/global. Handle the discount stacking priority. ⚠️ also fits: `Chain_of_Responsibility` · `Decorator_Pattern` · `Object_Oriented_Design` · `Rule_Engine` |
| 7 | Medium | Amazon | Object-Oriented Design, Strategy Pattern, State Pattern, Date Range | Design a car rental system with vehicle fleet management, reservation booking with date ranges, customer profiles, pricing strategies (daily, weekly, per-mile), insurance options, and late return penalty calculation. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 8 | Medium | Meta | Object-Oriented Design, Minimax Algorithm, Strategy Pattern, Game Theory | Design a Tic-Tac-Toe game supporting a configurable N x N board, two players, win condition checking (row, column, diagonal), and draw detection. Extend it to support an AI opponent using minimax. ⚠️ also fits: `Object_Oriented_Design` |
| 9 | Medium | Netflix | Object-Oriented Design, Feature Flags, Strategy Pattern, Targeting Rules | Design a feature toggle service at the class level supporting boolean flags, percentage rollouts, user segment targeting, mutual exclusion groups, and flag dependency management. Include an SDK for client integration. ⚠️ also fits: `Object_Oriented_Design` |
| 10 | Medium | Spotify | Object-Oriented Design, Strategy Pattern, State Pattern, Adapter Pattern | Design a media player application supporting multiple audio/video formats, playlist management, playback controls (play, pause, seek, speed), equalizer settings, and subtitle handling. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 11 | Hard | Google | Object-Oriented Design, Strategy Pattern, Iterator Pattern, Timezone Handling | Design a calendar application supporting event creation with recurrence rules (daily, weekly, monthly, custom), conflict detection, timezone handling, shared calendars, and event reminders. ⚠️ also fits: `Iterator_Pattern` · `Object_Oriented_Design` |
| 12 | Hard | Google | Object-Oriented Design, Strategy Pattern, State Pattern, Inventory Management | Design an airline reservation system with flight search, seat selection (economy, business, first class), booking with passenger details, cancellation policies, frequent flyer program, and overbooking management. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 13 | Hard | Meta | Object-Oriented Design, Strategy Pattern, Observer Pattern, Feed Ranking | Design a social media feed system at the class level with post creation (text, image, video), like/comment/share actions, follow/unfollow, and a feed generation algorithm (chronological and ranked). ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` |
| 14 | Hard | Netflix | Object-Oriented Design, Pipeline Pattern, Strategy Pattern, Adapter Pattern | Design a data validation and transformation pipeline (ETL at class level) that reads from multiple sources, applies configurable transformations, validates data against schemas, and writes to multiple sinks. Support erro ⚠️ also fits: `Object_Oriented_Design` |
| 15 | Hard | Stripe | Object-Oriented Design, Strategy Pattern, Token Bucket, Sliding Window | Design a rate limiter class supporting fixed window, sliding window, token bucket, and leaky bucket algorithms. It should be configurable per-client and support distributed usage with a shared store. ⚠️ also fits: `LLD_DataStructures` · `Object_Oriented_Design` |
| 16 | Hard | Stripe | Object-Oriented Design, Strategy Pattern, State Pattern, Idempotency | Design a payment processing system supporting multiple payment methods (credit card, debit card, UPI, wallet), transaction lifecycle management, refund handling, idempotency, and fraud detection hooks. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 17 | Hard | eBay | Object-Oriented Design, Strategy Pattern, State Pattern, Template Method | Design an auction system supporting English (ascending), Dutch (descending), and sealed-bid auctions. Include bid validation, time-based auction closing, winner determination, and anti-sniping extensions. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` · `Template_Method` |

## <a id="observer_pattern"></a>8. Observer Pattern — 12 questions

_Layer: **Behavioral — high-impact**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | Object-Oriented Design, Observer Pattern, Repository Pattern, Event Sourcing | Design an inventory management system for a warehouse with product tracking, stock level alerts, batch operations, multi-warehouse transfer, and barcode/SKU management. ⚠️ also fits: `Event_Sourcing` · `Object_Oriented_Design` · `Repository_Pattern` |
| 2 | Medium | Google | Object-Oriented Design, Interval Scheduling, Observer Pattern, Builder Pattern | Design a meeting room scheduler for an office building. Support room search by capacity and amenities, booking with conflict detection, recurring meetings, and integration with calendar notifications. ⚠️ also fits: `Builder_Pattern` · `Object_Oriented_Design` |
| 3 | Medium | Google | Design Patterns, Observer Pattern, Pub/Sub, Coupling | Explain the Observer pattern vs Pub/Sub pattern with concrete examples. When would you use each? What are the coupling implications? Implement both and discuss memory leak risks with event listeners. ⚠️ also fits: `Object_Oriented_Design` |
| 4 | Medium | Google | Object-Oriented Design, Observer Pattern, Composite Pattern, Search | Design an email client at the class level supporting compose, send, receive, folder management (inbox, sent, drafts, trash, custom), search, attachments, and email threading/conversation view. ⚠️ also fits: `Composite_Pattern` · `Object_Oriented_Design` |
| 5 | Medium | Microsoft | Object-Oriented Design, Observer Pattern, Strategy Pattern, Reputation System | Design a stack overflow-like Q&A platform at the class level with question posting, answering, voting (upvote/downvote), accepted answer marking, tagging, reputation system, and badge awarding. ⚠️ also fits: `Object_Oriented_Design` · `Strategy_Pattern` |
| 6 | Medium | Netflix | Object-Oriented Design, Observer Pattern, Strategy Pattern, Hot Reload | Design a configuration hot-reload system for a running application. Support file-based and remote config sources, change detection, validation before applying, rollback on error, and notifying dependent components of cha ⚠️ also fits: `Object_Oriented_Design` · `Strategy_Pattern` |
| 7 | Medium | Riot Games | Object-Oriented Design, Matchmaking, Observer Pattern, State Pattern | Design a multi-player online game lobby system supporting room creation, player matchmaking by skill level, ready-check mechanism, in-lobby chat, and game session initialization. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 8 | Medium | Uber | Object-Oriented Design, Observer Pattern, State Pattern, Scheduling | Design a restaurant reservation system with table management, time-slot booking, party size matching, waitlist management, and cancellation with notification. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 9 | Medium | eBay | Object-Oriented Design, Time Synchronization, Observer Pattern, Real-time | Design an online auction countdown timer system with bid extension on last-minute bids, synchronized time across clients, server-authoritative time, and handling clock drift between client and server. ⚠️ also fits: `Object_Oriented_Design` |
| 10 | Hard | Google | Object-Oriented Design, Observer Pattern, Message Queue, Pub-Sub | Design a publish-subscribe messaging system with topic-based routing, durable subscriptions, message ordering guarantees, acknowledgment, and dead letter queue support. ⚠️ also fits: `Object_Oriented_Design` |
| 11 | Hard | Google | Object-Oriented Design, Observer Pattern, Topological Sort, Expression Parsing | Design a spreadsheet application supporting cell value and formula input, formula evaluation with cell references (A1, B2), circular dependency detection, and auto-recalculation on cell updates. ⚠️ also fits: `LLD_DataStructures` · `Object_Oriented_Design` |
| 12 | Hard | Netflix | Object-Oriented Design, Event Sourcing, Mediator Pattern, Chain of Responsibility | Design an event-driven architecture framework with event bus, event sourcing, handlers, middleware chain, and dead letter queue. Support sync and async event processing. ⚠️ also fits: `Chain_of_Responsibility` · `Event_Sourcing` · `Object_Oriented_Design` |

## <a id="state_pattern"></a>9. State Pattern — 10 questions

_Layer: **Behavioral**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | Object-Oriented Design, State Pattern, Event Sourcing, Payment Integration | Design an order management system supporting order creation, status tracking (placed, confirmed, preparing, shipped, delivered, cancelled, returned), payment integration, refund processing, and order history with paginat ⚠️ also fits: `Event_Sourcing` · `Object_Oriented_Design` |
| 2 | Medium | Goldman Sachs | Object-Oriented Design, State Pattern, Chain of Responsibility, Concurrency | Design an ATM machine supporting cash withdrawal (multiple denominations), balance inquiry, mini statement, PIN change, fund transfer, and daily withdrawal limits. Handle concurrent access to the same account. ⚠️ also fits: `Chain_of_Responsibility` · `Object_Oriented_Design` |
| 3 | Medium | Google | Object-Oriented Design, State Pattern, Observer Pattern, Finite State Machine | Design a traffic signal control system for a 4-way intersection supporting vehicle detection, pedestrian crossing, emergency vehicle priority override, and configurable timing patterns. ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` |
| 4 | Hard | Amazon | Object-Oriented Design, State Pattern, Locking Mechanism, Seat Selection Algorithm | Design a movie ticket booking system like BookMyShow with theater/screen management, seat selection with real-time locking, showtime scheduling, pricing tiers, and booking confirmation with QR code generation. ⚠️ also fits: `Object_Oriented_Design` |
| 5 | Hard | DoorDash | Object-Oriented Design, State Pattern, Strategy Pattern, Observer Pattern | Design a food delivery system like DoorDash at the class level with restaurant onboarding, menu management, order placement, delivery assignment based on proximity/availability, real-time order tracking, and review syste ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` · `Strategy_Pattern` |
| 6 | Hard | Google | Object-Oriented Design, State Pattern, Generics, Framework Design | Design a state machine framework that supports state definition, transition rules, guards/conditions, entry/exit actions, hierarchical states, and event-driven transitions. Make it generic and reusable. ⚠️ also fits: `Object_Oriented_Design` · `Plugin_Architecture` |
| 7 | Hard | Google | Object-Oriented Design, NFA, State Machine, Parser | Design a regex engine that supports literal characters, dot (any character), star (*), plus (+), question mark (?), character classes ([abc]), and grouping with parentheses. Implement using NFA construction and simulatio ⚠️ also fits: `Object_Oriented_Design` |
| 8 | Hard | Google | Object-Oriented Design, State Machine, Strategy Pattern, NLP | Design a chat bot framework supporting intent recognition, entity extraction, conversation state management, context tracking across turns, fallback handling, and integration with external APIs for fulfillment. ⚠️ also fits: `Object_Oriented_Design` · `Plugin_Architecture` · `Strategy_Pattern` |
| 9 | Hard | Netflix | Object-Oriented Design, State Pattern, Chain of Responsibility, Saga Pattern | Design a workflow engine supporting sequential and parallel task execution, conditional branching, error handling with compensation, task timeout, and workflow versioning. ⚠️ also fits: `Chain_of_Responsibility` · `LLD_DataStructures` · `Object_Oriented_Design` |
| 10 | Hard | Uber | Object-Oriented Design, State Pattern, Strategy Pattern, Observer Pattern | Design a ride-sharing application at the class level with driver/rider registration, ride matching based on proximity, fare estimation, ride lifecycle management (request, match, pickup, trip, dropoff, payment), and rati ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` · `Strategy_Pattern` |

## <a id="command_pattern"></a>10. Command Pattern — 3 questions

_Layer: **Behavioral**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Adobe | Object-Oriented Design, Pipeline Pattern, Lazy Evaluation, Command Pattern | Design an image processing pipeline supporting operations like resize, crop, rotate, flip, grayscale, blur, and watermark. Operations should be composable, lazily evaluated, and support both single images and batch proce ⚠️ also fits: `Object_Oriented_Design` |
| 2 | Hard | Amazon | Object-Oriented Design, Inheritance, Polymorphism, Command Pattern | Design a chess game with all standard rules including castling, en passant, pawn promotion, check, checkmate, and stalemate detection. Model the board, pieces, moves, and game state. ⚠️ also fits: `Object_Oriented_Design` |
| 3 | Hard | Google | Object-Oriented Design, Command Pattern, Rope Data Structure, Memento Pattern | Design a text editor supporting insert, delete, cursor movement, undo/redo operations, copy/paste, and find/replace. Use appropriate data structures for efficient text manipulation. ⚠️ also fits: `Memento_Pattern` · `Object_Oriented_Design` |

## <a id="chain_of_responsibility"></a>11. Chain of Responsibility — 1 questions

_Layer: **Behavioral**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Netflix | Object-Oriented Design, Chain of Responsibility, Observer Pattern, Singleton Pattern | Design a logging framework supporting multiple log levels (DEBUG, INFO, WARN, ERROR, FATAL), multiple output sinks (console, file, remote), structured logging, log rotation, and async writes. ⚠️ also fits: `Object_Oriented_Design` · `Observer_Pattern` · `Singleton_Pattern` |

## <a id="template_method"></a>12. Template Method — 1 questions

_Layer: **Behavioral**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | Object-Oriented Design, Template Method Pattern, Strategy Pattern, Framework Design | Design a multiplayer card game framework that supports creating different card games (Poker, Blackjack, UNO). Support turn management, hand management, deck operations, scoring rules, and game-over detection. Use the Tem ⚠️ also fits: `Object_Oriented_Design` · `Plugin_Architecture` · `Strategy_Pattern` |

## <a id="iterator_pattern"></a>13. Iterator Pattern — 1 questions

_Layer: **Behavioral**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Spotify | Object-Oriented Design, Iterator Pattern, Strategy Pattern, Linked List | Design a music streaming playlist manager supporting playlist CRUD, song ordering, shuffle (Fisher-Yates), repeat modes (off, one, all), collaborative playlists, and listening history tracking. ⚠️ also fits: `LLD_DataStructures` · `Object_Oriented_Design` · `Strategy_Pattern` |

## <a id="decorator_pattern"></a>15. Decorator Pattern — 1 questions

_Layer: **Structural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Amazon | Object-Oriented Design, Proxy Pattern, Decorator Pattern, Caching | Design a caching decorator/proxy that wraps any service call with configurable caching. Support TTL, cache invalidation patterns (write-through, write-behind), cache-aside, and cache warming. Handle thundering herd probl ⚠️ also fits: `Object_Oriented_Design` |

## <a id="composite_pattern"></a>16. Composite Pattern — 2 questions

_Layer: **Structural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Dropbox | Object-Oriented Design, Composite Pattern, Tree Data Structure, Permission Model | Design an in-memory file system supporting directories, files, file content read/write, move, copy, and permission management (read, write, execute for owner, group, others). ⚠️ also fits: `Object_Oriented_Design` |
| 2 | Hard | Stripe | Object-Oriented Design, Interpreter Pattern, Composite Pattern, Rule Engine | Design a rules engine that evaluates business rules defined in a DSL or configuration. Support AND/OR/NOT composition, comparison operators, dynamic fact resolution, rule priority, and short-circuit evaluation. ⚠️ also fits: `Object_Oriented_Design` · `Rule_Engine` |

## <a id="interceptor_pattern"></a>18. Interceptor Pattern — 1 questions

_Layer: **Architectural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Microsoft | Object-Oriented Design, OAuth, PKCE, Token Management | Design an OAuth client library supporting authorization code flow with PKCE, token storage, automatic token refresh, intercepting HTTP requests to attach tokens, and handling concurrent token refresh races. ⚠️ also fits: `Object_Oriented_Design` |

## <a id="plugin_architecture"></a>19. Plugin Architecture — 2 questions

_Layer: **Architectural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Google | Object-Oriented Design, Framework Design, Template Method, Reflection | Design a test framework (like JUnit/Jest) supporting test discovery, setup/teardown hooks (before/after each/all), assertions, test suites, parameterized tests, mocking support, and test result reporting. ⚠️ also fits: `Object_Oriented_Design` · `Template_Method` |
| 2 | Hard | Microsoft | Object-Oriented Design, Plugin Architecture, Dependency Injection, Service Locator | Design a plugin architecture for an application where third-party developers can add features. Support plugin discovery, lifecycle management (load, enable, disable, unload), dependency resolution, and sandboxed executio ⚠️ also fits: `Dependency_Injection` · `Object_Oriented_Design` |

## <a id="dependency_injection"></a>20. Dependency Injection — 1 questions

_Layer: **Architectural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Google | Object-Oriented Design, Dependency Injection, Reflection, Singleton Pattern | Design a dependency injection container supporting constructor injection, field injection, singleton and transient lifecycles, circular dependency detection, and named/qualified bindings. ⚠️ also fits: `Factory_Pattern` · `Object_Oriented_Design` · `Singleton_Pattern` |

## <a id="rule_engine"></a>22. Rule Engine / RBAC — 2 questions

_Layer: **Architectural**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Microsoft | Object-Oriented Design, Versioning, RBAC, Template Pattern | Design a content management system (CMS) supporting page creation, rich text editing, media management, versioning with draft/publish workflow, role-based access control, and template rendering. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 2 | Hard | Google | Object-Oriented Design, RBAC, ABAC, Chain of Responsibility | Design a permission/authorization system supporting role-based access control (RBAC), attribute-based access control (ABAC), permission inheritance, and policy evaluation with deny-override. ⚠️ also fits: `Chain_of_Responsibility` · `Object_Oriented_Design` |

## <a id="retry_pattern"></a>23. Retry / Circuit Breaker — 3 questions

_Layer: **Resilience**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Netflix | Object-Oriented Design, Retry Pattern, Strategy Pattern, Circuit Breaker | Design a retry framework with support for fixed delay, exponential backoff with jitter, linear backoff, and custom retry policies. Include retry budget (max retries per time window), retryable exception classification, a ⚠️ also fits: `Object_Oriented_Design` · `Strategy_Pattern` |
| 2 | Medium | Netflix | Object-Oriented Design, Circuit Breaker, State Pattern, Resilience Pattern | Design a circuit breaker pattern implementation supporting closed, open, and half-open states, configurable failure thresholds, timeout duration, and health check probing. Integrate with a retry mechanism. ⚠️ also fits: `Object_Oriented_Design` · `State_Pattern` |
| 3 | Medium | Netflix | Object-Oriented Design, Interceptor Pattern, Builder Pattern, Retry Pattern | Design an HTTP client library with request/response interceptors, automatic retry with backoff, timeout handling, connection pooling, request cancellation, and response caching. Make it composable via middleware. ⚠️ also fits: `Builder_Pattern` · `Interceptor_Pattern` · `Object_Oriented_Design` |
