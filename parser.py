import json
import json5
import re
import time


try:
    from utils import update_terminal_log, query_llm, MAX_INPUT_TOKENS_SCREENER
except ImportError:

    def update_terminal_log(msg, level): pass
    def query_llm(*args, **kwargs): return None
    MAX_INPUT_TOKENS_SCREENER = 128000

def clean_json_response(raw_str):
    """
    Bulletproof JSON cleaning pipeline.
    Handles Markdown, Trailing Commas, Comments, and Control Characters.
    """
    if not raw_str:
        return ""

    raw_str = re.sub(r'```json\s*', '', raw_str)
    raw_str = re.sub(r'```\s*', '', raw_str)
    
    raw_str = re.sub(r'//.*', '', raw_str)
    
    raw_str = re.sub(r'/\*.*?\*/', '', raw_str, flags=re.DOTALL)
    
    raw_str = re.sub(r',\s*([}\]])', r'\1', raw_str)
    
    start = raw_str.find('{')
    end = raw_str.rfind('}')
    
    if start == -1 or end == -1 or end < start:
        return "" 
    
    cleaned = raw_str[start:end+1]
    
    def replace_newlines_in_strings(match):
        return match.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    cleaned = re.sub(r'"(?:\\.|[^"\\])*"', replace_newlines_in_strings, cleaned)
    
    return cleaned

def _attempt_re_extraction(original_text, provider_name, api_key, model_name, mode, fields_list):
    """
    If first attempt failed (empty or bad structure), try once more with a very strict prompt.
    """
    try:
        update_terminal_log("Re-extraction initiated...", "SYSTEM")
    except:
        pass
    
    text_snippet = original_text[:MAX_INPUT_TOKENS_SCREENER*3] 
    
    if mode == "screener":
        strict_prompt = f"""
You failed to provide a valid JSON response previously. You are an expert systematic reviewer.
Analyze this text and return a valid JSON object ONLY.

Text:
\"\"\"{text_snippet}\"\"\"

Required JSON Format:
{{
  "status": "Include/Exclude/Maybe",
  "reason": "Brief reason",
  "title": "Paper Title",
  "author": "Author Name",
  "year": "Year",
  "confidence": 0.5
}}
Return ONLY JSON object.
"""
    else:
        fields_str = ", ".join(fields_list)
        strict_prompt = f"""
You failed to provide a valid JSON response previously.
Extract these fields: {fields_str}.
If a field is not found, use the value "Not Found".

Text:
\"\"\"{text_snippet}\"\"\"

Required JSON Format:
{{
  "extracted": {{
    "{fields_list[0]}": "Value",
    ...
  }},
  "confidence": 0.5
}}
Return ONLY JSON object.
"""

    re_raw = query_llm(strict_prompt, provider_name, api_key, model_name, temperature=0.1, max_tokens=2048)
    del strict_prompt
    del text_snippet 
    
    if re_raw and re_raw != "RATE_LIMIT_ERROR":
        cleaned = clean_json_response(re_raw)
        try:
            data = json.loads(cleaned)
            try:
                update_terminal_log("Re-extraction successful.", "SUCCESS")
            except:
                pass
            del re_raw, cleaned
            return data
        except:
            pass
    
    try:
        update_terminal_log("Re-extraction failed. Using default/regex.", "ERROR")
    except:
        pass
    return _get_default_result(mode, fields_list)

def _get_default_result(mode, fields_list):
    if mode == "screener":
        return {
            "status": "Error",
            "reason": "Failed to extract data",
            "title": "Not Found",
            "author": "Not Found",
            "year": "Not Found",
            "confidence": 0.0
        }
    else:
        result = {"extracted": {}, "confidence": 0.0}
        if fields_list:
            for field in fields_list:
                result["extracted"][field] = "Not Found"
        return result

def _regex_extract_fallback(text, mode, fields_list):
    """
    Extracts specific key-value pairs from unstructured text using Regex.
    Used when JSON parsing fails completely. Improved to handle non-JSON formats.
    """
    try:
        update_terminal_log("Running Regex Fallback extraction...", "DEBUG")
    except:
        pass
    
    result = {}
    confidence = 0.2 
    
    if mode == "screener":
        result["status"] = "Error"
        result["reason"] = "Regex Fallback: AI Blocked - Using Local Rules"
        result["title"] = "Not Found"
        result["author"] = "Not Found"
        result["year"] = "Not Found"
        confidence = 0.2 

        lower_t = text.lower()
        
        if "include" in lower_t and "exclude" not in lower_t:
            result["status"] = "Include"
            result["reason"] = "Regex Fallback: Inferred Inclusion (Local)"
            confidence = 0.3
        elif "exclude" in lower_t:
            result["status"] = "Exclude"
            result["reason"] = "Regex Fallback: Inferred Exclusion (Local)"
            confidence = 0.3
        
        patterns = {
            "title": [r'"title"\s*:\s*"([^"]+)"', r'title\s*:\s*"?([^"\n]+)"?', r'Title\s*[:\-]\s*([^\n]+)'],
            "author": [r'"author"\s*:\s*"([^"]+)"', r'author\s*:\s*"?([^"\n]+)"?'],
            "year": [r'"year"\s*:\s*"([^"]+)"', r'year\s*:\s*(\d{4})']
        }
        
        for key, regex_list in patterns.items():
            for pattern in regex_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    result[key] = val
                    break 
        
    else:
        result = {"extracted": {}, "confidence": 0.2} 
        if fields_list:
            for field in fields_list:
                val = "Not Found"
                # FIX: Wrapped field in re.escape() to handle special chars like parentheses
                pattern = rf'"{re.escape(field)}"\s*:\s*"([^"]*)"'
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    # FIX: Wrapped field in re.escape() here as well
                    pattern = rf'{re.escape(field)}\s*[:\-]\s*"?([^"\n]+)"?'
                    match = re.search(pattern, text, re.IGNORECASE)
                
                if match:
                    val = match.group(1).strip()
                    result["extracted"][field] = val
                
        result["confidence"] = confidence
    
    return result

