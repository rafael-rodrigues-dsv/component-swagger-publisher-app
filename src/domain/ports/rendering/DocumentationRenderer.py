"""
DocumentationRenderer - Interface for rendering documentation
"""
from abc import ABC, abstractmethod
from src.domain.core.models.ApiSpecification import ApiSpecification
from src.domain.ports.rendering.RenderOptions import RenderOptions
from src.domain.ports.rendering.RenderedDocument import RenderedDocument


class DocumentationRenderer(ABC):
    """Abstract renderer for documentation"""

    @abstractmethod
    def render(self, spec: ApiSpecification, options: RenderOptions = None) -> RenderedDocument:
        """
        Render API specification to documentation format

        Args:
            spec: API specification
            options: Rendering options

        Returns:
            RenderedDocument: Rendered documentation

        Raises:
            Exception: If rendering fails
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """
        Get the format name this renderer produces

        Returns:
            str: Format name (e.g., "html", "confluence-xml")
        """
        pass

