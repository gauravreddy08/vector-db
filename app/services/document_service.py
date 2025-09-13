from typing import Dict, Any, Optional, List
from uuid import UUID
from app.repositories.base import BaseRepository
from app.domain.models import DocumentModel
from app.exceptions import NotFoundError

class DocumentService:
    """
    Application service that manages the Document aggregate, including its state and relationships to chunks.
    """
    
    def __init__(self,
                 library_repository: BaseRepository,
                 document_repository: BaseRepository,
                 chunk_service):
        """
        Initialize the DocumentService with its dependencies.
        
        Args:
            library_repository: Repository for library operations
            document_repository: Repository for document persistence
            chunk_service: Service for chunk operations
        """
        self._library_repository = library_repository
        self._document_repository = document_repository
        self._chunk_service = chunk_service
    
    def get_by_id(self, document_id: UUID, library_id: UUID) -> DocumentModel:
        """
        Retrieves a document if it exists within the specified library.
        
        Args:
            document_id: The UUID of the document
            library_id: The UUID of the library
            
        Returns:
            The DocumentModel if found within the library
            
        Raises:
            NotFoundError: If the document is not found in the library
        """
        document = self._document_repository.get_by_id(document_id)
        if not document or document.library_id != library_id:
            raise NotFoundError(f"Document with id {document_id} not found in library {library_id}")
        
        return document
    
    def create(self, library_id: UUID, metadata: dict) -> DocumentModel:
        """
        Create a new document in the specified library.
        
        Args:
            library_id: The UUID of the library
            metadata: Additional metadata for the document
            
        Returns:
            The created DocumentModel
            
        Raises:
            NotFoundError: If the library does not exist
        """
        # Step 1: Validate library exists
        if not self._library_repository.exists(library_id):
            raise NotFoundError(f"Library with id {library_id} does not exist.")
        
        # Step 2: Create and save document
        document = DocumentModel(
            library_id=library_id,
            metadata=metadata
        )
        self._document_repository.save(document)
        
        # Add document to library's document list
        self._library_repository.add_document_to_library(library_id, document.id)
        
        return document.model_copy(deep=True)
    
    def update(self, document_id: UUID, library_id: UUID, metadata: dict) -> DocumentModel:
        """
        Update a document's metadata.
        
        Args:
            document_id: The UUID of the document
            library_id: The UUID of the library
            metadata: The new metadata for the document
            
        Returns:
            The updated DocumentModel
            
        Raises:
            NotFoundError: If the document doesn't exist within the specified library
        """
        # Fetch the document to verify scope
        document = self.get_by_id(document_id, library_id)
        if not document:
            raise NotFoundError(f"Document with id {document_id} not found in library {library_id}")
        
        # Update metadata
        document.metadata = metadata
        
        # Save changes
        self._document_repository.update(document_id, document)
        
        return document.model_copy(deep=True)
    
    def delete(self, document_id: UUID, library_id: UUID) -> None:
        """
        Delete a document and cascade delete all its chunks.
        
        Args:
            document_id: The UUID of the document
            library_id: The UUID of the library
        """
        try:
            document = self.get_by_id(document_id, library_id)
        except NotFoundError:
            return
        
        chunk_ids = self._document_repository.get_chunks_by_document_id(document_id)
        
        for chunk_id in chunk_ids:
            self._chunk_service.delete(chunk_id, document_id, library_id)
        
        self._library_repository.remove_document_from_library(library_id, document_id)
        self._document_repository.delete(document_id)