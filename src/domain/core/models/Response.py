"""
Response Model - Response specification
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from src.domain.core.models.schema import Schema


@dataclass
class MediaTypeObject:
    """Media type content"""
    schema: Optional[Schema] = None
    example: Optional[dict] = None
    examples: Dict[str, dict] = field(default_factory=dict)


@dataclass
class Response:
    """Response specification"""
    description: str
    content: Dict[str, MediaTypeObject] = field(default_factory=dict)
    headers: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.description:
            raise ValueError("Response.description is required")




