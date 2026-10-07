# CV Coach Plan

**Decision:** [D-036](decisions.md) · **Status:** v1 BUILT (deterministic, no model call; 6 Oct 2026, EXP-20261006-CP3); CP3 refinements PLANNED (D-093 B) · **Proposed by:** Dion, 30 September 2026

**CP2 mentor feedback (D-093, 4 Oct 2026):** the mentor asked for CV improvement suggestions for the target vacancy once the core features work. This plan covers that request, so there is no separate feature. Suggestions come from the user's real CV evidence, the JD requirements and the gaps found, and they do not promise a better real fit.

## Why

Matching tells the user which requirements have no clear evidence in the CV. The CV coach helps the user fix that honestly: it asks about real work the user has done and turns the answers into stronger CV bullet points. It never invents experience.

## Flow

```text
1. Matching result:   "Computer vision: no evidence in the CV yet"
                            ↓
2. Question:          "Have you worked on a computer vision project?"
                            ↓
3a. "Yes"                               3b. "No"
    → 3 to 4 short questions                → no CV bullet is written
                            ↓                  → learning or project ideas instead
4. Draft of 1 to 2 CV bullets, each part linked to the answer it came from
                            ↓
5. User: accept / edit / reject / copy
                            ↓
6. User updates the CV and uploads it again → the score is computed from the new CV
```

## Fixed questions (v1)

| Question | Purpose |
| --- | --- |
| What was the project or job, and when? | Context and dates |
| Which part did you do yourself? | Own role versus team work |
| Which tools or methods did you use? | Evidence for the requirement |
| What was the result? Is there a number? | A concrete, strong bullet |

Example bullet, built only from the user's answers:
> Built an image classifier for product defects using PyTorch and ResNet-18 on 3,000 labeled photos, reaching 92% accuracy (personal project, Jul 2026).

## Rules

1. Only facts from the user's answers. Numbers only if the user gave them. Target: unsupported claims = 0.
2. "Not done" means no bullet. The user gets learning or project ideas instead.
3. Answers never change the score. Only an updated CV does.
4. Answers are user statements, kept only for the session, and pass the same privacy rules as the CV.
5. The user decides on every suggestion (accept, edit, reject).

## Versions

| | v1 (minimal) | Later upgrade |
| --- | --- | --- |
| Scope | One job, at most 3 most important gaps | All gaps, many jobs |
| Questions | 3 to 4 fixed questions per gap | Free multi-turn coaching |
| Output | 1 to 2 bullets per gap with accept / edit / reject / copy | Rewrite whole CV sections, export to .docx |
| When | CP3.1 (`/tailor`), only if matching is done | After v1, when time allows |
| Evaluation | About 10 scenarios: unsupported claims = 0, every bullet cites an answer, "not done" gives no bullet | Tests with real users |

## Status (7 Oct 2026)

### Built now (v1, local)

- `src/jobfit/support/cv_coach.py`: deterministic, with no model call. Up to 3 required gaps per job (NO_MATCH or PARTIAL units). Fixed questions. Bullets are built only from the user's answers (answers are capped at 300 characters). "Not done" gives learning or project ideas and no bullet.
- API endpoints `/tailor` and `/tailor/answer`, and the UI coach expander.
- Tests: `tests/test_cv_coach.py`, plus the coach check in `scripts/e2e_check.py`.
- Validated locally only (local end-to-end 27/27). Not checked on a deployed app yet.

### CP3 refinements (PLANNED, D-093 B; CP3.3 and CP3.4)

- Each suggestion shows its source: the JD requirement text and the current CV evidence status (missing, or partial with the quoted CV line).
- Explicit wording: the coach never invents skills or experience, a CV edit only helps when it adds true evidence, and a better real-world fit is not guaranteed.
- Validation: unsupported words = 0; "not done" gives no bullet; 2-3 screenshots from the deployed app.
- No LLM-based coach in CP3. It would add cost, latency and hallucination risk before the feature freeze.

### Optional future work (not CP3)

- Coaching across all gaps and many jobs, free multi-turn coaching, rewriting whole CV sections, `.docx` export.
- An LLM-written suggestion, only with the same evidence-grounding rules and its own evaluation.
- Tests with real users.

## Priority

Matching, evaluation, testing, privacy, and deployment come first. In the cut order of System Design v1.3 section 18, the CV suggestions feature is the first to be cut when time is short.
