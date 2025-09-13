from typing import Callable, List, Tuple, Dict, Any, Optional
from uuid import UUID
import heapq

from app.indexes.base import BaseIndex
from app.indexes.filters.engine import Filters
from app.utils.similarity import cosine_similarity

from readerwriterlock import rwlock

class LinearIndex(BaseIndex, Filters):
    def __init__(self, similarity_function: Callable[[List[float], List[float]], float] = cosine_similarity):
        super().__init__()

        self._chunks: Dict[UUID, List[float]] = {}
        self._metadata: Dict[UUID, Dict[str, Any]] = {}
        self._lock = rwlock.RWLockFair()
        self._similarity_function = similarity_function

        self.multiplier = 3 # Multiplier for the number of results to return when filters are applied

    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        with self._lock.gen_wlock():
            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
    
    def index(self) -> bool:
        return True

    def search(self, query_embedding: List[float], k: int, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        fetch_count = k * self.multiplier if filters else k
        
        # Sligthly optimized O(nlog(k)) < O(nlog(n)) : leetcode-937
        with self._lock.gen_rlock():
            heap = []
            for chunk_id, embedding in self._chunks.items():
                similarity = self._similarity_function(embedding, query_embedding)
                heapq.heappush(heap, (similarity, chunk_id))
                if len(heap) > fetch_count: heapq.heappop(heap)

            results = []

            while heap:    
                similarity, chunk_id = heapq.heappop(heap)
                if self._matches_filters(chunk_id, filters):
                    results.append((chunk_id, similarity))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:k]
        
    def delete(self, chunk_id: UUID) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks:
                return False
            del self._chunks[chunk_id]
            del self._metadata[chunk_id]
            return True
        
    def update(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks:
                return False
            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
            return True