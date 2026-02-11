"""
ParserFactory - Factory to select appropriate parser
"""
from typing import Union
from src.domain.core.parsing.contracts.parser_contract import ParserContract
from src.domain.utils.json_loader_utils import JsonLoaderUtils
from src.domain.core.parsing.parsers.swagger2_parser import Swagger2Parser
from src.domain.core.parsing.parsers.open_api3_parser import OpenApi3Parser


class ParserFactory:
    """Factory for selecting the right parser"""

    @staticmethod
    def get_parser(source: Union[str, dict]) -> ParserContract:
        """
        Get appropriate parser for the specification

        Args:
            source: URL, file path, or dict

        Returns:
            OpenApiParser: Appropriate parser

        Raises:
            ValueError: If no parser can handle the spec
        """
        # Load spec to detect version
        spec_dict = JsonLoaderUtils.load(source)

        # Try parsers
        parsers = [Swagger2Parser(), OpenApi3Parser()]

        for parser in parsers:
            if parser.can_parse(spec_dict):
                return parser

        raise ValueError("No parser found for this specification. Must be OpenAPI 2.0 or 3.x")

    @staticmethod
    def detect_version(source: Union[str, dict]) -> str:
        """
        Detect OpenAPI version

        Args:
            source: URL, file path, or dict

        Returns:
            str: Detected version
        """
        spec_dict = JsonLoaderUtils.load(source)

        if 'swagger' in spec_dict:
            return spec_dict['swagger']
        elif 'openapi' in spec_dict:
            return spec_dict['openapi']
        else:
            raise ValueError("Cannot detect OpenAPI version")





