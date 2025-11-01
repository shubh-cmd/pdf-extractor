"""
Streamlit Demo Application for PDF Extractor

Interactive web UI for demonstrating PDF extraction capabilities.
Run with: streamlit run demo_streamlit.py
"""
import streamlit as st
import json
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extractor.services.extraction_service import ExtractionServiceFactory
from extractor.utils.helpers import save_json


def main():
    st.set_page_config(
        page_title="PDF Extractor - Construction PDF Takeoff Intelligence",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 PDF Extractor - Construction PDF Takeoff Intelligence")
    st.markdown("Extract structured data from construction PDFs (plumbing submittals, work packages, etc.)")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        extraction_mode = st.radio(
            "Extraction Mode",
            ["Construction Takeoff (Default)", "Standard Text Extraction"],
            help="Construction mode extracts items, quantities, model numbers. Standard mode extracts general entities."
        )
        
        use_construction = extraction_mode == "Construction Takeoff (Default)"
        
        # LLM configuration
        st.subheader("🤖 LLM Enhancement (Optional)")
        use_llm = st.checkbox("Enable LLM Enhancement", help="Requires API key in environment variables")
        
        if use_llm:
            llm_type = st.selectbox(
                "LLM Provider",
                ["openai", "claude"],
                help="Choose OpenAI GPT or Anthropic Claude"
            )
            
            # Check for API keys
            if llm_type == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    st.warning("⚠️ OPENAI_API_KEY not found in environment")
                    st.info("Set it with: `export OPENAI_API_KEY=your_key`")
            else:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    st.warning("⚠️ ANTHROPIC_API_KEY not found in environment")
                    st.info("Set it with: `export ANTHROPIC_API_KEY=your_key`")
        else:
            llm_type = None
    
    # Main content area
    uploaded_file = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
        help="Upload a construction PDF (plumbing submittal, work package, etc.)"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_pdf_path = temp_dir / uploaded_file.name
        
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        
        # Extract button
        if st.button("🚀 Extract Data", type="primary"):
            with st.spinner("Processing PDF..."):
                try:
                    # Create extraction service
                    if use_construction:
                        service = ExtractionServiceFactory.create_construction_service(
                            use_ocr=False,
                            llm_type=llm_type if use_llm else None
                        )
                    else:
                        service = ExtractionServiceFactory.create_standard_service(use_ocr=False)
                    
                    # Perform extraction
                    result = service.extract(str(temp_pdf_path), show_progress=False)
                    
                    # Store in session state
                    st.session_state['extraction_result'] = result
                    st.session_state['pdf_name'] = uploaded_file.name
                    
                    st.success("✅ Extraction complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error during extraction: {str(e)}")
                    st.exception(e)
        
        # Display results if available
        if 'extraction_result' in st.session_state:
            result = st.session_state['extraction_result']
            pdf_name = st.session_state['pdf_name']
            
            st.header("📊 Extraction Results")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔍 Items/Entities", "📑 Raw JSON", "💾 Download"])
            
            with tab1:
                st.subheader("Extraction Summary")
                
                if result.get('extraction_mode') == 'construction_takeoff':
                    summary = result.get('summary', {})
                    stats = result.get('statistics', {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Items", summary.get('total_items', 0))
                    with col2:
                        st.metric("Items w/ Quantities", summary.get('items_with_quantities', 0))
                    with col3:
                        st.metric("Items w/ Model Numbers", summary.get('items_with_model_numbers', 0))
                    with col4:
                        st.metric("Pages Processed", summary.get('pages_processed', 0))
                    
                    st.markdown("---")
                    st.subheader("Document Statistics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Pages", stats.get('total_pages', 0))
                        st.metric("Total Words", stats.get('total_words', 0))
                    with col2:
                        st.metric("Total Characters", stats.get('total_characters', 0))
                        st.metric("Tables Found", summary.get('tables_found', 0))
                else:
                    # Standard mode
                    stats = result.get('statistics', {})
                    entities = result.get('entities', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Pages", stats.get('total_pages', 0))
                        st.metric("Total Words", stats.get('total_words', 0))
                    with col2:
                        st.metric("Total Characters", stats.get('total_characters', 0))
                    
                    if entities:
                        st.subheader("Extracted Entities")
                        for entity_type, values in entities.items():
                            st.metric(entity_type.replace('_', ' ').title(), len(values))
            
            with tab2:
                if result.get('extraction_mode') == 'construction_takeoff':
                    items = result.get('items', [])
                    if items:
                        st.subheader(f"Extracted Items ({len(items)} total)")
                        
                        # Filter/search
                        search_term = st.text_input("🔍 Search items", placeholder="Filter by fixture type, model, etc.")
                        
                        # Display items in expandable sections
                        for idx, item in enumerate(items):
                            if not search_term or search_term.lower() in str(item).lower():
                                with st.expander(f"Item {idx+1}: {item.get('fixture_type', 'Unknown')} - Page {item.get('page_number', '?')}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Fixture Type:** {item.get('fixture_type', 'N/A')}")
                                        st.write(f"**Quantity:** {item.get('quantity', 'N/A')}")
                                        st.write(f"**Model Number:** {item.get('model_number', 'N/A')}")
                                    with col2:
                                        st.write(f"**Dimensions:** {item.get('dimensions', 'N/A')}")
                                        st.write(f"**Mounting Type:** {item.get('mounting_type', 'N/A')}")
                                        st.write(f"**Page Number:** {item.get('page_number', 'N/A')}")
                                    
                                    if item.get('raw_text'):
                                        st.code(item.get('raw_text'), language='text')
                    else:
                        st.info("No items extracted from this PDF.")
                else:
                    # Standard mode - show entities
                    entities = result.get('entities', {})
                    if entities:
                        for entity_type, values in entities.items():
                            with st.expander(f"{entity_type.replace('_', ' ').title()} ({len(values)})"):
                                st.json(values)
                    else:
                        st.info("No entities extracted from this PDF.")
            
            with tab3:
                st.subheader("Raw JSON Output")
                st.json(result)
                
                # Copy button
                st.code(json.dumps(result, indent=2), language='json')
            
            with tab4:
                st.subheader("Download Results")
                
                # Generate output filename
                output_filename = f"{Path(pdf_name).stem}_extracted.json"
                
                # Create JSON string
                json_str = json.dumps(result, indent=2)
                
                st.download_button(
                    label="💾 Download JSON",
                    data=json_str,
                    file_name=output_filename,
                    mime="application/json"
                )
                
                st.info(f"💡 Tip: You can also use the CLI command: `pdfx {pdf_name} --construction`")
        
        # Cleanup temp file
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()
    
    else:
        # Show example output when no file is uploaded
        st.info("👆 Upload a PDF file to get started")
        
        with st.expander("📖 How it works"):
            st.markdown("""
            ### Extraction Process:
            1. **PDF Parsing**: Uses `pdfplumber` to extract text and tables
            2. **Pattern Matching**: Applies regex patterns to identify construction items
            3. **Table Extraction**: Parses structured tables with column mapping
            4. **LLM Enhancement** (optional): Uses GPT-4 or Claude for better accuracy
            5. **Structured Output**: Organizes data into JSON format
            
            ### Construction Mode Extracts:
            - Item/Fixture Types (valves, pipes, fittings, etc.)
            - Quantities
            - Model Numbers / Spec References
            - Dimensions
            - Mounting Types
            - Page References
            
            ### Technologies:
            - **pdfplumber**: PDF text and table extraction
            - **Regex Patterns**: Construction-specific parsing
            - **OpenAI GPT-4** / **Anthropic Claude**: Optional LLM enhancement
            - **Pydantic**: Data validation and structure
            """)
        
        with st.expander("📊 Example Output"):
            st.json({
                "extraction_mode": "construction_takeoff",
                "total_items_found": 3,
                "items": [
                    {
                        "fixture_type": "VALVE",
                        "quantity": 2,
                        "model_number": "VP-1234",
                        "dimensions": "1 1/2\"ø",
                        "mounting_type": "Wall-mounted",
                        "page_number": 2
                    }
                ],
                "summary": {
                    "total_items": 3,
                    "items_with_quantities": 2,
                    "items_with_model_numbers": 1,
                    "pages_processed": 2
                }
            })


if __name__ == "__main__":
    main()
