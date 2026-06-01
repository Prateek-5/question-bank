export const meta = {
  name: 'lld-batch-authoring',
  description: 'Author + judge + rectify a batch of LLD v2 walkthroughs against the rubric',
  phases: [
    { title: 'Author', detail: 'one agent writes each walkthrough against LLD/TEMPLATE-v2.md' },
    { title: 'Judge+Rectify', detail: 'score each file 0-100, fix gaps, re-judge (max 2 rounds)' },
  ],
}

// ---------------------------------------------------------------------------
// args: array of canonical question objects from LLD/AUTHORING_LEDGER.md, e.g.
//   [{ gid, bucket, title, difficulty, patternFocus, file, leetlens, raw }]
//   - file is RELATIVE to <repo>/LLD/Topics/
// Returns: array of per-question results the main loop writes back to the ledger.
// ---------------------------------------------------------------------------

const REPO = '/Users/prateek/Documents/personal-repos/bosscode-dsa-notes/bosscode-question-bank'
const TOPICS = REPO + '/LLD/Topics'
const TEMPLATE = REPO + '/LLD/TEMPLATE-v2.md'
const EXEMPLAR = REPO + '/LLD/Topics/Object_Oriented_Design/Parking_Lot.md'
const THEME_SRC = REPO + '/CONTINUATION.md' // §3 canonical mermaid block

const PASS = 85

let batch = args
if (typeof batch === 'string') {
  try { batch = JSON.parse(batch) } catch (e) { batch = [] }
}
if (batch && !Array.isArray(batch) && Array.isArray(batch.batch)) batch = batch.batch
if (!Array.isArray(batch)) batch = []
if (!batch.length) {
  log(`No questions passed in args (typeof args = ${typeof args}) — nothing to author.`)
  return { error: 'empty batch', argsType: typeof args, results: [] }
}

const JUDGE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['scoreTotal', 'dimensions', 'criticalMissing', 'gaps', 'verdict'],
  properties: {
    scoreTotal: { type: 'integer', minimum: 0, maximum: 100 },
    dimensions: {
      type: 'object',
      additionalProperties: false,
      required: ['sections', 'derivation', 'refreshers', 'mermaid', 'skeleton', 'selfcheck', 'length'],
      properties: {
        sections: { type: 'integer', minimum: 0, maximum: 25, description: 'all 15 template sections present' },
        derivation: { type: 'integer', minimum: 0, maximum: 20, description: 'naive->pain->pivots arc genuine, not asserted' },
        refreshers: { type: 'integer', minimum: 0, maximum: 15, description: 'mini-refresher boxes + pattern-discrimination cheatsheets' },
        mermaid: { type: 'integer', minimum: 0, maximum: 15, description: 'canonical theme block verbatim, no look:handDrawn, correct diagram types' },
        skeleton: { type: 'integer', minimum: 0, maximum: 10, description: 'C++17 shows shapes not full impls' },
        selfcheck: { type: 'integer', minimum: 0, maximum: 10, description: 'self-check + >=4 clarifying Qs + cross-references' },
        length: { type: 'integer', minimum: 0, maximum: 5, description: 'within difficulty band' },
      },
    },
    criticalMissing: { type: 'array', items: { type: 'string' }, description: 'critical failures e.g. missing §8, uses look:handDrawn' },
    gaps: { type: 'array', items: { type: 'string' }, description: 'specific, actionable fixes the rectify agent should apply' },
    verdict: { enum: ['pass', 'fail'] },
  },
}

