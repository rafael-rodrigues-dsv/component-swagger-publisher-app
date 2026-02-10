"""
Info Model - API Metadata
Represents the information about the API (title, description, version, contact, license)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactModel:
    """Contact information"""
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class LicenseModel:
    """License information"""
    name: str = ""
    url: Optional[str] = None


@dataclass
class InfoModel:
    """API Information and Metadata"""
    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = None
    contact: Optional[ContactModel] = None
    license: Optional[LicenseModel] = None

    def __post_init__(self):
        """Validate required fields"""
        if not self.title:
            raise ValueError("InfoModel.title is required")
        if not self.version:
            raise ValueError("InfoModel.version is required")




