# CP3 LLM cost/quality comparison: cp3_llm_cost_quality_comparison_v1

Development data only. Owner decision; no automatic promotion.

| Model | Valid pairs | Macro-F1 | Overclaims | Quote validity | Cost (US$) | p50 (s) | p95 (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-6-sol | 4/4 | 0.877 | 2 | 1.000 | 0.1513 | 20.6 | 21.2 |
| gpt-6-luna | 4/4 | 0.751 | 3 | 1.000 | 0.0079 | 25.7 | 27.6 |
| claude-haiku-5.5 | 3/4 | 0.694 | 1 | 1.000 | 0.0224 | 24.7 | 26.4 |

Versus gpt-6-sol:

| Challenger | ΔMacro-F1 | Cost ratio | Latency ratio (p50) | ΔOverclaims | ≥ Sol − 0.03 (reference only) | All pairs valid | Quotes 100% | Unsupported positives not increased | Cost materially lower |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| gpt-6-luna | -0.126 | 0.052 | 1.25 | +1 | False | True | True | False | True |
| claude-haiku-5.5 | -0.182 | 0.198 | 1.20 | -1 | False | False | True | False | True |

Sequential single-worker latency on one machine and one network path; not a load or concurrency benchmark.

Owner decision. This report does not promote or change the production model.
