from typing import Dict, Optional, Any, List, Tuple
from uuid import UUID
from app.indexes.base import BaseIndex
from app.indexes.factory import create_index
from app.exceptions import AlreadyExistsError, IndexError
from app.indexes.implementations.ivf import IVFIndex
from app.utils.embedding import CohereEmbedding
from app.domain.models import ChunkModel
from app.repositories.base import BaseRepository

class IndexService:
    
    def __init__(self, chunk_repository: BaseRepository, embedding_service: CohereEmbedding):
        self._active_indexes: Dict[UUID, BaseIndex] = {}
        self._embedding_service = embedding_service
        self._chunk_repository = chunk_repository
    
    def create_index_for_library(self, library_id: UUID, index_type: str, params: Optional[Dict[str, Any]] = None) -> None:
        if library_id in self._active_indexes:
            raise AlreadyExistsError(f"Index already exists for library {library_id}")
        
        index = create_index(index_type, params)
        self._active_indexes[library_id] = index
    
    def get_index(self, library_id: UUID) -> Optional[BaseIndex]:
        return self._active_indexes.get(library_id)
    
    def delete_index_for_library(self, library_id: UUID) -> None:
        if library_id in self._active_indexes:
            del self._active_indexes[library_id]
    
    def build_index(self, library_id: UUID) -> None:
        index = self.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")

        index.index()

    def search(self, library_id: UUID, query_text: str, k: int,
               filters: Optional[Dict[str, Any]] = None) -> List[Tuple[ChunkModel, float]]:
        index = self.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")
        
        query_embedding = self._embedding_service.embed(query_text, input_type="search_query")
        results = index.search(query_embedding, k, filters=filters)
        results = [(self._chunk_repository.get_by_id(result[0]), result[1]) for result in results]
        return results