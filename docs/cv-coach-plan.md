# CV Coach Plan

**Decision:** [D-036](decisions.md) · **Status:** planned, built only after the matching feature is complete · **Proposed by:** Dion, 30 September 2026

**CP2 mentor feedback (D-093, 4 Oct 2026):** the mentor asked for vacancy-specific CV improvement guidance once the core features work. That request is carried by this plan; no separate feature is created. Guidance stays grounded in the user's real CV evidence, the JD requirements and the identified gaps, and does not promise a higher true suitability.

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

## Priority

Matching, evaluation, testing, privacy, and deployment come first. In the cut order of System Design v1.3 section 18, the CV suggestions feature is the first to be cut when time is short.
