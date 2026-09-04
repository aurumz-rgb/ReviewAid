import pytest
import screener
from tier1_gate import evaluate_tier1

def test_find_exclusion_matches_uses_gate():
    # 'men' inside 'women' is no longer a match (v3 substring bug)
    assert screener.find_exclusion_matches(
        "Eighty women were enrolled.", ["men"]) == []

def test_find_exclusion_matches_skips_negated():
    text = "Patients with no acute LBP were not recruited."
    assert screener.find_exclusion_matches(text, ["acute LBP"]) == []

def test_find_exclusion_matches_returns_original_spelling():
    text = "Exclusion criteria: Pregnant women, prisoners."
    assert screener.find_exclusion_matches(text, ["pregnant"]) == ["pregnant"]

def test_evaluate_tier1_screening_contract():
    pop_inc = "adults with chronic low back pain"
    pop_exc = "acute LBP, pregnant"
    int_inc = "exercise therapy"
    int_exc = "surgery"
    filler = ("Introduction. Low back pain is a leading cause of disability "
              "worldwide and drives substantial health-care use, while "
              "imaging findings correlate poorly with symptoms in this "
              "population. ")
    text = (filler +
            "Previous studies of acute LBP motivated our question, as prior "
            "surveys in this setting remain sparse and no regional registry "
            "currently exists. Setting. Four physiotherapy clinics took part "
            "with ethics approval from the university board. Methods. We "
            "randomised 200 adults with chronic low back pain to exercise "
            "therapy or usual care.")
    excl = [c.strip() for c in pop_exc.split(",")] + [int_exc]
    v = evaluate_tier1(text, excl, [pop_inc, int_inc])
    assert v["decision"] == "escalate"
    discarded = {d["criterion"]: d["reason"] for d in v["discarded"]}
    assert discarded.get("acute LBP") == "background"
    assert "adults with chronic low back pain" in v["qualified_inclusions"]
