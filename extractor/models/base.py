"""
Base models shared across all extraction modes.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Statistics(BaseModel):
    """Document statistics - shared across all extraction modes."""
    
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    total_characters: int = Field(..., ge=0, description="Total characters extracted")
    total_words: int = Field(..., ge=0, description="Total words extracted")
    avg_chars_per_page: float = Field(..., ge=0, description="Average characters per page")
    avg_words_per_page: float = Field(..., ge=0, description="Average words per page")


class PageInfo(BaseModel):
    """Basic page information - shared across all extraction modes."""
    
    page_num: int = Field(..., ge=1, description="Page number")
    text_preview: Optional[str] = Field(
        None,
        description="Preview of page text (first 200 chars)"
    )
    has_tables: bool = Field(
        False,
        description="Whether this page contains tables"
    )


class PageData(BaseModel):
    """Full page data including text and metadata - used in standard mode."""
    
    page_num: int = Field(..., ge=1, description="Page number")
    text: str = Field(default="", description="Full text content of the page")
    width: Optional[float] = Field(None, description="Page width in points")
    height: Optional[float] = Field(None, description="Page height in points")
    tables: Optional[List[List[List[Optional[str]]]]] = Field(
        default=None,
        description="Extracted tables (if any, cells may be null or empty strings)"
    )


class BaseExtractionResult(BaseModel):
    """Base model for all extraction results with common fields."""
    
    source_pdf: str = Field(..., description="Path to source PDF file")
    extraction_mode: str = Field(..., description="Extraction mode used")
    statistics: Statistics = Field(..., description="Document statistics")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Custom encoders if needed
        }

