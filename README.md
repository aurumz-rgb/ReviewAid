![Banner](assets/RA_banner.png)

# ReviewAid

**ReviewAid** is an AI-powered Research article full-text Screener and Extractor designed to streamline the systematic review process. Upload research papers, automatically screen for relevance, extract key data fields, and accelerate your literature review workflow — all in one intuitive, easy-to-use web tool.


📂 **Code & Archive (Zenodo DOI):** [10.5281/zenodo.18060973](https://doi.org/10.5281/zenodo.18060973)

---

## 🚀 Features

- **AI-based full-text screening:** Quickly filter large batches of research articles based on your custom inclusion and exclusion criteria.  
- **Extraction:** Extract any part of the paper you want! 
- **Customizable data extraction:** Define exactly what data fields you want extracted, and let's AI do the heavy lifting.  
- **Bulk PDF upload & management:** Easily upload and organize hundreds of research articles in PDF format.
- **Clean, modern, and responsive UI:** Focus on your research without distractions thanks to a sleek interface built with Streamlit.  
- **Privacy-first approach:** Your uploaded documents and API keys stay private and are never stored or shared.  
- **Open-source and extensible:** Built on Python and Streamlit for easy customization and community contributions.  

- **NOTE:** 
  ReviewAid is used as a supplementary tool alongside manual screening and data extraction to minimise errors and improve research accuracy, without replacing human judgment.

---

## Important Notes

- **Performance:**  
  Depending on the number and size of PDFs uploaded and your internet connection, AI processing can take some time. Please be patient — progress indicators and termianl will keep you updated. 


- **Limitations:**  
  The web is hosted on Streamlit and hence users may face **cold starts** when the user has to wait **30 seconds** for the web to initialise. 
  As per tool usage, the developer may decide to host it on better sources to avoid such **cold starts**.

---


##  Usage

1.  **Run the Streamlit app:**

2.  **Select Mode:**
    *   **Full-text Paper Screener:** Choose this mode to screen papers based on PICO (Population, Intervention, Comparison, Outcome) criteria.
    *   **Full-text Data Extractor:** Choose this mode to extract specific fields (Author, Year, Conclusion, etc.) from research papers.

3.  **Workflow (Screener):**
    *   Enter your PICO criteria (Inclusion/Exclusion) in the input fields.
    *   Upload your PDF papers (Batch upload supported).
    *   Click "Screen Papers".
    *   Monitor the "System Terminal" for real-time logs of extraction, API calls, and processing status.
    *   View the "Screening Dashboard" for a pie chart of Included/Excluded/Maybe decisions.
    *   Download results as CSV, XLSX, or DOCX.

4.  **Workflow (Extractor):**
    *   Enter the fields you want to extract (comma-separated).
    *   Upload your PDF papers.
    *   Click "Process Papers".
    *   Monitor the "System Terminal" for logs.
    *   View extracted data in the dashboard.
    *   Download extracted data as CSV, XLSX, or DOCX.

---


## 📸 Screenshots


![User Interface](screenshots/screenshot1.png)  
*User Interface.*

![Upload PDFs](screenshots/screenshot2.png)  
*Upload pdfs to Screen & Extract.*


![Result](screenshots/screenshot4.png)  
*Extracted results (example), Can be downloaded in the available formats.*

---

## 🎯 Citation

If you use ReviewAid, please cite:

**Sahu, V. (2025). ReviewAid: AI-Driven Full-Text Screening and Data Extraction for Systematic Reviews and Evidence Synthesis (v2.0.0). Zenodo.** DOI: [10.5281/zenodo.18060973](https://doi.org/10.5281/zenodo.18060973)

---

##  License

This project is licensed under the Apache 2.0 License.

---

## 📬 Contact

Questions, feedback, or collaboration ideas? Reach out at [pteroisvolitans12@gmail.com](mailto:pteroisvolitans12@gmail.com) or open an issue on GitHub.

Contributions are always welcome!

---

*Happy reviewing!*


