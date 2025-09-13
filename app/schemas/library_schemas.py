from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from app.domain.models import LibraryModel

class IndexTypeEnum(str, Enum):
    LINEAR = "linear"
    IVF = "ivf"

class LibraryCreateRequest(BaseModel):
    """Request schema for creating a library"""
    name: str = Field(..., min_length=1, description="Name of the library")
    index_type: IndexTypeEnum = Field(default=IndexTypeEnum.LINEAR, description="Type of index to use for the library (default linear)")
    index_params: Optional[Dict[str, Any]] = Field(default=None, description="Optional index hyperparameters (e.g., n_clusters, n_probes for IVF)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for the library (default empty)")

class LibraryResponse(BaseModel):
    """Response schema for library operations"""
    id: UUID
    name: str
    created_at: datetime
    metadata: Dict[str, Any]
    index_type: str
    index_params: Optional[Dict[str, Any]]
    documents: List[UUID]

    @classmethod
    def from_domain(cls, library: LibraryModel) -> "LibraryResponse":
        """Convert domain model to API response"""
        return cls(
            id=library.id,
            name=library.name,
            created_at=library.created_at,
            metadata=library.metadata,
            index_type=library.index_type.value,
            documents=library.documents,
            index_params=getattr(library, "index_params", None)
        )

class LibraryUpdateRequest(BaseModel):
    """Request schema for updating a library"""
    name: Optional[str] = Field(default=None, description="Updated name for the library")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata for the library")
    
    @validator('name', always=True)
    def validate_at_least_one_field(cls, v, values):
        """Ensure at least one of name or metadata is provided."""
        metadata = values.get('metadata')
        if v is None and metadata is None:
            raise ValueError('At least one of name or metadata must be provided for update')
        return v
