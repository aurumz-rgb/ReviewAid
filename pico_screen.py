import json
import re

from parser import clean_json_response

SCREEN_PROMPT = """You are an expert systematic reviewer. Apply EACH criterion below to the paper separately and strictly.

For EVERY criterion return:
- "verdict": "yes" or "no" or "unsure"
- "quote": the sentence from the paper text the verdict is based on, in the paper's own words ("" when unsure)

Meaning of "yes":
- For an INCLUSION criterion: the paper clearly satisfies it.
- For an EXCLUSION criterion: the paper's own study has the excluded property, so the paper must be excluded. If the paper merely mentions the topic in passing, answer "no".

Judge only what the text says about THE PAPER ITSELF - its own participants, methods and results. Ignore background mentions, related work, other studies and category definitions.

**Criteria**
Inclusion:
{inclusion_block}
Exclusion:
{exclusion_block}
{outcome_line}

**Paper Text:**
\"\"\"
{text}
\"\"\"

Return ONLY a JSON object in this exact shape:
{{
  "criteria": [
    {{"id": 1, "verdict": "yes", "quote": "..."}},
    {{"id": 2, "verdict": "no", "quote": "..."}}
  ],
  "reason": "one short paragraph summarising the decision"
}}"""

ADJUDICATION_PROMPT = """You are the senior reviewer settling disagreements in a systematic review screening.

For each disputed criterion below, the junior judgments did not agree. Read the paper text and give the FINAL verdict.

Return ONLY a JSON object in this exact shape:
{{
  "rulings": [
    {{"id": 1, "verdict": "yes" or "no" or "unsure", "quote": "the sentence from the paper that settles it"}}
  ]
}}

**Disputed criteria:**
{disputes}

**Paper Text:**
\"\"\"
{text}
\"\"\"
"""

_AGREEMENT_FLOOR = 0.67
_ABSTRACT_LIMIT = 2500
_SECTION_HEADING = re.compile(
    r"\n\s*(introduction|background|methods?|materials and methods)\s*\n",
    re.IGNORECASE)


def split_criteria(criteria_dict):
    """Comma-split the screener criteria blocks into (inclusions, exclusions)."""
    def items(*keys):
        out = []
        for k in keys:
            for c in (criteria_dict.get(k) or "").split(","):
                c = c.strip()
                if c:
                    out.append(c)
        return out
    return (items("pop_inc", "int_inc", "comp_inc"),
            items("pop_exc", "int_exc", "comp_exc"))


def build_screen_prompt(text, criteria_dict):
    inclusions, exclusions = split_criteria(criteria_dict)
    inclusion_block = "\n".join(f"{i+1}. {c}" for i, c in enumerate(inclusions)) or "1. (none)"
    exclusion_block = "\n".join(f"{i+1}. {c}" for i, c in enumerate(exclusions)) or "1. (none)"
    outcome = (criteria_dict.get("outcome") or "").strip()
    outcome_line = f"Outcome of interest (context only, not judged): {outcome}" if outcome else ""
    return SCREEN_PROMPT.format(text=text, inclusion_block=inclusion_block,
                                exclusion_block=exclusion_block,
                                outcome_line=outcome_line)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def parse_screen_response(raw, text):
    """Parse one sample into per-criterion verdicts, grounding every quote.

    A verdict whose quote cannot be found in the paper text is downgraded
    to "unsure" - the same Check-A idea the extractor applies to fields,
    applied to screening judgments. Returns None when nothing usable came
    back.
    """
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(clean_json_response(raw), strict=False)
    except (ValueError, TypeError):
        return None
    items = data.get("criteria") if isinstance(data, dict) else None
    if not isinstance(items, list) or not items:
        return None
    t = _norm(text)
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        verdict = str(item.get("verdict", "unsure")).strip().lower()
        if verdict not in ("yes", "no", "unsure"):
            verdict = "unsure"
        quote = str(item.get("quote", "") or "").strip()
        grounded = bool(quote) and _norm(quote) in t
        if quote and not grounded:
            verdict = "unsure"
        out.append({"verdict": verdict, "quote": quote if grounded else "",
                    "grounded": grounded})
    if not out:
        return None
    return {"criteria": out, "reason": str(data.get("reason", "") or "")}