function authorPrompt(q) {
  const abs = TOPICS + '/' + q.file
  return [
    `You are authoring a v2 Low-Level Design teaching walkthrough for the bosscode question bank.`,
    ``,
    `QUESTION (GID ${q.gid}, bucket ${q.bucket}, ${q.difficulty}):`,
    `"${q.raw || q.title}"`,
    `Pattern focus the interviewer is probing: ${q.patternFocus}.`,
    ``,
    `BEFORE WRITING, read these three files in full — they are the contract:`,
    `1. ${TEMPLATE}  (the LLD v2 template — all 15 required sections, style rules 1-8, the checklist, length targets)`,
    `2. ${EXEMPLAR}  (the canonical gold-standard exemplar — match its depth, voice, and diagram quality)`,
    `3. ${THEME_SRC}  §3 only (the canonical mermaid theme block you must copy VERBATIM into every diagram)`,
    ``,
    `Then WRITE the complete walkthrough to this absolute path (create parent dirs if needed):`,
    `   ${abs}`,
    ``,
    `IDEMPOTENCY GUARD — read this path FIRST. If a file already exists there AND it is a`,
    `complete walkthrough (has a "## 15." or "Self-check" section and >400 lines), DO NOT`,
    `overwrite or modify it. Stop immediately and return exactly:  path=${abs} | status=already-exists`,
    `Only author when the file is absent or an obvious stub. This prevents reworking finished walkthroughs.`,
    ``,
    `NON-NEGOTIABLE requirements (a judge will score against these):`,
    `- All 15 body sections in order (§1 clarifying Qs ... §15 self-check). §1 must have >=4 clarifying questions.`,
    `- DERIVATION over ASSERTION: §7 naive design first (with inline mermaid classDiagram + ~30-50 lines C++17), §8 makes the pain concrete (>=3 future requirements, name the files/lines that hurt, end with a pivot question), then §9/§10/§11 introduce ONE pattern per painful axis with a mini-refresher and a pattern-discrimination cheatsheet.`,
    `- Every design pattern and SOLID principle gets an inline mini-refresher box at first use. Sprinkle 1-2 pattern-discrimination cheatsheets (e.g. Strategy vs State).`,
    `- Every mermaid diagram uses the canonical theme block VERBATIM. ABSOLUTELY NO 'look: handDrawn'. Use classDiagram for §7/§9-12, sequenceDiagram for §14. Add an HTML anchor (id="fig-...") on diagram-bearing headings.`,
    `- C++17 skeletons show SHAPES: abstract base + 1-2 concrete classes per pattern, '// elided' for the rest. unique_ptr ownership, enum class, const-correct.`,
    `- §15 ends with a "Self-check — the question to ask next time" block.`,
    `- Cross-references block at the bottom (parent manifest, vertical overview, template, related walkthroughs).`,
    `- External links use <a href="..." target="_blank" rel="noopener noreferrer">.`,
    `- Length: ${/hard/i.test(q.difficulty) ? '700-1000 lines (Hard)' : '500-700 lines (Medium)'}.`,
    `- Mentor voice, no LaTeX (plain ASCII math), no corporate tone.`,
    ``,
    `Your final text is a return value, not a message to a human. Return ONLY a compact JSON-ish line:`,
    `   path=<abs path written> | sections=<count of body sections you wrote> | diagrams=<mermaid block count> | lines=<approx line count>`,
  ].join('\n')
}

function judgePrompt(q, round) {
  const abs = TOPICS + '/' + q.file
  return [
    `You are an exacting reviewer of a v2 LLD walkthrough. Be skeptical — default to deducting points when a requirement is only partially met.`,
    round > 0 ? `This is a RE-JUDGE after a rectify pass. Score the CURRENT file state.` : ``,
    ``,
    `Read the file under review:  ${abs}`,
    `Read the contract it must satisfy:  ${TEMPLATE}  (sections + style rules + checklist + length targets)`,
    `Reference the canonical mermaid theme block in:  ${THEME_SRC} §3 (to verify diagrams copy it verbatim and do NOT use look:handDrawn)`,
    ``,
    `Score each rubric dimension (max points in parens). Be strict:`,
    `- sections (25): all 15 body sections present and non-stub. If ANY of §7 naive / §8 pain / §9-11 pivots / §12 final diagram / §14 sequence / §15 self-check is missing or a stub, this dimension caps at 12 and you MUST add an entry to criticalMissing.`,
    `- derivation (20): is the design DERIVED (naive -> concrete file-level pain -> pattern-with-justification) or merely ASSERTED? Assertion-style answers score <=8 and add a criticalMissing entry.`,
    `- refreshers (15): mini-refresher box at first use of every pattern/SOLID principle + at least one pattern-discrimination cheatsheet.`,
    `- mermaid (15): every diagram uses the canonical theme block verbatim; correct diagram types; anchors present. ANY 'look: handDrawn' caps this dimension at 4 and is a criticalMissing entry.`,
    `- skeleton (10): C++17 shapes not full implementations; idiomatic (unique_ptr, enum class, // elided).`,
    `- selfcheck (10): self-check block present + >=4 clarifying questions in §1 + cross-references block.`,
    `- length (5): reward DEPTH that matches the canonical exemplar Parking_Lot.md (~1650 lines). Full marks for 700-1650 lines. The repo's REAL failure mode is being too THIN (skimpy §7 naive / §8 pain / §9-11 pivots), not too long. Deduct heavily ONLY if <600 lines, or if length comes from obviously redundant padding (e.g. the exact same class diagram repeated verbatim in two different sections). Do NOT penalize a thorough 1000-1450 line walkthrough — that is on target.`,
    ``,
    `scoreTotal = sum of the seven dimension scores.`,
    `verdict = "pass" ONLY IF scoreTotal >= ${PASS} AND criticalMissing is empty. Otherwise "fail".`,
    `gaps = specific, actionable instructions a rewriter can follow (cite the section). Empty if pass.`,
  ].filter(Boolean).join('\n')
}

