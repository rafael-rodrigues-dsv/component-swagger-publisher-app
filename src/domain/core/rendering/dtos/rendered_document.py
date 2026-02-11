"""
RenderedDocument - DTO for rendered documentation
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RenderedDocument:
    """Rendered documentation output"""
    html_content: str
    xml_content: Optional[str] = None
    css_content: Optional[str] = None
    assets: Dict[str, str] = field(default_factory=dict)  # filename -> content
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.html_content:
            raise ValueError("RenderedDocument.html_content is required")




