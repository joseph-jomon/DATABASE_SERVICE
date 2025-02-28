from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, List
from pydantic import BaseModel
from vdb_app.services.vdb_es_client import VDBSearchManager, get_vdb_search_manager

combi_search_router = APIRouter()

class SearchRequest(BaseModel):
    search_vector: List[float]

class SearchHit(BaseModel):
    id: str
    score: float
    source: dict

class SearchResponse(BaseModel):
    hits: List[SearchHit]

@combi_search_router.post("/combined_search/", response_model=SearchResponse)
async def combined_search_endpoint(
    search_request: SearchRequest,
    search_manager: Annotated[VDBSearchManager, Depends(get_vdb_search_manager)]
) -> SearchResponse:
    try:
        # Execute the search queries using the search_manager
        search_response_dict = await search_manager.combined_search(search_vector=search_request.search_vector)

        # Validate the search response
        validated_response = SearchResponse(
            hits=[
                SearchHit(
                    id=hit["_id"],
                    score=hit["_score"],
                    source=hit["_source"]
                ) for hit in search_response_dict["hits"]
            ]
        )
        return validated_response
    except Exception as e:
        # If the search fails, raise an exception with the error message
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
