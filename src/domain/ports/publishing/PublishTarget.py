"""
PublishTarget - DTO for publish configuration
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PublishTarget:
    """Configuration for publishing target"""
    publisher_type: str  # confluence, github-pages, etc.
    output_path: str
    title: Optional[str] = None
    labels: Optional[list] = None
    space_key: Optional[str] = None  # For Confluence
    parent_page_id: Optional[str] = None  # For Confluence

