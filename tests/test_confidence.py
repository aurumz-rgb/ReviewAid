import pytest
from confidence import estimate_confidence

# 1. Test Exact Match (Check A)
def test_extractor_exact_match():
    """Check A: Exact string match should verify the field."""
    text = "The study enrolled 45 participants. The conclusion is positive."
    extracted_data = {"Sample Size": "45 participants"}
    score = estimate_confidence(text, mode="extractor", extracted_data=extracted_data)
    assert score == 0.95  

# 2. Test Negation Detection (Check E)
def test_extractor_negation_detection():
    """Check E: Negation detection should drop the score if 'not' is near the match."""
    text = "Natalizumab is not safe during active SARS-CoV-2 infection."
    extracted_data = {"Safety": "Natalizumab is safe"}
    score = estimate_confidence(text, mode="extractor", extracted_data=extracted_data)
    assert score < 0.5  

# 3. Test Hallucination Catch (Check B)
def test_extractor_hallucination_catch():
    """Check B: Low token overlap should drop the score for hallucinated data."""
    text = "The drug is effective for treating multiple sclerosis."
    extracted_data = {"Conclusion": "The drug is completely toxic and kills everyone instantly."}
    score = estimate_confidence(text, mode="extractor", extracted_data=extracted_data)
    assert score < 0.5  

# 4. Test Paraphrased Match (Check B)
def test_extractor_paraphrased_match():
    """Check B: Semantic token overlap should verify paraphrased text."""
    text = "The clinical trial proved that the vaccine works well and is highly effective."
    extracted_data = {"Conclusion": "The vaccine works well."}
    score = estimate_confidence(text, mode="extractor", extracted_data=extracted_data)
    assert score > 0.5  

# 5. Test Screener Keyword Match
def test_screener_keyword_match():
    """Test Screener heuristic logic."""
    text = "This study focuses on adults receiving Natalizumab for MS."
    criteria_dict = {
        "pop_inc": "adults",
        "int_inc": "Natalizumab",
        "pop_exc": "Children"
    }
    score = estimate_confidence(text, mode="screener", criteria_dict=criteria_dict)
    assert score > 0.5