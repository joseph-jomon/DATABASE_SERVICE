# vdb_app/services/vdb_es_client.py

from elasticsearch import AsyncElasticsearch, helpers
from vdb_app.vdb_config import vdb_settings
from fastapi import FastAPI, Request

class VDBConnection:
    def __init__(self, host: str, timeout: int):
        self.client = AsyncElasticsearch(host, timeout=timeout)

    async def ping(self):
        # Asynchronous ping to check if the Elasticsearch cluster is up
        return await self.client.ping()

class VDBIndexManager:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def create_index(self, index: str, mappings: dict):
        # Check if the index already exists
        exists = await self.client.indices.exists(index=index)
        if not exists:
            # Create the index with the specified mappings
            return await self.client.indices.create(index=index, body={"mappings": mappings})
        else:
            # Return an acknowledgment if the index already exists
            return {"acknowledged": True, "index": index, "message": "Index already exists"}

    async def refresh_index(self, index: str):
        # Refresh the index to make recent changes searchable
        return await self.client.indices.refresh(index=index)

class VDBDocumentManager:
    def __init__(self, client: AsyncElasticsearch, index_doc: str):
        self.client = client
        self.index_doc = index_doc

    async def insert_document(self, doc: dict, doc_id: str):
        # Insert a single document asynchronously
        return await self.client.index(index=self.index_doc, id=doc_id, document=doc)

    async def bulk_insert(self, actions: list):
        # Perform asynchronous bulk insertion
        # The actions list should contain the individual operations in the appropriate bulk API format
        return await helpers.async_bulk(self.client, actions)

    async def search_documents(self, query: dict):
        # Asynchronously search the index based on the provided query
        return await self.client.search(index=self.index_doc, body=query)

# Initialize the Elasticsearch client and store it in FastAPI's app.state
async def init_es_client(app: FastAPI):
    # Create an instance of VDBConnection
    es_client = VDBConnection(
        host=vdb_settings.ELASTICSEARCH_HOST,
        timeout=vdb_settings.TIMEOUT
    )
    app.state.es_client = es_client

# Cleanup the Elasticsearch client when the app is shutting down
async def close_es_client(app: FastAPI):
    # Close the Elasticsearch client connection asynchronously
    es_client = app.state.es_client
    if es_client:
        await es_client.client.close()

# Dependency injection functions for FastAPI
async def get_vdb_connection(request: Request) -> VDBConnection:
    # Get the Elasticsearch connection from the app state
    return request.app.state.es_client

async def get_vdb_index_manager(request: Request) -> VDBIndexManager:
    # Create an instance of VDBIndexManager using the shared Elasticsearch client
    return VDBIndexManager(client=request.app.state.es_client.client)

async def get_vdb_document_manager(request: Request, index_name: str) -> VDBDocumentManager:
    # Create an instance of VDBDocumentManager for the specified index
    return VDBDocumentManager(client=request.app.state.es_client.client, index_doc=index_name)
