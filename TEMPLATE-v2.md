# Question File Template — v2 (Learner-First)

This is the canonical structure every question file should follow. v2 reorders the v1 template so a **first-time learner** can read top-to-bottom and build understanding before seeing the answer.

> **Design principle:** write from *the problem's* perspective, not *the answer's*. A reader who has never seen the question should know **what they're being asked**, **why it's hard**, **how to think about it**, and **only then** see the solution.

---

## File anatomy

```
# <Title — one sentence; the headline result>

> **Difficulty:** Easy / Medium / Senior   |   **Time:** ~10/25/45 min   |   **Prereqs:** [link to primer or sibling file]

## 1. Problem statement
## 2. Plain-English restatement
## 3. Why this matters in interviews
## 4. Mental model
## 5. Try it yourself first
## 6. Brute force — walked through
## 7. The unlocking insight + journey to optimal
## 8. Solution (annotated)
## 9. Step-by-step dry run
## 10. Common confusion + traps
## 11. Senior follow-ups & variants
## 12. How to think aloud in the interview
## 13. 60-second revision block

---

> **Related:** [sibling files] · **Concept primer:** [link]
```

---

## Section guidance

### Header
- **Title** — declarative one-liner. Not "Counter" — "Build a counter factory that retains private state across calls."
- **Difficulty chip** — Easy / Medium / Senior. Calibrate by "what % of senior candidates miss this": Easy = 0-10%, Medium = 10-40%, Senior = 40%+.
- **Time** — realistic time-to-solve at the whiteboard once you understand the pattern. Easy ≤ 10m, Medium ≤ 25m, Senior ≤ 45m.
- **Prereqs** — markdown link to a primer or sibling file. If none, "none."

### 1. Problem statement (NEW)
Three blocks, all explicit:

```
**Signature:** function createCounter(n: number): () => number

**Input/Output examples**
| Input                | Returned function called 3× | Output      |
|----------------------|------------------------------|-------------|
| createCounter(10)    | c(); c(); c();              | 10, 11, 12  |
| createCounter(0)     | c(); c();                   | 0, 1        |
| createCounter(-5)    | c();                        | -5          |

**Constraints**
- 1 ≤ n ≤ 1000 (or whatever the source says)
- The returned function may be called up to 1000 times.
- Each `createCounter()` call must return an INDEPENDENT counter.
```

This is the single biggest pedagogical lift. Do not skip.

### 2. Plain-English restatement (NEW)
One paragraph in conversational language. "The interviewer hands you a function `createCounter(n)` and asks you to make it return another function. Every time *that* returned function is called, it gives you back the next number in sequence, starting from `n`."

### 3. Why this matters in interviews
- Keep, but **trim pressure language**.
- 1 short paragraph (3-5 sentences). What skill is tested. Where the pattern reappears in production.
- ❌ Avoid: "Whiff this and the rest of the round goes downhill."
- ✅ Prefer: "This is the smallest example that exercises [skill X]. The same shape reappears in [Y, Z]."

### 4. Mental model (MOVED EARLIER)
- 2-4 sentences + ASCII diagram.
- Goal: a *picture* the reader can hold in their head before reading any code.
- Counter: "imagine a vault with a number inside. The factory hands out an opener. The opener reveals the number, then bumps it up by 1."
- Diagram is mandatory. Even crude `┌──┐` boxes.

### 5. Try it yourself first (NEW)
A short callout box. 1-3 prediction prompts. Examples:

> **Predict before reading on:**
> 1. If you call `createCounter(0)` twice and run each one, do they share state? Why or why not?
> 2. Should `return n++` or `return ++n` be used? What does each produce on the first call?
> 3. Could you implement this without using `function`/`class`?

This forces engagement. Even a quick "I'd guess..." attempt makes the next sections stick.

### 6. Brute force — walked through (EXPANDED)
Replace v1's one-line dismissal with a real walkthrough:

```
**Attempt 1: global counter**
```js
let n = 0;
function createCounter() { return () => n++; }
```
Looks fine. But: two callers of `createCounter()` share the *same* `n`. If they meant independent counters, this is wrong. Demo:
```js
const a = createCounter(); const b = createCounter();
a(); a(); b();  // a returned 0,1; b returned 2 — leaked
```
Lesson: we need per-instance isolation, not module-level state.

**Attempt 2: parameter as variable**
```js
function createCounter(n) { return () => n++; }
```
Works. Why? Each call to `createCounter` creates its own `n`. That's the insight we'll formalize in section 7.
```

This is where learners actually grow. Walk *through* failure, not past it.

### 7. The unlocking insight (NEW)
A single bolded sentence that captures the trick, followed by 2-3 paragraphs explaining the principle from first principles.

For counter: **"Every function call creates a fresh local environment, and a returned inner function keeps that environment alive."**

Explain LE/scope-chain *here*, with the example actively in front of the reader. Don't pre-emptively dump theory.

### 8. Solution (annotated)
Code block. Each meaningful line gets an inline comment that explains *what it's doing* and *why*.

```js
function createCounter(n) {        // step 1: outer function holds the private slot `n`
  return function () {              // step 2: the inner function is what gets returned
    return n++;                     // step 3: post-increment — returns current value, then bumps
  };
}
```

