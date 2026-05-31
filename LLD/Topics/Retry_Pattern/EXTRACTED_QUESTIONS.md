# Retry / Circuit Breaker — Extracted Questions

> **3 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Retry_Pattern` · Bucket study-order rank in vertical: **23**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 3
- **Difficulty mix:** Medium: 3
- **Top companies:** Netflix (3)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Netflix | Design a retry framework with support for fixed delay, exponential backoff with jitter, linear backoff, and custom retry policies. Include retry budget (max retries per time window), retryable exception classification, and circuit breaker integration. | Object-Oriented Design, Retry Pattern, Strategy Pattern, Circuit Breaker, +1 | `490ea197` | `Object_Oriented_Design` · `Strategy_Pattern` |
| 2 | Medium | Netflix | Design a circuit breaker pattern implementation supporting closed, open, and half-open states, configurable failure thresholds, timeout duration, and health check probing. Integrate with a retry mechanism. | Object-Oriented Design, Circuit Breaker, State Pattern, Resilience Pattern | `4a825994` | `Object_Oriented_Design` · `State_Pattern` |
| 3 | Medium | Netflix | Design an HTTP client library with request/response interceptors, automatic retry with backoff, timeout handling, connection pooling, request cancellation, and response caching. Make it composable via middleware. | Object-Oriented Design, Interceptor Pattern, Builder Pattern, Retry Pattern, +1 | `ce2f1995` | `Builder_Pattern` · `Interceptor_Pattern` · `Object_Oriented_Design` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.