from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from uuid import UUID

class BaseIndex(ABC):

    @abstractmethod
    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def index(self) -> bool:
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], k: int,
               filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        pass

    @abstractmethod
    def delete(self, chunk_id: UUID) -> bool:
        pass

    @abstractmethod
    def update(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        pass