def parse_result(raw_result, provider_name, api_key, model_name, mode="screener", fields_list=None, original_text=None):
    """
    Parses AI response with extreme prejudice.
    Tries Standard JSON -> JSON5 -> AI Repair -> Re-extraction -> Regex Fallback.
    """
    if raw_result is None:
        try:
            update_terminal_log("API response was None. Using Regex Fallback (Local Processing).", "WARN")
        except:
            pass
        if original_text:
            return _regex_extract_fallback(original_text, mode, fields_list)
        else:
            return _get_default_result(mode, fields_list)
    
    try:
        update_terminal_log("Starting Bulletproof JSON parsing pipeline...", "DEBUG")
    except:
        pass
    
    cleaned_json = clean_json_response(raw_result)
    
    if not cleaned_json or len(cleaned_json) < 10:
        try:
            update_terminal_log("Cleaned JSON is empty or invalid. Structure likely missing.", "WARN")
        except:
            pass
        if original_text:
            try:
                update_terminal_log("Attempting Re-extraction due to structural failure...", "WARN")
            except:
                pass
            res = _attempt_re_extraction(original_text, provider_name, api_key, model_name, mode, fields_list)
            del original_text 
            return res
        return _regex_extract_fallback(raw_result, mode, fields_list)

    try:
        try:
            update_terminal_log("Attempting standard json.loads()...", "DEBUG")
        except:
            pass
        data = json.loads(cleaned_json)
        try:
            update_terminal_log("Standard JSON parse successful.", "SUCCESS")
        except:
            pass
        del cleaned_json 
        return data
    except json.JSONDecodeError as e:
        try:
            update_terminal_log(f"Standard JSON failed: {str(e)}", "WARN")
        except:
            pass

    try:
        try:
            update_terminal_log("Attempting JSON5 parser (relaxed standard)...", "DEBUG")
        except:
            pass
        data = json5.loads(cleaned_json)
        try:
            update_terminal_log("JSON5 parse successful.", "SUCCESS")
        except:
            pass
        del cleaned_json 
        return data
    except Exception as e:
        try:
            update_terminal_log(f"JSON5 failed: {str(e)}", "WARN")
        except:
            pass

    try:
        update_terminal_log("Attempting AI-based JSON repair...", "WARN")
    except:
        pass
    repair_prompt = f"""
The system generated a malformed JSON response. Your task is to fix the syntax errors and return ONLY a valid JSON object.

Rules:
1. Do NOT change the values, only fix the syntax (quotes, commas, braces).
2. Do NOT include markdown formatting (```).
3. Return ONLY the JSON.

Malformed JSON:
{cleaned_json}
"""
    fixed_raw = query_llm(repair_prompt, provider_name, api_key, model_name, temperature=0.1, max_tokens=1024)
    del repair_prompt 
    
    if fixed_raw and fixed_raw != "RATE_LIMIT_ERROR":
        fixed_cleaned = clean_json_response(fixed_raw)
        if fixed_cleaned:
            try:
                try:
                    update_terminal_log("Testing AI-Repaired JSON...", "DEBUG")
                except:
                    pass
                data = json.loads(fixed_cleaned)
                try:
                    update_terminal_log("AI repair successful.", "SUCCESS")
                except:
                    pass
                del fixed_raw, fixed_cleaned
                return data
            except:
                try:
                    update_terminal_log("AI repair failed.", "ERROR")
                except:
                    pass
    else:
        try:
            update_terminal_log("AI repair skipped (empty/rate limit).", "WARN")
        except:
            pass

    try:
        update_terminal_log("All parsers failed. Using Regex Extraction Fallback.", "ERROR")
    except:
        pass
    return _regex_extract_fallback(raw_result, mode, fields_list)

def df_from_results(results):
    rows = []
    for r in results:
        row = {
            "Filename": r.get("filename", ""),
            "Title": r.get("title", ""),
            "Author": r.get("author", ""),
            "Year": r.get("year", ""),
            "Confidence": r.get("confidence", "")
        }
        
        status = r.get("status", "").lower()
        if status == "include":
            row["Reason for Inclusion"] = r.get("reason", "")
        elif status == "exclude":
            row["Reason for Exclusion"] = r.get("reason", "")
        elif status == "maybe":
            row["Reason for Maybe"] = r.get("reason", "")
            
        rows.append(row)
    import pandas as pd
    return pd.DataFrame(rows)

def df_from_extracted_results(results):
    rows = []
    for r in results:
        row = {
            "Filename": r.get("filename", ""),
            "Confidence": r.get("confidence", "")
        }
        row.update(r.get("extracted", {}))
        rows.append(row)
    import pandas as pd
    return pd.DataFrame(rows)