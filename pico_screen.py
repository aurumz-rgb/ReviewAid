import json
import re

from parser import clean_json_response

SCREEN_PROMPT = """You are an expert systematic reviewer. Apply EACH criterion below to the paper separately and strictly.

For EVERY criterion return:
- "verdict": "yes" (the paper meets the criterion), "no" (it does not), or "unsure" (the text does not let you decide)
- "quote": the exact sentence from the paper text the verdict is based on, copied verbatim ("" when unsure)

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

_AGREEMENT_FLOOR = 0.67


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


def aggregate(samples, inclusions, exclusions):
    """Majority-vote k samples into one screening decision.

    Exclusion wins only on a grounded majority "yes" to an exclusion
    criterion with no inclusion met; inclusion needs every sample stable
    enough to clear the agreement floor; anything else refers as "maybe".
    """
    n_inc, n_exc = len(inclusions), len(exclusions)
    per = []
    for idx in range(n_inc + n_exc):
        verdicts = [s["criteria"][idx]["verdict"] for s in samples
                    if idx < len(s["criteria"])]
        if not verdicts:
            continue
        verdict, agreement = _majority(verdicts)
        kind = "inc" if idx < n_inc else "exc"
        label = inclusions[idx] if kind == "inc" else exclusions[idx - n_inc]
        quote = next((s["criteria"][idx]["quote"] for s in samples
                      if idx < len(s["criteria"]) and s["criteria"][idx]["quote"]), "")
        per.append({"criterion": label, "kind": kind, "verdict": verdict,
                    "agreement": round(agreement, 3), "quote": quote})
    if not per:
        return {"decision": "maybe", "reason": "no usable judgments",
                "criteria": per, "agreement": 0.0}

    inc_met = [c for c in per if c["kind"] == "inc" and c["verdict"] == "yes"]
    exc_met = [c for c in per if c["kind"] == "exc" and c["verdict"] == "yes"]
    agreement = round(sum(c["agreement"] for c in per) / len(per), 3)
    reasons = [s.get("reason", "") for s in samples if s.get("reason")]

    if exc_met and not inc_met:
        decision = "exclude"
        reason = "Excluded: met exclusion criteria " + \
            ", ".join(c["criterion"] for c in exc_met) + "."
    elif inc_met and not exc_met and \
            min(c["agreement"] for c in inc_met) >= _AGREEMENT_FLOOR:
        decision = "include"
        reason = "Included: met inclusion criteria " + \
            ", ".join(c["criterion"] for c in inc_met) + "."
    else:
        decision = "maybe"
        if inc_met and exc_met:
            reason = "Conflicting criteria met - referred for review."
        elif inc_met:
            reason = "Low judgment agreement - referred for review."
        else:
            reason = "Criteria not clearly met - referred for review."
    if reasons:
        reason += " " + reasons[0]
    return {"decision": decision, "reason": reason.strip(), "criteria": per,
            "agreement": agreement}
