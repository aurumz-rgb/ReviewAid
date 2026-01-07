import re


try:
    from utils import update_terminal_log
except ImportError:
    def update_terminal_log(msg, level): pass

def estimate_confidence(text, mode="screener", criteria_dict=None, extracted_data=None, fields_list=None):
    try:
        update_terminal_log(f"Calculating heuristic confidence for mode: {mode}", "DEBUG")
    except:
        pass
    
    if not text or len(text.strip()) < 30:
        return 0.1 

    text_lower = text.lower()

    if mode == "screener":
        match_count = 0
        total_criteria = 0

        def count_matches(criteria_string):
            nonlocal match_count, total_criteria
            if not criteria_string or not criteria_string.strip():
                return
            items = [c.strip() for c in criteria_string.split(",") if c.strip()]
            total_criteria += len(items)
            for item in items:
                if item.lower() in text_lower:
                    match_count += 1
        
        if criteria_dict:
            count_matches(criteria_dict.get("pop_inc", ""))
            count_matches(criteria_dict.get("pop_exc", ""))
            count_matches(criteria_dict.get("int_inc", ""))
            count_matches(criteria_dict.get("int_exc", ""))
            count_matches(criteria_dict.get("comp_inc", ""))
            count_matches(criteria_dict.get("comp_exc", ""))
            count_matches(criteria_dict.get("outcome", ""))

        if total_criteria == 0:
            try:
                update_terminal_log("No criteria provided for heuristic estimation. Defaulting to 0.4.", "DEBUG")
            except:
                pass
            return 0.4
        
        score = match_count / total_criteria
        
        if score > 0.8:
            score = min(score + 0.1, 1.0)
        
        try:
            update_terminal_log(f"Screener Heuristic: {match_count}/{total_criteria} criteria matched. Score: {score:.2f}", "DEBUG")
        except:
            pass
        return round(score, 2)

    elif mode == "extractor":
        if not extracted_data or not isinstance(extracted_data, dict):
            try:
                update_terminal_log("No extracted data available for validation. Defaulting to 0.4.", "DEBUG")
            except:
                pass
            return 0.4
            
        valid_fields = 0
        found_fields = 0
        
        for key, value in extracted_data.items():
            if value and str(value).strip() != "Not Found":
                valid_fields += 1

                val_str = str(value).strip()
                if len(val_str) > 5: 
                    if val_str.lower() in text_lower:
                        found_fields += 1
                    else:
                        words = val_str.split()[:3] 
                        if all(word in text_lower for word in words):
                            found_fields += 1
                elif len(val_str) > 0:
                     if val_str.lower() in text_lower:
                        found_fields += 1
        
        if valid_fields == 0:
            return 0.1
        
        score = found_fields / valid_fields
        try:
            update_terminal_log(f"Extractor Heuristic: {found_fields}/{valid_fields} fields verified in text. Score: {score:.2f}", "DEBUG")
        except:
            pass
        return round(score, 2)

    return 0.4