"""
RequestBody Model - Request body specification
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from src.domain.models.schema_model import SchemaModel


@dataclass
class MediaTypeObjectModel:
    """Media type content"""
    schema: Optional[SchemaModel] = None
    example: Optional[dict] = None
    examples: Dict[str, dict] = field(default_factory=dict)


@dataclass
class RequestBodyModel:
    """Request body specification"""
    description: Optional[str] = None
    content: Dict[str, MediaTypeObjectModel] = field(default_factory=dict)
    required: bool = False




