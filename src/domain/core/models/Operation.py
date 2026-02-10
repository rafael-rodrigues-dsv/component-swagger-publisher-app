"""
Operation Model - HTTP Operation (GET, POST, etc.)
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from src.domain.core.models.parameter import Parameter
from src.domain.core.models.request_body import RequestBody
from src.domain.core.models.response import Response


@dataclass
class Operation:
    """HTTP Operation"""
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: Dict[str, Response] = field(default_factory=dict)
    deprecated: bool = False
    security: Optional[List[Dict[str, List[str]]]] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.method:
            raise ValueError("Operation.method is required")
        if not self.path:
            raise ValueError("Operation.path is required")
        if self.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']:
            raise ValueError(f"Invalid HTTP method: {self.method}")




