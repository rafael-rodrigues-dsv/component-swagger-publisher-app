"""
Server Model - API Server/Endpoint configuration
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class ServerVariable:
    """Server variable with possible values"""
    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class Server:
    """API Server/Endpoint"""
    url: str
    description: Optional[str] = None
    variables: Dict[str, ServerVariable] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.url:
            raise ValueError("Server.url is required")

