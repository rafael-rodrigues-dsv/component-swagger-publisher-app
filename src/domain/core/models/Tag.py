"""
Tag Model - Groups operations logically
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tag:
    """Tag for grouping operations"""
    name: str
    description: Optional[str] = None
    external_docs: Optional[dict] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.name:
            raise ValueError("Tag.name is required")

