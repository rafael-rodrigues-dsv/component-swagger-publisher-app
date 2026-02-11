"""
RendererContract - Interface for rendering documentation
"""
from abc import ABC, abstractmethod
from src.domain.models.api_specification_model import ApiSpecificationModel
from src.domain.core.rendering.dtos.render_options_dto import RenderOptionsDTO
from src.domain.core.rendering.dtos.rendered_document_dto import RenderedDocumentDTO


class RendererContract(ABC):
    """Abstract renderer for documentation"""

    @abstractmethod
    def render(self, spec: ApiSpecificationModel, options: RenderOptionsDTO = None) -> RenderedDocumentDTO:
        """
        Render API specification to documentation format

        Args:
            spec: API specification
            options: Rendering options

        Returns:
            RenderedDocumentDTO: Rendered documentation

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




