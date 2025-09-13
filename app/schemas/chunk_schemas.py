"""
Chunk API schemas for request/response models.
"""
from pydantic import BaseModel, Field, validator, model_validator
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime



class ChunkCreateRequest(BaseModel):
    """Request schema for creating a chunk."""
    text: str = Field(..., min_length=1, description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    document_id: Optional[UUID] = Field(None, description="Document ID (creates new document if not provided)")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for new document if document_id not provided")

class ChunkUpdateRequest(BaseModel):
    """Request schema for updating a chunk."""
    text: Optional[str] = Field(None, min_length=1, description="Updated text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated chunk metadata")

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one of text or metadata is provided."""
        if self.text is None and self.metadata is None:
            raise ValueError('Either text or metadata must be provided for update')
        return self


class ChunkResponse(BaseModel):
    """Response schema for chunk operations."""
    id: UUID
    document_id: UUID
    library_id: UUID
    text: str
    metadata: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_domain(cls, chunk) -> "ChunkResponse":
        """Convert domain model to response schema."""
        return cls(
            id=chunk.id,
            document_id=chunk.document_id,
            library_id=chunk.library_id,
            text=chunk.text,
            metadata=chunk.metadata,
            created_at=chunk.created_at
        )
