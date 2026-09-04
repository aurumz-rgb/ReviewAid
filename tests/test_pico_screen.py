import pytest
from pico_screen import (aggregate, build_screen_prompt, parse_screen_response,
                        split_criteria)

PAPER = ("We randomised 60 adults with chronic low back pain. "
         "Patients with cancer were excluded from the cohort.")

CRITERIA = {"pop_inc": "adults with chronic low back pain",
            "pop_exc": "cancer, pregnancy",
            "int_inc": "exercise therapy",
            "int_exc": "",
            "comp_inc": "",
            "comp_exc": "",
            "outcome": "pain intensity at 12 months"}


def test_split_criteria_across_blocks():
    inc, exc = split_criteria(CRITERIA)
    assert inc == ["adults with chronic low back pain", "exercise therapy"]
    assert exc == ["cancer", "pregnancy"]

def test_prompt_carries_criteria_and_text():
    prompt = build_screen_prompt(PAPER, CRITERIA)
    assert "adults with chronic low back pain" in prompt
    assert "cancer" in prompt
    assert PAPER in prompt
    assert "pain intensity" in prompt

def test_parse_grounds_quotes_against_text():
    raw = ('{"criteria": ['
           '{"id": 1, "verdict": "yes", "quote": "We randomised 60 adults '
           'with chronic low back pain."},'
           '{"id": 2, "verdict": "yes", "quote": "This line is nowhere '
           'in the paper."}], "reason": "r"}')
    out = parse_screen_response(raw, PAPER)
    assert out["criteria"][0] == {"verdict": "yes", "quote":
                                  "We randomised 60 adults with chronic "
                                  "low back pain.", "grounded": True}
    assert out["criteria"][1]["verdict"] == "unsure"
    assert out["criteria"][1]["quote"] == ""
    assert out["criteria"][1]["grounded"] is False

def test_parse_returns_none_on_garbage():
    assert parse_screen_response("", PAPER) is None
    assert parse_screen_response("not json at all", PAPER) is None
    assert parse_screen_response('{"reason": "no criteria"}', PAPER) is None

def sample(inc, exc, reason="r"):
    crits = [{"verdict": v, "quote": "q" if v == "yes" else "", "grounded": True}
             for v in inc + exc]
    return {"criteria": crits, "reason": reason}


def test_exclusion_majority_excludes():
    samples = [sample(["no"], ["yes", "no"]),
               sample(["no"], ["yes", "no"]),
               sample(["no"], ["no", "no"])]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "exclude"
    assert "cancer" in out["reason"]

def test_stable_inclusion_includes():
    samples = [sample(["yes"], ["no", "no"]) for _ in range(3)]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "include"
    assert out["agreement"] == 1.0

def test_conflicting_criteria_refer():
    samples = [sample(["yes"], ["yes", "no"]) for _ in range(3)]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "maybe"

def test_shaky_inclusion_refers():
    samples = [sample(["yes"], ["no", "no"]),
               sample(["yes"], ["no", "no"]),
               sample(["no"], ["no", "no"])]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "maybe"
    assert "agreement" in out["reason"].lower()

def test_no_usable_samples_refers():
    out = aggregate([], ["adults"], ["cancer"])
    assert out["decision"] == "maybe"
    assert out["criteria"] == []
