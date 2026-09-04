import re




# Same negation vocabulary as the Check E windows in confidence.py, plus a
# few population forms ("non-pregnant", "free of acute LBP").
_NEGATORS = ("not ", "no ", "non-", "without ", "failed", "unable", "cannot",
             "never", "nor ", "absence of", "free of")

# A negator this many chars before a hit vetoes it.
_NEGATION_WINDOW = 48


def _match_pattern(criterion):
    # Anchor at word boundaries so "men" cannot match inside "women", but
    # let phrases that start/end in punctuation (e.g. "18-65 years") pass.
    head = r"\b" if re.match(r"\w", criterion[0]) else ""
    tail = r"\b" if re.search(r"\w$", criterion[-1]) else ""
    return head + re.escape(criterion) + tail


def _qualifying_hits(criterion, text_lower):
    """Spans of hits for one criterion that survive the negation guard.

    The window sits strictly before the match, so a criterion that is itself
    a negated phrase ("no dementia") is never vetoed by its own wording.
    """
    spans = []
    for m in re.finditer(_match_pattern(criterion), text_lower):
        window = text_lower[max(0, m.start() - _NEGATION_WINDOW):m.start()]
        if any(neg in window for neg in _NEGATORS):
            continue
        spans.append((m.start(), m.end()))
    return spans


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
        if _qualifying_hits(c, t):
            found.append(criterion.strip())
    return found
