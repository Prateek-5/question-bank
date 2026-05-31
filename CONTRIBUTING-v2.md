# Contributing — Repo Conventions (v2)

> The repo-level umbrella document. Read this once before adding new content.
> It does NOT replace the topic-specific templates — it tells you where to find them, when to use them, and the conventions every file must follow.

---

## 1. What this repo is

A self-paced, interview-prep question bank with **five verticals**:

| Vertical | Path | What lives there |
|---|---|---|
| **DSA** (algorithms) | `DSA/Topics/<Topic>/` | 226 v1 problems across 22 topics + `EXTRACTED_QUESTIONS.md` manifests from LeetLens |
| **JavaScript** | `javascript-interview-prep/questions/<NN-topic>/` | ~232 question files across 10 folders + LeetLens overflow manifest |
| **Backend** | `backend-data-prep/questions/<topic>/` | Net-new question bank for backend interviews |
| **LLD** (Low-Level Design) | `LLD/Topics/<Pattern>/` | NEW — seeded from LeetLens: 146 questions across 19 design-pattern buckets, metadata-only manifests, walkthroughs TBD |
| **HLD** (High-Level Design) | `HLD/Topics/<Archetype>/` | NEW — seeded from LeetLens: 357 questions across 17 system-design archetype buckets, metadata-only manifests, walkthroughs TBD |

The two algorithmic-content verticals (DSA + JS) follow the **two-tier learning model** (reference card + teaching walkthrough). The two new design verticals (LLD + HLD) are currently metadata-only; their templates are placeholders.

---

## 2. The two-tier learning model

Every problem can have **two** files:

| Tier | File path pattern | Purpose | Voice |
|---|---|---|---|
| **Reference card** | `Topics/X/Problem.md` (DSA) · `questions/NN-topic/problem.md` (JS) | Quick refresh AFTER mastery — list the trick, why it works, the code | Compact, assumes the reader already saw the problem once |
| **Teaching walkthrough** | `Topics/X/learn/Problem.md` (DSA) · *(coming)* `questions/NN-topic/learn/problem.md` (JS) | First-time learner — hand-hold through every sub-concept inline | Paced, mentor-to-peer, refreshers built in |

**Rule:** if you're adding a new question, START with the reference card. Add the walkthrough only when you've proven the topic is worth deep-paced treatment.

---

## 3. Where the templates live

| Template | Path | When to use |
|---|---|---|
| **DSA walkthrough template** | [`DSA/TEMPLATE-v2.md`](./DSA/TEMPLATE-v2.md) | Any new file in `DSA/Topics/X/learn/` |
| **JS walkthrough template** | [`TEMPLATE-v2.md`](./TEMPLATE-v2.md) (repo root) | Any new file in `javascript-interview-prep/` |
| **JS counter exemplar** | [`javascript-interview-prep/questions/02-closures/counter.md`](./javascript-interview-prep/questions/02-closures/counter.md) | Canonical worked example for the JS template |
| **DSA exemplar** | [`DSA/Topics/Arrays_and_Matrices/learn/Total_Hamming_Distance.md`](./DSA/Topics/Arrays_and_Matrices/learn/Total_Hamming_Distance.md) | Canonical worked example for the DSA template |

The two templates are **intentionally separate**. DSA is algorithmic (brute force → pivot → optimal). JS is concept/behavior-driven (mental model → mechanism → traps). Don't merge them.

---

## 4. Repo layout

