"""
Library API endpoints.
Handles HTTP requests for library operations.
"""
from fastapi import APIRouter, Depends, status
from app.services.library_service import LibraryService
from app.schemas.library_schemas import LibraryCreateRequest, LibraryResponse, IndexTypeEnum, LibraryUpdateRequest
from app.api.dependencies import get_library_service
from app.exceptions import NotFoundError, AlreadyExistsError, IndexError, ValidationError
from uuid import UUID
from fastapi import HTTPException
from typing import List

# Create the router with prefix and tags for organization
router = APIRouter(prefix="/libraries", tags=["libraries"])

# Listing all libraries
@router.get("/", response_model=List[UUID])
async def list_libraries(
    service: LibraryService = Depends(get_library_service)
) -> List[LibraryResponse]:
    """
    List all libraries.
    """
    return service.list_all()

# Reading a library by its ID
@router.get("/{library_id}", response_model=LibraryResponse)
async def get_library(
    library_id: UUID,
    service: LibraryService = Depends(get_library_service)
) -> LibraryResponse:
    """
    Get a library by its ID.
    """
    try:
        library = service.get_by_id(library_id)
        return LibraryResponse.from_domain(library)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Creating a library
@router.post("/", 
             response_model=LibraryResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_library(
    request: LibraryCreateRequest,
    service: LibraryService = Depends(get_library_service)
) -> LibraryResponse:
    """
    Create a new library.
    
    - **name**: Library name (required)
    - **metadata**: Optional metadata dictionary
    
    Returns the created library with its generated ID.
    """
    
    try:
        library = service.create(
            name=request.name,
            index_type=request.index_type,  
            metadata=request.metadata,
            index_params=request.index_params
        )
        return LibraryResponse.from_domain(library)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Updating a library
@router.patch("/{library_id}", response_model=LibraryResponse)
async def update_library(
    library_id: UUID,
    request: LibraryUpdateRequest,
    service: LibraryService = Depends(get_library_service)
) -> LibraryResponse:
    """
    Update a library by its ID.
    """
    try:
        library = service.update(
            id=library_id,
            name=request.name,  
            metadata=request.metadata
        )
        return LibraryResponse.from_domain(library)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Deleting a library
@router.delete("/{library_id}", status_code=status.HTTP_200_OK)
async def delete_library(
    library_id: UUID,
    service: LibraryService = Depends(get_library_service)
) -> None:
    """
    Delete a library by its ID.
    """
    try:
        service.delete(library_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
