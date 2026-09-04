import re




# Same negation vocabulary as the Check E windows in confidence.py, plus a
# few population forms ("non-pregnant", "free of acute LBP").
_NEGATORS = ("not ", "no ", "non-", "without ", "failed", "unable", "cannot",
             "never", "nor ", "absence of", "free of")

# A negator this many chars before a hit vetoes it.
_NEGATION_WINDOW = 48

# A hit sitting in background/related-work discourse is demoted, but only
# when no eligibility language surrounds it. Conservative on purpose: with
# neither kind of marker nearby, the hit stays.
_ELIGIBILITY_MARKERS = ("inclusion", "exclusion", "eligible", "eligibility",
                        "criteria", "included", "excluded", "enrolled",
                        "recruited", "randomised", "randomized", "allocated",
                        "screened", "consented", "selected", "diagnosed with",
                        "patients with", "adults with", "participants with",
                        "underwent", "received")
_ELIGIBILITY_WINDOW = 140

_BACKGROUND_MARKERS = ("previous", "prior ", "literature", "guideline",
                       "recommend", "meta-analysis", "meta-analyses",
                       "systematic review", "studies have", "studies of",
                       "have shown", "have reported", "have been ",
                       "evidence suggests", "whether", "unlike",
                       "in contrast", "history of", "risk of", "remains",
                       "controversial")
_BACKGROUND_BEFORE = 100
_BACKGROUND_AFTER = 60


def _match_pattern(criterion):
    # Anchor at word boundaries so "men" cannot match inside "women", but
    # let phrases that start/end in punctuation (e.g. "18-65 years") pass.
    head = r"\b" if re.match(r"\w", criterion[0]) else ""
    tail = r"\b" if re.search(r"\w$", criterion[-1]) else ""
    return head + re.escape(criterion) + tail


def _is_background_hit(text_lower, start, end):
    """True when a hit only occurs in background discourse.

    Requires a background marker just before or after the hit AND no
    eligibility marker in the wider context; the two checks together keep
    study-design and eligibility statements safe from demotion.
    """
    nearby = (text_lower[max(0, start - _BACKGROUND_BEFORE):start] +
              text_lower[end:end + _BACKGROUND_AFTER])
    if not any(m in nearby for m in _BACKGROUND_MARKERS):
        return False
    context = text_lower[max(0, start - _ELIGIBILITY_WINDOW):
                         min(len(text_lower), end + _ELIGIBILITY_WINDOW)]
    return not any(m in context for m in _ELIGIBILITY_MARKERS)


def _hit_verdicts(criterion, text_lower):
    """(start, end, status) for every hit of one criterion.

    status is "clean", "negated" or "background". The negation window sits
    strictly before the match, so a criterion that is itself a negated
    phrase ("no dementia") is never vetoed by its own wording.
    """
    verdicts = []
    for m in re.finditer(_match_pattern(criterion), text_lower):
        window = text_lower[max(0, m.start() - _NEGATION_WINDOW):m.start()]
        if any(neg in window for neg in _NEGATORS):
            verdicts.append((m.start(), m.end(), "negated"))
        elif _is_background_hit(text_lower, m.start(), m.end()):
            verdicts.append((m.start(), m.end(), "background"))
        else:
            verdicts.append((m.start(), m.end(), "clean"))
    return verdicts


def find_matches(text, criteria_list):
    """Criteria with at least one clean hit in the text.

    Same contract as the v3 substring scan, minus substring-inside-word
    false hits ("men" no longer matches "women") and minus mentions that
    only occur under negation ("no acute LBP" is not a population hit).
    """
    t = (text or "").lower()
    found = []
    for criterion in criteria_list:
        c = (criterion or "").strip().lower()
        if not c:
            continue
        if any(v[2] == "clean" for v in _hit_verdicts(c, t)):
            found.append(criterion.strip())
    return found


def evaluate_tier1(text, exclusion_criteria, inclusion_criteria):
    """One paper's full Tier-1 verdict: fire the gate or hand it to the LLM.

    The decision contract is v3's - exclude on qualifying exclusion
    criteria with no qualifying inclusion criterion - with the guards
    applied before counting. Every hit a guard threw out is reported in
    "discarded" so an exclusion can be audited after the fact.

    Guards live on the exclusion side only. Inclusion criteria keep v3's
    raw substring match on purpose: they never decide a paper, they only
    defer it, so the loose match is the safe direction. Guarding them too
    let papers lose their protective inclusion hit and fired the gate on
    papers v3 would have deferred (seen in the corpus replay).
    """
    t = (text or "").lower()
    qualified_exclusions, qualified_inclusions, discarded = [], [], []

    for criterion in exclusion_criteria:
        c = (criterion or "").strip().lower()
        if not c:
            continue
        verdicts = _hit_verdicts(c, t)
        if any(v[2] == "clean" for v in verdicts):
            qualified_exclusions.append(criterion.strip())
        for start, end, status in verdicts:
            if status != "clean":
                entry = {"criterion": criterion.strip(), "reason": status}
                if entry not in discarded:
                    discarded.append(entry)

    for criterion in inclusion_criteria:
        c = (criterion or "").strip().lower()
        if not c:
            continue
        if c in t:
            qualified_inclusions.append(criterion.strip())

    fire = corroborated(qualified_exclusions) and not qualified_inclusions
    if fire:
        reason = (f"Auto-excluded because {len(qualified_exclusions)} "
                  f"exclusion criteria matched: "
                  f"{', '.join(qualified_exclusions)}")
    else:
        reason = ""

    return {
        "decision": "exclude" if fire else "escalate",
        "qualified_exclusions": qualified_exclusions,
        "qualified_inclusions": qualified_inclusions,
        "discarded": discarded,
        "reason": reason,
    }


def corroborated(matches):
    """Whether the qualified exclusion list is strong enough to auto-exclude.

    One-word criteria ("adults", "children", "pregnant") occur somewhere in
    nearly every paper's text, so a lone such word never decides a paper -
    it needs any second qualifying criterion behind it. Multi-word phrases
    ("acute LBP", "cross-sectional studies") keep deciding on their own, as
    in v3. Distinctness is case-insensitive so a duplicated criterion
    cannot corroborate itself.
    """
    distinct = {m.lower() for m in matches}
    if len(distinct) >= 2:
        return True
    if len(distinct) == 1:
        return len(next(iter(distinct)).split()) > 1
    return False
