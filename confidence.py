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
            try: update_terminal_log("No extracted data available for validation. Defaulting to 0.4.", "DEBUG")
            except: pass
            return 0.4
            
        valid_fields = 0
        verified_fields = 0
        
        for key, value in extracted_data.items():
            if value and str(value).strip() != "Not Found":
                valid_fields += 1
                if key == "Effect Direction":
                    verified_fields += 1
                    continue
                val_str = str(value).strip()
                val_lower = val_str.lower()
                


                exact_match_idx = text_lower.find(val_lower)
                if exact_match_idx != -1:
                  
                    search_start = max(0, exact_match_idx - 20)
                    search_end = min(len(text_lower), exact_match_idx + len(val_lower) + 20)
                    context_window = text_lower[search_start:search_end]
                    
                    if not any(neg in context_window for neg in ["not ", "no ", "failed", "unable", "cannot", "without"]):
                        verified_fields += 1
                    else:
                        try: update_terminal_log(f"Tier 1: Negation detected near exact match for '{key}'. Dropping score.", "WARN")
                        except: pass
                else:
       
                    words = set(re.findall(r'\b\w{4,}\b', val_lower))
                    if not words:
                        verified_fields += 1
                        continue
                        
                    words_found = sum(1 for w in words if w in text_lower)
                    overlap_ratio = words_found / len(words)
                    
                    if overlap_ratio > 0.6:
              
                        first_word = next(iter(words))
                        word_idx = text_lower.find(first_word)
                        if word_idx != -1:
                            search_start = max(0, word_idx - 20)
                            search_end = min(len(text_lower), word_idx + len(val_lower) + 20)
                            context_window = text_lower[search_start:search_end]
                            if any(neg in context_window for neg in ["not ", "no ", "failed", "unable", "cannot", "without"]):
                                try: update_terminal_log(f"Tier 1: Negation detected near overlap for '{key}'. Dropping score.", "WARN")
                                except: pass
                                continue
                        verified_fields += 1
                    else:
                        try: update_terminal_log(f"Tier 1: Low overlap ({overlap_ratio:.2f}) for '{key}'. Possible hallucination.", "WARN")
                        except: pass
        
        if valid_fields == 0:
            return 0.1
        
        score = verified_fields / valid_fields
        try: update_terminal_log(f"Tier 1 Deterministic Check: {verified_fields}/{valid_fields} fields verified. Score: {score:.2f}", "DEBUG")
        except: pass
        
        if score == 1.0 and verified_fields == valid_fields:
            return 0.95  
        elif score > 0.5:
            return round(score * 0.8, 2) 
        else:
            return 0.3 

    return 0.4