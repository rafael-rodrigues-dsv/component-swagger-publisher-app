"""
OpenApi3Parser - Parser for OpenAPI 3.x specifications
"""
from typing import Union, Dict, Any
from src.domain.ports.parsing.OpenApiParser import OpenApiParser
from src.domain.ports.parsing.ParsedSpec import ParsedSpec
from src.domain.utils.JsonLoader import JsonLoader


class OpenApi3Parser(OpenApiParser):
    """Parser for OpenAPI 3.x specifications"""

    def parse(self, source: Union[str, dict]) -> ParsedSpec:
        """Parse OpenAPI 3.x specification"""
        # Load the spec
        spec_dict = JsonLoader.load(source)

        # Validate version
        if not self.can_parse(spec_dict):
            raise ValueError(f"Not a valid OpenAPI 3.x specification")

        # Get version
        version = spec_dict.get('openapi', '3.0.0')

        # Store source URL if applicable
        source_url = source if isinstance(source, str) and source.startswith('http') else None

        return ParsedSpec(
            version=version,
            raw_dict=spec_dict,
            refs={},  # TODO: Resolve $refs
            source_url=source_url
        )

    def can_parse(self, spec_dict: dict) -> bool:
        """Check if this is an OpenAPI 3.x spec"""
        return 'openapi' in spec_dict and spec_dict['openapi'].startswith('3.')

    def get_version(self) -> str:
        """Get supported version"""
        return "3.0"

