"""
Construction-specific parser for extracting structured data from construction PDFs.
Extracts items, quantities, model numbers, dimensions, mounting types, etc.
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class ConstructionParser:
    """Parse construction-related data from PDF text."""
    
    def __init__(self):
        # Patterns for common construction terms
        self.fixture_patterns = [
            r'\b(pipe|fitting|duct|conduit|fixture|valve|faucet|sink|toilet|shower|bathtub|drain|vent|elbow|tee|coupling|reducer|adapter|cap|plug|flange|gasket|hanger|bracket|mount|bracket)\b',
            r'\b(ABS|PVC|CPVC|PEX|copper|steel|stainless|galvanized|cast iron|brass|bronze)\b',
        ]
        
        # Patterns for quantities
        self.quantity_patterns = [
            r'\b(\d+)\s*(ea|each|pcs|pieces|pc|unit|units|lf|linear feet|ft|feet|sq ft|sq\.?\s*ft\.?|square feet)\b',
            r'\bqty[:\s]+(\d+)\b',
            r'\bquantity[:\s]+(\d+)\b',
            r'\b(\d+)\s*x\s*\d+',  # Dimensions that might be quantities
        ]
        
        # Patterns for model numbers
        self.model_patterns = [
            r'\b(model|part\s*#|part\s*number|pn|sku|cat\s*#|catalog\s*#|item\s*#)[:\s]+([A-Z0-9\-\.]+)',
            r'\b([A-Z]{2,}\d+[A-Z0-9\-\.]*)\b',  # Alphanumeric codes
        ]
        
        # Patterns for dimensions
        self.dimension_patterns = [
            r'\b(\d+[\/\.]\d+|\d+)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+)\s*["\']?\b',  # L x W x H
            r'\b(\d+[\/\.]\d+|\d+)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+)\s*["\']?\b',  # L x W
            r'\b(\d+[\/\.]\d+|\d+)\s*["\']\s*(diameter|dia|OD|ID)\b',
            r'\b(\d+[\/\.]\d+|\d+)\s*inch(es)?\s*(diameter|dia|OD|ID)\b',
        ]
        
        # Patterns for mounting types
        self.mounting_patterns = [
            r'\b(wall[-\s]*hung|wall[-\s]*mount|floor[-\s]*mount|floor[-\s]*mounted|ceiling[-\s]*mount|surface[-\s]*mount|recessed|concealed|exposed|flush|undercounter|countertop|freestanding)\b',
        ]
        
        # Patterns for specifications/standards
        self.spec_patterns = [
            r'\b(ASTM|ANSI|UL|CSA|ASME|NEMA|NFPA|AWWA|IPC)[\s\-]?([A-Z0-9\.]+)',
            r'\b(grade|class|type)\s+([A-Z0-9]+)',
        ]
    
    def extract_items(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract construction items from text.
        
        Args:
            text: Text to parse
            page_num: Page number where text appears
            
        Returns:
            List of extracted items with metadata
        """
        items = []
        lines = text.split('\n')
        
        # Look for table-like structures and item descriptions
        current_item = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect potential item descriptions (lines with numbers and text)
            item_match = self._detect_item_line(line)
            if item_match:
                # Save previous item if exists
                if current_item and current_item.get('fixture_type'):
                    items.append(current_item)
                
                # Start new item
                current_item = {
                    'fixture_type': item_match.get('type'),
                    'quantity': item_match.get('quantity'),
                    'model_number': item_match.get('model'),
                    'dimensions': item_match.get('dimensions'),
                    'mounting_type': item_match.get('mounting'),
                    'spec_reference': item_match.get('spec'),
                    'page_number': page_num,
                    'raw_text': line,
                    'line_number': line_num + 1,
                }
            elif current_item:
                # Try to enrich current item with more info
                self._enrich_item(current_item, line)
        
        # Add last item if exists
        if current_item and current_item.get('fixture_type'):
            items.append(current_item)
        
        return items
    
    def _detect_item_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Detect if a line contains item information."""
        item_data = {}
        
        # Check for fixture types
        for pattern in self.fixture_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                item_data['type'] = match.group(0).strip()
                break
        
        # Check for quantities
        for pattern in self.quantity_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                item_data['quantity'] = int(match.group(1))
                break
        
        # Check for model numbers
        for pattern in self.model_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Get the last non-empty group
                groups = match.groups()
                if groups:
                    # Find the last non-empty group
                    for group in reversed(groups):
                        if group and group.strip():
                            item_data['model'] = group.strip()
                            break
                else:
                    # If no groups, use the full match
                    item_data['model'] = match.group(0).strip()
                break
        
        # Check for dimensions
        for pattern in self.dimension_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                dims = match.groups()
                item_data['dimensions'] = ' x '.join([d for d in dims if d])
                break
        
        # Check for mounting types
        for pattern in self.mounting_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                item_data['mounting'] = match.group(0).strip()
                break
        
        # Check for specs
        for pattern in self.spec_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                item_data['spec'] = ' '.join(match.groups()).strip()
                break
        
        return item_data if item_data else None
    
    def _enrich_item(self, item: Dict[str, Any], line: str):
        """Enrich an item with additional information from following lines."""
        # Add quantity if missing
        if not item.get('quantity'):
            for pattern in self.quantity_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    item['quantity'] = int(match.group(1))
                    break
        
        # Add model if missing
        if not item.get('model_number'):
            for pattern in self.model_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Get the last non-empty group
                    groups = match.groups()
                    if groups:
                        # Find the last non-empty group
                        for group in reversed(groups):
                            if group and group.strip():
                                item['model_number'] = group.strip()
                                break
                    else:
                        # If no groups, use the full match
                        item['model_number'] = match.group(0).strip()
                    break
        
        # Add dimensions if missing
        if not item.get('dimensions'):
            for pattern in self.dimension_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    dims = match.groups()
                    item['dimensions'] = ' x '.join([d for d in dims if d])
                    break
        
        # Add mounting type if missing
        if not item.get('mounting_type'):
            for pattern in self.mounting_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    item['mounting_type'] = match.group(0).strip()
                    break
        
        # Add spec if missing
        if not item.get('spec_reference'):
            for pattern in self.spec_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    item['spec_reference'] = ' '.join(match.groups()).strip()
                    break
    
    def parse_tables(self, tables: List[List[List[str]]], page_num: int) -> List[Dict[str, Any]]:
        """
        Parse table data into structured items.
        
        Args:
            tables: List of tables (each table is a list of rows, each row is a list of cells)
            page_num: Page number where tables appear
            
        Returns:
            List of extracted items from tables
        """
        items = []
        
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:  # Need at least header + 1 row
                continue
            
            headers = [cell.strip().lower() if cell else '' for cell in table[0]]
            
            # Common column name mappings
            column_mapping = {
                'fixture_type': ['item', 'fixture', 'type', 'description', 'product', 'component'],
                'quantity': ['qty', 'quantity', 'qty.', 'count', 'number', 'pieces'],
                'model_number': ['model', 'part #', 'part number', 'pn', 'sku', 'cat #', 'catalog #', 'item #'],
                'dimensions': ['size', 'dimension', 'dimensions', 'length', 'width', 'height', 'diameter'],
                'mounting_type': ['mounting', 'mount', 'installation', 'location'],
                'spec_reference': ['spec', 'specification', 'standard', 'grade', 'class'],
            }
            
            # Map headers to fields
            header_map = {}
            for col_idx, header in enumerate(headers):
                for field, keywords in column_mapping.items():
                    if any(keyword in header for keyword in keywords):
                        header_map[col_idx] = field
                        break
            
            # Parse rows
            for row_idx, row in enumerate(table[1:], start=1):
                item = {
                    'page_number': page_num,
                    'table_number': table_idx + 1,
                    'row_number': row_idx,
                }
                
                for col_idx, cell_value in enumerate(row):
                    if col_idx in header_map:
                        field = header_map[col_idx]
                        value = cell_value.strip() if cell_value else ''
                        
                        # Clean up value based on field type
                        if field == 'quantity' and value:
                            # Extract numeric quantity
                            qty_match = re.search(r'\d+', value)
                            if qty_match:
                                item[field] = int(qty_match.group())
                        else:
                            item[field] = value if value else None
                
                # Only add item if it has at least fixture_type or quantity
                if item.get('fixture_type') or item.get('quantity'):
                    items.append(item)
        
        return items

