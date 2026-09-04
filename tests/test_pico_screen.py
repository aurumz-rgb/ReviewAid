import pytest
from pico_screen import (aggregate, build_adjudication_prompt,
                        build_screen_prompt, parse_adjudication,
                        parse_screen_response, screen_paper, split_criteria)

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

def sample(inc, exc, reason="r", grounded=True):
    crits = [{"verdict": v, "quote": "q" if v == "yes" else "", "grounded": grounded}
             for v in inc + exc]
    return {"criteria": crits, "reason": reason}


def test_unanimous_grounded_exclusion_excludes():
    samples = [sample(["no"], ["yes", "no"]),
               sample(["no"], ["yes", "no"]),
               sample(["no"], ["yes", "no"])]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "exclude"
    assert "cancer" in out["reason"]

# Recall-first: a split exclusion vote refers instead of deciding
def test_split_exclusion_vote_refers():
    samples = [sample(["no"], ["yes", "no"]),
               sample(["no"], ["yes", "no"]),
               sample(["no"], ["no", "no"])]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "maybe"

def test_ungrounded_exclusion_refers():
    samples = [sample(["no"], ["yes", "no"], grounded=False)
               for _ in range(3)]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert out["decision"] == "maybe"

def test_priority_score_present_and_bounded():
    samples = [sample(["yes"], ["no", "no"]) for _ in range(3)]
    out = aggregate(samples, ["adults"], ["cancer", "pregnancy"])
    assert 0.0 <= out["priority"] <= 1.0
    assert out["priority"] > 0

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

# screen_paper: triage + self-consistency through a query callback
import json as _json

FULL_PAPER = ("We screened 60 adolescents aged 12-15 with chronic low "
              "back pain.\n"
              "Introduction\nPrior work on rehabilitation is long.\n"
              "Methods\nPatients were adults with chronic low back pain "
              "allocated to exercise or usual care.")
TRIAGE_CRITERIA = {"pop_inc": "adults with chronic low back pain",
                   "pop_exc": "adolescents",
                   "int_inc": "", "int_exc": "",
                   "comp_inc": "", "comp_exc": "", "outcome": ""}


def resp(*pairs):
    """A canned model response judging every criterion in order."""
    return _json.dumps({"criteria": [{"id": i + 1, "verdict": v, "quote": q}
                                     for i, (v, q) in enumerate(pairs)],
                        "reason": "r"})


INC_YES = ("yes", "Patients were adults with chronic low back pain "
           "allocated to exercise or usual care.")
EXC_YES = ("yes", "We screened 60 adolescents aged 12-15 with chronic low "
           "back pain.")


class FakeLLM:
    def __init__(self, abstract_reply, full_reply):
        self.calls = []
        self.abstract_reply = abstract_reply
        self.full_reply = full_reply

    def __call__(self, prompt):
        self.calls.append(prompt)
        if "Introduction" in prompt:
            return self.full_reply
        return self.abstract_reply


def test_abstract_stage_excludes_without_reading_full_text():
    llm = FakeLLM(resp(("no", ""), EXC_YES), resp(("no", ""), ("no", "")))
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, llm, k=2, triage=True)
    assert out["decision"] == "exclude"
    assert out["stage"] == "abstract"
    assert len(llm.calls) == 2

def test_undecided_abstract_falls_through_to_full_text():
    llm = FakeLLM("", resp(INC_YES, ("no", "")))
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, llm, k=2, triage=True)
    assert out["decision"] == "include"
    assert out["stage"] == "full_text"
    assert len(llm.calls) == 4
    assert any("allocated to exercise" in p for p in llm.calls)

def test_triage_off_runs_single_stage():
    llm = FakeLLM("", resp(INC_YES, ("no", "")))
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, llm, k=3, triage=False)
    assert out["stage"] == "single_stage"
    assert len(llm.calls) == 3

def test_unusable_samples_are_dropped_not_counted():
    replies = iter(["", "not json", resp(INC_YES, ("no", ""))])
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, lambda p: next(replies),
                       k=3, triage=False)
    assert out["decision"] == "include"
    assert out["samples_used"] == 1

# Tiebreaker adjudication for split criteria
def test_adjudication_prompt_lists_votes_and_quotes():
    disputes = [{"id": 0, "kind": "inclusion", "criterion": "adults",
                 "votes": {"yes": 2, "no": 1}, "quotes": ["q1", "q2"]}]
    prompt = build_adjudication_prompt(disputes, "paper text")
    assert "adults" in prompt
    assert "2 yes" in prompt
    assert "q1" in prompt

def test_parse_adjudication_grounds_rulings():
    raw = _json.dumps({"rulings": [{"id": 0, "verdict": "yes",
                                    "quote": "We screened 60 adolescents aged 12-15 with chronic low back pain."}]})
    out = parse_adjudication(raw, FULL_PAPER)
    assert out[0][0] == "yes"
    assert out[0][2] is True
    assert parse_adjudication("garbage", FULL_PAPER) is None

def test_disagreement_triggers_tiebreaker_call():
    ruling = _json.dumps({"rulings": [{"id": 0, "verdict": "yes",
                                       "quote": "We screened 60 adolescents aged 12-15 with chronic low back pain."}]})
    def raw_sample(inc, exc):
        crits = [{"id": i + 1, "verdict": v, "quote": "", "grounded": False}
                 for i, v in enumerate(inc + exc)]
        return _json.dumps({"criteria": crits, "reason": "r"})
    replies = iter([raw_sample(["yes"], ["no"]), raw_sample(["no"], ["no"]), ruling])
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, lambda p: next(replies), k=2)
    assert out["decision"] == "include"
    assert out["adjudicated"] is True
    assert out["samples_used"] == 2

def test_no_disagreement_skips_tiebreaker():
    def raw_sample(inc, exc):
        crits = [{"id": i + 1, "verdict": v, "quote": "", "grounded": False}
                 for i, v in enumerate(inc + exc)]
        return _json.dumps({"criteria": crits, "reason": "r"})
    replies = iter([raw_sample(["yes"], ["no"]), raw_sample(["yes"], ["no"])])
    out = screen_paper(FULL_PAPER, TRIAGE_CRITERIA, lambda p: next(replies), k=2)
    assert out["adjudicated"] is False