def _majority(verdicts):
    counts = {"yes": 0, "no": 0, "unsure": 0}
    for v in verdicts:
        counts[v] = counts.get(v, 0) + 1
    best = max(counts, key=counts.get)
    return best, counts[best] / len(verdicts)


def _collect(samples, inclusions, exclusions):
    """Per-criterion majority verdicts from the k samples."""
    per = []
    for idx in range(len(inclusions) + len(exclusions)):
        entries = [s["criteria"][idx] for s in samples
                   if idx < len(s["criteria"])]
        if not entries:
            continue
        verdicts = [e["verdict"] for e in entries]
        verdict, agreement = _majority(verdicts)
        kind = "inc" if idx < len(inclusions) else "exc"
        label = inclusions[idx] if kind == "inc" else exclusions[idx - len(inclusions)]
        quote = next((e["quote"] for e in entries if e.get("quote")), "")
        per.append({"id": idx, "criterion": label, "kind": kind,
                    "verdict": verdict, "agreement": round(agreement, 3),
                    "quote": quote,
                    "grounded": any(e.get("grounded") for e in entries),
                    "unanimous": len(set(verdicts)) == 1})
    return per


def decide(per, inclusions, reasons=()):
    """Recall-first decision from per-criterion verdicts.

    A paper is excluded only when an exclusion criterion is met
    unanimously across all samples AND carries a grounded quote - weak
    evidence can never take a study out. Include needs the driving
    criteria above the agreement floor with no exclusion met. Everything
    else is referred. The priority score ranks the human review queue:
    highest first, so workload-saved at a given recall is measurable.
    """
    if not per:
        return {"decision": "maybe", "reason": "no usable judgments",
                "criteria": per, "agreement": 0.0, "priority": 0.0}

    agreement = round(sum(c["agreement"] for c in per) / len(per), 3)
    inc_met = [c for c in per if c["kind"] == "inc" and c["verdict"] == "yes"]
    exc_any = [c for c in per if c["kind"] == "exc" and c["verdict"] == "yes"]
    exc_fired = [c for c in exc_any if c["unanimous"] and c["grounded"]]

    if exc_fired and not inc_met:
        decision = "exclude"
        reason = "Excluded: met exclusion criteria " + \
            ", ".join(c["criterion"] for c in exc_fired) + "."
    elif inc_met and not exc_any and \
            min(c["agreement"] for c in inc_met) >= _AGREEMENT_FLOOR:
        decision = "include"
        reason = "Included: met inclusion criteria " + \
            ", ".join(c["criterion"] for c in inc_met) + "."
    else:
        decision = "maybe"
        if inc_met and exc_any:
            reason = "Conflicting criteria met - referred for review."
        elif inc_met:
            reason = "Low judgment agreement - referred for review."
        else:
            reason = "Criteria not clearly met - referred for review."
    reason = reason.strip()
    if reasons:
        reason += " " + reasons[0]

    inc = [c for c in per if c["kind"] == "inc"]
    inc_strength = (sum(c["agreement"] for c in inc if c["verdict"] == "yes")
                    / len(inc)) if inc else 0.0
    coverage = sum(1 for c in per if c["quote"]) / len(per)
    priority = round(0.6 * inc_strength + 0.25 * coverage + 0.15 * agreement, 3)

    return {"decision": decision, "reason": reason.strip(), "criteria": per,
            "agreement": agreement, "priority": priority}


def aggregate(samples, inclusions, exclusions):
    """Majority-vote k samples into one screening decision."""
    per = _collect(samples, inclusions, exclusions)
    reasons = [s.get("reason", "") for s in samples if s.get("reason")]
    return decide(per, inclusions, reasons)


def _title_abstract(text):
    """The text before the first section heading, capped at a budget."""
    m = _SECTION_HEADING.search(text)
    cut = m.start() if m else min(len(text), _ABSTRACT_LIMIT)
    abstract = text[:cut].strip()
    return abstract or text[:_ABSTRACT_LIMIT]


def _gather_samples(text, criteria_dict, query_fn, k):
    prompt = build_screen_prompt(text, criteria_dict)
    samples = []
    for i in range(k):
        parsed = parse_screen_response(query_fn(prompt, i + 1), text)
        if parsed:
            samples.append(parsed)
    return samples


