from app.repositories.base import BaseRepository
from app.domain.models import DocumentModel
from app.exceptions import NotFoundError
from readerwriterlock import rwlock

from typing import Dict, Optional, List
from uuid import UUID

# CRUD operations for Document (DocumentModel)
# Includes locking for thread safety
# Also, includes ops for adding/removing chunks to/from a document

class InMemoryDocumentRepository(BaseRepository):
    def __init__(self):
        self._documents: Dict[UUID, DocumentModel] = {}
        self._lock = rwlock.RWLockFair()

    def save(self, document: DocumentModel) -> None:
        with self._lock.gen_wlock():
            self._documents[document.id] = document

    def get_by_id(self, id: UUID) -> Optional[DocumentModel]:
        with self._lock.gen_rlock():
            document = self._documents.get(id)
            return document.model_copy(deep=True) if document else None
    
    def update(self, id: UUID, document: DocumentModel) -> bool:
        with self._lock.gen_wlock():
            if id not in self._documents:
                return False
            self._documents[id] = document
            return True
    
    def delete(self, id: UUID) -> bool: 
        with self._lock.gen_wlock():
            if id not in self._documents:
                return False
            del self._documents[id]
            return True
    
    def exists(self, id: UUID) -> bool:
        with self._lock.gen_rlock():
            return id in self._documents
    
    def list_all(self) -> List[UUID]:
        with self._lock.gen_rlock():
            return list(self._documents.keys())
    
    def get_all(self) -> List[DocumentModel]:
        with self._lock.gen_rlock():
            return [document.model_copy(deep=True) for document in self._documents.values()]

    # Chunk Level Operations
    
    def add_chunk_to_document(self, document_id: UUID, chunk_id: UUID) -> None:
        with self._lock.gen_wlock():
            if document_id not in self._documents: 
                raise NotFoundError(f"Document with id {document_id} not found.")
            
            self._documents[document_id].chunks.add(chunk_id)
    
    def remove_chunk_from_document(self, document_id: UUID, chunk_id: UUID) -> bool:
        with self._lock.gen_wlock():
            if document_id not in self._documents: 
                raise NotFoundError(f"Document with id {document_id} not found.")
            
            if chunk_id not in self._documents[document_id].chunks:
                return False
            self._documents[document_id].chunks.remove(chunk_id)
            return True
    
    def get_chunks_by_document_id(self, document_id: UUID) -> List[UUID]:
        with self._lock.gen_rlock():
            if document_id not in self._documents: 
                raise NotFoundError(f"Document with id {document_id} not found.")
            
            return list(self._documents[document_id].chunks)