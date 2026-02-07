"""
Info Model - API Metadata
Represents the information about the API (title, description, version, contact, license)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Contact:
    """Contact information"""
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class License:
    """License information"""
    name: str = ""
    url: Optional[str] = None


@dataclass
class Info:
    """API Information and Metadata"""
    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.title:
            raise ValueError("Info.title is required")
        if not self.version:
            raise ValueError("Info.version is required")

