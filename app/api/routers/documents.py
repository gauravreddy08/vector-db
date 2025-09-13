"""
Document API endpoints for nested resource pattern.
Handles HTTP requests for document operations within libraries.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from app.services.document_service import DocumentService
from app.schemas.document_schemas import (
        DocumentCreateRequest, 
        DocumentUpdateRequest, 
        DocumentResponse
    )
from app.api.dependencies import get_document_service
from app.exceptions import NotFoundError
from uuid import UUID

# Create the router with prefix for nested resources
router = APIRouter(prefix="/libraries/{library_id}/documents", tags=["documents"])

# Reading a document by its ID
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    library_id: UUID,
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Get a document by its ID within a library.
    """
    try:
        document = service.get_by_id(document_id, library_id)
        return DocumentResponse.from_domain(document)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Creating a document
@router.post("/", 
             response_model=DocumentResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_document(
    library_id: UUID,
    request: DocumentCreateRequest,
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Create a new document in a library.
    
    - **metadata**: Optional metadata dictionary for the document
    
    Returns the created document with its generated ID.
    """
    try:
        document = service.create(
            library_id=library_id,
            metadata=request.metadata
        )
        return DocumentResponse.from_domain(document)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Updating a document
@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    library_id: UUID,
    document_id: UUID,
    request: DocumentUpdateRequest,
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Update a document's metadata within a library.
    """
    try:
        document = service.update(
            document_id=document_id,
            library_id=library_id,
            metadata=request.metadata
        )
        return DocumentResponse.from_domain(document)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Deleting a document
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    library_id: UUID,
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
) -> None:
    """
    Delete a document and all its chunks from a library.
    """
    try:
        service.delete(document_id, library_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))