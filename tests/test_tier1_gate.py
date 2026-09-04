import pytest
from tier1_gate import find_matches

# 1. Plain phrase match still fires (v3 behaviour preserved)
def test_plain_phrase_match():
    """A criterion present in the text is still a match."""
    text = "We randomised 60 adults with chronic low back pain."
    assert find_matches(text, ["chronic low back pain"]) == ["chronic low back pain"]

# 2. v3 substring bug: 'men' must not match inside 'women'
def test_no_substring_inside_larger_word():
    text = "Eighty women were enrolled in the study."
    assert find_matches(text, ["men"]) == []

# 3. Partial-word noise: 'rat' must not match 'ratio' or 'rates'
def test_no_partial_word_match():
    text = "The response ratio improved across both treatment rates."
    assert find_matches(text, ["rat"]) == []

# 4. Singular and plural are distinct words at the boundary
def test_singular_plural_are_distinct_words():
    text = "Trials of acupuncture in adults with chronic pain."
    assert find_matches(text, ["trials"]) == ["trials"]
    assert find_matches(text, ["trial"]) == []

# 5. Hyphenated criteria match on word edges; the phrase itself must be exact
def test_hyphenated_criterion():
    text = "Design: a cross-sectional study of school teachers."
    assert find_matches(text, ["cross-sectional study"]) == ["cross-sectional study"]
    assert find_matches(text, ["cross-sectional studies"]) == []

# 6. Punctuation next to a word still counts as a boundary
def test_punctuation_counts_as_boundary():
    text = "Exclusion criteria: pregnant women, prisoners."
    assert find_matches(text, ["pregnant"]) == ["pregnant"]

# 7. Blank criteria are ignored and empty text never matches
def test_blank_inputs():
    assert find_matches("any text at all", ["", "   ", None]) == []
    assert find_matches("", ["adults"]) == []

# 8. Matching is case-insensitive on both sides; the original criterion
#    spelling is what gets returned
def test_case_insensitive():
    text = "Patients were excluded if they were PREGNANT."
    assert find_matches(text, ["Pregnant"]) == ["Pregnant"]
