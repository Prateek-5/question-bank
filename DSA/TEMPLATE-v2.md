# DSA v2 Teaching Template

**Purpose.** Original problem files in each topic folder (`Topics/X/Problem.md`) are **reference cards** — good once you've understood the solution and want a quick refresh. They list the trick and explain why it works, but they assume you already see the trick.

**v2 files** live in a parallel **`learn/`** subfolder inside each topic (`Topics/X/learn/Problem.md`) and are **teaching walkthroughs** — they hand-hold a learner who has never seen the problem before, building every sub-concept inline so the reader never has to switch tabs or look something up elsewhere.

> Canonical example to read first: [`Topics/Arrays_and_Matrices/learn/Total_Hamming_Distance.md`](./Topics/Arrays_and_Matrices/learn/Total_Hamming_Distance.md). Every v2 file should feel like that.

---

## Audience assumption (zero-prior-knowledge contract)

A v2 file MAY assume the reader knows:

- For loops, while loops, basic `if/else`.
- Arrays / indexing (`nums[i]`).
- Basic arithmetic (`+`, `−`, `×`, `/`, `%`).
- Variable assignment.

A v2 file MAY NOT assume the reader knows, without an inline refresher:

- Binary representation, bits, bit positions.
- Bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`).
- Modular arithmetic ("mod K").
- What XOR / AND / OR mean at the bit level.
- Popcount / built-in bit counters.
- Counting combinations (`n choose 2`, multiplication rule).
- Big-O notation or what "TLE" means.
- Recursion / the call stack.
- Stack, queue, hash map, set as data structures.
- Tree / graph terminology.
- BFS / DFS.
- Dynamic programming, memoization, "state."
- Greedy proofs / exchange arguments.
- Segment trees, Fenwick trees, tries.
- Floyd's tortoise and hare.
- Two-pointer pattern.
- Sliding window pattern.

**If the problem touches any of these, embed a mini-refresher box where the concept first appears.** See the format below.

---

## The 11 required sections

Every v2 file follows this skeleton. Some sections may collapse to a sentence for trivial problems; none may be omitted (use "N/A — this problem is simple enough" for explicit waivers).

### Section header (top of file)

```markdown
# Problem Name — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Problem.md`](../Problem.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/..." target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/...</a>
```

> **External link policy** — all `http(s)://` URLs in this repo use HTML anchors with `target="_blank" rel="noopener noreferrer"` so they open in a new tab. Plain markdown can't enforce target; HTML is required. See [`../CONTRIBUTING-v2.md`](../CONTRIBUTING-v2.md) §7 for the policy + bulk-conversion script. Internal relative links (e.g., `[../sibling.md](../sibling.md)`) stay as plain markdown so the reader can navigate the repo in the same tab.

### Section "How to use this file"

```markdown
## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~N minutes if you do every small example by hand. Every concept the problem touches — X, Y, Z — is explained **inline** so you don't have to go to another tab.

**Map of this file (N short sections):**

1. Read the problem and translate it
2. The natural first attempt
3. Why that fails
4. The pivot — looking at it a different way
5. The shortcut / derivation
6. ... (problem-specific)
N. The shape — when else this trick applies + self-check
```

### Required body sections

1. **Read the problem and translate it.** Restate in your own words. Worked example with concrete numbers. Inline mini-refreshers for each unfamiliar term.

2. **The natural first attempt.** WITH CODE. The obvious-but-slow approach. Trace it on the small example.

3. **Why the brute force fails.** Concrete number bottleneck: "for `n = 10⁴`, that's ~5×10⁷ pairs → 16 seconds → TLE." Not generic "too slow."

4. **The pivot — stated as a QUESTION.** Not "think about each bit." Instead: "What if we consider one bit at a time?" The question is the bridge.

5. **Derive the answer from the pivot.** Plain arithmetic on the small example. **No formal notation** (no LaTeX, no sigma, no abstract `∀ ∃`). Show the move concretely — regroup, count, simplify — *then* name the result.

6. **Sub-concept refreshers as needed.** If the solution uses a non-trivial coding idiom (e.g. `(x >> b) & 1`, `head.next.next = head`, deque-from-both-ends), insert a refresher box here.

7. **The full algorithm + code.** Annotated. Comments only on lines that aren't self-explanatory.

8. **Trace the code line-by-line on the small example.** Not just "the algorithm produces..." — actually evaluate the operators step by step.

9. **Complexity comparison.** Brute vs new, in concrete numbers. "1000× faster on max input."

10. **Common pitfalls.** Specific bugs a learner WILL hit if they're not careful. Not generic "watch for edge cases."

