"""CP3 Phase 2B: dark, fail-closed production runtime safety layer (D-096, D-097, D-101).

Built around the frozen D-087 runtime, never inside it: reservations, a correlated usage
ledger with durable call intents, the phase-scoped live gate, the per-IP ticket and the
operation runner. Public live stays blocked by the D-096 bound (full analysis US$84.77 > US$2).
"""
