# CP3 evidence-matching LLM comparison: cost, quality and latency

**STATUS: COMPLETED / EXECUTED** (owner Local Mac, 9 Oct 2026; total paid cost about US$0.182). The paid run and the offline evaluation were done by the owner, who also made the model decision below. No production or runtime configuration change is authorized. The frozen D-087 pipeline and the held-out test are unchanged.

## Results

The figures below are from the owner's local run and its offline evaluation. All 73 units are in every denominator.

| Model | Valid pairs | Macro-F1 | Overclaims | Quote validity | Cost (US$) | p50 (s) | p95 (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-6 Sol (baseline) | 4/4 | 0.877 | 2 | 1.000 | 0.1513 | 20.6 | 21.2 |
| GPT-6 Luna | 4/4 | 0.751 | 3 | 1.000 | 0.0079 | 25.7 | 27.6 |
| Claude Haiku 5.5 | 3/4 | 0.694 | 1 | 1.000 | 0.0224 | 24.7 | 26.4 |

**Versus Sol:**

| Challenger | ΔMacro-F1 | Cost ratio vs Sol | Historical reference (≥ Sol − 0.03) |
| --- | ---: | ---: | --- |
| GPT-6 Luna | −0.126 | 0.052 | not met |
| Claude Haiku 5.5 | −0.182 | 0.198 | not met |

**Total paid cost:** 0.1513 + 0.0079 + 0.0224 ≈ **US$0.182**.

**What the run shows:**
- **Quotes:** every output that was assessed had 100% exact-quote validity.
- **Haiku 5.5's failed pair:** the CV1/F00332 pair failed at pair level with `invalid_structured_output_or_source`. Its 16 units count as false negatives, so Haiku 5.5 had 3/4 valid pairs.
- **Luna:** about 19× cheaper than Sol, but 0.126 lower in Macro-F1 and slower at p50 and p95.
- **Haiku 5.5:** the fewest overclaims, but the lowest Macro-F1 and one failed pair.
- **Run-to-run variation:** Sol scored 0.877 here against 0.846 in D-079 on the same benchmark (+0.031). One run per model cannot separate small differences.

**Conclusion (owner decision):**
- Keep GPT-6 Sol as the primary evidence matcher.
- Keep GPT-6 Luna as the existing fallback.
- Do not promote Claude Haiku 5.5.
- No production or runtime configuration change is authorized.
- D-087 remains unchanged.
- Conditional cheap-model routing may be considered later as a separate optimization experiment.

## Question and hypothesis

**Question:** on the canonical development evidence benchmark, how much evidence-matching quality do the cheaper models give up against GPT-6 Sol, and what does each cost and how long does it take?

**Hypothesis (descriptive, not a gate):** one of the cheap challengers keeps Macro-F1 within the historical reference (Sol − 0.03). It does so with 4/4 valid pairs, 100% quote validity and no more unsupported positives than Sol, at a materially lower cost.

The earlier D-079 sweep found:
- **Sol:** 0.846;
- **Luna:** 0.736;
- **Haiku 4.5:** 2/4 valid pairs.

Claude Haiku 5.5 is new.

**Outcome:** the hypothesis was not supported. Neither challenger stayed within Sol − 0.03, and Haiku 5.5 did not reach 4/4 valid pairs.

## Candidates

The same request settings apply to every model. No model-specific reasoning or effort setting is configured; reasoning tokens are recorded when the provider reports them.

| Key | OpenRouter id | Price ceiling (US$ per 1M in/out) | Role |
| --- | --- | --- | --- |
| `gpt-6-sol` | `openai/gpt-6-sol` | 2.00 / 10.00 | baseline (D-083 matcher) |
| `gpt-6-luna` | `openai/gpt-6-luna` | 0.10 / 0.50 | cheap OpenAI challenger (D-083 fallback) |
| `claude-haiku-5.5` | `anthropic/claude-haiku-5.5` | 0.10 / 0.50 | cheap Anthropic challenger |

The ceilings are sent to OpenRouter as `max_price` and also drive the cost bound.

**Required before `--execute`:** the runtime network preflight on the owner's machine must find every id with a structured-output endpoint priced at or below its ceiling. If any check fails, the run stops and names the model. No other model is substituted. The preparation container could not reach openrouter.ai. `--execute` refuses to start without a passing network preflight, so the ids and prices were checked on the owner's machine at run time.

## Benchmark (development only, fixed inputs)

The benchmark is the D-062/D-063 canonical development evidence benchmark: the four fixed CV1/CV2 pairs of D-079, with 73 reviewed requirement units.

| Pair | Units |
| --- | ---: |
| CV1 × F00332 | 16 |
| CV1 × F00036 | 17 (duration input 0.75 y) |
| CV2 × F00815 | 16 |
| CV2 × F00018 | 24 |

- **Classes:** the r3 gold has 35 MATCH, 22 PARTIAL and 16 NO_MATCH. The evaluation uses the D-067 reference, where `CV2/F00815/P52-U10` is MATCH, giving 36 / 21 / 16.
- **Requirements:** they come from the reviewed gold through `fixed_reviewed_requirements`, not from a model extraction. DeepSeek Flash stays the JD extractor and is not exercised.
- **Method:** the D-079 method, the same for every model:
  - prompt v1.1;
  - quote validator v1.1;
  - dynamic output policy;
  - 240 s timeout;
  - at most one validation repair and one length continuation;
  - one worker, no cache.
- **Guardrails:** G1/G2 (with the SQL example adapter) and the D-067 reference are applied in the offline evaluation, as in D-079.
- **Same inputs:** every model receives the same input objects and the same system prompt. Both are hashed per request and per pair.

**Leakage protection is identity-based.** The run is refused unless:
- only CV1/CV2 are used;
- the pairs are exactly the four approved ones;
- every job is in `dev_job_ids` and not in `test_job_ids`;
- every fixed input matches its hash.

A check on the locked CP2.4 test paths is kept as a second line of defence. CV3–CV5, the 214 held-out test jobs, the CP2.4 test labels and the held-out report are never read.

## Protected hashes (sha256)

The first six equal the D-063 approval receipt.

| File | sha256 |
| --- | --- |
| `evals/gold/development_v13_reviewed_20261003_stage1_r3/evidence_gold.jsonl` | `510bbe15bd02ed370b2a94982582169c6c9d38f62b5e6e27311bb55a0f3ef49e` |
| `evals/gold/development_v13_reviewed_20261003_stage1_r3/extraction_gold.jsonl` | `f69fe7de750358d285b120e7c00c0f5941bef054912abda5e04020d156491a84` |
| `evals/results/cp23_stage2_fixed_matching_20261003_v1_plan.json` | `360e16a8ed41a3c357b15c8b019f262adfcb6b2942344f677c92b8d8f9d4ccdd` |
| `src/jobfit/eval/fixed_requirements.py` | `c947d63fac6418dd3eb1a03c9838dfbabc97d601e5e90dfc87190a92136ec955` |
| `prompts/evidence_matching_v1_1.md` | `19576d1940ad74015954f7014ba816f428ac835e726d89b3bfd107eb93e81d1f` |
| `evals/annotation_guideline_v1_3.md` | `3d964a28fd105e16b24ad51b8b0a22b34bb9255e438b51e4e6e0eda551c57645` |
| `data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md` | `6ab96764175536fea1f8d6bb56b0671ad947eebda01dd98a697cc821ee0d396a` |
| `data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md` | `63dd7aabb355d46a55ddf5cf3874a86b0a263e74fe84192e1a23ac96d9d36469` |
| `evals/results/cp22_extraction_repair_v13_20261003_02.json` (CV1 parse) | `644ae3e531f37512b61f5f6f703d5fd34d2c6599a5e77306ffc2bf92d3f1702e` |
| `evals/splits/dev_job_ids.txt` | `3e1a6bb9ac784381bbe94a659248a2c5f4642cb5374337e344dbdb3ddb0955e6` |
| `evals/splits/test_job_ids.txt` | `b4fe01b3cf9f8f265e976eef9d1bb1549d3e25b1bb7c0a9433b5ca4058ea3435` |

**System prompt sent to every model** (prompt v1.1 + guideline v1.3): `342866df713e3834041a7e5d2fb774dca2f544d87e95b4f6755dd6d81634ced2`.

## Metrics

All 73 units are always in the denominator. A failed, unrun or unassessed unit counts as a false negative.

- **Process:**
  - valid pairs out of 4;
  - assessed units out of 73;
  - structured-output failures (schema or JSON);
  - validation failures (output returned but rejected by the validator);
  - repair attempts and length continuations;
  - truncations;
  - failed requests;
  - model fallbacks (always 0: this experiment has no fallback route);
  - providers that served each model.
- **Evidence quality:**
  - confusion matrix (with `not_assessed`);
  - Macro-F1: G1/G2 headline, with the unguarded result as a diagnostic;
  - per-class precision, recall and F1 for MATCH, PARTIAL and NO_MATCH;
  - overclaims and underclaims (labels stronger or weaker than gold);
  - quote validity (every MATCH/PARTIAL quote found word for word in the CV) and invalid quotes;
  - unsupported positives (positive on a gold NO_MATCH, plus invalid-quote items);
  - unassessed units.
- **Actual cost:** what the provider reported, from the project ledger, reconciled with the per-request usage in `requests.jsonl`.
  - input, output, reasoning and total tokens;
  - cost per request, per model, per valid pair, per reference unit and per assessed unit.

  Ledger rows without a reported cost (uncertain upper bounds, estimates) are summed separately. Preflight estimates are never mixed with actual cost.
- **Latency:**
  - per-attempt provider latency, p50 and p95 (nearest rank);
  - per-pair wall time;
  - per-model and total wall time.

  These are sequential, single-worker numbers on one machine: **not a load or concurrency benchmark.**
- **Versus Sol:**
  - ΔMacro-F1, with paired unit and pair bootstrap intervals (seed 20261004);
  - cost ratio per valid pair;
  - latency ratio (p50, p95);
  - Δoverclaims;
  - the historical reference `challenger_macro_f1 >= sol_macro_f1 - 0.03` (D-029 rule 3 / D-066), printed only.
  - **Separate flags:** all pairs valid; 100% quote validity; unsupported positives not increased; cost materially lower (≤ 0.5 × Sol per valid pair).

**Output table:** Model | Valid pairs | Macro-F1 | Overclaims | Quote validity | Cost | p50 | p95.

## Cost guard

**Conservative maximum (the run cap): US$6.5691.**

| Model | Conservative maximum (US$) |
| --- | ---: |
| Sol | 5.9719 |
| Luna | 0.2986 |
| Haiku 5.5 | 0.2986 |

How the cap is built:
- Each pair is costed as a main attempt + one length continuation + one validation repair. Each attempt uses its largest output allowance; the continuation and repair are at 2× the output. Input is counted in UTF-8 bytes (≥ tokens), and every attempt is priced at the ceiling.
- The request shapes come from the exact requests the matcher would send, captured offline with no provider call.
- The cap is enforced in the run: `CappedClient` reserves each attempt's upper bound before dispatch.
- The project hard stop must also have headroom: ledger + cap ≤ `API_HARD_STOP_USD`.

**Requests:** 12 main requests (3 models × 4 pairs), and at most 36.

**Estimate (informational, not the cap): about US$0.20.**

| Model | Estimate (US$) |
| --- | ---: |
| Sol | 0.165 |
| Luna | 0.011 |
| Haiku 5.5 | 0.025 |

The estimate uses the D-079 method: 4 pairs × 1.5 × the median reported cost per call in the development ledger. Haiku 5.5 has no history, so it uses 11k input and 6k output tokens at the ceiling.

**Actual (provider-reported): about US$0.182.**

| Model | Actual (US$) |
| --- | ---: |
| Sol | 0.1513 |
| Luna | 0.0079 |
| Haiku 5.5 | 0.0224 |

The actual cost stayed close to the estimate and far below the cap.

## Execution (run on the owner's machine)

The commands below are kept as the record of how the run was made.

1. **Preflight, no paid call.** This includes the network metadata check: ids, structured endpoints and prices.
   ```sh
   python scripts/run_cp3_llm_cost_quality_comparison.py
   ```
   It must print `"execute_ready": true` and `"problems": []`. If `API_HARD_STOP_USD` lacks headroom for the cap, the owner decides whether to change it; nothing raises it automatically.
2. **The paid run.**
   ```sh
   python scripts/run_cp3_llm_cost_quality_comparison.py --execute
   ```
   `--execute` is refused in these cases:
   - with `--skip-network-check`;
   - with any preflight problem;
   - with a non-inference key;
   - when `evals/results/cp3_llm_cost_quality_comparison/cp3_llm_cost_quality_comparison_v1/` already exists.

   A route error stops only that model; its remaining pairs are written as `not_run`. A budget or key error stops the run.
3. **Offline evaluation, no call.**
   ```sh
   python scripts/evaluate_cp3_llm_cost_quality_comparison.py --write
   ```

## Outputs

The executed run artifacts are committed under `evals/results/cp3_llm_cost_quality_comparison/cp3_llm_cost_quality_comparison_v1/` for reproducibility.
- `plan.json`: the preflight receipt;
- `pairs/<model>__<cv>_<job>.json`: 12 files, one per model and pair, including failures;
- `requests.jsonl`: one metadata row per provider attempt, with no CV text, prompt or output;
- `summary.json`;
- after evaluation, `comparison.json` and `comparison.md`.

## Interpretation rules

- **No automatic promotion.** Model selection is the owner's.
- The 0.03 rule is a historical reference, reported next to the four separate flags.
- A challenger with fewer than 4 valid pairs keeps every failed unit as a false negative. Its answered-only quality is not the headline.
- A difference inside the bootstrap interval is not a quality difference.
- Cost uses the provider's reported charge only.

## Limitations

- **Small sample:** only 4 development pairs (2 synthetic CVs) and 73 units. A few points of Macro-F1 are noise.
- **Single run:** one run per model, and model outputs vary between runs. Sol moved by +0.031 against D-079 on the same benchmark.
- **Latency:** sequential single-worker latency on one machine. It is not a load or concurrency benchmark.
- **Moving targets:** prices, routes and serving providers change over time.
- **Earlier failures do not carry over:** Haiku 4.5's D-079 failures did not predict Haiku 5.5.
- **Matching only:** extraction is fixed to the reviewed requirements, so end-to-end quality with DeepSeek extraction is not measured here.
- **Source of the figures:** the results come from the owner's local run, and its artifacts are not in the repository.

## Files

- **Config:** `config/cp3/llm_cost_quality_comparison_v1.yaml`.
- **Runner:** `scripts/run_cp3_llm_cost_quality_comparison.py`. It reuses the D-079 sweep (`stages`, `fetch_metadata`, `SweepAdapter`/`SweepClient`), `CappedClient`, the fixed `inputs()` and the CP2.3 leakage helpers. `RecordingAdapter` overrides `with_options`, so the adapter OpenRouterClient uses stays recording into the same sink. Main, repair and continuation attempts are all recorded.
- **Evaluator:** `scripts/evaluate_cp3_llm_cost_quality_comparison.py`. It reuses the D-079 `predictions`, `reference_rows`, `evidence_metrics`, `error_profile`, `paired_bootstrap` and `quote_validity`. On the saved D-079 Sol outputs it reproduces the historical Sol Macro-F1 of 0.846.
- **Tests:** `tests/test_cp3_llm_cost_quality_comparison.py`, offline with a fake SDK replaying the saved D-079 outputs.
