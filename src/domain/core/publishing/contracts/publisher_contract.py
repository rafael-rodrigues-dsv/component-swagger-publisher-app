"""
PublisherContract - Interface for publishing documentation
"""
from abc import ABC, abstractmethod
from src.domain.core.rendering.dtos.rendered_document import RenderedDocument
from src.domain.core.publishing.dtos.publish_target import PublishTarget
from src.domain.core.publishing.dtos.publish_result import PublishResult


class PublisherContract(ABC):
    """Abstract publisher for documentation"""

    @abstractmethod
    def publish(self, document: RenderedDocument, target: PublishTarget) -> PublishResult:
        """
        Publish rendered documentation to target

        Args:
            document: Rendered documentation
            target: Publishing target configuration

        Returns:
            PublishResult: Result of publishing

        Raises:
            Exception: If publishing fails
        """
        pass

    @abstractmethod
    def get_publisher_type(self) -> str:
        """
        Get the publisher type

        Returns:
            str: Publisher type (e.g., "confluence", "github-pages")
        """
        pass

    @abstractmethod
    def validate_target(self, target: PublishTarget) -> bool:
        """
        Validate publishing target configuration

        Args:
            target: Publishing target

        Returns:
            bool: True if valid, False otherwise
        """
        pass




