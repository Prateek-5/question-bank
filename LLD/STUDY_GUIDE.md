# LLD Study Guide — what to learn, in what order

> A student-facing roadmap through the **completed** LLD walkthroughs. Every LLD section is now authored, so this is the full curriculum. For authoring status and internal scores, see [`AUTHORING_LEDGER.md`](./AUTHORING_LEDGER.md).
>
> **Last updated:** 2026-06-05 · **Walkthroughs available:** 90 (19 sections, grouped into 5 parts) · **Status:** ✅ complete

## How to use this guide

- **Work part-by-part, top-to-bottom.** Parts are ordered so each builds on the patterns learned before it. Within a section, questions go **Medium → Hard** and from most-foundational to most-advanced.
- **Each walkthrough is self-contained** — it derives the design from a naive version, so you can also jump straight to any single question you're prepping for.
- The **Pattern focus** column names the main idea being drilled. The **Score** is the internal quality score (all ≥95) — treat the 100s as the cleanest reference exemplars.
- **First time doing LLD?** Start with the ⭐ **Parking lot** walkthrough (Part A) — it's the canonical teaching exemplar the whole repo is modeled on.
- **Part E (Data Structures from scratch)** is an orthogonal track — you can interleave it with the pattern work whenever you want a break from GoF patterns.

## Recommended order at a glance

| Part | Theme | Sections | Count |
|---|---|---|---:|
| **A** | Foundations — principles + modeling | SOLID Principles · Object-Oriented Design | 19 |
| **B** | Behavioral patterns (the most-asked core) | Strategy · State · Observer · Command · Template Method · Iterator · Chain of Responsibility | 45 |
| **C** | Structural & creational patterns | Composite · Decorator · Factory family · Builder · Dependency Injection · Interceptor | 7 |
| **D** | Resilience & extensibility (composite, applied) | Retry · Rule Engine · Plugin Architecture | 7 |
| **E** | Data structures from scratch (parallel track) | LLD Data Structures | 12 |

**Section sequence:** SOLID → OOD → Strategy → State → Observer → Command → Template Method → Iterator → Chain of Responsibility → Composite → Decorator → Factory → Builder → Dependency Injection → Interceptor → Retry → Rule Engine → Plugin Architecture → Data Structures.

---

# Part A — Foundations

> The design vocabulary and modeling reflexes every other part assumes.

## 1. SOLID Principles  ✅ 1 walkthrough

> The five principles you'll cite in every interview. Read this first so the terms in later sections (SRP, OCP, dependency inversion) already mean something.

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 | SOLID principles (explainer) | S/O/L/I/D with counterexamples | [SOLID_Principles_Explained](./Topics/SOLID_Principles/SOLID_Principles_Explained.md) | 100 |

## 2. Object-Oriented Design  ✅ 18 walkthroughs

> The modeling reflexes — entity extraction, composition over inheritance, SOLID in practice — that every other section relies on.

### Easier first — Medium (warm-up + core modeling)

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 ⭐ | Parking lot system | SOLID + Strategy + State | [Parking_Lot](./Topics/Object_Oriented_Design/Parking_Lot.md) | exemplar |
| 2 | Vending machine | State + Strategy (FSM) | [Vending_Machine](./Topics/Object_Oriented_Design/Vending_Machine.md) | 97 |
| 3 | Snake game | Game loop + queue | [Snake_Game](./Topics/Object_Oriented_Design/Snake_Game.md) | 99 |
| 4 | Hotel booking system | Strategy + State | [Hotel_Booking_System](./Topics/Object_Oriented_Design/Hotel_Booking_System.md) | 98 |
| 5 | Hash map from scratch | Encapsulation + generics | [Hash_Map_From_Scratch](./Topics/Object_Oriented_Design/Hash_Map_From_Scratch.md) | 100 |
| 6 | Library management system | Observer + Repository + SOLID | [Library_Management_System](./Topics/Object_Oriented_Design/Library_Management_System.md) | 100 |
| 7 | Healthcare appointment scheduling | Observer + State | [Healthcare_Appointment_Scheduling](./Topics/Object_Oriented_Design/Healthcare_Appointment_Scheduling.md) | 100 |
| 8 | Form validation library | Strategy + Composite | [Form_Validation_Library](./Topics/Object_Oriented_Design/Form_Validation_Library.md) | 100 |
| 9 | E-book reader | Observer + Strategy + Memento | [EBook_Reader](./Topics/Object_Oriented_Design/EBook_Reader.md) | 99 |

