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
        if self.client.indices.exists(index=index):
            self.client.indices.delete(index=index)
        return self.client.indices.create(index=index, mappings=mappings)

    def refresh_index(self, index: str):
        return self.client.indices.refresh(index=index)

class VDBDocumentManager:
    def __init__(self, client: Elasticsearch, index: str):
        self.client = client
        self.index = index

    def insert_document(self, doc: dict, doc_id: int):
        return self.client.index(index=self.index, id=doc_id, document=doc)

    def search_documents(self, query: dict):
        return self.client.search(index=self.index, body=query)

# Dependency Injection
def get_vdb_connection():
    return VDBConnection(
        host=vdb_settings.ELASTICSEARCH_HOST,
        timeout=vdb_settings.TIMEOUT
    )

def get_vdb_index_manager(connection: VDBConnection = Depends(get_vdb_connection)):
    return VDBIndexManager(client=connection.client)

def get_vdb_document_manager(index: str, connection: VDBConnection = Depends(get_vdb_connection)):
    return VDBDocumentManager(client=connection.client, index=index)
