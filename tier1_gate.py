import re




def _match_pattern(criterion):
    # Anchor at word boundaries so "men" cannot match inside "women", but
    # let phrases that start/end in punctuation (e.g. "18-65 years") pass.
    head = r"\b" if re.match(r"\w", criterion[0]) else ""
    tail = r"\b" if re.search(r"\w$", criterion[-1]) else ""
    return head + re.escape(criterion) + tail


def find_matches(text, criteria_list):
    """Criteria whose phrase occurs at a word boundary anywhere in the text.

    Same contract as the v3 substring scan, minus substring-inside-word
    false hits ("men" no longer matches "women", "rat" no longer matches
    "ratio").
    """
    t = (text or "").lower()
    found = []
    for criterion in criteria_list:
        c = (criterion or "").strip().lower()
        if not c:
            continue
        if re.search(_match_pattern(c), t):
            found.append(criterion.strip())
    return found
