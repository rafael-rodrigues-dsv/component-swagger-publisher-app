"""
PathItem Model - Path with operations
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from src.domain.models.operation_model import OperationModel
from src.domain.models.parameter_model import ParameterModel


@dataclass
class PathItemModel:
    """Path with operations"""
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operations: Dict[str, OperationModel] = field(default_factory=dict)  # method -> Operation
    parameters: List[ParameterModel] = field(default_factory=list)  # Common parameters

    def __post_init__(self):
        """Validate required fields"""
        if not self.path:
            raise ValueError("PathItemModel.path is required")

    def get_operation(self, method: str) -> Optional[OperationModel]:
        """Get operation by HTTP method"""
        return self.operations.get(method.upper())

    def add_operation(self, method: str, operation: OperationModel):
        """Add operation"""
        self.operations[method.upper()] = operation




