"""
ParsedSpec - Intermediate DTO from parsers
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ParsedSpec:
    """Intermediate parsed specification"""
    version: str  # OpenAPI version (2.0, 3.0.0, 3.1.0, etc.)
    raw_dict: Dict[str, Any]  # Original parsed dict
    refs: Dict[str, Any]  # Resolved references
    source_url: Optional[str] = None  # Source URL if loaded from URL

    def __post_init__(self):
        """Validate required fields"""
        if not self.version:
            raise ValueError("ParsedSpec.version is required")
        if not self.raw_dict:
            raise ValueError("ParsedSpec.raw_dict is required")




