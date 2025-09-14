from typing import Dict, Any, Optional, List
from uuid import UUID
from app.repositories.base import BaseRepository
from app.domain.models import LibraryModel
from app.services.document_service import DocumentService
from app.services.index_service import IndexService
from app.exceptions import NotFoundError, IndexError

class LibraryService:
    
    def __init__(self, 
                 library_repository: BaseRepository,
                 document_service: DocumentService,
                 index_service: IndexService):
        self._library_repository = library_repository
        self._document_service = document_service
        self._index_service = index_service
    
    def create(self, name: str, index_type, metadata: Dict[str, Any], index_params: Dict[str, Any] | None = None) -> LibraryModel:
        library = LibraryModel(
            name=name,
            index_type=index_type,
            metadata=metadata,
            index_params=index_params or {}
        )
        
        self._library_repository.save(library)
        
        self._index_service.create_index_for_library(library.id, index_type.value, index_params or {})
        
        return library.model_copy(deep=True)
    
    def get_by_id(self, id: UUID) -> LibraryModel:
        library = self._library_repository.get_by_id(id)
        if library is None:
            raise NotFoundError(f"Library with id {id} not found")
        return library
    
    def update(self, id: UUID, name: Optional[str] = None, metadata: Optional[dict] = None) -> LibraryModel:
        library = self._library_repository.get_by_id(id)
        if not library:
            raise NotFoundError(f"Library with id {id} not found.")
        
        if name is not None:
            library.name = name
        if metadata is not None:
            library.metadata = metadata
        
        self._library_repository.update(id, library)
        
        return library.model_copy(deep=True)
    
    def delete(self, id: UUID) -> None:
        library = self._library_repository.get_by_id(id)
        if not library:
            return
        
        document_ids = self._library_repository.get_documents_by_library_id(id)
        
        for document_id in document_ids:
            self._document_service.delete(document_id, id)
        
        self._index_service.delete_index_for_library(id)
        
        self._library_repository.delete(id)
    
    def list_all(self) -> List[UUID]:
        return self._library_repository.list_all()