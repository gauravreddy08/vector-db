"""
Dependency injection for FastAPI endpoints.
Creates singleton instances of services and repositories.
"""
from app.services.library_service import LibraryService
from app.services.document_service import DocumentService
from app.services.chunk_service import ChunkService

from app.services.index_service import IndexService
from app.utils.embedding import CohereEmbedding

from app.repositories.memory.library_repository import InMemoryLibraryRepository
from app.repositories.memory.document_repository import InMemoryDocumentRepository
from app.repositories.memory.chunk_repository import InMemoryChunkRepository

# Create singleton instances (shared across all requests)
_library_repo = InMemoryLibraryRepository()
_document_repo = InMemoryDocumentRepository()
_chunk_repo = InMemoryChunkRepository()
_index_service = IndexService()
_embedding_service = CohereEmbedding()

# Create services with their dependencies
_chunk_service = ChunkService(
    chunk_repository=_chunk_repo,
    library_repository=_library_repo,
    document_repository=_document_repo,
    index_service=_index_service,
    embedding_service=_embedding_service
)

_document_service = DocumentService(
    library_repository=_library_repo,
    document_repository=_document_repo,
    chunk_service=_chunk_service)

_library_service = LibraryService(
    library_repository=_library_repo,
    document_service=_document_service,
    index_service=_index_service
)

def get_library_service() -> LibraryService:
    """
    Dependency injection for LibraryService.
    Returns the same instance for all requests (singleton pattern).
    """
    return _library_service

def get_document_service() -> DocumentService:
    """
    Dependency injection for DocumentService.
    Returns the same instance for all requests (singleton pattern).
    """
    return _document_service

def get_chunk_service() -> ChunkService:
    """
    Dependency injection for ChunkService.
    Returns the same instance for all requests (singleton pattern).
    """
    return _chunk_service

def get_index_service() -> IndexService:
    """
    Dependency injection for IndexService.
    Returns the same instance for all requests (singleton pattern).
    """
    return _index_service
