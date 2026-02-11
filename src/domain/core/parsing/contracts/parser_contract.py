"""
ParserContract - Interface for parsing OpenAPI specifications
"""
from abc import ABC, abstractmethod
from typing import Union
from src.domain.core.parsing.dtos.parsed_spec import ParsedSpec


class ParserContract(ABC):
    """Abstract parser for OpenAPI specifications"""

    @abstractmethod
    def parse(self, source: Union[str, dict]) -> ParsedSpec:
        """
        Parse OpenAPI specification from URL, file path, or dict

        Args:
            source: URL, file path, or dict

        Returns:
            ParsedSpec: Intermediate parsed specification

        Raises:
            ValueError: If source is invalid
            Exception: If parsing fails
        """
        pass

    @abstractmethod
    def can_parse(self, spec_dict: dict) -> bool:
        """
        Check if this parser can parse the given specification

        Args:
            spec_dict: Specification dictionary

        Returns:
            bool: True if can parse, False otherwise
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Get the OpenAPI version this parser supports

        Returns:
            str: Version string (e.g., "2.0", "3.0", "3.1")
        """
        pass




