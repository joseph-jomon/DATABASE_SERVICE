To implement the `vdb_es_client.py` with the async version of Elasticsearch, you will need to make some changes to the code to support asynchronous operations. This involves using `AsyncElasticsearch` instead of `Elasticsearch` and modifying the methods to be asynchronous.

### Updated `vdb_es_client.py`

Here’s how you can modify the `vdb_es_client.py` to use the async version of Elasticsearch:

```python
# vdb_app/services/vdb_es_client.py

from elasticsearch import AsyncElasticsearch
from vdb_app.vdb_config import vdb_settings

class VDBConnection:
    def __init__(self, host: str, timeout: int):
        self.client = AsyncElasticsearch(host, timeout=timeout)

    async def ping(self):
        return await self.client.ping()

class VDBIndexManager:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def create_index(self, index: str, mappings: dict):
        exists = await self.client.indices.exists(index=index)
        if not exists:
            return await self.client.indices.create(index=index, body=mappings)
        else:
            return {"acknowledged": True, "index": index, "message": "Index already exists"}

    async def refresh_index(self, index: str):
        return await self.client.indices.refresh(index=index)

class VDBDocumentManager:
    def __init__(self, client: AsyncElasticsearch, index: str):
        self.client = client
        self.index = index

    async def insert_document(self, doc: dict, doc_id: str):
        return await self.client.index(index=self.index, id=doc_id, document=doc)

    async def search_documents(self, query: dict):
        return await self.client.search(index=self.index, body=query)

# Elasticsearch client instance
es_client = None

async def init_es_client():
    global es_client
    es_client = VDBConnection(
        host=vdb_settings.ELASTICSEARCH_HOST,
        timeout=vdb_settings.TIMEOUT
    )

async def get_vdb_connection():
    return es_client

async def get_vdb_index_manager():
    return VDBIndexManager(client=es_client.client)

async def get_vdb_document_manager(index: str):
    return VDBDocumentManager(client=es_client.client, index=index)

async def close_es_client():
    if es_client:
        await es_client.client.close()
```

### Key Changes:
1. **AsyncElasticsearch**: The `AsyncElasticsearch` class is used instead of `Elasticsearch` to support asynchronous operations.
2. **Async Methods**: All methods that interact with Elasticsearch are now asynchronous, using `await` for each operation.
3. **Asynchronous Lifecycle Management**: The functions `init_es_client()` and `close_es_client()` are now asynchronous.

### Do You Need to Change Other Files?

Yes, since you're using the async version of Elasticsearch, you'll also need to ensure that your FastAPI routes and any other functions interacting with these services are asynchronous. Here's what you should do:

#### 1. Update FastAPI Endpoints:
- Ensure that all FastAPI routes that use the `VDBDocumentManager` and `VDBIndexManager` are defined as `async def` and use `await` when calling the methods from these managers.

Example:

```python
from fastapi import APIRouter, Depends, HTTPException
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

async def get_document_manager(index_name: str) -> VDBDocumentManager:
    return await get_vdb_document_manager(index=index_name)

@router.post("/ingest/{index_name}")
async def ingest_document(
    index_name: str,
    doc: VDBDocument,
    index_manager: VDBIndexManager = Depends(get_vdb_index_manager),
    doc_manager: VDBDocumentManager = Depends(get_document_manager)
):
    try:
        # Ensure the index exists with the correct mappings
        mappings = {
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
        response = await index_manager.create_index(index=index_name, mappings=mappings)
        if not response.get('acknowledged'):
            raise HTTPException(status_code=500, detail="Failed to create index")

        response = await doc_manager.insert_document(doc.model_dump(), doc_id=doc.id)
        await index_manager.refresh_index(index=index_name)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")

@router.get("/search/{index_name}")
async def search(
    index_name: str,
    query_vector: list[float],
    doc_manager: VDBDocumentManager = Depends(get_document_manager)
):
    query = {
        "knn": {
            "field": "EMBEDDINGS_TEXT",
            "query_vector": query_vector,
            "k": 10,
            "num_candidates": 100,
        },
        "fields": ["Image", "Combined_Text", "Immobilie", "Headline", "Lage"],
    }

    try:
        response = await doc_manager.search_documents(query=query)
        return {"hits": response['hits']['hits']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

### Summary of Changes:
- **Asynchronous Code**: Convert all methods that interact with Elasticsearch to be asynchronous.
- **FastAPI Routes**: Update any FastAPI routes that use these services to be asynchronous as well.
- **Dependencies**: Ensure that dependencies are also updated to use `await` when necessary.

These changes ensure that your application leverages asynchronous operations throughout, providing better scalability and performance, especially when dealing with I/O-bound tasks like interacting with Elasticsearch.