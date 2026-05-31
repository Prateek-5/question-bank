# Parking Lot — LLD Walkthrough

> **Difficulty:** Medium · **Time:** ~40 min · **Pattern focus:** Strategy (pricing) + Factory (spot/vehicle) + State (ticket lifecycle)
>
> **Problem source(s):** representative of multiple LeetLens rows in [`./EXTRACTED_QUESTIONS.md`](./EXTRACTED_QUESTIONS.md). The most canonical LLD interview question.

---

## How to use this file

Paced for a candidate seeing parking lot for the first time. Reading time: ~30 minutes if you sketch the class diagram by hand. **The lesson: how to identify variability points, then map each one to a distinct pattern — instead of inheriting your way out of the problem.**

**Map of this file (14 sections):**

1. Problem statement + clarifying questions
2. Plain-English restatement
3. Why this matters
4. Mental model
5. Try it yourself first
6. Entity & verb extraction
7. Variability points
8. Pattern choice + alternatives
9. UML class diagram
10. Skeleton code (TypeScript)
11. Key flow — sequence diagram
12. Extensibility discussion
13. Common confusion + traps
14. Anti-patterns + how to think aloud + self-check

---

## 1. Problem statement + clarifying questions

**Prompt (typical phrasing):** "Design a parking lot system. It should allow vehicles to enter, be assigned a spot, get a ticket, and pay on exit."

**Clarifying questions to ask the interviewer BEFORE drawing anything:**

1. **Vehicle types?** Just cars, or motorcycles + trucks + EVs (with charging)?
2. **Spot types?** Compact / regular / large / handicapped / EV? Can a small vehicle use a large spot?
3. **Multi-floor?** Single lot or multi-floor garage? (Affects spot indexing.)
4. **Pricing model?** Flat hourly, tiered (first hour free), peak/off-peak, monthly subscriber?
5. **Payment methods?** Cash at exit, credit card, app pre-pay? Do all need supporting today?
6. **Entry/exit gates?** One gate or multiple? Does spot assignment happen at entry or is it find-your-own?
7. **Capacity display?** Real-time spot-count display per floor at entry?
8. **Concurrency?** Multiple vehicles entering simultaneously — do we need to worry about two getting assigned the same spot?

