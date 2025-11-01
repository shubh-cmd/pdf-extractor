# PDF Extractor - Construction PDF Takeoff Intelligence

A specialized Python tool for extracting structured data from construction PDFs (plumbing submittals, work packages, etc.). Extracts items, quantities, model numbers, dimensions, mounting types, and page references for construction takeoff and estimating.

## 🎯 Try It Now

- **🌐 Online Demo**: [https://pdf-extractr.streamlit.app/](https://pdf-extractr.streamlit.app/) - No installation required!
- **💻 Command Line**: Install with `pip install git+https://github.com/yourusername/pdf_extractor.git` and use the `pdfx` command

## 🎯 Purpose

This tool is designed for **construction PDF takeoff**, specifically to extract structured data from:
- Plumbing submittal PDFs
- Construction work packages
- Material schedules and cut sheets
- Product specifications and diagrams

## ✨ Features

- **Construction-specific extraction**: Automatically identifies fixtures, fittings, pipes, and materials
- **Table extraction**: Parses tables and schedules using pdfplumber
- **Structured output**: Extracts:
  - Item/Fixture Types
  - Quantities
  - Model Numbers / Spec References
  - Page References
  - Dimensions
  - Mounting Types
- **LLM-enhanced parsing**: Optional GPT-4 or Claude integration for better extraction
- **Progress indicators**: Real-time progress with animated spinners
- **Standard mode**: Also supports general PDF text extraction

## 🚀 Quick Start

### Option 1: Try Online (No Installation Required) 🌐

**Use the web-based demo directly in your browser:**

👉 **[https://pdf-extractr.streamlit.app/](https://pdf-extractr.streamlit.app/)**

Upload your PDF and get results instantly - no installation needed!

### Option 2: Install Command Line Tool

Install the `pdfx` command-line tool:

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install from GitHub
pip install git+https://github.com/yourusername/pdf_extractor.git

# Extract construction data from a plumbing submittal PDF
pdfx plumbing_submittal.pdf --construction
```

**Or install directly:**
```bash
pip install git+https://github.com/yourusername/pdf_extractor.git
```

After installation, use the `pdfx` command from anywhere:
```bash
pdfx your_pdf.pdf --construction
pdfx your_pdf.pdf --standard
pdfx your_pdf.pdf --construction --llm openai
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Recommended: Using Virtual Environment

**Step 1: Create a virtual environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Step 2: Install the package**

**Option A: Install from GitHub (Recommended for users)**

```bash
pip install git+https://github.com/yourusername/pdf_extractor.git
```

**Option B: Clone and install (Recommended for development)**

```bash
git clone https://github.com/yourusername/pdf_extractor.git
cd pdf_extractor
pip install -r requirements.txt
pip install -e .
```

After installation, the `pdfx` command will be available globally (you can run `pdfx` from any directory).

### Alternative: Install Without Virtual Environment

```bash
pip install git+https://github.com/yourusername/pdf_extractor.git
```

⚠️ **Note**: Using a virtual environment is strongly recommended to avoid conflicts with other Python packages.

For OCR support (optional, for scanned PDFs):
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt-get install tesseract-ocr`
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## 📖 Usage

**Important**: Make sure your virtual environment is activated (if using one):
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate    # Windows
```

### Construction PDF Takeoff Mode

The primary use case - extract structured construction data:

```bash
# Basic construction extraction (default mode)
pdfx plumbing_submittal.pdf

# Explicit construction mode
pdfx plumbing_submittal.pdf --construction

# With custom output file
pdfx plumbing_submittal.pdf --construction -o takeoff_results.json

# With LLM enhancement (requires API key)
export OPENAI_API_KEY=your_key_here
pdfx plumbing_submittal.pdf --construction --llm openai

# Or use Claude
export ANTHROPIC_API_KEY=your_key_here
pdfx plumbing_submittal.pdf --construction --llm claude
```

### Standard Text Extraction Mode

For general PDF text extraction:

```bash
# Standard text extraction mode
pdfx document.pdf --standard

# With custom output
pdfx document.pdf --standard -o results.json
```

## 📊 Output Format

### Construction Mode Output

```json
{
  "source_pdf": "plumbing_submittal.pdf",
  "extraction_mode": "construction_takeoff",
  "total_items_found": 42,
  "items": [
    {
      "fixture_type": "pipe fitting",
      "quantity": 12,
      "model_number": "PVC-12345",
      "dimensions": "2 x 4 x 6",
      "mounting_type": "wall-hung",
      "spec_reference": "ASTM D2665",
      "page_number": 3,
      "table_number": 1,
      "row_number": 5
    }
  ],
  "summary": {
    "total_items": 42,
    "items_with_quantities": 38,
    "items_with_model_numbers": 35,
    "items_with_dimensions": 28,
    "items_with_mounting_type": 15,
    "pages_processed": 15,
    "tables_found": 8
  }
}
```

## 🛠️ Technologies Used

- **pdfplumber**: PDF text and table extraction
- **pytesseract** (optional): OCR for scanned documents
- **OpenAI GPT-4** (optional): LLM-enhanced parsing
- **Anthropic Claude** (optional): Alternative LLM parser
- **Python 3.8+**: Core language

## 🧩 How It Works

1. **PDF Parsing**: Uses pdfplumber to extract text and tables from each page
2. **Pattern Matching**: Applies regex patterns to identify:
   - Construction materials and fixtures
   - Quantities and measurements
   - Model numbers and specifications
   - Dimensions and mounting information
3. **Table Extraction**: Parses structured tables with intelligent column mapping
4. **LLM Enhancement** (optional): Uses GPT-4 or Claude to improve extraction accuracy for ambiguous content
5. **Structured Output**: Organizes extracted data into JSON format with page references

## 📁 Project Structure

```
pdf_extractor/
 ├── main.py                      # Entry point with CLI
 ├── setup.py                     # Package configuration
 ├── demo_streamlit.py            # Streamlit web demo application
 ├── sample-pages_extracted.json  # Sample output file
 ├── extractor/
 │    ├── __init__.py
 │    ├── extractors/
 │    │    └── pdf_text_extractor.py  # PDF text & table extraction
 │    ├── parsers/
 │    │    ├── construction.py       # Construction-specific parsing
 │    │    ├── standard.py           # Standard entity extraction
 │    │    └── llm.py                # LLM integration (GPT/Claude)
 │    ├── services/
 │    │    └── extraction_service.py # Extraction orchestration
 │    ├── models/
 │    │    ├── base.py              # Base Pydantic models
 │    │    ├── construction.py      # Construction models
 │    │    └── standard.py          # Standard models
 │    └── utils/
 │         └── helpers.py           # Helper functions
 ├── requirements.txt
 ├── README.md
 └── STRUCTURE.md                  # Detailed architecture docs
```

## ⚙️ Configuration

### Environment Variables for LLM

```bash
# For OpenAI
export OPENAI_API_KEY=your_openai_api_key

# For Anthropic Claude
export ANTHROPIC_API_KEY=your_anthropic_api_key
```

## 🔍 Limitations & Assumptions

- **Table Structure**: Works best with well-formed tables. Complex layouts may require manual review
- **Document Quality**: Scanned PDFs require OCR (tesseract) and may have lower accuracy
- **Language**: Currently optimized for English language construction documents
- **LLM Usage**: Optional but recommended for better accuracy on complex documents
- **Extraction Patterns**: Based on common construction terminology; may miss specialized terms

## 💡 Tips for Best Results

1. **Use construction mode** for plumbing/construction PDFs: `--construction`
2. **Enable LLM parsing** for better accuracy on complex documents: `--llm openai`
3. **Review tables** - The tool extracts structured data best from tables
4. **Check output** - Review extracted items for accuracy, especially quantities
5. **Page references** - All items include page numbers for verification

## 📝 Example Use Cases

- **Material Takeoff**: Extract quantities and model numbers for procurement
- **Cost Estimating**: Gather fixture and material specifications for pricing
- **Submittal Review**: Parse product data from submittal packages
- **Schedule Creation**: Extract items from material schedules into structured format

## 🎬 Interactive Demo

### 🌐 Online Demo (Recommended)

**Try it instantly in your browser - no installation needed:**

🔗 **[https://pdf-extractr.streamlit.app/](https://pdf-extractr.streamlit.app/)**

Features:
- ✅ **No installation required** - works directly in your browser
- ✅ **Interactive UI**: Upload PDFs and see results instantly
- ✅ **Visual Summary**: Metrics and statistics dashboard
- ✅ **Item Browser**: Search and filter extracted items
- ✅ **JSON Viewer**: View raw output
- ✅ **Download**: Export results as JSON

### 💻 Local Demo

To run the demo locally on your machine:

```bash
# Install streamlit if not already installed
pip install streamlit

# Run the demo app
streamlit run demo_streamlit.py
```

Access the local demo at `http://localhost:8501` after running the command.

## 📦 Sample Files

### Sample Output
A sample output file is included: `sample-pages_extracted.json`

This demonstrates the expected structure of extracted data from a construction PDF.

### Sample Input
For testing, you can use any construction PDF (plumbing submittal, work package, etc.). The tool works best with:
- PDFs containing tables with item lists
- Material schedules and cut sheets
- Product specifications with model numbers and quantities

**Note**: Sample PDFs are excluded from the repository (see `.gitignore`). Add your own test PDFs to test the tool.

## 🤝 Contributing

This is a prototype tool. Feel free to extend and improve:
- Add more construction-specific patterns
- Improve table extraction accuracy
- Add support for diagrams and annotations
- Enhance LLM prompts for better extraction

## 📄 License

MIT
