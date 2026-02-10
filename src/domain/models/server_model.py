"""
Server Model - API Server/Endpoint configuration
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class ServerVariableModel:
    """Server variable with possible values"""
    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class ServerModel:
    """API Server/Endpoint"""
    url: str
    description: Optional[str] = None
    variables: Dict[str, ServerVariableModel] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.url:
            raise ValueError("ServerModel.url is required")




