"""
PDF text extraction using pdfplumber and optional OCR.
"""
import pdfplumber
import time
import threading
from typing import List, Dict, Optional
from pathlib import Path


class PDFTextExtractor:
    """Extract text from PDF files using pdfplumber or OCR."""
    
    def __init__(self, use_ocr: bool = False):
        """
        Initialize the PDF extractor.
        
        Args:
            use_ocr: If True, use OCR for scanned PDFs (requires pytesseract)
        """
        self.use_ocr = use_ocr
        self._stop_spinner = threading.Event()
        self._spinner_thread = None
        if use_ocr:
            try:
                import pytesseract
                from PIL import Image
                import pdf2image
            except ImportError:
                raise ImportError(
                    "OCR requires pytesseract, Pillow, and pdf2image. "
                    "Install with: pip install pytesseract Pillow pdf2image"
                )
    
    def extract_text(self, pdf_path: str | Path, show_progress: bool = True) -> List[Dict[str, any]]:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            show_progress: If True, display progress messages
            
        Returns:
            List of page dictionaries with 'page_num' and 'text' keys
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pages_data = []
        
        if self.use_ocr:
            pages_data = self._extract_with_ocr(pdf_path, show_progress)
        else:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                # Don't print here - progress will be shown per page
                
                def animate_spinner(page_num, total_pages):
                    """Animate spinner while processing."""
                    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    i = 0
                    while not self._stop_spinner.is_set():
                        spinner = spinner_chars[i % len(spinner_chars)]
                        print(f"\r  {spinner} Processing page {page_num}/{total_pages}...", end="", flush=True)
                        i += 1
                        time.sleep(0.1)
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    if show_progress:
                        self._stop_spinner.clear()
                        self._spinner_thread = threading.Thread(
                            target=animate_spinner, 
                            args=(page_num, total_pages),
                            daemon=True
                        )
                        self._spinner_thread.start()
                    
                    text = page.extract_text()
                    
                    # Extract tables if available (OPTIMIZED: only when needed)
                    # Table extraction is VERY slow (1-2 min per page), so we skip it unless needed
                    tables = []
                    try:
                        # Quick heuristic: only extract tables if page has clear table indicators
                        # This saves 1-2 minutes per page on most pages
                        has_table_indicators = False
                        
                        if text:
                            # Strong indicators: tabs (most reliable)
                            if '\t' in text:
                                has_table_indicators = True
                            # Check for table border characters
                            elif text.count('|') > 15 or text.count('│') > 8:
                                has_table_indicators = True
                        
                        # Only run expensive table extraction if we have strong indicators
                        if has_table_indicators:
                            # Use fastest possible settings to minimize time
                            page_tables = page.extract_tables(table_settings={
                                "vertical_strategy": "lines_strict",  # Fastest - only existing lines
                                "horizontal_strategy": "lines_strict",
                                "explicit_vertical_lines": [],  # Critical: don't search for lines
                                "explicit_horizontal_lines": [],
                                "snap_tolerance": 5,  # Higher = faster (less precise)
                                "join_tolerance": 5,
                                "edge_tolerance": 5
                            })
                            if page_tables:
                                tables = page_tables
                    except Exception as e:
                        # If table extraction fails or times out, continue without tables
                        # Don't let table extraction block the entire process
                        pass
                    
                    pages_data.append({
                        'page_num': page_num,
                        'text': text or '',
                        'width': page.width,
                        'height': page.height,
                        'tables': tables
                    })
                    
                    if show_progress:
                        self._stop_spinner.set()
                        if self._spinner_thread:
                            self._spinner_thread.join(timeout=0.2)
                        # Clear spinner line and show completion
                        print(f"\r  ✓ Processed page {page_num}/{total_pages}        ", flush=True)
        
        return pages_data
    
    def _extract_with_ocr(self, pdf_path: Path, show_progress: bool = True) -> List[Dict[str, any]]:
        """Extract text using OCR for scanned PDFs."""
        import pytesseract
        from pdf2image import convert_from_path
        
        if show_progress:
            print("  Converting PDF to images...", end="", flush=True)
        images = convert_from_path(pdf_path)
        total_pages = len(images)
        
        if show_progress:
            print(f"\r  Running OCR on {total_pages} page(s)...", end="", flush=True)
        
        def animate_spinner_ocr(page_num, total_pages):
            """Animate spinner while processing OCR."""
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            i = 0
            while not self._stop_spinner.is_set():
                spinner = spinner_chars[i % len(spinner_chars)]
                print(f"\r  {spinner} Running OCR on page {page_num}/{total_pages}...", end="", flush=True)
                i += 1
                time.sleep(0.1)
        
        pages_data = []
        for page_num, image in enumerate(images, start=1):
            if show_progress:
                self._stop_spinner.clear()
                self._spinner_thread = threading.Thread(
                    target=animate_spinner_ocr,
                    args=(page_num, total_pages),
                    daemon=True
                )
                self._spinner_thread.start()
            
            text = pytesseract.image_to_string(image)
            pages_data.append({
                'page_num': page_num,
                'text': text,
                'width': image.width,
                'height': image.height
            })
            
            if show_progress:
                self._stop_spinner.set()
                if self._spinner_thread:
                    self._spinner_thread.join(timeout=0.2)
                print(f"\r  ✓ OCR completed page {page_num}/{total_pages}...", end="", flush=True)
        
        if show_progress:
            print(f"\r  ✓ OCR completed on {total_pages} page(s)        ", flush=True)
        
        return pages_data

