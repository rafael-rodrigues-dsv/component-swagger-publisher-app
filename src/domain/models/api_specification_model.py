"""
ApiSpecification Model - Root canonical model
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.domain.models.info_model import InfoModel
from src.domain.models.server_model import ServerModel
from src.domain.models.path_item_model import PathItemModel
from src.domain.models.tag_model import TagModel
from src.domain.models.security_scheme_model import SecuritySchemeModel
from src.domain.models.schema_model import SchemaModel


@dataclass
class ComponentsModel:
    """Reusable components"""
    schemas: Dict[str, SchemaModel] = field(default_factory=dict)
    security_schemes: Dict[str, SecuritySchemeModel] = field(default_factory=dict)
    responses: Dict[str, dict] = field(default_factory=dict)
    parameters: Dict[str, dict] = field(default_factory=dict)
    examples: Dict[str, dict] = field(default_factory=dict)
    request_bodies: Dict[str, dict] = field(default_factory=dict)
    headers: Dict[str, dict] = field(default_factory=dict)


@dataclass
class ApiSpecificationModel:
    """Root canonical API specification model"""
    openapi_version: str  # Original version (2.0, 3.0.0, 3.1.0, etc.)
    info: InfoModel
    servers: List[ServerModel] = field(default_factory=list)
    paths: Dict[str, PathItemModel] = field(default_factory=dict)
    components: ComponentsModel = field(default_factory=ComponentsModel)
    tags: List[TagModel] = field(default_factory=list)
    security: Optional[List[Dict[str, List[str]]]] = None
    external_docs: Optional[dict] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.openapi_version:
            raise ValueError("ApiSpecificationModel.openapi_version is required")
        if not self.info:
            raise ValueError("ApiSpecificationModel.info is required")

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




