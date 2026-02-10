"""
HtmlRenderer - Renders API documentation as HTML
"""
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.domain.models.api_specification_model import ApiSpecificationModel
from src.domain.ports.rendering.documentation_renderer import DocumentationRenderer
from src.domain.ports.rendering.render_options import RenderOptions
from src.domain.ports.rendering.rendered_document import RenderedDocument
from src.domain.utils.example_generator_utils import ExampleGeneratorUtils


class HtmlRenderer(DocumentationRenderer):
    """Renders API documentation as responsive HTML"""

    def __init__(self, templates_dir: str = None):
        """Initialize renderer with templates directory"""
        if templates_dir is None:
            # Default to src/infrastructure/repository/templates/confluence
            # This file is in src/infrastructure/rendering/HtmlRenderer.py
            # We need to go up to infrastructure: ..
            base_dir = Path(__file__).parent.parent
            templates_dir = base_dir / "repository" / "templates" / "confluence"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

        # Add custom filters
        self.env.filters['tojson_pretty'] = lambda x: json.dumps(x, indent=2, ensure_ascii=False) if x else '{}'

    def render(self, spec: ApiSpecificationModel, options: RenderOptions = None) -> RenderedDocument:
        """Render API specification to HTML (Confluence preview)"""
        if options is None:
            options = RenderOptions()

        # Create example generator with available schemas
        schemas = {}
        if spec.components and spec.components.schemas:
            schemas = spec.components.schemas
        example_generator = ExampleGeneratorUtils(schemas)

        # Load Confluence-specific CSS
        css_path = self.templates_dir / "confluence-preview.css"
        css_content = ""
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        else:
            # Fallback to old styles.css if new one doesn't exist
            fallback_css = self.templates_dir / "styles.css"
            if fallback_css.exists():
                with open(fallback_css, 'r', encoding='utf-8') as f:
                    css_content = f.read()

        # Load Confluence preview template
        template_name = 'confluence-preview.html.j2'
        if not (self.templates_dir / template_name).exists():
            # Fallback to old template if new one doesn't exist
            template_name = 'index.html.j2'

        template = self.env.get_template(template_name)

        # Render HTML with Confluence-specific data
        html_content = template.render(
            api=spec,
            css_content=css_content,
            options=options,
            space_key='DDS',  # Using configured space key
            example_generator=example_generator,
            schemas=schemas
        )

        return RenderedDocument(
            html_content=html_content,
            css_content=css_content,
            metadata={
                'title': spec.info.title,
                'version': spec.info.version,
                'format': 'confluence-preview'
            }
        )

    def get_format_name(self) -> str:
        """Get format name"""
        return "html"




