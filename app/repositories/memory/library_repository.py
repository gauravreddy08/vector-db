from app.repositories.base import BaseRepository
from app.domain.models import LibraryModel
from app.exceptions import NotFoundError

from typing import Dict, Optional, List
from uuid import UUID
from readerwriterlock import rwlock

# CRUD operations for Library (LibraryModel)
# Includes locking for thread safety
# Also, includes ops for adding/removing documents to/from a library

class InMemoryLibraryRepository(BaseRepository):
    def __init__(self):
        self._libraries: Dict[UUID, LibraryModel] = {}
        self._lock = rwlock.RWLockFair()

    def save(self, library: LibraryModel) -> None:
        with self._lock.gen_wlock():
            self._libraries[library.id] = library

    def get_by_id(self, id: UUID) -> Optional[LibraryModel]:
        with self._lock.gen_rlock():
            lib = self._libraries.get(id)
            return lib.model_copy(deep=True) if lib else None
    
    def update(self, id: UUID, library: LibraryModel) -> bool:
        with self._lock.gen_wlock():
            if id not in self._libraries:
                return False
            self._libraries[id] = library
            return True
    
    def delete(self, id: UUID) -> bool:
        with self._lock.gen_wlock():
            if id not in self._libraries:
                return False
            del self._libraries[id]
            return True
    
    def exists(self, id: UUID) -> bool:
        with self._lock.gen_rlock():
            return id in self._libraries
    
    def list_all(self) -> List[UUID]:
        with self._lock.gen_rlock():
            return list(self._libraries.keys())
    
    def get_all(self) -> List[LibraryModel]:
        with self._lock.gen_rlock():
            return [library.model_copy(deep=True) for library in self._libraries.values()]
    
    # Document Level Operations
    
    def add_document_to_library(self, library_id: UUID, document_id: UUID) -> None:
        with self._lock.gen_wlock():
            if library_id not in self._libraries:
                raise NotFoundError(f"Library with id {library_id} not found.")
        
            self._libraries[library_id].documents.add(document_id)
    
    def remove_document_from_library(self, library_id: UUID, document_id: UUID) -> bool:    
        with self._lock.gen_wlock():
            if library_id not in self._libraries:
                raise NotFoundError(f"Library with id {library_id} not found.")
        
            if document_id not in self._libraries[library_id].documents:
                return False
        
            self._libraries[library_id].documents.remove(document_id)
            return True
    
    def get_documents_by_library_id(self, library_id: UUID) -> List[UUID]:
        with self._lock.gen_rlock():
            if library_id not in self._libraries:
                raise NotFoundError(f"Library with id {library_id} not found.")
        
            return list(self._libraries[library_id].documents)