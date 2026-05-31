# LLD v2 Teaching Template

**Purpose.** A Low-Level Design (LLD) interview is not a coding speed test — it's a **pattern-discrimination test**. The interviewer wants to see: can you reason about entities, identify variability points, choose the right design pattern, and defend your choice? This template structures every LLD walkthrough so a first-time learner builds *that judgment* alongside the answer.

**Companion templates.** For algorithmic walkthroughs use [`../DSA/TEMPLATE-v2.md`](../DSA/TEMPLATE-v2.md). For JS concept/behavior walkthroughs use [`../TEMPLATE-v2.md`](../TEMPLATE-v2.md). For HLD use [`../HLD/TEMPLATE-v2.md`](../HLD/TEMPLATE-v2.md). LLD differs from all three — its "answer" is a *defensible class structure*, not an algorithm or a system architecture.

**Canonical exemplar:** [`Topics/Object_Oriented_Design/Parking_Lot.md`](./Topics/Object_Oriented_Design/Parking_Lot.md). Every v2 LLD file should feel like that.

---

## Audience assumption (zero-prior-knowledge contract)

A v2 LLD file MAY assume the reader knows:

- Basic OOP: classes, methods, fields, constructors, inheritance, interfaces.
- A typed language at literacy level (Java / TS / C# / Kotlin — examples will be in TypeScript by default).
- Basic data structures: list, map, set, queue.

A v2 LLD file MAY NOT assume the reader knows, without an inline refresher:

- The named GoF design patterns (Strategy, State, Observer, Command, Decorator, Composite, Chain of Responsibility, Template Method, Iterator, Memento, Builder, Factory, Singleton, Abstract Factory).
- SOLID principles individually (SRP, OCP, LSP, ISP, DIP).
- Composition vs. inheritance tradeoffs.
- Aggregation vs. composition (UML relationship distinction).
- Dependency injection.
- Open/closed principle violation diagnosis.
- Interface segregation in practice.
- Polymorphism via interfaces vs via base classes.
- Cohesion vs. coupling.
- Pattern-discrimination pairs (Strategy vs State; Decorator vs Composite; Observer vs Mediator; Builder vs Factory).

**If the solution invokes any of these, embed a mini-refresher box where it first appears.** Same convention as DSA TEMPLATE-v2.md §"Rule 3."

---

## The 14 required sections

Every v2 LLD file follows this skeleton. Some sections may collapse to a sentence for trivial designs; none may be omitted (use "N/A — this design is simple enough" for explicit waivers).

### Section header (top of file)

```markdown
# Problem Name — LLD Walkthrough

> **Reference:** N/A (LLD vertical is greenfield; no reference card layer yet)
>
> **Difficulty:** Medium / Hard   |   **Time:** ~30/45 min   |   **Pattern focus:** Strategy + Factory (or whatever applies)
>
> **Problem source(s):** linked LeetLens IDs from the parent `EXTRACTED_QUESTIONS.md`.
```

### Section "How to use this file"

```markdown
## How to use this file

Paced for a candidate seeing this design problem for the first time. Reading time: ~N minutes if you sketch the class diagram by hand. The lesson: **<one-sentence pattern-discrimination takeaway>**.

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
10. Skeleton code
11. Key flow — sequence diagram
12. Extensibility discussion
13. Common confusion + traps
14. Anti-patterns and how to think aloud
```

### Required body sections

1. **Problem statement + clarifying questions.** Restate the prompt. List 4-6 clarifying questions a senior candidate would ask the interviewer BEFORE drawing anything. Make explicit assumptions if the interviewer dodges.

2. **Plain-English restatement.** One paragraph in mentor voice. "The interviewer wants a class structure for X that supports Y operations and is open to Z future extensions."

3. **Why this matters.** 3-5 sentences. What skill is being probed. Where the pattern reappears in production code.

4. **Mental model.** 2-4 sentences + ASCII sketch of the **domain** (not code yet — the real-world thing). For parking lot: "imagine a multi-floor garage with attendant kiosks at entry/exit and a board showing free spots per floor."

5. **Try it yourself first.** 2-3 prediction prompts the reader should attempt before reading on. Examples:
   - "List the nouns you'd turn into classes."
   - "What's the ONE thing that's most likely to change about this system?"
   - "If you had to use exactly one design pattern, which would it be? Why?"

6. **Entity & verb extraction.** Two side-by-side lists:
   - **Nouns → class candidates.** With note on which to *promote* to a class vs leave as a simple field.
   - **Verbs → method candidates.** Grouped by the class they'd live on.

7. **Variability points.** The single most important LLD section. List 3-5 things that are MOST LIKELY to change about this system over time. These are where you reach for design patterns.

8. **Pattern choice + alternatives.** For each variability point in §7, name the pattern you'd pick AND name 1-2 patterns you'd reject + why. This is the pattern-discrimination muscle.

9. **UML class diagram.** Both an excalidraw source file (sibling `.excalidraw`) AND an ASCII rendering inline. See the excalidraw convention below.

10. **Skeleton code.** Interfaces + 1-2 concrete classes. NOT the full implementation. Show the SHAPES, not the SOLUTIONS.

11. **Key flow — sequence diagram.** Walk through the ONE operation that exercises the design most ("park a vehicle and pay on exit"). Sibling `.sequence.excalidraw` + ASCII fallback.

12. **Extensibility discussion.** State 2-3 hypothetical new requirements. For each: "here's exactly which class(es) change, and what doesn't change at all." If too many classes change, the design is wrong — back up.

13. **Common confusion + traps.** Pattern-discrimination edge cases. "If you find yourself reaching for inheritance to share behavior across unrelated classes, stop — that's composition's job."

14. **Anti-patterns + how to think aloud + self-check.** Three sub-blocks:
    - **Anti-patterns:** 3-5 bad smells a beginner would commit ("God class", "feature envy", "tag-driven if/else instead of polymorphism").
    - **How to think aloud:** 4-6 beats of the candidate's monologue at the whiteboard.
    - **Self-check:** the ONE pattern-discrimination question to ask next time you see a similar problem.

### Cross-references (bottom)

```markdown
## Cross-references

- **Parent topic manifest:** [`./EXTRACTED_QUESTIONS.md`](./EXTRACTED_QUESTIONS.md)
- **Vertical overview:** [`../../LEARNING.md`](../../LEARNING.md)
- **Related v2 walkthroughs:** [`<sibling>.md`]
- **Diagrams:** [`./Problem_Name.class-diagram.excalidraw`](./Problem_Name.class-diagram.excalidraw), [`./Problem_Name.sequence.excalidraw`](./Problem_Name.sequence.excalidraw)
```

---

## Style rules

### Rule 1 — No code dumps; show SHAPES

A v2 LLD file should fit in 400-700 lines. If you find yourself writing the full implementation of every method, you're missing the point. Show:

- **Interface declarations** with method signatures.
- **One or two CONCRETE classes** with method bodies that demonstrate the pattern.
- **Stub the rest** — `// elided: standard getter/setter` is fine.

The reader should see the CHOICE, not the labor.

### Rule 2 — Mini-refresher boxes for OOD concepts

Same convention as DSA TEMPLATE-v2.md. Embed inline at first appearance, never as a "prerequisites" dump up-front.

```markdown
> **Mini-refresher: Strategy pattern.**
>
> Strategy lets you swap an algorithm at runtime by delegating to an interface that has multiple implementations. You inject the strategy into the context object; the context delegates to it without knowing which concrete strategy is in play.
>
> Quick example: a `Sorter` class takes a `CompareStrategy` in its constructor. Pass `AscendingCompare` or `DescendingCompare` — the sorter doesn't care.
```

**OOD concepts that virtually always need a refresher (when touched by the solution):**

- Strategy / State / Observer / Command / Decorator / Composite / Chain of Responsibility / Template Method / Iterator / Memento / Builder / Factory / Singleton / Abstract Factory
- SOLID (each principle on its first mention)
- Composition vs. inheritance
- Aggregation vs. composition (UML diamond)
- Dependency injection
- Open/closed principle
- Polymorphism via interfaces
- Cohesion vs. coupling

### Rule 3 — Pattern-discrimination cheatsheets

When a section names a pattern, ALSO name the pattern's most-confused sibling AND the rule that separates them. Three-line format:

```markdown
**Strategy vs State.**
- *Strategy:* the caller picks which algorithm to use.
- *State:* the object picks (via internal transitions).
- Rule of thumb: if context.setStrategy() is called externally → Strategy. If context.handleEvent() flips state internally → State.
```

These cheatsheets are the transferable skill. Sprinkle 1-2 per file.

### Rule 4 — UML diagrams via excalidraw + ASCII fallback

**Excalidraw convention:**

1. The walkthrough file is `<Problem>.md`. Its diagrams are sibling files:
   - `<Problem>.class-diagram.excalidraw` — UML class diagram (required for every LLD walkthrough)
   - `<Problem>.sequence.excalidraw` — sequence diagram for the key flow (required)
   - Additional `.excalidraw` files as needed for state machines / collaboration diagrams.
2. Each `.excalidraw` file is committed as JSON. Open it in [https://excalidraw.com](https://excalidraw.com) to edit. Export to PNG when polishing for sharing.
3. **In the markdown**, ALWAYS include an ASCII-rendered version inline. The excalidraw file is the *editable* source; the ASCII rendering is what the reader sees in-browser. The two must stay in sync (manually — re-render the ASCII after every excalidraw edit).

**ASCII UML conventions used in this repo:**

```
┌──────────────────────┐
│   ClassName          │   ← class box, name top
├──────────────────────┤
│ - field: Type        │   ← private (`-`)
│ + publicField: Type  │   ← public (`+`)
│ # protected: Type    │
├──────────────────────┤
│ + method(): Type     │
│ + other(p: T): void  │
└──────────────────────┘

Arrows (UML standard):
  ───▷    inheritance (open triangle)
  ───◇    aggregation (open diamond on the WHOLE side)
  ───◆    composition (filled diamond on the WHOLE side)
  ─── ─▶  dependency (dashed)
  ───▶    association (solid)
```

Sequence diagram ASCII:

```
Actor      ParkingLot    Spot
  │             │          │
  │ enter()     │          │
  ├────────────▶│          │
  │             │ assign() │
  │             ├─────────▶│
  │             │ ◀────────┤  Spot#42
  │ Ticket ◀────┤          │
```

### Rule 5 — The "Variability points" section is required

If you can't name AT LEAST 3 things that might change about the system, you don't understand the problem yet. Go back to clarifying questions. Variability points drive pattern choice — without them, pattern selection is arbitrary.

### Rule 6 — Skeleton code in TypeScript by default

The repo's lingua franca for LLD is TypeScript (closest to interview-board pseudocode while being type-safe). If the question explicitly demands another language (Java for an Android role, C# for .NET role), use that instead and note the choice in the header.

```typescript
interface PaymentStrategy {
  charge(amount: number, account: string): Promise<TransactionId>;
}

class StripePayment implements PaymentStrategy {
  async charge(amount: number, account: string): Promise<TransactionId> {
    // elided: call Stripe SDK
    return { id: '...', status: 'ok' };
  }
}
```

### Rule 7 — Anti-patterns get NAMED, not just described

When listing anti-patterns, name them so the reader can pattern-match later. Examples:

- **"God class"** — single class owning every responsibility.
- **"Feature envy"** — method on class A that accesses class B's fields more than its own.
- **"Tag-driven if/else"** — `if (type === 'X') ... else if (type === 'Y') ...` where polymorphism would do.
- **"Mutable global state"** — singletons that store data, not just behavior.
- **"Anemic domain model"** — classes with only getters/setters and no behavior.

### Rule 8 — Self-check ends every file

End with a single, concrete question the reader should ask themselves the next time they see a similar problem.

```markdown
> **Self-check — the question to ask next time.**
>
> When you see "design a [thing] that supports multiple [variations]," before reaching for inheritance, ask:
>
> > **"Is the variation a behavior (Strategy) or a lifecycle state (State)?"**
>
> If behavior the caller picks → Strategy. If state the object transitions through → State.
```

---

## Length targets

| Question difficulty | Lines | Reading time |
|---|---|---|
| Medium (single-pattern focus: Strategy, Observer, Decorator) | 350-500 | ~25 min |
| Hard (multi-pattern: parking lot, splitwise, chess game) | 500-750 | ~40 min |
| Senior bar (event sourcing, plugin architecture, framework design) | 700-900 | ~50-60 min |

Going over isn't sin — going UNDER on sections §6 (entity/verb extraction), §7 (variability), §8 (pattern choice), §9 (UML diagram) is.

---

## Sub-concept inventory by LLD bucket

Use this as a checklist when writing v2 files in each bucket — these are the concepts that almost always need an inline refresher.

| Bucket | Likely sub-concepts |
|---|---|
| Object_Oriented_Design | composition vs inheritance, SOLID, polymorphism, aggregation diamond |
| LLD_DataStructures | encapsulation, invariant maintenance, generic types, thread safety basics |
| SOLID_Principles | each of S/O/L/I/D individually with a counterexample |
| Strategy_Pattern | Strategy interface, runtime swap, context-vs-strategy ownership |
| State_Pattern | state interface, internal transitions, vs Strategy |
| Observer_Pattern | subject/observer, push vs pull, weak refs vs strong, ordering guarantees |
| Command_Pattern | command interface, undo/redo stack, macro composition |
| Chain_of_Responsibility | next pointer, handle-or-pass, vs Pipeline |
| Template_Method | abstract base, hook methods, vs Strategy (inheritance vs composition) |
| Iterator_Pattern | external vs internal iterators, vs Java's Iterable, lazy evaluation |
| Decorator_Pattern | wrapping chain, vs Composite (decorator changes behavior, composite groups), vs inheritance |
| Composite_Pattern | uniform tree, leaf vs composite, recursion in operations |
| Factory_Pattern | factory method vs abstract factory, vs Builder, vs new |
| Builder_Pattern | fluent API, telescoping constructor avoidance, vs Factory |
| Singleton_Pattern | thread safety, lazy vs eager init, anti-pattern caveat |
| Repository_Pattern | abstraction over persistence, vs DAO, unit-of-work boundary |
| Plugin_Architecture | extension point, ServiceLoader/SPI, isolation strategies |
| Dependency_Injection | constructor vs setter vs interface, container vs manual |
| Event_Sourcing | event log as source of truth, projections, replay, vs CRUD |
| Rule_Engine | rule evaluation order, condition-action pairs, conflict resolution |
| Retry_Pattern | exponential backoff with jitter, circuit breaker state machine |
| Interceptor_Pattern | cross-cutting concerns, AOP, vs middleware |

---

## Checklist for each new v2 LLD file

Before submitting:

- [ ] Header with Difficulty / Time / Pattern focus
- [ ] "How to use this file" with reading-time + map of sections
- [ ] At least 4 clarifying questions in §1
- [ ] Mental model with a domain sketch (not code) in §4
- [ ] Entity & verb extraction in §6 with explicit "noun → class" and "noun → field" calls
- [ ] At least 3 variability points named in §7
- [ ] For each variability point: chosen pattern + rejected alternatives + reasoning
- [ ] Sibling `.class-diagram.excalidraw` file exists
- [ ] ASCII UML rendering inline AND matches the excalidraw source
- [ ] Sibling `.sequence.excalidraw` for the key flow
- [ ] Skeleton code shows SHAPES not full implementations (TS by default)
- [ ] At least 2 mini-refresher boxes on first-appearance OOD concepts
- [ ] At least 1 pattern-discrimination cheatsheet (THIS-vs-THAT)
- [ ] Extensibility discussion names specific future requirements + impact
- [ ] Anti-patterns block with NAMED smells
- [ ] How-to-think-aloud block (first-person)
- [ ] Self-check question at the very end
- [ ] Cross-references link to manifest + LEARNING.md + diagrams

---

## Workflow for applying this template

1. **Read the LeetLens question(s)** assigned to this bucket via `EXTRACTED_QUESTIONS.md` §1 (Net-new). Pick the one to author.
2. **Score against the rubric.** Identify which sections need most depth (often §7 variability + §8 pattern choice).
3. **List sub-concepts the design touches.** For each, decide if it needs a refresher.
4. **Draft on paper first:** clarifying questions, entity/verb lists, variability points. Don't open the IDE.
5. **Sketch the UML in excalidraw**, then transcribe to ASCII for the markdown.
6. **Write the v2 file** in `Topics/<Bucket>/<Problem>.md`.
7. **Run the checklist above** before considering done.
8. **Update the bucket's `EXTRACTED_QUESTIONS.md`** to mark the LeetLens row(s) as "covered" (move from §1 to §2 or annotate).

---

## See also

- [`../CONTRIBUTING-v2.md`](../CONTRIBUTING-v2.md) — repo-level conventions
- [`../DSA/TEMPLATE-v2.md`](../DSA/TEMPLATE-v2.md) — DSA flavor (algorithmic framing)
- [`../TEMPLATE-v2.md`](../TEMPLATE-v2.md) — JS flavor (concept/behavior framing)
- [`../HLD/TEMPLATE-v2.md`](../HLD/TEMPLATE-v2.md) — HLD flavor (architecture / capacity framing)
- [`./LEARNING.md`](./LEARNING.md) — LLD vertical overview + bucket study order
