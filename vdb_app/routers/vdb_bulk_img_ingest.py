# vdb_app/routers/vdb_vector_ingest.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated
from vdb_app.routers.validation_models import VectorDataBatch  # Import the new vector model
from vdb_app.services.vdb_es_client import (
    get_vdb_document_manager, get_vdb_index_manager, VDBIndexManager, VDBDocumentManager
)

# Create a separate router for vector ingestion
vector_router = APIRouter()

@vector_router.post("/ingest_img_bulk/")
async def ingest_vector_batch(
    batch: VectorDataBatch,
   # index_name: str,  # Specify the index name in the request
    index_manager: Annotated[VDBIndexManager, Depends(get_vdb_index_manager)],
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
):
    """
    Endpoint to ingest a batch of vector data items into Elasticsearch.
    
    Parameters:
    - `batch`: The list of vector data items for ingestion, structured according to `VectorDataBatch`.
    - `index_name`: The Elasticsearch index where vectors will be stored.

    Returns:
    - Status message indicating success or failure of the batch ingestion.
    """
    try:

        # Define mappings for the new index with dense vector fields
        vector_mappings = {
            "properties": {
                "image_embedding": {
                    "type": "dense_vector",
                    "dims": len(batch.items[0].image_embedding),  # Assuming each item has a 'image_embedding' field
                    "similarity": "cosine"
                },
                "id": {"type": "keyword"},
                "company_name": {"type": "keyword"},
                "tracking_path": {"type": "keyword"} # Add tracking_path to the mapping
            }
        }
        index_name = doc_manager.index_doc

        # Check if the index already exists
        index_exists = await index_manager.client.indices.exists(index=index_name)
        if not index_exists:
            # Create the index with vector mappings
            response = await index_manager.create_index(index=index_name, mappings=vector_mappings)
            if not response.get('acknowledged'):
                raise HTTPException(status_code=500, detail=f"Failed to create index: {index_name}")

        # Perform bulk insertion asynchronously
        actions = [
            {
                "_index": index_name, 
                "_id": f"{item.tracking_path}", 
                "_source": item.dict(exclude={"index_name"})
            }
            for item in batch.items
        ]
        response = await doc_manager.bulk_insert(actions)

        # Refresh the index to make recent changes searchable
        await index_manager.refresh_index(index=index_name)

        return {"status": "success", "message": f"{len(batch.items)} vector items ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest vector batch: {str(e)}")
