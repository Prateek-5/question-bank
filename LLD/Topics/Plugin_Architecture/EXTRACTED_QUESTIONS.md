# Plugin Architecture — Extracted Questions

> **2 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Plugin_Architecture` · Bucket study-order rank in vertical: **19**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 2
- **Difficulty mix:** Hard: 2
- **Top companies:** Microsoft (1), Google (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Hard | Microsoft | Design a plugin architecture for an application where third-party developers can add features. Support plugin discovery, lifecycle management (load, enable, disable, unload), dependency resolution, and sandboxed execution. | Object-Oriented Design, Plugin Architecture, Dependency Injection, Service Locator, +1 | `14ec0d48` | `Dependency_Injection` · `Object_Oriented_Design` |
| 2 | Hard | Google | Design a test framework (like JUnit/Jest) supporting test discovery, setup/teardown hooks (before/after each/all), assertions, test suites, parameterized tests, mocking support, and test result reporting. | Object-Oriented Design, Framework Design, Template Method, Reflection, +1 | `f4357306` | `Object_Oriented_Design` · `Template_Method` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.