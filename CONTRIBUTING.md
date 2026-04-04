
# Contributing to ReviewAid

Thank you for your interest in contributing to **ReviewAid**!
This project is an open-source AI-powered tool designed to assist researchers in **full-text screening and data extraction for systematic reviews and evidence synthesis**.

Contributions help improve reliability, usability, and transparency — all critical for research tools.

---

## Ways to Contribute

You can contribute in the following ways:

* 🛠️ Fix bugs or improve existing features
* 🚀 Add new features or enhancements
* 📄 Improve documentation or examples
* 🔗 Fix broken links or UI issues
* 🧪 Improve parsing, extraction, or confidence logic
* ⚡ Optimize performance (especially batch processing / LLM calls)

---

## Before You Start

* Check existing **Issues** to avoid duplicate work
* For major changes, open an issue first to discuss your idea
* Keep changes focused and minimal

---

## Development Setup

1. Fork the repository
2. Clone your fork:

```bash
git clone https://github.com/aurumz-rgb/ReviewAid.git
cd ReviewAid
```

3. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the app:

```bash
streamlit run app.py
```

---

## Project Structure Guidelines

When contributing:

* Keep logic modular (separate UI, parsing, and AI logic)
* Maintain the **robust parsing pipeline** (fallback-safe design)
* Avoid breaking:

  * Screening workflow
  * Extraction workflow
  * Confidence scoring system

---

## Coding Standards

* Use clear, readable Python code
* Follow **PEP8** conventions
* Write meaningful variable and function names
* Add comments where logic is complex (especially parsing / AI handling)

---

## AI & API Contributions

Since ReviewAid relies on LLMs:

* Ensure compatibility with:

  * OpenAI
  * Anthropic
  * Cohere
  * DeepSeek
  * Ollama (local)

* Do not:

  * Hardcode API keys
  * Store sensitive data

* Prefer:

  * Config-driven model selection
  * Graceful fallbacks

---

## UI / Streamlit Contributions

* Keep UI simple and research-focused
* Avoid clutter — prioritize usability
* Ensure a clear workflow (Upload → Process → Output)
* Provide helpful logs or feedback to users

---

## Continuous Integration (CI) Requirement

All contributions **must pass the repository’s Python CI workflow** before they can be merged.

* Ensure your code runs without errors
* Fix linting and formatting issues
* Make sure all tests (if present) pass

### Before submitting a PR:

Run checks locally if possible:

```bash
# Example (adjust based on repo setup)
pytest
```

If your PR fails CI:

* Review the GitHub Actions logs
* Fix the reported issues
* Push updates to your branch

**Pull requests that fail CI will not be merged.**

---

## Submitting a Pull Request

1. Create a new branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Commit clearly:

```bash
git commit -m "Add: short description of change"
```

4. Push your branch:

```bash
git push origin feature/your-feature-name
```

5. Open a Pull Request

---

## Pull Request Guidelines

* Describe **what** you changed and **why**
* Link related issues (if any)
* Keep PRs small, focused, and testable

---

## Reporting Issues

If you encounter problems, open an issue and include:

* Steps to reproduce
* Expected vs actual behavior
* Logs or screenshots (if applicable)
* Environment details (OS, Python version, model used)

---

## Important Notes

* ReviewAid is an **assistive tool**, not a replacement for manual research
* Always validate outputs, especially low-confidence results
* Do not expose sensitive or private data

---

## Final Note

ReviewAid is built **by a researcher, for researchers**.
Your contributions directly improve the quality and efficiency of evidence synthesis workflows 🚀
