import streamlit as st
import fitz  
import time
import os 
import re
import json
import json5
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from cryptography.fernet import Fernet
from fpdf import FPDF
from streamlit_lottie import st_lottie
import streamlit.components.v1 as components
import base64
import html
from zai import ZaiClient

st.set_page_config(
    page_title="ReviewAid",
    page_icon=os.path.abspath("favicon.ico"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stSidebar"] {display: none;}
    
    .main .block-container {
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        margin-top: -30px !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
    
    div[data-testid="stVerticalBlock"]:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .citation-box {
        background-color: rgba(65, 137, 220, 0.1);
        border-left: 4px solid #4189DC;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    
    .citation-box p {
        white-space: pre-line;
    }
    
    .support-links {
        display: flex;
        gap: 30px;
        margin: 20px 0;
    }
    
    .support-link-item {
        display: flex;
        flex-direction: column;
    }
    
    .support-link-item a {
        color: #4189DC;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1rem;
        transition: color 0.3s ease;
    }
    
    .support-link-item a:hover {
        color: #174D8B;
    }
    
    .support-link-item p {
        color: #d1d5db;
        margin-top: 5px;
        font-size: 0.9rem;
    }
    
    .custom-button {
        background-color: #4189DC !important;
        color: white !important;
        text-decoration: none !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
        border-radius: 5px !important;
        display: inline-block !important;
        margin: 0 !important;
        transition: background-color 0.3s ease !important;
        border: none !important;
        cursor: pointer !important;
    }
    
    .custom-button:hover {
        background-color: #174D8B !important;
    }
    
    .bold-white-link {
        color: #F0F4F8 !important;
        font-weight: bold !important;
        text-decoration: none !important;
        transition: color 0.3s ease !important;
    }
    
    .bold-white-link:hover {
        color: #45a4f3 !important;
    }
    
    .support-section {
        margin-top: 40px;
        margin-bottom: 30px;
    }
    
    .support-description {
        color: #d1d5db;
        margin-bottom: 20px;
        font-size: 1.2rem;
        line-height: 1.6;
    }
    
    .support-description a {
        color: #4189DC !important;
        text-decoration: none;
        font-weight: bold;
        transition: color 0.3s ease;
    }
    
    .support-description a:hover {
        color: #174D8B !important;
        text-decoration: underline;
    }
    
    .disclaimer-warning {
        background-color: #ccd0d9;
        color: #000000;
        border-left: 5px solid #174D8B;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    
    .disclaimer-warning h3 {
        margin-top: 0;
        color: #000000;
    }
    
    .disclaimer-warning p {
        margin-bottom: 10px;
        color: #000000;
    }
    
    .disclaimer-warning ul {
        margin-top: 10px;
        margin-bottom: 10px;
        padding-left: 20px;
    }
    
    .disclaimer-warning li {
        margin-bottom: 8px;
        color: #000000;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

color = "#4189DC"
hover_color = "#174D8B"

st.markdown(f"""
    <style>
    div.stButton > button:first-child {{
        background-color: {color} !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }}
    div.stButton > button:first-child:hover {{
        background-color: {hover_color} !important;
    }}
    
    .mode-card {{
        background-color: #1f2937;
        border-radius: 10px;
        padding: 30px;
        margin: 15px;
        width: 100%;
        max-width: 500px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    
    .mode-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }}
    
    .mode-title {{
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 15px;
        color: #F0F4F8;
    }}
    
    .mode-description {{
        color: #d1d5db;
        margin-bottom: 20px;
    }}
    
    .mode-selection-footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(8, 25, 45, 0.95);
        color: #d1d5db;
        font-size: 0.95rem;
        padding: 10px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 1000;
        backdrop-filter: blur(5px);
    }}
    
    .mode-selection-footer a {{
        color: #F0F4F8;
        text-decoration: none;
        font-weight: normal;
    }}
    
    .mode-selection-footer a:hover {{
        text-decoration: underline;
    }}
    
    .mode-selection-footer .center-text {{
        font-weight: normal;
    }}
    
    .mode-selection-footer .right-text {{
        font-weight: normal;
    }}
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def load_lottiefile(filepath: str):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

lottie_animation = load_lottiefile("animation.json")

if "included_results" not in st.session_state:
    st.session_state.included_results = []
if "excluded_results" not in st.session_state:
    st.session_state.excluded_results = []
if "maybe_results" not in st.session_state:
    st.session_state.maybe_results = []
if "extracted_results" not in st.session_state:
    st.session_state.extracted_results = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "disclaimer_acknowledged" not in st.session_state:
    st.session_state.disclaimer_acknowledged = False
if "app_mode" not in st.session_state:
    st.session_state.app_mode = None
if "page_load_count" not in st.session_state:
    st.session_state.page_load_count = 0

st.session_state.page_load_count += 1

def query_zai(prompt, api_key, temperature=0.8, max_tokens=1024):
    
    if not api_key:
        st.error("API key is missing. Please check your environment variables.")
        return None
    
    try:
        
        client = ZaiClient(api_key=api_key)
        
        
        response = client.chat.completions.create(
            model="GLM-4.5-Flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling Z.AI API: {str(e)}")
        return None

def display_citation_section():
    st.markdown("---")
    st.markdown("## Citation")

    apa_citation = (
        "Sahu, V. (2025). ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0). "
        "Zenodo. https://doi.org/10.5281/zenodo.17236600"
    )

    harvard_citation = (
        "Sahu, V., 2025. ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0). "
        "Zenodo. Available at: https://doi.org/10.5281/zenodo.17236600"
    )

    mla_citation = (
        "Sahu, Vihaan. \"ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0).\" "
        "2025, Zenodo, https://doi.org/10.5281/zenodo.17236600."
    )

    chicago_citation = (
        "Sahu, Vihaan. 2025. \"ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0).\" "
        "Zenodo. https://doi.org/10.5281/zenodo.17236600."
    )

    ieee_citation = (
        "V. Sahu, \"ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0),\" "
        "Zenodo, 2025. doi: 10.5281/zenodo.17236600."
    )

    vancouver_citation = (
        "Sahu V. ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0). "
        "Zenodo. 2025. doi:10.5281/zenodo.17236600"
    )

    ris_data = """TY  - JOUR
AU  - Sahu, V
TI  - ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0)
PY  - 2025
DO  - 10.5281/zenodo.17236600
ER  -"""

    bib_data = """@misc{Sahu2025,
  author={Sahu, V.},
  title={ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0)},
  year={2025},
  doi={10.5281/zenodo.17236600}
}"""

    citation_style = st.selectbox(
        "Select citation style",
        ["APA", "Harvard", "MLA", "Chicago", "IEEE", "Vancouver"]
    )

    if citation_style == "APA":
        citation_text = apa_citation
    elif citation_style == "Harvard":
        citation_text = harvard_citation
    elif citation_style == "MLA":
        citation_text = mla_citation
    elif citation_style == "Chicago":
        citation_text = chicago_citation
    elif citation_style == "IEEE":
        citation_text = ieee_citation
    elif citation_style == "Vancouver":
        citation_text = vancouver_citation

    escaped_citation = html.escape(citation_text)
    
    st.markdown(f'<p style="margin:0; color:#ffff; font-size:1.1rem;">A lot of Researchers use ReviewAid & do not disclose the use of A.i. in their Research. I would request Researchers to be transparent and to cite ReviewAid if they were to use it, even if just as a third person validator or just for Reference.</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="citation-box"><p style="margin:0; color: #F0F4F8;">{escaped_citation}</p></div>', unsafe_allow_html=True)

    js_citation_text = json.dumps(citation_text)
    
    st.markdown(f"""
    <div style="display:flex; gap:10px; margin-top:10px; margin-bottom:10px; position:relative;" id="button-container">
        <button id="copy-btn" class="custom-button">Copy</button>
        <a download="ReviewAid_citation.ris" href="data:application/x-research-info-systems;base64,{base64.b64encode(ris_data.encode()).decode()}" class="custom-button">RIS Format</a>
        <a download="ReviewAid_citation.bib" href="data:application/x-bibtex;base64,{base64.b64encode(bib_data.encode()).decode()}" class="custom-button">BibTeX Format</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <script>
    function copyCitation() {{
        const citationText = {js_citation_text};
        navigator.clipboard.writeText(citationText).then(() => {{
            const btn = document.getElementById('copy-btn');
            const originalText = btn.innerText;
            btn.innerText = "Copied!";
            setTimeout(() => {{ 
                btn.innerText = originalText; 
            }}, 2000);
        }}).catch(err => {{
            console.error('Failed to copy text: ', err);
        }});
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        const copyBtn = document.getElementById('copy-btn');
        if (copyBtn) {{
            copyBtn.addEventListener('click', copyCitation);
        }}
    }});
    </script>
    """, unsafe_allow_html=True)

if st.session_state.app_mode is not None:
    st.markdown("""
    <div class="return-button">
    """, unsafe_allow_html=True)
    if st.button("← Return to Mode Selection"):
        st.session_state.app_mode = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)

if lottie_animation:
    st.markdown("<div class='lottie-container' style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    st_lottie(lottie_animation, height=250, key=f"lottie_top_{st.session_state.page_load_count}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');

    .stApp {
        background-color: #0f1117;
        color: #F0F4F8;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .typewriter {
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 3.5rem;
        color: #F0F4F8;
    }

    .typewriter .typing {
        display: inline-block;
        overflow: hidden;
        border-right: .15em solid #F0F4F8;
        white-space: nowrap;
        letter-spacing: .04em;
        animation:
            typing 1s steps(11, end) forwards,
            blink-caret 1s step-end forwards;
        vertical-align: bottom;
    }

    .gold {
        color: #45a4f3;
    }

    .typewriter .dot {
        display: inline-block;
        vertical-align: bottom;
        margin-left: 2px;
        color: #F0F4F8;
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 11ch; }
    }

    @keyframes blink-caret {
        0%, 100% { border-color: transparent; }
        50% { border-color: #F0F4F8; }
    }
    </style>

    <div class="typewriter">
        <span class="typing">Review<span class="gold">Aid</span>.</span>
    </div>

    <h3 class="subheading" style='text-align: center; color: #F0F4F8; margin-top: 0; margin-bottom: 5px;'>
        An Ai based Full-text Research Article Screener & Extractor
    </h3>
    """,
    unsafe_allow_html=True
)

if not st.session_state.disclaimer_acknowledged:
    st.markdown("<div style='margin-top: 80px;'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="disclaimer-warning">
        <h3>ReviewAid Disclaimer:</h3>
<p>By using ReviewAid, you acknowledge and agree to the following:</p>
<ul>
    <li><strong>Researcher Responsibility:</strong> ReviewAid is an AI-assisted tool intended to support, not replace, the researcher's own judgment. All screening decisions, extracted data, and interpretations generated by the system must be independently verified by the user. The developer is not responsible for inaccuracies, omissions, or misclassifications arising from AI-generated outputs.</li>
    <li><strong>No Guarantee of Completeness or Accuracy:</strong> While ReviewAid aims to improve efficiency during the literature review and evidence synthesis process, the tool does not guarantee the completeness, correctness, or reliability of its results. Users should exercise critical evaluation and cross-check all information before including it in their research.</li>
    <li><strong>Data Responsibility & Privacy:</strong> Uploaded PDFs are processed only within the session and are not stored or collected by the developer. However, users remain responsible for ensuring that they have the legal and ethical right to upload and process the documents they submit.</li>
    <li><strong>Non-Liability:</strong> The developer is not liable for any direct, indirect, or consequential damages resulting from the use of this tool, including but not limited to errors in screening, extraction, data interpretation, or research outcomes.</li>
    <li><strong>Academic & Ethical Use:</strong> ReviewAid is intended solely for lawful academic and research purposes. Users must ensure compliance with all relevant institutional guidelines, copyright laws, and ethical standards.</li>
    <li><strong>AI Limitations:</strong> ReviewAid uses AI algorithms to assist with literature screening and data extraction. Outputs may contain errors, omissions, or biases, and should not be considered a substitute for expert review or professional judgment.</li>
    <li><strong>No Warranty:</strong> ReviewAid is provided "as is" without any warranty of any kind, either expressed or implied, including but not limited to accuracy, completeness, or fitness for a particular purpose.</li>
    <li><strong>Transparency & Citation:</strong> Many researchers use ReviewAid during their review process without disclosing the involvement of AI tools. Users are strongly encouraged to maintain transparency by acknowledging the use of ReviewAid in their methodology. Citation is appreciated whenever ReviewAid contributes to the research workflow, whether as a primary screener, a secondary/third-person validator, or simply as a reference tool.</li>
</ul>
<p>Proper attribution supports ethical research practices and helps sustain ongoing development and improvement of the tool for the academic community.</p>


    """, unsafe_allow_html=True)
    
    agree = st.checkbox("I have read and agree to the above disclaimer.")
    if agree and st.button("I Agree & Continue"):
        st.session_state.disclaimer_acknowledged = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# API Keys 
SCREENER_API_KEY = os.getenv("SCREENER_API_KEY")
EXTRACTOR_API_KEY = os.getenv("EXTRACTOR_API_KEY")


if st.session_state.app_mode == "screener":
    if not SCREENER_API_KEY:
        st.error("Screener API key is not set. Please set the SCREENER_API_KEY environment variable.")
elif st.session_state.app_mode == "extractor":
    if not EXTRACTOR_API_KEY:
        st.error("Extractor API key is not set. Please set the EXTRACTOR_API_KEY environment variable.")

if st.session_state.app_mode is None:
    st.markdown("<div class='mode-selection'>", unsafe_allow_html=True)
    
    st.markdown("## Select Application Mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-title">Full-text Paper Screener</div>
            <div class="mode-description">
            Screen research papers based on PICO (Population, Intervention, Comparison, Outcome) criteria.
            <ul>
                <li>Define inclusion/exclusion criteria</li>
                <li>Upload PDF papers</li>
                <li>Get AI-powered screening decisions</li>
                <li>Export results</li>
            </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Screener", key="screener_btn"):
            st.session_state.app_mode = "screener"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-title">Full-text Data Extractor</div>
            <div class="mode-description">
            Extract specific data fields from research papers.
            <ul>
                <li>Define fields to extract</li>
                <li>Upload PDF papers</li>
                <li>Get AI-powered data extraction</li>
                <li>Export results</li>
            </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Extractor", key="extractor_btn"):
            st.session_state.app_mode = "extractor"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='citation-section'>", unsafe_allow_html=True)
    display_citation_section()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("<div class='support-section'>", unsafe_allow_html=True)
    st.markdown("## Support")
    st.markdown("""
    <div class="support-description">
        ReviewAid is an open-source academic tool designed to streamline the literature review and evidence synthesis process. If this tool benefits your research, your support is greatly appreciated. I will be adding links to the <a href="https://github.com/aurumz-rgb/ReviewAid" target="_blank">GitHub repository</a> — please check it out to explore the source code, contribute, or support ongoing development.
    </div>
    <div class="support-description">
        I will also include my personal link to my other projects, where you can discover additional research-focused tools and resources. Check out my personal link <a href="https://aurumz-rgb.github.io" target="_blank">here</a>. If you have questions, or are interested in collaborating, feel free to reach out. I am always happy to connect with fellow researchers.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="mode-selection-footer">
        <div>© 2025 Vihaan Sahu – Licensed under Apache 2.0</div>
        <div class="center-text"><a href="https://github.com/aurumz-rgb/ReviewAid" target="_blank">GitHub Repository</a></div>
        <div class="right-text">Open-source</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join(page.get_text() for page in doc)

def extract_pdf_metadata(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    metadata = doc.metadata
    title = metadata.get('title', '')
    author = metadata.get('author', '')
    
    
    year = ''
    if not year:
        first_page_text = doc[0].get_text()
        year_match = re.search(r'\b(19|20)\d{2}\b', first_page_text)
        if year_match:
            year = year_match.group()
    
   
    if not year and metadata.get('creationDate'):
        creation_date = metadata['creationDate']
        year_match = re.search(r'\b(19|20)\d{2}\b', creation_date)
        if year_match:
            year = year_match.group()
    
    return title, author, year

def preprocess_text_for_ai(text, max_tokens=1024):
    text = " ".join(text.split())
    return text[:max_tokens * 4]  

def extract_json_substring(text):
   
    text = re.sub(r'```json\n?', '', text)
    text = re.sub(r'\n?```', '', text)
    
   
    start = text.find("{")
    end = text.rfind("}")
    
    if start == -1 or end == -1 or end < start:
        return text
    
    return text[start:end+1]

def repair_json_via_ai(broken_json_str, api_key):
    fix_prompt = f"""
The following JSON output is invalid or malformed. Please fix it and return ONLY valid JSON, no extra text:

{broken_json_str}
"""
    fixed_raw = query_zai(fix_prompt, api_key)
    return fixed_raw

def parse_result(raw_result, api_key, mode="screener", fields_list=None):
   
    if not raw_result or not raw_result.strip():
        if mode == "screener":
            return {
                "status": "Error",
                "reason": "Empty response from AI",
            }
        else:
            result = {"extracted": {}}
            if fields_list:
                for field in fields_list:
                    result["extracted"][field] = None
            return result
    
    try:
        cleaned = extract_json_substring(raw_result)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("⚠️ JSON parsing failed on cleaned string. Trying json5 parser...")

        try:
            return json5.loads(cleaned)
        except Exception as e:
            print(f"⚠️ json5 parser failed: {e}. Attempting manual repair...")

            repaired = cleaned.strip()

            
            repaired = re.sub(r'^[^{]*', '', repaired)
            repaired = re.sub(r'[^}]*$', '', repaired)

            if not repaired.startswith("{"):
                repaired = "{" + repaired
            if not repaired.endswith("}"):
                repaired += "}"

           
            repaired = re.sub(r'(\s*)([a-zA-Z0-9_]+):', r'\1"\2":', repaired)

            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                print("⚠️ Manual repair failed. Trying AI fix retry...")

                fixed_raw = repair_json_via_ai(raw_result, api_key)
                if not fixed_raw:
                    print("⚠️ AI fix returned empty response")
                else:
                    fixed_cleaned = extract_json_substring(fixed_raw)

                    try:
                        return json.loads(fixed_cleaned)
                    except json.JSONDecodeError:
                        print("⚠️ AI fix retry failed. Using fallback response.")
                
               
                if mode == "screener":
                    return {
                        "status": "Error",
                        "reason": "Invalid or unparseable JSON response after retries.",
                    }
                else:
                    result = {"extracted": {}}
                    if fields_list:
                        for field in fields_list:
                           
                            pattern = rf'"{field}"\s*:\s*"([^"]*)"'
                            match = re.search(pattern, raw_result, re.IGNORECASE)
                            if match:
                                result["extracted"][field] = match.group(1).strip()
                            else:
                              
                                simple_pattern = rf'{field}[:\s]+(.*?)(?=\n|"|\}})'
                                simple_match = re.search(simple_pattern, raw_result, re.IGNORECASE | re.DOTALL)
                                if simple_match:
                                    result["extracted"][field] = simple_match.group(1).strip()
                                else:
                                    result["extracted"][field] = None
                    return result
    
def estimate_confidence(text):
    if not text or len(text.strip()) < 30:
        return 0.2
    if "randomized" in text.lower():
        return 0.9
    return 0.6

def df_from_results(results):
    rows = []
    for r in results:
        row = {
            "Filename": r.get("filename", ""),
            "Title": r.get("title", ""),
            "Author": r.get("author", ""),
            "Year": r.get("year", ""),
            "Status": r.get("status", "").capitalize(),
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
    return pd.DataFrame(rows)

def to_docx(df):
    from docx import Document
    from docx.shared import Inches
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import io
    doc = Document()
    doc.add_heading('Exported Papers', 0)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr_cells[i].text = str(col)
        hdr_cells[i].width = Inches(2)
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            para = row_cells[i].paragraphs[0]
            para.add_run(str(val))
            tc = row_cells[i]._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.append(OxmlElement('w:vAlign'))
            tcPr[-1].set(qn('w:val'), 'top')
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def to_pdf(df):
    from fpdf import FPDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    col_width = 280 / len(df.columns)
    for col in df.columns:
        pdf.multi_cell(col_width, 6, str(col), border=1, align='C')
    pdf.ln(6)
    for _, row in df.iterrows():
        for val in row:
            pdf.multi_cell(col_width, 6, str(val), border=1)
        pdf.ln(6)
    return pdf.output(dest='S').encode('latin1')

def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def to_excel(df):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    buffer.seek(0)
    return buffer.getvalue()

def find_exclusion_matches(text, exclusion_lists):
    matches = []
    for criteria in exclusion_lists:
        criteria = criteria.strip()
        if criteria and criteria.lower() in text.lower():
            matches.append(criteria)
    return matches

if st.session_state.app_mode == "screener":
    st.markdown("## Full-text Paper Screener")
    
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

    uploaded_pdfs = st.file_uploader("Upload PDF Files", accept_multiple_files=True)

elif st.session_state.app_mode == "extractor":
    st.markdown("## Full-text Data Extractor")
    
    fields = st.text_input("Fields to Extract (comma-separated)", placeholder="e.g. Author, Year, Study Design, Sample Size, Conclusion")
    fields_list = [f.strip() for f in fields.split(",") if f.strip()]
    
   
    if "Paper Title" not in fields_list:
        fields_list.insert(0, "Paper Title")
    
   
    if len(fields_list) == 1 and fields_list[0] == "Paper Title":
        st.info("Only Paper Title will be extracted. Add more fields to extract additional information.")
    
    uploaded_pdfs = st.file_uploader("Upload PDF Files", accept_multiple_files=True)
    
    population_inclusion = ""
    population_exclusion = ""
    intervention_inclusion = ""
    intervention_exclusion = ""
    comparison_inclusion = ""
    comparison_exclusion = ""
    outcome_criteria = ""

if st.button("Process Papers" if st.session_state.app_mode == "extractor" else "Screen Papers"):

    if "unique_users" not in st.session_state:
       st.session_state.unique_users = set()
    if "user_api_keys" not in st.session_state:
       st.session_state.user_api_keys = set()
    if "papers_screened" not in st.session_state:
       st.session_state.papers_screened = 0

    st.session_state.papers_screened += min(len(uploaded_pdfs), 20)   

    st.session_state.unique_users.add("admin")

    if not uploaded_pdfs:
        st.warning("Please upload at least one PDF file.")
        st.stop()
    
    if st.session_state.app_mode == "screener" and not any([
        population_inclusion.strip(), population_exclusion.strip(),
        intervention_inclusion.strip(), intervention_exclusion.strip(),
        comparison_inclusion.strip(), comparison_exclusion.strip(),
        outcome_criteria.strip()
    ]):
        st.warning("Please enter at least one inclusion or exclusion criterion.")
        st.stop()


    if st.session_state.app_mode == "screener":
        if not SCREENER_API_KEY:
            st.error("Screener API key is not set. Please set the SCREENER_API_KEY environment variable.")
            st.stop()
        api_key = SCREENER_API_KEY
    else:
        if not EXTRACTOR_API_KEY:
            st.error("Extractor API key is not set. Please set the EXTRACTOR_API_KEY environment variable.")
            st.stop()
        api_key = EXTRACTOR_API_KEY

    if st.session_state.app_mode == "screener":
        st.session_state.included_results, st.session_state.excluded_results, st.session_state.maybe_results = [], [], []
    else:
        st.session_state.extracted_results = []

    max_papers = 20
    total_pdfs = min(len(uploaded_pdfs), max_papers)
    progress_bar = st.progress(0)

    for idx, pdf in enumerate(uploaded_pdfs[:max_papers], 1):
        st.info(f"Processing: {pdf.name}")
        try:
            pdf.seek(0)
            text = extract_text_from_pdf(pdf)

            if not text.strip():
                st.warning(f"PDF '{pdf.name}' appears empty or unreadable. Skipping.")
                progress_bar.progress(idx / total_pdfs)
                continue

            text = preprocess_text_for_ai(text, max_tokens=1024)
            confidence = estimate_confidence(text)

            if st.session_state.app_mode == "screener":
             
                pdf.seek(0)
                title, author, year = extract_pdf_metadata(pdf)
                
                all_exclusions = []
                for block in [population_exclusion, intervention_exclusion, comparison_exclusion]:
                    if block.strip():
                        all_exclusions.extend([c.strip() for c in block.split(",") if c.strip()])

                matches = find_exclusion_matches(text, all_exclusions)

                if len(matches) >= 1:
                    exclusion_reason = (
                        f"Auto-excluded because {len(matches)} exclusion criteria matched: {', '.join(matches)}"
                    )
                    result = {
                        "filename": pdf.name,
                        "status": "Exclude",
                        "reason": exclusion_reason,
                        "confidence": confidence,
                        "title": title,
                        "author": author,
                        "year": year
                    }
                    st.session_state.excluded_results.append(result)
                    st.warning(f"Auto-excluded {pdf.name}: {len(matches)} exclusion criteria matched")
                    progress_bar.progress(idx / total_pdfs)
                    continue

                prompt = f"""

**Population**
Inclusion: {population_inclusion}
Exclusion: {population_exclusion}

**Intervention**
Inclusion: {intervention_inclusion}
Exclusion: {intervention_exclusion}

**Comparison**
Inclusion: {comparison_inclusion}
Exclusion: {comparison_exclusion}

**Outcomes (if relevant)**: {outcome_criteria}

Paper text:
\"\"\"
{text}
\"\"\"

Based on the criteria above, classify this paper as "Include", "Exclude", or "Maybe".
Provide a detailed reason for your classification.

Also extract the following information:
- Paper Title: The full title of the paper
- Main Author: The first author or corresponding author
- Publication Year: The year the paper was published

Return exactly one valid JSON object with this format, no extra text or comments:

{{
  "status": "Include",
  "reason": "Detailed classification reason.",
  "title": "Full paper title",
  "author": "Main author name",
  "year": "2023"
}}
"""
            else:
               
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
                
                prompt += f"""
Paper text:
\"\"\"
{text}
\"\"\"

Return your response as a valid JSON object with this exact structure:
{{
  "extracted": {{
"""

                
                for field in fields_list:
                    prompt += f'    "{field}": "",\n'
                
               
                prompt = prompt.rstrip(",\n") + "\n  }\n}"
                
               
                prompt += """

IMPORTANT: 
1. Return ONLY the JSON object with no additional text, explanations, or formatting.
2. Fill in the extracted information for each field in the quotes.
3. If information for a field is not found in the paper, leave it as an empty string ("").
4. Ensure the JSON is valid and properly formatted.
"""
            
            with st.spinner(f"Analysing '{pdf.name}' using AI..."):
              
                if st.session_state.app_mode == "extractor":
                    raw_result = query_zai(prompt, api_key, temperature=0.3, max_tokens=1024)
                else:
                    raw_result = query_zai(prompt, api_key)

            if raw_result is None:
                st.error(f"Failed to analyse using AI for {pdf.name}")
                progress_bar.progress(idx / total_pdfs)
                continue

           
            if st.session_state.app_mode == "screener":
                result = parse_result(raw_result, api_key, mode="screener")
            else:
                result = parse_result(raw_result, api_key, mode="extractor", fields_list=fields_list)
                
              
                if "extracted" not in result:
                    result["extracted"] = {}
                
               
                for field in fields_list:
                    if field not in result["extracted"]:
                        result["extracted"][field] = None

            result["filename"] = pdf.name
            result["confidence"] = confidence
            if confidence < 0.5:
                result["flags"] = ["low_confidence"]

         
            if st.session_state.app_mode == "screener":
                
                if "title" not in result or not result["title"]:
                    result["title"] = title
                if "author" not in result or not result["author"]:
                    result["author"] = author
                if "year" not in result or not result["year"]:
                    result["year"] = year

            if st.session_state.app_mode == "screener":
                status = result.get("status", "").strip().lower()
                if status not in {"include", "exclude", "maybe"}:
                     status = "exclude"
               
                if status == "include":
                    st.session_state.included_results.append(result)
                elif status == "exclude":
                    st.session_state.excluded_results.append(result)
                elif status == "maybe":
                    st.session_state.maybe_results.append(result)
                else:
                    st.session_state.excluded_results.append(result)

                st.success(f"Processed: {pdf.name} — {status.capitalize()}")
            else:
                st.session_state.extracted_results.append(result)
                st.success(f"Processed: {pdf.name}")

        except Exception as e:
            st.error(f"Error processing {pdf.name}: {str(e)}")

        progress_bar.progress(idx / total_pdfs)
        time.sleep(0.5)

    st.info("All files processed!")

if st.session_state.app_mode == "screener":
    included = len(st.session_state.included_results)
    excluded = len(st.session_state.excluded_results)
    maybe = len(st.session_state.maybe_results)
    total = included + excluded + maybe

    session_duration = time.time() - st.session_state.start_time
    avg_speed = session_duration / total if total > 0 else 0

    with st.expander("Screening Dashboard", expanded=True):
         st.metric("Papers Screened", total)

         fig = px.pie(
            names=["Included", "Excluded", "Maybe"],
            values=[included, excluded, maybe],
            title="Screening Decisions"
        )
         st.plotly_chart(fig, use_container_width=True)

    included_results = st.session_state.included_results
    excluded_results = st.session_state.excluded_results
    maybe_results = st.session_state.maybe_results 

    if included_results:
        st.header("Included Papers")
        df_inc = df_from_results(included_results)
        st.dataframe(df_inc)
    else:
        st.info("No Included papers found.")

    if excluded_results:
        st.header("Excluded Papers")
        df_exc = df_from_results(excluded_results)
        st.dataframe(df_exc)
    else:
        st.info("No Excluded papers found.")

    if maybe_results:
        st.header("Maybe Papers")
        df_maybe = df_from_results(maybe_results)
        st.dataframe(df_maybe)
    else:
        st.info("No Maybe papers found.")

    if included_results or excluded_results or maybe_results:
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

        if excluded_results:
            st.subheader("Excluded Papers")
            df_exc = df_from_results(excluded_results)
            export_buttons(df_exc, "Excluded")

        if maybe_results:
            st.subheader("Maybe Papers")
            df_maybe = df_from_results(maybe_results)
            export_buttons(df_maybe, "Maybe")

else:
    extracted_results = st.session_state.extracted_results
    total = len(extracted_results)
    
    with st.expander("Extraction Dashboard", expanded=True):
         st.metric("Papers Processed", total)

    if extracted_results:
        st.header("Extracted Data")
        df_ext = df_from_extracted_results(extracted_results)
        st.dataframe(df_ext)
        
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
    else:
        st.info("No extracted data available. Upload and process papers to see results here.")

st.markdown(
    """
    <style>
        .github-link {
            display: inline-block;
            color: #4189DC;
            
            font-size: 16px;
            text-decoration: underline;
            cursor: pointer;
            transition: color 0.3s ease;
        }
        .github-link:hover {
            color: #174D8B;
        }
    </style>
   
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.app_mode is not None:
    st.markdown("<div class='citation-section'>", unsafe_allow_html=True)
    display_citation_section()
    st.markdown("</div>", unsafe_allow_html=True)

version = "2.0.0"
try:
    current_file = __file__
    last_modified_timestamp = os.path.getmtime(current_file)
    last_updated = datetime.fromtimestamp(last_modified_timestamp).strftime("%Y-%m-%d %H:%M:%S")
except Exception:
    last_updated = "Unknown"

st.markdown(
    f"""
    <style>
    .custom-footer-container {{
        width: 100%;
        font-family: 'Times New Roman', Times, serif;
        font-size: 13.5px;
        color: #F0F4F8;
        opacity: 0.9;
        padding: 8px 20px;
        position: fixed;
        bottom: 0;
        left: 0;
        background-color: rgba(31, 41, 55, 1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 9999;
        backdrop-filter: blur(5px);
    }}
    </style>

    <div class="custom-footer-container">
        <div style="white-space: nowrap; letter-spacing: 1px;">
            Made with 💙 by its Creator.
        </div>
        <div style="white-space: nowrap; letter-spacing: 1px;">
            Version {version}  
        </div>
    </div>
    """,
    unsafe_allow_html=True
)