from typing import Dict, Optional, Any, List, Tuple
from uuid import UUID
from app.indexes.base import BaseIndex
from app.indexes.factory import create_index
from app.exceptions import AlreadyExistsError, IndexError
from app.indexes.implementations.ivf import IVFIndex

class IndexService:
    """
    Infrastructure service that manages the lifecycle of in-memory VectorIndex objects.
    Acts as a registry for creating, retrieving, and destroying index instances as libraries are created and deleted.
    """
    
    def __init__(self):
        """Initialize the IndexService with an empty dictionary of active indexes."""
        self._active_indexes: Dict[UUID, BaseIndex] = {}
    
    def create_index_for_library(self, library_id: UUID, index_type: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Create a new index instance for a library.
        
        Args:
            library_id: The UUID of the library
            index_type: The type of index to create (e.g., "linear")
            
        Raises:
            AlreadyExistsError: If an index already exists for the library
        """
        if library_id in self._active_indexes:
            raise AlreadyExistsError(f"Index already exists for library {library_id}")
        
        index = create_index(index_type, params)
        self._active_indexes[library_id] = index
    
    def get_index(self, library_id: UUID) -> Optional[BaseIndex]:
        """
        Retrieve the active index object for a given library.
        
        Args:
            library_id: The UUID of the library
            
        Returns:
            The BaseIndex instance for the library, or None if not found
        """
        return self._active_indexes.get(library_id)
    
    def delete_index_for_library(self, library_id: UUID) -> None:
        """
        Delete the index instance for a library.
        
        Args:
            library_id: The UUID of the library
        """
        if library_id in self._active_indexes:
            del self._active_indexes[library_id]
    
    def build_index(self, library_id: UUID) -> None:
        """
        Orchestrate the potentially long-running build process on a specific index.
        
        Args:
            library_id: The UUID of the library
            
        Raises:
            IndexError: If no index exists for the library
        """
        index = self.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")

        index.index()

    def search(self, library_id: UUID, query_embedding: List[float], k: int,
               filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        index = self.get_index(library_id)
        if not index:
            raise IndexError(f"No index found for library {library_id}")
        return index.search(query_embedding, k, filters=filters)