"""
SecurityScheme Model - Security definitions
"""
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class OAuthFlow:
    """OAuth 2.0 Flow"""
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None
    scopes: Dict[str, str] = field(default_factory=dict)


@dataclass
class SecurityScheme:
    """Security scheme definition"""
    type: str  # apiKey, http, oauth2, openIdConnect
    description: Optional[str] = None
    name: Optional[str] = None  # For apiKey
    location: Optional[str] = None  # query, header, cookie (for apiKey)
    scheme: Optional[str] = None  # For http (bearer, basic, etc.)
    bearer_format: Optional[str] = None  # For http bearer
    flows: Optional[Dict[str, OAuthFlow]] = None  # For oauth2
    open_id_connect_url: Optional[str] = None  # For openIdConnect

    def __post_init__(self):
        """Validate required fields"""
        if not self.type:
            raise ValueError("SecurityScheme.type is required")
        if self.type not in ['apiKey', 'http', 'oauth2', 'openIdConnect']:
            raise ValueError(f"Invalid security type: {self.type}")
        if self.type == 'apiKey' and not self.name:
            raise ValueError("SecurityScheme.name is required for apiKey")
        if self.type == 'apiKey' and not self.location:
            raise ValueError("SecurityScheme.location is required for apiKey")