function rectifyPrompt(q, verdict) {
  const abs = TOPICS + '/' + q.file
  return [
    `You are fixing a v2 LLD walkthrough that FAILED review. Edit the file IN PLACE to address every gap. Do not rewrite passing sections wholesale — surgically fix what's flagged.`,
    ``,
    `File to fix:  ${abs}`,
    `Contract:    ${TEMPLATE}`,
    `Mermaid block source (verbatim):  ${THEME_SRC} §3`,
    ``,
    `Critical failures (MUST all be resolved):`,
    ...(verdict.criticalMissing.length ? verdict.criticalMissing.map(c => `  - ${c}`) : ['  (none)']),
    ``,
    `Gaps to fix:`,
    ...verdict.gaps.map(g => `  - ${g}`),
    ``,
    `Apply the fixes with Edit/Write. Return one line: fixed=<count of gaps addressed> | path=${abs}`,
  ].join('\n')
}

// --- run -------------------------------------------------------------------
log(`LLD batch: ${batch.length} question(s) — ${batch.map(q => q.gid).join(', ')}`)

const results = await pipeline(
  batch,
  // Stage 1: author
  async (q) => {
    const out = await agent(authorPrompt(q), { label: `author:${q.gid}`, phase: 'Author' })
    return { q, authorNote: out }
  },
  // Stage 2: judge, then rectify+rejudge up to 2 rounds
  async (prev, q) => {
    let round = 0
    let verdict = await agent(judgePrompt(q, round), { label: `judge:${q.gid}`, phase: 'Judge+Rectify', schema: JUDGE_SCHEMA })
    while (verdict.verdict === 'fail' && round < 2) {
      round++
      await agent(rectifyPrompt(q, verdict), { label: `rectify:${q.gid}#${round}`, phase: 'Judge+Rectify' })
      verdict = await agent(judgePrompt(q, round), { label: `rejudge:${q.gid}#${round}`, phase: 'Judge+Rectify', schema: JUDGE_SCHEMA })
    }
    // Polish pass: a file can pass (>= PASS) yet still carry real gaps (e.g. a
    // skeleton bug, an un-split §12). "Rectify if required" means fix those too.
    let polished = false
    if (verdict.verdict === 'pass' && (verdict.gaps?.length || 0) > 0) {
      await agent(rectifyPrompt(q, verdict), { label: `polish:${q.gid}`, phase: 'Judge+Rectify' })
      verdict = await agent(judgePrompt(q, round + 1), { label: `polish-judge:${q.gid}`, phase: 'Judge+Rectify', schema: JUDGE_SCHEMA })
      polished = true
    }
    return {
      gid: q.gid,
      bucket: q.bucket,
      file: q.file,
      title: q.title,
      score: verdict.scoreTotal,
      status: verdict.verdict === 'pass' ? 'passed' : 'needs-fix',
      rectifyRounds: round,
      polished,
      criticalMissing: verdict.criticalMissing,
      gaps: verdict.gaps,
      dimensions: verdict.dimensions,
    }
  }
)

const clean = results.filter(Boolean)
const passed = clean.filter(r => r.status === 'passed').length
log(`Batch complete: ${passed}/${clean.length} passed (>= ${PASS}).`)
return { results: clean, passed, total: clean.length }
