# vdb_app/services/vdb_es_client.py

from elasticsearch import Elasticsearch
from vdb_config import vdb_settings

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
