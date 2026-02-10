"""
PathItem Model - Path with operations
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from src.domain.core.models.operation import Operation
from src.domain.core.models.parameter import Parameter


@dataclass
class PathItem:
    """Path with operations"""
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operations: Dict[str, Operation] = field(default_factory=dict)  # method -> Operation
    parameters: List[Parameter] = field(default_factory=list)  # Common parameters

    def __post_init__(self):
        """Validate required fields"""
        if not self.path:
            raise ValueError("PathItem.path is required")

    def get_operation(self, method: str) -> Optional[Operation]:
        """Get operation by HTTP method"""
        return self.operations.get(method.upper())

    def add_operation(self, method: str, operation: Operation):
        """Add operation"""
        self.operations[method.upper()] = operation