```
bosscode-question-bank/
├── CONTRIBUTING-v2.md              ← you are here
├── COVERAGE.md                     ← original audit + migration history
├── TEMPLATE-v2.md                  ← JS walkthrough template
├── DSA/
│   ├── TEMPLATE-v2.md              ← DSA walkthrough template
│   ├── EXTRACTED_UNCATEGORIZED.md  ← 5 niche LeetLens DSA rows (hand-review)
│   └── Topics/<TopicName>/
│       ├── LEARNING.md             ← topic navigator: study order + dual-tier links
│       ├── Concepts.md             ← theory primer
│       ├── <Problem>.md            ← reference card (v1, generator-produced)
│       ├── EXTRACTED_QUESTIONS.md  ← LeetLens question manifest (metadata only)
│       └── learn/
│           └── <Problem>.md        ← teaching walkthrough (v2)
├── LLD/                            ← NEW: Low-Level Design (LeetLens-seeded)
│   ├── LEARNING.md                 ← vertical overview + bucket study order
│   ├── TEMPLATE-v2.md              ← PLACEHOLDER — LLD-specific template TBD
│   └── Topics/<Pattern>/
│       ├── EXTRACTED_QUESTIONS.md  ← LeetLens question manifest (metadata only)
│       └── <Question>.md           ← walkthrough (author later)
├── HLD/                            ← NEW: High-Level Design (LeetLens-seeded)
│   ├── LEARNING.md                 ← vertical overview + bucket study order
│   ├── TEMPLATE-v2.md              ← PLACEHOLDER — HLD-specific template TBD
│   ├── EXTRACTED_UNCATEGORIZED.md  ← 3 niche LeetLens HLD rows
│   └── Topics/<Archetype>/
│       ├── EXTRACTED_QUESTIONS.md
│       └── <Question>.md           ← walkthrough (author later)
├── javascript-interview-prep/
│   ├── concepts/                   ← shared JS concept primers
│   ├── EXTRACTED_QUESTIONS.md      ← 56 LeetLens JS-overflow rows
│   └── questions/<NN-topic>/
│       ├── INDEX.md                ← folder navigator
│       └── <question>.md           ← reference card + walkthrough live in one file currently
├── backend-data-prep/
│   └── questions/<topic>/
│       └── <question>.md
├── leetlens-import/                ← categorization catalogue (not content)
│   ├── STUDY-GUIDE.md              ← 12-week cross-vertical sequence
│   ├── DSA-questions.md
│   ├── LLD-questions.md
│   ├── HLD-questions.md
│   ├── overlaps.md
│   ├── INDEX.md
│   └── categorization-method.md
└── generator/                      ← Python scripts that emit DSA reference cards from Excel
    ├── generate.py
    ├── utils.py                    ← link policy lives here (see §7)
    └── data_*.py
```

---

## 5. Naming conventions

### File names

- **DSA reference card:** Match the LeetCode/source title, with non-alphanumeric chars replaced by `_`. Examples: `Two_Sum.md`, `Construct_Binary_Tree_from_Inorder_and_Postorder.md`.
- **DSA walkthrough:** Same filename as the reference card, placed in the `learn/` subfolder.
- **JS question:** lowercase-kebab-case based on what the question demonstrates. Examples: `counter.md`, `debounce.md`, `loop-closure-var-let.md`.
- **Backend question:** lowercase-kebab-case describing the scenario. Examples: `redis-redlock-distributed-lock.md`, `mongo-shard-key-design.md`.

### Folder names

- **DSA topics:** Title_Case_With_Underscores (e.g., `Dynamic_Programming_DP`). The generator's `clean_topic()` produces this from the Excel topic name.
- **JS topics:** `NN-kebab-name` (e.g., `02-closures`, `10-machine-coding-patterns`). The NN prefix preserves study order.
- **Backend topics:** lowercase-kebab (e.g., `transactions-concurrency`).

---

## 6. The five-step "add a new question" runbook

This is the canonical workflow. Skip steps only if you have a deliberate reason.

### For a DSA problem

1. **Add the reference card** at `DSA/Topics/<Topic>/<Problem>.md`. Either:
   - Add a row to the Excel sheet + a content dict in the matching `generator/data_<topic>.py`, then run `python3 generator/generate.py`, OR
   - Hand-write the file using the existing reference cards as a template.
2. **(Optional, recommended)** Add the walkthrough at `DSA/Topics/<Topic>/learn/<Problem>.md` following [`DSA/TEMPLATE-v2.md`](./DSA/TEMPLATE-v2.md).
3. **Update `LEARNING.md`** in the topic folder: add an entry under the correct sub-section in "Problems in study order" with BOTH the reference link AND the `[walkthrough →](./learn/<Problem>.md)` link (see existing entries for format).
4. **Cross-reference adjacent walkthroughs.** Edit nearby `learn/*.md` files to add this one in their "Coming next" footer.
5. **Verify** — run the `external_links_new_tab.py` script if you added any new external URLs (see §7), or just write them as `<a target="_blank">` directly.

