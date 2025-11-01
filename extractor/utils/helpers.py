"""
Utility functions and helpers for PDF extraction.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


def save_json(data: Dict[str, Any], output_path: str | Path) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        output_path: Path to output JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(input_path: str | Path) -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Args:
        input_path: Path to input JSON file
        
    Returns:
        Loaded data dictionary
    """
    input_path = Path(input_path)
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_page_reference(page_num: int, total_pages: int) -> str:
    """
    Format page reference string.
    
    Args:
        page_num: Page number (1-indexed)
        total_pages: Total number of pages
        
    Returns:
        Formatted page reference string
    """
    return f"Page {page_num} of {total_pages}"


def combine_pages_text(pages_data: List[Dict[str, Any]]) -> str:
    """
    Combine text from multiple pages.
    
    Args:
        pages_data: List of page dictionaries with 'text' key
        
    Returns:
        Combined text from all pages
    """
    texts = [page.get('text', '') for page in pages_data]
    return '\n\n'.join(texts)


def get_statistics(pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for extracted pages.
    
    Args:
        pages_data: List of page dictionaries
        
    Returns:
        Dictionary with statistics
    """
    total_chars = sum(len(page.get('text', '')) for page in pages_data)
    total_words = sum(len(page.get('text', '').split()) for page in pages_data)
    
    return {
        'total_pages': len(pages_data),
        'total_characters': total_chars,
        'total_words': total_words,
        'avg_chars_per_page': total_chars / len(pages_data) if pages_data else 0,
        'avg_words_per_page': total_words / len(pages_data) if pages_data else 0,
    }


def normalize_table_cells(tables: Optional[List[List[List[Any]]]]) -> Optional[List[List[List[Optional[str]]]]]:
    """
    Normalize table cell values to Optional[str] format.
    Converts None to empty string, other types to string.
    
    Args:
        tables: Raw table data from PDF extractor
        
    Returns:
        Normalized tables with Optional[str] cells
    """
    if tables is None:
        return None
    
    normalized = []
    for table in tables:
        normalized_table = []
        for row in table:
            normalized_row = []
            for cell in row:
                if cell is None:
                    normalized_row.append(None)
                elif isinstance(cell, str):
                    normalized_row.append(cell)
                else:
                    normalized_row.append(str(cell))
            normalized_table.append(normalized_row)
        normalized.append(normalized_table)
    
    return normalized

