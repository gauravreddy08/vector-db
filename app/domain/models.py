# Contains Data Models (Objects) for all the entities -> Library, Document, Chunk and also for Indexing

from pydantic import BaseModel, Field
from typing import Any, List, Dict, Set, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum

class IndexModel(Enum):
    """
    Enum for the different types of indexes.
    """
    LINEAR = "linear"
    IVF = "ivf"
    NSW = "nsw"

class ChunkModel(BaseModel):
    """
    A chunk of text with an embedding and metadata.
    
    Attributes:
        id: UUID
        document_id: UUID
        library_id: UUID
        text: str
        embedding: List[float]
        metadata: dict[str, Any]
        created_at: datetime
    """
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    library_id: UUID
    
    text: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_length=1)
    
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentModel(BaseModel):
    """
    A document with chunks and metadata.
    
    Attributes:
        id: UUID
        library_id: UUID
        chunks: Set[UUID]
        metadata: dict[str, Any]
        created_at: datetime
    """
    id: UUID = Field(default_factory=uuid4)
    library_id: UUID
    
    chunks: Set[UUID] = Field(default_factory=set)
    
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LibraryModel(BaseModel):
    """
    A library with documents and metadata.
    
    Attributes:
        id: UUID
        name: str
        index_type: IndexModel enum (default: LINEAR)
        index_params: Optional[dict[str, Any]]
        documents: Set[UUID]
        metadata: dict[str, Any]
        created_at: datetime
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    index_type: IndexModel = Field(default=IndexModel.LINEAR)
    index_params: Optional[dict[str, Any]] = Field(default=None)

    documents: Set[UUID] = Field(default_factory=set)

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))