### For a JS or Backend question

1. **Create the file** at the appropriate `questions/<topic>/<name>.md` path.
2. **Follow [`TEMPLATE-v2.md`](./TEMPLATE-v2.md)** (the root one — JS-flavored) for structure.
3. **Update the folder's `INDEX.md`** if one exists; otherwise create it.
4. **Cross-link** to related files in the footer.
5. **External links:** use `<a target="_blank">` form directly (see §7).

---

## 7. External link policy (REPO-WIDE)

**All external (http/https) links MUST open in a new tab.** Markdown alone can't do this, so we use HTML anchors:

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">example</a>
```

This is enforced across the repo (504 files were swept on 2026-05-25). Three places this matters:

| Where | What to do |
|---|---|
| Writing a new `.md` by hand | Use the HTML anchor form directly. Don't write bare `https://...` or `[text](https://...)`. |
| Editing the generator (`generator/utils.py`) | The link emission is already wrapped — see `link_html` in `make_question_md`. Don't revert it. |
| Bulk-converting old files | Run `python3 /tmp/external_links_new_tab.py` (idempotent; safe to re-run). The script is at the path used during the original sweep — recreate it from git history if missing. |

**Internal links** (relative paths like `./learn/foo.md` or `../sibling.md`) should remain plain markdown — they stay in the same tab so the reader can navigate the repo.

---

## 8. House style (voice, length, formatting)

These rules apply across DSA and JS walkthroughs. The two templates specialize them further.

### Voice

- **Mentor explaining to a smart peer**, not corporate / pressured.
- ❌ "Whiff this and you fail the round."
- ✅ "This is a high-frequency warmup; getting it cleanly signals strong fundamentals."

### Length targets

| Difficulty | Lines | Reading time |
|---|---|---|
| Trivial (Fizz Buzz, Concatenation, Climbing Stairs) | 200–300 | ~10 min |
| Easy-Medium (most array / closure / promise problems) | 300–550 | ~15–20 min |
| Medium-Hard (sliding window, DP intro, regex matching) | 500–700 | ~25–30 min |
| Hard / Senior bar (Edit Distance, Maximal Rectangle, Dungeon Game, hard async) | 700–900 | ~40–45 min |

If you blow past these, you're either over-explaining or the file should be split.

### Code blocks

- Use ` ```js ` for JavaScript, ` ```cpp ` for C++, ` ```python ` for Python, plain ` ``` ` for ASCII diagrams.
- **Annotate** the canonical solution with `// step 1`, `// step 2` comments.
- **Show expected output inline** as comments: `console.log(c());  // 10`. Don't put it in a separate output block.

### Tables

- Markdown tables for I/O examples, complexity comparisons, transfer tables.
- Three columns max for readability on narrow viewports.

### Mini-refreshers (a DSA convention worth using everywhere)

Inline blockquote, embedded at the FIRST point a non-trivial concept appears (never up-front in a "prerequisites" dump):

```markdown
> **Mini-refresher: <concept name>.**
>
> <30–60 seconds of explanation>
>
> Quick example: ...
```

See [`DSA/TEMPLATE-v2.md`](./DSA/TEMPLATE-v2.md) §"Rule 3" for the canonical format and a list of concepts that virtually always need one.

### The "Shape" closing section (transferable skill)

Every walkthrough ends by naming the **shape / pattern** and showing where else it applies. Include a NO column so the reader learns discrimination, not just recognition:

