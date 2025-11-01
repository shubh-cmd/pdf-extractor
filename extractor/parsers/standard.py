"""
Regex and heuristic parsing rules for extracted PDF text.
"""
import re
from typing import List, Dict, Optional, Pattern


class ParserRules:
    """Regex patterns and heuristic rules for parsing PDF text."""
    
    def __init__(self):
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            'date': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
            'currency': re.compile(r'\$[\d,]+\.?\d*'),
            'url': re.compile(r'https?://[^\s]+'),
            'ssn': re.compile(r'\d{3}-\d{2}-\d{4}'),
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using regex patterns.
        
        Args:
            text: Text to parse
            
        Returns:
            Dictionary mapping entity types to lists of matches
        """
        entities = {}
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = matches
        return entities
    
    def parse_structured_data(self, text: str, rules: Optional[Dict[str, Pattern]] = None) -> Dict:
        """
        Parse structured data from text using custom rules.
        
        Args:
            text: Text to parse
            rules: Optional custom regex patterns
            
        Returns:
            Dictionary of parsed data
        """
        if rules:
            patterns = {**self.patterns, **rules}
        else:
            patterns = self.patterns
        
        results = self.extract_entities(text)
        results['raw_text'] = text
        results['word_count'] = len(text.split())
        results['line_count'] = len(text.split('\n'))
        
        return results
    
    def find_key_value_pairs(self, text: str, separator: str = ':') -> Dict[str, str]:
        """
        Extract key-value pairs from text.
        
        Args:
            text: Text to parse
            separator: Character(s) that separate keys from values
            
        Returns:
            Dictionary of key-value pairs
        """
        pairs = {}
        lines = text.split('\n')
        
        for line in lines:
            if separator in line:
                parts = line.split(separator, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value:
                        pairs[key] = value
        
        return pairs

