Professional implementations of Elasticsearch clients in FastAPI applications emphasize **efficient connection management**, **scalability**, **maintainability**, and **robustness**. This typically involves:

1. **Using FastAPI's Lifespan Events**: To initialize and clean up resources during the application's startup and shutdown.
2. **Storing Clients in `app.state`**: To avoid global variables and ensure thread-safe access.
3. **Configuring Connection Pool Parameters**: To optimize performance based on application load.
4. **Dependency Injection**: To provide easy and testable access to the Elasticsearch client within your endpoints.
5. **Error Handling and Logging**: To gracefully handle failures and maintain observability.

Below is a comprehensive guide to professionally implement an Elasticsearch client with connection pooling in a FastAPI application.

### 1. **Refactor `vdb_es_client.py`**

We'll adjust your `vdb_es_client.py` to initialize the Elasticsearch client with connection pooling parameters, store it in `app.state`, and provide dependency injection functions.

```python
# vdb_app/services/vdb_es_client.py

from elasticsearch import AsyncElasticsearch, ElasticsearchException
from fastapi import FastAPI, Depends, HTTPException
from vdb_app.vdb_config import vdb_settings

class VDBConnection:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ping(self):
        try:
            return await self.client.ping()
        except ElasticsearchException as e:
            # Log the exception as needed
            return False

class VDBIndexManager:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def create_index(self, index: str, mappings: dict):
        try:
            exists = await self.client.indices.exists(index=index)
            if not exists:
                return await self.client.indices.create(index=index, body=mappings)
            else:
                return {"acknowledged": True, "index": index, "message": "Index already exists"}
        except ElasticsearchException as e:
            # Log the exception as needed
            raise e

    async def refresh_index(self, index: str):
        try:
            return await self.client.indices.refresh(index=index)
        except ElasticsearchException as e:
            # Log the exception as needed
            raise e

class VDBDocumentManager:
    def __init__(self, client: AsyncElasticsearch, index: str):
        self.client = client
        self.index = index

    async def insert_document(self, doc: dict, doc_id: str):
        try:
            return await self.client.index(index=self.index, id=doc_id, document=doc)
        except ElasticsearchException as e:
            # Log the exception as needed
            raise e

    async def search_documents(self, query: dict):
        try:
            return await self.client.search(index=self.index, body=query)
        except ElasticsearchException as e:
            # Log the exception as needed
            raise e

# Dependency Injection Functions
async def get_vdb_connection(app: FastAPI) -> VDBConnection:
    return app.state.es_connection

async def get_vdb_index_manager(app: FastAPI) -> VDBIndexManager:
    return VDBIndexManager(client=app.state.es_connection.client)

async def get_vdb_document_manager(app: FastAPI, index: str) -> VDBDocumentManager:
    return VDBDocumentManager(client=app.state.es_connection.client, index=index)
```

### 2. **Configure FastAPI Application Lifespan**

Utilize FastAPI's lifespan events to initialize and close the Elasticsearch client properly. This ensures that connections are established when the application starts and gracefully closed when the application shuts down.

```python
# vdb_app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from vdb_app.services.vdb_es_client import init_es_client, close_es_client
from vdb_app.routers import vdb_ingest  # Assuming you have a router module

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Elasticsearch client with connection pooling parameters
    es_client = AsyncElasticsearch(
        hosts=[vdb_settings.ELASTICSEARCH_HOST],
        timeout=vdb_settings.TIMEOUT,
        maxsize=20,  # Maximum number of connections in the pool
        # Additional connection pool settings can be configured here
        # e.g., http_auth, ssl, etc.
    )
    
    # Create VDBConnection instance
    app.state.es_connection = VDBConnection(client=es_client)
    
    # Optionally, ping Elasticsearch to ensure connectivity
    if not await app.state.es_connection.ping():
        raise RuntimeError("Cannot connect to Elasticsearch")
    
    yield  # Application runs here
    
    # Cleanup Elasticsearch client
    await app.state.es_connection.client.close()

app = FastAPI(lifespan=lifespan)

# Include your routers
app.include_router(vdb_ingest.router)

# Add CORS middleware or other middlewares as needed
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8000",
    # Add other allowed origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. **Implement Dependency Injection in Routers**

Ensure that your FastAPI routers utilize the dependency injection functions to access the Elasticsearch client and its managers. This promotes modularity and testability.

```python
# vdb_app/routers/vdb_ingest.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from vdb_app.services.vdb_es_client import (
    get_vdb_document_manager,
    get_vdb_index_manager,
    VDBIndexManager,
    VDBDocumentManager
)

router = APIRouter()

