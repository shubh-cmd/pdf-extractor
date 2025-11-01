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
        # Patterns to exclude - common non-item text (legal disclaimers, headers, instructions, etc.)
        self.exclude_patterns = [
            r'\b(prohibited|copyright|reserved|confidential|proprietary)\b',
            r'\b(use\s+in\s+whole|in\s+part|strictly\s+prohibited)\b',
            r'\b(all\s+rights\s+reserved|page\s+\d+|document\s+control)\b',
            r'\b(revision|date|prepared\s+by|approved\s+by)\b',
            r'^[A-Z\s]{20,}$',  # All caps long lines (often headers/disclaimers)
            r'^\d+$',  # Lines that are just numbers
            r'^[^\w\s]+$',  # Lines that are just punctuation/symbols
            # Instruction phrases (not actual items)
            r'^\s*(up\s+to|see\s+|refer\s+to|see\s+page|refer\s+page|see\s+drawing|refer\s+drawing|see\s+spec|refer\s+spec)\b',
            r'^\s*(note:|notice:|warning:|caution:)\b',
            r'^\s*(see|refer|use|install|mount|connect)\s+[A-Z0-9\-]+',  # Instructions like "SEE MAU-11"
        ]
        
        # Phrases that indicate this is NOT an item but an instruction/reference
        self.instruction_phrases = [
            'up to', 'see', 'refer to', 'see page', 'refer page', 'see drawing', 'refer drawing',
            'see spec', 'refer spec', 'use', 'install', 'mount', 'connect', 'note:', 'notice:'
        ]
        # Expanded patterns for construction/mechanical equipment and fixtures
        # Includes: valves, pumps, equipment, fixtures, stations, connections, etc.
        self.fixture_patterns = [
            # Core plumbing/HVAC components
            r'\b(pipe|fitting|duct|conduit|fixture|valve|faucet|sink|toilet|shower|bathtub|drain|vent|elbow|tee|coupling|reducer|adapter|cap|plug|flange|gasket|hanger|bracket|mount)\b',
            # Equipment types
            r'\b(pump|circulating\s+pump|booster\s+pump|centrifugal\s+pump|pump\s+package)\b',
            r'\b(equipment|boiler|heater|tower|cooling\s+tower|tank|reservoir|vessel|chiller)\b',
            r'\b(station|wash\s+station|eye\s+wash|safety\s+station|emergency\s+station)\b',
            r'\b(connection|fixture\s+connection|piping\s+connection|cooling\s+connection)\b',
            r'\b(package|valve\s+package|equipment\s+package|fixture\s+package)\b',
            # Shop/room fixtures
            r'\b(shop\s+fixture|repair\s+shop|body\s+shop|paint\s+booth|booth\s+equipment)\b',
            r'\b(fixtures|body\s+repair|paint\s+equipment|mechanical\s+equipment)\b',
            # Material types (may appear as items)
            r'\b(ABS|PVC|CPVC|PEX|copper|steel|stainless|galvanized|cast\s+iron|brass|bronze)\b',
            # Generic terms that often indicate items
            r'\b(item|component|part|unit|assembly|system)\b',
        ]
        
        # Patterns for quantities (expanded for better detection, but avoid extracting from model numbers)
        self.quantity_patterns = [
            # Explicit quantity labels (most reliable)
            r'\b(?:qty|quantity|qty\.)[:\s]+(\d+(?:\.\d+)?)\b',
            r'\b(?:qty|quantity)[:\s]+(\d+(?:\.\d+)?)\s*(?:ea|each|pcs|pieces|unit|units)?\b',
            # Quantities with units
            r'\b(\d+)\s*(?:ea|each|pcs|pieces|pc|unit|units)\b',
            r'\b(\d+)\s*(?:lf|linear feet|ft|feet|sq ft|sq\.?\s*ft\.?|square feet)\b',
            # Decimal references like "31.1, 31" (but not if it's part of a model number)
            r'(?<!-)(?<![A-Z])\b(\d+\.\d+)(?:\s*,\s*\d+(?:\.\d+)?)*\b(?![-A-Z])',  # Not after hyphen/letter
            # Quantities in parentheses at end of line
            r'\((\d+)\)(?:\s|$)',
            # Pattern: "Item Name (12)" - quantity in parens after item name
            r'\b[A-Z][A-Za-z\s]+\s*\((\d+)\)',
            # Standalone quantity (must be separate from model numbers)
            r'(?:^|\s|,|:)\s*(\d{1,3})\s*(?:ea|each|pcs|pieces|qty|quantity|unit|units|$)',  # Not model numbers (1-3 digits max for quantities)
        ]
        
        # Patterns for model numbers (more precise to avoid matching entire lines)
        self.model_patterns = [
            r'\b(model|part\s*#|part\s*number|pn|sku|cat\s*#|catalog\s*#|item\s*#)[:\s]+([A-Z0-9\-\.]+)',
            # Formats like OM-141, OM-105, HUH-13 (with hyphen and numbers)
            r'\b([A-Z]{2,}-\d+[A-Z0-9\-]*)\b',  # OM-141, HUH-13, etc. (must have hyphen)
            # Formats like CH30, VP1234 (letters followed by numbers, no space)
            r'\b([A-Z]{1,3}\d{2,}[A-Z0-9]*)\b',  # CH30, VP1234, etc.
            # NOTE: Removed "BOILER CIRCULATING PUMP" pattern - these are descriptions, not model numbers
            # Simple model references (avoid matching entire lines)
            r'\b([A-Z]{2,}\d+[A-Z0-9])\b',  # More restrictive - no dots, limited length
        ]
        
        # Patterns for dimensions (expanded for better coverage)
        self.dimension_patterns = [
            # Length dimensions with feet and inches: "25' -1 5/8"", "10' 6\"", "25'-1 5/8\""
            r'\b(\d+)\s*["\']\s*[-–]\s*(\d+)\s*(\d+\/\d+)\s*["\']',  # "25' -1 5/8""
            r'\b(\d+)\s*["\']\s*[-–]\s*(\d+)\s*["\']',  # "25' -1""
            r'\b(\d+)\s*["\']\s+(\d+)\s*(\d+\/\d+)\s*["\']',  # "25' 1 5/8""
            r'\b(\d+)\s*["\']\s+(\d+)\s*["\']',  # "25' 6""
            r'\b(\d+)\s*["\']\s*[-–]\s*(\d+)\s*(\d+\/\d+)\b',  # "25'-1 5/8" (without trailing quote)
            r'\b(\d+)\s*["\']\s*[-–]?\s*(\d+)\s*(\d+\/\d+)\s*["\']?\b',  # Flexible: "25'1 5/8""
            # L x W x H formats
            r'\b(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\b',
            # L x W formats
            r'\b(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\s*x\s*(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\b',
            # Diameter formats
            r'\b(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']\s*(?:diameter|dia|OD|ID|D|DIA)\b',
            r'\b(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*inch(es)?\s*(?:diameter|dia|OD|ID)\b',
            r'\b(?:diameter|dia|OD|ID|D|DIA)[\s:]+(\d+[\/\.]\d+|\d+(?:\.\d+)?)\s*["\']?\b',
            # Single dimension with unit (but NOT standalone numbers that might be quantities)
            r'\b(\d+(?:\.\d+)?)\s*["\'](?!\s*x)(?![A-Z0-9])',  # Like 12" but not part of "12" x 6" or model numbers
            r'\b(\d+(?:\.\d+)?)\s*(?:inch|inches|in|ft|feet|cm|mm)\b',  # Number with unit (avoid fractions alone)
            # Size formats like "1 1/2"", "2-1/2"" (fractional inches - must have space or hyphen before fraction)
            r'\b(\d+\s*[\/\-]\s*\d+\/\d+)\s*["\']\b',  # "1 1/2"" or "2-1/2""
            # Diameter formats with ø symbol - CRITICAL: Must capture full string like "1 1/2\"ø"
            r'(\d+\s+\d+\/\d+\s*["\']?\s*ø)',  # "1 1/2\"ø" or "1 1/2 ø"
            r'(\d+[- ]\d+\/\d+\s*["\']?\s*ø)',  # "1-1/2\"ø"
            r'(\d+\/\d+\s*["\']?\s*ø)',  # "1/2\"ø"
            r'(\d+\s*["\']?\s*ø)',  # "1\"ø" or "1 ø"
            # Fractional dimensions with context (diameter, size, etc.)
            r'(?:diameter|dia|OD|ID|size|dimension)[:\s]+(\d+\/\d+)\s*["\']?',
            # Avoid extracting simple fractions like "1/2" that might be part of model numbers or specs
            # Only extract if there's clear dimension context
            r'(?:\d+\s+)?(\d+\/\d+)\s*["\']\s*(?:diameter|dia|OD|ID|inch|inches)',
            # Metric dimensions
            r'\b(\d+(?:\.\d+)?)\s*(?:mm|cm|m)\s*x\s*(\d+(?:\.\d+)?)\s*(?:mm|cm|m)\b',
        ]
        
        # Patterns for mounting types (expanded)
        self.mounting_patterns = [
            # Wall mounting
            r'\b(wall[-\s]*(?:hung|mount|mounted|mounting))\b',
            # Floor mounting
            r'\b(floor[-\s]*(?:mount|mounted|mounting))\b',
            # Ceiling mounting
            r'\b(ceiling[-\s]*(?:mount|mounted|mounting))\b',
            # Surface mounting
            r'\b(surface[-\s]*(?:mount|mounted|mounting))\b',
            # Other mounting types
            r'\b(recessed|concealed|exposed|flush|flush[-\s]mount|undercounter|countertop|freestanding|portable|stationary|fixed|removable|slip[-\s]on|threaded|welded|bolted|hanging|suspended|ceiling[-\s]hung)\b',
            # Mounting type with context
            r'\b(mounting[-\s]type[:\s]+)(wall|floor|ceiling|surface|recessed|exposed)\b',
        ]
        
        # Patterns for specifications/standards and page references (expanded)
        self.spec_patterns = [
            # Industry standards
            r'\b(ASTM|ANSI|UL|CSA|ASME|NEMA|NFPA|AWWA|IPC|ISO|DIN|BS)[\s\-]?([A-Z0-9\.\-]+)',
            r'\b(grade|class|type|rating)\s+([A-Z0-9]+)',
            # Spec references - includes decimal numbers like "31.1", "30.1" that are spec/item references
            r'\b(spec[\.:]?\s*#?|specification[:\s]*|ref[\.:]?\s*#?|reference[:\s]*)([A-Z0-9\.\-]+)',
            r'\b(dwg[\.:]?\s*#?|drawing[:\s]*)([A-Z0-9\.\-]+)',
            # Spec item references (decimal numbers like "31.1", "30.1" when not marked as quantity)
            # These appear in construction docs to reference specific items/specs
            r'\b(\d+\.\d+)(?:\s|$|,|;|:)(?!\s*(?:ea|each|pcs|pieces|qty|quantity))',  # "31.1" but not "31.1 ea"
            # Page references
            r'\b(page\s+#?|pg[\.:]?\s*#?|p[\.:]?\s*#?)(\d+)',
            r'\b(see\s+)?(?:page|pg|p)\.?\s*(\d+)',
            r'\b(\d+)[\s\-]+(?:page|pg)\b',
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
        
        # Context-aware extraction: look at surrounding lines
        # Look for table-like structures and item descriptions
        current_item = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect potential item descriptions (lines with numbers and text)
            item_match = self._detect_item_line(line, page_num, line_num)
            if item_match:
                # Save previous item if exists
                if current_item and (current_item.get('fixture_type') or current_item.get('model_number') or current_item.get('quantity')):
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
                # Try to enrich current item with more info from current and surrounding lines
                # Look at previous line, current line, and next line for context
                context_lines = []
                if line_num > 0:
                    context_lines.append(lines[line_num - 1].strip())
                context_lines.append(line)  # Current line
                if line_num + 1 < len(lines):
                    context_lines.append(lines[line_num + 1].strip())
                
                # Enrich with all context lines
                for ctx_line in context_lines:
                    if ctx_line:
                        self._enrich_item(current_item, ctx_line)
        
        # Add last item if exists (check for any meaningful data)
        if current_item and (current_item.get('fixture_type') or current_item.get('model_number') or current_item.get('quantity')):
            items.append(current_item)
        
        return items
    
    def _detect_item_line(self, line: str, page_num: int = 0, line_num: int = 0) -> Optional[Dict[str, Any]]:
        """
        Detect if a line contains item information.
        More flexible: accepts lines with quantities, model numbers, or fixture types.
        """
        # First check: exclude lines that are clearly not items (legal disclaimers, headers, etc.)
        for exclude_pattern in self.exclude_patterns:
            if re.search(exclude_pattern, line, re.IGNORECASE):
                return None  # Skip this line entirely
        
        # Check for instruction phrases explicitly (lines that are instructions, not items)
        line_upper = line.upper().strip()
        for phrase in self.instruction_phrases:
            if line_upper.startswith(phrase.upper()):
                return None  # Skip instruction lines like "UP TO MAU-11", "SEE PAGE 5", etc.
        
        # Check for lines that start with action verbs (instructions, not items)
        if re.match(r'^\s*(up\s+to|see|refer|use|install|mount|connect|note|notice|warning)\s+', line, re.IGNORECASE):
            return None
        
        # Skip very short lines or lines that are just noise
        if len(line.strip()) < 3:
            return None
        
        item_data = {}
        has_indicators = False
        
        # Check for fixture types (try to get full phrase, not just single word)
        best_match = None
        best_match_len = 0
        
        for pattern in self.fixture_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                matched_text = match.group(0).strip()
                # Prefer longer matches (e.g., "circulating pump" over just "pump")
                if len(matched_text) > best_match_len:
                    best_match = matched_text
                    best_match_len = len(matched_text)
        
        if best_match:
            has_indicators = True
            # Try to extract full item description if it's capitalized or contains model numbers
            # Look for capitalized phrases before the match
            full_item_match = re.search(r'\b([A-Z][A-Za-z\s]+?)\s*(?:' + re.escape(best_match) + r'|package|equipment|fixture|station|connection)', line, re.IGNORECASE)
            if full_item_match:
                fixture_type = full_item_match.group(1).strip() + ' ' + best_match
                # Fix duplicate words (e.g., "VALVE VALVE PACKAGE" -> "Valve Package")
                words = fixture_type.split()
                unique_words = []
                prev_word = None
                for word in words:
                    if word.upper() != prev_word:  # Skip if same as previous word
                        unique_words.append(word)
                        prev_word = word.upper()
                item_data['type'] = ' '.join(unique_words).title()
            else:
                item_data['type'] = best_match.title()  # Capitalize first letter
        else:
            # If no fixture type found, try to infer from capitalized words or common patterns
            # BUT: Don't infer from dimensions or measurement patterns!
            # Look for capitalized multi-word phrases (likely item descriptions)
            capitalized_phrase = re.search(r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)', line)
            if capitalized_phrase:
                potential_type = capitalized_phrase.group(1).strip()
                
                # CRITICAL: Check if this is actually a dimension pattern (not a fixture type)
                # Patterns like "0' - 7", "10' 6\"", "25' -1 5/8\"" are dimensions, not fixture types
                is_dimension_pattern = bool(re.search(r'\d+\s*["\']\s*[-–]?\s*\d+', potential_type))
                # Also check if it's just numbers with units
                is_numeric_only = bool(re.match(r'^[\d\s\'\"\-\/\.]+$', potential_type.strip()))
                
                # Only use as fixture type if it's NOT a dimension pattern and looks like text
                if (len(potential_type.split()) >= 2 and len(potential_type) > 10 and 
                    not is_dimension_pattern and not is_numeric_only):
                    item_data['type'] = potential_type
                    has_indicators = True
        
        # Check for quantities (handle decimals and multiple references)
        # IMPORTANT: Don't extract quantities that are part of model numbers (e.g., MAU-11 -> don't extract 11 as quantity)
        for pattern in self.quantity_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    qty_str = match.group(1)
                    qty_num = int(qty_str) if '.' not in qty_str else None
                    
                    # CRITICAL: Check if this number is part of a model number pattern
                    # If line contains patterns like "MAU-11", "CH30", "OM-141", don't extract the number as quantity
                    model_patterns_in_line = [
                        r'[A-Z]{2,}-\d+',  # MAU-11, OM-141
                        r'[A-Z]{1,3}\d{2,}',  # CH30, VP1234
                    ]
                    
                    # Check if this quantity appears to be part of a model number
                    is_part_of_model = False
                    for model_pat in model_patterns_in_line:
                        model_match = re.search(model_pat, line, re.IGNORECASE)
                        if model_match and qty_str in model_match.group():
                            is_part_of_model = True
                            break
                    
                    # Also check if quantity appears right after instruction words
                    context_before = line[:match.start()].strip().upper()
                    if any(context_before.endswith(phrase.upper()) for phrase in ['UP TO', 'SEE', 'REFER TO', 'USE']):
                        is_part_of_model = True  # Treat as instruction, not quantity
                    
                    # CRITICAL: If it's a decimal like "31.1" and NOT explicitly marked as quantity,
                    # it's likely a spec reference, not an actual quantity
                    is_spec_reference = False
                    # First check: if we already found this as a spec reference, skip quantity
                    if item_data.get('_has_spec_decimal'):
                        if qty_str == item_data.get('_spec_decimal_value') or qty_str == item_data.get('spec', ''):
                            is_spec_reference = True  # This decimal was already identified as spec reference
                    elif '.' in qty_str:
                        # Decimal numbers without explicit "qty" or "quantity" labels are often spec references
                        if not re.search(r'\b(qty|quantity)[:\s]*\d+\.\d+', line, re.IGNORECASE):
                            # Check if line has dimensions or model numbers - if so, "31.1" is likely a spec ref
                            if re.search(r'\d+\s*["\']|OM-|MAU-|CH\d+|model|part\s*#', line, re.IGNORECASE):
                                is_spec_reference = True  # Likely a spec reference, not quantity
                                # Also add it as spec reference if we haven't found one yet
                                if not item_data.get('spec'):
                                    item_data['spec'] = qty_str
                                    item_data['_has_spec_decimal'] = True
                                    item_data['_spec_decimal_value'] = qty_str
                    
                    if not is_part_of_model and not is_spec_reference:
                        has_indicators = True
                        # Handle decimal quantities or take first number from comma-separated
                        if '.' in qty_str:
                            item_data['quantity'] = qty_str  # Keep as string only if explicitly marked as quantity
                        else:
                            item_data['quantity'] = int(qty_str)
                        break  # Only break if we actually set a quantity
                except (ValueError, IndexError):
                    pass
        
        # Check for model numbers (more strict - avoid matching entire lines and legal text)
        all_models = []
        for pattern in self.model_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if groups:
                    # Get the model number from groups
                    for group in reversed(groups):
                        if group and group.strip():
                            model = group.strip()
                            # Skip if it looks like a quantity, dimension, or is too long (likely not a model)
                            if not re.match(r'^\d+$', model) and len(model) > 1 and len(model) < 50:
                                # Must have some structure - letters and numbers
                                # Exclude very short codes (like L01) if they're in legal/disclaimer text
                                if len(model) >= 2:
                                    # Skip single letter + number codes if line contains legal text
                                    if len(model) <= 4 and re.match(r'^[A-Z]\d+$', model):
                                        # Check if line has legal disclaimer words
                                        if any(word in line.upper() for word in ['PROHIBITED', 'COPYRIGHT', 'RESERVED', 'CONFIDENTIAL', 'USE IN']):
                                            continue  # Skip this model - likely not a real model
                                        
                                        # Skip location codes (L01, A123) unless explicitly marked as model/part
                                        if not re.search(r'\b(model|part|pn|sku|cat|item\s*#)', line, re.IGNORECASE):
                                            continue  # Likely a location/room code, not a model
                                        
                                        # Additional check: skip if it's in a line that's just the code (likely location label)
                                        if len(line.strip().split()) <= 2 and model.upper() in line.upper():
                                            # Line is very short and mostly the code - likely a location label
                                            continue
                                        
                                        if re.search(r'[A-Z]', model) and re.search(r'\d', model):
                                            if model not in all_models:
                                                all_models.append(model)
                                    break
                else:
                    model = match.group(0).strip()
                    # Be strict - model must be reasonable length and have structure
                    if len(model) >= 3 and len(model) < 30:
                        # Skip very short codes in legal text
                        if len(model) <= 4 and re.match(r'^[A-Z]\d+$', model):
                            if any(word in line.upper() for word in ['PROHIBITED', 'COPYRIGHT', 'RESERVED', 'CONFIDENTIAL', 'USE IN']):
                                continue  # Skip
                        
                        # Must have letters and numbers or be a known format
                        if (re.search(r'[A-Z]', model) and re.search(r'\d', model)) or re.match(r'^[A-Z]{2,}-\d+', model):
                            if model not in all_models:
                                all_models.append(model)
        
        if all_models:
            has_indicators = True
            # Join multiple models with comma if found, otherwise use first
            item_data['model'] = ', '.join(all_models[:2])  # Limit to 2 to avoid too long
        
        # Check for dimensions (but avoid extracting fractions that are part of model numbers or specs)
        for pattern in self.dimension_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                dims = match.groups()
                dim_parts = [d for d in dims if d]
                if dim_parts:
                    # Filter out standalone fractions that might be part of model numbers (like "1/2" in context of "UP TO MAU-11")
                    # Only keep if it's clearly a dimension (has multiple parts, has units, or is in dimension context)
                    filtered_dims = []
                    for dim in dim_parts:
                        # Skip if it's just a simple fraction and the line contains model number patterns or instruction phrases
                        if '/' in dim and len(dim) <= 4:  # Simple fraction like "1/2", "3/4"
                            # Check if line has model number patterns or instruction phrases
                            has_model = bool(re.search(r'[A-Z]{2,}-\d+|[A-Z]{1,3}\d{2,}', line, re.IGNORECASE))
                            has_instruction = any(phrase in line.upper() for phrase in ['UP TO', 'SEE', 'REFER TO'])
                            # Only keep if there's clear dimension context (diameter, size, etc.) and no model/instruction
                            if (has_model or has_instruction) and not re.search(r'(diameter|dia|OD|ID|size|dimension|inch|inches|x\s*\d)', line, re.IGNORECASE):
                                continue  # Skip simple fractions when model numbers/instructions are present
                        filtered_dims.append(dim)
                    
                    if filtered_dims:
                        # Try to extract the full dimension string from the line (especially for feet-inches formats)
                        # Look for common dimension patterns first
                        full_dim_patterns = [
                            # Diameter formats with ø symbol (check FIRST - most specific)
                            r'(\d+\s+\d+\/\d+\s*["\']?\s*ø)',  # "1 1/2\"ø" or "1 1/2 ø"
                            r'(\d+[- ]\d+\/\d+\s*["\']?\s*ø)',  # "1-1/2\"ø"
                            r'(\d+\/\d+\s*["\']?\s*ø)',  # "1/2\"ø"
                            r'(\d+\s*["\']?\s*ø)',  # "1\"ø" or "1 ø"
                            # Length dimensions with feet and inches
                            r'(\d+\s*["\']\s*[-–]\s*\d+\s+\d+\/\d+\s*["\'])',  # "25' -1 5/8\""
                            r'(\d+\s*["\']\s*[-–]\s*\d+\s*["\'])',  # "25' -1""
                            r'(\d+\s*["\']\s+\d+\s+\d+\/\d+\s*["\'])',  # "25' 1 5/8\""
                            r'(\d+\s*["\']\s+\d+\s*["\'])',  # "25' 6\""
                            r'(\d+\s*["\']\s*[-–]?\s*\d+\s*\d+\/\d+)',  # "25'-1 5/8" (no trailing quote)
                            r'(\d+\s*["\']\s*[-–]?\s*\d+\s*\d+\/\d+\s*["\']?)',  # Flexible feet-inches
                            # Also catch patterns like "BE= 25' -1 5/8\"" where dimension follows "=" or ":"
                            r'(?:[=:]\s*)(\d+\s*["\']\s*[-–]?\s*\d+\s*\d+\/\d+\s*["\']?)',  # "BE= 25' -1 5/8\""
                            r'(?:[=:]\s*)(\d+\s*["\']\s*[-–]?\s*\d+\s*["\']?)',  # "BE= 25' -1\""
                        ]
                        
                        full_dim_found = None
                        for dim_pattern in full_dim_patterns:
                            full_match = re.search(dim_pattern, line, re.IGNORECASE)
                            if full_match:
                                full_dim_found = full_match.group(1).strip()
                                break
                        
                        if full_dim_found:
                            item_data['dimensions'] = full_dim_found
                        elif len(filtered_dims) >= 2:
                            item_data['dimensions'] = ' x '.join(filtered_dims)
                        else:
                            # CRITICAL: Only use single dimension if it's clearly a dimension
                            # Standalone numbers like "4", "2", "6" are NOT dimensions - they need units or context
                            single_dim = filtered_dims[0]
                            
                            # Skip if it's just a standalone number without units or dimension context
                            is_standalone_number = bool(re.match(r'^\d+$', single_dim.strip()))
                            
                            # Check if it's likely a dimension (has quotes, units, diameter symbol, or is part of dimension pattern)
                            has_dimension_context = bool(re.search(
                                r'["\']|inch|inches|in|feet|ft|cm|mm|diameter|dia|ø|"|\'|x\s*\d', 
                                line, re.IGNORECASE
                            ))
                            
                            # Also check if the dimension pattern itself contains units (like "1 1/2\"ø")
                            has_units_in_dim = bool(re.search(r'["\']|ø|inch|in|ft|cm|mm', single_dim, re.IGNORECASE))
                            
                            # Only extract if:
                            # 1. It has units in the dimension itself, OR
                            # 2. It has dimension context in the line AND is not just a standalone number
                            if has_units_in_dim or (has_dimension_context and not is_standalone_number):
                                item_data['dimensions'] = single_dim
                            else:
                                # Standalone numbers without units are likely quantities, spec refs, or noise - skip
                                continue
                        has_indicators = True
                        break
        
        # Check for mounting types
        for pattern in self.mounting_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                item_data['mounting'] = match.group(0).strip()
                has_indicators = True
                break
        
        # Check for specs FIRST (do this BEFORE quantity check to properly categorize decimal references)
        # This ensures "31.1" goes to spec_reference, not quantity
        for pattern in self.spec_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups:
                    spec_str = ' '.join([g for g in groups if g]).strip()
                else:
                    spec_str = match.group(0).strip()
                
                if spec_str:
                    item_data['spec'] = spec_str
                    has_indicators = True
                    # If we found a decimal spec reference like "31.1", mark it so quantity extraction skips it
                    if '.' in spec_str and re.match(r'^\d+\.\d+$', spec_str):
                        item_data['_has_spec_decimal'] = True  # Internal flag to prevent quantity extraction
                        item_data['_spec_decimal_value'] = spec_str  # Store the value
                    break
        
        # FINAL VALIDATION: Check if this is actually an instruction/reference, not an item
        # Even if it passed earlier checks, verify it's not an instruction
        line_stripped = line.strip().upper()
        instruction_indicators = [
            line_stripped.startswith('UP TO'),
            line_stripped.startswith('SEE '),
            line_stripped.startswith('REFER '),
            line_stripped.startswith('USE '),
            line_stripped.startswith('INSTALL '),
            line_stripped.startswith('MOUNT '),
            line_stripped.startswith('CONNECT '),
            'SEE PAGE' in line_stripped,
            'SEE DRAWING' in line_stripped,
            'SEE SPEC' in line_stripped,
            'REFER TO' in line_stripped,
        ]
        if any(instruction_indicators):
            return None  # This is an instruction, not an item
        
        # Check if line is a drawing/line reference (e.g., "L01-MP-P.1A", "LINE 1", "DWG-123")
        # These are drawing references, not actual fixtures
        drawing_reference_patterns = [
            r'^[A-Z]\d+[-\.][A-Z]+[-\.]',  # L01-MP-P.1A, A123-DWG-1
            r'^LINE\s+\d+',  # LINE 1, LINE 2
            r'^DWG[-\.]\d+',  # DWG-123, DWG.456
            r'^[A-Z]+\d*[-\.]MP[-\.]',  # L01-MP-P.1A pattern
        ]
        if any(re.match(pattern, line_stripped) for pattern in drawing_reference_patterns):
            # This is a drawing/line reference, not a fixture
            # If the entire line is just the reference, extract it as spec_reference instead of fixture_type
            if line_stripped == line.strip().upper():
                # The whole line is the reference - treat it as spec, not fixture
                if not item_data.get('spec'):
                    item_data['spec'] = line.strip()
                # Clear fixture_type if it was incorrectly set
                if item_data.get('type') == line.strip():
                    item_data.pop('type', None)
                # Only keep if we have other meaningful data (model, quantity, dimensions)
                if not (item_data.get('model') or item_data.get('quantity') or item_data.get('dimensions')):
                    return None  # Skip pure drawing references without item data
            else:
                # Drawing reference is part of a larger line - only create item if it has strong indicators
                if not (item_data.get('model') and (item_data.get('quantity') or item_data.get('dimensions'))):
                    return None  # Skip drawing references without real item data
        
        # Require STRONG indicators - don't create items from noise
        # Need either: (1) valid fixture type, OR (2) quantity + model number, OR (3) model number + fixture context
        has_strong_indicators = False
        
        # Strong indicator 1: Valid fixture type found
        if item_data.get('type') and best_match:  # Had a real fixture match
            has_strong_indicators = True
        
        # Strong indicator 2: Both quantity and model number (actual item data)
        if item_data.get('quantity') and item_data.get('model'):
            has_strong_indicators = True
        
        # Strong indicator 3: Model number that looks valid + some other data (but NOT just dimensions)
        # A model number alone with dimensions isn't enough - need actual fixture context
        if item_data.get('model'):
            # Check if we have mounting, spec, or an actual fixture type (not just dimensions)
            has_context_beyond_dimensions = (
                item_data.get('mounting') or 
                item_data.get('spec') or 
                item_data.get('type')  # Actual fixture type, not inferred from dimensions
            )
            if has_context_beyond_dimensions:
                has_strong_indicators = True
            # OR: model number + quantity is strong indicator
            elif item_data.get('quantity'):
                has_strong_indicators = True
        
        # Strong indicator 4: Valid quantity pattern with units (not random numbers)
        if item_data.get('quantity'):
            # Check if quantity came from a pattern with units (more reliable)
            qty_match = re.search(r'\b(\d+)\s*(ea|each|pcs|pieces|qty|quantity)', line, re.IGNORECASE)
            if qty_match:
                has_strong_indicators = True
        
        # Only create item if we have strong indicators
        if has_strong_indicators:
            # If no fixture type but we have strong data, try to infer from line content
            if not item_data.get('type') and (item_data.get('quantity') or item_data.get('model')):
                # Extract first meaningful phrase as type (but be very careful)
                words = line.split()
                if words:
                    # Take first 2-3 words, but skip if it's all caps and very long (likely noise)
                    potential_type = ' '.join(words[:3]).strip()
                    
                    # CRITICAL: Check if this looks like a dimension (e.g., "0' - 7", "25' -1 5/8\"")
                    is_dimension = bool(re.search(r'\d+\s*["\']\s*[-–]?\s*\d+', potential_type))
                    # Check if it's just numbers/units (not a real fixture name)
                    is_numeric = bool(re.match(r'^[\d\s\'\"\-\/\.]+$', potential_type.strip()))
                    
                    # Additional validation: exclude common non-item phrases and dimensions
                    exclude_phrases = [
                        'OR USE', 'USE IN', 'IN WHOLE', 'IN PART', 'PROHIBITED',
                        'COPYRIGHT', 'ALL RIGHTS', 'RESERVED', 'CONFIDENTIAL',
                        'STRICTLY PROHIBITED', 'WITHOUT WRITTEN'
                    ]
                    if (any(phrase in potential_type.upper() for phrase in exclude_phrases) or 
                        is_dimension or is_numeric):
                        # Don't set fixture_type if it's clearly not a fixture name
                        # But still create the item if we have model number or quantity
                        pass  # Keep the item but without fixture_type
                    elif len(potential_type) < 40:  # Reasonable length
                        item_data['type'] = potential_type
            
            # Clean up: remove internal flags before returning
            item_data.pop('_has_spec_decimal', None)
            item_data.pop('_spec_decimal_value', None)
            
            # CRITICAL: If quantity is a spec reference (decimal like "31.1"), remove it from quantity
            # Spec references should ONLY be in spec_reference, not quantity
            if item_data.get('quantity') and item_data.get('spec_reference'):
                if str(item_data['quantity']) == str(item_data['spec_reference']):
                    # Same value in both - remove from quantity (keep in spec_reference)
                    item_data.pop('quantity', None)
            
            # Fix duplicate words in fixture_type if any
            if item_data.get('type'):
                words = item_data['type'].split()
                unique_words = []
                prev_word = None
                for word in words:
                    if word.upper() != prev_word:  # Skip if same as previous word
                        unique_words.append(word)
                        prev_word = word.upper()
                item_data['type'] = ' '.join(unique_words)
            
            return item_data
        
        # Don't create items from weak/no indicators
        return None
    
    def _enrich_item(self, item: Dict[str, Any], line: str):
        """Enrich an item with additional information from following lines."""
        # Add quantity if missing
        if not item.get('quantity'):
            for pattern in self.quantity_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        qty_str = match.group(1)
                        # Handle decimal quantities or take first number from comma-separated
                        if '.' in qty_str:
                            item['quantity'] = qty_str  # Keep as string for references like "31.1"
                        else:
                            item['quantity'] = int(qty_str)
                    except (ValueError, IndexError):
                        pass
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
        
        # Add dimensions if missing (try multiple patterns)
        # CRITICAL: Don't extract standalone numbers without units as dimensions
        if not item.get('dimensions'):
            for pattern in self.dimension_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    dims = match.groups()
                    # Format dimensions nicely
                    dim_parts = [d.strip() for d in dims if d and d.strip()]
                    if dim_parts:
                        # Join with 'x' for multiple dimensions, or keep single dimension
                        if len(dim_parts) > 1:
                            item['dimensions'] = ' x '.join(dim_parts)
                        else:
                            # Single dimension - CRITICAL: Only extract if it has units or dimension context
                            single_dim = dim_parts[0]
                            
                            # Skip standalone numbers without units (like "4", "6", "22")
                            is_standalone_number = bool(re.match(r'^\d+$', single_dim.strip()))
                            
                            # Check if dimension has units or context
                            has_units = bool(re.search(r'["\']|ø|inch|inches|in|ft|feet|cm|mm|diameter|dia', single_dim, re.IGNORECASE))
                            has_context = bool(re.search(r'(diameter|dia|OD|ID|inch|in|"|\'|ø|x\s*\d)', line, re.IGNORECASE))
                            
                            # Only set dimension if:
                            # 1. It has units in the dimension itself, OR
                            # 2. It has dimension context AND is NOT just a standalone number
                            if has_units or (has_context and not is_standalone_number):
                                item['dimensions'] = single_dim
                            # Otherwise skip - standalone numbers are not dimensions
                    break
        
        # Add mounting type if missing
        if not item.get('mounting_type'):
            for pattern in self.mounting_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    mounting = match.group(0).strip() if match.group(0) else match.group(1).strip() if match.groups() else ''
                    if mounting:
                        # Normalize mounting type
                        mounting = re.sub(r'[-\s]+', '-', mounting.lower())
                        mounting = mounting.replace('mounting', 'mount').replace('hung', 'mount')
                        item['mounting_type'] = mounting.title()
                    break
        
        # Add spec reference if missing (includes page references and decimal spec numbers like "31.1")
        if not item.get('spec_reference'):
            for pattern in self.spec_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Join all groups or use full match
                    groups = match.groups()
                    if groups:
                        spec_str = ' '.join([g for g in groups if g]).strip()
                    else:
                        spec_str = match.group(0).strip()
                    
                    if spec_str:
                        item['spec_reference'] = spec_str
                        # If it's a decimal spec reference like "31.1", store it
                        if '.' in spec_str and re.match(r'^\d+\.\d+$', spec_str):
                            item['spec_reference'] = spec_str  # Store decimal spec references
                    
                    # Also extract page reference if found
                    if 'page' in pattern.lower() or 'pg' in pattern.lower():
                        page_match = re.search(r'\d+', spec_str)
                        if page_match:
                            try:
                                item['page_number'] = int(page_match.group())
                            except:
                                pass
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
                
                # More flexible: add item if it has ANY meaningful data
                # Don't require fixture_type - tables may have model numbers, quantities, etc.
                if item.get('fixture_type') or item.get('quantity') or item.get('model_number'):
                    items.append(item)
                elif any(item.get(k) for k in ['dimensions', 'mounting_type', 'spec_reference']):
                    # If only other fields exist, still create item with first cell as type
                    if row and row[0]:
                        item['fixture_type'] = str(row[0]).strip()
                        items.append(item)
        
        return items

