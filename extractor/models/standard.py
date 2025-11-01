"""
Models specific to standard text extraction mode.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator

from .base import BaseExtractionResult, PageData


class ExtractedEntities(BaseModel):
    """Model for extracted entities in standard mode."""
    
    email: Optional[List[str]] = Field(default_factory=list, description="Extracted email addresses")
    phone: Optional[List[str]] = Field(default_factory=list, description="Extracted phone numbers")
    date: Optional[List[str]] = Field(default_factory=list, description="Extracted dates")
    currency: Optional[List[str]] = Field(default_factory=list, description="Extracted currency amounts")
    url: Optional[List[str]] = Field(default_factory=list, description="Extracted URLs")
    ssn: Optional[List[str]] = Field(default_factory=list, description="Extracted SSNs")
    
    @classmethod
    def from_dict(cls, entities_dict: Dict[str, List[str]]):
        """Create ExtractedEntities from dictionary."""
        # Only include fields that exist in the model
        valid_fields = {k: v for k, v in entities_dict.items() if k in cls.__fields__}
        return cls(**valid_fields)


class StandardExtractionResult(BaseExtractionResult):
    """Standard text extraction result."""
    
    extraction_mode: str = Field(
        default="standard",
        description="Extraction mode"
    )
    pages: List[PageData] = Field(
        default_factory=list,
        description="Full page data"
    )
    full_text: str = Field(
        default="",
        description="Combined text from all pages"
    )
    entities: ExtractedEntities = Field(
        default_factory=ExtractedEntities,
        description="Extracted entities (emails, phones, dates, etc.)"
    )
    
    @validator('pages', pre=True)
    def validate_pages(cls, v):
        """Ensure all pages are valid PageData instances."""
        if not isinstance(v, list):
            return []
        validated = []
        for page in v:
            if isinstance(page, PageData):
                validated.append(page)
            elif isinstance(page, dict):
                # Convert dict to PageData model
                validated.append(PageData(**page))
            else:
                # Skip invalid entries
                continue
        return validated
    
    @validator('entities', pre=True)
    def validate_entities(cls, v):
        """Ensure entities are properly formatted."""
        if isinstance(v, dict):
            return ExtractedEntities.from_dict(v)
        return v if isinstance(v, ExtractedEntities) else ExtractedEntities()

