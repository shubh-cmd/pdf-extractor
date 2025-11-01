# Quick Start Guide

## For Reviewers / Demo

### Option 1: Streamlit Web Demo (Recommended)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Run Streamlit demo
streamlit run demo_streamlit.py
```

Open `http://localhost:8501` in your browser and upload a PDF!

### Option 2: Command Line Interface

```bash
# 1. Setup (same as above)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. Run extraction
pdfx your_pdf.pdf --construction

# With LLM enhancement (requires API key)
export OPENAI_API_KEY=your_key
pdfx your_pdf.pdf --construction --llm openai
```

## Project Meets All Deliverables ✅

1. ✅ **Source Code** - Complete, organized with OOP principles
2. ✅ **Sample Output** - `sample-pages_extracted.json`
3. ✅ **README** - Includes how it works, technologies, limitations
4. ✅ **Working Demo** - Streamlit web application

See `DELIVERABLES_CHECKLIST.md` for detailed verification.
