"""
RequestBody Model - Request body specification
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from src.domain.core.models.Schema import Schema


@dataclass
class MediaTypeObject:
    """Media type content"""
    schema: Optional[Schema] = None
    example: Optional[dict] = None
    examples: Dict[str, dict] = field(default_factory=dict)


@dataclass
class RequestBody:
    """Request body specification"""
    description: Optional[str] = None
    content: Dict[str, MediaTypeObject] = field(default_factory=dict)
    required: bool = False