class VDBDocument(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: List[float]
    EMBEDDINGS_IMAGE: List[float]

# Dependency to provide VDBDocumentManager with the correct index
async def get_document_manager(index_name: str, 
                               doc_manager: VDBDocumentManager = Depends(get_vdb_document_manager)) -> VDBDocumentManager:
    return await get_vdb_document_manager(index=index_name)

@router.post("/ingest/{index_name}")
async def ingest_document(
    index_name: str,
    doc: VDBDocument,
    index_manager: VDBIndexManager = Depends(get_vdb_index_manager),
    doc_manager: VDBDocumentManager = Depends(lambda index_name: get_document_manager(index_name))
):
    try:
        # Define mappings if necessary
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

        # Ensure the index exists
        response = await index_manager.create_index(index=index_name, mappings=mappings)
        if not response.get('acknowledged', False):
            raise HTTPException(status_code=500, detail="Failed to create index")

        # Insert the document
        response = await doc_manager.insert_document(doc.dict(), doc.id)
        
        # Refresh the index to make the document searchable immediately
        await index_manager.refresh_index(index=index_name)
        
        return {"status": "success", "response": response}
    except Exception as e:
        # Log the exception as needed
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")

@router.get("/search/{index_name}")
async def search(
    index_name: str,
    query_vector: List[float],
    doc_manager: VDBDocumentManager = Depends(lambda index_name: get_document_manager(index_name))
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
        # Log the exception as needed
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

**Note**: The above lambda usage in dependencies is a simple way to pass parameters, but for more complex scenarios, consider using custom dependencies or dependency factories.

### 4. **Optimize Connection Pool Parameters**

Professionally, you should configure the connection pool based on your application's load and Elasticsearch cluster's capacity. Here’s how to adjust some key parameters:

- **`maxsize`**: Maximum number of concurrent connections. Increase this if you have high traffic.
- **`connections_per_node`**: Number of connections per Elasticsearch node. Adjust based on the number of nodes and expected concurrency.

```python
# Example adjustment in init_es_client within lifespan
es_client = AsyncElasticsearch(
    hosts=[vdb_settings.ELASTICSEARCH_HOST],
    timeout=vdb_settings.TIMEOUT,
    maxsize=20,  # Adjust based on expected load
    connections_per_node=10,  # Adjust based on the number of nodes and concurrency
    # Additional settings:
    # e.g., SSL configurations, authentication, etc.
)
```

**Professional Tip**: Monitor your application's performance and Elasticsearch cluster's load. Tools like **Elasticsearch's own monitoring APIs**, **APM solutions**, and **FastAPI's logging** can help you tune these parameters effectively.

### 5. **Implement Robust Error Handling and Logging**

Ensure that your application gracefully handles Elasticsearch exceptions and logs relevant information for troubleshooting.

```python
# Example in vdb_es_client.py

from elasticsearch import ElasticsearchException
import logging

logger = logging.getLogger(__name__)

class VDBConnection:
    # ... existing code ...

    async def ping(self):
        try:
            return await self.client.ping()
        except ElasticsearchException as e:
            logger.error(f"Elasticsearch ping failed: {e}")
            return False

# Similarly, add logging in other methods
```

**Configure Logging in FastAPI**:

```python
# vdb_app/main.py

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 6. **Testing and Validation**

Professional applications include thorough testing to ensure connection management works as expected.

- **Unit Tests**: Mock the Elasticsearch client to test your dependency injection and endpoint logic without requiring a live Elasticsearch instance.
- **Integration Tests**: Test against a real or test Elasticsearch cluster to validate end-to-end functionality.

**Example with `pytest` and `httpx`**:

```python
# tests/test_ingest.py

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from vdb_app.main import app  # Import your FastAPI app

@pytest.mark.asyncio
async def test_ingest_document():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        doc = {
            "Image": "image_url",
            "Combined_Text": "Some combined text",
            "Immobilie": "Some property",
            "Headline": "A headline",
            "Lage": "Location",
            "id": "unique_id",
            "EMBEDDINGS_TEXT": [0.1] * 512,
            "EMBEDDINGS_IMAGE": [0.1] * 512
        }
        response = await ac.post("/ingest/test-index", json=doc)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

### 7. **Security Considerations**

Ensure that your Elasticsearch client connections are secure, especially in production environments.

- **Authentication**: Use proper authentication mechanisms (e.g., API keys, Basic Auth, OAuth).
- **SSL/TLS**: Encrypt communication between your application and Elasticsearch.
- **Access Controls**: Limit the permissions of the Elasticsearch user to only what's necessary.

**Example Configuration with SSL and Authentication**:

```python
es_client = AsyncElasticsearch(
    hosts=[vdb_settings.ELASTICSEARCH_HOST],
    timeout=vdb_settings.TIMEOUT,
    maxsize=20,
    connections_per_node=10,
    http_auth=(vdb_settings.ELASTICSEARCH_USER, vdb_settings.ELASTICSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=True,
    ssl_show_warn=False,
    # Optionally, provide paths to SSL certificates
    # ca_certs="/path/to/ca.crt",
    # client_cert="/path/to/client.crt",
    # client_key="/path/to/client.key",
)
```

### 8. **Monitoring and Metrics**

Integrate monitoring to track the health and performance of your Elasticsearch connections.

- **Elasticsearch's Monitoring APIs**: Use these to gather metrics about cluster health and performance.
- **Application Monitoring**: Integrate with monitoring tools like **Prometheus**, **Grafana**, or **New Relic** to track application-level metrics.
- **Logging**: Ensure that important events and errors are logged for auditing and troubleshooting.

**Example Integration with Prometheus**:

```python
# vdb_app/main.py

from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

### Summary of Professional Practices

1. **Initialization and Cleanup**: Use FastAPI's lifespan events to manage the lifecycle of your Elasticsearch client.
2. **Connection Pooling**: Configure `AsyncElasticsearch` with appropriate connection pool settings (`maxsize`, `connections_per_node`) based on your application's needs.
3. **Dependency Injection**: Utilize FastAPI's dependency injection to provide access to the Elasticsearch client and its managers within your routes.
4. **Error Handling and Logging**: Implement robust error handling and logging to monitor and troubleshoot issues effectively.
5. **Security**: Secure your Elasticsearch connections with authentication and SSL/TLS.
6. **Monitoring**: Integrate monitoring tools to keep track of the application's and Elasticsearch's performance and health.
7. **Testing**: Implement unit and integration tests to ensure the reliability of your connection management and overall application functionality.
8. **Configuration Management**: Use environment variables or configuration files to manage sensitive information and configuration parameters securely.

By following these practices, you ensure that your FastAPI application interacts with Elasticsearch in a scalable, maintainable, and secure manner, aligning with professional standards.