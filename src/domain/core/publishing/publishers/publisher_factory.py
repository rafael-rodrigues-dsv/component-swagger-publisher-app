"""
PublisherFactory - Factory to get appropriate publisher
"""
from src.domain.core.publishing.contracts.publisher_contract import PublisherContract
from src.domain.core.publishing.publishers.confluence_preview_publisher import ConfluencePreviewPublisher
from src.domain.core.publishing.publishers.confluence_publisher import ConfluencePublisher


class PublisherFactory:
    """Factory for getting publishers"""

    @staticmethod
    def get_publisher(publisher_type: str, mode: str = 'preview') -> PublisherContract:
        """
        Get publisher by type and mode

        Args:
            publisher_type: Type of publisher (confluence, github-pages, etc.)
            mode: 'preview' for local preview or 'publish' for real publication

        Returns:
            Publisher: Appropriate publisher

        Raises:
            ValueError: If publisher type is not supported
        """
        if publisher_type.lower() == 'confluence':
            if mode == 'publish':
                return ConfluencePublisher()  # Real Confluence publisher
            else:
                return ConfluencePreviewPublisher()  # Preview mode (default)

        raise ValueError(f"Unsupported publisher type: {publisher_type}")

    @staticmethod
    def get_available_publishers():
        """Get list of available publishers"""
        return ['confluence']




