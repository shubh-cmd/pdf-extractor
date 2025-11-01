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
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI parser.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
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
        prompt = f"""Extract structured data from the following text according to the provided schema.

Text:
{text}

Schema:
{json.dumps(schema, indent=2)}

Return a JSON object matching the schema."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
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
        prompt = f"""Extract structured data from the following text according to the provided schema.

Text:
{text}

Schema:
{json.dumps(schema, indent=2)}

Return a JSON object matching the schema."""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        return json.loads(response_text)

