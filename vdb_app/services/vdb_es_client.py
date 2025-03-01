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

class VDBSearchManager:
    def __init__(self, client: AsyncElasticsearch, text_index_name: str, image_index_name: str):
        self.client = client
        self.text_index_name = text_index_name
        self.image_index_name = image_index_name
    
    async def combined_search(self, search_vector: list) -> dict:
        # Define the k-NN search queries for both text and image embeddings
        text_query = {
            "knn": {
                "field": "text_embedding",
                "query_vector": search_vector,
                "k": 10,
                "num_candidates": 20,
            },
            "_source": ["id", "text_embedding"],
        }

        image_query = {
            "knn": {
                "field": "image_embedding",
                "query_vector": search_vector,
                "k": 10,
                "num_candidates": 10,
            },
            "_source": ["id", "image_embedding"],
        }

        # Execute the search queries using the doc_manager
        text_response = await self.client.search(index=self.text_index_name, body=text_query)
        image_response = await self.client.search(index=self.image_index_name, body=image_query)

        # Combine the hits from both responses
        combined_hits = text_response['hits']['hits'] + image_response['hits']['hits']

        # Sort the combined hits based on the similarity score
        sorted_hits = sorted(combined_hits, key=lambda x: x['_score'], reverse=True)

        # Create the search response
        search_response = {
            "hits": sorted_hits
        }
        return search_response

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

async def get_vdb_search_manager(request: Request, text_index_name: str, image_index_name: str) -> VDBSearchManager:
    # Create an instance of VDBSearchManager for the specified text and image indices
    return VDBSearchManager(client=request.app.state.es_client.client, text_index_name=text_index_name, image_index_name=image_index_name)
