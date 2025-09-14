from fastapi import APIRouter, Depends, status, HTTPException
from app.services.index_service import IndexService
from app.schemas.index_schemas import IndexResponse, SearchRequest, SearchResponse, SearchResult
from app.schemas.chunk_schemas import ChunkResponse
from app.api.dependencies import get_index_service
from app.exceptions import IndexError
from uuid import UUID

router = APIRouter(prefix="/libraries/{library_id}", tags=["index"])

@router.post("/index", response_model=IndexResponse)
async def index_library(
    library_id: UUID,
    service: IndexService = Depends(get_index_service)
) -> IndexResponse:
    """
    Index a library.
    """
    try:
        service.build_index(library_id)
        return IndexResponse(message="Index built successfully", library_id=library_id)
    except IndexError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search_library(
    library_id: UUID,
    request: SearchRequest,
    service: IndexService = Depends(get_index_service)
) -> SearchResponse:
    try:
        results = service.search(
            library_id=library_id,
            query_text=request.query,
            k=request.k,
            filters=request.filters
        )
        return SearchResponse(
            query=request.query,
            k=request.k,
            filters=request.filters,
            library_id=library_id,
            results=[
                SearchResult(
                    chunk_id=chunk.id,
                    chunk=ChunkResponse.from_domain(chunk),
                    score=score
                ) for chunk, score in results
            ]
        )
    except IndexError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))