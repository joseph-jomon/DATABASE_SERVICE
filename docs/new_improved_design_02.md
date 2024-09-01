To improve the structure of your FastAPI application, particularly with regard to managing Elasticsearch connections using lifespan events, we can optimize the handling of these connections to ensure they are initialized once, reused efficiently, and properly closed when the application shuts down. Below is a refined version of your existing implementation, incorporating these improvements.

### Refined Implementation

#### `vdb_es_client.py`

This module will be responsible for managing the Elasticsearch connection and ensuring that it is properly initialized and closed using the lifespan events.

```python
# vdb_app/services/vdb_es_client.py

from elasticsearch import Elasticsearch
from vdb_app.vdb_config import vdb_settings

class VDBConnection:
    def __init__(self, host: str, timeout: int):
        self.client = Elasticsearch(host, timeout=timeout)

    def ping(self):
        return self.client.ping()

class VDBIndexManager:
    def __init__(self, client: Elasticsearch):
        self.client = client

    def create_index(self, index: str, mappings: dict):
        if not self.client.indices.exists(index=index):
            return self.client.indices.create(index=index, body=mappings)
        else:
            return {"acknowledged": True, "index": index, "message": "Index already exists"}

    def refresh_index(self, index: str):
        return self.client.indices.refresh(index=index)

class VDBDocumentManager:
    def __init__(self, client: Elasticsearch, index: str):
        self.client = client
        self.index = index

    def insert_document(self, doc: dict, doc_id: str):
        return self.client.index(index=self.index, id=doc_id, document=doc)

    def search_documents(self, query: dict):
        return self.client.search(index=self.index, body=query)

# Elasticsearch client instance
es_client = None

def init_es_client():
    global es_client
    es_client = VDBConnection(
        host=vdb_settings.ELASTICSEARCH_HOST,
        timeout=vdb_settings.TIMEOUT
    )

def get_vdb_connection():
    return es_client

def get_vdb_index_manager():
    return VDBIndexManager(client=es_client.client)

def get_vdb_document_manager(index: str):
    return VDBDocumentManager(client=es_client.client, index=index)

def close_es_client():
    if es_client:
        es_client.client.transport.close()
```

### `vdb_main.py`

This is where we manage the lifecycle of the Elasticsearch connection using the `lifespan` context manager.

```python
# vdb_app/vdb_main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from vdb_app.routers import vdb_ingest
from vdb_app.services.vdb_es_client import init_es_client, close_es_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Elasticsearch client
    init_es_client()

    yield  # The application runs here

    # Cleanup the Elasticsearch client
    close_es_client()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware if needed
origins = [
    "http://localhost",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vdb_ingest.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### `vdb_ingest.py`

This module handles the API endpoints for interacting with Elasticsearch. The improvements include more streamlined dependency injection.

```python
# vdb_app/routers/vdb_ingest.py

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

@router.post("/ingest/{index_name}")
async def ingest_document(
    index_name: str,
    doc: VDBDocument,
    index_manager: VDBIndexManager = Depends(get_vdb_index_manager),
    doc_manager: VDBDocumentManager = Depends(lambda: get_vdb_document_manager(index=index_name))
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
        response = index_manager.create_index(index=index_name, mappings=mappings)
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
        "fields": ["Image", "Combined_Text", "Immobilie", "Headline", "Lage"],
    }

    try:
        response = doc_manager.search_documents(query=query)
        return {"hits": response['hits']['hits']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

### Benefits of the Refined Implementation

1. **Centralized Connection Management**: The Elasticsearch connection is managed centrally, ensuring it is only initialized once during the application startup and properly closed at shutdown. This avoids issues with multiple connections and ensures that resources are properly managed.

2. **Efficient Resource Usage**: By managing the connection lifecycle with the lifespan context manager, you ensure that resources are used efficiently, reducing the overhead associated with repeatedly opening and closing connections.

3. **Dependency Injection**: The use of FastAPI's `Depends` allows for clean, testable, and reusable code. Dependencies are injected into routes, ensuring that each route has the necessary tools (like `VDBDocumentManager`) to perform its tasks.

4. **Scalability**: This structure is scalable and can easily handle more complex scenarios, such as managing multiple indices or databases, by simply extending the services and routers.

### Summary

Using lifespan events in FastAPI is an excellent approach for managing database connections, particularly when dealing with connection pools or persistent connections like those used with Elasticsearch. The refined implementation ensures that your application is efficient, scalable, and easy to maintain, providing a robust foundation for building on top of Elasticsearch.