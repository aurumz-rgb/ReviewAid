import streamlit as st
import os
import time
import json
import base64
from dotenv import load_dotenv

from utils import (
    init_analytics, update_processing_stats, display_citation_section,
    get_firebase_stats, update_terminal_log, st_lottie
)

load_dotenv()


st.set_page_config(
    page_title="ReviewAid / AI Screener & Extractor",
    page_icon=os.path.abspath("favicon.ico"),
    layout="wide",
    initial_sidebar_state="collapsed", 
)


hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide Sidebar */
    [data-testid="stSidebar"] {display: none !important;} 

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

    .terminal-container {
        background-color: #0d1117; 
        color: #c9d1d9;
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        height: 400px; 
        overflow-y: auto;
        font-size: 13px;
        line-height: 1.4;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.6);
        scroll-behavior: smooth;
    }
    
    .terminal-line {
        margin-bottom: 2px;
        padding-bottom: 1px;
        display: block;
        white-space: pre-wrap;
    }
    
    .terminal-timestamp {
        color: #8b949e;
        margin-right: 10px;
        font-weight: bold;
        min-width: 70px;
        display: inline-block;
    }
    
    .log-info { color: #58a6ff; }
    .log-success { color: #3fb950; }
    .log-warn { color: #d29922; }
    .log-error { color: #f85149; }
    .log-system { color: #a371f7; font-weight: bold;}
    .log-debug { color: #6e7681; font-style: italic; font-size: 12px; }
    
    .terminal-container::-webkit-scrollbar {
        width: 10px;
    }
    
    .terminal-container::-webkit-scrollbar-track {
        background: #0d1117;
    }
    
    .terminal-container::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 5px;
    }
    
    .terminal-container::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    
    .important-note-box {
        background-color: rgba(65, 137, 220, 0.15);
        border-left: 5px solid #e64d43;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        color: #F0F4F8;
        font-size: 1rem;
        line-height: 1.5;
    }

    .confidence-table-container {
        background-color: rgba(31, 41, 55, 0.2);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 30px;
        color: #F0F4F8;
    }

    .confidence-table-container th {
        text-align: center;
        color: #45a4f3;
        border-bottom: 2px solid #45a4f3;
    }
    
    .confidence-table-container td {
        vertical-align: top;
        text-align: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(65, 137, 220, 0.2);
    }

    @media screen and (max-width: 768px) {
        .main .block-container {
            margin-top: -10px !important;
            padding-top: 10px !important;
        }
        .terminal-container {
            height: 250px !important;
            font-size: 11px !important;
            padding: 10px !important;
        }
        .terminal-timestamp {
            min-width: 55px;
            font-size: 10px;
        }
        .disclaimer-warning {
            padding: 10px !important;
            font-size: 0.9rem !important;
        }
        .important-note-box {
            padding: 10px !important;
            font-size: 0.9rem !important;
        }
        .stTextArea, .stTextInput {
            font-size: 0.9rem !important;
        }
        .confidence-table-container {
            padding: 10px !important;
            overflow-x: auto;
        }
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
    
    @media screen and (max-width: 768px) {{
        .mode-card {{
            padding: 15px !important;
            margin: 5px 0 !important;
            max-width: 100% !important;
        }}
        .mode-title {{
            font-size: 1.2rem !important;
        }}
        .mode-description {{
            font-size: 0.9rem !important;
        }}
        .mode-selection-footer {{
            flex-direction: column !important;
            text-align: center;
            gap: 5px;
            padding: 10px !important;
        }}
        .custom-button {{
            width: 100% !important;
            text-align: center !important;
            box-sizing: border-box;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

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

if "citation_selectbox_created" not in st.session_state:
    st.session_state.citation_selectbox_created = False
if "terminal_logs" not in st.session_state:
    st.session_state.terminal_logs = []
if "batch_file_hashes" not in st.session_state:
    st.session_state.batch_file_hashes = {}
if "terminal_placeholder" not in st.session_state:
    st.session_state.terminal_placeholder = st.empty()
if "last_log_update_time" not in st.session_state:
    st.session_state.last_log_update_time = 0

st.session_state.page_load_count += 1

img_src = ""
try:
    img_path = os.path.join("assets", "RA.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_src = f"data:image/png;base64,{encoded_string}"
        del encoded_string, image_file 
    else:
        img_path_root = "RA.png"
        if os.path.exists(img_path_root):
             with open(img_path_root, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
             img_src = f"data:image/png;base64,{encoded_string}"
             del encoded_string, image_file 
except Exception:
    pass 

if img_src:
    st.markdown(
        f"""
        <img src="{img_src}" style="position: fixed; bottom: 38px; right: 5px; width: 80px; height: 80px; z-index: 10000; opacity: 0.6; pointer-events: none;">
        """, unsafe_allow_html=True
    )

init_analytics()


if 'provider_name' not in st.session_state:
    st.session_state.provider_name = "Default"
    st.session_state.api_key = ""
    st.session_state.model_name = "GLM-4.6V-Flash"

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

    @media screen and (max-width: 768px) {
        .typewriter {
            font-size: 2.2rem !important;
        }
        .subheading {
            font-size: 1rem !important;
            margin-bottom: 10px;
        }
        .lottie-container svg {
            height: 180px !important;
        }
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
    
    with st.expander("Read Full Disclaimer"):
        st.markdown("""
        <div class="disclaimer-warning">
            <h3>ReviewAid Disclaimer:</h3>
    <p>By using ReviewAid, you acknowledge and agree to following:</p>
    <ul>
        <li><strong>Researcher Responsibility:</strong> ReviewAid is an AI-assisted tool intended to support, not replace, researcher's own judgment. All screening decisions, extracted data, and interpretations generated by system must be independently verified by user. The developer is not responsible for inaccuracies, omissions, or misclassifications arising from AI-generated outputs.</li>
        <li><strong>No Guarantee of Completeness or Accuracy:</strong> While ReviewAid aims to improve efficiency during literature review and evidence synthesis process, tool does not guarantee to completeness, correctness, or reliability of its results. Users should exercise critical evaluation and cross-check all information before including it in their research.</li>
        <li><strong>Data Responsibility & Privacy:</strong> Uploaded PDFs are processed only within the session and are not stored or collected by developer. However, users remain responsible for ensuring that they have the legal and ethical right to upload and process to documents they submit.</li>
        <li><strong>Non-Liability:</strong> The developer is not liable for any direct, indirect, or consequential damages resulting from the use of this tool, including but not limited to errors in screening, extraction, data interpretation, or research outcomes.</li>
        <li><strong>Academic & Ethical Use:</strong> ReviewAid is intended solely for lawful academic and research purposes. Users must ensure compliance with all relevant institutional guidelines, copyright laws, and ethical standards.</li>
        <li><strong>AI Limitations:</strong> ReviewAid uses AI algorithms to assist with literature screening and data extraction. Outputs may contain errors, omissions, or biases, and should not be considered a substitute for expert review or professional judgment.</li>
        <li><strong>No Warranty:</strong> ReviewAid is provided "as is" without any warranty of any kind, either expressed or implied, including but not limited to accuracy, completeness, or fitness for a particular purpose.</li>
        <li><strong>Transparency & Citation:</strong> Many researchers use ReviewAid during their review process without disclosing the involvement of AI tools. Users are strongly encouraged to maintain transparency by acknowledging the use of ReviewAid in their methodology. Citation is appreciated whenever ReviewAid contributes to the research workflow, whether as a primary screener, a secondary/third-person validator, or simply as a reference tool.</li>
    </ul>
    <p>Proper attribution supports ethical research practices and helps sustain ongoing development and improvement of the tool for the academic community.</p>
        </div>
        """, unsafe_allow_html=True)
    
    agree = st.checkbox("I acknowledge the disclaimer.")
    if agree and st.button("I Agree & Continue"):
        st.session_state.disclaimer_acknowledged = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

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
    st.markdown("""
    <div class="important-note-box">
        <strong>Note:</strong> The purpose of ReviewAid is not to substitute manual screening and data extraction but to serve as an additional, independent reference that helps minimise manual errors and improve the precision and reliability of the research process. 
          <strong>Have any Errors?</strong> Please visit this <a href="https://aurumz-rgb.github.io/ReviewAid" target="_blank">Web</a> or  <a href="https://github.com/aurumz-rgb/ReviewAid/issues" target="_blank">Github Issues</a>.  
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="important-note-box">
        <strong>IMPORTANT:</strong> Please restrict each submission to a maximum of 20 articles. Submissions exceeding this limit will result in processing of only the first 20 articles, after which the process will terminate prematurely. Kindly adhere to this restriction. Please respect this limit.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='citation-section'>", unsafe_allow_html=True)
    display_citation_section()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("<div class='support-section'>", unsafe_allow_html=True)
    st.markdown("## Support")
    st.markdown("""
    <div class="support-description">
        ReviewAid is an open-source academic tool designed to streamline the literature review and evidence synthesis process. If this tool benefits your research, your support is greatly appreciated. I will be adding links to the <a href="https://github.com/aurumz-rgb/ReviewAid" target="_blank">GitHub repository</a>, please check it out to explore the source code, contribute, or support ongoing development. Here is ReviewAid's preprint paper: <a href="https://osf.io/preprints/metaarxiv/3vhmt" target="_blank">ReviewAid MetaArXiV</a>
        <br><br>
        <strong>Supported AI Models:</strong> This tool supports a wide range of AI providers including <a href="https://openai.com" target="_blank">OpenAI</a>, <a href="https://www.anthropic.com" target="_blank">Anthropic</a>, <a href="https://cohere.com" target="_blank">Cohere</a>, <a href="https://www.deepseek.com" target="_blank">Deepseek</a>, <a href="https://huggingface.co/zai-org" target="_blank">GLM (Z.ai)</a>, and local <a href="https://ollama.com/" target="_blank">Ollama</a> models. You can configure these in the Configuration section within the application modes.
    </div>
    <div class="support-description">
        I will also include my personal link to my other projects, where you can discover additional research-focused tools and resources. Check out my personal link <a href="https://aurumz-rgb.github.io" target="_blank">here</a>. If you have questions, or are interested in collaborating, feel free to reach out. I am always happy to connect with fellow researchers.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    stats = get_firebase_stats()
    st.markdown("---")
    st.markdown("## 🌟 Global Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers Screened", stats["papers_screened"])
    c2.metric("Papers Extracted", stats["papers_extracted"])

  
    
    st.markdown("""
    <div class="mode-selection-footer">
        <div>© 2025 Vihaan Sahu – Licensed under Apache 2.0</div>
        <div class="center-text"><a href="https://github.com/aurumz-rgb/ReviewAid" target="_blank">GitHub Repository</a></div>
        <div class="right-text">Open-source</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()



if st.session_state.app_mode == "screener":
    import screener
    screener.run_screener()

elif st.session_state.app_mode == "extractor":
    import extractor
    extractor.run_extractor()



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

st.markdown("""
    <div class="important-note-box">
        <strong>IMPORTANT:</strong> Please restrict each submission to a maximum of 20 articles. Submissions exceeding this limit will result in processing of only the first 20 articles, after which the process will terminate prematurely. Kindly adhere to this restriction. Please respect this limit.
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="important-note-box">
        <strong>Note:</strong> The purpose of ReviewAid is not to substitute manual screening and data extraction but to serve as an additional, independent reference that helps minimise manual errors and improve the precision and reliability of the research process. 
          <strong>Have any Errors?</strong> Please visit this <a href="https://aurumz-rgb.github.io/ReviewAid" target="_blank">Web</a> or  <a href="https://github.com/aurumz-rgb/ReviewAid/issues" target="_blank">Github Issues</a>.  
    </div>
    """, unsafe_allow_html=True)



if st.session_state.app_mode is not None:
    st.markdown("<div class='citation-section'>", unsafe_allow_html=True)
    display_citation_section()
    st.markdown("</div>", unsafe_allow_html=True)

version = "2.1.0"
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
    @media screen and (max-width: 600px) {{
        .custom-footer-container {{
            flex-direction: column;
            height: auto;
            padding: 10px;
            gap: 5px;
            text-align: center;
            font-size: 11px;
        }}
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