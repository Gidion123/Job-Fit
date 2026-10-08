"""Operation horizons derived from the accepted Phase 2A call model and the frozen timeouts.

W(call) = frozen per-call timeout + GRACE (the SDK/httpx timeout bounds each connect/read/write
step, not the whole call). The horizon of a phase is the sum of W over every call the accepted
cost model says is reachable, plus a bounded orchestration margin: in any schedule the makespan
is at most the sum of all call durations plus orchestration time, so no reachable sequence is
cut short and Phase 3 scheduling changes cannot invalidate it. These are conservative operating
thresholds (D-101), not a proof that a request terminates; a breach fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

GRACE_SECONDS = 30.0
EMBED_TIMEOUT_SECONDS = 60.0          # literal in the frozen OpenRouterClient._embed_attempt (pinned by a test)
ORCHESTRATION_SECONDS = {'parse': 120.0, 'recommendation': 600.0,
                         'search': 60.0, 'job_analysis': 120.0}      # D-103 public-beta phases
PERSISTENCE_MARGIN_SECONDS = 60.0
MAX_WINDOW_SECONDS = 24 * 3600.0      # carry-over rows can then only come from the previous day


def chat_timeout_seconds(config_path: Path) -> float:
    value = yaml.safe_load(Path(config_path).read_text())['request_timeout_seconds']
    return float(value)


def max_attempts(chain) -> int:
    """Longest reachable attempt sequence of a ChainBound over all its regions."""
    return max(len(seq) for region in chain.regions.values() for seq in region.sequences.values())


@dataclass(frozen=True)
class PhaseWindow:
    phase: str
    chat_wall: float          # W(chat)
    embed_wall: float         # W(embed)
    calls_wall: float         # sum of W over the reachable call multiset
    horizon: float            # T_op: latest moment (after the admission anchor) a call may still be running
    window: float             # active_until - created_at

    def wall(self, kind: str) -> float:
        return self.embed_wall if kind == 'embed' else self.chat_wall


def phase_window(phase: str, bounds, chat_timeout: float) -> PhaseWindow:
    chat_wall = chat_timeout + GRACE_SECONDS
    embed_wall = EMBED_TIMEOUT_SECONDS + GRACE_SECONDS
    chains = bounds.chains
    if phase == 'parse':
        calls = max_attempts(chains['parse']) * chat_wall
    elif phase == 'recommendation':
        k = int(bounds.details['k'])
        chat_calls = k * sum(max_attempts(chains[c]) for c in ('extraction', 'matching', 'fallback'))
        calls = embed_wall + chat_calls * chat_wall
    elif phase == 'search':                       # D-103: one CV query embedding, no LLM call
        calls = embed_wall
    elif phase == 'job_analysis':                 # D-103: one JD: extraction, Sol matching, Luna fallback
        calls = sum(max_attempts(chains[c]) for c in ('extraction', 'matching', 'fallback')) * chat_wall
    else:
        raise ValueError(f'unknown phase {phase}')
    horizon = calls + ORCHESTRATION_SECONDS[phase]
    window = horizon + PERSISTENCE_MARGIN_SECONDS
    if not 0 < window < MAX_WINDOW_SECONDS:
        raise ValueError('operation window must be positive and below 24 hours')
    return PhaseWindow(phase, chat_wall, embed_wall, calls, horizon, window)
