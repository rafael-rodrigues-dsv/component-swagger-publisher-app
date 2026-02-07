"""
JsonLoader - Utility to load JSON/YAML from URL, file, or string
"""
import json
import yaml
import urllib.request
from pathlib import Path
from typing import Union, Dict, Any


class JsonLoader:
    """Load JSON/YAML from various sources"""

    @staticmethod
    def load(source: Union[str, dict]) -> Dict[str, Any]:
        """
        Load JSON/YAML from URL, file path, or dict

        Args:
            source: URL, file path, or dict

        Returns:
            Dict: Loaded specification

        Raises:
            ValueError: If source is invalid
            Exception: If loading fails
        """
        if isinstance(source, dict):
            return source

        if isinstance(source, str):
            # Check if it's a URL
            if source.startswith('http://') or source.startswith('https://'):
                return JsonLoader._load_from_url(source)

            # Check if it's a file
            path = Path(source)
            if path.exists():
                return JsonLoader._load_from_file(str(path))

            # Try to parse as JSON string
            try:
                return json.loads(source)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid source: not a URL, file, or valid JSON string: {source}")

        raise ValueError(f"Unsupported source type: {type(source)}")

    @staticmethod
    def _load_from_url(url: str) -> Dict[str, Any]:
        """Load from URL"""
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read().decode('utf-8')

            # Try JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try YAML
                return yaml.safe_load(content)

        except Exception as e:
            error_msg = str(e)

            # Add helpful suggestions for common errors
            if "403" in error_msg or "Forbidden" in error_msg:
                error_msg += "\n\n💡 This URL does not allow public access."
                error_msg += "\n\n✅ Try these verified APIs instead:"
                error_msg += "\n   • Petstore: https://petstore.swagger.io/v2/swagger.json"
                error_msg += "\n   • The Cat API: https://raw.githubusercontent.com/APIs-guru/openapi-directory/main/APIs/thecatapi.com/1.0.0/openapi.yaml"
                error_msg += "\n   • Spotify: https://raw.githubusercontent.com/sonallux/spotify-web-api/main/fixed-spotify-open-api.yml"
                error_msg += "\n\n📋 See full list: Run 'py tests/public_apis_list.py'"
            elif "404" in error_msg or "Not Found" in error_msg:
                error_msg += "\n\n💡 This URL does not exist."
                error_msg += "\n\n✅ Check the URL or try a verified API (see docs/VERIFIED_APIS.md)"

            raise Exception(f"Failed to load from URL {url}: {error_msg}")

    @staticmethod
    def _load_from_file(file_path: str) -> Dict[str, Any]:
        """Load from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Detect format by extension
            path = Path(file_path)
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(content)
            else:
                return json.loads(content)

        except Exception as e:
            raise Exception(f"Failed to load from file {file_path}: {str(e)}")

