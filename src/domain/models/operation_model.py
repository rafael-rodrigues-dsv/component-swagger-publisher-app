"""
Operation Model - HTTP Operation (GET, POST, etc.)
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from src.domain.models.parameter_model import ParameterModel
from src.domain.models.request_body_model import RequestBodyModel
from src.domain.models.response_model import ResponseModel


@dataclass
class OperationModel:
    """HTTP Operation"""
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[ParameterModel] = field(default_factory=list)
    request_body: Optional[RequestBodyModel] = None
    responses: Dict[str, ResponseModel] = field(default_factory=dict)
    deprecated: bool = False
    security: Optional[List[Dict[str, List[str]]]] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.method:
            raise ValueError("OperationModel.method is required")
        if not self.path:
            raise ValueError("OperationModel.path is required")
        if self.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']:
            raise ValueError(f"Invalid HTTP method: {self.method}")




