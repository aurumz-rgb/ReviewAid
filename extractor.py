

import streamlit as st
import pandas as pd
import time
import gc
import hashlib


from utils import (
    update_terminal_log, extract_pdf_content, preprocess_text_for_ai, 
    MAX_INPUT_TOKENS_EXTRACTOR, MAX_OUTPUT_TOKENS, update_processing_stats,
    to_docx, to_csv, to_excel, display_citation_section, query_llm
)
from parser import parse_result, df_from_extracted_results
from confidence import estimate_confidence

def run_extractor():
    st.markdown("## Full-text Data Extractor")
    

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
        st.info("Select a provider and enter the corresponding API key. For Ollama, ensure that server is running locally. 'Default' uses to system environment variables.")
        st.markdown("---")
  

    fields = st.text_input("Fields to Extract (comma-separated)", placeholder="e.g. Author, Year, Study Design, Sample Size, Conclusion")
    fields_list = [f.strip() for f in fields.split(",") if f.strip()]
    
    if "Paper Title" not in fields_list:
        fields_list.insert(0, "Paper Title")
    
    if len(fields_list) == 1 and fields_list[0] == "Paper Title":
        st.info("If left Empty, Only Paper Title will be extracted.")
        st.info("Important: Short-form field names (e.g., Intervention_Mean, Control_N) are not supported. You must use fully expanded descriptions (e.g., Intervention_Mean: mean value of the continuous outcome in the intervention group). Using short forms will result in failed or incomplete extraction.")
        st.markdown("---")
    
    uploaded_pdfs = st.file_uploader("Upload PDF Files (No docx/html formats, Strictly 20 papers in one time)", accept_multiple_files=True)
    
    if st.button("Process Papers"):

        selected_provider = st.session_state.get('provider_name', 'OpenAI')
        
        if selected_provider == "Default":

            mode = st.session_state.app_mode
            import os
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

        st.session_state.extracted_results = []
        st.session_state.batch_file_hashes = {}

        if not uploaded_pdfs:
            st.warning("Please upload at least one PDF file.")
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
        
       
        try:
            for idx, pdf in enumerate(uploaded_pdfs[:max_papers], 1):
                gc.collect()
                
                result = None
                text = ""
                full_text_backup = ""
                title, author, year = "", "", "" 
                
                if pdf is None:
                    continue

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
          
                        update_terminal_log(f"Duplicate file detected (Hash match). Using cached result.", "INFO")
                        cached_result = st.session_state.batch_file_hashes[pdf_hash]
                        cached_result["filename"] = pdf.name
                        
                        st.session_state.extracted_results.append(cached_result)
                        
                        update_processing_stats("extractor", 1)
                        
                        papers_processed_in_batch += 1
                        
         
                        try:
                            percent = int((idx / total_pdfs) * 100)
                            status_placeholder.markdown(f"<h4 style='text-align: center; color: #4189DC;'>{percent}% Work Done... Processing <span style='color: white'>{pdf.name}</span> (Cached)</h4>", unsafe_allow_html=True)
                            progress_bar.progress(idx / total_pdfs)
                            update_terminal_log("Skipped API call. Using cached data.", "SUCCESS")
                        except:
                            pass
                        
               
                        del pdf_bytes 
                        continue
                    
       
                    text, title, author, year = extract_pdf_content(pdf_bytes)
                    
                    del pdf_bytes 

                    if not text.strip():
                        update_terminal_log(f"PDF '{pdf.name}' appears empty or unreadable.", "WARN")
                        try:
                            progress_bar.progress(idx / total_pdfs)
                        except:
                            pass
                        continue
                    
                    full_text_backup = text
                    text = preprocess_text_for_ai(text, max_tokens=MAX_INPUT_TOKENS_EXTRACTOR)

         
                    criteria_dict = {} 
                    
                    confidence = estimate_confidence(
                        text, 
                        mode="extractor", 
                        criteria_dict=criteria_dict, 
                        extracted_data=None, 
                        fields_list=fields_list
                    )
                    
       
                    raw_result = None
                    prompt = ""

                    try:
                        update_terminal_log(f"Preparing extraction fields: {', '.join(fields_list)}", "INFO")
                    except:
                        pass
                    field_descriptions = {
                        "Paper Title": "The full title of the research paper",
                        "Author": "The main author(s) of the paper",
                        "Year": "The publication year of the paper",
                        "Journal": "The journal where the paper was published",
                        "DOI": "The Digital Object Identifier of the paper",
                        "Abstract": "A brief summary of the paper's content",
                        "Keywords": "Key terms associated with the paper",
                        "Study Design": "The methodology used in the study (e.g., randomized controlled trial, cohort study)",
                        "Sample Size": "The number of participants in the study",
                        "Intervention": "The treatment or intervention being studied",
                        "Comparison": "The control or comparison group",
                        "Outcome": "The main results or findings of the study",
                        "Conclusion": "The authors' conclusion based on the findings",
                        "Funding": "Information about who funded the research",
                        "Conflicts of Interest": "Any declared conflicts of interest by the authors"
                    }
                    
                    prompt = "Extract the following information from the research paper:\n\n"
                    for field in fields_list:
                        description = field_descriptions.get(field, f"Information about {field}")
                        prompt += f"- {field}: {description}\n"
                    
                    time.sleep(1)
                    
                    prompt += f"""
**Paper Text:**
\"\"\"
{text}
\"\"\"

**CRITICAL INSTRUCTION:**
Return your response as a SINGLE valid JSON object. Do not include markdown formatting. Ensure all keys are present.
If a field is not found in the text, use the value "Not Found".
**CONFIDENCE SCORE**: Rate your confidence (0.0 to 1.0).
- 1.0 = All extracted fields are explicitly stated in the text.
- 0.8 - 0.9 = Most fields are explicit, some inferred.
- 0.5 - 0.7 = Some fields missing or ambiguous.
- < 0.5 = Data largely missing or garbled.

**JSON Format Required:**
{{
  "extracted": {{
"""
                    for field in fields_list:
                        prompt += f'    "{field}": "",\n'
                    
                    prompt = prompt.rstrip(",\n") + "\n  },\n"
                    prompt += '  "confidence": 0.0\n}'
                    prompt += "\nEnsure that JSON is valid. Use 'Not Found' for missing data.\n"
                
         
                    max_api_attempts = 3 
                    retries_per_api_attempt = 3
                    
                    for api_attempt in range(max_api_attempts):
                        if api_attempt > 0:
                            try:
                                update_terminal_log("Previous attempt failed after retries. Initiating NEW API call for this paper...", "WARN")
                            except:
                                pass
                        
                        for retry_idx in range(retries_per_api_attempt):
                            raw_result = query_llm(prompt, provider_for_call, api_key, model_name, temperature=0.1, max_tokens=MAX_OUTPUT_TOKENS)
            
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
                    del text

                
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

                    result = parse_result(raw_result, provider_for_call, api_key, model_name, mode="extractor", fields_list=fields_list, original_text=full_text_backup)
                    
                    if "extracted" not in result:
                        result["extracted"] = {}
                    
                    for field in fields_list:
                        if field not in result["extracted"]:
                            result["extracted"][field] = "Not Found"
                    
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
                                    mode="extractor", 
                                    criteria_dict=criteria_dict, 
                                    extracted_data=result.get("extracted"),
                                    fields_list=fields_list
                                )
                        else:
                            try:
                                update_terminal_log(f"Confidence missing. Using heuristic fallback.", "WARN")
                            except:
                                pass

                            confidence = estimate_confidence(
                                full_text_backup, 
                                mode="extractor", 
                                criteria_dict=criteria_dict, 
                                extracted_data=result.get("extracted"),
                                fields_list=fields_list
                            )

                        result["confidence"] = confidence
                        
                        if confidence < 0.5:
                            result["flags"] = ["low_confidence"]
                            try:
                                update_terminal_log("Flagged: Low confidence score.", "WARN")
                            except:
                                pass
                             
                        if "Paper Title" in result["extracted"]:
                            if result["extracted"]["Paper Title"] == "Not Found" or not result["extracted"]["Paper Title"]:
                                result["extracted"]["Paper Title"] = title
                        
                        for key in result["extracted"]:
                            if isinstance(result["extracted"][key], str) and len(result["extracted"][key]) > 10000:
                                result["extracted"][key] = result["extracted"][key][:10000] + "..."

                        st.session_state.extracted_results.append(result)
                        try:
                            update_terminal_log("Data extraction completed.", "SUCCESS")
                        except:
                            pass
                        try:
                            update_processing_stats("extractor", 1)
                        except:
                            pass
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
                    

        except Exception as e:
            try:
                update_terminal_log(f"CRITICAL BATCH ERROR: {str(e)}", "ERROR")
            except:
                pass
            try:
                import traceback
                update_terminal_log(f"Traceback: {traceback.format_exc()}", "ERROR")
            except:
                pass

        status_placeholder.empty()
        try:
            update_terminal_log("=== Batch processing complete ===", "SYSTEM")
            update_terminal_log(f"Processed {papers_processed_in_batch} papers in this session.", "SUCCESS")
        except:
            pass

    extracted_results = st.session_state.extracted_results
    total = len(extracted_results)
    
    with st.expander("Extraction Dashboard", expanded=False):
         st.metric("Papers Processed", total)
        
    if extracted_results:
        st.header("Extracted Data")
        df_ext = df_from_extracted_results(extracted_results)
        
        def style_extractor_df(df):
            return df.style.set_properties(**{'text-align': 'left'})
            
        styled_ext = style_extractor_df(df_ext)
        st.dataframe(styled_ext, width='stretch', height=400)

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
                "DOCX": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", to_docx(df), f"{label_prefix.lower()}_data.docx"),
                "CSV":  ("text/csv", to_csv(df), f"{label_prefix.lower()}_data.csv"),
                "XLSX": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", to_excel(df), f"{label_prefix.lower()}_data.xlsx")
            }

            for fmt, (mime, data, filename) in formats.items():
                st.download_button(
                    label=f"Download {label_prefix} as {fmt}",
                    data=data,
                    file_name=filename,
                    mime=mime
                )
        
        export_buttons(df_ext, "Extracted")
        del df_ext
    else:
        st.info("No extracted data available. Upload and process papers to see results here.")
    
    
