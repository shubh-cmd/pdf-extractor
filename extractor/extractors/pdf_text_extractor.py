"""
PDF text extraction using pdfplumber and optional OCR.
"""
# Ensure unbuffered output for real-time spinner
import sys
import os

# Force unbuffered stdout at module level (for spinner thread)
if sys.stdout.isatty():
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except:
            pass

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
            use_ocr: If True, use OCR for scanned PDFs (requires pytesseract and poppler)
        """
        self.use_ocr = use_ocr
        self._ocr_available = False
        self._stop_spinner = threading.Event()
        self._spinner_thread = None
        
        if use_ocr:
            # Check if OCR dependencies are available
            try:
                import pytesseract
                from PIL import Image
                import pdf2image
                
                # Check if poppler is installed (required by pdf2image)
                try:
                    from pdf2image import convert_from_path
                    # Try a quick test conversion (will fail if poppler not installed)
                    # We'll catch this in extract_text instead
                    self._ocr_available = True
                except Exception:
                    self._ocr_available = False
                    
            except ImportError:
                self._ocr_available = False
    
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
            if not self._ocr_available:
                # OCR was requested but dependencies not available
                if show_progress:
                    print("  ⚠️  OCR requested but dependencies missing (poppler/tesseract)", flush=True)
                    print("  ℹ️  Falling back to regular PDF extraction...", flush=True)
                    print("  💡 To enable OCR: install poppler (brew install poppler) and tesseract", flush=True)
                # Fall through to regular extraction
            else:
                try:
                    pages_data = self._extract_with_ocr(pdf_path, show_progress)
                except Exception as e:
                    # If OCR fails (e.g., poppler not found), fall back to regular extraction
                    if show_progress:
                        error_msg = str(e)
                        if "poppler" in error_msg.lower() or "pdfinfo" in error_msg.lower():
                            print(f"\r  ⚠️  OCR failed: poppler not installed", flush=True)
                            print(f"  💡 Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)", flush=True)
                        else:
                            print(f"\r  ⚠️  OCR failed: {error_msg[:50]}", flush=True)
                        print(f"  ℹ️  Falling back to regular PDF extraction...", flush=True)
                    # Fall through to regular extraction below
        
        # If OCR wasn't used or failed, use regular extraction
        if not pages_data:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                def animate_spinner(page_num, total_pages):
                    """Animate spinner while processing."""
                    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    i = 0
                    while not self._stop_spinner.is_set():
                        spinner = spinner_chars[i % len(spinner_chars)]
                        # Use print with flush=True - this works correctly with python3 -u
                        print(f"\r  {spinner} Processing page {page_num}/{total_pages}...", end="", flush=True)
                        i += 1
                        time.sleep(0.1)
                
                # Quick check if PDF is image-based (sample first page only for speed)
                auto_ocr_needed = False
                if total_pages > 0:
                    try:
                        first_page_text = pdf.pages[0].extract_text()
                        if first_page_text and len(first_page_text.strip()) < 50:
                            # Very little text - likely image-based
                            auto_ocr_needed = True
                            if show_progress:
                                print(f"  ⚠️  Detected image-based PDF - enabling OCR...", flush=True)
                    except:
                        pass
                
                # Start processing pages with spinner
                for page_num, page in enumerate(pdf.pages, start=1):
                    if show_progress:
                        # Stop any previous spinner
                        self._stop_spinner.set()
                        if self._spinner_thread and self._spinner_thread.is_alive():
                            self._spinner_thread.join(timeout=0.1)
                        
                        # Start new spinner
                        self._stop_spinner.clear()
                        self._spinner_thread = threading.Thread(
                            target=animate_spinner, 
                            args=(page_num, total_pages),
                            daemon=True
                        )
                        self._spinner_thread.start()
                        # Critical: Give spinner time to actually render first frame
                        time.sleep(0.08)
                    
                    text = page.extract_text()
                    
                    # If text is very short and we detected image-based, try OCR for this page
                    if auto_ocr_needed and (not text or len(text.strip()) < 50):
                        try:
                            import pytesseract
                            from pdf2image import convert_from_path
                            from PIL import Image
                            
                            # Convert just this page to image and OCR
                            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=300)
                            if images:
                                ocr_text = pytesseract.image_to_string(images[0], config='--psm 6')
                                if ocr_text and len(ocr_text.strip()) > len(text.strip() if text else ''):
                                    text = ocr_text
                        except:
                            # If OCR fails, continue with whatever text we have
                            pass
                    
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
                            self._spinner_thread.join(timeout=0.3)  # Give spinner thread time to finish
                        # Clear spinner line and show completion (newline to ensure visibility)
                        import sys
                        print(f"\r  ✓ Processed page {page_num}/{total_pages}        ", flush=True)
                        sys.stdout.flush()  # Force immediate flush
        
        return pages_data
    
    def _extract_with_ocr(self, pdf_path: Path, show_progress: bool = True) -> List[Dict[str, any]]:
        """Extract text using OCR for scanned PDFs."""
        import pytesseract
        from pdf2image import convert_from_path
        
        if show_progress:
            print("  Converting PDF to images...", end="", flush=True)
        
        try:
            # Higher DPI for better OCR accuracy on small text and tables
            images = convert_from_path(pdf_path, dpi=300)
        except Exception as e:
            # Catch poppler-related errors
            error_msg = str(e)
            if "poppler" in error_msg.lower() or "pdfinfo" in error_msg.lower():
                raise FileNotFoundError(
                    "Poppler not installed. Required for OCR.\n"
                    "Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)"
                )
            raise
        total_pages = len(images)
        
        if show_progress:
            print(f"\r  Running OCR on {total_pages} page(s)...", end="", flush=True)
        
        def animate_spinner_ocr(page_num, total_pages):
            """Animate spinner while processing OCR."""
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            i = 0
            while not self._stop_spinner.is_set():
                spinner = spinner_chars[i % len(spinner_chars)]
                # Use print with flush=True - this works correctly with python3 -u
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
                # Give spinner time to start displaying
                time.sleep(0.05)
            
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
                    self._spinner_thread.join(timeout=0.3)  # Give spinner thread time to finish
                import sys
                print(f"\r  ✓ OCR completed page {page_num}/{total_pages}        ", flush=True)
                sys.stdout.flush()  # Force immediate flush
        
        if show_progress:
            print(f"\r  ✓ OCR completed on {total_pages} page(s)        ", flush=True)
        
        return pages_data