### Step up — Hard (systems-flavored modeling)

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 10 | Elevator system | Strategy + State machine | [Elevator_System](./Topics/Object_Oriented_Design/Elevator_System.md) | 100 |
| 11 | Connection pool manager | Object Pool + concurrency | [Connection_Pool_Manager](./Topics/Object_Oriented_Design/Connection_Pool_Manager.md) | 100 |
| 12 | Thread pool executor | Strategy (rejection policy) + concurrency | [Thread_Pool_Executor](./Topics/Object_Oriented_Design/Thread_Pool_Executor.md) | 100 |
| 13 | Key-value store (LSM / append log) | Storage engine modeling | [Key_Value_Store](./Topics/Object_Oriented_Design/Key_Value_Store.md) | 100 |
| 14 | Message broker (class-level) | Partitioning + consumer groups | [Message_Broker](./Topics/Object_Oriented_Design/Message_Broker.md) | 100 |
| 15 | Search engine (inverted index) | Inverted index + TF-IDF | [Search_Engine](./Topics/Object_Oriented_Design/Search_Engine.md) | 100 |
| 16 | JSON parser | Recursive descent + Visitor | [JSON_Parser](./Topics/Object_Oriented_Design/JSON_Parser.md) | 100 |
| 17 | Sudoku solver and validator | Backtracking + constraint propagation | [Sudoku_Solver](./Topics/Object_Oriented_Design/Sudoku_Solver.md) | 100 |
| 18 | Garbage collector | Strategy (mark-sweep / refcount / generational) | [Garbage_Collector](./Topics/Object_Oriented_Design/Garbage_Collector.md) | 100 |

---

# Part B — Behavioral patterns

> The most-asked family in LLD interviews. Strategy and State are the headline acts; learn them back-to-back since interviewers love testing whether you can tell them apart (**caller picks the algorithm = Strategy; the object transitions itself = State**).

## 3. Strategy Pattern  ✅ 17 walkthroughs

> "Encapsulate an algorithm behind an interface so the caller can swap it at runtime." Master this before State.

### Easier first — Medium

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 | Notification service | Strategy + Observer + Template Method | [Notification_Service](./Topics/Strategy_Pattern/Notification_Service.md) | 100 |
| 2 | Feature toggle service | Strategy (targeting rules) | [Feature_Toggle_Service](./Topics/Strategy_Pattern/Feature_Toggle_Service.md) | 100 |
| 3 | Online shopping cart | Strategy + Decorator + State | [Shopping_Cart](./Topics/Strategy_Pattern/Shopping_Cart.md) | 100 |
| 4 | Coupon / discount engine | Strategy + CoR + Decorator | [Coupon_Discount_Engine](./Topics/Strategy_Pattern/Coupon_Discount_Engine.md) | 100 |
| 5 | Car rental system | Strategy + State | [Car_Rental_System](./Topics/Strategy_Pattern/Car_Rental_System.md) | 100 |
| 6 | Media player | Strategy + State + Adapter | [Media_Player](./Topics/Strategy_Pattern/Media_Player.md) | 99 |
| 7 | Deck of cards (multi-game) | Strategy + Template Method | [Deck_Of_Cards](./Topics/Strategy_Pattern/Deck_Of_Cards.md) | 98 |
| 8 | Battleship game | Strategy (AI vs human) | [Battleship_Game](./Topics/Strategy_Pattern/Battleship_Game.md) | 98 |
| 9 | Tic-Tac-Toe (minimax) | Strategy (player AI) | [Tic_Tac_Toe](./Topics/Strategy_Pattern/Tic_Tac_Toe.md) | 100 |
| 10 | Load testing framework | Strategy (ramp / rate) | [Load_Testing_Framework](./Topics/Strategy_Pattern/Load_Testing_Framework.md) | 99 |

### Step up — Hard

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 11 | Payment processing system | Strategy + State + idempotency | [Payment_Processing](./Topics/Strategy_Pattern/Payment_Processing.md) | 99 |
| 12 | Rate limiter (4 algorithms) | Strategy (token / leaky / window) | [Rate_Limiter](./Topics/Strategy_Pattern/Rate_Limiter.md) | 100 |
| 13 | Calendar app (recurrence) | Strategy + Iterator | [Calendar_Application](./Topics/Strategy_Pattern/Calendar_Application.md) | 97 |
| 14 | Social media feed | Strategy (ranking) + Observer | [Social_Media_Feed](./Topics/Strategy_Pattern/Social_Media_Feed.md) | 100 |
| 15 | Airline reservation system | Strategy + State + inventory | [Airline_Reservation](./Topics/Strategy_Pattern/Airline_Reservation.md) | 99 |
| 16 | ETL pipeline (class-level) | Strategy + Adapter + pipeline | [ETL_Pipeline](./Topics/Strategy_Pattern/ETL_Pipeline.md) | 99 |
| 17 | Auction system (3 types) | Strategy + State + Template Method | [Auction_System](./Topics/Strategy_Pattern/Auction_System.md) | 100 |

