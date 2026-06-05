# Command Pattern — Extracted Questions

> **3 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Command_Pattern` · Bucket study-order rank in vertical: **10**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 3
- **Difficulty mix:** Medium: 1 · Hard: 2
- **Top companies:** Google (1), Adobe (1), Amazon (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Adobe | Design an image processing pipeline supporting operations like resize, crop, rotate, flip, grayscale, blur, and watermark. Operations should be composable, lazily evaluated, and support both single images and batch processing. ✅ [walkthrough](./Image_Processing_Pipeline.md) | Object-Oriented Design, Pipeline Pattern, Lazy Evaluation, Command Pattern, +1 | `78c1aa5d` | `Object_Oriented_Design` |
| 2 | Hard | Amazon | Design a chess game with all standard rules including castling, en passant, pawn promotion, check, checkmate, and stalemate detection. Model the board, pieces, moves, and game state. | Object-Oriented Design, Inheritance, Polymorphism, Command Pattern | `b0345354` | `Object_Oriented_Design` |
| 3 | Hard | Google | Design a text editor supporting insert, delete, cursor movement, undo/redo operations, copy/paste, and find/replace. Use appropriate data structures for efficient text manipulation. | Object-Oriented Design, Command Pattern, Rope Data Structure, Memento Pattern | `459fb15d` | `Memento_Pattern` · `Object_Oriented_Design` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.