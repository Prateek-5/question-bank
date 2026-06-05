# HLD Authoring — Session Starter Prompt

> Paste everything below the line into a **fresh session** to begin the HLD phase.
> LLD is 100% complete (89/89 passed; see `LLD/AUTHORING_LEDGER.md`). HLD has not started.

---

Begin the HLD authoring phase, holding top quality (85 bar + polish). Mirror the exact
approach proven on LLD (89/89 passed, avg ~99.3).

**Repo:** `/Users/prateek/Documents/personal-repos/bosscode-dsa-notes/bosscode-question-bank`
**Run from:** `HLD/Topics` (engine paths are relative to repo root — use absolute paths when firing the workflow).

**Reference material (read these FIRST):**
- Template: `HLD/TEMPLATE-v2.md` — the section structure every file must follow. HLD's two
  non-negotiables vs LLD: **capacity numbers** and **architecture diagrams**.
- Canonical exemplar: `HLD/Topics/URL_Shortener/URL_Shortener_Design.md` — every authored
  file should feel like this one.
- Audience contract + mini-refresher list: top of `HLD/TEMPLATE-v2.md` (CAP, quorum math,
  sharding, replication, consensus, etc. — embed a refresher box at first use).
- Proven LLD engine to clone: `tools/lld-batch-workflow.js` (calibrated; treat as the
  reference implementation — do NOT modify the LLD engine).
- Completed LLD ledger (format to copy): `LLD/AUTHORING_LEDGER.md`.

## Phase 0 — Dedup pre-pass + build the ledger (do this once, before any authoring)

1. There are **16 topic buckets** under `HLD/Topics/*/EXTRACTED_QUESTIONS.md` plus
   `HLD/EXTRACTED_UNCATEGORIZED.md`, totalling **~361 raw rows** (LeetLens IDs are the
   8-hex codes). They are NOT deduplicated and are heavily skewed:
   `HLD_Algorithmic_Foundations` = 128 rows, `Distributed_Systems_General` = 47,
   `Caching` = 34, `Messaging_StreamProcessing` = 34, `Data_Storage_Retrieval` = 24,
   `URL_Shortener` = 24, `Rate_Limiting` = 20, `Load_Balancing` = 19, the rest single digits.
   Expect aggressive collapse (many are sync/lang/complexity-noise variants of one design,
   exactly like the LLD "Min Deque ×14" case).
2. Produce `HLD/AUTHORING_LEDGER.md` modeled **exactly** on `LLD/AUTHORING_LEDGER.md`:
   - Same header, dedup-decisions table (with transparency on every collapse),
     status-value legend, rubric table, per-bucket question tables
     (GID | Title | Diff | focus | File | Status | Score | Merged | LeetLens),
     a Progress summary with a **"Next pending row"** field, and a Batch log.
   - `URL_Shortener` already has an authored exemplar — mark its canonical row `done`
     (pointing at `Topics/URL_Shortener/URL_Shortener_Design.md`), like `Parking_Lot` in LLD.
   - Assign GIDs per bucket (e.g. `CACHE1…`, `DSG1…`, `ALGO1…`).
3. The ledger is the **single source of truth** thereafter. Always read it FIRST and never
   trust prose state over it.

## Phase 1 — Clone the engine

Clone `tools/lld-batch-workflow.js` → `tools/hld-batch-workflow.js`, swapping in:
- `HLD/TEMPLATE-v2.md` as the section spec,
- `HLD/Topics/URL_Shortener/URL_Shortener_Design.md` as the exemplar,
- the **HLD rubric**: §0 glossary/refreshers, **capacity math** (QPS, storage, bandwidth,
  back-of-envelope), and **progressive architecture** (§10.A naive → §10.B bottleneck →
  §10.C scaled, mirroring the exemplar's arc), plus the mermaid canonical-theme-block rule
  (verbatim, no `look: handDrawn`) carried over from LLD.

## Phase 2 — Loop until HLD pending = 0

1. Read `HLD/AUTHORING_LEDGER.md`. Take the next 3 `pending` rows from "Next pending row".
   For each build `{gid,bucket,title,difficulty,patternFocus,file,leetlens,raw}`; get the
   full `raw` text by grepping the LeetLens ID in that bucket's `EXTRACTED_QUESTIONS.md`.
2. Fire: `Workflow({scriptPath:"<repo>/tools/hld-batch-workflow.js", args:{batch:[...3 rows...]}})`.
3. On return, write each result's status+score back to its row, append a Batch-log line, and
   update the progress counts AND "Next pending row". **Write the full ledger update BEFORE
   firing the next batch** (resume-safety guarantee).
4. Only ever pick `pending` rows; never re-author a `passed`/`done` row.

**Failure handling (same as LLD):** a batch returning 0 results / "completed without calling
StructuredOutput" with ~0 tokens is a **transient infra failure** (e.g. a model outage) — rows
stay `pending`, no files written; just re-fire the identical batch. If the model is mid-outage,
pause a few minutes (ScheduleWakeup ~270s) before re-firing rather than hammering it.

**Pacing:** at a clean cut point (right after a batch's ledger writes complete, before firing
the next), flag if context is getting heavy and a fresh session would be wise. The ledger is the
durable handoff point — a restart loses nothing.

## Carry-over notes from LLD (non-blocking)

- LLD open polish: `Strategy_Pattern/Calendar_Application.md` §12.3 abbreviated mermaid theme
  block (passed at 97); `Command_Pattern/Image_Processing_Pipeline.md` row hand-adjusted to 95.
  These do not affect HLD; listed only for continuity.