def _disputes(samples, inclusions, exclusions):
    """Criteria on which the samples did not agree."""
    out = []
    for idx in range(len(inclusions) + len(exclusions)):
        verdicts = [s["criteria"][idx]["verdict"] for s in samples
                    if idx < len(s["criteria"])]
        if len(set(verdicts)) > 1:
            kind = "inclusion" if idx < len(inclusions) else "exclusion"
            label = inclusions[idx] if idx < len(inclusions) \
                else exclusions[idx - len(inclusions)]
            quotes = [s["criteria"][idx]["quote"] for s in samples
                      if idx < len(s["criteria"]) and s["criteria"][idx]["quote"]]
            counts = {v: verdicts.count(v) for v in set(verdicts)}
            out.append({"id": idx, "kind": kind, "criterion": label,
                        "votes": counts, "quotes": quotes})
    return out


def build_adjudication_prompt(disputes, text):
    lines = []
    for i, d in enumerate(disputes, 1):
        votes = ", ".join(f"{n} {v}" for v, n in d["votes"].items())
        entry = (f"{i}. [{d['kind']}] {d['criterion']} - votes: {votes}. "
                 f"Quoted evidence so far: {' | '.join(d['quotes']) or 'none'}")
        lines.append(entry)
    return ADJUDICATION_PROMPT.format(disputes="\n".join(lines), text=text)


def parse_adjudication(raw, text):
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(clean_json_response(raw), strict=False)
    except (ValueError, TypeError):
        return None
    rulings = data.get("rulings") if isinstance(data, dict) else None
    if not isinstance(rulings, list) or not rulings:
        return None
    t = _norm(text)
    out = {}
    for item in rulings:
        if not isinstance(item, dict):
            continue
        try:
            rid = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        verdict = str(item.get("verdict", "unsure")).strip().lower()
        if verdict not in ("yes", "no", "unsure"):
            verdict = "unsure"
        quote = str(item.get("quote", "") or "").strip()
        grounded = bool(quote) and _norm(quote) in t
        out[rid] = (verdict, quote if grounded else "", grounded)
    return out or None


def _adjudicate(disputes, text, query_fn, k):
    return parse_adjudication(
        query_fn(build_adjudication_prompt(disputes, text), k + 1), text)


def screen_paper(text, criteria_dict, query_fn, k=3, triage=False):
    """Screen one paper: k per-criterion samples, majority-voted, with a
    senior-reviewer tiebreaker call for split criteria.

    Exclusion is recall-first: it fires only on unanimous, grounded
    exclusion evidence - weak evidence refers instead of deciding. The
    returned verdict carries a priority score for the human review queue.
    """
    inclusions, exclusions = split_criteria(criteria_dict)

    if triage:
        abstract = _title_abstract(text)
        samples = _gather_samples(abstract, criteria_dict, query_fn, k)
        if aggregate(samples, inclusions, exclusions)["decision"] == "exclude":
            verdict = aggregate(samples, inclusions, exclusions)
            verdict["stage"] = "abstract"
            verdict["samples_used"] = len(samples)
            return verdict

    samples = _gather_samples(text, criteria_dict, query_fn, k)
    per = _collect(samples, inclusions, exclusions)

    adjudicated = False
    disputes = _disputes(samples, inclusions, exclusions)
    if disputes and samples:
        rulings = _adjudicate(disputes, text, query_fn, k)
        if rulings:
            for d in disputes:
                ruling = rulings.get(d["id"])
                if not ruling:
                    continue
                verdict, quote, grounded = ruling
                for c in per:
                    if c["id"] == d["id"]:
                        c["verdict"] = verdict
                        c["quote"] = quote
                        c["grounded"] = grounded
                        c["unanimous"] = True
                        c["agreement"] = 1.0 if grounded else 0.5
                        adjudicated = True

    reasons = [s.get("reason", "") for s in samples if s.get("reason")]
    verdict = decide(per, inclusions, reasons)
    verdict["stage"] = "full_text" if triage else "single_stage"
    verdict["samples_used"] = len(samples)
    verdict["adjudicated"] = adjudicated
    return verdict
