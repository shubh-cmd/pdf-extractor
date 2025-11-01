"""
Extraction service that orchestrates PDF extraction using OOP principles.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from extractor.extractors import PDFTextExtractor
from extractor.models import (
    ConstructionExtractionResult,
    StandardExtractionResult,
    ExtractedItem,
    ConstructionExtractionSummary,
    ExtractedEntities,
    PageInfo,
    Statistics
)


class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies."""
    
    @abstractmethod
    def extract(self, pages_data: List[Dict[str, Any]], source_pdf: str) -> Dict[str, Any]:
        """
        Extract data from pages.
        
        Args:
            pages_data: List of page dictionaries
            source_pdf: Path to source PDF
            
        Returns:
            Dictionary with extraction results
        """
        pass
    
    @abstractmethod
    def get_statistics(self, pages_data: List[Dict[str, Any]]) -> Statistics:
        """Calculate and return statistics."""
        pass


class ConstructionExtractionStrategy(ExtractionStrategy):
    """Strategy for construction PDF takeoff extraction."""
    
    def __init__(self, construction_parser, llm_parser: Optional[Any] = None):
        """
        Initialize construction extraction strategy.
        
        Args:
            construction_parser: ConstructionParser instance
            llm_parser: Optional LLM parser for enhancement
        """
        self.construction_parser = construction_parser
        self.llm_parser = llm_parser
    
    def extract(self, pages_data: List[Dict[str, Any]], source_pdf: str) -> Dict[str, Any]:
        """Extract construction items from pages."""
        all_items = []
        all_tables = []
        
        # Extract items from text
        for page_data in pages_data:
            items = self.construction_parser.extract_items(
                page_data.get('text', ''),
                page_data.get('page_num', 0)
            )
            all_items.extend(items)
            
            # Extract items from tables
            tables = page_data.get('tables', [])
            if tables:
                table_items = self.construction_parser.parse_tables(
                    tables,
                    page_data.get('page_num', 0)
                )
                all_tables.extend(tables)
                all_items.extend(table_items)
        
        print(f"\r  ✓ Found {len(all_items)} items        ", flush=True)
        print("🔄 Step 2/4: Extracting construction items and quantities... ✓", flush=True)
        
        # Use LLM for hybrid enhancement if available (merges regex + LLM results)
        llm_success = False
        llm_was_requested = self.llm_parser is not None
        if self.llm_parser:
            regex_count = len(all_items)
            print(f"🔄 Step 3/4: Attempting LLM enhancement...", end="", flush=True)
            try:
                enhanced_items, llm_actually_worked = self._enhance_with_llm(all_items, pages_data)
                if llm_actually_worked:
                    llm_success = True
                    all_items = enhanced_items
                    llm_added = len(all_items) - regex_count
                    if llm_added > 0:
                        print(f"\r🔄 Step 3/4: LLM enhancement successful! ✓ (+{llm_added} additional items)", flush=True)
                    else:
                        print(f"\r🔄 Step 3/4: LLM enhancement successful! ✓ (merged with regex)", flush=True)
                else:
                    # LLM was called but returned no items or didn't enhance anything
                    llm_success = False
                    print(f"\r🔄 Step 3/4: LLM returned no items - processing without LLM... ✓", flush=True)
            except Exception as e:
                # Show clear error message if LLM was requested but failed
                error_msg = str(e)
                # Extract meaningful error message
                if "quota" in error_msg.lower() or "429" in error_msg:
                    error_msg = "quota exceeded"
                elif "model_not_found" in error_msg or "404" in error_msg:
                    error_msg = "model not available"
                elif "api_key" in error_msg.lower() or "401" in error_msg:
                    error_msg = "invalid API key"
                else:
                    # Get first meaningful part of error
                    error_msg = error_msg[:50] if len(error_msg) > 50 else error_msg
                
                llm_success = False
                print(f"\r🔄 Step 3/4: LLM enhancement failed ({error_msg}) - processing without LLM... ✓", flush=True)
        else:
            print("🔄 Step 3/4: Summarizing extracted data...", end="", flush=True)
        
        # Validate and create models
        validated_items = self._validate_items(all_items)
        summary = self._create_summary(validated_items, len(pages_data), len(all_tables))
        page_infos = self._create_page_infos(pages_data)
        statistics = self.get_statistics(pages_data)
        
        # Create result model
        result = ConstructionExtractionResult(
            source_pdf=str(source_pdf),
            extraction_mode='construction_takeoff',
            total_items_found=len(validated_items),
            items=validated_items,
            summary=summary,
            pages=page_infos,
            statistics=statistics,
        )
        
        if not self.llm_parser:
            print(" ✓", flush=True)
        
        # Remove source_pdf from output
        output = result.model_dump(mode='json')
        output.pop('source_pdf', None)
        
        # Add LLM usage flag (will be removed before saving to JSON)
        # Only mark as used if it actually succeeded
        output['_llm_used'] = llm_success
        output['_llm_requested'] = llm_was_requested
        
        return output
    
    def _validate_items(self, items: List[Dict[str, Any]]) -> List[ExtractedItem]:
        """Validate and convert items to ExtractedItem models."""
        validated_items = []
        for item in items:
            try:
                validated_items.append(ExtractedItem(**item))
            except Exception:
                # Create minimal valid item if validation fails
                validated_items.append(ExtractedItem(
                    page_number=item.get('page_number', 1),
                    fixture_type=item.get('fixture_type'),
                    quantity=item.get('quantity'),
                    model_number=item.get('model_number'),
                    dimensions=item.get('dimensions'),
                    mounting_type=item.get('mounting_type'),
                    spec_reference=item.get('spec_reference'),
                    table_number=item.get('table_number'),
                    row_number=item.get('row_number'),
                    raw_text=item.get('raw_text'),
                    line_number=item.get('line_number'),
                ))
        return validated_items
    
    def _create_summary(
        self,
        items: List[ExtractedItem],
        pages_processed: int,
        tables_found: int
    ) -> ConstructionExtractionSummary:
        """Create extraction summary."""
        return ConstructionExtractionSummary(
            total_items=len(items),
            items_with_quantities=sum(1 for item in items if item.quantity is not None),
            items_with_model_numbers=sum(1 for item in items if item.model_number),
            items_with_dimensions=sum(1 for item in items if item.dimensions),
            items_with_mounting_type=sum(1 for item in items if item.mounting_type),
            pages_processed=pages_processed,
            tables_found=tables_found,
        )
    
    def _create_page_infos(self, pages_data: List[Dict[str, Any]]) -> List[PageInfo]:
        """Create page info models with proper validation."""
        page_infos = []
        for p in pages_data:
            try:
                text_preview = p.get('text', '')
                if len(text_preview) > 200:
                    text_preview = text_preview[:200] + '...'
                page_info = PageInfo(
                    page_num=p.get('page_num', 1),
                    text_preview=text_preview if text_preview else None,
                    has_tables=bool(p.get('tables'))
                )
                page_infos.append(page_info)
            except Exception:
                # Fallback to minimal valid PageInfo
                page_infos.append(PageInfo(
                    page_num=max(1, p.get('page_num', 1)),
                    text_preview=None,
                    has_tables=False
                ))
        return page_infos
    
    def _enhance_with_llm(
        self,
        items: List[Dict[str, Any]],
        pages_data: List[Dict[str, Any]]
    ) -> tuple:
        """
        Hybrid approach: Enhance regex-extracted items with LLM results.
        Merges both sources intelligently rather than replacing.
        
        Returns:
            tuple: (merged_items, llm_actually_worked)
                - merged_items: The merged list of items
                - llm_actually_worked: True if LLM returned items and enhanced the results
        """
        # Combine text from pages
        from extractor.utils.helpers import combine_pages_text
        full_text = combine_pages_text(pages_data)
        
        # Start with regex items as base
        regex_items = items.copy()
        llm_items = []
        
        try:
            # More flexible schema to match actual requirements
            schema = {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "fixture_type": {
                                    "type": "string",
                                    "description": "Item/fixture type (e.g., 'Valve Package', 'Circulating Pump', 'Eye Wash Station')"
                                },
                                "quantity": {
                                    "type": ["integer", "string"],
                                    "description": "Quantity - can be integer (31) or string reference ('31.1, 31')"
                                },
                                "model_number": {
                                    "type": "string",
                                    "description": "Model number, spec reference, or catalog number (e.g., 'OM-141', 'HUH-13', 'BOILER CIRCULATING PUMP')"
                                },
                                "dimensions": {
                                    "type": "string",
                                    "description": "Associated dimensions if any (e.g., '1 1/2\"ø', '2 x 4 x 6')"
                                },
                                "mounting_type": {
                                    "type": "string",
                                    "description": "Mounting type if stated (e.g., 'wall-mounted', 'floor-mounted')"
                                },
                                "spec_reference": {
                                    "type": "string",
                                    "description": "Specification reference or page reference if available"
                                },
                                "page_number": {
                                    "type": ["integer", "string"],
                                    "description": "Page reference if mentioned in text"
                                }
                            }
                        }
                    }
                },
                "required": ["items"]
            }
            # Send more text to LLM (increase from 8000 to allow better context)
            # LLMs can handle more context now
            text_for_llm = full_text[:16000] if len(full_text) > 16000 else full_text
            enhanced = self.llm_parser.parse(text_for_llm, schema)
            
            if enhanced.get('items') and len(enhanced['items']) > 0:
                llm_items = enhanced['items']
            else:
                # LLM returned empty or no items
                return regex_items, False
        except Exception:
            # Exception occurred - LLM failed
            return regex_items, False
        
        # Merge regex and LLM results intelligently
        merged_items = self._merge_regex_and_llm_items(regex_items, llm_items)
        
        # Check if merge actually changed anything
        # Compare before and after - if items are the same, LLM didn't help
        if len(merged_items) == len(regex_items):
            # Check if any items were actually enhanced (have more fields filled)
            items_changed = False
            for merged, original in zip(merged_items, regex_items):
                # Count non-null fields
                merged_fields = sum(1 for v in merged.values() if v is not None and v != '')
                original_fields = sum(1 for v in original.values() if v is not None and v != '')
                if merged_fields > original_fields:
                    items_changed = True
                    break
            
            # If no items added and no items enhanced, LLM didn't work
            if not items_changed:
                return regex_items, False
        
        return merged_items, True
    
    def _merge_regex_and_llm_items(
        self,
        regex_items: List[Dict[str, Any]],
        llm_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Intelligently merge regex and LLM extracted items.
        
        Strategy:
        1. Use regex items as base (they have page numbers, line numbers, raw text)
        2. For each regex item, try to enrich with matching LLM item
        3. Add LLM items that don't match any regex item (new discoveries)
        4. Prefer more complete data (fill missing fields from LLM)
        """
        merged_items = []
        used_llm_indices = set()
        
        # Step 1: Enrich regex items with LLM data when they match
        for regex_item in regex_items:
            enriched_item = regex_item.copy()
            
            # Try to find matching LLM item
            best_match_idx = self._find_best_match(regex_item, llm_items, used_llm_indices)
            
            if best_match_idx is not None:
                # Merge: keep regex metadata, enrich with LLM data
                llm_item = llm_items[best_match_idx]
                enriched_item = self._merge_item_data(enriched_item, llm_item)
                used_llm_indices.add(best_match_idx)
            
            merged_items.append(enriched_item)
        
        # Step 2: Add LLM items that weren't matched (new discoveries)
        for idx, llm_item in enumerate(llm_items):
            if idx not in used_llm_indices:
                # This is a new item LLM found that regex missed
                # Ensure it has required fields
                if llm_item.get('page_number') or llm_item.get('fixture_type'):
                    merged_items.append(llm_item)
        
        return merged_items
    
    def _find_best_match(
        self,
        regex_item: Dict[str, Any],
        llm_items: List[Dict[str, Any]],
        used_indices: set
    ) -> Optional[int]:
        """
        Find the best matching LLM item for a regex item.
        Matches based on fixture_type, model_number, page_number, or similar text.
        """
        regex_fixture = (regex_item.get('fixture_type') or '').lower()
        regex_model = (regex_item.get('model_number') or '').lower()
        regex_page = regex_item.get('page_number')
        
        best_score = 0
        best_idx = None
        
        for idx, llm_item in enumerate(llm_items):
            if idx in used_indices:
                continue
            
            llm_fixture = (llm_item.get('fixture_type') or '').lower()
            llm_model = (llm_item.get('model_number') or '').lower()
            llm_page = llm_item.get('page_number')
            
            score = 0
            
            # Match on fixture type (strongest indicator)
            if regex_fixture and llm_fixture:
                if regex_fixture == llm_fixture:
                    score += 10
                elif regex_fixture in llm_fixture or llm_fixture in regex_fixture:
                    score += 5
            
            # Match on model number
            if regex_model and llm_model:
                if regex_model == llm_model:
                    score += 8
                elif regex_model in llm_model or llm_model in regex_model:
                    score += 4
            
            # Match on page number
            if regex_page and llm_page and regex_page == llm_page:
                score += 3
            
            # Prefer matches with more information
            if score > best_score:
                best_score = score
                best_idx = idx
        
        # Only return match if score is significant enough
        return best_idx if best_score >= 3 else None
    
    def _merge_item_data(
        self,
        base_item: Dict[str, Any],
        enhancement_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge enhancement data into base item.
        Prefers non-empty values, keeps base metadata (page_number, line_number, raw_text).
        """
        merged = base_item.copy()
        
        # Always preserve regex metadata
        preserved_fields = ['page_number', 'table_number', 'row_number', 
                          'line_number', 'raw_text']
        
        # Merge fields: use enhancement if base is missing or empty
        enhancement_fields = ['fixture_type', 'quantity', 'model_number', 
                             'dimensions', 'mounting_type', 'spec_reference']
        
        for field in enhancement_fields:
            base_value = base_item.get(field)
            enh_value = enhancement_item.get(field)
            
            # Prefer enhancement if base is missing/empty and enhancement has value
            if not base_value and enh_value:
                merged[field] = enh_value
            # If both exist, prefer the more complete one
            elif base_value and enh_value:
                # Keep base if it's more detailed, otherwise use enhancement
                if len(str(base_value)) > len(str(enh_value)):
                    merged[field] = base_value
                else:
                    merged[field] = enh_value
        
        return merged
    
    def get_statistics(self, pages_data: List[Dict[str, Any]]) -> Statistics:
        """Calculate statistics."""
        from extractor.utils.helpers import get_statistics
        stats_dict = get_statistics(pages_data)
        return Statistics(**stats_dict)


class StandardExtractionStrategy(ExtractionStrategy):
    """Strategy for standard text extraction."""
    
    def __init__(self, parser_rules):
        """
        Initialize standard extraction strategy.
        
        Args:
            parser_rules: ParserRules instance
        """
        self.parser_rules = parser_rules
    
    def extract(self, pages_data: List[Dict[str, Any]], source_pdf: str) -> Dict[str, Any]:
        """Extract standard entities from pages."""
        from extractor.utils.helpers import combine_pages_text, normalize_table_cells
        from extractor.models import ExtractedEntities, PageData
        full_text = combine_pages_text(pages_data)
        
        print("🔄 Step 2/4: Processing extracted data...", end="", flush=True)
        entities_dict = self.parser_rules.extract_entities(full_text)
        statistics = self.get_statistics(pages_data)
        print(" ✓", flush=True)
        
        # Convert entities dict to ExtractedEntities model
        entities = ExtractedEntities.from_dict(entities_dict)
        
        # Convert pages_data to properly validated PageData models
        validated_pages = []
        for page_dict in pages_data:
            page_data = PageData(
                page_num=page_dict['page_num'],
                text=page_dict.get('text', ''),
                width=page_dict.get('width'),
                height=page_dict.get('height'),
                tables=normalize_table_cells(page_dict.get('tables'))
            )
            validated_pages.append(page_data)
        
        print("🔄 Step 3/4: Summarizing extracted data...", end="", flush=True)
        # Create result with all validated models
        result = StandardExtractionResult(
            source_pdf=str(source_pdf),
            extraction_mode='standard',
            pages=validated_pages,  # List of validated PageData models
            full_text=full_text,
            statistics=statistics,  # Statistics model
            entities=entities  # ExtractedEntities model
        )
        print(" ✓", flush=True)
        
        # Serialize to JSON - Pydantic will handle nested model serialization
        output = result.model_dump(mode='json')
        # Remove source_pdf from output as requested
        output.pop('source_pdf', None)
        
        # Ensure output structure matches model exactly
        return output
    
    def get_statistics(self, pages_data: List[Dict[str, Any]]) -> Statistics:
        """Calculate statistics."""
        from extractor.utils.helpers import get_statistics
        stats_dict = get_statistics(pages_data)
        return Statistics(**stats_dict)


class ExtractionService:
    """Service class that orchestrates PDF extraction."""
    
    def __init__(
        self,
        extractor: PDFTextExtractor,
        strategy: ExtractionStrategy
    ):
        """
        Initialize extraction service.
        
        Args:
            extractor: PDFTextExtractor instance
            strategy: ExtractionStrategy to use
        """
        self.extractor = extractor
        self.strategy = strategy
    
    def extract(self, pdf_path: str | Path, show_progress: bool = True) -> Dict[str, Any]:
        """
        Extract data from PDF.
        
        Args:
            pdf_path: Path to PDF file
            show_progress: Whether to show progress indicators
            
        Returns:
            Dictionary with extraction results
        """
        # Extract pages using PDF extractor
        pages_data = self.extractor.extract_text(pdf_path, show_progress=show_progress)
        
        # Use strategy to process pages
        result = self.strategy.extract(pages_data, pdf_path)
        
        return result
    
    def get_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information from extraction result."""
        if result.get('extraction_mode') == 'construction_takeoff':
            return result.get('summary', {})
        else:
            return {
                'entities': result.get('entities', {}),
                'statistics': result.get('statistics', {})
            }


class ExtractionServiceFactory:
    """Factory class for creating extraction services."""
    
    @staticmethod
    def create_construction_service(
        use_ocr: bool = False,  # Optional - requires system dependencies (poppler). Use LLM with vision instead for platform independence
        llm_type: Optional[str] = None
    ) -> ExtractionService:
        """
        Create extraction service for construction PDFs.
        
        Args:
            use_ocr: Whether to use OCR
            llm_type: LLM type ('openai' or 'claude') for enhancement
            
        Returns:
            ExtractionService configured for construction extraction
        """
        extractor = PDFTextExtractor(use_ocr=use_ocr)
        construction_parser = ConstructionParser()
        
        llm_parser = None
        if llm_type:
            llm_parser = ExtractionServiceFactory._create_llm_parser(llm_type)
        
        strategy = ConstructionExtractionStrategy(
            construction_parser=construction_parser,
            llm_parser=llm_parser
        )
        
        return ExtractionService(extractor=extractor, strategy=strategy)
    
    @staticmethod
    def create_standard_service(use_ocr: bool = False) -> ExtractionService:
        """
        Create extraction service for standard text extraction.
        
        Args:
            use_ocr: Whether to use OCR
            
        Returns:
            ExtractionService configured for standard extraction
        """
        extractor = PDFTextExtractor(use_ocr=use_ocr)
        parser_rules = ParserRules()
        strategy = StandardExtractionStrategy(parser_rules=parser_rules)
        
        return ExtractionService(extractor=extractor, strategy=strategy)
    
    @staticmethod
    def _create_llm_parser(llm_type: str):
        """Create LLM parser instance."""
        import os
        
        if llm_type == 'openai':
            from extractor.parsers.llm import OpenAIParser
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return None
            try:
                # Try gpt-4o-mini first (cheaper, widely available)
                # Fallback to gpt-3.5-turbo if needed
                try:
                    return OpenAIParser(api_key=api_key, model="gpt-4o-mini")
                except Exception:
                    # Fallback to gpt-3.5-turbo if gpt-4o-mini fails
                    return OpenAIParser(api_key=api_key, model="gpt-3.5-turbo")
            except Exception:
                # Silently fail if initialization fails
                return None
        
        elif llm_type == 'claude':
            from extractor.parsers.llm import ClaudeParser
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return None
            try:
                return ClaudeParser(api_key=api_key)
            except Exception:
                # Silently fail if initialization fails
                return None
        
        return None


# Import at end to avoid circular imports
from extractor.parsers import ConstructionParser, ParserRules

