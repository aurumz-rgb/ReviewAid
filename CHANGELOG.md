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

### Per-criterion screening pipeline (same v4.0.0 release)

The Tier-2 LLM stage no longer emits one holistic verdict with a
self-reported confidence. `pico_screen.py` (new module):

- The model judges **each criterion separately** and must return a
  verbatim supporting quote; a quote that is not in the paper downgrades
  the judgment to `unsure` (grounding applied to screening).
- Each paper is judged **k = 3 independent samples**, majority-voted per
  criterion; the **sample agreement rate** replaces the self-reported
  confidence scalar.
- Each screened paper costs exactly **three API calls** (three independent
  judgments of the full text, majority-voted per criterion) - the
  accuracy-per-cost sweet spot; the optional abstract-triage stage remains
  available in `pico_screen.screen_paper` but is off in the default path.
- Exclusion is **recall-first**: it fires only on exclusion evidence that is
  unanimous across all samples and grounded in a quote; split votes and
  quoteless verdicts are referred, never decided.
- A senior-reviewer **tiebreaker call** settles criteria on which the
  samples split (one extra call, only on disagreement); the ruling is
  grounded like every other judgment.
- Every paper leaves with a **priority score** (inclusion strength, quote
  coverage, agreement) so the human review queue is worked highest-first
  and workload-saved at fixed recall is measurable from the export.
- Screener batch limit lowered from 20 to 10 papers per batch (extractor
  unchanged); running a local clone removes the restriction.
- Include requires the driving inclusion criteria to individually clear
  an agreement floor (0.67). Conflicts, shaky agreement and unusable
  samples are referred as `Maybe` with the full per-criterion trail;
  total sample failure is an honest referral, not a regex-fallback
  exclusion.
- Screener calls run at temperature 0.0.

### Extraction: structured effect direction

- `Effect Direction` is a closed label set (`significantly increases` /
  `significantly decreases` / `no significant difference` / `unclear`)
  and `Effect Direction Evidence` must quote the paper verbatim. Strict
  label scoring becomes measurable; the label's confidence is verified
  through its evidence sentence, not literal text matching.
- `parser.fallback_uses()` exposes how often the regex fallback decided
  instead of the LLM, so a validation pilot can fail an arm whose
  fallback rate is too high.

### Evidence (offline replay, deposited CSMeD-FT corpus, 1,968 papers)

- Auto-exclusions: 133 → 44, a strict subset of the v3.0.0 set.
- Gold-include papers killed by the gate: 53 → 17 (−68%).
- 53 previously-correct auto-exclusions are now deferred to the LLM tier
  instead - the deliberate cost of the conservative gate.
- New auto-exclusions v3.0.0 would not have made: **0**, locked in by
  property tests (`test_gate_never_expands_v3_decisions`).

### Measured and rejected

Two further tightenings were prototyped and measured against the same
replay before being rejected:

- Requiring every fired gate to include a multi-word criterion rescued 2
  gold-includes but deferred 7 correct keyword exclusions to LLMs that
  over-include - a net loss.
- Narrowing the eligibility-protection window (±140 → ±100/±80 chars)
  changed nothing.

The 17 residual gold-include kills are semantic cases a deterministic
keyword gate cannot decide: negated criteria whose phrase saturates the
paper itself ("no dementia" appearing 19 times in a dementia-detection
paper), population terms the paper discusses but does not study
("healthcare providers" 7-9 times, "ICU patients" in a discussion of
other settings), and phrases embedded in category definitions
("acute LBP" inside "sub-acute LBP"). Deciding those correctly is the
Tier-2 LLM's job, not more keyword rules; the remaining lever is
criteria quality, not the gate.

The v4.0.0 validation round will re-measure end-to-end sensitivity,
specificity and workload-saved with all three backends.
