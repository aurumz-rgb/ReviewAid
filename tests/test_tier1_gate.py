import pytest
from tier1_gate import corroborated, evaluate_tier1, find_matches

def test_plain_phrase_match():
    """A criterion present in the text is still a match."""
    text = "We randomised 60 adults with chronic low back pain."
    assert find_matches(text, ["chronic low back pain"]) == ["chronic low back pain"]

def test_no_substring_inside_larger_word():
    text = "Eighty women were enrolled in the study."
    assert find_matches(text, ["men"]) == []

def test_no_partial_word_match():
    text = "The response ratio improved across both treatment rates."
    assert find_matches(text, ["rat"]) == []

def test_singular_plural_are_distinct_words():
    text = "Trials of acupuncture in adults with chronic pain."
    assert find_matches(text, ["trials"]) == ["trials"]
    assert find_matches(text, ["trial"]) == []

def test_hyphenated_criterion():
    text = "Design: a cross-sectional study of school teachers."
    assert find_matches(text, ["cross-sectional study"]) == ["cross-sectional study"]
    assert find_matches(text, ["cross-sectional studies"]) == []

def test_punctuation_counts_as_boundary():
    text = "Exclusion criteria: pregnant women, prisoners."
    assert find_matches(text, ["pregnant"]) == ["pregnant"]

def test_blank_inputs():
    assert find_matches("any text at all", ["", "   ", None]) == []
    assert find_matches("", ["adults"]) == []

def test_case_insensitive():
    text = "Patients were excluded if they were PREGNANT."
    assert find_matches(text, ["Pregnant"]) == ["Pregnant"]

def test_negated_phrase_does_not_match():
    text = "Patients with no acute LBP were not recruited."
    assert find_matches(text, ["acute LBP"]) == []

def test_negation_prefixes():
    text = "The cohort consisted of non-pregnant adults."
    assert find_matches(text, ["pregnant"]) == []
    text2 = "Participants were free of acute LBP at baseline."
    assert find_matches(text2, ["acute LBP"]) == []

def test_clean_mention_survives_negated_mention():
    text = ("Background: no acute LBP cohort has been reported. "
            "Methods: we enrolled 120 adults with acute LBP.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

def test_negated_criterion_wording_is_not_self_vetoed():
    text = "We excluded studies of patients with no dementia."
    assert find_matches(text, ["no dementia"]) == ["no dementia"]

def test_background_mention_demoted():
    text = ("Introduction: Low back pain is a major problem. Previous "
            "studies have shown that acute LBP is usually self-limiting. "
            "Outcomes were measured at 12 months.")
    assert find_matches(text, ["acute LBP"]) == []

def test_eligibility_context_protects_hit():
    text = ("Previous research on acute LBP is mixed. We randomised 140 "
            "adults with acute LBP to exercise or usual care.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

def test_methods_mention_survives_background_mention():
    text = ("Background: acute LBP is common in primary care. "
            "Methods: we recruited adults with acute LBP from 4 clinics.")
    assert find_matches(text, ["acute LBP"]) == ["acute LBP"]

def test_study_design_mention_survives():
    text = ("Eligible patients were adults referred to physiotherapy. "
            "The follow-up survey was cross-sectional in design.")
    assert find_matches(text, ["cross-sectional"]) == ["cross-sectional"]

def test_lone_single_word_criterion_does_not_fire():
    assert corroborated(["adults"]) is False

def test_lone_multiword_criterion_fires():
    assert corroborated(["acute LBP"]) is True

def test_second_criterion_corroborates():
    assert corroborated(["adults", "acute LBP"]) is True
    assert corroborated(["adults", "children"]) is True

def test_duplicate_criteria_do_not_corroborate():
    assert corroborated(["adults", "Adults"]) is False

def test_empty_list_never_fires():
    assert corroborated([]) is False

def test_lone_generic_keyword_end_to_end():
    text = "Sixty adults completed the programme."
    matches = find_matches(text, ["adults"])
    assert matches == ["adults"]
    assert corroborated(matches) is False

def test_evaluate_excludes():
    text = ("We randomised 140 adults with acute LBP. Patients were "
            "excluded if they were pregnant.")
    v = evaluate_tier1(text, ["acute LBP", "pregnant"], ["chronic LBP"])
    assert v["decision"] == "exclude"
    assert v["qualified_exclusions"] == ["acute LBP", "pregnant"]
    assert v["qualified_inclusions"] == []
    assert v["reason"].startswith("Auto-excluded because 2")

def test_evaluate_inclusion_blocks():
    text = "Adults with chronic LBP were enrolled."
    v = evaluate_tier1(text, ["pregnant"], ["chronic LBP"])
    assert v["decision"] == "escalate"
    assert v["qualified_inclusions"] == ["chronic LBP"]

def test_evaluate_reports_discarded():
    text = ("Background studies have described acute LBP as common. "
            "No acute LBP cohort was available for the pilot.")
    v = evaluate_tier1(text, ["acute LBP"], [])
    assert v["decision"] == "escalate"
    reasons = {d["reason"] for d in v["discarded"]}
    assert reasons == {"background", "negated"}

def test_evaluate_lone_generic_escalates():
    v = evaluate_tier1("Sixty adults completed the programme.",
                       ["adults"], [])
    assert v["decision"] == "escalate"
    assert v["qualified_exclusions"] == ["adults"]

def test_inclusion_match_stays_loose():
    text = "Enrolment was restricted to noninstitutionalised adults."
    v = evaluate_tier1(text, ["surgery"], ["institutionalised adults"])
    assert v["decision"] == "escalate"
    assert v["qualified_inclusions"] == ["institutionalised adults"]

def test_negated_inclusion_mention_still_blocks():
    text = "No acute LBP cohort was available; all patients had chronic pain."
    v = evaluate_tier1(text, ["chronic pain"], ["acute LBP"])
    assert v["decision"] == "escalate"
    assert v["qualified_exclusions"] == ["chronic pain"]
    assert v["qualified_inclusions"] == ["acute LBP"]

def test_gate_never_expands_v3_decisions():
    texts = [
        # background-only exclusion mention, inclusion present (v3 fired)
        ("Previous studies of acute LBP are contradictory. We enrolled "
         "adults with chronic LBP and gave exercise therapy."),
        # lone generic keyword (v3 fired)
        ("Sixty adults completed the eight-week programme."),
        # negated mention plus a real hit (v3 fired on the real one)
        ("No acute LBP was seen at baseline. We randomised 90 adults "
         "with acute LBP to physiotherapy."),
        # clean corroborated exclusions (v3 fired)
        ("We excluded pregnant women and current smokers from the "
         "cohort of adults with asthma."),
    ]
    exclusions = ["acute LBP", "adults", "pregnant", "current smokers"]
    inclusions = ["chronic LBP", "adults with asthma"]
    for text in texts:
        v = evaluate_tier1(text, exclusions, inclusions)
        if v["decision"] != "exclude":
            continue
        tl = text.lower()
        v3_exc = any(c.lower() in tl for c in exclusions)
        v3_inc = any(c.lower() in tl for c in inclusions)
        assert v3_exc and not v3_inc, f"gate expanded on: {text[:50]}"

def test_background_acute_lbp_no_longer_excludes_chronic_trial():
    text = ("Introduction. Acute LBP is common and usually self-limiting. "
            "Previous studies of acute LBP shaped our outcome choice. "
            "Methods. We randomised 180 adults with chronic LBP to "
            "supervised exercise or usual care for 12 months.")
    v = evaluate_tier1(text, ["acute LBP"], ["chronic LBP"])
    assert v["decision"] == "escalate"
