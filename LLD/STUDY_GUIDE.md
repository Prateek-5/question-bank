# LLD Study Guide — what to learn, in what order

> A student-facing roadmap through the **completed** LLD walkthroughs. Only sections that already have authored answers appear here; this file grows as more sections finish. For the full authoring backlog and status, see [`AUTHORING_LEDGER.md`](./AUTHORING_LEDGER.md).
>
> **Last updated:** 2026-06-03 · **Walkthroughs available:** 55 (across 4 sections)

## How to use this guide

- **Work top-to-bottom.** Sections are ordered so each one builds on the patterns learned in the previous. Within a section, questions are ordered **Easy → Hard** and from most-foundational to most-advanced.
- **Each walkthrough is self-contained** — it derives the design from a naive version, so you can also jump straight to any single question you're prepping for.
- The **Pattern focus** column tells you the main idea being drilled. The **Score** is the internal quality score (all ≥97) — treat the 100s as the cleanest reference exemplars.
- **First time doing LLD?** Start with the ⭐ **Parking lot** walkthrough — it's the canonical teaching exemplar the whole repo is modeled on.

## Recommended section order

| # | Section | Why here | Status |
|---:|---|---|---|
| 1 | **Object-Oriented Design** | Foundations: composition vs inheritance, SOLID, the core GoF patterns. Everything else assumes this. | ✅ 18/18 |
| 2 | **Strategy Pattern** | The simplest, most-asked behavioral pattern — "swap an algorithm at runtime." | ✅ 17/17 |
| 3 | **State Pattern** | Builds directly on Strategy (its most-confused sibling). Learn them back-to-back. | ✅ 10/10 |
| 4 | **Observer Pattern** | Notifications / pub-sub. Rounds out the three core behavioral patterns. | 🚧 10/12 |

---

## 1. Object-Oriented Design  ✅ 18 walkthroughs

> Start here. These teach the modeling reflexes (entity extraction, composition, SOLID) every other section relies on.

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

## 2. Strategy Pattern  ✅ 17 walkthroughs

> "Encapsulate an algorithm behind an interface so the caller can swap it at runtime." The most common interview pattern — master it before State.

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

---

## 3. State Pattern  ✅ 10 walkthroughs

> "The object changes its own behavior as its internal state changes." Learn it right after Strategy — interviewers love testing whether you can tell them apart (caller picks = Strategy; object transitions = State).

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

---

## 4. Observer Pattern  🚧 10 of 12 walkthroughs available

> "Subjects notify a list of observers when they change." The basis of event systems and pub-sub. **Two questions in this section are still being authored** (listed at the bottom — not yet available).

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

> **Coming soon (not yet authored):** Pub-sub messaging system · Event-driven architecture framework. This section's order will be revised when they land.

---

## Sections not yet started

The following LLD sections have **no walkthroughs yet** and are intentionally omitted from this guide until they have answers: LLD_DataStructures, Command, Retry, Composite, Plugin Architecture, Rule Engine, Builder, Chain of Responsibility, Decorator, Dependency Injection, Factory, Interceptor, Iterator, SOLID Principles, Template Method. Track their progress in [`AUTHORING_LEDGER.md`](./AUTHORING_LEDGER.md).
