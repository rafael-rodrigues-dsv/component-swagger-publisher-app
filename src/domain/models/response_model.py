"""
Response Model - Response specification
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
class ResponseModel:
    """Response specification"""
    description: str
    content: Dict[str, MediaTypeObjectModel] = field(default_factory=dict)
    headers: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.description:
            raise ValueError("ResponseModel.description is required")




