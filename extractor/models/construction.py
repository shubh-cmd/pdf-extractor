"""
Models specific to construction PDF extraction mode.
"""
from typing import Optional, List, Union
from pydantic import BaseModel, Field, validator

from .base import BaseExtractionResult, PageInfo


class ExtractedItem(BaseModel):
    """Model for a single extracted construction item."""
    
    fixture_type: Optional[str] = Field(
        None,
        description="Type of fixture/item (e.g., pipe, fitting, valve, sink)"
    )
    quantity: Optional[Union[int, str]] = Field(
        None,
        description="Quantity of the item (can be integer or string for references like '31.1, 31')"
    )
    model_number: Optional[str] = Field(
        None,
        description="Model number, part number, SKU, or catalog number"
    )
    dimensions: Optional[str] = Field(
        None,
        description="Dimensions (e.g., '2 x 4 x 6', '3 inches diameter')"
    )
    mounting_type: Optional[str] = Field(
        None,
        description="Mounting type (e.g., wall-hung, floor-mounted, recessed)"
    )
    spec_reference: Optional[str] = Field(
        None,
        description="Specification reference (e.g., ASTM D2665, ANSI standard)"
    )
    page_number: int = Field(
        ...,
        description="Page number where this item was found",
        ge=1
    )
    table_number: Optional[int] = Field(
        None,
        description="Table number if item was extracted from a table",
        ge=1
    )
    row_number: Optional[int] = Field(
        None,
        description="Row number in table if applicable",
        ge=1
    )
    raw_text: Optional[str] = Field(
        None,
        description="Original text line where this item was found"
    )
    line_number: Optional[int] = Field(
        None,
        description="Line number in page text",
        ge=1
    )
    
    @validator('fixture_type', pre=True)
    def clean_fixture_type(cls, v):
        """Clean and normalize fixture type."""
        if v:
            return v.strip()
        return v
    
    @validator('quantity', pre=True)
    def clean_quantity(cls, v):
        """Clean quantity - accept int or string for references."""
        if v is None:
            return None
        # If it's already an int, return as is
        if isinstance(v, int):
            return v
        # If it's a string, try to parse as int first
        if isinstance(v, str):
            v = v.strip()
            # If it contains decimals or commas (like "31.1, 31"), keep as string
            if '.' in v or ',' in v:
                return v
            # Otherwise try to convert to int
            try:
                return int(v)
            except ValueError:
                return v  # Keep as string if can't parse
        return v
    
    @validator('model_number', pre=True)
    def clean_model_number(cls, v):
        """Clean model number."""
        if v:
            return v.strip().upper()
        return v
    
    @validator('dimensions', pre=True)
    def clean_dimensions(cls, v):
        """Clean dimensions string."""
        if v:
            return v.strip()
        return v


class ConstructionExtractionSummary(BaseModel):
    """Summary statistics specific to construction extraction."""
    
    total_items: int = Field(..., ge=0, description="Total number of items extracted")
    items_with_quantities: int = Field(
        ..., ge=0, description="Number of items that have quantities"
    )
    items_with_model_numbers: int = Field(
        ..., ge=0, description="Number of items that have model numbers"
    )
    items_with_dimensions: int = Field(
        ..., ge=0, description="Number of items that have dimensions"
    )
    items_with_mounting_type: int = Field(
        ..., ge=0, description="Number of items that have mounting type"
    )
    pages_processed: int = Field(..., ge=1, description="Total number of pages processed")
    tables_found: int = Field(..., ge=0, description="Total number of tables found")


class ConstructionExtractionResult(BaseExtractionResult):
    """Complete construction PDF extraction result."""
    
    extraction_mode: str = Field(
        default="construction_takeoff",
        description="Extraction mode used"
    )
    total_items_found: int = Field(..., ge=0, description="Total items extracted")
    items: List[ExtractedItem] = Field(
        default_factory=list,
        description="List of extracted construction items"
    )
    summary: ConstructionExtractionSummary = Field(
        ...,
        description="Construction-specific extraction summary statistics"
    )
    pages: List[PageInfo] = Field(
        default_factory=list,
        description="Page information"
    )
    
    @validator('items', pre=True)
    def validate_items(cls, v):
        """Ensure all items are valid ExtractedItem instances."""
        if not isinstance(v, list):
            return []
        return [
            ExtractedItem(**item) if isinstance(item, dict) else item
            for item in v
        ]


# Type alias for backward compatibility
ExtractionSummary = ConstructionExtractionSummary

