from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from .validation_models import  VDBDocument, VDBSearchDocument, SearchResponse, ES_Hit
from services.vdb_es_client import (
    get_vdb_document_manager, get_vdb_index_manager, VDBIndexManager, VDBDocumentManager
)
from pydantic import BaseModel, ValidationError

router = APIRouter()


# Centralized index mappings configuration
def get_index_mappings() -> dict:
    return {
        "mappings": {
            "properties": {
                "Image": {"type": "text", "analyzer": "german"},
                "Combined_Text": {"type": "text", "analyzer": "german"},
                "Immobilie": {"type": "text", "analyzer": "german"},
                "Headline": {"type": "text", "analyzer": "german"},
                "Lage": {"type": "text", "analyzer": "german"},
                "id": {"type": "keyword"},
                "EMBEDDINGS_TEXT": {
                    "type": "dense_vector",
                    "dims": 512,
                    "index": True,
                    "similarity": "cosine"
                },
                "EMBEDDINGS_IMAGE": {
                    "type": "dense_vector",
                    "dims": 512,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }


@router.post("/ingest/{index_name}")
async def ingest_document(
    index_name: str,
    doc: VDBDocument,
    index_manager: Annotated[VDBIndexManager, Depends(get_vdb_index_manager)],
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
):
    try:
        # Use the centralized index mappings
        mappings = get_index_mappings()
        response = await index_manager.create_index(index=index_name, mappings=mappings)
        if not response.get('acknowledged'):
            raise HTTPException(status_code=500, detail="Failed to create index")

        response = await doc_manager.insert_document(doc.model_dump(), doc_id=doc.id)
        await index_manager.refresh_index(index=index_name)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")

@router.post("/search/{index_name}", response_model=SearchResponse)  # Use POST instead of GET
async def search(
    query_vector: VDBSearchDocument,
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
) -> SearchResponse:
    query   = {
        "knn": {
            "field": "EMBEDDINGS_TEXT",
            "query_vector": query_vector.search_vector,
            "k": 10,
            "num_candidates": 100,
        },
       # "fields": ["Image"],# , "Combined_Text", "Immobilie", "Headline", "Lage"
    }

    try:
         # Execute the search query using the doc_manager
        response = await doc_manager.search_documents(query=query)
        hits_list = response['hits']['hits']
        search_response_dict = {
            "hits": hits_list
        }
        # Wrap the hits list in a dictionary and validate with the SearchResponse model
        try:
            SearchResponse(**search_response_dict)
        except ValidationError as exc:
            print(repr(exc.errors()[0]['type']))
        validated_response = SearchResponse(**search_response_dict)

        #validation setp
        try:
            SearchResponse.model_validate(validated_response)
        except ValidationError as exc:
            print(repr(exc.error()[0]['type']))
        return validated_response
    except Exception as e:
         # If the search fails, raise an exception with the error message
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
