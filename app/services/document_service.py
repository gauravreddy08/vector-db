from typing import Dict, Any, Optional, List
from uuid import UUID
from app.repositories.base import BaseRepository
from app.domain.models import DocumentModel
from app.exceptions import NotFoundError

class DocumentService:
    
    def __init__(self,
                 library_repository: BaseRepository,
                 document_repository: BaseRepository,
                 chunk_service):
        self._library_repository = library_repository
        self._document_repository = document_repository
        self._chunk_service = chunk_service
    
    def get_by_id(self, document_id: UUID, library_id: UUID) -> DocumentModel:
        document = self._document_repository.get_by_id(document_id)
        if not document or document.library_id != library_id:
            raise NotFoundError(f"Document with id {document_id} not found in library {library_id}")
        
        return document
    
    def create(self, library_id: UUID, metadata: dict) -> DocumentModel:
        if not self._library_repository.exists(library_id):
            raise NotFoundError(f"Library with id {library_id} does not exist.")
        
        document = DocumentModel(
            library_id=library_id,
            metadata=metadata
        )
        self._document_repository.save(document)
        
        self._library_repository.add_document_to_library(library_id, document.id)
        
        return document.model_copy(deep=True)
    
    def update(self, document_id: UUID, library_id: UUID, metadata: dict) -> DocumentModel:
        document = self.get_by_id(document_id, library_id)
        if not document:
            raise NotFoundError(f"Document with id {document_id} not found in library {library_id}")
        
        document.metadata = metadata
        
        self._document_repository.update(document_id, document)
        
        return document.model_copy(deep=True)
    
    def delete(self, document_id: UUID, library_id: UUID) -> None:
        try:
            document = self.get_by_id(document_id, library_id)
        except NotFoundError:
            return
        
        chunk_ids = self._document_repository.get_chunks_by_document_id(document_id)
        
        for chunk_id in chunk_ids:
            self._chunk_service.delete(chunk_id, document_id, library_id)
        
        self._library_repository.remove_document_from_library(library_id, document_id)
        self._document_repository.delete(document_id)