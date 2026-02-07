"""
RenderOptions - Configuration for rendering
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RenderOptions:
    """Options for rendering documentation"""
    theme: str = "light"
    locale: str = "en-US"
    include_toc: bool = True
    include_examples: bool = True
    include_schemas: bool = True
    syntax_highlight: bool = True
    responsive: bool = True

