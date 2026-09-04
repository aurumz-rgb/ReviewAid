# Changelog

## v4.0.0 (2026-09-04)

The decision architecture is unchanged from v3.0.0: Tier-1 deterministic
keyword gate → Tier-2 LLM screening with confidence override → heuristic
fallbacks. What changed is the Tier-1 keyword gate itself, which the
architecture validation study against CSMeD-FT human gold standards showed
was the single largest error source: 133 keyword auto-exclusions per
backend, 53 of them killing gold-include papers, driven by over-broad
criteria keywords ("adults", "children") and phrases that only occur in
background text ("acute LBP" in the introduction of a chronic-LBP trial).

### Tier-1 keyword gate (`tier1_gate.py`, new module)

- **Word-boundary matching** replaces raw substring scans: "men" no longer
  matches inside "women", "rat" no longer matches "ratio".
- **Negation guard**: a mention preceded by a negator ("no acute LBP",
  "non-pregnant", "free of") no longer fires the gate. The vocabulary
  extends the Check E negators already used by `confidence.py`.
- **Background-context guard**: a mention sitting in background or
  related-work discourse is ignored unless eligibility language appears
  nearby.
- **Corroboration**: a lone single-word exclusion criterion ("adults",
  "children", "pregnant") can no longer auto-exclude a paper; it needs a
  second qualifying criterion. Multi-word phrases still decide alone, as
  in v3.0.0.
- **Inclusion keywords keep v3's raw substring match** on purpose: they
  only ever defer a paper to the LLM tier, never decide it. Guarding them
  as well let papers lose their protective inclusion hit and made the
  gate fire on papers v3.0.0 would have deferred (caught by the corpus
  replay below).
- `evaluate_tier1()` returns the full verdict with every discarded hit
  (negated / background) so each auto-exclusion stays auditable; the
  System Terminal now reports discarded hits per paper.
- `screener.find_exclusion_matches` keeps its name and signature as a
  compatibility wrapper over the new matcher.

### Evidence (offline replay, deposited CSMeD-FT corpus, 1,968 papers)

- Auto-exclusions: 133 → 45, a strict subset of the v3.0.0 set.
- Gold-include papers killed by the gate: 53 → 18 (−66%).
- 53 previously-correct auto-exclusions are now deferred to the LLM tier
  instead - the deliberate cost of the conservative gate.
- New auto-exclusions v3.0.0 would not have made: **0**, locked in by
  property tests (`test_gate_never_expands_v3_decisions`).

The v4.0.0 validation round will re-measure end-to-end sensitivity,
specificity and workload-saved with all three backends.