## 4. State Pattern  ✅ 10 walkthroughs

> "The object changes its own behavior as its internal state changes." Learn it right after Strategy.

### Easier first — Medium

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 | Order management system | State + Event Sourcing | [Order_Management_System](./Topics/State_Pattern/Order_Management_System.md) | 98 |
| 2 | ATM machine | State + CoR + concurrency | [ATM_Machine](./Topics/State_Pattern/ATM_Machine.md) | 100 |
| 3 | Traffic signal control | State + Observer (FSM) | [Traffic_Signal_Control](./Topics/State_Pattern/Traffic_Signal_Control.md) | 100 |

### Step up — Hard

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 4 | State machine framework | State + generics (framework) | [State_Machine_Framework](./Topics/State_Pattern/State_Machine_Framework.md) | 100 |
| 5 | Movie ticket booking | State + seat locking | [Movie_Ticket_Booking](./Topics/State_Pattern/Movie_Ticket_Booking.md) | 100 |
| 6 | Ride-sharing application | State + Strategy + Observer | [Ride_Sharing_Application](./Topics/State_Pattern/Ride_Sharing_Application.md) | 100 |
| 7 | Food delivery system | State + Strategy + Observer | [Food_Delivery_System](./Topics/State_Pattern/Food_Delivery_System.md) | 99 |
| 8 | Workflow engine | State + CoR + Saga | [Workflow_Engine](./Topics/State_Pattern/Workflow_Engine.md) | 100 |
| 9 | Chatbot framework | State machine + Strategy | [Chatbot_Framework](./Topics/State_Pattern/Chatbot_Framework.md) | 99 |
| 10 | Regex engine (NFA) | State machine + parser | [Regex_Engine](./Topics/State_Pattern/Regex_Engine.md) | 99 |

## 5. Observer Pattern  ✅ 12 walkthroughs

> "Subjects notify a list of observers when they change." The basis of event systems and pub-sub. Start with the explainer, which also disambiguates Observer from Pub/Sub.

### Start with the concept, then Medium

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 | Observer vs Pub/Sub (explainer) | Observer vs Pub/Sub coupling | [Observer_Vs_PubSub](./Topics/Observer_Pattern/Observer_Vs_PubSub.md) | 99 |
| 2 | Config hot-reload system | Observer + Strategy | [Config_Hot_Reload](./Topics/Observer_Pattern/Config_Hot_Reload.md) | 100 |
| 3 | Email client (class-level) | Observer + Composite | [Email_Client](./Topics/Observer_Pattern/Email_Client.md) | 100 |
| 4 | Q&A platform (StackOverflow) | Observer + Strategy (reputation) | [QA_Platform](./Topics/Observer_Pattern/QA_Platform.md) | 100 |
| 5 | Auction countdown timer | Observer + time sync | [Auction_Countdown_Timer](./Topics/Observer_Pattern/Auction_Countdown_Timer.md) | 100 |
| 6 | Inventory management system | Observer + Repository + Event Sourcing | [Inventory_Management](./Topics/Observer_Pattern/Inventory_Management.md) | 100 |
| 7 | Meeting room scheduler | Observer + Builder + interval | [Meeting_Room_Scheduler](./Topics/Observer_Pattern/Meeting_Room_Scheduler.md) | 99 |
| 8 | Game lobby / matchmaking | Observer + State | [Game_Lobby](./Topics/Observer_Pattern/Game_Lobby.md) | 100 |
| 9 | Restaurant reservation system | Observer + State + scheduling | [Restaurant_Reservation](./Topics/Observer_Pattern/Restaurant_Reservation.md) | 100 |

### Step up — Hard

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 10 | Spreadsheet (formula recalc) | Observer + topo-sort + parsing | [Spreadsheet_Application](./Topics/Observer_Pattern/Spreadsheet_Application.md) | 99 |
| 11 | Pub-sub messaging system | Observer + message queue | [PubSub_Messaging_System](./Topics/Observer_Pattern/PubSub_Messaging_System.md) | 100 |
| 12 | Event-driven architecture framework | Mediator + CoR + Event Sourcing | [Event_Driven_Framework](./Topics/Observer_Pattern/Event_Driven_Framework.md) | 99 |

