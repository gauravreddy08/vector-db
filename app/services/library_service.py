from typing import Dict, Any, Optional, List
from uuid import UUID
from app.repositories.base import BaseRepository
from app.domain.models import LibraryModel
from app.services.document_service import DocumentService
from app.services.index_service import IndexService
from app.exceptions import NotFoundError, IndexError

class LibraryService:
    """
    Top-level orchestrator for library CRUD operations.
    Manages the lifecycle of the Library aggregate.
    """
    
    def __init__(self, 
                 library_repository: BaseRepository,
                 document_service: DocumentService,
                 index_service: IndexService):
        """
        Initialize the LibraryService with its dependencies.
        
        Args:
            library_repository: Repository for library persistence
            document_service: Service for document operations
            index_service: Service for managing vector indexes
        """
        self._library_repository = library_repository
        self._document_service = document_service
        self._index_service = index_service
    
    def create(self, name: str, index_type, metadata: Dict[str, Any], index_params: Dict[str, Any] | None = None) -> LibraryModel:
        """
        Create a new library with the specified name, index type, and metadata.
        
        Args:
            name: The name of the library
            index_type: The type of vector index to use (e.g., "linear")
            metadata: Additional metadata for the library
            
        Returns:
            The created LibraryModel
        """
        # Create the library model
        library = LibraryModel(
            name=name,
            index_type=index_type,
            metadata=metadata,
            index_params=index_params or {}
        )
        
        # Save to repository
        self._library_repository.save(library)
        
        # Create the corresponding index
        self._index_service.create_index_for_library(library.id, index_type.value, index_params or {})
        
        return library.model_copy(deep=True)
    
    def get_by_id(self, id: UUID) -> LibraryModel:
        """
        Retrieve a library by its ID.
        
        Args:
            id: The UUID of the library
            
        Returns:
            The LibraryModel if found
            
        Raises:
            NotFoundError: If the library is not found
        """
        library = self._library_repository.get_by_id(id)
        if library is None:
            raise NotFoundError(f"Library with id {id} not found")
        return library
    
    def update(self, id: UUID, name: Optional[str] = None, metadata: Optional[dict] = None) -> LibraryModel:
        """
        Update a library's name or metadata.
        
        Args:
            id: The UUID of the library
            name: The new name for the library (optional)
            metadata: The new metadata for the library (optional)
            
        Returns:
            The updated LibraryModel
            
        Raises:
            NotFoundError: If the library does not exist
        """
        # Fetch the library
        library = self._library_repository.get_by_id(id)
        if not library:
            raise NotFoundError(f"Library with id {id} not found.")
        
        # Update fields if provided
        if name is not None:
            library.name = name
        if metadata is not None:
            library.metadata = metadata
        
        # Save changes
        self._library_repository.update(id, library)
        
        return library.model_copy(deep=True)
    
    def delete(self, id: UUID) -> None:
        """
        Delete a library and cascade delete all its documents and chunks.
        
        Args:
            id: The UUID of the library
        """
        # Check if library exists
        library = self._library_repository.get_by_id(id)
        if not library:
            # Return silently for idempotency
            return
        
        # Step 1: Find all child document IDs
        document_ids = self._library_repository.get_documents_by_library_id(id)
        
        # Step 2: Delegate deletion to DocumentService for each document
        for document_id in document_ids:
            self._document_service.delete(document_id, id)
        
        # Step 3: Delete the index for this library
        self._index_service.delete_index_for_library(id)
        
        # Step 4: Delete the library itself
        self._library_repository.delete(id)
    
    def list_all(self) -> List[UUID]:
        """
        List all libraries.
        """
        return self._library_repository.list_all()