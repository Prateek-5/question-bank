# Categorization Method (Refined)

## Source

- Database: LeetLens Postgres at `localhost:5433`, db `leetlens`.
- Table: `processed.extracted_questions` — 905 rows on snapshot date **2026-05-31**.
- This folder covers the 785 DSA + LLD + HLD rows.
- Container: `leetlens-db`. Host has no `psql`; access via:
  ```bash
  docker exec leetlens-db psql -U leetlens -d leetlens
  ```

## Three-layer algorithm

Each question carries a `topics[]` array (LLM-extracted, ordered by importance, avg ~3 per question, max 7). The categorizer picks ONE primary bucket per question using THREE decision layers (first match wins):

### Layer 1 — Text-keyword override (highest priority)

Regex match against the lowercased question text. Used to catch questions where the LLM tagged a broad category but the text reveals a specific archetype. Example:

> `topics = ["System Design", "Hash Table", "Distributed Systems"]`
> Question: "Design a URL shortener like bit.ly..."

The topic walk would put this in `HLD_Algorithmic_Foundations` (hash table tag). But the text override catches `\burl shortener\b|tiny.{0,5}url|bit\.ly` and reroutes to `URL_Shortener`.

**Categories with text overrides:**

- **HLD** — 15 archetype patterns (URL shortener, rate limiter, load balancer, caching, messaging, search, geospatial, payments, A/B testing, media, data warehouse, distributed primitives)
- **LLD** — 22 pattern + machine names (Strategy, State, Observer, ..., plus "parking lot", "elevator", etc.)
- **DSA** — 2 JS-overflow rules (debounce/throttle/promise/etc.)

The regex list lives at the top of `/tmp/leetlens_refine.py`.

### Layer 2 — Topic-order walk (skipping catch-all terms)

Walk each row's `topics[]` IN ORDER. The first topic that maps to a bucket — AFTER skipping catch-all terms — wins.

**Catch-all terms skipped on this pass:**

| Category | Skip set |
|---|---|
| LLD | `object-oriented design`, `ood`, `design patterns`, `data structure` |
| HLD | `system design`, `distributed systems` |
| DSA | (none — DSA topics are usually specific) |

This prevents broad `topics[0]` tags from dominating. E.g. a question tagged `["Object-Oriented Design", "Strategy Pattern", "Stack"]` correctly lands in `Strategy_Pattern` (Strategy is the most specific intent).

### Layer 3 — Catch-all topic walk

If layers 1+2 didn't match, walk `topics[]` again including the skipped catch-all terms. This catches questions tagged ONLY with `["Object-Oriented Design"]` → `Object_Oriented_Design`, etc.

If still no match: `Uncategorized` (only 9 rows across 785 — under 1.2%).

## Secondary-bucket (overlap) detection

For each question, the categorizer ALSO computes the set of OTHER buckets it could fit:

- Run all text-override regexes (collect every match, not just first).
- Look up every topic in the topic→bucket map (collect every match).
- Subtract the primary bucket.

If the remaining set is non-empty, the question is marked as an "overlap." 476/785 (60.6%) qualify. These are listed in [`overlaps.md`](./overlaps.md) and annotated with `⚠️ also fits:` rows in the per-category files.

## Per-category buckets

- **DSA — 23 buckets.** 21 aligned to bosscode-question-bank's 22 DSA topics, plus two overflow: `JS_Coding_(out_of_DSA_scope)` (LeetLens's DSA category includes 56 JS/React/TS implementation questions) and `Distributed_Systems_(out_of_DSA_scope)` (24 Redis / consistent-hashing questions that belong in HLD).
- **LLD — 22 buckets.** GoF patterns first (Strategy, State, Observer, ...), then architectural patterns (Plugin, DI, Event Sourcing), then OOD catch-all, then `LLD_DataStructures` for data-structure-implementation questions ("implement LRU cache" etc.).
- **HLD — 17 buckets.** Specific archetypes (Rate_Limiting, URL_Shortener, Caching, ...), then `HLD_Algorithmic_Foundations` for graph/DP-heavy HLD, then `Distributed_Systems_General` for the catch-all tag.

## Refinement vs. the first-pass categorizer

The first-pass categorizer used only topic-tag matching. The refined categorizer adds text-keyword overrides, which significantly improves HLD (where the LLM tags broad category first):

| HLD bucket | First-pass | Refined | Delta |
|---|---:|---:|---:|
| Load_Balancing | 4 | 19 | +15 |
| Messaging_StreamProcessing | 19 | 34 | +15 |
| URL_Shortener | 17 | 24 | +7 |
| Rate_Limiting | 15 | 20 | +5 |
| Caching | 33 | 34 | +1 |
| HLD_Algorithmic_Foundations | 150 | 128 | −22 (good — was over-broad) |
| Distributed_Systems_General | 33 | 23 | −10 (good — specific archetypes pulled out) |

LLD also improved (text overrides on pattern names + concrete machines):

| LLD bucket | First-pass | Refined | Delta |
|---|---:|---:|---:|
| Object_Oriented_Design | 12 | 26 | +14 (text caught "Parking Lot", "Elevator", "ATM", etc.) |
| LLD_DataStructures | 67 | 60 | −7 |

DSA was already topic-tag-driven (specific tags) and didn't need much override.

## Known caveats

1. **One question, one primary bucket.** A question with three primary tags lands in one bucket; the others appear in [`overlaps.md`](./overlaps.md).
2. **Uncategorized is intentionally small.** Only 9 rows (5 DSA, 1 LLD, 3 HLD). They're niche cases (point geometry, Fibonacci generators, locking primitives) that don't fit any bucket cleanly. Inspect them individually.
3. **The 79 System-Design freeform + 38 Behavioral + 3 Other rows are NOT in this folder.** Different scheme would be needed for those.
4. **`HLD_Algorithmic_Foundations` (128 rows) is still a broad bucket.** It's HLD questions whose primary algorithmic foundation is graph/DP/heap. Further splitting would require LLM-grading per question — not done here.
5. **Difficulty is not assigned to any LLD/HLD Easy question** by the LLM. This is a data property — all open-ended design questions are Medium or Hard by nature.

## How to re-run

```bash
# 1. Dump fresh rows from the DB
docker exec leetlens-db psql -U leetlens -d leetlens -t -A -F$'\t' -c "
  SELECT id, category, difficulty, COALESCE(company,''),
         COALESCE(quality_score::text,''),
         array_to_string(topics, '|'),
         REPLACE(REPLACE(cleaned_question, E'\n', ' '), E'\t', ' ')
  FROM processed.extracted_questions
  WHERE category IN ('DSA','LLD','HLD')
  ORDER BY category, id;
" > /tmp/leetlens_dump.tsv

# 2. Re-run the refined categorizer
python3 /tmp/leetlens_refine.py
```

Output: `DSA-questions.md`, `LLD-questions.md`, `HLD-questions.md`, `overlaps.md`, plus a `/tmp/leetlens_categorized.json` data file for any downstream tools.

## Output files

| File | Rows | Approx size |
|---|---:|---:|
| `STUDY-GUIDE.md` | — | ~280 lines |
| `DSA-questions.md` | 302 | ~440 lines |
| `LLD-questions.md` | 146 | ~250 lines |
| `HLD-questions.md` | 337 | ~470 lines |
| `overlaps.md` | 476 | ~520 lines |
| `INDEX.md` | — | ~100 lines |
