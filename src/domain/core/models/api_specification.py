"""
ApiSpecification Model - Root canonical model
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.domain.core.models.info import Info
from src.domain.core.models.server import Server
from src.domain.core.models.path_item import PathItem
from src.domain.core.models.tag import Tag
from src.domain.core.models.security_scheme import SecurityScheme
from src.domain.core.models.schema import Schema


@dataclass
class Components:
    """Reusable components"""
    schemas: Dict[str, Schema] = field(default_factory=dict)
    security_schemes: Dict[str, SecurityScheme] = field(default_factory=dict)
    responses: Dict[str, dict] = field(default_factory=dict)
    parameters: Dict[str, dict] = field(default_factory=dict)
    examples: Dict[str, dict] = field(default_factory=dict)
    request_bodies: Dict[str, dict] = field(default_factory=dict)
    headers: Dict[str, dict] = field(default_factory=dict)


@dataclass
class ApiSpecification:
    """Root canonical API specification model"""
    openapi_version: str  # Original version (2.0, 3.0.0, 3.1.0, etc.)
    info: Info
    servers: List[Server] = field(default_factory=list)
    paths: Dict[str, PathItem] = field(default_factory=dict)
    components: Components = field(default_factory=Components)
    tags: List[Tag] = field(default_factory=list)
    security: Optional[List[Dict[str, List[str]]]] = None
    external_docs: Optional[dict] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.openapi_version:
            raise ValueError("ApiSpecification.openapi_version is required")
        if not self.info:
            raise ValueError("ApiSpecification.info is required")

    def get_all_operations(self):
        """Get all operations from all paths"""
        operations = []
        for path_item in self.paths.values():
            for operation in path_item.operations.values():
                operations.append(operation)
        return operations

    def get_operations_by_tag(self, tag_name: str):
        """Get operations filtered by tag"""
        operations = []
        for operation in self.get_all_operations():
            if tag_name in operation.tags:
                operations.append(operation)
        return operations




