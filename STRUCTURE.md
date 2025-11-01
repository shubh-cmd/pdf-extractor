# Project Structure

This document describes the enhanced, modular file structure of the PDF Extractor project.

## 📁 Directory Structure

```
pdf_extractor/
├── main.py                      # CLI entry point
├── setup.py                     # Package configuration
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── LICENSE                      # MIT License
├── MANIFEST.in                  # Package manifest
├── pdfx                         # Executable wrapper script
├── demo_app.py                  # Demo application
│
└── extractor/                   # Main package
    ├── __init__.py              # Package initialization with exports
    │
    ├── models/                  # Data models (Pydantic)
    │   ├── __init__.py          # Model exports
    │   ├── base.py              # Base/shared models
    │   ├── construction.py      # Construction extraction models
    │   └── standard.py          # Standard extraction models
    │
    ├── extractors/              # PDF extraction engines
    │   ├── __init__.py          # Extractor exports
    │   └── pdf_text_extractor.py # PDF text & table extraction
    │
    ├── parsers/                 # Text parsing modules
    │   ├── __init__.py          # Parser exports
    │   ├── construction.py      # Construction-specific parser
    │   ├── standard.py          # Standard entity parser
    │   └── llm.py               # LLM-based parsers (GPT/Claude)
    │
    ├── services/                # Service layer (OOP orchestration)
    │   ├── __init__.py          # Service exports
    │   └── extraction_service.py # Extraction service & strategies
    │
    └── utils/                   # Utility functions
        ├── __init__.py          # Utility exports
        └── helpers.py           # Helper functions
```

## 🏗️ Architecture Layers

### 1. **Models Layer** (`extractor/models/`)
**Purpose**: Type-safe data structures and validation

- **`base.py`**: Shared models (Statistics, PageInfo, BaseExtractionResult)
- **`construction.py`**: Construction-specific models (ExtractedItem, ConstructionExtractionResult)
- **`standard.py`**: Standard extraction models (ExtractedEntities, StandardExtractionResult)

### 2. **Extractors Layer** (`extractor/extractors/`)
**Purpose**: PDF text and table extraction

- **`pdf_text_extractor.py`**: Extracts text and tables from PDFs using pdfplumber

### 3. **Parsers Layer** (`extractor/parsers/`)
**Purpose**: Parse extracted text into structured data

- **`construction.py`**: Extracts construction items, quantities, model numbers
- **`standard.py`**: Extracts general entities (emails, phones, dates)
- **`llm.py`**: LLM-based parsing (OpenAI GPT, Anthropic Claude)

### 4. **Services Layer** (`extractor/services/`)
**Purpose**: High-level orchestration using OOP patterns

- **`extraction_service.py`**: 
  - `ExtractionStrategy` (abstract base class)
  - `ConstructionExtractionStrategy` (construction mode)
  - `StandardExtractionStrategy` (standard mode)
  - `ExtractionService` (service orchestrator)
  - `ExtractionServiceFactory` (factory for creating services)

### 5. **Utils Layer** (`extractor/utils/`)
**Purpose**: Helper functions

- **`helpers.py`**: JSON operations, text combination, statistics

## 🔄 Data Flow

```
PDF File
    ↓
PDFTextExtractor (extractors/)
    ↓
Pages Data (text + tables)
    ↓
ExtractionService (services/)
    ↓
ExtractionStrategy (services/)
    ├── ConstructionExtractionStrategy
    │   └── ConstructionParser (parsers/)
    │       └── ConstructionExtractionResult (models/)
    │
    └── StandardExtractionStrategy
        └── ParserRules (parsers/)
            └── StandardExtractionResult (models/)
```

## 🎯 Benefits of This Structure

1. **Separation of Concerns**: Each layer has a clear responsibility
2. **Modularity**: Easy to add new parsers, extractors, or strategies
3. **Testability**: Each component can be tested independently
4. **Scalability**: Easy to extend with new features
5. **Maintainability**: Clear organization makes code easy to navigate
6. **Type Safety**: Models ensure data integrity
7. **OOP Principles**: Strategy pattern, factory pattern, dependency injection

## 📦 Import Examples

```python
# Import services (recommended for most use cases)
from extractor.services import ExtractionServiceFactory

# Import specific components
from extractor.extractors import PDFTextExtractor
from extractor.parsers import ConstructionParser, ParserRules
from extractor.models import (
    ConstructionExtractionResult,
    StandardExtractionResult,
    ExtractedItem
)

# Import utilities
from extractor.utils import save_json, combine_pages_text
```

## 🚀 Usage

The main entry point (`main.py`) uses the service layer:

```python
from extractor.services import ExtractionServiceFactory

# Create service using factory
service = ExtractionServiceFactory.create_construction_service()

# Extract data
result = service.extract("document.pdf")
```

This structure follows clean architecture principles and makes the codebase professional, maintainable, and scalable.