## 6. Command Pattern  ✅ 3 walkthroughs

> "Wrap an action as an object" — the key to undo/redo, queuing, and replay. Builds naturally on the behavioral patterns above.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Image processing pipeline | Medium | Command + Composite + lazy eval + Builder | [Image_Processing_Pipeline](./Topics/Command_Pattern/Image_Processing_Pipeline.md) | 95 |
| 2 | Chess game | Hard | Command + polymorphism | [Chess_Game](./Topics/Command_Pattern/Chess_Game.md) | 100 |
| 3 | Text editor (undo/redo) | Hard | Command + Memento + rope | [Text_Editor](./Topics/Command_Pattern/Text_Editor.md) | 100 |

## 7. Template Method  ✅ 1 walkthrough

> "Define an algorithm's skeleton in a base class; let subclasses fill in the steps." The inheritance-based sibling of Strategy.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Multiplayer card game framework | Medium | Template Method + Strategy | [Card_Game_Framework](./Topics/Template_Method/Card_Game_Framework.md) | 100 |

## 8. Iterator  ✅ 1 walkthrough

> "Expose sequential access to a collection without revealing its internals." Pairs well with Strategy (e.g. swappable shuffle).

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Music playlist manager | Medium | Iterator + Strategy (shuffle) | [Playlist_Manager](./Topics/Iterator_Pattern/Playlist_Manager.md) | 100 |

## 9. Chain of Responsibility  ✅ 1 walkthrough

> "Pass a request along a chain of handlers until one handles it." The pipeline/middleware backbone.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Logging framework | Medium | Chain of Responsibility + Observer | [Logging_Framework](./Topics/Chain_of_Responsibility/Logging_Framework.md) | 98 |

---

# Part C — Structural & creational patterns

> How objects are composed and constructed. Shorter sections — most are a single deep example.

## 10. Composite Pattern  ✅ 2 walkthroughs

> "Treat individual objects and compositions of objects uniformly" — the tree pattern.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | In-memory file system | Hard | Composite + tree + permissions | [In_Memory_File_System](./Topics/Composite_Pattern/In_Memory_File_System.md) | 100 |
| 2 | Rules engine (DSL) | Hard | Interpreter + Composite | [Rules_Engine_DSL](./Topics/Composite_Pattern/Rules_Engine_DSL.md) | 100 |

## 11. Decorator Pattern  ✅ 1 walkthrough

> "Attach responsibilities to an object dynamically by wrapping it." Contrast with Proxy (same shape, different intent).

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Caching decorator / proxy | Hard | Decorator + Proxy | [Caching_Decorator](./Topics/Decorator_Pattern/Caching_Decorator.md) | 100 |

## 12. Factory family  ✅ 1 walkthrough

> When to reach for Factory Method vs Abstract Factory vs Builder — and what breaks if you pick wrong.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Factory vs Abstract Factory vs Builder | Medium | Factory family discrimination | [Factory_Family_Comparison](./Topics/Factory_Pattern/Factory_Family_Comparison.md) | 99 |

## 13. Builder  ✅ 1 walkthrough

> "Construct a complex object step by step" via a fluent API.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | SQL query builder (fluent API) | Medium | Builder | [SQL_Query_Builder](./Topics/Builder_Pattern/SQL_Query_Builder.md) | 100 |

## 14. Dependency Injection  ✅ 1 walkthrough

> Inversion of control made concrete — lifecycles, qualified bindings, circular-dependency detection.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Dependency injection container | Hard | DI + Factory + reflection | [DI_Container](./Topics/Dependency_Injection/DI_Container.md) | 100 |

## 15. Interceptor  ✅ 1 walkthrough

> Cross-cutting behavior (auth, retries, logging) attached to a request flow without touching the caller.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | OAuth client library | Medium | Interceptor + token management | [OAuth_Client_Library](./Topics/Interceptor_Pattern/OAuth_Client_Library.md) | 100 |

---

# Part D — Resilience & extensibility

> Composite, applied designs that stitch several patterns together. Best attempted once Parts A–C feel comfortable.

## 16. Retry Pattern  ✅ 3 walkthroughs

