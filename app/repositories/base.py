from abc import ABC, abstractmethod
from typing import Any, Optional, List
from uuid import UUID

class BaseRepository(ABC):
    @abstractmethod
    def save(self, entity: Any) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List[UUID]:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> Optional[Any]:
        pass
    
    @abstractmethod
    def update(self, entity_id: UUID, entity: Any) -> bool:
        pass
    
    @abstractmethod
    def delete(self, entity_id: UUID) -> bool:
        pass

    @abstractmethod
    def exists(self, entity_id: UUID) -> bool:
        pass