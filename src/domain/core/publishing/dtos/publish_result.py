"""
PublishResult - DTO for publishing result
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PublishResult:
    """Result of publishing operation"""
    success: bool
    output_paths: Dict[str, str] = field(default_factory=dict)  # type -> path
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None  # Published URL (for remote publishers)
    duration_seconds: float = 0.0




