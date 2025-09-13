from typing import Dict, Any, Optional
from uuid import UUID
from app.repositories.base import BaseRepository
from app.domain.models import ChunkModel, DocumentModel
from app.services.index_service import IndexService
from app.utils.embedding import CohereEmbedding
from app.exceptions import NotFoundError, ValidationError, IndexError, EmbeddingError
from uuid import uuid4

class ChunkService:
    """
    Main orchestrator for all use cases that begin with a chunk (create, update, delete).
    This is the lowest-level service in the hierarchy and cannot depend on services above it.
    """
    
    def __init__(self, 
                 chunk_repository: BaseRepository,
                 library_repository: BaseRepository,
                 document_repository: BaseRepository,
                 index_service: IndexService,
                 embedding_service: CohereEmbedding):
        """
        Initialize the ChunkService with its dependencies.
        
        Args:
            library_repository: Repository for library operations
            document_repository: Repository for document operations
            chunk_repository: Repository for chunk persistence
            index_service: Service for managing vector indexes
            embedding_service: Service for creating embeddings
        """
        self._library_repository = library_repository
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._index_service = index_service
        self._embedding_service = embedding_service
    
    def get_by_id(self, chunk_id: UUID, library_id: UUID, document_id: Optional[UUID] = None) -> ChunkModel:
        """
        Retrieve a chunk with optional document scope validation.
        
        Args:
            chunk_id: The UUID of the chunk
            library_id: The UUID of the library
            document_id: Optional UUID of the document (if provided, validates exact chunk-document pair)
            
        Returns:
            The ChunkModel if found and matches scope
            
        Raises:
            NotFoundError: If the chunk is not found or doesn't match scope
        """
        chunk = self._chunk_repository.get_by_id(chunk_id)
        if not chunk or chunk.library_id != library_id or (document_id is not None and chunk.document_id != document_id):
            raise NotFoundError(f"Chunk with given parameters does not exist")
            
        return chunk
    
    def create(self, library_id: UUID, text: str, metadata: dict, 
               document_id: Optional[UUID] = None, document_metadata: dict = {}) -> ChunkModel:
        """
        Create a new chunk with optional document creation.
        
        Args:
            library_id: The UUID of the library
            text: The text content of the chunk
            metadata: Additional metadata for the chunk
            document_id: Optional UUID of the document (if None, creates a new document)
            document_metadata: Optional metadata for document creation (default {})
            
        Returns:
            The created ChunkModel
            
        Raises:
            NotFoundError: If library or document doesn't exist
            ValidationError: If document exists in wrong library
            IndexError: If index is not found
        """
        if not self._library_repository.exists(library_id):
            raise NotFoundError(f"Library with id {library_id} does not exist.")
        
        if document_id is None:
            # Create a new document
            document = DocumentModel(
                library_id=library_id,
                metadata=document_metadata
            )
            self._document_repository.save(document)
            self._library_repository.add_document_to_library(library_id, document.id)
        
        else:
            document = self._document_repository.get_by_id(document_id)
            if not document or document.library_id != library_id:
                raise NotFoundError(f"Document with id {document_id} not found in library {library_id}")
        
        try:
            embedding = self._embedding_service.embed(text)
        except Exception as e:
            raise EmbeddingError(f"Error generating embedding: {e}")
        
        chunk = ChunkModel(
            library_id=library_id,
            document_id=document.id,
            text=text,
            embedding=embedding,
            metadata=metadata
        )
        
        self._chunk_repository.save(chunk)
        self._document_repository.add_chunk_to_document(document.id, chunk.id)
        index = self._index_service.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")
        
        index.add(
            chunk_id=chunk.id,
            embedding=embedding,
            metadata={
                "document_id": document.id,
                "library_id": library_id,
                **metadata
            }
        )
        
        return chunk.model_copy(deep=True)
    
    def update(self, chunk_id: UUID, library_id: UUID, text: Optional[str] = None, 
               metadata: Optional[dict] = None, document_id: Optional[UUID] = None) -> ChunkModel:
        """
        Update a chunk's text and/or metadata with optional document scope validation.
        
        Args:
            chunk_id: The UUID of the chunk
            library_id: The UUID of the library
            text: New text content (optional)
            metadata: New metadata (optional)
            document_id: Optional UUID of the document (if provided, validates exact chunk-document pair)
            
        Returns:
            The updated ChunkModel
            
        Raises:
            NotFoundError: If chunk doesn't exist in the correct scope
            IndexError: If index is not found
        """
    
        chunk = self.get_by_id(chunk_id, library_id, document_id)
        
        if text is not None:
            chunk.text = text
            try:
                chunk.embedding = self._embedding_service.embed(text)
            except Exception as e:
                raise EmbeddingError(f"Error generating embedding: {e}")
        
        if metadata is not None:
            chunk.metadata = metadata
        
        self._chunk_repository.update(chunk_id, chunk)
        
        index = self._index_service.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")
        
        index.update(
            chunk_id=chunk.id,
            embedding=chunk.embedding,
            metadata={
                "document_id": chunk.document_id,
                "library_id": library_id,
                **chunk.metadata
            }
        )
        
        return chunk.model_copy(deep=True)
    
    def delete(self, chunk_id: UUID, library_id: UUID, document_id: Optional[UUID] = None) -> None:
        """
        Delete a chunk and remove it from all relationships and indexes.
        
        Args:
            chunk_id: The UUID of the chunk
            library_id: The UUID of the library
            document_id: Optional UUID of the document (if provided, validates exact chunk-document pair)
        """
        try:
            chunk = self.get_by_id(chunk_id, library_id, document_id)
        except NotFoundError:
            return None
        
        index = self._index_service.get_index(library_id)
        if index: index.delete(chunk_id)
        
        self._document_repository.remove_chunk_from_document(chunk.document_id, chunk_id)
        
        self._chunk_repository.delete(chunk_id)
    
    