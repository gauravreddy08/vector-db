from app.repositories.base import BaseRepository
from app.domain.models import ChunkModel
from readerwriterlock import rwlock

from typing import Dict, Optional, List
from uuid import UUID

# CRUD operations for Chunk (ChunkModel)
# Includes locking for thread safety

class InMemoryChunkRepository(BaseRepository):
    def __init__(self):
        self._chunks: Dict[UUID, ChunkModel] = {}
        self._lock = rwlock.RWLockFair()

    def save(self, chunk: ChunkModel) -> None:
        with self._lock.gen_wlock():
            self._chunks[chunk.id] = chunk
    
    def update(self, id: UUID, chunk: ChunkModel) -> bool:
        with self._lock.gen_wlock():
            if id not in self._chunks:
                return False
            self._chunks[id] = chunk
            return True
        
    def get_by_id(self, id: UUID) -> Optional[ChunkModel]:
        with self._lock.gen_rlock():
            chunk = self._chunks.get(id)
            return chunk.model_copy(deep=True) if chunk else None
    
    def delete(self, id: UUID) -> bool:
        with self._lock.gen_wlock():
            if id not in self._chunks:
                return False
            del self._chunks[id]
            return True
    
    def exists(self, id: UUID) -> bool:
        with self._lock.gen_rlock():
            return id in self._chunks
    
    def list_all(self) -> List[UUID]:
        with self._lock.gen_rlock():
            return list(self._chunks.keys())
    
    def get_all(self) -> List[ChunkModel]:
        with self._lock.gen_rlock():
            return [chunk.model_copy(deep=True) for chunk in self._chunks.values()]