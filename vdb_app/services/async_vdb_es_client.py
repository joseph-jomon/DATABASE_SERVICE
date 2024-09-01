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