| Problem | Decomposes by | YES/NO |
|---|---|---|
| Total Hamming Distance | bit position | ✅ |
| Sum of XOR over pairs | bit position | ✅ |
| Sum of `a_i × a_j` over pairs | — | ❌ (product doesn't decompose per-bit) |

### Self-check question

End every walkthrough with ONE concrete question the learner can ask themselves the next time they see a similar problem. This is the **transferable skill** the file ships.

```markdown
> **Self-check — the question to ask next time.**
>
> When you see a problem asking for <category>, before reaching for the obvious approach, ask:
>
> > **"<the precise reframing question>"**
```

---

## 9. The `LEARNING.md` (topic navigator) format

Every DSA topic folder has a `LEARNING.md`. It serves as the topic's table of contents. After the 2026-05-25 dual-tier update, every problem entry has TWO links:

```markdown
1. **[Problem_Name.md](./Problem_Name.md)**  ·  [walkthrough →](./learn/Problem_Name.md) — One-line description. **must-do**
```

The script at `/tmp/update_learning.py` (used during the 2026-05-25 update) appends walkthrough links automatically — re-run it after adding new `learn/` files if you don't want to update by hand.

A "Two-tier format" note appears at the top of each updated `LEARNING.md` under the existing topic blurb. Preserve it.

---

## 10. The generator (DSA reference cards)

The reference cards in `DSA/Topics/<Topic>/<Problem>.md` are emitted from `generator/generate.py` reading `DSA_Questions.xlsx`.

| File | Role |
|---|---|
| `generator/generate.py` | Main entry — reads Excel, dispatches to topic data files, writes `<Problem>.md` files |
| `generator/utils.py` | Shared helpers: `clean_topic`, `clean_title`, `write`, `make_question_md` (link policy lives here) |
| `generator/data_<topic>.py` | Per-topic dict of `{title: {concept, intuition, ..., code, followups}}` |
| `generator/topic_concepts.py` | Per-topic `Concepts.md` content |
| `generator/teaching_concepts.py` · `teaching_format.py` | Pedagogical-layer helpers (not used by current main flow) |

To regenerate: `python3 generator/generate.py` from the repo root. It's destructive (overwrites existing reference cards). If you've hand-edited a reference card, either commit that change to the matching data dict OR don't re-run the generator.

**The generator preserves the link policy** — `make_question_md` wraps the URL in `<a target="_blank">` form. Don't revert this.

---

## 11. Forward-compatibility notes (for the future-you in 6 months)

1. **The DSA migration is complete** (22 topics, 226 problems). The walkthroughs are at `DSA/Topics/*/learn/*.md`. If you re-open this repo and aren't sure where to look — start with [`COVERAGE.md`](./COVERAGE.md) for the migration history, then [`DSA/TEMPLATE-v2.md`](./DSA/TEMPLATE-v2.md) for the writing rules.
2. **The JS migration is partial** (2/9 folders fully v2-migrated; rest are enhanced v1). [`COVERAGE.md`](./COVERAGE.md) tracks the status; the root [`TEMPLATE-v2.md`](./TEMPLATE-v2.md) is the playbook.
3. **The LeetLens DB** (separate repo at `/Users/prateek/Documents/build-using-claude-code/LeetLens/`) contains 905 LLM-extracted interview questions (DSA / LLD / HLD / System Design / Behavioral). It can be a source for extending this repo — connect via the Postgres container (`localhost:5433`, db `leetlens`, user `leetlens`).
4. **External link convention** — see §7. Bulk-conversion script lived at `/tmp/external_links_new_tab.py` during the 2026-05-25 sweep.
5. **If you onboard a new contributor / agent**, the order to read:
   - This file (`CONTRIBUTING-v2.md`)
   - [`COVERAGE.md`](./COVERAGE.md) (what's done, what's pending)
   - The relevant template ([DSA](./DSA/TEMPLATE-v2.md) or [JS](./TEMPLATE-v2.md))
   - One existing exemplar in the topic they're touching

---

## 12. Checklist for any new file

- [ ] Lives in the correct path (§4)
- [ ] Naming convention followed (§5)
- [ ] Follows the matching template (DSA or JS)
- [ ] External links use `<a target="_blank" rel="noopener noreferrer">` (§7)
- [ ] Mini-refreshers placed inline at first appearance of non-trivial concepts (§8)
- [ ] Closing "Shape" section with YES/NO transfer table (§8)
- [ ] Closing "Self-check" question (§8)
- [ ] `LEARNING.md` (DSA) or `INDEX.md` (JS) updated with the new entry + walkthrough link if applicable (§9)
- [ ] Cross-referenced from adjacent files in the same topic
- [ ] Length within target band (§8)
