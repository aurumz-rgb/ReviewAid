
import pytest
from parser import (clean_json_response, fallback_uses,
                    _regex_extract_fallback, parse_result, df_from_results,
                    df_from_extracted_results)
from unittest.mock import patch

# 1. Test JSON Cleaning
def test_clean_json_response_basic():
    dirty_json = '```json\n  { "status": "Include", "reason": "Good" } \n```'
    expected = '{ "status": "Include", "reason": "Good" }'
    result = clean_json_response(dirty_json)
    assert result.strip() == expected.strip()

def test_clean_json_remove_trailing_comma():
    dirty_json = '{ "status": "Include", "reason": "Good", }'
    result = clean_json_response(dirty_json)
    assert '} ,' not in result
    assert '}' in result

# 2. Test Regex Fallback
def test_regex_fallback_screener():
    text = "This is a study.\nTitle: AI Review\nAuthor: John Doe\nYear: 2023."
    result = _regex_extract_fallback(text, mode="screener", fields_list=[])
    
    assert result["status"] in ["Include", "Exclude", "Error"]
    assert result["title"] == "AI Review"
    assert result["author"] == "John Doe"
    assert result["year"] == "2023"

def test_regex_fallback_extractor():
    text = 'Intervention: Drug A\nSample Size: 50.'
    fields = ["Intervention", "Sample Size"]
    result = _regex_extract_fallback(text, mode="extractor", fields_list=fields)
    
    assert "extracted" in result
    assert result["extracted"]["Intervention"] == "Drug A"
    assert result["extracted"]["Sample Size"] == "50."

# 3. Test Main Parse Logic
@patch('parser.query_llm') 
@patch('parser.update_terminal_log')
def test_parse_result_success(mock_log, mock_query):
    valid_json_string = '{ "status": "Include", "reason": "Matches", "title": "Test", "author": "A", "year": "2024", "confidence": 0.9 }'
    
    result = parse_result(valid_json_string, "OpenAI", "fake-key", "gpt-4", mode="screener", fields_list=None, original_text=None)
    
    assert result["status"] == "Include"
    assert result["confidence"] == 0.9
    assert not mock_query.called 

@patch('parser.query_llm') 
@patch('parser.update_terminal_log')
def test_parse_result_with_unescaped_newlines(mock_log, mock_query):
    dirty_json_string = '{ "reason": "This is a multi-line\nreason.", "confidence": 0.8 }'
    
    result = parse_result(dirty_json_string, "OpenAI", "fake-key", "gpt-4", mode="screener", fields_list=None, original_text=None)
    
    assert result["reason"] == "This is a multi-line\nreason."
    assert result["confidence"] == 0.8
    assert not mock_query.called
def test_df_from_results_year_stays_string():
    """Mixed int/str years made pyarrow crash the results table."""
    results = [
        {"filename": "a.pdf", "title": "T1", "author": "A1", "year": 2015,
         "status": "include", "reason": "fits", "confidence": 0.9},
        {"filename": "b.pdf", "title": "T2", "author": "A2", "year": "2015",
         "status": "exclude", "reason": "wrong population", "confidence": 1.0},
    ]
    df = df_from_results(results)
    assert list(df["Year"]) == ["2015", "2015"]

def test_df_from_extracted_results_coerces_values_to_string():
    results = [
        {"filename": "a.pdf", "confidence": 0.8,
         "extracted": {"Sample Size": 120, "Year": None}},
        {"filename": "b.pdf", "confidence": 0.9,
         "extracted": {"Sample Size": "120", "Year": "2021"}},
    ]
    df = df_from_extracted_results(results)
    assert list(df["Sample Size"]) == ["120", "120"]
    assert list(df["Year"]) == ["", "2021"]

def test_fallback_counter_increments():
    before = fallback_uses()
    _regex_extract_fallback("some paper text", "screener", [])
    assert fallback_uses() == before + 1
