"""
Configuration loader for environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from .env file"""

    def __init__(self):
        """Load environment variables from .env file"""
        # Try multiple locations for .env file
        possible_paths = [
            # Try from current working directory
            Path.cwd() / 'config' / '.env',
            # Try relative to this file (src/infrastructure/config/config.py)
            Path(__file__).parent.parent.parent.parent / 'config' / '.env',
            # Try root .env
            Path.cwd() / '.env',
        ]

        loaded = False
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                loaded = True
                break

        # Confluence settings
        self.confluence_base_url = os.getenv('CONFLUENCE_BASE_URL')
        self.confluence_username = os.getenv('CONFLUENCE_USERNAME')
        self.confluence_token = os.getenv('CONFLUENCE_TOKEN')
        self.confluence_space_key = os.getenv('CONFLUENCE_SPACE_KEY')
        self.confluence_parent_page_id = os.getenv('CONFLUENCE_PARENT_PAGE_ID')

        # Application settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')

    def is_confluence_configured(self) -> bool:
        """Check if Confluence is properly configured"""
        return all([
            self.confluence_base_url,
            self.confluence_username,
            self.confluence_token,
            self.confluence_space_key
        ])

    def get_confluence_config(self) -> dict:
        """Get Confluence configuration as dictionary"""
        return {
            'base_url': self.confluence_base_url,
            'username': self.confluence_username,
            'token': self.confluence_token,
            'space_key': self.confluence_space_key,
            'parent_page_id': self.confluence_parent_page_id
        }

    def __repr__(self):
        """String representation (hiding sensitive data)"""
        return (
            f"Config(\n"
            f"  confluence_base_url='{self.confluence_base_url}',\n"
            f"  confluence_username='{self.confluence_username}',\n"
            f"  confluence_token='***{self.confluence_token[-8:] if self.confluence_token else None}',\n"
            f"  confluence_space_key='{self.confluence_space_key}',\n"
            f"  log_level='{self.log_level}',\n"
            f"  output_dir='{self.output_dir}'\n"
            f")"
        )


# Global config instance
config = Config()




