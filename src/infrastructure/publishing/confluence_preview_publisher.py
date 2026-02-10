"""
ConfluencePreviewPublisher - Saves documentation locally as preview
"""
from pathlib import Path
from datetime import datetime
from src.domain.ports.publishing.publisher import Publisher
from src.domain.ports.rendering.rendered_document import RenderedDocument
from src.domain.ports.publishing.publish_target import PublishTarget
from src.domain.ports.publishing.publish_result import PublishResult


class ConfluencePreviewPublisher(Publisher):
    """Publisher for Confluence preview (local HTML generation)"""

    def publish(self, document: RenderedDocument, target: PublishTarget) -> PublishResult:
        """
        Save documentation locally as HTML preview

        Args:
            document: Rendered documentation
            target: Publishing target

        Returns:
            PublishResult: Result with file paths
        """
        start_time = datetime.now()
        output_paths = {}
        warnings = []

        try:
            # Create output directory
            output_dir = Path(target.output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save HTML
            html_path = output_dir / "index.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(document.html_content)
            output_paths['html'] = str(html_path.absolute())

            # Save XML if available
            if document.xml_content:
                xml_path = output_dir / "index.xml"
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(document.xml_content)
                output_paths['xml'] = str(xml_path.absolute())

            # Save CSS separately if needed
            if document.css_content:
                css_path = output_dir / "styles.css"
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(document.css_content)
                output_paths['css'] = str(css_path.absolute())

            # Save assets
            if document.assets:
                assets_dir = output_dir / "assets"
                assets_dir.mkdir(exist_ok=True)
                for asset_name, asset_content in document.assets.items():
                    asset_path = assets_dir / asset_name
                    with open(asset_path, 'w', encoding='utf-8') as f:
                        f.write(asset_content)

            duration = (datetime.now() - start_time).total_seconds()

            return PublishResult(
                success=True,
                output_paths=output_paths,
                warnings=warnings,
                metadata={
                    'publisher': 'confluence',
                    'mode': 'local_preview',
                    'title': document.metadata.get('title', 'API Documentation')
                },
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return PublishResult(
                success=False,
                output_paths=output_paths,
                errors=[str(e)],
                duration_seconds=duration
            )

    def get_publisher_type(self) -> str:
        """Get publisher type"""
        return "confluence-preview"

    def validate_target(self, target: PublishTarget) -> bool:
        """Validate target configuration"""
        if not target.output_path:
            return False
        return True