Below the code block, a small **try-it** snippet with expected output as comments:

```js
const c = createCounter(10);
console.log(c());  // 10
console.log(c());  // 11
console.log(c());  // 12
```

### 9. Step-by-step dry run
Use a table. **Values first. Engine internals second.**

| Step | Action      | Value of `n` (in closure) | Returned | Notes |
|------|-------------|---------------------------|----------|-------|
| init | `createCounter(10)` | 10 | (function) | new LE created |
| 1    | `c()`       | 10 → 11                   | 10       | post-increment |
| 2    | `c()`       | 11 → 12                   | 11       | same LE |
| 3    | `c()`       | 12 → 13                   | 12       | same LE |

Below the table, **optionally** a collapsed `<details>` block for engine internals (LE pointers, call-stack frames). A learner who wants depth opens it; a learner who wants the answer skips it.

### 10. Common confusion + traps
Merge v1's "edge cases / interview traps" with the newer "common beginner confusion." Numbered list. Each item: **the misconception → the correction → a 1-line example**.

```
1. **"Each call resets `n`."** False — `n` lives in the outer LE which is shared across inner calls.
   Example: `c(); c();` → 10, 11 (not 10, 10).

2. **"Two factories share state."** False — each `createCounter()` makes a fresh LE.
   Example: `const a=createCounter(0); const b=createCounter(0); a();b();` → both return 0.

3. ...
```

### 11. Senior follow-ups & variants
Expand v1's variants section. Each variant gets a paragraph + (optional) code sketch:

```
**1. Counter II — `{ inc, dec, reset }`**
The interviewer extends the question. Now the factory returns an object with three methods, all closing over the same `n`. This generalizes the pattern: a closure can host *multiple* operations sharing private state — the closure-based module pattern in 6 lines.

```js
function createCounter(init) {
  let n = init;
  return {
    inc: () => ++n,
    dec: () => --n,
    reset: () => { n = init; return n; },
  };
}
```

**2. Counter with peek** ...

**3. Class with `#field` vs closure** — compare tradeoffs ...
```

### 12. How to think aloud in the interview
3-5 beats of the candidate's monologue. First-person voice. What you'd literally say while reaching for the marker:

> "Right — I need a function that, when called, returns *another* function. The inner one needs to remember a number across calls without exposing it externally. That's a closure: outer creates `n`, inner reads/mutates it. Post-increment so the first call returns the initial value. Two factory calls should be independent — they will be, because each call creates a fresh local environment. Let me write it."

### 13. 60-second revision block
Unchanged from v1. Tight bullets. Designed for the morning-of cram.

---

## Style notes

### Voice
- Mentor explaining to a smart peer who's encountering this fresh.
- Conversational, not corporate. Confident, not pressured.
- ❌ "Whiff this and you fail." ✅ "This is a high-frequency warmup; getting it cleanly signals strong fundamentals."

### Code blocks
- Annotated solutions get inline `// step N` comments.
- Show **expected output as comments** next to runnable examples — don't put it in a separate code block.
- Use ` ```js ` for runnable JS, plain ` ``` ` for ASCII diagrams.

### ASCII diagrams
- Always use code fences with no language so they render monospaced.
- Reach for them in sections 4 (Mental model), 9 (Dry run), and wherever state changes over time.

### Tables
- Markdown tables for I/O examples, dry-run traces, comparison axes.
- Three-column max for readability on narrow viewports.

### Length targets
- Easy file: 180-280 lines.
- Medium file: 250-400 lines.
- Senior file: 350-550 lines.
- Going over isn't sin — going *under* on sections 1, 5, 6, 7, 12 is.

### "Try it yourself" prompts
- Phrase as a question, not a directive.
- 1-3 max — more becomes a chore.
- Don't put the answer next to the prompt; the reader should commit to a prediction first.

---

## Migration checklist (for retro-fitting v1 files)

For each existing file:

- [ ] Add header chip line (Difficulty / Time / Prereqs).
- [ ] Add section 1 (Problem statement with I/O table).
- [ ] Add section 2 (Plain-English restatement).
- [ ] Move/create section 4 (Mental model) before any solution code.
- [ ] Add section 5 (Try it yourself).
- [ ] Expand section 6 (Brute force) from one-line dismissal to actual walkthrough.
- [ ] Add section 7 (Unlocking insight) — the bold one-sentence + 2-3 paragraph principle.
- [ ] Add inline `// step N` comments to the solution code in section 8.
- [ ] Restructure section 9 (Dry run) — table first, internals collapsed.
- [ ] Merge old "edge cases / traps" with new "common confusion" → section 10.
- [ ] Expand section 11 (Variants) — each gets a paragraph + optional sketch.
- [ ] Add section 12 (How to think aloud) — 3-5 beats, first-person.
- [ ] Soften pressure language across all sections.
- [ ] Add bottom-of-file links: `**Related:** ...` and `**Concept primer:** ...`.

---

## Exemplar

See [`02-closures/counter.v2.md`](javascript-interview-prep/questions/02-closures/counter.v2.md) for the canonical worked example. Every new or migrated file should match its shape and voice.
