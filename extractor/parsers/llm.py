"""
Optional LLM-based parsing for complex PDF extraction (GPT/Claude).
"""
import json
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class LLMParserBase(ABC):
    """Base class for LLM parsers."""
    
    @abstractmethod
    def parse(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Parse text using LLM with given schema."""
        pass


class OpenAIParser(LLMParserBase):
    """Parse PDF text using OpenAI GPT models."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI parser.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4o-mini - cheaper and widely available)
                   Options: gpt-4o-mini, gpt-4o, gpt-3.5-turbo, gpt-4-turbo
        """
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("OpenAI library required. Install with: pip install openai")
    
    def parse(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse text using OpenAI with structured output.
        
        Args:
            text: Text to parse
            schema: JSON schema for desired output structure
            
        Returns:
            Parsed data matching the schema
        """
        prompt = f"""You are an expert at extracting structured data from construction PDF documents (plumbing submittals, mechanical plans, work packages).

Your task is to extract construction items, fixtures, and equipment with:
- Item/Fixture Types (e.g., "Valve Package", "Circulating Pump", "Eye Wash Station", "Body Repair Shop Fixtures")
- Quantities (can be integers like 31 or references like "31.1, 31")
- Model Numbers / Spec References (e.g., "OM-141", "HUH-13", "30.1", "BOILER CIRCULATING PUMP")
- Page References (if available in text)
- Associated Dimensions (e.g., "1 1/2\"ø", "2 x 4 x 6")
- Mounting Type (e.g., "wall-mounted", "floor-mounted")

IMPORTANT INSTRUCTIONS:
1. Extract ALL construction items, equipment, and fixtures mentioned
2. Look for items in tables, lists, and free text
3. Handle abbreviations (e.g., "HHWS" = Heating Hot Water Supply, "CWR" = Cooling Water Return)
4. Extract quantities even if formatted as references (like "31.1, 31")
5. Model numbers can be in various formats: OM-141, HUH-13, 30.1, or descriptive like "BOILER CIRCULATING PUMP"
6. If quantity is a reference like "31.1, 31", keep it as string
7. Be thorough - extract items from tables, notes, and descriptions
8. Include context from surrounding text to identify complete item descriptions

Document Text:
{text}

Extract all construction items according to this schema:
{json.dumps(schema, indent=2)}

Return a JSON object with an "items" array containing all extracted items."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert construction document analyst specializing in extracting structured data from plumbing, mechanical, and construction PDFs. You understand construction terminology, abbreviations, and specifications."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class ClaudeParser(LLMParserBase):
    """Parse PDF text using Anthropic Claude models."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize Claude parser.
        
        Args:
            api_key: Anthropic API key
            model: Model name to use
        """
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Anthropic library required. Install with: pip install anthropic")
    
    def parse(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse text using Claude with structured output.
        
        Args:
            text: Text to parse
            schema: JSON schema for desired output structure
            
        Returns:
            Parsed data matching the schema
        """
        prompt = f"""You are an expert at extracting structured data from construction PDF documents (plumbing submittals, mechanical plans, work packages).

Your task is to extract construction items, fixtures, and equipment with:
- Item/Fixture Types (e.g., "Valve Package", "Circulating Pump", "Eye Wash Station", "Body Repair Shop Fixtures")
- Quantities (can be integers like 31 or references like "31.1, 31")
- Model Numbers / Spec References (e.g., "OM-141", "HUH-13", "30.1", "BOILER CIRCULATING PUMP")
- Page References (if available in text)
- Associated Dimensions (e.g., "1 1/2\"ø", "2 x 4 x 6")
- Mounting Type (e.g., "wall-mounted", "floor-mounted")

IMPORTANT INSTRUCTIONS:
1. Extract ALL construction items, equipment, and fixtures mentioned
2. Look for items in tables, lists, and free text
3. Handle abbreviations (e.g., "HHWS" = Heating Hot Water Supply, "CWR" = Cooling Water Return)
4. Extract quantities even if formatted as references (like "31.1, 31")
5. Model numbers can be in various formats: OM-141, HUH-13, 30.1, or descriptive like "BOILER CIRCULATING PUMP"
6. If quantity is a reference like "31.1, 31", keep it as string
7. Be thorough - extract items from tables, notes, and descriptions
8. Include context from surrounding text to identify complete item descriptions

Document Text:
{text}

Extract all construction items according to this schema:
{json.dumps(schema, indent=2)}

Return a JSON object with an "items" array containing all extracted items."""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        return json.loads(response_text)

