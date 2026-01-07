
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import gc
import hashlib
import os


from utils import (
    update_terminal_log, extract_pdf_content, preprocess_text_for_ai, 
    MAX_INPUT_TOKENS_SCREENER, MAX_OUTPUT_TOKENS, update_processing_stats,
    to_docx, to_csv, to_excel, display_citation_section, query_llm
)
from parser import parse_result, df_from_results
from confidence import estimate_confidence

def find_exclusion_matches(text, exclusion_lists):
    matches = []
    try:
        update_terminal_log("Scanning text for exclusion keywords...", "DEBUG")
    except:
        pass
    for criteria in exclusion_lists:
        criteria = criteria.strip()
        if criteria:
            if criteria.lower() in text.lower():
                try:
                    update_terminal_log(f"Match found for exclusion criteria: '{criteria}'", "INFO")
                except:
                    pass
                matches.append(criteria)
            else:
                try:
                    update_terminal_log(f"No match for exclusion criteria: '{criteria}'", "DEBUG")
                except:
                    pass
    return matches

def run_screener():
    st.markdown("## Full-text Paper Screener")
    

    with st.expander("⚙️ Configuration", expanded=False):

        available_providers = ["Default", "OpenAI", "Anthropic", "Cohere", "DeepSeek", "GLM (Z.ai)", "Ollama (Local)"]
        provider_name = st.selectbox("Select AI Provider", available_providers, index=0)
        
        st.markdown("**Provider Details:**")
        
        if provider_name == "Default":
            st.info("""
                **Default Mode Selected.**
                - **Provider:** GLM (Z.ai)
                - **Model:** GLM-4.6V-Flash
                - **API Keys:** Loaded from `.env` file (`SCREENER_API_KEY` or `EXTRACTOR_API_KEY`).
                """)
            st.session_state['provider_name'] = "Default"
            st.session_state['model_name'] = "GLM-4.6V-Flash"
            st.session_state['api_key'] = "HIDDEN" 
        elif provider_name == "OpenAI":
            model_name = st.text_input("Model Name", value="gpt-4o", help="e.g. gpt-4o")
            api_key = st.text_input("API Key", type="password", help="Enter your OpenAI API Key")
            st.session_state['provider_name'] = "OpenAI"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key
        elif provider_name == "Anthropic":
            model_name = st.text_input("Model Name", value="claude-sonnet-4-20250514", help="e.g. claude-sonnet-4-20250514")
            api_key = st.text_input("API Key", type="password", help="Enter your Anthropic API Key")
            st.session_state['provider_name'] = "Anthropic"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key
        elif provider_name == "Cohere":
            model_name = st.text_input("Model Name", value="command-a-03-2025", help="e.g. command-a-03-2025")
            api_key = st.text_input("API Key", type="password", help="Enter your Cohere API Key")
            st.session_state['provider_name'] = "Cohere"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key
        elif provider_name == "DeepSeek":
            model_name = st.text_input("Model Name", value="deepseek-chat", help="e.g. deepseek-chat")
            api_key = st.text_input("API Key", type="password", help="Enter your DeepSeek API Key")
            st.session_state['provider_name'] = "DeepSeek"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key
        elif provider_name == "GLM (Z.ai)":
            model_name = st.text_input("Model Name", value="GLM-4.6V-Flash", help="e.g. GLM-4.6V-Flash")
            api_key = st.text_input("API Key", type="password", help="Enter your Z.ai API Key")
            st.session_state['provider_name'] = "GLM (Z.ai)"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key
        elif provider_name == "Ollama (Local)":
            model_name = st.text_input("Model Name", value="llama3", help="e.g. llama3, mistral")
            api_key = st.text_input("API Key (Optional)", type="password", help="Leave empty if not configured")
            st.session_state['ollama_base_url'] = st.text_input("Ollama Base URL", value="http://localhost:11434")
            st.session_state['provider_name'] = "Ollama (Local)"
            st.session_state['model_name'] = model_name
            st.session_state['api_key'] = api_key

        st.markdown("---")
        st.markdown("### ℹ️ Info")
        st.info("Select a provider and enter the corresponding API key. For Ollama, ensure the server is running locally. 'Default' uses the system environment variables.")
        st.markdown("---")


    st.subheader("Population Criteria")
    population_inclusion = st.text_area("Population Inclusion Criteria", placeholder="e.g. Adults aged 18–65 with MS")
    population_exclusion = st.text_area("Population Exclusion Criteria", placeholder="e.g. Patients with comorbid autoimmune diseases")

    st.subheader("Intervention Criteria")
    intervention_inclusion = st.text_area("Intervention Inclusion Criteria", placeholder="e.g. Natalizumab treatment ≥ 6 months")
    intervention_exclusion = st.text_area("Intervention Exclusion Criteria", placeholder="e.g. Dose outside approved range")

    st.subheader("Comparison Criteria")
    comparison_inclusion = st.text_area("Comparison Inclusion Criteria", placeholder="e.g. Placebo or no treatment")
    comparison_exclusion = st.text_area("Comparison Exclusion Criteria", placeholder="e.g. Active comparator like interferon beta")

    st.subheader("Outcome Criteria (Optional)")
    outcome_criteria = st.text_area("Outcome Criteria", placeholder="e.g. Annualized relapse rate, disability progression")

    uploaded_pdfs = st.file_uploader("Upload PDF Files (No docx/html formats, Strictly 20 papers in one time)", accept_multiple_files=True)
    
    fields_list = []

    if st.button("Screen Papers"):

        selected_provider = st.session_state.get('provider_name', 'OpenAI')
        
        if selected_provider == "Default":
  
            mode = st.session_state.app_mode
            from dotenv import load_dotenv
            load_dotenv()
            
            if mode == "screener":
                api_key = os.getenv("SCREENER_API_KEY")
            else:
                api_key = os.getenv("EXTRACTOR_API_KEY")
            
            if not api_key:
                st.error("SCREENER_API_KEY or EXTRACTOR_API_KEY not found in environment variables (.env).")
                st.stop()
                
            model_name = "GLM-4.6V-Flash"
            
            provider_for_call = "GLM (Z.ai)"
            update_terminal_log(f"Using Default Provider (GLM 4.6V-Flash) with Env Key.", "INFO")
        else:
 
            api_key = st.session_state.get('api_key', '')
            model_name = st.session_state.get('model_name', 'gpt-4o')
            provider_for_call = selected_provider
            
            if not api_key and provider_for_call != "Ollama (Local)":
                st.error("Please enter an API Key in the Configuration section.")
                st.stop()

        st.session_state.included_results = []
        st.session_state.excluded_results = []
        st.session_state.maybe_results = []
        st.session_state.batch_file_hashes = {}

        if not uploaded_pdfs:
            st.warning("Please upload at least one PDF file.")
            st.stop()
        
        if not any([
            population_inclusion.strip(), population_exclusion.strip(),
            intervention_inclusion.strip(), intervention_exclusion.strip(),
            comparison_inclusion.strip(), comparison_exclusion.strip(),
            outcome_criteria.strip()
        ]):
            st.warning("Please enter at least one inclusion or exclusion criterion.")
            st.stop()

        st.session_state.terminal_logs = []
        with st.expander("System Terminal (Background Processing)", expanded=True):
            st.session_state.terminal_placeholder = st.empty()
            update_terminal_log("Initializing processing session...", "SYSTEM")
            update_terminal_log(f"Mode detected: {st.session_state.app_mode}", "INFO")
            update_terminal_log(f"Provider: {provider_for_call} | Model: {model_name}", "INFO")
            update_terminal_log(f"Files to process: {min(len(uploaded_pdfs), 2000)}", "INFO")
            update_terminal_log("Allocating resources...", "DEBUG")

        max_papers = 21 
        total_pdfs = min(len(uploaded_pdfs), max_papers)
        
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        papers_processed_in_batch = 0
        

        for idx, pdf in enumerate(uploaded_pdfs[:max_papers], 1):
            
   
            if pdf is None:
                continue
            
  
            title, author, year = "", "", ""
            result = None
            text = ""
            full_text_backup = ""
            
       
            try:
                start_time_file = time.time()
                

                try:
                    pdf.seek(0)
                    pdf_bytes = pdf.read()
                except Exception as e:
                    update_terminal_log(f"File read error for {pdf.name}: {str(e)}", "ERROR")
                  
                    progress_bar.progress(idx / total_pdfs)
                    continue
                
        
                pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
                
                if pdf_hash in st.session_state.batch_file_hashes:
       
                    update_terminal_log(f"Duplicate detected (Hash match). Using cached result.", "INFO")
                    cached_result = st.session_state.batch_file_hashes[pdf_hash]
                    cached_result["filename"] = pdf.name
                    
                    status = cached_result.get("status", "").lower()
                    if "include" in status:
                        st.session_state.included_results.append(cached_result)
                    elif "exclude" in status:
                        st.session_state.excluded_results.append(cached_result)
                    elif "maybe" in status:
                        st.session_state.maybe_results.append(cached_result)
                    else:
                        st.session_state.excluded_results.append(cached_result)
                    
                    update_processing_stats("screener", 1)
                    
  
                    percent = int((idx / total_pdfs) * 100)
                    status_placeholder.markdown(f"<h4 style='text-align: center; color: #4189DC;'>{percent}% Work Done... Processing <span style='color: white'>{pdf.name}</span> (Cached)</h4>", unsafe_allow_html=True)
                    progress_bar.progress(idx / total_pdfs)
                    
          
                    del pdf_bytes 
                    continue
                
      
                text, title, author, year = extract_pdf_content(pdf_bytes)
                del pdf_bytes 

                if not text.strip():
                    update_terminal_log(f"PDF '{pdf.name}' appears empty or unreadable.", "WARN")
                    progress_bar.progress(idx / total_pdfs)
                    continue
                
                full_text_backup = text
                text = preprocess_text_for_ai(text, max_tokens=MAX_INPUT_TOKENS_SCREENER)

       
                criteria_dict = {
                    "pop_inc": population_inclusion,
                    "pop_exc": population_exclusion,
                    "int_inc": intervention_inclusion,
                    "int_exc": intervention_exclusion,
                    "comp_inc": comparison_inclusion,
                    "comp_exc": comparison_exclusion,
                    "outcome": outcome_criteria
                }
                
                confidence = estimate_confidence(
                    text, 
                    mode="screener", 
                    criteria_dict=criteria_dict, 
                    extracted_data=None, 
                    fields_list=fields_list
                )
                
              
                all_exclusions = []
                for block in [population_exclusion, intervention_exclusion, comparison_exclusion]:
                    if block.strip():
                        all_exclusions.extend([c.strip() for c in block.split(",") if c.strip()])
                
       
                matches_exc = find_exclusion_matches(text, all_exclusions)

                all_inclusions = []
                for block in [population_inclusion, intervention_inclusion, comparison_inclusion]:
                    if block.strip():
                        all_inclusions.extend([c.strip() for c in block.split(",") if c.strip()])
                
        
                matches_inc = []
                for criteria in all_inclusions:
                    if criteria.strip() and criteria.lower() in text.lower():
                        try:
                            update_terminal_log(f"Match found for inclusion criteria: '{criteria}'", "INFO")
                        except:
                            pass
                        matches_inc.append(criteria)
            
    
                if len(matches_exc) >= 1 and len(matches_inc) == 0:
                    exclusion_reason = (
                        f"Auto-excluded because {len(matches_exc)} exclusion criteria matched: {', '.join(matches_exc)}"
                    )
                    confidence = 1.0 
                    
                    result = {
                        "filename": pdf.name,
                        "status": "Exclude",
                        "reason": exclusion_reason[:500], 
                        "confidence": confidence,
                        "title": title,
                        "author": author,
                        "year": year
                    }
                    
                    st.session_state.batch_file_hashes[pdf_hash] = result
                    st.session_state.excluded_results.append(result)
                    
                    update_processing_stats("screener", 1)
                    papers_processed_in_batch += 1

               
                    percent = int((idx / total_pdfs) * 100)
                    status_placeholder.markdown(f"<h4 style='text-align: center; color: #4189DC;'>{percent}% Work Done... Processing <span style='color: white'>{pdf.name}</span></h4>", unsafe_allow_html=True)
                    progress_bar.progress(idx / total_pdfs)
                    
        
                    del text, full_text_backup, matches_exc, matches_inc, title, author, year, all_exclusions, all_inclusions
                    continue
                

                time.sleep(1) 
                
                prompt = f"""
You are an expert systematic reviewer. Your task is to screen a research paper based on specific PICO criteria.

**CRITICAL INSTRUCTION:**
Return your response as a SINGLE valid JSON object. Do not include markdown formatting (like ```json), do not add comments, and do not include conversational filler text.

**Population**
Inclusion: {population_inclusion}
Exclusion: {population_exclusion}

**Intervention**
Inclusion: {intervention_inclusion}
Exclusion: {intervention_exclusion}

**Comparison**
Inclusion: {comparison_inclusion}
Exclusion: {comparison_exclusion}

**Outcomes**: {outcome_criteria}

**Paper Text:**
\"\"\"
{text}
\"\"\"

**Task:**
1. Classify paper as "Include", "Exclude", or "Maybe" based strictly on the criteria.
2. Provide a detailed reason for the classification.
3. Extract the Paper Title, Main Author, and Publication Year.
4. If a value is not found, use "Not Found".
5. **CONFIDENCE SCORE**: Rate your confidence (0.0 to 1.0). 
   - 1.0 = The paper perfectly matches or perfectly violates the criteria with explicit evidence.
   - 0.8 - 0.9 = High confidence based on strong evidence.
   - 0.5 - 0.7 = Moderate confidence (Some ambiguity in criteria or text).
   - < 0.5 = Low confidence (Guessing, criteria vague, or text unclear).

**JSON Format Required:**
{{
  "status": "Include",
  "reason": "Detailed classification reason explaining why it fits or fails the criteria.",
  "title": "Full paper title extracted from text",
  "author": "Main author name",
  "year": "2023",
  "confidence": 0.95
}}
"""
                
       
                max_api_attempts = 3 
                retries_per_api_attempt = 3
                
                for api_attempt in range(max_api_attempts):
                    if api_attempt > 0:
                        try:
                            update_terminal_log("Previous attempt failed after retries. Initiating NEW API call for this paper...", "WARN")
                        except:
                            pass
                    
                    for retry_idx in range(retries_per_api_attempt):
                        raw_result = query_llm(prompt, provider_for_call, api_key, model_name, temperature=0.1, max_tokens=8192)
        
                        if raw_result is None:
                            try:
                                update_terminal_log("API returned None after exhaustive retries. Falling back to Regex.", "ERROR")
                            except:
                                pass
                            processing_successful = False
                            break 
                        
                        if raw_result and raw_result.strip():
                            processing_successful = True
                            break 
                        
                        if retry_idx < retries_per_api_attempt - 1:
                             try:
                                 update_terminal_log(f"API returned empty response. Retry {retry_idx + 2}/{retries_per_api_attempt}...", "ERROR")
                             except:
                                 pass
                             time.sleep(2)
                    
                    if processing_successful:
                        break
                
       
                del prompt 
                
                
                if not processing_successful:
                    try:
                        update_terminal_log("AI processing failed. Switching to Regex Fallback (Local Processing) to ensure result is generated.", "WARN")
                    except:
                        pass

                if raw_result:
                     try:
                         update_terminal_log(f"API response received. Length: {len(raw_result)} chars.", "SUCCESS")
                     except:
                         pass
                     try:
                         update_terminal_log("Parsing JSON response...", "INFO")
                     except:
                         pass
                else:
                     try:
                         update_terminal_log("Using Fallback Strategy for parsing...", "WARN")
                     except:
                         pass

        
                result = parse_result(raw_result, provider_for_call, api_key, model_name, mode="screener", original_text=full_text_backup, fields_list=fields_list)
                    
                if result:
                    processing_successful = True
                    
                    if "filename" not in result:
                        result["filename"] = pdf.name
                
     
                if raw_result:
                    del raw_result
                
   
                del full_text_backup
                gc.collect()

      
                if result and processing_successful:
                    try:
                        update_terminal_log("Result generation completed (AI or Fallback).", "SUCCESS")
                    except:
                        pass

                    ai_confidence = result.get("confidence", None)
                    if ai_confidence is not None:
                        try:
                            confidence = float(ai_confidence)
                            confidence = max(0.0, min(1.0, confidence))
                            update_terminal_log(f"Using reported confidence: {confidence}", "INFO")
                        except ValueError:
                            try:
                                update_terminal_log(f"Confidence invalid format. Using fallback.", "WARN")
                            except:
                                pass

                            confidence = estimate_confidence(
                                full_text_backup, 
                                mode="screener", 
                                criteria_dict=criteria_dict, 
                                extracted_data=None,
                                fields_list=fields_list
                            )
                    else:
                        try:
                            update_terminal_log(f"Confidence missing. Using heuristic fallback.", "WARN")
                        except:
                            pass

                        confidence = estimate_confidence(
                            full_text_backup, 
                            mode="screener", 
                            criteria_dict=criteria_dict, 
                            extracted_data=None,
                            fields_list=fields_list
                        )

                    result["confidence"] = confidence
                    
                    if confidence < 0.5:
                        result["flags"] = ["low_confidence"]
                        try:
                            update_terminal_log("Flagged: Low confidence score.", "WARN")
                        except:
                            pass

                    if "title" not in result or not result["title"] or result["title"] == "":
                        result["title"] = title
                    if "author" not in result or not result["author"] or result["author"] == "":
                        result["author"] = author
                    if "year" not in result or not result["year"] or result["year"] == "":
                        result["year"] = year
                    
                    
                    del title, author, year

                    status = result.get("status", "").strip().lower() 
                    if "include" in status:
                        status = "include"
                    elif "exclude" in status:
                        status = "exclude"
                    elif "maybe" in status:
                        status = "maybe"
                    else:
                         status = "exclude"
                    
                    if len(result.get("reason", "")) > 500:
                        result["reason"] = result["reason"][:500] + "..."

                    if status == "include":
                        st.session_state.included_results.append(result)
                        try:
                            update_terminal_log(f"Final Decision: INCLUDE", "SUCCESS")
                        except:
                            pass
                    elif status == "exclude":
                        st.session_state.excluded_results.append(result)
                        try:
                            update_terminal_log(f"Final Decision: EXCLUDE", "SUCCESS")
                        except:
                            pass
                    elif status == "maybe":
                        st.session_state.maybe_results.append(result)
                        try:
                            update_terminal_log(f"Final Decision: MAYBE", "SUCCESS")
                        except:
                            pass
                    else:
                        st.session_state.excluded_results.append(result)
                        try:
                            update_terminal_log(f"Final Decision: EXCLUDE (Default)", "INFO")
                        except:
                            pass
                    
                    update_processing_stats("screener", 1)
                    papers_processed_in_batch += 1

                    st.session_state.batch_file_hashes[pdf_hash] = result
                
             
                elapsed = time.time() - start_time_file
                try:
                    update_terminal_log(f"File processed in {elapsed:.2f}s.", "SYSTEM")
                except:
                    pass
                    
                percent = int((idx / total_pdfs) * 100)
                status_placeholder.markdown(f"<h6 style='text-align: center; color: 'white';'>Processed {percent}% of papers... Processing <span style='color: #4189DC'> {pdf.name}</span></h6>", unsafe_allow_html=True)
                progress_bar.progress(idx / total_pdfs)

            except Exception as e:               
                try:
                    update_terminal_log(f"CRITICAL ERROR processing {pdf.name}: {str(e)}", "ERROR")
                except:
                    pass
                try:
                    import traceback
                    update_terminal_log(f"Traceback: {traceback.format_exc()}", "ERROR")
                except:
                    pass
        
        
                gc.collect()


        status_placeholder.empty()
        try:
            update_terminal_log("=== Batch processing complete ===", "SYSTEM")
            update_terminal_log(f"Processed {papers_processed_in_batch} papers in this session.", "SUCCESS")
        except:
            pass

    included = len(st.session_state.included_results)
    excluded = len(st.session_state.excluded_results)
    maybe = len(st.session_state.maybe_results)
    total = included + excluded + maybe

    session_duration = time.time() - st.session_state.start_time
    avg_speed = session_duration / total if total > 0 else 0

    with st.expander("Screening Dashboard", expanded=False):
         st.metric("Papers Screened", total)
         
         colors_map = {
             "Included": "#3fb950", 
             "Excluded": "#f85149",
             "Maybe": "#d29922"     
         }
         
         fig = px.pie(
            names=["Included", "Excluded", "Maybe"],
            values=[included, excluded, maybe],
            title="Screening Decisions",
            hole=0.4,
            color=["Included", "Excluded", "Maybe"],
            color_discrete_map=colors_map
        )
         
         fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F0F4F8'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            title_font=dict(size=20)
         )
         
         col_g1, col_g2 = st.columns([3, 1])
         with col_g1:
             st.plotly_chart(fig, width='stretch')
         with col_g2:
             html_string = fig.to_html()
             st.download_button(
                label="Download Graph",
                data=html_string,
                file_name="screening_decisions_graph.html",
                mime="text/html"
            )
             del html_string

    included_results = st.session_state.included_results
    excluded_results = st.session_state.excluded_results
    maybe_results = st.session_state.maybe_results 

    def color_status(val):
        if val == "Include":
            return 'background-color: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: bold;'
        elif val == "Exclude":
            return 'background-color: rgba(239, 68, 68, 0.15); color: #f87171; font-weight: bold;'
        elif val == "Maybe":
            return 'background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; font-weight: bold;'
        return ''

    if included_results:
        st.header("Included Papers")
        df_inc = df_from_results(included_results)
        styled_inc = df_inc.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_inc, width='stretch', height=400)
        del df_inc
    else:
        st.info("No Included papers found.")

    if excluded_results:
        st.header("Excluded Papers")
        df_exc = df_from_results(excluded_results)
        styled_exc = df_exc.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_exc, width='stretch', height=400)
        del df_exc
    else:
        st.info("No Excluded papers found.")

    if maybe_results:
        st.header("Maybe Papers")
        df_maybe = df_from_results(maybe_results)
        styled_maybe = df_maybe.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_maybe, width='stretch', height=400)
        del df_maybe
    else:
        st.info("No Maybe papers found.")

    if included_results or excluded_results or maybe_results:
        st.markdown("""
        <div class="confidence-table-container">
            <h3 style="margin-top:0;">Confidence Score Interpretation</h3>
            <table style="width:100%; border-collapse: collapse; color: #F0F4F8;">
                <thead>
                    <tr>
                        <th>Confidence Score</th>
                        <th>Classification</th>
                        <th>Description</th>
                        <th>Implication</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>1.0 (100%)</strong></td>
                        <td>Definitive Match</td>
                        <td>Deterministic rule-based classification / No ambiguity.</td>
                        <td>Fully automated decision</td>
                    </tr>
                    <tr>
                        <td><strong>0.8 – 1.0</strong></td>
                        <td>Very High Confidence</td>
                        <td>AI strongly validates decision using explicit textual evidence.</td>
                        <td>Safe to accept</td>
                    </tr>
                    <tr>
                        <td><strong>0.6 – 0.79</strong></td>
                        <td>High Confidence</td>
                        <td>Criteria appear satisfied based on standard academic structure and content.</td>
                        <td>Review optional</td>
                    </tr>
                    <tr>
                        <td><strong>0.4 – 0.59</strong></td>
                        <td>Moderate Confidence</td>
                        <td>Ambiguous context or loosely met criteria.</td>
                        <td>Manual verification recommended</td>
                    </tr>
                    <tr>
                        <td><strong>0.1 – 0.39</strong></td>
                        <td>Low Confidence</td>
                        <td>Based mainly on heuristic keyword estimation.</td>
                        <td>High risk of error</td>
                    </tr>
                    <tr>
                        <td><strong>&lt; 0.1</strong></td>
                        <td>Unreliable</td>
                        <td>Derived from fallback or failed extraction methods.</td>
                        <td>Mandatory manual review</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.header("Export Results")

        def export_buttons(df, label_prefix):
            formats = {
                "DOCX": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", to_docx(df), f"{label_prefix.lower()}_papers.docx"),
                "CSV":  ("text/csv", to_csv(df), f"{label_prefix.lower()}_papers.csv"),
                "XLSX": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", to_excel(df), f"{label_prefix.lower()}_papers.xlsx")
            }

            for fmt, (mime, data, filename) in formats.items():
                st.download_button(
                    label=f"Download {label_prefix} as {fmt}",
                    data=data,
                    file_name=filename,
                    mime=mime
                )

        if included_results:
            st.subheader("Included Papers")
            df_inc = df_from_results(included_results)
            export_buttons(df_inc, "Included")
            del df_inc

        if excluded_results:
            st.subheader("Excluded Papers")
            df_exc = df_from_results(excluded_results)
            export_buttons(df_exc, "Excluded")
            del df_exc

        if maybe_results:
            st.subheader("Maybe Papers")
            df_maybe = df_from_results(maybe_results)
            export_buttons(df_maybe, "Maybe")
            del df_maybe
    