**Assumptions if interviewer dodges:** multi-floor garage, multiple vehicle/spot types, tiered pricing, credit-card payment at exit, system assigns the closest free spot, single-threaded for now (we'll discuss concurrency in extensibility §12).

---

## 2. Plain-English restatement

We're building the software that runs a multi-floor garage. The system must: track which spots are occupied, assign a vehicle to a compatible free spot when it arrives, issue a ticket, calculate the bill on exit based on time + spot type + applicable discounts, accept payment, and release the spot. The design must accommodate adding new vehicle types, new pricing rules, and new payment methods WITHOUT rewriting the core flow.

---

## 3. Why this matters

This is the #1 interview LLD question across FAANG / unicorn / mid-stage companies. It looks simple but tests: do you reach for inheritance everywhere (a beginner reflex), or do you correctly use composition + Strategy for things that vary, and inheritance only for genuine "is-a" relationships? The discrimination between Strategy / State / Template Method shows up here. Most candidates write a working solution; the senior bar is in defending the choices.

---

## 4. Mental model

A garage is a **collection of slots** + a **rule-book**. The slots are basically a 2D grid (floor × position). The rule-book has three rule families that change independently: **which slot can hold which vehicle** (assignment), **how much to charge** (pricing), and **how the ticket transitions** (states: ACTIVE → PAID → EXITED).

```
Real-world sketch (NOT a UML diagram yet):

         ┌──────────────────────────────────┐
         │     Garage (3 floors)            │
         │                                  │
         │  Floor 3: [□] [█] [□] [EV] ...   │  □ = free spot
         │  Floor 2: [█] [█] [□] [□]  ...   │  █ = occupied
         │  Floor 1: [█] [□] [□] [EV] ...   │
         └──────────────┬───────────────────┘
                        │
                ┌───────┴────────┐
                ▼                ▼
            [Entry Gate]    [Exit Gate]
                │                │
              issue            charge
              ticket            + release
```

Three rule families that change:

1. **What fits where** — small car can fit large spot, but motorcycle can't use EV spot.
2. **How much to bill** — flat / tiered / peak / monthly.
3. **What payment methods are accepted** — cash, card, app.

---

## 5. Try it yourself first

> **Predict before reading on:**
>
> 1. List 5 nouns you'd promote to a class. List 3 nouns you'd leave as fields.
> 2. Which of the 3 "things that change" (vehicle/spot compatibility, pricing, payment) would you NOT make a Strategy? Why?
> 3. If a "monthly subscriber" parks for free, what changes about the design? Which class(es) touch?

---

## 6. Entity & verb extraction

> **Mini-refresher: noun → class, but not every noun.**
>
> Naive OOD makes every noun a class. Senior OOD promotes a noun to a class only if the noun has BEHAVIOR and STATE that need to live together. A noun like "color" usually stays a field; a noun like "ticket" usually becomes a class because it has lifecycle behavior.

**Nouns from the prompt:**

| Noun | Decision | Why |
|---|---|---|
| ParkingLot / Garage | **Class** (top-level coordinator) | Owns floors and orchestrates park/exit |
| Floor | **Class** | Has spots, can report free count |
| Spot | **Class** | Has type, occupancy, can be assigned to a vehicle |
| Vehicle | **Class** (abstract) + concrete subclasses | Has type + license plate; subclasses encode size constraints |
| Ticket | **Class** | Lifecycle state machine + billing target |
| Gate | **Class** | EntryGate / ExitGate — orchestrates park / exit flows |
| PricingStrategy | **Interface** | Variability — see §7 |
| PaymentMethod | **Interface** | Variability — see §7 |
| LicensePlate | **Field on Vehicle** (string) | No behavior of its own |
| Time / Duration | **Library type** (Date / Duration) | No domain behavior |
| Floor number | **Field on Floor** | Not a class |

**Verbs (and the class they live on):**

| Verb | Owner class |
|---|---|
| park(vehicle) | EntryGate (delegates to ParkingLot) |
| assignSpot(vehicle) | ParkingLot (or a SpotAssignmentStrategy — see §7) |
| issueTicket(spot, vehicle) | ParkingLot |
| exit(ticketId) | ExitGate |
| computeFee(ticket) | PricingStrategy |
| charge(amount, method) | PaymentMethod |
| markOccupied() / markFree() | Spot |
| transition(event) | Ticket |

---

## 7. Variability points

**These are the things most likely to change.** Each gets a distinct pattern in §8.

1. **Pricing.** Flat hourly today, but next month we add "first 30 min free", quarter after that we add "monthly subscriber bypass", year after that we add dynamic peak pricing. → **Strategy.**
2. **Spot-vehicle compatibility.** Today: simple "any vehicle fits a same-or-larger spot." Future: EV spots only fit EVs, handicapped spots require a credential. → **Strategy** (or rules engine; we'll use Strategy for now).
3. **Payment method.** Cash / card today, app + crypto + corporate-account tomorrow. → **Strategy.**
4. **Ticket lifecycle.** ACTIVE → PAID → EXITED today, but eventually: lost-ticket flow, expired-ticket flow, refund flow. → **State.**
5. **Spot assignment algorithm.** Today: closest-free-spot. Future: by-floor-balance / by-vehicle-preference / VIP-section priority. → **Strategy.**

> **Mini-refresher: why three different "Strategy" decisions don't share one interface.**
>
> Strategy is a *role*, not a type. PricingStrategy, PaymentStrategy, and SpotAssignmentStrategy are three INDEPENDENT Strategy hierarchies — they have nothing in common at the type level (different inputs, different outputs). Don't try to unify them under a single `Strategy<T>` interface; that's premature genericism.

---

## 8. Pattern choice + alternatives

For each variability point, the chosen pattern + the rejected alternatives:

### 8.1 Pricing — Strategy

> **Mini-refresher: Strategy pattern.**
>
> Encapsulates an algorithm behind an interface so it can be swapped at runtime. The CALLER decides which strategy to use; the strategy doesn't know about other strategies.

- **Chosen:** Strategy. Each pricing rule is a class implementing `PricingStrategy`. ParkingLot holds a reference.
- **Rejected — Template Method:** would force a base class with a template method and subclass hooks. Inheritance is rigid; we'd have one base for "free first hour" and another for "peak pricing" — what about a rule combining BOTH? Strategy + composition lets us combine; Template Method can't.
- **Rejected — Chain of Responsibility:** "first matching rule wins" is appealing, but most pricing rules COMPOSE (apply discount AND tiered rate). Chain assumes one handler; pricing isn't that.

**Pattern-discrimination cheatsheet — Strategy vs Template Method:**
- *Strategy:* whole algorithm in one swappable object; chosen at runtime via composition.
- *Template Method:* algorithm skeleton in base class; subclasses fill in hooks via inheritance.
- *Rule of thumb:* if you'd need MULTIPLE distinct variants AND might combine them or change them at runtime, → Strategy. If the algorithm has a fixed skeleton with optional steps and 2-3 variants, → Template Method.

### 8.2 Spot-vehicle compatibility — Strategy

- **Chosen:** Strategy. `CompatibilityRule` interface with `canPark(vehicle, spot): boolean`.
- **Rejected — inheritance hierarchy:** "EVSpot extends Spot extends Vehicle" — instant tangle. EV charging is BEHAVIOR, not a type identity.
- **Rejected — boolean fields on Spot:** `spot.isElectric`, `spot.isHandicapped` — works for now but every new rule means a new field + every `canPark` site needs updating. OCP violation.

### 8.3 Payment method — Strategy

- **Chosen:** Strategy. `PaymentMethod` interface; `CashPayment`, `CardPayment`, `AppPayment` implementations.
- **Rejected — switch/if-else inside Ticket.charge():** classic "tag-driven if/else" anti-pattern. Every new method = surgery in the same function.

### 8.4 Ticket lifecycle — State

> **Mini-refresher: State pattern.**
>
> Each lifecycle state is a class. The context object delegates `handleEvent()` to its current state, and the STATE decides what the next state should be. Transitions are INTERNAL, driven by events the context receives.

- **Chosen:** State. Each ticket state (`ActiveTicket`, `PaidTicket`, `ExitedTicket`, `LostTicket`) is a class with state-specific methods.
- **Rejected — enum + switch:** works for 3 states but with lost/expired/refund flows we end up with N² switch cases.
- **Rejected — Strategy:** Strategy is for *interchangeable algorithms*. State is for *lifecycle progression* — different conceptually.

**Pattern-discrimination cheatsheet — Strategy vs State:**
- *Strategy:* CALLER picks which one to use; strategies are usually unaware of each other.
- *State:* the OBJECT picks its next state internally; states know about each other (each state knows valid transitions).
- *Rule of thumb:* if the swap happens because external code says so → Strategy. If the swap happens because of an internal event flow → State.

### 8.5 Spot assignment algorithm — Strategy

- **Chosen:** Strategy. `SpotAssignmentStrategy` with `findSpot(vehicle, garage): Spot | null`.
- **Rejected — hardcoded in ParkingLot.park():** if we ever want VIP-section priority or floor-balancing, we'd be back rewriting park(). Inject the strategy.

---

## 9. UML class diagram

> **Editable source:** [`./Parking_Lot.class-diagram.excalidraw`](./Parking_Lot.class-diagram.excalidraw)
>
> Open in [https://excalidraw.com](https://excalidraw.com) and use File → Open. Export PNG when polishing for sharing.

**ASCII rendering:**

```
                    ┌─────────────────────────────┐
                    │      ParkingLot             │
                    ├─────────────────────────────┤
                    │ - floors: Floor[]           │
                    │ - assignment: SpotAssignmentStrategy │
                    │ - pricing: PricingStrategy  │
                    │ - tickets: Map<id, Ticket>  │
                    ├─────────────────────────────┤
                    │ + park(v: Vehicle): Ticket  │
                    │ + exit(id, pmt): Receipt    │
                    └────┬────────┬───────────┬───┘
                  ◆     │      ◆ │       ◆   │
                ┌───────┘        ▼           ▼
                │           ┌─────────┐  ┌──────────────────┐
                │           │ Pricing │  │ SpotAssignment   │
                │           │Strategy │  │    Strategy      │
                │           └────▲────┘  └────────▲─────────┘
                ▼                │                │
        ┌────────────┐     implemented        implemented
        │   Floor    │     ┌────┴─────┐  ┌─────┴─────────┐
        ├────────────┤     │FlatRate  │  │ClosestFreeSpot│
        │ - num: int │     │Tiered    │  │FloorBalanced  │
        │ - spots[]  │     │Subscriber│  │VIPPriority    │
        └─────┬──────┘     └──────────┘  └───────────────┘
              │ ◆
              ▼
         ┌────────┐      ┌──────────────────┐
         │  Spot  │      │  Compatibility   │
         ├────────┤      │      Rule        │
         │-type   │─uses▶├──────────────────┤
         │-occupied│     │+canPark(v,s):bool│
         │ -vehicle│     └────────▲─────────┘
         └────────┘               │ implemented
                          ┌───────┼─────────┐
                          │       │         │
                       ┌──┴──┐ ┌──┴──┐ ┌────┴────┐
                       │Size │ │ EV  │ │Handicap │
                       │Match│ │Rule │ │Rule     │
                       └─────┘ └─────┘ └─────────┘

         ┌────────┐                 ┌─────────┐
         │Vehicle │ ─── parks in ──▶│ Ticket  │
         ├────────┤                 ├─────────┤
         │ +type  │                 │ -spot   │
         │ +plate │                 │ -vehicle│
         └───▲────┘                 │ -state  │◆──────▶┌─────────────┐
             │                      │ -entry  │        │ TicketState │
        ┌────┴──────┬──────┐        └─────────┘        └──────▲──────┘
        │           │      │                                  │
     ┌──┴─┐      ┌──┴──┐ ┌─┴────┐                  ┌──────────┼──────────┐
     │Car │      │Bike │ │Truck │              ┌───┴───┐ ┌────┴───┐ ┌────┴────┐
     └────┘      └─────┘ └──────┘              │Active │ │ Paid   │ │ Exited  │
                                               └───────┘ └────────┘ └─────────┘
                                                         │     ◆
                                                         ▼
                                                 ┌───────────────┐
                                                 │ PaymentMethod │
                                                 ├───────────────┤
                                                 │+charge(amt)   │
                                                 └───────▲───────┘
                                                ┌────────┼─────────┐
                                             ┌──┴──┐ ┌───┴──┐ ┌────┴────┐
                                             │Cash │ │ Card │ │  App    │
                                             └─────┘ └──────┘ └─────────┘
```

**Relationship reading:**

- `ParkingLot ◆── Floor` (composition — lot owns floors)
- `Floor ◆── Spot` (composition)
- `ParkingLot ◇── Strategy` (aggregation — strategies are injected, not owned)
- `Vehicle ────▷ Car/Bike/Truck` (inheritance — true is-a)
- `TicketState ────▷ Active/Paid/Exited` (inheritance for state classes)
- `Ticket ◆── TicketState` (composition — ticket holds its current state)

---

## 10. Skeleton code (TypeScript)

> Show the SHAPES, not the full impl. ~80 lines.

```typescript
// ── Vehicle hierarchy ───────────────────────────────────────────────
abstract class Vehicle {
  constructor(public readonly plate: string) {}
  abstract get sizeClass(): SpotSize;
}
class Car extends Vehicle  { get sizeClass() { return SpotSize.REGULAR; } }
class Bike extends Vehicle { get sizeClass() { return SpotSize.SMALL; } }
class Truck extends Vehicle { get sizeClass() { return SpotSize.LARGE; } }

// ── Spot ────────────────────────────────────────────────────────────
enum SpotSize { SMALL, REGULAR, LARGE, EV, HANDICAPPED }

class Spot {
  occupied = false;
  vehicle: Vehicle | null = null;
  constructor(public readonly id: string, public readonly type: SpotSize) {}
  assign(v: Vehicle) { this.vehicle = v; this.occupied = true; }
  release()          { this.vehicle = null; this.occupied = false; }
}

// ── Strategies ──────────────────────────────────────────────────────
interface CompatibilityRule { canPark(v: Vehicle, s: Spot): boolean; }
class SizeMatch implements CompatibilityRule {
  canPark(v: Vehicle, s: Spot): boolean {
    // simple: vehicle.size <= spot.size; refinements added in subclasses
    return v.sizeClass <= s.type;
  }
}

interface PricingStrategy { computeFee(ticket: Ticket): number; }
class FlatRate implements PricingStrategy {
  constructor(private hourly: number) {}
  computeFee(t: Ticket): number {
    const hours = Math.ceil((t.exitTime!.getTime() - t.entryTime.getTime()) / 3_600_000);
    return hours * this.hourly;
  }
}
// (Tiered, Subscriber, Peak — elided; same interface)

interface PaymentMethod { charge(amount: number): Promise<{ ok: boolean; ref: string }>; }
class CardPayment implements PaymentMethod {
  async charge(amount: number) { /* call payment gateway */ return { ok: true, ref: 'TXN-...' }; }
}

interface SpotAssignmentStrategy { findSpot(v: Vehicle, garage: ParkingLot): Spot | null; }
// (ClosestFreeSpot etc. — elided)

// ── Ticket + State ──────────────────────────────────────────────────
interface TicketState {
  pay(ticket: Ticket, method: PaymentMethod): Promise<void>;
  exit(ticket: Ticket): void;
}
class ActiveState implements TicketState {
  async pay(ticket: Ticket, method: PaymentMethod) {
    const fee = ticket.lot.pricing.computeFee(ticket);
    const res = await method.charge(fee);
    if (res.ok) ticket.transitionTo(new PaidState(res.ref));
  }
  exit(_t: Ticket) { throw new Error('Cannot exit unpaid ticket'); }
}
class PaidState implements TicketState {
  constructor(public readonly txnRef: string) {}
  async pay() { throw new Error('Already paid'); }
  exit(t: Ticket) { t.spot.release(); t.transitionTo(new ExitedState()); }
}
class ExitedState implements TicketState { /* terminal */ }

class Ticket {
  readonly id = generateId();
  readonly entryTime = new Date();
  exitTime: Date | null = null;
  private state: TicketState = new ActiveState();

  constructor(public readonly lot: ParkingLot,
              public readonly vehicle: Vehicle,
              public readonly spot: Spot) {}

  transitionTo(s: TicketState) { this.state = s; }
  pay(method: PaymentMethod)   { return this.state.pay(this, method); }
  exit()                        { this.exitTime = new Date(); this.state.exit(this); }
}

// ── ParkingLot (orchestrator) ───────────────────────────────────────
class ParkingLot {
  constructor(
    public readonly floors: Floor[],
    public assignment: SpotAssignmentStrategy,
    public pricing: PricingStrategy,
    public compatibility: CompatibilityRule,
  ) {}

  park(v: Vehicle): Ticket {
    const spot = this.assignment.findSpot(v, this);
    if (!spot || !this.compatibility.canPark(v, spot)) throw new Error('Lot full');
    spot.assign(v);
    return new Ticket(this, v, spot);
  }

  async exit(ticket: Ticket, method: PaymentMethod) {
    await ticket.pay(method);
    ticket.exit();
  }
}
```

---

## 11. Key flow — sequence diagram

> **Editable source:** [`./Parking_Lot.sequence.excalidraw`](./Parking_Lot.sequence.excalidraw)

**Scenario:** A car arrives, parks, and exits paying by card.

**ASCII rendering:**

```
 Driver       EntryGate     ParkingLot   Assignment  Spot      Ticket
   │             │              │             │        │          │
   │ approach    │              │             │        │          │
   ├────────────▶│ park(car)    │             │        │          │
   │             ├─────────────▶│ findSpot(car)         │          │
   │             │              ├────────────▶│ scan all spots
   │             │              │             ├───────▶│ free?
   │             │              │             │◀───────┤ yes
   │             │              │ canPark?    │        │
   │             │              ├─compat──────┘        │
   │             │              │ assign(car)          │
   │             │              ├─────────────────────▶│ occupied=true
   │             │              │ new Ticket(ACTIVE)   │
   │             │              ├────────────────────────────────▶│
   │             │◀─ Ticket #42 ┤                                  │
   │◀─ ticket ───┤              │                                  │
   │                                                               │
   │  ... time passes ...                                          │
   │                                                               │
   │ ExitGate    │ exit(#42, card)                                 │
   ├────────────▶│              │                                  │
   │             ├──────────────▶ ticket.pay(card)                 │
   │             │              ├─ pricing.computeFee(ticket) ─┐   │
   │             │              │◀─────── $8.50 ───────────────┘   │
   │             │              ├─ card.charge($8.50) ─▶ Stripe    │
   │             │              │◀────────── TXN-... ─────         │
   │             │              ├──────── ticket.transitionTo(Paid)│
   │             │              ├─ ticket.exit()                   │
   │             │              ├──────────── spot.release() ─────▶│
   │             │              ├────── ticket.transitionTo(Exited)│
   │             │◀── Receipt ──┤                                  │
   │◀ open gate ─┤              │                                  │
```

Key thing to notice: the **State pattern hides the validation**. Trying to `exit()` an ActiveState ticket throws "Cannot exit unpaid"; trying to `pay()` a PaidState ticket throws "Already paid." No `if (ticket.status === 'paid')` chains anywhere.

---

## 12. Extensibility discussion

For each hypothetical new requirement, name EXACTLY which class(es) change. If the answer is "everything," the design is wrong.

### Requirement A: "EV spots that charge while parked, with surcharge for slow chargers."

- **Changes:** Add `EVChargingSpot extends Spot` (or compose `Spot + Charger`); add `EVChargingPricing` (PricingStrategy or decorator).
- **No change:** Vehicle hierarchy (an EV is still a Car for parking; only its compatibility rule cares); Ticket lifecycle; PaymentMethod; ParkingLot.park() itself.
- **Smell check:** ✅ One pattern decision per change. Good.

### Requirement B: "Monthly subscribers — flat $200/month, no per-visit charge."

- **Changes:** Add `SubscriberPricing implements PricingStrategy` (returns 0 if vehicle.plate ∈ subscribers; throws to `FlatRate` otherwise — use Decorator or Chain of Responsibility around the existing pricing). Subscribers tracked in a `SubscriberRegistry` injected into the strategy.
- **No change:** Spot, Vehicle, Ticket, PaymentMethod, ParkingLot.park().
- **Smell check:** ✅ Pricing was the variability point we identified in §7. Strategy makes this trivial.

### Requirement C: "Lost ticket — driver claims to have lost the ticket. Charge max-day rate, generate replacement."

- **Changes:** Add `LostTicketState extends TicketState`; add a method on ExitGate `reportLost(plate)` that transitions ACTIVE→LOST→PAID with max-day fee.
- **No change:** Spot, Vehicle, Pricing/Payment strategies (LostTicket uses existing pricing via decorator).
- **Smell check:** ✅ State pattern handles new lifecycle states without touching the rest.

### Requirement D: "Concurrent entries — two cars arrive simultaneously, both should not get the same spot."

- **Changes:** `assignment.findSpot()` must be thread-safe — use a mutex / atomic CAS / fine-grained per-floor locks; `Spot.assign()` needs to fail loudly if already occupied (raise → retry assignment loop).
- **No change:** Pattern choices stay; only the assignment strategy's INTERNALS get a lock.
- **Smell check:** ✅ Concurrency is orthogonal to design pattern choice.

If a future requirement makes you change Vehicle, Spot, Pricing, AND Ticket together — go back to §7 and re-identify variability points; you likely missed one.

---

## 13. Common confusion + traps

1. **"Should Vehicle subclasses have a `pay()` method?"**
   No. Vehicle has no business with payment — that's the Ticket's concern. The misconception is "I want to ask the car to pay" → no, the GATE asks the TICKET to pay; the ticket asks the payment method to charge. Separation of concerns.

2. **"Should I make Spot abstract with subclasses RegularSpot, EVSpot, HandicappedSpot?"**
   Tempting but usually wrong. The DIFFERENCE between spots is behavior (can-park rules + maybe charging), not identity. Use one `Spot` class + a `type` field + a CompatibilityRule strategy. You'd only subclass Spot if the data-fields-per-type diverge significantly.

3. **"Why not make Ticket an enum-state machine instead of using the State pattern?"**
   Works for 3 states. Falls apart at 6+ states because the transition matrix becomes N². The State pattern colocates "what events are valid in state X" with state X. Also, exception-throwing on invalid transitions is cleaner.

4. **"Why is PricingStrategy injected into ParkingLot and not into Ticket?"**
   Because pricing is a LOT-WIDE policy (changing the rate doesn't depend on which ticket). The ticket delegates to the lot's strategy at exit time. If pricing varied per-ticket (e.g., promotional codes), you'd attach the strategy to the ticket.

---

## 14. Anti-patterns + how to think aloud + self-check

### Anti-patterns

- **"God class ParkingLot"** — ParkingLot doing assignment + pricing + payment + state-tracking. Pull each into its own collaborator.
- **"Inheritance chain for variations"** — `RegularSpot → EVSpot → HighVoltageEVSpot → HighVoltageEVSpotWithReservation` is a smell. Switch to composition.
- **"Tag-driven if/else for payment"** — `if (method === 'cash') ... else if (method === 'card') ...` inside Ticket.charge(). Use the Strategy interface and let polymorphism do the dispatch.
- **"Anemic Ticket"** — a Ticket that's a data bag with only getters/setters. Tickets have lifecycle behavior; put it on the class.
- **"Singleton-everything"** — making ParkingLot a singleton because "there's one lot." There may be multiple lots in a chain; dependency-inject instead.

### How to think aloud

> "OK, parking lot. Let me clarify scope first. [Asks 4-6 questions from §1.] Got it.
>
> The nouns: ParkingLot, Floor, Spot, Vehicle, Ticket, Gate. Sketches them. Vehicle is a hierarchy — Car/Bike/Truck differ in size. Spot has a type. Lot has floors, floors have spots.
>
> Now the variability — what's most likely to change? Pricing for sure. Payment methods. Spot-vehicle compatibility rules. Ticket states once we add lost-ticket flow.
>
> Pricing → Strategy. Payment → Strategy. Compatibility → Strategy. Ticket lifecycle → State pattern (because transitions are internal to the ticket).
>
> Sketches the class diagram. ParkingLot has-a SpotAssignmentStrategy, has-a PricingStrategy. Floor is composed inside ParkingLot. Spot is composed inside Floor. Ticket has-a current TicketState. Three concrete states: Active / Paid / Exited.
>
> Now the park flow: gate.park(car) → lot.findSpot via strategy → spot.assign → new ActiveTicket → return ticket.
>
> Exit flow: gate.exit(ticket, payment) → ticket.pay(payment) — but pay() delegates to the current state, ActiveState.pay() computes fee via pricing strategy, charges via payment, transitions to PaidState. Then exit() works only on PaidState.
>
> Extensibility check: monthly subscriber? Add a SubscriberPricing strategy. EV charging? Compose Spot + Charger; add EVCompatibilityRule. Lost ticket? Add LostTicketState. No core changes."

### Self-check

> **Self-check — the question to ask next time.**
>
> When you see a "design a [system that does X with many variations of Y]" question, before reaching for inheritance, ask:
>
> > **"What are the 3-5 things most likely to change about this system? For each, which pattern fits — Strategy (caller picks the variation), State (object picks based on lifecycle), or Decorator (variations stack)?"**
>
> Answer that, and the class diagram falls out for free.

---

## Cross-references

- **Parent topic manifest:** [`./EXTRACTED_QUESTIONS.md`](./EXTRACTED_QUESTIONS.md)
- **Vertical overview:** [`../../LEARNING.md`](../../LEARNING.md)
- **Template:** [`../../TEMPLATE-v2.md`](../../TEMPLATE-v2.md)
- **Diagrams:**
  - [`./Parking_Lot.class-diagram.excalidraw`](./Parking_Lot.class-diagram.excalidraw)
  - [`./Parking_Lot.sequence.excalidraw`](./Parking_Lot.sequence.excalidraw)
- **Related LLD walkthroughs (future):**
  - Strategy Pattern deep-dive (in `../Strategy_Pattern/`)
  - State Pattern deep-dive (in `../State_Pattern/`)
