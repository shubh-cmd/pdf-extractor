"""
PDF Extractor Package
=====================

A flexible Python tool for extracting and parsing text from PDF files,
with specialized support for construction PDF takeoff.

Main Components:
- extractors: PDF text and table extraction
- parsers: Text parsing and entity extraction
- models: Data models for type safety
- services: High-level extraction orchestration
- utils: Helper functions
"""

__version__ = "1.0.0"

# Convenience imports for common use cases
from extractor.extractors import PDFTextExtractor
from extractor.parsers import ConstructionParser, ParserRules
from extractor.services import ExtractionServiceFactory

__all__ = [
    'PDFTextExtractor',
    'ConstructionParser',
    'ParserRules',
    'ExtractionServiceFactory',
]

