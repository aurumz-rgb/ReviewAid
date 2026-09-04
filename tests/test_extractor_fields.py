import pytest
from extractor import FIELD_DESCRIPTIONS, effect_direction_rule
from confidence import estimate_confidence

# 1. The effect-direction fields exist with their labelling contract
def test_effect_direction_field_descriptions():
    assert "significantly increases" in FIELD_DESCRIPTIONS["Effect Direction"]
    assert "copied verbatim" in FIELD_DESCRIPTIONS["Effect Direction Evidence"]

def test_effect_direction_rule_only_for_direction_fields():
    assert effect_direction_rule(["Intervention", "Outcome"]) == ""
    rule = effect_direction_rule(["Effect Direction",
                                  "Effect Direction Evidence"])
    assert "significantly decreases" in rule
    assert "copied verbatim" in rule

# 2. The categorical direction label is verified through its Evidence
#    sentence, not through literal text matching
def test_effect_direction_label_exempt_from_grounding():
    text = ("Patients on natalizumab had significantly fewer relapses "
            "than placebo.")
    extracted = {"Effect Direction": "significantly decreases",
                 "Effect Direction Evidence": "significantly fewer relapses "
                                              "than placebo"}
    score = estimate_confidence(text, mode="extractor",
                                extracted_data=extracted)
    assert score == 0.95

# 3. A direction with no grounded evidence still scores low
def test_ungrounded_evidence_keeps_confidence_low():
    text = "The paper discusses an exercise programme for older adults."
    extracted = {"Effect Direction": "significantly decreases",
                 "Effect Direction Evidence": "relapses were far fewer."}
    score = estimate_confidence(text, mode="extractor",
                                extracted_data=extracted)
    assert score < 0.5
