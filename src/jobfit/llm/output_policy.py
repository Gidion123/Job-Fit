"""Versioned output allowances for the CP2.3 development coverage experiment.

The ratios are the observed p99 output/input ratios from successful Part B
OpenRouter calls, multiplied by 1.5. CV parsing has only three observations.
This policy changes an allowance, not a prompt or an evaluation rule.
"""
from __future__ import annotations

from math import ceil
import json

POLICY_VERSION = 'pipeline-v1.1-output-policy'
# Minimum max_completion_tokens among the published DeepSeek V4.1 Flash
# OpenRouter endpoints inspected on 4 October 2026.
MODEL_OUTPUT_LIMIT = 131_072
POLICY = {
    'jd_extraction': {'ratio': 2.004420866489832 * 1.5, 'floor': 20_000, 'per_unit': 96},
    'evidence_matching': {'ratio': 1.5464025026068822 * 1.5, 'floor': 18_000, 'per_unit': 64},
    'cv_parsing': {'ratio': 9.030508474576271 * 1.5, 'floor': 12_000, 'per_unit': 128},
}


def output_allowance(task: str, input_tokens: int, expected_units: int,
                     model_output_limit: int = MODEL_OUTPUT_LIMIT) -> int:
    if task not in POLICY:
        raise ValueError('unknown output allowance task')
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0
           for n in (input_tokens, expected_units)):
        raise ValueError('input tokens and expected units must be nonnegative integers')
    if isinstance(model_output_limit, bool) or model_output_limit < 1:
        raise ValueError('model output limit must be positive')
    row = POLICY[task]
    value = max(row['floor'], ceil(row['ratio'] * input_tokens +
                                    row['per_unit'] * expected_units))
    return min(model_output_limit, value)


def estimate_input_tokens(prompt: str, payload: dict, schema: dict) -> int:
    """Conservative local estimate for sizing only; reported usage stays authoritative."""
    serialized = json.dumps({'prompt': prompt, 'payload': payload, 'schema': schema}, ensure_ascii=False)
    return max(1, ceil(len(serialized.encode('utf-8')) / 4))
