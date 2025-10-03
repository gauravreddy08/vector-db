"""
Index API schemas for request/response models.
"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.schemas.chunk_schemas import ChunkResponse

class IndexResponse(BaseModel):
    library_id: UUID
    message: str
    last_indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(..., ge=1)
    filters: Optional[Dict[str, Any]] = Field(default=None)

class SearchResult(BaseModel):
    chunk_id: UUID
    chunk: ChunkResponse
    score: float

class SearchResponse(BaseModel):
    library_id: UUID
    query: str
    k: int
    filters: Optional[Dict[str, Any]]
    results: List[SearchResult]
