"""
PublishingService - Main orchestration service
"""
from pathlib import Path
from src.domain.models.api_specification_model import ApiSpecificationModel
from src.domain.ports.parsing.parsed_spec import ParsedSpec
from src.domain.ports.rendering.render_options import RenderOptions
from src.domain.ports.publishing.publish_target import PublishTarget
from src.domain.ports.publishing.publish_result import PublishResult
from src.infrastructure.parsing.parser_factory import ParserFactory
from src.domain.utils.domain_mapper_utils import DomainMapperUtils
from src.infrastructure.rendering.html_renderer import HtmlRenderer
from src.infrastructure.publishing.publisher_factory import PublisherFactory


class PublishingService:
    """Main service to orchestrate the publishing process"""

    def __init__(self):
        self.html_renderer = HtmlRenderer()

    def publish_documentation(
        self,
        source_url: str,
        publisher_type: str = 'confluence',
        output_dir: str = None,
        mode: str = 'preview'
    ) -> PublishResult:
        """
        Main method to publish API documentation

        Args:
            source_url: URL or path to OpenAPI spec
            publisher_type: Type of publisher (default: confluence)
            output_dir: Output directory (default: output/publisher/{publisher_type})
            mode: 'preview' for local preview or 'publish' for real publication

        Returns:
            PublishResult: Result of publishing
        """
        try:
            # 1. Parse specification
            parser = ParserFactory.get_parser(source_url)
            parsed_spec = parser.parse(source_url)

            # 2. Map to domain model
            api_spec = DomainMapperUtils.to_domain(parsed_spec)

            # 3. Render HTML
            render_options = RenderOptions(
                theme='light',
                responsive=True,
                include_examples=True
            )
            rendered_doc = self.html_renderer.render(api_spec, render_options)

            # Add API specification to metadata for publisher to use
            rendered_doc.metadata['api_spec'] = api_spec

            # 4. Prepare publish target
            if output_dir is None:
                base_dir = Path.cwd()
                output_dir = base_dir / "output" / "publisher" / publisher_type

            target = PublishTarget(
                publisher_type=publisher_type,
                output_path=str(output_dir),
                title=api_spec.info.title,
                labels=[tag.name for tag in api_spec.tags] + [api_spec.info.version]
            )

            # 5. Publish
            publisher = PublisherFactory.get_publisher(publisher_type, mode)
            result = publisher.publish(rendered_doc, target)

            return result

        except Exception as e:
            return PublishResult(
                success=False,
                errors=[f"Publishing failed: {str(e)}"]
            )

    def get_api_info(self, source_url: str) -> dict:
        """
        Extract API information without publishing

        Args:
            source_url: URL or path to OpenAPI spec

        Returns:
            dict: API information (title, version, description, etc.)
        """
        try:
            parser = ParserFactory.get_parser(source_url)
            parsed_spec = parser.parse(source_url)
            api_spec = DomainMapperUtils.to_domain(parsed_spec)

            return {
                'title': api_spec.info.title,
                'version': api_spec.info.version,
                'description': api_spec.info.description,
                'openapi_version': api_spec.openapi_version,
                'servers': [s.url for s in api_spec.servers],
                'tags': [t.name for t in api_spec.tags],
                'endpoint_count': len([op for path in api_spec.paths.values() for op in path.operations.values()])
            }
        except Exception as e:
            return {'error': str(e)}




