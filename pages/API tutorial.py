import streamlit as st
import os 
import plotly.express as px
import pandas as pd
import streamlit as st
from datetime import datetime
from cryptography.fernet import Fernet
from streamlit_lottie import st_lottie
import streamlit as st





st.set_page_config(
    page_title="ReviewAid",
    page_icon=os.path.abspath("favicon.ico"),
    layout="wide",
    initial_sidebar_state="expanded",
)
hide_streamlit_style = """
    <style>
    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}
    /* Hide footer */
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)








st.title("How to Make a Free Cohere API Key.")

st.write("""
Follow these simple steps:
""")

st.header("Step 1: Go to Cohere Website")
st.write("Visit [https://cohere.ai](https://cohere.ai) and click on **Sign In**.")
st.image("screenshots/step1.png", caption="Step 1", width=700)
st.image("screenshots/step2.png", caption="Step 2", width=700)

st.header("Step 2: Register Your Account")
st.write("Fill in your details and create an account.")


st.header("Step 3: Verify Email")
st.write("Verify your email address from the email sent by Cohere.")

st.header("Step 4: Get Your API Key")
st.write("Once logged in, navigate to your dashboard and find your API key. Follow the order of Steps.")
st.image("screenshots/step4.png", caption="Step 1", width=700)
st.image("screenshots/step5.png", caption="Step 2", width=700)
st.image("screenshots/step6.png", caption="Step 3", width=700)



st.write(
    """
    <p style="font-size: 1rem; color: #a0aec0; margin-top: 60px;">
        ⚠️ <em>It is the user's responsibility in handling their API key. The tool does not record or store user's API key.  Make sure to keep your API key safe and do not share it publicly. I do not take any responsibility for the use or misuse of the API key you obtain. 
        Please use it responsibly and comply with Cohere’s policies.</em>
    </p>
    """,
    unsafe_allow_html=True
)





st.markdown(
    f"""
    <style>
    .custom-footer-acceptance {{
        width: 100%;
        font-family: 'Times New Roman', Times, serif;
        font-size: 14px;  /* bigger text */
        color: #a0aec0;
        opacity: 0.95;
        padding: 8px 6px;
        background-color: #1f2937;
        position: fixed;
        bottom: 0;  /* stick to bottom */
        left: 0;
        text-align: center;
        z-index: 9999;
    }}
    .custom-footer-acceptance a {{
        color: #63b3ed;
        text-decoration: none;
    }}
    .custom-footer-acceptance a:hover {{
        text-decoration: underline;
    }}
    </style>

    <div class="custom-footer-acceptance">
        By Registering, you agree to comply with 
        <a href="https://cohere.com/terms-of-use" target="_blank" rel="noopener noreferrer">Cohere's Terms of Service</a> and 
        <a href="https://docs.cohere.com/docs/cohere-labs-acceptable-use-policy" target="_blank" rel="noopener noreferrer">Acceptable Use Policy</a>.
    </div>
    """,
    unsafe_allow_html=True
)