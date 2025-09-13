"""
Chunk API endpoints for nested resource pattern.
Handles HTTP requests for chunk operations within libraries and documents.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from app.services.chunk_service import ChunkService
from app.schemas.chunk_schemas import (
    ChunkCreateRequest, 
    ChunkUpdateRequest, 
    ChunkResponse
)
from app.api.dependencies import get_chunk_service
from app.exceptions import NotFoundError, ValidationError, IndexError, EmbeddingError
from uuid import UUID
from typing import Optional

# Create the router with prefix for nested resources
router = APIRouter(prefix="/libraries/{library_id}/chunks", tags=["chunks"])

# Reading a chunk by its parameters (library_id and chunk_id are required, document_id is optional)
@router.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(
    library_id: UUID,
    chunk_id: UUID,
    document_id: Optional[UUID] = None,
    service: ChunkService = Depends(get_chunk_service)
) -> ChunkResponse:
    """
    Get a chunk by its ID within a library, optionally scoped to a document.
    
    - **document_id**: Optional document ID to validate chunk belongs to specific document,
        if not provided, the chunk is returned without document scope validation
    """
    try:
        chunk = service.get_by_id(chunk_id, library_id, document_id)
        return ChunkResponse.from_domain(chunk)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Creating a chunk
@router.post("/", 
             response_model=ChunkResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_chunk(
    library_id: UUID,
    request: ChunkCreateRequest,
    service: ChunkService = Depends(get_chunk_service)
) -> ChunkResponse:
    """
    Create a new chunk in a library.
    
    - **text**: Text content of the chunk (required)
    - **metadata**: Optional metadata dictionary for the chunk
    - **document_id**: Optional document ID (default None, creates new document if not provided)
    - **document_metadata**: Optional metadata for new document creation (default {})
    
    Returns the created chunk with its generated ID.
    """
    try:
        chunk = service.create(
            library_id=library_id,
            text=request.text,
            metadata=request.metadata,
            document_id=request.document_id,
            document_metadata=request.document_metadata
        )
        return ChunkResponse.from_domain(chunk)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Updating a chunk
@router.patch("/{chunk_id}", response_model=ChunkResponse)
async def update_chunk(
    library_id: UUID,
    chunk_id: UUID,
    request: ChunkUpdateRequest,
    document_id: Optional[UUID] = None,
    service: ChunkService = Depends(get_chunk_service)
) -> ChunkResponse:
    """
    Update a chunk's text and/or metadata within a library.
    
    - **document_id**: Optional document ID to validate chunk belongs to specific document
    """
    try:
        chunk = service.update(
            chunk_id=chunk_id,
            library_id=library_id,
            text=request.text,
            metadata=request.metadata,
            document_id=document_id
        )
        return ChunkResponse.from_domain(chunk)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Deleting a chunk
@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(
    library_id: UUID,
    chunk_id: UUID,
    document_id: Optional[UUID] = None,
    service: ChunkService = Depends(get_chunk_service)
) -> None:
    """
    Delete a chunk from a library.
    
    - **document_id**: Optional document ID to validate chunk belongs to specific document
    """
    try:
        service.delete(chunk_id, library_id, document_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))