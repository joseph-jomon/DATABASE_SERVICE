# vdb_app/routers/vdb_ingest.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated
from vdb_app.routers.validation_models import IngestDataBatch, SearchRequest, SearchResponse
from vdb_app.services.vdb_es_client import (
    get_vdb_document_manager, get_vdb_index_manager, VDBIndexManager, VDBDocumentManager
)

router = APIRouter()

@router.post("/ingest/")
async def ingest_data_batch(
    batch: IngestDataBatch,
    index_manager: Annotated[VDBIndexManager, Depends(get_vdb_index_manager)],
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
):
    try:
        # Group items by index_name
        index_batches = {}
        for item in batch.items:
            if item.index_name not in index_batches:
                index_batches[item.index_name] = []
            index_batches[item.index_name].append(item)

        # Process each index separately
        for index_name, items in index_batches.items():
            # Define the index mappings
            mappings = {
                "properties": {
                    "text_embedding": {
                        "type": "dense_vector",
                        "dims": len(items[0].text_embedding),
                        "index": True,
                        "similarity": "cosine"
                    },
                    "image_embedding": {
                        "type": "dense_vector",
                        "dims": len(items[0].image_embedding),
                        "index": True,
                        "similarity": "cosine"
                    },
                    "id": {"type": "keyword"}
                }
            }

            # Check if the index already exists
            index_exists = await index_manager.client.indices.exists(index=index_name)
            if not index_exists:
                # Create the index with the specified mappings
                response = await index_manager.create_index(index=index_name, mappings=mappings)
                if not response.get('acknowledged'):
                    raise HTTPException(status_code=500, detail=f"Failed to create or update index: {index_name}")

            # Perform bulk insertion asynchronously
            actions = [
                {"_index": index_name, "_id": item.id, "_source": item.dict(exclude={"index_name"})}
                for item in items
            ]
            response = await doc_manager.bulk_insert(actions)

            # Refresh the index to make recent changes searchable
            await index_manager.refresh_index(index=index_name)

        return {"status": "success", "message": f"{len(batch.items)} items ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest batch: {str(e)}")

@router.post("/search/{index_name}", response_model=SearchResponse)
async def search(
    index_name: str,
    search_request: SearchRequest,
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
) -> SearchResponse:
    # Define the k-NN search query using the search vector from the request
    query = {
        "knn": {
            "field": "text_embedding",
            "query_vector": search_request.search_vector,
            "k": 10,
            "num_candidates": 100,
        },
        "_source": ["id", "text_embedding", "image_embedding"],
    }

    try:
        # Execute the search query using the doc_manager
        response = await doc_manager.search_documents(query=query)
        hits_list = response['hits']['hits']
        search_response_dict = {
            "hits": hits_list
        }
        # Validate the search response
        validated_response = SearchResponse(**search_response_dict)
        return validated_response
    except Exception as e:
        # If the search fails, raise an exception with the error message
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
