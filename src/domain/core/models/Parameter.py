"""
Parameter Model - Operation parameters
"""
from dataclasses import dataclass
from typing import Optional, Any
from src.domain.core.models.Schema import Schema


@dataclass
class Parameter:
    """Parameter for operations"""
    name: str
    location: str  # query, header, path, cookie
    description: Optional[str] = None
    required: bool = False
    deprecated: bool = False
    allow_empty_value: bool = False

    # Schema
    schema: Optional[Schema] = None

    # Style
    style: Optional[str] = None
    explode: bool = False

    # Example
    example: Optional[Any] = None

    def __post_init__(self):
        """Validate required fields"""
        # If name is missing, use a placeholder instead of failing
        if not self.name:
            # Use a fallback name for malformed specs
            object.__setattr__(self, 'name', 'unnamed_parameter')

        # Swagger 2.0 includes 'body' and 'formData', OpenAPI 3.x uses 'query', 'header', 'path', 'cookie'
        valid_locations = ['query', 'header', 'path', 'cookie', 'body', 'formData']
        if self.location not in valid_locations:
            # Use 'query' as default for invalid locations
            object.__setattr__(self, 'location', 'query')

        if self.location == 'path' and not self.required:
            # Fix path parameters to be required
            object.__setattr__(self, 'required', True)

