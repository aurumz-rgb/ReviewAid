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

# 9. Negation guard: "no acute LBP" is not a population hit
def test_negated_phrase_does_not_match():
    text = "Patients with no acute LBP were not recruited."
    assert find_matches(text, ["acute LBP"]) == []

# 10. Prefixed negation forms are vetoed too
def test_negation_prefixes():
    text = "The cohort consisted of non-pregnant adults."
    assert find_matches(text, ["pregnant"]) == []
    text2 = "Participants were free of acute LBP at baseline."
    assert find_matches(text2, ["acute LBP"]) == []

# 11. A negated mention does not hide a clean mention elsewhere
def test_clean_mention_survives_negated_mention():
    text = ("Background: no acute LBP cohort has been reported. "
            "Methods: we enrolled 120 adults with acute LBP.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

# 12. A criterion that is itself a negated phrase is not vetoed by its
#     own wording
def test_negated_criterion_wording_is_not_self_vetoed():
    text = "We excluded studies of patients with no dementia."
    assert find_matches(text, ["no dementia"]) == ["no dementia"]

# 13. Background demotion: the phrase appears only in intro discourse,
#     far from any eligibility language
def test_background_mention_demoted():
    text = ("Introduction: Low back pain is a major problem. Previous "
            "studies have shown that acute LBP is usually self-limiting. "
            "Outcomes were measured at 12 months.")
    assert find_matches(text, ["acute LBP"]) == []

# 14. Eligibility language nearby protects the same phrase
def test_eligibility_context_protects_hit():
    text = ("Previous research on acute LBP is mixed. We randomised 140 "
            "adults with acute LBP to exercise or usual care.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

# 15. A demoted background mention does not hide a methods mention
def test_methods_mention_survives_background_mention():
    text = ("Background: acute LBP is common in primary care. "
            "Methods: we recruited adults with acute LBP from 4 clinics.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

# 16. Study-design self-descriptions are not background discourse
def test_study_design_mention_survives():
    text = ("Eligible patients were adults referred to physiotherapy. "
            "The follow-up survey was cross-sectional in design.")
    assert find_matches(text, ["cross-sectional"]) == ["cross-sectional"]
