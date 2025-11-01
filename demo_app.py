"""
Simple demo application for PDF extraction.
"""
from extractor.pdf_text_extractor import PDFTextExtractor
from extractor.parser_rules import ParserRules
from extractor.utils import save_json, get_statistics, combine_pages_text


def demo(pdf_path: str = "sample.pdf"):
    """Run a demo extraction."""
    print("=" * 50)
    print("PDF Extractor Demo")
    print("=" * 50)
    
    # Extract text
    print(f"\n1. Extracting text from {pdf_path}...")
    extractor = PDFTextExtractor()
    pages_data = extractor.extract_text(pdf_path)
    print(f"   ✓ Extracted {len(pages_data)} pages")
    
    # Statistics
    stats = get_statistics(pages_data)
    print(f"\n2. Statistics:")
    print(f"   - Total pages: {stats['total_pages']}")
    print(f"   - Total words: {stats['total_words']}")
    print(f"   - Total characters: {stats['total_characters']}")
    
    # Entity extraction
    print(f"\n3. Extracting entities...")
    parser = ParserRules()
    full_text = combine_pages_text(pages_data)
    entities = parser.extract_entities(full_text)
    
    if entities:
        print("   ✓ Found entities:")
        for entity_type, values in entities.items():
            print(f"     - {entity_type}: {len(values)} found")
    else:
        print("   - No entities found")
    
    # Save results
    output_data = {
        'pages': pages_data,
        'statistics': stats,
        'entities': entities
    }
    save_json(output_data, 'output.json')
    print(f"\n4. Results saved to output.json")
    print("\n" + "=" * 50)


if __name__ == '__main__':
    import sys
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    demo(pdf_file)

