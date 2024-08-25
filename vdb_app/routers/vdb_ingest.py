# vdb_app/routers/vdb_ingest.py

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from vdb_app.services.vdb_es_client import (
    get_vdb_document_manager, get_vdb_index_manager, VDBIndexManager, VDBDocumentManager
)

router = APIRouter()

class VDBDocument(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: list[float]
    EMBEDDINGS_IMAGE: list[float]

@router.post("/ingest/{index_name}")
async def ingest_document(
    index_name: str,
    doc: VDBDocument,
    index_manager: VDBIndexManager = Depends(get_vdb_index_manager),
    doc_manager: VDBDocumentManager = Depends(lambda: get_vdb_document_manager(index=index_name))
):
    try:
        # Ensure the index exists
        response = index_manager.create_index(index=index_name, mappings={})
        if not response.get('acknowledged'):
            raise HTTPException(status_code=500, detail="Failed to create index")

        response = doc_manager.insert_document(doc.dict(), doc_id=doc.id)
        index_manager.refresh_index(index=index_name)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")

@router.get("/search/{index_name}")
async def search(
    index_name: str,
    query_vector: list[float],
    doc_manager: VDBDocumentManager = Depends(lambda: get_vdb_document_manager(index=index_name))
):
    query = {
        "knn": {
            "field": "EMBEDDINGS_TEXT",
            "query_vector": query_vector,
            "k": 10,
            "num_candidates": 100,
        },
        "fields": ["Image"],
    }

    try:
        response = doc_manager.search_documents(query=query)
        return {"hits": response['hits']['hits']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