> Fault-tolerance building blocks. Do them in order — the HTTP client at the end combines retry + circuit breaker + interceptors.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Retry framework (backoff) | Medium | Strategy + circuit breaker | [Retry_Framework](./Topics/Retry_Pattern/Retry_Framework.md) | 100 |
| 2 | Circuit breaker | Medium | State (closed / open / half-open) | [Circuit_Breaker](./Topics/Retry_Pattern/Circuit_Breaker.md) | 99 |
| 3 | HTTP client library | Medium | Interceptor + Builder + retry | [HTTP_Client_Library](./Topics/Retry_Pattern/HTTP_Client_Library.md) | 99 |

## 17. Rule Engine  ✅ 2 walkthroughs

> Policy and workflow evaluation — RBAC/ABAC, draft/publish, deny-override.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Content management system | Medium | State (draft/publish) + RBAC + Template | [Content_Management_System](./Topics/Rule_Engine/Content_Management_System.md) | 100 |
| 2 | Permission / authorization (RBAC / ABAC) | Hard | CoR + policy evaluation | [Authorization_System](./Topics/Rule_Engine/Authorization_System.md) | 99 |

## 18. Plugin Architecture  ✅ 2 walkthroughs

> Extensible hosts that load third-party code — the capstone that ties DI, lifecycle, and reflection together.

| Order | Question | Diff | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---|---:|
| 1 | Plugin architecture (lifecycle) | Hard | Plugin host + DI + service locator | [Plugin_Architecture](./Topics/Plugin_Architecture/Plugin_Architecture.md) | 100 |
| 2 | Test framework (JUnit / Jest) | Hard | Template Method + reflection | [Test_Framework](./Topics/Plugin_Architecture/Test_Framework.md) | 100 |

---

# Part E — Data structures from scratch (parallel track)

> "Implement a data structure with these guarantees" rather than "apply a design pattern." Orthogonal to Parts A–D — interleave it whenever you want. The Min-* family share one core trick (carry the running min/max alongside the data), so do them together.

## 19. LLD Data Structures  ✅ 12 walkthroughs

### Foundations — Medium

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 1 | LRU Cache O(1) | DLL + hashmap + eviction callback | [LRU_Cache](./Topics/LLD_DataStructures/LRU_Cache.md) | 100 |
| 2 | Min Stack O(1) | Auxiliary-stack invariant | [Min_Stack](./Topics/LLD_DataStructures/Min_Stack.md) | 100 |
| 3 | Min Queue O(1) | Two-stack / monotonic deque | [Min_Queue](./Topics/LLD_DataStructures/Min_Queue.md) | 99 |
| 4 | Min Deque | Monotonic deque invariant | [Min_Deque](./Topics/LLD_DataStructures/Min_Deque.md) | 100 |
| 5 | Min Heap / Min Priority Queue | Binary heap from scratch | [Min_Heap](./Topics/LLD_DataStructures/Min_Heap.md) | 100 |
| 6 | URL shortener (class-level) | Base62 + Repository | [URL_Shortener_LLD](./Topics/LLD_DataStructures/URL_Shortener_LLD.md) | 100 |

### Step up — Hard

| Order | Question | Pattern focus | Walkthrough | Score |
|---:|---|---|---|---:|
| 7 | API rate limiter middleware | Decorator/middleware + sliding window | [Rate_Limiter_Middleware](./Topics/LLD_DataStructures/Rate_Limiter_Middleware.md) | 100 |
| 8 | Type-ahead suggestion (trie) | Trie + ranking + fuzzy | [Typeahead_Suggestion](./Topics/LLD_DataStructures/Typeahead_Suggestion.md) | 100 |
| 9 | Task scheduler (DAG + retry) | Priority queue + DAG + Observer | [Task_Scheduler](./Topics/LLD_DataStructures/Task_Scheduler.md) | 99 |
| 10 | Cron job scheduler | Cron parser + priority queue + DAG | [Cron_Job_Scheduler](./Topics/LLD_DataStructures/Cron_Job_Scheduler.md) | 99 |
| 11 | Version control (simplified Git) | Content-addressable store + DAG | [Version_Control_System](./Topics/LLD_DataStructures/Version_Control_System.md) | 100 |
| 12 | Distributed queue (microservices) | Queue modeling + delivery semantics | [Distributed_Queue](./Topics/LLD_DataStructures/Distributed_Queue.md) | 100 |

---

> **What's next:** once you've worked the patterns here, move on to system design — see the HLD track (`../HLD/`), which assumes the modeling fluency this guide builds.