11. **The shape — when else this trick applies + self-check.** Table with YES + NO rows showing which sibling problems share the shape. End with a single question the learner should ask themselves next time they see this kind of problem.

### Cross-references (bottom)

```markdown
## Cross-references

- **Reference card (post-mastery):** [`../Problem.md`](../Problem.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`...`]
```

---

## Style rules

### Rule 1 — No LaTeX in the body

LaTeX (`$...$`, `$$...$$`, `\sum`, `\frac`, `\mathbb{1}`) does NOT render reliably in markdown viewers. Even when it renders, formal notation is a wall for learners who don't already know the math.

**Allowed:** plain ASCII arithmetic, ASCII tables, code blocks.

**Replace this:** `$$\text{Total} = \sum_{b=0}^{31} c_b \times (n - c_b)$$`

**With this:**
```
Total over all bits = 0 + 2 + 2 + 2 = 6
```
or
```
For each bit b:
    c = count of numbers with bit b set
    total += c × (n − c)
```

### Rule 2 — Plain arithmetic before any formula

When introducing a counting / aggregation formula:

1. **First**, work it out by hand on the small example. Show the literal numbers being added/multiplied.
2. **Then** name the pattern.
3. **Only at the end**, write the compact formula (in plain ASCII, like `c × (n − c)`).

The reader should think *"oh, I just did that with my hands"* — not *"here's a formula I have to decode."*

### Rule 3 — Mini-refresher boxes

Format:

```markdown
> **Mini-refresher: <concept name>.**
>
> <30–60 seconds of explanation>
>
> Quick example: ...
```

Boxed using markdown blockquote (`>`). Embed inline at the **first** point the concept appears, never up-front in a "prerequisites" dump.

**Concepts that virtually always need a refresher:**

- Bit positions / binary representation (whenever bits come up)
- XOR semantics (`differ` vs `same`)
- Counting pairs (`n × (n-1) / 2`)
- Multiplication rule for counting cross-pairs
- `(x >> b) & 1` bit-test idiom
- Floyd's cycle algorithm setup (when "slow/fast pointers" appear)
- Recursion call stack (when stack depth matters)
- Stable vs unstable sort (when stability matters)
- Adjacency list / adjacency matrix (whenever graphs appear)
- DP state vs transition (first DP problem in any topic)
- Modular arithmetic (whenever `mod K` appears)
- Heap / priority queue invariant (whenever heap appears)

### Rule 4 — Mini-exercises with collapsible answers

Encourage active engagement at least once per file:

```markdown
> **Mini-exercise:** What does `(4 >> 1) & 1` return?
>
> <details>
> <summary>Click to expand answer</summary>
>
> - `4 >> 1` = `0010` = 2
> - `2 & 1` = `0000` = 0
> - So bit 1 of 4 is 0. ✓
> </details>
```

Place after introducing a concept, before using it heavily. Two or three per file is plenty.

### Rule 5 — Pivot stated as a question, before its answer

The "aha" moment in a problem deserves its own section. State the move as a **question**, then derive the answer.

**Bad:** "Think about each bit independently."
**Good:** "What if we count contributions per bit instead of per pair?"

**Bad:** "We do a backward DP."
**Good:** "Forward DP would need to track two pieces of state. What if we reverse the direction — what do we need to enter this cell to survive from here?"

### Rule 6 — Line-by-line code trace

Not just "the algorithm produces X on input Y." Actually evaluate the operators:

```
b = 1:
  scan:
    x = 4:  (4 >> 1) & 1 = (2) & 1 = 0. Not set.
    x = 14: (14 >> 1) & 1 = (7) & 1 = 1. Set!  c = 1.
    x = 2:  (2 >> 1) & 1 = (1) & 1 = 1. Set!  c = 2.
  total += 2 * (3 − 2) = 2.  total = 2.
```

### Rule 7 — Self-check at the end

End every file with a single, concrete question the learner should ask themselves the next time they see a similar problem. This is the **transferable skill** — the pivot question, generalized.

```markdown
> **Self-check — the question to ask next time.**
>
> When you see a problem asking for **<some category of aggregation>**, before reaching for a nested loop, ask:
>
> > **"<the precise reframing question>"**
>
> If yes, you've turned `O(n²)` into `O(n)`.
```

### Rule 8 — Transfer table with NO column

Don't just list "where else this works." Also list "where it looks like it should work but doesn't" — the NO column. It teaches discrimination, not just recognition.

