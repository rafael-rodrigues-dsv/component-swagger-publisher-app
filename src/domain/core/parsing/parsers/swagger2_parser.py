"""
Swagger2Parser - Parser for OpenAPI 2.0 (Swagger) specifications
"""
from typing import Union
from src.domain.core.parsing.contracts.parser_contract import ParserContract
from src.domain.core.parsing.dtos.parsed_spec import ParsedSpec
from src.domain.utils.json_loader_utils import JsonLoaderUtils


class Swagger2Parser(ParserContract):
    """Parser for Swagger 2.0 specifications"""

    def parse(self, source: Union[str, dict]) -> ParsedSpec:
        """Parse Swagger 2.0 specification"""
        # Load the spec
        spec_dict = JsonLoaderUtils.load(source)

        # Validate version
        if not self.can_parse(spec_dict):
            raise ValueError(f"Not a valid Swagger 2.0 specification")

        # Get version
        version = spec_dict.get('swagger', '2.0')

        # Store source URL if applicable
        source_url = source if isinstance(source, str) and source.startswith('http') else None

        return ParsedSpec(
            version=version,
            raw_dict=spec_dict,
            refs={},  # TODO: Resolve $refs
            source_url=source_url
        )

    def can_parse(self, spec_dict: dict) -> bool:
        """Check if this is a Swagger 2.0 spec"""
        return 'swagger' in spec_dict and spec_dict['swagger'].startswith('2.')

    def get_version(self) -> str:
        """Get supported version"""
        return "2.0"




