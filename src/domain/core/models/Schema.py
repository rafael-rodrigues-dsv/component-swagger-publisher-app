"""
Schema Model - Data type definitions
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class Schema:
    """Schema/Type definition"""
    type: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    # Validation
    enum: Optional[List[Any]] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    # Object properties
    properties: Dict[str, 'Schema'] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    additional_properties: Optional['Schema'] = None

    # Array items
    items: Optional['Schema'] = None

    # Composition
    all_of: Optional[List['Schema']] = None
    one_of: Optional[List['Schema']] = None
    any_of: Optional[List['Schema']] = None

    # Reference
    ref: Optional[str] = None

    # Example
    example: Optional[Any] = None
    default: Optional[Any] = None

    # Metadata
    nullable: bool = False
    read_only: bool = False
    write_only: bool = False
    deprecated: bool = False




