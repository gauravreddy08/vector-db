"""
Document API schemas for request/response models.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

class DocumentCreateRequest(BaseModel):
    """Request schema for creating a document."""
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

class DocumentUpdateRequest(BaseModel):
    """Request schema for updating a document."""
    metadata: Dict[str, Any] = Field(..., description="Updated document metadata")

class DocumentResponse(BaseModel):
    """Response schema for document operations."""
    id: UUID
    library_id: UUID
    chunks: List[UUID]
    metadata: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_domain(cls, document) -> "DocumentResponse":
        """Convert domain model to response schema."""
        return cls(
            id=document.id,
            library_id=document.library_id,
            chunks=list(document.chunks),
            metadata=document.metadata,
            created_at=document.created_at
        )
