# LLD v2 Teaching Template

**Purpose.** A Low-Level Design (LLD) interview is a **pattern-discrimination** test — the interviewer wants to see you DERIVE the design, not assert it. This template structures every LLD walkthrough so the reader **gradually arrives** at the final class structure: starts with a naive design, watches it break under hypothetical changes, then introduces one pattern at a time WITH the justification, and only then sees the final class diagram. Mirrors the DSA template's "brute force → pivot → optimal" arc.

**Companion templates.** [`../DSA/TEMPLATE-v2.md`](../DSA/TEMPLATE-v2.md) (algorithmic). [`../TEMPLATE-v2.md`](../TEMPLATE-v2.md) (JS concept/behavior). [`../HLD/TEMPLATE-v2.md`](../HLD/TEMPLATE-v2.md) (system design). LLD differs from all three — its "answer" is a *defensible class structure*, derived progressively.

**Canonical exemplar:** [`Topics/Object_Oriented_Design/Parking_Lot.md`](./Topics/Object_Oriented_Design/Parking_Lot.md).

---

## Audience assumption (zero-prior-knowledge contract)

A v2 LLD file MAY assume:

- Basic OOP: classes, methods, fields, constructors, inheritance, virtual functions.
- C++ literacy (default language; Java/C#/Kotlin equivalents understood).
- Basic data structures: list, map, set, queue.

A v2 LLD file MAY NOT assume, without an inline refresher:

- The named GoF design patterns.
- SOLID principles individually.
- Composition vs. inheritance, aggregation vs. composition.
- Dependency injection.
- Open/closed principle.
- Pattern-discrimination pairs (Strategy vs State, Decorator vs Composite, Observer vs Mediator, Builder vs Factory).

**Embed a mini-refresher box where each concept first appears.** Same convention as DSA TEMPLATE-v2.md §"Rule 3."

---

## Diagram convention — inline mermaid with `look: handDrawn` + explicit light theme

All LLD diagrams are **inline mermaid code blocks** in the walkthrough `.md` file. No external sources (no `.excalidraw`, no PNG, no SVG, no ASCII). Mermaid renders natively in GitHub, VS Code, and most markdown viewers — zero rendering step, zero binary artifacts.

**Why mermaid (and not bespoke excalidraw renders).** Earlier iterations of this template tried excalidraw JSON sources + a programmatic render pipeline. Two losing battles surfaced: (a) programmatic layout can't match human visual taste; (b) rendered snapshots stale relative to their sources. Mermaid trades artistic polish for **always-correct + always-inline + zero-workflow** rendering. The right tradeoff.

**Canonical theme block — MANDATORY: copy verbatim at the top of every mermaid diagram.**

Uses `theme: neutral` + an explicit soft-pastel palette. Three non-obvious bits worth understanding:

1. **`edgeLabelBackground` / `labelBackground`** give every flowchart arrow label a **white card backdrop**. Without this, arrow labels float on the page bg — invisible in dark-mode viewers.
2. **`themeCSS` halo for sequence message labels.** Mermaid sequence-diagram message labels (like "1: park(car)" floating above an arrow) have no built-in `messageBackgroundColor` variable. We apply `paint-order: stroke fill` with a 5px white stroke, rendering a white halo around each glyph — visually equivalent to a white card behind the text. Works in VS Code; **GitHub strips themeCSS**, in which case labels fall back to plain slate text. Best-effort.
3. **`lineColor` / `signalColor` = `#0d47a1`** (Material blue-900, deep navy) — same hue family as `primaryBorderColor` `#084298`, so arrows visually unify with box outlines. Bold on light page bg.
4. **`themeCSS` arrow stroke-width.** Default mermaid arrows are 1-1.5 px (thin). We force 2.5 px on every edge type (`.edgePath`, `.flowchart-link`, `.messageLine0/1`, `.relation`, etc.) via themeCSS. Bolder lines, more visually prominent. **GitHub strips themeCSS**, so on GitHub web arrows revert to default thin stroke; to force thickness for a specific flowchart in GitHub, add `linkStyle default stroke-width:2.5px` directive at the end of the diagram body.
5. **`look: handDrawn` is INTENTIONALLY OMITTED** — caused dark-bg rendering on multiple viewers.

````markdown
```mermaid
---
config:
  theme: neutral
  themeVariables:
    background: '#ffffff'
    primaryColor: '#cfe2ff'
    primaryTextColor: '#1f2937'
    primaryBorderColor: '#084298'
    secondaryColor: '#fff3cd'
    secondaryTextColor: '#1f2937'
    secondaryBorderColor: '#664d03'
    tertiaryColor: '#d1e7dd'
    tertiaryTextColor: '#1f2937'
    tertiaryBorderColor: '#0a3622'
    lineColor: '#0d47a1'
    textColor: '#1f2937'
    noteBkgColor: '#fff3cd'
    noteTextColor: '#1f2937'
    noteBorderColor: '#997404'
    actorBkg: '#cfe2ff'
    actorBorder: '#084298'
    actorTextColor: '#1f2937'
    signalColor: '#0d47a1'
    signalTextColor: '#1f2937'
    labelBoxBkgColor: '#ffffff'
    labelBoxBorderColor: '#d3d3d3'
    labelTextColor: '#1f2937'
    edgeLabelBackground: '#ffffff'
    labelBackground: '#ffffff'
    classText: '#1f2937'
    fontFamily: 'system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif'
  themeCSS: |
    .messageText, .labelText, .sequenceNumber {
      paint-order: stroke fill;
      stroke: #ffffff;
      stroke-width: 5px;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
---
classDiagram
  ...
```
````

**Color semantics:**

| Role | Variable | Hex | Visible on white? | Visible on dark? |
|---|---|---|---|---|
| Concrete domain class | `primaryColor` fill + `primaryBorderColor` | `#bbdefb` / `#1565c0` | ✓ | ✓ |
| Interface / abstract | `secondaryColor` + `secondaryBorderColor` | `#fff9c4` / `#f57f17` | ✓ | ✓ |
| Concrete impl / leaf | `tertiaryColor` + `tertiaryBorderColor` | `#c8e6c9` / `#2e7d32` | ✓ | ✓ |
| Lines / arrows | `lineColor` `signalColor` | `#1976d2` (medium blue) | ✓ | ✓ |
| In-box text | `*TextColor` | `#0d47a1` (deep navy) | ✓ (against pastel fill) | ✓ (same) |

**Recommended mermaid diagram types per LLD section:**

| Section | Mermaid type | What it shows |
|---|---|---|
| §7 Naive | `classDiagram` | Bare classes, no patterns; mark ⚠ pain points in field/method labels |
| §9–§11 Pivots | `classDiagram` | After-state showing the slice that changed (the new interface + impls) |
| §12 Final | `classDiagram` | Decomposed into 12.1/12.2/12.3 sub-diagrams (don't draw one huge diagram) |
| §14 Sequences | `sequenceDiagram` | Numbered messages: `1: park(car)`, `2: assign(spot)`, … |

**Naming convention** when prose refers to a diagram: name it by what it depicts ("the iteration-1 diagram", "the §12.3 lifecycle diagram"), not by section number alone (which rots if sections renumber).

**See:** [`Topics/Object_Oriented_Design/Parking_Lot.md`](./Topics/Object_Oriented_Design/Parking_Lot.md) for the canonical exemplar with 8 mermaid diagrams across 5 sections.

**Cross-referencing.** Add an HTML anchor to every figure-bearing section so prose elsewhere can link to it:

```markdown
## <a id="fig-class-diagram"></a>12. Final class diagram
```

Reference from prose: `... (see [Final class diagram](#fig-class-diagram))`.

---

## The 15 required sections

Every v2 LLD file follows this skeleton. Pivot count flexes (2-4) depending on how many patterns the design needs. Total length: 600-1000 lines.

### Section header (top of file)

```markdown
# Problem Name — LLD Walkthrough

> **Difficulty:** Medium / Hard   |   **Time:** ~30/45 min   |   **Pattern focus:** Strategy + State (or whatever applies)
>
> **Problem source(s):** linked LeetLens IDs from the parent `EXTRACTED_QUESTIONS.md`.
>
> **Diagrams:** PNG inline (rendered from `.excalidraw` sources by `tools/render-diagrams/`). See diagram convention above.
```

### Section "How to use this file"

Reading time + lesson summary + map of N sections.

### Required body sections

1. **Problem statement + clarifying questions.** Restate. List 4-6 clarifying questions a senior candidate would ask BEFORE drawing anything. Make explicit assumptions if the interviewer dodges.
2. **Plain-English restatement.** One paragraph in mentor voice.
3. **Why this matters.** 3-5 sentences. Skill being probed; where it reappears.
4. **Mental model.** 2-4 sentences + a domain sketch (NOT code yet). What real-world thing are we modeling?
5. **Try it yourself first.** 2-3 prediction prompts.
6. **Entity & verb extraction.** Two side-by-side lists: nouns → class candidates, verbs → method owners. **No design patterns yet.**
7. **Iteration 1: the naive design.** What a beginner would write FIRST.
   - Class diagram via mermaid block (inline)
   - ~30-50 lines of C++ skeleton with NO patterns — straight conditionals, enums, if/else
   - State explicitly: "this works. it has zero design patterns. let's see what's wrong with it."
8. **Where the naive design hurts.** List 3-5 hypothetical future requirements. For each:
   - Name the change.
   - Walk through the FILES + LINES that have to change in the naive design.
   - Note the smell.
   - End with a **pivot question** that names the variability axes.
9. **Pivot 1: first pattern.** Take the MOST PAINFUL axis from §8. Name the pattern. Derive WHY it fits.
   - Brief mini-refresher.
   - Show the refactored C++ code for just the affected slice (~40 lines).
   - Pattern-discrimination cheatsheet: which pattern did you NOT pick, and why.
10. **Pivot 2: second pattern.** Same shape for the next variability axis.
11. **Pivot 3+: remaining variability.** Repeat. Often shorter — same shape, different axis.
12. **<a id="fig-class-diagram"></a>Final class diagram.** Mermaid block, full UML. Two-paragraph reading guide.
13. **Skeleton code.** C++ interfaces + 1-2 concrete classes per pattern. ~100-150 lines.
14. **<a id="fig-sequence"></a>Key flow — sequence diagram.** Mermaid sequenceDiagram block. Brief prose pointing out what the State / Strategy patterns HIDE from the caller.
15. **Extensibility re-check + anti-patterns + how to think aloud + self-check.** Five sub-blocks.

### Cross-references (bottom)

```markdown
## Cross-references

- **Parent topic manifest:** [`./EXTRACTED_QUESTIONS.md`](./EXTRACTED_QUESTIONS.md)
- **Vertical overview:** [`../../LEARNING.md`](../../LEARNING.md)
- **Optional editable diagrams:** sibling `.excalidraw` files (supplementary)
- **Related v2 walkthroughs:** ...
```

---

## Style rules

### Rule 1 — DERIVATION over ASSERTION

The single biggest difference between a "v2 LLD walkthrough" and a generic "LLD answer" is the derivation arc. A walkthrough must:

1. Show the naive design FIRST (§7).
2. Make the pain CONCRETE (§8) — name the future requirements, name the files that hurt.
3. Pivot WITH the reader, not for them. The pivot question is stated; the pattern is the answer.

❌ "We'll use the Strategy pattern for pricing."
✅ "Every new pricing rule touches three files in the naive design — that's the open/closed principle violation. The variability is *the algorithm itself*. The pattern that swaps an algorithm at runtime is Strategy."

### Rule 2 — Show SHAPES, not full implementations

Skeleton = abstract bases + 1-2 concrete classes per pattern. Comment out the rest with `// elided`. The reader should see the CHOICE, not the labor.

### Rule 3 — Mini-refresher boxes

Embed inline at first appearance. Never up-front in a "prerequisites" dump.

```markdown
> **Mini-refresher: Strategy pattern.**
>
> Encapsulates an algorithm behind an interface so it can be swapped at runtime. The CALLER decides which strategy to use; the strategy doesn't know about its peers.
>
> Quick example: a `Sorter` class takes a `CompareStrategy*` in its constructor. Pass `AscendingCompare` or `DescendingCompare` — the sorter doesn't care.
```

**Concepts that virtually always need a refresher when touched:**

- Strategy / State / Observer / Command / Decorator / Composite / Chain of Responsibility / Template Method / Iterator / Memento / Builder / Factory / Singleton / Abstract Factory
- SOLID (each principle on its first mention)
- Composition vs. inheritance
- Aggregation vs. composition (UML diamond)
- Dependency injection
- Open/closed principle
- Smart pointers (`std::unique_ptr` ownership, `std::shared_ptr` shared, `weak_ptr` for back-refs)
- Pure virtual / abstract base / `virtual ~Foo() = default`

### Rule 4 — Pattern-discrimination cheatsheets

When introducing a pattern, ALSO name the pattern's most-confused sibling AND the rule that separates them. Three-line format:

```markdown
**Strategy vs State.**
- *Strategy:* the caller picks which algorithm to use.
- *State:* the object picks (via internal transitions).
- *Rule of thumb:* if `context.setStrategy(x)` is called externally → Strategy. If `context.handleEvent(e)` flips state internally → State.
```

Sprinkle 1-2 per file.

### Rule 5 — Inline mermaid with anchor

Every diagram-bearing section gets an HTML anchor in its heading:

```markdown
## <a id="fig-class-diagram"></a>12. Final class diagram

```mermaid
---
config:
  look: handDrawn
  theme: default
---
classDiagram
  ...
```

A reading guide (1-3 sentences explaining what the diagram shows): ParkingLot composes Floor[]; each Floor composes Spot[]. The three Strategy interfaces hang off ParkingLot via aggregation. Ticket composes a TicketState which drives the lifecycle.
```

The reading guide replaces ASCII renderings. It's 1-3 sentences of prose explaining what the diagram shows, NOT a re-derivation.

### Rule 6 — C++ skeleton style

The repo's lingua franca for LLD is **C++17**. If the question explicitly demands Java/C#/Kotlin, switch and note the choice in the header.

**Style conventions:**

- Abstract base classes for interfaces: `class Foo { public: virtual ~Foo() = default; virtual void bar() = 0; };`
- `std::unique_ptr` for exclusive ownership; `std::shared_ptr` only when ownership is genuinely shared.
- `enum class` for typed enums (never bare `enum`).
- `const` correctness on getters and methods that don't mutate.
- Pass-by-const-reference for objects that don't change ownership.
- Forward declarations to break cycles. Comment them: `class Ticket; // forward — defined below`.
- `// elided` for stubs.

**Skeleton example:**

```cpp
class PricingStrategy {
public:
    virtual ~PricingStrategy() = default;
    virtual double computeFee(const Ticket& t) const = 0;
};

class FlatRate : public PricingStrategy {
public:
    FlatRate(std::unordered_map<SpotSize, double> hourly)
        : hourly_(std::move(hourly)) {}
    double computeFee(const Ticket& t) const override {
        const auto hours = std::ceil(t.durationHours());
        return hours * hourly_.at(t.spot().type());
    }
private:
    std::unordered_map<SpotSize, double> hourly_;
};
// other strategies elided
```

### Rule 7 — Each pivot is self-contained

A reader should be able to skim §7, §8, §9 alone and understand "naive → pain → first pattern." Don't refer ahead to §10 mid-§9 ("we'll also need State, but that's later"). Make each pivot stand alone.

### Rule 8 — Self-check ends every file

```markdown
> **Self-check — the question to ask next time.**
>
> When you see "design a [thing] with multiple [variations]," before reaching for inheritance, ask:
>
> > **"Is the variation a behavior the CALLER picks (Strategy) or a lifecycle state the OBJECT transitions through (State)?"**
>
> Behavior → Strategy. State → State. If both, both.
```

---

## Length targets

| Difficulty | Lines | Reading time |
|---|---|---|
| Medium (1-2 patterns) | 500-700 | ~30 min |
| Hard (3-4 patterns interacting) | 700-1000 | ~45 min |
| Senior bar (full multi-pattern: chess, framework, plugin host) | 900-1200 | ~60 min |

Going UNDER on §7 (naive design), §8 (where it hurts), or §§9-11 (pivots) is the most common failure mode — the walkthrough then reads as "assertion of an answer" instead of "derivation of an answer."

---

## Sub-concept inventory by LLD bucket

| Bucket | Likely sub-concepts |
|---|---|
| Object_Oriented_Design | composition vs inheritance, SOLID, polymorphism, aggregation diamond |
| LLD_DataStructures | encapsulation, invariant maintenance, templates, basic thread safety |
| SOLID_Principles | each of S/O/L/I/D with a counterexample |
| Strategy_Pattern | Strategy interface, runtime swap, context-vs-strategy ownership |
| State_Pattern | state interface, internal transitions, vs Strategy |
| Observer_Pattern | subject/observer, push vs pull, weak_ptr for back-refs, ordering |
| Command_Pattern | command interface, undo/redo, macro composition |
| Chain_of_Responsibility | next pointer, handle-or-pass, vs Pipeline |
| Template_Method | abstract base, hook methods, vs Strategy (inheritance vs composition) |
| Iterator_Pattern | external vs internal, lazy evaluation, STL iterator concept |
| Decorator_Pattern | wrapping chain, vs Composite, vs inheritance |
| Composite_Pattern | uniform tree, leaf vs composite, recursion in operations |
| Factory_Pattern | factory method vs abstract factory, vs Builder, vs `new` |
| Builder_Pattern | fluent API, telescoping-constructor avoidance, vs Factory |
| Singleton_Pattern | Meyers singleton, thread safety, anti-pattern caveat |
| Repository_Pattern | abstraction over persistence, vs DAO, unit-of-work boundary |
| Plugin_Architecture | extension point, dynamic loading via dlopen, isolation strategies |
| Dependency_Injection | constructor vs setter vs interface, container vs manual |
| Event_Sourcing | event log as source of truth, projections, replay, vs CRUD |
| Rule_Engine | evaluation order, condition-action pairs, conflict resolution |
| Retry_Pattern | exponential backoff with jitter, circuit breaker state machine |
| Interceptor_Pattern | cross-cutting concerns, AOP, vs middleware |

---

## Checklist for each new v2 LLD file

- [ ] Header with Difficulty / Time / Pattern focus + diagram-convention note
- [ ] "How to use this file" with map of sections + reading time
- [ ] §1: at least 4 clarifying questions
- [ ] §4: domain sketch (NOT code yet)
- [ ] §6: nouns → class/field + verbs → owner method
- [ ] §7: naive design WITH inline mermaid class diagram and ~30-50 lines of C++ skeleton
- [ ] §8: at least 3 future requirements walked through, naming file-touch impact + ends with pivot question
- [ ] §9, §10, §11: each pivot has a derivation, a mini-refresher (if new pattern), and a pattern-discrimination cheatsheet
- [ ] §12: final class diagram — inline mermaid block + anchor `id="fig-class-diagram"` on heading
- [ ] §13: skeleton code in C++ showing SHAPES
- [ ] §14: sequence diagram — inline mermaid sequenceDiagram block + anchor
- [ ] §15: extensibility re-check + named anti-patterns + first-person think-aloud + self-check
- [ ] Cross-references at bottom

---

## Workflow for applying this template

1. **Read the LeetLens question(s)** in `EXTRACTED_QUESTIONS.md` §1 (Net-new). Pick the canonical one to author.
2. **Draft on paper:**
   - Clarifying questions
   - Naive design (entity inventory + simple class diagram + ~30 lines of pseudo-C++)
   - The 3-5 hypothetical changes that should hurt the naive design
   - For each painful axis: name the pattern + the pattern you would reject
3. **Author the markdown** with inline mermaid blocks for diagrams. No PNG/SVG export step needed; mermaid renders natively in GitHub.
4. **Optional:** create a `.excalidraw` sibling if you want a freehand editable version. Not required.
5. **Run the checklist** before considering done.
6. **Update the bucket's `EXTRACTED_QUESTIONS.md`** to mark covered LeetLens rows.

---

## See also

- [`../CONTRIBUTING-v2.md`](../CONTRIBUTING-v2.md) — repo conventions
- [`../DSA/TEMPLATE-v2.md`](../DSA/TEMPLATE-v2.md) — DSA flavor
- [`../TEMPLATE-v2.md`](../TEMPLATE-v2.md) — JS flavor
- [`../HLD/TEMPLATE-v2.md`](../HLD/TEMPLATE-v2.md) — HLD flavor
- [`./LEARNING.md`](./LEARNING.md) — LLD vertical overview
- **Canonical sample:** [`./Topics/Object_Oriented_Design/Parking_Lot.md`](./Topics/Object_Oriented_Design/Parking_Lot.md)
