#!/usr/bin/env python3
"""
Main entry point for PDF extractor.
Simple tool with two parameters: input (mandatory) and output (optional).
Supports construction PDF takeoff extraction mode.
Uses OOP principles with service classes and strategy pattern.
"""
import argparse
from pathlib import Path
from extractor.services import ExtractionServiceFactory
from extractor.utils import save_json


def generate_output_filename(input_path: str) -> str:
    """
    Generate a meaningful output filename based on input filename.
    
    Args:
        input_path: Path to input PDF file
        
    Returns:
        Output filename (e.g., document.pdf -> document_extracted.json)
    """
    input_path = Path(input_path)
    base_name = input_path.stem
    return f"{base_name}_extracted.json"


def main():
    parser = argparse.ArgumentParser(
        description='Extract and parse text from PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Construction PDF takeoff (default mode - recommended for plumbing/construction PDFs)
  pdfx plumbing_submittal.pdf
  pdfx plumbing_submittal.pdf --llm openai
  pdfx plumbing_submittal.pdf -o takeoff.json
  
  # Standard text extraction (for general documents)
  pdfx document.pdf --standard
  pdfx document.pdf --standard -o results.json
  
  # Explicit construction mode (same as default)
  pdfx plumbing_submittal.pdf --construction
  
  # Or if not installed:
  ./main.py document.pdf
  python main.py document.pdf
        """
    )
    parser.add_argument('input', type=str, help='Input PDF file path (required)')
    parser.add_argument('-o', '--output', type=str, default=None, 
                        help='Output JSON file path (optional, auto-generated if not provided)')
    parser.add_argument('--standard', action='store_true',
                        help='Use standard text extraction mode (default is construction takeoff mode)')
    parser.add_argument('--construction', action='store_true',
                        help='Enable construction PDF takeoff mode (default, extracts items, quantities, model numbers, etc.)')
    parser.add_argument('--llm', type=str, choices=['openai', 'claude'], default=None,
                        help='Use LLM for enhanced extraction (requires API key in environment)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Generate output filename if not provided
    if args.output is None:
        args.output = generate_output_filename(args.input)
    
    # Default to construction mode unless --standard is specified
    use_construction_mode = not args.standard
    
    # Print processing header
    print(f"📄 Processing: {args.input}")
    mode_str = " (Construction Takeoff Mode)" if use_construction_mode else " (Standard Mode)"
    print(f"🔄 Step 1/4: Extracting text and tables from PDF{mode_str}...")
    
    # Use factory to create appropriate extraction service
    if use_construction_mode:
        service = ExtractionServiceFactory.create_construction_service(
            use_ocr=False,
            llm_type=args.llm
        )
    else:
        service = ExtractionServiceFactory.create_standard_service(use_ocr=False)
    
    # Perform extraction using service (this will show page-by-page progress)
    output_data = service.extract(args.input, show_progress=True)
    
    # Step 2 and 3 are handled inside the service/strategy
    # Just show that we're moving to final step
    
    # Save to JSON
    print("🔄 Step 4/4: Saving results...", end="", flush=True)
    save_json(output_data, args.output)
    print(f" ✓", flush=True)
    print(f"\n✅ Done! Results saved to: {args.output}")
    
    # Get summary for display
    summary = service.get_summary(output_data)
    
    # Print summary
    if use_construction_mode:
        print(f"\n📊 Extraction Summary:")
        print(f"  - Total items found: {summary.get('total_items', 0)}")
        print(f"  - Items with quantities: {summary.get('items_with_quantities', 0)}")
        print(f"  - Items with model numbers: {summary.get('items_with_model_numbers', 0)}")
        print(f"  - Tables extracted: {summary.get('tables_found', 0)}")
        print(f"  - Pages processed: {summary.get('pages_processed', 0)}")
    else:
        entities = summary.get('entities', {})
        if entities:
            print("\nExtracted entities:")
            for entity_type, values in entities.items():
                print(f"  - {entity_type}: {len(values)} found")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