| Problem | Decomposes by | YES/NO |
|---|---|---|
| Total Hamming Distance | bit position | ✅ |
| Sum of XOR over pairs | bit position | ✅ |
| Sum of `a_i × a_j` over pairs | — | ❌ (product doesn't decompose per-bit) |

---

## Length targets

| Difficulty | Lines | Reading time |
|---|---|---|
| Trivial (Fizz Buzz, Concatenation) | 200–300 | ~10 min |
| Easy-Medium (most array / linked list) | 400–550 | ~20 min |
| Medium-Hard (sliding window, DP intro) | 500–700 | ~30 min |
| Hard (Edit Distance, Maximal Rectangle, advanced DP/graph) | 700–900 | ~45 min |

If you blow past these, you're either explaining something the reader doesn't need OR splitting the problem into multiple files.

---

## Sub-concept inventory by topic

Use this as a checklist when writing v2 files in each topic — these are the concepts that almost always need an inline refresher.

| Topic | Likely sub-concepts |
|---|---|
| Arrays_and_Matrices | row/column indexing, in-place mutation |
| 1_D_and_2_D_Arrays | prefix sum, 2D prefix sum inclusion-exclusion, index mapping |
| Two_Pointers | "shorter side" reasoning, dedup-while loops, monotonicity proofs |
| Hashing_Sliding_Window | hash map default value, prefix-sum-and-hash idiom, window invariants |
| Stack | LIFO mental model, monotonic stack pop reasoning, popcount via stack |
| Linked_List | dummy head, slow/fast, three-pointer reverse, Floyd's math |
| Searching_Binary_Search | lower/upper bound templates, binary-search-on-answer monotonicity |
| Math | GCD via Euclid, modular reduction, closed-form vs simulation |
| Bit_Manipulation | binary, all 6 bit ops, bit-test idioms, popcount, two's complement |
| Queues | FIFO, two-stack queue, monotonic deque, sliding window of indices |
| Sorting | comparator semantics, stability, partition (Lomuto/Hoare), quickselect |
| Recursion | call stack, choose/explore/unchoose, snapshot copy |
| Backtracking | constraint set tracking, pruning, depth limit |
| Trees | node structure, the 4 traversals, recursion-on-trees pattern |
| BST | BST property, inorder=sorted |
| Trie | character trie, bit trie, prefix matching |
| Heap | heap invariant, push/pop, two-heap median trick, size-k heap |
| Graph | adjacency representations, visited set, BFS queue, DFS stack, topological order, DSU primitives, Dijkstra's relaxation |
| Greedy | exchange argument, sort-then-pick, interval scheduling end-sort |
| DP | state, transition, base case, rolling-array space optimization, top-down vs bottom-up |
| Segment Tree | range query primitive, lazy propagation, tree-as-array indexing |
| Number Theory | sieve of Eratosthenes, fast exponentiation, divisor enumeration up to √n |

---

## Checklist for each new v2 file

Before submitting a v2 file, verify:

- [ ] Header with reference link + problem link
- [ ] "How to use this file" with reading-time estimate + map of sections
- [ ] Section 1 has a worked example with concrete numbers
- [ ] Every sub-concept the problem touches has an inline refresher box on first appearance
- [ ] No LaTeX / formal math notation anywhere in the body
- [ ] Brute force shown WITH CODE, then traced on the small example
- [ ] "Why brute fails" gives a concrete number (TLE math)
- [ ] Pivot stated as a **question** before its answer
- [ ] Derivation works through plain arithmetic on the small example before stating any formula
- [ ] At least one mini-exercise with collapsible answer
- [ ] Code trace evaluates operators line-by-line, not just step-by-step
- [ ] Complexity comparison gives concrete numbers
- [ ] Pitfalls section lists specific bugs, not generic edge cases
- [ ] Shape / transfer table includes a NO column
- [ ] Self-check ends with a concrete question the learner can carry forward
- [ ] Cross-references link to original file + LEARNING.md + related v2 files
- [ ] File length within target band for the problem's difficulty

---

## Workflow for applying this template

1. **Read the original file** in `Topics/X/Problem.md`. Note the trick, the algorithm, the existing trace.
2. **Score against the rubric** (8 criteria from sample-rating exercise). Identify which sections need building from scratch vs reshuffling vs lifting from the original.
3. **List sub-concepts the problem touches.** For each, decide if it needs a refresher box.
4. **Write the v2 file** in `Topics/X/learn/Problem.md` following the 11-section skeleton.
5. **Run the checklist above** before considering it done.
6. **Update the topic's `LEARNING.md`** to link to the v2 file ("→ for first-time study, see `learn/Problem.md`; for revision, see `Problem.md`").
